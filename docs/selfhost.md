# Self-hosting mcmusic

mcmusic is designed to run on one machine you control. The Flask server owns
the database, music files and sessions; the web, Android and desktop clients
are only frontends. There is no account or sync service in the middle.

This guide is the short path from a fresh machine to a working server. The
root `README.md` has extra detail on Rotur/Discord presence, embeds and library
maintenance.

## 1. What you need

- Linux server with Python 3.11+ and Node 20.19+ / 22.12+ (for Vite 7).
- A music directory the server user can read.
- A writable data directory for SQLite, sessions and caches.
- A public HTTPS address (strongly recommended — Android 14 blocks cleartext
  traffic by default).
- Optional: JDK 17 + Android SDK if you want to build the signed APK locally.
  CI already does this for you.

## 2. Install

```bash
git clone https://github.com/mc20000-01/mcmusic.git
cd mcmusic

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp mcmusic.env.example mcmusic.env
$EDITOR mcmusic.env
```

Set at least these values in `mcmusic.env`:

```dotenv
PUBLIC_URL=https://music.example.com
MUSIC_DIR=/srv/mcmusic/music
DATA_DIR=/srv/mcmusic/data
INVITE_CODE=change-me
```

- `PUBLIC_URL` is used for reset links, build links and the Android redirect.
  It must match the URL users actually visit.
- `MUSIC_DIR` is read-only library storage.
- `DATA_DIR` holds `mcmusic.db`; back it up.
- `INVITE_CODE` creates the first account. Change it before exposing the site.

Build the web client (this writes `web/ui/`, which `/` serves):

```bash
./scripts/build_ui.sh
# or: ( cd ui && npm ci && npm run build )
```

Run it directly for a smoke test:

```bash
PYTHONPATH=.:src .venv/bin/gunicorn -w 1 --threads 8 -b 0.0.0.0:8000 \
  --timeout 600 mcmusic:app
```

Visit `https://<your-host>/auth` and create the first account with
`INVITE_CODE`. The first account is an admin.

## 3. Run as a service

An example unit is in `deploy/mcmusic.service`. Adjust the paths, user and
Python location, then install it:

```bash
sudo cp deploy/mcmusic.service /etc/systemd/system/mcmusic.service
sudo systemctl daemon-reload
sudo systemctl enable --now mcmusic.service
sudo systemctl status mcmusic.service
```

The unit does not build the UI. After every upgrade run:

```bash
git pull
( cd ui && npm ci && npm run build )
sudo systemctl restart mcmusic.service
```

## 4. Put HTTPS in front

mcmusic listens on plain HTTP locally. Terminate TLS at Caddy or nginx.

Caddy example:

```caddyfile
music.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

nginx example:

```nginx
server {
    listen 443 ssl http2;
    server_name music.example.com;
    ssl_certificate     /etc/letsencrypt/live/music.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/music.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        client_max_body_size 512M;
    }
}
```

Keep port 8000 firewalled from the public internet.

## 5. Connect the clients

### Web

Open `PUBLIC_URL`. The web client uses an HttpOnly cookie session and needs no
per-device setup.

### Android

1. Open the app and, if needed, set **Server URL** on the sign-in screen to
   `https://music.example.com`.
2. Sign in with your email/username and password, or use Continue with Rotur.
3. In-app updates come from `/api/builds`; they install the same signed APK as
   the website's `/get` download.

To build locally instead of using CI:

```bash
export JAVA_HOME="$PWD/.toolchain/jdk"
export ANDROID_HOME="$PWD/.toolchain/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
( cd gui/android && ./gradlew :app:assembleRelease --no-daemon )
./scripts/publish_apps.sh
```

Never replace `keystore/mcmusic.p12` — it is what makes new APKs update the
existing app instead of conflicting with it.

### Desktop

```bash
.venv/bin/pip install -r app/linux/requirements.txt
./app/linux/mcmusic-desktop
```

Set the server URL in desktop Settings. The Qt client also exposes MPRIS and
media keys on Linux. macOS and Windows launchers live in `app/macos/` and
`app/windows/`.

## 6. Optional integrations

All are optional and disabled when blank:

- **SMTP** (`SMTP_*`) — password resets and build emails. Reset links use
  `PUBLIC_URL`, so set it correctly before enabling mail.
- **Rotur** (`ROTUR_APP`, `ROTUR_SECRET`, `ROTUR_REDIRECT_URI`) — Rotur sign-in
  and now-playing activity. The redirect URI must be
  `<PUBLIC_URL>/api/auth/rotur/callback`.
- **Discord** (`DISCORD_*`) — account linking, bot commands and Rich Presence.
  The OAuth redirect URI must be
  `<PUBLIC_URL>/api/auth/discord/callback`. Presence needs the Discord desktop
  client running on the server host; see the README for the headless setup.

## 7. Backups and recovery

Back up together:

```text
data/mcmusic.db
data/next_song_mdl.json
mcmusic.env
MUSIC_DIR
keystore/mcmusic.p12   # only if you build/sign APKs locally
```

`mcmusic.env` contains secrets and signing/provider credentials; keep it out of
git. `old/` is a local archive and is gitignored.

## 8. Troubleshooting

- `/` shows a 503 asking to build the UI — run `./scripts/build_ui.sh`.
- Android cannot sign in — check `PUBLIC_URL`, HTTPS, and that `/api/me` works
  from the phone's network. The earlier “login not sticking” symptom was Wi-Fi,
  not a server fault.
- Reset emails point to the wrong host — fix `PUBLIC_URL` and restart.
- In-app update says no update — `/api/builds` reads `apps/android/`; run
  `./scripts/publish_apps.sh` after placing a new signed APK there.

## 9. Where to find more

- `README.md` — full feature notes, embeds and presence setup.
- `requirements.md` — current implementation and parity task list.
- `docs/algo-learning.md` — learning-only next-song model notes.
- `docs/` — platform/design research.
- `/api/docs` on your server — API index.
