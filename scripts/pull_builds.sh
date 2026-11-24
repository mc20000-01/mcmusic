#!/usr/bin/env bash
# Pull the current public clients from the rolling GitHub Release into apps/.
#
# The server also does this automatically at boot and every ten minutes, but a
# maintainer can run this after publishing a release to refresh immediately.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=src python3 - <<'PY'
import github_builds
count = github_builds.sync()
print(f"pulled {count} build(s) from the latest GitHub Release")
PY
