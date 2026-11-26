#!/usr/bin/env bash
# Publish the rolling "latest" release and an immutable v<version> snapshot.
#
#   ./scripts/publish-release.sh          # publish from builds/
#   DRY_RUN=1 ./scripts/publish-release.sh  # print every gh/git command only
#
# The desktop version.py is the source of truth. Android versionName must agree;
# a mixed-version release would make the update checks lie, so that is fatal.
# versioned releases are snapshots: an existing tag is never overwritten.
set -euo pipefail

DRY_RUN="${DRY_RUN:-0}"
GH="${GH:-gh}"
GH_REPO="${GITHUB_REPOSITORY:-${GH_REPO:-mc20000-01/mcmusic}}"
SHA="${GITHUB_SHA:-$(git rev-parse HEAD)}"
REMOTE="${REMOTE:-origin}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${VERSION_FILE:-$ROOT/app/linux/mcmusic_linux/version.py}"
ANDROID_VERSION_FILE="${ANDROID_VERSION_FILE:-$ROOT/gui/android/app/build.gradle.kts}"
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

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

version="$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$VERSION_FILE" 2>/dev/null | head -1 || true)"
[[ -n $version ]] || die "could not read FALLBACK_VERSION from $VERSION_FILE"

android_version="$(sed -n 's/.*versionName[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$ANDROID_VERSION_FILE" 2>/dev/null | head -1 || true)"
[[ -n $android_version ]] || die "could not read Android versionName from $ANDROID_VERSION_FILE"
[[ $android_version == "$version" ]] || \
  die "version mismatch: version.py=$version but Android versionName=$android_version"

tag="v${version}"

# Only this run's artifacts. Old APKs stay in builds/ for rollback but are not
# attached to either release, and README.md is repo documentation, not a build.
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
  if [[ -f $BUILD_DIR/$name ]]; then
    assets+=("$BUILD_DIR/$name")
  else
    note "WARNING: $name is missing from $BUILD_DIR; skipping it"
  fi
done
((${#assets[@]} > 0)) || die "no current-version artifacts found in $BUILD_DIR"

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
    printf '| `%s` | %s | `%s` |\n' "$base" "$size" "$sum"
  done
}

previous_tag="$(git tag --list 'v[0-9]*' --sort=-version:refname \
  | grep -v "^${tag}$" | head -1 || true)"
changes() {
  if [[ -n $previous_tag ]]; then
    git log --pretty=format:'- %s (%h)' "${previous_tag}..${SHA}" 2>/dev/null || true
  else
    git log --pretty=format:'- %s (%h)' -n 12 "$SHA" 2>/dev/null || true
  fi
}

{
  echo "## mcmusic latest (${version})"
  echo
  echo "Current version: **${version}**. See [${tag}](https://github.com/${GH_REPO}/releases/tag/${tag}) for the immutable snapshot."
  echo
  echo "Built from \`${SHA:0:12}\`."
  echo
  artifact_table
  echo
  echo '### Recent changes'
  changes
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
  changes
  echo
} > "$version_notes"

tag_exists() {
  local wanted=$1
  if [[ -n $(git tag --list "$wanted") ]]; then
    return 0
  fi
  if [[ $DRY_RUN == 1 ]]; then
    return 1
  fi
  git ls-remote --exit-code --tags "$REMOTE" "refs/tags/$wanted" >/dev/null 2>&1
}

latest_assets() {
  if [[ $DRY_RUN == 1 ]]; then
    # stderr keeps this diagnostic out of the captured asset-name list.
    printf '# gh release view latest --json assets -q .assets[].name\n' >&2
    return 0
  fi
  "$GH" release view latest --json assets -q '.assets[].name' 2>/dev/null || true
}

# Move the tag first: gh release edit cannot move a release tag, and the
# fallback server reads releases/latest, which must resolve to this commit.
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

if tag_exists "$tag"; then
  note "${tag} already exists, only refreshing latest (versioned releases are immutable)"
else
  run_gh release create "$tag" --target "$SHA" --title "mcmusic $version" \
    --notes-file "$version_notes" --latest=false
  run_gh release upload "$tag" "${assets[@]}"
fi

if tag_exists latest; then
  run_gh release edit latest --title "mcmusic latest ($version)" \
    --notes-file "$latest_notes" --latest
else
  run_gh release create latest --target "$SHA" --title "mcmusic latest ($version)" \
    --notes-file "$latest_notes" --latest
fi
run_gh release upload latest "${assets[@]}" --clobber

if [[ $DRY_RUN == 1 ]]; then
  note "gh api repos/${GH_REPO}/releases/latest -q .tag_name (must be latest)"
else
  actual="$("$GH" api "repos/${GH_REPO}/releases/latest" -q .tag_name)"
  [[ $actual == latest ]] || die "GitHub Latest is '$actual', expected 'latest'"
  note "GitHub Latest verified: $actual"
fi
