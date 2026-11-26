"""Update discovery, download and hand-off for the native desktop client.

Every client reads the same ``/api/builds`` registry. This module turns that
registry into one concrete artifact for the running OS, downloads it into the
per-user cache, verifies the bytes published by the server, and opens the
result with the desktop's normal handler. It never replaces a running app:
macOS DMGs mount, Linux .debs hand off to the package manager, and portable
AppImages/ZIPs are revealed in the file manager.
"""
from __future__ import annotations

import hashlib
import os
import platform
import re
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import parse_qs, urlsplit

import requests
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

from .models import BuildInfo
from .paths import cache_dir
from .version import USER_AGENT

_VERSION = re.compile(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)")
_HEX = re.compile(r"^[0-9a-f]+$", re.I)


def version_tuple(value: str) -> tuple[int, ...]:
    """Numeric components of a dotted version; () means 'not a version'.

    Build names such as ``mcmusic-x86_64.AppImage`` contain numbers but no
    dotted client version. Treating those as 86.64 would make every AppImage
    look perpetually newer than 4.1.0, so they are deliberately unversioned.
    """
    match = _VERSION.search(str(value or ""))
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(candidate: str, current: str) -> bool:
    """True when *candidate* is a strictly newer dotted version."""
    new = version_tuple(candidate)
    old = version_tuple(current)
    if not new:
        return False
    width = max(len(new), len(old))
    new += (0,) * (width - len(new))
    old += (0,) * (width - len(old))
    return new > old


def platform_kinds(system: Optional[str] = None) -> tuple[str, ...]:
    """Kinds to consider, in the order the current platform should install."""
    system = system or platform.system()
    if system == "Darwin":
        return ("macos-dmg", "macos")
    if system == "Windows":
        return ("windows-zip", "windows")
    # AppImages self-identify through APPDIR/APPIMAGE; otherwise prefer the
    # distro package so the desktop launcher stays intact.
    if os.environ.get("APPIMAGE") or os.environ.get("APPDIR"):
        return ("linux-appimage", "linux-deb")
    return ("linux-deb", "linux-appimage")


def find_update(builds: Iterable[BuildInfo], current: str,
                system: Optional[str] = None) -> Optional[BuildInfo]:
    """Pick the newest installable artifact for this platform, if any."""
    kinds = platform_kinds(system)
    rank = {kind: index for index, kind in enumerate(kinds)}
    candidates = [
        build for build in builds
        if build.available and build.kind in rank
        and is_newer(build.version, current) and build.url and build.file
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda b: (rank[b.kind], version_tuple(b.version)))


def absolute_url(base_url: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def updates_dir() -> Path:
    path = cache_dir() / "updates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _expected_digest(url: str) -> str:
    query = parse_qs(urlsplit(url).query)
    values = query.get("v") or []
    digest = values[0].lower() if values else ""
    return digest if _HEX.match(digest) else ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified(path: Path, digest: str, size: int) -> bool:
    if not path.is_file():
        return False
    if digest and not _sha256(path).startswith(digest):
        return False
    return not size or path.stat().st_size == size


def download(build: BuildInfo, base_url: str,
             progress: Optional[Callable[[int, int], None]] = None) -> Path:
    """Stream one build into the update cache and verify what was served.

    The server's ``?v=`` query carries the first 16 hex digits of its SHA-256.
    A truncated download, an edge-cache mix-up or a corrupt copy therefore
    fails the build before it is handed to the user.
    """
    url = absolute_url(base_url, build.url)
    digest = _expected_digest(url)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(build.file).name)
    tag = (digest[:8] or build.version or "latest")
    destination = updates_dir() / f"{tag}-{name}"
    if _verified(destination, digest, build.bytes):
        return destination

    partial = destination.with_suffix(destination.suffix + ".part")
    response = requests.get(
        url, stream=True, timeout=(15, 120),
        headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
    )
    response.raise_for_status()
    declared = response.headers.get("Content-Length")
    try:
        total = int(declared) if declared and declared.isdigit() else build.bytes or 0
        written = 0
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                handle.write(chunk)
                written += len(chunk)
                if progress:
                    progress(written, total)
        if total and written != total:
            raise IOError(f"Incomplete download: got {written} of {total} bytes")
        if not _verified(partial, digest, written):
            raise IOError("Downloaded build failed its checksum")
        os.replace(partial, destination)
    finally:
        response.close()
        if partial.exists():
            partial.unlink()

    if build.kind == "linux-appimage" or destination.name.endswith(".AppImage"):
        mode = destination.stat().st_mode
        destination.chmod(mode | 0o111)
    return destination


def open_installer(path: Path, system: Optional[str] = None) -> bool:
    """Open the artifact with the OS shell; portable bundles open their folder."""
    system = system or platform.system()
    reveal = (
        (system == "Windows")
        or (system == "Linux" and str(path).lower().endswith(".appimage"))
    )
    target = path.parent if reveal else path
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
