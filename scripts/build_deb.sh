#!/usr/bin/env bash
# Build the Linux desktop client into a .deb.
#
#   ./scripts/build_deb.sh                 # -> apps/linux/mcmusic-desktop_<version>_all.deb
#
# The package ships the Python sources and uses the distribution's Qt 6
# bindings, so it stays small. Qt is a declared dependency, not vendored:
# bundling PySide6 would add hundreds of megabytes for no gain.
set -euo pipefail
cd "$(dirname "$0")/.."

version=$(grep -oP '^version\s*=\s*"\K[^"]+' app/linux/pyproject.toml | head -1)
version=${version:-0.0.0}
# A deb version must start with a digit.
case "$version" in [0-9]*) ;; *) version="0.${version}" ;; esac

src=app/linux
out=apps/linux
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

root="$stage/mcmusic-desktop_${version}_all"
mkdir -p "$root/DEBIAN" \
         "$root/usr/lib/mcmusic-desktop" \
         "$root/usr/bin" \
         "$root/usr/share/applications" \
         "$root/usr/share/icons/hicolor/scalable/apps"

cp -a "$src/mcmusic_linux" "$root/usr/lib/mcmusic-desktop/"
find "$root/usr/lib/mcmusic-desktop" -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > "$root/usr/bin/mcmusic-desktop" <<'LAUNCH'
#!/bin/sh
# Run the packaged client from the system Python and the system Qt bindings.
PYTHONPATH=/usr/lib/mcmusic-desktop${PYTHONPATH:+:$PYTHONPATH}
export PYTHONPATH
exec python3 -m mcmusic_linux.cli "$@"
LAUNCH
chmod 0755 "$root/usr/bin/mcmusic-desktop"

install -m 0644 "$src/mcmusic.desktop" "$root/usr/share/applications/mcmusic.desktop"
install -m 0644 "$src/mcmusic_linux/assets/mcmusic.svg" \
  "$root/usr/share/icons/hicolor/scalable/apps/mcmusic.svg"

size=$(du -sk "$root/usr" | cut -f1)
cat > "$root/DEBIAN/control" <<CONTROL
Package: mcmusic-desktop
Version: ${version}
Section: sound
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-pyside6.qtmultimedia, python3-pyside6.qtsvg, python3-pyside6.qtdbus
Installed-Size: ${size}
Maintainer: mcmusic <mcmusic-support@sdisk.us>
Homepage: https://github.com/mc20000-01/mcmusic
Description: Native desktop client for a self-hosted mcmusic server
 Your library, your room, your rules. Streams from the server you own, with
 one speaker at a time and every other signed-in device acting as a remote.
 .
 Includes the Qt window and the no-dependency terminal client (--tui).
CONTROL

mkdir -p "$out"
deb="$out/mcmusic-desktop_${version}_all.deb"
dpkg-deb --root-owner-group --build "$root" "$deb" >/dev/null
echo "built $deb ($(du -h "$deb" | cut -f1))"
