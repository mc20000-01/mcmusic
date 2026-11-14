"""Lyrics lookup (LRCLIB) + a gentle backfill for the existing library.

Lyrics live on `tracks.lyrics` / `tracks.lyrics_source`; the scanner already
imports sidecar files, so this only fills the gaps. LRCLIB is free and needs no
key; keep the backfill slow (one request every ~0.4 s) so we stay a good guest.
"""
from __future__ import annotations

import sqlite3
import threading
import time

import requests

from config import DB_PATH

BASE = "https://lrclib.net/api"
UA = {"User-Agent": "mcmusic/1.0 (https://mcmusic.sdisk.us)"}

_state = {"running": False, "done": 0, "failed": 0, "total": 0}
_lock = threading.Lock()


def lookup(title: str, artist: str, duration=None, album: str = "") -> tuple[str, str] | None:
    if not title:
        return None
    params = {"track_name": title, "artist_name": artist or ""}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = int(duration)
    try:
        r = requests.get(f"{BASE}/get", params=params, headers=UA, timeout=12)
        if r.status_code == 200:
            d = r.json()
            synced = d.get("syncedLyrics")
            plain = d.get("plainLyrics")
            if synced:
                return synced, "lrclib-synced"
            if plain:
                return plain, "lrclib"
    except requests.RequestException:
        pass
    try:
        r = requests.get(f"{BASE}/search", params={"q": f"{title} {artist}".strip()},
                         headers=UA, timeout=12)
        if r.status_code == 200:
            for d in r.json() or []:
                if d.get("syncedLyrics"):
                    return d["syncedLyrics"], "lrclib-synced"
                if d.get("plainLyrics"):
                    return d["plainLyrics"], "lrclib"
    except requests.RequestException:
        pass
    return None


def save(track_id: int, text: str, source: str) -> None:
    c = sqlite3.connect(DB_PATH, timeout=10)
    try:
        c.execute("update tracks set lyrics=?, lyrics_source=? where id=?",
                  (text, source, track_id))
        c.commit()
    finally:
        c.close()


def status() -> dict:
    with _lock:
        return dict(_state)


def start_backfill(limit: int = 500) -> bool:
    """Fetch missing lyrics in a daemon thread. False if already running."""
    with _lock:
        if _state["running"]:
            return False
        _state.update(running=True, done=0, failed=0, total=0)
    threading.Thread(target=_backfill, args=(limit,), name="lyrics-backfill", daemon=True).start()
    return True


def _backfill(limit: int) -> None:
    try:
        c = sqlite3.connect(DB_PATH, timeout=10)
        rows = c.execute(
            "select id, title, artist, album, duration from tracks"
            " where lyrics is null or trim(lyrics)='' order by id limit ?", (limit,)
        ).fetchall()
        c.close()
        with _lock:
            _state["total"] = len(rows)
        for tid, title, artist, album, duration in rows:
            found = lookup(title or "", artist or "", duration, album or "")
            if found:
                save(tid, found[0], found[1])
                with _lock:
                    _state["done"] += 1
            else:
                with _lock:
                    _state["failed"] += 1
            time.sleep(0.4)
    finally:
        with _lock:
            _state["running"] = False


if __name__ == "__main__":
    import os

    limit = int(os.environ.get("LYRICS_LIMIT", "2000"))
    print(f"lyrics backfill: up to {limit} tracks", flush=True)
    start_backfill(limit)
    while status()["running"]:
        time.sleep(2)
    print(f"lyrics backfill finished: {status()}", flush=True)
