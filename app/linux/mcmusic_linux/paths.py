"""Cross-platform locations for settings and cached audio.

Linux and macOS keep their XDG paths so existing installations are unchanged.
Windows uses ``%APPDATA%\\mcmusic`` for settings and ``%LOCALAPPDATA%\\mcmusic``
for cache files, matching ``app/windows/README.md``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP = "mcmusic"


def config_dir() -> Path:
    """Writable per-user directory for settings."""
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
    else:
        root = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(root) / APP


def cache_dir() -> Path:
    """Writable per-user directory for cached audio."""
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
    else:
        root = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(root) / APP


def settings_file() -> Path:
    """On-disk Qt settings file: native ``.conf`` on Unix, INI on Windows."""
    name = "mcmusic-desktop.ini" if sys.platform == "win32" else "mcmusic-desktop.conf"
    return config_dir() / name


def audio_cache_dir() -> Path:
    return cache_dir() / "audio"


def tui_config_file() -> Path:
    return config_dir() / "tui.json"


def tui_cache_dir() -> Path:
    return cache_dir() / "tui-audio"
