"""End-to-end coverage for the RoturLink friend-code claim flow.

Runs against a throwaway DATA_DIR with a real Flask request context, so the
claim route exercises the schema, the pending handoff and account creation
together. Rotur's network calls are not involved: the callback is simulated by
stashing a verified pending identity, which is exactly what callback_route does.

    .venv/bin/python -m unittest discover -s tests -v
"""
import os
import shutil
import sys
import tempfile
import time
import unittest

_TMP = tempfile.mkdtemp(prefix="mcm-claim-test-")
os.environ["DATA_DIR"] = _TMP
os.environ.pop("INVITE_CODE", None)
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"),
)

from flask import Flask  # noqa: E402

import database  # noqa: E402
import rotur  # noqa: E402
from auth import create_user  # noqa: E402


def tearDownModule():
    shutil.rmtree(_TMP, ignore_errors=True)


class RoturClaimTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "claim-test"
        database.init_db(self.app)
        with self.app.app_context():
            c = database._db()
            for table in ("rotur_pending", "rotur_sessions", "users", "invite_codes"):
                c.execute(f"delete from {table}")
            c.commit()

    @staticmethod
    def _pending(name="tester", rid="4242"):
        return {
            "rid": rid,
            "name": name,
            "access": "access-value",
            "refresh": "refresh-value",
            "expires_at": 0,
            "ticket": "",
            "next": "",
        }

    def _count(self, c, table):
        return c.execute(f"select count(*) n from {table}").fetchone()["n"]

    def test_bootstrap_claim_creates_the_account(self):
        """On a fresh server the first Rotur identity claims without a code."""
        with self.app.app_context():
            c = database._db()
            with self.app.test_request_context(
                "/api/auth/rotur/claim", method="POST", data={}
            ):
                rotur._stash_pending(c, self._pending())
                resp = rotur.claim_route()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.headers["Location"], "/")
            user = c.execute("select username, rotur_id from users").fetchone()
            self.assertEqual(user["rotur_id"], "4242")
            self.assertEqual(user["username"], "tester")
            self.assertEqual(self._count(c, "rotur_pending"), 0)
            self.assertEqual(self._count(c, "rotur_sessions"), 1)

    def test_existing_server_requires_a_friend_code(self):
        """The pending identity must survive a rejected claim for a retry."""
        with self.app.app_context():
            c = database._db()
            create_user(c, "owner", "secret1")
            with self.app.test_request_context(
                "/api/auth/rotur/claim", method="POST", data={"invite": ""}
            ):
                rotur._stash_pending(c, self._pending())
                resp = rotur.claim_route()

            self.assertEqual(resp.status_code, 403)
            self.assertIn(b"Friend code required", resp.data)
            self.assertEqual(self._count(c, "users"), 1)
            self.assertEqual(self._count(c, "rotur_pending"), 1)

    def test_valid_friend_code_claims_and_consumes_a_use(self):
        with self.app.app_context():
            c = database._db()
            create_user(c, "owner", "secret1")
            c.execute(
                "insert into invite_codes(code, created, max_uses, uses, expires, active)"
                " values('INV-1', ?, 2, 0, 0, 1)",
                (time.time(),),
            )
            c.commit()
            with self.app.test_request_context(
                "/api/auth/rotur/claim", method="POST", data={"invite": "INV-1"}
            ):
                rotur._stash_pending(c, self._pending(name="newcomer", rid="777"))
                resp = rotur.claim_route()

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(self._count(c, "users"), 2)
            claimed = c.execute(
                "select id, rotur_id from users where rotur_id='777'"
            ).fetchone()
            self.assertIsNotNone(claimed)
            invites = c.execute("select uses from invite_codes where code='INV-1'").fetchone()
            self.assertEqual(invites["uses"], 1)
            self.assertEqual(self._count(c, "rotur_pending"), 0)

    def test_expired_pending_claim_is_refused(self):
        with self.app.app_context():
            c = database._db()
            with self.app.test_request_context(
                "/api/auth/rotur/claim", method="POST", data={}
            ):
                token = rotur._stash_pending(c, self._pending())
                c.execute(
                    "update rotur_pending set created=? where token=?", (0, token)
                )
                c.commit()
                resp = rotur.claim_route()

            self.assertEqual(resp.status_code, 403)
            self.assertIn(b"Sign-in expired", resp.data)
            self.assertEqual(self._count(c, "users"), 0)
            self.assertEqual(self._count(c, "rotur_pending"), 0)


if __name__ == "__main__":
    unittest.main()
