#!/usr/bin/env bash
# Cut a GitHub Release from the builds already sitting in apps/.
#
#   ./scripts/release.sh              # build the APK, publish, release it
#   ./scripts/release.sh --no-build   # release what is already in apps/
#   ./scripts/release.sh --draft      # create it hidden, publish by hand later
#
# Every artifact in the release is the same file the website links to. The
# script never commits binaries — apps/ is ignored on purpose.
set -euo pipefail
cd "$(dirname "$0")/.."

build=1
draft=0
notes_file=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-build) build=0 ;;
    --draft) draft=1 ;;
    --notes) notes_file="${2:?--notes needs a file}"; shift ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' app/android/app/build.gradle.kts | head -1)
version=${version:-0.0.0}
tag="v${version}"
sha=$(git rev-parse --short=12 HEAD 2>/dev/null || echo unknown)

if [ "$build" = 1 ]; then
  echo "→ building Android $version"
  (
    cd app/android
    JAVA_HOME="$PWD/.toolchain/jdk" \
    PATH="$PWD/.toolchain/jdk/bin:$PATH" \
      .toolchain/gradle/bin/gradle -p . assembleDebug --console=plain --offline
  )
fi

./scripts/publish_apps.sh

files=()
add() { [ -f "$1" ] && files+=("$1"); return 0; }

add "apps/android/mcmusic-${version}.apk"
for f in apps/linux/*.AppImage apps/linux/*.deb; do add "$f"; done
if [ ${#files[@]} -eq 0 ]; then
  echo "nothing to release: no builds in apps/" >&2
  exit 1
fi

# Checksums let someone verify the download without trusting the CDN.
( cd apps && sha256sum $(for f in "${files[@]}"; do echo "${f#apps/}"; done) > SHA256SUMS )

notes="${notes_file:-}"
if [ -z "$notes" ]; then
  notes=$(mktemp)
  {
    echo "## mcmusic ${version}"
    echo
    echo "Source: \`${sha}\`"
    echo
    echo "| Build | Size | File |"
    echo "| --- | --- | --- |"
    for f in "${files[@]}"; do
      name=$(basename "$f")
      size=$(du -h "$f" | cut -f1)
      echo "| ${name##*.} | ${size} | \`${name}\` |"
    done
    echo
    echo "Android installs over the current copy; nothing is wiped."
    echo "Linux AppImage: \`chmod +x\` then run. deb: \`sudo apt install ./file.deb\`."
    echo
    echo "The same files are served at https://mcmusic.sdisk.us/apps/ — and"
    echo "\`/get\` always redirects to the newest Android build."
  } > "$notes"
fi

args=(release create "$tag" "${files[@]}" "apps/SHA256SUMS"
      --title "mcmusic ${version}" --notes-file "$notes")
[ "$draft" = 1 ] && args+=(--draft)

if gh release view "$tag" >/dev/null 2>&1; then
  echo "→ release $tag exists; uploading the new files over it"
  gh release upload "$tag" "${files[@]}" "apps/SHA256SUMS" --clobber
else
  echo "→ creating release $tag"
  gh "${args[@]}"
fi

echo "→ https://github.com/mc20000-01/mcmusic/releases/tag/${tag}"
