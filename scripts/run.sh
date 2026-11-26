#!/usr/bin/env bash
# Start mcmusic with the same one-worker gunicorn settings and import path as
# deploy/mcmusic.service.example. Safe to call from any working directory.
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export PYTHONPATH="$root:$root/src${PYTHONPATH:+:$PYTHONPATH}"

gunicorn_bin="$root/.venv/bin/gunicorn"
if [ ! -x "$gunicorn_bin" ]; then
    gunicorn_bin=gunicorn
fi

exec "$gunicorn_bin" -w 1 --threads 8 \
    -b "${MCMUSIC_BIND:-127.0.0.1:8000}" --timeout 600 \
    --access-logfile - --error-logfile - mcmusic:app "$@"
