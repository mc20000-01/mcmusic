"""API route registration — listen-along rooms, download requests, devices, admin."""
from flask import (
    Blueprint, request, jsonify, session, Response, send_file, current_app,
)
from html import escape
from urllib.parse import quote
import os, secrets, threading, time, shlex, subprocess, shutil, math
from collections import defaultdict

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from auth import (
    _auth_uid, login_required, admin_required, is_bot_request,
    create_device_code, claim_device_code, list_device_tokens,
    revoke_device_token,
)
from database import _db, track_dict, liked_ids, find_repeat_request, video_in_library
from library_scan import scan_library

bp = Blueprint("system_api", __name__)
START_TIME = time.time()

# --------------------------------------------------------------------------- config refs
from config import (
    MUSIC_DIR, DL_SCRIPT, DL_ARGS, STAGING_DIR, AUTO_APPROVE, LOG_DIR, API_RATE_LIMIT,
    PUBLIC_URL,
)

@bp.get("/health")
def health():
    """Unauthenticated liveness probe for monitors and reverse proxies.

    Deliberately touches no database and reads no session, so it stays fast
    even while the library importer is saturating the worker.
    """
    return jsonify(
        ok=True, service="mcmusic",
        uptime=round(time.time() - START_TIME, 1),
    )


@bp.get("/api/ping")
def api_ping():
    """Cheap health check that also tells a native client whether a token works."""
    uid = _auth_uid()
    user = None
    if uid is not None:
        r = _db().execute(
            "select id, username, is_admin from users where id=?", (uid,)
        ).fetchone()
        if r:
            user = {
                "id": r["id"], "username": r["username"],
                "is_admin": bool(r["is_admin"]),
            }
    return jsonify(
        ok=True, service="mcmusic", api=3, user=user,
        uptime=round(time.time() - START_TIME, 1), time=time.time(),
    )


# --------------------------------------------------------------------------- listen-along rooms (in-memory, single worker)
rooms = {}
rooms_lock = threading.Lock()
ROOM_STALE = 45


def _prune_rooms():
    now = time.time()
    for code in [c for c, r in rooms.items() if now - r["ts"] > 6 * 3600]:
        del rooms[code]


def personal_room_code(uid: int) -> str:
    """The account's permanent room code, so its invite link never changes."""
    c = _db()
    row = c.execute("select room_code from users where id=?", (uid,)).fetchone()
    code = (row["room_code"] if row else "") or ""
    if not code:
        code = secrets.token_urlsafe(6)
        c.execute("update users set room_code=? where id=?", (code, uid))
        c.commit()
    return code


def room_url(uid: int) -> str:
    """Absolute listen-along invite link for an account."""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    return f"{base}/#room={personal_room_code(uid)}"


def _public_account(username):
    """Resolve a username to its account and current playback, without auth."""
    c = _db()
    account = c.execute(
        "select id, username from users where username=? collate nocase",
        (username,),
    ).fetchone()
    if not account:
        return None, None
    playback = c.execute(
        """select p.track_id, p.position, p.playing, p.updated,
                  t.title, t.artist, t.album
             from playback p left join tracks t on t.id=p.track_id
            where p.user_id=? limit 1""",
        (account["id"],),
    ).fetchone()
    return account, playback


@bp.get("/u/<username>")
def public_profile(username):
    """A no-login profile card suitable for a Discord/Rotur status link."""
    account, now = _public_account(username)
    if not account:
        return Response("<h1>Profile not found</h1>", status=404, mimetype="text/html")

    base = PUBLIC_URL or request.url_root.rstrip("/")
    name = account["username"]
    profile_url = f"{base}/u/{quote(name)}"
    track_id = now["track_id"] if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    cover_ver = f"{int(track_id)}-{updated}" if track_id else str(updated or int(time.time() // 60))
    cover_url = f"{base}/u/{quote(name)}/cover.png?v={quote(cover_ver)}"
    track = now["title"] if now and now["title"] else ""
    artist = now["artist"] if now and now["artist"] else ""
    album = now["album"] if now and now["album"] else ""
    listening = bool(now and now["playing"] and track)
    if track:
        detail = f"{track} — {artist}" if artist else track
        state = "Listening now" if listening else "Paused"
    else:
        detail = "Nothing playing at the moment"
        state = "mcmusic"
    title = f"{name} · mcmusic"
    desc = f"{state}: {detail}" if track else detail

    page = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>{escape(title)}</title>
<link rel="canonical" href="{escape(profile_url)}">
<meta property="og:type" content="profile">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{escape(profile_url)}">
<meta property="og:image" content="{escape(cover_url)}">
<meta property="og:image:secure_url" content="{escape(cover_url)}">
<meta property="og:image:alt" content="{escape(detail)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(title)}">
<meta name="twitter:description" content="{escape(desc)}">
<meta name="twitter:image" content="{escape(cover_url)}">
<style>
:root{{color-scheme:dark;--bg:#0e0a13;--panel:#1b1325;--line:#3e2b54;--fg:#f2edf7;--dim:#b9abc9;--accent:#ffffff}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:radial-gradient(circle at 50% 0,#241931 0,var(--bg) 55%);color:var(--fg);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif;display:grid;place-items:center;padding:24px}}
a{{color:inherit}}.card{{width:min(100%,430px);background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:18px;box-shadow:0 24px 80px #0008}}
img{{width:100%;aspect-ratio:1;object-fit:cover;border-radius:15px;display:block;background:#241931}}
.kicker{{margin:18px 0 4px;color:var(--accent);font-size:11px;letter-spacing:.14em;text-transform:uppercase}}
h1{{margin:0;font-size:27px;line-height:1.1;letter-spacing:-.03em}}
.state{{color:var(--dim);font-size:12px;margin-top:8px}}.track{{font-size:16px;margin-top:14px;font-weight:600}}
.meta{{color:var(--dim);font-size:12px;margin-top:3px}}.foot{{display:flex;justify-content:space-between;gap:12px;margin-top:20px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--dim)}}
.btn{{color:var(--accent);text-decoration:none;font-weight:600}}@media(max-width:380px){{body{{padding:12px}}.card{{padding:12px;border-radius:18px}}}}
</style></head><body><main class="card">
<img src="{escape(cover_url)}" alt="">
<p class="kicker">mcmusic profile</p>
<h1>{escape(name)}</h1>
<p class="state">{escape(state)}</p>
<p class="track">{escape(track) if track else 'Nothing playing right now'}</p>
<p class="meta">{escape(artist)}{(' · ' + escape(album)) if album else ''}</p>
<div class="foot"><span>{escape(profile_url)}</span><a class="btn" href="{escape(base)}">Open mcmusic</a></div>
</main></body></html>"""
    return Response(page, mimetype="text/html", headers={
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    })


@bp.get("/u/<username>/cover.png")
def public_cover(username):
    """The current track cover, public for status embeds; fallback is the app icon."""
    account, now = _public_account(username)
    if not account:
        return Response(status=404)
    track_id = int(now["track_id"]) if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    etag = f'W/"{track_id}-{updated}"'
    headers = {
        "ETag": etag,
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, s-maxage=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Access-Control-Allow-Origin": "*",
        "Vary": "Accept-Encoding",
    }
    # Always honor versioned URLs as unique resources for CDN caches.
    if request.headers.get("If-None-Match") == etag and not request.args.get("v"):
        return Response(status=304, headers=headers)
    if track_id:
        from routes.library_routes import _track_path, read_cover
        p = _track_path(track_id)
        art = read_cover(p) if p else None
        if art:
            return Response(art[0], mimetype=art[1], headers=headers)
    fallback = os.path.join(current_app.static_folder or "", "icon-512.png")
    if os.path.isfile(fallback):
        resp = send_file(fallback, mimetype="image/png")
        for k, v in headers.items():
            resp.headers[k] = v
        return resp
    return Response(status=404, headers={"Cache-Control": "no-store", "Access-Control-Allow-Origin": "*"})



def _public_payload(username):
    account, now = _public_account(username)
    if not account:
        return None
    base = PUBLIC_URL or request.url_root.rstrip("/")
    name = account["username"]
    track_id = int(now["track_id"]) if now and now["track_id"] else 0
    updated = int((now["updated"] if now and now["updated"] else 0) or 0)
    cover_ver = f"{track_id}-{updated}" if track_id else str(updated or int(time.time() // 60))
    duration = float(now["duration"] or 0) if now and "duration" in now.keys() and now["duration"] is not None else 0.0
    track = {
        "id": track_id,
        "title": (now["title"] if now and now["title"] else ""),
        "artist": (now["artist"] if now and now["artist"] else ""),
        "album": (now["album"] if now and now["album"] else ""),
        "duration": duration,
    } if track_id else None
    listening = bool(now and now["playing"] and track_id)
    position = float(now["position"] or 0) if now and now["position"] is not None else 0.0
    return {
        "ok": True,
        "user": {"username": name},
        "listening": listening,
        "position": position,
        "updated": updated,
        "track": track,
        "profile_url": f"{base}/u/{quote(name)}",
        "cover_url": f"{base}/u/{quote(name)}/cover.png?v={quote(cover_ver)}",
        "base_url": base,
    }


@bp.get("/api/public/now/<username>")
def public_now(username):
    """Now-playing payload used by the web embeds and widgets."""
    payload = _public_payload(username)
    if not payload:
        return jsonify(error="not found"), 404, {"Access-Control-Allow-Origin": "*"}
    resp = jsonify(payload)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "public, max-age=5"
    return resp


@bp.get("/api/public/listening")
def public_listening():
    """Recently active listeners (public, no auth) for embeds/directory pages."""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    since = time.time() - 180
    c = _db()
    rows = c.execute(
        """
        select u.username,
               d.current_track_id as track_id, d.current_position as position,
               d.current_paused as paused, d.current_updated as updated,
               t.title, t.artist, t.album, t.duration
          from devices d
          join users u on u.id = d.user_id
          left join tracks t on t.id = d.current_track_id
         where d.is_active = 1 and d.current_updated >= ?
         order by case when d.current_paused = 0 and d.current_track_id is not null then 0 else 1 end,
                  d.current_updated desc
         limit 40
        """,
        (since,),
    ).fetchall()
    users = []
    seen = set()
    for r in rows:
        name = r["username"]
        if name in seen:
            continue
        seen.add(name)
        track_id = int(r["track_id"]) if r["track_id"] else 0
        updated = int(r["updated"] or 0)
        cover_ver = f"{track_id}-{updated}" if track_id else str(updated or int(time.time() // 60))
        track = None
        if track_id and r["title"]:
            track = {
                "id": track_id,
                "title": r["title"] or "",
                "artist": r["artist"] or "",
                "album": r["album"] or "",
                "duration": float(r["duration"] or 0),
            }
        listening = bool(track_id and not r["paused"])
        users.append({
            "username": name,
            "listening": listening,
            "position": float(r["position"] or 0),
            "updated": updated,
            "track": track,
            "profile_url": f"{base}/u/{quote(name)}",
            "cover_url": f"{base}/u/{quote(name)}/cover.png?v={quote(cover_ver)}",
        })
    resp = jsonify(ok=True, users=users, base_url=base, now=int(time.time()))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "public, max-age=8"
    return resp


@bp.get("/embed")
@bp.get("/embeds")
def embed_info():
    """Public embed gallery: live demos of every widget, copyable tags and a starter stylesheet."""
    base = PUBLIC_URL or request.url_root.rstrip("/")
    html = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>mcmusic embeds — live demo &amp; copy-paste widgets</title>
<meta name="description" content="Live demos of every mcmusic embed widget, with copy-paste script tags, HTML tags and a basic CSS template.">
<link rel="stylesheet" href="/static/ui/flufi-ui.css"><style>
/* Monochrome embeds: pure black/white, no tinted surfaces. */
:root{color-scheme:dark;--back:#000;--back-raised:#0a0a0a;--flat-hover:#161616;--prim:#0d0d0d;--prim-brighter:#111;--seco:#161616;--tert:#222;--tert-hover:#444;--accent:#fff;--accent-hover:#e6e6e6;--text:#ededed;--text-bright:#fff;--text-dim:#a3a3a3;--text-dark:#6b6b6b;--back-border:#222;--prim-border:#262626;--text-on-light:#000}
/* Layout only. Colours, controls, tags and tables come from flufi-ui. */
*,*::before,*::after{box-sizing:border-box}
body{margin:0;font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--text);background:var(--back)}
a{color:var(--accent)}
.wrap{max-width:1120px;margin:0 auto;padding:26px 18px 70px}
.hero{padding:12px 0 4px}
section{margin-top:18px}
.eyebrow{margin:0 0 8px;font:11px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
h1{margin:0;font-size:clamp(27px,5vw,40px);letter-spacing:-.025em;line-height:1.1}
h2{margin:0 0 4px;font-size:19px}
h3{margin:0;font-size:15px}
p{margin:8px 0;color:var(--text-dim)}
.lead{font-size:16px;max-width:64ch}
em{color:var(--text);font-style:normal}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.container{padding:16px}
.muted{color:var(--text-dim);font-size:13px}
pre{margin:12px 0 0;background:var(--prim);border:1px solid var(--prim-border);border-radius:6px;padding:12px 13px;overflow:auto;color:var(--text);font:12.5px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;tab-size:2}
code{font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--text);background:var(--seco);padding:1px 5px;border-radius:4px}
pre code{background:none;padding:0}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}
.controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(185px,100%),1fr));gap:12px;margin-top:14px}
.field{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--text-dim)}
.inline{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--text-dim);cursor:pointer}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(315px,100%),1fr));gap:14px;margin-top:12px}
.w{display:flex;flex-direction:column;gap:8px;background:var(--prim);border:1px solid var(--back-border);border-radius:6px;padding:14px}
.w .head{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.w pre{margin:0;flex:1}
.stage{border:1px dashed var(--prim-border);border-radius:6px;padding:14px;background:var(--back);display:flex;align-items:center;min-height:104px;overflow:auto}
.stage > *{max-width:100%;min-width:0}
.tag.live{color:var(--text-bright)}
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:13px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--back-border);vertical-align:top}
th{color:var(--text-bright);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.07em}
td:first-child{white-space:nowrap}
footer{margin-top:30px;color:var(--text-dark);font-size:13px}
@media(max-width:640px){
  thead{display:none}
  tr{display:block;border:1px solid var(--back-border);border-radius:6px;padding:9px 11px;margin:0 0 9px}
  tr:last-child{margin-bottom:0}
  td{display:block;border:0;padding:2px 0}
  td:first-child{padding-top:0;white-space:normal;font-size:14px;font-weight:600;color:var(--text-bright)}
  td:not(:first-child)::before{content:attr(data-label);display:block;font:10.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--text-dim);margin:5px 0 1px}
  table{margin-top:12px}
}
@media(max-width:520px){
  .wrap{padding:18px 12px 54px}
  .container,.w{padding:12px}
  .stage{padding:11px;min-height:0}
  .w .head{flex-wrap:wrap;row-gap:4px}
  .w pre{white-space:pre-wrap;overflow-wrap:anywhere}
  .row button{width:100%}
  pre{font-size:11.5px;padding:10px 11px}
  h2{font-size:17px}
  .lead{font-size:15px}
  footer{font-size:12px}
  .hero{padding:6px 0 0}
}
</style></head><body><div class="wrap">

<header class="hero">
  <p class="eyebrow">mcmusic · public widgets</p>
  <h1>Embed what you're listening to</h1>
  <p class="lead">Every card below is live: it's rendered by the same script you paste into your own page. Pick a user, tweak the theme, then copy the tags.</p>
  <div class="pills">
    <span class="tag">No account needed</span>
    <span class="tag">Shadow-DOM isolated</span>
    <span class="tag">Zero dependencies</span>
    <span class="tag">Auto-refreshes</span>
  </div>
</header>

<section class="container" id="builder">
  <h2>1 · Include the script once per page</h2>
  <p class="muted">Put this just before <code>&lt;/body&gt;</code>. It registers every widget tag below.</p>
  <pre id="code-script"></pre>
  <div class="row"><button class="button variant-accent" data-copy="code-script">Copy script tag</button></div>

  <h2 style="margin-top:22px">2 · Pick a user and options</h2>
  <p class="muted">Snippets and every preview on this page update as you change these.</p>
  <div class="controls">
    <div class="field"><span>Username</span>
      <input class="input" type="text" id="user" list="live-users" placeholder="username" autocomplete="off" spellcheck="false">
    </div>
    <div class="field"><span>Theme</span>
      <select class="input" id="theme"></select>
    </div>
    <div class="field"><span>Accent colour</span>
      <span class="row" style="margin:0">
        <input type="color" id="accent" value="#ffffff">
        <label class="inline"><input type="checkbox" id="accent-off" checked> use theme colour</label>
      </span>
    </div>
    <div class="field"><span>Refresh every (seconds)</span>
      <input class="input" type="number" id="refresh" min="5" max="600" step="1" value="12">
    </div>
    <div class="field"><span>Scroll text longer than (characters)</span>
      <input class="input" type="number" id="maxlen" min="0" max="200" step="1" value="0" placeholder="0 = never">
    </div>
    <div class="field"><span>Scroll speed (seconds per pass)</span>
      <input class="input" type="number" id="speed" min="3" max="60" step="1" value="18" placeholder="18">
    </div>
    <div class="field"><span>Compact</span>
      <label class="inline"><input type="checkbox" id="compact"> tighter padding and artwork</label>
    </div>
  </div>
  <datalist id="live-users"></datalist>
  <p class="muted" id="note"></p>
</section>

<section>
  <h2>3 · Every widget, live</h2>
  <p class="muted">Six widgets plus three aliases. The previews use <code>refresh="30"</code> to be gentle on the API; the tags you copy use your refresh setting. With no username picked they render built-in sample data, so you can see them working straight away.</p>
  <div class="gallery" id="gallery"></div>
</section>

<section class="container">
  <h2>4 · Basic CSS template</h2>
  <p class="muted">Widgets render inside a shadow root, so your page CSS can't reach their internals — that's why they look consistent anywhere. What <em>does</em> work from outside: width, margins, <code>--mc-radius</code>, <code>--mc-font</code> and the colour variables. Set colours with the <code>theme</code> and <code>accent</code> attributes for ready-made palettes, or with <code>--mc-bg</code>, <code>--mc-bg2</code>, <code>--mc-fg</code>, <code>--mc-dim</code>, <code>--mc-line</code> and <code>--mc-accent</code> from your own CSS — page CSS wins over the attributes.</p>
  <pre id="code-css"></pre>
  <div class="row"><button class="button variant-accent" data-copy="code-css">Copy CSS template</button></div>
  <table class="table">
    <thead><tr><th>Attribute</th><th>Values</th><th>Default</th><th>What it does</th></tr></thead>
    <tbody>
      <tr><td><code>user</code></td><td data-label="Values">any mcmusic username</td><td data-label="Default">—</td><td data-label="What it does">Whose status to show. Required.</td></tr>
      <tr><td><code>theme</code></td><td data-label="Values"><code>dusk</code> <code>paper</code> <code>ink</code> <code>tide</code> <code>copper</code> <code>forest</code> <code>rose</code> <code>auto</code></td><td data-label="Default"><code>dusk</code></td><td data-label="What it does">Colour palette; <code>auto</code> follows the visitor's light/dark preference.</td></tr>
      <tr><td><code>accent</code></td><td data-label="Values">any CSS colour</td><td data-label="Default">theme accent</td><td data-label="What it does">Overrides the highlight colour (dot, progress bar, links). Page CSS <code>--mc-accent</code> beats it.</td></tr>
      <tr><td><code>compact</code></td><td data-label="Values">presence</td><td data-label="Default">off</td><td data-label="What it does">Smaller padding and artwork.</td></tr>
      <tr><td><code>refresh</code></td><td data-label="Values">seconds, min <code>5</code></td><td data-label="Default"><code>12</code></td><td data-label="What it does">How often the widget re-polls the public API.</td></tr>
      <tr><td><code>maxlen</code></td><td data-label="Values">characters, <code>0</code>–<code>200</code></td><td data-label="Default"><code>0</code></td><td data-label="What it does">Longest run of title, artist or badge text shown whole. Past that the line scrolls like the ticker instead of ending in an ellipsis; <code>0</code> never scrolls.</td></tr>
      <tr><td><code>speed</code></td><td data-label="Values">seconds, <code>3</code>–<code>60</code></td><td data-label="Default"><code>18</code></td><td data-label="What it does">Seconds for one pass of scrolling text. Only matters when <code>maxlen</code> is set; lower is faster.</td></tr>
      <tr><td><code>demo</code></td><td data-label="Values">presence</td><td data-label="Default">off</td><td data-label="What it does">Shows built-in sample data instead of polling, for galleries and drafts. Ignored once <code>user</code> is set.</td></tr>
    </tbody>
  </table>
</section>

<section class="container">
  <h2>5 · Complete page</h2>
  <p class="muted">Script, tags and template together — save it as <code>index.html</code> and open it.</p>
  <pre id="code-full"></pre>
  <div class="row"><button class="button variant-accent" data-copy="code-full">Copy full page</button></div>
</section>

<section>
  <h2>Live listeners</h2>
  <p class="muted">People syncing right now. Pick one to use them in the demo above.</p>
  <div class="gallery" id="live"></div>
</section>

<footer>Base URL <code id="base"></code> · JSON: <code>/api/public/now/&lt;username&gt;</code> and <code>/api/public/listening</code></footer>
</div>

<script>
const BASE = "__BASE__";
const SCRIPT_TAG = '<script src="' + BASE + '/static/embed/widgets.js" data-mcmusic-base="' + BASE + '" defer></' + 'script>';

const THEMES = ['dusk', 'paper', 'ink', 'tide', 'copper', 'forest', 'rose', 'auto'];

const WIDGETS = [
  {tag: 'mcmusic-now',         title: 'Now playing',           blurb: 'Cover, track, artist, live progress and listening state — the default card.'},
  {tag: 'mcmusic-turntable',   title: 'Turntable',             blurb: 'Spinning vinyl that turns while they listen and stops when paused.'},
  {tag: 'mcmusic-card',        title: 'Profile card',          blurb: 'Larger profile-style card with artwork and username up front.'},
  {tag: 'mcmusic-bar',         title: 'Mini bar',              blurb: 'One-line horizontal bar for headers, footers and navs.'},
  {tag: 'mcmusic-marquee',     title: 'Marquee',               blurb: 'Scrolling ticker for the tightest spaces.'},
  {tag: 'mcmusic-badge',       title: 'Badge',                 blurb: 'Tiny inline pill for bios and link-in-bio pages.'},
  {tag: 'mcmusic-now-playing', title: 'Alias · now-playing',   blurb: 'Same component as mcmusic-now.', alias: true},
  {tag: 'mcmusic-profile',     title: 'Alias · profile',       blurb: 'Same component as mcmusic-card.', alias: true},
  {tag: 'mcmusic-ticker',      title: 'Alias · ticker',        blurb: 'Same component as mcmusic-marquee.', alias: true},
];

const state = {
  user: localStorage.getItem('mc-embed-user') || '',
  theme: localStorage.getItem('mc-embed-theme') || 'dusk',
  accent: localStorage.getItem('mc-embed-accent') || '',
  compact: localStorage.getItem('mc-embed-compact') === '1',
  refresh: localStorage.getItem('mc-embed-refresh') || '12',
  maxlen: localStorage.getItem('mc-embed-maxlen') || '0',
  speed: localStorage.getItem('mc-embed-speed') || '18',
};

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

function tagFor(w, refresh, demo) {
  const parts = [
    demo ? 'demo' : 'user="' + esc(state.user || 'username') + '"',
    'theme="' + esc(state.theme) + '"',
  ];
  if (state.accent) parts.push('accent="' + esc(state.accent) + '"');
  if (state.compact) parts.push('compact');
  if (state.maxlen && state.maxlen !== '0') {
    parts.push('maxlen="' + esc(state.maxlen) + '"');
    if (state.speed !== '18') parts.push('speed="' + esc(state.speed) + '"');
  }
  parts.push('refresh="' + esc(refresh) + '"');
  return '<' + w.tag + ' ' + parts.join(' ') + '></' + w.tag + '>';
}

function cssTemplate() {
  return [
    '/* mcmusic embeds — basic template',
    '   Widgets render inside a shadow root, so page CSS cannot reach their',
    '   internals. Style them from outside with width, margins, --mc-radius,',
    '   --mc-font and the --mc-* colour variables; the theme and accent',
    '   attributes only supply the defaults.',
    '',
    '   Long titles: maxlen="N" scrolls any line longer than N characters',
    '   instead of clipping it, and speed="S" sets the seconds per pass',
    '   (3-60, default 18). Both are tag attributes, not CSS. */',
    '',
    'mcmusic-now, mcmusic-now-playing,',
    'mcmusic-card, mcmusic-profile,',
    'mcmusic-turntable {',
    '  display: block;',
    '  max-width: 360px;      /* card widgets read best at 320-420px */',
    '  margin: 16px 0;',
    '  --mc-radius: 16px;     /* corner rounding (default 18px) */',
    '  --mc-font: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;',
    '  /* colours — uncomment and set your own to ignore the palette: */',
    '  /* --mc-bg: #101820;  --mc-bg2: #080d12;  --mc-fg: #f2f6f8; */',
    '  /* --mc-dim: #a8b8c2;  --mc-line: #2c3d4a;  --mc-accent: #79d8a5; */',
    '}',
    '',
    'mcmusic-bar, mcmusic-marquee, mcmusic-ticker {',
    '  display: block;',
    '  max-width: 520px;      /* full width for headers and footers */',
    '  margin: 12px 0;',
    '  --mc-radius: 12px;',
    '  --mc-font: inherit;    /* match the surrounding page font */',
    '}',
    '',
    'mcmusic-badge {',
    '  display: inline-block; /* sits next to text in a bio */',
    '  vertical-align: middle;',
    '  --mc-font: inherit;',
    '}',
    '',
    '@media (max-width: 380px) {',
    '  mcmusic-now, mcmusic-now-playing,',
    '  mcmusic-card, mcmusic-profile,',
    '  mcmusic-turntable { margin: 12px 0; }',
    '}',
  ].join('\n');
}

function renderGallery() {
  const host = document.getElementById('gallery');
  host.innerHTML = WIDGETS.map((w) => {
    const code = tagFor(w, state.refresh);
    const preview = tagFor(w, 30, !state.user);
    return '<div class="w">'
      + '<div class="head"><h3>' + esc(w.title) + '</h3><span class="tag">' + (w.alias ? 'alias' : '&lt;' + w.tag + '&gt;') + '</span></div>'
      + '<p class="muted" style="margin:0">' + esc(w.blurb) + '</p>'
      + '<div class="stage">' + preview + '</div>'
      + '<pre id="code-' + w.tag + '">' + esc(code) + '</pre>'
      + '<div class="row"><button class="button variant-panel" data-copy="code-' + w.tag + '">Copy tag</button></div>'
      + '</div>';
  }).join('');
}

function renderFull() {
  const now = tagFor(WIDGETS[0], state.refresh);
  const bar = tagFor(WIDGETS[3], state.refresh);
  const badge = tagFor(WIDGETS[5], state.refresh);
  document.getElementById('code-full').textContent = [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '  <meta charset="utf-8">',
    '  <meta name="viewport" content="width=device-width, initial-scale=1">',
    '  <title>Now playing</title>',
    '  <style>',
    cssTemplate().split('\n').map(l => '    ' + l).join('\n'),
    '  </style>',
    '</head>',
    '<body>',
    '  <h1>Now playing</h1>',
    '  ' + now,
    '',
    '  <p>Also listening:</p>',
    '  ' + bar,
    '  ' + badge,
    '',
    '  <!-- mcmusic embeds: load once, after the tags -->',
    '  ' + SCRIPT_TAG,
    '</body>',
    '</html>',
  ].join('\n');
}

function renderNote() {
  const el = document.getElementById('note');
  const user = state.user || 'sample data (no username needed)';
  el.innerHTML = 'Showing <em>' + esc(user) + '</em> · theme <em>' + esc(state.theme) + '</em>'
    + (state.compact ? ' · compact' : '')
    + (state.maxlen && state.maxlen !== '0'
      ? ' · text scrolls past <em>' + esc(state.maxlen) + '</em> chars, <em>' + esc(state.speed) + '</em>s per pass'
      : '')
    + (state.accent ? ' · accent <em>' + esc(state.accent) + '</em>' : '')
    + (state.user
      ? '. Unknown usernames render an “unavailable” state.'
      : '. Type a username (or pick a live listener below) to see your own.');
}

let renderTimer = null;
function scheduleRender() {
  clearTimeout(renderTimer);
  renderTimer = setTimeout(() => { renderGallery(); renderFull(); renderNote(); }, 220);
}

function setUser(name) {
  state.user = name || '';
  document.getElementById('user').value = state.user;
  localStorage.setItem('mc-embed-user', state.user);
  scheduleRender();
}

function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
  }
  return Promise.resolve(fallbackCopy(text));
}
function fallbackCopy(text) {
  const t = document.createElement('textarea');
  t.value = text;
  t.setAttribute('readonly', '');
  t.style.position = 'fixed';
  t.style.top = '-1000px';
  document.body.appendChild(t);
  t.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
  t.remove();
  return ok;
}

document.addEventListener('click', (e) => {
  const use = e.target.closest('[data-use]');
  if (use) {
    setUser(use.getAttribute('data-use'));
    document.getElementById('builder').scrollIntoView({behavior: 'smooth', block: 'center'});
    return;
  }
  const btn = e.target.closest('[data-copy]');
  if (!btn) return;
  const el = document.getElementById(btn.getAttribute('data-copy'));
  if (!el) return;
  const label = btn.textContent;
  copyText(el.textContent).then((ok) => {
    btn.classList.toggle('copied', !!ok);
    btn.textContent = ok ? 'Copied ✓' : 'Press ⌘/Ctrl+C';
    setTimeout(() => { btn.classList.remove('copied'); btn.textContent = label; }, 1600);
  });
});

function syncControls() {
  document.getElementById('user').value = state.user;
  document.getElementById('theme').value = state.theme;
  document.getElementById('accent').value = state.accent || '#ffffff';
  document.getElementById('accent-off').checked = !state.accent;
  document.getElementById('accent').disabled = !state.accent;
  document.getElementById('compact').checked = state.compact;
  document.getElementById('refresh').value = state.refresh;
  document.getElementById('maxlen').value = state.maxlen;
  document.getElementById('speed').value = state.speed;
}

function init() {
  const themes = document.getElementById('theme');
  themes.innerHTML = THEMES.map(t => '<option value="' + t + '">' + t + (t === 'auto' ? ' (follow system)' : '') + '</option>').join('');

  document.getElementById('code-script').textContent = SCRIPT_TAG;
  document.getElementById('code-css').textContent = cssTemplate();
  document.getElementById('base').textContent = BASE;

  document.getElementById('user').addEventListener('input', (e) => {
    state.user = e.target.value.trim();
    localStorage.setItem('mc-embed-user', state.user);
    scheduleRender();
  });
  document.getElementById('theme').addEventListener('change', (e) => {
    state.theme = e.target.value;
    localStorage.setItem('mc-embed-theme', state.theme);
    scheduleRender();
  });
  document.getElementById('accent').addEventListener('input', (e) => {
    if (!state.accent) return;
    state.accent = e.target.value;
    localStorage.setItem('mc-embed-accent', state.accent);
    scheduleRender();
  });
  document.getElementById('accent-off').addEventListener('change', (e) => {
    state.accent = e.target.checked ? '' : document.getElementById('accent').value;
    document.getElementById('accent').disabled = e.target.checked;
    localStorage.setItem('mc-embed-accent', state.accent);
    scheduleRender();
  });
  document.getElementById('compact').addEventListener('change', (e) => {
    state.compact = e.target.checked;
    localStorage.setItem('mc-embed-compact', state.compact ? '1' : '0');
    scheduleRender();
  });
  document.getElementById('refresh').addEventListener('change', (e) => {
    const n = Math.min(600, Math.max(5, parseInt(e.target.value, 10) || 12));
    state.refresh = String(n);
    e.target.value = state.refresh;
    localStorage.setItem('mc-embed-refresh', state.refresh);
    scheduleRender();
  });
  document.getElementById('maxlen').addEventListener('change', (e) => {
    const n = Math.min(200, Math.max(0, parseInt(e.target.value, 10) || 0));
    state.maxlen = String(n);
    e.target.value = state.maxlen;
    localStorage.setItem('mc-embed-maxlen', state.maxlen);
    scheduleRender();
  });
  document.getElementById('speed').addEventListener('change', (e) => {
    const n = Math.min(60, Math.max(3, parseInt(e.target.value, 10) || 18));
    state.speed = String(n);
    e.target.value = state.speed;
    localStorage.setItem('mc-embed-speed', state.speed);
    scheduleRender();
  });

  syncControls();
  renderGallery();
  renderFull();
  renderNote();
  loadListening();
  setInterval(loadListening, 20000);
}

async function loadListening() {
  const host = document.getElementById('live');
  try {
    const res = await fetch(BASE + '/api/public/listening', {headers: {accept: 'application/json'}});
    const data = await res.json();
    const users = data.users || [];
    document.getElementById('live-users').innerHTML = users.map(u => '<option value="' + esc(u.username) + '"></option>').join('');
    if (!state.user && users.length) setUser(users[0].username);
    host.innerHTML = users.map((u) => {
      const t = u.track || {};
      const title = t.title || 'Nothing playing';
      const sub = t.artist ? t.artist + (t.album ? ' · ' + t.album : '') : (u.listening ? 'Listening' : 'Paused');
      return '<div class="w">'
        + '<div class="head"><h3>' + esc(u.username) + '</h3><span class="tag' + (u.listening ? ' live' : '') + '">' + (u.listening ? 'listening' : 'paused') + '</span></div>'
        + '<div class="row" style="margin-top:6px;align-items:center;flex-wrap:nowrap">'
        + '<img class="cover" src="' + esc(u.cover_url) + '" alt="" loading="lazy">'
        + '<div style="min-width:0"><b style="display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(title) + '</b>'
        + '<span class="muted">' + esc(sub) + '</span></div></div>'
        + '<div class="row"><button class="button variant-panel" data-use="' + esc(u.username) + '">Demo this user</button></div>'
        + '</div>';
    }).join('') || '<p class="muted">Nobody is listening right now. The previews above are showing sample data — type a username in the box above to see your own.</p>';
  } catch (e) {
    host.innerHTML = '<p class="muted">Could not load listeners.</p>';
  }
}

init();
</script>
<script src="__SCRIPT__" data-mcmusic-base="__BASE__" defer></script>
</body></html>"""
    html = html.replace("__BASE__", base).replace("__SCRIPT__", f"{base}/static/embed/widgets.js")
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-cache"})


@bp.post("/api/rooms")
@login_required
def room_create():
    """Create a listen-along room for the signed-in account."""
    uid = session["uid"]
    name = _db().execute("select username from users where id=?", (uid,)).fetchone()["username"]
    code = personal_room_code(uid)
    with rooms_lock:
        _prune_rooms()
        for old in [c for c, r in rooms.items() if r["host"] == uid and c != code]:
            del rooms[old]
        rooms[code] = {"host": uid, "host_name": name, "track_id": None, "pos": 0.0,
                       "playing": False, "ts": time.time()}
    return jsonify(code=code)


@bp.post("/api/rooms/<code>/state")
@login_required
def room_push(code):
    """Push the current track/position into a room."""
    d = request.get_json(silent=True) or {}
    with rooms_lock:
        r = rooms.get(code)
        if not r:
            return jsonify(error="no such room"), 404
        if r["host"] != session["uid"]:
            return jsonify(error="not the host"), 403
        tid = d.get("track_id")
        if tid is not None and not _db().execute("select 1 from tracks where id=?", (int(tid),)).fetchone():
            return jsonify(error="no such track"), 404
        r.update(track_id=int(tid) if tid is not None else None,
                 pos=max(0.0, float(d.get("pos", 0) or 0)),
                 playing=bool(d.get("playing")), ts=time.time())
    return jsonify(ok=True)


@bp.get("/api/rooms/<code>")
@login_required
def room_get(code):
    """Snapshot of a room (track, position, listeners)."""
    with rooms_lock:
        r = dict(rooms.get(code) or {})
    if not r:
        return jsonify(error="room not found or ended"), 404
    now = time.time()
    track = None
    if r["track_id"] is not None:
        row = _db().execute("select * from tracks where id=?", (r["track_id"],)).fetchone()
        track = track_dict(_db(), row, liked_ids(_db(), session["uid"])) if row else None
    away = now - r["ts"] > ROOM_STALE
    return jsonify(host_id=r["host"], host_name=r["host_name"], track=track, pos=r["pos"],
                   playing=r["playing"] and not away, host_away=away,
                   state_ts=r["ts"], server_now=now)


@bp.delete("/api/rooms/<code>")
@login_required
def room_close(code):
    """Close a room owned by the signed-in account."""
    with rooms_lock:
        r = rooms.get(code)
        if r and r["host"] == session["uid"]:
            del rooms[code]
    return jsonify(ok=True)


@bp.get("/api/admin/rooms")
@admin_required
def admin_rooms():
    """All open rooms, for the admin overview."""
    now = time.time()
    with rooms_lock:
        data = [(code, dict(r)) for code, r in rooms.items()]
    out = []
    for code, r in data:
        track = None
        if r["track_id"] is not None:
            row = _db().execute("select id,title,artist,album from tracks where id=?", (r["track_id"],)).fetchone()
            track = dict(row) if row else None
        out.append({"code": code, "host": r["host_name"], "host_id": r["host"], "track": track,
                    "pos": r["pos"], "playing": r["playing"], "idle": now - r["ts"],
                    "away": now - r["ts"] > ROOM_STALE})
    out.sort(key=lambda x: -x["idle"])
    return jsonify(rooms=out)


@bp.delete("/api/admin/rooms/<code>")
@admin_required
def admin_room_close(code):
    """Force-close a room as an admin."""
    with rooms_lock:
        rooms.pop(code, None)
    return jsonify(ok=True)


# --------------------------------------------------------------------------- download requests
dl_q = __import__("queue").Queue()
running = {}
running_lock = threading.Lock()
cancel_requested = set()
_size_cache = {"t": 0.0, "v": 0}


def req_log_path(rid):
    return os.path.join(LOG_DIR, f"{rid}.log")


def read_req_log(rid, tail=200_000):
    try:
        with open(req_log_path(rid), "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - tail))
            return fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def trim_req_log(rid):
    p = req_log_path(rid)
    try:
        if os.path.getsize(p) <= 512 * 1024:
            return
        with open(p, "rb") as fh:
            fh.seek(-(512 * 1024 // 2), os.SEEK_END)
            data = fh.read()
        with open(p, "wb") as fh:
            fh.write(b"[... earlier output trimmed ...]\n" + data)
    except OSError:
        pass


def dir_size(path, ttl=30):
    now = time.time()
    if now - _size_cache["t"] > ttl:
        total = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        _size_cache.update(t=now, v=total)
    return _size_cache["v"]


def valid_yt(url):
    from urllib.parse import urlparse
    u = urlparse(url)
    return u.scheme == "https" and (u.hostname or "").lower() in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"
    }


def worker():
    conn = _db()
    while True:
        rid = dl_q.get()
        row = conn.execute("select * from requests where id=?", (rid,)).fetchone()
        if not row or row["status"] != "approved":
            continue
        conn.execute("update requests set status='running', finished=NULL where id=?", (rid,))
        conn.commit()
        cmd = [
            __import__("sys").executable, DL_SCRIPT, row["url"], "-o", MUSIC_DIR,
            "--staging", STAGING_DIR,
        ] + shlex.split(DL_ARGS)
        logp = req_log_path(rid)
        ok, cancelled = False, False
        with open(logp, "w") as fh:
            fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] request #{rid}\n")
            fh.write("$ " + " ".join(shlex.quote(c) for c in cmd) + "\n\n")
            fh.flush()
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            with running_lock:
                running[rid] = {"pid": proc.pid, "started": time.time(), "proc": proc}
            last_sync = 0.0
            last_scan = 0.0
            with open(logp, "a") as fh:
                for line in proc.stdout:
                    fh.write(line)
                    fh.flush()
                    now = time.time()
                    if now - last_sync > 2:
                        last_sync = now
                        conn.execute("update requests set log=? where id=?", (read_req_log(rid, 4000), rid))
                        conn.commit()
                    if now - last_scan > 30:
                        last_scan = now
                        try:
                            scan_library(conn)
                        except Exception as e:
                            fh.write(f"[scan warning] {e}\n")
                            fh.flush()
            rc = proc.wait()
            ok = rc == 0
            with open(logp, "a") as fh:
                fh.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] exited with code {rc}\n")
        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.exception("download request %s failed", rid)
            except Exception:
                pass
            with open(logp, "a") as fh:
                fh.write(f"\n[ERROR] {e}\n")
        finally:
            with running_lock:
                running.pop(rid, None)
                cancelled = rid in cancel_requested
                cancel_requested.discard(rid)
        trim_req_log(rid)
        try:
            scan_library(conn)
        except Exception:
            pass
        status = "cancelled" if cancelled else ("done" if ok else "failed")
        conn.execute(
            "update requests set status=?, log=?, finished=? where id=?",
            (status, read_req_log(rid, 4000), time.time(), rid),
        )
        conn.commit()


@bp.post("/api/requests")
@login_required
def req_create():
    """Submit a download request; admins start it immediately."""
    url = str((request.get_json(silent=True) or {}).get("url", "")).strip()
    if len(url) > 2048:
        return jsonify(error="URL too long"), 400
    if not valid_yt(url):
        return jsonify(error="need an https YouTube / YouTube Music video or playlist link"), 400
    c = _db()
    repeat = find_repeat_request(c, url)
    if repeat:
        return jsonify(error="that link is already queued", request_id=repeat["id"],
                       status=repeat["status"]), 409
    if video_in_library(c, url):
        return jsonify(error="that song is already in the library"), 409
    admin = c.execute("select is_admin from users where id=?", (session["uid"],)).fetchone()["is_admin"]
    status = "approved" if (AUTO_APPROVE or admin) else "pending"
    cur = c.execute(
        "insert into requests(user_id,url,status,created) values(?,?,?,?)",
        (session["uid"], url, status, time.time()),
    )
    c.commit()
    if status == "approved":
        dl_q.put(cur.lastrowid)
    return jsonify(id=cur.lastrowid, status=status)


@bp.get("/api/requests")
@login_required
def req_list():
    """The signed-in user's download requests."""
    c = _db()
    admin = c.execute("select is_admin from users where id=?", (session["uid"],)).fetchone()["is_admin"]
    q = """select r.id, r.url, r.status, r.created, r.log, u.username from requests r
           join users u on u.id=r.user_id {} order by r.id desc limit 100"""
    rows = c.execute(q.format("" if admin else "where r.user_id=?"), () if admin else (session["uid"],))
    return jsonify(requests=[dict(r, log=(r["log"] or "")[-500:]) for r in rows], is_admin=bool(admin))


@bp.post("/api/requests/<int:rid>/<action>")
@admin_required
def req_act(rid, action):
    """Approve, reject, cancel or retry a download request."""
    if action not in ("approve", "reject"):
        return jsonify(error="bad action"), 400
    r = _db().execute("select status from requests where id=?", (rid,)).fetchone()
    if not r or r["status"] not in ("pending", "failed"):
        return jsonify(error="can't change that request"), 409
    _db().execute("update requests set status=? where id=?", ("approved" if action == "approve" else "rejected", rid))
    _db().commit()
    if action == "approve":
        dl_q.put(rid)
    return jsonify(ok=True)


# --------------------------------------------------------------------------- devices (cross-device sync)
@bp.get("/api/devices")
@login_required
def devices_list():
    """Devices registered to the current account."""
    rows = _db().execute(
        """select d.id, d.device_hash, d.ip, d.user_agent, d.name, d.last_seen,
                   d.current_track_id, d.current_position, d.current_paused,
                   d.current_updated, d.is_active,
                   t.title as track_title, t.artist as track_artist
             from devices d left join tracks t on t.id=d.current_track_id
             where d.user_id=? order by d.is_active desc, d.last_seen desc""",
        (session["uid"],)
    )
    return jsonify(devices=[dict(r) for r in rows])


@bp.post("/api/devices/heartbeat")
@login_required
def devices_heartbeat():
    """Heartbeat from a playing client; updates presence and the active device."""
    d = request.get_json(silent=True) or {}
    device_hash = str(d.get("device_hash", ""))[:64].strip()
    if not device_hash:
        return jsonify(error="device_hash required"), 400
    name = str(d.get("name", "")).strip()[:64] or None
    ua = str(request.headers.get("User-Agent", ""))[:200]
    ip = request.remote_addr or "0.0.0.0"
    now = time.time()
    track_id = d.get("track_id")
    position = d.get("position")
    paused = d.get("paused", 0)
    c = _db()
    row = c.execute("select id from devices where user_id=? and device_hash=?", (session["uid"], device_hash)).fetchone()
    if row:
        c.execute(
            """update devices set ip=?, user_agent=?, name=coalesce(?,name), last_seen=?,
                           current_track_id=?, current_position=?, current_paused=?, current_updated=?
                           where id=?""",
            (ip, ua, name, now, track_id, position, int(bool(paused)), now, row["id"]),
        )
        did = row["id"]
    else:
        cur = c.execute(
            """insert into devices(user_id, device_hash, ip, user_agent, name, last_seen,
                           current_track_id, current_position, current_paused, current_updated, is_active)
                           values(?,?,?,?,?,?,?,?,?,?,0)""",
            (session["uid"], device_hash, ip, ua, name, now, track_id, position,
             int(bool(paused)), now),
        )
        did = cur.lastrowid
    n = c.execute("select count(*) cnt from devices where user_id=?", (session["uid"],)).fetchone()["cnt"]
    if n == 1:
        c.execute("update devices set is_active=1 where id=?", (did,))
    c.commit()
    active_id = c.execute("select id from devices where user_id=? and is_active=1", (session["uid"],)).fetchone()[0]
    return jsonify(id=did, active=did == active_id)


@bp.post("/api/devices/<int:did>/activate")
@login_required
def devices_activate(did):
    """Make one of the account's devices the active speaker."""
    row = _db().execute("select id from devices where id=? and user_id=?", (did, session["uid"])).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    _db().execute("update devices set is_active=0 where user_id=?", (session["uid"],))
    _db().execute("update devices set is_active=1 where id=?", (did,))
    _db().commit()
    return jsonify(ok=True, active_device=did)


@bp.patch("/api/devices/<int:did>")
@login_required
def devices_rename(did):
    """Rename a single registered device."""
    row = _db().execute("select id from devices where id=? and user_id=?", (did, session["uid"])).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()[:64]
    if not name:
        return jsonify(error="name required"), 400
    _db().execute("update devices set name=? where id=?", (name, did))
    _db().commit()
    return jsonify(ok=True, name=name)


@bp.delete("/api/devices/<int:did>")
@login_required
def devices_forget(did):
    """Forget (delete) a single registered device."""
    row = _db().execute("select id from devices where id=? and user_id=?", (did, session["uid"])).fetchone()
    if not row:
        return jsonify(error="not found"), 404
    _db().execute("delete from devices where id=?", (did,))
    _db().commit()
    return jsonify(ok=True, id=did)


@bp.post("/api/devices/cleanup")
@login_required
def devices_cleanup():
    """Drop devices not seen in 30+ days."""
    c = _db()
    cutoff = time.time() - 30 * 86400
    c.execute("delete from devices where last_seen < ?", (cutoff,))
    c.commit()
    return jsonify(ok=True)


@bp.post("/api/devices/clear")
@login_required
def devices_clear():
    """Remove device records for this user (fixes broken/stale devices after updates)."""
    c = _db()
    c.execute("delete from devices where user_id=?", (session["uid"],))
    c.commit()
    return jsonify(ok=True)


@bp.get("/api/devices/sync")
@login_required
def devices_sync():
    """Playback sync payload shared between the account's devices."""
    row = _db().execute(
        """select d.id, d.device_hash, d.name, d.current_track_id, d.current_position,
                  d.current_paused, d.current_updated,
                  t.title as track_title, t.artist as track_artist, t.album as track_album,
                  t.duration as track_duration
             from devices d
             left join tracks t on t.id = d.current_track_id
            where d.user_id=? and d.is_active=1 limit 1""", (session["uid"],)
    ).fetchone()
    if not row:
        return jsonify(sync=None)
    return jsonify(sync=dict(row))


# --------------------------------------------------------------------------- device pairing
@bp.post("/api/devices/code")
@login_required
def devices_code():
    """Mint a short code the user reads out to an old phone or handheld."""
    c = _db()
    uid = session["uid"]
    out = create_device_code(c, uid)
    row = c.execute("select username from users where id=?", (uid,)).fetchone()
    base = PUBLIC_URL or request.url_root.rstrip("/")
    out.update(
        ok=True,
        account=row["username"] if row else None,
        claim_url=f"{base}/#devices",
        hint="Enter this code in the app you want to sign in. It works once, "
             "for five minutes.",
    )
    return jsonify(**out)


@bp.post("/api/devices/claim")
def devices_claim():
    """Unpaired device: trade the short code for a long-lived bearer token."""
    d = request.get_json(silent=True) or {}
    out = claim_device_code(
        _db(),
        str(d.get("code", "")),
        name=str(d.get("name", "")),
        ip=request.remote_addr or "0.0.0.0",
        ua=str(request.headers.get("User-Agent", ""))[:200],
        device_hash=str(d.get("device_hash", "")),
    )
    if not out:
        return jsonify(
            error="That code is wrong, already used, or expired. "
                  "Ask for a fresh one."
        ), 400
    return jsonify(ok=True, **out)


@bp.get("/api/devices/tokens")
@login_required
def devices_tokens_list():
    """List device tokens by prefix only, never the secret."""
    return jsonify(tokens=list_device_tokens(_db(), session["uid"]))


@bp.post("/api/devices/tokens/<int:tid>/revoke")
@login_required
def devices_token_revoke(tid):
    """Revoke one device token, signing that client out."""
    if not revoke_device_token(_db(), session["uid"], tid):
        return jsonify(error="not found"), 404
    return jsonify(ok=True)


@bp.get("/api/admin/devices")
@admin_required
def admin_devices():
    """All devices across accounts, for admins."""
    rows = _db().execute(
        """select d.id, d.device_hash, d.ip, d.user_agent, d.name, d.last_seen,
                  d.current_track_id, d.current_position, d.current_paused,
                  d.current_updated, d.is_active, u.username
             from devices d join users u on u.id=d.user_id
             order by d.last_seen desc limit 200"""
    )
    return jsonify(devices=[dict(r) for r in rows])


# --------------------------------------------------------------------------- admin
@bp.get("/api/admin/invite-codes")
@admin_required
def admin_invite_list():
    """Invite codes with usage and expiry state."""
    c = _db()
    rows = c.execute(
        "select i.*, u.username created_by_name from invite_codes i "
        "left join users u on u.id=i.created_by order by i.created desc limit 200"
    ).fetchall()
    out = []
    now = time.time()
    for r in rows:
        d = dict(r)
        d["expired"] = bool(r["expires"] and now > r["expires"])
        d["exhausted"] = r["uses"] >= r["max_uses"]
        d["used_by"] = [dict(x) for x in c.execute(
            "select username, created from users where invite_code=? order by created",
            (r["code"],),
        )]
        out.append(d)
    return jsonify(codes=out)


@bp.post("/api/admin/invite-codes")
@admin_required
def admin_invite_create():
    """Create an invite code with a use limit and optional expiry."""
    d = request.get_json(silent=True) or {}
    try:
        uses = max(1, min(int(d.get("uses") or 1), 100))
    except (TypeError, ValueError):
        uses = 1
    try:
        hours = max(0, min(float(d.get("hours") or 0), 24 * 365))
    except (TypeError, ValueError):
        hours = 0
    note = str(d.get("note", ""))[:100]
    for_user = str(d.get("for_user", "")).strip()[:32]
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    c = _db()
    code = "".join(secrets.choice(alphabet) for _ in range(4)) + "-" + \
        "".join(secrets.choice(alphabet) for _ in range(4))
    while c.execute("select 1 from invite_codes where code=?", (code,)).fetchone():
        code = "".join(secrets.choice(alphabet) for _ in range(9))
    cur = c.execute(
        "insert into invite_codes(code,created_by,created,max_uses,uses,expires,note,for_user,active)"
        " values(?,?,?,?,0,?,?,?,1)",
        (code, session["uid"], time.time(), uses,
         time.time() + hours * 3600 if hours else 0, note, for_user),
    )
    c.commit()
    return jsonify(id=cur.lastrowid, code=code, max_uses=uses,
                   expires=time.time() + hours * 3600 if hours else 0)


@bp.delete("/api/admin/invite-codes/<int:code_id>")
@admin_required
def admin_invite_revoke(code_id):
    """Revoke an invite code so it can no longer be redeemed."""
    c = _db()
    c.execute("update invite_codes set active=0 where id=?", (code_id,))
    c.commit()
    return jsonify(ok=True)


@bp.get("/api/admin/stats")
@admin_required
def admin_stats():
    """Counts, disk usage and request totals for the admin overview."""
    c = _db()
    req = {r["status"]: r["n"] for r in c.execute("select status, count(*) n from requests group by status")}
    dur = shutil.disk_usage(MUSIC_DIR)
    with running_lock:
        run = [{"id": rid, "pid": v["pid"], "elapsed": time.time() - v["started"]}
               for rid, v in running.items()]
    with rooms_lock:
        room_count = len(rooms)
    return jsonify(
        users=c.execute("select count(*) n from users").fetchone()["n"],
        admins=c.execute("select count(*) n from users where is_admin=1").fetchone()["n"],
        tracks=c.execute("select count(*) n from tracks").fetchone()["n"],
        albums=c.execute("select count(distinct album) n from tracks").fetchone()["n"],
        playlists=c.execute("select count(*) n from playlists").fetchone()["n"],
        plays=c.execute("select count(*) n from plays").fetchone()["n"],
        requests=req, queue=dl_q.qsize(), rooms=room_count, running=run,
        music_bytes=dir_size(MUSIC_DIR), disk_total=dur.total, disk_free=dur.free, disk_used=dur.used,
        uptime=time.time() - START_TIME, pid=os.getpid(),
    )


@bp.get("/api/admin/algo")
@admin_required
def admin_algo():
    """Read-only view of the learning-only next-song model."""
    from next_song_model import algo_status
    return jsonify(algo_status())


@bp.get("/api/admin/requests")
@admin_required
def admin_req_list():
    """Every download request, newest first."""
    limit = min(max(int(request.args.get("limit", 200)), 1), 500)
    rows = _db().execute(
        "select r.*, u.username from requests r left join users u on u.id=r.user_id order by r.id desc limit ?",
        (limit,),
    ).fetchall()
    now = time.time()
    with running_lock:
        active = set(running)
    out = []
    for r in rows:
        d = dict(r)
        d["running"] = r["id"] in active
        d["elapsed"] = ((now if r["status"] == "running" else (r["finished"] or now)) - r["created"]) if r["created"] else None
        d["log"] = read_req_log(r["id"], 4000) if d["running"] else (r["log"] or "")
        try:
            d["log_size"] = os.path.getsize(req_log_path(r["id"]))
        except OSError:
            d["log_size"] = 0
        out.append(d)
    return jsonify(requests=out, is_admin=True)


@bp.get("/api/admin/requests/<int:rid>/log")
@admin_required
def admin_req_log(rid):
    """Tail of a request's downloader log."""
    r = _db().execute("select id,status,created,finished,url from requests where id=?", (rid,)).fetchone()
    if not r:
        return jsonify(error="not found"), 404
    tail = min(max(int(request.args.get("tail", 200_000)), 1024), 1_000_000)
    with running_lock:
        ent = running.get(rid)
        is_running, pid = ent is not None, (ent["pid"] if ent else None)
    text = read_req_log(rid, tail)
    if not text:
        text = _db().execute("select log from requests where id=?", (rid,)).fetchone()["log"] or ""
    return jsonify(id=rid, status=r["status"], running=is_running, pid=pid,
                   created=r["created"], finished=r["finished"], url=r["url"], log=text)


@bp.post("/api/admin/requests/<int:rid>/cancel")
@admin_required
def admin_req_cancel(rid):
    """Cancel a queued or running request."""
    with running_lock:
        ent = running.get(rid)
        if ent:
            cancel_requested.add(rid)
            proc = ent["proc"]
    if not ent:
        r = _db().execute("select status from requests where id=?", (rid,)).fetchone()
        if not r:
            return jsonify(error="not found"), 404
        if r["status"] not in ("approved", "pending"):
            return jsonify(error="not running or queued"), 409
        _db().execute("update requests set status='cancelled', finished=? where id=?", (time.time(), rid))
        _db().commit()
        return jsonify(ok=True)
    proc.terminate()

    def _kill():
        if proc.poll() is None:
            proc.kill()

    t = threading.Timer(5, _kill)
    t.daemon = True
    t.start()
    return jsonify(ok=True)


@bp.post("/api/admin/requests/<int:rid>/retry")
@admin_required
def admin_req_retry(rid):
    """Requeue a failed request."""
    with running_lock:
        if rid in running:
            return jsonify(error="still running"), 409
    if not _db().execute("select 1 from requests where id=?", (rid,)).fetchone():
        return jsonify(error="not found"), 404
    try:
        with open(req_log_path(rid), "w") as fh:
            fh.write("")
    except OSError:
        pass
    _db().execute("update requests set status='approved', log='', finished=NULL where id=?", (rid,))
    _db().commit()
    dl_q.put(rid)
    return jsonify(ok=True)


@bp.delete("/api/admin/requests/<int:rid>")
@admin_required
def admin_req_delete(rid):
    """Delete a request row and its log."""
    with running_lock:
        if rid in running:
            return jsonify(error="cancel it first"), 409
    _db().execute("delete from requests where id=?", (rid,))
    _db().commit()
    try:
        os.remove(req_log_path(rid))
    except OSError:
        pass
    return jsonify(ok=True)


@bp.get("/api/admin/users")
@admin_required
def admin_users():
    """Accounts with play/like/playlist counts."""
    rows = _db().execute(
        """select u.id, u.username, u.email, u.is_admin, u.created,
            (select count(*) from plays p where p.user_id=u.id) plays,
            (select count(*) from likes l where l.user_id=u.id) likes,
            (select count(*) from playlists pl where pl.user_id=u.id) playlists,
            (select count(*) from requests r where r.user_id=u.id) requests
            from users u order by u.id"""
    ).fetchall()
    return jsonify(users=[dict(r) for r in rows])


@bp.post("/api/admin/users/<int:uid>/admin")
@admin_required
def admin_user_admin(uid):
    """Promote or demote an account."""
    val = 1 if (request.get_json(silent=True) or {}).get("is_admin") else 0
    u = _db().execute("select id, is_admin from users where id=?", (uid,)).fetchone()
    if not u:
        return jsonify(error="not found"), 404
    if uid == session["uid"] and not val:
        return jsonify(error="you can't remove your own admin"), 400
    if not val and u["is_admin"]:
        n = _db().execute("select count(*) n from users where is_admin=1 and id!=?", (uid,)).fetchone()["n"]
        if n == 0:
            return jsonify(error="at least one admin is required"), 400
    _db().execute("update users set is_admin=? where id=?", (val, uid))
    _db().commit()
    return jsonify(ok=True)


@bp.delete("/api/admin/users/<int:uid>")
@admin_required
def admin_user_delete(uid):
    """Delete an account and everything it owns."""
    if uid == session["uid"]:
        return jsonify(error="you can't delete yourself"), 400
    u = _db().execute("select id, is_admin from users where id=?", (uid,)).fetchone()
    if not u:
        return jsonify(error="not found"), 404
    if u["is_admin"]:
        n = _db().execute("select count(*) n from users where is_admin=1 and id!=?", (uid,)).fetchone()["n"]
        if n == 0:
            return jsonify(error="at least one admin is required"), 400
    if _db().execute("select 1 from requests where user_id=? and status in ('running','approved') limit 1", (uid,)).fetchone():
        return jsonify(error="user has active requests; cancel them first"), 409
    ids = [r["id"] for r in _db().execute("select id from requests where user_id=?", (uid,))]
    _db().execute("delete from users where id=?", (uid,))
    _db().commit()
    for rid in ids:
        try:
            os.remove(req_log_path(rid))
        except OSError:
            pass
    return jsonify(ok=True)


@bp.post("/api/admin/scan")
@admin_required
def admin_scan():
    """Rescan the music folder into the database."""
    scan_library(_db())
    c = _db()
    return jsonify(tracks=c.execute("select count(*) n from tracks").fetchone()["n"],
                   albums=c.execute("select count(distinct album) n from tracks").fetchone()["n"])


# --------------------------------------------------------------------------- YouTube enrichment (admin)
@bp.get("/api/admin/enrich")
@admin_required
def enrich_status():
    """Progress of the background metadata enrichment job."""
    c = _db()
    return jsonify(
        total=c.execute("select count(*) n from tracks").fetchone()["n"],
        linked=c.execute("select count(*) n from tracks where yt_id is not null").fetchone()["n"],
        fetched=c.execute("select count(*) n from tracks where yt_likes is not null").fetchone()["n"],
        pending=0,
    )


@bp.get("/api/admin/lyrics")
@admin_required
def lyrics_status():
    """Progress of the background lyrics fetch."""
    import lyrics
    return jsonify(lyrics.status())


@bp.post("/api/admin/lyrics")
@admin_required
def lyrics_start():
    """Start fetching missing lyrics."""
    import lyrics
    started = lyrics.start_backfill()
    return jsonify(started=started, **lyrics.status())


@bp.post("/api/admin/enrich")
@admin_required
def enrich_start():
    """Start metadata enrichment for the library."""
    if (request.get_json(silent=True) or {}).get("force"):
        _db().execute("update tracks set yt_checked=null")
        _db().commit()
    return jsonify(queued=0)


# --------------------------------------------------------------------------- playback registry
# The browser owns audio. It publishes a snapshot here so bots, the sticky
# dashboard and other devices can render real state, and it collects commands
# (skip/pause/enqueue) that a chat channel issued.
@bp.post("/api/playback")
@login_required
def playback_push():
    """Client pushes its playback state for the sync/now-playing views."""
    d = request.get_json(silent=True) or {}
    uid = session["uid"]
    queue = d.get("queue") or []
    if not isinstance(queue, list):
        queue = []
    ids = []
    for v in queue[:200]:
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue
    tid = d.get("track_id")
    try:
        tid = int(tid) if tid is not None else None
    except (TypeError, ValueError):
        tid = None
    from database import save_playback, get_active_device, claim_device
    device = str(d.get("device", ""))[:64].strip() or None
    active = get_active_device(_db(), uid)

    # First push after a fresh install claims the room. Without this, a user
    # whose device rows all predate the single-speaker rule would publish into
    # the void and no device would ever be allowed to play.
    if device and not active:
        claim_device(_db(), uid, device)
        active = device

    # If this device is not the active one, pause it and don't take over.
    if device and device != active:
        return jsonify(ok=True, ignored=True, active_device=active or "")
    save_playback(_db(), uid, tid, d.get("position") or 0,
                  d.get("duration") or 0, bool(d.get("playing")), ids, device)
    return jsonify(ok=True, active_device=active or "")


@bp.get("/api/playback")
@login_required
def playback_pull():
    """Client pulls the playback state of the account's active device."""
    uid = session["uid"]
    c = _db()
    from database import get_playback
    pb = get_playback(c, uid)
    if pb:
        row = c.execute("select * from tracks where id=?", (pb["track_id"],)).fetchone() \
            if pb["track_id"] else None
        pb["track"] = track_dict(c, row, liked_ids(c, uid)) if row else None
        if pb.get("device"):
            drow = c.execute(
                "select name from devices where user_id=? and device_hash=?",
                (uid, pb["device"]),
            ).fetchone()
            pb["device_name"] = drow["name"] if drow and drow["name"] else "another device"
        else:
            pb["device_name"] = ""

    device = str(request.args.get("device", ""))[:64]
    rows = c.execute(
        "select id, action, arg, origin from playback_commands "
        "where user_id=? and consumed=0 and (target is null or target='' or target=?)"
        " and (origin is null or origin<>?) order by id limit 20",
        (uid, device, device),
    ).fetchall()
    if rows:
        c.execute(
            "update playback_commands set consumed=1 where id in (%s)"
            % ",".join("?" * len(rows)), [r["id"] for r in rows]
        )
        c.commit()
    cmds = []
    for r in rows:
        try:
            arg = __import__("json").loads(r["arg"] or "{}")
        except ValueError:
            arg = {}
        # Resolve enqueue targets here so the client gets a playable object.
        if r["action"] == "enqueue" and arg.get("track_id"):
            row = c.execute("select * from tracks where id=?", (arg["track_id"],)).fetchone()
            if row:
                arg["track"] = track_dict(c, row, liked_ids(c, uid))
        cmds.append({"id": r["id"], "action": r["action"], "arg": arg})
    return jsonify(state=pb, commands=cmds)


@bp.post("/api/playback/command")
@login_required
def playback_command():
    """Queue a remote-control action. Bots may target any linked user."""
    d = request.get_json(silent=True) or {}
    action = str(d.get("action", ""))
    if action not in ("play", "pause", "toggle", "skip", "next", "prev", "enqueue",
                      "remove", "seek", "play_track"):
        return jsonify(error="bad action"), 400
    target = d.get("user_id")
    if target is None or int(target) == session["uid"]:
        target = session["uid"]
    elif not is_bot_request():
        return jsonify(error="cannot control another user"), 403
    c = _db()
    arg = {"track_id": d.get("track_id"), "index": d.get("index"),
           "url": d.get("url"), "position": d.get("position"),
           "from": str(d.get("origin_name") or "another device")[:64]}
    if action == "play_track" and arg.get("track_id"):
        row = c.execute("select * from tracks where id=?", (int(arg["track_id"]),)).fetchone()
        if row:
            arg["track"] = track_dict(c, row, liked_ids(c, int(target)))
    origin = str(d.get("origin", ""))[:64] or None
    target_device = str(d.get("target", ""))[:64] or None
    c.execute(
        "insert into playback_commands(user_id,action,arg,origin,target,created,consumed)"
        " values(?,?,?,?,?,?,0)",
        (int(target), action, __import__("json").dumps(arg), origin, target_device, time.time()),
    )
    c.commit()
    return jsonify(ok=True, action=action, target=int(target))


@bp.get("/api/queue")
@login_required
def queue_snapshot():
    """Queue ids the current user's client last published."""
    c = _db()
    from database import get_playback
    pb = get_playback(c, session["uid"]) or {}
    ids = pb.get("queue") or []
    if not ids:
        return jsonify(queue=[], current=None)
    marks = ",".join("?" * len(ids))
    rows = {r["id"]: r for r in c.execute(
        "select id,title,artist,album,duration from tracks where id in (%s)" % marks, ids)}
    return jsonify(
        current=dict(rows[pb["track_id"]]) if pb.get("track_id") in rows else None,
        queue=[dict(rows[i]) for i in ids if i in rows],
    )
