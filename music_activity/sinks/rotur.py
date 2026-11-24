"""Rotur status-websocket sink: one long-lived socket, no heartbeats.

Verified against docs.rotur.dev/assorted-apis/status-websocket:
  * auth within 15 s, `{"cmd": "ready"}`
  * `{"cmd": "join", "rooms": [...]}`
  * `{"cmd": "add_activity", ...}` (same id replaces), `remove_activity`
  * errors arrive as `{"cmd": "error", "message": ...}` on an open connection
  * websockets auto-answers ping frames, which is the only keepalive that counts
"""
from __future__ import annotations

import asyncio
import json
import queue
import threading

from music_activity.config import ROTUR_ACTIVITY_ID, ROTUR_WS, valid_rooms
from music_activity.sinks.base import Backoff, daemon_thread
from music_activity.state import PlayerState

try:  # imported lazily so the rest of the package works without the dep
    import websockets
except Exception:  # noqa: BLE001
    websockets = None


class RoturFatal(RuntimeError):
    """Bad key or missing scope: retrying cannot help."""


class RoturSink:
    def __init__(
        self,
        token: str,
        rooms: list[str] | None = None,
        *,
        endpoint: str = ROTUR_WS,
        activity_id: str = ROTUR_ACTIVITY_ID,
        app_name: str = "mcmusic",
        app_url: str = "https://mcmusic.sdisk.us",
        token_provider=None,
        log=print,
    ) -> None:
        self.token = token
        self._token_provider = token_provider
        self.rooms = valid_rooms(rooms or ["originChats"])
        self.endpoint = endpoint
        self.activity_id = activity_id
        self.app_name = app_name
        self.app_url = app_url
        self.log = log
        self._q: queue.Queue = queue.Queue(maxsize=8)
        self._stop = threading.Event()
        self._fatal = threading.Event()
        self._last: PlayerState | None = None
        self._thread: threading.Thread | None = None

    # ── Sink API ─────────────────────────────────────────────────────────
    def _resolve_token(self) -> str:
        """Called before every connection attempt so a refresh can be picked up."""
        if self._token_provider is not None:
            return str(self._token_provider() or "")
        return self.token

    def connect(self) -> None:
        if not self.token and self._token_provider is None:
            raise RoturFatal("ROTUR_TOKEN is not set")
        if websockets is None:
            raise RoturFatal("the 'websockets' package is not installed")
        self._thread = daemon_thread("rotur-activity", self._run)

    @property
    def running(self) -> bool:
        """True while the reconnect loop is still alive and usable."""
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._fatal.is_set()
            and not self._stop.is_set()
        )

    def publish(self, state: PlayerState) -> None:
        self._last = state
        self._put(("publish", state))

    def clear(self) -> None:
        self._last = None
        self._put(("clear", None))

    def close(self) -> None:
        self._stop.set()
        self._put(("stop", None))
        if self._thread:
            self._thread.join(timeout=6)

    # ── plumbing ─────────────────────────────────────────────────────────
    def _put(self, item) -> None:
        try:
            self._q.put_nowait(item)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(item)
            except queue.Full:
                pass

    def _run(self) -> None:
        backoff = Backoff(1.0, 30.0)
        while not self._stop.is_set() and not self._fatal.is_set():
            try:
                try:
                    self.token = self._resolve_token()
                except Exception as exc:  # noqa: BLE001
                    raise RuntimeError(f"token refresh failed: {exc}") from exc
                if not self.token:
                    raise RoturFatal("ROTUR_TOKEN is not set")
                asyncio.run(self._session())
                backoff.reset()
            except RoturFatal as exc:
                self._fatal.set()
                self.log(f"rotur: {exc} (not retrying)")
                return
            except Exception as exc:  # noqa: BLE001
                if self._stop.is_set():
                    return
                wait = backoff.next()
                self.log(f"rotur: {exc}; reconnecting in {wait:.0f}s")
                if self._stop.wait(wait):
                    return

    async def _session(self) -> None:
        assert websockets is not None
        async with websockets.connect(
            self.endpoint, max_size=2**16, ping_interval=20, open_timeout=15
        ) as ws:
            await ws.send(json.dumps({"cmd": "auth", "key": self.token}))
            await self._await_ready(ws)
            await ws.send(json.dumps({"cmd": "join", "rooms": self.rooms}))
            await self._await_join(ws)
            self.log(f"rotur: connected, joined {', '.join(self.rooms)}")
            if self._last is not None:
                await self._send_activity(ws, self._last)

            receiver = asyncio.create_task(self._receiver(ws))
            try:
                while not self._stop.is_set() and not self._fatal.is_set():
                    try:
                        kind, state = self._q.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.25)
                        continue
                    if kind == "publish" and state is not None:
                        await self._send_activity(ws, state)
                    elif kind == "clear":
                        await ws.send(json.dumps(
                            {"cmd": "remove_activity", "id": self.activity_id}
                        ))
                    elif kind == "stop":
                        return
            finally:
                receiver.cancel()

    async def _await_ready(self, ws) -> None:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=15)
        except asyncio.TimeoutError:
            raise RoturFatal("auth timed out after 15s")
        msg = self._msg(raw)
        cmd = msg.get("cmd")
        if cmd == "ready":
            return
        if cmd == "error":
            raise RoturFatal(self._explain(msg.get("message", "")))
        raise RoturFatal(f"unexpected auth reply: {msg}")

    async def _await_join(self, ws) -> None:
        deadline = asyncio.get_running_loop().time() + 6
        while asyncio.get_running_loop().time() < deadline:
            left = max(0.1, deadline - asyncio.get_running_loop().time())
            try:
                msg = self._msg(await asyncio.wait_for(ws.recv(), timeout=left))
            except asyncio.TimeoutError:
                return
            if msg.get("cmd") == "join_ok":
                return
            if msg.get("cmd") == "error":
                self.log(f"rotur: join failed: {msg.get('message', msg)}")
                return

    async def _receiver(self, ws) -> None:
        try:
            async for raw in ws:
                msg = self._msg(raw)
                if msg.get("cmd") == "error":
                    text = self._explain(msg.get("message", ""))
                    self.log(f"rotur: {text}")
                    if "invalid key" in text.lower() or "permission" in text.lower():
                        self._fatal.set()
                        return
        except Exception:  # noqa: BLE001 - the sender loop reconnects
            return

    async def _send_activity(self, ws, state: PlayerState) -> None:
        await ws.send(json.dumps(self.activity(state), ensure_ascii=False))

    def activity(self, s: PlayerState) -> dict:
        t = s.track
        assert t is not None
        payload: dict = {
            "cmd": "add_activity",
            "id": self.activity_id,
            "title": "Listening to mcmusic",
            "application": {"name": self.app_name, "url": self.app_url},
            "status": s.status_line(),
        }
        if t.cover_url:
            payload["image"] = t.cover_url
        room = (s.room_url or "").strip()
        profile = (s.profile_url or (t.url if t else "") or "").strip()
        # The heading should open the listening room; the profile stays one
        # click away as a button. Rotur renders `buttons` as real links.
        payload["url"] = (room or profile or self.app_url)[:512]
        buttons: list[dict] = []
        if room.startswith(("http://", "https://")):
            buttons.append({"label": "Play with me", "url": room[:512]})
        if profile.startswith(("http://", "https://")) and profile != room:
            buttons.append({"label": "mcmusic profile", "url": profile[:512]})
        if buttons:
            payload["buttons"] = buttons
        media = t.media()
        if s.start_ms is not None and s.end_ms is not None:
            media["start"] = s.start_ms
            media["end"] = s.end_ms
        payload["media"] = media
        payload["player"] = {
            "playing": s.playing,
            "loop": s.loop,
            "shuffle": s.shuffle,
            "queue_index": s.queue_index,
            "queue_len": s.queue_len,
            "next": {"title": s.next.title, "artist": s.next.artist} if s.next else None,
        }
        return payload

    @staticmethod
    def _msg(raw) -> dict:
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _explain(message: str) -> str:
        text = str(message or "")
        low = text.lower()
        if "invalid key" in low:
            return f"invalid key: {text} (fix ROTUR_TOKEN)"
        if "permission" in low:
            return f"token lacks account:profile: {text} (mint a sub-token with that scope)"
        if "not authenticated" in low:
            return "not authenticated (send auth first)"
        return text or "Rotur returned an error"
