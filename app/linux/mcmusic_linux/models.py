"""Typed payloads for the mcmusic API.

Mirrors app/android/.../data/Models.kt and ``database.track_dict`` so the
desktop client talks to exactly the same server contract as web and Android.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# ── tolerant JSON helpers ────────────────────────────────────────────────────


def _s(o: dict, key: str, default: str = "") -> str:
    v = o.get(key)
    if v is None:
        return default
    text = str(v).strip()
    return text or default


def _i(o: dict, key: str, default: int = 0) -> int:
    try:
        v = o.get(key)
        return default if v is None else int(v)
    except (TypeError, ValueError):
        return default


def _f(o: dict, key: str, default: float = 0.0) -> float:
    try:
        v = o.get(key)
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def _b(o: dict, key: str, default: bool = False) -> bool:
    v = o.get(key)
    return default if v is None else bool(v)


def _opt_i(o: dict, key: str) -> Optional[int]:
    v = o.get(key)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _opt_s(o: dict, key: str) -> Optional[str]:
    v = o.get(key)
    if v is None:
        return None
    text = str(v).strip()
    return text or None


# ── models ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Track:
    id: int
    title: str
    artist: str
    album: str
    track_no: int = 0
    genre: str = ""
    year: str = ""
    duration: float = 0.0
    liked: bool = False
    explicit: bool = False
    yt_id: Optional[str] = None
    yt_likes: Optional[int] = None
    yt_views: Optional[int] = None
    yt_channel: Optional[str] = None
    yt_date: Optional[str] = None
    added: float = 0.0

    @property
    def initials(self) -> str:
        return (self.title[:1] or "?").upper()

    @staticmethod
    def from_json(o: dict) -> "Track":
        return Track(
            id=_i(o, "id"),
            title=_s(o, "title", "Unknown"),
            artist=_s(o, "artist", "Unknown Artist"),
            album=_s(o, "album"),
            track_no=_i(o, "track_no"),
            genre=_s(o, "genre"),
            year=_s(o, "year"),
            duration=_f(o, "duration"),
            liked=_b(o, "liked"),
            explicit=_b(o, "explicit"),
            yt_id=_opt_s(o, "yt_id"),
            yt_likes=_opt_i(o, "yt_likes"),
            yt_views=_opt_i(o, "yt_views"),
            yt_channel=_opt_s(o, "yt_channel"),
            yt_date=_opt_s(o, "yt_date"),
            added=_f(o, "added"),
        )

    @staticmethod
    def list_json(rows: Iterable[dict] | None) -> list["Track"]:
        return [Track.from_json(r) for r in (rows or []) if isinstance(r, dict)]


@dataclass(frozen=True)
class AlbumRef:
    album: str
    artist: str = ""
    n: int = 0
    cover_id: Optional[int] = None

    @staticmethod
    def from_json(o: dict) -> "AlbumRef":
        return AlbumRef(
            album=_s(o, "album", "Unknown Album"),
            artist=_s(o, "artist"),
            n=_i(o, "n"),
            cover_id=_opt_i(o, "cover_id"),
        )

    @staticmethod
    def list_json(rows: Iterable[dict] | None) -> list["AlbumRef"]:
        return [AlbumRef.from_json(r) for r in (rows or []) if isinstance(r, dict)]


@dataclass(frozen=True)
class ArtistRef:
    artist: str
    n: int = 0
    albums: int = 0
    cover_id: Optional[int] = None

    @staticmethod
    def from_json(o: dict) -> "ArtistRef":
        return ArtistRef(
            artist=_s(o, "artist", "Unknown Artist"),
            n=_i(o, "n"),
            albums=_i(o, "albums"),
            cover_id=_opt_i(o, "cover_id"),
        )

    @staticmethod
    def list_json(rows: Iterable[dict] | None) -> list["ArtistRef"]:
        return [ArtistRef.from_json(r) for r in (rows or []) if isinstance(r, dict)]


@dataclass(frozen=True)
class PlaylistRef:
    id: int
    name: str
    n: int = 0
    cover_id: Optional[int] = None

    @staticmethod
    def from_json(o: dict) -> "PlaylistRef":
        return PlaylistRef(
            id=_i(o, "id"),
            name=_s(o, "name", "Playlist"),
            n=_i(o, "n"),
            cover_id=_opt_i(o, "cover_id"),
        )

    @staticmethod
    def list_json(rows: Iterable[dict] | None) -> list["PlaylistRef"]:
        return [PlaylistRef.from_json(r) for r in (rows or []) if isinstance(r, dict)]


@dataclass(frozen=True)
class Section:
    title: str
    tracks: list[Track] = field(default_factory=list)


@dataclass(frozen=True)
class HomeData:
    sections: list[Section] = field(default_factory=list)
    albums: list[AlbumRef] = field(default_factory=list)


@dataclass(frozen=True)
class SearchData:
    tracks: list[Track] = field(default_factory=list)
    albums: list[AlbumRef] = field(default_factory=list)
    artists: list[ArtistRef] = field(default_factory=list)


@dataclass(frozen=True)
class Me:
    id: int = 0
    username: str = ""
    is_admin: bool = False
    rotur_id: Optional[str] = None
    rotur_linked: bool = False

    @staticmethod
    def from_json(o: dict) -> "Me":
        return Me(
            id=_i(o, "id"),
            username=_s(o, "username"),
            is_admin=_b(o, "is_admin"),
            rotur_id=_opt_s(o, "rotur_id"),
            rotur_linked=_b(o, "rotur_linked"),
        )


@dataclass(frozen=True)
class RequestRow:
    id: int
    url: str
    status: str = ""
    created: float = 0.0
    log: str = ""
    username: Optional[str] = None

    @staticmethod
    def from_json(o: dict) -> "RequestRow":
        return RequestRow(
            id=_i(o, "id"),
            url=_s(o, "url"),
            status=_s(o, "status"),
            created=_f(o, "created"),
            log=_s(o, "log"),
            username=_opt_s(o, "username"),
        )


@dataclass(frozen=True)
class AdminStats:
    users: int = 0
    admins: int = 0
    tracks: int = 0
    albums: int = 0
    playlists: int = 0
    plays: int = 0
    queue: int = 0
    rooms: int = 0
    music_bytes: int = 0
    disk_free: int = 0
    disk_total: int = 0
    uptime: float = 0.0

    @staticmethod
    def from_json(o: dict) -> "AdminStats":
        return AdminStats(
            users=_i(o, "users"),
            admins=_i(o, "admins"),
            tracks=_i(o, "tracks"),
            albums=_i(o, "albums"),
            playlists=_i(o, "playlists"),
            plays=_i(o, "plays"),
            queue=_i(o, "queue"),
            rooms=_i(o, "rooms"),
            music_bytes=_i(o, "music_bytes"),
            disk_free=_i(o, "disk_free"),
            disk_total=_i(o, "disk_total"),
            uptime=_f(o, "uptime"),
        )


@dataclass(frozen=True)
class AdminUser:
    id: int
    username: str
    is_admin: bool = False
    plays: int = 0
    likes: int = 0
    playlists: int = 0
    requests: int = 0

    @staticmethod
    def from_json(o: dict) -> "AdminUser":
        return AdminUser(
            id=_i(o, "id"),
            username=_s(o, "username"),
            is_admin=_b(o, "is_admin"),
            plays=_i(o, "plays"),
            likes=_i(o, "likes"),
            playlists=_i(o, "playlists"),
            requests=_i(o, "requests"),
        )


@dataclass(frozen=True)
class Settings:
    """Mirrors DEFAULT_SETTINGS in mcmusic.py and the Android Settings class."""

    theme: str = "dusk"
    accent: str = "#d98a3d"
    density: str = "comfy"
    covers: bool = True
    autoplay: bool = True
    hide_explicit: bool = False
    private: bool = False
    yt_stats: bool = True
    remember_volume: bool = True
    volume: float = 0.8
    prefetch: bool = True
    offline_audio: bool = True

    def to_json(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "accent": self.accent,
            "density": self.density,
            "covers": self.covers,
            "autoplay": self.autoplay,
            "hide_explicit": self.hide_explicit,
            "private": self.private,
            "yt_stats": self.yt_stats,
            "remember_volume": self.remember_volume,
            "volume": self.volume,
            "prefetch": self.prefetch,
            "offline_audio": self.offline_audio,
        }

    @staticmethod
    def from_json(o: dict) -> "Settings":
        d = Settings()
        return Settings(
            theme=_s(o, "theme", d.theme),
            accent=_s(o, "accent", d.accent),
            density=_s(o, "density", d.density),
            covers=_b(o, "covers", d.covers),
            autoplay=_b(o, "autoplay", d.autoplay),
            hide_explicit=_b(o, "hide_explicit", d.hide_explicit),
            private=_b(o, "private", d.private),
            yt_stats=_b(o, "yt_stats", d.yt_stats),
            remember_volume=_b(o, "remember_volume", d.remember_volume),
            volume=_f(o, "volume", d.volume),
            prefetch=_b(o, "prefetch", d.prefetch),
            offline_audio=_b(o, "offline_audio", d.offline_audio),
        )


# ── formatting (mirrors ui.js / Format.kt) ──────────────────────────────────


def fmt_time(seconds: float) -> str:
    s = max(0, int(seconds or 0))
    return f"{s // 60}:{s % 60:02d}"


def _trim(v: float) -> str:
    return f"{v:.1f}".removesuffix(".0")


def fmt_count(n: Optional[int]) -> str:
    if n is None:
        return ""
    if n >= 1_000_000_000:
        return _trim(n / 1_000_000_000) + "B"
    if n >= 1_000_000:
        return _trim(n / 1_000_000) + "M"
    if n >= 1_000:
        return _trim(n / 1_000) + "K"
    return str(n)


def fmt_total(seconds: float) -> str:
    m = int((seconds or 0) / 60)
    if m < 60:
        return f"{m} min"
    return f"{m // 60} hr {m % 60} min"


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    units = ["KB", "MB", "GB", "TB"]
    v = n / 1024.0
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return f"{v:.0f} {units[i]}" if v >= 10 else f"{v:.1f} {units[i]}"


def fmt_uptime(seconds: float) -> str:
    total = abs(int(seconds or 0))
    d, h, m = total // 86400, (total % 86400) // 3600, (total % 3600) // 60
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def initials(name: str) -> str:
    return (name[:1] or "?").upper()
