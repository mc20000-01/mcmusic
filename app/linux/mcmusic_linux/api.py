"""HTTP + session layer for the mcmusic server.

The server authenticates with the signed ``mcmusic_session`` cookie, exactly
like the browser and Android clients. Requests run off the GUI thread through a
small thread pool; results are delivered back on the Qt main thread.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import requests
from PySide6.QtCore import QObject, QSettings, Qt, Signal, Slot

from .models import (
    AdminStats,
    AdminUser,
    AlbumRef,
    ArtistRef,
    BuildInfo,
    DeviceRow,
    HomeData,
    ListeningUser,
    Me,
    PlaylistRef,
    RequestRow,
    SearchData,
    Section,
    Settings,
    Track,
)
from .paths import audio_cache_dir, settings_file
from .version import USER_AGENT

DEFAULT_SERVER = "http://127.0.0.1:8000"

# Only replay-safe writes go in the outbox. Toggles are kept separately so
# every tap survives a replay (mirrors the web client's REPLAYABLE list).
REPLAYABLE = [
    ("POST", re.compile(r"^like/\d+$"), True),
    ("POST", re.compile(r"^playlists/\d+/tracks$"), False),
    ("PATCH", re.compile(r"^playlists/\d+$"), False),
    ("DELETE", re.compile(r"^playlists/\d+$"), False),
    ("DELETE", re.compile(r"^playlists/\d+/tracks/\d+$"), False),
    ("PUT", re.compile(r"^settings$"), False),
]
CACHEABLE = [
    re.compile(r"^(me|settings|home|tracks|search|albums|album|artists|artist|likes|playlists|requests|devices|builds|version|ping)(/.*)?$"),
    re.compile(r"^tracks/\d+/(lyrics|sources)$"),
    re.compile(r"^public/(now/[^/]+|listening)$"),
    re.compile(r"^auth/(rotur|discord)/status$"),
]
CACHE_TTL = {
    "settings": 300, "home": 120, "tracks": 300, "albums": 600, "artists": 600,
    "likes": 120, "playlists": 120, "builds": 3600, "version": 3600,
    "devices": 60, "public/listening": 8, "requests": 30,
}


def _replay_rule(method: str, path: str):
    for verb, pattern, toggle in REPLAYABLE:
        if verb == method and pattern.match(path):
            return toggle
    return None


def _cache_ttl(path: str) -> int:
    head = path.split("/", 1)[0]
    return CACHE_TTL.get(head, 120)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status

    @property
    def offline(self) -> bool:
        """True for a transport failure, as opposed to an HTTP error."""
        return self.status == 0


# ── background runner ───────────────────────────────────────────────────────


class _Bridge(QObject):
    done = Signal(int, bool, object)


class Async(QObject):
    """Submit blocking work; callbacks run on the GUI thread."""

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="mcmusic-net")
        self._seq = 0
        self._lock = threading.Lock()
        self._callbacks: dict[int, tuple[Optional[Callable], Optional[Callable]]] = {}
        self._bridge = _Bridge(self)
        self._bridge.done.connect(self._finish, Qt.ConnectionType.QueuedConnection)

    def submit(self, fn: Callable[[], Any],
               ok: Optional[Callable[[Any], None]] = None,
               error: Optional[Callable[[Exception], None]] = None) -> int:
        with self._lock:
            self._seq += 1
            token = self._seq
            self._callbacks[token] = (ok, error)

        def work() -> None:
            try:
                value = fn()
            except Exception as exc:  # noqa: BLE001 - handed to the UI
                self._bridge.done.emit(token, False, exc)
            else:
                self._bridge.done.emit(token, True, value)

        try:
            self._pool.submit(work)
        except RuntimeError:
            self._callbacks.pop(token, None)
        return token

    @Slot(int, bool, object)
    def _finish(self, token: int, succeeded: bool, payload: object) -> None:
        with self._lock:
            pair = self._callbacks.pop(token, None)
        if not pair:
            return
        ok, error = pair
        if succeeded:
            if ok:
                ok(payload)
        elif error:
            error(payload if isinstance(payload, Exception) else Exception(str(payload)))

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


# ── persistent client state ────────────────────────────────────────────────


class SessionStore:
    """QSettings-backed session cookie + local preferences."""

    def __init__(self) -> None:
        if sys.platform == "win32":
            # The Windows bundle keeps its settings beside the other per-user
            # app data instead of the registry, so roaming/profile cleanup and
            # the documented %APPDATA% location actually agree.
            path = settings_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._s = QSettings(str(path), QSettings.IniFormat)
        else:
            # Preserve the existing native QSettings location on Linux/macOS.
            self._s = QSettings("mcmusic", "mcmusic-desktop")

    # base url -------------------------------------------------------------
    @property
    def base_url(self) -> str:
        return str(self._s.value("base_url", DEFAULT_SERVER) or DEFAULT_SERVER)

    @base_url.setter
    def base_url(self, value: str) -> None:
        self._s.setValue("base_url", value)
        self._s.sync()

    # cookies --------------------------------------------------------------
    def load_cookies(self) -> dict[str, str]:
        raw = str(self._s.value("cookies", "") or "")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            return {str(k): str(v) for k, v in data.items() if v}
        except (ValueError, TypeError):
            return {}

    def save_cookies(self, cookies: dict[str, str]) -> None:
        self._s.setValue("cookies", json.dumps(cookies, separators=(",", ":")))
        self._s.sync()

    def clear_session(self) -> None:
        self._s.remove("cookies")
        self._s.remove("me")
        self._s.sync()

    # cached me ------------------------------------------------------------
    @property
    def cached_me(self) -> Optional[Me]:
        raw = str(self._s.value("me", "") or "")
        if not raw:
            return None
        try:
            return Me.from_json(json.loads(raw))
        except (ValueError, TypeError):
            return None

    @cached_me.setter
    def cached_me(self, me: Optional[Me]) -> None:
        if me is None:
            self._s.remove("me")
        else:
            self._s.setValue("me", json.dumps(me.to_json(), separators=(",", ":")))
        self._s.sync()

    # native app token (Rotur sign-in / device pairing) --------------------
    @property
    def device_token(self) -> str:
        return str(self._s.value("device_token", "") or "")

    @device_token.setter
    def device_token(self, value: str) -> None:
        if value:
            self._s.setValue("device_token", value)
        else:
            self._s.remove("device_token")
        self._s.sync()

    @property
    def pending_token(self) -> str:
        return str(self._s.value("pending_token", "") or "")

    @pending_token.setter
    def pending_token(self, value: str) -> None:
        if value:
            self._s.setValue("pending_token", value)
        else:
            self._s.remove("pending_token")
        self._s.sync()

    # derived listen-along invite link (never saved to server settings) ---
    @property
    def room_url(self) -> str:
        return str(self._s.value("room_url", "") or "")

    @room_url.setter
    def room_url(self, value: str) -> None:
        self._s.setValue("room_url", value)
        self._s.sync()

    # offline GET cache ----------------------------------------------------
    def _json_value(self, key: str, default: Any):
        raw = str(self._s.value(key, "") or "")
        if not raw:
            return default
        try:
            value = json.loads(raw)
            return value if isinstance(value, type(default)) else default
        except (ValueError, TypeError):
            return default

    def _set_json(self, key: str, value: Any) -> None:
        self._s.setValue(key, json.dumps(value, separators=(",", ":")))
        self._s.sync()

    def cache_get(self, key: str) -> Optional[dict]:
        entry = self._json_value("http_cache", {}).get(key)
        return entry if isinstance(entry, dict) and isinstance(entry.get("data"), dict) else None

    def cache_put(self, key: str, data: Any) -> None:
        if not isinstance(data, dict):
            return
        cache = self._json_value("http_cache", {})
        cache[key] = {"at": time.time(), "data": data}
        # A few hundred responses is plenty; keep the newest ones.
        if len(cache) > 400:
            for old in sorted(cache, key=lambda k: cache[k].get("at", 0))[:len(cache) - 400]:
                cache.pop(old, None)
        self._set_json("http_cache", cache)

    def cache_stats(self) -> tuple[int, int]:
        cache = self._json_value("http_cache", {})
        files = 0
        root = audio_cache_dir()
        if root.is_dir():
            files = sum(1 for p in root.iterdir() if p.is_file() and p.suffix != ".part")
        return len(cache), files

    def cache_clear(self, *, responses: bool = True, audio: bool = True) -> int:
        removed = 0
        if responses:
            removed += len(self._json_value("http_cache", {}))
            self._s.remove("http_cache")
        if audio:
            root = audio_cache_dir()
            if root.is_dir():
                for p in root.iterdir():
                    if p.is_file():
                        try:
                            p.unlink()
                            removed += 1
                        except OSError:
                            pass
        self._s.sync()
        return removed

    def cache_prune(self, max_age_days: int = 30, max_bytes: int = 2 * 1024**3) -> int:
        """Drop old audio files until the cache is under *max_bytes*."""
        root = audio_cache_dir()
        if not root.is_dir():
            return 0
        files = [p for p in root.iterdir() if p.is_file()]
        cutoff = time.time() - max(1, max_age_days) * 86400
        removed = 0
        for p in files:
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except OSError:
                pass
        total = sum(p.stat().st_size for p in files if p.exists())
        for p in sorted((p for p in files if p.exists()), key=lambda f: f.stat().st_mtime):
            if total <= max_bytes:
                break
            try:
                total -= p.stat().st_size
                p.unlink()
                removed += 1
            except OSError:
                pass
        return removed

    # offline write outbox -------------------------------------------------
    @property
    def outbox(self) -> list[dict]:
        return self._json_value("outbox", [])

    def outbox_add(self, method: str, path: str, body: Any = None) -> int:
        items = self.outbox
        toggle = _replay_rule(method, path)
        if not toggle:
            items = [i for i in items
                     if not (i.get("method") == method and i.get("path") == path
                             and json.dumps(i.get("body"), sort_keys=True)
                             == json.dumps(body, sort_keys=True))]
        items.append({"method": method, "path": path, "body": body, "at": time.time()})
        items = items[-200:]
        self._set_json("outbox", items)
        return len(items)

    def outbox_set(self, items: list[dict]) -> None:
        self._set_json("outbox", items)

    # queue / sleep timer snapshots ----------------------------------------
    @property
    def queue_snapshot(self) -> dict:
        snap = self._json_value("queue_snapshot", {})
        return snap if isinstance(snap, dict) else {}

    @queue_snapshot.setter
    def queue_snapshot(self, value: dict) -> None:
        self._set_json("queue_snapshot", value)

    @property
    def sleep_timer(self) -> dict:
        timer = self._json_value("sleep_timer", {})
        return timer if isinstance(timer, dict) else {}

    @sleep_timer.setter
    def sleep_timer(self, value: dict) -> None:
        if value:
            self._set_json("sleep_timer", value)
        else:
            self._s.remove("sleep_timer")
            self._s.sync()

    @property
    def reset_token(self) -> str:
        return str(self._s.value("reset_token", "") or "")

    @reset_token.setter
    def reset_token(self, value: str) -> None:
        if value:
            self._s.setValue("reset_token", value)
        else:
            self._s.remove("reset_token")
        self._s.sync()

    # appearance -----------------------------------------------------------
    @property
    def theme(self) -> str:
        return str(self._s.value("theme", "violet") or "violet")

    @theme.setter
    def theme(self, value: str) -> None:
        self._s.setValue("theme", value)

    @property
    def accent(self) -> str:
        return str(self._s.value("accent", "") or "")

    @accent.setter
    def accent(self, value: str) -> None:
        self._s.setValue("accent", value)

    @staticmethod
    def _icon_stroke(value) -> float:
        try:
            scale = float(value)
        except (TypeError, ValueError):
            return 1.0
        return min((1.0, 1.5, 2.0), key=lambda choice: abs(choice - scale))

    @property
    def icon_stroke(self) -> float:
        return self._icon_stroke(self._s.value("iconStroke", 1.0))

    @icon_stroke.setter
    def icon_stroke(self, value: float) -> None:
        self._s.setValue("iconStroke", self._icon_stroke(value))

    @property
    def icon_filled(self) -> bool:
        return bool(self._s.value("iconFilled", False))

    @icon_filled.setter
    def icon_filled(self, value: bool) -> None:
        self._s.setValue("iconFilled", bool(value))

    # Local 4.2.0 motion switch. It lives in QSettings only: server settings
    # have no `playfulMotion` key and the stored server payload is unchanged.
    @property
    def playful_motion(self) -> bool:
        value = self._s.value("playfulMotion", True)
        if isinstance(value, str):
            return value.casefold() in ("1", "true", "yes", "on")
        return bool(value)

    @playful_motion.setter
    def playful_motion(self, value: bool) -> None:
        self._s.setValue("playfulMotion", bool(value))
        self._s.sync()

    # Local-only lyrics-sheet tab; the server settings payload is untouched.
    @property
    def local_lyrics_tab(self) -> str:
        value = str(self._s.value("localLyricsTab", "lyrics") or "lyrics")
        return value if value in ("lyrics", "up-next") else "lyrics"

    @local_lyrics_tab.setter
    def local_lyrics_tab(self, value: str) -> None:
        key = str(value)
        self._s.setValue("localLyricsTab", key if key in ("lyrics", "up-next") else "lyrics")
        self._s.sync()

    @property
    def volume(self) -> float:
        try:
            return float(self._s.value("volume", 0.8))
        except (TypeError, ValueError):
            return 0.8

    @volume.setter
    def volume(self, value: float) -> None:
        self._s.setValue("volume", round(float(value), 3))

    @property
    def device_hash(self) -> str:
        existing = str(self._s.value("device_hash", "") or "")
        if existing:
            return existing
        import hashlib
        seed = f"{platform.node()}-{os.path.expanduser('~')}-{platform.machine()}"
        value = hashlib.sha1(seed.encode("utf-8"), usedforsecurity=False).hexdigest()[:32]
        self._s.setValue("device_hash", value)
        return value

    def sync(self) -> None:
        self._s.sync()


# ── HTTP client ─────────────────────────────────────────────────────────────


class Api:
    def __init__(self, store: SessionStore):
        self.store = store
        self.cookies: dict[str, str] = store.load_cookies()
        self.token: str = store.device_token
        self._local = threading.local()
        self._flush_lock = threading.Lock()
        self.base_url = normalize(store.base_url)

    # transport ------------------------------------------------------------
    def _session(self) -> requests.Session:
        s = getattr(self._local, "session", None)
        system = "Darwin" if platform.system() == "Darwin" else (
            "Windows" if platform.system() == "Windows" else "Linux")
        if s is None:
            s = requests.Session()
            s.headers.update({
                "User-Agent": USER_AGENT.replace("Qt", f"{system}; Qt"),
                "Accept": "application/json",
            })
            self._local.session = s
        if self.token:
            s.headers["Authorization"] = f"Bearer {self.token}"
        else:
            s.headers.pop("Authorization", None)
        return s

    def set_token(self, token: str) -> None:
        """Adopt a native-client device token (Rotur sign-in / pairing)."""
        self.token = token.strip()
        self.store.device_token = self.token

    def clear_token(self) -> None:
        self.token = ""
        self.store.device_token = ""

    def set_base(self, raw: str) -> str:
        self.base_url = normalize(raw, self.base_url)
        self.store.base_url = self.base_url
        return self.base_url

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def web_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def cover_url(self, track_id: int | None) -> Optional[str]:
        return self.url(f"tracks/{track_id}/cover") if track_id else None

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def _absorb_cookies(self, response: requests.Response) -> None:
        changed = False
        for cookie in response.cookies:
            if cookie.value:
                if self.cookies.get(cookie.name) != cookie.value:
                    self.cookies[cookie.name] = cookie.value
                    changed = True
            else:
                self.cookies.pop(cookie.name, None)
                changed = True
        if changed:
            self.store.save_cookies(self.cookies)

    def request(self, method: str, path: str, body: dict | None = None,
                params: dict | None = None, timeout: tuple[float, float] = (12, 40),
                raw: bool = False, headers: dict | None = None) -> Any:
        url = self.url(path)
        final_headers = dict(headers or {})
        if self.cookies:
            final_headers["Cookie"] = self._cookie_header()
        try:
            response = self._session().request(
                method, url, json=body, params=params, headers=final_headers,
                timeout=timeout, allow_redirects=True,
            )
        except requests.Timeout:
            raise ApiError("Server timed out") from None
        except requests.ConnectionError:
            raise ApiError("Can't reach the server") from None
        except requests.RequestException as exc:
            raise ApiError(str(exc) or "Network error") from None

        self._absorb_cookies(response)
        if response.status_code == 401:
            raise ApiError("login required", 401)
        if raw:
            if response.status_code >= 400:
                raise ApiError(f"HTTP {response.status_code}", response.status_code)
            return response.content, response.headers.get("Content-Type", "")

        text = response.text
        try:
            data = response.json() if text.strip() else {}
        except ValueError:
            data = {"error": text[:200] or f"HTTP {response.status_code}"}
        if response.status_code >= 400:
            message = ""
            if isinstance(data, dict):
                message = str(data.get("error") or data.get("message") or "")
            raise ApiError(message or f"HTTP {response.status_code}", response.status_code)
        return data

    @staticmethod
    def cache_key(path: str, params: dict | None) -> str:
        return path + ("?" + urlencode(sorted((params or {}).items())) if params else "")

    def get(self, path: str, params: dict | None = None) -> Any:
        """Read-through cache: use the network when possible, saved body otherwise."""
        key = self.cache_key(path, params)
        try:
            data = self.request("GET", path, params=params)
        except ApiError as exc:
            if not exc.offline or not any(p.match(path) for p in CACHEABLE):
                raise
            hit = self.store.cache_get(self.base_url + "|" + key)
            if hit is None:
                raise
            return hit["data"]
        if any(p.match(path) for p in CACHEABLE):
            self.store.cache_put(self.base_url + "|" + key, data)
        return data

    def write(self, method: str, path: str, body: dict | None = None) -> Any:
        """Queue replay-safe writes when the server cannot be reached."""
        try:
            return self.request(method, path, body=body)
        except ApiError as exc:
            if exc.offline and _replay_rule(method, path) is not None:
                pending = self.store.outbox_add(method, path, body)
                return {"queued": True, "pending": pending}
            raise

    def post(self, path: str, body: dict | None = None) -> Any:
        return self.write("POST", path, body)

    def put(self, path: str, body: dict | None = None) -> Any:
        return self.write("PUT", path, body)

    def patch(self, path: str, body: dict | None = None) -> Any:
        return self.write("PATCH", path, body)

    def delete(self, path: str) -> Any:
        return self.write("DELETE", path)

    def pending_writes(self) -> int:
        return len(self.store.outbox)

    def flush_outbox(self) -> tuple[int, int]:
        """Replay pending writes oldest-first. Returns (sent, still_pending)."""
        if not self._flush_lock.acquire(blocking=False):
            return 0, self.pending_writes()
        try:
            items = self.store.outbox
            sent = 0
            while items:
                item = items[0]
                try:
                    self.request(item["method"], item["path"], body=item.get("body"))
                except ApiError as exc:
                    if exc.status == 401 or exc.offline or exc.status >= 500 or exc.status == 429:
                        break
                    # A permanent 4xx (e.g. already deleted) is done; drop it.
                items = items[1:]
                self.store.outbox_set(items)
                sent += 1
            return sent, len(items)
        finally:
            self._flush_lock.release()

    def get_bytes(self, path: str) -> tuple[bytes, str]:
        return self.request("GET", path, raw=True)

    def download(self, path: str, dest: Path,
                 progress: Optional[Callable[[int, int], None]] = None,
                 cancel: Optional[Callable[[], bool]] = None) -> str:
        """Stream ``path`` to ``dest`` atomically; returns Content-Type."""
        url = self.url(path)
        headers = {"Cookie": self._cookie_header()} if self.cookies else {}
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        try:
            with self._session().get(url, headers=headers, stream=True,
                                     timeout=(12, 120)) as response:
                if response.status_code == 401:
                    raise ApiError("login required", 401)
                if response.status_code >= 400:
                    raise ApiError(f"HTTP {response.status_code}", response.status_code)
                self._absorb_cookies(response)
                total = int(response.headers.get("Content-Length") or 0)
                got = 0
                with open(tmp, "wb") as fh:
                    for chunk in response.iter_content(65536):
                        if cancel and cancel():
                            raise ApiError("cancelled")
                        if not chunk:
                            continue
                        fh.write(chunk)
                        got += len(chunk)
                        if progress:
                            progress(got, total)
                os.replace(tmp, dest)
                return response.headers.get("Content-Type", "")
        except requests.RequestException as exc:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise ApiError(str(exc) or "Download failed") from None
        except Exception:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def normalize(raw: str, fallback: str = DEFAULT_SERVER) -> str:
    value = (raw or "").strip()
    if not value:
        return fallback.rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = "http://" + value
    value = value.rstrip("/")
    if value.endswith("/api"):
        value = value[:-4].rstrip("/")
    return value


# ── repository ──────────────────────────────────────────────────────────────


class Repo:
    """Endpoint map mirroring routes/*.py and the Android Repo class."""

    def __init__(self, api: Api):
        self.api = api

    # auth -----------------------------------------------------------------
    def me(self, force: bool = False) -> Me:
        """Current identity. Session checks must bypass the stale-if-error cache."""
        data = (self.api.request("GET", "me") if force else self.api.get("me"))
        return Me.from_json(data)

    def login(self, username: str, password: str) -> Me:
        return Me.from_json(self.api.post("login", {"username": username, "password": password}))

    def register(self, username: str, password: str, invite: str) -> Me:
        return Me.from_json(self.api.post("register", {
            "username": username, "password": password, "invite": invite,
        }))

    def logout(self) -> None:
        try:
            self.api.post("logout")
        except ApiError:
            pass

    def change_password(self, old: str, new: str) -> None:
        self.api.post("password", {"old": old, "new": new})

    def set_email(self, email: str) -> Me:
        return Me.from_json(self.api.post("auth/email", {"email": email}))

    def request_reset(self, email: str) -> dict:
        return self.api.post("auth/reset/request", {"email": email})

    def check_reset(self, token: str) -> None:
        self.api.post("auth/reset/check", {"token": token})

    def confirm_reset(self, token: str, password: str) -> None:
        self.api.post("auth/reset/confirm", {"token": token, "password": password})

    def verify_token(self, token: str) -> Me:
        """Verify a native device token without adopting it yet."""
        data = self.api.request(
            "GET", "me", timeout=(8, 12),
            headers={"Authorization": f"Bearer {token.strip()}"},
        )
        return Me.from_json(data)

    def adopt_token(self, token: str) -> Me:
        """Persist and start using a native device token, then verify it."""
        self.api.set_token(token)
        try:
            # Never accept a device token on the strength of a cached identity.
            return self.me(force=True)
        except ApiError:
            self.api.clear_token()
            raise

    def app_logout(self) -> None:
        if self.api.token:
            try:
                self.api.post("auth/app/logout")
            except ApiError:
                pass
            self.api.clear_token()

    # Rotur / Discord -------------------------------------------------------
    def rotur_status(self) -> dict:
        return self.api.get("auth/rotur/status")

    def unlink_rotur(self) -> None:
        self.api.post("auth/rotur/unlink")

    def rotur_authorize_url(self, device_hash: str = "") -> str:
        params = {"app": "1"}
        if device_hash:
            params["device_hash"] = device_hash
        return self.api.web_url("api/auth/rotur/authorize?" + urlencode(params))

    def rotur_activity(self, track_id: Optional[int], position: float,
                       playing: bool) -> None:
        self.api.post("auth/rotur/activity", {
            "track_id": track_id, "position": position, "playing": playing,
        })

    def discord_status(self) -> dict:
        return self.api.get("auth/discord/status")

    def discord_authorize_url(self) -> str:
        return self.api.web_url("api/auth/discord/authorize")

    def discord_unlink(self) -> None:
        self.api.post("auth/discord/unlink")

    def discord_activity(self, track_id: Optional[int], position: float,
                         playing: bool) -> None:
        self.api.post("auth/discord/activity", {
            "track_id": track_id, "position": position, "playing": playing,
        })

    # settings -------------------------------------------------------------
    def settings(self) -> Settings:
        return Settings.from_json(self.api.get("settings"))

    def save_settings(self, settings: Settings) -> None:
        self.api.put("settings", settings.to_json())

    # server metadata -------------------------------------------------------
    def ping(self) -> dict:
        return self.api.get("ping")

    def version(self) -> dict:
        return self.api.get("version")

    def builds(self) -> list[BuildInfo]:
        return BuildInfo.list_json(self.api.get("builds").get("builds"))

    def email_build(self, kind: str, email: str) -> dict:
        return self.api.post("builds/email", {"build": kind, "email": email})

    def build_url(self, path: str) -> str:
        return self.api.web_url(path.lstrip("/"))

    # library --------------------------------------------------------------
    def home(self) -> HomeData:
        o = self.api.get("home")
        sections = [
            Section(title=str(s.get("title", "")), tracks=Track.list_json(s.get("tracks")))
            for s in (o.get("sections") or []) if isinstance(s, dict)
        ]
        return HomeData(sections, AlbumRef.list_json(o.get("albums")))

    def tracks(self, query: str = "", limit: int = 2000) -> list[Track]:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["q"] = query
        return Track.list_json(self.api.get("tracks", params).get("tracks"))

    def find_track(self, track_id: int) -> Optional[Track]:
        """Resolve one track from the cached library list (no single-track GET)."""
        return next((t for t in self.tracks() if t.id == int(track_id)), None)

    def search(self, query: str) -> SearchData:
        o = self.api.get("search", {"q": query})
        return SearchData(
            Track.list_json(o.get("tracks")),
            AlbumRef.list_json(o.get("albums")),
            ArtistRef.list_json(o.get("artists")),
        )

    def albums(self) -> list[AlbumRef]:
        return AlbumRef.list_json(self.api.get("albums").get("albums"))

    def album(self, name: str) -> list[Track]:
        return Track.list_json(self.api.get("album", {"name": name}).get("tracks"))

    def artists(self) -> list[ArtistRef]:
        return ArtistRef.list_json(self.api.get("artists").get("artists"))

    def artist(self, name: str) -> list[Track]:
        return Track.list_json(self.api.get("artist", {"name": name}).get("tracks"))

    def lyrics(self, track_id: int) -> dict:
        """Lyrics for one track; the server looks them up on first listen."""
        return self.api.get(f"tracks/{int(track_id)}/lyrics")

    def track_sources(self, track_id: int) -> list[dict]:
        data = self.api.get(f"tracks/{int(track_id)}/sources")
        return [r for r in (data.get("sources") or []) if isinstance(r, dict)]

    def likes(self) -> list[Track]:
        return Track.list_json(self.api.get("likes").get("tracks"))

    def like(self, track_id: int):
        """Returns the new liked state, or a queued marker when offline."""
        data = self.api.post(f"like/{track_id}")
        if isinstance(data, dict) and data.get("queued"):
            return data
        return bool(data.get("liked"))

    def report_play(self, track_id: int, completed: bool) -> None:
        self.api.post("plays", {
            "track_id": track_id, "completed": completed, "client": "desktop",
        })

    def report_metric(
        self, track_id: int, event: str, position: float = 0.0, duration: float = 0.0,
    ) -> None:
        """Always-on listening events: admin insight and Faves ranking."""
        if event not in {"play", "skip", "complete", "seek"}:
            return
        self.api.post("metrics", {"events": [{
            "track_id": track_id, "event": event,
            "position": float(position), "duration": float(duration),
            "client": "desktop",
        }]})

    def set_explicit(self, track_id: int, explicit: bool) -> bool:
        return bool(self.api.patch(f"tracks/{track_id}", {"explicit": explicit}).get("explicit"))

    def radio(self, track_id: int) -> list[Track]:
        return Track.list_json(self.api.get(f"radio/{track_id}").get("tracks"))

    def model_rank(self, current: int, ids: list[int]) -> list[int]:
        """MDL queue order, empty until the 76% work-rate gate opens."""
        data = self.api.post("model/rank", {
            "current": int(current),
            "ids": [int(i) for i in ids][:500],
        })
        if not data.get("active"):
            return []
        return [int(i) for i in (data.get("ids") or [])]

    # playlists ------------------------------------------------------------
    def playlists(self) -> list[PlaylistRef]:
        return PlaylistRef.list_json(self.api.get("playlists").get("playlists"))

    def playlist(self, playlist_id: int) -> tuple[str, list[Track]]:
        o = self.api.get(f"playlists/{playlist_id}")
        return str(o.get("name") or "Playlist"), Track.list_json(o.get("tracks"))

    def create_playlist(self, name: str) -> int:
        return int(self.api.post("playlists", {"name": name}).get("id") or 0)

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        self.api.patch(f"playlists/{playlist_id}", {"name": name})

    def delete_playlist(self, playlist_id: int) -> None:
        self.api.delete(f"playlists/{playlist_id}")

    def add_to_playlist(self, playlist_id: int, track_id: int) -> None:
        self.api.post(f"playlists/{playlist_id}/tracks", {"track_id": track_id})

    def remove_from_playlist(self, playlist_id: int, track_id: int) -> None:
        self.api.delete(f"playlists/{playlist_id}/tracks/{track_id}")

    # requests -------------------------------------------------------------
    def requests(self) -> tuple[bool, list[RequestRow]]:
        o = self.api.get("requests")
        rows = [RequestRow.from_json(r) for r in (o.get("requests") or []) if isinstance(r, dict)]
        return bool(o.get("is_admin")), rows

    def request_add(self, url: str) -> str:
        return str(self.api.post("requests", {"url": url}).get("status") or "")

    def request_act(self, request_id: int, action: str) -> None:
        self.api.post(f"requests/{request_id}/{action}")

    # admin ----------------------------------------------------------------
    def admin_stats(self) -> AdminStats:
        return AdminStats.from_json(self.api.get("admin/stats"))

    def admin_users(self) -> list[AdminUser]:
        return [AdminUser.from_json(u) for u in (self.api.get("admin/users").get("users") or [])]

    def admin_set_admin(self, user_id: int, is_admin: bool) -> None:
        self.api.post(f"admin/users/{user_id}/admin", {"is_admin": is_admin})

    def admin_scan(self) -> tuple[int, int]:
        o = self.api.post("admin/scan")
        return int(o.get("tracks") or 0), int(o.get("albums") or 0)

    # public listening ------------------------------------------------------
    def public_listening(self) -> tuple[list[ListeningUser], str]:
        data = self.api.get("public/listening")
        return ListeningUser.list_json(data.get("users")), str(data.get("base_url") or "")

    def public_now(self, username: str) -> dict:
        return self.api.get(f"public/now/{username}")

    # rooms -----------------------------------------------------------------
    def room_create(self) -> str:
        return str(self.api.post("rooms").get("code") or "")

    def room_state(self, code: str, track_id: int | None, pos: float,
                   playing: bool) -> None:
        self.api.post(f"rooms/{code}/state", {
            "track_id": track_id, "pos": pos, "playing": playing,
        })

    def room_get(self, code: str) -> dict:
        return self.api.get(f"rooms/{code}")

    def room_close(self, code: str) -> None:
        self.api.delete(f"rooms/{code}")

    # devices / playback registry ------------------------------------------
    def heartbeat(self, device_hash: str, name: str, track_id: int | None,
                  position: float, paused: bool) -> None:
        self.api.post("devices/heartbeat", {
            "device_hash": device_hash, "name": name, "track_id": track_id,
            "position": position, "paused": paused,
        })

    def devices(self) -> list[DeviceRow]:
        return DeviceRow.list_json(self.api.get("devices").get("devices"))

    def device_activate(self, device_id: int) -> None:
        self.api.post(f"devices/{int(device_id)}/activate")

    def device_rename(self, device_id: int, name: str) -> None:
        self.api.patch(f"devices/{int(device_id)}", {"name": name})

    def device_forget(self, device_id: int) -> None:
        self.api.delete(f"devices/{int(device_id)}")

    def devices_cleanup(self) -> None:
        self.api.post("devices/cleanup")

    def devices_clear(self) -> None:
        self.api.post("devices/clear")

    def devices_sync(self) -> dict:
        return self.api.get("devices/sync")

    def device_code(self) -> dict:
        return self.api.post("devices/code")

    def device_claim(self, code: str, name: str = "") -> dict:
        return self.api.post("devices/claim", {
            "code": code, "name": name, "device_hash": self.api.store.device_hash,
        })

    def device_tokens(self) -> list[dict]:
        data = self.api.get("devices/tokens")
        return [t for t in (data.get("tokens") or []) if isinstance(t, dict)]

    def device_token_revoke(self, token_id: int) -> None:
        self.api.post(f"devices/tokens/{int(token_id)}/revoke")

    def admin_devices(self) -> list[DeviceRow]:
        return DeviceRow.list_json(self.api.get("admin/devices").get("devices"))

    def publish_playback(self, track_id: int | None, position: float, duration: float,
                         playing: bool, queue: list[int], device: str = "") -> None:
        self.api.post("playback", {
            "track_id": track_id, "position": position, "duration": duration,
            "playing": playing, "queue": queue, "device": device or self.api.store.device_hash,
        })

    def playback(self, device: str = "") -> dict:
        return self.api.get("playback", {"device": device or self.api.store.device_hash})

    def playback_command(self, action: str, **arg) -> None:
        self.api.post("playback/command", {"action": action, **arg})

    def queue_snapshot(self) -> dict:
        return self.api.get("queue")

    # advanced request / admin ---------------------------------------------
    def admin_requests(self, limit: int = 200) -> list[RequestRow]:
        data = self.api.get("admin/requests", {"limit": limit})
        return [RequestRow.from_json(r) for r in (data.get("requests") or [])]

    def request_log(self, request_id: int) -> dict:
        return self.api.get(f"admin/requests/{int(request_id)}/log")

    def request_cancel(self, request_id: int) -> None:
        self.api.post(f"admin/requests/{int(request_id)}/cancel")

    def request_retry(self, request_id: int) -> None:
        self.api.post(f"admin/requests/{int(request_id)}/retry")

    def request_delete(self, request_id: int) -> None:
        self.api.delete(f"admin/requests/{int(request_id)}")

    def admin_delete_user(self, user_id: int) -> None:
        self.api.delete(f"admin/users/{int(user_id)}")

    def admin_invites(self) -> list[dict]:
        data = self.api.get("admin/invite-codes")
        return [r for r in (data.get("codes") or []) if isinstance(r, dict)]

    def admin_invite_create(self, uses: int = 1, hours: float = 0, note: str = "") -> dict:
        return self.api.post("admin/invite-codes", {
            "uses": uses, "hours": hours, "note": note,
        })

    def admin_invite_revoke(self, code_id: int) -> None:
        self.api.delete(f"admin/invite-codes/{int(code_id)}")

    def admin_rooms(self) -> list[dict]:
        data = self.api.get("admin/rooms")
        return [r for r in (data.get("rooms") or []) if isinstance(r, dict)]

    def admin_room_close(self, code: str) -> None:
        self.api.delete(f"admin/rooms/{code}")

    def admin_enrich_status(self) -> dict:
        return self.api.get("admin/enrich")

    def admin_enrich_start(self, force: bool = False) -> None:
        self.api.post("admin/enrich", {"force": force})

    def admin_lyrics_status(self) -> dict:
        return self.api.get("admin/lyrics")

    def admin_lyrics_start(self) -> None:
        self.api.post("admin/lyrics", {})

    def admin_channels(self) -> list[dict]:
        data = self.api.get("channels")
        return [r for r in (data.get("channels") or []) if isinstance(r, dict)]


def device_name() -> str:
    system = platform.system()
    try:
        host = platform.node() or system
    except Exception:
        host = system
    label = "macOS" if system == "Darwin" else (
        "Windows" if system == "Windows" else "Linux")
    return f"{host} · {label}"


def query(params: dict[str, Any]) -> str:
    return "?" + urlencode(params)
