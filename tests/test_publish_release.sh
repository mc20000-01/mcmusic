#!/usr/bin/env bash
# Fake-gh coverage for scripts/publish-release.sh (no network, no real release).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/scripts/publish-release.sh"
TMP="$(mktemp -d)"
if [[ ${KEEP_TEST_TMP:-0} == 1 ]]; then
  trap 'printf "kept test fixtures in %s\n" "$TMP"' EXIT
else
  trap 'rm -rf "$TMP"' EXIT
fi

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

contains() {
  grep -F -- "$2" "$1" >/dev/null 2>&1 || fail "missing in $1: $2"
}

not_contains() {
  if grep -F -- "$2" "$1" >/dev/null 2>&1; then
    fail "unexpected in $1: $2"
  fi
}

setup_case() {
  local name=$1
  local dir="$TMP/$name"
  mkdir -p "$dir/builds" "$dir/repo" "$dir/remote.git"
  git init -q --bare "$dir/remote.git"
  git init -q "$dir/repo"
  (
    cd "$dir/repo"
    git config user.email test@example.invalid
    git config user.name test
    printf 'one\n' > file.txt
    git add file.txt
    git commit -qm 'initial'
    git remote add origin "$dir/remote.git"
    git push -q -u origin HEAD
  )

  mkdir -p "$dir/src/app/linux/mcmusic_linux" "$dir/src/gui/android/app"
  printf 'FALLBACK_VERSION = "4.1.0"\n' > "$dir/src/app/linux/mcmusic_linux/version.py"
  printf 'versionName = "4.1.0"\n' > "$dir/src/gui/android/app/build.gradle.kts"

  local file
  for file in \
    mcmusic-4.1.0.apk mcmusic-4.0.1.apk mcmusic-desktop_4.1.0_all.deb \
    mcmusic-x86_64.AppImage mcmusic-macos-4.1.0.app.zip mcmusic-4.1.0.dmg \
    mcmusic-windows-4.1.0.zip mcmusic-ios-simulator-4.1.0.app.zip \
    mcmusic-linux-source.zip SHA256SUMS; do
    printf 'fixture\n' > "$dir/builds/$file"
  done

  cat > "$dir/gh" <<'SHIM'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_LOG"
case "$1" in
  release)
    if [[ $2 == view && $3 == latest ]]; then
      printf '%s\n' stale.apk
    fi
    ;;
  api) printf '%s\n' latest ;;
esac
SHIM
  chmod +x "$dir/gh"
  printf '%s\n' "$dir"
}

run_case() {
  local dir=$1
  (
    cd "$dir/repo"
    GH_LOG="$dir/gh.log" \
    GITHUB_SHA="$(git rev-parse HEAD)" \
    GITHUB_REPOSITORY=owner/repo \
    BUILD_DIR="$dir/builds" \
    VERSION_FILE="$dir/src/app/linux/mcmusic_linux/version.py" \
    ANDROID_VERSION_FILE="$dir/src/gui/android/app/build.gradle.kts" \
    GH="$dir/gh" \
    "$SCRIPT" > "$dir/out.txt" 2>&1
  )
}

# (a) a new version creates v<version> with --latest=false and no clobber.
new_case="$(setup_case new)"
(
  cd "$new_case/repo"
  git tag latest
  git push -q origin latest
)
run_case "$new_case"
contains "$new_case/gh.log" 'release create v4.1.0'
contains "$new_case/gh.log" '--latest=false'
contains "$new_case/gh.log" 'release upload v4.1.0'
if grep -F 'release upload v4.1.0' "$new_case/gh.log" | grep -q -- '--clobber'; then
  fail 'versioned upload used --clobber'
fi

# (b) an existing version is never clobbered.
existing_case="$(setup_case existing)"
(
  cd "$existing_case/repo"
  git tag latest
  git tag v4.1.0
  git push -q origin latest v4.1.0
)
run_case "$existing_case"
contains "$existing_case/out.txt" 'v4.1.0 already exists, only refreshing latest'
not_contains "$existing_case/gh.log" 'release create v4.1.0'
not_contains "$existing_case/gh.log" 'release upload v4.1.0'

# (c) latest is always refreshed with --latest and may clobber stale assets.
for case_dir in "$new_case" "$existing_case"; do
  contains "$case_dir/gh.log" 'release edit latest'
  contains "$case_dir/gh.log" '--latest'
  contains "$case_dir/gh.log" 'release upload latest'
  contains "$case_dir/gh.log" 'release delete-asset latest stale.apk'
  if ! grep -F 'release upload latest' "$case_dir/gh.log" | grep -q -- '--clobber'; then
    fail 'latest upload did not use --clobber'
  fi
done

# (d) a mismatch between the two version sources fails before any gh call.
mismatch_case="$(setup_case mismatch)"
printf 'versionName = "4.1.1"\n' > \
  "$mismatch_case/src/gui/android/app/build.gradle.kts"
set +e
run_case "$mismatch_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'version mismatch was accepted'
contains "$mismatch_case/out.txt" 'version mismatch: version.py=4.1.0 but Android versionName=4.1.1'
[[ ! -f "$mismatch_case/gh.log" ]] || fail 'gh was called despite version mismatch'

printf 'publish-release tests: 4 checks passed\n'
