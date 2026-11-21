"""Library scan + YouTube enrichment background workers (extracted from monolith)."""
import json, os, re, time, threading, queue, random
import mutagen
from mutagen.id3 import ID3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC

from config import MUSIC_DIR, AUDIO_EXTS, YT_ENRICH, YT_HOSTS
from database import _db
from artists import index_track

# Ensure tables exist for rotur_codes (kept for legacy code flow)
CREATE_ROTUR_CODES = """
create table if not exists rotur_codes(
  code text primary key,
  user_id integer references users(id) on delete cascade,
  created real,
  expires real,
  used integer default 0
);
create index if not exists rotur_codes_user on rotur_codes(user_id);
"""


YT_ID_RE = re.compile(r"(?:youtube\.com/watch\?[^\s'\"]*?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{11})")
KEY_OK = re.compile(r"purl|comment|cmt|^comm", re.I)
KEY_BAD = re.compile(r"desc|synop|lyr|uslt", re.I)


def _first(tags, key, default=""):
    try:
        v = tags.get(key) if tags else None
        return str(v[0]).strip() if v else default
    except Exception:
        return default


def read_tags(full, rel):
    base = os.path.splitext(os.path.basename(rel))[0]
    title = re.sub(r"^\d+\s*-\s*", "", base)
    # Never derive the album from the folder: for downloads that is just the
    # name of the playlist the track came from. A track with no album of its
    # own falls back to the song name.
    album = ""
    artist, track_no, genre, year, dur = "Unknown Artist", 0, "", "", 0.0
    try:
        f = mutagen.File(full, easy=True)
        if f is not None:
            dur = float(getattr(f.info, "length", 0) or 0)
            tg = f.tags
            title = _first(tg, "title", title) or title
            artist = _first(tg, "artist", artist) or artist
            album = _first(tg, "album")
            genre = _first(tg, "genre")
            year = _first(tg, "date")[:4]
            m = re.match(r"\d+", _first(tg, "tracknumber", "0"))
            track_no = int(m.group()) if m else 0
    except Exception:
        pass
    album = album or title
    artist = re.sub(r"\s*-\s*Topic$", "", artist)
    lyrics, lyrics_source = read_lyrics(full)
    return title, artist, album, track_no, genre, year, dur, lyrics, lyrics_source


def read_lyrics(full):
    """Lyrics from a sidecar .lrc file, else an embedded USLT/©lyr tag."""
    text, source = "", ""
    lrc = os.path.splitext(full)[0] + ".lrc"
    try:
        if os.path.exists(lrc) and os.path.getsize(lrc) > 0:
            with open(lrc, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            source = "lrc"
    except OSError:
        pass
    if not text.strip():
        try:
            f = mutagen.File(full)
            tags = getattr(f, "tags", None) or {}
            for k, v in tags.items():
                if str(k).startswith(("USLT", "LYRICS", "\xa9lyr")):
                    text = str(v)
                    source = "tag"
                    break
        except Exception:
            pass
    text = (text or "").strip()
    return (text, source) if text else ("", "")


def read_yt_sidecar(full):
    """YouTube metadata the downloader saved next to the audio (<stem>.yt.json)."""
    path = os.path.splitext(full)[0] + ".yt.json"
    try:
        if not os.path.exists(path):
            return None
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def read_yt_id(full):
    try:
        f = mutagen.File(full)
        if f is None or not f.tags:
            return None
        for k, v in f.tags.items():
            ks = str(k)
            if ks.startswith("APIC") or ks == "covr" or KEY_BAD.search(ks) or not KEY_OK.search(ks):
                continue
            m = YT_ID_RE.search(str(v)[:2000])
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


scan_lock = threading.Lock()


def scan_library(conn):
    """Walk MUSIC_DIR, upsert tracks, remove deleted files, optionally enqueue YT enrichment."""
    with scan_lock:
        known = {r["path"]: r["mtime"] for r in conn.execute("select path, mtime from tracks")}
        seen = set()
        for root, dirs, files in os.walk(MUSIC_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if os.path.splitext(f)[1].lower() not in AUDIO_EXTS:
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, MUSIC_DIR)
                seen.add(rel)
                try:
                    mt = os.path.getmtime(full)
                except OSError:
                    continue
                if known.get(rel) == mt:
                    continue
                title, artist, album, no, genre, year, dur, lyrics, lsrc = read_tags(full, rel)
                yt = read_yt_sidecar(full) or {}
                genre = genre or (yt.get("genre") or "") or ""
                year = year or str(yt.get("upload_date") or "")[:4]
                album = album if not yt.get("album") else yt["album"]
                artist = (yt.get("artist") or yt.get("creator") or artist) or artist
                yt_id = yt.get("id") or read_yt_id(full)
                yt_tags = json.dumps(yt.get("tags") or []) if yt.get("tags") else None
                for extra in (".lrc", ".yt.json"):
                    try:
                        mt = max(mt, os.path.getmtime(os.path.splitext(full)[0] + extra))
                    except OSError:
                        pass
                conn.execute(
                    """insert into tracks(path,title,artist,album,track_no,genre,year,duration,
                                          mtime,added,yt_id,lyrics,lyrics_source,yt_tags)
                       values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                       on conflict(path) do update set title=excluded.title, artist=excluded.artist,
                       album=excluded.album, track_no=excluded.track_no, genre=excluded.genre,
                       year=excluded.year, duration=excluded.duration, mtime=excluded.mtime,
                       yt_id=coalesce(excluded.yt_id, tracks.yt_id),
                       lyrics=excluded.lyrics, lyrics_source=excluded.lyrics_source,
                       yt_tags=coalesce(excluded.yt_tags, tracks.yt_tags)""",
                    (rel, title, artist, album, no, genre, year, dur, mt, time.time(),
                     yt_id, lyrics, lsrc, yt_tags),
                )
                tid = conn.execute("select id from tracks where path=?", (rel,)).fetchone()[0]
                index_track(conn, tid, artist, title)
                if yt:
                    # Sidecar knowledge is better than a later API round trip.
                    conn.execute(
                        """update tracks set yt_views=?, yt_likes=?, yt_channel=?, yt_date=?,
                                  yt_checked=? where path=?""",
                        (yt.get("view_count"), yt.get("like_count"),
                         yt.get("channel") or yt.get("uploader"), yt.get("upload_date"),
                         time.time(), rel),
                    )
        for rel in set(known) - seen:
            conn.execute(
                "delete from track_artists where track_id in (select id from tracks where path=?)",
                (rel,),
            )
            conn.execute("delete from tracks where path=?", (rel,))
        conn.commit()
    if YT_ENRICH:
        queue_enrich(conn)


# --------------------------------------------------------------------------- YouTube enrichment
yt_q = queue.Queue()
yt_pending = set()
yt_lock = threading.Lock()
yt_blocked_until = 0.0
yt_backoff = 0.0

YT_RATE_RE = re.compile(
    r"(?:http error 429|too many requests|rate[- ]?limit|ratelimit|"
    r"confirm you[’']re not a bot|http error 403|403: forbidden|"
    r"temporarily blocked|please try again later)", re.I
)


def queue_enrich(conn):
    n = 0
    for r in conn.execute("select id from tracks where yt_id is not null and yt_checked is null"):
        with yt_lock:
            if r["id"] in yt_pending:
                continue
            yt_pending.add(r["id"])
        yt_q.put(r["id"])
        n += 1
    return n


def yt_rate_limited(exc):
    return bool(YT_RATE_RE.search(str(exc or "")))


def yt_worker():
    global yt_blocked_until, yt_backoff
    conn = _db()
    while True:
        tid = yt_q.get()
        retry = False
        try:
            while True:
                delay = yt_blocked_until - time.time()
                if delay <= 0:
                    break
                time.sleep(min(5.0, delay))
            r = conn.execute("select yt_id from tracks where id=?", (tid,)).fetchone()
            if r and r["yt_id"]:
                info = None
                try:
                    import yt_dlp
                    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True,
                                           "noplaylist": True, "socket_timeout": 20}) as y:
                        info = y.extract_info("https://www.youtube.com/watch?v=" + r["yt_id"], download=False)
                    yt_backoff = 0.0
                except Exception as e:
                    if yt_rate_limited(e):
                        yt_backoff = min(1800.0, 60.0 if yt_backoff <= 0 else yt_backoff * 2)
                        yt_blocked_until = time.time() + yt_backoff * random.uniform(0.9, 1.1)
                        retry = True
                if info:
                    title = info.get("title") or ""
                    ex = 1 if (info.get("age_limit") or 0) >= 18 or re.search(r"[\(\[]\s*explicit\s*[\)\]]", title, re.I) else 0
                    conn.execute("""update tracks set yt_likes=?, yt_views=?, yt_channel=?, yt_date=?,
                                    explicit_auto=?, yt_checked=? where id=?""",
                                 (info.get("like_count"), info.get("view_count"),
                                  info.get("channel") or info.get("uploader"), info.get("upload_date"),
                                  ex, time.time(), tid))
                elif not retry:
                    conn.execute("update tracks set yt_checked=? where id=?", (time.time(), tid))
                conn.commit()
        except Exception:
            pass
        finally:
            with yt_lock:
                yt_pending.discard(tid)
                if retry:
                    yt_pending.add(tid)
            if retry:
                yt_q.put(tid)
        time.sleep(1.5)


# Backfill rotur_codes table for existing databases (legacy support)
def ensure_rotur_codes_table():
    conn = _db()
    conn.executescript(CREATE_ROTUR_CODES)
    conn.commit()
