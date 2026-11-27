#!/usr/bin/env bash
# Verify every checked-in version source agrees with the desktop source of truth.
#
#   ./scripts/check-versions.sh
#
# Called by CI and by scripts/publish-release.sh. A mixed-version release makes
# the native update checks lie, so every mismatch is fatal here. The web
# manifest and a root package.json are checked only when they declare a version;
# they currently do not, so they are reported as skipped rather than invented.
set -euo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
VERSION_FILE="${VERSION_FILE:-$ROOT/app/linux/mcmusic_linux/version.py}"
ANDROID_FILE="${ANDROID_FILE:-$ROOT/gui/android/app/build.gradle.kts}"
IOS_FILE="${IOS_FILE:-$ROOT/app/ios/project.yml}"
UI_PACKAGE="${UI_PACKAGE:-$ROOT/ui/package.json}"
WEB_MANIFEST="${WEB_MANIFEST:-$ROOT/web/manifest.webmanifest}"
ROOT_PACKAGE="${ROOT_PACKAGE:-$ROOT/package.json}"
BUILD_DIR="${BUILD_DIR:-$ROOT/builds}"

die() {
  printf '%s\n' "$*" >&2
  exit 1
}

version="$(sed -n 's/^FALLBACK_VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$VERSION_FILE" 2>/dev/null | head -1 || true)"
[[ -n $version ]] || die "could not read FALLBACK_VERSION from $VERSION_FILE"

android="$(sed -n 's/.*versionName[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$ANDROID_FILE" 2>/dev/null | head -1 || true)"
[[ -n $android ]] || die "could not read Android versionName from $ANDROID_FILE"

ios="$(sed -n 's/.*MARKETING_VERSION:[[:space:]]*"\([^"]*\)".*/\1/p' \
  "$IOS_FILE" 2>/dev/null | head -1 || true)"
[[ -n $ios ]] || die "could not read iOS MARKETING_VERSION from $IOS_FILE"

check() {
  local label=$1 value=$2
  if [[ $value != "$version" ]]; then
    die "version mismatch: version.py=$version but $label=$value"
  fi
  printf '%-28s %s\n' "$label" "$value"
}

check "version.py" "$version"
check "Android versionName" "$android"
check "iOS MARKETING_VERSION" "$ios"

optional_json_version() {
  local label=$1 file=$2 found
  [[ -f $file ]] || {
    printf '%-28s absent\n' "$label"
    return 0
  }
  found="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$file" 2>/dev/null | head -1 || true)"
  if [[ -z $found ]]; then
    printf '%-28s no version field\n' "$label"
    return 0
  fi
  check "$label" "$found"
}

optional_json_version "ui/package.json" "$UI_PACKAGE"
optional_json_version "web/manifest.webmanifest" "$WEB_MANIFEST"
optional_json_version "package.json" "$ROOT_PACKAGE"

deb_file="${DEB_FILE:-}"
if [[ -z $deb_file ]]; then
  for candidate in \
    "$BUILD_DIR/mcmusic-desktop_${version}_all.deb" \
    "$ROOT/apps/linux/mcmusic-desktop_${version}_all.deb" \
    "$ROOT/apps/linux/mainbuild.deb"; do
    if [[ -f $candidate ]]; then
      deb_file=$candidate
      break
    fi
  done
fi

if [[ -n $deb_file && -f $deb_file ]]; then
  if command -v dpkg-deb >/dev/null 2>&1 && [[ $(basename "$deb_file") != control ]]; then
    deb="$(dpkg-deb -f "$deb_file" Version)"
  else
    # A plain DEBIAN/control fixture is useful in hermetic tests.
    deb="$(sed -n 's/^Version:[[:space:]]*//p' "$deb_file" | head -1 || true)"
  fi
  [[ -n $deb ]] || die "could not read Version from $deb_file"
  check "deb control" "$deb"
else
  # A clean checkout has no built package. The tracked release manifest is a
  # small text record of the last published artifact set, so it can prove the
  # version without committing a binary. CI still builds a real .deb first and
  # therefore takes the branch above.
  manifest="${MANIFEST_FILE:-$BUILD_DIR/release-manifest.json}"
  [[ -f $manifest ]] || \
    die "could not find a .deb or release manifest to verify (set DEB_FILE or MANIFEST_FILE)"
  manifest_version="$(python3 -c \
    'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' \
    "$manifest" 2>/dev/null || true)"
  [[ -n $manifest_version ]] || die "could not read version from $manifest"
  check "release manifest" "$manifest_version"
fi

printf 'all version sources agree: %s\n' "$version"
