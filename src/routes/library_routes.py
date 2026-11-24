"""API route registration — library, playback, and track endpoints."""
from flask import Blueprint, request, jsonify, send_file, Response, session
import json, os, re, time

from auth import _auth_uid, login_required, admin_required
from database import _db, liked_ids, track_dict
from config import MUSIC_DIR, AUDIO_EXTS
import mutagen
from mutagen.id3 import ID3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC

bp = Blueprint("library_api", __name__)

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
    return title, artist, album, track_no, genre, year, dur


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


def read_cover(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".mp3":
            for k, fr in ID3(path).items():
                if k.startswith("APIC"):
                    return fr.data, fr.mime
        elif ext in (".m4a", ".aac"):
            c = (MP4(path).tags or {}).get("covr")
            if c:
                mime = "image/png" if c[0].imageformat == MP4Cover.FORMAT_PNG else "image/jpeg"
                return bytes(c[0]), mime
        elif ext == ".flac":
            p = FLAC(path).pictures
            if p:
                return p[0].data, p[0].mime
    except Exception:
        pass
    return None


def _track_path(tid):
    r = _db().execute("select path from tracks where id=?", (tid,)).fetchone()
    if not r:
        return None
    p = os.path.realpath(os.path.join(MUSIC_DIR, r["path"]))
    return p if p.startswith(MUSIC_DIR) and os.path.exists(p) else None


# --------------------------------------------------------------------------- tracks
@bp.get("/api/tracks")
@login_required
def tracks():
    """Paginated track list; `q` matches title, artist or album."""
    q = request.args.get("q", "").strip()
    try:
        limit = min(max(int(request.args.get("limit", 200)), 1), 2000)
        off = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        return jsonify(error="bad paging parameters"), 400
    L = liked_ids(_db(), session["uid"])
    if q:
        like = f"%{q}%"
        rows = _db().execute(
            """select * from tracks where title like ? or artist like ? or album like ? or genre like ?
               order by artist, album, track_no limit ? offset ?""",
            (like, like, like, like, limit, off),
        )
    else:
        rows = _db().execute(
            "select * from tracks order by artist, album, track_no limit ? offset ?", (limit, off)
        )
    return jsonify(tracks=[track_dict(_db(), r, L) for r in rows])


@bp.get("/api/search")
@login_required
def search():
    """Combined search over tracks, albums and artists for the v3 client."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(tracks=[], albums=[], artists=[])
    like, c = f"%{q}%", _db()
    L = liked_ids(c, session["uid"])
    tr = c.execute(
        """select * from tracks where title like ? or artist like ? or album like ? or genre like ?
           order by (title like ?) desc, artist, album, track_no limit 60""",
        (like, like, like, like, f"{q}%"),
    )
    al = c.execute(
        "select album, artist, count(*) n, min(id) cover_id from tracks where album like ? "
        "group by album order by album collate nocase limit 12", (like,)
    )
    # Search should offer every credited artist, not the raw "A, B" string
    # stored in tracks.artist for a collaboration.
    ar = c.execute(
        "select artist, n, cover_id from ("
        " select a.artist_key, "
        " (select x.artist from track_artists x where x.artist_key=a.artist_key "
        "   and x.artist <> '' and x.artist not like 'Unknown%' "
        "   group by x.artist order by count(*) desc, x.artist collate nocase limit 1) artist, "
        " count(distinct a.track_id) n, min(a.track_id) cover_id "
        " from track_artists a join tracks t on t.id=a.track_id "
        " where (a.artist like ? or t.artist like ?) "
        "   and a.artist <> '' and a.artist not like 'Unknown%' "
        " group by a.artist_key"
        ") order by artist collate nocase limit 12", (like, like)
    )
    return jsonify(
        tracks=[track_dict(c, r, L) for r in tr],
        albums=[dict(r) for r in al],
        artists=[dict(r) for r in ar],
    )


@bp.get("/api/albums")
@login_required
def albums():
    """Album rows with track count and a cover id, paged for the 1000+ grid.

    q filters on album or artist, sort is name/artist/recent, and
    min_tracks keeps one-song \"albums\" out of the default view.
    """
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "name")
    try:
        min_tracks = max(1, int(request.args.get("min_tracks", 1)))
        limit = min(200, max(1, int(request.args.get("limit", 60))))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        return jsonify(error="bad paging parameters"), 400

    where = "where album <> ''"
    params: list = []
    if q:
        where += " and (album like ? or artist like ?)"
        params += [f"%{q}%", f"%{q}%"]

    order = {
        "artist": "artist collate nocase, album collate nocase",
        "recent": "max(id) desc",
    }.get(sort, "album collate nocase")

    db = _db()
    rows = db.execute(
        "select album, artist, count(*) n, min(id) cover_id, max(id) added_id "
        f"from tracks {where} group by album having count(*) >= ? "
        f"order by {order} limit ? offset ?",
        (*params, min_tracks, limit, offset),
    ).fetchall()
    total = db.execute(
        "select count(*) n from (select album from tracks "
        f"{where} group by album having count(*) >= ?)",
        (*params, min_tracks),
    ).fetchone()["n"]
    # Cheap ETag so clients/proxies can revalidate quickly.
    fp = f"{total}:{rows[0]['added_id'] if rows else 0}:{min_tracks}:{sort}:{q}:{offset}:{limit}"
    etag = f'W/"albums-{abs(hash(fp)) & 0x7fffffff:x}"'
    if request.headers.get("If-None-Match") == etag:
        resp = Response(status=304)
        resp.headers["Cache-Control"] = "private, max-age=30"
        resp.headers["ETag"] = etag
        return resp
    resp = jsonify(albums=[dict(r) for r in rows], total=total, limit=limit, offset=offset)
    resp.headers["Cache-Control"] = "private, max-age=30"
    resp.headers["ETag"] = etag
    return resp


@bp.get("/api/album")
@login_required
def album():
    """Tracks for one album name, ordered by disc/track number."""
    L = liked_ids(_db(), session["uid"])
    rows = _db().execute(
        "select * from tracks where album=? order by track_no, title", (request.args.get("name", ""),)
    )
    return jsonify(tracks=[track_dict(_db(), r, L) for r in rows])


@bp.get("/api/artists")
@login_required
def artists():
    """Artists grouped by normalized key so spelling variants share one page."""
    # Grouped by artist_key so "Uraru" and "うらる" are one artist; the most
    # common spelling becomes the display name.
    rows = _db().execute(
        "select a.artist_key, "
        "(select x.artist from track_artists x where x.artist_key=a.artist_key "
        "  and x.artist <> '' and x.artist not like 'Unknown%' "
        "  group by x.artist order by count(*) desc, x.artist collate nocase limit 1) artist, "
        "count(distinct t.id) n, count(distinct t.album) albums, min(t.id) cover_id "
        "from track_artists a join tracks t on t.id=a.track_id "
        "where a.artist <> '' and a.artist not like 'Unknown%' "
        "group by a.artist_key order by artist collate nocase"
    )
    return jsonify(artists=[dict(r) for r in rows])


@bp.get("/api/artist")
@login_required
def artist():
    """Tracks credited to one artist, collaborations included."""
    L = liked_ids(_db(), session["uid"])
    # Collabs: a track credited "A, B" belongs to both artist pages. The key
    # also folds case, spacing and kana spelling variants together.
    from artists import norm_key
    name = request.args.get("name", "")
    key = norm_key(name) or name.casefold()
    if key in {"", "unknown", "unknown artist", "unknownartist"}:
        return jsonify(tracks=[])
    rows = _db().execute(
        "select t.* from tracks t join track_artists a on a.track_id=t.id "
        "where a.artist_key=? order by t.album, t.track_no, t.title",
        (key,)
    )
    return jsonify(tracks=[track_dict(_db(), r, L) for r in rows])


@bp.patch("/api/tracks/<int:tid>")
@admin_required
def track_patch(tid):
    """Update mutable track fields (currently the explicit flag)."""
    d = request.get_json(silent=True) or {}
    if "explicit" in d:
        v = d["explicit"]
        _db().execute("update tracks set explicit_ovr=? where id=?", (None if v is None else int(bool(v)), tid))
        _db().commit()
    r = _db().execute("select * from tracks where id=?", (tid,)).fetchone()
    if not r:
        return jsonify(error="not found"), 404
    return jsonify(track_dict(_db(), r))


@bp.delete("/api/tracks/<int:tid>")
@admin_required
def track_delete(tid):
    """Remove a track for good: the row, the file and anything pointing at it."""
    c = _db()
    row = c.execute("select id, title, artist, path from tracks where id=?", (tid,)).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    path = _track_path(tid)

    c.execute("delete from tracks where id=?", (tid,))
    # playback.track_id and devices.current_track_id have no foreign key, so a
    # deleted row would otherwise leave those pointing at nothing.
    c.execute(
        "update playback set track_id=null, playing=0, position=0 where track_id=?",
        (tid,),
    )
    for pb in c.execute("select user_id, queue from playback where queue is not null").fetchall():
        try:
            ids = json.loads(pb["queue"] or "[]")
        except (TypeError, ValueError):
            continue
        if tid in ids:
            c.execute(
                "update playback set queue=? where user_id=?",
                (json.dumps([i for i in ids if i != tid]), pb["user_id"]),
            )
    c.execute(
        "update devices set current_track_id=null, current_position=0, current_paused=1 "
        "where current_track_id=?",
        (tid,),
    )
    c.commit()

    removed = False
    if path:
        try:
            os.remove(path)
            removed = True
        except OSError:
            pass

    return jsonify(ok=True, id=tid, title=row["title"], artist=row["artist"], file_removed=removed)


@bp.get("/api/tracks/<int:tid>/stream")
@login_required
def stream(tid):
    """Stream the audio file with range support so the player can seek."""
    p = _track_path(tid)
    if not p:
        return jsonify(error="not found"), 404
    return send_file(p, conditional=True)


@bp.get("/api/tracks/<int:tid>/sources")
@login_required
def track_sources(tid):
    """YouTube sources recorded for a track (one row per download)."""
    rows = _db().execute(
        "select yt_id, url, title, added from track_sources where track_id=? order by added",
        (tid,),
    )
    return jsonify(sources=[dict(r) for r in rows])


@bp.get("/api/tracks/<int:tid>/lyrics")
@login_required
def track_lyrics(tid):
    """Stored or synced lyrics, fetched and cached on first request."""
    r = _db().execute(
        "select lyrics, lyrics_source, title, artist, album, duration from tracks where id=?", (tid,)
    ).fetchone()
    if not r:
        return jsonify(error="not found"), 404
    text, source = r["lyrics"] or "", r["lyrics_source"] or ""
    if not text.strip():
        # First listen pays the lookup; later ones read the stored copy.
        from lyrics import lookup, save
        found = lookup(r["title"] or "", r["artist"] or "", r["duration"], r["album"] or "")
        if found:
            text, source = found
            save(tid, text, source)
    return jsonify(lyrics=text, source=source,
                   title=r["title"], artist=r["artist"])


@bp.get("/api/tracks/<int:tid>/cover")
@login_required
def cover(tid):
    """Embedded cover art for a track, with content-type sniffing."""
    p = _track_path(tid)
    c = read_cover(p) if p else None
    if not c:
        return jsonify(error="no cover"), 404
    try:
        st = os.stat(p)
        etag = f'W/"{st.st_mtime_ns}-{st.st_size}"'
    except OSError:
        etag = None
    inm = request.headers.get("If-None-Match")
    if etag and inm and inm == etag:
        resp = Response(status=304)
    else:
        resp = Response(c[0], mimetype=c[1])
    resp.headers["Cache-Control"] = "private, max-age=86400"
    if etag:
        resp.headers["ETag"] = etag
    return resp
