#!/usr/bin/env python3
"""Frozen-app entry point for the Windows build.

The shared client lives in ``app/linux``; the launcher only exists so both the
macOS and Windows bundles have a stable PyInstaller entry point. Running this
from a checkout also works.

The import is deliberately absolute: PyInstaller follows it and bundles
``mcmusic_linux``. ``build.ps1`` passes ``--paths`` and the hidden/collect
flags needed for an editable install to be resolved at analysis time.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SIBLING = os.path.abspath(os.path.join(_HERE, "..", "linux"))

if not getattr(sys, "frozen", False) and os.path.isdir(_SIBLING):
    sys.path.insert(0, _SIBLING)

try:
    from mcmusic_linux.cli import main  # noqa: E402
except ModuleNotFoundError as exc:
    if exc.name == "mcmusic_linux" or exc.name.startswith("mcmusic_linux."):
        raise SystemExit(
            "mcmusic could not find its bundled client module.\n"
            "Rebuild with app\\windows\\build.ps1: it passes --paths, "
            "--hidden-import mcmusic_linux.cli and "
            "--collect-submodules mcmusic_linux to PyInstaller."
        ) from exc
    raise

raise SystemExit(main())
