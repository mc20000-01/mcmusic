"""End-to-end coverage for device pairing (short code -> bearer token).

A real throwaway server is started, an account is registered with a cookie jar,
then a native client trades an 8-character code for a long-lived token and uses
it on ordinary API routes. Rate limiting is raised by the fixture so the suite
measures the pairing flow, not the guard.

    .venv/bin/python -m unittest discover -s tests -v
"""
import http.cookiejar
import json
import os
import sqlite3
import sys
import time
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fixture_server import ThrowawayServer  # noqa: E402


def _call(opener, method, url, data=None, token=None):
    body = None
    if data is not None:
        body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with opener.open(req, timeout=10) as res:
            raw = res.read()
            return res.status, json.loads(raw or b"{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw or b"{}")


class DeviceAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThrowawayServer().start()
        cls.base = cls.server.base
        cls.cookies = http.cookiejar.CookieJar()
        cls.browser = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cls.cookies)
        )
        cls.anon = urllib.request.build_opener()

        status, me = _call(
            cls.browser, "POST", cls.base + "/api/register",
            {"username": "devtester", "password": "hunter22"},
        )
        assert status == 200, (status, me)
        cls.uid = me["id"]

        status, code = _call(cls.browser, "POST", cls.base + "/api/devices/code")
        assert status == 200, (status, code)
        cls.code = code

        # Lowercase + hyphen proves the code is normalised before lookup.
        typed = code["display"].lower()
        status, claimed = _call(
            cls.anon, "POST", cls.base + "/api/devices/claim",
            {"code": typed, "name": "Old 2DS"},
        )
        assert status == 200, (status, claimed)
        cls.claim = claimed
        cls.token = claimed["token"]

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_01_code_is_short_and_human(self):
        self.assertEqual(len(self.code["code"]), 8)
        self.assertEqual(self.code["display"], self.code["code"][:4] + "-" + self.code["code"][4:])
        self.assertGreater(self.code["expires"], time.time())
        self.assertEqual(self.code["account"], "devtester")
        self.assertIn("hint", self.code)

    def test_02_claim_returns_token_and_user(self):
        self.assertTrue(self.token.startswith("mcd_"))
        self.assertEqual(self.claim["user"]["username"], "devtester")
        self.assertEqual(self.claim["name"], "Old 2DS")
        self.assertGreater(self.claim["device_id"], 0)

    def test_03_ping_anonymous_has_no_user(self):
        status, out = _call(self.anon, "GET", self.base + "/api/ping")
        self.assertEqual(status, 200)
        self.assertTrue(out["ok"])
        self.assertIsNone(out["user"])

    def test_04_bearer_token_authenticates(self):
        status, out = _call(self.anon, "GET", self.base + "/api/ping", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(out["user"]["username"], "devtester")

    def test_05_bearer_works_on_session_routes(self):
        status, me = _call(self.anon, "GET", self.base + "/api/me", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(me["username"], "devtester")
        status, devices = _call(self.anon, "GET", self.base + "/api/devices", token=self.token)
        self.assertEqual(status, 200)
        self.assertTrue(any(d["name"] == "Old 2DS" for d in devices["devices"]))

    def test_06_code_is_single_use(self):
        status, out = _call(
            self.anon, "POST", self.base + "/api/devices/claim",
            {"code": self.code["code"], "name": "Second try"},
        )
        self.assertEqual(status, 400)
        self.assertIn("expired", out["error"])

    def test_07_expired_code_is_rejected(self):
        expired = "ZZZZZZZZ"
        db = sqlite3.connect(os.path.join(self.server.data_dir, "mcmusic.db"))
        try:
            db.execute(
                "insert into device_codes(code,user_id,created,expires,used)"
                " values(?,?,?,?,0)",
                (expired, self.uid, time.time() - 600, time.time() - 300),
            )
            db.commit()
        finally:
            db.close()
        status, out = _call(
            self.anon, "POST", self.base + "/api/devices/claim",
            {"code": expired, "name": "Late"},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", out)

    def test_08_token_list_and_revoke(self):
        status, code = _call(self.browser, "POST", self.base + "/api/devices/code")
        self.assertEqual(status, 200)
        status, second = _call(
            self.anon, "POST", self.base + "/api/devices/claim",
            {"code": code["code"], "name": "Spare"},
        )
        self.assertEqual(status, 200)

        status, listed = _call(
            self.anon, "GET", self.base + "/api/devices/tokens", token=self.token
        )
        self.assertEqual(status, 200)
        spare = [t for t in listed["tokens"] if t["name"] == "Spare"]
        self.assertEqual(len(spare), 1)
        self.assertEqual(spare[0]["prefix"], second["token"][:10])

        status, out = _call(
            self.anon, "POST",
            self.base + f"/api/devices/tokens/{spare[0]['id']}/revoke",
            token=self.token,
        )
        self.assertEqual(status, 200)
        self.assertTrue(out["ok"])

        status, ping = _call(
            self.anon, "GET", self.base + "/api/ping", token=second["token"]
        )
        self.assertEqual(status, 200)
        self.assertIsNone(ping["user"])
        # The original device keeps working.
        status, ping = _call(
            self.anon, "GET", self.base + "/api/ping", token=self.token
        )
        self.assertEqual(ping["user"]["username"], "devtester")

    def test_09_unknown_token_is_anonymous(self):
        status, ping = _call(
            self.anon, "GET", self.base + "/api/ping", token="mcd_not-a-real-token"
        )
        self.assertEqual(status, 200)
        self.assertIsNone(ping["user"])


if __name__ == "__main__":
    unittest.main()
