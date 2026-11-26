"""Offscreen window-construction smoke test for the Qt client.

This is the source-tree twin of the ``--selftest`` check in ``build.ps1``. It
runs the packaged entry point in a subprocess with ``QT_QPA_PLATFORM=offscreen``
so a native crash is reported as a failed test instead of taking down the whole
suite. No display, server, sign-in or audio backend is involved. The old
``tests/test_qt_ui.py`` integration suite needs a fixture server and a working
audio stack on this host; this check only covers the startup crash path.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LINUX = ROOT / "app" / "linux"
sys.path.insert(0, str(LINUX))

from mcmusic_linux.cli import USAGE, _split  # noqa: E402

try:
    if find_spec("PySide6") is None or find_spec("PySide6.QtWidgets") is None:
        raise ImportError("PySide6/QtWidgets is not installed")
except ImportError as exc:
    QT_ERROR = str(exc)
else:
    QT_ERROR = ""


class QtSelftestTests(unittest.TestCase):
    def test_selftest_flag_is_dispatched_as_its_own_mode(self):
        self.assertIn("--selftest", USAGE)
        mode, _, _ = _split(["--tui", "--selftest"])
        self.assertEqual(mode, "selftest")

    @unittest.skipIf(QT_ERROR, f"PySide6 not available: {QT_ERROR}")
    def test_cli_selftest_builds_the_window_offscreen(self):
        with tempfile.TemporaryDirectory(prefix="mcm-qt-selftest-") as tmp:
            env = os.environ.copy()
            env.update({
                "QT_QPA_PLATFORM": "offscreen",
                "XDG_CONFIG_HOME": str(Path(tmp) / "config"),
                "XDG_CACHE_HOME": str(Path(tmp) / "cache"),
                "PYTHONPATH": os.pathsep.join(
                    [str(LINUX), env.get("PYTHONPATH", "")]
                ),
            })
            result = subprocess.run(
                [sys.executable, "-m", "mcmusic_linux", "--selftest"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
            )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, f"selftest output:\n{output}")
        self.assertIn("mcmusic selftest: ok", result.stdout)
        self.assertNotIn("Failed to execute script", output)
        self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
