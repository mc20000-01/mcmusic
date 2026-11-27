#!/usr/bin/env bash
# Build the APK, refresh apps/ + builds/, then publish through the same
# immutable release script CI uses.
#
#   ./scripts/release.sh              # build the APK, publish, release it
#   ./scripts/release.sh --no-build   # release what is already in apps/
#
# Every artifact in the release is the same file the website links to. The
# script never commits binaries — apps/ and builds/ are ignored on purpose;
# only the small text manifest is tracked.
set -euo pipefail
cd "$(dirname "$0")/.."

build=1
while [ $# -gt 0 ]; do
  case "$1" in
    --no-build) build=0 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

android_version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' gui/android/app/build.gradle.kts 2>/dev/null | head -1 || true)

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
./scripts/publish-release.sh
