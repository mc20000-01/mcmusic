"""Public build fallback from the rolling GitHub Release.

A self-hosted server does not have to compile every client. When a local
artifact is missing, this module downloads the exact bytes from the public
`latest` release into apps/ so /api/builds, /apps/... and /downloads keep
working. Local builds still win until the next sync; GitHub is the fallback
and the source of truth for a fresh install.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from config import PROJECT_DIR

REPO = os.environ.get("MCMUSIC_GITHUB_REPO", "mc20000-01/mcmusic").strip("/")
RELEASE = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOADS = f"https://github.com/{REPO}/releases/download/latest"
APPS = os.path.join(PROJECT_DIR, "apps")
CACHE_SECONDS = 300
SYNC_SECONDS = 600
UA = "mcmusic-selfhost/1.0"

_log = logging.getLogger(__name__)
_lock = threading.RLock()
_cached: tuple[float, list[dict]] | None = None
_sync_started = False

# Asset name -> directory inside apps/ and the stable alias every API points at.
ASSETS: dict[str, tuple[str, str]] = {
    "android": ("android", "mainbuild.apk"),
    "linux-appimage": ("linux", "mcmusic-x86_64.AppImage"),
    "linux-deb": ("linux", "mainbuild.deb"),
    "macos": ("macos", "mainbuild.zip"),
    "macos-dmg": ("macos", "mainbuild.dmg"),
    "windows": ("windows", "mainbuild.zip"),
    "windows-zip": ("windows", "mainbuild.zip"),
    "linux-source": ("linux", "mcmusic-linux-source.zip"),
}

_APK = re.compile(r"^mcmusic-\d[\w.-]*\.apk$", re.I)
_APPIMAGE = re.compile(r"^mcmusic-x86_64\.AppImage$", re.I)
_DEB = re.compile(r"^mcmusic-desktop_.+_all\.deb$", re.I)
_MACOS_ZIP = re.compile(r"^mcmusic-macos-.+\.zip$", re.I)
_MACOS_DMG = re.compile(r"^mcmusic-.+\.dmg$", re.I)
_WINDOWS_ZIP = re.compile(r"^mcmusic-windows-.+\.zip$", re.I)
_SOURCE_ZIP = re.compile(r"^mcmusic-linux-source\.zip$", re.I)


def _request(url: str, timeout: int = 20, accept: str = "application/json") -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": accept},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def assets(force: bool = False) -> list[dict]:
    """Assets on the public latest release; cached briefly and failure-tolerant."""
    global _cached
    with _lock:
        now = time.monotonic()
        if not force and _cached and now - _cached[0] < CACHE_SECONDS:
            return _cached[1]
    try:
        raw = json.loads(_request(RELEASE, timeout=15).decode("utf-8"))
        rows = []
        for a in raw.get("assets", []):
            name = str(a.get("name") or "")
            digest = str(a.get("digest") or "")
            rows.append({
                "name": name,
                "url": str(a.get("browser_download_url") or f"{DOWNLOADS}/{name}"),
                "size": int(a.get("size") or 0),
                "digest": digest.split(":", 1)[-1] if digest.startswith("sha256:") else digest,
                "created": str(a.get("created_at") or a.get("updated_at") or ""),
            })
        with _lock:
            _cached = (time.monotonic(), rows)
        return rows
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        _log.warning("GitHub release lookup failed: %s", exc)
        with _lock:
            return _cached[1] if _cached else []


def kind_for(name: str) -> str | None:
    if _APK.match(name):
        return "android"
    if _APPIMAGE.match(name):
        return "linux-appimage"
    if _DEB.match(name):
        return "linux-deb"
    if _MACOS_ZIP.match(name):
        return "macos"
    if _MACOS_DMG.match(name):
        return "macos-dmg"
    if _WINDOWS_ZIP.match(name):
        return "windows"
    if _SOURCE_ZIP.match(name):
        return "linux-source"
    if name in ("README.md", "SHA256SUMS"):
        return "checksums"
    return None


def match(kind: str) -> dict | None:
    """Latest release asset for one build kind."""
    wanted = kind_for(kind) or kind
    for asset in assets():
        if kind_for(asset["name"]) == wanted:
            return asset
    return None


def match_path(rel: str) -> dict | None:
    """Find the release asset that satisfies a missing /apps/<path> request."""
    rel = rel.replace("\\", "/").strip("/")
    name = os.path.basename(rel)
    folder = os.path.dirname(rel).lower()
    kind = None
    if name in ("mainbuild.apk",) or _APK.match(name) or re.match(r"^mainbuild-[0-9a-f]{16}\.apk$", name):
        kind = "android"
    elif name.lower().endswith(".appimage"):
        kind = "linux-appimage"
    elif name.lower().endswith(".deb"):
        kind = "linux-deb"
    elif name.lower().endswith(".dmg"):
        kind = "macos-dmg"
    elif _MACOS_ZIP.match(name) or (name == "mainbuild.zip" and folder == "macos"):
        kind = "macos"
    elif _WINDOWS_ZIP.match(name) or (name == "mainbuild.zip" and folder == "windows"):
        kind = "windows"
    elif _SOURCE_ZIP.match(name) or (name == "mainbuild.zip" and folder == "linux"):
        kind = "linux-source"
    elif name in ("README.md", "SHA256SUMS"):
        kind = "checksums"
    if not kind:
        return None
    # A requested versioned filename must not be answered with another version.
    for asset in assets():
        if kind_for(asset["name"]) != kind:
            continue
        if re.match(r"^mcmusic-\d[\w.-]*\.apk$", name) or _MACOS_ZIP.match(name) \
                or _WINDOWS_ZIP.match(name) or _MACOS_DMG.match(name) or _DEB.match(name):
            if asset["name"] != name:
                continue
        return asset
    return None


def destinations(asset: dict) -> list[str]:
    """Local files that should contain these exact bytes."""
    name = asset["name"]
    kind = kind_for(name)
    if not kind or kind == "checksums":
        folder = "android" if name.endswith(".apk") else "linux"
        return [os.path.join(APPS, folder, name)]
    folder, stable = ASSETS[kind]
    paths = [os.path.join(APPS, folder, name)]
    if stable != name:
        paths.append(os.path.join(APPS, folder, stable))
    digest = asset.get("digest") or ""
    if re.fullmatch(r"[0-9a-f]{16,64}", digest):
        ext = os.path.splitext(name)[1]
        paths.append(os.path.join(APPS, folder, f"mainbuild-{digest[:16]}{ext}"))
    return list(dict.fromkeys(paths))


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fresh(path: str, asset: dict) -> bool:
    if not os.path.isfile(path):
        return False
    if asset.get("size") and os.path.getsize(path) != asset["size"]:
        return False
    digest = asset.get("digest") or ""
    return bool(digest) and _sha256(path) == digest


def download(asset: dict, force: bool = False) -> bool:
    """Download one release asset into apps/, verifying GitHub's sha256."""
    target = destinations(asset)[0]
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with _lock:
        if not force and _fresh(target, asset):
            return True
        temp = target + ".download"
        try:
            req = urllib.request.Request(
                asset["url"], headers={"User-Agent": UA, "Accept": "application/octet-stream"}
            )
            with urllib.request.urlopen(req, timeout=180) as resp, open(temp, "wb") as fh:
                shutil.copyfileobj(resp, fh, 1024 * 1024)
            digest = asset.get("digest") or ""
            if digest and _sha256(temp) != digest:
                raise ValueError(f"checksum mismatch for {asset['name']}")
            os.replace(temp, target)
            for extra in destinations(asset)[1:]:
                os.makedirs(os.path.dirname(extra), exist_ok=True)
                tmp = extra + ".download"
                shutil.copyfile(target, tmp)
                os.replace(tmp, extra)
            _log.info("pulled %s from GitHub Release", asset["name"])
            return True
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            _log.warning("could not pull %s: %s", asset["name"], exc)
            try:
                if os.path.exists(temp):
                    os.remove(temp)
            except OSError:
                pass
            return False


def ensure(kind: str) -> bool:
    asset = match(kind)
    return bool(asset and download(asset))


def ensure_path(rel: str) -> bool:
    asset = match_path(rel)
    return bool(asset and download(asset))


def sync(force: bool = False) -> int:
    """Pull every public client into apps/; returns the number refreshed."""
    count = 0
    for asset in assets(force=force):
        if not kind_for(asset["name"]):
            continue
        if download(asset, force=force):
            count += 1
    return count


def start_sync() -> None:
    """Background refresh, so a fresh server fills itself without a build."""
    global _sync_started
    with _lock:
        if _sync_started:
            return
        _sync_started = True

    def loop():
        while True:
            try:
                sync()
            except Exception:
                _log.exception("GitHub build sync failed")
            time.sleep(SYNC_SECONDS)

    threading.Thread(target=loop, name="github-build-sync", daemon=True).start()


def built_stamp(asset: dict) -> str:
    raw = asset.get("created") or ""
    try:
        when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return when.astimezone(timezone.utc).strftime("%d %b %Y")
    except ValueError:
        return "GitHub Release"
