#!/usr/bin/env python3
"""
yt_playlist_to_mp3.py

Download one or more YouTube playlists as audio files (MP3 by default, or
M4A/AAC/Opus/FLAC/WAV/WebM) with embedded metadata (artist, title, album,
track number, genre, year, cover art) and a chosen cover-art image format.
Built for speed and for surviving flaky connections / crashed previous runs.

Requirements:
    pip install yt-dlp
    ffmpeg (and ffprobe, which ships with it) must be on PATH
        - Arch:   sudo pacman -S ffmpeg
        - Debian: sudo apt install ffmpeg
    Strongly recommended for speed -- multi-connection segment fetching:
        - Arch:   sudo pacman -S aria2
        - Debian: sudo apt install aria2
      Auto-detected and used if present. Without it you're on yt-dlp's
      native single-path fragment downloader, which is noticeably slower.

Cover art format:
    --thumbnail-format {jpg,png,gif,webp}   default: jpg (safest, most players read it)

Output format:
    --format {mp3,m4a,aac,opus,flac,wav,webm,best}   default: mp3
    m4a/opus/webm/best skip re-encoding when the source already matches,
    which is much faster than mp3 (always transcodes). The script also
    requests a matching *source* stream when possible so there's less to
    convert in the first place.

Performance:
    --turbo               shortcut for aggressive workers/fragments/chunk-size/
                          scan-workers/fast-client all at once
    --workers N            videos downloaded in parallel
                          (default: min(12, cores*2); turbo: min(24, cores*4))
    --fragments N           connections per video (default: 16; turbo: 32)
    --chunk-size N MiB       HTTP chunk size (default: 10; turbo: 20)
    --scan-workers N          parallel workers for the repair/fix-minor
                          integrity+metadata scan (default: min(24, cores*3);
                          turbo: min(48, cores*6))
    --fast-client            use a shorter yt-dlp client-fallback list
                          (android + web instead of every client yt-dlp
                          knows) -- fewer requests per video extraction.
                          Still compatible with --cookies (web client covers
                          cookie auth). Bundled into --turbo.
    --relist                 ignore the cached playlist listing and re-fetch
                          from YouTube even if a fresh cache exists
    --cache-minutes N          how long a cached playlist listing stays valid
                          before auto-refreshing (default: 30, 0 = never cache)

Fixing a previous run's errors:
    --repair               clean up leftover partial/broken files from a
                           crashed or interrupted earlier run (.part/.ytdl/
                           .frag temp files, zero-byte files, audio files
                           that fail an integrity check because a merge
                           didn't finish).
    --fix-minor             patch small issues in otherwise-good files: songs
                           missing embedded metadata or cover art get fixed
                           in place, stray leftover image files get cleaned up.
                           (--repair and --fix-minor now share a single
                           parallelized scan instead of two separate ones.)
    --retry-failed          re-attempt exactly the videos that failed or were
                           left unfinished on the last run (tracked in
                           <output>/.failed_indices.txt), instead of assuming
                           progress was linear.
    --full-scan             ground truth mode: re-lists the real playlist,
                           walks every file actually on disk, and downloads
                           whatever's genuinely missing. Ignores the archive
                           file and failed-list entirely.
    --fix-everything          shortcut for --repair --fix-minor --full-scan
                           together. The "just fix my whole library" button.

Resuming:
    --resume            (default) skip anything already in the archive file,
                         resume partial .part files
    --resume 112          jump straight to the 112th video in listing order
    --no-resume            ignore archive, start over

Authentication (age-restricted / members-only videos):
    --cookies PATH       path to a cookies.txt (Netscape format) exported
                         from your browser while logged into YouTube

Error handling:
    --max-retries N       per-video retry attempts on failure (default: 5)
    --retry-forever        keep retrying a video indefinitely
    --retry-wait N          base seconds between retries, doubles each attempt
    Rate limiting: when YouTube throttles us (HTTP 429/403, "confirm you're
    not a bot", "too many requests"...), ALL workers pause for a shared
    cooldown and then retry automatically. The cooldown doubles on each
    repeated hit, up to --rate-limit-max-wait, and only gives up after being
    continuously blocked for --rate-limit-max-total seconds (default 2h).
    Throttling never consumes a video's normal retry budget.
    Ctrl+C stops cleanly: in-flight videos finish their current attempt, no
    new ones start, and it prints the exact --resume N and confirms
    .failed_indices.txt is up to date for a --retry-failed rerun.

Logging:
    Every log line is timestamped (HH:MM:SS). Once downloads start, a
    periodic progress line reports how many videos are done, elapsed time,
    and an ETA for the rest based on the rolling average time/video so far.
    --log-file PATH        also append the full timestamped log to a file
                           (handy for reviewing what happened on a long
                           unattended run, or one that got interrupted).
    --quiet                 only print warnings/errors and the final summary
                           (progress heartbeat and per-video lines are
                           suppressed; maintenance and listing summaries
                           still print)

Startup checks:
    Before doing any work the script verifies ffmpeg/ffprobe are on PATH
    and warns if the output volume looks low on free space -- useful when
    writing to a small removable drive.
"""

import argparse
import concurrent.futures
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
import urllib.request

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp is not installed. Run: pip install yt-dlp")

print_lock = threading.Lock()
stop_event = threading.Event()

AUDIO_FORMATS = {"mp3", "m4a", "aac", "opus", "flac", "wav", "webm", "best"}
THUMBNAIL_FORMATS = {"jpg", "png", "gif", "webp"}
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
STRAY_EXTENSIONS = (".part", ".ytdl", ".frag", ".temp", ".ffmpeg")
STRAY_MARKERS = (".fixtmp.",)  # substring markers for stray temp files (not simple suffixes)
CACHE_FILENAME = ".playlist_cache.json"
FAST_CLIENTS = ["android", "web"]
LOW_DISK_WARN_MB = 500

LOG_FILE = None
QUIET = False


def set_log_file(path):
    """Enable teeing all log() output to a file as well as stdout."""
    global LOG_FILE
    if not path:
        return
    LOG_FILE = path
    try:
        with open(path, "a") as fh:
            fh.write(f"\n=== Run started {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    except OSError as e:
        LOG_FILE = None
        print(f"[WARN] Could not open --log-file {path}: {e}", flush=True)


def set_quiet(value):
    global QUIET
    QUIET = value


def log(msg, level="INFO", quiet_ok=False):
    """Timestamped logging, optionally tagged (WARN/ERROR) and mirrored to
    --log-file. quiet_ok=True lets a line still print under --quiet (used
    for the periodic heartbeat and per-video lines that --quiet suppresses)."""
    tag = "" if level == "INFO" else f"[{level}] "
    ts = time.strftime("%H:%M:%S")
    text = f"[{ts}] {tag}{msg}"
    if QUIET and quiet_ok and level == "INFO":
        # Suppressed on screen under --quiet, but still recorded to file.
        if LOG_FILE:
            try:
                with open(LOG_FILE, "a") as fh:
                    fh.write(text + "\n")
            except OSError:
                pass
        return
    with print_lock:
        print(text, flush=True)
        if LOG_FILE:
            try:
                with open(LOG_FILE, "a") as fh:
                    fh.write(text + "\n")
            except OSError:
                pass


def format_duration(seconds):
    """1234.5 -> '20m34s', 45 -> '45s', 3700 -> '1h01m40s'."""
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def format_size(nbytes):
    if nbytes <= 0:
        return "0 MiB"
    mib = nbytes / (1024 * 1024)
    if mib >= 1024:
        return f"{mib / 1024:.2f} GiB"
    return f"{mib:.1f} MiB"


# ---------------------------------------------------------------------------
# Rate-limit detection & global backoff
#
# YouTube answers bursts of traffic with 429s, "Sign in to confirm you're not
# a bot", and bare 403s. Instead of failing the playlist, any worker that sees
# one of those parks *every* worker for a shared cooldown, then they all retry.
# Each repeated hit doubles the cooldown (with jitter) so we back off further
# the longer the block lasts. Success resets it. This is what makes the
# downloader "wait until we're not rate limited anymore" instead of erroring.
# ---------------------------------------------------------------------------
RATE_LIMIT_RE = re.compile(
    r"(?:"
    r"http error 429|too many requests|rate[- ]?limit|ratelimit|"
    r"sign in to confirm you[’']?re not a bot|confirm you[’']re not a bot|"
    r"this content isn[’']t available, try again later|"
    r"http error 403|403: forbidden|"
    r"request (?:was )?blocked|temporarily blocked|"
    r"please (?:try|sign in) again later|please sign in|login required"
    r")",
    re.I,
)


def is_rate_limited(exc):
    """True when an exception message looks like throttling / bot-blocking."""
    return bool(RATE_LIMIT_RE.search(str(exc)))


class RateLimiter:
    """Process-wide rate-limit gate shared by every download/listing thread."""

    def __init__(self, base=60, maximum=1800, max_total=7200):
        self.base = max(5, int(base))
        self.maximum = max(self.base, int(maximum))
        self.max_total = int(max_total)  # 0 = never give up
        self._lock = threading.Lock()
        self._until = 0.0
        self._strikes = 0
        self._incident_start = 0.0

    def _remaining(self):
        with self._lock:
            return max(0.0, self._until - time.time())

    def blocked(self):
        return self._remaining() > 0

    def note_success(self):
        """A request got through: clear the cooldown and the escalation.
        Ignored while a cooldown is still running so in-flight successes don't
        cancel a pause that other workers are already waiting on."""
        with self._lock:
            if self._until > time.time():
                return
            had = self._strikes > 0
            self._until = 0.0
            self._strikes = 0
            self._incident_start = 0.0
        if had:
            log("Rate limit cleared -- resuming downloads.")

    def note_limit(self, context=""):
        """Register a throttling response; returns the shared cooldown length."""
        with self._lock:
            now = time.time()
            if not self._incident_start:
                self._incident_start = now
            self._strikes += 1
            wait = min(self.maximum, self.base * (2 ** (self._strikes - 1)))
            wait *= random.uniform(0.85, 1.15)
            self._until = max(self._until, now + wait)
            remaining = self._until - now
            total = now - self._incident_start
            strikes = self._strikes
        log(
            f"Rate limited ({context or 'YouTube'}) -- pausing all downloads for "
            f"~{format_duration(remaining)}, then retrying automatically "
            f"(hit {strikes}, {format_duration(total)} in this incident).",
            level="WARN",
        )
        return remaining

    def incident_expired(self):
        """True once we've been stuck in one continuous block for too long."""
        if self.max_total <= 0:
            return False
        with self._lock:
            started = self._incident_start
        return bool(started) and time.time() - started > self.max_total

    def wait(self, stop_evt=None):
        """Block until the shared cooldown expires. False if we were stopped."""
        while True:
            rem = self._remaining()
            if rem <= 0:
                with self._lock:
                    recovering = self._strikes > 0
                if recovering:
                    # Stagger the wake-up so 24 workers don't slam YouTube at once.
                    deadline = time.time() + random.uniform(0.5, 5.0)
                    while time.time() < deadline:
                        if stop_evt is not None and stop_evt.is_set():
                            return False
                        time.sleep(0.25)
                return not (stop_evt is not None and stop_evt.is_set())
            if stop_evt is not None and stop_evt.is_set():
                return False
            time.sleep(min(5.0, rem))


RATE_LIMIT = RateLimiter()


class RunStats:
    """Thread-safe tracking of progress/timing across the download pool, used
    for per-video timing lines, the periodic heartbeat, and the final ETA."""

    def __init__(self, total):
        self.total = total
        self.done = 0
        self.failed = 0
        self.durations = []
        self.bytes_done = 0
        self.start = time.time()
        self.lock = threading.Lock()

    def record(self, duration, success, nbytes=0):
        with self.lock:
            if success:
                self.done += 1
                self.durations.append(duration)
            else:
                self.failed += 1
            self.bytes_done += nbytes

    def snapshot(self):
        with self.lock:
            return self.done, self.failed, len(self.durations), self.bytes_done, (
                sum(self.durations) / len(self.durations) if self.durations else 0.0
            )

    def eta_str(self):
        done, failed, n, _bytes, avg = self.snapshot()
        remaining = self.total - done - failed
        if remaining <= 0 or avg <= 0:
            return None
        return format_duration(avg * remaining)

    def progress_line(self):
        done, failed, _n, nbytes, avg = self.snapshot()
        elapsed = time.time() - self.start
        parts = [f"{done}/{self.total} done"]
        if failed:
            parts.append(f"{failed} failed")
        parts.append(f"elapsed {format_duration(elapsed)}")
        eta = self.eta_str()
        if eta:
            parts.append(f"ETA {eta}")
        if nbytes:
            parts.append(format_size(nbytes) + " downloaded")
        return ", ".join(parts)


def heartbeat_logger(stats, stop_evt, interval=30):
    """Background thread: periodically logs overall progress + ETA so a long
    run (or one that's stalled on a single video) still shows signs of life."""
    while not stop_evt.wait(interval):
        done, failed, _n, _b, _avg = stats.snapshot()
        if done + failed >= stats.total:
            continue
        log("Progress: " + stats.progress_line(), quiet_ok=True)


def check_dependencies():
    missing = [t for t in ("ffmpeg", "ffprobe") if shutil.which(t) is None]
    if missing:
        sys.exit(
            "Missing required tool(s): " + ", ".join(missing) + ". Install ffmpeg "
            "(Arch: sudo pacman -S ffmpeg | Debian: sudo apt install ffmpeg) -- "
            "ffprobe ships with it."
        )


def check_disk_space(path, min_mb=LOW_DISK_WARN_MB):
    target = path if os.path.isdir(path) else (os.path.dirname(os.path.abspath(path)) or ".")
    try:
        free_mb = shutil.disk_usage(target).free / (1024 * 1024)
    except OSError:
        return
    if free_mb < min_mb:
        log(f"Only {free_mb:.0f} MiB free at {os.path.abspath(target)} -- "
            f"downloads may fail partway through if space runs out.", level="WARN")


def handle_sigint(signum, frame):
    if stop_event.is_set():
        log("\nForce quitting.")
        os._exit(1)
    log("\nStopping after in-flight videos finish (Ctrl+C again to force quit)...")
    stop_event.set()


def split_artist_title(raw_title: str):
    parts = re.split(r"\s[-\u2013\u2014]\s", raw_title, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, raw_title.strip()


# ---------------------------------------------------------------------------
# Maintenance: repair (corrupt/partial cleanup) + fix-minor (metadata/cover
# patching) merged into ONE parallelized pass -- one ffprobe call per file,
# spread across --scan-workers threads, instead of two separate serial walks.
# ---------------------------------------------------------------------------

def probe_full(path, attempts=2):
    """Single ffprobe call returning both container/format tags and stream
    info (used to detect embedded cover art), instead of two separate calls.
    Retries once on transient failure (slow/removable disks occasionally
    hiccup on a single read) before treating the file as unreadable."""
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", path],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                last_err = result.stderr
            else:
                return json.loads(result.stdout or "{}")
        except Exception as e:
            last_err = e
        if attempt < attempts:
            time.sleep(0.5)
    if last_err:
        log(f"Maintenance scan: could not probe {os.path.basename(path)} "
            f"after {attempts} attempt(s): {last_err}", level="WARN")
    return None


def classify_and_fix(path, cover_path, do_repair, do_fix_minor):
    data = probe_full(path)
    fmt = (data or {}).get("format") or {}
    try:
        duration = float(fmt.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    streams = (data or {}).get("streams") or []
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    broken = data is None or duration <= 0 or not has_audio

    if do_repair and broken:
        try:
            os.remove(path)
        except OSError:
            pass
        return "corrupt"

    if not do_fix_minor:
        return "ok"

    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    title = tags.get("title")
    artist = tags.get("artist")
    album = tags.get("album")
    has_cover = any(s.get("codec_type") == "video" for s in streams)

    needs_meta = not title or not artist or not album
    needs_cover = bool(cover_path) and not has_cover
    if not needs_meta and not needs_cover:
        return "ok"

    name = os.path.basename(path)
    base = os.path.splitext(name)[0]
    m = re.match(r"^(\d+)\s*-\s*(.+)$", base)
    track_num = m.group(1) if m else ""
    fallback_title = m.group(2) if m else base
    ext = os.path.splitext(name)[1]
    tmp_path = path + ".fixtmp" + ext

    cmd = ["ffmpeg", "-y", "-i", path]
    if needs_cover:
        cmd += ["-i", cover_path, "-map", "0:a", "-map", "1",
                "-c", "copy", "-id3v2_version", "3", "-disposition:v", "attached_pic"]
    else:
        cmd += ["-map", "0", "-c", "copy"]
    cmd += ["-metadata", f"title={title or fallback_title}"]
    cmd += ["-metadata", f"artist={artist or 'Unknown Artist'}"]
    cmd += ["-metadata", f"album={album or title or fallback_title}"]
    if track_num:
        cmd += ["-metadata", f"track={track_num}"]
    cmd += [tmp_path]

    last_err = None
    for attempt in range(1, 3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists(tmp_path):
                os.replace(tmp_path, path)
                if needs_meta and needs_cover:
                    return "meta_cover_fixed"
                return "cover_fixed" if needs_cover else "meta_fixed"
            last_err = result.stderr
        except Exception as e:
            last_err = e
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        if attempt == 1:
            time.sleep(0.5)
    log(f"Maintenance scan: could not patch {os.path.basename(path)}: {last_err}", level="WARN")
    return "patch_failed"


def maintenance_pass(out_dir, audio_format, scan_workers, do_repair, do_fix_minor):
    if not (do_repair or do_fix_minor) or not os.path.isdir(out_dir):
        return
    exts = {f".{e}" for e in (AUDIO_FORMATS - {"best"})} if audio_format == "best" else {f".{audio_format}"}

    removed_stray = 0
    if do_repair:
        for root, _dirs, files in os.walk(out_dir):
            for name in files:
                path = os.path.join(root, name)
                lower = name.lower()
                if lower.endswith(STRAY_EXTENSIONS) or any(m in lower for m in STRAY_MARKERS):
                    try:
                        os.remove(path)
                        removed_stray += 1
                    except OSError:
                        pass
                    continue
                try:
                    if os.path.getsize(path) == 0:
                        os.remove(path)
                        removed_stray += 1
                except OSError:
                    pass

    jobs = []
    all_images = []
    for root, _dirs, files in os.walk(out_dir):
        images = sorted(f for f in files if os.path.splitext(f)[1].lower() in IMG_EXTS)
        audios = sorted(f for f in files if os.path.splitext(f)[1].lower() in exts)
        if images:
            all_images.extend(os.path.join(root, i) for i in images)
        if not audios:
            continue
        cover_path = os.path.join(root, images[0]) if images else None
        for name in audios:
            jobs.append((os.path.join(root, name), cover_path))

    counts = {"corrupt": 0, "meta_fixed": 0, "cover_fixed": 0, "meta_cover_fixed": 0,
              "ok": 0, "patch_failed": 0}

    if jobs:
        scan_start = time.time()
        log(f"Maintenance scan: checking {len(jobs)} audio file(s) with "
            f"{scan_workers} parallel worker(s)...")
        scanned = 0
        milestone = max(1, len(jobs) // 10)
        with concurrent.futures.ThreadPoolExecutor(max_workers=scan_workers) as pool:
            futs = {
                pool.submit(classify_and_fix, p, c, do_repair, do_fix_minor): p
                for p, c in jobs
            }
            for f in concurrent.futures.as_completed(futs):
                try:
                    status = f.result()
                except Exception as e:
                    status = "patch_failed"
                    log(f"Maintenance scan: error on {futs[f]} -> {e}", level="ERROR")
                counts[status] = counts.get(status, 0) + 1
                scanned += 1
                if scanned % milestone == 0 or scanned == len(jobs):
                    log(f"Maintenance scan: {scanned}/{len(jobs)} checked...", quiet_ok=True)
        log(f"Maintenance scan: finished in {format_duration(time.time() - scan_start)}.")

    parts = []
    if do_repair:
        parts.append(f"{removed_stray} stray/incomplete file(s) removed")
        parts.append(f"{counts['corrupt']} corrupt/unmerged file(s) removed")
    if do_fix_minor:
        meta_total = counts["meta_fixed"] + counts["meta_cover_fixed"]
        cover_total = counts["cover_fixed"] + counts["meta_cover_fixed"]
        parts.append(f"{meta_total} file(s) had metadata patched")
        parts.append(f"{cover_total} file(s) had cover art embedded")
        if counts["patch_failed"]:
            parts.append(f"{counts['patch_failed']} file(s) could not be patched")
    if parts:
        log("Maintenance scan: " + ", ".join(parts) + ".")

    if do_fix_minor and all_images:
        cleaned = 0
        for img in all_images:
            try:
                os.remove(img)
                cleaned += 1
            except OSError:
                pass
        log(f"Maintenance scan: removed {cleaned} stray image file(s).")

    if do_repair:
        archive_path = os.path.join(out_dir, ".archive.txt")
        if os.path.exists(archive_path):
            os.remove(archive_path)
            log("--repair: cleared the archive file so nothing is falsely skipped "
                "(already-good files are still skipped automatically because "
                "their output file already exists).")


# ---------------------------------------------------------------------------
# Failed-indices tracking, for --retry-failed
# ---------------------------------------------------------------------------

def failed_indices_path(out_dir):
    return os.path.join(out_dir, ".failed_indices.txt")


def load_failed_indices(out_dir):
    path = failed_indices_path(out_dir)
    if not os.path.exists(path):
        return set()
    with open(path) as fh:
        return {int(line.strip()) for line in fh if line.strip().isdigit()}


def save_failed_indices(out_dir, indices):
    path = failed_indices_path(out_dir)
    if not indices:
        if os.path.exists(path):
            os.remove(path)
        return
    with open(path, "w") as fh:
        for i in sorted(indices):
            fh.write(f"{i}\n")


# ---------------------------------------------------------------------------
# Ground-truth disk scan, for --full-scan
# ---------------------------------------------------------------------------

def scan_existing_indices(out_dir, audio_format):
    exts = {f".{e}" for e in (AUDIO_FORMATS - {"best"})} if audio_format == "best" else {f".{audio_format}"}
    found = set()
    if not os.path.isdir(out_dir):
        return found
    for _root, _dirs, files in os.walk(out_dir):
        for name in files:
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            m = re.match(r"^(\d+)\s*-\s*", name)
            if m:
                found.add(int(m.group(1)))
    return found


# ---------------------------------------------------------------------------
# Playlist listing, with a small on-disk cache to avoid re-hitting YouTube
# every single run for a playlist that hasn't changed.
# ---------------------------------------------------------------------------

def load_cached_listing(out_dir, url, max_age_seconds):
    if max_age_seconds <= 0:
        return None
    path = os.path.join(out_dir, CACHE_FILENAME)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as fh:
            data = json.load(fh)
    except Exception:
        return None
    entry = data.get(url)
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > max_age_seconds:
        return None
    return entry.get("entries")


def save_cached_listing(out_dir, url, entries):
    path = os.path.join(out_dir, CACHE_FILENAME)
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except Exception:
            data = {}
    data[url] = {"ts": time.time(), "entries": entries}
    try:
        with open(path, "w") as fh:
            json.dump(data, fh)
    except OSError:
        pass


def list_playlist_entries(url, max_retries, cookies=None, fast_client=False):
    # A watch?v=...&list=... URL comes back from yt-dlp's flat extractor as a
    # single "url" item, not the playlist. Listing the canonical playlist URL
    # is reliable and yields every entry.
    m = re.search(r"[?&]list=([\w-]+)", url)
    fetch_url = f"https://www.youtube.com/playlist?list={m.group(1)}" if m else url
    attempt = 0
    while True:
        if stop_event.is_set():
            return []
        if not RATE_LIMIT.wait(stop_event):
            return []
        attempt += 1
        try:
            opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True,
                "noplaylist": False,
                "socket_timeout": 20,
            }
            opts.update(_js_opts())
            if cookies:
                opts["cookiefile"] = cookies
            if fast_client:
                opts["extractor_args"] = {"youtube": {"player_client": FAST_CLIENTS}}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(fetch_url, download=False)
            RATE_LIMIT.note_success()
            # A playlist URL must come back as a playlist. If YouTube hands
            # back just a single video (transient error, bot check, etc.)
            # retry instead of caching a bogus one-item listing.
            if info is not None and "entries" not in info and (m or re.search(r"[?&]list=", url)):
                raise RuntimeError("expected a playlist but YouTube returned a single video")
            break
        except Exception as e:
            if is_rate_limited(e):
                # Throttling is not a real failure: don't spend a retry on it.
                attempt -= 1
                RATE_LIMIT.note_limit(f"listing {url}")
                if RATE_LIMIT.incident_expired():
                    log(f"Still rate limited after "
                        f"{format_duration(RATE_LIMIT.max_total)}; giving up on listing {url}.",
                        level="ERROR")
                    return []
                continue
            if attempt > max_retries:
                log(f"Failed to list playlist after {attempt} attempts: {url} -> {e}")
                return []
            wait = min(60, 5 * (2 ** (attempt - 1)))
            log(f"Listing failed ({e}); retrying in {wait}s [{attempt}/{max_retries}]")
            time.sleep(wait)

    if info is None:
        return []

    if "entries" not in info:
        return [{"url": info.get("webpage_url", url),
                  "playlist_title": info.get("title") or "Unknown Album",
                  "index": 1}]

    playlist_title = info.get("title") or "Unknown Album"
    entries = []
    seq = 0
    for entry in info["entries"]:
        if entry is None:
            continue  # deleted/private video -- skip without burning a number
        video_url = entry.get("url") or entry.get("webpage_url")
        if not video_url:
            continue
        if not video_url.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"
        seq += 1
        entries.append({"url": video_url, "playlist_title": playlist_title, "index": seq})
    return entries


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

LYRICS_API = os.environ.get("LYRICS_API", "https://lrclib.net/api")
UA = "mcmusic-downloader/1.0 (+https://mcmusic.sdisk.us)"
BAD_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name, max_len=120):
    """Filesystem-safe name. Display metadata is never touched by this."""
    name = unicodedata.normalize("NFC", str(name or ""))
    name = BAD_NAME_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().strip(". ")
    if len(name) > max_len:
        name = name[:max_len].rstrip(". ")
    return name or "untitled"


def fetch_lyrics(title, artist, duration=None, timeout=10):
    """Look lyrics up on LRCLIB. Returns (text, synced_flag)."""
    title = (title or "").strip()
    if not title:
        return "", 0
    params = {"track_name": title}
    if artist:
        params["artist_name"] = str(artist).strip()
    if duration:
        try:
            params["duration"] = int(round(float(duration)))
        except (TypeError, ValueError):
            pass
    try:
        url = f"{LYRICS_API}/get?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return "", 0
    synced = (data.get("syncedLyrics") or "").strip()
    plain = (data.get("plainLyrics") or "").strip()
    return (synced or plain), (1 if synced else 0)


def write_lyrics_sidecar(audio_path, info):
    """Write <track>.lrc next to the audio file so the scanner can index it."""
    stem = os.path.splitext(audio_path)[0]
    lrc_path = stem + ".lrc"
    if os.path.exists(lrc_path) and os.path.getsize(lrc_path) > 0:
        return "exists"
    info = info or {}
    title = info.get("track") or info.get("title")
    artist = (info.get("artist") or info.get("creator") or info.get("uploader")
              or info.get("channel"))
    text, synced = fetch_lyrics(title, artist, info.get("duration"))
    if not text:
        return "none"
    try:
        with open(lrc_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except OSError as e:
        log(f"[lyrics warn] {os.path.basename(audio_path)}: {e}", level="WARN")
        return "error"
    return "synced" if synced else "plain"


YT_SIDECAR_KEYS = (
    "id", "title", "track", "artist", "creator", "uploader", "channel", "channel_id",
    "duration", "view_count", "like_count", "comment_count", "repost_count",
    "upload_date", "release_date", "genre", "categories", "tags", "album",
    "description", "webpage_url", "thumbnail", "age_limit", "was_live",
)


def write_yt_sidecar(audio_path, info):
    """Store the YouTube metadata next to the audio so the scanner can index it."""
    info = info or {}
    data = {k: info.get(k) for k in YT_SIDECAR_KEYS if info.get(k) not in (None, "", [])}
    if not data.get("id"):
        return "none"
    path = os.path.splitext(audio_path)[0] + ".yt.json"
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
    except OSError as e:
        log(f"[sidecar warn] {os.path.basename(audio_path)}: {e}", level="WARN")
        return "error"
    return "ok"


def set_album_tag(path, album):
    """Write the album tag in place (stream copy, no re-encode).

    yt-dlp's metadata postprocessor already embeds the album when the extractor
    knows it (YouTube Music does), so this is only used for the fallback case:
    music that has no album of its own gets the song name.
    """
    album = str(album or "").strip()
    if not album:
        return False
    ext = os.path.splitext(path)[1]
    tmp_path = f"{path}.album{ext}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", path, "-map", "0", "-c", "copy",
           "-metadata", f"album={album}", tmp_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            os.replace(tmp_path, path)
            return True
        log(f"[album warn] {os.path.basename(path)}: {result.stderr.strip()[:200]}",
            level="WARN")
    except Exception as e:
        log(f"[album warn] {os.path.basename(path)}: {e}", level="WARN")
    try:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except OSError:
        pass
    return False


def resolve_audio_path(job, out_dir, audio_format):
    """Find the finished file for a job after postprocessing changed its extension."""
    folder = os.path.join(out_dir, sanitize_filename(job["playlist_title"]))
    prefix = f"{job['index']:02d} - "
    exts = AUDIO_FORMATS - {"best"} if audio_format == "best" else {audio_format}
    try:
        names = os.listdir(folder)
    except OSError:
        return None
    best = None
    for name in names:
        if not name.startswith(prefix):
            continue
        if os.path.splitext(name)[1].lstrip(".").lower() not in exts:
            continue
        full = os.path.join(folder, name)
        try:
            mtime = os.path.getmtime(full)
        except OSError:
            continue
        if best is None or mtime > best[0]:
            best = (mtime, full)
    return best[1] if best else None


def source_format_string(audio_format):
    """Prefer a source stream that already matches the target codec/container
    so ffmpeg can copy instead of transcode -- faster and no quality loss."""
    if audio_format == "opus":
        return "bestaudio[acodec=opus]/bestaudio/best"
    if audio_format in ("m4a", "aac"):
        return "bestaudio[ext=m4a]/bestaudio/best"
    if audio_format == "webm":
        return "bestaudio[ext=webm]/bestaudio/best"
    return "bestaudio/best"


def _js_opts():
    """YouTube signature/n challenges need a JS runtime plus the EJS solver script."""
    try:
        import shutil
        if not shutil.which("node"):
            return {}
    except Exception:
        return {}
    return {"js_runtimes": {"node": {}}, "remote_components": {"ejs:github"}}


def make_ydl_opts(job, out_dir, split_artist, quality, ffmpeg_threads, archive_path,
                   fragments, use_aria2c, embed_thumb, audio_format, thumbnail_format,
                   chunk_size, extra_meta, cookies=None, fast_client=False):
    outtmpl = os.path.join(out_dir, sanitize_filename(job["playlist_title"]),
                            f"{job['index']:02d} - %(title)s.%(ext)s")

    codec = None if audio_format in ("best", "webm") else audio_format
    postprocessors = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": codec or "best",
        "preferredquality": quality,
    }]
    # Metadata must run before EmbedThumbnail: FFmpegMetadata rewrites the
    # file with ffmpeg, which would drop the cover art embedded by the
    # thumbnail postprocessor if the order were reversed.
    postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if embed_thumb:
        postprocessors.append({"key": "FFmpegThumbnailsConvertor", "format": thumbnail_format})
        postprocessors.append({"key": "EmbedThumbnail"})

    # The album is deliberately NOT forced here. yt-dlp's metadata
    # postprocessor writes the real album whenever the extractor knows it
    # (YouTube Music does), and overriding that with the playlist title was
    # putting every track of a playlist into an album named after the
    # playlist. Tracks with no album of their own get the song name in
    # download_one, once the video metadata is known.
    ffmeta_args = ["-metadata", f"track={job['index']}",
                   "-metadata", f"purl={job['url']}"]
    for k, v in extra_meta.items():
        ffmeta_args += ["-metadata", f"{k}={v}"]

    ydl_opts = {
        "format": source_format_string(audio_format),
        "outtmpl": outtmpl,
        "writethumbnail": embed_thumb,
        "postprocessors": postprocessors,
        "ignoreerrors": False,
        "quiet": False,
        "no_warnings": False,
        "continuedl": True,
        "download_archive": archive_path,
        "concurrent_fragment_downloads": fragments,
        "http_chunk_size": chunk_size * 1024 * 1024,
        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 3,
        "file_access_retries": 10,
        "socket_timeout": 20,
        "postprocessor_args": {
            # yt-dlp's pp_key() strips the leading "ffmpeg", so the metadata
            # postprocessor is "metadata" (keys are "<pp>+<exe>"), not
            # "ffmpegmetadata"; using the wrong key silently dropped album/track.
            "metadata+ffmpeg": ffmeta_args,
            "ffmpeg": ["-threads", str(ffmpeg_threads)],
        },
        "parse_metadata": ["uploader:(?P<meta_artist>.+)"],
        "trim_file_name": 120,
        "windowsfilenames": False,
    }

    ydl_opts.update(_js_opts())
    if cookies:
        ydl_opts["cookiefile"] = cookies
    if fast_client:
        ydl_opts["extractor_args"] = {"youtube": {"player_client": FAST_CLIENTS}}

    if use_aria2c:
        ydl_opts["external_downloader"] = "aria2c"
        # aria2c's -x and --max-connection-per-server are the same option and
        # must be 1..16. Keep the high yt-dlp fragment concurrency while
        # clamping the external downloader to its supported range.
        aria_conns = str(min(fragments, 16))
        ydl_opts["external_downloader_args"] = {
            "aria2c": ["-x", aria_conns, "-s", aria_conns, "-k", "1M",
                       "--max-connection-per-server", aria_conns,
                       "--min-split-size", "1M", "--retry-wait", "5",
                       "--max-tries", "0", "--continue=true"]
        }

    def hook(d):
        if d.get("status") != "finished":
            return
        nbytes = d.get("downloaded_bytes") or d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        job["_info"] = d.get("info_dict") or {}
        job["_file"] = d.get("filename")
        if nbytes:
            job["_bytes"] = job.get("_bytes", 0) + nbytes
        if split_artist:
            info = d.get("info_dict", {})
            artist, title = split_artist_title(info.get("title", ""))
            if artist:
                info["artist"] = artist
    ydl_opts["progress_hooks"] = [hook]

    return ydl_opts


def download_one(job, out_dir, split_artist, quality, ffmpeg_threads, archive_path,
                  fragments, use_aria2c, embed_thumb, audio_format, thumbnail_format,
                  chunk_size, extra_meta, max_retries, retry_forever, retry_wait,
                  completed, failed, stats, cookies=None, fast_client=False, lyrics=True):
    opts = make_ydl_opts(job, out_dir, split_artist, quality, ffmpeg_threads, archive_path,
                          fragments, use_aria2c, embed_thumb, audio_format, thumbnail_format,
                          chunk_size, extra_meta, cookies, fast_client)
    job_start = time.time()
    attempt = 0
    while True:
        if stop_event.is_set():
            log(f"[skipped, stopping] {job['playlist_title']} #{job['index']:02d}")
            return
        # Hold here while any other worker has detected throttling.
        if not RATE_LIMIT.wait(stop_event):
            log(f"[skipped, stopping] {job['playlist_title']} #{job['index']:02d}")
            return
        attempt += 1
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([job["url"]])
            RATE_LIMIT.note_success()
            audio_path = resolve_audio_path(job, out_dir, audio_format)
            if audio_path:
                info = job.get("_info") or {}
                if not info.get("album"):
                    album = (info.get("track") or info.get("title")
                             or job.get("title"))
                    set_album_tag(audio_path, album)
                write_yt_sidecar(audio_path, job.get("_info"))
                if lyrics:
                    status = write_lyrics_sidecar(audio_path, job.get("_info"))
                    if status in ("plain", "synced"):
                        log(f"[lyrics:{status}] {os.path.basename(audio_path)}", quiet_ok=True)
            duration = time.time() - job_start
            nbytes = job.get("_bytes", 0)
            stats.record(duration, True, nbytes)
            eta = stats.eta_str()
            msg = (f"[done] {job['playlist_title']} #{job['index']:02d} "
                   f"in {format_duration(duration)} ({stats.progress_line()})")
            log(msg, quiet_ok=True)
            with print_lock:
                completed.add(job["index"])
            return
        except Exception as e:
            if is_rate_limited(e):
                # Don't burn a retry on throttling -- wait for the block to lift.
                attempt -= 1
                RATE_LIMIT.note_limit(f"{job['playlist_title']} #{job['index']:02d}")
                if RATE_LIMIT.incident_expired():
                    duration = time.time() - job_start
                    stats.record(duration, False)
                    log(f"[FAILED, still rate limited after "
                        f"{format_duration(RATE_LIMIT.max_total)}] {job['url']}",
                        level="ERROR")
                    with print_lock:
                        failed.add(job["index"])
                    return
                continue
            if not retry_forever and attempt > max_retries:
                duration = time.time() - job_start
                stats.record(duration, False)
                log(f"[FAILED, giving up after {attempt - 1} retries] {job['url']} -> {e}",
                    level="ERROR")
                with print_lock:
                    failed.add(job["index"])
                return
            wait = min(60, retry_wait * (2 ** (attempt - 1)))
            log(f"[retrying in {wait}s, attempt {attempt}] {job['playlist_title']} "
                f"#{job['index']:02d} -> {e}", level="WARN")
            slept = 0
            while slept < wait and not stop_event.is_set():
                time.sleep(1)
                slept += 1


def download_playlists(urls, out_dir, split_artist, quality, workers, ffmpeg_threads,
                        fragments, resume_from, embed_thumb, audio_format, thumbnail_format,
                        chunk_size, extra_meta, max_retries, retry_forever, retry_wait,
                        listing_retries, retry_failed_only, repair, fix_minor, full_scan,
                        cookies=None, fast_client=False, scan_workers=8, relist=False,
                        cache_minutes=30, staging_dir=None, lyrics=True, dedupe=True):
    if staging_dir:
        os.makedirs(staging_dir, exist_ok=True)
        check_disk_space(staging_dir)
    os.makedirs(out_dir, exist_ok=True)
    check_disk_space(out_dir)

    # Maintenance (repair/fix-minor) is CPU+disk bound; playlist listing is
    # network bound. Run them concurrently instead of back-to-back.
    maintenance_thread = None
    if repair or fix_minor:
        maintenance_thread = threading.Thread(
            target=maintenance_pass,
            args=(out_dir, audio_format, scan_workers, repair, fix_minor),
        )
        maintenance_thread.start()

    # Archive + cache live in the staging dir (if set) so resume works across
    # staging→library moves; they track video IDs, not paths.
    archive_root = staging_dir or out_dir
    archive_path = os.path.join(archive_root, ".archive.txt")

    all_jobs = []
    for url in urls:
        cached = None if relist else load_cached_listing(archive_root, url, cache_minutes * 60)
        if cached is not None:
            log(f"Using cached listing for {url} ({len(cached)} video(s)). "
                f"Pass --relist to force a refresh.")
            entries = cached
        else:
            log(f"Listing playlist: {url}")
            entries = list_playlist_entries(url, listing_retries, cookies, fast_client)
            log(f"  -> {len(entries)} video(s) found")
            if entries:
                save_cached_listing(archive_root, url, entries)
        all_jobs.extend(entries)

    if maintenance_thread:
        maintenance_thread.join()

    if not all_jobs:
        raise RuntimeError("No videos found across the given URL(s).")

    if full_scan:
        existing = scan_existing_indices(archive_root, audio_format)
        missing = [j for j in all_jobs if j["index"] not in existing]
        log(f"--full-scan: {len(existing)} video(s) already present on disk, "
            f"{len(missing)} genuinely missing -- fetching those.")
        all_jobs = missing
    elif retry_failed_only:
        wanted = load_failed_indices(archive_root)
        if not wanted:
            log("--retry-failed: no .failed_indices.txt entries found -- nothing was marked "
                "as failed, so continuing with a normal run over everything remaining instead "
                "of stopping.")
        else:
            all_jobs = [j for j in all_jobs if j["index"] in wanted]
            log(f"--retry-failed: retrying exactly {len(all_jobs)} previously-failed video(s): "
                f"{sorted(wanted)}")
            resume_from = None

    if not full_scan and not retry_failed_only:
        if resume_from and resume_from > 1:
            skipped = resume_from - 1
            all_jobs = all_jobs[skipped:]
            log(f"--resume {resume_from}: skipping first {skipped} video(s), "
                f"{len(all_jobs)} remaining.")

    if not all_jobs:
        log("\nNothing to download -- everything's already accounted for.")
        return 0, 0

    use_aria2c = shutil.which("aria2c") is not None
    if use_aria2c:
        log("aria2c found -- using it for multi-connection segment downloads.")
    else:
        log("aria2c not found -- using yt-dlp's native concurrent fragment downloader. "
            "Install it for a real speed boost: sudo pacman -S aria2")

    total = len(all_jobs)
    log(f"\nStarting download of {total} video(s) with {workers} parallel worker(s), "
        f"{fragments} connection(s)/fragments per video, {ffmpeg_threads} ffmpeg thread(s) each, "
        f"audio format: {audio_format}, cover art format: {thumbnail_format}.\n")

    completed = set()
    failed = set()
    stats = RunStats(total)
    heartbeat_stop = threading.Event()
    heartbeat_thread = None
    if total > 3:
        heartbeat_thread = threading.Thread(
            target=heartbeat_logger, args=(stats, heartbeat_stop), daemon=True,
        )
        heartbeat_thread.start()

    old_handler = signal.signal(signal.SIGINT, handle_sigint)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(download_one, job, out_dir, split_artist, quality, ffmpeg_threads,
                            archive_path, fragments, use_aria2c, embed_thumb, audio_format,
                            thumbnail_format, chunk_size, extra_meta, max_retries, retry_forever,
                            retry_wait, completed, failed, stats, cookies, fast_client,
                            lyrics)
                for job in all_jobs
            ]
            for f in concurrent.futures.as_completed(futures):
                f.result()
    finally:
        signal.signal(signal.SIGINT, old_handler)
        heartbeat_stop.set()
        if heartbeat_thread:
            heartbeat_thread.join(timeout=1)

    _done, _failed, _n, total_bytes, avg = stats.snapshot()
    elapsed = time.time() - stats.start
    summary = (f"\n{len(completed)}/{total} video(s) completed this run "
               f"in {format_duration(elapsed)}")
    if avg > 0:
        summary += f" (avg {format_duration(avg)}/video"
        if total_bytes:
            summary += f", {format_size(total_bytes)} downloaded"
            if elapsed > 0:
                summary += f", {format_size(total_bytes / elapsed)}/s avg"
        summary += ")"
    log(summary + ".")

    # --- staging → library move -------------------------------------------
    if staging_dir:
        moved = 0
        for root, _dirs, files in os.walk(staging_dir):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, staging_dir)
                dst = os.path.join(out_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    if os.path.exists(dst):
                        os.remove(src)
                    else:
                        shutil.move(src, dst)
                    moved += 1
                except OSError as e:
                    log(f"[staging move warn] {rel}: {e}", level="WARN")
        log(f"Staging→library: {moved} file(s) moved to {out_dir}")
        # Remove empty staging subdirs
        for root, dirs, _files in os.walk(staging_dir, topdown=False):
            for d in dirs:
                p = os.path.join(root, d)
                try:
                    os.rmdir(p)
                except OSError:
                    pass

    # Same song from two links should be one entry with both links attached.
    if dedupe:
        try:
            import dedupe_library
            dedupe_library.run(dry_run=False)
        except Exception as e:
            log(f"[dedupe warn] {e}", level="WARN")

    not_done = sorted(j["index"] for j in all_jobs if j["index"] not in completed)
    save_failed_indices(out_dir, set(not_done))

    if not_done:
        log(f"Not finished: {len(not_done)} video(s): {not_done}", level="WARN")
        log(f"Rerun with --retry-failed to target exactly these, "
            f"or --resume {not_done[0]} to resume from the earliest gap onward.")
    else:
        log("Nothing left outstanding.")
    return len(completed), total


def parse_meta_args(pairs):
    result = {}
    for p in pairs or []:
        if "=" not in p:
            log(f"Ignoring malformed --meta value (expected KEY=VALUE): {p}")
            continue
        k, v = p.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def resume_type(value):
    return int(value)


def default_cookies(explicit=None):
    """Cookie jar for YouTube's "confirm you're not a bot" checks.

    Precedence: --cookies, then $YTDLP_COOKIES, then data/cookies.txt next to
    this script or in the project root (both ignored by git).
    """
    if explicit:
        return explicit
    env = os.environ.get("YTDLP_COOKIES")
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, "data", "cookies.txt"),
                 os.path.join(os.path.dirname(here), "data", "cookies.txt")):
        if os.path.isfile(path):
            return path
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="*", help="Playlist URL(s)")
    parser.add_argument("-f", "--file", help="Text file with one playlist URL per line")
    parser.add_argument("-o", "--output", default="./music", help="Final library directory")
    parser.add_argument("--staging", default=None,
                         help="Staging directory for in-progress downloads. "
                              "Files are moved here→output on success. "
                              "Default: <output>/.staging")
    parser.add_argument("--split-artist", action="store_true",
                         help="Split 'Artist - Title' video titles into separate tags")

    parser.add_argument("--format", dest="audio_format", default="mp3", choices=sorted(AUDIO_FORMATS),
                         help="Output audio format. Default: mp3")
    parser.add_argument("--thumbnail-format", default="jpg", choices=sorted(THUMBNAIL_FORMATS),
                         help="Cover art image format: jpg, png, gif, or webp. Default: jpg")
    parser.add_argument("--quality", default="192", help="Bitrate in kbps for lossy formats. Default: 192")

    parser.add_argument("--genre", help="Set genre tag on every track")
    parser.add_argument("--year", help="Set year/date tag on every track")
    parser.add_argument("--comment", help="Set comment tag on every track")
    parser.add_argument("--no-dedupe", action="store_true",
                         help="Skip the post-run duplicate fold (same song from two links "
                              "becomes one track with both links attached)")
    parser.add_argument("--no-lyrics", action="store_true",
                         help="Skip the lyrics lookup (LRCLIB) that writes a .lrc next to "
                              "each finished track")
    parser.add_argument("--meta", action="append", metavar="KEY=VALUE",
                         help="Set an arbitrary metadata field, repeatable")
    parser.add_argument("--no-thumbnail", action="store_true", help="Skip embedding cover art")

    parser.add_argument("--turbo", action="store_true",
                         help="Aggressive performance defaults: higher workers/fragments/"
                              "chunk-size/scan-workers, plus --fast-client")
    parser.add_argument("--workers", type=int, default=None,
                         help="Videos in parallel. Default: min(12, cores*2), or min(24, cores*4) with --turbo")
    parser.add_argument("--threads", type=int, default=2, help="ffmpeg encoding threads per video")
    parser.add_argument("--fragments", type=int, default=None,
                         help="Connections per video. Default: 16, or 32 with --turbo")
    parser.add_argument("--chunk-size", type=int, default=None,
                         help="HTTP chunk size in MiB. Default: 10, or 20 with --turbo")
    parser.add_argument("--scan-workers", type=int, default=None,
                         help="Parallel workers for the repair/fix-minor scan. "
                              "Default: min(24, cores*3), or min(48, cores*6) with --turbo")
    parser.add_argument("--fast-client", action="store_true",
                         help="Use a short yt-dlp client-fallback list (android+web) instead of "
                              "the full default set -- fewer requests per video. Compatible with "
                              "--cookies. Bundled automatically into --turbo.")

    parser.add_argument("--resume", nargs="?", const=True, default=True,
                         type=lambda v: resume_type(v) if v is not None else True,
                         metavar="N",
                         help="Resume from archive (default), or --resume N to jump to the Nth video")
    parser.add_argument("--no-resume", action="store_true", help="Ignore archive, start over")
    parser.add_argument("--retry-failed", action="store_true",
                         help="Retry exactly the videos recorded as failed/unfinished last run")
    parser.add_argument("--repair", action="store_true",
                         help="Clean up partial/corrupt files left by a crashed previous run")
    parser.add_argument("--fix-minor", action="store_true",
                         help="Patch missing metadata/cover art on otherwise-good files, "
                              "clean up stray leftover image files")
    parser.add_argument("--full-scan", action="store_true",
                         help="Ground-truth check: download whatever's genuinely missing on "
                              "disk vs. the real playlist listing")
    parser.add_argument("--fix-everything", action="store_true",
                         help="Shortcut for --repair --fix-minor --full-scan together")

    parser.add_argument("--relist", action="store_true",
                         help="Ignore the cached playlist listing, force a fresh fetch")
    parser.add_argument("--cache-minutes", type=int, default=30,
                         help="How long a cached playlist listing stays valid. Default: 30, 0=never cache")

    parser.add_argument("--max-retries", type=int, default=5, help="Per-video retry attempts")
    parser.add_argument("--retry-forever", action="store_true", help="Retry a failing video indefinitely")
    parser.add_argument("--retry-wait", type=int, default=5, help="Base seconds between retries (doubles, capped 60)")
    parser.add_argument("--listing-retries", type=int, default=5, help="Retries for playlist listing failures")
    parser.add_argument("--rate-limit-wait", type=int, default=60,
                         help="Base seconds to pause when YouTube rate limits us; doubles on each "
                              "further hit. Default: 60")
    parser.add_argument("--rate-limit-max-wait", type=int, default=1800,
                         help="Maximum length of a single rate-limit cooldown in seconds. Default: 1800")
    parser.add_argument("--rate-limit-max-total", type=int, default=7200,
                         help="Give up only after being continuously rate limited for this many "
                              "seconds (0 = wait indefinitely). Default: 7200")
    parser.add_argument("--cookies", metavar="PATH",
                         help="Path to a cookies.txt (Netscape format) for age-restricted or "
                              "members-only videos. Default: $YTDLP_COOKIES, else "
                              "data/cookies.txt when that file exists.")

    parser.add_argument("--log-file", metavar="PATH",
                         help="Also append the full timestamped log output to this file")
    parser.add_argument("--quiet", action="store_true",
                         help="Only print warnings/errors and the final summary; suppresses "
                              "the periodic progress heartbeat and per-video [done] lines "
                              "(still written to --log-file if given)")

    args = parser.parse_args()

    set_log_file(args.log_file)
    set_quiet(args.quiet)
    check_dependencies()

    RATE_LIMIT.base = max(5, args.rate_limit_wait)
    RATE_LIMIT.maximum = max(RATE_LIMIT.base, args.rate_limit_max_wait)
    RATE_LIMIT.max_total = max(0, args.rate_limit_max_total)

    urls = list(args.urls)
    if args.file:
        with open(args.file) as fh:
            urls += [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    if not urls:
        parser.error("Provide at least one playlist URL, or use -f/--file")

    resume_from = args.resume if isinstance(args.resume, int) and args.resume is not True else None

    cores = os.cpu_count() or 2
    workers = args.workers or (min(24, cores * 4) if args.turbo else min(12, cores * 2))
    fragments = args.fragments or (32 if args.turbo else 16)
    chunk_size = args.chunk_size or (20 if args.turbo else 10)
    scan_workers = args.scan_workers or (min(48, cores * 6) if args.turbo else min(24, cores * 3))
    fast_client = args.fast_client or args.turbo

    out_dir = args.output
    staging_dir = args.staging or os.path.join(out_dir, ".staging")
    if args.no_resume:
        archive_path = os.path.join(out_dir, ".archive.txt")
        if os.path.exists(archive_path):
            os.remove(archive_path)

    extra_meta = parse_meta_args(args.meta)
    if args.genre:
        extra_meta["genre"] = args.genre
    if args.year:
        extra_meta["date"] = args.year
    if args.comment:
        extra_meta["comment"] = args.comment

    repair = args.repair or args.fix_everything
    fix_minor = args.fix_minor or args.fix_everything
    full_scan = args.full_scan or args.fix_everything

    done, total = download_playlists(
        urls, out_dir, args.split_artist, args.quality, workers, args.threads,
        fragments, resume_from, not args.no_thumbnail, args.audio_format,
        args.thumbnail_format, chunk_size, extra_meta, args.max_retries,
        args.retry_forever, args.retry_wait, args.listing_retries,
        args.retry_failed, repair, fix_minor, full_scan, default_cookies(args.cookies),
        fast_client, scan_workers, args.relist, args.cache_minutes,
        lyrics=not args.no_lyrics, dedupe=not args.no_dedupe,
    )
    log(f"\nDone. Files are in: {os.path.abspath(out_dir)}")
    if total and done == 0:
        log("No videos completed this run; treating the request as failed.", level="ERROR")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nInterrupted.", level="WARN")
        sys.exit(1)
    except Exception as e:
        log(f"Fatal error: {e}", level="ERROR")
        sys.exit(1)
