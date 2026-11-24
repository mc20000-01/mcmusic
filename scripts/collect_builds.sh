#!/usr/bin/env bash
# Collect every shippable client into ./builds at the repo root.
#
#   ./scripts/collect_builds.sh
#
# Run by publish_apps.sh and by .github/workflows/release.yml, so the folder
# holds the same bytes that /api/builds and the GitHub Release serve. Only the
# current version of each artifact is replaced; one older APK is kept.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p builds

android_dir=gui/android
gradle_file="$android_dir/app/build.gradle.kts"
apk="$android_dir/app/build/outputs/apk/release/app-release.apk"
android_version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' "$gradle_file" | head -1 || true)
android_version=${android_version:-dev}
desktop_version=$(PYTHONPATH=app/linux python3 -c 'from mcmusic_linux.version import FALLBACK_VERSION; print(FALLBACK_VERSION)' 2>/dev/null || true)
desktop_version=${desktop_version:-0.0.0}

# Release output is the only thing that ships. A debug build must never be
# copied into a folder named after a release version.
if [ -f "$apk" ]; then
  sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$PWD/.toolchain/sdk}}"
  aapt=$(find "$sdk/build-tools" -type f -name aapt 2>/dev/null | sort -V | tail -n 1 || true)
  if [ -n "$aapt" ]; then
    badging=$("$aapt" dump badging "$apk" || true)
    apk_version=$(grep -m1 -o "versionName='[^']*'" <<<"$badging" | cut -d"'" -f2 || true)
    if [ "$apk_version" != "$android_version" ]; then
      echo "refusing to collect $apk: embedded version '$apk_version' != Gradle version '$android_version'" >&2
      exit 1
    fi
  fi
  cp "$apk" "builds/mcmusic-${android_version}.apk"
  echo "collected builds/mcmusic-${android_version}.apk"
else
  echo "no release APK at $apk (build gui/android with ./gradlew :app:assembleRelease)" >&2
fi

deb_src="apps/linux/mcmusic-desktop_${desktop_version}_all.deb"
if [ -f "$deb_src" ]; then
  find builds -maxdepth 1 -name 'mcmusic-desktop_*_all.deb' -delete
  cp "$deb_src" "builds/mcmusic-desktop_${desktop_version}_all.deb"
  echo "collected builds/mcmusic-desktop_${desktop_version}_all.deb"
else
  echo "no deb at $deb_src (run scripts/build_deb.sh first)" >&2
fi

if [ -f apps/linux/mainbuild.zip ]; then
  cp apps/linux/mainbuild.zip builds/mcmusic-linux-source.zip
  echo "collected builds/mcmusic-linux-source.zip"
fi

# A desktop AppImage is built on the maintainer's machine; keep the newest
# copy that is already present rather than pretending CI can produce one.
if [ -f mcmusic-x86_64.AppImage ]; then
  cp mcmusic-x86_64.AppImage builds/mcmusic-x86_64.AppImage
  echo "collected builds/mcmusic-x86_64.AppImage"
fi

(
  cd builds
  files=$(find . -maxdepth 1 -type f ! -name SHA256SUMS ! -name README.md -printf '%P\n' | sort)
  if [ -n "$files" ]; then
    # shellcheck disable=SC2086
    sha256sum $files > SHA256SUMS
    echo "wrote builds/SHA256SUMS"
  fi
)
