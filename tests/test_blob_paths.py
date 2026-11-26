"""Offscreen coverage for the Qt blob-path reader.

Generated blob paths are authored once in ``design/tokens.json`` and carried
into the Qt client verbatim. These checks make sure every shipped id parses,
stays inside the normalised 100x100 box, scales into a target rect, and maps
names onto stable ids across processes.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

pytest.importorskip("PySide6.QtCore")
pytest.importorskip("PySide6.QtGui")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app" / "linux"))

from PySide6.QtCore import QRectF  # noqa: E402

from mcmusic_linux.blobs import BLOB_PATHS  # noqa: E402
from mcmusic_linux.blob_paths import blob_id_for, blob_path  # noqa: E402

EPS = 1e-6


def test_every_generated_id_parses_inside_the_normalised_box():
    assert set(BLOB_PATHS) == {f"blob-{i}" for i in range(1, 6)}
    for blob_id in BLOB_PATHS:
        path = blob_path(blob_id, QRectF(0, 0, 100, 100))
        assert path.elementCount() >= 10, blob_id
        bounds = path.boundingRect()
        assert -EPS <= bounds.left() <= bounds.right() <= 100 + EPS, blob_id
        assert -EPS <= bounds.top() <= bounds.bottom() <= 100 + EPS, blob_id
        assert bounds.width() > 50 and bounds.height() > 50, blob_id


def test_blob_path_fits_a_target_rect():
    target = QRectF(10, 20, 60, 30)
    bounds = blob_path("blob-2", target).boundingRect()
    assert target.left() - EPS <= bounds.left() <= bounds.right() <= target.right() + EPS
    assert target.top() - EPS <= bounds.top() <= bounds.bottom() <= target.bottom() + EPS
    assert bounds.width() < target.width()
    assert bounds.height() < target.height()


def test_blob_id_for_is_stable_and_generated():
    known = {
        "": "blob-1",
        "a": "blob-1",
        "b": "blob-2",
        "c": "blob-4",
        "Seeded Song": "blob-3",
    }
    for name, expected in known.items():
        assert blob_id_for(name) == expected
        assert blob_id_for(name) == blob_id_for(name)
        assert blob_id_for(name) in BLOB_PATHS
