#!/usr/bin/env python3
"""Frozen-app entry point for the Windows build.

The shared client lives in ``app/linux``; the launcher only exists so both the
macOS and Windows bundles have a stable PyInstaller entry point. Running this
from a checkout also works.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SIBLING = os.path.abspath(os.path.join(_HERE, "..", "linux"))

if not getattr(sys, "frozen", False) and os.path.isdir(_SIBLING):
    sys.path.insert(0, _SIBLING)

from mcmusic_linux.cli import main  # noqa: E402

raise SystemExit(main())
