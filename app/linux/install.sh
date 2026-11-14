#!/usr/bin/env bash
# Per-user install of the native mcmusic desktop client.
# Creates a venv next to the sources, installs the package, then adds a
# freedesktop menu entry and the scalable app icon.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}
VENV="$PWD/.venv"

echo "==> creating virtualenv at $VENV"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip >/dev/null
echo "==> installing mcmusic-desktop and Qt"
"$VENV/bin/python" -m pip install .

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
mkdir -p "$DATA/applications" "$DATA/icons/hicolor/scalable/apps"
install -m 0644 mcmusic.desktop "$DATA/applications/mcmusic.desktop"
install -m 0644 mcmusic_linux/assets/mcmusic.svg "$DATA/icons/hicolor/scalable/apps/mcmusic.svg"

# Point the menu entry at this checkout's venv.
sed -i "s|^Exec=.*|Exec=$VENV/bin/mcmusic-desktop %U|" "$DATA/applications/mcmusic.desktop"
sed -i "s|^TryExec=.*|TryExec=$VENV/bin/mcmusic-desktop|" "$DATA/applications/mcmusic.desktop"

command -v update-desktop-database >/dev/null \
  && update-desktop-database "$DATA/applications" >/dev/null 2>&1 || true
command -v gtk-update-icon-cache >/dev/null \
  && gtk-update-icon-cache -f -t "$DATA/icons/hicolor" >/dev/null 2>&1 || true

echo "==> installed"
echo "Launch from your app menu, or run: $VENV/bin/mcmusic-desktop"
