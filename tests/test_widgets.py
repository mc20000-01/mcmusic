"""Run the embed widget suite under unittest.

The widgets in web/embed/widgets.js are browser custom elements with no browser
runner in this repo, so the suite is a plain ESM script (tests/widgets.test.mjs)
that evaluates them against stubbed DOM and fetch. Wrapping it here keeps
`python -m unittest discover -s tests` a single command for the whole repo, and
the suite skips cleanly where Node is not installed.

    .venv/bin/python -m unittest discover -s tests -v
"""
import os
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "widgets.test.mjs")


class EmbedWidgetsTest(unittest.TestCase):
    def test_every_widget_registers_and_renders(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")

        proc = subprocess.run(
            [node, SCRIPT],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            self.fail(
                "widget suite failed\n"
                f"--- stdout ---\n{proc.stdout}\n"
                f"--- stderr ---\n{proc.stderr}"
            )
        self.assertIn("WIDGETS-TEST-PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
