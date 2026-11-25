#!/usr/bin/env bash
# Build the macOS .app from the shared Qt client in app/linux.
#
#   ./build.sh              -> dist/mcmusic.app
#   MAKE_DMG=1 ./build.sh   -> dist/mcmusic.app + dist/mcmusic-<version>.dmg
#
# Everything is written under app/macos/{.venv-macos,build,dist}, none of which
# is committed. Release checklist: codesign/notarize with APPLE_ID,
# APPLE_TEAM_ID and APPLE_APP_PASSWORD when available, publish to apps/macos,
# and verify MPNowPlayingInfoCenter metadata plus remote media keys in the
# packaged .app (source checkouts do not exercise the PyInstaller bundle).
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
LINUX="$ROOT/app/linux"
# The shared client version.py is the single source of truth for every bundle.
VERSION="${VERSION:-$(sed -n 's/^FALLBACK_VERSION = "\(.*\)"/\1/p' \
  "$LINUX/mcmusic_linux/version.py" | head -n 1)}"
PYTHON="${PYTHON:-python3}"
ARCH="${ARCH:-}"
MAKE_DMG="${MAKE_DMG:-0}"
PUBLISH_APPS="${PUBLISH_APPS:-1}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "build.sh needs macOS: PyInstaller cannot cross-build a .app from Linux." >&2
  echo "The client itself still runs from app/linux on this machine." >&2
  exit 1
fi

for tool in sips iconutil codesign; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "missing $tool — install the Xcode command-line tools: xcode-select --install" >&2
    exit 1
  fi
done

echo "==> Python environment (.venv-macos)"
if [ ! -d .venv-macos ]; then
  "$PYTHON" -m venv .venv-macos
fi
# shellcheck disable=SC1091
source .venv-macos/bin/activate
python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -e "$LINUX[macos-media]" pyinstaller >/dev/null

echo "==> Icon"
mkdir -p build
# The repo keeps a 512px PNG; sips can expand it cleanly for the 1024 slot.
sips -z 1024 1024 "$ROOT/web/icon-512.png" --out build/icon-1024.png >/dev/null
iconset=build/mcmusic.iconset
rm -rf "$iconset" && mkdir -p "$iconset"
# iconutil wants the exact @1x/@2x names; render each slot from the master
# image directly so a missing intermediate size can never break the build.
while read -r name size; do
  sips -z "$size" "$size" build/icon-1024.png --out "$iconset/$name" >/dev/null
done <<'ICONS'
icon_16x16.png 16
icon_16x16@2x.png 32
icon_32x32.png 32
icon_32x32@2x.png 64
icon_128x128.png 128
icon_128x128@2x.png 256
icon_256x256.png 256
icon_256x256@2x.png 512
icon_512x512.png 512
icon_512x512@2x.png 1024
ICONS
iconutil -c icns "$iconset" -o build/mcmusic.icns
rm -rf "$iconset" build/icon-1024.png

echo "==> PyInstaller"
rm -rf build/mcmusic dist/mcmusic.app
arch_args=()
if [ -n "$ARCH" ]; then arch_args=(--target-arch "$ARCH"); fi

python -m PyInstaller \
  --noconfirm --clean --windowed \
  --name mcmusic \
  --icon build/mcmusic.icns \
  --osx-bundle-identifier dev.mcmusic.app \
  --paths "$LINUX" \
  --hidden-import mcmusic_linux.cli \
  --collect-submodules mcmusic_linux \
  --collect-data mcmusic_linux \
  --hidden-import Foundation --hidden-import MediaPlayer --hidden-import objc \
  ${arch_args[@]+"${arch_args[@]}"} \
  launcher.py

# Put a readable version in the bundle so About/Finder agree with the build.
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" \
  dist/mcmusic.app/Contents/Info.plist 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $VERSION" \
  dist/mcmusic.app/Contents/Info.plist 2>/dev/null || true

if [ -n "${CODESIGN_ID:-}" ]; then
  echo "==> Signing as $CODESIGN_ID"
  codesign --deep --force --options runtime \
    --sign "$CODESIGN_ID" dist/mcmusic.app
  if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] \
          && [ -n "${APPLE_APP_PASSWORD:-}" ]; then
    echo "==> Notarizing"
    xcrun notarytool submit dist/mcmusic.app \
      --apple-id "$APPLE_ID" --team-id "$APPLE_TEAM_ID" \
      --password "$APPLE_APP_PASSWORD" --wait
    xcrun stapler staple dist/mcmusic.app
  fi
fi

if [ "$MAKE_DMG" = "1" ]; then
  echo "==> Disk image"
  rm -rf build/dmg && mkdir -p build/dmg
  cp -R dist/mcmusic.app build/dmg/
  ln -s /Applications build/dmg/Applications
  hdiutil create -volname "mcmusic" -srcfolder build/dmg \
    -ov -format UDZO "dist/mcmusic-$VERSION.dmg" >/dev/null
  rm -rf build/dmg
  echo "wrote dist/mcmusic-$VERSION.dmg"
fi

if [ "$PUBLISH_APPS" = "1" ]; then
  echo "==> Publishing to apps/macos (PUBLISH_APPS=0 to skip)"
  mkdir -p "$ROOT/apps/macos"
  (cd dist && zip -qry "$ROOT/apps/macos/mcmusic-$VERSION-macos.zip" mcmusic.app)
  cp "$ROOT/apps/macos/mcmusic-$VERSION-macos.zip" \
    "$ROOT/apps/macos/mainbuild.zip"
  if [ "$MAKE_DMG" = "1" ]; then
    cp "dist/mcmusic-$VERSION.dmg" "$ROOT/apps/macos/mcmusic-$VERSION.dmg"
    cp "dist/mcmusic-$VERSION.dmg" "$ROOT/apps/macos/mainbuild.dmg"
  fi
fi

echo
echo "Done: dist/mcmusic.app"
echo "Unsigned builds may need: xattr -dr com.apple.quarantine dist/mcmusic.app"
