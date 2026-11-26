#!/usr/bin/env bash
# Smoke test for every server command documented in README.md.
# Each command is started from the repository root, polled on the public
# /api/version endpoint, then stopped. All state is isolated under TMPDIR.
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
smoke_root=$(mktemp -d "${TMPDIR:-/tmp}/mcmusic-startup.XXXXXX")
cleanup() {
    rm -rf "$smoke_root"
}
trap cleanup EXIT

mkdir -p "$smoke_root/data" "$smoke_root/music"
export DATA_DIR="$smoke_root/data"
export MUSIC_DIR="$smoke_root/music"
export MCMUSIC_NO_BOT=1
export SCAN_ON_START=0

probe() {
    local label="$1"
    shift
    local log="$smoke_root/$label.log"
    (
        cd "$root"
        "$@" >"$log" 2>&1
    ) &
    local pid=$!
    local ready=0
    for _ in $(seq 1 60); do
        if curl -fsS --max-time 2 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
            ready=1
            break
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 0.5
    done
    kill -TERM "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    if [ "$ready" -ne 1 ]; then
        echo "FAIL: $label never answered /api/version" >&2
        cat "$log" >&2
        exit 1
    fi
    echo "PASS: $label answered /api/version"
}

cd "$root"

# 1. README: quick development server.
probe dev-server .venv/bin/python src/mcmusic.py

# 2. README: explicit production command, with the documented relative PYTHONPATH.
export PYTHONPATH=".:src"
probe gunicorn .venv/bin/gunicorn -w 1 --threads 8 \
    -b 127.0.0.1:8000 --timeout 600 mcmusic:app

# 3. README: cwd-independent launcher.
probe run-sh ./scripts/run.sh
