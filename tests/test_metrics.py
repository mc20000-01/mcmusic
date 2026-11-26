"""Integration coverage for always-on metrics, Faves and Likes-as-playlist.

Runs against the real throwaway server from ``tests/fixture_server.py`` so the
schema migration, auth and admin routes are all exercised together.
"""
import http.cookiejar
import json
import os
import sys
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fixture_server import ThrowawayServer  # noqa: E402


class ListeningMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThrowawayServer().start()
        cls.jar = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.jar))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def call(self, path, payload=None, method=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.server.base + path, data=data,
            headers={"Content-Type": "application/json"} if data else {},
            method=method or ("POST" if data is not None else "GET"),
        )
        try:
            with self.opener.open(req, timeout=15) as res:
                return res.status, json.loads(res.read() or b"{}")
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read() or b"{}")
            exc.close()
            return exc.code, body

    def test_01_plays_and_metrics_build_faves_and_like_playlist(self):
        status, me = self.call("/api/register", {"username": "metrics", "password": "secret1"})
        self.assertEqual(status, 200, me)
        self.assertTrue(me["is_admin"])

        status, found = self.call("/api/tracks")
        self.assertEqual(status, 200, found)
        self.assertTrue(found["tracks"])
        tid = found["tracks"][0]["id"]

        status, liked = self.call(f"/api/like/{tid}", {})
        self.assertEqual(status, 200, liked)
        self.assertTrue(liked["liked"])

        for _ in range(2):
            status, res = self.call("/api/plays", {"track_id": tid, "completed": False,
                                                   "client": "web"})
            self.assertEqual(status, 200, res)
        status, res = self.call("/api/metrics", {"events": [
            {"event": "complete", "track_id": tid, "position": 180, "duration": 180,
             "client": "android"},
            {"event": "bogus", "track_id": tid},
        ]})
        self.assertEqual(status, 200, res)
        self.assertEqual(res["saved"], 1)

        status, data = self.call("/api/playlists")
        self.assertEqual(status, 200, data)
        rows = data["playlists"]
        self.assertEqual([r["name"] for r in rows[:2]], ["Faves", "Likes"])
        self.assertTrue(rows[0]["pinned"] and rows[1]["pinned"])
        faves, likes = rows[0]["id"], rows[1]["id"]

        status, data = self.call(f"/api/playlists/{faves}")
        self.assertEqual(status, 200, data)
        self.assertIn(tid, [t["id"] for t in data["tracks"]])
        status, data = self.call(f"/api/playlists/{likes}")
        self.assertEqual(status, 200, data)
        self.assertIn(tid, [t["id"] for t in data["tracks"]])

        for path, payload, method in (
            (f"/api/playlists/{faves}", {"name": "Renamed"}, "PATCH"),
            (f"/api/playlists/{faves}", None, "DELETE"),
            (f"/api/playlists/{likes}/tracks", {"track_id": tid}, "POST"),
        ):
            status, res = self.call(path, payload, method)
            self.assertEqual(status, 409, (path, res))

    def test_02_admin_insights_report_recorded_events(self):
        status, data = self.call("/api/admin/metrics")
        self.assertEqual(status, 200, data)
        self.assertGreaterEqual(data["events"], 3)
        self.assertGreaterEqual(data["by_event"].get("play", 0), 2)
        self.assertEqual(data["by_event"].get("complete"), 1)
        self.assertTrue(data["top_tracks"])
        self.assertTrue(data["listeners"])
        self.assertTrue(data["days"])

        status, users = self.call("/api/admin/users")
        self.assertEqual(status, 200, users)
        uid = users["users"][0]["id"]
        status, data = self.call(f"/api/admin/history/{uid}")
        self.assertEqual(status, 200, data)
        self.assertEqual(data["user"]["username"], "metrics")
        self.assertTrue(data["events"])
        self.assertIn("complete", [e["event"] for e in data["events"]])


if __name__ == "__main__":
    unittest.main()
