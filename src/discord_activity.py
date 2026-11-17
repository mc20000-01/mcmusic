"""Per-account Discord Rich Presence sessions.

Rich presence is published over Discord's local IPC socket, so this only works
when the Discord desktop client runs on the same host as mcmusic. The protocol
lives in ``music_activity/sinks/discord.py`` (also used by the desktop bridge);
this module keeps one sink per signed-in account so the web and Android clients
never import pypresence.
"""
from __future__ import annotations

import logging
import os
import sys
import threading

# ``src`` is on sys.path when gunicorn imports mcmusic; the shared activity
# package lives at the repository root.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from music_activity.sinks.discord import DiscordSink  # noqa: E402
from music_activity.state import PlayerState  # noqa: E402

log = logging.getLogger(__name__)

_sessions: dict[int, DiscordSink] = {}
_lock = threading.Lock()


# A Discord application is identified by one id; the bot deployment already
# stores it as DISCORD_APPLICATION_ID and the OAuth link as DISCORD_CLIENT_ID.
def app_id() -> str:
    for name in ("DISCORD_APP_ID", "DISCORD_APPLICATION_ID", "DISCORD_CLIENT_ID"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def configured() -> bool:
    return bool(app_id())


def client_running() -> bool:
    """Is a Discord desktop client alive on this host (signed in or not)?

    The IPC socket only appears once the client finishes signing in, so process
    presence is the only way to tell "not installed/running" from "not signed
    in yet" in the message the settings screen shows.
    """
    try:
        entries = os.listdir("/proc")
    except OSError:
        return False
    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/comm", encoding="utf-8") as fh:
                if fh.read().strip() == "Discord":
                    return True
        except OSError:
            continue
    return False


def available() -> tuple[bool, str]:
    """Can a presence be delivered from this host right now?

    The sink queues updates and retries in the background, so without this check
    a request would report success while nothing ever reached Discord.
    """
    if not app_id():
        return False, "no Discord application id is set (DISCORD_APP_ID or DISCORD_CLIENT_ID)"
    try:
        from pypresence.utils import get_ipc_path
    except Exception:  # noqa: BLE001 - pypresence is optional
        return False, "the 'pypresence' package is not installed"
    try:
        if get_ipc_path(0):
            return True, ""
    except Exception:  # noqa: BLE001
        # A socket left behind by a crashed client raises instead of returning
        # None; the process check below says more than a raw errno would.
        pass
    if client_running():
        return False, "the Discord client on this server is not signed in yet"
    return False, "Discord is not running on this server"


def state() -> dict:
    """What the settings screen needs to explain a toggle that cannot work."""
    usable, why = available()
    return {"configured": configured(), "available": usable, "reason": why}


def _new_sink(uid: int) -> DiscordSink:
    sink = DiscordSink(app_id(), log=lambda msg: log.info("discord[%s]: %s", uid, msg))
    sink.connect()
    return sink


def publish(uid: int, state: PlayerState) -> tuple[bool, str]:
    """Send a player state through the account's presence session."""
    with _lock:
        sink = _sessions.get(uid)
        if sink is None:
            try:
                sink = _new_sink(uid)
            except Exception as exc:  # noqa: BLE001 - surface a useful API error
                return False, f"Could not start Discord activity: {exc}"
            _sessions[uid] = sink
    sink.publish(state)
    return True, ""


def clear(uid: int) -> None:
    """Remove the activity if this account ever published one."""
    with _lock:
        sink = _sessions.get(uid)
    if sink is not None:
        sink.clear()


def close(uid: int) -> None:
    """Drop the session, clearing the presence it published."""
    with _lock:
        sink = _sessions.pop(uid, None)
    if sink is not None:
        sink.close()


__all__ = ["available", "clear", "close", "configured", "publish"]
