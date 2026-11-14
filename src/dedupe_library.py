#!/usr/bin/env python3
"""Fold duplicate tracks into one row and keep every YouTube link on it.

Two files for the same song (two uploads, two links) become one library entry:
the extra file is moved to <music>/.dupes/ (recoverable, ignored by the
scanner) and its link is recorded in track_sources so the UI can offer both.

    python src/dedupe_library.py --dry-run     # show what would merge
    python src/dedupe_library.py               # merge for real
"""
import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import unicodedata

from config import DB_PATH, MUSIC_DIR

BRACKETS_RE = re.compile(r"[\(\[\{][^\)\]\}]*[\)\]\}]")
FEAT_RE = re.compile(r"\b(?:feat|ft|featuring)\.?\s+.*$", re.I)
JUNK_RE = re.compile(r"\b(?:official|video|audio|lyrics?|hd|hq|remaster(?:ed)?|mv|m/?v)\b", re.I)
WORD_RE = re.compile(r"[^a-z0-9]+")
DURATION_SLACK = 3.0


def norm(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode()
    text = text.lower()
    text = BRACKETS_RE.sub(" ", text)
    text = FEAT_RE.sub(" ", text)
    text = JUNK_RE.sub(" ", text)
    return WORD_RE.sub(" ", text).strip()


def key_for(row):
    return (norm(row["title"]), norm(row["artist"]) or "unknown")


def find_groups(rows):
    """Rows that describe the same song: same normalised name and close length."""
    buckets = {}
    for row in rows:
        buckets.setdefault(key_for(row), []).append(row)
    groups = []
    for items in buckets.values():
        if len(items) < 2:
            continue
        items.sort(key=lambda r: r["id"])
        used = set()
        for i, head in enumerate(items):
            if head["id"] in used:
                continue
            used.add(head["id"])
            bucket = [head]
            for other in items[i + 1:]:
                if other["id"] in used:
                    continue
                a, b = head["duration"] or 0, other["duration"] or 0
                if a and b and abs(a - b) > DURATION_SLACK:
                    continue
                bucket.append(other)
                used.add(other["id"])
            if len(bucket) > 1:
                groups.append(bucket)
    return groups


def _names(raw):
    try:
        value = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return [str(v) for v in value if str(v).strip()]


def quarantine(rel_path):
    """Move a duplicate file out of the library instead of deleting it."""
    src = os.path.join(MUSIC_DIR, rel_path)
    if not os.path.exists(src):
        return None
    dest = os.path.join(MUSIC_DIR, ".dupes", rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    base, ext = os.path.splitext(dest)
    n = 1
    while os.path.exists(dest):
        dest = f"{base}.{n}{ext}"
        n += 1
    try:
        shutil.move(src, dest)
    except OSError as e:
        print(f"  ! could not move {rel_path}: {e}", file=sys.stderr)
        return None
    for side in (".lrc", ".yt.json"):
        side_src = os.path.splitext(src)[0] + side
        if os.path.exists(side_src):
            try:
                shutil.move(side_src, os.path.splitext(dest)[0] + side)
            except OSError:
                pass
    return dest


def run(dry_run=True):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "select id, path, title, artist, artists, duration, yt_id from tracks order by id"
    ).fetchall()
    groups = find_groups(rows)
    folded = 0
    links = 0
    for bucket in groups:
        keep = bucket[0]
        for item in bucket:
            if not item["yt_id"]:
                continue
            url = f"https://www.youtube.com/watch?v={item['yt_id']}"
            if dry_run:
                links += 1
                continue
            cur = conn.execute(
                """insert or ignore into track_sources(track_id, yt_id, url, title, added)
                   values(?,?,?,?,?)""",
                (keep["id"], item["yt_id"], url, item["title"], time.time()),
            )
            links += cur.rowcount
        for dup in bucket[1:]:
            print(f"  merge #{dup['id']} {dup['title']!r} -> #{keep['id']}")
            if dry_run:
                folded += 1
                continue
            # A collab credit on either file belongs to the survivor.
            names = _names(keep["artists"]) + [
                n for n in _names(dup["artists"]) if n.casefold() not in
                {x.casefold() for x in _names(keep["artists"])}
            ]
            conn.execute("update tracks set artists=? where id=?",
                         (json.dumps(names), keep["id"]))
            for pos, name in enumerate(names):
                conn.execute(
                    "insert or ignore into track_artists(track_id, artist, position) "
                    "values(?,?,?)",
                    (keep["id"], name, pos),
                )
            conn.execute("delete from track_artists where track_id=?", (dup["id"],))
            conn.execute(
                "insert or ignore into likes(user_id, track_id, ts) "
                "select user_id, ?, ts from likes where track_id=?",
                (keep["id"], dup["id"]),
            )
            conn.execute("update plays set track_id=? where track_id=?", (keep["id"], dup["id"]))
            conn.execute("delete from tracks where id=?", (dup["id"],))
            quarantine(dup["path"])
            folded += 1
    if not dry_run:
        conn.commit()
    conn.close()
    verb = "would fold" if dry_run else "folded"
    print(f"{len(groups)} duplicate group(s) found; {verb} {folded} track(s), "
          f"{links} link(s) kept on the survivor.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Merge duplicate songs, keep all their links.")
    ap.add_argument("--dry-run", action="store_true", help="Report only, change nothing")
    args = ap.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
