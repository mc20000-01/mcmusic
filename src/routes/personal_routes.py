"""API route registration — playlists, likes, plays, recommendations, home, radio."""
from flask import Blueprint, request, jsonify, session
import math, random, time
from collections import defaultdict

from auth import _auth_uid, login_required
from database import _db, liked_ids, track_dict

bp = Blueprint("personal_api", __name__)


# --------------------------------------------------------------------------- plays / likes
@bp.post("/api/plays")
@login_required
def add_play():
    d = request.get_json(silent=True) or {}
    try:
        tid = int(d.get("track_id") or 0)
    except (TypeError, ValueError):
        tid = 0
    c = _db()
    if not tid or not c.execute("select 1 from tracks where id=?", (tid,)).fetchone():
        return jsonify(error="unknown track"), 400
    c.execute(
        "insert into plays(user_id,track_id,ts,completed) values(?,?,?,?)",
        (session["uid"], tid, time.time(), int(bool(d.get("completed")))),
    )
    c.commit()
    _refresh_faves(c, session["uid"])
    return jsonify(ok=True)


@bp.post("/api/like/<int:tid>")
@login_required
def like(tid):
    c, uid = _db(), session["uid"]
    if not c.execute("select 1 from tracks where id=?", (tid,)).fetchone():
        return jsonify(error="not found"), 404
    if c.execute("select 1 from likes where user_id=? and track_id=?", (uid, tid)).fetchone():
        c.execute("delete from likes where user_id=? and track_id=?", (uid, tid))
        liked = False
    else:
        c.execute("insert into likes values(?,?,?)", (uid, tid, time.time()))
        liked = True
    c.commit()
    return jsonify(liked=liked)


@bp.get("/api/likes")
@login_required
def likes():
    rows = _db().execute(
        """select t.* from likes l join tracks t on t.id=l.track_id
           where l.user_id=? order by l.ts desc""", (session["uid"],)
    )
    return jsonify(tracks=[track_dict(_db(), r, {r["id"]}) for r in rows])


# --------------------------------------------------------------------------- playlists
def _own_pl(pid):
    return _db().execute("select * from playlists where id=? and user_id=?", (pid, session["uid"])).fetchone()


def _faves_id(c, uid):
    row = c.execute(
        "select id from playlists where user_id=? and name='Faves'", (uid,)
    ).fetchone()
    if row:
        return row["id"]
    return c.execute(
        "insert into playlists(user_id,name,created) values(?,?,?)",
        (uid, "Faves", time.time()),
    ).lastrowid


def _refresh_faves(c, uid):
    """Keep the automatic Faves playlist on your most-repeated tracks."""
    pid = _faves_id(c, uid)
    top = c.execute(
        "select track_id, count(*) n from plays where user_id=? group by track_id "
        "having n > 1 order by n desc, max(ts) desc limit 40", (uid,)
    ).fetchall()
    c.execute("delete from playlist_tracks where playlist_id=?", (pid,))
    for i, r in enumerate(top):
        c.execute(
            "insert or ignore into playlist_tracks(playlist_id,track_id,pos) values(?,?,?)",
            (pid, r["track_id"], i),
        )
    c.commit()
    return pid


@bp.post("/api/download/collection")
@login_required
def download_collection():
    """Queue server downloads for liked songs, Faves, or one playlist."""
    d = request.get_json(silent=True) or {}
    kind = str(d.get("kind", "likes"))
    c, uid = _db(), session["uid"]
    if kind == "likes":
        rows = c.execute("select track_id from likes where user_id=?", (uid,)).fetchall()
    elif kind == "faves":
        pid = _refresh_faves(c, uid)
        rows = c.execute(
            "select track_id from playlist_tracks where playlist_id=? order by pos", (pid,)
        ).fetchall()
    elif kind == "playlist":
        try:
            pid = int(d.get("id") or 0)
        except (TypeError, ValueError):
            pid = 0
        if not _own_pl(pid):
            return jsonify(error="not found"), 404
        rows = c.execute(
            "select track_id from playlist_tracks where playlist_id=? order by pos", (pid,)
        ).fetchall()
    else:
        return jsonify(error="unknown collection"), 400

    from routes.system_routes import dl_q
    queued = 0
    skipped = 0
    for r in rows:
        src = c.execute(
            "select url from track_sources where track_id=? order by added limit 1",
            (r["track_id"],),
        ).fetchone()
        if not src or not src["url"]:
            skipped += 1
            continue
        dup = c.execute(
            "select 1 from requests where url=? and status in ('pending','approved','running')",
            (src["url"],),
        ).fetchone()
        if dup:
            skipped += 1
            continue
        cur = c.execute(
            "insert into requests(url,user_id,status,created) values(?,?,'approved',?)",
            (src["url"], uid, time.time()),
        )
        dl_q.put(cur.lastrowid)
        queued += 1
    c.commit()
    return jsonify(ok=True, queued=queued, skipped=skipped)


@bp.get("/api/playlists")
@login_required
def playlists():
    _refresh_faves(_db(), session["uid"])
    rows = _db().execute(
        """select p.id, p.name, count(pt.track_id) n,
                 (select track_id from playlist_tracks where playlist_id=p.id order by pos limit 1) cover_id
           from playlists p left join playlist_tracks pt on pt.playlist_id=p.id
           where p.user_id=? group by p.id order by p.name collate nocase""", (session["uid"],)
    )
    return jsonify(playlists=[dict(r) for r in rows])


@bp.post("/api/playlists")
@login_required
def playlist_create():
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()[:100]
    if not name:
        return jsonify(error="name required"), 400
    cur = _db().execute(
        "insert into playlists(user_id,name,created) values(?,?,?)", (session["uid"], name, time.time())
    )
    _db().commit()
    return jsonify(id=cur.lastrowid, name=name)


@bp.get("/api/playlists/<int:pid>")
@login_required
def playlist_get(pid):
    p = _own_pl(pid)
    if not p:
        return jsonify(error="not found"), 404
    L = liked_ids(_db(), session["uid"])
    rows = _db().execute(
        """select t.* from playlist_tracks pt join tracks t on t.id=pt.track_id
           where pt.playlist_id=? order by pt.pos""", (pid,)
    )
    return jsonify(id=pid, name=p["name"], tracks=[track_dict(_db(), r, L) for r in rows])


@bp.patch("/api/playlists/<int:pid>")
@login_required
def playlist_rename(pid):
    if not _own_pl(pid):
        return jsonify(error="not found"), 404
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()[:100]
    if not name:
        return jsonify(error="name required"), 400
    _db().execute("update playlists set name=? where id=?", (name, pid))
    _db().commit()
    return jsonify(ok=True)


@bp.delete("/api/playlists/<int:pid>")
@login_required
def playlist_delete(pid):
    if not _own_pl(pid):
        return jsonify(error="not found"), 404
    _db().execute("delete from playlists where id=?", (pid,))
    _db().commit()
    return jsonify(ok=True)


@bp.post("/api/playlists/<int:pid>/tracks")
@login_required
def playlist_add(pid):
    if not _own_pl(pid):
        return jsonify(error="not found"), 404
    tid = int((request.get_json(silent=True) or {}).get("track_id", 0))
    if not _db().execute("select 1 from tracks where id=?", (tid,)).fetchone():
        return jsonify(error="no such track"), 404
    pos = _db().execute(
        "select coalesce(max(pos),0)+1 p from playlist_tracks where playlist_id=?", (pid,)
    ).fetchone()["p"]
    _db().execute("insert or ignore into playlist_tracks values(?,?,?)", (pid, tid, pos))
    _db().commit()
    return jsonify(ok=True)


@bp.delete("/api/playlists/<int:pid>/tracks/<int:tid>")
@login_required
def playlist_remove(pid, tid):
    if not _own_pl(pid):
        return jsonify(error="not found"), 404
    _db().execute("delete from playlist_tracks where playlist_id=? and track_id=?", (pid, tid))
    _db().commit()
    return jsonify(ok=True)


# --------------------------------------------------------------------------- recommendations
def affinity(uid):
    A, B, G = defaultdict(float), defaultdict(float), defaultdict(float)
    now = time.time()
    c = _db()

    def add(r, w):
        A[r["artist"]] += w
        B[r["album"]] += w * 0.7
        if r["genre"]:
            G[r["genre"]] += w * 0.5

    for r in c.execute(
        """select p.completed, p.ts, t.artist, t.album, t.genre from plays p
           join tracks t on t.id=p.track_id where p.user_id=? and p.ts>?""",
        (uid, now - 90 * 86400),
    ):
        add(r, (1.0 if r["completed"] else 0.3) * 0.5 ** ((now - r["ts"]) / (30 * 86400)))
    for r in c.execute(
        "select t.artist, t.album, t.genre from likes l join tracks t on t.id=l.track_id where l.user_id=?", (uid,)
    ):
        add(r, 3.0)
    for d in (A, B, G):
        m = max(d.values(), default=0)
        if m:
            for k in d:
                d[k] /= m
    return A, B, G


def recommend(uid, n=30, unplayed_only=False):
    c = _db()
    A, B, G = affinity(uid)
    ever = {r["track_id"] for r in c.execute("select distinct track_id from plays where user_id=?", (uid,))}
    recent = {r["track_id"] for r in c.execute(
        "select distinct track_id from plays where user_id=? and ts>?", (uid, time.time() - 2 * 86400)
    )}
    scored = []
    for t in c.execute("select * from tracks"):
        if unplayed_only and t["id"] in ever:
            continue
        s = 0.6 * A.get(t["artist"], 0) + 0.25 * B.get(t["album"], 0) + 0.15 * G.get(t["genre"], 0)
        s += __import__("math").log10(1 + (t["yt_likes"] or 0)) / 7 * 0.05
        if t["id"] in recent:
            s *= 0.2
        elif t["id"] not in ever:
            s += 0.05
        scored.append((s + random.random() * 0.12, t))
    scored.sort(key=lambda x: -x[0])
    out, per_artist = [], defaultdict(int)
    for _, t in scored:
        if per_artist[t["artist"]] >= 5:
            continue
        per_artist[t["artist"]] += 1
        out.append(t)
        if len(out) >= n:
            break
    return out


@bp.get("/api/home")
@login_required
def home():
    uid, c = session["uid"], _db()
    L = liked_ids(c, uid)
    top = c.execute(
        """select t.* from plays p join tracks t on t.id=p.track_id where p.user_id=?
           group by t.id order by count(*) desc limit 20""", (uid,)
    )
    recent = c.execute("select * from tracks order by added desc limit 20")
    popular = c.execute(
        "select * from tracks where yt_likes is not null order by yt_likes desc limit 20"
    )
    secs = [
        ("Made for you", recommend(uid, 30)),
        ("Discover", recommend(uid, 20, unplayed_only=True)),
        ("Your top tracks", top),
        ("Recently added", recent),
        ("Most liked on YouTube", popular),
    ]
    albums_ = c.execute(
        """select album, artist, count(*) n, min(id) cover_id from tracks
           group by album order by max(added) desc limit 14"""
    )
    return jsonify(
        sections=[{"title": t, "tracks": [track_dict(c, r, L) for r in rows]} for t, rows in secs if rows],
        albums=[dict(r) for r in albums_],
    )


@bp.get("/api/radio/<int:tid>")
@login_required
def radio(tid):
    seed = _db().execute("select * from tracks where id=?", (tid,)).fetchone()
    if not seed:
        return jsonify(error="not found"), 404
    scored = []
    for t in _db().execute("select * from tracks where id!=?", (tid,)):
        s = (1.0 if t["artist"] == seed["artist"] else 0) + (0.8 if t["album"] == seed["album"] else 0) \
            + (0.5 if seed["genre"] and t["genre"] == seed["genre"] else 0) + random.random() * 0.6
        scored.append((s, t))
    scored.sort(key=lambda x: -x[0])
    L = liked_ids(_db(), session["uid"])
    return jsonify(tracks=[track_dict(_db(), t, L) for _, t in scored[:40]])
