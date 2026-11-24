"""Sink-agnostic player state and the text both sinks share."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

Loop = Literal["off", "all", "one"]

LOOP_ICON = {"off": "", "all": "🔁 All", "one": "🔂 One"}


def mmss(seconds: float) -> str:
    total = max(0, int(seconds))
    return f"{total // 60}:{total % 60:02d}"


@dataclass
class Track:
    id: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    cover_url: str | None = None
    url: str | None = None

    def media(self) -> dict:
        out = {"title": self.title, "artist": self.artist}
        if self.album:
            out["album"] = self.album
        return out


@dataclass
class PlayerState:
    track: Track | None
    playing: bool
    position: float = 0.0
    updated_at: float = field(default_factory=time.time)
    loop: Loop = "off"
    shuffle: bool = False
    queue_index: int = 0
    queue_len: int = 0
    next: Track | None = None
    # Free-form suffix shared by every sink, e.g. this account's room invite.
    extra: str = ""
    # Clickable links for rich status cards. ``extra`` stays as display text so
    # plain-text sinks do not suddenly gain raw URLs in the status line.
    room_url: str = ""
    profile_url: str = ""

    # ── derived ──────────────────────────────────────────────────────────
    @property
    def start_ms(self) -> int | None:
        if self.track is None or not self.playing:
            return None
        return int((self.updated_at - self.position) * 1000)

    @property
    def end_ms(self) -> int | None:
        if self.start_ms is None or not self.track or self.track.duration <= 0:
            return None
        return self.start_ms + int(self.track.duration * 1000)

    @property
    def progress(self) -> float:
        if not self.track or self.track.duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.position / self.track.duration))

    # ── text ─────────────────────────────────────────────────────────────
    def loop_text(self) -> str:
        return LOOP_ICON.get(self.loop, "")

    def queue_text(self) -> str:
        if self.queue_len <= 0:
            return ""
        return f"{min(self.queue_index + 1, self.queue_len)}/{self.queue_len}"

    def progress_bar(self, width: int = 8) -> str:
        filled = round(self.progress * width)
        return "▰" * filled + "▱" * (width - filled)

    def progress_text(self) -> str:
        if not self.track or self.track.duration <= 0:
            return ""
        return f"{self.progress_bar()} {mmss(self.position)}/{mmss(self.track.duration)}"

    def playthrough_text(self) -> str:
        if self.loop == "one":
            return "Repeating"
        if self.next:
            return f"Next: {self.next.title} - {self.next.artist}".strip(" -")
        return ""

    def status_line(self) -> str:
        parts: list[str] = []
        if not self.playing:
            parts.append("Paused")
        if self.loop_text():
            parts.append(self.loop_text())
        if self.shuffle:
            parts.append("🔀")
        if self.queue_text():
            parts.append(self.queue_text())
        if self.progress_text():
            parts.append(self.progress_text())
        if self.extra:
            parts.append(self.extra)
        return " · ".join(parts)[:128]

    def fallback_text(self) -> str:
        """Plain-text description for sinks without a rich activity card."""
        if not self.track:
            return ""
        head = f"🎵 {self.track.title} - {self.track.artist}"
        tail = " · ".join(
            x for x in (self.status_line(), self.playthrough_text(), self.extra) if x
        )
        return f"{head}\n{tail}".strip()

    def key(self) -> tuple:
        """Everything that should trigger a sink update (not the clock)."""
        t = self.track
        return (
            t.id if t else None, self.playing, round(self.position, 1), self.loop,
            self.shuffle, self.queue_index, self.queue_len,
            self.next.id if self.next else None, self.extra,
            self.room_url, self.profile_url,
        )
