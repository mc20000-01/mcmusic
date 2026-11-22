"""API route registration — auth endpoints.

Password auth exists for the first-run bootstrap account only. Everything else
goes through RoturLink. Legacy flows (6-digit codes, raw Rotur-id login, claim
by id, personal API tokens) are gone.
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import json
import time
from urllib.parse import quote

from config import (
    INVITE_CODE, ROTUR_CALLBACK_PATH, ROTUR_APP, BOT_TOKEN, RESET_TTL, PUBLIC_URL,
)
from auth import (
    _auth_uid, login_required, is_bot_request, me_dict,
    validate_username, validate_password, create_user, authenticate_user,
    create_ticket, validate_email, email_taken, set_email,
    create_reset, reset_user, consume_reset,
    create_device_code, claim_device_code, revoke_device_token_raw,
)
import mailer
import discord_link
from database import _db
import rotur
import discord_activity as discord_presence

bp = Blueprint("auth_api", __name__)


@bp.post("/api/register")
def register():
    """Create a local account (first account becomes admin; later ones need an invite)."""
    d = request.get_json(silent=True) or {}
    name = str(d.get("username", "")).strip()
    pw = str(d.get("password", ""))
    code = str(d.get("invite", "")).strip()

    c = _db()
    bootstrap = c.execute("select count(*) n from users").fetchone()["n"] == 0

    invite = None
    if not bootstrap:
        if not code:
            return jsonify(error="invite code required"), 403
        # Admin-issued invite codes take priority; the server-wide INVITE_CODE
        # remains a fallback so old deployments keep working.
        invite = _db().execute(
            "select id, code, max_uses, uses, expires, active, for_user, created_by "
            "from invite_codes where code=? and active=1", (code,)
        ).fetchone()
        if invite:
            if invite["uses"] >= invite["max_uses"]:
                return jsonify(error="invite code used up"), 403
            if invite["expires"] and time.time() > invite["expires"]:
                return jsonify(error="invite code expired"), 403
            if invite["for_user"] and invite["for_user"] != name:
                return jsonify(error="this invite is for another username"), 403
        elif not (INVITE_CODE and code == INVITE_CODE):
            return jsonify(error="bad invite code"), 403

    if not validate_username(name):            return jsonify(error="username: 1-32 chars, letters/numbers/._-"), 400
    if not validate_password(pw):
        return jsonify(error="password must be 6+ chars"), 400
    if c.execute("select 1 from users where username=?", (name,)).fetchone():
        return jsonify(error="username taken"), 409

    email = validate_email(d.get("email", ""))
    if email and email_taken(c, email):
        return jsonify(error="email already in use"), 409

    uid = create_user(c, name, pw)
    if email:
        set_email(c, uid, email)
    if invite:
        c.execute("update invite_codes set uses=uses+1 where id=?", (invite["id"],))
        c.execute(
            "update users set invite_code=?, invited_by=? where id=?",
            (invite["code"], invite["created_by"], uid),
        )
        c.commit()
    elif code:
        # Server-wide INVITE_CODE: still record what the person typed.
        c.execute("update users set invite_code=? where id=?", (code[:64], uid))
        c.commit()

    session.permanent = True
    session["uid"] = uid
    return jsonify(me_dict(c.execute("select * from users where id=?", (uid,)).fetchone()))


@bp.post("/api/login")
def login():
    """Password sign-in; sets the session cookie the web client uses."""
    d = request.get_json(silent=True) or {}
    identifier = d.get("username") or d.get("email") or ""
    u = authenticate_user(_db(), str(identifier), str(d.get("password", "")))
    if not u:
        time.sleep(0.5)
        return jsonify(error="wrong email/username or password"), 401
    session.permanent = True
    session["uid"] = u["id"]
    return jsonify(me_dict(u))


@bp.post("/api/auth/app/login")
def app_login():
    """Native-client sign-in: verify the password, then hand back a device token.

    The browser uses a session cookie, but a phone cannot rely on a cookie jar
    surviving WebView-style quirks. Device tokens already exist for the 3DS and
    Qt clients and every endpoint accepts them as `Authorization: Bearer`, so
    this is the same credential, minted in one round trip.
    """
    d = request.get_json(silent=True) or {}
    identifier = d.get("username") or d.get("email") or ""
    name = str(identifier).strip()
    pw = str(d.get("password", ""))
    c = _db()
    u = authenticate_user(c, name, pw)
    if not u:
        time.sleep(0.4)
        return jsonify(error="wrong email/username or password"), 401
    minted = create_device_code(c, u["id"])
    claim = claim_device_code(
        c, minted["code"],
        name=str(d.get("device") or "Android")[:64],
        ip=request.remote_addr or "",
        ua=(request.headers.get("User-Agent") or "")[:200],
        device_hash=str(d.get("device_hash") or "")[:64],
    )
    if not claim:
        return jsonify(error="could not mint a device token"), 500
    return jsonify(token=claim["token"], device_id=claim["device_id"], user=claim["user"])


@bp.post("/api/auth/app/token")
@login_required
def app_token():
    """Mint a device token for an existing web/Rotur session.

    The native app opens Rotur OAuth in the browser and comes back with a
    signed session cookie. This turns that cookie into the same bearer
    credential the password flow returns, so both sign-in methods share one
    app session.
    """
    d = request.get_json(silent=True) or {}
    c = _db()
    uid = _auth_uid()
    minted = create_device_code(c, uid)
    claim = claim_device_code(
        c, minted["code"],
        name=str(d.get("device") or "Android")[:64],
        ip=request.remote_addr or "",
        ua=(request.headers.get("User-Agent") or "")[:200],
        device_hash=str(d.get("device_hash") or "")[:64],
    )
    if not claim:
        return jsonify(error="could not mint a device token"), 500
    return jsonify(token=claim["token"], device_id=claim["device_id"], user=claim["user"])


@bp.post("/api/auth/app/logout")
def app_logout():
    """Revoke the bearer token this request was signed with."""
    supplied = request.headers.get("Authorization", "")
    raw = supplied[7:].strip() if supplied.startswith("Bearer ") else ""
    revoke_device_token_raw(_db(), raw)
    session.clear()
    return jsonify(ok=True)


@bp.post("/api/logout")
def logout():
    """Clear the session cookie."""
    uid = _auth_uid()
    if uid is not None:
        rotur.close_activity(uid)
        discord_presence.close(uid)
    session.clear()
    return jsonify(ok=True)


@bp.get("/api/me")
def me():
    """The signed-in account, or null."""
    uid = _auth_uid()
    if uid is None:
        return jsonify(error="not logged in"), 401
    u = _db().execute("select * from users where id=?", (uid,)).fetchone()
    if not u:
        session.clear()
        return jsonify(error="not logged in"), 401
    return jsonify(me_dict(u))


@bp.post("/api/password")
@login_required
def change_password():
    """Change the current account's password after checking the old one."""
    d = request.get_json(silent=True) or {}
    uid = _auth_uid()
    u = _db().execute("select * from users where id=?", (uid,)).fetchone()
    if not u or not u["pw"] or not check_password_hash(u["pw"], str(d.get("old", ""))):
        return jsonify(error="current password is wrong"), 403
    new = str(d.get("new", ""))
    if not validate_password(new):
        return jsonify(error="new password must be 6+ chars"), 400
    _db().execute("update users set pw=? where id=?", (generate_password_hash(new), uid))
    _db().commit()
    return jsonify(ok=True)


# --------------------------------------------------------------------------- email resets
@bp.post("/api/auth/email")
@login_required
def set_own_email():
    """Attach or change the address that reset links are sent to."""
    d = request.get_json(silent=True) or {}
    email = validate_email(d.get("email", ""))
    if not email:
        return jsonify(error="enter a valid email address"), 400
    uid = _auth_uid()
    c = _db()
    if email_taken(c, email, uid=uid):
        return jsonify(error="email already in use"), 409
    set_email(c, uid, email)
    return jsonify(me_dict(c.execute("select * from users where id=?", (uid,)).fetchone()))


def _reset_link(token):
    """Absolute URL of a password-reset link."""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    return f"{base}/reset?token={token}"


@bp.post("/api/auth/reset/request")
def request_reset():
    """Mail a one-time reset link. Always answers the same way, so the endpoint
    cannot be used to find out which addresses have accounts."""
    d = request.get_json(silent=True) or {}
    email = validate_email(d.get("email", ""))
    out = {"ok": True, "mail": mailer.configured()}
    if not email:
        return jsonify(out)

    c = _db()
    u = c.execute(
        "select * from users where lower(email)=lower(?)", (email,)
    ).fetchone()
    if not u:
        return jsonify(out)

    link = _reset_link(create_reset(c, u["id"], RESET_TTL))
    try:
        mailer.send(
            u["email"],
            "Reset your mcmusic password",
            "Someone asked to reset the password for your mcmusic account.\n\n"
            f"{link}\n\n"
            f"The link works once and expires in {max(1, RESET_TTL // 60)} minutes.\n"
            "If this wasn't you, ignore this message — your password is unchanged.\n",
        )
    except mailer.MailError as e:
        current_app.logger.warning("reset mail failed: %s", e)
        out["mail"] = False
    return jsonify(out)


@bp.post("/api/auth/reset/check")
def check_reset():
    """Say whether a link can still be spent, so the form can say so up front."""
    d = request.get_json(silent=True) or {}
    if reset_user(_db(), str(d.get("token", ""))):
        return jsonify(ok=True)
    return jsonify(error="this reset link is invalid or has expired"), 400


@bp.post("/api/auth/reset/confirm")
def confirm_reset():
    """Spend a reset token, set the new password, and mail a confirmation."""
    d = request.get_json(silent=True) or {}
    token = str(d.get("token", ""))
    pw = str(d.get("password", ""))
    if not validate_password(pw):
        return jsonify(error="password must be 6+ chars"), 400

    c = _db()
    u = reset_user(c, token)
    if not u:
        return jsonify(error="this reset link is invalid or has expired"), 400

    c.execute("update users set pw=? where id=?", (generate_password_hash(pw), u["id"]))
    c.commit()
    consume_reset(c, token)

    try:
        if u["email" if "email" in u.keys() else "username"]:
            mailer.send(
                u["email"] if "email" in u.keys() else None,
                "Your mcmusic password was changed",
                "The password for your mcmusic account was just reset from a "
                "one-time link.\n\nIf this wasn't you, use \"Forgot password?\" "
                "on the sign-in screen to take the account back.\n",
            )
    except mailer.MailError as e:
        current_app.logger.warning("reset confirmation mail failed: %s", e)

    session.clear()
    return jsonify(ok=True)


# --------------------------------------------------------------------------- RoturLink
@bp.get("/api/auth/rotur/authorize")
def rotur_authorize():
    """Start the Rotur OAuth hand-off."""
    return rotur.authorize_route()


@bp.get(ROTUR_CALLBACK_PATH)
def rotur_callback():
    """Rotur redirect target; links the Rotur id to the account and returns to the app."""
    return rotur.callback_route()


@bp.post("/api/auth/rotur/claim")
def rotur_claim():
    """Claim a pending Rotur link with its one-time token."""
    return rotur.claim_route()


@bp.get("/api/auth/rotur/status")
def rotur_status():
    """Whether the account has a linked Rotur id."""
    return rotur.status_route()


@bp.get("/api/auth/rotur/key")
def rotur_key():
    """API discovery: the key a client mints a validator for, plus endpoints."""
    return rotur.key_route()


@bp.post("/api/auth/rotur/link")
def rotur_link():
    """Link a Rotur identity to the signed-in mcmusic account via a validator."""
    return rotur.link_route()


def _listening_activity(uid, row, position):
    """Build the sink-agnostic listening state every activity sink shares."""
    settings = {}
    sr = _db().execute("select data from settings where user_id=?", (uid,)).fetchone()
    if sr and sr["data"]:
        try:
            settings = json.loads(sr["data"])
        except ValueError:
            settings = {}
    room = ""
    if settings.get("show_room_url"):
        from routes.system_routes import room_url
        room = room_url(uid)

    user_row = _db().execute(
        "select username from users where id=?", (uid,)
    ).fetchone()
    username = user_row["username"] if user_row else ""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    profile_url = f"{base}/u/{quote(username)}" if username else ""
    cover_url = f"{base}/u/{quote(username)}/cover.png" if username else ""
    return rotur.listening_activity(
        row, position, room,
        cover_url=cover_url, profile_url=profile_url,
    )


@bp.post("/api/auth/rotur/activity")
@bp.post("/api/auth/rotur/live")
@login_required
def rotur_activity():
    """Stream the current track as a Rotur rich activity.

    /live stays as an alias for existing clients; it is no longer a status
    string writer. Activities go out over the Rotur status WebSocket.
    """
    uid = session["uid"]
    d = request.get_json(silent=True) or {}
    playing = bool(d.get("playing", True))
    tid = d.get("track_id")
    if not playing or tid in (None, ""):
        rotur.clear_activity(uid)
        return jsonify(ok=True, activity=None)
    try:
        tid = int(tid)
    except (TypeError, ValueError):
        return jsonify(error="track_id must be a number"), 400
    row = _db().execute("select * from tracks where id=?", (tid,)).fetchone()
    if not row:
        return jsonify(error="no such track"), 404

    activity = _listening_activity(uid, row, float(d.get("position", 0) or 0))
    ok, err = rotur.push_activity(
        uid, activity, str(d.get("presence", "online")),
    )
    return jsonify(
        ok=ok,
        error=err or None,
        activity={
            "type": "listening",
            "details": activity.track.title,
            "state": activity.track.artist,
        },
    ), (200 if ok else 502)


@bp.post("/api/auth/rotur/unlink")
@login_required
def rotur_unlink():
    """Remove the Rotur link from the account."""
    return rotur.unlink_route()


# --------------------------------------------------------------------------- Discord link
@bp.get("/api/auth/discord/authorize")
def discord_authorize():
    """Start the Discord OAuth hand-off."""
    return discord_link.authorize_route()


@bp.get("/api/auth/discord/callback")
def discord_callback():
    """Discord redirect target; stores the tokens on the account."""
    return discord_link.callback_route()


@bp.get("/api/auth/discord/status")
def discord_status():
    """Whether the account has a linked Discord id."""
    data = discord_link.status_route()
    # Settings shows why the activity toggle cannot deliver anything yet: no
    # application id, or no Discord client on this host.
    data["presence"] = discord_presence.state()
    return jsonify(data)


@bp.post("/api/auth/discord/unlink")
@login_required
def discord_unlink():
    """Remove the Discord link and stop presence updates."""
    return jsonify(discord_link.unlink_route())


@bp.post("/api/auth/discord/activity")
@login_required
def discord_activity_push():
    """Stream the current track as a Discord Rich Presence activity.

    Presence can only be set by a Discord client, so the desktop app has to be
    running on this host; when it is not, say so instead of reporting success
    on a queued update that will never arrive.
    """
    uid = session["uid"]
    d = request.get_json(silent=True) or {}
    playing = bool(d.get("playing", True))
    tid = d.get("track_id")
    if not playing or tid in (None, ""):
        discord_presence.clear(uid)
        return jsonify(ok=True, activity=None)
    try:
        tid = int(tid)
    except (TypeError, ValueError):
        return jsonify(error="track_id must be a number"), 400
    row = _db().execute("select * from tracks where id=?", (tid,)).fetchone()
    if not row:
        return jsonify(error="no such track"), 404

    usable, why = discord_presence.available()
    if not usable:
        return jsonify(ok=False, error=why), 503
    activity = _listening_activity(uid, row, float(d.get("position", 0) or 0))
    ok, err = discord_presence.publish(uid, activity)
    return jsonify(
        ok=ok,
        error=err or None,
        activity={
            "type": "listening",
            "details": activity.track.title,
            "state": activity.track.artist,
        },
    ), (200 if ok else 502)


# --------------------------------------------------------------------------- bot login handoff
@bp.post("/api/bot/rotur-ticket")
def bot_rotur_ticket():
    """Mint a single-use RoturLink URL for a chat user. Bot credential only."""
    if not is_bot_request():
        return jsonify(error="bot credential required"), 403
    d = request.get_json(silent=True) or {}
    platform = str(d.get("platform", "discord")).strip()[:32]
    platform_user = str(d.get("platform_user", "")).strip()[:64]
    if not platform_user:
        return jsonify(error="platform_user required"), 400
    c = _db()
    existing = c.execute(
        "select user_id from channel_links where platform=? and platform_user=?",
        (platform, platform_user),
    ).fetchone()
    code = create_ticket(c, "login", platform, platform_user,
                         user_id=existing["user_id"] if existing else None)
    base = request.url_root.rstrip("/")
    return jsonify(
        url=f"{base}/api/auth/rotur/authorize?t={code}",
        code=code,
        expires_in=600,
        already_linked=bool(existing),
    )




# --------------------------------------------------------------------------- builds

@bp.get("/api/builds")
def list_builds():
    """What we ship, what exists right now, and how big it is."""
    import builds
    return jsonify(builds=builds.all_builds())


# A small in-memory brake so the public form can't be used to post 13 MB at
# strangers. Two sends per address per hour, one per address every 30 seconds.
_SENT = {}


def _too_soon(email):
    """Rate-limit gate for repeat reset/build mails."""
    now = time.time()
    last = _SENT.get(email)
    if last and now - last < 30:
        return True
    recent = [t for t in _SENT.values() if now - t < 3600]
    if len(recent) >= 40:
        return True
    return False


def _send_build(kind, email):
    """Mail a build link, with rate limiting and a friendly error."""
    import builds

    spec = builds.describe(kind)
    if spec is None:
        return jsonify(error="unknown build"), 404
    if not spec.get("available"):
        return jsonify(error=f"{spec['label']} isn't built yet"), 409
    if _too_soon(email):
        return jsonify(error="That address was just sent a build. Give it a minute."), 429

    path, filename, mimetype = builds.attachment(kind)
    url = PUBLIC_URL.rstrip("/") + spec["url"]

    # Gmail, Outlook, and most large providers reject .apk attachments outright
    # (including inside a zip), so a message that "sends" fine is dropped before
    # it reaches the inbox. The link and a renamed copy both get through.
    blocked = filename.lower().endswith(".apk")
    attach_name = f"{filename}.bin" if blocked else filename
    size_mb = spec["bytes"] / 1048576

    if blocked:
        why_text = (
            "Why the attachment ends in .bin: Gmail and several other mail\n"
            "providers refuse .apk attachments before they ever reach you. The\n"
            f"attached file is the real APK — rename it back to {filename}\n"
            "after downloading and it installs normally. The link is faster."
        )
        why_html = (
            "Gmail blocks .apk attachments, so the attached copy is named "
            f"<b style='color:#b9b0cc'>{attach_name}</b>. It is the same file — "
            f"rename it to {filename} and it installs. The button above is faster."
        )
    else:
        why_text = f"Attached: {filename}"
        why_html = "The build is attached to this message."

    subject = f"Your {spec['label']} build of mcmusic"
    text = f"""Hi,

The {spec['label']} build of mcmusic you asked for is ready.

  {spec['name']}
  {spec['note']}
  Built {spec['built']} · {size_mb:.1f} MB

The quickest way to get it onto your phone is this link — tap it on the device:

  {url}

Android will ask once to allow installs from this source. It updates over the
copy you already have; nothing is wiped.

{why_text}

If you didn't ask for this, ignore the message — no account was created and
nothing was charged.

— mcmusic
"""

    html = f"""<!doctype html>
<html><body style="margin:0;padding:0;background:#0e0a13;">
<div style="max-width:520px;margin:0 auto;padding:36px 24px;
  font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#f2edf7;">
  <div style="font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#9a8cab;">
    mcmusic
  </div>
  <h1 style="margin:10px 0 6px;font-size:24px;font-weight:600;color:#f2edf7;">
    {spec['name']}
  </h1>
  <p style="margin:0 0 22px;font-size:13px;line-height:1.6;color:#b9abc9;">
    {spec['note']} &middot; built {spec['built']} &middot; {size_mb:.1f} MB
  </p>
  <a href="{url}" style="display:inline-block;padding:13px 22px;border-radius:10px;
    background:#b080ea;color:#191023;font-weight:600;font-size:14px;
    text-decoration:none;">Download the {spec['label']} build</a>
  <p style="margin:18px 0 0;font-size:12px;line-height:1.6;color:#9a8cab;">
    Or paste this into the phone:<br>
    <a href="{url}" style="color:#b080ea;word-break:break-all;">{url}</a>
  </p>
  <p style="margin:26px 0 0;font-size:11px;line-height:1.7;color:#9a8cab;">
    {why_html}
  </p>
</div>
</body></html>
"""

    try:
        mailer.send_with_attachment(
            email, subject, text,
            attachment_path=path,
            attachment_name=attach_name,
            mimetype=mimetype,
            html=html,
        )
    except mailer.MailError as e:
        return jsonify(error=str(e)), 500
    _SENT[email] = time.time()
    return jsonify(ok=True, build=kind, file=attach_name, bytes=spec["bytes"], url=url)


@bp.post("/api/apk-email")
@bp.post("/api/auth/apk-email")
@bp.post("/api/builds/email")
def request_apk_email():
    """Mail a build to an address. Public on purpose: someone who hasn't made an
    account yet is exactly who wants the app."""
    d = request.get_json(silent=True) or {}
    email = validate_email(str(d.get("email") or "").strip())
    if not email:
        return jsonify(error="That doesn't look like an email address"), 400
    return _send_build(str(d.get("build") or "android").strip(), email)
