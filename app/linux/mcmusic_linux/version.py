"""Single source of truth for the desktop client version.

The installed package metadata is canonical; the constant is the fallback for
running straight from a source checkout (and for the packaging scripts, which
read this file before the package is installed).
"""
from __future__ import annotations

FALLBACK_VERSION = "4.2.0"


def app_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version
        return version("mcmusic-desktop")
    except (ImportError, PackageNotFoundError, ValueError):
        return FALLBACK_VERSION


VERSION = app_version()
USER_AGENT = f"mcmusic-desktop/{VERSION} (Qt)"
