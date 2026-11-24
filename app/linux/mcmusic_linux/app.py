"""mcmusic desktop — native Qt 6 client for the mcmusic server."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import theme
from .api import Api, Async, Repo, SessionStore
from .art import ART
from .models import Settings
from .mpris import Mpris
from .player import PlayerEngine
from .platform_media import MediaBridge
from .shell import McWindow
from .version import VERSION

ASSETS = Path(__file__).with_name("assets")


def main(argv: list[str] | None = None) -> int:
    """Compatibility entry point; the GUI/TUI flag dispatch lives in .cli."""
    from .cli import main as cli_main
    return cli_main(argv)


def run_gui(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    # mcmusic://rotur?token=… / mcmusic-desktop://rotur?token=… from the browser.
    link_token = ""
    qt_args = [argv[0]] if argv else []
    for arg in argv[1:]:
        if arg.startswith(("mcmusic://", "mcmusic-desktop://")):
            parsed = urlparse(arg)
            values = parse_qs(parsed.query)
            link_token = (
                values.get("token", [""])[0]
                or values.get("access_token", [""])[0]
                or parsed.path.lstrip("/")
            )
        else:
            qt_args.append(arg)
    app = QApplication(qt_args)
    app.setApplicationName("mcmusic")
    app.setApplicationDisplayName("mcmusic")
    app.setApplicationVersion(VERSION)
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
    if link_token:
        store.pending_token = link_token
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
        store=store,
    )
    player.set_volume(store.volume)

    window = McWindow(store, api, repo, runner, player)
    holder["window"] = window
    window.mpris = Mpris(player, window.close)  # type: ignore[attr-defined]
    window.media_bridge = MediaBridge(player, window)  # type: ignore[attr-defined]
    window.show()

    app.aboutToQuit.connect(window.media_bridge.shutdown)  # type: ignore[attr-defined]
    app.aboutToQuit.connect(player.shutdown)
    app.aboutToQuit.connect(runner.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
