"""Generated design artifacts must match their sources in the working tree.

Runs each generator's own ``--check`` mode.  The only skip is a genuinely
missing Node executable (detected with ``shutil.which``); a stale artifact or a
generator error is always a failure with the combined stdout/stderr reported.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")
if NODE is None:
    pytest.skip(
        "node executable not found via shutil.which('node'); "
        "cannot run token generators",
        allow_module_level=True,
    )

SCRIPTS = ("scripts/gen-tokens.mjs", "scripts/gen-lucide.mjs")


def test_generated_files_are_fresh():
    failures = []
    for relative in SCRIPTS:
        script = ROOT / relative
        if not script.is_file():
            continue  # the optional icon generator is not present in this tree
        result = subprocess.run(
            [NODE, str(script), "--check"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        combined = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            failures.append(
                "node %s --check exited %d\n%s"
                % (relative, result.returncode, combined.rstrip())
            )

    assert not failures, (
        "generated files are stale (run the generators listed above):\n%s"
        % "\n".join(failures)
    )
