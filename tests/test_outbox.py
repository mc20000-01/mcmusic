"""Run the browser-side outbox suite under unittest.

The offline queue has no browser runner in this repo, so the suite is a plain
ESM script (tests/outbox.test.mjs) with IndexedDB and fetch stubbed. Wrapping it here means `python -m unittest discover -s tests`
covers the legacy client as well as the server. The suite skips cleanly where
Node or the archived `web/js` source is not present; the current Preact client
lives under `ui/` and is covered by `npm run build`.

    .venv/bin/python -m unittest discover -s tests -v
"""
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "outbox.test.mjs")


class OutboxTest(unittest.TestCase):
    def test_offline_writes_replay_correctly(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        legacy_api = os.path.join(ROOT, "web", "js", "api.js")
        if not os.path.exists(legacy_api):
            self.skipTest("legacy web/js outbox source is archived in old/")

        proc = subprocess.run(
            [node, SCRIPT],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0:
            self.fail(
                "outbox suite failed\n"
                f"--- stdout ---\n{proc.stdout}\n"
                f"--- stderr ---\n{proc.stderr}"
            )
        self.assertIn("OUTBOX-TEST-PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
