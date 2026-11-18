#!/usr/bin/env bash
# Collect every shippable client into ./builds at the repo root.
#
#   ./scripts/collect_builds.sh
#
# Run by publish_apps.sh and by .github/workflows/release.yml, so the folder
# always holds the same bytes that /api/builds and the GitHub Release serve.
# Old versioned APK/deb snapshots are removed; one current copy of each stays.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p builds

# The Android client lives in gui/android (the backend and the clients are
# separate trees); app/android is still honoured when it comes back.
android_dir=""
android_version=""
for candidate_dir in app/android gui/android; do
  if [ -f "$candidate_dir/app/build.gradle.kts" ]; then
    android_dir=$candidate_dir
    android_version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' "$candidate_dir/app/build.gradle.kts" | head -1)
    break
  fi
done
android_version=${android_version:-dev}
desktop_version=$(grep -oP '^version\s*=\s*"\K[^"]+' app/linux/pyproject.toml | head -1)
desktop_version=${desktop_version:-0.0.0}

# Release output is what ships; a debug build is only a local fallback.
apk_src=""
for candidate_apk in \
  "$android_dir/app/build/outputs/apk/release/app-release.apk" \
  "$android_dir/app/build/outputs/apk/debug/app-debug.apk"; do
  if [ -n "$android_dir" ] && [ -f "$candidate_apk" ]; then apk_src=$candidate_apk; fi
done
deb_src="apps/linux/mcmusic-desktop_${desktop_version}_all.deb"

# Only replace an artifact when a fresh one was actually produced: a publish
# run without a deb step must not erase the copy people are downloading.

# Keep the APK copies side by side: phones only move forward, and old builds are
# the fallback when a new one misbehaves. Only the current version is replaced.
if [ -n "$apk_src" ] && [ -f "$apk_src" ]; then
  cp "$apk_src" "builds/mcmusic-${android_version}.apk"
  echo "collected builds/mcmusic-${android_version}.apk"
else
  echo "no Android APK found (build gui/android with ./gradlew :app:assembleRelease)" >&2
fi

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
