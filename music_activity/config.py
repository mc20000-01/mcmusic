"""Environment configuration for music_activity. Never log ROTUR_TOKEN."""
from __future__ import annotations

import os
import re

ROTUR_TOKEN = os.environ.get("ROTUR_TOKEN", "").strip()
ROTUR_ROOMS = [r.strip() for r in os.environ.get("ROTUR_ROOMS", "originChats").split(",") if r.strip()]
# originChats clients join `originChats:<server>` so that server's members see it.
ORIGINCHATS_SERVER = os.environ.get("ORIGINCHATS_SERVER", "").strip().rstrip("/")
ROTUR_WS = os.environ.get("ROTUR_WS", "wss://api.rotur.dev/v2/status/ws")
ROTUR_ACTIVITY_ID = os.environ.get("ROTUR_ACTIVITY_ID", "mcmusic")

ORIGINCHATS_BASE = os.environ.get("ORIGINCHATS_BASE", "").rstrip("/")
ORIGINCHATS_TOKEN = os.environ.get("ORIGINCHATS_TOKEN", "")
ORIGINCHATS_CHANNEL = os.environ.get("ORIGINCHATS_CHANNEL", "")
DISCORD_APP_ID = os.environ.get("DISCORD_APP_ID", "").strip()

MCMUSIC_BASE = os.environ.get("MCMUSIC_BASE", "https://mcmusic.sdisk.us").rstrip("/")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
ORIGINCHATS_MESSAGE_FILE = os.environ.get(
    "ORIGINCHATS_MESSAGE_FILE", os.path.join(DATA_DIR, "music_activity_originchats.json")
)
MCMUSIC_USER_ID = os.environ.get("MCMUSIC_USER_ID", "")

ROOM_RE = re.compile(r"^[a-zA-Z0-9_\-:.]+$")


def valid_rooms(rooms: list[str]) -> list[str]:
    """Return only names Rotur accepts (1-64 chars); one bad name fails a join."""
    good = [r for r in rooms if 0 < len(r) <= 64 and ROOM_RE.match(r)]
    return good or ["originChats"]


def rotur_rooms() -> list[str]:
    """Base rooms plus the originChats server room when one is configured."""
    rooms = list(ROTUR_ROOMS)
    if ORIGINCHATS_SERVER:
        room = f"originChats:{ORIGINCHATS_SERVER}"
        if room not in rooms:
            rooms.append(room)
    return valid_rooms(rooms)


def originchats_configured() -> bool:
    return bool(ORIGINCHATS_BASE and ORIGINCHATS_TOKEN and ORIGINCHATS_CHANNEL)
