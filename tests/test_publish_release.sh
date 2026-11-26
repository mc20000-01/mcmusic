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
  if [[ -f $1 ]] && grep -F -- "$2" "$1" >/dev/null 2>&1; then
    fail "unexpected in $1: $2"
  fi
}

seed_state() {
  printf '%s=%s\n' "$2" "$3" >> "$1"
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
    mcmusic-linux-source.zip; do
    printf 'fixture\n' > "$dir/builds/$file"
  done
  (
    cd "$dir/builds"
    sha256sum mcmusic-4.1.0.apk mcmusic-desktop_4.1.0_all.deb \
      mcmusic-x86_64.AppImage mcmusic-macos-4.1.0.app.zip mcmusic-4.1.0.dmg \
      mcmusic-windows-4.1.0.zip mcmusic-ios-simulator-4.1.0.app.zip \
      mcmusic-linux-source.zip > SHA256SUMS
  )

  cat > "$dir/check-versions.sh" <<'CHECK'
#!/usr/bin/env bash
set -euo pipefail
v=$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$VERSION_FILE" | head -1)
a=$(sed -n 's/.*versionName[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' "$ANDROID_VERSION_FILE" | head -1)
if [[ $a != "$v" ]]; then
  printf 'version mismatch: version.py=%s but Android versionName=%s\n' "$v" "$a" >&2
  exit 1
fi
printf 'fixture version check ok\n'
CHECK
  chmod +x "$dir/check-versions.sh"

  cat > "$dir/gh" <<'SHIM'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$GH_LOG"
state_file=$GH_STATE
mkdir -p "$GH_NOTES_DIR"

get_state() {
  local line
  line=$(grep -F "$1=" "$state_file" 2>/dev/null | tail -n 1 || true)
  printf '%s' "${line#*=}"
}

set_state() {
  printf '%s=%s\n' "$1" "$2" >> "$state_file"
}

has_arg() {
  local needle=$1
  shift
  local arg
  for arg in "$@"; do
    [[ $arg == "$needle" ]] && return 0
  done
  return 1
}

case "$1" in
  release)
    case "$2" in
      view)
        tag=$3
        if [[ " $* " == *" --json isDraft "* ]]; then
          state=$(get_state "release:$tag")
          [[ -n $state ]] || state=missing
          case $state in
            missing) exit 1 ;;
            draft) printf 'true\n' ;;
            *) printf 'false\n' ;;
          esac
        elif [[ " $* " == *" --json assets "* ]]; then
          if [[ $tag == latest ]]; then
            list=$(get_state "assets:latest")
            if [[ -n $list ]]; then
              printf '%s\n' "$list" | tr ',' '\n' | sed '/^$/d'
            else
              state=$(get_state release:latest)
              if [[ -n $state && $state != missing ]]; then
                printf '%s\n' stale.apk README.md
              fi
            fi
          else
            get_state "assets:$tag" | tr ',' '\n' | sed '/^$/d'
          fi
        fi
        ;;
      create|edit)
        tag=$3
        previous=''
        for arg in "$@"; do
          if [[ $previous == --notes-file ]]; then
            cp "$arg" "$GH_NOTES_DIR/${tag}-notes.md"
          fi
          previous=$arg
        done
        if [[ $2 == create ]]; then
          state=published
          has_arg --draft "$@" && state=draft
          set_state "release:$tag" "$state"
        else
          if has_arg --draft=false "$@"; then
            set_state "release:$tag" published
          fi
        fi
        printf 'https://github.com/owner/repo/releases/tag/%s\n' "$tag"
        ;;
      upload)
        tag=$3
        if [[ $tag == v4.1.0 && ${SHIM_FAIL_UPLOAD_V:-0} == 1 ]]; then
          printf 'simulated version upload failure\n' >&2
          exit 1
        fi
        list=$(get_state "assets:$tag")
        if [[ $tag == latest ]]; then
          list=''
        fi
        for arg in "${@:4}"; do
          case $arg in --*) continue ;; esac
          base=${arg##*/}
          if [[ -n ${SHIM_HIDE_ASSET:-} && $base == "$SHIM_HIDE_ASSET" ]]; then
            continue
          fi
          if [[ -n $list ]]; then
            list="$list,$base"
          else
            list=$base
          fi
        done
        if [[ $tag == latest && ${SHIM_LATEST_HAS_README:-0} == 1 ]]; then
          list="$list,README.md"
        fi
        set_state "assets:$tag" "$list"
        ;;
      delete)
        tag=$3
        set_state "release:$tag" missing
        set_state "assets:$tag" ''
        printf 'deleted %s and cleaned up its tag\n' "$tag"
        ;;
      delete-asset)
        list=$(get_state assets:latest)
        if [[ -n $list ]]; then
          list=$(printf '%s\n' "$list" | tr ',' '\n' | grep -v -x "$4" | paste -sd, -)
          set_state assets:latest "$list"
        fi
        ;;
      download)
        dir=''
        while (($#)); do
          case $1 in
            --dir) dir=$2; shift 2 ;;
            *) shift ;;
          esac
        done
        [[ -n $dir ]] || dir=.
        mkdir -p "$dir"
        cp "$BUILD_DIR"/SHA256SUMS "$dir/SHA256SUMS"
        cp "$BUILD_DIR"/* "$dir/"
        if [[ ${SHIM_CORRUPT_SHA:-0} == 1 ]]; then
          sed -i "1s/^[0-9a-f]*/$(printf '0%.0s' {1..64})/" "$dir/SHA256SUMS"
        fi
        if [[ -n ${SHIM_SHA_EXTRA:-} ]]; then
          printf '%064d  %s\n' 0 "$SHIM_SHA_EXTRA" >> "$dir/SHA256SUMS"
        fi
        ;;
    esac
    ;;
  api) printf '%s\n' latest ;;
esac
SHIM
  chmod +x "$dir/gh"
  printf '%s\n' "$dir"
}

run_case() {
  local dir=$1
  shift
  (
    cd "$dir/repo"
    GH_LOG="$dir/gh.log" \
    GH_STATE="$dir/gh.state" \
    GH_NOTES_DIR="$dir/notes" \
    GITHUB_SHA="$(git rev-parse HEAD)" \
    GITHUB_REPOSITORY=owner/repo \
    BUILD_DIR="$dir/builds" \
    VERSION_FILE="$dir/src/app/linux/mcmusic_linux/version.py" \
    ANDROID_VERSION_FILE="$dir/src/gui/android/app/build.gradle.kts" \
    VERSION_CHECK="$dir/check-versions.sh" \
    GH="$dir/gh" \
    "$@" "$SCRIPT" > "$dir/out.txt" 2>&1
  )
}

remote_tags() {
  git -C "$1/repo" ls-remote --tags origin | sed -n '1,20p'
}

# (a) missing artifact aborts before any create, tag push or gh call.
missing_case="$(setup_case missing)"
rm "$missing_case/builds/mcmusic-x86_64.AppImage"
set +e
run_case "$missing_case"
status=$?
set -e
[[ $status -ne 0 ]] || fail 'missing artifact was accepted'
contains "$missing_case/out.txt" 'missing required artifact:'
not_contains "$missing_case/gh.log" 'release create'
[[ -z $(remote_tags "$missing_case") ]] || fail 'missing artifact touched remote tags'

# (b) a fresh repo creates latest without trying to edit it.
fresh_case="$(setup_case fresh)"
run_case "$fresh_case"
contains "$fresh_case/gh.log" 'release create v4.1.0 --draft'
contains "$fresh_case/gh.log" 'release upload v4.1.0'
contains "$fresh_case/gh.log" 'release edit v4.1.0 --draft=false --latest=false'
contains "$fresh_case/out.txt" 'published asset checksums verified'
contains "$fresh_case/gh.log" 'release create latest'
not_contains "$fresh_case/gh.log" 'release edit latest'
if grep -F 'release upload v4.1.0' "$fresh_case/gh.log" | grep -q -- '--clobber'; then
  fail 'versioned upload used --clobber'
fi

# (c) an existing published version is immutable; latest is edited.
existing_case="$(setup_case existing)"
seed_state "$existing_case/gh.state" release:v4.1.0 published
seed_state "$existing_case/gh.state" release:latest published
run_case "$existing_case" env SHIM_LATEST_HAS_README=1
contains "$existing_case/out.txt" 'is published; versioned releases are immutable'
not_contains "$existing_case/gh.log" 'release create v4.1.0'
not_contains "$existing_case/gh.log" 'release upload v4.1.0'
contains "$existing_case/gh.log" 'release edit latest'

# (d) a stale draft is not treated as an existing immutable release.
draft_case="$(setup_case draft)"
seed_state "$draft_case/gh.state" release:v4.1.0 draft
seed_state "$draft_case/gh.state" release:latest published
run_case "$draft_case" env SHIM_LATEST_HAS_README=1
contains "$draft_case/out.txt" 'discarding stale draft release v4.1.0'
contains "$draft_case/gh.log" 'release delete v4.1.0 -y --cleanup-tag'
contains "$draft_case/gh.log" 'release create v4.1.0 --draft'

# (e) an upload failure deletes the draft and the tag it created.
upload_fail_case="$(setup_case upload-fail)"
set +e
run_case "$upload_fail_case" env SHIM_FAIL_UPLOAD_V=1
status=$?
set -e
[[ $status -ne 0 ]] || fail 'upload failure was accepted'
contains "$upload_fail_case/gh.log" 'release create v4.1.0 --draft'
contains "$upload_fail_case/gh.log" 'release delete v4.1.0 -y --cleanup-tag'
[[ -z $(remote_tags "$upload_fail_case") ]] || fail 'upload failure left remote tags behind'
[[ -z $(git -C "$upload_fail_case/repo" tag --list v4.1.0) ]] || fail 'upload failure left a local tag'

# (f) a missing uploaded asset fails the name check and cleans up the draft.
asset_case="$(setup_case asset-check)"
set +e
run_case "$asset_case" env SHIM_HIDE_ASSET=mcmusic-4.1.0.apk
status=$?
set -e
[[ $status -ne 0 ]] || fail 'incomplete asset list was accepted'
contains "$asset_case/out.txt" 'asset list for v4.1.0 does not match'
contains "$asset_case/gh.log" 'release delete v4.1.0 -y --cleanup-tag'
[[ -z $(git -C "$asset_case/repo" tag --list v4.1.0) ]] || fail 'asset check failure left a local tag'

# (g) latest still clobbers stale artifacts and keeps README.md.
contains "$existing_case/gh.log" 'release delete-asset latest stale.apk'
for case_dir in "$fresh_case" "$existing_case"; do
  contains "$case_dir/gh.log" 'release upload latest'
  if ! grep -F 'release upload latest' "$case_dir/gh.log" | grep -q -- '--clobber'; then
    fail 'latest upload did not use --clobber'
  fi
done

# (h) an unchanged version with new commits annotates the warning.
warning_case="$(setup_case warning)"
seed_state "$warning_case/gh.state" release:v4.1.0 published
seed_state "$warning_case/gh.state" release:latest published
(
  cd "$warning_case/repo"
  printf 'two\n' > file.txt
  git add file.txt
  git commit -qm 'Update published builds'
  git tag v4.1.0
  git push -q origin v4.1.0
  printf 'three\n' > file.txt
  git add file.txt
  git commit -qm 'change without a version bump'
)
run_case "$warning_case" env SHIM_LATEST_HAS_README=1
contains "$warning_case/out.txt" '1 commits after v4.1.0; version not bumped'
contains "$warning_case/out.txt" '::warning::1 commits after v4.1.0; version not bumped'
contains "$warning_case/notes/latest-notes.md" '1 commits after v4.1.0; version not bumped'
contains "$warning_case/notes/latest-notes.md" 'change without a version bump'
not_contains "$warning_case/notes/latest-notes.md" 'Update published builds'

# (i) a checksum mismatch after publishing fails and cleans up draft and tag.
sha_case="$(setup_case bad-sha)"
set +e
run_case "$sha_case" env SHIM_CORRUPT_SHA=1
status=$?
set -e
[[ $status -ne 0 ]] || fail 'bad published checksum was accepted'
contains "$sha_case/out.txt" 'published asset checksum verification failed'
contains "$sha_case/gh.log" 'release delete v4.1.0 -y --cleanup-tag'
[[ -z $(git -C "$sha_case/repo" tag --list v4.1.0) ]] || fail 'checksum failure left a local tag'

# (j) SHA256SUMS may not describe a file that was not attached to the release.
extra_case="$(setup_case extra-sha)"
set +e
run_case "$extra_case" env SHIM_SHA_EXTRA=unattached.bin
status=$?
set -e
[[ $status -ne 0 ]] || fail 'unattached checksum entry was accepted'
contains "$extra_case/out.txt" 'SHA256SUMS in v4.1.0 lists files that are not attached'
contains "$extra_case/gh.log" 'release delete v4.1.0 -y --cleanup-tag'
[[ -z $(git -C "$extra_case/repo" tag --list v4.1.0) ]] || fail 'extra checksum entry left a local tag'

# (k) a version mismatch fails before any gh call.
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

printf 'publish-release tests: 11 checks passed\n'
