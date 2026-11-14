"""Discord account linking (OAuth2 authorization code).

The Discord bot already has its own login handshake. This module links a
signed-in mcmusic account to a Discord identity so channel commands can be
attributed without asking anyone for a password. Tokens stay server-side.
"""
from __future__ import annotations

import secrets
import time
from urllib.parse import urlencode

import requests
from flask import Response, redirect, request, session

from auth import _auth_uid, link_channel_user
from config import (
    DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_REDIRECT_URI,
    DISCORD_SCOPE, PUBLIC_URL,
)
from database import _db

_DISCORD_AUTH = "https://discord.com/oauth2/authorize"
_DISCORD_TOKEN = "https://discord.com/api/oauth2/token"
_DISCORD_ME = "https://discord.com/api/v10/users/@me"
_STATE_KEY = "discord_oauth"


def missing_config():
    missing = []
    if not DISCORD_CLIENT_ID:
        missing.append("DISCORD_CLIENT_ID")
    if not DISCORD_CLIENT_SECRET:
        missing.append("DISCORD_CLIENT_SECRET")
    return missing


def configured():
    return not missing_config()


def _redirect_uri():
    if DISCORD_REDIRECT_URI:
        return DISCORD_REDIRECT_URI
    base = PUBLIC_URL or request.url_root.rstrip("/")
    return base + "/api/auth/discord/callback"


def _html(title, body, status=200):
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · mcmusic</title>
<link rel="stylesheet" href="/static/css/link.css">
</head><body><main class="card">
<h1>{title}</h1><p>{body}</p><a class="btn" href="/">Open mcmusic</a>
</main></body></html>"""
    return Response(page, status=status, mimetype="text/html")


def _upsert(c, uid, did, username, access, refresh, expires):
    now = time.time()
    c.execute(
        """insert into discord_links
           (user_id, discord_id, discord_username, access_token, refresh_token,
            expires_at, created, updated)
           values(?,?,?,?,?,?,?,?)
           on conflict(user_id) do update set
             discord_id=excluded.discord_id,
             discord_username=excluded.discord_username,
             access_token=excluded.access_token,
             refresh_token=excluded.refresh_token,
             expires_at=excluded.expires_at,
             updated=excluded.updated""",
        (uid, did, username[:100], access, refresh, expires, now, now),
    )
    c.commit()


def authorize_route():
    uid = _auth_uid()
    if uid is None:
        return _html("Sign in first", "Open mcmusic, sign in, then link Discord from Settings.", 401)
    if not configured():
        missing = " and ".join(missing_config())
        return _html("Discord is not configured",
                     f"Add {missing} to the server environment, then restart.", 503)

    state = secrets.token_urlsafe(24)
    session[_STATE_KEY] = {
        "state": state,
        "next": request.args.get("next", "")[:300],
        "created": time.time(),
    }
    session.permanent = True
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": DISCORD_SCOPE,
        "state": state,
        "prompt": "consent",
    }
    return redirect(f"{_DISCORD_AUTH}?{urlencode(params)}")


def callback_route():
    ctx = session.pop(_STATE_KEY, None) or {}
    state = request.args.get("state", "")
    err = request.args.get("error", "")
    if err:
        return _html("Discord linking cancelled", f"Discord returned: {err}", 400)
    if not ctx or not state or state != ctx.get("state"):
        return _html("Discord linking failed", "The link request expired or was tampered with.", 403)
    if time.time() - ctx.get("created", 0) > 600:
        return _html("Discord linking expired", "Please start again from Settings.", 403)

    code = request.args.get("code", "")
    if not code:
        return _html("Discord linking failed", "Discord did not return an authorization code.", 400)

    try:
        tok = requests.post(
            _DISCORD_TOKEN,
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _redirect_uri(),
            },
            headers={"Accept": "application/json"},
            timeout=20,
        )
        if tok.status_code >= 400:
            return _html("Discord linking failed", f"Token exchange returned {tok.status_code}.", 502)
        tokens = tok.json()
        access = tokens.get("access_token")
        if not access:
            return _html("Discord linking failed", "Discord did not return an access token.", 502)
        me = requests.get(
            _DISCORD_ME,
            headers={"Authorization": f"Bearer {access}", "Accept": "application/json"},
            timeout=20,
        )
        if me.status_code >= 400:
            return _html("Discord linking failed", f"Profile lookup returned {me.status_code}.", 502)
        profile = me.json()
    except requests.RequestException as e:
        return _html("Discord linking failed", f"Could not reach Discord: {e}", 502)
    except ValueError:
        return _html("Discord linking failed", "Discord returned an invalid response.", 502)

    uid = _auth_uid()
    if uid is None:
        return _html("Sign in first", "Your mcmusic session expired; sign in and try again.", 401)
    did = str(profile.get("id") or "")
    if not did:
        return _html("Discord linking failed", "Discord did not return a user id.", 502)
    username = str(profile.get("global_name") or profile.get("username") or did)

    c = _db()
    other = c.execute(
        "select user_id from discord_links where discord_id=? and user_id<>?",
        (did, uid),
    ).fetchone()
    if other:
        return _html("Discord already linked",
                     "That Discord account is linked to another mcmusic account.", 409)

    expires = time.time() + float(tokens.get("expires_in") or 604800)
    _upsert(c, uid, did, username, access, tokens.get("refresh_token"), expires)
    # Keep the chat-control mapping in sync with the OAuth link.
    link_channel_user(c, "discord", did, uid)

    nxt = ctx.get("next") or "/"
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect("/")


def status_route():
    uid = _auth_uid()
    if uid is None:
        return {"linked": False, "configured": configured(), "missing": missing_config()}
    row = _db().execute(
        "select discord_id, discord_username, expires_at "
        "from discord_links where user_id=?", (uid,)
    ).fetchone()
    return {
        "linked": bool(row),
        "configured": configured(),
        "missing": missing_config(),
        "discord_id": row["discord_id"] if row else None,
        "discord_username": row["discord_username"] if row else None,
        "session_valid": bool(row and (row["expires_at"] or 0) > time.time()),
    }


def unlink_route():
    uid = _auth_uid()
    if uid is None:
        return {"error": "login required"}, 401
    c = _db()
    row = c.execute("select discord_id from discord_links where user_id=?", (uid,)).fetchone()
    if row:
        c.execute("delete from discord_links where user_id=?", (uid,))
        c.execute(
            "delete from channel_links where platform='discord' and platform_user=?",
            (row["discord_id"],),
        )
        c.commit()
    return {"ok": True, "linked": False}
