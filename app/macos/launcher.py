#!/usr/bin/env python3
"""Frozen-app entry point for the macOS build.

PyInstaller imports this file, not the checkout's ``mcmusic-desktop`` script.
When running from a source tree it falls back to ``app/linux`` so the same
launcher is useful before a build.

The import is deliberately absolute: ``build.sh`` passes ``--paths`` and the
hidden/collect flags so PyInstaller bundles ``mcmusic_linux`` even when the
shared package was installed in editable mode.
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
            "Rebuild with app/macos/build.sh: it passes --paths, "
            "--hidden-import mcmusic_linux.cli and "
            "--collect-submodules mcmusic_linux to PyInstaller."
        ) from exc
    raise

raise SystemExit(main())
