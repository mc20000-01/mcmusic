#!/usr/bin/env bash
# Build the macOS .app from the shared Qt client in app/linux.
#
#   ./build.sh              -> dist/mcmusic.app
#   MAKE_DMG=1 ./build.sh   -> dist/mcmusic.app + dist/mcmusic-<version>.dmg
#
# Everything is written under app/macos/{.venv-macos,build,dist}, none of which
# is committed.
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(cd ../.. && pwd)"
LINUX="$ROOT/app/linux"
VERSION="${VERSION:-1.1}"
PYTHON="${PYTHON:-python3}"
ARCH="${ARCH:-}"
MAKE_DMG="${MAKE_DMG:-0}"

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
python -m pip install -e "$LINUX" pyinstaller >/dev/null

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
  --collect-data mcmusic_linux \
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

echo
echo "Done: dist/mcmusic.app"
echo "Unsigned builds may need: xattr -dr com.apple.quarantine dist/mcmusic.app"
