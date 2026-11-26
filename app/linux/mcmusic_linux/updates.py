"""Check ``/api/builds`` for a newer version of the desktop client.

This module is deliberately read-only: it compares published versions with the
running app and opens the server's public download page in the browser. It does
not download, verify, unpack or launch anything. Builds are unsigned, so a
download cannot be trusted merely because the server published a hash for it —
the user chooses and inspects the artifact in the browser instead.
"""
from __future__ import annotations

import os
import platform
import re
from typing import Iterable, Optional

from .models import BuildInfo

_VERSION = re.compile(r"(?<!\d)(\d+(?:\.\d+)+)(?!\d)")


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
    """Kinds to consider, in the order the current platform prefers."""
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
    """Pick the newest build for this platform, if any."""
    kinds = platform_kinds(system)
    rank = {kind: index for index, kind in enumerate(kinds)}
    candidates = [
        build for build in builds
        if build.available and build.kind in rank and is_newer(build.version, current)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda b: (rank[b.kind], version_tuple(b.version)))


def download_page(base_url: str) -> str:
    """The public, no-sign-in build list the user opens in their browser."""
    return f"{base_url.rstrip('/')}/downloads"
