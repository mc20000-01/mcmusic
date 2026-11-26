"""Entry point for the Linux client: pick a front end before importing one.

``--tui`` starts the terminal client, ``--gui`` (or no flag at all) starts the
Qt window, and ``--selftest`` builds that window offscreen and exits. The
dispatch lives here, outside ``app.py`` and ``tui.py``, so the GUI never has to
be importable for the TUI to start: the terminal mode runs on a bare Python 3
install with no Qt and no third-party packages.
"""
from __future__ import annotations

import sys

TUI_FLAGS = {"--tui", "--terminal", "-T"}
GUI_FLAGS = {"--gui", "-G"}
SELFTEST_FLAGS = {"--selftest"}

USAGE = """\
mcmusic desktop client

usage: mcmusic-desktop [--gui | --tui | --selftest] [options]

front ends
  --gui, -G        Qt 6 window (default when no flag is given)
  --tui, --terminal, -T
                   terminal client; needs no Qt and no display
  --selftest       build the Qt window offscreen, refresh theme, exit 0

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
    if SELFTEST_FLAGS.intersection(args):
        # A smoke-test flag wins over front-end flags regardless of order.
        mode = "selftest"
    return mode, gui, tui


def _run_selftest() -> int:
    """Build the real main window offscreen, refresh its theme and exit 0.

    This is the check the packaged Windows build runs after PyInstaller and CI
    runs from source. It keeps the object graph to what widget construction
    needs: no sign-in, no HTTP and no ``PlayerEngine``/``QAudioOutput``, so no
    audio device is touched. All Qt imports stay local so ``--tui`` still runs
    on a machine without PySide6. Exceptions are allowed to propagate: a crash
    in the window or in ``widgets.refresh_theme`` must fail the process.
    """
    import os
    import tempfile

    # Keep the smoke test from reading or writing the user's real settings.
    scratch = tempfile.TemporaryDirectory(prefix="mcmusic-selftest-")
    env_keys = ("QT_QPA_PLATFORM", "XDG_CONFIG_HOME", "XDG_CACHE_HOME",
                "APPDATA", "LOCALAPPDATA")
    old_env = {key: os.environ.get(key) for key in env_keys}
    try:
        root = scratch.name
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        os.environ["XDG_CONFIG_HOME"] = os.path.join(root, "config")
        os.environ["XDG_CACHE_HOME"] = os.path.join(root, "cache")
        # SessionStore uses %APPDATA%/%LOCALAPPDATA% on Windows.
        os.environ["APPDATA"] = os.path.join(root, "appdata")
        os.environ["LOCALAPPDATA"] = os.path.join(root, "localappdata")

        from PySide6.QtCore import QObject, Signal
        from PySide6.QtWidgets import QApplication

        from . import theme
        from .api import Api, Async, SessionStore
        from .shell import McWindow

        class _SilentPlayer(QObject):
            """Only the surface McWindow needs; never constructs audio output."""

            changed = Signal()
            tick = Signal()
            error = Signal(str)
            loading_changed = Signal(bool)
            natural_end = Signal(int)

            def __init__(self) -> None:
                super().__init__()
                self.queue: list = []
                self.index = -1
                self.current = None
                self.playing = False
                self.shuffle = False
                self.repeat = "off"
                self.volume = 0.8
                self.muted = False
                self.position = 0.0
                self.duration = 0.0

            def set_volume(self, value: float) -> None:
                self.volume = value

            def play(self, tracks, index=0, shuffle_start=False) -> None:
                pass

            def pause(self) -> None:
                pass

            def toggle(self) -> None:
                pass

            def next(self) -> None:
                pass

            def prev(self) -> None:
                pass

            def seek_fraction(self, fraction: float) -> None:
                pass

            def seek(self, seconds: float) -> None:
                pass

            def toggle_mute(self) -> None:
                pass

            def toggle_shuffle(self) -> None:
                pass

            def cycle_repeat(self) -> None:
                pass

            def clear(self) -> None:
                pass

            def clear_upcoming(self) -> None:
                pass

            def remove_at(self, index: int) -> None:
                pass

            def jump(self, index: int) -> None:
                pass

            def move(self, source: int, target: int) -> bool:
                return False

            def add(self, track, *, next=False) -> None:
                pass

            def mark_liked(self, track_id: int, liked: bool) -> None:
                pass

            def queue_ids(self) -> list:
                return []

            def restore_snapshot(self, ids=None) -> bool:
                return False

            def save_snapshot(self) -> None:
                pass

            def shutdown(self) -> None:
                pass

        class _OfflineRepo:
            """No HTTP: construction only reaches these activity callbacks."""

            def save_settings(self, settings) -> None:
                pass

            def rotur_activity(self, *args, **kwargs) -> None:
                pass

            def discord_activity(self, *args, **kwargs) -> None:
                pass

        app = QApplication.instance() or QApplication([])
        app.setApplicationName("mcmusic")
        theme.set_appearance("violet-dark", "#9f7eff")
        app.setStyle("Fusion")
        app.setFont(theme.ui(13))
        app.setStyleSheet(theme.stylesheet())
        app.setPalette(theme.qpalette())

        store = SessionStore()
        store.clear_session()
        api = Api(store)
        runner = Async()
        player = _SilentPlayer()
        window = McWindow(store, api, _OfflineRepo(), runner, player)
        # Exercises widgets.refresh_theme on the full widget tree.
        window.apply_settings(window.settings, persist=False)
        app.processEvents()

        print("mcmusic selftest: ok", flush=True)
        player.shutdown()
        runner.shutdown()
        return 0
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        scratch.cleanup()


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv if argv is None else argv)
    program = raw[0] if raw else "mcmusic-desktop"
    args = raw[1:]

    if "-h" in args or "--help" in args:
        print(USAGE, end="")
        return 0

    mode, gui_args, tui_args = _split(args)

    if mode == "selftest":
        return _run_selftest()

    if mode == "tui":
        from .tui import main as tui_main
        return tui_main(tui_args)

    from .app import run_gui
    return run_gui([program, *gui_args])
