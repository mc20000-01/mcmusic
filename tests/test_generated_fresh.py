"""Generated design artifacts must match their sources in the working tree.

Runs each generator's own ``--check`` mode.  The only skip is a genuinely
missing Node executable (detected with ``shutil.which``); a stale artifact or a
generator error is always a failure with the combined stdout/stderr reported.
"""
import subprocess
from pathlib import Path

import pytest

from ui_deps import problem

ROOT = Path(__file__).resolve().parents[1]
_skip = problem(need_modules=True)
if _skip:
    pytest.skip(_skip, allow_module_level=True)
NODE = "node"

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
