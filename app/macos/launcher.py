#!/usr/bin/env python3
"""Frozen-app entry point for the macOS build.

PyInstaller imports this file, not the checkout's ``mcmusic-desktop`` script.
When running from a source tree it falls back to ``app/linux`` so the same
launcher is useful before a build.
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
