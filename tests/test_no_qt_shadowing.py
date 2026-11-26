"""Guard against storing widget attributes under names Qt already uses.

The 4.0.1 Windows crash was caused by ``self.update = McButton(...)``: it
replaced the inherited ``QWidget.update()`` method. This test scans the Qt
client source and fails as soon as that pattern comes back.
"""
from __future__ import annotations

import ast
import os
import pathlib
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QComboBox,
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTabWidget,
    QTableView,
    QTextEdit,
    QToolButton,
    QTreeView,
    QWidget,
)

QT_CLASSES = (
    QObject, QWidget, QAbstractButton, QPushButton, QToolButton, QFrame,
    QLabel, QDialog, QLineEdit, QScrollArea, QMainWindow, QTextEdit,
    QComboBox, QSlider, QListView, QTableView, QTreeView, QStackedWidget,
    QTabWidget,
)
QT_BASE_NAMES = {cls.__name__ for cls in QT_CLASSES}
QT_MEMBERS = {name for cls in QT_CLASSES for name in dir(cls)}

# Intentional overrides must be justified here. The list is empty: every Qt
# member name in the client is now free, including `update`, `window`, `layout`,
# `pos`, `icon`, `scroll`, `actions` and `clear`.
ALLOWLIST: set[tuple[str, str]] = set()

QT_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "linux" / "mcmusic_linux"


def assigned_self_attributes(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {ast.unparse(base) for base in node.bases}
        if not bases & QT_BASE_NAMES:
            continue
        for stmt in ast.walk(node):
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                continue
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            for target in targets:
                if (isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"):
                    yield node.name, target.attr, stmt.lineno


class QtShadowingTests(unittest.TestCase):
    def test_no_qt_members_are_shadowed(self) -> None:
        offenders = []
        for path in sorted(QT_DIR.glob("*.py")):
            for class_name, attr, line in assigned_self_attributes(path):
                if attr.startswith("_") or attr in ALLOWLIST:
                    continue
                if attr in QT_MEMBERS:
                    offenders.append(f"{path.name}:{line} {class_name}.{attr}")
        self.assertEqual([], offenders, "Qt members shadowed by stored attributes")


if __name__ == "__main__":
    unittest.main()
