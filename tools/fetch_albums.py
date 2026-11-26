#!/usr/bin/env python3
"""Restore real album names from YouTube, in place.

The old downloader overwrote every album tag with the playlist title, so the
real album only survived in the <track>.yt.json sidecar -- and most tracks
never got one. YouTube still has it for YouTube Music releases, so this walks
the tracks that are currently falling back to their song name and asks
yt-dlp for the album, then writes the tag, the DB row and (if one exists) the
sidecar.

Tracks without an album on the source are left as the song name.
Already-done ids are remembered in data/.album_fetch_done.json so a re-run
continues where the last one stopped.

    python tools/fetch_albums.py --dry-run --limit 20
    python tools/fetch_albums.py --workers 4
"""
import argparse
import json
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_music_db import DATA_DIR, MUSIC_DIR, set_album_tag  # noqa: E402

DB_PATH = os.path.join(DATA_DIR, "mcmusic.db")
DONE_PATH = os.path.join(DATA_DIR, ".album_fetch_done.json")

RATE_RE = ("429", "too many requests", "rate limit", "confirm you", "403", "not a bot")

YDLOPS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
    "socket_timeout": 20,
    "retries": 3,
}


def load_done():
    try:
        with open(DONE_PATH) as fh:
            data = json.load(fh)
        return set(int(v) for v in data) if isinstance(data, list) else set()
    except (OSError, ValueError):
        return set()


def save_done(done):
    tmp = DONE_PATH + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(sorted(done), fh)
    os.replace(tmp, DONE_PATH)


def merge_sidecar_album(path, album):
    """Keep an existing sidecar in sync so a rescan does not undo the fix.

    We never create a sidecar here: a stub without the video id would wipe the
    YouTube stats the scanner stores from it.
    """
    sidecar = os.path.splitext(path)[0] + ".yt.json"
    if not os.path.exists(sidecar):
        return False
    try:
        with open(sidecar, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    data["album"] = album
    tmp = sidecar + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, sidecar)
    return True


def fetch_album(yt_id):
    import yt_dlp
    with yt_dlp.YoutubeDL(YDLOPS) as ydl:
        info = ydl.extract_info("https://www.youtube.com/watch?v=" + yt_id, download=False)
    return info or {}


def main():
    ap = argparse.ArgumentParser(description="Fill real album names from YouTube, in place.")
    ap.add_argument("--music-dir", default=MUSIC_DIR)
    ap.add_argument("--data-dir", default=DATA_DIR)
    ap.add_argument("--limit", type=int, default=0, help="Only check this many tracks (0 = all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--track-id", type=int, action="append", default=None,
                    help="Only check these track ids (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db_path = os.path.join(os.path.abspath(args.data_dir), "mcmusic.db")
    music_dir = os.path.abspath(args.music_dir)
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}")
        return 1

    done = load_done()
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "select id, path, title, album, yt_id from tracks "
        "where yt_id is not null and (album is null or album = '' or album = title) "
        "order by id"
    )]
    rows = [r for r in rows if r["id"] not in done]
    if args.track_id:
        wanted = set(args.track_id)
        rows = [r for r in rows if r["id"] in wanted]
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} track(s) to check for a real album "
          f"({len(done)} already done).")
    if not rows:
        return 0

    lock = threading.Lock()
    blocked_until = 0.0
    failures = 0
    fixed = 0
    unchanged = 0
    missing_file = 0

    def work(row):
        nonlocal blocked_until, failures
        while True:
            with lock:
                wait = blocked_until - time.time()
            if wait <= 0:
                break
            time.sleep(min(2.0, wait))
        try:
            info = fetch_album(row["yt_id"])
            with lock:
                failures = 0
            return row, info
        except Exception as e:
            msg = str(e).lower()
            if any(token in msg for token in RATE_RE):
                with lock:
                    failures += 1
                    blocked_until = time.time() + min(600, 15 * failures)
                time.sleep(min(15, failures * 3))
            return row, None

    started = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(work, r) for r in rows]
        for n, fut in enumerate(as_completed(futures), 1):
            row, info = fut.result()
            album = str((info or {}).get("album") or "").strip()
            full = os.path.join(music_dir, row["path"])
            if not os.path.exists(full):
                missing_file += 1
            elif not album or album == (row["album"] or "").strip():
                unchanged += 1
            else:
                print(f"  [{row['id']}] {row['album']!r} -> {album!r}")
                if not args.dry_run:
                    if set_album_tag(full, album):
                        conn.execute(
                            "update tracks set album=?, mtime=? where id=?",
                            (album, os.path.getmtime(full), row["id"]),
                        )
                        merge_sidecar_album(full, album)
                        fixed += 1
                else:
                    fixed += 1
            with lock:
                done.add(row["id"])
            if not args.dry_run and n % 25 == 0:
                conn.commit()
                save_done(done)
                print(f"  ... {n}/{len(rows)} checked, {fixed} album(s) restored")
            if n % 25 == 0 and not args.dry_run:
                remaining = len(rows) - n
                rate = n / max(1.0, time.time() - started)
                print(f"      ~{rate:.1f}/s, ~{remaining / max(rate, 0.01):.0f}s left")

    if not args.dry_run:
        conn.commit()
        save_done(done)
    conn.close()
    verb = "would restore" if args.dry_run else "restored"
    print(f"\nDone: {verb} {fixed} album(s); {unchanged} had no album on the source, "
          f"{missing_file} file(s) missing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
