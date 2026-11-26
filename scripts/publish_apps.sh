#!/usr/bin/env bash
# Publish built clients to /apps/... on the server.
#
# Three names land for each build, all the same bytes:
#   mainbuild.apk               stable link, always the newest
#   mcmusic-<version>.apk       readable, survives in the folder
#   mainbuild-<hash>.apk        content-addressed, safe to cache forever
# The web app reads /api/builds, which appends ?v=<digest> so an edge cache
# can never hand out yesterday's file.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p apps/android apps/linux

android_dir=gui/android
gradle_file="$android_dir/app/build.gradle.kts"
apk="$android_dir/app/build/outputs/apk/release/app-release.apk"

if [ ! -f "$gradle_file" ]; then
  echo "missing $gradle_file" >&2
  exit 1
fi
if [ ! -f "$apk" ]; then
  echo "no release APK at $apk — run ./gradlew :app:assembleRelease first" >&2
  exit 1
fi

version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' "$gradle_file" | head -1)
if [ -z "$version" ]; then
  echo "could not read versionName from $gradle_file" >&2
  exit 1
fi

# Never publish a stale or differently signed APK under a new version name.
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$PWD/.toolchain/sdk}}"
aapt=$(find "$sdk/build-tools" -type f -name aapt 2>/dev/null | sort -V | tail -n 1 || true)
apksigner=$(find "$sdk/build-tools" -type f -name apksigner 2>/dev/null | sort -V | tail -n 1 || true)
if [ -z "$aapt" ] || [ -z "$apksigner" ]; then
  echo "Android build tools not found under $sdk (set ANDROID_HOME)" >&2
  exit 1
fi
badging=$("$aapt" dump badging "$apk" || true)
apk_version=$(grep -m1 -o "versionName='[^']*'" <<<"$badging" | cut -d"'" -f2 || true)
if [ "$apk_version" != "$version" ]; then
  echo "refusing to publish $apk: embedded version '$apk_version' != Gradle version '$version'" >&2
  exit 1
fi
signer=$("$apksigner" verify --print-certs "$apk" | tr '[:upper:]' '[:lower:]' || true)
expected=0b0fd0fa35ff712901d42cab215d5e3cb706daef57bffa7ebef61cacda1dc4ce
if ! grep -q "$expected" <<<"$signer"; then
  echo "refusing to publish $apk: unexpected signer certificate" >&2
  exit 1
fi

hash=$(sha256sum "$apk" | cut -c1-16)
cp "$apk" apps/android/mainbuild.apk
cp "$apk" "apps/android/mcmusic-${version}.apk"
cp "$apk" "apps/android/mainbuild-${hash}.apk"

# Keep the publish folder from turning into a museum: the ten newest
# hash-named builds and the current + one previous version stay.
newest() {
  # Retention applies only to the published apps/ folder, never to builds/.
  find apps/android -maxdepth 1 -type f -name "$1" -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr | tail -n "+$2" | cut -d' ' -f2- | xargs -r rm -f
}
newest 'mainbuild-*.apk' 11
newest 'mcmusic-*.apk' 3

printf 'published apps/android/mainbuild.apk  (%s, v%s, %s)\n' \
  "$(du -h apps/android/mainbuild.apk | cut -f1)" "$version" "$hash"

if [ -d app/linux ]; then
  python3 - <<'PY'
import pathlib, zipfile
root = pathlib.Path("app")
out = pathlib.Path("apps/linux/mainbuild.zip")
out.parent.mkdir(parents=True, exist_ok=True)
skip = {".venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".git"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted((root / "linux").rglob("*")):
        if p.is_file() and not any(part in skip for part in p.parts):
            z.write(p, p.relative_to(root))
print(f"published apps/linux/mainbuild.zip ({out.stat().st_size} bytes)")
PY
fi

./scripts/collect_builds.sh
