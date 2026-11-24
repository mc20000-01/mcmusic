"""RoturLink — Sign in with Rotur (OAuth 2.0 authorization code + PKCE S256).

Protocol notes (per the Rotur docs):
  * authorise  GET  https://api.rotur.dev/oauth/authorize
  * token      POST https://api.rotur.dev/oauth/token
  * user info  GET  https://api.rotur.dev/oauth/userinfo
  * PKCE S256 is mandatory for every client.
  * scopes are "profile" (and optionally "email"); there is no openid scope.
  * access tokens last ~1 hour, authorisation codes last five minutes and are
    single use. Client authentication is client_secret_post for confidential apps.

The browser never stores a Rotur token: the code exchange happens here, the
resulting session is our own signed cookie, and tokens stay server-side.
"""
import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
import threading
import time
from typing import Optional

import app_links
import rotur_activity
from flufi_pages import flufi_page
from music_activity.config import ROTUR_WS
from music_activity.state import PlayerState, Track

import requests
from flask import (
    session, redirect, request, jsonify, current_app, has_app_context, Response, url_for,
)

from config import (
    INVITE_CODE, PUBLIC_URL,
    ROTUR_APP, ROTUR_SECRET, ROTUR_BASE_URL, ROTUR_SCOPE,
    ROTUR_AUTHORIZE_PATH, ROTUR_TOKEN_PATH, ROTUR_USERINFO_PATH,
    ROTUR_CALLBACK_PATH, ROTUR_STATE_TTL,
)
from auth import (
    save_rotur_session, get_rotur_session, clear_rotur_session, _auth_uid,
    create_user, unique_username, link_channel_user, get_ticket, consume_ticket,
    validate_email, email_taken, set_email,
    create_device_code, claim_device_code,
)
from database import _db

STATE_KEY = "rotur_oauth"
SESSION_SKEY = "rotur_pkce"
PENDING_KEY = "rotur_pending"

log = logging.getLogger(__name__)

# A server-wide Rotur key (the Token Manager sub-token) may be configured for
# the account that owns this instance. It belongs to exactly one Rotur user, so
# it must never be used for anybody else: otherwise a friend's listening
# activity lands on the owner's profile. The owner is discovered from the
# socket's `ready` frame once and then cached.
ROTUR_TOKEN = os.environ.get("ROTUR_TOKEN", "").strip()
_TOKEN_OWNER_LOCK = threading.Lock()
_TOKEN_OWNER_CACHE: dict[str, object] = {"id": "", "checked": 0.0}
_TOKEN_OWNER_TTL = 3600

# A Rotur sign-in that has no account yet waits in the database until a friend
# code is supplied, so a restart (or a second worker) does not lose the flow.
# Only the random handle rides in the browser session cookie.
_PENDING_TTL = 900

# The activity socket carries the rich state. Presence only needs to be set
# when it changes or after a long gap; doing a PUT for every 3 s update invites
# rate limits and adds latency to the activity itself.
_PRESENCE_LOCK = threading.Lock()
_PRESENCE_LAST: dict[int, tuple[str, float]] = {}


def _presence_due(uid, presence):
    now = time.time()
    with _PRESENCE_LOCK:
        last = _PRESENCE_LAST.get(uid)
        if last and last[0] == presence and now - last[1] < 60:
            return False
        _PRESENCE_LAST[uid] = (presence, now)
        return True


# --------------------------------------------------------------------------- helpers
def _pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


def _invite_problem(c, code, username):
    """Validate a friend code for a brand-new account (same rules as /api/register)."""
    if c.execute("select count(*) n from users").fetchone()["n"] == 0:
        return None, None
    if INVITE_CODE:
        return (None, None) if code == INVITE_CODE else ("That friend code isn't valid.", None)
    if not code:
        return "A friend code is required to create a new account.", None
    inv = c.execute(
        "select id, code, max_uses, uses, expires, active, for_user, created_by "
        "from invite_codes where code=? and active=1", (code,)
    ).fetchone()
    if not inv:
        return "That friend code isn't valid.", None
    if inv["uses"] >= inv["max_uses"]:
        return "That friend code has already been used up.", None
    if inv["expires"] and time.time() > inv["expires"]:
        return "That friend code has expired.", None
    if inv["for_user"] and inv["for_user"] != username:
        return "That friend code belongs to a different username.", None
    return None, inv


def _stash_pending(c, pending):
    token = secrets.token_urlsafe(24)
    now = time.time()
    c.execute("delete from rotur_pending where created < ?", (now - _PENDING_TTL,))
    c.execute(
        "insert into rotur_pending(token, rotur_user_id, username, access_token,"
        " refresh_token, token_expires, ticket, next_path, email, app, device_hash, created)"
        " values(?,?,?,?,?,?,?,?,?,?,?,?)",
        (token, pending["rid"], pending["name"], pending.get("access"),
         pending.get("refresh"), pending.get("expires_at") or 0,
         pending.get("ticket") or "", pending.get("next") or "",
         pending.get("email") or "", "1" if pending.get("app") else "",
         pending.get("device_hash") or "", now),
    )
    c.commit()
    session[PENDING_KEY] = token
    return token


def _pending_now(c):
    token = session.get(PENDING_KEY)
    if not token:
        return None
    row = c.execute("select * from rotur_pending where token=?", (token,)).fetchone()
    if not row:
        session.pop(PENDING_KEY, None)
        return None
    if time.time() - (row["created"] or 0) > _PENDING_TTL:
        c.execute("delete from rotur_pending where token=?", (token,))
        c.commit()
        session.pop(PENDING_KEY, None)
        return None
    return {
        "rid": row["rotur_user_id"],
        "name": row["username"],
        "access": row["access_token"],
        "refresh": row["refresh_token"],
        "expires_at": row["token_expires"],
        "ticket": row["ticket"] or "",
        "next": row["next_path"] or "",
        "email": row["email"] if "email" in row.keys() else "",
        "app": bool(row["app"]) if "app" in row.keys() else False,
        "device_hash": row["device_hash"] if "device_hash" in row.keys() else "",
    }


def _activate_pending(c, pending, invite_row):
    """Create (or reuse) the account behind a verified Rotur sign-in."""
    rid = pending["rid"]
    existing = c.execute("select id from users where rotur_id=?", (rid,)).fetchone()
    created = not existing
    if existing:
        uid = existing["id"]
    else:
        uid = create_user(c, pending["name"], secrets.token_urlsafe(48), rotur_id=rid)
    _store_rotur_email(c, uid, pending.get("email"))
    if created and invite_row:
        c.execute("update invite_codes set uses=uses+1 where id=?", (invite_row["id"],))
        c.execute(
            "update users set invite_code=?, invited_by=? where id=?",
            (invite_row["code"], invite_row["created_by"], uid),
        )
        c.commit()
    return uid


def _invite_form(message):
    return (
        f'<span class="text">{_esc(message)}</span>'
        '<form class="link-form" method="post" action="/api/auth/rotur/claim">'
        '<input class="input" type="text" name="invite" placeholder="Friend code" '
        'autocomplete="one-time-code" required>'
        '<button class="button variant-accent" type="submit">Continue</button>'
        "</form>"
    )


def _client_redirect_uri():
    """Callback URL registered with the Rotur app (exact match required)."""
    override = current_app.config.get("ROTUR_REDIRECT_URI")
    if override:
        return override
    return request.url_root.rstrip("/") + ROTUR_CALLBACK_PATH


def configured():
    return bool(ROTUR_APP and ROTUR_SECRET)


def authorize_url(redirect_uri, state, challenge, extra=None):
    from urllib.parse import urlencode

    params = {
        "client_id": ROTUR_APP,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ROTUR_SCOPE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if extra:
        params.update(extra)
    return f"{ROTUR_BASE_URL}{ROTUR_AUTHORIZE_PATH}?{urlencode(params)}"


def _post_token(data):
    resp = requests.post(
        f"{ROTUR_BASE_URL}{ROTUR_TOKEN_PATH}",
        data=data,
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RoturError(f"token endpoint returned {resp.status_code}", resp.text[:400])
    return resp.json()


def exchange_code(code, redirect_uri, verifier):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": ROTUR_APP,
        "code_verifier": verifier,
    }
    if ROTUR_SECRET:
        data["client_secret"] = ROTUR_SECRET
    return _post_token(data)


def refresh_tokens(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": ROTUR_APP,
    }
    if ROTUR_SECRET:
        data["client_secret"] = ROTUR_SECRET
    return _post_token(data)


def fetch_user(access_token):
    resp = requests.get(
        f"{ROTUR_BASE_URL}{ROTUR_USERINFO_PATH}",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RoturError(f"userinfo returned {resp.status_code}", resp.text[:400])
    return resp.json()


def profile_identity(profile):
    """Normalise the Rotur profile into (rotur_id, username)."""
    if not isinstance(profile, dict):
        raise RoturError("unexpected userinfo payload", repr(profile)[:200])
    rid = profile.get("id") or profile.get("user_id") or profile.get("sub")
    if rid is None:
        nested = profile.get("user") if isinstance(profile.get("user"), dict) else {}
        rid = nested.get("id") or nested.get("user_id")
    if rid is None:
        raise RoturError("profile is missing a user id", str(profile)[:200])
    name = (
        profile.get("username") or profile.get("name")
        or profile.get("display_name") or profile.get("preferred_username")
    )
    return str(rid), (name or "").strip()


def profile_email(profile):
    """Return the address Rotur shared with the `email` scope, if any."""
    if not isinstance(profile, dict):
        return ""
    nested = profile.get("user") if isinstance(profile.get("user"), dict) else {}
    for source in (profile, nested):
        for key in ("email", "email_address"):
            value = str(source.get(key) or "").strip()
            if value:
                return value
    return ""


def _store_rotur_email(c, uid, email):
    """Keep Rotur's verified address for email sign-in and password resets."""
    cleaned = validate_email(email)
    if cleaned and not email_taken(c, cleaned, uid=uid):
        set_email(c, uid, cleaned)


def _native_redirect(c, uid, device_hash=""):
    """Hand a verified Rotur session back to the Android app as a device token."""
    from urllib.parse import urlencode

    minted = create_device_code(c, uid)
    claim = claim_device_code(
        c, minted["code"],
        name="Android",
        ip=request.remote_addr or "",
        ua=(request.headers.get("User-Agent") or "")[:200],
        device_hash=str(device_hash or "")[:64],
    )
    if not claim:
        return _html("Sign-in failed", "Could not create an Android session.", 500)
    who = c.execute("select username from users where id=?", (uid,)).fetchone()
    query = urlencode({
        "token": claim["token"],
        "username": who["username"] if who else "",
    })
    return redirect(f"mcmusic://oauth?{query}")


class RoturError(Exception):
    def __init__(self, message, detail=""):
        super().__init__(message)
        self.detail = detail


# --------------------------------------------------------------------------- routes
def authorize_route():
    """Start the RoturLink flow. Optional ?t=<ticket> binds a chat identity."""
    if not configured():
        return jsonify(error="RoturLink is not configured on this server "
                             "(set ROTUR_APP and ROTUR_SECRET)"), 503

    c = _db()
    ticket = None
    code = request.args.get("t", "")
    if code:
        ticket = get_ticket(c, code)
        if not ticket:
            return _html("Link expired",
                         "This login link is no longer valid. Ask the bot for a new one.", 410)

    # The native app cannot send its bearer token to the browser redirect, so it
    # hands over a one-use ticket instead. Burn it now and carry the uid in the
    # OAuth state until the callback links the provider identity.
    link_uid = None
    link_ticket = request.args.get("link", "")
    if link_ticket:
        link_uid = app_links.consume(link_ticket)
        if link_uid is None:
            return _html("Link expired",
                         "That link request expired. Open Settings and try again.", 410)

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(24)
    session[STATE_KEY] = {
        "state": state,
        "verifier": verifier,
        "next": request.args.get("next", "")[:300],
        "invite": request.args.get("invite", "")[:80],
        "ticket": code or "",
        "app": str(request.args.get("app", "")) == "1",
        "app_link": link_uid is not None,
        "link_uid": link_uid,
        "device_hash": request.args.get("device_hash", "")[:64],
        "created": time.time(),
    }
    session.permanent = True

    return redirect(authorize_url(_client_redirect_uri(), state, challenge))


def callback_route():
    """Rotur redirects here with ?code&state. Exchange, link, and establish a session."""
    ctx = session.get(STATE_KEY) or {}
    state = request.args.get("state", "")
    err = request.args.get("error", "")

    if err:
        return _html("Sign-in cancelled",
                     f"Rotur returned: {err}", 400)
    if not ctx or not state or state != ctx.get("state"):
        return _html("Sign-in failed", "The login request expired or was tampered with.", 403)
    if time.time() - ctx.get("created", 0) > ROTUR_STATE_TTL:
        session.pop(STATE_KEY, None)
        return _html("Sign-in expired", "Please start again.", 403)

    code = request.args.get("code", "")
    if not code:
        return _html("Sign-in failed", "No authorization code was returned.", 400)

    verifier = ctx.get("verifier")
    redirect_uri = _client_redirect_uri()
    session.pop(STATE_KEY, None)

    try:
        tokens = exchange_code(code, redirect_uri, verifier)
        access = tokens.get("access_token")
        if not access:
            raise RoturError("no access_token in response", str(tokens)[:200])
        profile = fetch_user(access)
        rid, rname = profile_identity(profile)
        email = validate_email(profile_email(profile))
    except RoturError as e:
        return _html("RoturLink failed", f"{e} {e.detail}".strip(), 400)
    except requests.RequestException as e:
        return _html("RoturLink failed", f"Could not reach Rotur: {e}", 502)

    expires_at = time.time() + float(tokens.get("expires_in") or 3600)
    c = _db()
    link_uid = ctx.get("link_uid")
    uid = link_uid or _auth_uid()
    linked = c.execute("select id from users where rotur_id=?", (rid,)).fetchone()
    if link_uid and linked and linked["id"] != link_uid:
        return _html("Already linked",
                     "That Rotur account belongs to another mcmusic account.", 409)

    if linked:
        uid = linked["id"]
        _store_rotur_email(c, uid, email)
    elif uid:
        c.execute("update users set rotur_id=? where id=?", (rid, uid))
        c.commit()
        _store_rotur_email(c, uid, email)
    else:
        # A new Rotur identity never mints an account on its own: the friend
        # code is checked first, and the pending link waits server-side.
        name = unique_username(c, rname or f"rotur_{rid}")
        pending = {
            "rid": rid,
            "name": name,
            "access": access,
            "refresh": tokens.get("refresh_token"),
            "expires_at": expires_at,
            "ticket": ctx.get("ticket") or "",
            "next": ctx.get("next") or "",
            "email": email,
            "app": ctx.get("app"),
            "device_hash": ctx.get("device_hash"),
        }
        invite = str(request.args.get("invite") or ctx.get("invite") or "").strip()
        problem, invite_row = _invite_problem(c, invite, name)
        if problem:
            _stash_pending(c, pending)
            return _html("Friend code required", _invite_form(problem), 403)
        uid = _activate_pending(c, pending, invite_row)

    if rname:
        c.execute("update users set rotur_username=? where id=?", (rname[:100], uid))
    save_rotur_session(c, uid, rid, access, tokens.get("refresh_token"), expires_at)
    c.commit()
    session.permanent = True
    session["uid"] = uid

    ticket_code = ctx.get("ticket")
    if ticket_code:
        ticket = get_ticket(c, ticket_code)
        if ticket and not ticket["user_id"]:
            consume_ticket(c, ticket_code)
            link_channel_user(c, ticket["platform"], ticket["platform_user"], uid)
            who = c.execute("select username from users where id=?", (uid,)).fetchone()
            return _html(
                "Linked to mcmusic",
                f"Signed in as <b>{_esc(who['username'])}</b>. "
                f"Your {_esc(ticket['platform'] or 'chat')} account can now control playback — "
                "you can close this tab and go back to the channel.",
                200,
            )

    if ctx.get("app_link"):
        return redirect("mcmusic://oauth?linked=rotur")

    if ctx.get("app"):
        return _native_redirect(c, uid, ctx.get("device_hash"))

    nxt = ctx.get("next") or ""
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect("/")


def claim_route():
    """Finish a pending Rotur sign-in once a valid friend code is supplied."""
    if _auth_uid() is not None:
        return redirect("/")
    c = _db()
    pending = _pending_now(c)
    if not pending:
        return _html("Sign-in expired", "Please start the Rotur sign-in again.", 403)

    payload = request.get_json(silent=True) or {}
    code = str((request.form.get("invite") if request.form else "") or payload.get("invite", "")).strip()
    problem, invite_row = _invite_problem(c, code, pending["name"])
    if problem:
        return _html("Friend code required", _invite_form(problem), 403)

    uid = _activate_pending(c, pending, invite_row)
    save_rotur_session(
        c, uid, pending["rid"], pending["access"],
        pending.get("refresh"), pending["expires_at"],
    )
    session.permanent = True
    session["uid"] = uid
    token = session.get(PENDING_KEY)
    session.pop(PENDING_KEY, None)
    if token:
        c.execute("delete from rotur_pending where token=?", (token,))
        c.commit()

    ticket_code = pending.get("ticket") or ""
    if ticket_code:
        ticket = get_ticket(c, ticket_code)
        if ticket and not ticket["user_id"]:
            consume_ticket(c, ticket_code)
            link_channel_user(c, ticket["platform"], ticket["platform_user"], uid)
            who = c.execute("select username from users where id=?", (uid,)).fetchone()
            return _html(
                "Linked to mcmusic",
                f"Signed in as <b>{_esc(who['username'])}</b>. "
                f"Your {_esc(ticket['platform'] or 'chat')} account can now control playback — "
                "you can close this tab and go back to the channel.",
                200,
            )

    if pending.get("app"):
        return _native_redirect(c, uid, pending.get("device_hash"))

    nxt = pending.get("next") or ""
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect("/")


def _activity_state(valid_session: bool, uid=None) -> dict:
    """Whether the listening activity can publish, and what is missing if not."""
    if not configured():
        return {"ready": False, "reason": "Rotur is not configured on this server"}
    if valid_session:
        return {"ready": True, "reason": ""}
    if uid is not None and ROTUR_TOKEN:
        owner = _server_token_owner()
        if owner and owner == _account_rotur_id(uid):
            return {"ready": True, "reason": ""}
        return {
            "ready": False,
            "reason": "The server's Rotur key is for another account — "
                      "sign in with Rotur, or link a personal token, to share activity",
        }
    return {
        "ready": False,
        "reason": "Sign in with Rotur again — the activity needs a live session",
    }


def status_route():
    uid = _auth_uid()
    if uid is None:
        return jsonify(
            linked=False, configured=configured(), activity=_activity_state(False),
        )
    c = _db()
    row = c.execute("select rotur_id, rotur_username from users where id=?", (uid,)).fetchone()
    sess = get_rotur_session(c, uid)
    linked = bool(row and row["rotur_id"])
    valid = bool(sess and sess["expires_at"] > time.time())
    # Whether "Share as Rotur activity" can publish at all, so the settings
    # screen can say why instead of only failing when a track starts.
    activity = _activity_state(valid, uid)
    return jsonify(
        linked=linked,
        rotur_id=row["rotur_id"] if row else None,
        rotur_username=row["rotur_username"] if row else None,
        configured=configured(),
        has_tokens=bool(sess),
        session_valid=valid,
        activity=activity,
    )


def _live_token(uid):
    """Access token for status writes, refreshed when the hour is up.

    `get_rotur_session` returns a sqlite Row, not a dict — the earlier
    `.get("access_token")` silently turned into no token and every push 502'd.
    """
    c = _db()
    row = get_rotur_session(c, uid)
    if not row:
        return None, "Rotur session expired — sign in again"
    sess = dict(row)
    token = sess.get("access_token")
    if token and (sess.get("expires_at") or 0) > time.time() + 30:
        return token, ""
    refresh = sess.get("refresh_token")
    if not refresh:
        return token, "" if token else "Rotur session expired — sign in again"
    try:
        fresh = refresh_tokens(refresh)
    except RoturError:
        return None, "Rotur session expired — sign in again"
    except requests.RequestException as e:
        return None, f"Could not reach Rotur: {e}"
    new_token = fresh.get("access_token")
    if not new_token:
        return None, "Rotur did not return an access token"
    save_rotur_session(
        c, uid, sess.get("rotur_user_id"), new_token,
        fresh.get("refresh_token") or refresh,
        time.time() + float(fresh.get("expires_in") or 3600),
    )
    return new_token, ""


async def _probe_token_owner():
    """Ask Rotur which account a key belongs to (auth only, no status change)."""
    try:
        import websockets
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"the 'websockets' package is not installed: {e}") from e
    async with websockets.connect(ROTUR_WS, max_size=2**16, open_timeout=10) as ws:
        await ws.send(json.dumps({"cmd": "auth", "key": ROTUR_TOKEN}))
        raw = await asyncio.wait_for(ws.recv(), timeout=10)
    try:
        msg = json.loads(raw)
    except (TypeError, ValueError):
        return ""
    if not isinstance(msg, dict) or msg.get("cmd") != "ready":
        message = msg.get("message") if isinstance(msg, dict) else raw
        raise RuntimeError(str(message or "Rotur rejected ROTUR_TOKEN"))
    return str(msg.get("user_id") or msg.get("id") or "")


def _server_token_owner():
    """Rotur id that ``ROTUR_TOKEN`` authenticates as, or ``""`` if unknown.

    Cached because the lookup opens one short socket. A failure is cached too,
    but only briefly, so a restart or a restored connection can recover.
    """
    if not ROTUR_TOKEN:
        return ""
    now = time.time()
    with _TOKEN_OWNER_LOCK:
        age = now - float(_TOKEN_OWNER_CACHE["checked"] or 0)
        ttl = _TOKEN_OWNER_TTL if _TOKEN_OWNER_CACHE["id"] else 60
        if _TOKEN_OWNER_CACHE["checked"] and age < ttl:
            return str(_TOKEN_OWNER_CACHE["id"] or "")
    try:
        owner = asyncio.run(_probe_token_owner())
    except Exception as e:  # noqa: BLE001 - activity is optional
        log.warning("rotur: could not identify the account behind ROTUR_TOKEN: %s", e)
        owner = ""
    with _TOKEN_OWNER_LOCK:
        _TOKEN_OWNER_CACHE["id"] = owner
        _TOKEN_OWNER_CACHE["checked"] = now
    if owner:
        log.info("rotur: ROTUR_TOKEN belongs to %s", owner)
    return owner


def _account_rotur_id(uid):
    row = _db().execute("select rotur_id from users where id=?", (uid,)).fetchone()
    return (row["rotur_id"] if row else "") or ""


def _activity_token(uid):
    """The key that may post activity for *this* account.

    The shared server key is only valid for the Rotur account that owns it.
    Everyone else uses their own linked session (or a personal sub-token that
    was supplied through ``/api/auth/rotur/link``).
    """
    if ROTUR_TOKEN:
        owner = _server_token_owner()
        if owner and owner == _account_rotur_id(uid):
            return ROTUR_TOKEN, ""
    token, problem = _live_token(uid)
    if token:
        return token, problem
    if ROTUR_TOKEN and not problem:
        problem = "This account has no Rotur key of its own for activity"
    return None, problem or "Rotur session expired — sign in again"


def _token_provider(uid):
    # The RoturSink resolves its token on a background thread. Flask's request
    # context (and therefore _db()) is not available there, so carry the real
    # app object into that thread instead of letting every first connect fail
    # with "Working outside of application context".
    app = current_app._get_current_object() if has_app_context() else None

    def get():
        if app is None:
            return _activity_token(uid)[0]
        with app.app_context():
            token, _problem = _activity_token(uid)
            return token

    return get


def _set_presence(uid, token, presence="online"):
    """Keep the account online while its rich activity is on the socket."""
    if presence not in ("online", "idle", "dnd", "invisible"):
        presence = "online"
    try:
        resp = requests.put(
            f"{ROTUR_BASE_URL}/v2/status/live",
            json={"presence": presence},
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code >= 400:
            return False, f"Rotur returned {resp.status_code}: {resp.text[:120]}"
    except requests.RequestException as e:
        return False, str(e)
    return True, ""


def listening_activity(track, position=0.0, room_url="", playing=True, cover_url="",
                       profile_url="", status_room=""):
    """Build the sink-agnostic player state for a Rotur listening activity.

    ``room_url`` is the clickable listen-along invite. ``status_room`` is the
    older plain-text copy, which still follows the show-room-link setting.
    """
    title = str(track["title"] or "Unknown track")[:128]
    artist = str(track["artist"] or "")[:128]
    album = str(track["album"] or "")[:128]
    duration = float(track["duration"] or 0)
    t = Track(
        id=str(track["id"]),
        title=title,
        artist=artist,
        album=album,
        duration=duration,
        cover_url=cover_url or None,
        url=profile_url or room_url or None,
    )
    return PlayerState(
        track=t,
        playing=bool(playing),
        position=max(0.0, float(position or 0)),
        extra=status_room or "",
        room_url=room_url or "",
        profile_url=profile_url or "",
    )


def push_activity(uid, state: PlayerState, presence="online"):
    """Stream a rich activity over Rotur's status WebSocket."""
    token, problem = _activity_token(uid)
    if not token:
        return False, problem
    if _presence_due(uid, presence):
        _set_presence(uid, token, presence)
    try:
        rotur_activity.publish(uid, state, _token_provider(uid))
    except Exception as e:  # noqa: BLE001 - surface a useful API error
        return False, f"Could not start Rotur activity: {e}"
    return True, ""


def clear_activity(uid):
    """Remove the activity when playback pauses or the setting is turned off."""
    rotur_activity.clear(uid, _token_provider(uid))
    return True, ""


def close_activity(uid):
    """Close the socket on logout/unlink; closing removes the activity."""
    rotur_activity.close(uid)
    _PRESENCE_LAST.pop(uid, None)
    return True, ""


def push_live_status(uid, status, presence="online"):
    """Compatibility shim for older callers; status strings are not activities."""
    token, problem = _live_token(uid)
    if not token:
        return False, problem
    return _set_presence(uid, token, presence)


# --------------------------------------------------------------------------- validator linking (API only)
# A validator proves ownership of a Rotur account without sharing its token:
#   POST {base}/v2/validators?key=<app id>   (with the person's Rotur token)
#   GET  {base}/v2/validators/verify?v=…&key=…  (no auth; returns id + username)
# This is the API-only counterpart to the browser OAuth flow, so a TUI or any
# other client can link a Rotur identity without the official mcmusic UI.
_VALIDATOR_LOCK = threading.Lock()
_VALIDATOR_CACHE: dict[str, dict] = {}


def validator_ready():
    """Validator linking only needs the app id, not the OAuth client secret."""
    return bool(ROTUR_APP)


def _validator_from_request(payload):
    value = str(payload.get("validator") or payload.get("v") or "").strip()
    if not value:
        value = request.headers.get("X-Rotur-Validator", "").strip()
    if not value:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("rotur "):
            value = auth[6:].strip()
    return value[:1024]


def verify_validator(validator):
    """Ask Rotur who owns a validator. A yes is cached until it expires."""
    now = time.time()
    with _VALIDATOR_LOCK:
        hit = _VALIDATOR_CACHE.get(validator)
        if hit and (hit.get("expires_at") or 0) / 1000.0 > now + 5:
            return hit

    resp = requests.get(
        f"{ROTUR_BASE_URL}/v2/validators/verify",
        params={"v": validator, "key": ROTUR_APP},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code >= 400:
        raise RoturError(
            f"validator check returned {resp.status_code}", resp.text[:400]
        )
    try:
        data = resp.json()
    except ValueError:
        raise RoturError("validator check returned invalid JSON", resp.text[:400])
    if not isinstance(data, dict):
        raise RoturError("validator check returned an unexpected payload", repr(data)[:200])

    if data.get("valid"):
        with _VALIDATOR_LOCK:
            for key, cached in list(_VALIDATOR_CACHE.items()):
                if (cached.get("expires_at") or 0) / 1000.0 <= now:
                    _VALIDATOR_CACHE.pop(key, None)
            _VALIDATOR_CACHE[validator] = data
    return data


def key_route():
    """Public discovery data for API clients that want to link a Rotur account."""
    ready = validator_ready()
    key = ROTUR_APP if ready else ""
    return jsonify(
        configured=ready,
        key=key,
        app=key,
        mint=f"POST {ROTUR_BASE_URL}/v2/validators?key={key}",
        verify=f"GET {ROTUR_BASE_URL}/v2/validators/verify?v=<validator>&key={key}",
        link=f"{(PUBLIC_URL or request.url_root).rstrip('/')}/api/auth/rotur/link",
        header="X-Rotur-Validator",
        body={"validator": "<validator>"},
        note=(
            "Mint a validator with your Rotur token, then POST it here with a "
            "mcmusic API token. No browser or official client is required."
        ),
    )


def link_route():
    """Link the authenticated mcmusic account to a Rotur identity by validator."""
    uid = _auth_uid()
    if uid is None:
        return jsonify(
            error="sign in with a mcmusic API token first",
            code="login_required",
        ), 401
    if not validator_ready():
        return jsonify(
            error="Rotur linking is not configured on this server",
            code="rotur_unconfigured",
        ), 503

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}
    validator = _validator_from_request(payload)
    if not validator:
        return jsonify(
            error="a Rotur validator is required",
            code="validator_required",
            hint="POST /v2/validators?key=<key> with your Rotur token, then send the validator",
        ), 400

    try:
        info = verify_validator(validator)
    except RoturError as e:
        return jsonify(error=str(e), detail=e.detail, code="rotur_unreachable"), 502
    except requests.RequestException as e:
        return jsonify(error=f"Could not reach Rotur: {e}", code="rotur_unreachable"), 502

    if not info.get("valid"):
        return jsonify(
            error=info.get("error") or "Rotur rejected that validator",
            code=info.get("code") or "invalid_validator",
            reason=info.get("reason"),
            until=info.get("until"),
        ), 401

    rid = str(info.get("id") or "").strip()
    rname = str(info.get("username") or "").strip()
    if not rid:
        return jsonify(
            error="Rotur did not return an account id",
            code="rotur_bad_response",
        ), 502

    # An optional Rotur access token also seeds the session used for activity
    # pushes. The validator alone is enough to link.
    rotur_token = str(
        payload.get("token") or request.headers.get("X-Rotur-Token", "")
    ).strip()
    access = ""
    refresh = ""
    token_expires = 0.0
    if rotur_token:
        try:
            profile = fetch_user(rotur_token)
            token_rid, token_name = profile_identity(profile)
        except RoturError as e:
            return jsonify(
                error=f"Rotur rejected that token: {e}",
                detail=e.detail,
                code="rotur_token_invalid",
            ), 401
        except requests.RequestException as e:
            return jsonify(
                error=f"Could not reach Rotur: {e}",
                code="rotur_unreachable",
            ), 502
        if token_rid != rid:
            return jsonify(
                error="that token belongs to a different Rotur account",
                code="rotur_token_mismatch",
            ), 400
        if token_name:
            rname = token_name
        access = rotur_token
        token_expires = time.time() + 3600

    c = _db()
    other = c.execute(
        "select id from users where rotur_id=? and id<>?", (rid, uid)
    ).fetchone()
    if other:
        return jsonify(
            error="that Rotur account is already linked to another mcmusic user",
            code="rotur_already_linked",
        ), 409

    previous = c.execute(
        "select rotur_id from users where id=?", (uid,)
    ).fetchone()
    if previous and previous["rotur_id"] and previous["rotur_id"] != rid:
        close_activity(uid)
        clear_rotur_session(c, uid)

    c.execute(
        "update users set rotur_id=?, rotur_username=? where id=?",
        (rid, rname[:100], uid),
    )
    if access:
        save_rotur_session(c, uid, rid, access, refresh, token_expires)
    c.commit()

    return jsonify(
        ok=True,
        linked=True,
        rotur_id=rid,
        rotur_username=rname,
        expires_at=info.get("expires_at"),
        account_type=info.get("account_type"),
        owner=info.get("owner"),
        has_tokens=bool(access),
    )


def unlink_route():
    uid = _auth_uid()
    if uid is None:
        return jsonify(error="login required"), 401
    close_activity(uid)
    c = _db()
    c.execute("update users set rotur_id=NULL where id=?", (uid,))
    clear_rotur_session(c, uid)
    c.commit()
    return jsonify(ok=True, linked=False)


# --------------------------------------------------------------------------- tiny HTML
def _esc(v):
    return (str(v).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _html(title, body, status=200):
    page = (
        f'<section class="container box">'
        f'<h1 class="header">{_esc(title)}</h1>'
        f'<div class="text">{body}</div>'
        '<a class="button variant-accent" href="/">Open mcmusic</a>'
        '</section>'
    )
    return flufi_page(title, page, status=status)
