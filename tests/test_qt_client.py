"""Integration coverage for the Qt client's API layer against a real server.

The desktop client has no widget tests yet, but its network layer — ``Api``
(``requests`` + ``QSettings`` session), ``Repo`` (the endpoint map) and
``Async`` (worker thread, callbacks back on the Qt thread) — is where a route
change actually breaks it. Each piece is real here: a genuine server process
from ``tests/fixture_server.py``, a genuine ``QCoreApplication`` event loop, and
the same ``SessionStore`` code the window uses, pointed at a temporary config
directory.

    .venv/bin/python -m unittest discover -s tests -v

Needs PySide6 and requests (both in the project venv); it is skipped rather
than failed when they are missing. Methods are numbered because they share one
server and one account pair.
"""
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "app", "linux"))

from fixture_server import ThrowawayServer  # noqa: E402

try:
    from PySide6.QtCore import QEventLoop
    from PySide6.QtWidgets import QApplication

    from mcmusic_linux import theme
    from mcmusic_linux.api import Api, ApiError, Async, Repo, SessionStore, normalize
    from mcmusic_linux.models import HomeData, Me
except ImportError as exc:  # the venv has both; system python may not
    QT_ERROR = str(exc)
else:
    QT_ERROR = ""


@unittest.skipIf(QT_ERROR, f"PySide6/requests not available: {QT_ERROR}")
class QtApiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # QSettings("mcmusic", "mcmusic-desktop") resolves through the XDG
        # config dir, so point it at scratch space before the first store.
        cls._old_config = os.environ.get("XDG_CONFIG_HOME")
        cls.tmp = Path(tempfile.mkdtemp(prefix="mcm-qt-it-"))
        os.environ["XDG_CONFIG_HOME"] = str(cls.tmp / "config")
        # A QApplication (not just QCoreApplication) so the widget suite can
        # share this instance; discovery imports every module before running,
        # so whichever class starts first must create the app the other reuses.
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

        cls.server = ThrowawayServer().start()
        cls.runner = Async()
        cls.store = SessionStore()
        cls.store.clear_session()
        cls.api = Api(cls.store)
        cls.api.set_base(cls.server.base)
        cls.repo = Repo(cls.api)

    @classmethod
    def tearDownClass(cls):
        if QT_ERROR:
            return
        cls.runner.shutdown()
        cls.server.stop()
        if cls._old_config is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = cls._old_config
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

    def run_sync(self, fn, *args, **kwargs):
        """Drive Async the way the window does and return the value."""
        box = {}

        def on_ok(value):
            box["value"] = value

        def on_error(exc):
            box["error"] = exc

        self.runner.submit(lambda: fn(*args, **kwargs), on_ok, on_error)
        name = getattr(fn, "__name__", "call")
        self.pump_until(lambda: "value" in box or "error" in box, name)
        if "error" in box:
            raise box["error"]
        return box["value"]

    def track(self):
        if not hasattr(self, "_track"):
            tracks = self.run_sync(self.repo.tracks)
            self.assertTrue(tracks, "fixture did not seed a track")
            self._track = tracks[0]
        return self._track

    # ------------------------------------------------------------------ tests
    def test_01_sign_in_persists_session_and_base_url(self):
        me = self.run_sync(self.repo.register, "qtadmin", "secret1", "")
        self.assertIsInstance(me, Me)
        self.assertEqual(me.username, "qtadmin")
        self.assertTrue(me.is_admin, "the first account on a fresh server is the admin")
        self.assertEqual(self.run_sync(self.repo.me).username, "qtadmin")

        cookies = self.store.load_cookies()
        self.assertTrue(cookies, "no session cookie was stored")
        self.assertEqual(self.store.base_url, self.server.base)
        conf = Path(os.environ["XDG_CONFIG_HOME"]) / "mcmusic" / "mcmusic-desktop.conf"
        self.assertTrue(conf.exists(), "QSettings never wrote the session to disk")

        # A new store (what the window builds on the next launch) restores both
        # the server address and the session without signing in again.
        store = SessionStore()
        self.assertEqual(store.base_url, self.server.base)
        self.assertEqual(self.run_sync(Repo(Api(store)).me).username, "qtadmin")

        # A store with no session is refused rather than given an empty client.
        anonymous = SessionStore()
        anonymous.clear_session()
        api = Api(anonymous)
        api.set_base(self.server.base)
        with self.assertRaises(ApiError) as err:
            self.run_sync(Repo(api).me)
        self.assertEqual(err.exception.status, 401)

        self.assertEqual(normalize("example.test:8000/api/"), "http://example.test:8000")

    def test_02_invite_gate_and_async_errors_come_back_on_the_main_thread(self):
        with self.assertRaises(ApiError) as err:
            self.run_sync(self.repo.register, "qtguest", "secret2", "")
        self.assertEqual(err.exception.status, 403)
        self.assertIn("invite", str(err.exception))

        seen = {}

        def on_ok(value):
            seen["thread"] = threading.current_thread()
            seen["value"] = value

        self.runner.submit(lambda: "delivered", on_ok, lambda exc: seen.setdefault("error", exc))
        self.pump_until(lambda: "value" in seen or "error" in seen, "async callback")
        self.assertNotIn("error", seen)
        self.assertEqual(seen["value"], "delivered")
        self.assertIs(seen["thread"], threading.main_thread(),
                      "callbacks must land on the Qt thread, not the worker")

        # A second signed-in client for the member account; the admin client
        # keeps its own cookie in memory. Each test method gets a fresh
        # TestCase instance, so the repo lives on the class.
        guest_api = Api(SessionStore())
        guest_api.set_base(self.server.base)
        guest_api.cookies.clear()
        type(self).guest_repo = Repo(guest_api)
        guest = self.run_sync(self.guest_repo.register, "qtguest", "secret2", self.server.invite)
        self.assertEqual(guest.username, "qtguest")
        self.assertFalse(guest.is_admin)

    def test_03_library_search_and_browse_shapes(self):
        home = self.run_sync(self.repo.home)
        self.assertIsInstance(home, HomeData)
        self.assertEqual({a.album for a in home.albums}, {"Test Album"})
        self.assertIsInstance(home.sections, list)

        track = self.track()
        self.assertEqual(track.title, "Seeded Song")
        self.assertEqual(track.artist, "Test Artist")

        found = self.run_sync(self.repo.search, "seeded")
        self.assertEqual([t.id for t in found.tracks], [track.id])
        self.assertIsInstance(found.albums, list)
        self.assertIsInstance(found.artists, list)

        self.assertEqual([a.album for a in self.run_sync(self.repo.albums)], ["Test Album"])
        self.assertEqual([a.artist for a in self.run_sync(self.repo.artists)], ["Test Artist"])
        self.assertEqual([t.id for t in self.run_sync(self.repo.album, "Test Album")], [track.id])
        self.assertEqual([t.id for t in self.run_sync(self.repo.artist, "Test Artist")], [track.id])
        self.assertEqual(self.run_sync(self.repo.tracks, "seeded")[0].id, track.id)

    def test_04_playlists_are_owned_by_the_account_that_made_them(self):
        track = self.track()
        pid = self.run_sync(self.repo.create_playlist, "Qt List")
        self.assertIn("Qt List", [p.name for p in self.run_sync(self.repo.playlists)])

        self.run_sync(self.repo.rename_playlist, pid, "Renamed")
        self.run_sync(self.repo.add_to_playlist, pid, track.id)
        name, items = self.run_sync(self.repo.playlist, pid)
        self.assertEqual(name, "Renamed")
        self.assertEqual([t.id for t in items], [track.id])
        renamed = next(p for p in self.run_sync(self.repo.playlists) if p.name == "Renamed")
        self.assertEqual(renamed.n, 1)

        self.run_sync(self.repo.remove_from_playlist, pid, track.id)
        self.assertEqual(self.run_sync(self.repo.playlist, pid)[1], [])

        with self.assertRaises(ApiError) as err:
            self.run_sync(self.guest_repo.playlist, pid)
        self.assertEqual(err.exception.status, 404, "another account must not read this list")

        self.run_sync(self.repo.delete_playlist, pid)
        with self.assertRaises(ApiError) as err:
            self.run_sync(self.repo.playlist, pid)
        self.assertEqual(err.exception.status, 404)

    def test_05_requests_and_admin_routes(self):
        status = self.run_sync(self.guest_repo.request_add, "https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(status, "pending", "AUTO_APPROVE=0 must hold requests for an admin")

        is_admin, rows = self.run_sync(self.guest_repo.requests)
        self.assertFalse(is_admin)
        self.assertEqual([r.username for r in rows], ["qtguest"])

        is_admin, rows = self.run_sync(self.repo.requests)
        self.assertTrue(is_admin, "an admin sees every account's requests")
        self.assertEqual(len(rows), 1)
        request_id = rows[0].id

        with self.assertRaises(ApiError) as err:
            self.run_sync(self.guest_repo.admin_stats)
        self.assertEqual(err.exception.status, 403)

        with self.assertRaises(ApiError) as err:
            self.run_sync(self.guest_repo.request_act, request_id, "approve")
        self.assertEqual(err.exception.status, 403)

        self.run_sync(self.repo.request_act, request_id, "approve")
        deadline = time.time() + 15
        status = "pending"
        while time.time() < deadline:
            status = next(r.status for r in self.run_sync(self.repo.requests)[1]
                          if r.id == request_id)
            if status != "pending":
                break
            time.sleep(0.25)
        self.assertIn(status, {"approved", "running", "done", "failed"})

        self.run_sync(self.guest_repo.request_add, "https://youtu.be/9bZkp7q19f0")
        reject_id = max(r.id for r in self.run_sync(self.repo.requests)[1])
        self.run_sync(self.repo.request_act, reject_id, "reject")
        statuses = {r.id: r.status for r in self.run_sync(self.repo.requests)[1]}
        self.assertEqual(statuses[reject_id], "rejected")

        stats = self.run_sync(self.repo.admin_stats)
        self.assertEqual(stats.users, 2)
        self.assertEqual(stats.admins, 1)
        users = {u.username: u for u in self.run_sync(self.repo.admin_users)}
        self.assertEqual(set(users), {"qtadmin", "qtguest"})
        self.assertFalse(users["qtguest"].is_admin)

        self.run_sync(self.repo.admin_set_admin, users["qtguest"].id, True)
        self.assertEqual(self.run_sync(self.repo.admin_stats).admins, 2)
        self.assertTrue(self.run_sync(self.guest_repo.requests)[0],
                        "promoted account now reads the admin view")
        self.run_sync(self.repo.admin_set_admin, users["qtguest"].id, False)
        self.assertEqual(self.run_sync(self.repo.admin_stats).admins, 1)

    def test_06_settings_playback_and_streaming(self):
        track = self.track()
        settings = self.run_sync(self.repo.settings)
        self.assertEqual(settings.theme, "violet")
        changed = replace(settings, density="compact", private=True, volume=0.31)
        self.run_sync(self.repo.save_settings, changed)
        stored = self.run_sync(self.repo.settings)
        self.assertEqual((stored.density, stored.private, stored.volume), ("compact", True, 0.31))

        self.run_sync(self.repo.publish_playback, track.id, 30.0, 180.0, True, [track.id])
        state = self.api.get("playback")["state"]
        self.assertEqual(state["track_id"], track.id)
        self.assertEqual(state["duration"], 180.0)
        self.assertTrue(state["playing"])
        self.assertEqual(state["queue"], [track.id])

        self.assertTrue(self.run_sync(self.repo.like, track.id))
        self.assertEqual([t.id for t in self.run_sync(self.repo.likes)], [track.id])
        self.assertFalse(self.run_sync(self.repo.like, track.id))
        self.assertEqual(self.run_sync(self.repo.likes), [])

        self.run_sync(self.repo.report_play, track.id, True)
        self.assertEqual(self.run_sync(self.repo.admin_stats).plays, 1)
        self.run_sync(self.repo.heartbeat, "qt-test-device", "Qt Test", track.id, 30.0, False)

        # The player fetches audio through Api.download, not a raw media URL.
        dest = self.tmp / "audio" / "track.bin"
        content_type = self.run_sync(self.api.download, f"tracks/{track.id}/stream", dest)
        self.assertTrue(dest.exists())
        self.assertEqual(content_type.split(";")[0].strip(), "audio/mpeg")

    def test_07_a_rescan_trusts_the_disk(self):
        self.assertEqual(self.run_sync(self.repo.admin_scan), (1, 1))
        (self.server.music_dir / "seeded.mp3").unlink()
        self.assertEqual(self.run_sync(self.repo.admin_scan), (0, 0))
        self.assertEqual(self.run_sync(self.repo.admin_stats).tracks, 0)

    def test_08_theme_previews_and_aliases_resolve(self):
        for name in theme.THEME_ORDER:
            surface, accent = theme.theme_preview(name)
            self.assertTrue(surface.startswith("#"), f"{name}: {surface}")
            self.assertTrue(accent.startswith("#"), f"{name}: {accent}")
        self.assertEqual(theme.family_of("dusk"), "violet")
        self.assertEqual(theme.mode_of("dusk"), "dark")
        self.assertEqual(theme.family_of("system"), "violet")
        self.assertEqual(theme.mode_of("system"), "auto")


if __name__ == "__main__":
    unittest.main()
