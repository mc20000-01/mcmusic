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

android_version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' app/android/app/build.gradle.kts | head -1)
android_version=${android_version:-dev}
desktop_version=$(grep -oP '^version\s*=\s*"\K[^"]+' app/linux/pyproject.toml | head -1)
desktop_version=${desktop_version:-0.0.0}

apk_src=app/android/app/build/outputs/apk/debug/app-debug.apk
deb_src="apps/linux/mcmusic-desktop_${desktop_version}_all.deb"

# Keep the folder to the current builds instead of a growing museum.
find builds -maxdepth 1 -name 'mcmusic-desktop_*_all.deb' -delete
find builds -maxdepth 1 -name 'mcmusic-linux-source.zip' -delete

# CI without the original debug keystore must not replace the working APK:
# a freshly generated key has a different signature and Android refuses the
# update. In that mode the committed APK is the one that ships.
if [ "${MCMUSIC_KEEP_APK:-0}" = "1" ]; then
  echo "keeping the committed Android APK (MCMUSIC_KEEP_APK=1)"
else
  find builds -maxdepth 1 -name 'mcmusic-*.apk' -delete
  if [ -f "$apk_src" ]; then
    cp "$apk_src" "builds/mcmusic-${android_version}.apk"
    echo "collected builds/mcmusic-${android_version}.apk"
  else
    echo "no Android APK at $apk_src" >&2
  fi
fi

if [ -f "$deb_src" ]; then
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
