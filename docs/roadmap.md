# Roadmap — every client, ordered by what is actually doable next

This is the running list of the things that have been asked for, sorted by how
much work stands between the idea and something you can hold. Status is checked
against the repo, not against intentions.

## Now (done in this pass)

| Thing | Where | Status |
| --- | --- | --- |
| One brand: the `mc` mark on a palette field | `web/`, Android launcher, splash | ✅ Violet family `#9f7eff` on `#171721` by default |
| Friendlier web sign-in | `web/js/app.js` (`showLogin`) | ✅ two-column welcome stage, feature list, vinyl, mode-aware copy |
| Warmer web home | `web/js/views.js` (`renderHome`) | ✅ greeting + shelf counts + “Shuffle everything” + “Jump back in” |
| Android home | `app/android/.../ui/Screens.kt` | ✅ same lead/subtitle/shuffle pattern, native Compose |
| Android now playing | `app/android/.../ui/NowPlaying.kt` | ✅ centred type, soft accent halo behind the art |
| New-user palette is Violet | web defaults, `src/mcmusic.py`, Android `Settings` | ✅ five swappable families, no brass default |
| Installed on the phone | `apps/android/mainbuild.apk` via adb | ✅ device `79SOE6VGSGSODU4P` (SN509C, Android 14) |
| Binaries in git | none | ✅ GitHub Releases + ignored `apps/` cache; only text manifest tracked |
| Cookieless device sign-in | `src/auth.py`, `src/routes/system_routes.py` | ✅ short code → `mcd_…` bearer token, revocable |
| Pairing UI | `web/js/views.js` (Settings → Devices) | ✅ get code, list paired devices, revoke |
| 3DS homebrew scaffold | `app/3ds/` | ✅ pair, list, download to SD; audio decoder next |

## 1. macOS app — scaffolded, needs a Mac to ship

The macOS build is the **same PySide6 Qt client** as `app/linux`, not a second
app. `app/macos/` holds a launcher, an icon pipeline and a PyInstaller script
that produce `mcmusic.app` and an optional `.dmg`.

- **Why first:** zero new UI code; the shared client already has parity with the
  web contracts.
- **Left to do:** run `app/macos/build.sh` on macOS, wire `MPNowPlayingInfoCenter`
  for the system Now Playing panel, and optionally sign/notarize.
- **Cannot be built here:** PyInstaller cannot cross-build a `.app` from Linux.

## 2. Windows desktop — scaffolded, needs a Windows machine

`app/linux` is Qt 6 + PySide6 and already platform-neutral apart from MPRIS.
`app/windows/` holds the launcher and a `build.ps1` that produces
`dist\mcmusic\mcmusic.exe` (plus an optional zip):

- `python -m PyInstaller --noconfirm --clean --windowed --name mcmusic --icon build\mcmusic.ico --paths app\linux --hidden-import mcmusic_linux.cli --collect-submodules mcmusic_linux --collect-data mcmusic_linux --hidden-import winsdk.windows.media launcher.py`
- Icon is generated from `web/icon-512.png` into a multi-size `.ico`.
- MPRIS is skipped on Windows; the shared `MediaBridge` supplies SMTC instead.
- Audio currently goes through QtMultimedia; verify the WASAPI backend.

**Effort:** an afternoon once a Windows machine is available.

## 3. Nintendo 2DS / 3DS — plan first, build second

See `docs/3ds-client.md` for the platform reality. Short version: it is a C
homebrew `.3dsx`/`.cia` (devkitARM + libctru + citro2d), and the hard part is
server auth, not drawing.

Server half — ✅ shipped:

1. ✅ `POST /api/devices/code` → 8-character single-use code, 5-minute expiry.
2. ✅ `POST /api/devices/claim` → long-lived `mcd_…` token (hash stored only).
3. ✅ `Authorization: Bearer <token>` accepted beside the session cookie.
4. ✅ `GET /api/ping` → service + current user for a fast startup check.
5. ✅ Settings → Devices: get a code, see paired devices, revoke one.
6. ✅ `tests/test_device_auth.py` covers issue, claim, reuse, expiry, bearer
   access, listing and revocation against a real server.

Console milestones:

1. ✅ Client scaffold (`app/3ds/`): pair, list tracks, download to SD.
2. ⏳ Audio: fixed-point MP3 decoder or server PCM/ADPCM transcode, `ndsp` ring
   buffer. The scaffold deliberately does not fake playback.
3. ⏳ Library + queue + on-screen keyboard search + small SD cover cache.
4. ⏳ Playback reporting + heartbeat so the console appears in the devices list
   and can be remote-controlled like Android.
5. ⏳ Offline play counts sync, `.cia` icon/banner, sleep pause, 2DS colours.

**Reality check:** this is weekends of C, not an afternoon. It should be a
player, not a client for admin/rooms/Rotur.

## 4. Shared client polish that helps every platform

- **Offline parity:** Android and web both cache audio; the desktop cache is
  smaller. Align the eviction policy and show a single “offline” badge.
- **Device handoff:** the server already tracks devices, heartbeat and the
  active owner. Add “continue on this device” to the deck on all clients.
- **Lyrics:** web and Android have a lyrics sheet. Port it to Qt.
- **Room links:** web and Android show the permanent room link; add the same
  panel to the Qt settings screen.

## 5. Presence and integrations

- Rotur activity is live (`music_activity/`), Discord Rich Presence optional.
- Add a “what the room is playing” card to the web home when a room is active.
- Keep tokens server-side; no client gets the Rotur password.

## 6. Quality of life

- Publish every build to `apps/` with stable URLs (already done by
  `scripts/publish_apps.sh`).
- One `make check` style target: `node --check` on web modules, `py_compile` on
  `src/`, Kotlin compile, and the existing unittest suites.
- Version the clients together (web shell `9`, Android `1.1`, desktop `1.1`).

## Ordering rule

Ship the thing that removes a whole platform gap with the least new code:
**macOS → Windows → 3DS server auth → 3DS client**. Everything else is polish
that can ride along.
