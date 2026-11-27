"""The shared ui dependency preflight skips with an actionable message."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ui_deps


class UiDepsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ui-deps-")
        self.addCleanup(self.temp.cleanup)
        self.tmp = Path(self.temp.name)
        (self.tmp / "node_modules").mkdir(parents=True)
        (self.tmp / "package.json").write_text(
            json.dumps({"version": "4.3.0"}), encoding="utf-8"
        )
        self.lock = {
            "name": "mcmusic-ui",
            "version": "4.3.0",
            "lockfileVersion": 3,
            "packages": {"": {"version": "4.3.0"}},
        }
        (self.tmp / "package-lock.json").write_text(
            json.dumps(self.lock), encoding="utf-8"
        )
        self.patch = mock.patch.object(ui_deps, "UI", self.tmp)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_fresh_lock_and_modules_are_ready(self):
        self.assertIsNone(ui_deps.problem(need_modules=True))

    def test_missing_modules_points_at_npm_ci(self):
        shutil.rmtree(self.tmp / "node_modules")
        reason = ui_deps.problem(need_modules=True)
        self.assertIsNotNone(reason)
        self.assertIn("npm ci in ui/", reason)

    def test_wrong_lockfile_version_points_at_npm_ci(self):
        self.lock["lockfileVersion"] = 2
        (self.tmp / "package-lock.json").write_text(
            json.dumps(self.lock), encoding="utf-8"
        )
        reason = ui_deps.problem()
        self.assertIsNotNone(reason)
        self.assertIn("lockfileVersion is 2", reason)
        self.assertIn("npm ci in ui/", reason)

    def test_version_mismatch_points_at_npm_ci(self):
        self.lock["packages"][""]["version"] = "4.2.0"
        (self.tmp / "package-lock.json").write_text(
            json.dumps(self.lock), encoding="utf-8"
        )
        reason = ui_deps.problem()
        self.assertIsNotNone(reason)
        self.assertIn("does not match", reason)
        self.assertIn("npm ci in ui/", reason)


if __name__ == "__main__":
    unittest.main()
