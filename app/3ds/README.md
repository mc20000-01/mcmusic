# mcmusic for Nintendo 2DS / 3DS

A homebrew player for old 3DS-family hardware: **one short code, no password,
no browser**. It pairs with the same account as the web and Android apps and
keeps a long-lived `mcd_…` token on the SD card.

New to mcmusic? The [self-hosting guide](../../docs/selfhost.md) covers server
setup and pairing this handheld client.

```
app/3ds/
  Makefile         # devkitARM + libctru + citro2d
  source/main.c    # pairing, library shelf, SD download
```

## What this milestone does

- `POST /api/ping` on boot to check the saved token.
- Pairs with `POST /api/devices/code` → `POST /api/devices/claim`.
- Saves `server=` and `token=` in `sdmc:/3ds/mcmusic/config.txt`.
- Lists up to 100 tracks from `GET /api/tracks` on the top screen.
- Downloads the selected track to `sdmc:/3ds/mcmusic/cache/<id>.bin`.

It deliberately **does not decode audio yet**. libctru ships ADPCM but not MP3,
and the server currently serves the original file. The next milestone is either
a small fixed-point MP3 decoder or a server-side transcode endpoint that offers
PCM/ADPCM for handhelds. Do not claim playback until one of those lands.

## Build

Install [devkitPro](https://devkitpro.org/wiki/Getting_Started) with the `3ds-dev`
group, then:

```bash
export DEVKITPRO=/opt/devkitpro
export DEVKITARM=$DEVKITPRO/devkitARM
cd app/3ds
make
```

Output: `mcmusic.3dsx`. Copy it to `sdmc:/3ds/mcmusic.3dsx` and launch it from
the Homebrew Launcher. A `.cia` needs an icon, banner and `makerom`; those are
packaging polish, not a blocker for the first run.

## First run

1. On the web app, open **Settings → Devices → Pair a device** and leave the
   8-character code on screen.
2. Start the homebrew build. On a fresh SD card it asks for the server address
   (`192.168.1.20:8000` is fine; `http://` is added for you) and then the code.
3. It stores the token and shows the shelf. Press `Y` at any time to pair again,
   `B` to refresh, `A` to save the highlighted track to SD.

## Storage layout

```
sdmc:/3ds/mcmusic/
  config.txt     # server + token — treat the SD card as a credential
  cache/<id>.bin # downloaded originals
```

Revoke a lost console from **Settings → Devices** (or
`POST /api/devices/tokens/<id>/revoke`). The token is hashed on the server, so
the row you see there is only a prefix.

## HTTP and TLS

The first milestone targets the LAN over plain HTTP, which is common for
homebrew and keeps the build free of a CA bundle. For an internet-facing server,
bundle a CA store and keep `SSLCOPT_ENTROPY`; do not ship a build that silently
skips certificate checks. The server already accepts
`Authorization: Bearer <token>` on every route the client uses.

## Next milestones

1. Audio: fixed-point decoder or server transcode, ring buffer into `ndsp`.
2. Search with the on-screen keyboard, albums/artists, queue.
3. Heartbeat and `/api/plays` reporting so the console appears in the devices
   list and can be remote-controlled from web/Android.
4. Offline sync of play counts.
5. `.cia` icon/banner, sleep-mode pause, dimmer 2DS colour pass.
