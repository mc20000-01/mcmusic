"""Short-lived local cache of requested music videos.

The native app plays these files directly instead of embedding YouTube. A
request downloads its video into this cache next to the audio import; watching
slides the expiry forward by four hours, so frequently watched videos stay and
one-off views quietly disappear.

Only the cache index and the mp4 files live on disk. Nothing here makes a
prediction or influences the library, radio, queue or shuffle.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import threading
import time

from config import DATA_DIR
from song_meta import video_id

TTL_SECONDS = 4 * 60 * 60
MAX_BYTES = 400 * 1024 * 1024
VID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

CACHE_DIR = os.path.join(DATA_DIR, "video-cache")
INDEX_PATH = os.path.join(CACHE_DIR, "index.json")

_lock = threading.RLock()
_inflight: set[str] = set()
_index: dict[str, dict] | None = None
_log = logging.getLogger(__name__)


def _load() -> dict[str, dict]:
    global _index
    if _index is None:
        try:
            with open(INDEX_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _index = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _index = {}
    return _index


def _save() -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = INDEX_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(_index or {}, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, INDEX_PATH)


def _path(vid: str) -> str:
    return os.path.join(CACHE_DIR, f"{vid}.mp4")


def _partial(vid: str) -> str:
    return os.path.join(CACHE_DIR, f"{vid}.part.mp4")


def _valid(vid: str) -> bool:
    return bool(VID_RE.fullmatch(str(vid or "")))


def _track_info(vid: str) -> dict:
    """Best known title/artist for a video id, for the Videos list."""
    try:
        from database import _db
        c = _db()
        row = c.execute(
            "select id, title, artist from tracks where yt_id=? order by id limit 1", (vid,)
        ).fetchone() or c.execute(
            "select t.id, t.title, t.artist from track_sources s "
            "join tracks t on t.id=s.track_id where s.yt_id=? order by t.id limit 1", (vid,)
        ).fetchone()
        if row:
            return {"track_id": row["id"], "title": row["title"], "artist": row["artist"]}
    except Exception:
        pass
    return {"track_id": None, "title": "", "artist": ""}


def _entry(vid: str, entry: dict, state: str = "ready") -> dict:
    info = _track_info(vid)
    last = float(entry.get("last") or 0)
    return {
        "yt_id": vid,
        "state": state,
        "title": entry.get("title") or info["title"] or vid,
        "artist": entry.get("artist") or info["artist"],
        "track_id": info["track_id"],
        "last": last,
        "expires": last + TTL_SECONDS,
        "bytes": int(entry.get("bytes") or 0),
        "url": f"/video-cache/{vid}.mp4" if state == "ready" else None,
    }


def sweep() -> None:
    """Remove videos untouched for four hours (and their stale index rows)."""
    with _lock:
        index = _load()
        now = time.time()
        changed = False
        for vid, entry in list(index.items()):
            if not _valid(vid) or now - float(entry.get("last") or 0) > TTL_SECONDS:
                for path in (_path(vid), _partial(vid)):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                index.pop(vid, None)
                changed = True
        if changed:
            _save()


def status(vid: str, url: str = "", prepare: bool = False) -> dict:
    """Return cache state, optionally starting a background download."""
    if not _valid(vid):
        return {"yt_id": vid or "", "state": "missing", "title": "", "artist": "",
                "track_id": None, "last": 0, "expires": 0, "bytes": 0, "url": None}
    sweep()
    with _lock:
        index = _load()
        entry = index.get(vid)
        ready = bool(entry and os.path.isfile(_path(vid)) and os.path.getsize(_path(vid)) > 0)
        if ready:
            entry["last"] = time.time()
            _save()
            return _entry(vid, entry)
        if vid in _inflight:
            return _entry(vid, entry or {}, state="preparing")
        if prepare:
            _inflight.add(vid)
            threading.Thread(
                target=_download, args=(vid, url), name=f"video-cache-{vid}", daemon=True
            ).start()
            return _entry(vid, entry or {}, state="preparing")
    return _entry(vid, entry or {}, state="missing")


def touch(vid: str) -> None:
    """Called when a video is streamed; frequently watched copies survive."""
    if not _valid(vid):
        return
    with _lock:
        index = _load()
        entry = index.get(vid)
        if entry and os.path.isfile(_path(vid)):
            entry["last"] = time.time()
            _save()


def path(vid: str) -> str | None:
    """Resolved file path for an authenticated stream, or None."""
    if not _valid(vid) or not os.path.isfile(_path(vid)):
        return None
    touch(vid)
    return _path(vid)


def listing() -> list[dict]:
    """Ready videos, most recently watched first."""
    sweep()
    with _lock:
        rows = [
            _entry(vid, entry)
            for vid, entry in _load().items()
            if os.path.isfile(_path(vid))
        ]
    return sorted(rows, key=lambda row: row["last"], reverse=True)


def prepare_from_url(url: str) -> dict:
    """Cache the video behind a request URL once the audio import succeeds."""
    vid = video_id(url)
    if not vid:
        return {"yt_id": "", "state": "missing"}
    return status(vid, url=url, prepare=True)


def _download(vid: str, url: str) -> None:
    temp = _partial(vid)
    final = _path(vid)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        for stale in (temp, final):
            if os.path.exists(stale):
                os.remove(stale)
        target = url or f"https://www.youtube.com/watch?v={vid}"
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist", "--no-warnings", "--socket-timeout", "20",
            "--retries", "2", "--max-filesize", str(MAX_BYTES),
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", temp, target,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15 * 60)
        if proc.returncode != 0 or not os.path.isfile(temp) or os.path.getsize(temp) == 0:
            _log.warning("video cache %s failed: %s", vid, (proc.stderr or proc.stdout or "")[-500:])
            return
        if os.path.getsize(temp) > MAX_BYTES:
            _log.warning("video cache %s exceeded size limit", vid)
            return
        os.replace(temp, final)
        info = _track_info(vid)
        with _lock:
            index = _load()
            index[vid] = {
                "last": time.time(),
                "title": info["title"],
                "artist": info["artist"],
                "bytes": os.path.getsize(final),
            }
            _save()
    except Exception:
        _log.exception("video cache %s failed", vid)
    finally:
        with _lock:
            _inflight.discard(vid)
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except OSError:
                pass
