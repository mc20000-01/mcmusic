#!/usr/bin/env bash
# Build the Linux desktop client as an AppImage.
#
#   ./scripts/build_appimage.sh                 # -> builds/mcmusic-x86_64.AppImage
#   APPIMAGETOOL=/path/to/tool ./scripts/build_appimage.sh
#
# Like the .deb, this ships the Python sources and uses the host's Python and
# Qt 6 bindings. appimagetool packs the small tree into a portable AppImage;
# no interpreter or Qt libraries are vendored.
set -euo pipefail
cd "$(dirname "$0")/.."

tool="${APPIMAGETOOL:-appimagetool}"
if ! command -v "$tool" >/dev/null 2>&1; then
  echo "appimagetool is required to build the AppImage (set APPIMAGETOOL)" >&2
  exit 1
fi

version=$(PYTHONPATH=app/linux python3 -c 'from mcmusic_linux.version import FALLBACK_VERSION; print(FALLBACK_VERSION)')
version=${version:-0.0.0}

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT
appdir="$stage/mcmusic.AppDir"

mkdir -p "$appdir/usr/lib" \
         "$appdir/usr/share/applications" \
         "$appdir/usr/share/icons/hicolor/scalable/apps"
cp -a app/linux/mcmusic_linux "$appdir/usr/lib/"
find "$appdir/usr/lib/mcmusic_linux" -name '__pycache__' -type d -prune -exec rm -rf {} +

cat > "$appdir/AppRun" <<'RUN'
#!/bin/sh
# Resolve the AppDir from AppRun's location in the mounted image.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONPATH="$here/usr/lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m mcmusic_linux "$@"
RUN
chmod 0755 "$appdir/AppRun"

# appimagetool reads the desktop file and icon from the AppDir root.
sed -e 's|^Exec=.*|Exec=AppRun %U|' \
    -e 's|^TryExec=.*|TryExec=AppRun|' \
    app/linux/mcmusic.desktop > "$appdir/mcmusic.desktop"
cp app/linux/mcmusic_linux/assets/mcmusic.svg "$appdir/mcmusic.svg"
cp "$appdir/mcmusic.desktop" "$appdir/usr/share/applications/mcmusic.desktop"
cp "$appdir/mcmusic.svg" "$appdir/usr/share/icons/hicolor/scalable/apps/mcmusic.svg"

# The launcher must use the package's __main__, not cli.py directly: cli.py
# defines main() but has no __main__ guard, so invoking it as a module exits
# silently. --help needs no Qt and proves the entry point really dispatches.
help_output=$(PYTHONPATH="$appdir/usr/lib" python3 -m mcmusic_linux --help)
[[ $help_output == *"usage: mcmusic-desktop"* ]] || {
  echo "AppImage entry point did not print usage" >&2
  exit 1
}

mkdir -p builds
out="builds/mcmusic-x86_64.AppImage"
ARCH=x86_64 "$tool" "$appdir" "$out"
echo "built $out for mcmusic $version"
