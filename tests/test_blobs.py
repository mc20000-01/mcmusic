"""Blob geometry is a shared, generated contract across every client.

The authored shapes live in ``design/tokens.json``; each client consumes a
generated copy so no path can drift by hand.  Paths are normalised to a
100x100 viewBox.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ("blob-1", "blob-2", "blob-3", "blob-4", "blob-5")


def authored():
    return json.loads((ROOT / "design/tokens.json").read_text())


def test_blob_tokens_are_generated_verbatim():
    blobs = authored()["blobs"]
    generated = json.loads((ROOT / "design/tokens.generated.json").read_text())

    assert [blob["id"] for blob in blobs] == list(IDS)
    assert generated["blobs"] == blobs

    for blob in blobs:
        assert blob["shape"]
        assert blob["borderRadius"]
        path = blob["path"]
        assert path.startswith("M ") and path.endswith(" Z"), blob["id"]
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", path)]
        assert all(-2 <= n <= 102 for n in numbers), blob["id"]
        assert min(numbers) <= 5 and max(numbers) >= 95, blob["id"]


def test_every_client_carries_authored_geometry():
    blobs = authored()["blobs"]
    targets = (
        ROOT / "ui/src/common/blobs.generated.ts",
        ROOT / "gui/android/app/src/main/java/dev/mcmusic/app/ui/design/Blobs.kt",
        ROOT / "app/ios/McMusic/Blobs.swift",
        ROOT / "app/linux/mcmusic_linux/blobs.py",
    )
    for target in targets:
        assert target.is_file(), f"missing generated blob module: {target}"
        text = target.read_text()
        for blob in blobs:
            assert json.dumps(blob["path"]) in text, f"{target.name}: stale {blob['id']} path"
            assert json.dumps(blob["borderRadius"]) in text, f"{target.name}: stale {blob['id']} radius"

    css = (ROOT / "ui/src/env.css").read_text()
    for blob in blobs:
        assert f"--{blob['id']}-radius: {blob['borderRadius']};" in css, blob["id"]
