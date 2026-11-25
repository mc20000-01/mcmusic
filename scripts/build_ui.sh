#!/usr/bin/env bash
# Build the v3 web client into web/ui/ — what the Flask app serves at /.
#
#   ./scripts/build_ui.sh
#
# CI, the release workflow and any deployment should call this instead of
# npm directly, so a missing lockfile or a silently broken build fails here.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to build the web UI (install Node 20+)" >&2
  exit 1
fi

(
  cd ui
  if [ ! -d node_modules ] || [ package-lock.json -nt node_modules/.package-lock.json ]; then
    npm ci --no-audit --no-fund
  fi
  npm run build
)

# Stable URL for the embed gallery and widget pages, which have no bundler.
# Append the static violet-dark fallback after flufi's :root so non-SPA pages
# start on the default palette; the SPA then pins its palette inline at runtime.
cat ui/node_modules/flufi-ui/dist/style.css ui/src/env.css > web/ui/flufi-ui.css

test -f web/ui/index.html
echo "built web/ui ($(du -sh web/ui | cut -f1))"
