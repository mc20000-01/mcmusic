"""mcmusic configuration — all environment-driven, with sensible defaults."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Defaults point at the project root, not src/, so CLI tools (dedupe, scan)
# read the same database the service does even without the service env file.
PROJECT_DIR = os.path.dirname(HERE)
MUSIC_DIR = os.path.abspath(os.environ.get("MUSIC_DIR", os.path.join(PROJECT_DIR, "music")))
DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR", os.path.join(PROJECT_DIR, "data")))
DL_SCRIPT = os.environ.get("DL_SCRIPT", os.path.join(HERE, "yt_playlist_to_mp3.py"))
DL_ARGS = os.environ.get("DL_ARGS", "--turbo")
STAGING_DIR = os.environ.get("STAGING_DIR", os.path.join(MUSIC_DIR, ".staging"))

INVITE_CODE = os.environ.get("INVITE_CODE", "")
AUTO_APPROVE = os.environ.get("AUTO_APPROVE", "1") == "1"
YT_ENRICH = os.environ.get("YT_ENRICH", "1") == "1"
# Fold duplicates after every library scan, not only at the end of a download.
DEDUPE_AFTER_SCAN = os.environ.get("DEDUPE_AFTER_SCAN", "1") == "1"
# 0 keeps a deliberately emptied library empty: start-up will not re-import
# files that are still on disk (downloads still trigger their own scan).
SCAN_ON_START = os.environ.get("SCAN_ON_START", "1").lower() not in ("0", "false", "no")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"

# --------------------------------------------------------------------- RoturLink
# Sign in with Rotur is OAuth 2.0 + PKCE (S256) at api.rotur.dev.
# Scopes are "profile" (and optionally "email"); there is no openid scope.
# Status/activity writes need the account:profile permission, so ask for it up
# front; accounts linked before this change must re-run the sign-in.
ROTUR_APP = os.environ.get("ROTUR_APP", "")
ROTUR_SECRET = os.environ.get("ROTUR_SECRET", "")  # server-side only
ROTUR_BASE_URL = os.environ.get("ROTUR_BASE_URL", "https://api.rotur.dev").rstrip("/")
ROTUR_SCOPE = os.environ.get("ROTUR_SCOPE", "profile account:profile email")
ROTUR_AUTHORIZE_PATH = "/oauth/authorize"
ROTUR_TOKEN_PATH = "/oauth/token"
ROTUR_USERINFO_PATH = "/oauth/userinfo"
ROTUR_CALLBACK_PATH = "/api/auth/rotur/callback"
ROTUR_STATE_TTL = 600

# ------------------------------------------------------------- control channels
# Shared bot credential. Bots never hold user credentials.
BOT_TOKEN = os.environ.get("MCMUSIC_BOT_TOKEN", "") or os.environ.get("DISCORD_ADMIN_TOKEN", "")
BOT_USER = os.environ.get("MCMUSIC_BOT_USER", "")

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
DISCORD_ADMIN_TOKEN = os.environ.get("DISCORD_ADMIN_TOKEN", "")

# Discord account linking (OAuth2). Register <public-url>/api/auth/discord/callback
# in the Discord developer portal. The secret stays on the server.
# The bot deployment already has DISCORD_APPLICATION_ID; accept it as the
# OAuth client id too, so only the client secret needs to be added.
DISCORD_CLIENT_ID = (
    os.environ.get("DISCORD_CLIENT_ID", "")
    or os.environ.get("DISCORD_APPLICATION_ID", "")
    or os.environ.get("DISCORD_APP_ID", "")
)
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
DISCORD_SCOPE = os.environ.get("DISCORD_SCOPE", "identify")

# OriginChats: any REST chat bridge exposing the documented message contract.
ORIGINCHATS_BASE = os.environ.get("ORIGINCHATS_BASE", "").rstrip("/")
ORIGINCHATS_TOKEN = os.environ.get("ORIGINCHATS_TOKEN", "")
ORIGINCHATS_CHANNEL = os.environ.get("ORIGINCHATS_CHANNEL", "")

DASHBOARD_INTERVAL = float(os.environ.get("DASHBOARD_INTERVAL", "4"))

# ------------------------------------------------------------------ rate limiting
API_RATE_LIMIT = int(os.environ.get("API_RATE_LIMIT", "1200"))
API_RATE_WINDOW = float(os.environ.get("API_RATE_WINDOW", "60"))
API_BAN_BASE = float(os.environ.get("API_BAN_BASE", "10"))
API_BAN_MAX = float(os.environ.get("API_BAN_MAX", "600"))
API_BAN_WINDOW = float(os.environ.get("API_BAN_WINDOW", "1800"))
API_AUTH_LIMIT = int(os.environ.get("API_AUTH_LIMIT", "40"))
API_AUTH_WINDOW = float(os.environ.get("API_AUTH_WINDOW", "300"))
# No cross-origin access unless an operator opts in. Leave empty for the
# same-origin web app and native clients (OkHttp/URLSession/Qt do not enforce
# CORS); set to one trusted origin, e.g. https://music.example.com, when a
# separate browser origin really needs the API. An empty value generates no
# usable Allow-Origin grant, so browsers reject cross-origin reads.
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "").strip()

# ----------------------------------------------------------------------- paths
DB_PATH = os.path.join(DATA_DIR, "mcmusic.db")
LOG_DIR = os.path.join(DATA_DIR, "logs")

# ----------------------------------------------------------------------- audio
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".opus", ".flac", ".wav", ".webm", ".ogg"}
YT_HOSTS = {
    "youtube.com", "www.youtube.com", "m.youtube.com",
    "music.youtube.com", "youtu.be",
}

os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --------------------------------------------------------------------- session
SESSION_COOKIE_NAME = "mcmusic_session"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 90  # 90 days

# ------------------------------------------------------------------- mail / resets
# Password reset links and password-change notices go out over plain SMTP, so a
# self-hosted server needs no vendor account. With SMTP_HOST empty the reset
# endpoint still answers normally (no account enumeration) and simply does not
# send anything.
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "") or SMTP_USER
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "1") == "1"
# Reset links are single use and short lived.
RESET_TTL = int(os.environ.get("RESET_TTL", "3600"))
# Absolute base for links in mail; falls back to the request's own origin.
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

# ---------------------------------------------------------------------- assets
# Bump when the offline cache contract changes (audio/art caches are separate
# from the shell cache so an update never discards downloaded media).
SHELL_VERSION = os.environ.get("SHELL_VERSION", "11")
MEDIA_CACHE = "mcmusic-media-v1"
