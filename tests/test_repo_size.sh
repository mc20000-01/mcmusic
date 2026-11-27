#!/usr/bin/env bash
# Fixture coverage for scripts/check-repo-size.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/scripts/check-repo-size.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

contains() {
  grep -F -- "$2" "$1" >/dev/null 2>&1 || fail "missing in $1: $2"
}

setup_case() {
  local dir="$TMP/$1"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" config user.name tester
  git -C "$dir" config user.email tester@example.invalid
  printf 'hello\n' > "$dir/note.txt"
  git -C "$dir" add note.txt
  git -C "$dir" commit -qm init
  printf '%s\n' "$dir"
}

run_case() {
  local dir=$1
  shift
  REPO_ROOT="$dir" "$@" "$SCRIPT" > "$dir/out.txt" 2>&1
}

ok_case="$(setup_case ok)"
run_case "$ok_case" env
contains "$ok_case/out.txt" 'tracked tree:'
contains "$ok_case/out.txt" 'tree <= 100 MiB'

big_case="$(setup_case big)"
printf '12345678901\n' > "$big_case/large.bin"
git -C "$big_case" add large.bin
set +e
run_case "$big_case" env MAX_FILE_BYTES=10
status=$?
set -e
[[ $status -ne 0 ]] || fail 'oversized file was accepted'
contains "$big_case/out.txt" 'tracked file over 0 MiB: large.bin'

binary_case="$(setup_case binary)"
printf 'fake\n' > "$binary_case/mcmusic-9.9.9.apk"
git -C "$binary_case" add mcmusic-9.9.9.apk
set +e
run_case "$binary_case" env
status=$?
set -e
[[ $status -ne 0 ]] || fail 'tracked APK was accepted'
contains "$binary_case/out.txt" 'tracked binary: mcmusic-9.9.9.apk'

tree_case="$(setup_case tree)"
for n in 1 2 3; do
  printf '123456789\n' > "$tree_case/blob-$n.dat"
  git -C "$tree_case" add "blob-$n.dat"
done
set +e
run_case "$tree_case" env MAX_TREE_BYTES=20
status=$?
set -e
[[ $status -ne 0 ]] || fail 'oversized tree was accepted'
contains "$tree_case/out.txt" 'limit is 20 bytes'

printf 'repo size guard tests: 4 checks passed\n'
