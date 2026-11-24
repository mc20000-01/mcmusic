"""Short-lived, one-use tickets for linking OAuth accounts from the native app.

The Android client authenticates with a bearer token, but an OAuth redirect is a
plain browser request with no Authorization header. A ticket bridges that gap:
the app asks for one with its token, opens the provider in the browser with the
ticket, and the callback trades the ticket for the user id before linking.

Tickets live only in this process and expire quickly. A restart invalidates any
still in flight, which is fine — the app just mints another one.
"""
import secrets
import threading
import time

_TTL = 10 * 60
_codes = {}
_lock = threading.Lock()


def mint(uid: int, ttl: int = _TTL) -> str:
    """Return a one-use ticket bound to [uid], valid for ten minutes."""
    code = secrets.token_urlsafe(24)
    now = time.time()
    with _lock:
        for key, (_, expires) in list(_codes.items()):
            if expires < now:
                _codes.pop(key, None)
        _codes[code] = (int(uid), now + ttl)
    return code


def consume(code: str):
    """Resolve and burn a ticket; returns its user id or None."""
    if not code:
        return None
    with _lock:
        entry = _codes.pop(str(code)[:128], None)
    if not entry:
        return None
    uid, expires = entry
    return uid if time.time() <= expires else None
