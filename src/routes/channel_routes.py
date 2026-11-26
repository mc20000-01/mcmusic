"""API route registration — music control channels and bot context."""
from flask import Blueprint, request, jsonify
import time

from auth import _auth_uid, is_bot_request
from database import _db, find_repeat_request, video_in_library
from config import BOT_TOKEN
import music_channels as mc

bp = Blueprint("channel_api", __name__)


def _require_bot_or_admin():
    """Guard for the channel endpoints: bot token or admin session."""
    if is_bot_request():
        return None
    uid = _auth_uid()
    if uid is None:
        return jsonify(error="login required"), 401
    r = _db().execute("select is_admin from users where id=?", (uid,)).fetchone()
    if not r or not r["is_admin"]:
        return jsonify(error="admin only"), 403
    return None


def _serialize(ch):
    """JSON shape of a channel row."""
    return {
        "id": ch["id"], "platform": ch["platform"], "channel_id": ch["channel_id"],
        "guild_id": ch["guild_id"], "mode": ch["mode"],
        "dashboard_id": ch["dashboard_id"],
        "owner_user_id": ch["owner_user_id"], "updated": ch["updated"],
    }


@bp.get("/api/channels")
def channels_list():
    """Channels linked to the bot, for the dashboard."""
    guard = _require_bot_or_admin()
    if guard:
        return guard
    c = _db()
    platform = request.args.get("platform") or None
    rows = mc.list_channels(c, platform)
    out = []
    for ch in rows:
        d = _serialize(ch)
        if request.args.get("state") == "1":
            d["state"] = mc.dashboard_state(c, ch)
        out.append(d)
    return jsonify(channels=out, configured=bool(BOT_TOKEN))


@bp.post("/api/channels")
def channels_bind():
    """Bind a chat channel to a music control channel."""
    guard = _require_bot_or_admin()
    if guard:
        return guard
    d = request.get_json(silent=True) or {}
    platform = str(d.get("platform", "discord")).strip().lower()
    if platform not in mc.PLATFORMS:
        return jsonify(error=f"platform must be one of {', '.join(mc.PLATFORMS)}"), 400
    channel_id = str(d.get("channel_id", "")).strip()
    if not channel_id:
        return jsonify(error="channel_id required"), 400
    mode = str(d.get("mode", "control")).strip().lower()
    if mode not in ("control", "history"):
        return jsonify(error="mode must be control or history"), 400

    owner = d.get("owner_user_id")
    if owner is None:
        owner = _auth_uid()
    owner = int(owner) if owner else None
    guild_id = str(d.get("guild_id", "")).strip()

    c = _db()
    ch = mc.bind(c, platform, channel_id, guild_id, owner, mode)
    return jsonify(ok=True, channel=_serialize(ch), state=mc.dashboard_state(c, ch))


@bp.delete("/api/channels/<int:cid>")
def channels_unbind(cid):
    """Remove a channel binding."""
    guard = _require_bot_or_admin()
    if guard:
        return guard
    c = _db()
    if not mc.channel_row(c, cid):
        return jsonify(error="not found"), 404
    mc.unbind(c, cid)
    return jsonify(ok=True)


@bp.get("/api/channels/<int:cid>/state")
def channel_state(cid):
    """Current playback/queue state of one channel."""
    guard = _require_bot_or_admin()
    if guard:
        return guard
    c = _db()
    ch = mc.channel_row(c, cid)
    if not ch:
        return jsonify(error="not found"), 404
    state = mc.dashboard_state(c, ch)
    state["text"] = mc.render_text(state)
    state["embed"] = mc.render_embed(state)
    return jsonify(state)


@bp.post("/api/channels/<int:cid>/dashboard")
def channel_dashboard(cid):
    """Update the dashboard/now-playing message for a channel."""
    guard = _require_bot_or_admin()
    if guard:
        return guard
    d = request.get_json(silent=True) or {}
    c = _db()
    if not mc.channel_row(c, cid):
        return jsonify(error="not found"), 404
    mc.set_dashboard(c, cid, d.get("message_id"))
    return jsonify(ok=True)


@bp.post("/api/bot/enqueue")
def bot_enqueue():
    """Add music for a linked chat user: a URL becomes a download, text becomes a track."""
    if not is_bot_request():
        return jsonify(error="bot credential required"), 403
    d = request.get_json(silent=True) or {}
    platform = str(d.get("platform", "discord"))[:32]
    platform_user = str(d.get("platform_user", ""))[:64]
    c = _db()
    link = c.execute(
        "select user_id from channel_links where platform=? and platform_user=?",
        (platform, platform_user),
    ).fetchone()
    if not link:
        return jsonify(error="link your account first with /login"), 403
    uid = link["user_id"]

    url = str(d.get("url", "")).strip()
    if url:
        from routes.system_routes import valid_yt, dl_q
        if not valid_yt(url):
            return jsonify(error="that is not a YouTube link"), 400
        repeat = find_repeat_request(c, url)
        if repeat:
            return jsonify(error="that link is already queued", request_id=repeat["id"],
                           status=repeat["status"]), 409
        if video_in_library(c, url):
            return jsonify(error="that song is already in the library"), 409
        cur = c.execute(
            "insert into requests(user_id,url,status,created) values(?,?,'approved',?)",
            (uid, url, time.time()),
        )
        c.commit()
        dl_q.put(cur.lastrowid)
        return jsonify(ok=True, queued="download", request_id=cur.lastrowid)

    q = str(d.get("query", "")).strip()
    if not q:
        return jsonify(error="url or query required"), 400
    row = c.execute(
        """select * from tracks where title like ? or artist like ? or album like ?
           order by (title like ?) desc, artist limit 1""",
        (f"%{q}%", f"%{q}%", f"%{q}%", f"{q}%"),
    ).fetchone()
    if not row:
        return jsonify(error=f"no track matched \"{q}\""), 404
    c.execute(
        "insert into playback_commands(user_id,action,arg,created,consumed) values(?,?,?,?,0)",
        (uid, "enqueue", __import__("json").dumps({"track_id": row["id"]}), time.time()),
    )
    c.commit()
    return jsonify(ok=True, queued="track", track={"id": row["id"], "title": row["title"],
                                                     "artist": row["artist"]})


@bp.get("/api/bot/context")
def bot_context():
    """Everything a bot needs to execute a command as one chat user."""
    if not is_bot_request():
        return jsonify(error="bot credential required"), 403
    platform = str(request.args.get("platform", "discord"))[:32]
    platform_user = str(request.args.get("platform_user", ""))[:64]
    c = _db()

    uid = None
    link = c.execute(
        "select user_id from channel_links where platform=? and platform_user=?",
        (platform, platform_user),
    ).fetchone() if platform_user else None
    if link:
        uid = link["user_id"]

    me = None
    if uid:
        u = c.execute("select id, username, is_admin from users where id=?", (uid,)).fetchone()
        if u:
            me = {"id": u["id"], "username": u["username"], "is_admin": bool(u["is_admin"])}

    playback = None
    if uid:
        pb = c.execute("select * from playback where user_id=?", (uid,)).fetchone()
        if pb:
            row = c.execute("select id,title,artist,album,duration from tracks where id=?",
                            (pb["track_id"],)).fetchone() if pb["track_id"] else None
            playing = bool(pb["playing"]) and (time.time() - (pb["updated"] or 0)) < 120
            playback = {
                "track": dict(row) if row else None,
                "position": float(pb["position"] or 0),
                "duration": float(pb["duration"] or 0),
                "playing": playing,
            }

    channels = [_serialize(ch) for ch in mc.list_channels(c, platform)]
    return jsonify(
        linked=bool(me),
        me=me,
        playback=playback,
        channels=channels,
        legend=[{"command": a, "hint": b} for a, b in mc.LEGEND],
    )
