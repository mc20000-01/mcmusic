"""Custom-painted widgets that carry the mcmusic look natively.

Everything here draws with QPainter from the shared palette tokens: squared
blocks, hairline rules, mono labels, brass accent. No HTML, no QWebEngine.
"""
from __future__ import annotations

import inspect
from typing import Callable, Optional, Sequence

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .art import ART
from .icons import draw_icon
from .models import Track, fmt_time

STATE = {"covers": True, "density": "comfy"}


def set_covers(enabled: bool) -> None:
    STATE["covers"] = bool(enabled)


def set_density(value: str) -> None:
    STATE["density"] = "compact" if value == "compact" else "comfy"


def C(token: str, alpha: Optional[int] = None) -> QColor:
    color = QColor(getattr(theme.pal(), token))
    if alpha is not None:
        color.setAlpha(alpha)
    return color


def refresh_theme(root: QWidget) -> None:
    for widget in [root, *root.findChildren(QWidget)]:
        hook = getattr(widget, "refresh_theme", None)
        # Qt callables (signals, wrapper objects) can surface under Python
        # attribute names; only invoke hooks we actually declared as methods.
        if inspect.ismethod(hook) or inspect.isfunction(hook):
            hook()
        # Use the inherited QWidget implementation: a widget can legitimately
        # hold a field called `update` (for example a Download button), which
        # shadows the repaint method and made theme refresh crash at startup.
        if isinstance(widget, QWidget):
            QWidget.update(widget)
        else:
            widget.update()


def _fm(font: QFont, text: str) -> int:
    return QFontMetrics(font).horizontalAdvance(text)


def _elide(font: QFont, text: str, width: float) -> str:
    return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, max(8, int(width)))


# ── primitives ──────────────────────────────────────────────────────────────


class Rule(QWidget):
    def __init__(self, height: int = 1, token: str = "line", parent=None):
        super().__init__(parent)
        self._token = token
        self.setFixedHeight(height)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), C(self._token))


class Txt(QLabel):
    def __init__(self, text: str = "", *, size: float = 13, token: str = "fg",
                 family: str = "ui", weight: QFont.Weight = QFont.Weight.Normal,
                 spacing: float = 0.0, wrap: bool = False, selectable: bool = False,
                 align: Qt.AlignmentFlag | None = None, parent=None):
        super().__init__(text, parent)
        self._token = token
        if family == "display":
            self._font = theme.display(size, weight)
        elif family == "mono":
            self._font = theme.mono(size, weight, spacing)
        else:
            self._font = theme.ui(size, weight)
        self.setFont(self._font)
        self.setWordWrap(wrap)
        if align is not None:
            self.setAlignment(align)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse if selectable
            else Qt.TextInteractionFlag.NoTextInteraction
        )
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"color: {getattr(theme.pal(), self._token)}; background: transparent;")

    def set_token(self, token: str) -> None:
        self._token = token
        self.refresh_theme()


class Glyph(QWidget):
    def __init__(self, name: str, size: int = 16, token: str = "dim",
                 fill: bool = False, stroke: float | None = None, parent=None):
        super().__init__(parent)
        self._name = name
        self._token = token
        self._fill = fill
        self._stroke = stroke
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_icon(p, self._name, QRectF(self.rect()), getattr(theme.pal(), self._token),
                  self._stroke, self._fill)

    def set_icon(self, name: str) -> None:
        self._name = name
        self.update()


class IconButton(QAbstractButton):
    def __init__(self, name: str, *, size: int = 32, icon_size: float = 17,
                 token: str = "dim", active_token: str = "accent", fill: bool = False,
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        self._name = name
        self._icon_size = icon_size
        self._token = token
        self._active_token = active_token
        self._fill = fill
        self._active = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def set_icon(self, name: str) -> None:
        if self._name != name:
            self._name = name
            self.update()

    def set_fill(self, fill: bool) -> None:
        self._fill = fill
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.underMouse() or self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent", 42) if self._active else C("surface"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)
        color = getattr(theme.pal(), self._active_token if self._active else
                        ("fg" if self.underMouse() else self._token))
        side = min(self.width(), self.height()) * (self._icon_size / max(1, self.width()))
        rect = QRectF(0, 0, side, side)
        rect.moveCenter(QRectF(self.rect()).center())
        draw_icon(p, self._name, rect, color, fill=self._fill)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class McButton(QAbstractButton):
    def __init__(self, text: str, *, solid: bool = False, ghost: bool = False,
                 danger: bool = False, small: bool = False, icon: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        self._text = text
        self._symbol = icon
        self._solid = solid
        self._ghost = ghost
        self._danger = danger
        self._small = small
        self._font = theme.mono(9 if small else 10, QFont.Weight.DemiBold, 1.1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(28 if small else 36)
        self.setMinimumWidth(self.sizeHint().width())

    def set_text(self, text: str) -> None:
        self._text = text
        self.setMinimumWidth(self.sizeHint().width())
        self.update()

    def sizeHint(self) -> QSize:
        label = self._text.upper()
        width = _fm(self._font, label) + (34 if not self._small else 24)
        if self._symbol:
            width += 20 if not self._small else 17
        return QSize(max(52, width), 28 if self._small else 36)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 14 if self._small else 18
        hover = self.underMouse()
        if self._solid:
            bg = C("accent")
            if hover:
                bg = C("accent").lighter(108)
            border = bg
            fg = C("accent_fg")
        elif self._ghost:
            bg = C("surface") if hover else QColor(0, 0, 0, 0)
            border = QColor(0, 0, 0, 0)
            fg = C("fg" if hover else "dim")
        elif self._danger:
            bg = C("err", 30) if hover else QColor(0, 0, 0, 0)
            border = C("err", 120)
            fg = C("err")
        else:
            bg = C("surface") if hover else QColor(0, 0, 0, 0)
            border = C("dim2" if hover else "line2")
            fg = C("fg")
        if not self.isEnabled():
            fg = C("dim2")
            bg = QColor(0, 0, 0, 0) if not self._solid else C("line")
            border = C("line")
        # A tonal underlay gives the button a soft second layer on every palette.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("accent" if self._solid else "line2", 34))
        p.drawRoundedRect(rect.translated(0, 2), radius, radius)
        p.setPen(QPen(border, 1))
        p.setBrush(bg)
        p.drawRoundedRect(rect, radius, radius)

        label = self._text.upper()
        icon_w = 0
        if self._symbol:
            icon_w = 15
        text_w = _fm(self._font, label)
        total = text_w + (icon_w + 7 if self._symbol else 0)
        x = rect.center().x() - total / 2
        if self._symbol:
            icon_rect = QRectF(x, rect.center().y() - 7, 14, 14)
            draw_icon(p, self._symbol, icon_rect, fg)
            x += icon_w + 7
        p.setFont(self._font)
        p.setPen(QPen(fg))
        p.drawText(QRectF(x, rect.top(), text_w + 4, rect.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class NavButton(QAbstractButton):
    def __init__(self, text: str, icon: str, *, parent=None):
        super().__init__(parent)
        self._text = text
        self._icon = icon
        self._active = False
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._font = theme.ui(13, QFont.Weight.Medium)
        self.setFont(self._font)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0, 1, 0, -1)
        if self._active or self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent", 46) if self._active else C("surface"))
            p.drawRoundedRect(rect, 18, 18)
        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent"))
            p.drawRoundedRect(QRectF(4, 8, 4, self.height() - 16), 2, 2)
        draw_icon(p, self._icon, QRectF(12, (self.height() - 16) / 2, 16, 16),
                  C("accent" if self._active else "dim"))
        p.setFont(self._font)
        p.setPen(QPen(C("fg" if self._active else "dim")))
        p.drawText(QRectF(38, 0, self.width() - 42, self.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), self._text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class PlaylistNavButton(QAbstractButton):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._active = False
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._font = theme.ui(13)
        self.setFont(self._font)

    def set_text(self, text: str) -> None:
        self._text = text
        self.update()

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self._active or self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent", 42) if self._active else C("surface"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 15, 15)
        p.setFont(self._font)
        p.setPen(QPen(C("fg" if self._active else "dim")))
        text = QFontMetrics(self._font).elidedText(
            self._text, Qt.TextElideMode.ElideRight, self.width() - 20
        )
        p.drawText(QRectF(10, 0, self.width() - 20, self.height()),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


# ── artwork ────────────────────────────────────────────────────────────────


class Artwork(QWidget):
    clicked = Signal()

    def __init__(self, size: int = 46, round_: bool = False, kind: str = "disc",
                 shadow: bool = False, parent=None):
        super().__init__(parent)
        self._size = size
        self._round = round_
        self._kind = kind
        self._shadow = shadow
        self._track_id: Optional[int] = None
        self._pixmap: Optional[QPixmap] = None
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        ART.loaded.connect(self._art_loaded)

    @property
    def kind(self) -> str:
        return self._kind

    def set_cover(self, track_id: Optional[int], kind: Optional[str] = None) -> None:
        if kind:
            self._kind = kind
        if track_id == self._track_id:
            return
        self._track_id = track_id
        self._pixmap = ART.request(track_id) if STATE["covers"] else None
        self.update()

    def set_pixmap(self, pixmap: Optional[QPixmap]) -> None:
        self._pixmap = pixmap
        self.update()

    def _art_loaded(self, track_id: int) -> None:
        if track_id == self._track_id and STATE["covers"]:
            self._pixmap = ART.cached(track_id)
            self.update()

    def _path(self, rect: QRectF) -> QPainterPath:
        path = QPainterPath()
        if self._round:
            path.addEllipse(rect)
        else:
            path.addRoundedRect(rect, 12, 12)
        return path

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self._shadow:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent", 58))
            shadow = QRectF(rect).translated(3, 5)
            if self._round:
                p.drawEllipse(shadow)
            else:
                p.drawRoundedRect(shadow, 14, 14)
        path = self._path(rect)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface2"))
        p.drawPath(path)
        p.save()
        p.setClipPath(path)
        if self._pixmap is not None and not self._pixmap.isNull() and STATE["covers"]:
            pm = self._pixmap.scaled(
                int(rect.width()), int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRect((pm.width() - rect.width()) / 2, (pm.height() - rect.height()) / 2,
                        rect.width(), rect.height())
            p.drawPixmap(rect, pm, QRectF(src))
        else:
            icon = "users" if self._kind == "artist" else "disc-3"
            side = rect.width() * 0.38
            box = QRectF(0, 0, side, side)
            box.moveCenter(rect.center())
            p.setOpacity(0.5)
            draw_icon(p, icon, box, C("dim2"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(C("line"), 1))
        p.drawPath(path)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


# ── track table ────────────────────────────────────────────────────────────


class TrackList(QWidget):
    """Virtualised track table: paints only the rows in the damage rect."""

    play_requested = Signal(int)
    like_requested = Signal(object)
    more_requested = Signal(object, int, object)

    def __init__(self, *, show_stats: bool = False, parent=None,
                 like_enabled: bool = True):
        super().__init__(parent)
        self.tracks: list[Track] = []
        self.current_id: Optional[int] = None
        self.show_stats = show_stats
        self.like_enabled = like_enabled
        self._hover = -1
        self._pressed = -1
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        ART.loaded.connect(self._art_loaded)

    @property
    def compact(self) -> bool:
        return STATE["density"] == "compact"

    @property
    def row_height(self) -> int:
        return 34 if self.compact else 44

    # data ---------------------------------------------------------------
    def set_tracks(self, tracks: Sequence[Track], current_id: Optional[int] = None,
                   show_stats: Optional[bool] = None) -> None:
        self.tracks = list(tracks)
        self.current_id = current_id
        if show_stats is not None:
            self.show_stats = show_stats
        self._hover = -1
        self._sync_height()
        self.update()

    def set_current(self, track_id: Optional[int]) -> None:
        if self.current_id != track_id:
            self.current_id = track_id
            self.update()

    def set_liked(self, track_id: int, liked: bool) -> None:
        from dataclasses import replace
        self.tracks = [replace(t, liked=liked) if t.id == track_id else t for t in self.tracks]
        self.update()

    def _sync_height(self) -> None:
        self.setFixedHeight(max(self.row_height, len(self.tracks) * self.row_height))

    def sizeHint(self) -> QSize:
        return QSize(720, max(self.row_height, len(self.tracks) * self.row_height))

    def minimumSizeHint(self) -> QSize:
        return QSize(320, max(self.row_height, len(self.tracks) * self.row_height))

    def refresh_theme(self) -> None:
        self._sync_height()
        self.update()

    def _art_loaded(self, track_id: int) -> None:
        for i, t in enumerate(self.tracks):
            if t.id == track_id:
                self.update(0, i * self.row_height, self.width(), self.row_height)
                break

    # geometry -----------------------------------------------------------
    def _metrics(self, index: int) -> dict[str, QRectF]:
        rh = self.row_height
        y = index * rh
        art = 26 if self.compact else 36
        x = 8.0 + 22 + 10
        art_rect = QRectF(x, y + (rh - art) / 2, art, art)
        x += art + 10
        right = self.width() - 8
        more = QRectF(right - 26, y + (rh - 26) / 2, 26, 26)
        like = QRectF(right - 26 - 4 - 26, y + (rh - 26) / 2, 26, 26)
        right = like.left() - 6
        dur = QRectF(right - 40, y, 40, rh)
        right -= 46
        stats = None
        if self.show_stats:
            stats = QRectF(right - 50, y, 50, rh)
            right -= 56
        album = None
        if self.width() >= 780 and any(t.album for t in self.tracks[index:index + 1]):
            album_w = min(190.0, self.width() * 0.2)
            album = QRectF(right - album_w, y, album_w, rh)
            right -= album_w + 12
        title = QRectF(x, y + (rh - 32) / 2, max(40.0, right - x), 18)
        artist = QRectF(x, title.bottom() + 1, max(40.0, right - x), 15)
        return {
            "row": QRectF(0, y, self.width(), rh),
            "index": QRectF(8, y, 22, rh),
            "art": art_rect,
            "title": title,
            "artist": artist,
            "album": album,
            "stats": stats,
            "duration": dur,
            "like": like,
            "more": more,
        }

    # painting -----------------------------------------------------------
    def paintEvent(self, event) -> None:
        if not self.tracks:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rh = self.row_height
        top = max(0, event.rect().top() // rh)
        bottom = min(len(self.tracks), event.rect().bottom() // rh + 2)
        num_font = theme.mono(10, spacing=0.3)
        title_font = theme.ui(13, QFont.Weight.Medium)
        title_font_c = theme.ui(13, QFont.Weight.Medium)
        small_font = theme.mono(10, spacing=0.2)
        chip_font = theme.mono(8, QFont.Weight.DemiBold)

        for i in range(top, bottom):
            track = self.tracks[i]
            m = self._metrics(i)
            row = m["row"]
            current = track.id == self.current_id
            hovered = i == self._hover
            if hovered or current:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(C("accent", 46) if current else C("glass"))
                p.drawRoundedRect(row.adjusted(2, 1, 2, -1), 16, 16)
                if current:
                    p.setPen(QPen(C("accent", 110), 1))
                    p.drawRoundedRect(row.adjusted(2.5, 1.5, 2.5, -1.5), 16, 16)

            p.setFont(num_font)
            p.setPen(QPen(C("accent" if current else "dim2")))
            p.drawText(m["index"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       f"{i + 1:02d}")

            self._paint_cover(p, track, m["art"])

            p.setFont(title_font_c if current else title_font)
            p.setPen(QPen(C("accent" if current else "fg")))
            chip_w = 0
            if track.explicit:
                chip_w = 15
            title_width = m["title"].width() - (chip_w + 4 if chip_w else 0)
            p.drawText(m["title"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       _elide(title_font, track.title, title_width))
            if track.explicit:
                chip = QRectF(m["title"].x() + title_width + 4,
                              m["title"].center().y() - 7, 14, 14)
                p.setPen(QPen(C("dim2"), 1))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(chip, 2, 2)
                p.setFont(chip_font)
                p.setPen(QPen(C("dim")))
                p.drawText(chip, int(Qt.AlignmentFlag.AlignCenter), "E")

            p.setFont(small_font)
            p.setPen(QPen(C("dim")))
            p.drawText(m["artist"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                       _elide(small_font, track.artist, m["artist"].width()))

            if m["album"] is not None:
                p.setFont(small_font)
                p.setPen(QPen(C("dim2")))
                p.drawText(m["album"], int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                           _elide(small_font, track.album, m["album"].width()))
            if m["stats"] is not None:
                from .models import fmt_count
                p.setFont(small_font)
                p.setPen(QPen(C("dim2")))
                p.drawText(m["stats"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                           fmt_count(track.yt_likes))
            p.setFont(small_font)
            p.setPen(QPen(C("dim2")))
            p.drawText(m["duration"], int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       fmt_time(track.duration))

            if self.like_enabled:
                heart = m["like"]
                box = QRectF(0, 0, 15, 15)
                box.moveCenter(heart.center())
                color = C("accent" if track.liked else ("fg" if hovered else "dim"))
                draw_icon(p, "heart", box, color, fill=track.liked)
            more = m["more"]
            box = QRectF(0, 0, 15, 15)
            box.moveCenter(more.center())
            draw_icon(p, "more-vertical", box, C("fg" if hovered else "dim"))

    def _paint_cover(self, p: QPainter, track: Track, rect: QRectF) -> None:
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        p.save()
        p.setClipPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface2"))
        p.drawPath(path)
        pm = ART.request(track.id) if STATE["covers"] else None
        if pm is not None and not pm.isNull():
            scaled = pm.scaled(
                int(rect.width()), int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRectF((scaled.width() - rect.width()) / 2, (scaled.height() - rect.height()) / 2,
                         rect.width(), rect.height())
            p.drawPixmap(rect, scaled, src)
        else:
            box = QRectF(0, 0, rect.width() * 0.5, rect.height() * 0.5)
            box.moveCenter(rect.center())
            p.setOpacity(0.45)
            draw_icon(p, "disc-3", box, C("dim2"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(C("line"), 1))
        p.drawPath(path)

    # interaction --------------------------------------------------------
    def _row_at(self, y: float) -> int:
        if not self.tracks:
            return -1
        index = int(y // self.row_height)
        return index if 0 <= index < len(self.tracks) else -1

    def mousePressEvent(self, event) -> None:
        pos = event.position()
        index = self._row_at(pos.y())
        self._pressed = -1
        if index < 0:
            return
        m = self._metrics(index)
        if event.button() == Qt.MouseButton.RightButton:
            self.more_requested.emit(self.tracks[index], index,
                                     self.mapToGlobal(pos.toPoint()))
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.like_enabled and m["like"].contains(pos):
            self.like_requested.emit(self.tracks[index])
            return
        if m["more"].contains(pos):
            self.more_requested.emit(self.tracks[index], index,
                                     self.mapToGlobal(pos.toPoint()))
            return
        self._pressed = index

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = self._row_at(event.position().y())
        if index >= 0 and index == self._pressed:
            m = self._metrics(index)
            pos = event.position()
            if not m["like"].contains(pos) and not m["more"].contains(pos):
                self.play_requested.emit(index)
        self._pressed = -1

    def mouseMoveEvent(self, event) -> None:
        index = self._row_at(event.position().y())
        if index != self._hover:
            self._hover = index
            self.update()

    def leaveEvent(self, event) -> None:
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self._hover >= 0:
            self.play_requested.emit(self._hover)
        super().keyPressEvent(event)


# ── tiles, grids, shelves ──────────────────────────────────────────────────


class Tile(QAbstractButton):
    play_clicked = Signal()

    BASE = 158

    def __init__(self, title: str, subtitle: str = "", cover_id: Optional[int] = None,
                 *, round_: bool = False, kind: str = "album", payload=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.cover_id = cover_id
        self.round_ = round_
        self.kind = kind
        self.payload = payload
        self._width = self.BASE
        self._hover = False
        ART.loaded.connect(self._art_loaded)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.set_width(self.BASE)

    def set_width(self, width: int) -> None:
        self._width = max(120, int(width))
        self.setFixedSize(self._width, self._width + 58)

    def _art_rect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._width)

    def _play_rect(self) -> QRectF:
        art = self._art_rect()
        return QRectF(art.right() - 44, art.bottom() - 44, 38, 38)

    def _art_loaded(self, track_id: int) -> None:
        if self.cover_id == track_id:
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Lists and tiles are unboxed; only the artwork carries the surface.
        art = self._art_rect()
        path = QPainterPath()
        if self.round_:
            path.addEllipse(art)
        else:
            path.addRoundedRect(art, 18, 18)
        p.save()
        p.setClipPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("surface2"))
        p.drawPath(path)
        pm = ART.request(self.cover_id) if STATE["covers"] else None
        if pm is not None and not pm.isNull():
            scaled = pm.scaled(
                int(art.width()), int(art.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            src = QRectF((scaled.width() - art.width()) / 2, (scaled.height() - art.height()) / 2,
                         art.width(), art.height())
            p.drawPixmap(art, scaled, src)
        else:
            icon = "users" if self.round_ else "disc-3"
            box = QRectF(0, 0, art.width() * 0.36, art.height() * 0.36)
            box.moveCenter(art.center())
            p.setOpacity(0.45)
            draw_icon(p, icon, box, C("dim2"))
        p.restore()
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(C("line"), 1))
        p.drawPath(path)

        if self._hover:
            play = self._play_rect()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(C("accent", 64))
            p.drawEllipse(play.translated(0, 2))
            p.setBrush(C("accent"))
            p.drawEllipse(play)
            box = QRectF(0, 0, 15, 15)
            box.moveCenter(play.center())
            draw_icon(p, "play", box, C("accent_fg"))

        font_title = theme.ui(13, QFont.Weight.Medium)
        font_sub = theme.mono(10, spacing=0.2)
        text_align = (Qt.AlignmentFlag.AlignHCenter if self.round_
                      else Qt.AlignmentFlag.AlignLeft)
        title_rect = QRectF(10, art.bottom() + 8, self._width - 20, 18)
        sub_rect = QRectF(10, title_rect.bottom() + 1, self._width - 20, 14)
        p.setFont(font_title)
        p.setPen(QPen(C("fg")))
        p.drawText(title_rect, int(text_align | Qt.AlignmentFlag.AlignVCenter),
                   _elide(font_title, self.title, title_rect.width()))
        p.setFont(font_sub)
        p.setPen(QPen(C("dim")))
        p.drawText(sub_rect, int(text_align | Qt.AlignmentFlag.AlignVCenter),
                   _elide(font_sub, self.subtitle, sub_rect.width()))

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._play_rect().contains(event.position()):
            self.play_clicked.emit()
            return
        super().mouseReleaseEvent(event)


class TileGrid(QWidget):
    opened = Signal(object)
    played = Signal(object)

    def __init__(self, *, gap: int = 14, tile_width: int = 158, parent=None):
        super().__init__(parent)
        self._gap = gap
        self._base = tile_width
        self._tiles: list[Tile] = []
        self._last_width = -1
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(gap)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    @property
    def tiles(self) -> list[Tile]:
        return self._tiles

    def set_items(self, items: Sequence[dict]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._tiles = []
        for item in items:
            tile = Tile(
                item.get("title", ""), item.get("subtitle", ""), item.get("cover_id"),
                round_=bool(item.get("round")), kind=item.get("kind", "album"),
                payload=item.get("payload"),
            )
            tile.clicked.connect(lambda _=False, t=tile: self.opened.emit(t.payload))
            tile.play_clicked.connect(lambda t=tile: self.played.emit(t.payload))
            self._tiles.append(tile)
        self._last_width = -1
        self._relayout(force=True)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._relayout()

    def _relayout(self, force: bool = False) -> None:
        if not self._tiles:
            return
        width = self.width()
        if width <= 1:
            return
        cols = max(1, int((width + self._gap) // (self._base + self._gap)))
        tile_w = int((width - self._gap * (cols - 1)) / cols)
        if not force and width == self._last_width:
            return
        self._last_width = width
        while self._grid.count():
            self._grid.takeAt(0)
        for i, tile in enumerate(self._tiles):
            tile.set_width(tile_w)
            self._grid.addWidget(tile, i // cols, i % cols)
        for col in range(cols):
            self._grid.setColumnStretch(col, 0)
        self.updateGeometry()


class HScroll(QScrollArea):
    """Horizontal shelf with a thin scrollbar and wheel-to-scroll."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("background: transparent; border: none;")

    def wheelEvent(self, event) -> None:
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - event.angleDelta().y())
        event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        inner = self.widget()
        if inner is not None:
            inner.setMinimumHeight(self.viewport().height())

    def refresh_theme(self) -> None:
        self.viewport().update()


class Shelf(QWidget):
    opened = Signal(object)
    played = Signal(object)

    def __init__(self, title: str, meta: str = "", *, tile_width: int = 158, parent=None):
        super().__init__(parent)
        self._tile_w = tile_width
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(10)
        self.title_label = Txt(title, size=18, family="display", token="fg")
        head.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignBottom)
        self.meta_label = Txt(meta.upper(), size=9, family="mono", token="dim2", spacing=1.1)
        head.addWidget(self.meta_label, 0, Qt.AlignmentFlag.AlignBottom)
        head.addStretch(1)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(6)
        head.addLayout(self._actions)
        layout.addLayout(head)

        self.scroll = HScroll()
        self.inner = QWidget()
        self.inner.setStyleSheet("background: transparent;")
        self.row = QHBoxLayout(self.inner)
        self.row.setContentsMargins(0, 0, 0, 4)
        self.row.setSpacing(12)
        self.scroll.setWidget(self.inner)
        self.scroll.setFixedHeight(tile_width + 58 + 16)
        layout.addWidget(self.scroll)

    def add_action(self, widget: QWidget) -> None:
        self._actions.addWidget(widget)

    def set_items(self, items: Sequence[dict]) -> None:
        while self.row.count():
            item = self.row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for data in items:
            tile = Tile(
                data.get("title", ""), data.get("subtitle", ""), data.get("cover_id"),
                round_=bool(data.get("round")), kind=data.get("kind", "album"),
                payload=data.get("payload"),
            )
            tile.set_width(self._tile_w)
            tile.clicked.connect(lambda _=False, t=tile: self.opened.emit(t.payload))
            tile.play_clicked.connect(lambda t=tile: self.played.emit(t.payload))
            self.row.addWidget(tile)
        self.row.addStretch(1)

    def set_meta(self, meta: str) -> None:
        self.meta_label.setText(meta.upper())


# ── page furniture ─────────────────────────────────────────────────────────


class PageHead(QWidget):
    def __init__(self, title: str, kicker: str = "", meta: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        if kicker:
            self.kicker = Txt(kicker.upper(), size=10, family="mono", token="accent", spacing=1.8)
            layout.addWidget(self.kicker)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self.title_label = Txt(title, size=30, family="display", token="fg")
        row.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignBottom)
        if meta:
            self.meta_label = Txt(meta.upper(), size=9, family="mono", token="dim2", spacing=1.2)
            row.addWidget(self.meta_label, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        row.addLayout(self.actions)
        layout.addLayout(row)
        layout.addSpacing(10)
        layout.addWidget(Rule())

    def add_action(self, widget: QWidget) -> None:
        self.actions.addWidget(widget)


class Hero(QWidget):
    def __init__(self, kicker: str, title: str, subs: Sequence[str] = (),
                 cover_id: Optional[int] = None, *, round_: bool = False, parent=None):
        super().__init__(parent)
        self._round = round_
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.setMaximumHeight(300)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 20)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(26)
        row.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.art = Artwork(190, round_, "artist" if round_ else "album", shadow=True)
        self.art.set_cover(cover_id)
        row.addWidget(self.art, 0, Qt.AlignmentFlag.AlignBottom)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 2)
        info.setSpacing(7)
        info.addStretch(1)
        self.kicker = Txt(kicker.upper(), size=10, family="mono", token="accent", spacing=1.8)
        info.addWidget(self.kicker)
        self.title_label = Txt(title, size=34, family="display", token="fg", wrap=True)
        info.addWidget(self.title_label)
        self.sub_label = Txt("  ·  ".join([s for s in subs if s]), size=11, family="mono",
                             token="dim", spacing=0.4, wrap=True)
        info.addWidget(self.sub_label)
        self.actions = QHBoxLayout()
        self.actions.setContentsMargins(0, 6, 0, 0)
        self.actions.setSpacing(8)
        info.addLayout(self.actions)
        row.addLayout(info, 1)
        outer.addLayout(row)
        outer.addSpacing(16)
        outer.addWidget(Rule())

    def add_action(self, widget: QWidget) -> None:
        self.actions.addWidget(widget)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        gradient = QLinearGradient(0, 0, 0, min(self.height(), 210))
        soft = C("accent")
        soft.setAlpha(28)
        gradient.setColorAt(0.0, soft)
        transparent = QColor(soft)
        transparent.setAlpha(0)
        gradient.setColorAt(1.0, transparent)
        p.fillRect(QRectF(0, 0, self.width(), min(self.height(), 210)), gradient)


class EmptyState(QWidget):
    def __init__(self, title: str, hint: str = "", *, icon: str = "music",
                 action: Optional[tuple[str, Callable[[], None]]] = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 48, 20, 48)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        glyph = Glyph(icon, 26, "dim2")
        layout.addWidget(glyph, 0, Qt.AlignmentFlag.AlignHCenter)
        title_label = Txt(title, size=18, family="display", token="fg", align=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignHCenter)
        if hint:
            hint_label = Txt(hint, size=13, token="dim2", wrap=True,
                             align=Qt.AlignmentFlag.AlignHCenter)
            hint_label.setMaximumWidth(420)
            layout.addWidget(hint_label, 0, Qt.AlignmentFlag.AlignHCenter)
        if action:
            label, callback = action
            button = McButton(label, small=True)
            button.clicked.connect(callback)
            layout.addSpacing(4)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.setMinimumHeight(200)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(C("line2"), 1, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 7, 7)


class Panel(QWidget):
    def __init__(self, title: Optional[str] = None, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        if title:
            head = Txt(title.upper(), size=10, family="mono", token="dim2", spacing=1.5)
            head.setContentsMargins(16, 12, 16, 11)
            outer.addWidget(head)
            outer.addWidget(Rule())
        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.rows = QVBoxLayout(self.body)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(0)
        outer.addWidget(self.body)

    def add_row(self, title: str, subtitle: str = "", trailing: Optional[QWidget] = None,
                last: bool = False) -> "SettingRow":
        row = SettingRow(title, subtitle, trailing, last)
        self.rows.addWidget(row)
        return row

    def add_widget(self, widget: QWidget) -> None:
        self.rows.addWidget(widget)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("glass_border"), 1))
        p.setBrush(C("glass"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 22, 22)


class SettingRow(QWidget):
    def __init__(self, title: str, subtitle: str = "", trailing: Optional[QWidget] = None,
                 last: bool = False, parent=None):
        super().__init__(parent)
        self._last = last
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)
        self.title_label = Txt(title, size=13, token="fg", weight=QFont.Weight.Medium)
        text.addWidget(self.title_label)
        self.subtitle_label = None
        if subtitle:
            self.subtitle_label = Txt(subtitle, size=11, token="dim2", wrap=True)
            text.addWidget(self.subtitle_label)
        layout.addLayout(text, 1)
        if trailing is not None:
            layout.addWidget(trailing, 0, Qt.AlignmentFlag.AlignVCenter)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        if not self._last:
            p.fillRect(QRect(16, self.height() - 1, self.width() - 16, 1), C("line"))


class StatCard(QWidget):
    """A soft elevated tile for admin counters."""

    def __init__(self, value: str, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.value = Txt(value, size=18, family="mono", token="fg", weight=QFont.Weight.DemiBold)
        layout.addWidget(self.value)
        layout.addWidget(Txt(label.upper(), size=9, family="mono", token="dim2", spacing=1.1))
        self.setMinimumWidth(112)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("accent", 30))
        p.drawRoundedRect(rect.translated(0, 2), 18, 18)
        p.setPen(QPen(C("line"), 1))
        p.setBrush(C("bg2"))
        p.drawRoundedRect(rect, 18, 18)


# ── controls ───────────────────────────────────────────────────────────────


class SeekBar(QWidget):
    seeked = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._position = 0.0
        self._duration = 0.0
        self._drag: Optional[float] = None
        self._hover = False
        self.setFixedHeight(20)
        self.setMinimumWidth(90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_values(self, position: float, duration: float) -> None:
        self._position = max(0.0, position or 0)
        self._duration = max(0.0, duration or 0)
        self.update()

    def fraction(self) -> float:
        if self._drag is not None:
            return self._drag
        if self._duration <= 0:
            return 0.0
        return min(1.0, max(0.0, self._position / self._duration))

    def _apply(self, event) -> None:
        width = max(1, self.width() - 8)
        frac = (event.position().x() - 4) / width
        self._drag = min(1.0, max(0.0, frac))
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = 0.0
            self._apply(event)

    def mouseMoveEvent(self, event) -> None:
        self._hover = True
        if self._drag is not None:
            self._apply(event)
        else:
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag is not None:
            frac = self._drag
            self._drag = None
            self.seeked.emit(frac)
            self.update()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        left = 4.0
        width = self.width() - 8.0
        cy = self.height() / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("line"))
        p.drawRoundedRect(QRectF(left, cy - 2, width, 4), 1, 1)
        frac = self.fraction()
        if frac > 0:
            p.setBrush(C("accent"))
            p.drawRoundedRect(QRectF(left, cy - 2, width * frac, 4), 1, 1)
        if self._hover or self._drag is not None:
            p.setBrush(C("fg"))
            p.setPen(QPen(C("bg2"), 2))
            p.drawEllipse(QPointF(left + width * frac, cy), 5, 5)


class VolumeControl(QWidget):
    changed = Signal(float)
    mute_clicked = Signal()

    def __init__(self, level: float = 0.8, parent=None):
        super().__init__(parent)
        self._level = level
        self._muted = False
        self._hover = False
        self._drag = False
        self.setFixedSize(132, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_level(self, value: float, muted: bool = False) -> None:
        self._level = min(1.0, max(0.0, float(value)))
        self._muted = muted
        self.update()

    def _groove(self) -> QRectF:
        return QRectF(28, self.height() / 2 - 2, self.width() - 32, 4)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if event.position().x() < 24:
            self.mute_clicked.emit()
            return
        self._drag = True
        self._set_from(event.position().x())

    def mouseMoveEvent(self, event) -> None:
        self._hover = True
        if self._drag:
            self._set_from(event.position().x())
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        self._drag = False
        self.update()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def _set_from(self, x: float) -> None:
        groove = self._groove()
        value = (x - groove.x()) / max(1.0, groove.width())
        value = min(1.0, max(0.0, value))
        self._level = value
        self._muted = value <= 0.001
        self.changed.emit(value)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        icon = "volume-x"
        if not self._muted and self._level > 0.01:
            icon = "volume-1" if self._level < 0.5 else "volume-2"
        draw_icon(p, icon, QRectF(1, (self.height() - 17) / 2, 17, 17),
                  C("dim" if not self._hover else "fg"))
        groove = self._groove()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("line"))
        p.drawRoundedRect(groove, 1, 1)
        frac = 0.0 if self._muted else self._level
        if frac > 0:
            p.setBrush(C("accent"))
            p.drawRoundedRect(QRectF(groove.x(), groove.y(), groove.width() * frac, groove.height()), 1, 1)
        if self._hover or self._drag:
            p.setBrush(C("fg"))
            p.setPen(QPen(C("bg2"), 2))
            p.drawEllipse(QPointF(groove.x() + groove.width() * frac, groove.center().y()), 4.5, 4.5)


class Switch(QAbstractButton):
    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(38, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(lambda _=False: self.update())

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(C("accent" if self.isChecked() else "line2"))
        p.drawRoundedRect(QRectF(0, 0, 38, 20), 10, 10)
        p.setBrush(C("accent_fg" if self.isChecked() else "fg"))
        x = 20 if self.isChecked() else 2
        p.drawEllipse(QRectF(x, 2, 16, 16))


class Segmented(QWidget):
    changed = Signal(str)

    def __init__(self, options: Sequence[tuple[str, str]], selected: str = "", parent=None):
        super().__init__(parent)
        self._options = list(options)
        self._selected = selected or (self._options[0][0] if self._options else "")
        self._font = theme.mono(9, QFont.Weight.DemiBold, 0.9)
        self.setFixedHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(self.sizeHint().width())

    @property
    def selected(self) -> str:
        return self._selected

    def set_selected(self, key: str) -> None:
        if key != self._selected:
            self._selected = key
            self.update()

    def _segment_rects(self) -> list[tuple[str, str, QRectF]]:
        out = []
        x = 2.0
        for key, label in self._options:
            w = _fm(self._font, label.upper()) + 24
            out.append((key, label, QRectF(x, 2, w, self.height() - 4)))
            x += w + 2
        return out

    def sizeHint(self) -> QSize:
        return QSize(int(sum(r.width() for _, _, r in self._segment_rects()) + 6), 28)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("line"), 1))
        p.setBrush(C("bg2"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)
        p.setFont(self._font)
        for key, label, rect in self._segment_rects():
            on = key == self._selected
            if on:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(C("accent"))
                p.drawRoundedRect(rect, 10, 10)
            p.setPen(QPen(C("accent_fg" if on else "dim")))
            p.drawText(rect, int(Qt.AlignmentFlag.AlignCenter), label.upper())

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        for key, _label, rect in self._segment_rects():
            if rect.contains(event.position()):
                if key != self._selected:
                    self._selected = key
                    self.update()
                    self.changed.emit(key)
                return


class StatusChip(QWidget):
    def __init__(self, text: str, token: str = "dim", parent=None):
        super().__init__(parent)
        self._text = text.upper()
        self._token = token
        self._font = theme.mono(9, spacing=0.5)
        self.setFixedHeight(18)
        self.setMinimumWidth(self.sizeHint().width())

    def sizeHint(self) -> QSize:
        return QSize(_fm(self._font, self._text) + 16, 18)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = C(self._token)
        border = QColor(color)
        border.setAlpha(120)
        p.setPen(QPen(border, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 2, 2)
        p.setFont(self._font)
        p.setPen(QPen(color))
        p.drawText(QRectF(self.rect()), int(Qt.AlignmentFlag.AlignCenter), self._text)


class Spinner(QWidget):
    def __init__(self, size: int = 18, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    def _step(self) -> None:
        self._angle = (self._angle + 9) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setPen(QPen(C("line2"), 2))
        p.drawArc(rect, 0, 5760)
        p.setPen(QPen(C("accent"), 2))
        p.drawArc(rect, -self._angle * 16, 120 * 16)


# ── fields ─────────────────────────────────────────────────────────────────


class SearchField(QWidget):
    text_changed = Signal(str)
    submitted = Signal(str)

    def __init__(self, placeholder: str = "Search songs, albums, artists", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(7)
        self.icon = Glyph("search", 15, "dim2")
        layout.addWidget(self.icon)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFrame(False)
        self.edit.setStyleSheet(
            "QLineEdit{background:transparent;border:none;padding:0;color:inherit;}"
            "QLineEdit:focus{border:none;}"
        )
        self.edit.setClearButtonEnabled(False)
        self.edit.textChanged.connect(self._changed)
        self.edit.returnPressed.connect(lambda: self.submitted.emit(self.edit.text()))
        self.edit.installEventFilter(self)
        layout.addWidget(self.edit, 1)
        self.clear = IconButton("x", size=26, icon_size=14, tooltip="Clear search")
        self.clear.clicked.connect(self._clear)
        self.clear.setVisible(False)
        layout.addWidget(self.clear)
        self._focused = False

    def text(self) -> str:
        return self.edit.text()

    def set_text(self, text: str) -> None:
        if self.edit.text() != text:
            self.edit.setText(text)

    def focus(self) -> None:
        self.edit.setFocus()
        self.edit.selectAll()

    def _clear(self) -> None:
        self.edit.clear()
        self.focus()

    def _changed(self, text: str) -> None:
        self.clear.setVisible(bool(text))
        self.text_changed.emit(text)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.edit:
            if event.type() == event.Type.FocusIn:
                self._focused = True
                self.update()
            elif event.type() == event.Type.FocusOut:
                self._focused = False
                self.update()
        return super().eventFilter(obj, event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("glass_highlight" if self._focused else "glass_border"), 1))
        p.setBrush(C("glass"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)
        p.end()
        super().paintEvent(_event)

    def refresh_theme(self) -> None:
        self.update()


class LabeledField(QWidget):
    def __init__(self, label: str, placeholder: str = "", *, password: bool = False,
                 leading: Optional[str] = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(Txt(label.upper(), size=9, family="mono", token="dim2", spacing=1.4))
        row = QWidget()
        row.setFixedHeight(38)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 0, 10, 0)
        row_layout.setSpacing(7)
        if leading:
            row_layout.addWidget(Glyph(leading, 15, "dim2"))
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFrame(False)
        self.edit.setStyleSheet("QLineEdit{background:transparent;border:none;padding:0;}")
        if password:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        row_layout.addWidget(self.edit, 1)
        layout.addWidget(row)

    def text(self) -> str:
        return self.edit.text()

    def set_text(self, text: str) -> None:
        self.edit.setText(text)


class FieldFrame(QWidget):
    """Rounded bg2 field frame; keyboard input is a transparent QLineEdit."""

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("line2"), 1))
        p.setBrush(C("bg2"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)


# ── dialogs and overlays ───────────────────────────────────────────────────


class Sheet(QDialog):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self._title = title

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        self.card = QWidget()
        self.card.setObjectName("sheetCard")
        self.card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        head = QWidget()
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(16, 14, 10, 10)
        head_layout.setSpacing(8)
        head_layout.addWidget(Txt(title, size=18, family="display", token="fg"), 1)
        close = IconButton("x", size=28, icon_size=15, tooltip="Close")
        close.clicked.connect(self.reject)
        head_layout.addWidget(close)
        card_layout.addWidget(head)
        card_layout.addWidget(Rule())
        body = QWidget()
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(16, 14, 16, 18)
        self.body.setSpacing(10)
        card_layout.addWidget(body)
        self.setFixedWidth(470)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        p = theme.pal()
        self.card.setStyleSheet(
            f"QWidget#sheetCard{{background:{p.bg2};border:1px solid {p.line2};"
            f"border-radius:12px;}}"
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.adjustSize()
        host = self.parentWidget()
        if host is not None:
            center = host.window().frameGeometry().center()
            self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)


def _dialog_buttons(layout: QVBoxLayout, sheet: Sheet, confirm: str, *, danger: bool,
                    on_confirm: Callable[[], None]) -> None:
    row = QHBoxLayout()
    row.setSpacing(8)
    row.addStretch(1)
    cancel = McButton("Cancel", ghost=True)
    cancel.clicked.connect(sheet.reject)
    row.addWidget(cancel)
    ok = McButton(confirm, solid=True, danger=danger)
    ok.clicked.connect(on_confirm)
    row.addWidget(ok)
    layout.addSpacing(4)
    layout.addLayout(row)


def prompt(parent, title: str, label: str, *, placeholder: str = "", initial: str = "",
           confirm: str = "Save") -> Optional[str]:
    sheet = Sheet(parent, title)
    field = LabeledField(label, placeholder)
    field.set_text(initial)
    sheet.body.addWidget(field)
    result: dict[str, Optional[str]] = {"value": None}

    def accept() -> None:
        result["value"] = field.text().strip()
        sheet.accept()

    _dialog_buttons(sheet.body, sheet, confirm, danger=False, on_confirm=accept)
    field.edit.returnPressed.connect(accept)
    field.edit.setFocus()
    sheet.exec()
    return result["value"] or None


def confirm(parent, title: str, message: str, *, confirm_label: str = "Delete",
            danger: bool = True) -> bool:
    sheet = Sheet(parent, title)
    sheet.body.addWidget(Txt(message, size=13, token="dim", wrap=True))
    answer = {"ok": False}

    def accept() -> None:
        answer["ok"] = True
        sheet.accept()

    _dialog_buttons(sheet.body, sheet, confirm_label, danger=danger, on_confirm=accept)
    sheet.exec()
    return answer["ok"]


def message(parent, title: str, text: str) -> None:
    sheet = Sheet(parent, title)
    sheet.body.addWidget(Txt(text, size=13, token="dim", wrap=True))
    row = QHBoxLayout()
    row.addStretch(1)
    ok = McButton("OK", solid=True)
    ok.clicked.connect(sheet.accept)
    row.addWidget(ok)
    sheet.body.addLayout(row)
    sheet.exec()


class Toast(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._message = ""
        self._font = theme.ui(13, QFont.Weight.Medium)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, msec: int = 2800) -> None:
        self._message = text
        self._timer.start(msec)
        fm = QFontMetrics(self._font)
        width = min(int(fm.horizontalAdvance(text)) + 28, max(200, self.parent().width() - 48))
        self.setFixedSize(width, 34)
        self._reposition()
        self.show()
        self.raise_()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        x = (parent.width() - self.width()) // 2
        y = parent.height() - 150
        self.move(max(12, x), max(12, y))

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(C("glass_border"), 1))
        p.setBrush(C("glass_strong"))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)
        p.setFont(self._font)
        p.setPen(QPen(C("fg")))
        p.drawText(QRectF(14, 0, self.width() - 28, self.height()),
                   int(Qt.AlignmentFlag.AlignCenter),
                   QFontMetrics(self._font).elidedText(
                       self._message, Qt.TextElideMode.ElideRight, self.width() - 28))
