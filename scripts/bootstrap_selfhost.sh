#!/usr/bin/env bash
# Idempotent first-run setup for a self-hosted mcmusic server.
# Run from the repository root: ./scripts/bootstrap_selfhost.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== mcmusic self-host bootstrap =="

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v npm >/dev/null || { echo "npm is required to build the web client" >&2; exit 1; }

if [ ! -d .venv ]; then
  echo "Creating .venv"
  python3 -m venv .venv
fi

echo "Installing Python requirements"
.venv/bin/pip install --upgrade pip >/dev/null
.venv/bin/pip install -r requirements.txt

if [ ! -f mcmusic.env ]; then
  cp mcmusic.env.example mcmusic.env
  echo "Created mcmusic.env — edit PUBLIC_URL, MUSIC_DIR, DATA_DIR and INVITE_CODE before starting."
else
  echo "mcmusic.env already exists; leaving it alone."
fi

value() {
  local key="$1"
  sed -n "s/^${key}=//p" mcmusic.env | head -n 1 | sed 's/^"//; s/"$//' || true
}

data_dir="$(value DATA_DIR)"
music_dir="$(value MUSIC_DIR)"

if [ -n "$data_dir" ]; then
  mkdir -p "$data_dir"
  echo "Data directory ready: $data_dir"
fi
if [ -n "$music_dir" ]; then
  mkdir -p "$music_dir"
  echo "Music directory ready: $music_dir"
fi

echo "Building web client into web/ui/"
( cd ui && npm ci && npm run build )

echo
echo "Done. Next:"
echo "  1. Edit mcmusic.env"
echo "  2. Smoke test: PYTHONPATH=.:src .venv/bin/gunicorn -w 1 --threads 8 -b 127.0.0.1:8000 mcmusic:app"
echo "  3. Install deploy/mcmusic.service.example as a systemd unit (see docs/selfhost.md)"
echo "  4. Put HTTPS in front and open PUBLIC_URL/auth"
