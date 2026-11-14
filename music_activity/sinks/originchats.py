"""originChats text fallback: one "now playing" message, edited in place.

Uses the same REST contract as `src/originchats.py`:

  POST  {base}/channels/{channel}/messages       {"content": "..."} -> {"id": "..."}
  PATCH {base}/channels/{channel}/messages/{id}  {"content": "..."}

The message id is persisted, so a restart edits the existing message instead of
posting a second one. If the message was deleted (404) a new one is posted once.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time

import requests

from music_activity.config import (
    ORIGINCHATS_BASE,
    ORIGINCHATS_CHANNEL,
    ORIGINCHATS_MESSAGE_FILE,
    ORIGINCHATS_TOKEN,
    originchats_configured,
)
from music_activity.sinks.base import daemon_thread
from music_activity.state import PlayerState

MAX_TEXT = 1900
IDLE_TEXT = "🎵 Nothing playing"


def render_text(state: PlayerState) -> str:
    """Markdown is rendered by the originChats client's message renderer."""
    if not state.track:
        return IDLE_TEXT
    t = state.track
    lines = [f"**{t.title}** — {t.artist}".strip(" —")]
    meta = " · ".join(x for x in (state.status_line(), state.playthrough_text()) if x)
    if meta:
        lines.append(meta)
    if t.url:
        lines.append(t.url)
    return "\n".join(lines)[:MAX_TEXT]


class OriginChatsSink:
    def __init__(
        self,
        base: str = "",
        token: str = "",
        channel: str = "",
        *,
        message_file: str = "",
        min_interval: float = 5.0,
        log=print,
    ) -> None:
        self.base = (base or ORIGINCHATS_BASE).rstrip("/")
        self.token = token or ORIGINCHATS_TOKEN
        self.channel = channel or ORIGINCHATS_CHANNEL
        self.message_file = message_file or ORIGINCHATS_MESSAGE_FILE
        self.min_interval = min_interval
        self.log = log
        self.message_id: str | None = self._load_id()
        self._q: queue.Queue = queue.Queue(maxsize=4)
        self._stop = threading.Event()
        self._last_sent = 0.0
        self._thread: threading.Thread | None = None

    def configured(self) -> bool:
        return bool(self.base and self.token and self.channel) or originchats_configured()

    # ── Sink API ─────────────────────────────────────────────────────────
    def connect(self) -> None:
        if not self.configured():
            raise RuntimeError("ORIGINCHATS_BASE/TOKEN/CHANNEL are not set")
        self._thread = daemon_thread("originchats-activity", self._run)

    def publish(self, state: PlayerState) -> None:
        self._put(("publish", state))

    def clear(self) -> None:
        self._put(("clear", None))

    def close(self) -> None:
        self._stop.set()
        self._put(("stop", None))
        if self._thread:
            self._thread.join(timeout=4)

    # ── message bookkeeping ──────────────────────────────────────────────
    def _load_id(self) -> str | None:
        try:
            with open(self.message_file, encoding="utf-8") as fh:
                return json.load(fh).get("message_id") or None
        except (OSError, ValueError):
            return None

    def _save_id(self) -> None:
        if not self.message_file:
            return
        try:
            os.makedirs(os.path.dirname(self.message_file), exist_ok=True)
            with open(self.message_file, "w", encoding="utf-8") as fh:
                json.dump({"message_id": self.message_id}, fh)
        except OSError as exc:
            self.log(f"originchats: could not save message id: {exc}")

    def _request(self, method: str, path: str, body: dict | None = None):
        return requests.request(
            method,
            f"{self.base}{path}",
            json=body,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=20,
        )

    def _write(self, text: str) -> None:
        text = text[:MAX_TEXT]
        if self.message_id:
            resp = self._request(
                "PATCH", f"/channels/{self.channel}/messages/{self.message_id}",
                {"content": text},
            )
            if resp.status_code == 404:
                self.message_id = None
                self._save_id()
            elif resp.status_code >= 400:
                raise RuntimeError(f"PATCH message -> {resp.status_code}: {resp.text[:160]}")
            else:
                return
        resp = self._request(
            "POST", f"/channels/{self.channel}/messages", {"content": text}
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"POST message -> {resp.status_code}: {resp.text[:160]}")
        try:
            self.message_id = str(resp.json().get("id") or "") or None
        except ValueError:
            self.message_id = None
        self._save_id()

    # ── worker ───────────────────────────────────────────────────────────
    def _run(self) -> None:
        while not self._stop.is_set():
            kind, state = self._q.get()
            if kind == "stop":
                return
            wait = self.min_interval - (time.time() - self._last_sent)
            if wait > 0 and self._stop.wait(wait):
                return
            try:
                if kind == "clear":
                    self._write(IDLE_TEXT)
                else:
                    assert state is not None
                    self._write(render_text(state))
                self._last_sent = time.time()
            except Exception as exc:  # noqa: BLE001 - never take the player down
                self.log(f"originchats: {exc}")

    def _put(self, item) -> None:
        try:
            self._q.put_nowait(item)
        except queue.Full:
            try:
                self._q.get_nowait()
                self._q.put_nowait(item)
            except (queue.Empty, queue.Full):
                pass
