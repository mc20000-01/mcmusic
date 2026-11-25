"""Run the pure web icon-style assertions from the Python test suite."""
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WebIconStyleTests(unittest.TestCase):
    def test_theme_helpers_match_native_clients(self):
        result = subprocess.run(
            ["node", "--experimental-strip-types", "tests/icons.test.mjs"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
