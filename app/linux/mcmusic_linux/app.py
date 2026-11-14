"""mcmusic desktop — native Qt 6 client for the mcmusic server."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import theme
from .api import Api, Async, Repo, SessionStore
from .art import ART
from .models import Settings
from .mpris import Mpris
from .player import PlayerEngine
from .shell import McWindow

ASSETS = Path(__file__).with_name("assets")


def main(argv: list[str] | None = None) -> int:
    """Compatibility entry point; the GUI/TUI flag dispatch lives in .cli."""
    from .cli import main as cli_main
    return cli_main(argv)


def run_gui(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName("mcmusic")
    app.setApplicationDisplayName("mcmusic")
    app.setOrganizationName("mcmusic")
    app.setOrganizationDomain("mcmusic.dev")
    app.setDesktopFileName("mcmusic")
    # Fusion keeps metrics and control chrome identical on KDE, GNOME,
    # Hyprland and plain X11 sessions; all colours come from the palette below.
    app.setStyle("Fusion")

    icon_path = ASSETS / "mcmusic.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    store = SessionStore()
    theme.set_appearance(store.theme, store.accent)
    app.setFont(theme.ui(13))
    app.setStyleSheet(theme.stylesheet())
    app.setPalette(theme.qpalette())

    runner = Async()
    api = Api(store)
    api.set_base(store.base_url)
    repo = Repo(api)
    ART.bind(api, runner)

    holder: dict[str, object] = {"window": None}
    player = PlayerEngine(
        repo, api, runner,
        lambda: holder["window"].settings if holder["window"] is not None else Settings(),
    )
    player.set_volume(store.volume)

    window = McWindow(store, api, repo, runner, player)
    holder["window"] = window
    window.mpris = Mpris(player, window.close)  # type: ignore[attr-defined]
    window.show()

    app.aboutToQuit.connect(player.shutdown)
    app.aboutToQuit.connect(runner.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
