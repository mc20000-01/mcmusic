"""Protected accounts cannot be deleted by the API or by direct SQL."""
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from flask import Flask  # noqa: E402

import database  # noqa: E402
from routes.system_routes import bp as system_bp  # noqa: E402

NOTE = "DO_NOT_DELETE - protected account"


class ProtectedUserTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "protected.db"
        patcher = mock.patch.object(database, "DB_PATH", str(self.path))
        patcher.start()
        self.addCleanup(patcher.stop)

        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        database.ensure_schema(con)
        con.execute(
            "insert into users(username,pw,is_admin,created,notes) values(?,?,?,?,?)",
            ("boss", "not-a-real-hash", 1, time.time(), ""),
        )
        con.execute(
            "insert into users(username,pw,is_admin,created,notes) values(?,?,?,?,?)",
            ("sandisk", "not-a-real-hash", 0, time.time(), NOTE),
        )
        con.commit()
        con.close()

        self.app = Flask(__name__)
        self.app.secret_key = "protected-test"
        self.app.config.update(TESTING=True)
        self.app.register_blueprint(system_bp)

    def test_sqlite_trigger_blocks_direct_delete(self):
        con = sqlite3.connect(self.path)
        with self.assertRaises(sqlite3.IntegrityError):
            con.execute("delete from users where username='sandisk'")
        self.assertTrue(con.execute(
            "select 1 from users where username='sandisk'").fetchone())
        con.close()

    def test_admin_delete_endpoint_refuses(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session["uid"] = 1
        response = client.delete("/api/admin/users/2")
        self.assertEqual(409, response.status_code)
        self.assertIn("protected", response.get_json()["error"])
        con = sqlite3.connect(self.path)
        self.assertTrue(con.execute(
            "select 1 from users where username='sandisk'").fetchone())
        con.close()


if __name__ == "__main__":
    unittest.main()
