# A mcmusic client for the Nintendo 2DS / 3DS — feasibility notes

Short version: it is buildable as a **homebrew .3dsx / .cia**, but it is a
different kind of project from the Android app. The 3DS has no browser engine,
no WebView, no `fetch`, and no modern TLS from JavaScript. Everything is C on
bare-ish hardware with a 268 MHz ARM11 (Old 3DS) or 804 MHz (New 3DS) and
128 MB / 256 MB of RAM.

## What the platform gives us

| Need | 3DS facility | Reality check |
| --- | --- | --- |
| Build | devkitARM + libctru, `citro2d`/`citro3d` for drawing | Standard homebrew toolchain, `smdh` + banner for a `.cia` |
| UI | `citro2d` sprites/text, or `citro3d` for the top screen | No layouts or CSS; every screen is manually drawn at 400×240 (top) / 320×240 (bottom) |
| Audio | `ndsp` with linear PCM, ADPCM, and (on 3DS) some AAC/M4A | Streaming MP3 is not a safe assumption; decoding happens on the ARM11 |
| Networking | `httpc` with TLS 1.2 | Works against HTTPS hosts with enough RAM; long-lived connections are fragile |
| Storage | SD card via `fs` | Good for caching cover art and pre-downloaded tracks |
| Input | Buttons, circle pad, touch | A "now playing" screen with a touch scrubber is very doable |

## The parts that are genuinely hard

1. **Authentication.** The web app is session-cookie based, and Android reuses
   the same cookies. A 3DS client should not try to keep a browser cookie jar.
   The clean route is a short-lived device token minted by the server (QR code
   or 8-character code entered on the console, similar to the existing Rotur
   ticket flow). That is new server work, not just a new client.
2. **Streaming audio.** The server's `/api/tracks/<id>/stream` is an HTTP range
   endpoint. `httpc` can fetch ranges, but buffering, seeking and pause all need
   a small ring buffer plus an `ndsp` wave buffer queue. Pre-downloading to SD
   (the Android offline path) is much easier and should be the first milestone.
3. **TLS and certificates.** `httpc` needs a CA bundle baked into the app.
   Expect to pin or bundle the current roots and revisit when they rotate.
4. **Text.** No system font with the same coverage; bundle a small bitmap font
   (or use the system font via `fontEnsureMapped`) and accept a reduced
   character set.
5. **Memory.** Cover art has to be decoded at 48×48 or 64×64, not full size.
   A 1000×1000 PNG will simply fail to allocate.

## Suggested milestones

1. **Read-only client (proof of life).** Log in with a device code, list
   playlists/albums, render titles on the top screen, stream one track to
   `ndsp`. This validates HTTP + TLS + audio in one go.
2. **Library + queue.** Browse, search with the on-screen keyboard, queue
   tracks, show cover art from a small SD cache.
3. **Playback reporting.** Send `/api/plays` reports and heartbeat so the
   device shows up in the devices list and can be remote-controlled by the web
   or Android clients (the command protocol added for cross-device sync already
   fits this: the 3DS is just another `device_hash`).
4. **Offline mode.** Download to SD, play without the network, sync plays later.
5. **Polish.** Bottom-screen transport, sleep-mode pause, a proper `.cia`
   banner, and a 2DS-safe colour pass (the 2DS screen is dimmer).

## Effort estimate

A usable read-only + streaming client is roughly a few weekends of C work for
someone comfortable with libctru. Full parity with the web app (rooms, admin,
Rotur linking) is not worth it; the 3DS should be a **player**, not a client for
every feature.

## The server half is done

- `POST /api/devices/code` → 8-character single-use code, five-minute expiry
  (Settings → Devices → **Get code** in the web app).
- `POST /api/devices/claim` with that code → long-lived `mcd_…` bearer token.
  Only its SHA-256 hash is stored; the server keeps a display prefix.
- `Authorization: Bearer <token>` is accepted beside the session cookie, so the
  same routes work for the console. `GET /api/devices/tokens` and
  `POST /api/devices/tokens/<id>/revoke` manage the list.
- `GET /api/ping` returns service, API version and the current user for a fast
  startup check.

Covered by `tests/test_device_auth.py` against a real throwaway server.

## The client scaffold

`app/3ds/` is a devkitARM + libctru + citro2d project. The first milestone
pairs, lists up to 100 tracks, and downloads the selected track to
`sdmc:/3ds/mcmusic/cache/`. It does **not** decode audio yet: libctru ships
ADPCM but not MP3, and the stream endpoint currently serves the original file.
That decoder (or a server-side PCM/ADPCM transcode endpoint) is the next real
block of work, not a UI detail.

## Status (2026-11-09)

Server auth: shipped. Homebrew scaffold: builds with devkitARM, but has not been
compiled on this Linux host because the toolchain is not installed here. Audio
playback: not started. The 2DS/3DS remains a player in scope, not a full client
for rooms, admin or Rotur linking.
