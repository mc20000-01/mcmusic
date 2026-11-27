"""End-to-end coverage for the authentication failure throttle.

Real throwaway servers are used so the database, Flask hooks and proxy setting
are the ones production uses. The limit/window are lowered in most cases to keep
the suite quick; the lockout test uses the shipped 10/900 defaults.

    python3 -m pytest tests/test_auth_throttle.py -q
"""
import http.cookiejar
import json
import os
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fixture_server import ThrowawayServer  # noqa: E402


def call(opener, method, url, data=None, xff=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if xff:
        req.add_header("X-Forwarded-For", xff)
    try:
        with opener.open(req, timeout=10) as res:
            return res.status, json.loads(res.read() or b"{}"), res.headers
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}"), exc.headers


def browser():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def register(base, username, password="hunter22", invite=None):
    data = {"username": username, "password": password}
    if invite:
        data["invite"] = invite
    status, body, _ = call(browser(), "POST", base + "/api/register", data)
    assert status == 200, (status, body)
    return body


class AuthThrottleTest(unittest.TestCase):
    def test_default_lockout_has_no_artificial_sleep(self):
        # Source check: password hashing is deliberately slow, so a timing
        # threshold cannot distinguish it from the old fixed sleep.
        source = (Path(__file__).resolve().parents[1] / "src" / "routes"
                  / "auth_routes.py").read_text(encoding="utf-8")
        for name in ("login", "app_login"):
            start = source.index(f"def {name}(")
            end = source.find("\ndef ", start + 1)
            body = source[start:end if end > 0 else None]
            self.assertNotIn("sleep", body, f"{name} still sleeps")

        with ThrowawayServer().start() as server:
            base = server.base
            register(base, "alice")
            for _ in range(10):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "alice", "password": "wrong"})
                self.assertEqual(status, 401)

            status, body, headers = call(
                browser(), "POST", base + "/api/login",
                {"username": "alice", "password": "wrong"},
            )
            self.assertEqual(status, 429, body)
            retry = int(headers.get("Retry-After", "0"))
            self.assertGreaterEqual(retry, 1)
            self.assertLessEqual(retry, 900)

            # The correct password cannot bypass an active lockout.
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "alice", "password": "hunter22"})
            self.assertEqual(status, 429)

    def test_expiry_and_success_reset(self):
        env = {"AUTH_THROTTLE_LIMIT": "2", "AUTH_THROTTLE_WINDOW": "3"}
        with ThrowawayServer().start(env) as server:
            base = server.base
            register(base, "bob")
            for _ in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "bob", "password": "wrong"})
                self.assertEqual(status, 401)
            status, _, headers = call(browser(), "POST", base + "/api/login",
                                      {"username": "bob", "password": "wrong"})
            self.assertEqual(status, 429)
            self.assertGreaterEqual(int(headers.get("Retry-After", "0")), 1)

            time.sleep(3.2)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "bob", "password": "hunter22"})
            self.assertEqual(status, 200)

            # A success cleared the account counter: two fresh failures are
            # needed before the next attempt is blocked again.
            for _ in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "bob", "password": "wrong"})
                self.assertEqual(status, 401)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "bob", "password": "wrong"})
            self.assertEqual(status, 429)

    def test_account_and_ip_are_isolated_when_proxy_is_configured(self):
        env = {
            "AUTH_THROTTLE_LIMIT": "2",
            "AUTH_THROTTLE_WINDOW": "60",
            "TRUST_PROXY": "1",
        }
        with ThrowawayServer().start(env) as server:
            base = server.base
            register(base, "carol")
            register(base, "dave", invite=server.invite)
            # Lock carol's account from one IP (which also locks that IP).
            for _ in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "carol", "password": "wrong"},
                                    xff="10.0.0.1")
                self.assertEqual(status, 401)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "carol", "password": "hunter22"},
                                xff="10.0.0.1")
            self.assertEqual(status, 429)

            # A different account from a different IP is unaffected.
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "dave", "password": "hunter22"},
                                xff="10.0.0.2")
            self.assertEqual(status, 200)
            # The account lock follows carol even when her IP is clean.
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "carol", "password": "hunter22"},
                                xff="10.0.0.3")
            self.assertEqual(status, 429)

            # An IP-only lock (unknown account) does not follow a clean IP.
            for _ in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "ghost", "password": "wrong"},
                                    xff="10.0.0.5")
                self.assertEqual(status, 401)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "dave", "password": "hunter22"},
                                xff="10.0.0.5")
            self.assertEqual(status, 429)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "dave", "password": "hunter22"},
                                xff="10.0.0.6")
            self.assertEqual(status, 200)

    def test_forwarded_for_is_ignored_without_opt_in(self):
        env = {"AUTH_THROTTLE_LIMIT": "2", "AUTH_THROTTLE_WINDOW": "60"}
        with ThrowawayServer().start(env) as server:
            base = server.base
            register(base, "erin")
            for n in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/login",
                                    {"username": "erin", "password": "wrong"},
                                    xff=f"10.1.0.{n + 1}")
                self.assertEqual(status, 401)
            status, _, _ = call(browser(), "POST", base + "/api/login",
                                {"username": "erin", "password": "wrong"},
                                xff="10.1.0.99")
            self.assertEqual(status, 429)

    def test_pair_and_app_login_are_throttled(self):
        env = {"AUTH_THROTTLE_LIMIT": "2", "AUTH_THROTTLE_WINDOW": "60"}
        with ThrowawayServer().start(env) as server:
            base = server.base
            register(base, "frank")
            for _ in range(2):
                status, _, _ = call(browser(), "POST",
                                    base + "/api/devices/claim", {"code": "NOPE1234"})
                self.assertEqual(status, 400)
            status, _, headers = call(browser(), "POST",
                                      base + "/api/devices/claim", {"code": "NOPE1234"})
            self.assertEqual(status, 429)
            self.assertGreaterEqual(int(headers.get("Retry-After", "0")), 1)

            for _ in range(2):
                status, _, _ = call(browser(), "POST", base + "/api/auth/app/login",
                                    {"username": "frank", "password": "wrong"})
                self.assertEqual(status, 401)
            status, _, _ = call(browser(), "POST", base + "/api/auth/app/login",
                                {"username": "frank", "password": "hunter22"})
            self.assertEqual(status, 429)


if __name__ == "__main__":
    unittest.main()
