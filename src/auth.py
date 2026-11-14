"""Authentication: web sessions, RoturLink tickets, and a server-side bot credential.

The credentials are:

* the signed session cookie established by password bootstrap or RoturLink;
* a paired-device bearer token (``mcd_…``) minted from a short one-time code;
* a shared bot credential (``MCMUSIC_BOT_TOKEN``) that acts as a configured
  service account and never appears in the web UI.
"""
import hashlib
import hmac
import re
import secrets
import time

from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, request, g, jsonify

from config import (
    SESSION_COOKIE_NAME, SESSION_COOKIE_SAMESITE, SESSION_COOKIE_HTTPONLY,
    PERMANENT_SESSION_LIFETIME, BOT_TOKEN, BOT_USER,
)
from database import _db


# --------------------------------------------------------------------------- session helpers
def _bot_uid(c):
    """Resolve the service account used by bots (first admin by default)."""
    if BOT_USER:
        r = c.execute("select id from users where username=?", (BOT_USER,)).fetchone()
        if r:
            return r["id"]
    r = c.execute("select id from users where is_admin=1 order by id limit 1").fetchone()
    return r["id"] if r else None


def _auth_uid():
    """Resolve the current user id from the session cookie or the bot credential."""
    if "uid" in session:
        return session["uid"]

    supplied = request.headers.get("X-MCMUSIC-BOT", "")
    if not supplied:
        h = request.headers.get("Authorization", "")
        if h.startswith("Bearer "):
            supplied = h[7:].strip()
    if supplied.startswith(DEVICE_TOKEN_PREFIX):
        uid = resolve_device_token(_db(), supplied)
        if uid is not None:
            session["uid"] = uid  # keeps session-based handlers working
        return uid
    if supplied and BOT_TOKEN and hmac.compare_digest(supplied, BOT_TOKEN):
        uid = _bot_uid(_db())
        if uid is not None:
            session["uid"] = uid  # keeps session-based handlers working
        return uid
    return None


def is_bot_request():
    supplied = request.headers.get("X-MCMUSIC-BOT", "")
    if not supplied:
        h = request.headers.get("Authorization", "")
        if h.startswith("Bearer "):
            supplied = h[7:].strip()
    return bool(supplied and BOT_TOKEN and hmac.compare_digest(supplied, BOT_TOKEN))


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrap(*a, **k):
        if _auth_uid() is None:
            return jsonify(error="login required"), 401
        return fn(*a, **k)

    return wrap


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrap(*a, **k):
        uid = _auth_uid()
        if uid is None:
            return jsonify(error="login required"), 401
        r = _db().execute("select is_admin from users where id=?", (uid,)).fetchone()
        if not r or not r["is_admin"]:
            return jsonify(error="admin only"), 403
        return fn(*a, **k)

    return wrap


def me_dict(u):
    return {
        "id": u["id"],
        "username": u["username"],
        "email": u["email"] if "email" in u.keys() else None,
        "is_admin": bool(u["is_admin"]),
        "rotur_id": u["rotur_id"],
        "rotur_linked": bool(u["rotur_id"]),
    }


# --------------------------------------------------------------------------- password auth
def validate_username(name):
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", name))


def validate_password(pw):
    return len(pw) >= 6


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")


def validate_email(value):
    """Return a normalised address, or "" when it is not usable."""
    v = str(value or "").strip().lower()
    if len(v) > 254 or not EMAIL_RE.match(v):
        return ""
    return v


def email_taken(c, email, uid=None):
    """True when an account other than `uid` already uses this address."""
    r = c.execute(
        "select id from users where lower(email)=lower(?)", (email,)
    ).fetchone()
    return bool(r and (uid is None or r["id"] != uid))


def set_email(c, uid, email):
    c.execute("update users set email=? where id=?", (email, uid))
    c.commit()


def create_user(c, name, pw, is_admin=0, rotur_id=None):
    first = c.execute("select count(*) n from users").fetchone()["n"] == 0
    cur = c.execute(
        "insert into users(username,pw,is_admin,created,rotur_id) values(?,?,?,?,?)",
        (name, generate_password_hash(pw), int(is_admin or first), time.time(), rotur_id),
    )
    c.commit()
    return cur.lastrowid


def unique_username(c, base, suffix=""):
    """Return a username that satisfies validate_username and is unused."""
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", (base or "listener").strip())[:32] or "listener"
    if len(name) < 3:
        name = (name + "_listener")[:32]
    if not c.execute("select 1 from users where username=?", (name,)).fetchone():
        return name
    tail = suffix or secrets.token_hex(3)
    stem = name[: 32 - len(tail) - 1]
    return unique_username(c, f"{stem}_{tail}", secrets.token_hex(3))


def authenticate_user(c, name, pw):
    u = c.execute("select * from users where username=?", (name,)).fetchone()
    if not u or not u["pw"] or not check_password_hash(u["pw"], pw):
        return None
    return u


# --------------------------------------------------------------------------- login tickets
# A ticket is a short-lived, single-use handle that lets a chat bot start a
# RoturLink login for one platform user without ever seeing their credentials.
def create_ticket(c, purpose, platform="", platform_user="", user_id=None, ttl=600):
    code = secrets.token_urlsafe(24)
    now = time.time()
    c.execute(
        "insert into login_tickets(code,purpose,platform,platform_user,user_id,created,expires,used)"
        " values(?,?,?,?,?,?,?,0)",
        (code, purpose, platform, platform_user, user_id, now, now + ttl),
    )
    c.commit()
    return code


def get_ticket(c, code):
    r = c.execute("select * from login_tickets where code=?", (code,)).fetchone()
    if not r or r["used"] or r["expires"] < time.time():
        return None
    return r


def consume_ticket(c, code):
    c.execute("update login_tickets set used=1 where code=?", (code,))
    c.commit()


def prune_tickets(c):
    c.execute("delete from login_tickets where expires < ?", (time.time() - 3600,))
    c.commit()


# --------------------------------------------------------------------------- device pairing
# A signed-in browser mints a short code, the device trades that code for a
# long-lived bearer token. Only the SHA-256 hash of the token is stored, so a
# database leak does not hand out working credentials. This is how the 3DS,
# Qt and other native clients sign in without typing a password.
DEVICE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DEVICE_CODE_TTL = 300
DEVICE_TOKEN_PREFIX = "mcd_"


def normalize_device_code(value):
    """Case and separator insensitive: 'abcd-efgh' and 'ABCDEFGH' match."""
    return re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()


def _device_token_hash(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def create_device_code(c, uid, ttl=DEVICE_CODE_TTL):
    """Mint a single-use pairing code for the signed-in account."""
    now = time.time()
    c.execute("delete from device_codes where expires < ?", (now - 86400,))
    code = "".join(secrets.choice(DEVICE_CODE_ALPHABET) for _ in range(8))
    while c.execute("select 1 from device_codes where code=?", (code,)).fetchone():
        code = "".join(secrets.choice(DEVICE_CODE_ALPHABET) for _ in range(8))
    c.execute(
        "insert into device_codes(code,user_id,created,expires,used) values(?,?,?,?,0)",
        (code, uid, now, now + ttl),
    )
    c.commit()
    return {
        "code": code,
        "display": f"{code[:4]}-{code[4:]}",
        "expires": now + ttl,
        "expires_in": ttl,
    }


def live_device_code(c, code):
    """The code row when it is still unused and unexpired, else None."""
    code = normalize_device_code(code)
    if len(code) != 8:
        return None
    r = c.execute("select * from device_codes where code=?", (code,)).fetchone()
    if not r or r["used"] or r["expires"] < time.time():
        return None
    return r


def claim_device_code(c, code, name="", ip="", ua="", device_hash=""):
    """Trade a pairing code for a bearer token and register the device.

    Returns None when the code is wrong, already spent or expired. The
    conditional update makes a double claim lose cleanly instead of minting two
    tokens from one code.
    """
    row = live_device_code(c, code)
    if not row:
        return None
    now = time.time()
    cur = c.execute(
        "update device_codes set used=1, claimed_at=? where code=? and used=0",
        (now, row["code"]),
    )
    if cur.rowcount != 1:
        return None
    raw = DEVICE_TOKEN_PREFIX + secrets.token_urlsafe(32)
    token_hash = _device_token_hash(raw)
    label = (str(name or "").strip()[:64] or "New device")
    dh = str(device_hash or "").strip()[:64] or token_hash[:32]
    uid = row["user_id"]
    c.execute(
        """insert into device_tokens(user_id,token_hash,prefix,name,device_hash,created,last_used)
           values(?,?,?,?,?,?,?)""",
        (uid, token_hash, raw[:10], label, dh, now, now),
    )
    dev = c.execute(
        "select id from devices where user_id=? and device_hash=?", (uid, dh)
    ).fetchone()
    if dev:
        c.execute(
            "update devices set name=?, ip=?, user_agent=?, last_seen=? where id=?",
            (label, ip, ua, now, dev["id"]),
        )
        did = dev["id"]
    else:
        have = c.execute(
            "select count(*) n from devices where user_id=?", (uid,)
        ).fetchone()["n"]
        cur = c.execute(
            """insert into devices(user_id,device_hash,ip,user_agent,name,last_seen,is_active)
               values(?,?,?,?,?,?,?)""",
            (uid, dh, ip, ua, label, now, 1 if have == 0 else 0),
        )
        did = cur.lastrowid
    c.commit()
    user = c.execute("select * from users where id=?", (uid,)).fetchone()
    return {
        "token": raw,
        "device_id": did,
        "name": label,
        "user": me_dict(user) if user else None,
    }


def resolve_device_token(c, raw, touch=True):
    """The user id behind a live bearer token, or None. Touches once a minute."""
    if not raw or not raw.startswith(DEVICE_TOKEN_PREFIX):
        return None
    r = c.execute(
        "select id, user_id, device_hash, last_used, revoked from device_tokens"
        " where token_hash=?", (_device_token_hash(raw),)
    ).fetchone()
    if not r or r["revoked"]:
        return None
    now = time.time()
    if touch and (not r["last_used"] or now - r["last_used"] > 60):
        c.execute("update device_tokens set last_used=? where id=?", (now, r["id"]))
        if r["device_hash"]:
            c.execute(
                "update devices set last_seen=? where user_id=? and device_hash=?",
                (now, r["user_id"], r["device_hash"]),
            )
        c.commit()
    return r["user_id"]


def list_device_tokens(c, uid):
    rows = c.execute(
        "select id, prefix, name, device_hash, created, last_used, revoked"
        " from device_tokens where user_id=? order by created desc",
        (uid,),
    )
    return [dict(r) for r in rows]


def revoke_device_token(c, uid, tid):
    r = c.execute(
        "select device_hash from device_tokens where id=? and user_id=?", (tid, uid)
    ).fetchone()
    if not r:
        return False
    c.execute(
        "update device_tokens set revoked=1 where id=? and user_id=?", (tid, uid)
    )
    if r["device_hash"]:
        c.execute(
            "delete from devices where user_id=? and device_hash=?",
            (uid, r["device_hash"]),
        )
    c.commit()
    return True


# --------------------------------------------------------------------------- rotur links
def link_channel_user(c, platform, platform_user, uid):
    c.execute(
        """insert into channel_links(platform,platform_user,user_id,created)
           values(?,?,?,?)
           on conflict(platform,platform_user) do update set
             user_id=excluded.user_id, created=excluded.created""",
        (platform, str(platform_user), uid, time.time()),
    )
    c.commit()


def channel_user(c, platform, platform_user):
    return c.execute(
        "select user_id from channel_links where platform=? and platform_user=?",
        (platform, str(platform_user)),
    ).fetchone()


# --------------------------------------------------------------------------- rotur sessions
def save_rotur_session(c, uid, rotur_user_id, access_token, refresh_token, expires_at):
    at_h = hashlib.sha256((access_token or "").encode()).hexdigest()
    rt_h = hashlib.sha256((refresh_token or "").encode()).hexdigest()
    now = time.time()
    c.execute("delete from rotur_sessions where user_id=?", (uid,))
    c.execute(
        """insert into rotur_sessions
           (user_id, rotur_user_id, access_token_hash, refresh_token_hash,
            expires_at, created_at, last_validated, access_token, refresh_token)
           values(?,?,?,?,?,?,?,?,?)""",
        (uid, rotur_user_id, at_h, rt_h, expires_at, now, now,
         access_token, refresh_token),
    )
    c.commit()


def get_rotur_session(c, uid):
    return c.execute(
        "select * from rotur_sessions where user_id=? order by created_at desc limit 1",
        (uid,),
    ).fetchone()


def clear_rotur_session(c, uid):
    c.execute("delete from rotur_sessions where user_id=?", (uid,))
    c.commit()


# --------------------------------------------------------------------------- resets
def _reset_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset(c, uid, ttl=3600):
    """Mint a single-use reset token. Only its hash is stored.

    Link already in an inbox stays valid: asking for another one must not kill
    the mail someone is halfway through using. Only expired rows go, and a user
    keeps at most a handful of live links.
    """
    raw = secrets.token_urlsafe(32)
    now = time.time()
    c.execute("delete from password_resets where expires < ?", (now,))
    c.execute(
        "insert into password_resets(token_hash,user_id,created,expires,used)"
        " values(?,?,?,?,0)",
        (_reset_hash(raw), uid, now, now + ttl),
    )
    c.execute(
        "delete from password_resets where user_id=? and rowid not in ("
        "  select rowid from password_resets where user_id=?"
        "  order by created desc limit 5)",
        (uid, uid),
    )
    c.commit()
    return raw


def reset_user(c, token):
    """The user a live, unused reset token belongs to, else None."""
    if not token:
        return None
    r = c.execute(
        "select * from password_resets where token_hash=?", (_reset_hash(token),)
    ).fetchone()
    if not r or r["used"] or r["expires"] < time.time():
        return None
    return c.execute("select * from users where id=?", (r["user_id"],)).fetchone()


def consume_reset(c, token):
    c.execute("update password_resets set used=1 where token_hash=?", (_reset_hash(token),))
    c.commit()
