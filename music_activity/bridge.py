"""Legacy single-account feed from mcmusic's playback table.

The Flask server now keeps one Rotur session per account (see
``src/rotur_activity.py``) and posts activity from the account that is actually
playing. This bridge still watches exactly one ``MCMUSIC_USER_ID`` and, if set,
posts with the shared ``ROTUR_TOKEN`` — so only run it when that token belongs
to the same account. Two publishers on one account fight over the activity id.

Run next to the service, e.g.
  MCMUSIC_USER_ID=1 ROTUR_TOKEN=... python -m music_activity.bridge
"""
from __future__ import annotations

import json
import os
import signal
import sqlite3
import time

import requests

from music_activity.config import (
    DATA_DIR, MCMUSIC_BASE, MCMUSIC_USER_ID, ROTUR_TOKEN, originchats_configured, rotur_rooms,
)
from music_activity.manager import Manager
from music_activity.sinks.originchats import OriginChatsSink
from music_activity.sinks.rotur import RoturSink
from music_activity.state import PlayerState, Track


def _track(row) -> Track | None:
    if not row:
        return None
    tid = row["id"]
    return Track(
        id=str(tid),
        title=row["title"] or "",
        artist=row["artist"] or "",
        album=row["album"] or "",
        duration=float(row["duration"] or 0),
        cover_url=f"{MCMUSIC_BASE}/api/tracks/{tid}/cover",
        url=f"{MCMUSIC_BASE}/",
    )


def _status_extra(c, uid: int) -> str:
    """The account's room invite, when it asked for it in the status."""
    row = c.execute("select data from settings where user_id=?", (uid,)).fetchone()
    if not row or not row["data"]:
        return ""
    try:
        if not json.loads(row["data"]).get("show_room_url"):
            return ""
    except ValueError:
        return ""
    room = c.execute("select room_code from users where id=?", (uid,)).fetchone()
    code = (room["room_code"] if room else "") or ""
    return f"{MCMUSIC_BASE}/#room={code}" if code else ""


def read_state(db_path: str, uid: int) -> PlayerState | None:
    c = sqlite3.connect(db_path, timeout=5)
    c.row_factory = sqlite3.Row
    try:
        pb = c.execute("select * from playback where user_id=?", (uid,)).fetchone()
        if not pb:
            return None
        cur = _track(c.execute("select * from tracks where id=?", (pb["track_id"],)).fetchone()
                     if pb["track_id"] else None)
        if cur is None:
            return PlayerState(track=None, playing=False)
        try:
            queue = json.loads(pb["queue"] or "[]")
        except ValueError:
            queue = []
        idx = queue.index(pb["track_id"]) if pb["track_id"] in queue else 0
        nxt = None
        if idx + 1 < len(queue):
            nxt = _track(c.execute("select * from tracks where id=?", (queue[idx + 1],)).fetchone())
        return PlayerState(
            extra=_status_extra(c, uid),
            track=cur,
            playing=bool(pb["playing"]),
            position=float(pb["position"] or 0),
            updated_at=float(pb["updated"] or time.time()),
            queue_index=idx,
            queue_len=len(queue),
            next=nxt,
        )
    finally:
        c.close()


def load_token(db_path: str, uid: int) -> str:
    """Reuse the account's Rotur session, refreshing the hourly access token.

    ROTUR_TOKEN wins when set (a long-lived sub-token). Otherwise the session
    written by the web sign-in is read; if it is about to expire the refresh
    token is exchanged and the new pair is written back.
    """
    if ROTUR_TOKEN:
        return ROTUR_TOKEN
    c = sqlite3.connect(db_path, timeout=5)
    c.row_factory = sqlite3.Row
    try:
        row = c.execute(
            "select access_token, refresh_token, expires_at, rotur_user_id"
            " from rotur_sessions where user_id=?", (uid,)
        ).fetchone()
    finally:
        c.close()
    if not row or not row["access_token"]:
        raise RuntimeError("no Rotur session for this user; sign in with Rotur on the web app first")
    if float(row["expires_at"] or 0) > time.time() + 60:
        return row["access_token"]
    refresh = row["refresh_token"]
    if not refresh:
        raise RuntimeError("Rotur token expired and there is no refresh token; sign in again")
    app_id = os.environ.get("ROTUR_APP", "")
    base = os.environ.get("ROTUR_BASE_URL", "https://api.rotur.dev").rstrip("/")
    if not app_id:
        raise RuntimeError("Rotur token expired and ROTUR_APP is not set")
    data = {"grant_type": "refresh_token", "refresh_token": refresh, "client_id": app_id}
    secret = os.environ.get("ROTUR_SECRET", "")
    if secret:
        data["client_secret"] = secret
    resp = requests.post(f"{base}/oauth/token", data=data, timeout=20)
    if resp.status_code >= 400:
        raise RuntimeError(f"Rotur token refresh returned {resp.status_code}")
    tokens = resp.json()
    access = tokens.get("access_token")
    if not access:
        raise RuntimeError("Rotur token refresh returned no access token")
    new_refresh = tokens.get("refresh_token") or refresh
    expires = time.time() + float(tokens.get("expires_in") or 3600)
    c = sqlite3.connect(db_path, timeout=5)
    try:
        c.execute(
            "update rotur_sessions set access_token=?, refresh_token=?, expires_at=?"
            " where user_id=?", (access, new_refresh, expires, uid)
        )
        c.commit()
    finally:
        c.close()
    return access


def main() -> int:
    uid = int(MCMUSIC_USER_ID or "0")
    if not uid:
        print("MCMUSIC_USER_ID is not set")
        return 2
    db_path = os.path.join(DATA_DIR, "mcmusic.db")
    sink = RoturSink(
        ROTUR_TOKEN, rotur_rooms(),
        token_provider=lambda: load_token(db_path, uid),
    )
    sinks = [sink]
    if originchats_configured():
        oc = OriginChatsSink()
        oc.connect()
        sinks.append(oc)
        print("originchats: text fallback enabled", flush=True)
    manager = Manager(sinks, debounce=0.5, log=print)
    sink.connect()

    stop = False

    def _stop(*_):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    last = None
    last_pos = 0.0
    last_at = time.time()
    try:
        while not stop:
            try:
                state = read_state(db_path, uid)
            except sqlite3.Error as exc:
                print(f"bridge: {exc}")
                state = None
            if state:
                moved = abs(state.position - (last_pos + (time.time() - last_at if last and last.playing else 0)))
                changed = last is None or (
                    state.track.id != (last.track.id if last.track else None)
                    or state.playing != last.playing
                    or state.queue_len != last.queue_len
                    or moved > 2.5
                )
                if changed:
                    manager.on_event(state)
                    last, last_pos, last_at = state, state.position, time.time()
            elif last is not None:
                manager.on_event(PlayerState(track=None, playing=False))
                last = None
            time.sleep(2)
    finally:
        manager.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
