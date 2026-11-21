# mcmusic

A self-hosted music room. Your library, your playlists, your rules — streamed
from a server you own, with one speaker at a time and every other signed-in
device acting as a remote.

No feed. No algorithm. Only the records you put here.

## What is in here

| Path | What it is |
| --- | --- |
| `src/` | Flask server: library, playlists, lyrics, requests, devices, playback |
| `ui/` | The web client (Preact + Vite), forked from flufi-music/v3-client. Builds into `web/ui/`; `/` serves it |
| `web/` | The previous PWA — vanilla ES modules, no build step. Still served at `/legacy` |
| `gui/` | Where the new Android client will live; the previous one was removed in full |
| `app/linux/` | Qt 6 desktop client, shared with the macOS and Windows launch scripts |
| `app/3ds/` | Nintendo 3DS homebrew scaffold (pairing and library browsing) |
| `music_activity/` | Presence sinks the server uses for Rotur/Discord/originChats |
| `scripts/` | Publish builds, cut a GitHub Release |
| `docs/` | Roadmap, platform notes, design research |

The clients all talk to the same server API. There is no sync service in the
middle and no account anywhere else: one `data/mcmusic.db` is the truth.

## Running it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # Flask, gunicorn, mutagen, …
cp mcmusic.env.example mcmusic.env               # then edit it
( cd ui && npm ci && npm run build )             # writes web/ui/, what `/` serves
.venv/bin/python -m src.mcmusic                  # or: gunicorn mcmusic:app
```

Without `web/ui/` the server falls back to the legacy shell in `web/`, which
stays reachable at `/legacy`.

Configuration is environment-only. The names that matter:

- `PUBLIC_URL`, `MUSIC_DIR`, `DATA_DIR`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- `ROTUR_APP`, `ROTUR_SECRET`, `INVITE_CODE`
- `DISCORD_CLIENT_ID` (or existing `DISCORD_APPLICATION_ID`), `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`
- `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_ADMIN_TOKEN`, `MCMUSIC_BOT_TOKEN`
- `DISCORD_APP_ID` (optional override for Discord presence; `DISCORD_CLIENT_ID` is used otherwise)

Nothing under `data/` (database, cookies, session key) or `mcmusic.env` is in
this repository, and `.gitignore` keeps it that way.

### Library maintenance

```bash
python tools/fix_music_db.py --fix-albums        # album tag = sidecar album, else song name
python tools/fetch_albums.py --workers 6         # ask YouTube for real albums, resumable
python src/dedupe_library.py --dry-run           # duplicate songs, what would merge
python src/dedupe_library.py                     # merge them, keep both links
```

### Discord account linking

Create an application in the Discord Developer Portal, then add its OAuth2
client ID and client secret to `mcmusic.env` (the ID is also accepted as
`DISCORD_APPLICATION_ID`). Register this exact redirect URI under OAuth2:

```
<PUBLIC_URL>/api/auth/discord/callback
```

`DISCORD_CLIENT_SECRET` is the only required value that cannot be derived from
the bot token. The bot itself also needs **Message Content Intent** enabled
under Bot → Privileged Gateway Intents, otherwise Discord refuses the login.

### Discord presence

Settings → Discord has a **Share as Discord activity** toggle, the counterpart
of the Rotur one. It posts the current track to
`POST /api/auth/discord/activity` (same body as the Rotur route, plus a
`playing: false` clear) and the server publishes it as a Listening presence.

Presence can only be set by a Discord client, so this needs an application id —
`DISCORD_APP_ID`, or the `DISCORD_CLIENT_ID` / `DISCORD_APPLICATION_ID` you
already set for linking (same application) — and the Discord desktop app running
**on the server host**. That is why the route answers `503` with the reason
(“Discord is not running on this server”) instead of pretending to succeed, and
why Settings → Discord states the same thing under the toggle: `GET
/api/auth/discord/status` reports `presence: {configured, available, reason}`.
The activity carries a **Listen along** button when the room link is shared and
a **mcmusic profile** button, so a listener can jump from Discord to the track.
On a shared server the local client has one presence, so the last account to
publish wins.

Both activity toggles (Rotur and Discord) describe the server state in Settings
and re-check it every 10 s while the page is open, so starting or quitting the
Discord client — or a Rotur session expiring — shows up without a reload.
`GET /api/auth/rotur/status` reports the Rotur equivalent as
`activity: {ready, reason}`.

#### Running Discord on the server

This host has no monitor, so the client runs on a virtual X display that also
serves VNC. Two systemd units, enabled at boot:

| Unit | What it does |
| --- | --- |
| `mcmusic-discord-display.service` | `Xvnc :99`, VNC on `127.0.0.1:5901` only |
| `mcmusic-discord.service` | `/usr/local/bin/discord-headless` on `DISPLAY=:99` |

The IPC socket only appears **after** the client is signed in, so the account
has to log in once through that display:

```bash
ssh -L 5901:127.0.0.1:5901 server@<host>     # then point a VNC viewer at localhost:5901
```

Sign in with a password, or scan the QR code the client shows, in the client
itself — do not inject a user token. After that
`/run/user/1000/discord-ipc-0` exists, and presence publishes on the account
signed in there for every listener who enables the toggle. Keep expectations
straight: it is **one** account's profile, not each user's.

Host-specific details worth keeping:

- `/usr/local/bin/discord-headless` runs the newest `~/.config/discord/app-*/Discord`
  directly with `--disable-gpu --disable-dev-shm-usage --enable-low-end-device-mode`.
  The `/usr/bin/discord` updater wrapper stalls forever on its update check here,
  and without low-end mode the web app never finishes loading on this CPU.
- Both `mcmusic-discord.service` and `mcmusic.service` set
  `XDG_RUNTIME_DIR=/run/user/1000` so they agree on where the IPC socket lives;
  `loginctl enable-linger server` keeps that directory alive across reboots.
- The client starts at `Nice=-5` with `MemoryHigh=900M` / `MemoryMax=1.5G`:
  startup needs the CPU to beat the 60 s web-app watchdog, but once loaded it
  idles around 200–800 MB. Raise the caps rather than the priority if the
  client starts getting OOM-killed.
- A client that sits on "Starting…" for minutes with memory flat near 200 MB
  usually has a bad Chromium disk cache: stop the unit, delete `Cache`,
  `Code Cache` and `GPUCache` in `~/.config/discord` (login data is kept), and
  start it again.

## Builds

```bash
# The Android client is being rebuilt from scratch under gui/, so there is no
# APK target here right now. The signing key it will need is kept in keystore/.

# Publish stable names into apps/ (ignored by git)
./scripts/publish_apps.sh

# Create/refresh the GitHub Release with every published file
./scripts/release.sh
```

`https://<your-server>/get` still redirects to the newest published Android
build, and `/api/builds` is the list the website and the email form read.

## Embeds

Any page can show what one of your users is playing with a single custom
element. `/embeds` on your server is a live gallery of every widget with copy
buttons, a theme/accent picker and a starter stylesheet:

```html
<script src="https://<your-server>/static/embed/widgets.js"
        data-mcmusic-base="https://<your-server>" defer></script>

<mcmusic-now user="sandisk"></mcmusic-now>
```

| Tag | Shape |
| --- | --- |
| `mcmusic-now` | Cover, title, artist, live progress, listening state |
| `mcmusic-turntable` | Spinning vinyl that stops when playback pauses |
| `mcmusic-card` | Larger profile-style card, artwork and username first |
| `mcmusic-bar` | One-line horizontal bar |
| `mcmusic-marquee` | Scrolling ticker |
| `mcmusic-badge` | Inline pill for bios and link-in-bio pages |
| `mcmusic-now-playing`, `mcmusic-profile`, `mcmusic-ticker` | Aliases of `now`, `card` and `marquee` |

Attributes: `user` (required, except with `demo`), `theme` (`dusk`, `paper`,
`ink`, `tide`, `copper`, `forest`, `rose` or `auto`), `accent` (any CSS colour),
`compact` (presence), `refresh` (seconds, minimum 5, default 12), `maxlen`
(default `0`), `speed` (seconds per scroll pass, 3–60, default 18) and `demo`
(presence). Titles, artist lines and badge text longer than `maxlen` characters
scroll like the ticker instead of being cut off with an ellipsis; leave it at
`0` to keep them static, and use `speed` to set how long one pass takes. `demo`
renders built-in sample data without polling, so a gallery or a draft page works
before any username is known (a real `user` wins if both are set). Widgets render in a
shadow root, so page CSS only reaches the outside: width, margins,
`--mc-radius`, `--mc-font` and the colour variables.

Colours come from the `theme` and `accent` attributes unless your own CSS
declares them, in which case the page wins — so a site-wide palette is just:

```css
mcmusic-now, mcmusic-card, mcmusic-bar {
  --mc-bg: #101418;    /* card background      */
  --mc-bg2: #0a0d10;   /* gradient end         */
  --mc-fg: #f2f4f7;    /* primary text         */
  --mc-dim: #a9b4bf;   /* secondary text       */
  --mc-line: #2a343d;  /* borders              */
  --mc-accent: #7bd6a0; /* dot, progress, links */
}
```

The same variables also work as `style="--mc-fg: …"` on an individual tag.
Widgets poll `/api/public/now/<username>`; `/api/public/listening` lists
recently active users, and both send `Access-Control-Allow-Origin: *` so an
embed can live on any domain.

## A note on email

Gmail and several other providers reject `.apk` attachments outright — even
inside a zip — and drop the message before it reaches the inbox. The build
email therefore always includes a download button and a direct link, and the
attached copy is named `….apk.bin`. It is the real APK; rename it after
downloading, or just use the link.

## License

Not chosen yet. Treat the code as all rights reserved until a LICENSE file is
added.
