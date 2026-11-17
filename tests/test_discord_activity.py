"""Discord presence: availability reporting and the activity route.

Presence is published over Discord's local IPC socket, which this host does not
have. The interesting behaviour is what the API answers in that case: a missing
DISCORD_APP_ID and a missing desktop client must be distinguishable instead of
reporting success on an update that never leaves the queue.

    .venv/bin/python -m unittest discover -s tests -v
"""
import atexit
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

# Routes need the real schema, so point the app at a throwaway database. Only
# claim DATA_DIR when no earlier test module already did: database.DB_PATH is
# fixed on first import, and removing a directory another module now shares
# would break it. The dir is removed when the test process exits instead.
_OWN_TMP = None
if not os.environ.get("DATA_DIR"):
    _OWN_TMP = tempfile.mkdtemp(prefix="mcm-discord-test-")
    os.environ["DATA_DIR"] = _OWN_TMP
    atexit.register(shutil.rmtree, _OWN_TMP, True)
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"),
)

from flask import Flask, session  # noqa: E402

import database  # noqa: E402
import discord_activity  # noqa: E402
from auth import create_user  # noqa: E402
from routes import auth_routes  # noqa: E402


class DiscordAvailabilityTest(unittest.TestCase):
    def test_unconfigured_reports_the_missing_app_id(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": ""}):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("DISCORD_APP_ID", why)

    def test_no_client_reports_discord_is_not_running(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value=None):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("not running", why)

    def test_a_live_socket_counts_as_available(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value="/run/user/1/discord-ipc-0"):
            usable, why = discord_activity.available()
        self.assertTrue(usable, why)

    def test_clearing_an_unused_session_is_a_no_op(self):
        with mock.patch.object(discord_activity, "_new_sink") as new_sink:
            discord_activity.clear(424242)
            discord_activity.close(424242)
        new_sink.assert_not_called()


class DiscordActivityRouteTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "discord-test"
        self.app.register_blueprint(auth_routes.bp)
        database.init_db(self.app)
        with self.app.app_context():
            c = database._db()
            for table in ("tracks", "settings", "users"):
                c.execute(f"delete from {table}")
            c.commit()
            self.uid = create_user(c, "listener", "secret1")
            cur = c.execute(
                "insert into tracks(path,title,artist,album,duration) values(?,?,?,?,?)",
                ("/music/one.flac", "Test Track", "Test Artist", "Test Album", 215.5),
            )
            c.commit()
            self.track_id = cur.lastrowid

    def _post(self, body, uid=True):
        with self.app.test_request_context("/api/auth/discord/activity", method="POST", json=body):
            if uid:
                session["uid"] = self.uid
            raw = auth_routes.discord_activity_push()
        # Flask routes here return either a response or (response, status).
        if isinstance(raw, tuple):
            return raw[0], raw[1]
        return raw, raw.status_code

    def test_login_is_required(self):
        _, status = self._post({"playing": False}, uid=False)
        self.assertEqual(status, 401)

    def test_pausing_clears_without_touching_the_track(self):
        resp, status = self._post({"playing": False})
        self.assertEqual(status, 200)
        self.assertIsNone(resp.get_json()["activity"])

    def test_unknown_track_is_a_404(self):
        _, status = self._post({"track_id": 999999, "playing": True})
        self.assertEqual(status, 404)

    def test_missing_app_id_is_reported_not_swallowed(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": ""}):
            resp, status = self._post({"track_id": self.track_id, "playing": True, "position": 12})
        self.assertEqual(status, 503)
        body = resp.get_json()
        self.assertFalse(body["ok"])
        self.assertIn("DISCORD_APP_ID", body["error"])

    def test_a_connected_client_receives_the_track(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value="/run/user/1/discord-ipc-0"), \
                mock.patch.object(discord_activity, "publish", return_value=(True, "")) as publish:
            resp, status = self._post({"track_id": self.track_id, "playing": True, "position": 12})
        self.assertEqual(status, 200)
        self.assertEqual(resp.get_json()["activity"]["details"], "Test Track")
        state = publish.call_args.args[1]
        self.assertEqual(state.track.title, "Test Track")
        self.assertTrue(state.playing)
        self.assertAlmostEqual(state.position, 12)


if __name__ == "__main__":
    unittest.main()
