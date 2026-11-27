"""Database layer: schema, migrations, connection management, and core queries."""
import json
import sqlite3
import time
from flask import g

from config import DB_PATH
from song_meta import video_id

# --------------------------------------------------------------------------- schema
SCHEMA = """
create table if not exists users(
  id integer primary key,
  username text unique collate nocase,
  pw text,
  is_admin integer default 0,
  created real,
  rotur_id text,
  email text,
  notes text default ''
);
create table if not exists tracks(
  id integer primary key,
  path text unique,
  title text,
  artist text,
  album text,
  track_no integer,
  genre text,
  year text,
  duration real,
  mtime real,
  added real,
  yt_id text,
  yt_likes integer,
  yt_views integer,
  yt_channel text,
  yt_date text,
  yt_checked real,
  explicit_auto integer default 0,
  explicit_ovr integer,
  yt_tags text,
  artists text,
  themes text
);
create table if not exists playlists(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  name text,
  created real,
  system_kind text default ''
);
create table if not exists playlist_tracks(
  playlist_id integer references playlists(id) on delete cascade,
  track_id integer references tracks(id) on delete cascade,
  pos integer,
  primary key(playlist_id, track_id)
);
create table if not exists plays(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  track_id integer references tracks(id) on delete cascade,
  ts real,
  completed integer
);
create index if not exists plays_u on plays(user_id, ts);
create index if not exists plays_uid_id on plays(user_id, id);
-- Always-on listening metrics. `plays` stays as the simple play counter used
-- by older clients; this table keeps the richer timeline (skips, completions,
-- position, client) that powers Faves and the admin insight pages.
create table if not exists listening_events(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  track_id integer references tracks(id) on delete cascade,
  ts real,
  event text,
  position real default 0,
  duration real default 0,
  client text
);
create index if not exists listening_events_u on listening_events(user_id, ts);
create index if not exists listening_events_e on listening_events(event, ts);
create index if not exists listening_events_t on listening_events(track_id);
create table if not exists likes(
  user_id integer references users(id) on delete cascade,
  track_id integer references tracks(id) on delete cascade,
  ts real,
  primary key(user_id, track_id)
);
create table if not exists track_sources(
  track_id integer references tracks(id) on delete cascade,
  yt_id text,
  url text,
  title text,
  added real,
  primary key(track_id, url)
);
create index if not exists track_sources_t on track_sources(track_id);
create table if not exists track_artists(
  track_id integer references tracks(id) on delete cascade,
  artist text,
  artist_key text,
  position integer default 0,
  primary key(track_id, artist)
);
create index if not exists track_artists_a on track_artists(artist);
create table if not exists requests(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  url text,
  status text,
  log text,
  created real,
  finished real
);
create table if not exists settings(
  user_id integer primary key references users(id) on delete cascade,
  data text
);
create table if not exists password_resets(
  token_hash text primary key,
  user_id integer references users(id) on delete cascade,
  created real,
  expires real,
  used integer default 0
);
create index if not exists password_resets_u on password_resets(user_id);
create table if not exists invite_codes(
  id integer primary key,
  code text unique,
  created_by integer references users(id) on delete set null,
  created real,
  max_uses integer default 1,
  uses integer default 0,
  expires real default 0,
  note text,
  for_user text,
  active integer default 1
);
create index if not exists invite_codes_code on invite_codes(code);
create table if not exists devices(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  device_hash text,
  ip text,
  user_agent text,
  name text,
  last_seen real,
  current_track_id integer,
  current_position real,
  current_paused integer default 0,
  current_updated real,
  is_active integer default 0
);
create index if not exists devices_u on devices(user_id);
create index if not exists devices_hash on devices(device_hash);
create table if not exists device_codes(
  code text primary key,
  user_id integer references users(id) on delete cascade,
  created real,
  expires real,
  used integer default 0,
  claimed_at real
);
create index if not exists device_codes_user on device_codes(user_id);
-- Sliding-window auth failure log. Timestamps are kept as rows so the window
-- expires naturally and a successful sign-in can clear just the account/code.
create table if not exists auth_failures(
  scope text not null,
  subject text not null,
  ts real not null
);
create index if not exists auth_failures_lookup on auth_failures(scope, subject, ts);
create table if not exists device_tokens(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  token_hash text unique,
  prefix text,
  name text,
  device_hash text,
  created real,
  last_used real,
  revoked integer default 0
);
create index if not exists device_tokens_user on device_tokens(user_id);
create table if not exists rotur_sessions(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  rotur_user_id text,
  access_token_hash text unique,
  refresh_token_hash text,
  expires_at real,
  created_at real,
  last_validated real
);
create index if not exists rotur_sessions_user on rotur_sessions(user_id);
create table if not exists login_tickets(
  code text primary key,
  purpose text,
  platform text,
  platform_user text,
  user_id integer references users(id) on delete cascade,
  created real,
  expires real,
  used integer default 0
);
create table if not exists channel_links(
  platform text,
  platform_user text,
  user_id integer references users(id) on delete cascade,
  created real,
  primary key(platform, platform_user)
);
create table if not exists discord_links(
  user_id integer primary key references users(id) on delete cascade,
  discord_id text unique,
  discord_username text,
  access_token text,
  refresh_token text,
  expires_at real,
  created real,
  updated real
);
create index if not exists discord_links_id on discord_links(discord_id);
create table if not exists music_channels(
  id integer primary key,
  platform text,
  guild_id text,
  channel_id text,
  owner_user_id integer references users(id) on delete set null,
  dashboard_id text,
  mode text default 'control',
  created real,
  updated real,
  unique(platform, channel_id)
);
create table if not exists playback(
  user_id integer primary key references users(id) on delete cascade,
  track_id integer,
  position real,
  duration real,
  playing integer,
  queue text,
  updated real
);
create table if not exists playback_commands(
  id integer primary key,
  user_id integer references users(id) on delete cascade,
  action text,
  arg text,
  created real,
  consumed integer default 0
);
create index if not exists playback_commands_u on playback_commands(user_id, consumed);
create table if not exists rotur_pending(
  token text primary key,
  rotur_user_id text,
  username text,
  access_token text,
  refresh_token text,
  token_expires real,
  ticket text,
  next_path text,
  email text,
  app text,
  device_hash text,
  created real
);
"""

# Columns added after v1 (also applied to existing databases)
NEW_COLS = {
    "yt_id": "text",
    "yt_likes": "integer",
    "yt_views": "integer",
    "yt_channel": "text",
    "yt_date": "text",
    "yt_checked": "real",
    "explicit_auto": "integer default 0",
    "explicit_ovr": "integer",
    "lyrics": "text",
    "lyrics_source": "text",
    "yt_tags": "text",
    "artists": "text",
    "themes": "text",
}
NEW_USER_COLS = {
    "rotur_id": "text", "rotur_username": "text", "email": "text",
    # permanent listen-along code: the room invite link never changes
    "room_code": "text",
    # how a person got in: the invite they used and the admin who made it
    "invite_code": "text", "invited_by": "integer",
    # operator notes. A note containing DO_NOT_DELETE blocks account deletion
    # in both the admin API and a SQLite trigger (defence in depth).
    "notes": "text default ''",
}
# Access tokens are needed again for server-side Rotur calls, so they are kept on
# the row (the hash columns stay for backwards compatibility).
NEW_ROTUR_COLS = {"access_token": "text", "refresh_token": "text"}
NEW_PENDING_COLS = {"email": "text", "app": "text", "device_hash": "text"}
NEW_PLAYLIST_COLS = {"system_kind": "text default ''"}


def _connect():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    # A busy handler is what makes concurrent writers wait instead of failing;
    # set it explicitly so it also applies to the pragmas below.
    c.execute("pragma busy_timeout=30000")
    # The mode is stored in the database file, so this is a no-op after the
    # first connection. It can still fail with "database is locked" when
    # another thread is mid-write, and that must not turn into a 500.
    try:
        c.execute("pragma journal_mode=wal")
    except sqlite3.OperationalError:
        pass
    c.execute("pragma foreign_keys=on")
    return c


def _db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_e=None):
    d = g.pop("db", None)
    if d:
        d.close()


def ensure_schema(c):
    """Create tables if missing and backfill columns for existing databases."""
    c.executescript(SCHEMA)
    _ensure_cols(c)
    # An operator note with DO_NOT_DELETE is a hard delete guard, not just a
    # label. It also covers direct sqlite writes and old admin tooling that may
    # not use the Flask endpoint.
    c.execute(
        "create trigger if not exists users_protected_no_delete "
        "before delete on users "
        "when old.notes like '%DO_NOT_DELETE%' "
        "begin select raise(abort, 'protected account: DO_NOT_DELETE'); end"
    )
    # Split collab credits once for libraries scanned before track_artists existed;
    # new files are indexed by the scanner itself.
    # device-to-device control: who sent a command, and which device it is for
    pbhave = {r["name"] for r in c.execute("pragma table_info(playback)")}
    if "device" not in pbhave:
        c.execute("alter table playback add device text")
    phave = {r["name"] for r in c.execute("pragma table_info(playback_commands)")}
    if "origin" not in phave:
        c.execute("alter table playback_commands add column origin text")
    if "target" not in phave:
        c.execute("alter table playback_commands add column target text")
    c.commit()

    version = c.execute("pragma user_version").fetchone()[0] or 0
    if version < 1:
        from artists import backfill
        backfill(c)
    if version < 2:
        # v2 added artist_key (case/spacing/kana-insensitive matching).
        from artists import reindex_all
        reindex_all(c)
        c.execute("pragma user_version=2")
    # Index the address only after _ensure_cols has added the column, or a
    # pre-existing database fails to boot on the missing column.
    c.execute("create index if not exists users_email on users(lower(email))")
    c.commit()


def _ensure_cols(c):
    have = {r["name"] for r in c.execute("pragma table_info(tracks)")}
    for k, t in NEW_COLS.items():
        if k not in have:
            c.execute(f"alter table tracks add column {k} {t}")
    uhave = {r["name"] for r in c.execute("pragma table_info(users)")}
    for k, t in NEW_USER_COLS.items():
        if k not in uhave:
            c.execute(f"alter table users add column {k} {t}")
    rhave = {r["name"] for r in c.execute("pragma table_info(rotur_sessions)")}
    for k, t in NEW_ROTUR_COLS.items():
        if k not in rhave:
            c.execute(f"alter table rotur_sessions add column {k} {t}")
    phave = {r["name"] for r in c.execute("pragma table_info(rotur_pending)")}
    for k, t in NEW_PENDING_COLS.items():
        if k not in phave:
            c.execute(f"alter table rotur_pending add column {k} {t}")
    plhave = {r["name"] for r in c.execute("pragma table_info(playlists)")}
    for k, t in NEW_PLAYLIST_COLS.items():
        if k not in plhave:
            c.execute(f"alter table playlists add column {k} {t}")
    ahave = {r["name"] for r in c.execute("pragma table_info(track_artists)")}
    if "artist_key" not in ahave:
        c.execute("alter table track_artists add column artist_key text")
    c.execute("create index if not exists track_artists_k on track_artists(artist_key)")
    c.commit()


def init_db(app):
    """Register teardown and run schema init on app context."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        c = _db()
        ensure_schema(c)
        c.commit()


# --------------------------------------------------------------------------- helpers
def dict_row(r):
    return dict(r) if r else None


def dict_rows(rs):
    return [dict(r) for r in rs]


# Track helpers
def liked_ids(c, uid):
    return {r["track_id"] for r in c.execute(
        "select track_id from likes where user_id=?", (uid,))}


# A link that is already queued or already in the library should not start a
# second download. Playlist links have no single video id, so they are matched
# on the exact URL instead.
ACTIVE_REQUESTS = ("pending", "approved", "running")


def find_repeat_request(c, url):
    row = c.execute(
        "select id,url,status from requests where url=? and status in (?,?,?) "
        "order by id desc limit 1", (url, *ACTIVE_REQUESTS),
    ).fetchone()
    if row:
        return row
    vid = video_id(url)
    if not vid:
        return None
    for other in c.execute(
        "select id,url,status from requests where status in (?,?,?) order by id desc",
        ACTIVE_REQUESTS,
    ):
        if video_id(other["url"]) == vid:
            return other
    return None


def video_in_library(c, url):
    vid = video_id(url)
    if not vid:
        return False
    return bool(c.execute(
        "select 1 from tracks where yt_id=? union "
        "select 1 from track_sources where yt_id=? limit 1", (vid, vid),
    ).fetchone())


def _json_list(raw):
    try:
        v = json.loads(raw or "[]")
        return v if isinstance(v, list) else []
    except ValueError:
        return []


def _row_get(r, key, default=None):
    try:
        return r[key]
    except (IndexError, KeyError):
        return default


def track_dict(c, r, liked=()):
    ex = r["explicit_ovr"] if r["explicit_ovr"] is not None else r["explicit_auto"]
    return {
        "id": r["id"], "title": r["title"], "artist": r["artist"],
        "album": r["album"], "track_no": r["track_no"], "genre": r["genre"],
        "year": r["year"], "duration": r["duration"],
        "liked": r["id"] in liked, "explicit": bool(ex),
        "yt_id": r["yt_id"], "yt_likes": r["yt_likes"], "yt_views": r["yt_views"],
        "yt_channel": r["yt_channel"], "yt_date": r["yt_date"], "added": r["added"],
        "has_lyrics": bool(_row_get(r, "lyrics")),
        "lyrics_source": _row_get(r, "lyrics_source"),
        "yt_tags": _json_list(_row_get(r, "yt_tags")),
        "themes": _json_list(_row_get(r, "themes")),
        "artists": _json_list(_row_get(r, "artists")) or ([r["artist"]] if r["artist"] else []),
    }


# ------------------------------------------------------------------- playback state
def save_playback(c, uid, track_id, position, duration, playing, queue_ids, device=None):
    c.execute(
        """insert into playback(user_id,track_id,position,duration,playing,queue,updated,device)
           values(?,?,?,?,?,?,?,?)
           on conflict(user_id) do update set
             track_id=excluded.track_id, position=excluded.position,
             duration=excluded.duration, playing=excluded.playing,
             queue=excluded.queue, updated=excluded.updated, device=excluded.device""",
        (uid, track_id, float(position or 0), float(duration or 0),
         int(bool(playing)), json.dumps(list(queue_ids or [])[:200]), time.time(),
         (str(device)[:64] if device else None)),
    )
    c.commit()


def get_playback(c, uid):
    r = c.execute("select * from playback where user_id=?", (uid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    try:
        d["queue"] = json.loads(d.get("queue") or "[]")
    except ValueError:
        d["queue"] = []
    return d


def get_active_device(c, uid):
    """The device hash currently allowed to make sound, or None.

    `devices.device_hash` is the same value the clients send on their heartbeat
    and playback pushes, so this is the one identity both sides agree on.
    """
    r = c.execute(
        "select device_hash from devices where user_id=? and is_active=1 limit 1",
        (uid,),
    ).fetchone()
    if r and r["device_hash"]:
        return r["device_hash"]
    return None


def claim_device(c, uid, device):
    """Make `device` the one active speaker. First push after a fresh install
    claims the room; later takes are explicit."""
    c.execute("update devices set is_active=0 where user_id=?", (uid,))
    c.execute(
        "update devices set is_active=1 where user_id=? and device_hash=?",
        (uid, device),
    )
    c.commit()
