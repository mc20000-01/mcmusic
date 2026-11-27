#!/usr/bin/env bash
# Fixture coverage for scripts/check-versions.sh (no live builds or packages).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/scripts/check-versions.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

contains() {
  grep -F -- "$2" "$1" >/dev/null 2>&1 || fail "missing in $1: $2"
}

contains_spaced() {
  grep -E -- "$2" "$1" >/dev/null 2>&1 || fail "missing pattern in $1: $2"
}

setup_case() {
  local dir="$TMP/$1"
  mkdir -p "$dir/app/linux/mcmusic_linux" "$dir/gui/android/app" "$dir/app/ios" "$dir/ui" "$dir/web"
  printf 'FALLBACK_VERSION = "4.1.0"\n' > "$dir/app/linux/mcmusic_linux/version.py"
  printf 'versionName = "4.1.0"\n' > "$dir/gui/android/app/build.gradle.kts"
  printf '  MARKETING_VERSION: "4.1.0"\n' > "$dir/app/ios/project.yml"
  printf '{"name":"mcmusic-ui","version":"4.1.0"}\n' > "$dir/ui/package.json"
  printf '{"name":"mcmusic"}\n' > "$dir/web/manifest.webmanifest"
  printf 'Version: 4.1.0\n' > "$dir/control"
  printf '%s\n' "$dir"
}

run_case() {
  local dir=$1
  shift
  REPO_ROOT="$dir" \
  VERSION_FILE="$dir/app/linux/mcmusic_linux/version.py" \
  ANDROID_FILE="$dir/gui/android/app/build.gradle.kts" \
  IOS_FILE="$dir/app/ios/project.yml" \
  UI_PACKAGE="$dir/ui/package.json" \
  WEB_MANIFEST="$dir/web/manifest.webmanifest" \
  ROOT_PACKAGE="$dir/package.json" \
  DEB_FILE="$dir/control" \
  "$@" "$SCRIPT" > "$dir/out.txt" 2>&1
}

run_case_manifest() {
  local dir=$1
  REPO_ROOT="$dir" \
  VERSION_FILE="$dir/app/linux/mcmusic_linux/version.py" \
  ANDROID_FILE="$dir/gui/android/app/build.gradle.kts" \
  IOS_FILE="$dir/app/ios/project.yml" \
  UI_PACKAGE="$dir/ui/package.json" \
  WEB_MANIFEST="$dir/web/manifest.webmanifest" \
  ROOT_PACKAGE="$dir/package.json" \
  BUILD_DIR="$dir/builds" \
  "$SCRIPT" > "$dir/out.txt" 2>&1
}

ok_case="$(setup_case ok)"
run_case "$ok_case"
contains_spaced "$ok_case/out.txt" 'Android versionName +4\.1\.0'
contains_spaced "$ok_case/out.txt" 'iOS MARKETING_VERSION +4\.1\.0'
contains_spaced "$ok_case/out.txt" 'ui/package\.json +4\.1\.0'
contains "$ok_case/out.txt" 'no version field'
contains_spaced "$ok_case/out.txt" 'deb control +4\.1\.0'
contains "$ok_case/out.txt" 'all version sources agree: 4.1.0'

ios_case="$(setup_case ios)"
printf '  MARKETING_VERSION: "4.1.1"\n' > "$ios_case/app/ios/project.yml"
set +e
run_case "$ios_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'iOS mismatch was accepted'
contains "$ios_case/out.txt" 'version mismatch: version.py=4.1.0 but iOS MARKETING_VERSION=4.1.1'

deb_case="$(setup_case deb)"
printf 'Version: 4.0.1\n' > "$deb_case/control"
set +e
run_case "$deb_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'deb mismatch was accepted'
contains "$deb_case/out.txt" 'version mismatch: version.py=4.1.0 but deb control=4.0.1'

manifest_case="$(setup_case manifest)"
printf '{"name":"mcmusic","version":"4.0.1"}\n' > "$manifest_case/web/manifest.webmanifest"
set +e
run_case "$manifest_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'web manifest mismatch was accepted'
contains "$manifest_case/out.txt" 'version mismatch: version.py=4.1.0 but web/manifest.webmanifest=4.0.1'

release_case="$(setup_case release)"
mkdir -p "$release_case/builds"
printf '{"version":"4.1.0","tag":"latest","assets":[]}\n' \
  > "$release_case/builds/release-manifest.json"
run_case_manifest "$release_case"
contains_spaced "$release_case/out.txt" 'release manifest +4\.1\.0'

stale_case="$(setup_case stale)"
mkdir -p "$stale_case/builds"
printf '{"version":"4.0.1","tag":"latest","assets":[]}\n' \
  > "$stale_case/builds/release-manifest.json"
set +e
run_case_manifest "$stale_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'stale release manifest was accepted'
contains "$stale_case/out.txt" 'version mismatch: version.py=4.1.0 but release manifest=4.0.1'

printf 'check-versions tests: 6 checks passed\n'
