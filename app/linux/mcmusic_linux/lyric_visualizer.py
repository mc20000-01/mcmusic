"""A compact lyric-sheet visualizer for the Qt desktop client.

Pure PySide6. The animation is a deterministic function of the player's
reported ``position``; ``playing`` only decides whether repaints are needed.
No QtMultimedia objects are created or inspected beyond those two properties,
so opening the lyrics sheet never touches the local audio backend.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

# Flufi identity, kept literal so the panel reads the same in every theme.
VIOLET = QColor("#A06BFF")
INK = QColor("#08060D")


class LyricVisualizer(QWidget):
    """Small Bars / Wave / Glow panel driven entirely by playback position."""

    MODES: tuple[str, ...] = ("Bars", "Wave", "Glow")

    def __init__(self, player, parent=None):
        super().__init__(parent)
        self._player = player
        self._mode = 0
        self.setFixedHeight(104)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Visualizer: Bars — click to cycle (Bars / Wave / Glow)")
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_timeout)

    # ── public API ───────────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self.MODES[self._mode]

    def cycle_mode(self) -> str:
        self._mode = (self._mode + 1) % len(self.MODES)
        self.setToolTip(f"Visualizer: {self.mode} — click to cycle")
        self.update()
        return self.mode

    def stop(self) -> None:
        self._timer.stop()

    # ── player state (read-only) ─────────────────────────────────────────
    def _position(self) -> float:
        try:
            value = float(self._player.position)
        except (AttributeError, TypeError, ValueError):
            return 0.0
        return value if math.isfinite(value) and value > 0 else 0.0

    def _playing(self) -> bool:
        try:
            return bool(self._player.playing)
        except (AttributeError, TypeError, ValueError):
            return False

    def _on_timeout(self) -> None:
        # Position freezes with the media, so a paused track needs no redraws.
        if self._playing():
            self.update()

    # ── lifecycle ────────────────────────────────────────────────────────
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event) -> None:
        self.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        self.stop()
        super().closeEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.cycle_mode()
            event.accept()
            return
        super().mousePressEvent(event)

    # ── painting ─────────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(INK)
        p.drawRoundedRect(rect, 10, 10)
        wash = QColor(VIOLET)
        wash.setAlpha(18)
        p.setBrush(wash)
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        edge = QColor(VIOLET)
        edge.setAlpha(72)
        p.setPen(QPen(edge, 1))
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        p.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)

        t = self._position()
        if self._mode == 0:
            self._draw_bars(p, rect, t)
        elif self._mode == 1:
            self._draw_wave(p, rect, t)
        else:
            self._draw_glow(p, rect, t)
        self._draw_chip(p, rect)

    @staticmethod
    def _inner(rect: QRectF) -> QRectF:
        # Extra headroom keeps the mode chip clear of the animation.
        return rect.adjusted(12, 26, -12, 12)

    def _draw_bars(self, p: QPainter, rect: QRectF, t: float) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        count = 26
        gap = 3.0
        bar_w = max(1.5, (inner.width() - gap * (count - 1)) / count)
        base = inner.bottom()
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(count):
            a = math.sin(t * 2.17 + i * 0.53)
            b = math.sin(t * 0.91 - i * 0.29 + 1.1)
            c = math.sin(t * 3.31 + i * 0.11 + 2.4)
            energy = min(1.0, max(0.08, 0.42 + 0.28 * a + 0.18 * b + 0.10 * c))
            h = energy * inner.height() * 0.94
            x = inner.left() + i * (bar_w + gap)
            color = QColor(VIOLET)
            color.setAlphaF(0.35 + 0.6 * energy)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, base - h, bar_w, h), bar_w / 2, bar_w / 2)
        baseline = QColor(VIOLET)
        baseline.setAlpha(38)
        p.setPen(QPen(baseline, 1))
        p.drawLine(QPointF(inner.left(), base + 1), QPointF(inner.right(), base + 1))

    def _draw_wave(self, p: QPainter, rect: QRectF, t: float) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        mid = inner.center().y()
        amp = inner.height() * 0.32
        steps = max(32, int(inner.width() / 4))

        def wave(u: float, phase: float) -> float:
            return (
                0.60 * math.sin(u * math.tau * 2.0 + t * 2.0 + phase)
                + 0.28 * math.sin(u * math.tau * 5.0 - t * 1.3 + phase * 0.5)
                + 0.12 * math.sin(u * math.tau * 9.0 + t * 0.7 - phase)
            )

        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        for phase, alpha, width in ((0.0, 205, 2.2), (1.35, 78, 1.4)):
            path = QPainterPath()
            for step in range(steps + 1):
                u = step / steps
                x = inner.left() + inner.width() * u
                y = mid + amp * wave(u, phase)
                if step == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            color = QColor(VIOLET)
            color.setAlpha(alpha)
            p.setPen(QPen(color, width))
            p.drawPath(path)

    def _draw_glow(self, p: QPainter, rect: QRectF, t: float) -> None:
        inner = self._inner(rect)
        if inner.isEmpty():
            return
        center = QPointF(inner.center().x(), inner.center().y())
        pulse = 0.5 + 0.5 * math.sin(t * 1.7)
        base = min(inner.width(), inner.height()) * (0.22 + 0.06 * pulse)
        p.setPen(Qt.PenStyle.NoPen)
        for ring in range(4):
            radius = base * (1.0 + ring * 0.62)
            grad = QRadialGradient(center, radius)
            core = QColor(VIOLET)
            core.setAlphaF(0.30 * (1.0 - ring / 4.0) * (0.65 + 0.35 * pulse))
            edge = QColor(VIOLET)
            edge.setAlpha(0)
            grad.setColorAt(0.0, core)
            grad.setColorAt(1.0, edge)
            p.setBrush(grad)
            p.drawEllipse(center, radius, radius)
        p.setBrush(VIOLET)
        dot = 3.5 + 2.0 * pulse
        p.drawEllipse(center, dot, dot)

    def _draw_chip(self, p: QPainter, rect: QRectF) -> None:
        label = f"{self.mode.upper()} >"
        font = QFont()
        font.setFamily("monospace")
        font.setPointSize(9)
        font.setBold(True)
        p.setFont(font)
        width = QFontMetrics(font).horizontalAdvance(label) + 20
        chip = QRectF(rect.right() - 12 - width, rect.top() + 8, width, 20)
        back = QColor(VIOLET)
        back.setAlpha(34)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(back)
        p.drawRoundedRect(chip, 10, 10)
        p.setPen(QPen(VIOLET))
        p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), label)
