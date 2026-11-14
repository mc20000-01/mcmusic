"""Per-account Rotur activity sessions.

Rotur's status WebSocket protocol is already implemented and live-tested in
``music_activity/sinks/rotur.py``. This module keeps one sink per signed-in
account so the web/Android clients never speak the socket protocol directly.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from typing import Callable, Optional

# ``src`` is on sys.path when gunicorn imports mcmusic; the shared activity
# package lives at the repository root.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from music_activity.sinks.rotur import RoturFatal, RoturSink  # noqa: E402
from music_activity.state import PlayerState  # noqa: E402

log = logging.getLogger(__name__)

_sessions: dict[int, RoturSink] = {}
_lock = threading.Lock()


def _new_sink(uid: int, token_provider: Callable[[], Optional[str]]) -> RoturSink:
    sink = RoturSink(
        "",
        ["originChats"],
        token_provider=token_provider,
        app_name="mcmusic",
        app_url=os.environ.get("PUBLIC_URL", "https://mcmusic.sdisk.us").rstrip("/"),
        log=lambda msg: log.info("rotur[%s]: %s", uid, msg),
    )
    sink.connect()
    return sink


def publish(uid: int, state: PlayerState, token_provider: Callable[[], Optional[str]]):
    """Publish a player state through the account's long-lived socket.

    A sink whose thread has exited (expired token, revoked scope, dropped
    account) is replaced instead of silently accepting updates forever.
    """
    stale: Optional[RoturSink] = None
    with _lock:
        sink = _sessions.get(uid)
        if sink is not None and not sink.running:
            stale = _sessions.pop(uid, None)
            sink = None
        if sink is None:
            sink = _new_sink(uid, token_provider)
            _sessions[uid] = sink
    if stale is not None:
        stale.close()
    sink.publish(state)


def clear(uid: int, token_provider: Callable[[], Optional[str]]):
    """Remove the activity if this account ever opened a session.

    Do not create a socket just to clear an activity that was never published;
    a signed-out or paused account would otherwise spin a failing reconnect.
    """
    stale: Optional[RoturSink] = None
    with _lock:
        sink = _sessions.get(uid)
        if sink is not None and not sink.running:
            stale = _sessions.pop(uid, None)
            sink = None
    if stale is not None:
        stale.close()
    elif sink is not None:
        sink.clear()


def close(uid: int):
    """Close the socket and drop the session, removing its activity."""
    with _lock:
        sink = _sessions.pop(uid, None)
    if sink is not None:
        sink.close()


__all__ = ["RoturFatal", "clear", "close", "publish"]
