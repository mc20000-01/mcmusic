"""Discord Rich Presence sink (local IPC only, desktop client required)."""
from __future__ import annotations

import queue
import threading
import time

from music_activity.sinks.base import daemon_thread
from music_activity.state import PlayerState

try:
    from pypresence import ActivityType, Presence
except Exception:  # noqa: BLE001
    Presence = None
    ActivityType = None


class DiscordSink:
    """Updates at most every 15 s; quiet 30 s retry when Discord is closed."""

    def __init__(self, app_id: str, *, log=print, min_interval: float = 15.0) -> None:
        self.app_id = app_id
        self.log = log
        self.min_interval = min_interval
        self._q: queue.Queue = queue.Queue(maxsize=4)
        self._stop = threading.Event()
        self._rpc = None
        self._thread: threading.Thread | None = None
        self._supported = True
        self._last_key = None
        self._last_sent = 0.0

    def connect(self) -> None:
        if not self.app_id:
            raise RuntimeError("DISCORD_APP_ID is not set")
        if Presence is None:
            raise RuntimeError("the 'pypresence' package is not installed")
        self._thread = daemon_thread("discord-activity", self._run)

    def publish(self, state: PlayerState) -> None:
        self._put(("publish", state))

    def clear(self) -> None:
        self._put(("clear", None))

    def close(self) -> None:
        self._stop.set()
        self._put(("stop", None))
        if self._thread:
            self._thread.join(timeout=4)

    # ── plumbing ─────────────────────────────────────────────────────────
    def _put(self, item) -> None:
        try:
            self._q.put_nowait(item)
        except queue.Full:
            try:
                self._q.get_nowait()
                self._q.put_nowait(item)
            except (queue.Empty, queue.Full):
                pass

    def _run(self) -> None:
        while not self._stop.is_set():
            kind, state = self._q.get()
            if kind == "stop":
                return
            if self._rpc is None and not self._connect():
                if self._stop.wait(30):
                    return
                continue
            if kind == "clear":
                self._safe_clear()
                self._last_key = None
                continue
            assert state is not None
            self._maybe_update(state)

    def _connect(self) -> bool:
        try:
            self._rpc = Presence(self.app_id)
            self._rpc.connect()
            self.log("discord: connected")
            return True
        except Exception as exc:  # noqa: BLE001
            self.log(f"discord: unavailable ({exc}); retrying in 30s")
            self._rpc = None
            return False

    def _maybe_update(self, state: PlayerState) -> None:
        if state.key() == self._last_key:
            return
        now = time.time()
        if now - self._last_sent < self.min_interval:
            return
        try:
            self._update(state)
            self._last_key = state.key()
            self._last_sent = now
        except Exception as exc:  # noqa: BLE001
            self.log(f"discord: update failed ({exc}), reconnecting")
            self._rpc = None
            self._last_key = None

    def _update(self, state: PlayerState) -> None:
        t = state.track
        assert t is not None and self._rpc is not None
        details = (t.title or "mcmusic")[:128]
        if len(details) < 2:
            details = (details + " ·")[:128]
        loop = state.loop_text()
        tail = " · ".join(x for x in (loop, state.queue_text()) if x)
        if state.playing:
            parts = [t.artist or "mcmusic"]
            if tail:
                parts.append(tail)
            state_text = " · ".join(parts)[:128]
            if len(state_text) < 2:
                state_text = "Playing"
            now = time.time()
            start = int(state.updated_at - state.position)
            end = int(start + t.duration) if t.duration > 0 else None
        else:
            state_text = ("Paused" + (f" · {tail}" if tail else ""))[:128]
            start = end = None
        kwargs = {
            "details": details,
            "state": state_text,
            "large_image": t.cover_url or "mcmusic",
            "large_text": (t.album or "mcmusic")[:128],
            "small_image": "loop_one" if state.loop == "one" else "loop",
            "small_text": (loop or "Loop: off")[:128],
        }
        if state.playing:
            kwargs["start"] = start
            if end:
                kwargs["end"] = end
        buttons = self._buttons(state)
        if buttons:
            kwargs["buttons"] = buttons
        try:
            self._send(kwargs)
        except Exception:
            # Clients older than the button support reject the whole activity,
            # and a dropped presence is worse than a missing link.
            if "buttons" not in kwargs:
                raise
            kwargs.pop("buttons")
            self.log("discord: buttons unsupported, publishing without links")
            self._send(kwargs)

    @staticmethod
    def _buttons(state: PlayerState) -> list[dict]:
        """Discord allows two links; offer the room first, then the profile."""
        out: list[dict] = []
        room = (state.extra or "").strip()
        if room.startswith(("http://", "https://")):
            out.append({"label": "Listen along", "url": room[:512]})
        profile = (state.track.url if state.track else None) or ""
        profile = profile.strip()
        if profile.startswith(("http://", "https://")) and profile != room:
            out.append({"label": "mcmusic profile", "url": profile[:512]})
        return out[:2]

    def _send(self, kwargs: dict) -> None:
        assert self._rpc is not None
        if self._supported and ActivityType is not None:
            try:
                self._rpc.update(activity_type=ActivityType.LISTENING, **kwargs)
                return
            except Exception:  # noqa: BLE001 - older clients reject the field
                self._supported = False
                self.log("discord: activity_type unsupported, falling back to Playing")
        self._rpc.update(**kwargs)

    def _safe_clear(self) -> None:
        try:
            if self._rpc:
                self._rpc.clear()
        except Exception:  # noqa: BLE001
            self._rpc = None
