#!/usr/bin/env bash
# Publish built clients to /apps/... on the server.
#
# Three names land for each build, all the same bytes:
#   mainbuild.apk               stable link, always the newest
#   mcmusic-<version>.apk       readable, survives in the folder
#   mainbuild-<hash>.apk        content-addressed, safe to cache forever
# The web app reads /api/builds, which appends ?v=<mtime> so an edge cache
# can never hand out yesterday's file.
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p apps/android apps/linux

# The client lives in gui/android now; app/android is still honoured if it
# comes back. Release output wins because that is what ships.
android_dir=""
for candidate_dir in app/android gui/android; do
  if [ -f "$candidate_dir/app/build.gradle.kts" ]; then
    android_dir=$candidate_dir
    break
  fi
done
apk=""
if [ -n "$android_dir" ]; then
  for candidate in \
    "$android_dir/app/build/outputs/apk/release/app-release.apk" \
    "$android_dir/app/build/outputs/apk/debug/app-debug.apk"; do
    if [ -f "$candidate" ]; then
      apk=$candidate
      break
    fi
  done
fi
if [ -n "$apk" ] && [ -f "$apk" ]; then
  version=$(grep -oP 'versionName\s*=\s*"\K[^"]+' "$android_dir/app/build.gradle.kts" | head -1)
  version=${version:-dev}
  hash=$(sha256sum "$apk" | cut -c1-16)

  cp "$apk" apps/android/mainbuild.apk
  cp "$apk" "apps/android/mcmusic-${version}.apk"
  cp "$apk" "apps/android/mainbuild-${hash}.apk"

  # Keep the publish folder from turning into a museum: the ten newest
  # hash-named builds stay, older ones go.
  ls -1t apps/android/mainbuild-*.apk 2>/dev/null | tail -n +11 | xargs -r rm -f

  printf 'published apps/android/mainbuild.apk  (%s, v%s, %s)\n' \
    "$(du -h apps/android/mainbuild.apk | cut -f1)" "$version" "$hash"
else
  echo "no android apk yet (build gui/android with ./gradlew :app:assembleRelease)" >&2
fi

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
