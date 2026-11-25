"""Terminal client for mcmusic — ``mcmusic-desktop --tui``.

Standard library only. The TUI deliberately does not import PySide6 or the
Qt-side ``api``/``player`` modules, so it starts on a headless box with nothing
installed beyond Python 3.10. It speaks the same ``/api`` contract, reuses the
shared payload models in ``.models``, and keeps its own session/config file so
it can never corrupt the Qt client's QSettings.

Audio is played by an external process: mpv when available (full transport via
its IPC socket), otherwise ffplay (play/pause-free playback). Without either,
everything except audio output still works.
"""
from __future__ import annotations

import curses
import json
import os
import queue as queue_mod
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from .models import (
    AdminStats,
    AdminUser,
    AlbumRef,
    ArtistRef,
    HomeData,
    PlaylistRef,
    RequestRow,
    Section,
    Track,
    fmt_bytes,
    fmt_time,
    fmt_uptime,
)

VERSION = "1.0.0"
DEFAULT_SERVER = "http://127.0.0.1:8000"

AUDIO_EXT = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "audio/x-flac": ".flac",
    "audio/ogg": ".ogg",
    "audio/opus": ".opus",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
}

VIEWS: list[tuple[str, str]] = [
    ("home", "Home"),
    ("library", "Library"),
    ("albums", "Albums"),
    ("artists", "Artists"),
    ("liked", "Liked"),
    ("playlists", "Playlists"),
    ("queue", "Queue"),
]

HINTS = ("1-9 views · / search · Enter play · space pause · n/p skip · "
         "l like · A add to playlist · N new · ? help · q quit")


# ── local state ─────────────────────────────────────────────────────────────


def config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "mcmusic" / "tui.json"


def cache_path() -> Path:
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    path = root / "mcmusic" / "tui-audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def gui_base_url() -> str:
    """Best-effort read of the Qt client's saved server, so both agree."""
    conf = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "mcmusic" / "mcmusic-desktop.conf"
    try:
        text = conf.read_text("utf-8", "replace")
    except OSError:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("base_url="):
            return normalize(line.split("=", 1)[1].strip().strip('"'))
    return ""


class Config:
    def __init__(self) -> None:
        self.path = config_path()
        self.base_url = DEFAULT_SERVER
        self.cookies: dict[str, str] = {}
        self.volume = 70
        self.username = ""
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text("utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        saved = str(data.get("base_url") or "").strip()
        self.base_url = normalize(saved or gui_base_url() or DEFAULT_SERVER)
        cookies = data.get("cookies")
        if isinstance(cookies, dict):
            self.cookies = {str(k): str(v) for k, v in cookies.items() if v}
        try:
            self.volume = max(0, min(100, int(data.get("volume", self.volume))))
        except (TypeError, ValueError):
            pass
        self.username = str(data.get("username") or "")

    def save(self) -> None:
        payload = {
            "base_url": self.base_url,
            "cookies": self.cookies,
            "volume": self.volume,
            "username": self.username,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2) + "\n", "utf-8")
            tmp.chmod(0o600)
            os.replace(tmp, self.path)
        except OSError:
            pass


# ── API ─────────────────────────────────────────────────────────────────────


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class Client:
    """The subset of ``/api`` the terminal client needs."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.base = normalize(cfg.base_url)
        self.cookies = dict(cfg.cookies)

    # transport ------------------------------------------------------------
    def set_base(self, raw: str) -> str:
        self.base = normalize(raw, self.base)
        self.cfg.base_url = self.base
        return self.base

    def _headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": f"mcmusic-tui/{VERSION}",
        }
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if extra:
            headers.update(extra)
        return headers

    def _absorb(self, headers: Any) -> None:
        changed = False
        for raw in list(headers or []):
            pair = raw.split(";", 1)[0]
            if "=" not in pair:
                continue
            name, value = pair.split("=", 1)
            name, value = name.strip(), value.strip()
            if not name:
                continue
            if value:
                if self.cookies.get(name) != value:
                    self.cookies[name] = value
                    changed = True
            elif name in self.cookies:
                self.cookies.pop(name, None)
                changed = True
        if changed:
            self.cfg.cookies = dict(self.cookies)
            self.cfg.save()

    def call(self, method: str, path: str, body: dict | None = None,
             params: dict | None = None, timeout: float = 25) -> Any:
        url = f"{self.base}/api/{path.lstrip('/')}"
        if params:
            qs = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v not in (None, "")}
            )
            if qs:
                url += "?" + qs
        data = json.dumps(body).encode("utf-8") if body is not None else None
        extra = {"Content-Type": "application/json"} if data is not None else None
        req = urllib.request.Request(
            url, data=data, headers=self._headers(extra), method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                raw = res.read()
                self._absorb(res.headers.get_all("Set-Cookie"))
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            # Read the headers before closing: a rejected response is a full
            # HTTPError object, and leaving it open leaks the socket.
            self._absorb(exc.headers.get_all("Set-Cookie") if exc.headers else None)
            exc.close()
            message = ""
            try:
                payload = json.loads(raw.decode("utf-8", "replace") or "{}")
                if isinstance(payload, dict):
                    message = str(payload.get("error") or payload.get("message") or "")
            except ValueError:
                message = raw.decode("utf-8", "replace")[:120]
            if exc.code == 401:
                raise ApiError("login required", 401) from None
            raise ApiError(message or f"HTTP {exc.code}", exc.code) from None
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                raise ApiError("Server timed out") from None
            raise ApiError(f"Can't reach {self.base}") from None
        except (TimeoutError, socket.timeout):
            raise ApiError("Server timed out") from None
        except OSError:
            raise ApiError(f"Can't reach {self.base}") from None

        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except ValueError:
            raise ApiError("Server sent an invalid response") from None

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.call("GET", path, params=params)

    def post(self, path: str, body: dict | None = None) -> Any:
        return self.call("POST", path, body=body)

    # auth -----------------------------------------------------------------
    def me(self):
        from .models import Me
        return Me.from_json(self.get("me"))

    def login(self, username: str, password: str):
        from .models import Me
        return Me.from_json(self.post("login", {"username": username, "password": password}))

    def register(self, username: str, password: str, invite: str):
        from .models import Me
        return Me.from_json(self.post("register", {
            "username": username, "password": password, "invite": invite,
        }))

    def logout(self) -> None:
        try:
            self.post("logout")
        except ApiError:
            pass

    # library --------------------------------------------------------------
    def home(self) -> HomeData:
        o = self.get("home")
        sections = [
            Section(title=str(s.get("title") or ""), tracks=Track.list_json(s.get("tracks")))
            for s in (o.get("sections") or []) if isinstance(s, dict)
        ]
        return HomeData(sections, AlbumRef.list_json(o.get("albums")))

    def tracks(self, limit: int = 2000) -> list[Track]:
        return Track.list_json(self.get("tracks", {"limit": limit}).get("tracks"))

    def search(self, query: str):
        from .models import SearchData
        o = self.get("search", {"q": query})
        return SearchData(
            Track.list_json(o.get("tracks")),
            AlbumRef.list_json(o.get("albums")),
            ArtistRef.list_json(o.get("artists")),
        )

    def albums(self) -> list[AlbumRef]:
        return AlbumRef.list_json(self.get("albums").get("albums"))

    def album(self, name: str) -> list[Track]:
        return Track.list_json(self.get("album", {"name": name}).get("tracks"))

    def artists(self) -> list[ArtistRef]:
        return ArtistRef.list_json(self.get("artists").get("artists"))

    def artist(self, name: str) -> list[Track]:
        return Track.list_json(self.get("artist", {"name": name}).get("tracks"))

    def likes(self) -> list[Track]:
        return Track.list_json(self.get("likes").get("tracks"))

    def like(self, track_id: int) -> bool:
        return bool(self.post(f"like/{track_id}").get("liked"))

    def radio(self, track_id: int) -> list[Track]:
        return Track.list_json(self.get(f"radio/{track_id}").get("tracks"))

    def playlists(self) -> list[PlaylistRef]:
        return PlaylistRef.list_json(self.get("playlists").get("playlists"))

    def playlist(self, playlist_id: int) -> tuple[str, list[Track]]:
        o = self.get(f"playlists/{playlist_id}")
        return str(o.get("name") or "Playlist"), Track.list_json(o.get("tracks"))

    def create_playlist(self, name: str) -> int:
        return int(self.post("playlists", {"name": name}).get("id") or 0)

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        self.call("PATCH", f"playlists/{playlist_id}", {"name": name})

    def delete_playlist(self, playlist_id: int) -> None:
        self.call("DELETE", f"playlists/{playlist_id}")

    def add_to_playlist(self, playlist_id: int, track_id: int) -> None:
        self.post(f"playlists/{playlist_id}/tracks", {"track_id": track_id})

    def remove_from_playlist(self, playlist_id: int, track_id: int) -> None:
        self.call("DELETE", f"playlists/{playlist_id}/tracks/{track_id}")

    # requests -------------------------------------------------------------
    def requests(self) -> tuple[bool, list[RequestRow]]:
        o = self.get("requests")
        rows = [RequestRow.from_json(r) for r in (o.get("requests") or []) if isinstance(r, dict)]
        return bool(o.get("is_admin")), rows

    def request_add(self, url: str) -> str:
        return str(self.post("requests", {"url": url}).get("status") or "")

    def request_act(self, request_id: int, action: str) -> None:
        self.post(f"requests/{request_id}/{action}")

    # admin ----------------------------------------------------------------
    def admin_stats(self) -> AdminStats:
        return AdminStats.from_json(self.get("admin/stats"))

    def admin_users(self) -> list[AdminUser]:
        return [AdminUser.from_json(u) for u in (self.get("admin/users").get("users") or [])]

    def admin_set_admin(self, user_id: int, is_admin: bool) -> None:
        self.post(f"admin/users/{user_id}/admin", {"is_admin": is_admin})

    def admin_scan(self) -> tuple[int, int]:
        o = self.post("admin/scan")
        return int(o.get("tracks") or 0), int(o.get("albums") or 0)

    # playback registry ----------------------------------------------------
    def publish_playback(self, track_id: Optional[int], position: float,
                         duration: float, playing: bool,
                         queue: list[int]) -> None:
        self.post("playback", {
            "track_id": track_id, "position": position, "duration": duration,
            "playing": playing, "queue": list(queue)[:200],
        })

    # audio ----------------------------------------------------------------
    def download_stream(self, track_id: int, folder: Path) -> Path:
        url = f"{self.base}/api/tracks/{track_id}/stream"
        req = urllib.request.Request(
            url, headers=self._headers({"Accept": "audio/*"}), method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                self._absorb(res.headers.get_all("Set-Cookie"))
                ctype = (res.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                ext = AUDIO_EXT.get(ctype, ".mp3")
                folder.mkdir(parents=True, exist_ok=True)
                dest = folder / f"{track_id}{ext}"
                tmp = dest.with_name(dest.name + ".part")
                try:
                    with open(tmp, "wb") as fh:
                        while True:
                            chunk = res.read(65536)
                            if not chunk:
                                break
                            fh.write(chunk)
                    os.replace(tmp, dest)
                except OSError:
                    tmp.unlink(missing_ok=True)
                    raise
                return dest
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise ApiError("login required", 401) from None
            raise ApiError(f"HTTP {exc.code}", exc.code) from None
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                raise ApiError("Download timed out") from None
            raise ApiError("Download failed") from None
        except (TimeoutError, socket.timeout):
            raise ApiError("Download timed out") from None
        except OSError:
            raise ApiError("Download failed") from None


def prune_cache(limit: int = 300) -> None:
    """Keep the terminal audio cache bounded; artwork lives elsewhere."""
    folder = cache_path()
    try:
        files = [p for p in folder.iterdir() if p.is_file()]
    except OSError:
        return
    if len(files) <= limit:
        return
    files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0)
    for old in files[: len(files) - limit]:
        try:
            old.unlink()
        except OSError:
            pass


# ── audio process ───────────────────────────────────────────────────────────


class Player:
    """mpv (full transport) or ffplay (playback only), driven out of process."""

    def __init__(self, volume: int = 70):
        self.volume = max(0, min(100, int(volume)))
        self.proc: Optional[subprocess.Popen] = None
        self.track: Optional[Track] = None
        self.paused = False
        self.backend = "mpv" if shutil.which("mpv") else (
            "ffplay" if shutil.which("ffplay") else None
        )
        self._sock: Optional[str] = None
        self._dir: Optional[tempfile.TemporaryDirectory] = None

    @property
    def available(self) -> bool:
        return self.backend is not None

    @property
    def can_pause(self) -> bool:
        return self.backend == "mpv"

    @property
    def alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def finished(self) -> bool:
        return self.proc is not None and self.proc.poll() is not None

    def play(self, path: Path, track: Track) -> None:
        self.stop()
        if not self.backend:
            return
        if self.backend == "mpv":
            self._dir = tempfile.TemporaryDirectory(prefix="mcmusic-tui-")
            self._sock = os.path.join(self._dir.name, "mpv.sock")
            argv = [
                "mpv", "--no-video", "--no-terminal", "--really-quiet",
                "--force-window=no", "--idle=no", f"--volume={self.volume}",
                f"--input-ipc-server={self._sock}", str(path),
            ]
        else:
            argv = [
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "error",
                "-volume", str(self.volume), str(path),
            ]
        try:
            self.proc = subprocess.Popen(
                argv, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            self.proc = None
            return
        self.track = track
        self.paused = False

    def _ipc(self, command: list[Any]) -> Any:
        if not self._sock:
            return None
        payload = json.dumps({"command": command}).encode("utf-8") + b"\n"
        for _ in range(12):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.6)
                    sock.connect(self._sock)
                    sock.sendall(payload)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = sock.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    return json.loads(data.decode("utf-8", "replace") or "{}").get("data")
            except (OSError, ValueError):
                time.sleep(0.05)
        return None

    def toggle_pause(self) -> Optional[bool]:
        if not self.can_pause or not self.alive:
            return None
        state = self._ipc(["get_property", "pause"])
        target = (not bool(state)) if isinstance(state, bool) else (not self.paused)
        self._ipc(["set_property", "pause", target])
        self.paused = target
        return self.paused

    def set_volume(self, value: int) -> None:
        self.volume = max(0, min(100, int(value)))
        if self.can_pause and self.alive:
            self._ipc(["set_property", "volume", self.volume])

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=1.5)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self.proc.kill()
                except OSError:
                    pass
        self.proc = None
        self.track = None
        self.paused = False
        if self._dir is not None:
            self._dir.cleanup()
            self._dir = None
            self._sock = None


# ── rows ────────────────────────────────────────────────────────────────────


@dataclass
class Row:
    # heading | track | album | artist | playlist | request | admin-stat | admin-user | empty
    kind: str
    label: str
    sub: str = ""
    track: Optional[Track] = None
    album: Optional[str] = None
    artist: Optional[str] = None
    playlist_id: int = 0
    liked: bool = False
    request: Optional[RequestRow] = None
    user: Optional[AdminUser] = None


def track_row(track: Track) -> Row:
    sub = track.artist
    if track.duration:
        sub = f"{sub} · {fmt_time(track.duration)}"
    return Row("track", track.title, sub, track=track, liked=track.liked)


def fetch(client: Client, view: str, arg: Any = None) -> tuple[str, list[Row]]:
    """Load one view. Pure network + shaping, so it is testable without curses."""
    if view == "home":
        data = client.home()
        rows: list[Row] = []
        for section in data.sections:
            if not section.tracks:
                continue
            rows.append(Row("heading", section.title))
            rows.extend(track_row(t) for t in section.tracks)
        if data.albums:
            rows.append(Row("heading", "Albums"))
            rows.extend(
                Row("album", a.album, a.artist or "Album", album=a.album)
                for a in data.albums
            )
        return "Home", rows or [Row("empty", "Nothing here yet")]

    if view == "library":
        return "Library", [track_row(t) for t in client.tracks()]

    if view == "albums":
        return "Albums", [
            Row("album", a.album, f"{a.artist or 'Unknown Artist'} · {a.n} tracks", album=a.album)
            for a in client.albums()
        ]

    if view == "artists":
        return "Artists", [
            Row("artist", a.artist, f"{a.n} tracks · {a.albums} albums", artist=a.artist)
            for a in client.artists()
        ]

    if view == "liked":
        return "Liked", [track_row(t) for t in client.likes()]

    if view == "playlists":
        return "Playlists", [
            Row("playlist", p.name, f"{p.n} tracks", playlist_id=p.id)
            for p in client.playlists()
        ]

    if view == "search":
        query = str(arg or "")
        data = client.search(query)
        rows = [track_row(t) for t in data.tracks]
        if data.albums:
            rows.append(Row("heading", "Albums"))
            rows.extend(Row("album", a.album, a.artist, album=a.album) for a in data.albums)
        if data.artists:
            rows.append(Row("heading", "Artists"))
            rows.extend(
                Row("artist", a.artist, f"{a.n} tracks", artist=a.artist)
                for a in data.artists
            )
        return f"Search · {query}", rows or [Row("empty", "No matches")]

    if view == "album":
        tracks = client.album(str(arg))
        return str(arg), [track_row(t) for t in tracks] or [Row("empty", "No songs here yet")]

    if view == "artist":
        tracks = client.artist(str(arg))
        return str(arg), [track_row(t) for t in tracks] or [Row("empty", "No songs here yet")]

    if view == "playlist":
        name, tracks = client.playlist(int(arg))
        return name, [track_row(t) for t in tracks] or [Row("empty", "No songs in this playlist yet")]

    raise ApiError("unknown view")


def fetch_requests(client: Client) -> tuple[str, list[Row], bool]:
    is_admin, requests = client.requests()
    rows: list[Row] = []
    for row in requests:
        who = f"{row.username} · " if row.username else ""
        rows.append(Row("request", row.url, f"{who}{row.status}", request=row))
    if not rows:
        rows = [Row("empty", "No requests yet — N adds one")]
    return ("Requests", rows, is_admin)


def fetch_admin(client: Client) -> tuple[str, list[Row]]:
    stats = client.admin_stats()
    users = client.admin_users()
    rows = [
        Row("admin-stat", "Library",
            f"{stats.tracks} tracks · {stats.albums} albums · {stats.playlists} playlists"),
        Row("admin-stat", "Users", f"{stats.users} users · {stats.admins} admins"),
        Row("admin-stat", "Plays", str(stats.plays)),
        Row("admin-stat", "Storage",
            f"{fmt_bytes(stats.music_bytes)} music · {fmt_bytes(stats.disk_free)} free"),
        Row("admin-stat", "Uptime", fmt_uptime(stats.uptime)),
        Row("heading", "Users"),
    ]
    for user in users:
        role = "admin" if user.is_admin else "member"
        rows.append(Row("admin-user", user.username,
                        f"{role} · {user.plays} plays · {user.likes} likes", user=user))
    return "Admin", rows


# ── application ─────────────────────────────────────────────────────────────


class App:
    def __init__(self, screen: "curses.window", cfg: Config):
        self.scr = screen
        self.cfg = cfg
        self.client = Client(cfg)
        self.player = Player(cfg.volume)

        self.mode = "browse"          # browse | login | connecting
        self.view = "home"
        self.arg: Any = None
        self.title = "Home"
        self.rows: list[Row] = []
        self.history: list[tuple[str, Any, str]] = []
        self.cursor = 0
        self.offset = 0
        self.loading = False
        self.status = ""
        self.err = ""
        self.help = False
        self.quit = False

        self.username = cfg.username
        self.queue: list[Track] = []
        self.qindex = -1

        self.login = {
            "server": cfg.base_url,
            "username": cfg.username,
            "password": "",
            "invite": "",
        }
        self.login_index = 0
        self.register = False
        self.prompt: Optional[str] = None
        self.prompt_label = "/"
        self.prompt_done: Optional[Callable[[str], None]] = None
        self.is_admin = False
        self.requests_admin = False
        self.picker: Optional[list[PlaylistRef]] = None
        self.picker_index = 0
        self.pending_track: Optional[Track] = None

        self.q: "queue_mod.Queue[tuple]" = queue_mod.Queue()

    # ── async plumbing ───────────────────────────────────────────────────
    def submit(self, fn: Callable[[], Any], done: Callable[[Any], None],
               label: str = "") -> None:
        if label:
            self.status = label
        self.loading = True

        def work() -> None:
            try:
                value = fn()
            except ApiError as exc:
                self.q.put(("error", str(exc), exc.status))
            except Exception as exc:  # noqa: BLE001 - surfaced in the status bar
                self.q.put(("error", str(exc), 0))
            else:
                self.q.put(("ok", done, value))

        threading.Thread(target=work, daemon=True).start()

    def drain(self) -> None:
        while True:
            try:
                kind, first, second = self.q.get_nowait()
            except queue_mod.Empty:
                return
            if kind == "ok":
                self.loading = False
                try:
                    first(second)
                except Exception as exc:  # noqa: BLE001
                    self.on_error(str(exc), 0)
            else:
                self.loading = False
                self.on_error(str(first), int(second or 0))

    def on_error(self, message: str, status: int) -> None:
        self.err = message
        if self.mode == "connecting":
            self.mode = "login"
        if status == 401:
            self.client.cookies.clear()
            self.cfg.cookies = {}
            self.cfg.save()
            self.mode = "login"
            self.err = "Session expired — sign in again"
            self.register = False
            self.login_index = 0
        if self.mode != "login":
            self.status = message

    # ── views ────────────────────────────────────────────────────────────
    def views(self) -> list[tuple[str, str]]:
        out = list(VIEWS)
        out.append(("requests", "Requests"))
        if self.is_admin:
            out.append(("admin", "Admin"))
        return out

    def load(self, view: str, arg: Any = None, push: bool = False) -> None:
        if push:
            self.history.append((self.view, self.arg, self.title))
        self.view = view
        self.arg = arg
        self.cursor = 0
        self.offset = 0
        self.err = ""

        if view == "queue":
            self.title = "Queue"
            self.rows = [track_row(t) for t in self.queue] or [Row("empty", "Queue is empty")]
            return

        if view == "requests":
            self.submit(lambda: fetch_requests(self.client), self.show_requests, "Loading…")
            return

        if view == "admin":
            self.submit(lambda: fetch_admin(self.client), self.show_admin, "Loading…")
            return

        self.submit(
            lambda: fetch(self.client, view, arg),
            lambda result: self.show_rows(*result),
            "Loading…",
        )

    def show_rows(self, title: str, rows: list[Row]) -> None:
        self.title = title
        self.rows = rows
        self.status = ""

    def show_requests(self, result: tuple[str, list[Row], bool]) -> None:
        title, rows, is_admin = result
        self.requests_admin = is_admin
        self.show_rows(title, rows)

    def show_admin(self, result: tuple[str, list[Row]]) -> None:
        self.show_rows(*result)

    def back(self) -> None:
        if self.history:
            view, arg, title = self.history.pop()
            self.load(view, arg)
            self.title = title
            return
        if self.view not in ("home", "queue"):
            self.load("home")
            self.history.clear()

    # ── playback ─────────────────────────────────────────────────────────
    def play_list(self, tracks: list[Track], index: int) -> None:
        if not tracks:
            return
        self.queue = list(tracks)
        self.qindex = max(0, min(len(tracks) - 1, index))
        self.play_current()

    def play_current(self) -> None:
        if not (0 <= self.qindex < len(self.queue)):
            return
        track = self.queue[self.qindex]
        if not self.player.available:
            self.status = "Install mpv (full controls) or ffplay to hear audio"
            return
        self.status = f"Buffering {track.title}…"
        self.submit(
            lambda: self.audio_file(track),
            lambda path: self.start_audio(track, path),
        )

    def audio_file(self, track: Track) -> Path:
        folder = cache_path()
        for ext in dict.fromkeys(AUDIO_EXT.values()):
            cached = folder / f"{track.id}{ext}"
            if cached.exists() and cached.stat().st_size > 0:
                return cached
        path = self.client.download_stream(track.id, folder)
        prune_cache()
        return path

    def start_audio(self, track: Track, path: Path) -> None:
        self.player.play(path, track)
        if self.player.alive:
            self.status = f"Playing {track.title} — {track.artist}"
            self.err = ""
            self.publish()
        else:
            self.status = "The audio player failed to start"

    def toggle_pause(self) -> None:
        if not self.player.track or not self.player.alive:
            self.status = "Nothing is playing"
            return
        state = self.player.toggle_pause()
        if state is None:
            self.status = "Pause needs mpv; install it for transport controls"
        else:
            self.status = "Paused" if state else "Playing"
            self.publish()

    def step(self, delta: int) -> None:
        if not self.queue:
            self.status = "Queue is empty"
            return
        self.qindex = (self.qindex + delta) % len(self.queue)
        self.play_current()

    def check_player(self) -> None:
        if self.player.track is not None and self.player.finished():
            track = self.player.track
            self.player.stop()
            if self.queue:
                self.status = f"Finished {track.title}"
                self.step(1)

    def enqueue(self, track: Track) -> None:
        self.queue.append(track)
        self.status = f"Queued {track.title}"

    def like_selected(self) -> None:
        row = self.current_row()
        if not row or not row.track:
            self.status = "Select a track to like"
            return
        track = row.track
        self.submit(lambda: self.client.like(track.id), lambda liked: self.after_like(track, liked))

    def after_like(self, track: Track, liked: bool) -> None:
        for row in self.rows:
            if row.track and row.track.id == track.id:
                row.liked = liked
        self.queue = [
            Track(**{**t.__dict__, "liked": liked}) if t.id == track.id else t
            for t in self.queue
        ]
        self.status = "Liked" if liked else "Unliked"

    def publish(self) -> None:
        """Best-effort playback snapshot for bots, the dashboard and other devices."""
        if self.mode != "browse" or not self.client.cookies:
            return
        track = self.player.track
        track_id = track.id if track else None
        duration = track.duration if track else 0.0
        playing = bool(self.player.alive and not self.player.paused)
        queue = [t.id for t in self.queue]

        def work() -> None:
            try:
                self.client.publish_playback(track_id, 0.0, duration, playing, queue)
            except (ApiError, OSError):
                pass

        threading.Thread(target=work, daemon=True).start()

    def radio_selected(self) -> None:
        row = self.current_row()
        if not row or not row.track:
            self.status = "Select a track for radio"
            return
        track = row.track
        self.submit(lambda: self.client.radio(track.id),
                    lambda tracks: self.play_list(tracks, 0) if tracks else None,
                    "Starting radio…")

    # ── input ────────────────────────────────────────────────────────────
    def current_row(self) -> Optional[Row]:
        if 0 <= self.cursor < len(self.rows):
            return self.rows[self.cursor]
        return None

    def move(self, delta: int) -> None:
        if not self.rows:
            return
        self.cursor = max(0, min(len(self.rows) - 1, self.cursor + delta))

    def activate(self) -> None:
        row = self.current_row()
        if not row:
            return
        if row.kind == "track" and row.track:
            tracks = [r.track for r in self.rows if r.kind == "track" and r.track]
            index = tracks.index(row.track) if row.track in tracks else 0
            self.play_list(tracks, index)
        elif row.kind == "album" and row.album:
            self.load("album", row.album, push=True)
        elif row.kind == "artist" and row.artist:
            self.load("artist", row.artist, push=True)
        elif row.kind == "playlist" and row.playlist_id:
            self.load("playlist", row.playlist_id, push=True)

    def handle(self, ch: Any) -> None:
        if self.mode != "browse":
            self.handle_login(ch)
            return
        if self.help:
            self.help = False
            return
        if self.picker is not None:
            self.handle_picker(ch)
            return
        if self.prompt is not None:
            self.handle_prompt(ch)
            return

        if isinstance(ch, int):
            if ch == curses.KEY_UP:
                self.move(-1)
            elif ch == curses.KEY_DOWN:
                self.move(1)
            elif ch == curses.KEY_PPAGE:
                self.move(-10)
            elif ch == curses.KEY_NPAGE:
                self.move(10)
            elif ch == curses.KEY_HOME:
                self.cursor = 0
            elif ch == curses.KEY_END:
                self.cursor = max(0, len(self.rows) - 1)
            elif ch == curses.KEY_ENTER:
                self.activate()
            elif ch == curses.KEY_BACKSPACE:
                self.back()
            elif ch == curses.KEY_RESIZE:
                pass
            return

        if ch == "\x1b":
            self.back()
        elif ch in ("\n", "\r"):
            self.activate()
        elif ch == "q":
            self.quit = True
        elif ch.isdigit() and ch != "0":
            views = self.views()
            index = int(ch) - 1
            if index < len(views):
                self.history.clear()
                self.load(views[index][0])
        elif ch == "/":
            self.start_prompt("Search: ", "", self.search_for)
        elif ch == "j":
            self.move(1)
        elif ch == "k":
            self.move(-1)
        elif ch == "g":
            self.cursor = 0
        elif ch == "G":
            self.cursor = max(0, len(self.rows) - 1)
        elif ch == " ":
            self.toggle_pause()
        elif ch == "n":
            self.step(1)
        elif ch == "p":
            self.step(-1)
        elif ch in ("+", "="):
            self.change_volume(5)
        elif ch == "-":
            self.change_volume(-5)
        elif ch == "l":
            self.like_selected()
        elif ch == "a":
            row = self.current_row()
            if row and row.track:
                self.enqueue(row.track)
        elif ch == "r":
            self.radio_selected()
        elif ch == "c":
            self.queue.clear()
            self.qindex = -1
            self.player.stop()
            self.status = "Queue cleared"
            if self.view == "queue":
                self.load("queue")
        elif ch == "N":
            if self.view == "requests":
                self.start_prompt("Request URL: ", "", self.add_request)
            elif self.view in ("playlists", "playlist"):
                self.start_prompt("New playlist: ", "", self.new_playlist)
            else:
                self.status = "Open Playlists (6) to add one"
        elif ch == "R":
            self.rename_selected()
        elif ch == "d":
            self.delete_selected()
        elif ch == "A":
            self.open_picker()
        elif ch == "x":
            if self.view == "requests":
                self.request_action("reject")
            elif self.view == "playlist":
                self.remove_selected_track()
        elif ch == "y":
            if self.view == "requests":
                self.request_action("approve")
        elif ch == "t":
            if self.view == "admin":
                self.toggle_admin()
        elif ch == "s":
            if self.view == "admin":
                self.scan_library()
        elif ch == "?":
            self.help = True
        elif ch == "u":
            self.sign_out()
        elif ch == "S":
            self.mode = "login"
            self.login_index = 0
            self.register = False
            self.login["password"] = ""

    def handle_prompt(self, ch: Any) -> None:
        if isinstance(ch, int):
            if ch == curses.KEY_BACKSPACE:
                self.prompt = (self.prompt or "")[:-1]
            elif ch == curses.KEY_ENTER:
                self.finish_prompt()
            return
        if ch == "\x1b":
            self.prompt = None
            self.prompt_done = None
            self.status = ""
        elif ch in ("\n", "\r"):
            self.finish_prompt()
        elif ch in ("\x7f", "\b"):
            self.prompt = (self.prompt or "")[:-1]
        elif ch.isprintable():
            self.prompt = (self.prompt or "") + ch

    def start_prompt(self, label: str, initial: str,
                     done: Callable[[str], None]) -> None:
        self.prompt = initial
        self.prompt_label = label
        self.prompt_done = done
        self.status = ""

    def finish_prompt(self) -> None:
        text = (self.prompt or "").strip()
        done = self.prompt_done
        self.prompt = None
        self.prompt_done = None
        self.status = ""
        if done is not None:
            done(text)

    def search_for(self, query: str) -> None:
        if not query:
            return
        self.history.clear()
        self.load("search", query)

    def change_volume(self, delta: int) -> None:
        self.player.set_volume(self.player.volume + delta)
        self.cfg.volume = self.player.volume
        self.cfg.save()
        self.status = f"Volume {self.player.volume}%"

    def sign_out(self) -> None:
        self.client.logout()
        self.client.cookies.clear()
        self.cfg.cookies = {}
        self.cfg.save()
        self.player.stop()
        self.queue.clear()
        self.qindex = -1
        self.rows = []
        self.history.clear()
        self.is_admin = False
        self.requests_admin = False
        self.mode = "login"
        self.login_index = 0
        self.login["password"] = ""

    # ── login ────────────────────────────────────────────────────────────
    # ── playlists ────────────────────────────────────────────────────────
    def playlist_context(self) -> tuple[int, str]:
        if self.view == "playlist" and self.arg:
            return int(self.arg), self.title
        row = self.current_row()
        if row and row.kind == "playlist":
            return row.playlist_id, row.label
        return 0, ""

    def new_playlist(self, name: str) -> None:
        name = name.strip()[:100]
        if not name:
            self.status = "Playlist name required"
            return
        self.submit(lambda: self.client.create_playlist(name),
                    lambda _: self.after_playlist_write(f"Created {name}", "playlists"),
                    "Creating…")

    def rename_selected(self) -> None:
        playlist_id, name = self.playlist_context()
        if not playlist_id:
            self.status = "Select a playlist to rename"
            return
        self.start_prompt("Rename to: ", name,
                          lambda new: self.rename_playlist(playlist_id, new))

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        name = name.strip()[:100]
        if not name:
            self.status = "Name required"
            return
        self.submit(lambda: self.client.rename_playlist(playlist_id, name),
                    lambda _: self.after_playlist_write(f"Renamed to {name}", None),
                    "Renaming…")

    def delete_selected(self) -> None:
        playlist_id, name = self.playlist_context()
        if not playlist_id:
            self.status = "Select a playlist to delete"
            return
        self.start_prompt(f"Delete '{name}'? y/n: ", "",
                          lambda answer: self.delete_playlist(playlist_id, name, answer))

    def delete_playlist(self, playlist_id: int, name: str, answer: str) -> None:
        if answer.lower() not in ("y", "yes"):
            self.status = "Cancelled"
            return
        self.submit(lambda: self.client.delete_playlist(playlist_id),
                    lambda _: self.after_playlist_write(f"Deleted {name}", "playlists"),
                    "Deleting…")

    def after_playlist_write(self, message: str, view: Optional[str]) -> None:
        self.status = message
        if view:
            self.history.clear()
            self.load(view)
        elif self.view == "playlist":
            self.load("playlist", self.arg)
        else:
            self.load("playlists")

    def open_picker(self) -> None:
        row = self.current_row()
        if not row or not row.track:
            self.status = "Select a track first"
            return
        self.pending_track = row.track
        self.submit(self.client.playlists, self.show_picker, "Loading playlists…")

    def show_picker(self, playlists: list[PlaylistRef]) -> None:
        if not playlists:
            self.status = "No playlists yet — press 6 then N"
            return
        self.picker = playlists
        self.picker_index = 0

    def handle_picker(self, ch: Any) -> None:
        if self.picker is None:
            return
        count = len(self.picker) or 1
        if isinstance(ch, int):
            if ch == curses.KEY_UP:
                self.picker_index = (self.picker_index - 1) % count
            elif ch == curses.KEY_DOWN:
                self.picker_index = (self.picker_index + 1) % count
            elif ch == curses.KEY_ENTER:
                self.picker_choose()
            return
        if ch == "\x1b":
            self.picker = None
            self.pending_track = None
        elif ch in ("\n", "\r"):
            self.picker_choose()
        elif ch == "k":
            self.picker_index = (self.picker_index - 1) % count
        elif ch == "j":
            self.picker_index = (self.picker_index + 1) % count

    def picker_choose(self) -> None:
        if not self.picker or not self.pending_track:
            self.picker = None
            self.pending_track = None
            return
        target = self.picker[self.picker_index % len(self.picker)]
        track = self.pending_track
        self.picker = None
        self.pending_track = None
        self.submit(lambda: self.client.add_to_playlist(target.id, track.id),
                    lambda _: self.after_added(target.name, track),
                    "Adding…")

    def after_added(self, playlist: str, track: Track) -> None:
        self.status = f"Added {track.title} to {playlist}"

    def remove_selected_track(self) -> None:
        row = self.current_row()
        playlist_id = int(self.arg or 0) if self.view == "playlist" else 0
        if not row or not row.track or not playlist_id:
            self.status = "Open a playlist and select a track"
            return
        track = row.track
        self.submit(lambda: self.client.remove_from_playlist(playlist_id, track.id),
                    lambda _: self.after_removed(playlist_id, track),
                    "Removing…")

    def after_removed(self, playlist_id: int, track: Track) -> None:
        self.status = f"Removed {track.title}"
        self.load("playlist", playlist_id)

    # ── requests ─────────────────────────────────────────────────────────
    def add_request(self, url: str) -> None:
        if not url:
            return
        self.submit(lambda: self.client.request_add(url),
                    self.after_request, "Submitting…")

    def after_request(self, status: str) -> None:
        self.status = f"Request {status}" if status else "Request submitted"
        if self.view == "requests":
            self.load("requests")

    def request_action(self, action: str) -> None:
        if not self.requests_admin:
            self.status = "Admins only"
            return
        row = self.current_row()
        if not row or row.kind != "request" or not row.request:
            self.status = "Select a request"
            return
        request_id = row.request.id
        self.submit(lambda: self.client.request_act(request_id, action),
                    lambda _: self.after_request_action(action),
                    f"{action.title()}…")

    def after_request_action(self, action: str) -> None:
        done = {"approve": "approved", "reject": "rejected"}.get(action, action)
        self.status = f"Request {done}"
        self.load("requests")

    # ── admin ────────────────────────────────────────────────────────────
    def scan_library(self) -> None:
        self.submit(self.client.admin_scan,
                    lambda counts: self.after_scan(counts), "Scanning library…")

    def after_scan(self, counts: tuple[int, int]) -> None:
        self.status = f"Scanned: {counts[0]} tracks · {counts[1]} albums"
        self.load("admin")

    def toggle_admin(self) -> None:
        row = self.current_row()
        if not row or row.kind != "admin-user" or not row.user:
            self.status = "Select a user"
            return
        user = row.user
        self.submit(lambda: self.client.admin_set_admin(user.id, not user.is_admin),
                    lambda _: self.after_toggle(user), "Saving…")

    def after_toggle(self, user: AdminUser) -> None:
        role = "a member" if user.is_admin else "an admin"
        self.status = f"{user.username} is now {role}"
        self.load("admin")

    # ── login ────────────────────────────────────────────────────────────
    def login_fields(self) -> list[str]:
        return ["server", "username", "password"] + (["invite"] if self.register else [])

    def handle_login(self, ch: Any) -> None:
        fields = self.login_fields()
        if isinstance(ch, int):
            if ch == curses.KEY_UP:
                self.login_index = (self.login_index - 1) % len(fields)
            elif ch == curses.KEY_DOWN:
                self.login_index = (self.login_index + 1) % len(fields)
            elif ch == curses.KEY_F2:
                self.register = not self.register
                self.login_index = min(self.login_index, len(self.login_fields()) - 1)
            elif ch == curses.KEY_ENTER:
                self.submit_login()
            elif ch == curses.KEY_BACKSPACE:
                key = fields[min(self.login_index, len(fields) - 1)]
                self.login[key] = self.login[key][:-1]
            return

        if ch == "\x1b":
            self.quit = True
        elif ch in ("\n", "\r"):
            self.submit_login()
        elif ch == "\t":
            self.login_index = (self.login_index + 1) % len(fields)
        elif ch in ("\x7f", "\b"):
            key = fields[min(self.login_index, len(fields) - 1)]
            self.login[key] = self.login[key][:-1]
        elif ch.isprintable():
            key = fields[min(self.login_index, len(fields) - 1)]
            self.login[key] = self.login[key] + ch

    def submit_login(self) -> None:
        user = self.login["username"].strip()
        password = self.login["password"]
        invite = self.login["invite"].strip()
        self.client.set_base(self.login["server"].strip() or DEFAULT_SERVER)
        self.cfg.save()
        if not user:
            self.err = "Enter a username"
            return
        if not password:
            self.err = "Enter a password"
            return
        if self.register and not invite:
            self.err = "Registration needs an invite code"
            return

        self.err = ""
        self.mode = "connecting"

        def work():
            if self.register:
                return self.client.register(user, password, invite)
            return self.client.login(user, password)

        self.submit(work, self.after_login, "Signing in…")

    def after_login(self, me) -> None:
        self.username = me.username or self.login["username"].strip()
        self.cfg.username = self.username
        self.is_admin = bool(me.is_admin)
        self.cfg.save()
        self.mode = "browse"
        self.login["password"] = ""
        self.history.clear()
        self.load("home")

    # ── drawing ──────────────────────────────────────────────────────────
    def put(self, y: int, x: int, text: str, width: int, attr: int = 0) -> None:
        if y < 0 or x < 0 or width <= 0:
            return
        try:
            self.scr.addnstr(y, x, text, max(0, width - x - 1), attr)
        except curses.error:
            pass

    def draw(self) -> None:
        self.scr.erase()
        try:
            height, width = self.scr.getmaxyx()
        except curses.error:
            return
        if height < 8 or width < 30:
            self.put(0, 0, "mcmusic: terminal too small", width)
            self.scr.refresh()
            return

        if self.mode in ("login", "connecting"):
            self.draw_login(height, width)
        else:
            self.draw_browse(height, width)

        try:
            self.scr.refresh()
        except curses.error:
            pass

    def draw_browse(self, height: int, width: int) -> None:
        head = f" mcmusic  {self.title}"
        right = f"{self.username or 'signed out'} · {self.client.base} "
        self.put(0, 0, head.ljust(width), width,
                 curses.A_REVERSE | curses.A_BOLD)
        if len(head) + len(right) < width:
            self.put(0, width - len(right) - 1, right, width, curses.A_REVERSE)

        x = 1
        for index, (view, label) in enumerate(self.views()):
            text = f" {index + 1} {label} "
            attr = curses.A_REVERSE | curses.A_BOLD if view == self.view else curses.A_DIM
            self.put(1, x, text, width, attr)
            x += len(text)

        top = 2
        bottom = height - 3
        visible = max(1, bottom - top)
        if self.cursor < self.offset:
            self.offset = self.cursor
        elif self.cursor >= self.offset + visible:
            self.offset = self.cursor - visible + 1

        for line in range(visible):
            index = self.offset + line
            if index >= len(self.rows):
                break
            row = self.rows[index]
            y = top + line
            if row.kind == "heading":
                self.put(y, 2, row.label.upper(), width, curses.A_BOLD | curses.A_UNDERLINE)
                continue
            if row.kind == "empty":
                self.put(y, 2, row.label, width, curses.A_DIM)
                continue

            mark = ">" if self.playing_row(row) else " "
            heart = "L" if row.liked else " "
            text = f"{mark} {row.label}"
            self.put(y, 2, text, width)
            sub = row.sub
            if sub:
                start = max(2 + len(text) + 2, width - len(sub) - 8)
                if start + len(sub) < width - 2:
                    self.put(y, start, sub, width, curses.A_DIM)
            self.put(y, width - 3, heart, width,
                     curses.A_BOLD if row.liked else curses.A_DIM)
            if index == self.cursor:
                self.fill_row(y, width)

        now = self.now_playing()
        self.put(height - 3, 1, now, width,
                 curses.A_BOLD if self.player.track else curses.A_DIM)

        if self.prompt is not None:
            label = self.prompt_label
            self.put(height - 2, 1, label + (self.prompt or ""), width, curses.A_BOLD)
            self.show_cursor(height - 2, 1 + len(label) + len(self.prompt or ""), width)
        elif self.err:
            self.put(height - 2, 1, self.err, width, curses.A_BOLD)
        elif self.status:
            self.put(height - 2, 1, self.status, width)

        self.put(height - 1, 1, HINTS, width, curses.A_DIM)

        if self.help:
            self.draw_help(height, width)
        if self.picker is not None:
            self.draw_picker(height, width)

    def fill_row(self, y: int, width: int) -> None:
        """Reverse the whole row so the selection follows the text."""
        try:
            self.scr.chgat(y, 1, max(1, width - 1), curses.A_REVERSE)
        except curses.error:
            pass

    def playing_row(self, row: Row) -> bool:
        track = self.player.track
        return bool(track and row.track and track.id == row.track.id)

    def now_playing(self) -> str:
        track = self.player.track
        if not track:
            return "[stopped]"
        state = "[paused]" if self.player.paused else "[playing]"
        return f"{state} {track.title} — {track.artist}   vol {self.player.volume}%"

    def draw_help(self, height: int, width: int) -> None:
        lines = [
            ("Enter", "play / open album, artist or playlist"),
            ("space", "pause or resume (mpv)"),
            ("n / p", "next / previous track"),
            ("l", "like or unlike the selection"),
            ("a", "append the selection to the queue"),
            ("r", "start radio from the selection"),
            ("c", "clear the queue"),
            ("N", "new playlist, or new download request"),
            ("A", "add the selection to a playlist"),
            ("R / d", "rename / delete the selected playlist"),
            ("x", "remove from playlist, or reject a request"),
            ("y", "approve a pending request (admin)"),
            ("t / s", "toggle admin, rescan library (admin)"),
            ("/", "search the library"),
            ("Esc", "back"),
            ("1-9", "views, including requests and admin"),
            ("+ / -", "volume"),
            ("S", "change server / account"),
            ("u", "sign out"),
            ("q", "quit"),
        ]
        box_w = min(width - 4, 62)
        box_h = min(height - 4, len(lines) + 4)
        top = max(1, (height - box_h) // 2)
        left = max(1, (width - box_w) // 2)
        self.put(top, left, "─" * box_w, width, curses.A_BOLD)
        for i, (key, text) in enumerate(lines[: box_h - 3]):
            self.put(top + 1 + i, left + 2, f"{key:<7}", width, curses.A_BOLD)
            self.put(top + 1 + i, left + 11, text, width)
        self.put(top + box_h - 1, left, "─" * box_w, width, curses.A_BOLD)
        self.put(top + box_h - 2, left + 2, "any key closes help", width, curses.A_DIM)

    def draw_picker(self, height: int, width: int) -> None:
        playlists = self.picker or []
        box_h = min(height - 4, len(playlists) + 4)
        box_w = min(width - 6, 56)
        top = max(1, (height - box_h) // 2)
        left = max(1, (width - box_w) // 2)
        self.put(top, left, "─" * box_w, width, curses.A_BOLD)
        self.put(top + 1, left + 2, "Add to playlist", width, curses.A_BOLD)
        selected = self.picker_index % (len(playlists) or 1)
        for index, playlist in enumerate(playlists[: max(0, box_h - 4)]):
            attr = curses.A_REVERSE if index == selected else 0
            text = f" {playlist.name} · {playlist.n} tracks"
            self.put(top + 2 + index, left + 1,
                     text.ljust(max(1, box_w - 2)), width, attr)
        self.put(top + box_h - 2, left + 2, "Enter adds · Esc cancels",
                 width, curses.A_DIM)
        self.put(top + box_h - 1, left, "─" * box_w, width, curses.A_BOLD)

    def show_cursor(self, y: int, x: int, width: int) -> None:
        try:
            self.scr.move(y, min(x, width - 2))
            curses.curs_set(1)
        except curses.error:
            pass

    def draw_login(self, height: int, width: int) -> None:
        self.put(0, 0, " mcmusic — sign in".ljust(width), width,
                 curses.A_REVERSE | curses.A_BOLD)
        fields = self.login_fields()
        labels = {
            "server": "Server",
            "username": "Username",
            "password": "Password",
            "invite": "Invite",
        }
        top = max(2, (height - (len(fields) + 5)) // 2)
        self.put(top, 2, "mcmusic", width, curses.A_BOLD)
        self.put(top + 1, 2, "the same library as web, Android and the Qt client",
                 width, curses.A_DIM)

        y = top + 3
        for index, key in enumerate(fields):
            value = self.login[key]
            if key == "password":
                shown = "*" * len(value)
            else:
                shown = value
            active = index == self.login_index
            self.put(y + index, 2, f"{labels[key]:<9}", width,
                     curses.A_BOLD if active else curses.A_DIM)
            self.put(y + index, 12, shown, width - 12,
                     curses.A_UNDERLINE if active else 0)
            if active:
                self.show_cursor(y + index, 12 + len(shown), width)

        hint_y = y + len(fields) + 1
        mode = "create an account (F2 to sign in instead)" if self.register \
            else "F2 to register with an invite · Esc to quit"
        self.put(hint_y, 2, mode, width, curses.A_DIM)
        self.put(hint_y + 1, 2, "Enter to continue · Tab for the next field",
                 width, curses.A_DIM)

        if self.mode == "connecting":
            self.put(height - 2, 2, self.status or "Connecting…", width, curses.A_BOLD)
        elif self.err:
            self.put(height - 2, 2, self.err, width, curses.A_BOLD)
        self.put(height - 1, 2, f"server: {self.client.base}", width, curses.A_DIM)

    # ── loop ─────────────────────────────────────────────────────────────
    def boot(self) -> None:
        if not self.cfg.cookies:
            self.mode = "login"
            return
        self.mode = "connecting"
        self.submit(self.client.me, self.after_boot, "Connecting…")

    def after_boot(self, me) -> None:
        self.username = me.username or self.username
        self.cfg.username = self.username
        self.is_admin = bool(me.is_admin)
        self.mode = "browse"
        self.load("home")

    def run(self) -> int:
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.scr.timeout(150)
        try:
            self.scr.keypad(True)
        except curses.error:
            pass

        self.boot()
        while not self.quit:
            self.drain()
            self.draw()
            try:
                ch = self.scr.get_wch()
            except curses.error:
                ch = None
            except KeyboardInterrupt:
                break
            if ch is not None:
                self.handle(ch)
            self.check_player()

        self.player.stop()
        self.publish()
        self.cfg.save()
        return 0


# ── entry point ─────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    server = ""
    for index, arg in enumerate(args):
        if arg == "--server" and index + 1 < len(args):
            server = args[index + 1]
        elif arg.startswith("--server="):
            server = arg.split("=", 1)[1]

    cfg = Config()
    if server:
        cfg.base_url = normalize(server)
        cfg.save()

    try:
        return curses.wrapper(lambda screen: App(screen, cfg).run())
    except KeyboardInterrupt:
        return 130
    except curses.error:
        print("mcmusic: --tui needs an interactive terminal", file=sys.stderr)
        return 1
