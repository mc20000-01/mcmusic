"""API route registration — listen-along rooms, download requests, devices, admin."""
from flask import (
    Blueprint, request, jsonify, session, Response, send_file, current_app,
)
from html import escape
from urllib.parse import quote
import os, secrets, threading, time, shlex, subprocess, shutil, math
from collections import defaultdict

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from auth import (
    _auth_uid, login_required, admin_required, is_bot_request,
    create_device_code, claim_device_code, list_device_tokens,
    revoke_device_token,
)
from database import _db, track_dict, liked_ids
from library_scan import scan_library

bp = Blueprint("system_api", __name__)
START_TIME = time.time()

# --------------------------------------------------------------------------- config refs
from config import (
    MUSIC_DIR, DL_SCRIPT, DL_ARGS, STAGING_DIR, AUTO_APPROVE, LOG_DIR, API_RATE_LIMIT,
    PUBLIC_URL,
)

@bp.get("/api/ping")
def api_ping():
    """Cheap health check that also tells a native client whether a token works."""
    uid = _auth_uid()
    user = None
    if uid is not None:
        r = _db().execute(
            "select id, username, is_admin from users where id=?", (uid,)
        ).fetchone()
        if r:
            user = {
                "id": r["id"], "username": r["username"],
                "is_admin": bool(r["is_admin"]),
            }
    return jsonify(
        ok=True, service="mcmusic", api=3, user=user,
        uptime=round(time.time() - START_TIME, 1), time=time.time(),
    )


# --------------------------------------------------------------------------- listen-along rooms (in-memory, single worker)
rooms = {}
rooms_lock = threading.Lock()
ROOM_STALE = 45


def _prune_rooms():
    now = time.time()
    for code in [c for c, r in rooms.items() if now - r["ts"] > 6 * 3600]:
        del rooms[code]


def personal_room_code(uid: int) -> str:
    """The account's permanent room code, so its invite link never changes."""
    c = _db()
    row = c.execute("select room_code from users where id=?", (uid,)).fetchone()
    code = (row["room_code"] if row else "") or ""
    if not code:
        code = secrets.token_urlsafe(6)
        c.execute("update users set room_code=? where id=?", (code, uid))
        c.commit()
    return code


def room_url(uid: int) -> str:
    """Absolute listen-along invite link for an account."""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    return f"{base}/#room={personal_room_code(uid)}"


def _public_account(username):
    """Resolve a username to its account and current playback, without auth."""
    c = _db()
    account = c.execute(
        "select id, username from users where username=? collate nocase",
        (username,),
    ).fetchone()
    if not account:
        return None, None
    playback = c.execute(
        """select p.track_id, p.position, p.playing, p.updated,
                  t.title, t.artist, t.album
             from playback p left join tracks t on t.id=p.track_id
            where p.user_id=? limit 1""",
        (account["id"],),
    ).fetchone()
    return account, playback


@bp.get("/u/<username>")
def public_profile(username):
    """A no-login profile card suitable for a Discord/Rotur status link."""
    account, now = _public_account(username)
    if not account:
        return Response("<h1>Profile not found</h1>", status=404, mimetype="text/html")

    base = PUBLIC_URL or request.url_root.rstrip("/")
    name = account["username"]
    profile_url = f"{base}/u/{quote(name)}"
    track_id = now["track_id"] if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    cover_ver = f"{int(track_id)}-{updated}" if track_id else str(updated or int(time.time() // 60))
    cover_url = f"{base}/u/{quote(name)}/cover.png?v={quote(cover_ver)}"
    track = now["title"] if now and now["title"] else ""
    artist = now["artist"] if now and now["artist"] else ""
    album = now["album"] if now and now["album"] else ""
    listening = bool(now and now["playing"] and track)
    if track:
        detail = f"{track} — {artist}" if artist else track
        state = "Listening now" if listening else "Paused"
    else:
        detail = "Nothing playing at the moment"
        state = "mcmusic"
    title = f"{name} · mcmusic"
    desc = f"{state}: {detail}" if track else detail

    page = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>{escape(title)}</title>
<link rel="canonical" href="{escape(profile_url)}">
<meta property="og:type" content="profile">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{escape(profile_url)}">
<meta property="og:image" content="{escape(cover_url)}">
<meta name="twitter:card" content="summary_large_image">
<style>
:root{{color-scheme:dark;--bg:#08060d;--panel:#15101f;--line:#2c2440;--fg:#f2ecff;--dim:#a99bbd;--accent:#a06bff}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:radial-gradient(circle at 50% 0,#2b1850 0,var(--bg) 55%);color:var(--fg);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;display:grid;place-items:center;padding:24px}}
a{{color:inherit}}.card{{width:min(100%,430px);background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:18px;box-shadow:0 24px 80px #0008}}
img{{width:100%;aspect-ratio:1;object-fit:cover;border-radius:15px;display:block;background:#241b31}}
.kicker{{margin:18px 0 4px;color:var(--accent);font-size:11px;letter-spacing:.14em;text-transform:uppercase}}
h1{{margin:0;font-size:27px;line-height:1.1;letter-spacing:-.03em}}
.state{{color:var(--dim);font-size:12px;margin-top:8px}}.track{{font-size:16px;margin-top:14px;font-weight:600}}
.meta{{color:var(--dim);font-size:12px;margin-top:3px}}.foot{{display:flex;justify-content:space-between;gap:12px;margin-top:20px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--dim)}}
.btn{{color:var(--accent);text-decoration:none;font-weight:600}}@media(max-width:380px){{body{{padding:12px}}.card{{padding:12px;border-radius:18px}}}}
</style></head><body><main class="card">
<img src="{escape(cover_url)}" alt="">
<p class="kicker">mcmusic profile</p>
<h1>{escape(name)}</h1>
<p class="state">{escape(state)}</p>
<p class="track">{escape(track) if track else 'Nothing playing right now'}</p>
<p class="meta">{escape(artist)}{(' · ' + escape(album)) if album else ''}</p>
<div class="foot"><span>{escape(profile_url)}</span><a class="btn" href="{escape(base)}">Open mcmusic</a></div>
</main></body></html>"""
    return Response(page, mimetype="text/html", headers={"Cache-Control": "no-store"})


@bp.get("/u/<username>/cover.png")
def public_cover(username):
    """The current track cover, public for status embeds; fallback is the app icon."""
    account, now = _public_account(username)
    if not account:
        return Response(status=404)
    track_id = int(now["track_id"]) if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    etag = f'W/"{track_id}-{updated}"'
    if request.headers.get("If-None-Match") == etag:
        return Response(status=304, headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=0, must-revalidate",
            "Access-Control-Allow-Origin": "*",
        })
    if track_id:
        from routes.library_routes import _track_path, read_cover
        p = _track_path(track_id)
        art = read_cover(p) if p else None
        if art:
            return Response(
                art[0],
                mimetype=art[1],
                headers={
                    "Cache-Control": "public, max-age=0, must-revalidate",
                    "ETag": etag,
                    "Access-Control-Allow-Origin": "*",
                },
            )
    fallback = os.path.join(current_app.static_folder or "", "icon-512.png")
    if os.path.isfile(fallback):
        resp = send_file(fallback, mimetype="image/png")
        resp.headers["Cache-Control"] = "public, max-age=60"
        resp.headers["ETag"] = etag
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    return Response(status=404, headers={"Cache-Control": "no-store", "Access-Control-Allow-Origin": "*"})



def _public_payload(username):
    account, now = _public_account(username)
    if not account:
        return None
    base = PUBLIC_URL or request.url_root.rstrip("/")
    name = account["username"]
    track_id = int(now["track_id"]) if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    cover_ver = f"{track_id}-{updated}" if track_id else str(updated or int(time.time() // 60))
    track = {
        "id": track_id,
        "title": (now["title"] if now and now["title"] else ""),
        "artist": (now["artist"] if now and now["artist"] else ""),
        "album": (now["album"] if now and now["album"] else ""),
    } if track_id else None
    listening = bool(now and now["playing"] and track_id)
    position = float(now["position"] or 0) if now and now["position"] is not None else 0.0
    return {
        "ok": True,
        "user": {"username": name},
        "listening": listening,
        "position": position,
        "updated": updated,
        "track": track,
        "profile_url": f"{base}/u/{quote(name)}",
        "cover_url": f"{base}/u/{quote(name)}/cover.png?v={quote(cover_ver)}",
        "base_url": base,
    }


@bp.get("/api/public/now/<username>")
def public_now(username):
    payload = _public_payload(username)
    if not payload:
        return jsonify(error="not found"), 404, {"Access-Control-Allow-Origin": "*"}
    resp = jsonify(payload)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "public, max-age=5"
    return resp


@bp.get("/embed")
def embed_info():
    base = PUBLIC_URL or request.url_root.rstrip("/")
    html = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>mcmusic widgets</title>
<style>body{{font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:32px;background:#08060d;color:#f2ecff}}
code,pre{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}pre{{background:#151022;border:1px solid #332a4d;border-radius:14px;padding:14px;overflow:auto}}
a{{color:#a06bff}}.card{{max-width:860px;margin:0 auto}}</style></head><body><div class="card">
<h1>mcmusic embed widgets</h1>
<p>Public, no-login widgets for any website. Add the script once, then drop custom tags where you want them.</p>
<pre>&lt;script src="{escape(base)}/static/embed/widgets.js" data-mcmusic-base="{escape(base)}" defer&gt;&lt;/script&gt;

&lt;mcmusic-now user="username" theme="dusk" accent="#a06bff"&gt;&lt;/mcmusic-now&gt;
&lt;mcmusic-turntable user="username" theme="dusk"&gt;&lt;/mcmusic-turntable&gt;</pre>
<p>Attributes: <code>user</code> (required), <code>theme</code> (<code>dusk|paper|ink|tide|copper|forest|rose|auto</code>), <code>accent</code>, <code>compact</code>, <code>refresh</code> (seconds).</p>
<p>Style with CSS vars on the element: <code>--mc-accent</code>, <code>--mc-bg</code>, <code>--mc-fg</code>, <code>--mc-radius</code>, <code>--mc-font</code>.</p>
</div></body></html>"""
    return Response(html, mimetype="text/html")


@bp.post("/api/rooms")
@login_required
def room_create():
    uid = session["uid"]
    name = _db().execute("select username from users where id=?", (uid,)).fetchone()["username"]
    code = personal_room_code(uid)
    with rooms_lock:
        _prune_rooms()
        for old in [c for c, r in rooms.items() if r["host"] == uid and c != code]:
            del rooms[old]
        rooms[code] = {"host": uid, "host_name": name, "track_id": None, "pos": 0.0,
                       "playing": False, "ts": time.time()}
    return jsonify(code=code)


@bp.post("/api/rooms/<code>/state")
@login_required
def room_push(code):
    d = request.get_json(silent=True) or {}
    with rooms_lock:
        r = rooms.get(code)
        if not r:
            return jsonify(error="no such room"), 404
        if r["host"] != session["uid"]:
            return jsonify(error="not the host"), 403
        tid = d.get("track_id")
        if tid is not None and not _db().execute("select 1 from tracks where id=?", (int(tid),)).fetchone():
            return jsonify(error="no such track"), 404
        r.update(track_id=int(tid) if tid is not None else None,
                 pos=max(0.0, float(d.get("pos", 0) or 0)),
                 playing=bool(d.get("playing")), ts=time.time())
    return jsonify(ok=True)


@bp.get("/api/rooms/<code>")
@login_required
def room_get(code):
    with rooms_lock:
        r = dict(rooms.get(code) or {})
    if not r:
        return jsonify(error="room not found or ended"), 404
    now = time.time()
    track = None
    if r["track_id"] is not None:
        row = _db().execute("select * from tracks where id=?", (r["track_id"],)).fetchone()
        track = track_dict(_db(), row, liked_ids(_db(), session["uid"])) if row else None
    away = now - r["ts"] > ROOM_STALE
    return jsonify(host_id=r["host"], host_name=r["host_name"], track=track, pos=r["pos"],
                   playing=r["playing"] and not away, host_away=away,
                   state_ts=r["ts"], server_now=now)


@bp.delete("/api/rooms/<code>")
@login_required
def room_close(code):
    with rooms_lock:
        r = rooms.get(code)
        if r and r["host"] == session["uid"]:
            del rooms[code]
    return jsonify(ok=True)


@bp.get("/api/admin/rooms")
@admin_required
def admin_rooms():
    now = time.time()
    with rooms_lock:
        data = [(code, dict(r)) for code, r in rooms.items()]
    out = []
    for code, r in data:
        track = None
        if r["track_id"] is not None:
            row = _db().execute("select id,title,artist,album from tracks where id=?", (r["track_id"],)).fetchone()
            track = dict(row) if row else None
        out.append({"code": code, "host": r["host_name"], "host_id": r["host"], "track": track,
                    "pos": r["pos"], "playing": r["playing"], "idle": now - r["ts"],
                    "away": now - r["ts"] > ROOM_STALE})
    out.sort(key=lambda x: -x["idle"])
    return jsonify(rooms=out)


@bp.delete("/api/admin/rooms/<code>")
@admin_required
def admin_room_close(code):
    with rooms_lock:
        rooms.pop(code, None)
    return jsonify(ok=True)


# --------------------------------------------------------------------------- download requests
dl_q = __import__("queue").Queue()
running = {}
running_lock = threading.Lock()
cancel_requested = set()
_size_cache = {"t": 0.0, "v": 0}


def req_log_path(rid):
    return os.path.join(LOG_DIR, f"{rid}.log")


def read_req_log(rid, tail=200_000):
    try:
        with open(req_log_path(rid), "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - tail))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def trim_req_log(rid):
    p = req_log_path(rid)
    try:
        if os.path.getsize(p) <= 512 * 1024:
            return
        with open(p, "rb") as fh:
            fh.seek(-(512 * 1024 // 2), os.SEEK_END)
            data = fh.read()
        with open(p, "wb") as fh:
            fh.write(b"[... earlier output trimmed ...]\n" + data)
    except OSError:
        pass


def dir_size(path, ttl=30):
    now = time.time()
    if now - _size_cache["t"] > ttl:
        total = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        _size_cache.update(t=now, v=total)
    return _size_cache["v"]


def valid_yt(url):
    from urllib.parse import urlparse
    u = urlparse(url)
    return u.scheme == "https" and (u.hostname or "").lower() in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"
    }


def worker():
    conn = _db()
    while True:
        rid = dl_q.get()
        row = conn.execute("select * from requests where id=?", (rid,)).fetchone()
        if not row or row["status"] != "approved":
            continue
        conn.execute("update requests set status='running', finished=NULL where id=?", (rid,))
        conn.commit()
        cmd = [
            __import__("sys").executable, DL_SCRIPT, row["url"], "-o", MUSIC_DIR,
            "--staging", STAGING_DIR,
        ] + shlex.split(DL_ARGS)
        logp = req_log_path(rid)
        ok, cancelled = False, False
        with open(logp, "w") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] request #{rid}\n")
            fh.write("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n")
            fh.flush()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            with running_lock:
                running[rid] = {"pid": proc.pid, "started": time.time(), "proc": proc}
            last_sync = 0.0
            last_scan = 0.0
            with open(logp, "a") as fh:
                for line in proc.stdout:
                    fh.write(line)
                    fh.flush()
                    now = time.time()
                    if now - last_sync > 2:
                        last_sync = now
                        conn.execute("update requests set log=? where id=?", (read_req_log(rid, 4000), rid))
                        conn.commit()
                    if now - last_scan > 30:
                        last_scan = now
                        try:
                            scan_library(conn)
                        except Exception as e:
                            fh.write(f"[scan warning] {e}\n")
                            fh.flush()
            rc = proc.wait()
            ok = rc == 0
            with open(logp, "a") as fh:
                fh.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] exited with code {rc}\n")
        except Exception as e:
            with open(logp, "a") as fh:
                fh.write(f"\n[ERROR] {e}\n")
        finally:
            with running_lock:
                running.pop(rid, None)
                cancelled = rid in cancel_requested
                cancel_requested.discard(rid)
        trim_req_log(rid)
        try:
            scan_library(conn)
        except Exception:
            pass
        status = "cancelled" if cancelled else ("done" if ok else "failed")
        conn.execute(
            "update requests set status=?, log=?, finished=? where id=?",
            (status, read_req_log(rid, 4000), time.time(), rid),
        )
        conn.commit()


@bp.post("/api/requests")
@login_required
def req_create():
    url = str((request.get_json(silent=True) or {}).get("url", "")).strip()
    if not valid_yt(url):
        return jsonify(error="need an https YouTube / YouTube Music video or playlist link"), 400
    c = _db()
    admin = c.execute("select is_admin from users where id=?", (session["uid"],)).fetchone()["is_admin"]
    status = "approved" if (AUTO_APPROVE or admin) else "pending"
    cur = c.execute(
        "insert into requests(user_id,url,status,created) values(?,?,?,?)",
        (session["uid"], url, status, time.time()),
    )
    c.commit()
    if status == "approved":
        dl_q.put(cur.lastrowid)
    return jsonify(id=cur.lastrowid, status=status)


@bp.get("/api/requests")
@login_required
def req_list():
    c = _db()
    admin = c.execute("select is_admin from users where id=?", (session["uid"],)).fetchone()["is_admin"]
    q = """select r.id, r.url, r.status, r.created, r.log, u.username from requests r
           join users u on u.id=r.user_id {} order by r.id desc limit 100"""
    rows = c.execute(q.format("" if admin else "where r.user_id=?"), () if admin else (session["uid"],))
    return jsonify(requests=[dict(r, log=(r["log"] or "")[-500:]) for r in rows], is_admin=bool(admin))


@bp.post("/api/requests/<int:rid>/<action>")
@admin_required
def req_act(rid, action):
    if action not in ("approve", "reject"):
        return jsonify(error="bad action"), 400
    r = _db().execute("select status from requests where id=?", (rid,)).fetchone()
    if not r or r["status"] not in ("pending", "failed"):
        return jsonify(error="can't change that request"), 409
    _db().execute("update requests set status=? where id=?", ("approved" if action == "approve" else "rejected", rid))
    _db().commit()
    if action == "approve":
        dl_q.put(rid)
    return jsonify(ok=True)


# --------------------------------------------------------------------------- devices (cross-device sync)
@bp.get("/api/devices")
@login_required
def devices_list():
    rows = _db().execute(
        """select d.id, d.device_hash, d.ip, d.user_agent, d.name, d.last_seen,
                   d.current_track_id, d.current_position, d.current_paused,
                   d.current_updated, d.is_active,
                   t.title as track_title, t.artist as track_artist
             from devices d left join tracks t on t.id=d.current_track_id
             where d.user_id=? order by d.is_active desc, d.last_seen desc""",
        (session["uid"],)
    )
    return jsonify(devices=[dict(r) for r in rows])


@bp.post("/api/devices/heartbeat")
@login_required
def devices_heartbeat():
    d = request.get_json(silent=True) or {}
    device_hash = str(d.get("device_hash", ""))[:64].strip()
    if not device_hash:
        return jsonify(error="device_hash required"), 400
    name = str(d.get("name", "")).strip()[:64] or None
    ua = str(request.headers.get("User-Agent", ""))[:200]
    ip = request.remote_addr or "0.0.0.0"
    now = time.time()
    track_id = d.get("track_id")
    position = d.get("position")
    paused = d.get("paused", 0)
    c = _db()
    row = c.execute("select id from devices where user_id=? and device_hash=?", (session["uid"], device_hash)).fetchone()
    if row:
        c.execute(
            """update devices set ip=?, user_agent=?, name=coalesce(?,name), last_seen=?,
                           current_track_id=?, current_position=?, current_paused=?, current_updated=?
                           where id=?""",
            (ip, ua, name, now, track_id, position, int(bool(paused)), now, row["id"]),
        )
        did = row["id"]
    else:
        cur = c.execute(
            """insert into devices(user_id, device_hash, ip, user_agent, name, last_seen,
                           current_track_id, current_position, current_paused, current_updated, is_active)
                           values(?,?,?,?,?,?,?,?,?,?,0)""",
            (session["uid"], device_hash, ip, ua, name, now, track_id, position,
             int(bool(paused)), now),
        )
        did = cur.lastrowid
    n = c.execute("select count(*) cnt from devices where user_id=?", (session["uid"],)).fetchone()["cnt"]
    if n == 1:
        c.execute("update devices set is_active=1 where id=?", (did,))
    c.commit()
    active_id = c.execute("select id from devices where user_id=? and is_active=1", (session["uid"],)).fetchone()[0]
    return jsonify(id=did, active=did == active_id)


@bp.post("/api/devices/<int:did>/activate")
@login_required
def devices_activate(did):
    row = _db().execute("select id from devices where id=? and user_id=?", (did, session["uid"])).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    _db().execute("update devices set is_active=0 where user_id=?", (session["uid"],))
    _db().execute("update devices set is_active=1 where id=?", (did,))
    _db().commit()
    return jsonify(ok=True, active_device=did)


@bp.get("/api/devices/sync")
@login_required
def devices_sync():
    row = _db().execute(
        """select id, device_hash, name, current_track_id, current_position,
                  current_paused, current_updated
             from devices where user_id=? and is_active=1 limit 1""", (session["uid"],)
    ).fetchone()
    if not row:
        return jsonify(sync=None)
    return jsonify(sync=dict(row))


# --------------------------------------------------------------------------- device pairing
@bp.post("/api/devices/code")
@login_required
def devices_code():
    """Mint a short code the user reads out to an old phone or handheld."""
    c = _db()
    uid = session["uid"]
    out = create_device_code(c, uid)
    row = c.execute("select username from users where id=?", (uid,)).fetchone()
    base = PUBLIC_URL or request.url_root.rstrip("/")
    out.update(
        ok=True,
        account=row["username"] if row else None,
        claim_url=f"{base}/#devices",
        hint="Enter this code in the app you want to sign in. It works once, "
             "for five minutes.",
    )
    return jsonify(**out)


@bp.post("/api/devices/claim")
def devices_claim():
    """Unpaired device: trade the short code for a long-lived bearer token."""
    d = request.get_json(silent=True) or {}
    out = claim_device_code(
        _db(),
        str(d.get("code", "")),
        name=str(d.get("name", "")),
        ip=request.remote_addr or "0.0.0.0",
        ua=str(request.headers.get("User-Agent", ""))[:200],
        device_hash=str(d.get("device_hash", "")),
    )
    if not out:
        return jsonify(
            error="That code is wrong, already used, or expired. "
                  "Ask for a fresh one."
        ), 400
    return jsonify(ok=True, **out)


@bp.get("/api/devices/tokens")
@login_required
def devices_tokens_list():
    return jsonify(tokens=list_device_tokens(_db(), session["uid"]))


@bp.post("/api/devices/tokens/<int:tid>/revoke")
@login_required
def devices_token_revoke(tid):
    if not revoke_device_token(_db(), session["uid"], tid):
        return jsonify(error="not found"), 404
    return jsonify(ok=True)


@bp.get("/api/admin/devices")
@admin_required
def admin_devices():
    rows = _db().execute(
        """select d.id, d.device_hash, d.ip, d.user_agent, d.name, d.last_seen,
                  d.current_track_id, d.current_position, d.current_paused,
                  d.current_updated, d.is_active, u.username
             from devices d join users u on u.id=d.user_id
             order by d.last_seen desc limit 200"""
    )
    return jsonify(devices=[dict(r) for r in rows])


# --------------------------------------------------------------------------- admin
@bp.get("/api/admin/invite-codes")
@admin_required
def admin_invite_list():
    c = _db()
    rows = c.execute(
        "select i.*, u.username created_by_name from invite_codes i "
        "left join users u on u.id=i.created_by order by i.created desc limit 200"
    ).fetchall()
    out = []
    now = time.time()
    for r in rows:
        d = dict(r)
        d["expired"] = bool(r["expires"] and now > r["expires"])
        d["exhausted"] = r["uses"] >= r["max_uses"]
        d["used_by"] = [dict(x) for x in c.execute(
            "select username, created from users where invite_code=? order by created",
            (r["code"],),
        )]
        out.append(d)
    return jsonify(codes=out)


@bp.post("/api/admin/invite-codes")
@admin_required
def admin_invite_create():
    d = request.get_json(silent=True) or {}
    try:
        uses = max(1, min(int(d.get("uses") or 1), 100))
    except (TypeError, ValueError):
        uses = 1
    try:
        hours = max(0, min(float(d.get("hours") or 0), 24 * 365))
    except (TypeError, ValueError):
        hours = 0
    note = str(d.get("note", ""))[:100]
    for_user = str(d.get("for_user", "")).strip()[:32]
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    c = _db()
    code = "".join(secrets.choice(alphabet) for _ in range(4)) + "-" + \
        "".join(secrets.choice(alphabet) for _ in range(4))
    while c.execute("select 1 from invite_codes where code=?", (code,)).fetchone():
        code = "".join(secrets.choice(alphabet) for _ in range(9))
    cur = c.execute(
        "insert into invite_codes(code,created_by,created,max_uses,uses,expires,note,for_user,active)"
        " values(?,?,?,?,0,?,?,?,1)",
        (code, session["uid"], time.time(), uses,
         time.time() + hours * 3600 if hours else 0, note, for_user),
    )
    c.commit()
    return jsonify(id=cur.lastrowid, code=code, max_uses=uses,
                   expires=time.time() + hours * 3600 if hours else 0)


@bp.delete("/api/admin/invite-codes/<int:code_id>")
@admin_required
def admin_invite_revoke(code_id):
    c = _db()
    c.execute("update invite_codes set active=0 where id=?", (code_id,))
    c.commit()
    return jsonify(ok=True)


@bp.get("/api/admin/stats")
@admin_required
def admin_stats():
    c = _db()
    req = {r["status"]: r["n"] for r in c.execute("select status, count(*) n from requests group by status")}
    dur = shutil.disk_usage(MUSIC_DIR)
    with running_lock:
        run = [{"id": rid, "pid": v["pid"], "elapsed": time.time() - v["started"]}
               for rid, v in running.items()]
    with rooms_lock:
        room_count = len(rooms)
    return jsonify(
        users=c.execute("select count(*) n from users").fetchone()["n"],
        admins=c.execute("select count(*) n from users where is_admin=1").fetchone()["n"],
        tracks=c.execute("select count(*) n from tracks").fetchone()["n"],
        albums=c.execute("select count(distinct album) n from tracks").fetchone()["n"],
        playlists=c.execute("select count(*) n from playlists").fetchone()["n"],
        plays=c.execute("select count(*) n from plays").fetchone()["n"],
        requests=req, queue=dl_q.qsize(), rooms=room_count, running=run,
        music_bytes=dir_size(MUSIC_DIR), disk_total=dur.total, disk_free=dur.free, disk_used=dur.used,
        uptime=time.time() - START_TIME, pid=os.getpid(),
    )


@bp.get("/api/admin/requests")
@admin_required
def admin_req_list():
    limit = min(max(int(request.args.get("limit", 200)), 1), 500)
    rows = _db().execute(
        "select r.*, u.username from requests r left join users u on u.id=r.user_id order by r.id desc limit ?",
        (limit,),
    ).fetchall()
    now = time.time()
    with running_lock:
        active = set(running)
    out = []
    for r in rows:
        d = dict(r)
        d["running"] = r["id"] in active
        d["elapsed"] = ((now if r["status"] == "running" else (r["finished"] or now)) - r["created"]) if r["created"] else None
        d["log"] = read_req_log(r["id"], 4000) if d["running"] else (r["log"] or "")
        try:
            d["log_size"] = os.path.getsize(req_log_path(r["id"]))
        except OSError:
            d["log_size"] = 0
        out.append(d)
    return jsonify(requests=out, is_admin=True)


@bp.get("/api/admin/requests/<int:rid>/log")
@admin_required
def admin_req_log(rid):
    r = _db().execute("select id,status,created,finished,url from requests where id=?", (rid,)).fetchone()
    if not r:
        return jsonify(error="not found"), 404
    tail = min(max(int(request.args.get("tail", 200_000)), 1024), 1_000_000)
    with running_lock:
        ent = running.get(rid)
        is_running, pid = ent is not None, (ent["pid"] if ent else None)
    text = read_req_log(rid, tail)
    if not text:
        text = _db().execute("select log from requests where id=?", (rid,)).fetchone()["log"] or ""
    return jsonify(id=rid, status=r["status"], running=is_running, pid=pid,
                   created=r["created"], finished=r["finished"], url=r["url"], log=text)


@bp.post("/api/admin/requests/<int:rid>/cancel")
@admin_required
def admin_req_cancel(rid):
    with running_lock:
        ent = running.get(rid)
        if ent:
            cancel_requested.add(rid)
            proc = ent["proc"]
    if not ent:
        r = _db().execute("select status from requests where id=?", (rid,)).fetchone()
        if not r:
            return jsonify(error="not found"), 404
        if r["status"] not in ("approved", "pending"):
            return jsonify(error="not running or queued"), 409
        _db().execute("update requests set status='cancelled', finished=? where id=?", (time.time(), rid))
        _db().commit()
        return jsonify(ok=True)
    proc.terminate()

    def _kill():
        if proc.poll() is None:
            proc.kill()

    t = threading.Timer(5, _kill)
    t.daemon = True
    t.start()
    return jsonify(ok=True)


@bp.post("/api/admin/requests/<int:rid>/retry")
@admin_required
def admin_req_retry(rid):
    with running_lock:
        if rid in running:
            return jsonify(error="still running"), 409
    if not _db().execute("select 1 from requests where id=?", (rid,)).fetchone():
        return jsonify(error="not found"), 404
    try:
        with open(req_log_path(rid), "w") as fh:
            fh.write("")
    except OSError:
        pass
    _db().execute("update requests set status='approved', log='', finished=NULL where id=?", (rid,))
    _db().commit()
    dl_q.put(rid)
    return jsonify(ok=True)


@bp.delete("/api/admin/requests/<int:rid>")
@admin_required
def admin_req_delete(rid):
    with running_lock:
        if rid in running:
            return jsonify(error="cancel it first"), 409
    _db().execute("delete from requests where id=?", (rid,))
    _db().commit()
    try:
        os.remove(req_log_path(rid))
    except OSError:
        pass
    return jsonify(ok=True)


@bp.get("/api/admin/users")
@admin_required
def admin_users():
    rows = _db().execute(
        """select u.id, u.username, u.email, u.is_admin, u.created,
            (select count(*) from plays p where p.user_id=u.id) plays,
            (select count(*) from likes l where l.user_id=u.id) likes,
            (select count(*) from playlists pl where pl.user_id=u.id) playlists,
            (select count(*) from requests r where r.user_id=u.id) requests
            from users u order by u.id"""
    ).fetchall()
    return jsonify(users=[dict(r) for r in rows])


@bp.post("/api/admin/users/<int:uid>/admin")
@admin_required
def admin_user_admin(uid):
    val = 1 if (request.get_json(silent=True) or {}).get("is_admin") else 0
    u = _db().execute("select id, is_admin from users where id=?", (uid,)).fetchone()
    if not u:
        return jsonify(error="not found"), 404
    if uid == session["uid"] and not val:
        return jsonify(error="you can't remove your own admin"), 400
    if not val and u["is_admin"]:
        n = _db().execute("select count(*) n from users where is_admin=1 and id!=?", (uid,)).fetchone()["n"]
        if n == 0:
            return jsonify(error="at least one admin is required"), 400
    _db().execute("update users set is_admin=? where id=?", (val, uid))
    _db().commit()
    return jsonify(ok=True)


@bp.delete("/api/admin/users/<int:uid>")
@admin_required
def admin_user_delete(uid):
    if uid == session["uid"]:
        return jsonify(error="you can't delete yourself"), 400
    u = _db().execute("select id, is_admin from users where id=?", (uid,)).fetchone()
    if not u:
        return jsonify(error="not found"), 404
    if u["is_admin"]:
        n = _db().execute("select count(*) n from users where is_admin=1 and id!=?", (uid,)).fetchone()["n"]
        if n == 0:
            return jsonify(error="at least one admin is required"), 400
    if _db().execute("select 1 from requests where user_id=? and status in ('running','approved') limit 1", (uid,)).fetchone():
        return jsonify(error="user has active requests; cancel them first"), 409
    ids = [r["id"] for r in _db().execute("select id from requests where user_id=?", (uid,))]
    _db().execute("delete from users where id=?", (uid,))
    _db().commit()
    for rid in ids:
        try:
            os.remove(req_log_path(rid))
        except OSError:
            pass
    return jsonify(ok=True)


@bp.post("/api/admin/scan")
@admin_required
def admin_scan():
    scan_library(_db())
    c = _db()
    return jsonify(tracks=c.execute("select count(*) n from tracks").fetchone()["n"],
                   albums=c.execute("select count(distinct album) n from tracks").fetchone()["n"])


# --------------------------------------------------------------------------- YouTube enrichment (admin)
@bp.get("/api/admin/enrich")
@admin_required
def enrich_status():
    c = _db()
    return jsonify(
        total=c.execute("select count(*) n from tracks").fetchone()["n"],
        linked=c.execute("select count(*) n from tracks where yt_id is not null").fetchone()["n"],
        fetched=c.execute("select count(*) n from tracks where yt_likes is not null").fetchone()["n"],
        pending=0,
    )


@bp.get("/api/admin/lyrics")
@admin_required
def lyrics_status():
    import lyrics
    return jsonify(lyrics.status())


@bp.post("/api/admin/lyrics")
@admin_required
def lyrics_start():
    import lyrics
    started = lyrics.start_backfill()
    return jsonify(started=started, **lyrics.status())


@bp.post("/api/admin/enrich")
@admin_required
def enrich_start():
    if (request.get_json(silent=True) or {}).get("force"):
        _db().execute("update tracks set yt_checked=null")
        _db().commit()
    return jsonify(queued=0)


# --------------------------------------------------------------------------- playback registry
# The browser owns audio. It publishes a snapshot here so bots, the sticky
# dashboard and other devices can render real state, and it collects commands
# (skip/pause/enqueue) that a chat channel issued.
@bp.post("/api/playback")
@login_required
def playback_push():
    d = request.get_json(silent=True) or {}
    uid = session["uid"]
    queue = d.get("queue") or []
    if not isinstance(queue, list):
        queue = []
    ids = []
    for v in queue[:200]:
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue
    tid = d.get("track_id")
    try:
        tid = int(tid) if tid is not None else None
    except (TypeError, ValueError):
        tid = None
    from database import save_playback, get_active_device, claim_device
    device = str(d.get("device", ""))[:64].strip() or None
    active = get_active_device(_db(), uid)

    # First push after a fresh install claims the room. Without this, a user
    # whose device rows all predate the single-speaker rule would publish into
    # the void and no device would ever be allowed to play.
    if device and not active:
        claim_device(_db(), uid, device)
        active = device

    # If this device is not the active one, pause it and don't take over.
    if device and device != active:
        return jsonify(ok=True, ignored=True, active_device=active or "")
    save_playback(_db(), uid, tid, d.get("position") or 0,
                  d.get("duration") or 0, bool(d.get("playing")), ids, device)
    return jsonify(ok=True, active_device=active or "")


@bp.get("/api/playback")
@login_required
def playback_pull():
    uid = session["uid"]
    c = _db()
    from database import get_playback
    pb = get_playback(c, uid)
    if pb:
        row = c.execute("select * from tracks where id=?", (pb["track_id"],)).fetchone() \
            if pb["track_id"] else None
        pb["track"] = track_dict(c, row, liked_ids(c, uid)) if row else None
        if pb.get("device"):
            drow = c.execute(
                "select name from devices where user_id=? and device_hash=?",
                (uid, pb["device"]),
            ).fetchone()
            pb["device_name"] = drow["name"] if drow and drow["name"] else "another device"
        else:
            pb["device_name"] = ""

    device = str(request.args.get("device", ""))[:64]
    rows = c.execute(
        "select id, action, arg, origin from playback_commands "
        "where user_id=? and consumed=0 and (target is null or target='' or target=?)"
        " and (origin is null or origin<>?) order by id limit 20",
        (uid, device, device),
    ).fetchall()
    if rows:
        c.execute(
            "update playback_commands set consumed=1 where id in (%s)"
            % ",".join("?" * len(rows)), [r["id"] for r in rows]
        )
        c.commit()
    cmds = []
    for r in rows:
        try:
            arg = __import__("json").loads(r["arg"] or "{}")
        except ValueError:
            arg = {}
        # Resolve enqueue targets here so the client gets a playable object.
        if r["action"] == "enqueue" and arg.get("track_id"):
            row = c.execute("select * from tracks where id=?", (arg["track_id"],)).fetchone()
            if row:
                arg["track"] = track_dict(c, row, liked_ids(c, uid))
        cmds.append({"id": r["id"], "action": r["action"], "arg": arg})
    return jsonify(state=pb, commands=cmds)


@bp.post("/api/playback/command")
@login_required
def playback_command():
    """Queue a remote-control action. Bots may target any linked user."""
    d = request.get_json(silent=True) or {}
    action = str(d.get("action", ""))
    if action not in ("play", "pause", "toggle", "skip", "next", "prev", "enqueue",
                      "remove", "seek", "play_track"):
        return jsonify(error="bad action"), 400
    target = d.get("user_id")
    if target is None or int(target) == session["uid"]:
        target = session["uid"]
    elif not is_bot_request():
        return jsonify(error="cannot control another user"), 403
    c = _db()
    arg = {"track_id": d.get("track_id"), "index": d.get("index"),
           "url": d.get("url"), "position": d.get("position"),
           "from": str(d.get("origin_name") or "another device")[:64]}
    if action == "play_track" and arg.get("track_id"):
        row = c.execute("select * from tracks where id=?", (int(arg["track_id"]),)).fetchone()
        if row:
            arg["track"] = track_dict(c, row, liked_ids(c, int(target)))
    origin = str(d.get("origin", ""))[:64] or None
    target_device = str(d.get("target", ""))[:64] or None
    c.execute(
        "insert into playback_commands(user_id,action,arg,origin,target,created,consumed)"
        " values(?,?,?,?,?,?,0)",
        (int(target), action, __import__("json").dumps(arg), origin, target_device, time.time()),
    )
    c.commit()
    return jsonify(ok=True, action=action, target=int(target))


@bp.get("/api/queue")
@login_required
def queue_snapshot():
    """Queue ids the current user's client last published."""
    c = _db()
    from database import get_playback
    pb = get_playback(c, session["uid"]) or {}
    ids = pb.get("queue") or []
    if not ids:
        return jsonify(queue=[], current=None)
    marks = ",".join("?" * len(ids))
    rows = {r["id"]: r for r in c.execute(
        "select id,title,artist,album,duration from tracks where id in (%s)" % marks, ids)}
    return jsonify(
        current=dict(rows[pb["track_id"]]) if pb.get("track_id") in rows else None,
        queue=[dict(rows[i]) for i in ids if i in rows],
    )
