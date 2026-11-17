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


_NO_IDS = {"DISCORD_APP_ID": "", "DISCORD_APPLICATION_ID": "", "DISCORD_CLIENT_ID": ""}


class DiscordAvailabilityTest(unittest.TestCase):
    def test_unconfigured_reports_the_missing_app_id(self):
        with mock.patch.dict(os.environ, _NO_IDS):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("DISCORD_APP_ID", why)

    def test_the_linking_client_id_is_the_same_application(self):
        # The deployment already stores the id as DISCORD_CLIENT_ID/APPLICATION_ID;
        # presence must not need a second copy of it under a new name.
        with mock.patch.dict(os.environ, {**_NO_IDS, "DISCORD_CLIENT_ID": "1234567890"}):
            self.assertEqual(discord_activity.app_id(), "1234567890")
            self.assertTrue(discord_activity.state()["configured"])
        with mock.patch.dict(os.environ, {**_NO_IDS, "DISCORD_APPLICATION_ID": "987654321"}):
            self.assertEqual(discord_activity.app_id(), "987654321")

    def test_no_client_reports_discord_is_not_running(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value=None), \
                mock.patch.object(discord_activity, "client_running", return_value=False):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("not running", why)

    def test_a_stale_socket_is_not_reported_as_an_errno(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", side_effect=ConnectionRefusedError(111, "refused")), \
                mock.patch.object(discord_activity, "client_running", return_value=True):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("not signed in", why)

    def test_a_client_at_the_login_screen_is_not_called_missing(self):
        # The IPC socket only appears after signing in; telling the user Discord
        # is not running while it sits on the login screen sends them hunting
        # for an install that is already there.
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value=None), \
                mock.patch.object(discord_activity, "client_running", return_value=True):
            usable, why = discord_activity.available()
        self.assertFalse(usable)
        self.assertIn("not signed in", why)

    def test_a_live_socket_counts_as_available(self):
        with mock.patch.dict(os.environ, {"DISCORD_APP_ID": "1234567890"}), \
                mock.patch("pypresence.utils.get_ipc_path", return_value="/run/user/1/discord-ipc-0"), \
                mock.patch.object(discord_activity, "client_running", return_value=True):
            usable, why = discord_activity.available()
        self.assertTrue(usable, why)

    def test_clearing_an_unused_session_is_a_no_op(self):
        with mock.patch.object(discord_activity, "_new_sink") as new_sink:
            discord_activity.clear(424242)
            discord_activity.close(424242)
        new_sink.assert_not_called()


class DiscordButtonsTest(unittest.TestCase):
    def _buttons(self, room: str, profile: str):
        from music_activity.sinks.discord import DiscordSink
        from music_activity.state import PlayerState, Track
        state = PlayerState(
            track=Track(id="1", title="Song", artist="Artist", url=profile or None),
            playing=True,
            extra=room,
        )
        return DiscordSink("123")._buttons(state)

    def test_room_link_comes_first_then_the_profile(self):
        buttons = self._buttons("https://mcmusic.sdisk.us/s/abc", "https://mcmusic.sdisk.us/u/ann")
        self.assertEqual(
            buttons,
            [
                {"label": "Listen along", "url": "https://mcmusic.sdisk.us/s/abc"},
                {"label": "mcmusic profile", "url": "https://mcmusic.sdisk.us/u/ann"},
            ],
        )

    def test_a_profile_alone_is_still_a_button(self):
        buttons = self._buttons("", "https://mcmusic.sdisk.us/u/ann")
        self.assertEqual(buttons, [{"label": "mcmusic profile", "url": "https://mcmusic.sdisk.us/u/ann"}])

    def test_non_links_are_never_sent_to_discord(self):
        self.assertEqual(self._buttons("abc123", ""), [])


class DiscordUpdateFallbackTest(unittest.TestCase):
    def test_buttons_are_dropped_when_the_client_rejects_them(self):
        from music_activity.sinks.discord import DiscordSink
        from music_activity.state import PlayerState, Track

        calls = []

        class Rpc:
            def update(self, **kwargs):
                calls.append(kwargs)
                if "buttons" in kwargs:
                    raise RuntimeError("buttons unsupported")

        sink = DiscordSink("123", log=lambda _m: None)
        sink._rpc = Rpc()
        state = PlayerState(
            track=Track(id="1", title="Song", artist="Artist", duration=200,
                        url="https://mcmusic.sdisk.us/u/ann"),
            playing=True,
            extra="https://mcmusic.sdisk.us/s/abc",
        )
        sink._update(state)

        self.assertIn("buttons", calls[0])
        self.assertNotIn("buttons", calls[-1])
        self.assertEqual(calls[-1]["details"], "Song")


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

    def test_status_explains_a_presence_that_cannot_work(self):
        with mock.patch.dict(os.environ, _NO_IDS):
            with self.app.test_request_context("/api/auth/discord/status"):
                body = auth_routes.discord_status().get_json()
        presence = body["presence"]
        self.assertFalse(presence["configured"])
        self.assertFalse(presence["available"])
        self.assertIn("application id", presence["reason"])

    def test_missing_app_id_is_reported_not_swallowed(self):
        with mock.patch.dict(os.environ, _NO_IDS):
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
