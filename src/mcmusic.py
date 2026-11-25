#!/usr/bin/env python3
"""
mcmusic — tiny self-hosted music server.

Library = folder produced by yt_playlist_to_mp3.py (tags are the metadata).
  pip install flask mutagen yt-dlp gunicorn requests
Run (ONE worker — it owns the download queue, YouTube fetcher and listen-along rooms):
  MUSIC_DIR=/srv/music INVITE_CODE=somesecret ROTUR_APP=app_xxxx \
  ROTUR_SECRET=rsec_xxxx gunicorn -w1 --threads 16 -b 127.0.0.1:8000 mcmusic:app

Env: MUSIC_DIR, DATA_DIR, DL_SCRIPT, DL_ARGS, INVITE_CODE (blank = open signup),
     AUTO_APPROVE, COOKIE_SECURE, YT_ENRICH,
     ROTUR_APP / ROTUR_SECRET / ROTUR_SCOPE / ROTUR_REDIRECT_URI (RoturLink),
     MCMUSIC_BOT_TOKEN, MCMUSIC_BOT_USER (control-channel bots),
     DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, ORIGINCHATS_BASE/TOKEN/CHANNEL.
"""
import hashlib
import json
import math
import os
import secrets
import sys
import threading
import time

from flask import Flask, g, session, request, jsonify, Response, send_file, redirect
from markupsafe import escape

from config import (
    PROJECT_DIR,
    SESSION_COOKIE_NAME, SESSION_COOKIE_SAMESITE, SESSION_COOKIE_HTTPONLY,
    PERMANENT_SESSION_LIFETIME, COOKIE_SECURE, ROTUR_APP, ROTUR_SCOPE,
    DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_ADMIN_TOKEN, HERE,
    INVITE_CODE, SHELL_VERSION, DATA_DIR, PUBLIC_URL,
)
from database import init_db, _db, ensure_schema
from library_scan import scan_library, yt_worker

# Trust the reverse proxy (nginx/Caddy/cloudflared) so request.remote_addr and
# request.scheme reflect the real client instead of 127.0.0.1. Set
# X-Forwarded-For / X-Forwarded-Proto / X-Forwarded-Host at the proxy.
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

def _pick_dir(*candidates):
    """First existing directory from the candidates (else the first one)."""
    for cand in candidates:
        if os.path.isdir(cand):
            return cand
    return candidates[0]


# Frontend assets live in web/ but are still served under the stable /static/
# URL prefix, so the service worker, manifest and boot shell need no rewrites.
# Resolved from both layouts so moving the Python into src/ does not repoint it.
WEB_DIR = _pick_dir(
    os.path.join(HERE, "web"),                   # flat layout
    os.path.join(os.path.dirname(HERE), "web"),  # python moved into src/
)

app = Flask(
    __name__,
    static_folder=WEB_DIR,
    static_url_path="/static",
)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
_kp = os.path.join(DATA_DIR, "secret.key")
if not os.path.exists(_kp):
    with open(_kp, "w") as fh:
        fh.write(secrets.token_hex(32))
    try:
        os.chmod(_kp, 0o600)
    except OSError:
        pass
app.secret_key = open(_kp).read().strip()
app.config.update(
    SESSION_COOKIE_NAME=SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_HTTPONLY=SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SECURE=COOKIE_SECURE,
    PERMANENT_SESSION_LIFETIME=PERMANENT_SESSION_LIFETIME,
    ROTUR_REDIRECT_URI=os.environ.get("ROTUR_REDIRECT_URI", ""),
    SEND_FILE_MAX_AGE_DEFAULT=0,
)

START_TIME = time.time()


# ---------------------------------------------------------------- rate limiting (API)
class RateGuard:
    def __init__(self, limit, window, ban_base, ban_max, ban_window):
        self.limit = max(1, int(limit))
        self.window = max(1.0, float(window))
        self.ban_base = max(1.0, float(ban_base))
        self.ban_max = max(self.ban_base, float(ban_max))
        self.ban_window = max(1.0, float(ban_window))
        self._lock = threading.Lock()
        self._states = {}
        self._last_gc = 0.0

    def hit(self, key):
        now = time.time()
        with self._lock:
            if now - self._last_gc > 300:
                self._last_gc = now
                for k in [k for k, v in self._states.items()
                          if not v["hits"] and v["until"] < now - 60]:
                    self._states.pop(k, None)
            st = self._states.get(key)
            if st is None:
                st = self._states[key] = {"hits": [], "until": 0.0,
                                           "offenses": 0, "last": 0.0}
            if now < st["until"]:
                return st["until"] - now, 0, st["until"] - now, True
            st["hits"] = [t for t in st["hits"] if t > now - self.window]
            st["hits"].append(now)
            used = len(st["hits"])
            if used > self.limit:
                if st["offenses"] and now - st["last"] <= self.ban_window:
                    st["offenses"] += 1
                else:
                    st["offenses"] = 1
                st["last"] = now
                ban = min(self.ban_max, self.ban_base * (2 ** (st["offenses"] - 1)))
                st["until"] = now + ban
                st["hits"] = []
                return ban, 0, ban, True
            reset = (st["hits"][0] + self.window - now) if st["hits"] else self.window
            return 0.0, max(0, self.limit - used), reset, False


from config import (
    API_RATE_LIMIT, API_RATE_WINDOW, API_BAN_BASE, API_BAN_MAX, API_BAN_WINDOW,
    API_AUTH_LIMIT, API_AUTH_WINDOW, CORS_ORIGIN,
)
API_GUARD = RateGuard(API_RATE_LIMIT, API_RATE_WINDOW, API_BAN_BASE, API_BAN_MAX, API_BAN_WINDOW)
AUTH_GUARD = RateGuard(API_AUTH_LIMIT, API_AUTH_WINDOW, 300, 3600, 3600)


def _auth_uid():
    from auth import _auth_uid as _au
    return _au()


@app.before_request
def _api_gate():
    if not request.path.startswith("/api/") or request.method == "OPTIONS":
        return None
    uid = _auth_uid()
    # Stricter for login/register + pairing + download requests
    if request.path in (
        "/api/login", "/api/register", "/api/auth/app/login",
        "/api/auth/reset/request",
    ):
        guard, key = AUTH_GUARD, "auth:" + (request.remote_addr or "?")
    elif request.path in ("/api/devices/code", "/api/devices/claim") or request.path.startswith("/api/download") or request.path == "/api/requests":
        guard, key = AUTH_GUARD, "auth:" + (request.remote_addr or "?")
    else:
        guard = API_GUARD
        key = ("u:%s" % uid) if uid is not None else ("ip:" + (request.remote_addr or "?"))
    wait, remaining, reset, banned = guard.hit(key)
    g.rl_limit, g.rl_remaining, g.rl_reset = guard.limit, remaining, max(1, int(math.ceil(reset)))
    if banned:
        resp = jsonify(error="rate limited", retry_after=round(wait, 1), ban_seconds=round(wait, 1))
        resp.status_code = 429
        resp.headers["Retry-After"] = str(max(1, int(math.ceil(wait))))
        resp.headers["X-RateLimit-Limit"] = str(guard.limit)
        resp.headers["X-RateLimit-Remaining"] = "0"
        return resp
    return None


@app.after_request
def _api_headers(resp):
    if request.path.startswith("/api/") or request.path in ("/manifest.webmanifest", "/sw.js"):
        resp.headers.setdefault("Access-Control-Allow-Origin", CORS_ORIGIN)
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-MCMUSIC-BOT, Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        resp.headers["Access-Control-Expose-Headers"] = (
            "Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset")
        resp.headers["Vary"] = "Origin"
    # Cloudflare and several other edges ignore Cache-Control on binaries and
    # keep serving an old APK for hours. CDN-Cache-Control/Cloudflare-CDN-Cache-Control
    # are the headers those edges actually honour, and builds.py adds a content
    # hash to the URL as a second line of defence.
    if request.path.startswith("/apps/") or request.path == "/api/builds":
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["CDN-Cache-Control"] = "no-store"
        resp.headers["Cloudflare-CDN-Cache-Control"] = "no-store"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    if request.path.startswith("/api/"):
        if getattr(g, "rl_limit", None):
            resp.headers["X-RateLimit-Limit"] = str(g.rl_limit)
            resp.headers["X-RateLimit-Remaining"] = str(g.rl_remaining)
            resp.headers["X-RateLimit-Reset"] = str(g.rl_reset)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
    if request.path.startswith("/static/"):
        resp.headers["Cache-Control"] = "public, max-age=300, must-revalidate"
    return resp


# ---------------------------------------------------------------- docs contract
@app.get("/api")
@app.get("/api/")
def api_root():
    """The API lives under /api; the docs are its index."""
    return api_docs()


@app.get("/api/docs")
def api_docs():
    return jsonify(
        name="mcmusic API", version=3,
        self_hosting={
            "guide": "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md",
            "health": "GET /health (or GET /api/ping for token auth)",
            "version": "GET /api/version",
            "web_client_build": "./scripts/build_ui.sh",
        },
        auth={
            "web": "POST /api/login for the bootstrap account, or GET "
                   "/api/auth/rotur/authorize for RoturLink. A session cookie follows.",
            "rotur": "OAuth 2.0 + PKCE S256 against api.rotur.dev. Tokens never reach the browser. "
                     "API-only clients can link by validator instead: GET /api/auth/rotur/key, "
                     "mint a validator for that key, then POST /api/auth/rotur/link.",
            "bot": "Send X-MCMUSIC-BOT: <MCMUSIC_BOT_TOKEN>. Bots act as the service account.",
            "device": "Signed in? POST /api/devices/code for an 8-character code, "
                      "then POST /api/devices/claim with it. The returned mcd_ "
                      "token goes in Authorization: Bearer <token>.",
        },
        rate_limit={
            "limit": API_RATE_LIMIT, "window_seconds": API_RATE_WINDOW,
            "ban_base_seconds": API_BAN_BASE, "ban_max_seconds": API_BAN_MAX,
            "ban_window_seconds": API_BAN_WINDOW,
        },
        endpoints={
            "auth": ["POST /api/register", "POST /api/login", "POST /api/logout",
                     "GET /api/me", "POST /api/password",
                     "POST /api/auth/email", "POST /api/auth/reset/request",
                     "POST /api/auth/reset/check", "POST /api/auth/reset/confirm",
                     "GET /api/auth/rotur/authorize", "GET /api/auth/rotur/callback",
                     "GET /api/auth/rotur/status", "GET /api/auth/rotur/key",
                     "POST /api/auth/rotur/link", "POST /api/auth/rotur/activity",
                     "POST /api/auth/rotur/unlink", "GET /api/auth/discord/authorize",
                     "GET /api/auth/discord/callback", "GET /api/auth/discord/status",
                     "POST /api/auth/discord/unlink", "POST /api/auth/discord/activity"],
            "library": ["GET /api/tracks", "GET /api/search", "GET /api/albums",
                        "GET /api/album?name=", "GET /api/artists", "GET /api/artist?name=",
                        "GET /api/tracks/<id>/stream", "GET /api/tracks/<id>/cover"],
            "personal": ["GET|POST /api/playlists", "GET|PATCH|DELETE /api/playlists/<id>",
                         "POST|DELETE /api/playlists/<id>/tracks[/<track>]",
                         "POST /api/like/<track>", "GET /api/likes", "POST /api/plays",
                         "GET /api/home", "GET /api/radio/<track>",
                         "GET|PUT /api/settings", "GET|POST /api/playback",
                         "GET /api/queue", "POST /api/playback/command"],
            "channels": ["GET|POST /api/channels", "DELETE /api/channels/<id>",
                         "GET /api/channels/<id>/state", "POST /api/channels/<id>/dashboard",
                         "GET /api/bot/context", "POST /api/bot/rotur-ticket"],
            "public": ["GET /u/<username> (no auth)",
                       "GET /u/<username>/cover.png (no auth)",
                       "GET /u/<username>/<song>.png (no auth)"],
            "requests": ["POST /api/requests", "GET /api/requests",
                         "POST /api/requests/<id>/<action>"],
            "rooms": ["POST /api/rooms", "GET|DELETE /api/rooms/<code>",
                      "POST /api/rooms/<code>/state"],
            "devices": ["GET /api/devices", "POST /api/devices/heartbeat",
                        "POST /api/devices/<id>/activate", "GET /api/devices/sync",
                        "POST /api/devices/code", "POST /api/devices/claim",
                        "GET /api/devices/tokens",
                        "POST /api/devices/tokens/<id>/revoke", "GET /api/ping"],
            "apps": ["GET /apps/android/mainbuild.apk"],
            "admin": ["GET|POST /api/admin/invite-codes",
                      "DELETE /api/admin/invite-codes/<id>", "GET /api/admin/stats",
                      "GET /api/admin/users", "GET /api/admin/requests",
                      "POST /api/admin/scan", "GET|POST /api/admin/enrich",
                      "GET /api/admin/algo"],
        })


# ---------------------------------------------------------------- settings + version
DEFAULT_SETTINGS = {
    "theme": "violet", "accent": "", "density": "comfy", "material": "plane",
    "covers": True, "autoplay": True, "hide_explicit": False, "private": False,
    "yt_stats": True, "remember_volume": True, "volume": 0.8, "prefetch": True,
    "offline_audio": True, "rotur_activity": False, "discord_activity": False,
    "show_room_url": False,
    "real_glass": "auto",
}


@app.get("/api/settings")
def settings_get():
    from auth import _auth_uid
    uid = _auth_uid()
    if uid is None:
        return jsonify(error="login required"), 401
    r = _db().execute("select data from settings where user_id=?", (uid,)).fetchone()
    stored = {}
    if r and r["data"]:
        try:
            stored = json.loads(r["data"])
        except ValueError:
            stored = {}
    out = dict(DEFAULT_SETTINGS)
    if isinstance(stored, dict):
        out.update({k: v for k, v in stored.items() if k in DEFAULT_SETTINGS})
    from routes.system_routes import room_url
    out["room_url"] = room_url(uid)
    return jsonify(out)


@app.put("/api/settings")
def settings_put():
    from auth import _auth_uid
    uid = _auth_uid()
    if uid is None:
        return jsonify(error="login required"), 401
    d = request.get_json(silent=True) or {}
    if not isinstance(d, dict):
        return jsonify(error="object required"), 400
    clean = {k: v for k, v in d.items() if k in DEFAULT_SETTINGS}
    c = _db()
    c.execute(
        """insert into settings(user_id,data) values(?,?)
           on conflict(user_id) do update set data=excluded.data""",
        (uid, json.dumps(clean)),
    )
    c.commit()
    return jsonify(ok=True)


def _build_id():
    """Stable fingerprint of the shipped frontend, used for update checks."""
    h = hashlib.sha256(SHELL_VERSION.encode())
    root = WEB_DIR
    for base, _dirs, files in os.walk(root):
        for f in sorted(files):
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            h.update(f"{os.path.relpath(p, root)}:{int(st.st_mtime)}:{st.st_size}".encode())
    return h.hexdigest()[:16]


BUILD = _build_id()


@app.get("/api/version")
def version():
    resp = jsonify(build=BUILD, shell=SHELL_VERSION, started=START_TIME)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------- Discord integration
@app.post("/api/discord/queue")
def discord_queue():
    """Legacy shim: the bot now uses /api/playback/command."""
    from auth import is_bot_request, _auth_uid
    if not is_bot_request() and _auth_uid() is None:
        return jsonify(error="login required"), 401
    d = request.get_json(silent=True) or {}
    url = str(d.get("url", "")).strip()
    if not url:
        return jsonify(error="url required"), 400
    uid = _auth_uid()
    c = _db()
    cur = c.execute(
        "insert into requests(url,user_id,status,created) values(?,?,'approved',?)",
        (url, uid, time.time()),
    )
    c.commit()
    from routes.system_routes import dl_q
    dl_q.put(cur.lastrowid)
    return jsonify(ok=True, request_id=cur.lastrowid)


# ---------------------------------------------------------------- PWA static routes
STATIC_DIR = WEB_DIR


@app.get("/manifest.webmanifest")
def pwa_manifest():
    p = os.path.join(STATIC_DIR, "manifest.webmanifest")
    if not os.path.exists(p):
        return jsonify(error="not found"), 404
    resp = send_file(p, mimetype="application/manifest+json")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.get("/sw.js")
def pwa_sw():
    p = os.path.join(STATIC_DIR, "sw.js")
    if not os.path.exists(p):
        return jsonify(error="not found"), 404
    resp = send_file(p, mimetype="application/javascript")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp


@app.get("/icon.svg")
def pwa_icon_svg():
    return send_file(os.path.join(STATIC_DIR, "icon.svg"), mimetype="image/svg+xml")


@app.get("/icon-maskable-512.png")
def pwa_icon_maskable():
    return send_file(os.path.join(STATIC_DIR, "icon-maskable-512.png"), mimetype="image/png")


@app.get("/apple-touch-icon.png")
def pwa_apple_touch():
    """Apple touch icon for the installed PWA."""
    return send_file(os.path.join(STATIC_DIR, "apple-touch-icon.png"), mimetype="image/png")


@app.get("/icon-<int:size>.png")
def pwa_icon_png(size):
    """Generated PWA icon at the requested size."""
    p = os.path.join(STATIC_DIR, f"icon-{size}.png")
    if not os.path.exists(p):
        return jsonify(error="not found"), 404
    return send_file(p, mimetype="image/png")


# ---------------------------------------------------------------- app builds
# Published binaries live outside the repo's web root: /apps/android/mainbuild.apk
# etc. A rebuild copies over the same filename, so the link never changes.
APP_DIST = os.path.join(PROJECT_DIR, "apps")


@app.get("/apps/<path:name>")
def app_build(name):
    """Serve a published APK/desktop artifact."""
    base = os.path.realpath(APP_DIST)
    path = os.path.realpath(os.path.join(base, name))
    if path.startswith(base + os.sep) and not os.path.isfile(path):
        # A server that never built clients locally still serves the same URL:
        # pull the exact artifact from the public GitHub Release first, then
        # redirect to GitHub if this host cannot write or reach the network.
        import github_builds
        asset = github_builds.match_path(name)
        if asset and github_builds.download(asset):
            path = os.path.realpath(os.path.join(base, name))
        elif asset:
            resp = redirect(asset["url"], code=302)
            resp.headers["Cache-Control"] = "no-store"
            return resp
    if not path.startswith(base + os.sep) or not os.path.isfile(path):
        return jsonify(error="not found"), 404
    mime = "application/vnd.android.package-archive" if path.endswith(".apk") else None
    resp = send_file(path, mimetype=mime or "application/octet-stream",
                     as_attachment=True, download_name=os.path.basename(path))
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.get("/downloads")
def downloads_page():
    """Public build list — no account required, works from any browser."""
    import builds
    rows = []
    for b in builds.all_builds():
        if not b.get("available"):
            continue
        badge = "GitHub" if b.get("source") == "github" else "server"
        rows.append(
            "<li><div><strong>{label}</strong><small>{version} · {size} · {built} · {source}</small>"
            "<p>{hint}</p></div><a class='download' href='{url}' download>Get it</a></li>".format(
                label=escape(b.get("label") or b["kind"]),
                version=escape(b.get("version") or "latest"),
                size=f"{b.get('bytes', 0) / 1048576:.1f} MB",
                built=escape(b.get("built") or ""),
                source=badge,
                hint=escape(b.get("hint") or b.get("note") or ""),
                url=escape(b["url"]),
            )
        )
    listing = "".join(rows) or "<li><div><strong>No builds yet</strong><p>Publish a release, then refresh this page.</p></div></li>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>mcmusic downloads</title>
<style>
:root{{color-scheme:dark;--ink:#171721;--ink2:#222130;--violet:#9F7EFF;--fg:#FFFFFF;--dim:#AAAAB7;--line:#35344B}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--ink);color:var(--fg);font:15px/1.5 system-ui,sans-serif;min-height:100vh}}
main{{max-width:760px;margin:auto;padding:40px 18px 64px}}h1{{font-size:34px;margin:0 0 6px}}p{{color:var(--dim)}}
a{{color:var(--violet)}}ul{{list-style:none;padding:0;display:grid;gap:12px;margin-top:28px}}
li{{display:flex;gap:16px;align-items:center;justify-content:space-between;background:#ffffff0d;border:1px solid var(--line);border-radius:10px;padding:16px}}
small{{display:block;color:var(--dim);font-size:12px}}li p{{margin:4px 0 0;font-size:13px}}
.download{{flex:none;text-decoration:none;background:var(--violet);color:#08060D;font-weight:700;border-radius:999px;padding:10px 18px}}
footer{{margin-top:30px;font-size:13px;color:var(--dim)}}
</style></head><body><main>
<h1>mcmusic downloads</h1>
<p>Official clients for your phone, tablet and computer. No sign-in needed.</p>
<ul>{listing}</ul>
<p><a href="/get">/get</a> always opens the newest signed Android APK.</p>
<footer>Builds are pulled from the public <a href="https://github.com/mc20000-01/mcmusic/releases/tag/latest">GitHub Release</a> when this server has no local build. See the <a href="https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md">self-hosting guide</a>.</footer>
</main></body></html>"""


@app.get("/get")
def get_app():
    """One short link that always hands over the newest Android build.

    People read this off a screen or type it on a phone, so it cannot be a long
    versioned path. `/get` resolves the same registry the settings page uses, so
    it never points at yesterday's file.
    """
    import builds
    spec = builds.describe("android")
    if not spec or not spec.get("available"):
        return jsonify(error="no Android build is published yet"), 404
    resp = redirect(PUBLIC_URL.rstrip("/") + spec["url"], code=302)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["CDN-Cache-Control"] = "no-store"
    resp.headers["Cloudflare-CDN-Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


# ---------------------------------------------------------------- index (web client)
UI_DIR = os.path.join(WEB_DIR, "ui")


def _ui_response():
    """The v3 client (ui/ -> web/ui/): one bundle for every app route."""
    path = os.path.join(UI_DIR, "index.html")
    if not os.path.exists(path):
        from flufi_pages import flufi_page
        body = (
            '<section class="container box">'
            '<h1 class="header">mcmusic</h1>'
            '<p class="text">The web client has not been built on this server.</p>'
            '<pre>./scripts/build_ui.sh</pre>'
            '<p class="text">Full setup and upgrade steps are in the '
            '<a href="https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md">'
            'self-hosting guide</a>.</p>'
            '</section>'
        )
        return flufi_page("mcmusic", body, status=503)
    with open(path, encoding="utf-8") as fh:
        body = fh.read()
    return Response(body, mimetype="text/html",
                    headers={"Cache-Control": "no-cache, must-revalidate"})


@app.get("/")
def index():
    """Serve the v3 client's index.html."""
    return _ui_response()


@app.get("/auth")
@app.get("/upload")
@app.get("/artists")
@app.get("/artist/<path:rest>")
@app.get("/set/<path:rest>")
@app.get("/playlists")
@app.get("/playlist/<path:rest>")
@app.get("/search")
@app.get("/likes")
@app.get("/downloads")
@app.get("/listeners")
@app.get("/not-allowed")
@app.get("/settings")
@app.get("/devices")
@app.get("/admin")
def ui_route(rest=None):
    """Client-side routes: refresh on a deep link must return the app."""
    return _ui_response()


@app.get("/reset")
@app.get("/reset/")
@app.get("/forgot")
def reset_page():
    """Deep link from a reset email; the client reads ?token= off the URL.

    The aliases exist so a mail client appending a slash, or someone typing
    /forgot, still lands on the app instead of a 404.
    """
    return _ui_response()


# ---------------------------------------------------------------- boot
def boot():
    """Application factory: config, routes, background jobs."""
    with app.app_context():
        c = _db()
        ensure_schema(c)
        from config import SCAN_ON_START
        if SCAN_ON_START:
            scan_library(c)
        c.execute("update requests set status='approved' where status='running'")
        c.commit()
        from routes.system_routes import dl_q
        for r in c.execute("select id from requests where status='approved' order by id"):
            dl_q.put(r["id"])
        c.close()

    def _worker_with_ctx():
        with app.app_context():
            from routes.system_routes import worker as _worker
            _worker()

    def _yt_worker_with_ctx():
        with app.app_context():
            yt_worker()

    threading.Thread(target=_worker_with_ctx, daemon=True).start()
    threading.Thread(target=_yt_worker_with_ctx, daemon=True).start()

    def _stall_watchdog_with_ctx():
        with app.app_context():
            from routes.system_routes import stall_watchdog
            stall_watchdog()

    threading.Thread(target=_stall_watchdog_with_ctx, daemon=True).start()

    def _build_sync_with_ctx():
        with app.app_context():
            import github_builds
            github_builds.start_sync()

    threading.Thread(target=_build_sync_with_ctx, daemon=True).start()

    if DISCORD_BOT_TOKEN:
        import subprocess as _sp
        env = os.environ.copy()
        env["MCMUSIC_BASE"] = os.environ.get("MCMUSIC_BASE", "http://127.0.0.1:8000")
        if DISCORD_ADMIN_TOKEN:
            env["DISCORD_ADMIN_TOKEN"] = DISCORD_ADMIN_TOKEN
        if DISCORD_GUILD_ID:
            env["DISCORD_GUILD_ID"] = DISCORD_GUILD_ID
        bot_path = os.path.join(HERE, "discord_bot.py")
        logp = os.path.join(DATA_DIR, "discord_bot.log")
        if os.path.exists(bot_path) and not os.environ.get("MCMUSIC_NO_BOT"):
            print(f"[discord] starting bot from {bot_path}", flush=True)
            _sp.Popen([sys.executable, bot_path], env=env,
                      stdout=open(logp, "ab"), stderr=open(logp, "ab"))


from routes import auth_bp, library_bp, personal_bp, system_bp, channel_bp, video_bp

app.register_blueprint(auth_bp)
app.register_blueprint(library_bp)
app.register_blueprint(personal_bp)
app.register_blueprint(system_bp)
app.register_blueprint(channel_bp)
app.register_blueprint(video_bp)

init_db(app)
boot()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
