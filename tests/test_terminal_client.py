"""Integration coverage for the terminal client against a real server.

Every other surface of the Linux client is exercised against stubs; this suite
starts an actual mcmusic server (tests/fixture_server.py) on a free port with a
throwaway DATA_DIR and MUSIC_DIR, signs in for real, and drives the TUI's HTTP
client through the routes it uses — playlists, download requests, admin and the
playback registry. If a route changes shape, this fails instead of the terminal
client failing at runtime.

    .venv/bin/python -m unittest discover -s tests -v

The methods are numbered because they share one server: each builds on the
accounts and rows the previous one created.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TMP = tempfile.mkdtemp(prefix="mcm-tui-it-")
os.environ["XDG_CONFIG_HOME"] = os.path.join(TMP, "config")
os.environ["XDG_CACHE_HOME"] = os.path.join(TMP, "cache")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "app", "linux"))

from fixture_server import ThrowawayServer  # noqa: E402
from mcmusic_linux.tui import ApiError, Client, Config, fetch_admin, fetch_requests  # noqa: E402

INVITE = "test-invite"


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


class TerminalClientIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThrowawayServer().start()
        cls.base = cls.server.base

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    # helpers -----------------------------------------------------------
    @classmethod
    def client(cls):
        """A signed-out client, even though earlier tests have saved cookies."""
        cfg = Config()
        cfg.cookies = {}
        c = Client(cfg)
        c.set_base(cls.base)
        return c

    @classmethod
    def seed_track(cls):
        if not hasattr(cls, "_track"):
            tracks = cls.admin.tracks()
            assert tracks, "fixture did not seed a track"
            cls._track = tracks[0]
        return cls._track

    # ------------------------------------------------------------------ tests
    def test_01_bootstrap_account_signs_in_and_is_admin(self):
        self.__class__.admin = self.client()
        me = self.__class__.admin.register("tester", "secret1", "")
        self.assertEqual(me.username, "tester")
        self.assertTrue(me.is_admin, "the first account on a fresh server is the admin")

        # The session cookie was captured and persisted to the client's own config.
        cfg = self.__class__.admin.cfg
        self.assertTrue(cfg.cookies, "no session cookie was captured")
        self.assertTrue(cfg.path.exists(), "config was not written")
        self.assertEqual(cfg.path.stat().st_mode & 0o777, 0o600)
        saved = json.loads(cfg.path.read_text())
        self.assertEqual(saved["base_url"], self.base)

        # A separate client can sign in with the password alone.
        fresh = self.client()
        self.assertEqual(fresh.login("tester", "secret1").username, "tester")

        # Anonymous access is refused rather than served an empty library.
        anon = self.client()
        with self.assertRaises(ApiError) as err:
            anon.tracks()
        self.assertEqual(err.exception.status, 401)

    def test_02_second_account_needs_the_invite_code(self):
        with self.assertRaises(ApiError) as err:
            self.client().register("guest_1", "secret2", "")
        self.assertEqual(err.exception.status, 403)
        self.assertIn("invite", str(err.exception))

        self.__class__.guest = self.client()
        me = self.__class__.guest.register("guest_1", "secret2", INVITE)
        self.assertEqual(me.username, "guest_1")
        self.assertFalse(me.is_admin)

    def test_03_playlists_round_trip_through_the_client(self):
        admin = self.__class__.admin
        night = admin.create_playlist("Night")
        self.assertGreater(night, 0)
        self.assertIn("Night", [p.name for p in admin.playlists()])

        admin.rename_playlist(night, "Late Night")
        self.assertIn("Late Night", [p.name for p in admin.playlists()])

        track = self.seed_track()
        admin.add_to_playlist(night, track.id)
        name, items = admin.playlist(night)
        self.assertEqual(name, "Late Night")
        self.assertEqual([t.id for t in items], [track.id])
        late = next(p for p in admin.playlists() if p.name == "Late Night")
        self.assertEqual(late.n, 1)

        admin.remove_from_playlist(night, track.id)
        self.assertEqual(admin.playlist(night)[1], [])

        admin.delete_playlist(night)
        self.assertNotIn("Late Night", [p.name for p in admin.playlists()])
        with self.assertRaises(ApiError) as err:
            admin.playlist(night)
        self.assertEqual(err.exception.status, 404)

    def test_04_playlists_are_private_and_validate_tracks(self):
        admin, guest = self.__class__.admin, self.__class__.guest
        mine = admin.create_playlist("Admin Only")
        self.assertNotIn("Admin Only", [p.name for p in guest.playlists()])
        with self.assertRaises(ApiError):
            guest.playlist(mine)
        with self.assertRaises(ApiError) as err:
            admin.add_to_playlist(mine, 999999)
        self.assertEqual(err.exception.status, 404)
        admin.delete_playlist(mine)

    def test_05_requests_are_per_user_and_pending(self):
        guest = self.__class__.guest
        status = guest.request_add("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(status, "pending", "AUTO_APPROVE=0 must hold requests for an admin")

        title, rows, is_admin = fetch_requests(guest)
        self.assertEqual(title, "Requests")
        self.assertFalse(is_admin)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].sub, "guest_1 · pending")
        self.assertEqual(rows[0].request.status, "pending")

        _title, rows, is_admin = fetch_requests(self.__class__.admin)
        self.assertTrue(is_admin)
        self.assertEqual(len(rows), 1, "an admin sees every account's requests")

        with self.assertRaises(ApiError) as err:
            guest.request_act(rows[0].request.id, "approve")
        self.assertEqual(err.exception.status, 403)

    def test_06_admin_approves_one_request_and_rejects_another(self):
        admin, guest = self.__class__.admin, self.__class__.guest
        approve_id = fetch_requests(admin)[1][0].request.id
        admin.request_act(approve_id, "approve")

        deadline = time.time() + 15
        status = "pending"
        while time.time() < deadline:
            status = next(r.request.status for r in fetch_requests(admin)[1]
                          if r.request.id == approve_id)
            if status != "pending":
                break
            time.sleep(0.25)
        self.assertIn(status, {"approved", "running", "done", "failed"})

        guest.request_add("https://youtu.be/9bZkp7q19f0")
        reject_id = max(r.request.id for r in fetch_requests(guest)[1])
        admin.request_act(reject_id, "reject")
        statuses = {r.request.id: r.request.status for r in fetch_requests(admin)[1]}
        self.assertEqual(statuses[reject_id], "rejected")

    def test_07_admin_dashboard_shows_users_and_toggles_roles(self):
        admin, guest = self.__class__.admin, self.__class__.guest
        title, rows = fetch_admin(admin)
        self.assertEqual(title, "Admin")
        kinds = [r.kind for r in rows]
        self.assertEqual(kinds[:5], ["admin-stat"] * 5)
        self.assertEqual(kinds[5], "heading")

        users = {r.user.username: r for r in rows if r.kind == "admin-user"}
        self.assertEqual(set(users), {"tester", "guest_1"})
        self.assertTrue(users["tester"].sub.startswith("admin"))
        self.assertTrue(users["guest_1"].sub.startswith("member"))

        guest_id = users["guest_1"].user.id
        admin.admin_set_admin(guest_id, True)
        self.assertEqual(admin.admin_stats().admins, 2)
        self.assertTrue(fetch_requests(guest)[0], "promoted account now reads the admin view")
        admin.admin_set_admin(guest_id, False)
        self.assertEqual(admin.admin_stats().admins, 1)

    def test_08_playback_snapshot_is_published_and_read_back(self):
        admin = self.__class__.admin
        track = self.seed_track()
        admin.publish_playback(track.id, 12.5, 180.0, True, [track.id])
        state = admin.get("playback")["state"]
        self.assertEqual(state["track_id"], track.id)
        self.assertEqual(state["duration"], 180.0)
        self.assertTrue(state["playing"])
        self.assertEqual(state["queue"], [track.id])
        self.assertEqual(state["track"]["title"], "Seeded Song")

        admin.publish_playback(None, 0, 0, False, [])
        state = admin.get("playback")["state"]
        self.assertIsNone(state["track_id"])
        self.assertFalse(state["playing"])
        self.assertEqual(state["queue"], [])

    def test_09_rescan_trusts_the_disk(self):
        admin = self.__class__.admin
        self.assertEqual(admin.admin_stats().tracks, 1, "fixture row should still be there")
        self.assertEqual(admin.admin_scan(), (1, 1))

        (self.server.music_dir / "seeded.mp3").unlink()
        self.assertEqual(admin.admin_scan(), (0, 0), "the file is gone, so the row goes too")
        self.assertEqual(admin.admin_stats().tracks, 0)


if __name__ == "__main__":
    unittest.main()
