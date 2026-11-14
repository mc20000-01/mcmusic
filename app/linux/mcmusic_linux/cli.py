"""Entry point for the Linux client: pick a front end before importing one.

``--tui`` starts the terminal client, ``--gui`` (or no flag at all) starts the
Qt window. The dispatch lives here, outside ``app.py`` and ``tui.py``, so the
GUI never has to be importable for the TUI to start: the terminal mode runs on
a bare Python 3 install with no Qt and no third-party packages.
"""
from __future__ import annotations

import sys

TUI_FLAGS = {"--tui", "--terminal", "-T"}
GUI_FLAGS = {"--gui", "-G"}

USAGE = """\
mcmusic desktop client

usage: mcmusic-desktop [--gui | --tui] [options]

front ends
  --gui, -G        Qt 6 window (default when no flag is given)
  --tui, --terminal, -T
                   terminal client; needs no Qt and no display

options
  --server URL     server to use (terminal mode; the GUI has a field for it)
  -h, --help       show this message
"""


def _split(args: list[str]) -> tuple[str, list[str], list[str]]:
    """Return ``(mode, gui_args, tui_args)`` for the arguments after argv[0]."""
    mode = "gui"
    gui: list[str] = []
    tui: list[str] = []
    for arg in args:
        if arg in TUI_FLAGS:
            mode = "tui"
        elif arg in GUI_FLAGS:
            mode = "gui"
        else:
            gui.append(arg)
            tui.append(arg)
    return mode, gui, tui


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv if argv is None else argv)
    program = raw[0] if raw else "mcmusic-desktop"
    args = raw[1:]

    if "-h" in args or "--help" in args:
        print(USAGE, end="")
        return 0

    mode, gui_args, tui_args = _split(args)

    if mode == "tui":
        from .tui import main as tui_main
        return tui_main(tui_args)

    from .app import run_gui
    return run_gui([program, *gui_args])
