#!/usr/bin/env python3
"""Fold duplicate tracks into one row and keep every YouTube link on it.

Two files for the same song (two uploads, two links) become one library entry:
the extra file is moved to <music>/.dupes/ (recoverable, ignored by the
scanner) and its link is recorded in track_sources so the UI can offer both.

Matching is deliberately conservative: the same video id always merges, and
files merge when they share a normalised title + artist and a similar length.
Bracketed text that says what a version is -- "(English Cover)", "(Live)", a
remixer's name -- is kept, so a cover and the original never merge; only
brackets that just say "official video"/"lyrics" are ignored.

Every reference is re-pointed at the survivor before the duplicate row goes:
playlists, likes, plays, track artists, sources, the playback queue and the
track a device is currently on.

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

from config import DB_PATH, MUSIC_DIR
from artists import norm_key, split_artists
import song_meta

DURATION_SLACK = 5.0


def _row_get(row, key, default=None):
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def norm(value):
    """Matching key that keeps non-Latin titles and folds kana/romaji."""
    return norm_key(song_meta.match_text(value))


def _names(raw):
    try:
        value = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return [str(v) for v in value if str(v).strip()]


def artist_credit(row):
    """Every credited artist, from the indexed JSON or the raw tag."""
    return [n for n in (_names(_row_get(row, "artists")) or split_artists(
        _row_get(row, "artist", ""), _row_get(row, "title", ""))) if n]


def artist_key(row):
    """Order-insensitive key over the credited artists, not the raw credit blob."""
    keys = sorted({norm_key(n) for n in artist_credit(row) if norm_key(n)})
    return "|".join(keys) or norm(_row_get(row, "artist")) or "unknown"


def artist_overlap(a, b):
    """Two credits agree if they share a name; an unknown credit agrees with any.

    A file scanned before YouTube enrichment often has no artist at all. That
    is missing information, not a conflicting artist, so it must not stop a
    merge -- but two *different* named artists with the same title stay apart.
    """
    ka = {norm_key(n) for n in artist_credit(a) if norm_key(n)}
    kb = {norm_key(n) for n in artist_credit(b) if norm_key(n)}
    return not (ka and kb) or bool(ka & kb)


def duration_close(a, b):
    da, db = a["duration"] or 0, b["duration"] or 0
    return not (da and db and abs(da - db) > DURATION_SLACK)


def find_groups(rows):
    """Components of rows that describe the same recording."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    # 1) same YouTube video is the same recording, whatever the tags say.
    by_yt = {}
    for i, row in enumerate(rows):
        if row["yt_id"]:
            other = by_yt.setdefault(row["yt_id"], i)
            if other != i:
                union(i, other)

    # 2) same normalised title + artist, close length. An uncredited file is
    # allowed to merge with a credited one so a fresh rip can replace a row
    # that was indexed before its YouTube metadata arrived.
    by_key = {}
    for i, row in enumerate(rows):
        key = norm(row["title"])
        for j in by_key.get(key, []):
            if artist_overlap(row, rows[j]) and duration_close(row, rows[j]):
                union(i, j)
        by_key.setdefault(key, []).append(i)

    groups = {}
    for i in range(len(rows)):
        groups.setdefault(find(i), []).append(rows[i])
    return [sorted(items, key=lambda r: r["id"]) for items in groups.values() if len(items) > 1]


def richness(row):
    score = 0
    if row["yt_id"]:
        score += 4
    if row["lyrics"]:
        score += 2
    if row["genre"]:
        score += 1
    album = (row["album"] or "").strip()
    if album and album != (row["title"] or "").strip():
        score += 2
    return score


def survivor(bucket):
    """Keep the best-annotated row, not just the oldest one."""
    return sorted(bucket, key=lambda r: (-richness(r), r["id"]))[0]


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
    for side in (".lrc", ".yt.json", ".meta.json"):
        side_src = os.path.splitext(src)[0] + side
        if os.path.exists(side_src):
            try:
                shutil.move(side_src, os.path.splitext(dest)[0] + side)
            except OSError:
                pass
    return dest


def fill_missing(conn, keep, dup):
    """Copy annotations the survivor is missing from the duplicate."""
    updates = {}
    keep_album = (keep["album"] or "").strip()
    dup_album = (dup["album"] or "").strip()
    # Only take the duplicate's album when the survivor has none or is still
    # showing the song-name fallback.
    if (not keep_album or keep_album == (keep["title"] or "").strip()) \
            and dup_album and dup_album != (dup["title"] or "").strip():
        updates["album"] = dup_album
    for column in ("genre", "year", "lyrics", "lyrics_source", "yt_likes",
                   "yt_views", "yt_channel", "yt_date", "yt_tags", "themes"):
        if not keep[column] and dup[column]:
            updates[column] = dup[column]
    if not keep["duration"] and dup["duration"]:
        updates["duration"] = dup["duration"]
    if updates:
        sets = ", ".join(f"{k}=?" for k in updates)
        conn.execute(f"update tracks set {sets} where id=?", (*updates.values(), keep["id"]))


def repoint(conn, keep, dup):
    """Move every reference from the duplicate to the survivor."""
    # Playlists: keep the survivor's position when already present.
    conn.execute(
        "insert or ignore into playlist_tracks(playlist_id, track_id, pos) "
        "select playlist_id, ?, pos from playlist_tracks where track_id=?",
        (keep["id"], dup["id"]),
    )
    conn.execute("delete from playlist_tracks where track_id=?", (dup["id"],))

    # Likes and plays.
    conn.execute(
        "insert or ignore into likes(user_id, track_id, ts) select user_id, ?, ts from likes where track_id=?",
        (keep["id"], dup["id"]),
    )
    conn.execute("delete from likes where track_id=?", (dup["id"],))
    conn.execute("update plays set track_id=? where track_id=?", (keep["id"], dup["id"]))

    # All links live on the survivor.
    conn.execute(
        "insert or ignore into track_sources(track_id, yt_id, url, title, added) "
        "select ?, yt_id, url, title, added from track_sources where track_id=?",
        (keep["id"], dup["id"]),
    )
    conn.execute("delete from track_sources where track_id=?", (dup["id"],))

    # 'now playing' pointers, including queues stored as JSON lists.
    conn.execute("update playback set track_id=? where track_id=?", (keep["id"], dup["id"]))
    for pb in conn.execute("select user_id, queue from playback where queue is not null").fetchall():
        try:
            ids = json.loads(pb["queue"] or "[]")
        except (TypeError, ValueError):
            continue
        if dup["id"] in ids:
            merged = []
            for track_id in ids:
                real = keep["id"] if track_id == dup["id"] else track_id
                if real not in merged:
                    merged.append(real)
            conn.execute(
                "update playback set queue=? where user_id=?",
                (json.dumps(merged), pb["user_id"]),
            )
    conn.execute(
        "update devices set current_track_id=? where current_track_id=?", (keep["id"], dup["id"])
    )


def merge_artists(conn, keep, dup):
    names = _names(keep["artists"])
    seen = {n.casefold() for n in names}
    names += [n for n in _names(dup["artists"]) if n.casefold() not in seen]
    for pos, name in enumerate(names):
        conn.execute(
            "insert or ignore into track_artists(track_id, artist, artist_key, position) "
            "values(?,?,?,?)",
            (keep["id"], name, norm_key(name) or name.casefold(), pos),
        )
    if names:
        conn.execute("update tracks set artists=?, artist=? where id=?",
                     (json.dumps(names), ", ".join(names), keep["id"]))
    conn.execute("delete from track_artists where track_id=?", (dup["id"],))


def run(dry_run=True, quiet=False):
    def say(message):
        if not quiet:
            print(message)

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "select id, path, title, artist, artists, album, genre, year, duration, "
        "track_no, yt_id, yt_likes, yt_views, yt_channel, yt_date, lyrics, lyrics_source, "
        "yt_tags, themes from tracks order by id"
    ).fetchall()
    groups = find_groups(rows)
    folded = 0
    links = 0
    for bucket in groups:
        keep = survivor(bucket)
        for item in bucket:
            if item["id"] == keep["id"]:
                continue
            if item["yt_id"]:
                url = f"https://www.youtube.com/watch?v={item['yt_id']}"
                if dry_run:
                    links += 1
                else:
                    cur = conn.execute(
                        """insert or ignore into track_sources(track_id, yt_id, url, title, added)
                           values(?,?,?,?,?)""",
                        (keep["id"], item["yt_id"], url, item["title"], time.time()),
                    )
                    links += cur.rowcount
            say(f"  merge #{item['id']} {item['title']!r} -> #{keep['id']} {keep['title']!r}")
            if dry_run:
                folded += 1
                continue
            fill_missing(conn, keep, item)
            merge_artists(conn, keep, item)
            repoint(conn, keep, item)
            conn.execute("delete from tracks where id=?", (item["id"],))
            quarantine(item["path"])
            folded += 1
    if not dry_run:
        conn.commit()
    conn.close()
    verb = "would fold" if dry_run else "folded"
    say(f"{len(groups)} duplicate group(s) found; {verb} {folded} track(s), "
        f"{links} link(s) kept on the survivor.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Merge duplicate songs, keep all their links.")
    ap.add_argument("--dry-run", action="store_true", help="Report only, change nothing")
    args = ap.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
