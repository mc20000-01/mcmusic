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

android_version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' gui/android/app/build.gradle.kts 2>/dev/null | head -1 || true)
desktop_version=$(PYTHONPATH=app/linux python3 -c 'from mcmusic_linux.version import FALLBACK_VERSION; print(FALLBACK_VERSION)' 2>/dev/null || true)
version=${android_version:-${desktop_version:-0.0.0}}
tag="v${version}"
sha=$(git rev-parse --short=12 HEAD 2>/dev/null || echo unknown)

if [ "$build" = 1 ]; then
  echo "→ building Android $android_version"
  repo=$PWD
  rm -f gui/android/app/build/outputs/apk/release/app-release.apk
  (
    cd gui/android
    JAVA_HOME="$repo/.toolchain/jdk" \
    ANDROID_HOME="$repo/.toolchain/sdk" \
    ANDROID_SDK_ROOT="$repo/.toolchain/sdk" \
    PATH="$repo/.toolchain/jdk/bin:$PATH" \
      "$repo/.toolchain/gradle/bin/gradle" -p . :app:assembleRelease --console=plain --offline
  )
fi

./scripts/publish_apps.sh

files=()
add() { [ -f "$1" ] && files+=("$1"); return 0; }

add "apps/android/mcmusic-${android_version}.apk"
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
    if [ -n "$android_version" ]; then echo "Android installs over the current copy; nothing is wiped."; fi
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
