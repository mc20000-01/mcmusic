#!/usr/bin/env python3
"""Import audio files from ZIP archives into the server library.

The puller normally writes tracks itself from a YouTube URL. This module is
the other half: it takes MP3s that already exist on disk (often inside a zip),
reads their tags/filename, finds the matching YouTube video by the embedded
purl or by artist + song name, saves the YouTube metadata as a .yt.json
sidecar, then runs the normal scan so dedupe and enrichment see a normal track.

Everything here runs on the server; no client changes are needed.

    python tools/import_zip.py tracks.zip --dry-run
    python tools/import_zip.py tracks.zip
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import zipfile

from config import DB_PATH, DATA_DIR, MUSIC_DIR, AUDIO_EXTS
from library_scan import read_tags, read_yt_id, scan_library
from artists import norm_key
import song_meta

CACHE_PATH = os.path.join(DATA_DIR, ".zip_import_done.json")
_UNSAFE = re.compile(r"[^\w\s\-\.\(\)\[\]_,+&'’]+", re.UNICODE)


def say(message, quiet=False):
    if not quiet:
        print(message, flush=True)


def safe_name(name):
    """A ZIP member name reduced to a safe basename (no traversal, no drive)."""
    name = os.path.basename(str(name or "").replace("\\", "/")).strip()
    name = _UNSAFE.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or None


UNKNOWN_ARTISTS = {"", "unknown", "unknown artist", "unknownartist"}


def has_artist(artists):
    return any(str(n).strip().casefold() not in UNKNOWN_ARTISTS for n in (artists or []))


def filename_meta(rel):
    """Best-effort 'Artist - Song' fallback for files with no useful tags."""
    stem = os.path.splitext(os.path.basename(rel))[0]
    text = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()
    text = re.sub(r"^\d{1,3}\s*-\s*", "", text)
    if " - " in text:
        artist, title = text.split(" - ", 1)
        return title.strip(), artist.strip()
    return text, ""


def clean_meta(title, artist, genre="", info=None, rel=None):
    """Parse tags, falling back to the filename, then to YouTube metadata."""
    meta = song_meta.parse_song_meta(title, artist=artist, genre=genre)
    if not has_artist(meta["artists"]):
        file_title, file_artist = filename_meta(rel or title)
        meta = song_meta.parse_song_meta(file_title or title, artist=file_artist, genre=genre)
    if info:
        meta = song_meta.parse_song_meta(
            info.get("title") or meta["raw_title"] or title,
            artist=info.get("artist") or (meta["artists"][0] if meta["artists"] else artist),
            creator=info.get("creator"),
            uploader=info.get("uploader"),
            channel=info.get("channel"),
            description=info.get("description"),
            tags=info.get("tags"),
            categories=info.get("categories"),
            genre=genre or info.get("genre") or "",
        )
    return meta


def load_cache():
    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return set(data) if isinstance(data, list) else set()
    except (OSError, ValueError):
        return set()


def save_cache(done):
    tmp = CACHE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(sorted(done), fh, indent=1)
    os.replace(tmp, CACHE_PATH)


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def folder_for(conn, title, artists):
    """Reuse an existing artist folder, or make one under Zip Imports/."""
    if artists:
        row = conn.execute(
            "select path from tracks where instr(artists, ?) > 0 order by id limit 1",
            (artists[0],),
        ).fetchone()
        if row and os.path.dirname(row["path"]):
            return os.path.dirname(row["path"])
        return os.path.join("Zip Imports", safe_name(artists[0]) or "Unknown Artist")
    return os.path.join("Zip Imports", safe_name(title) or "Unknown")


def video_info(yt_id, timeout=20):
    """Full yt-dlp metadata for one known video id."""
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "skip_download": True,
            "noplaylist": True, "socket_timeout": timeout}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info("https://www.youtube.com/watch?v=" + yt_id,
                                download=False)


def search_video(title, artists, timeout=15):
    """Find a video id from the song name and credited artist(s).

    An embedded purl is better and is always preferred; this is the fallback
    for plain rips that only carry title/artist tags.
    """
    import yt_dlp
    query = " ".join(filter(None, [(artists[0] if artists else ""), title])).strip()
    if not query:
        return None
    opts = {"quiet": True, "no_warnings": True, "skip_download": True,
            "extract_flat": True, "playlistend": 3, "socket_timeout": timeout}
    with yt_dlp.YoutubeDL(opts) as ydl:
        found = ydl.extract_info("ytsearch3:" + query, download=False)
    entries = [e for e in (found or {}).get("entries", []) if e and e.get("id")]
    if not entries:
        return None
    target = norm_key(song_meta.clean_title(title))
    target_words = set(target.split())

    def rank(entry):
        name = norm_key(song_meta.clean_title(entry.get("title") or ""))
        words = set(name.split())
        overlap = len(target_words & words) / max(1, len(target_words))
        return (0 if name == target else 1, -overlap, -(entry.get("view_count") or 0))

    return sorted(entries, key=rank)[0]["id"]


def write_sidecar(full, yt_id, info, title, artist):
    """Write the .yt.json the scanner already understands."""
    from yt_playlist_to_mp3 import write_yt_sidecar
    data = dict(info or {})
    data.setdefault("id", yt_id)
    data.setdefault("title", title)
    data.setdefault("artist", artist)
    return write_yt_sidecar(full, data)


def extract_members(zip_path, conn, quiet=False, dry_run=False,
                    search=True, force=False):
    """Extract audio (and its sidecars) from one zip; return track descriptions."""
    done = load_cache()
    digest = _digest(zip_path)
    if digest in done and not force and not dry_run:
        say(f"already imported {zip_path} ({digest[:10]}); use --force to redo", quiet)
        return []
    imported = []
    staging = os.path.join(MUSIC_DIR, ".staging",
                           f"zipimport-{os.getpid()}-{int(time.time())}")
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [m for m in archive.infolist()
                       if not m.is_dir()
                       and os.path.splitext(m.filename)[1].lower() in AUDIO_EXTS]
            if not members:
                say(f"no audio files in {zip_path}", quiet)
                return []
            for member in members:
                rel_name = safe_name(member.filename)
                if not rel_name:
                    continue
                if dry_run:
                    say(f"would import {member.filename}", quiet)
                    imported.append({"path": rel_name})
                    continue
                os.makedirs(staging, exist_ok=True)
                staged = os.path.join(staging, rel_name)
                with archive.open(member) as src, open(staged, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                title, artist, album, no, genre, year, dur, lyrics, lsrc = read_tags(
                    staged, rel_name)
                meta = clean_meta(title, artist, genre, rel=rel_name)
                full = os.path.join(MUSIC_DIR,
                                    folder_for(conn, meta["title"], meta["artists"]),
                                    rel_name)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                shutil.move(staged, full)
                yt_id = read_yt_id(full)
                info = None
                if yt_id:
                    try:
                        info = video_info(yt_id)
                    except Exception as e:
                        say(f"  ! YouTube lookup failed for {yt_id}: {e}", quiet)
                if not yt_id and search:
                    try:
                        yt_id = search_video(meta["title"], meta["artists"])
                    except Exception as e:
                        say(f"  ! YouTube search failed for {rel_name}: {e}", quiet)
                    if yt_id:
                        try:
                            info = video_info(yt_id)
                        except Exception as e:
                            say(f"  ! YouTube lookup failed for {yt_id}: {e}", quiet)
                if info:
                    meta = clean_meta(title, artist, genre, info, rel_name)
                if yt_id:
                    write_sidecar(full, yt_id, info, meta["title"], meta["artist"] or artist)
                # Also bring along sidecars that were zipped next to the audio.
                stem = os.path.splitext(member.filename)[0]
                for side in (".lrc", ".yt.json"):
                    sibling = stem + side
                    try:
                        data = archive.read(sibling)
                    except KeyError:
                        continue
                    with open(os.path.splitext(full)[0] + side, "wb") as fh:
                        fh.write(data)
                imported.append({"path": full, "title": meta["title"],
                                 "artists": meta["artists"], "yt_id": yt_id})
                say(f"  {rel_name}: {meta['title']!r} "
                    f"[{', '.join(meta['artists']) or 'no artist'}] "
                    f"yt={yt_id or 'none'}", quiet)
    finally:
        if os.path.isdir(staging):
            shutil.rmtree(staging, ignore_errors=True)
    return imported


def import_zip(zip_path, dry_run=False, search=True, force=False, quiet=False):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        tracks = extract_members(zip_path, conn, quiet=quiet, dry_run=dry_run,
                                 search=search, force=force)
        if tracks and not dry_run:
            # One scan indexes the new rows, queues enrichment and folds
            # duplicates by name + artist(s), preferring the fuller credit.
            scan_library(conn)
            digest = _digest(zip_path)
            done = load_cache()
            done.add(digest)
            save_cache(done)
            say(f"imported {len(tracks)} track(s) from {zip_path}", quiet)
        return len(tracks)
    finally:
        conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Import audio from a ZIP into the library.")
    ap.add_argument("zipfile", nargs="+", help="ZIP archive(s) to import")
    ap.add_argument("--dry-run", action="store_true", help="List what would be imported")
    ap.add_argument("--no-search", action="store_true",
                    help="Only use a YouTube id already embedded in the file")
    ap.add_argument("--force", action="store_true", help="Import even if cached as done")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    total = 0
    for path in args.zipfile:
        total += import_zip(path, dry_run=args.dry_run, search=not args.no_search,
                            force=args.force, quiet=args.quiet)
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
