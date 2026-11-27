#!/usr/bin/env bash
# Keep the tracked repository small. Release binaries belong on GitHub
# Releases and in the server's ignored apps/ cache, never in git.
#
#   ./scripts/check-repo-size.sh
#
# Limits are enforced on files reachable from the checked-out index: no
# tracked file over 25 MiB, no tracked tree over 100 MiB, and no published
# artifact file under builds/, apps/, releases/ or web/apps/.
set -euo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MAX_FILE="${MAX_FILE_BYTES:-$((25 * 1024 * 1024))}"
MAX_TREE="${MAX_TREE_BYTES:-$((100 * 1024 * 1024))}"

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

fail=0
total=0
count=0

while IFS= read -r -d '' file; do
  count=$((count + 1))

  case "$file" in
    builds/README.md|builds/SHA256SUMS|builds/release-manifest.json) ;;
    builds/*|apps/*|releases/*|web/apps/*)
      printf 'tracked release artifact: %s\n' "$file" >&2
      fail=1
      ;;
  esac
  case "$file" in
    *.apk|*.deb|*.AppImage|*.dmg|*.exe|*.msi|*.zip)
      printf 'tracked binary: %s\n' "$file" >&2
      fail=1
      ;;
  esac

  if [[ -f $ROOT/$file ]]; then
    size=$(stat -c %s -- "$ROOT/$file")
  else
    # A path can be tracked but absent in sparse checkouts; the object still
    # costs the repository the same amount, so measure it from HEAD.
    size=$(git -C "$ROOT" cat-file -s "HEAD:$file")
  fi
  total=$((total + size))
  if (( size > MAX_FILE )); then
    printf 'tracked file over %d MiB: %s (%d bytes)\n' \
      "$((MAX_FILE / 1048576))" "$file" "$size" >&2
    fail=1
  fi
done < <(git -C "$ROOT" ls-files -z)

if (( fail != 0 )); then
  die "repository size guard failed"
fi
if (( total > MAX_TREE )); then
  die "tracked tree is $total bytes; limit is $MAX_TREE bytes"
fi

printf 'tracked tree: %d files, %d bytes (file <= %d MiB, tree <= %d MiB)\n' \
  "$count" "$total" "$((MAX_FILE / 1048576))" "$((MAX_TREE / 1048576))"
