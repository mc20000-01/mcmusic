"""Shared preflight for Python tests that rely on the ui/ Node toolchain.

These tests must never fail with a cryptic ``FileNotFoundError`` when a
checkout has no ``ui/node_modules``. Instead they skip with one explicit
instruction: run ``npm ci in ui/``. The committed lockfile is also checked so
dependencies from a different package.json version cannot silently produce
stale generated artifacts.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"
INSTALL = "run npm ci in ui/ and rerun the test"


def problem(*, need_modules: bool = False, sentinel: Path | None = None) -> str | None:
    """Return a skip reason when ui dependencies are unusable, else None."""
    if not shutil.which("node"):
        return f"node executable not found; install Node, then {INSTALL}"
    lock_path = UI / "package-lock.json"
    pkg_path = UI / "package.json"
    if not lock_path.is_file() or not pkg_path.is_file():
        return f"ui/package.json or ui/package-lock.json is missing; {INSTALL}"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"could not read ui lockfiles ({exc}); {INSTALL}"

    version = lock.get("lockfileVersion")
    if version != 3:
        return f"ui/package-lock.json lockfileVersion is {version!r}, expected 3; {INSTALL}"
    root_version = lock.get("packages", {}).get("", {}).get("version")
    package_version = pkg.get("version")
    if root_version != package_version or lock.get("version") != package_version:
        return (
            f"ui lock version {root_version!r} does not match "
            f"ui/package.json {package_version!r}; {INSTALL}"
        )
    if need_modules and not (UI / "node_modules").is_dir():
        return f"ui/node_modules is missing; {INSTALL}"
    if sentinel is not None and not Path(sentinel).is_dir():
        return f"installed dependency {Path(sentinel).relative_to(ROOT)} is missing; {INSTALL}"
    return None
