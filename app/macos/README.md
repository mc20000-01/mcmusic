# mcmusic for macOS

The macOS app is the **same native Qt client** as `app/linux`, packaged as a
`.app`. There is no second codebase to keep in sync: the rail, deck, screens,
theme tokens and Lucide icon geometry are identical, and PySide6 ships a real
Cocoa backend on macOS.

```
app/macos/
  launcher.py   # frozen-app entry point (imports mcmusic_linux.cli)
  build.sh      # venv → PyInstaller → mcmusic.app (+ optional .dmg)
```

## What works out of the box

- Qt 6 window with the full client: home, search, library, albums, artists,
  liked, playlists, queue, requests, settings and admin.
- `--tui` still works from a checkout for headless use over SSH.
- Audio through QtMultimedia (CoreAudio on macOS).
- The same server contracts and theme keys as the web, Android and Linux
  clients, so a theme or accent picked anywhere renders the same here.

## What is Linux-only

The Linux build registers an MPRIS2 D-Bus service for desktop media keys.
macOS uses the system Now Playing panel instead; wiring `MPNowPlayingInfoCenter`
is a follow-up, not a blocker. The Linux `.desktop` file and `install.sh` are
not used on macOS.

## Build

You need macOS, Xcode command-line tools (`sips`, `iconutil`), Python 3.10+
and an internet connection for the wheels.

```bash
cd app/macos
./build.sh
```

Output:

```
dist/mcmusic.app        # drag to /Applications
dist/mcmusic-1.1.dmg    # with MAKE_DMG=1
```

The script creates `.venv-macos/`, installs `app/linux` in editable mode plus
PyInstaller, builds the icon set from `web/icon-512.png`, and bundles
`mcmusic_linux` with `--collect-data` so the `mc` mark and assets travel with
the app.

Useful switches:

```bash
PYTHON=python3.12 ./build.sh          # pick an interpreter
ARCH=universal2 ./build.sh            # universal binary (needs universal wheels)
MAKE_DMG=1 ./build.sh                 # also write a .dmg
VERSION=1.2 ./build.sh                # override the bundle version
```

## Running from a checkout

```bash
cd app/linux
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
./mcmusic-desktop
```

## Signing and Gatekeeper

The build is unsigned. On first launch macOS may say the app is from an
unidentified developer; right-click → **Open**, or clear the quarantine flag:

```bash
xattr -dr com.apple.quarantine dist/mcmusic.app
```

For distribution to other people, set `CODESIGN_ID` to a Developer ID
certificate and add notarization (`xcrun notarytool`) to `build.sh`. That is a
deliberate opt-in because it needs an Apple account and credentials.
