"""End-to-end coverage for the cookie-origin (CSRF) guard.

A throwaway server is started once; every test signs in again so a logout from
one case cannot leak state into the next.

    python3 -m pytest tests/test_csrf_guard.py -q
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


def call(opener, method, url, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with opener.open(req, timeout=10) as res:
            return res.status, json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


class CsrfGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThrowawayServer().start()
        cls.base = cls.server.base
        cls.jar = http.cookiejar.CookieJar()
        cls.browser = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cls.jar)
        )
        status, body = call(cls.browser, "POST", cls.base + "/api/register",
                            {"username": "csrfuser", "password": "hunter22"})
        assert status == 200, (status, body)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        status, body = call(self.browser, "POST", self.base + "/api/login",
                            {"username": "csrfuser", "password": "hunter22"})
        self.assertEqual(status, 200, body)

    def logout(self, headers=None, opener=None):
        return call(opener or self.browser, "POST", self.base + "/api/logout",
                    {}, headers)

    def test_same_origin_write_is_allowed(self):
        status, body = self.logout({"Origin": self.base})
        self.assertEqual(status, 200, body)
        self.assertTrue(body["ok"])

    def test_cross_site_origin_is_rejected(self):
        status, body = self.logout({"Origin": "https://evil.example"})
        self.assertEqual(status, 403, body)
        self.assertIn("cross-site", body["error"])

    def test_cross_site_fetch_site_is_rejected_even_with_same_origin(self):
        status, body = self.logout({
            "Origin": self.base,
            "Sec-Fetch-Site": "cross-site",
        })
        self.assertEqual(status, 403, body)

    def test_same_site_fetch_site_is_allowed(self):
        status, body = self.logout({
            "Origin": self.base,
            "Sec-Fetch-Site": "same-site",
        })
        self.assertEqual(status, 200, body)

    def test_missing_headers_are_allowed_for_cookie_clients(self):
        status, body = self.logout()
        self.assertEqual(status, 200, body)

    def test_bearer_token_request_is_exempt(self):
        status, minted = call(self.browser, "POST",
                              self.base + "/api/auth/app/token",
                              {"device": "test"}, {"Origin": self.base})
        self.assertEqual(status, 200, minted)
        native = urllib.request.build_opener()  # no session cookie at all
        status, body = self.logout({
            "Origin": "https://evil.example",
            "Sec-Fetch-Site": "cross-site",
            "Authorization": "Bearer " + minted["token"],
        }, opener=native)
        self.assertEqual(status, 200, body)

    def test_get_with_cross_site_origin_is_allowed(self):
        status, body = call(self.browser, "GET", self.base + "/api/me",
                            headers={"Origin": "https://evil.example"})
        self.assertEqual(status, 200, body)


if __name__ == "__main__":
    unittest.main()
