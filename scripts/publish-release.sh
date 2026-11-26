#!/usr/bin/env bash
# Publish the rolling "latest" release and one immutable v<version> snapshot.
#
#   ./scripts/publish-release.sh            # publish from builds/
#   DRY_RUN=1 ./scripts/publish-release.sh  # print every gh/git command only
#
# version.py is the source of truth; scripts/check-versions.sh verifies every
# other checked-in version source before this script touches a tag or release.
# All current artifacts must exist: latest is the server fallback, so a skipped
# asset would silently break downloads. Version releases are snapshots: a
# published tag is never overwritten. A new version is built as a draft, fully
# uploaded and verified, then published; any failure cleans up the draft/tag.
set -euo pipefail

DRY_RUN="${DRY_RUN:-0}"
GH="${GH:-gh}"
GH_REPO="${GITHUB_REPOSITORY:-${GH_REPO:-mc20000-01/mcmusic}}"
SHA="${GITHUB_SHA:-$(git rev-parse HEAD)}"
REMOTE="${REMOTE:-origin}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${VERSION_FILE:-$ROOT/app/linux/mcmusic_linux/version.py}"
VERSION_CHECK="${VERSION_CHECK:-$ROOT/scripts/check-versions.sh}"
BUILD_DIR="${BUILD_DIR:-$ROOT/builds}"

print_cmd() {
  local tool=$1
  shift
  printf '%s' "$tool"
  printf ' %q' "$@"
  printf '\n'
}

run_gh() {
  if [[ $DRY_RUN == 1 ]]; then
    print_cmd gh "$@"
  else
    "$GH" "$@"
  fi
}

run_git() {
  if [[ $DRY_RUN == 1 ]]; then
    print_cmd git "$@"
  else
    git "$@"
  fi
}

note() {
  printf '# %s\n' "$*"
}

warn() {
  printf '%s\n' "$*" >&2
  printf '::warning::%s\n' "$*" >&2
}

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

version="$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$VERSION_FILE" 2>/dev/null | head -1 || true)"
[[ -n $version ]] || die "could not read FALLBACK_VERSION from $VERSION_FILE"

tag="v${version}"

# Fail before any tag or release is touched. This is deliberately fatal for
# every artifact, including latest: a partial rolling release would leave the
# build fallback serving a broken set of files.
BUILD_DIR="$BUILD_DIR" "$VERSION_CHECK"

declare -a expected=(
  "mcmusic-${version}.apk"
  "mcmusic-desktop_${version}_all.deb"
  "mcmusic-x86_64.AppImage"
  "mcmusic-macos-${version}.app.zip"
  "mcmusic-${version}.dmg"
  "mcmusic-windows-${version}.zip"
  "mcmusic-ios-simulator-${version}.app.zip"
  "mcmusic-linux-source.zip"
  SHA256SUMS
)
declare -a assets=()
for name in "${expected[@]}"; do
  [[ -f $BUILD_DIR/$name ]] || die "missing required artifact: $BUILD_DIR/$name"
  assets+=("$BUILD_DIR/$name")
done
note "all ${#assets[@]} current artifacts are present in $BUILD_DIR"

notes_dir="$(mktemp -d)"
trap 'rm -rf "$notes_dir"' EXIT
latest_notes="$notes_dir/latest.md"
version_notes="$notes_dir/version.md"

artifact_table() {
  local f base size sum
  echo '| Artifact | Size | SHA256 |'
  echo '| --- | ---: | --- |'
  for f in "${assets[@]}"; do
    base="$(basename "$f")"
    [[ $base == SHA256SUMS ]] && continue
    size="$(du -h "$f" | cut -f1)"
    sum="$(sha256sum "$f" | cut -d' ' -f1)"
    printf "| \`%s\` | %s | \`%s\` |\n" "$base" "$size" "$sum"
  done
}

recent_changes() {
  # Never walk back to the previous version tag for "Recent changes", and
  # never let CI's binary-only commits crowd out real changes.
  git log --pretty=format:'- %s (%h)' --invert-grep \
    --grep='^Update published builds' -n 12 "$SHA" 2>/dev/null || true
}

version_changes() {
  local previous
  previous="$(git tag --list 'v[0-9]*' --sort=-version:refname \
    | grep -v "^${tag}$" | head -1 || true)"
  if [[ -n $previous ]]; then
    git log --pretty=format:'- %s (%h)' --invert-grep \
      --grep='^Update published builds' "${previous}..${SHA}" 2>/dev/null || true
  else
    recent_changes
  fi
}

behind_note=""
tag_commit="$(git rev-list -n 1 "$tag" 2>/dev/null || true)"
if [[ -n $tag_commit && $tag_commit != "$SHA" ]]; then
  behind="$(git rev-list --count "${tag_commit}..${SHA}" 2>/dev/null || true)"
  if [[ -n $behind && $behind != 0 ]]; then
    behind_note="${behind} commits after ${tag}; version not bumped"
    warn "$behind_note"
  fi
fi

{
  echo "## mcmusic latest (${version})"
  echo
  echo "Current version: **${version}**. See [${tag}](https://github.com/${GH_REPO}/releases/tag/${tag}) for the immutable snapshot."
  echo
  echo "Built from \`${SHA:0:12}\`."
  if [[ -n $behind_note ]]; then
    echo
    echo "**${behind_note}**"
  fi
  echo
  artifact_table
  echo
  echo '### Recent changes'
  recent_changes
  echo
} > "$latest_notes"

{
  echo "## mcmusic ${version}"
  echo
  echo "Stable snapshot from \`${SHA:0:12}\`."
  echo
  echo '### Artifacts'
  artifact_table
  echo
  echo '### Changes since the previous version'
  version_changes
  echo
} > "$version_notes"

# Decide from the GitHub release, not from a tag: a leftover tag or a draft is
# not an immutable published release. This runs before the latest tag moves.
release_state() {
  local wanted=$1 state
  if [[ $DRY_RUN == 1 ]]; then
    printf '# gh release view %s --json isDraft -q .isDraft\n' "$wanted" >&2
  fi
  # Viewing a release is read-only, so dry runs use the real state instead of
  # guessing; otherwise a dry run could suggest deleting a published tag.
  if ! state=$("$GH" release view "$wanted" --json isDraft -q .isDraft 2>/dev/null); then
    printf 'missing\n'
    return 0
  fi
  if [[ $state == true ]]; then
    printf 'draft\n'
  else
    printf 'published\n'
  fi
}

latest_assets() {
  if [[ $DRY_RUN == 1 ]]; then
    printf '# gh release view latest --json assets -q .assets[].name\n' >&2
  fi
  "$GH" release view latest --json assets -q '.assets[].name' 2>/dev/null || true
}

release_asset_names() {
  local wanted=$1
  if [[ $DRY_RUN == 1 ]]; then
    printf '# gh release view %s --json assets -q .assets[].name\n' "$wanted" >&2
  fi
  "$GH" release view "$wanted" --json assets -q '.assets[].name'
}

expect_asset_names() {
  local wanted=$1 listed
  listed="$(release_asset_names "$wanted")"
  printf '%s\n' "${expected[@]}" | LC_ALL=C sort > "$notes_dir/expected-names"
  # README.md is long-standing release documentation on the rolling release.
  # It is neither a build artifact nor required; any other extra asset fails.
  if [[ $wanted == latest ]]; then
    printf '%s\n' "$listed" | grep -v '^README\.md$' > "$notes_dir/actual-names" || true
  else
    printf '%s\n' "$listed" > "$notes_dir/actual-names"
  fi
  LC_ALL=C sort -o "$notes_dir/actual-names" "$notes_dir/actual-names"
  if ! diff -u "$notes_dir/expected-names" "$notes_dir/actual-names"; then
    die "asset list for $wanted does not match the expected current artifacts"
  fi
  note "asset names verified for $wanted (${#expected[@]} files)"
}

verify_published_assets() {
  local dir="$notes_dir/download"
  mkdir -p "$dir"
  if [[ $DRY_RUN == 1 ]]; then
    printf '# gh release download %s --repo %s --pattern SHA256SUMS --dir %q --clobber\n' \
      "$tag" "$GH_REPO" "$dir" >&2
    printf '# gh release download %s --repo %s --dir %q --clobber\n' \
      "$tag" "$GH_REPO" "$dir" >&2
    note "sha256sum -c SHA256SUMS; SHA256SUMS must list exactly the ${#expected[@]} attached files"
    return 0
  fi
  "$GH" release download "$tag" --repo "$GH_REPO" --pattern SHA256SUMS \
    --dir "$dir" --clobber
  "$GH" release download "$tag" --repo "$GH_REPO" --dir "$dir" --clobber
  awk '{print $2}' "$dir/SHA256SUMS" | LC_ALL=C sort > "$dir/listed-names"
  # A checksum manifest never lists itself, but every other line must be an
  # asset attached to this release.
  printf '%s\n' "${expected[@]}" | grep -v '^SHA256SUMS$' | LC_ALL=C sort > "$dir/expected-names"
  if ! diff -u "$dir/expected-names" "$dir/listed-names"; then
    die "SHA256SUMS in $tag lists files that are not attached to the release"
  fi
  if ! (cd "$dir" && sha256sum -c SHA256SUMS); then
    die "published asset checksum verification failed for $tag"
  fi
  note "published asset checksums verified for $tag"
}

version_state="$(release_state "$tag")"
latest_state="$(release_state latest)"

draft_created=0
cleanup_exit() {
  local status=$?
  trap - EXIT
  if [[ $draft_created == 1 ]]; then
    if ! run_gh release delete "$tag" -y --cleanup-tag; then
      printf 'ERROR: could not clean up failed release %s\n' "$tag" >&2
    fi
  fi
  exit "$status"
}
trap cleanup_exit EXIT

if [[ $version_state == published ]]; then
  note "${tag} is published; versioned releases are immutable, only refreshing latest"
else
  if [[ $version_state == draft ]]; then
    note "discarding stale draft release ${tag} so this run can retry cleanly"
    run_gh release delete "$tag" -y --cleanup-tag
  elif [[ -n $(git tag --list "$tag") ]]; then
    # A local tag without a release is an incomplete previous attempt.
    run_git tag -d "$tag"
  fi

  draft_created=1
  run_gh release create "$tag" --draft --target "$SHA" --title "mcmusic $version" \
    --notes-file "$version_notes" --latest=false
  run_gh release upload "$tag" "${assets[@]}"
  expect_asset_names "$tag"
  run_gh release edit "$tag" --draft=false --latest=false
  verify_published_assets
  draft_created=0
fi

if [[ $latest_state == draft ]]; then
  note 'latest is a draft; discarding it before recreating the rolling release'
  run_gh release delete latest -y --cleanup-tag
  latest_state=missing
fi

# Move the tag only after create-vs-edit was decided from the release itself.
run_git tag -f latest "$SHA"
run_git push -f "$REMOTE" latest

declare -a current_names=()
for f in "${assets[@]}"; do
  current_names+=("$(basename "$f")")
done

while IFS= read -r old; do
  [[ -n $old ]] || continue
  # README.md is release documentation, not a stale build artifact.
  [[ $old == README.md ]] && continue
  for current in "${current_names[@]}"; do
    [[ $old == "$current" ]] && continue 2
  done
  run_gh release delete-asset latest "$old" -y
done < <(latest_assets)

if [[ $latest_state == published ]]; then
  run_gh release edit latest --title "mcmusic latest ($version)" \
    --notes-file "$latest_notes" --latest
else
  run_gh release create latest --target "$SHA" --title "mcmusic latest ($version)" \
    --notes-file "$latest_notes" --latest
fi
run_gh release upload latest "${assets[@]}" --clobber
expect_asset_names latest

if [[ $DRY_RUN == 1 ]]; then
  note "gh api repos/${GH_REPO}/releases/latest -q .tag_name (must be latest)"
else
  actual="$("$GH" api "repos/${GH_REPO}/releases/latest" -q .tag_name)"
  [[ $actual == latest ]] || die "GitHub Latest is '$actual', expected 'latest'"
  note "GitHub Latest verified: $actual"
fi
