"""Shipped Python must not pass shell=True to subprocess.

The original security report cited ``src/mcmusic.py:376``; in the audited tree
that line is a JSON response field (``shell=SHELL_VERSION``), not a subprocess
call, and no tracked Python source uses a shell interpreter. This guard keeps
that property from regressing. Legitimate shell use would need an explicit
documented exception here, which this test deliberately does not provide.
"""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("src", "app", "scripts")
SHELL_TRUE = re.compile(r"\bshell\s*=\s*True\b")


class NoShellTrueTest(unittest.TestCase):
    def test_no_shell_true_in_shipped_python(self):
        offenders = []
        for name in SCAN_ROOTS:
            for path in sorted((ROOT / name).rglob("*.py")):
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if SHELL_TRUE.search(line):
                        offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
        self.assertEqual(offenders, [], "shell=True found in shipped Python")


if __name__ == "__main__":
    unittest.main()
