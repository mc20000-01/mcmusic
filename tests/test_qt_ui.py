"""Widget-level smoke coverage for the Qt window against a real server.

``tests/test_qt_client.py`` proves the network layer speaks the server's
contract; this suite proves the window built on top of it actually comes up
and fills its screens. It builds the same object graph ``run_gui`` does — a
``QApplication`` on the offscreen platform, a ``SessionStore`` pointed at a
scratch config dir, ``Api``/``Repo``/``Async``, the real ``PlayerEngine`` and
``McWindow`` — against the throwaway server, then signs in and visits every
route, waiting for the worker pool's callbacks to paint each screen.

    .venv/bin/python -m unittest discover -s tests -v

No display, widget click or pixel comparison is involved; the assertions are
about which screen the router chose and whether the async data reached it.
Set ``MC_MUSIC_QT_AUDIO_STUB=1`` on hosts without an audio device to replace
only QAudioOutput/QMediaPlayer with headless fakes. Skipped rather than failed
when PySide6 (with QtMultimedia) is missing.
"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "app", "linux"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from fixture_server import ThrowawayServer  # noqa: E402

try:
    from PySide6.QtCore import QEventLoop
    from PySide6.QtWidgets import QApplication

    from mcmusic_linux import theme
    from mcmusic_linux.api import Api, Async, Repo, SessionStore
    from mcmusic_linux.art import ART
    from mcmusic_linux.login import LoginPage
    from mcmusic_linux.player import PlayerEngine
    from mcmusic_linux.screens import (
        AdminScreen,
        CollectionScreen,
        HomeScreen,
        LibraryScreen,
        LikesScreen,
        PlaylistScreen,
        PlaylistsScreen,
        RequestsScreen,
        SearchScreen,
        SettingsScreen,
    )
    from mcmusic_linux.shell import McWindow
    from mcmusic_linux.widgets import EmptyState, Hero, Shelf
except ImportError as exc:
    QT_ERROR = str(exc)
else:
    QT_ERROR = ""


def _find(layout, kind):
    """The first widget of ``kind`` in a layout, skipping spacing items."""
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if isinstance(widget, kind):
            return widget
    return None


@unittest.skipIf(QT_ERROR, f"PySide6/QtMultimedia not available: {QT_ERROR}")
class QtWindowIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_config = os.environ.get("XDG_CONFIG_HOME")
        cls._old_cache = os.environ.get("XDG_CACHE_HOME")
        cls.tmp = Path(tempfile.mkdtemp(prefix="mcm-qt-ui-"))
        os.environ["XDG_CONFIG_HOME"] = str(cls.tmp / "config")
        os.environ["XDG_CACHE_HOME"] = str(cls.tmp / "cache")

        cls.app = QApplication.instance() or QApplication([])
        cls.server = ThrowawayServer().start()

        cls.store = SessionStore()
        cls.store.clear_session()
        cls.api = Api(cls.store)
        cls.api.set_base(cls.server.base)
        cls.repo = Repo(cls.api)
        cls.runner = Async()
        cls.me = cls.repo.register("uiadmin", "secret1", "")
        tracks = cls.repo.tracks()
        assert tracks, "fixture did not seed a track"
        cls.track = tracks[0]
        cls.repo.like(cls.track.id)
        cls.playlist_id = cls.repo.create_playlist("UI List")
        ART.bind(cls.api, cls.runner)
        theme.set_appearance("violet-dark", "#9f7eff")

        if os.environ.get("MC_MUSIC_QT_AUDIO_STUB") == "1":
            # Headless CI has no sound device; QtMultimedia can abort the
            # process while constructing QAudioOutput. Swap only the audio
            # classes, leaving all client logic under test.
            from qt_audio_stub import install
            install()

        cls.player = PlayerEngine(
            cls.repo, cls.api, cls.runner,
            lambda: cls.window.settings if getattr(cls, "window", None) else
            __import__("mcmusic_linux.models", fromlist=["Settings"]).Settings(),
        )
        cls.player.set_volume(0.3)
        cls.window = McWindow(cls.store, cls.api, cls.repo, cls.runner, cls.player)
        # The window would show the login page here; the login form itself is
        # exercised by the API suite, so hand the window a finished session.
        cls.window.after_login(cls.me)

    @classmethod
    def tearDownClass(cls):
        if QT_ERROR:
            return
        cls.window.close()
        cls.player.shutdown()
        cls.runner.shutdown()
        cls.server.stop()
        for key, old in (("XDG_CONFIG_HOME", cls._old_config),
                         ("XDG_CACHE_HOME", cls._old_cache)):
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # helpers -----------------------------------------------------------
    def pump_until(self, predicate, what="condition", timeout=30.0):
        deadline = time.time() + timeout
        while True:
            if predicate():
                return
            if time.time() > deadline:
                self.fail(f"timed out waiting for {what}")
            self.app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)

    def settle(self, rounds: int = 6) -> None:
        for _ in range(rounds):
            self.app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)

    # ------------------------------------------------------------------ tests
    def test_01_signed_in_window_lands_on_a_filled_home_screen(self):
        self.assertIs(self.window.stack.currentWidget(), self.window.shell)
        self.assertEqual(self.window.me.username, "uiadmin")
        self.assertEqual(self.window.rail.user_button._name, "uiadmin")
        self.assertFalse(self.window.rail._admin_nav.isHidden())
        self.assertEqual(self.window.deck.title.text(), "Nothing playing right now")

        self.assertIsInstance(self.window.current_screen, HomeScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: _find(screen.body_layout, Shelf) is not None, "home shelves")

    def test_02_library_and_album_routes_show_the_seeded_track(self):
        self.window.navigate(("library",))
        self.assertIsInstance(self.window.current_screen, LibraryScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: screen.track_list is not None, "library songs")
        self.assertEqual([t.title for t in screen.tracks], ["Seeded Song"])

        screen._switch("albums")
        self.pump_until(lambda: screen.clayout.count() >= 2, "album grid")
        self.assertEqual(screen.tab, "albums")

        self.window.navigate(("album", "Test Album"))
        self.assertIsInstance(self.window.current_screen, CollectionScreen)
        album = self.window.current_screen
        self.pump_until(lambda: album.track_list is not None, "album tracks")
        self.assertEqual(album.name, "Test Album")
        self.assertEqual([t.title for t in album.tracks], ["Seeded Song"])

    def test_03_likes_route_reflects_the_like(self):
        self.window.navigate(("likes",))
        self.assertIsInstance(self.window.current_screen, LikesScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: screen.track_list is not None, "liked tracks")
        self.assertIsNotNone(_find(screen.body_layout, Hero))

    def test_04_playlists_route_and_sidebar_share_the_playlist_list(self):
        self.window.refresh_playlists()
        self.pump_until(lambda: bool(self.window.playlists), "playlist refresh")
        # Faves and Likes are generated by the server alongside user lists.
        self.assertIn("UI List", [p.name for p in self.window.playlists])
        self.assertEqual(len(self.window.rail._pl_buttons), len(self.window.playlists))

        self.window.navigate(("playlists",))
        self.assertIsInstance(self.window.current_screen, PlaylistsScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: screen.body_layout.count() >= 2, "playlist tiles")

        self.window.navigate(("playlist", self.playlist_id))
        self.assertIsInstance(self.window.current_screen, PlaylistScreen)
        detail = self.window.current_screen
        self.pump_until(lambda: detail.playlist_name != "", "playlist detail")
        self.assertEqual(detail.playlist_name, "UI List")
        self.assertEqual(detail.tracks, [])

    def test_05_requests_route_renders_the_empty_state(self):
        self.window.navigate(("requests",))
        self.assertIsInstance(self.window.current_screen, RequestsScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: screen.llayout.count() == 1, "requests list")
        self.assertIsInstance(screen.llayout.itemAt(0).widget(), EmptyState)

    def test_06_settings_route_shows_the_server_preferences(self):
        self.window.navigate(("settings",))
        self.assertIsInstance(self.window.current_screen, SettingsScreen)
        screen = self.window.current_screen
        self.pump_until(lambda: bool(screen._theme_cards), "settings rows")
        self.assertEqual(len(screen._theme_cards), len(theme.THEME_ORDER))
        self.assertEqual(len(screen._swatches), len(theme.ACCENTS))
        self.assertEqual(self.window.settings.theme, "violet")
        self.assertEqual(self.window.settings.density, "comfy",
                         "the server's settings never replaced the local copy")
        self.assertEqual(self.window.api.base_url, self.server.base)

    def test_07_admin_console_renders_stats_and_users(self):
        self.window.navigate(("admin",))
        self.assertIsInstance(self.window.current_screen, AdminScreen)
        screen = self.window.current_screen
        self.pump_until(
            lambda: screen._stats_host.layout() is not None
            and screen._stats_host.layout().count() >= 11,
            "admin stats",
        )
        self.pump_until(lambda: screen._users_line.count() > 0, "admin users")

    def test_08_search_route_takes_over_from_the_header_field(self):
        self.window.on_search_text("seeded")
        self.assertEqual(self.window.route, ("search",))
        self.assertIsInstance(self.window.current_screen, SearchScreen)
        self.assertEqual(self.window._search, "seeded")
        screen = self.window.current_screen
        self.pump_until(lambda: screen.body_layout.count() >= 2, "search results")
        self.window.on_search_text("")

    def test_09_signing_out_returns_to_the_login_page(self):
        self.window.sign_out()
        self.settle()
        self.assertIsNone(self.window.me)
        self.assertIsInstance(self.window.stack.currentWidget(), LoginPage)
        self.assertEqual(self.window.api.cookies, {})
        self.assertEqual(self.window.rail.user_button._name, "")
        self.assertEqual(self.window.player.queue, [])


if __name__ == "__main__":
    unittest.main()
