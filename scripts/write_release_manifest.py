#!/usr/bin/env python3
"""Write the small, tracked release manifest from GitHub's rolling release.

The binaries themselves live on GitHub Releases and in the server's ignored
apps/ cache. This script records only their names, sizes and SHA-256 digests,
so the repository can describe the current release without carrying any bytes.
Called by the release workflow after publication.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get("GH_REPO", os.environ.get("GITHUB_REPOSITORY", "mc20000-01/mcmusic"))
GH = os.environ.get("GH", "gh")
BUILD_DIR = Path(os.environ.get("BUILD_DIR", ROOT / "builds"))
_VERSION = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)")


def latest_release() -> dict:
    raw = subprocess.run(
        [GH, "api", f"repos/{REPO}/releases/latest"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(raw)


def digest(asset: dict) -> str:
    value = str(asset.get("digest") or "")
    if not value.startswith("sha256:"):
        raise SystemExit(f"asset {asset.get('name')!r} has no sha256 digest")
    return value.split(":", 1)[1]


def version_for(rows: list[dict]) -> str:
    for row in rows:
        match = _VERSION.search(row["name"])
        if match:
            return match.group(1)
    raise SystemExit("could not derive a version from release asset names")


def main() -> int:
    release = latest_release()
    rows = []
    for asset in release.get("assets", []):
        name = str(asset.get("name") or "")
        if not name or name == "SHA256SUMS":
            continue
        rows.append({
            "name": name,
            "size": int(asset.get("size") or 0),
            "sha256": digest(asset),
            "url": str(asset.get("browser_download_url") or ""),
        })
    rows.sort(key=lambda row: row["name"])
    if not rows:
        raise SystemExit("latest release has no assets")

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": version_for(rows),
        "tag": release.get("tag_name"),
        "release": release.get("name"),
        "source": f"https://api.github.com/repos/{REPO}/releases/latest",
        "assets": rows,
    }
    (BUILD_DIR / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    sums = "".join(
        f"{row['sha256']}  {row['name']}\n"
        for row in rows if row["name"] != "README.md"
    )
    (BUILD_DIR / "SHA256SUMS").write_text(sums, encoding="utf-8")

    print(f"wrote {BUILD_DIR / 'release-manifest.json'} ({len(rows)} assets)")
    print(f"wrote {BUILD_DIR / 'SHA256SUMS'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
