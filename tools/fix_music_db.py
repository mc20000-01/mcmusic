#!/usr/bin/env python3
"""
fix_music_db.py — Clean up music library filenames and metadata.

Scans the music directory, normalizes filenames (strips leading track numbers
and " - " prefixes so files are just "<Song Name>.ext"), writes extracted
metadata to sidecar JSON files and/or embeds it into file tags, and syncs
the mcmusic SQLite database.

Usage:
  python tools/fix_music_db.py [--music-dir /path/to/music] [--data-dir /path/to/data] [--dry-run] [--embed] [--rename]
  python tools/fix_music_db.py --fix-albums [--dry-run]

--fix-albums rewrites album tags in place so each track carries its real album
(from the <track>.yt.json sidecar the downloader wrote) instead of the name of
the playlist folder it was downloaded into. Tracks that have no album of their
own get the song name, per library convention.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime

try:
    from mutagen import File
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
except ImportError:
    print("mutagen is required: pip install mutagen")
    sys.exit(1)

MUSIC_DIR = os.environ.get("MUSIC_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "music"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "mcmusic.db")

AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".opus", ".flac", ".wav", ".webm", ".ogg"}

# Matches "NN - Title.ext" or "Title.ext"
FILENAME_RE = re.compile(r"^(?:(\d+)\s*[-–]\s*)?(.+?)$")


def parse_filename(filename):
    """Return (track_number_or_None, song_name, extension)."""
    base, ext = os.path.splitext(filename)
    m = FILENAME_RE.match(base)
    if not m:
        return None, base, ext
    track_no = int(m.group(1)) if m.group(1) else None
    song_name = m.group(2).strip()
    return track_no, song_name, ext


def read_tags(path):
    """Read existing metadata from audio file."""
    try:
        f = File(path, easy=True)
        if f is None:
            return {}
        tags = {}
        for key in ("title", "artist", "album", "genre", "date", "tracknumber"):
            if key in f:
                v = f[key]
                tags[key] = v[0] if isinstance(v, list) else v
        return tags
    except Exception:
        return {}


def read_yt_album(path):
    """The real album the downloader recorded in <track>.yt.json, if any."""
    sidecar = os.path.splitext(path)[0] + ".yt.json"
    try:
        with open(sidecar, encoding="utf-8") as fh:
            data = json.load(fh)
        album = data.get("album") if isinstance(data, dict) else None
        return str(album).strip() if album else ""
    except (OSError, ValueError):
        return ""


def set_album_tag(path, album):
    """Set only the album tag, leaving every other tag/stream untouched."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".mp3":
            try:
                f = ID3(path)
            except ID3NoHeaderError:
                f = ID3()
            f["TALB"] = TALB(encoding=3, text=album)
            f.save(path)
        elif ext in (".m4a", ".aac", ".mp4"):
            f = MP4(path)
            if f.tags is None:
                f.add_tags()
            f.tags["\xa9alb"] = [album]
            f.save()
        elif ext == ".flac":
            f = FLAC(path)
            f["album"] = [album]
            f.save()
        else:
            f = File(path, easy=True)
            if f is None:
                return False
            if f.tags is None:
                f.add_tags()
            f["album"] = [album]
            f.save()
        return True
    except Exception as e:
        print(f"  [WARN] could not write album to {path}: {e}")
        return False


def pick_album(root, title, current, yt_album):
    """Real album if we know one; otherwise the song name -- never the folder.

    The folder a download lands in is the playlist it came from, so it only
    counts as an album value when it has already been replaced by something
    that is not the folder name.
    """
    folder = os.path.basename(root)
    if yt_album:
        return yt_album
    current = (current or "").strip()
    if current and current != folder:
        return current
    return (title or "").strip()


def fix_albums(music_dir, db_path, dry_run):
    """Rewrite album tags/DB rows so they are the track's real album."""
    conn = sqlite3.connect(db_path)
    checked = fixed = kept = failed = db_updated = 0
    shown = 0
    for root, dirs, files in os.walk(music_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() not in AUDIO_EXTS:
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, music_dir)
            checked += 1
            existing = read_tags(full)
            _track_no, song_name, _ext = parse_filename(f)
            title = (existing.get("title") or song_name or "").strip()
            current = (existing.get("album") or "").strip()
            desired = pick_album(root, title, current, read_yt_album(full))
            if not desired or desired == current:
                kept += 1
                continue
            if shown < 20:
                print(f"  ALBUM: {rel}\n         {current or '(none)'} -> {desired}")
                shown += 1
                if shown == 20:
                    print("  ... (further changes are counted, not listed)")
            if dry_run:
                fixed += 1
                continue
            if not set_album_tag(full, desired):
                failed += 1
                continue
            fixed += 1
            try:
                cur = conn.execute(
                    "update tracks set album=?, mtime=? where path=?",
                    (desired, os.path.getmtime(full), rel),
                )
                db_updated += max(cur.rowcount, 0)
            except sqlite3.Error as e:
                print(f"  [WARN] db row for {rel} not updated: {e}")
    if not dry_run:
        conn.commit()
    conn.close()
    verb = "would fix" if dry_run else "fixed"
    print(f"\nAlbums: {checked} file(s) checked, {fixed} {verb}, {kept} already correct, "
          f"{failed} failed, {db_updated} db row(s) updated." +
          ("\nDRY RUN: no files were modified." if dry_run else ""))
    return fixed, failed


def write_tags(path, metadata):
    """Embed metadata into audio file tags."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".mp3":
            try:
                f = ID3(path)
            except ID3NoHeaderError:
                f = ID3()
            for frame, key in (("TIT2", "title"), ("TPE1", "artist"), ("TALB", "album"),
                               ("TCON", "genre"), ("TDRC", "date"), ("TRCK", "tracknumber")):
                if key in metadata:
                    cls = {"TIT2": TIT2, "TPE1": TPE1, "TALB": TALB,
                           "TCON": TCON, "TDRC": TDRC, "TRCK": TRCK}[frame]
                    f[frame] = cls(encoding=3, text=str(metadata[key]))
            f.save(path)
        elif ext in (".m4a", ".aac"):
            f = MP4(path)
            if "title" in metadata:
                f.tags["\xa9nam"] = metadata["title"]
            if "artist" in metadata:
                f.tags["\xa9ART"] = metadata["artist"]
            if "album" in metadata:
                f.tags["\xa9alb"] = metadata["album"]
            if "genre" in metadata:
                f.tags["\xa9gen"] = metadata["genre"]
            if "date" in metadata:
                f.tags["\xa9day"] = metadata["date"]
            if "tracknumber" in metadata:
                f.tags["trkn"] = [(int(metadata["tracknumber"]), 0)]
            f.save()
        elif ext == ".flac":
            f = FLAC(path)
            if "title" in metadata:
                f["title"] = metadata["title"]
            if "artist" in metadata:
                f["artist"] = metadata["artist"]
            if "album" in metadata:
                f["album"] = metadata["album"]
            if "genre" in metadata:
                f["genre"] = metadata["genre"]
            if "date" in metadata:
                f["date"] = metadata["date"]
            if "tracknumber" in metadata:
                f["tracknumber"] = str(metadata["tracknumber"])
            f.save()
        return True
    except Exception as e:
        print(f"  [WARN] could not write tags to {path}: {e}")
        return False


def write_sidecar(path, metadata):
    """Write metadata to a sidecar .json file."""
    sidecar = os.path.splitext(path)[0] + ".meta.json"
    try:
        with open(sidecar, "w") as fh:
            json.dump(metadata, fh, indent=2)
        return True
    except Exception as e:
        print(f"  [WARN] could not write sidecar {sidecar}: {e}")
        return False


def sync_database(conn, music_dir, updates):
    """Update tracks table with cleaned names/paths."""
    for upd in updates:
        old_path = upd["old_path"]
        new_path = upd["new_path"]
        title = upd["title"]
        track_no = upd.get("track_no")
        artist = upd.get("artist", "Unknown Artist")
        album = upd.get("album") or title

        conn.execute(
            """insert into tracks(path,title,artist,album,track_no,genre,year,duration,mtime,added)
               values(?,?,?,?,?,?,?,?,?,?)
               on conflict(path) do update set
                 title=excluded.title, artist=excluded.artist, album=excluded.album,
                 track_no=excluded.track_no, genre=excluded.genre, year=excluded.year,
                 duration=excluded.duration, mtime=excluded.mtime""",
            (new_path, title, artist, album, track_no, upd.get("genre", ""),
             upd.get("year", ""), upd.get("duration", 0.0),
             os.path.getmtime(os.path.join(music_dir, new_path)) if os.path.exists(os.path.join(music_dir, new_path)) else 0,
             time.time()),
        )

        # Remove old entry if path changed
        if old_path != new_path:
            conn.execute("delete from tracks where path=?", (old_path,))

    conn.commit()


def main():
    ap = argparse.ArgumentParser(description="Clean up music library filenames and metadata.")
    ap.add_argument("--music-dir", default=MUSIC_DIR, help="Music library directory")
    ap.add_argument("--data-dir", default=DATA_DIR, help="Data directory (contains mcmusic.db)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change without modifying anything")
    ap.add_argument("--embed", action="store_true", help="Embed metadata into file tags (ID3/MP4/FLAC)")
    ap.add_argument("--sidecar", action="store_true", default=True, help="Write sidecar .meta.json files (default: on)")
    ap.add_argument("--no-sidecar", action="store_true", help="Disable sidecar metadata files")
    ap.add_argument("--rename", action="store_true", help="Rename files on disk to <Song Name>.ext")
    ap.add_argument("--db-only", action="store_true", help="Only sync database, don't touch files")
    ap.add_argument("--fix-albums", action="store_true",
                    help="Rewrite album tags in place: real album from the .yt.json sidecar, "
                         "else the song name (never the playlist folder the track was downloaded into)")
    args = ap.parse_args()

    music_dir = os.path.abspath(args.music_dir)
    data_dir = os.path.abspath(args.data_dir)
    db_path = os.path.join(data_dir, "mcmusic.db")

    if not os.path.isdir(music_dir):
        print(f"ERROR: music dir not found: {music_dir}")
        sys.exit(1)
    if not os.path.exists(db_path):
        print(f"ERROR: database not found: {db_path}")
        sys.exit(1)

    if args.fix_albums:
        fix_albums(music_dir, db_path, args.dry_run)
        return

    write_sidecar = args.sidecar and not args.no_sidecar

    print(f"Scanning {music_dir}...")
    updates = []
    files_scanned = 0
    files_renamed = 0
    files_tagged = 0
    files_sidecar = 0

    for root, dirs, files in os.walk(music_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in AUDIO_EXTS:
                continue

            files_scanned += 1
            full = os.path.join(root, f)
            rel = os.path.relpath(full, music_dir)

            track_no, song_name, file_ext = parse_filename(f)

            # Determine new filename
            if args.rename and not args.db_only:
                new_filename = f"{song_name}{file_ext}"
                new_full = os.path.join(root, new_filename)
                if new_full != full and os.path.exists(new_full):
                    # Avoid collision: add track number suffix
                    new_filename = f"{song_name} [{track_no or ''}]{file_ext}"
                    new_full = os.path.join(root, new_filename)
                new_rel = os.path.relpath(new_full, music_dir)
            else:
                new_rel = rel

            # Build metadata from existing tags + filename
            existing = read_tags(full)
            metadata = {
                "original_filename": f,
                "song_name": song_name,
                "track_number": track_no,
                "title": existing.get("title") or song_name,
                "artist": existing.get("artist") or "Unknown Artist",
                "album": existing.get("album") or read_yt_album(full) or song_name,
                "genre": existing.get("genre") or "",
                "year": existing.get("date") or "",
            }

            updates.append({
                "old_path": rel,
                "new_path": new_rel,
                "title": metadata["title"],
                "track_no": track_no,
                "artist": metadata["artist"],
                "album": metadata["album"],
                "genre": metadata["genre"],
                "year": metadata["year"],
            })

            # Rename file on disk
            if args.rename and not args.db_only and new_full != full:
                try:
                    os.rename(full, new_full)
                    files_renamed += 1
                    print(f"  RENAME: {rel} -> {new_rel}")
                except OSError as e:
                    print(f"  [ERROR] rename failed {rel}: {e}")

            # Embed tags
            if args.embed and not args.db_only:
                target = new_full if (args.rename and new_full != full) else full
                if write_tags(target, metadata):
                    files_tagged += 1
                    print(f"  TAGS:   {os.path.relpath(target, music_dir)}")

            # Sidecar
            if write_sidecar and not args.db_only:
                target = new_full if (args.rename and new_full != full) else full
                if write_sidecar(target, metadata):
                    files_sidecar += 1
                    print(f"  SIDECAR: {os.path.splitext(target)[0]}.meta.json")

    if args.dry_run:
        print(f"\nDRY RUN: {files_scanned} files scanned, {len(updates)} would be updated.")
        print("No changes were made.")
        return

    # Sync database
    print(f"\nSyncing database {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=wal")
    conn.execute("pragma foreign_keys=on")

    # Ensure tracks table exists
    conn.execute("""create table if not exists tracks(
        id integer primary key, path text unique, title text, artist text,
        album text, track_no integer, genre text, year text, duration real,
        mtime real, added real, yt_id text, yt_likes integer, yt_views integer,
        yt_channel text, yt_date text, yt_checked real,
        explicit_auto integer default 0, explicit_ovr integer)""")
    conn.commit()

    sync_database(conn, music_dir, updates)
    conn.close()

    print(f"\nDone. {files_scanned} files scanned, {files_renamed} renamed, "
          f"{files_tagged} tagged, {files_sidecar} sidecars written.")


if __name__ == "__main__":
    main()
