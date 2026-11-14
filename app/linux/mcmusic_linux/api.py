"""HTTP + session layer for the mcmusic server.

The server authenticates with the signed ``mcmusic_session`` cookie, exactly
like the browser and Android clients. Requests run off the GUI thread through a
small thread pool; results are delivered back on the Qt main thread.
"""
from __future__ import annotations

import json
import os
import platform
import threading
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
    HomeData,
    Me,
    PlaylistRef,
    RequestRow,
    SearchData,
    Section,
    Settings,
    Track,
)

VERSION = "1.0.0"
DEFAULT_SERVER = "http://127.0.0.1:8000"


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


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
            self._s.setValue("me", json.dumps({
                "id": me.id, "username": me.username, "is_admin": me.is_admin,
                "rotur_id": me.rotur_id, "rotur_linked": me.rotur_linked,
            }))
        self._s.sync()

    # appearance -----------------------------------------------------------
    @property
    def theme(self) -> str:
        return str(self._s.value("theme", "dusk") or "dusk")

    @theme.setter
    def theme(self, value: str) -> None:
        self._s.setValue("theme", value)

    @property
    def accent(self) -> str:
        return str(self._s.value("accent", "#d98a3d") or "#d98a3d")

    @accent.setter
    def accent(self, value: str) -> None:
        self._s.setValue("accent", value)

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
        value = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:32]
        self._s.setValue("device_hash", value)
        return value

    def sync(self) -> None:
        self._s.sync()


# ── HTTP client ─────────────────────────────────────────────────────────────


class Api:
    def __init__(self, store: SessionStore):
        self.store = store
        self.cookies: dict[str, str] = store.load_cookies()
        self._local = threading.local()
        self.base_url = normalize(store.base_url)

    # transport ------------------------------------------------------------
    def _session(self) -> requests.Session:
        s = getattr(self._local, "session", None)
        if s is None:
            s = requests.Session()
            s.headers.update({
                "User-Agent": f"mcmusic-desktop/{VERSION} (Linux; Qt)",
                "Accept": "application/json",
            })
            self._local.session = s
        return s

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
                raw: bool = False) -> Any:
        url = self.url(path)
        headers = {}
        if self.cookies:
            headers["Cookie"] = self._cookie_header()
        try:
            response = self._session().request(
                method, url, json=body, params=params, headers=headers,
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

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, body: dict | None = None) -> Any:
        return self.request("POST", path, body=body)

    def put(self, path: str, body: dict | None = None) -> Any:
        return self.request("PUT", path, body=body)

    def patch(self, path: str, body: dict | None = None) -> Any:
        return self.request("PATCH", path, body=body)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

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
    def me(self) -> Me:
        return Me.from_json(self.api.get("me"))

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

    def rotur_status(self) -> dict:
        return self.api.get("auth/rotur/status")

    def unlink_rotur(self) -> None:
        self.api.post("auth/rotur/unlink")

    # settings -------------------------------------------------------------
    def settings(self) -> Settings:
        return Settings.from_json(self.api.get("settings"))

    def save_settings(self, settings: Settings) -> None:
        self.api.put("settings", settings.to_json())

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

    def likes(self) -> list[Track]:
        return Track.list_json(self.api.get("likes").get("tracks"))

    def like(self, track_id: int) -> bool:
        return bool(self.api.post(f"like/{track_id}").get("liked"))

    def report_play(self, track_id: int, completed: bool) -> None:
        self.api.post("plays", {"track_id": track_id, "completed": completed})

    def set_explicit(self, track_id: int, explicit: bool) -> bool:
        return bool(self.api.patch(f"tracks/{track_id}", {"explicit": explicit}).get("explicit"))

    def radio(self, track_id: int) -> list[Track]:
        return Track.list_json(self.api.get(f"radio/{track_id}").get("tracks"))

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

    # devices / playback registry ------------------------------------------
    def heartbeat(self, device_hash: str, name: str, track_id: int | None,
                  position: float, paused: bool) -> None:
        self.api.post("devices/heartbeat", {
            "device_hash": device_hash, "name": name, "track_id": track_id,
            "position": position, "paused": paused,
        })

    def publish_playback(self, track_id: int | None, position: float, duration: float,
                         playing: bool, queue: list[int]) -> None:
        self.api.post("playback", {
            "track_id": track_id, "position": position, "duration": duration,
            "playing": playing, "queue": queue,
        })


def device_name() -> str:
    try:
        host = platform.node() or "Linux"
    except Exception:
        host = "Linux"
    return f"{host} · Linux"


def query(params: dict[str, Any]) -> str:
    return "?" + urlencode(params)
