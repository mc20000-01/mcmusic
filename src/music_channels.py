"""Music control channels — shared model, dashboard payloads and text renderers.

A bound channel holds exactly one sticky dashboard message. The bot owns the
platform side (posting/editing/deleting); this module owns the state and the
markup so Discord and OriginChats can never drift apart.

Platform contract (OriginChats / generic REST bridges) is documented in
originchats.py; Discord uses the same payload through discord.py embeds.
"""
import time

from config import DASHBOARD_INTERVAL

LEGEND = [
    ("/login", "link your Rotur account"),
    ("/addtoqueue <url|track>", "queue music"),
    ("/removefromqueue <position>", "drop a queued track"),
    ("/skip", "next track"),
    ("/pause", "pause / resume"),
]

PLATFORMS = ("discord", "originchats")


def _track_row(c, tid):
    return c.execute("select * from tracks where id=?", (tid,)).fetchone()


def _summary(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"] or "Unknown",
        "artist": row["artist"] or "Unknown Artist",
        "album": row["album"] or "",
        "duration": float(row["duration"] or 0),
    }


def channel_row(c, cid):
    return c.execute("select * from music_channels where id=?", (cid,)).fetchone()


def channel_for(c, platform, channel_id):
    return c.execute(
        "select * from music_channels where platform=? and channel_id=?",
        (platform, str(channel_id)),
    ).fetchone()


def bind(c, platform, channel_id, guild_id="", owner_user_id=None, mode="control"):
    now = time.time()
    c.execute(
        """insert into music_channels
           (platform,guild_id,channel_id,owner_user_id,dashboard_id,mode,created,updated)
           values(?,?,?,?,NULL,?,?,?)
           on conflict(platform,channel_id) do update set
             guild_id=excluded.guild_id,
             owner_user_id=coalesce(excluded.owner_user_id, music_channels.owner_user_id),
             mode=excluded.mode, dashboard_id=NULL, updated=excluded.updated""",
        (platform, str(guild_id or ""), str(channel_id), owner_user_id, mode, now, now),
    )
    c.commit()
    return channel_for(c, platform, channel_id)


def set_dashboard(c, cid, message_id):
    c.execute(
        "update music_channels set dashboard_id=?, updated=? where id=?",
        (str(message_id) if message_id else None, time.time(), cid),
    )
    c.commit()


def unbind(c, cid):
    c.execute("delete from music_channels where id=?", (cid,))
    c.commit()


def list_channels(c, platform=None):
    if platform:
        return c.execute(
            "select * from music_channels where platform=? order by id", (platform,)
        ).fetchall()
    return c.execute("select * from music_channels order by id").fetchall()


def _progress(pos, dur):
    if not dur or dur <= 0:
        return 0.0
    return max(0.0, min(1.0, pos / dur))


def _bar(pct, width=12):
    filled = int(round(pct * width))
    return "▰" * filled + "▱" * (width - filled)


def _clock(s):
    s = max(0, int(round(s or 0)))
    return f"{s // 60}:{s % 60:02d}"


def dashboard_state(c, ch):
    """Build the single source of truth for a channel dashboard."""
    owner = ch["owner_user_id"]
    now = time.time()
    pb = None
    if owner:
        pb = c.execute("select * from playback where user_id=?", (owner,)).fetchone()

    track = None
    position = 0.0
    playing = False
    duration = 0.0
    queue = []
    user = None

    if owner:
        u = c.execute("select id, username from users where id=?", (owner,)).fetchone()
        user = {"id": u["id"], "username": u["username"]} if u else None

    if pb:
        duration = float(pb["duration"] or 0)
        position = float(pb["position"] or 0)
        playing = bool(pb["playing"]) and (now - (pb["updated"] or 0)) < 120
        if playing:
            position = min(duration or position + 86400,
                           position + (now - (pb["updated"] or now)))
        row = _track_row(c, pb["track_id"]) if pb["track_id"] else None
        track = _summary(row)
        if track and not duration:
            duration = track["duration"]

        import json
        try:
            ids = json.loads(pb["queue"] or "[]")
        except ValueError:
            ids = []
        seen = set()
        for tid in ids:
            if tid in seen or tid == (pb["track_id"] or -1):
                continue
            seen.add(tid)
            q = _track_row(c, tid)
            s = _summary(q)
            if s:
                queue.append(s)
            if len(queue) >= 10:
                break

    pct = _progress(position, duration)
    return {
        "channel": {
            "id": ch["id"], "platform": ch["platform"], "channel_id": ch["channel_id"],
            "guild_id": ch["guild_id"], "mode": ch["mode"],
            "dashboard_id": ch["dashboard_id"],
        },
        "owner": user,
        "now": track,
        "position": round(position, 1),
        "duration": round(duration, 1),
        "progress": round(pct, 4),
        "playing": playing,
        "queue": queue,
        "legend": [{"command": a, "hint": b} for a, b in LEGEND],
        "updated": now,
        "stale": not pb,
        "poll_seconds": DASHBOARD_INTERVAL,
    }


def render_text(state):
    """Plain-text dashboard used by OriginChats and as a Discord fallback."""
    lines = []
    if state["now"]:
        t = state["now"]
        mark = "▶" if state["playing"] else "❚❚"
        lines.append(f"{mark}  {t['title']} — {t['artist']}")
        lines.append(
            f"{_clock(state['position'])} {_bar(state['progress'])} {_clock(state['duration'])}"
        )
        if t["album"]:
            lines.append(f"album · {t['album']}")
    else:
        lines.append("· nothing playing ·")

    if state["queue"]:
        lines.append("")
        lines.append("up next")
        for i, t in enumerate(state["queue"][:6], 1):
            lines.append(f"{i:>2}. {t['title']} — {t['artist']}")

    lines.append("")
    lines.append("commands")
    for item in state["legend"]:
        lines.append(f"  {item['command']}   {item['hint']}")
    return "\n".join(lines)


def render_embed(state):
    """Discord embed description + fields."""
    t = state["now"]
    if t:
        title = f"{'▶' if state['playing'] else '❚❚'} {t['title']}"
        desc = (
            f"**{t['artist']}**"
            + (f" · *{t['album']}*" if t["album"] else "")
            + f"\n`{_clock(state['position'])}` {_bar(state['progress'], 16)} "
              f"`{_clock(state['duration'])}`"
        )
    else:
        title = "Nothing playing"
        desc = "Queue something with `/addtoqueue`."

    fields = []
    if state["queue"]:
        fields.append({
            "name": "Up next",
            "value": "\n".join(
                f"`{i}.` {q['title']} — {q['artist']}"
                for i, q in enumerate(state["queue"][:8], 1)
            )[:1024],
            "inline": False,
        })
    fields.append({
        "name": "Commands",
        "value": " · ".join(f"`{i['command']}`" for i in state["legend"]),
        "inline": False,
    })
    return {"title": title[:256], "description": desc[:4000], "fields": fields}
