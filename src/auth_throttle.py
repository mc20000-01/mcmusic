"""Sliding-window throttle for authentication and pairing endpoints.

Ten rejected attempts in fifteen minutes lock a subject out until its oldest
failure leaves the window. Failures are recorded per account (or device code)
*and* per client IP, so neither password spraying one account nor trying many
accounts from one address gets unlimited guesses. A success clears only the
account/code counter; the IP counter still expires on its own.

State lives in the application's SQLite database, so restarts do not reset the
window. Time is injectable in the helpers to make expiry testable without a
long sleep.
"""
from __future__ import annotations

import math
import time
from functools import wraps

from flask import jsonify, request, session

from config import AUTH_THROTTLE_LIMIT, AUTH_THROTTLE_WINDOW
from database import _db

DENIED = "too many failed attempts; try again later"


def _normalize(value: str, limit: int = 160) -> str:
    return str(value or "").strip().lower()[:limit]


def json_field(*names: str):
    """Return the first non-empty named field from a JSON request body."""
    data = request.get_json(silent=True) or {}
    for name in names:
        if data.get(name):
            return _normalize(data[name])
    return ""


def session_account() -> str:
    """Account identifier for endpoints already protected by a session."""
    uid = session.get("uid")
    return str(uid) if uid is not None else ""


def _subjects(account: str = "", code: str = "") -> list[str]:
    out = []
    if account:
        out.append("acct:" + account)
    if code:
        out.append("code:" + code)
    out.append("ip:" + (_normalize(request.remote_addr or "?", 64)))
    return out


def _prune(c, now: float) -> None:
    c.execute("delete from auth_failures where ts < ?", (now - AUTH_THROTTLE_WINDOW,))
    c.commit()


def retry_after(scope: str, account: str = "", code: str = "",
                now: float | None = None) -> float:
    """Seconds until this request may be retried, or zero when allowed."""
    now = time.time() if now is None else now
    c = _db()
    _prune(c, now)
    for subject in _subjects(account, code):
        row = c.execute(
            "select count(*) n, min(ts) oldest from auth_failures "
            "where scope=? and subject=?", (scope, subject),
        ).fetchone()
        if row and row["n"] >= AUTH_THROTTLE_LIMIT:
            wait = float(row["oldest"]) + AUTH_THROTTLE_WINDOW - now
            if wait > 0:
                return wait
            # All failures in this window expired between prune and read.
            c.execute(
                "delete from auth_failures where scope=? and subject=? and ts<=?",
                (scope, subject, now - AUTH_THROTTLE_WINDOW),
            )
            c.commit()
    return 0.0


def record(scope: str, account: str = "", code: str = "",
           now: float | None = None) -> None:
    """Record one rejected attempt against the account/code and the IP."""
    now = time.time() if now is None else now
    c = _db()
    _prune(c, now)
    for subject in _subjects(account, code):
        c.execute(
            "insert into auth_failures(scope, subject, ts) values(?,?,?)",
            (scope, subject, now),
        )
    c.commit()


def reset(scope: str, account: str = "", code: str = "") -> None:
    """Clear the account/code counter after a successful attempt."""
    c = _db()
    subjects = [s for s in _subjects(account, code) if not s.startswith("ip:")]
    for subject in subjects:
        c.execute(
            "delete from auth_failures where scope=? and subject=?",
            (scope, subject),
        )
    c.commit()


def denied(wait: float):
    resp = jsonify(error=DENIED)
    resp.status_code = 429
    resp.headers["Retry-After"] = str(max(1, int(math.ceil(wait))))
    return resp


def _status(result) -> int:
    if isinstance(result, tuple) and len(result) > 1:
        try:
            return int(result[1])
        except (TypeError, ValueError):
            return 200
    return int(getattr(result, "status_code", 200))


def throttled(scope: str, *, account=None, code=None):
    """Guard a view with the sliding-window failure limit.

    ``account`` and ``code`` are callables returning the subject to record.
    Responses with status 400/401/403/409 count as failures; anything else
    counts as a success and clears the account/code counter.
    """
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            who = str(account() if account else "").strip()
            which = str(code() if code else "").strip()
            wait = retry_after(scope, who, which)
            if wait > 0:
                return denied(wait)
            result = fn(*args, **kwargs)
            status = _status(result)
            if status in (400, 401, 403, 409):
                record(scope, who, which)
            elif status < 400:
                reset(scope, who, which)
            return result
        return wrapped
    return decorate
