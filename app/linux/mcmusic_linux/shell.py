"""The native window: rail, masthead, content stack, deck and overlays."""
from __future__ import annotations

import platform
import time
from dataclasses import replace
from typing import Any, Callable, Optional, Sequence

from shiboken6 import isValid
from PySide6.QtCore import (
    QPoint, QPointF, QRectF, QSize, Qt, QTimer, QUrl, QMimeData, Signal,
)
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QDrag,
    QFont,
    QGuiApplication,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPen,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import icons, theme, widgets
from .api import Api, ApiError, Async, Repo, SessionStore, device_name
from .art import ART
from .icons import draw_icon
from .lyric_visualizer import LyricVisualizer
from .login import LoginPage, SplashPage
from .models import (
    Me, PlaylistRef, Settings, Track, fmt_bytes, fmt_count, fmt_time,
)
from .player import PlayerEngine
from .screens import (
    AdminScreen,
    CollectionScreen,
    DevicesScreen,
    DownloadsScreen,
    HomeScreen,
    LibraryScreen,
    LikesScreen,
    ListeningScreen,
    PlaylistScreen,
    PlaylistsScreen,
    RequestsScreen,
    SearchScreen,
    SettingsScreen,
    Screen,
)
from .version import VERSION
from .widgets import (
    Artwork,
    Glyph,
    IconButton,
    McButton,
    PlaylistNavButton,
    NavButton,
    Rule,
    SearchField,
    SeekBar,
    Sheet,
    Spinner,
    Txt,
    VolumeControl,
    confirm,
    message,
    prompt,
)


def _elide(text: str, width: int, font: QFont) -> str:
    from PySide6.QtGui import QFontMetrics
    return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, max(10, width))


class Mark(QWidget):
    def __init__(self, size: int = 26, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        icons.draw_mark(p, QRectF(self.rect()), theme.pal().q("accent"))


class OnlineDot(QWidget):
    def __init__(self, size: int = 5, parent=None):
        super().__init__(parent)
        self._online = True
        self.setFixedSize(size, size)

    def set_online(self, online: bool) -> None:
        self._online = online
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.pal().q("ok" if self._online else "err"))
        p.drawEllipse(QRectF(self.rect()))


class UserButton(QAbstractButton):
    def __init__(self, username: str = "", parent=None):
        super().__init__(parent)
        self._name = username
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_user(self, username: str) -> None:
        self._name = username
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        font = theme.ui(11)
        width = 32 + (QFontMetricsWidth(font, self._name) + 10 if self._name else 0)
        return QSize(max(30, width), 30)

    def paintEvent(self, _event) -> None:
        from PySide6.QtGui import QFontMetrics
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(theme.pal().q("surface"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 4, 4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.pal().q("accent"))
        p.drawEllipse(QRectF(2, 4, 22, 22))
        p.setFont(theme.mono(9, QFont.Weight.Bold))
        p.setPen(QPen(theme.pal().q("accent_fg")))
        p.drawText(QRectF(2, 4, 22, 22), int(Qt.AlignmentFlag.AlignCenter),
                   (self._name[:1] or "?").upper())
        if self._name:
            p.setFont(theme.ui(11))
            p.setPen(QPen(theme.pal().q("dim")))
            text = QFontMetrics(theme.ui(11)).elidedText(
                self._name, Qt.TextElideMode.ElideRight, self.width() - 38
            )
            p.drawText(QRectF(32, 0, self.width() - 34, self.height()),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), text)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


def QFontMetricsWidth(font: QFont, text: str) -> int:
    from PySide6.QtGui import QFontMetrics
    return QFontMetrics(font).horizontalAdvance(text)


class PlayButton(QAbstractButton):
    def __init__(self, size: int = 38, parent=None):
        super().__init__(parent)
        self._size = size
        self._playing = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_playing(self, playing: bool) -> None:
        if self._playing != playing:
            self._playing = playing
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        color = theme.pal().q("fg")
        if self.underMouse():
            color = color.lighter(110)
        p.setBrush(color)
        p.drawEllipse(QRectF(self.rect()))
        icon = "pause" if self._playing else "play"
        side = self._size * 0.42
        box = QRectF(0, 0, side, side)
        box.moveCenter(QRectF(self.rect()).center())
        if icon == "play":
            box.translate(1, 0)
        draw_icon(p, icon, box, theme.pal().bg)


class Rail(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.window = window
        self._nav: dict[str, NavButton] = {}
        self._pl_buttons: list[PlaylistNavButton] = []
        self._online = OnlineDot(5)
        self._net_label = Txt("ONLINE", size=8, family="mono", token="dim2", spacing=1.4)
        self.setFixedWidth(252)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 14)
        layout.setSpacing(0)

        brand = QWidget()
        brand_line = QHBoxLayout(brand)
        brand_line.setContentsMargins(10, 0, 10, 16)
        brand_line.setSpacing(9)
        brand_line.addWidget(Mark(26))
        brand_line.addWidget(Txt("mcmusic", size=20, family="display", token="fg"))
        brand_line.addStretch(1)
        brand_line.addWidget(Txt("LINUX", size=8, family="mono", token="dim2", spacing=1.6))
        layout.addWidget(brand)

        for key, label, icon in (
            ("home", "Home", "home"),
            ("search", "Search", "search"),
            ("library", "Library", "library"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        layout.addWidget(self._label("YOUR LISTS"))
        for key, label, icon in (
            ("likes", "Liked", "heart"),
            ("playlists", "Playlists", "list-music"),
            ("requests", "Requests", "download"),
            ("downloads", "Downloads", "cloud-download"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        layout.addWidget(self._label("SERVER"))
        for key, label, icon in (
            ("devices", "Devices", "smartphone"),
            ("listening", "Listening", "users"),
        ):
            layout.addWidget(self._nav_button(key, label, icon))

        layout.addWidget(self._rule(12, 10, 12, 10))
        pl_head = QWidget()
        pl_line = QHBoxLayout(pl_head)
        pl_line.setContentsMargins(10, 0, 6, 6)
        pl_line.setSpacing(4)
        pl_line.addWidget(Txt("PLAYLISTS", size=9, family="mono", token="dim2", spacing=1.6))
        pl_line.addStretch(1)
        new_pl = IconButton("plus", size=20, icon_size=12, tooltip="New playlist")
        new_pl.clicked.connect(window.create_playlist)
        pl_line.addWidget(new_pl)
        layout.addWidget(pl_head)

        self.pl_scroll = QScrollArea()
        self.pl_scroll.setWidgetResizable(True)
        self.pl_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pl_scroll.viewport().setAutoFillBackground(False)
        self.pl_scroll.setStyleSheet("background: transparent; border: none;")
        self.pl_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pl_inner = QWidget()
        self.pl_inner.setStyleSheet("background: transparent;")
        self.pl_layout = QVBoxLayout(self.pl_inner)
        self.pl_layout.setContentsMargins(0, 0, 0, 0)
        self.pl_layout.setSpacing(1)
        self.pl_layout.addStretch(1)
        self.pl_scroll.setWidget(self.pl_inner)
        layout.addWidget(self.pl_scroll, 1)

        self._settings_nav = self._nav_button("settings", "Settings", "settings")
        layout.addWidget(self._settings_nav)
        self._admin_nav = self._nav_button("admin", "Admin", "users")
        self._admin_nav.setVisible(False)
        layout.addWidget(self._admin_nav)

        layout.addWidget(self._rule(8, 10, 8, 10))
        foot = QWidget()
        foot_line = QVBoxLayout(foot)
        foot_line.setContentsMargins(6, 8, 6, 2)
        foot_line.setSpacing(6)
        self.user_button = UserButton()
        self.user_button.clicked.connect(lambda: window.navigate(("settings",)))
        foot_line.addWidget(self.user_button)
        net = QWidget()
        net_line = QHBoxLayout(net)
        net_line.setContentsMargins(4, 0, 0, 0)
        net_line.setSpacing(6)
        net_line.addWidget(self._online)
        net_line.addWidget(self._net_label)
        net_line.addStretch(1)
        foot_line.addWidget(net)
        layout.addWidget(foot)

    def _nav_button(self, key: str, label: str, icon: str) -> NavButton:
        button = NavButton(label, icon)
        button.clicked.connect(lambda _=False, k=key: self.window.navigate((k,)))
        self._nav[key] = button
        return button

    def _label(self, text: str) -> Txt:
        label = Txt(text, size=9, family="mono", token="dim2", spacing=1.6)
        label.setContentsMargins(10, 0, 10, 6)
        return label

    def _rule(self, top: int, left: int, bottom: int, right: int) -> QWidget:
        wrap = QWidget()
        line = QVBoxLayout(wrap)
        line.setContentsMargins(left, top, right, bottom)
        line.addWidget(Rule())
        return wrap

    def set_active(self, route: tuple) -> None:
        kind = route[0] if route else "home"
        active_key = {
            "album": "library", "artist": "library", "playlist": "playlists",
            "home": "home", "search": "search", "library": "library", "likes": "likes",
            "playlists": "playlists", "requests": "requests", "downloads": "downloads",
            "devices": "devices", "listening": "listening", "settings": "settings",
            "admin": "admin",
        }.get(kind, "")
        for key, button in self._nav.items():
            button.set_active(key == active_key)
        playlist_id = route[1] if kind == "playlist" and len(route) > 1 else None
        for button, pid in self._pl_buttons:
            button.set_active(pid == playlist_id)

    def set_user(self, me: Optional[Me]) -> None:
        self.user_button.set_user(me.username if me else "")
        self._admin_nav.setVisible(bool(me and me.is_admin))

    def set_online(self, online: bool) -> None:
        self._online.set_online(online)
        self._net_label.setText("ONLINE" if online else "OFFLINE")

    def set_playlists(self, playlists: Sequence[PlaylistRef], active_id: Optional[int]) -> None:
        while self.pl_layout.count():
            item = self.pl_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self._pl_buttons = []
        for playlist in playlists[:200]:
            button = PlaylistNavButton(playlist.name)
            button.set_active(playlist.id == active_id)
            button.clicked.connect(
                lambda _=False, pid=playlist.id: self.window.navigate(("playlist", pid))
            )
            self.pl_layout.addWidget(button)
            self._pl_buttons.append((button, playlist.id))
        self.pl_layout.addStretch(1)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        card = QRectF(self.rect()).adjusted(8, 12, -8, -12)
        p.setPen(QPen(palette.glass_border, 1))
        p.setBrush(palette.glass)
        p.drawRoundedRect(card, 28, 28)
        p.setPen(QPen(palette.glass_highlight, 1))
        p.drawLine(card.topLeft() + QPointF(20, 1), card.topRight() + QPointF(-20, 1))


class TopBar(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.setFixedHeight(58)
        line = QHBoxLayout(self)
        line.setContentsMargins(26, 0, 26, 0)
        line.setSpacing(10)
        self.back = IconButton("chevron-left", size=28, tooltip="Back")
        self.back.clicked.connect(window.back)
        self.back.setVisible(False)
        line.addWidget(self.back)
        self.search = SearchField()
        self.search.setMaximumWidth(460)
        self.search.text_changed.connect(window.on_search_text)
        self.search.submitted.connect(window.on_search_submit)
        line.addWidget(self.search, 2)
        line.addStretch(1)
        queue = IconButton("list-music", size=32, tooltip="Queue")
        queue.clicked.connect(window.toggle_queue)
        line.addWidget(queue)
        self.user = UserButton()
        self.user.clicked.connect(lambda: window.navigate(("settings",)))
        line.addWidget(self.user)

    def paintEvent(self, _event) -> None:
        # The shell gradient shows through; no attached masthead bar.
        pass


class Deck(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.setFixedHeight(76)
        grid = QGridLayout(self)
        grid.setContentsMargins(26, 6, 26, 10)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)

        left = QWidget()
        left_line = QHBoxLayout(left)
        left_line.setContentsMargins(0, 0, 0, 0)
        left_line.setSpacing(11)
        self.art = Artwork(46, kind="track")
        self.art.clicked.connect(window.show_now_playing)
        left_line.addWidget(self.art)
        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(1)
        self.title = Txt("Nothing playing right now", size=13, token="fg", weight=QFont.Weight.Medium)
        self.title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.artist = Txt("Pick a song from your library", size=10, family="mono",
                          token="dim", spacing=0.3)
        self.artist.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(self.title)
        meta.addWidget(self.artist)
        left_line.addLayout(meta, 1)
        self.like = IconButton("heart", size=30, tooltip="Like")
        self.like.clicked.connect(window.like_current)
        left_line.addWidget(self.like)
        grid.addWidget(left, 0, 0)

        center = QWidget()
        center_line = QVBoxLayout(center)
        center_line.setContentsMargins(0, 0, 0, 0)
        center_line.setSpacing(2)
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(2)
        controls.addStretch(1)
        self.shuffle = IconButton("shuffle", size=28, icon_size=15, tooltip="Shuffle")
        self.shuffle.clicked.connect(window.toggle_shuffle)
        controls.addWidget(self.shuffle)
        prev = IconButton("skip-back", size=28, icon_size=16, token="fg", tooltip="Previous")
        prev.clicked.connect(window.player.prev)
        controls.addWidget(prev)
        self.play = PlayButton(38)
        self.play.clicked.connect(window.player.toggle)
        controls.addWidget(self.play)
        nxt = IconButton("skip-forward", size=28, icon_size=16, token="fg", tooltip="Next")
        nxt.clicked.connect(window.player.next)
        controls.addWidget(nxt)
        self.repeat = IconButton("repeat", size=28, icon_size=15, tooltip="Repeat")
        self.repeat.clicked.connect(window.player.cycle_repeat)
        controls.addWidget(self.repeat)
        controls.addStretch(1)
        center_line.addLayout(controls)

        progress = QHBoxLayout()
        progress.setContentsMargins(0, 0, 0, 0)
        progress.setSpacing(9)
        self.pos = Txt("0:00", size=10, family="mono", token="dim", spacing=0.3,
                       align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.pos.setFixedWidth(36)
        progress.addWidget(self.pos)
        self.seek = SeekBar()
        self.seek.seeked.connect(window.player.seek_fraction)
        progress.addWidget(self.seek, 1)
        self.dur = Txt("0:00", size=10, family="mono", token="dim", spacing=0.3)
        self.dur.setFixedWidth(36)
        progress.addWidget(self.dur)
        center_line.addLayout(progress)
        grid.addWidget(center, 0, 1)

        right = QWidget()
        right_line = QHBoxLayout(right)
        right_line.setContentsMargins(0, 0, 0, 0)
        right_line.setSpacing(4)
        right_line.addStretch(1)
        expand = IconButton("tv-2", size=30, tooltip="Now playing")
        expand.clicked.connect(window.show_now_playing)
        right_line.addWidget(expand)
        queue = IconButton("list-music", size=30, tooltip="Queue")
        queue.clicked.connect(window.toggle_queue)
        right_line.addWidget(queue)
        self.volume = VolumeControl()
        self.volume.changed.connect(window.set_volume)
        self.volume.mute_clicked.connect(window.player.toggle_mute)
        right_line.addWidget(self.volume)
        grid.addWidget(right, 0, 2)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        card = QRectF(self.rect()).adjusted(12, 2, -12, -8)
        p.setPen(QPen(palette.glass_border, 1))
        p.setBrush(palette.glass)
        p.drawRoundedRect(card, 20, 20)
        p.setPen(QPen(palette.glass_highlight, 1))
        p.drawLine(card.topLeft() + QPointF(18, 1), card.topRight() + QPointF(-18, 1))


QUEUE_MIME = "application/x-mcmusic-queue-index"


class QueueRow(QWidget):
    def __init__(self, window: "McWindow", track: Track, index: int,
                 *, current: bool = False, removable: bool = True,
                 reorder: bool = False, parent=None):
        super().__init__(parent)
        self.window = window
        self.track = track
        self.index = index
        self.current = current
        self._hover = False
        self._reorder = bool(reorder and not current)
        self._drag_start: Optional[QPoint] = None
        self._dragging = False
        self._drop_target = False
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._reorder:
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.setAcceptDrops(True)
            self.setToolTip("Drag to reorder, or use Up/Down when focused")
        line = QHBoxLayout(self)
        line.setContentsMargins(6, 5, 6, 5)
        line.setSpacing(10)
        art = Artwork(34, kind="track")
        art.set_cover(track.id)
        art.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        line.addWidget(art)
        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(1)
        title = Txt(track.title, size=13, token="accent" if current else "fg")
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(title)
        artist = Txt(track.artist, size=10, family="mono", token="dim", spacing=0.2)
        artist.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        meta.addWidget(artist)
        line.addLayout(meta, 1)
        if self._reorder:
            up = IconButton("chevron-up", size=26, icon_size=13, tooltip="Move up")
            up.setEnabled(index > window.player.index + 1)
            up.clicked.connect(lambda: self._shift(-1))
            line.addWidget(up)
            down = IconButton("chevron-down", size=26, icon_size=13, tooltip="Move down")
            down.setEnabled(index + 1 < len(window.player.queue))
            down.clicked.connect(lambda: self._shift(1))
            line.addWidget(down)
        if removable and not current:
            remove = IconButton("x", size=26, icon_size=13, tooltip="Remove from queue")
            remove.clicked.connect(lambda: window.player.remove_at(index))
            line.addWidget(remove)

    def _shift(self, delta: int) -> None:
        target = self.index + delta
        if self.window.player.move(self.index, target):
            self.window.drawer.focus_index(target)

    @staticmethod
    def _mime_index(event) -> Optional[int]:
        if event.mimeData().hasFormat(QUEUE_MIME):
            raw = bytes(event.mimeData().data(QUEUE_MIME)).decode("utf-8", "replace")
        elif event.mimeData().hasText():
            raw = event.mimeData().text()
        else:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def _can_drop(self, event) -> bool:
        source = self._mime_index(event)
        player = self.window.player
        return (source is not None and self._reorder
                and source > player.index and self.index > player.index
                and source != self.index)

    def mousePressEvent(self, event) -> None:
        if self._reorder and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (self._reorder and self._drag_start is not None
                and (event.position().toPoint() - self._drag_start).manhattanLength()
                >= QApplication.startDragDistance()):
            self._dragging = True
            mime = QMimeData()
            mime.setData(QUEUE_MIME, str(self.index).encode("ascii"))
            mime.setText(str(self.index))
            drag = QDrag(self)
            drag.setMimeData(mime)
            drag.setPixmap(self.grab())
            drag.setHotSpot(self._drag_start)
            drag.exec(Qt.DropAction.MoveAction)
            self._drag_start = None
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        dragged = self._dragging
        self._drag_start = None
        self._dragging = False
        if not dragged and event.button() == Qt.MouseButton.LeftButton:
            self.window.player.jump(self.index)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if not self._reorder:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key.Key_Up:
            self._shift(-1)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self._shift(1)
            event.accept()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.window.player.remove_at(self.index)
            event.accept()
        elif event.key() == Qt.Key.Key_Return:
            self.window.player.jump(self.index)
            event.accept()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if self._can_drop(event):
            self._drop_target = True
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if self._can_drop(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, _event) -> None:
        self._drop_target = False
        self.update()

    def dropEvent(self, event) -> None:
        source = self._mime_index(event)
        self._drop_target = False
        self.update()
        if source is None or not self._reorder:
            event.ignore()
            return
        target = self.index
        if self.window.player.move(source, target):
            self.window.drawer.focus_index(target)
            event.acceptProposedAction()
        else:
            event.ignore()

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:
        palette = theme.pal()
        if self._hover or self.hasFocus() or self._drop_target:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            if self._hover or self.hasFocus():
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(palette.q("surface"))
                p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 4, 4)
            if self._drop_target:
                p.setPen(QPen(palette.q("accent"), 2))
                p.drawLine(QPoint(2, 1), QPoint(self.width() - 2, 1))


class Scrim(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.window = window
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.hide()

    def paintEvent(self, _event) -> None:
        QPainter(self).fillRect(self.rect(), QColor(0, 0, 0, 135))

    def mouseReleaseEvent(self, event) -> None:
        self.window.close_overlays()
        super().mouseReleaseEvent(event)


class QueueDrawer(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.window = window
        self.setFixedWidth(390)
        self.hide()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        head = QWidget()
        head_line = QHBoxLayout(head)
        head_line.setContentsMargins(16, 16, 12, 12)
        head_line.addWidget(Txt("Queue", size=18, family="display", token="fg"))
        head_line.addStretch(1)
        close = IconButton("x", size=28, icon_size=15, tooltip="Close queue")
        close.clicked.connect(window.close_overlays)
        head_line.addWidget(close)
        outer.addWidget(head)
        outer.addWidget(Rule())
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll.viewport().setAutoFillBackground(False)
        self.inner = QWidget()
        self.inner.setStyleSheet("background: transparent;")
        self.body = QVBoxLayout(self.inner)
        self.body.setContentsMargins(12, 10, 12, 24)
        self.body.setSpacing(2)
        self._rows: dict[int, QueueRow] = {}
        self.scroll.setWidget(self.inner)
        outer.addWidget(self.scroll, 1)

    def focus_index(self, index: int) -> None:
        row = self._rows.get(index)
        if row is not None and isValid(row):
            row.setFocus(Qt.FocusReason.OtherFocusReason)

    def refresh(self) -> None:
        self._rows.clear()
        while self.body.count():
            item = self.body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        player = self.window.player
        current = player.current
        if current is None:
            self.body.addWidget(Txt("Queue is empty", size=13, token="dim"))
            self.body.addStretch(1)
            return
        label = Txt("NOW PLAYING", size=9, family="mono", token="dim2", spacing=1.6)
        label.setContentsMargins(6, 8, 6, 4)
        self.body.addWidget(label)
        current_row = QueueRow(self.window, current, player.index, current=True,
                               removable=False)
        self._rows[player.index] = current_row
        self.body.addWidget(current_row)
        upcoming = [(i, t) for i, t in enumerate(player.queue) if i > player.index]
        head = QWidget()
        head_line = QHBoxLayout(head)
        head_line.setContentsMargins(6, 16, 4, 6)
        head_line.addWidget(Txt(f"Next up ({len(upcoming)})", size=9, family="mono",
                                token="dim2", spacing=1.2))
        head_line.addStretch(1)
        if upcoming:
            clear = McButton("Clear next", small=True, ghost=True)
            clear.clicked.connect(player.clear_upcoming)
            head_line.addWidget(clear)
        self.body.addWidget(head)
        for index, track in upcoming[:80]:
            row = QueueRow(self.window, track, index, reorder=True)
            self._rows[index] = row
            self.body.addWidget(row)
        if not upcoming:
            self.body.addWidget(Txt("Nothing queued", size=11, token="dim2"))
        else:
            hint = Txt("Drag to reorder or focus a row and press Up/Down", size=10,
                       token="dim2")
            hint.setContentsMargins(6, 8, 6, 0)
            self.body.addWidget(hint)
        self.body.addStretch(1)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), theme.pal().q("bg2"))
        p.fillRect(0, 0, 1, self.height(), theme.pal().q("line2"))


class PickRow(QAbstractButton):
    def __init__(self, playlist: PlaylistRef, parent=None):
        super().__init__(parent)
        self.playlist = playlist
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(theme.pal().q("surface"))
            p.drawRoundedRect(QRectF(self.rect()).adjusted(0, 1, 0, -1), 4, 4)
        box = QRectF(4, (self.height() - 32) / 2, 32, 32)
        path = QRectF(box)
        pm = ART.request(self.playlist.cover_id)
        p.setPen(QPen(theme.pal().q("line"), 1))
        p.setBrush(theme.pal().q("surface2"))
        p.drawRoundedRect(path, 4, 4)
        if pm is not None and not pm.isNull():
            p.save()
            p.setClipRect(path)
            scaled = pm.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(box.toRect(), scaled)
            p.restore()
        else:
            draw_icon(p, "disc-3", box.adjusted(8, 8, -8, -8), theme.pal().dim2)
        p.setFont(theme.ui(13, QFont.Weight.Medium))
        p.setPen(QPen(theme.pal().q("fg")))
        p.drawText(QRectF(46, 4, self.width() - 56, 20),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   _elide(self.playlist.name, self.width() - 56, theme.ui(13)))
        p.setFont(theme.mono(10, spacing=0.2))
        p.setPen(QPen(theme.pal().q("dim2")))
        p.drawText(QRectF(46, 22, self.width() - 56, 16),
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   f"{self.playlist.n} tracks")


class NowPlayingOverlay(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__(window.shell)
        self.window = window
        self._up_next_key: tuple = ()
        self.hide()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.viewport().setAutoFillBackground(False)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        body = QVBoxLayout(inner)
        body.setContentsMargins(28, 16, 28, 28)
        body.setSpacing(0)

        header = QHBoxLayout()
        close = IconButton("chevron-down", size=32, tooltip="Close player")
        close.clicked.connect(window.close_overlays)
        header.addWidget(close)
        header.addStretch(1)
        header.addWidget(Txt("NOW PLAYING", size=10, family="mono", token="accent",
                             spacing=2.2))
        header.addStretch(1)
        self.more = IconButton("more-vertical", size=32, tooltip="Track options")
        self.more.clicked.connect(self._more)
        header.addWidget(self.more)
        body.addLayout(header)
        body.addSpacing(10)

        art_row = QHBoxLayout()
        art_row.addStretch(1)
        self.art = Artwork(300, kind="track", shadow=True)
        art_row.addWidget(self.art)
        art_row.addStretch(1)
        body.addLayout(art_row)
        body.addSpacing(20)

        self.title = Txt("Nothing playing right now", size=27, family="display", token="fg",
                         wrap=True, align=Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(self.title)
        body.addSpacing(4)
        self.artist = Txt("", size=11, family="mono", token="dim", spacing=0.6,
                          align=Qt.AlignmentFlag.AlignHCenter)
        body.addWidget(self.artist)
        body.addSpacing(18)

        seek_wrap = QWidget()
        seek_line = QHBoxLayout(seek_wrap)
        seek_line.setContentsMargins(0, 0, 0, 0)
        seek_line.setSpacing(9)
        self.pos = Txt("0:00", size=10, family="mono", token="dim", spacing=0.3)
        self.pos.setFixedWidth(38)
        seek_line.addWidget(self.pos)
        self.seek = SeekBar()
        self.seek.seeked.connect(window.player.seek_fraction)
        seek_line.addWidget(self.seek, 1)
        self.dur = Txt("0:00", size=10, family="mono", token="dim", spacing=0.3,
                       align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.dur.setFixedWidth(38)
        seek_line.addWidget(self.dur)
        wrap = QHBoxLayout()
        wrap.addStretch(1)
        seek_wrap.setMaximumWidth(560)
        wrap.addWidget(seek_wrap, 3)
        wrap.addStretch(1)
        body.addLayout(wrap)
        body.addSpacing(16)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self.shuffle = IconButton("shuffle", size=40, icon_size=18, tooltip="Shuffle")
        self.shuffle.clicked.connect(window.toggle_shuffle)
        controls.addWidget(self.shuffle)
        prev = IconButton("skip-back", size=44, icon_size=20, token="fg")
        prev.clicked.connect(window.player.prev)
        controls.addWidget(prev)
        self.play = PlayButton(58)
        self.play.clicked.connect(window.player.toggle)
        controls.addWidget(self.play)
        nxt = IconButton("skip-forward", size=44, icon_size=20, token="fg")
        nxt.clicked.connect(window.player.next)
        controls.addWidget(nxt)
        self.repeat = IconButton("repeat", size=40, icon_size=18, tooltip="Repeat")
        self.repeat.clicked.connect(window.player.cycle_repeat)
        controls.addWidget(self.repeat)
        controls.addStretch(1)
        body.addLayout(controls)
        body.addSpacing(10)

        secondary = QHBoxLayout()
        secondary.addStretch(1)
        self.like = IconButton("heart", size=40, tooltip="Like")
        self.like.clicked.connect(window.like_current)
        secondary.addWidget(self.like)
        lyrics = McButton("Lyrics", small=True, ghost=True, icon="text")
        lyrics.clicked.connect(window.show_lyrics)
        secondary.addWidget(lyrics)
        self.sleep_button = McButton("Sleep", small=True, ghost=True, icon="clock")
        self.sleep_button.clicked.connect(
            lambda _=False, b=self.sleep_button: window.show_sleep_menu(b)
        )
        secondary.addWidget(self.sleep_button)
        queue = McButton("Queue", small=True, ghost=True, icon="list-music")
        queue.clicked.connect(window.toggle_queue)
        secondary.addWidget(queue)
        add = IconButton("folder-plus", size=40, tooltip="Add to playlist")
        add.clicked.connect(lambda: window.add_current_to_playlist())
        secondary.addWidget(add)
        secondary.addStretch(1)
        body.addLayout(secondary)
        body.addSpacing(18)

        body.addWidget(Rule())
        body.addSpacing(14)
        self.up_next_label = Txt("UP NEXT", size=9, family="mono", token="dim2", spacing=1.6)
        body.addWidget(self.up_next_label)
        body.addSpacing(6)
        self.up_next = QVBoxLayout()
        self.up_next.setContentsMargins(0, 0, 0, 0)
        self.up_next.setSpacing(1)
        body.addLayout(self.up_next)
        body.addStretch(1)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _more(self) -> None:
        track = self.window.player.current
        if track is not None:
            self.window.open_track_menu(track, self.window.player.index,
                                        self.mapToGlobal(QPoint(self.width() - 44, 48)))

    def refresh(self) -> None:
        player = self.window.player
        track = player.current
        if track is None:
            self.title.setText("Nothing playing right now")
            self.artist.setText("Pick a song from your library")
            self.art.set_cover(None)
            self.more.setEnabled(False)
            self.like.setVisible(False)
        else:
            self.art.set_cover(track.id)
            self.title.setText(track.title)
            parts = [track.artist]
            if track.album:
                parts.append(track.album)
            self.artist.setText("  ·  ".join(p for p in parts if p))
            self.more.setEnabled(True)
            self.like.setVisible(True)
            self.like.set_active(track.liked)
            self.like.set_fill(track.liked)
        self.play.set_playing(player.playing)
        self.shuffle.set_active(player.shuffle)
        name = "repeat-1" if player.repeat == "one" else "repeat"
        self.repeat.set_icon(name)
        self.repeat.set_active(player.repeat != "off")
        self.pos.setText(fmt_time(player.position))
        self.dur.setText(fmt_time(player.duration))
        self.seek.set_values(player.position, player.duration)
        timer = self.window.store.sleep_timer
        try:
            left = max(0, int((float(timer.get("ends_at", 0)) - time.time()) / 60))
        except (TypeError, ValueError):
            left = 0
        self.sleep_button.set_text(f"Sleep {left}m" if left else "Sleep")

        key = tuple((i, t.id) for i, t in enumerate(player.queue) if i > player.index)[:8]
        if key != self._up_next_key:
            self._up_next_key = key
            while self.up_next.count():
                item = self.up_next.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
            upcoming = [(i, t) for i, t in enumerate(player.queue) if i > player.index][:8]
            for index, queued in upcoming:
                self.up_next.addWidget(QueueRow(self.window, queued, index))
            if not upcoming:
                self.up_next.addWidget(Txt("Nothing queued", size=11, token="dim2"))

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), theme.pal().q("bg"))
        grad = QLinearGradient(0, 0, 0, min(self.height(), 300))
        soft = theme.pal().q("accent")
        soft.setAlpha(18)
        clear = QColor(soft)
        clear.setAlpha(0)
        grad.setColorAt(0, soft)
        grad.setColorAt(1, clear)
        p.fillRect(0, 0, self.width(), min(self.height(), 300), grad)


class StatusStrip(QWidget):
    """A quiet, persistent line for offline/pending/update notices."""

    def __init__(self, window: "McWindow"):
        super().__init__()
        self.window = window
        self._online = True
        self._pending = 0
        self._notice = ""
        self.setFixedHeight(0)
        line = QHBoxLayout(self)
        line.setContentsMargins(30, 0, 26, 0)
        line.setSpacing(8)
        self.icon = Glyph("check", 13, "ok")
        line.addWidget(self.icon)
        self.label = Txt("", size=10, family="mono", token="dim", spacing=0.4)
        line.addWidget(self.label, 1)
        self.sync = McButton("Sync now", small=True, ghost=True, icon="refresh-cw")
        self.sync.clicked.connect(window.sync_outbox)
        self.sync.setVisible(False)
        line.addWidget(self.sync)
        self.update = McButton("Download", small=True, ghost=True, icon="download")
        self.update.clicked.connect(window.open_update)
        self.update.setVisible(False)
        line.addWidget(self.update)

    def set_state(self, *, online: bool, pending: int = 0, notice: str = "",
                  has_update: bool = False) -> None:
        self._online = online
        self._pending = max(0, int(pending or 0))
        self._notice = notice or ""
        if not online:
            text = "OFFLINE — using saved session"
            self.icon.set_icon("wifi-off")
        elif self._pending:
            text = f"{self._pending} pending change" + ("s" if self._pending != 1 else "") + " — will sync"
            self.icon.set_icon("refresh-cw")
        elif self._notice:
            text = self._notice
            self.icon.set_icon("arrow-up-right")
        else:
            text = ""
            self.icon.set_icon("check")
        self.label.setText(text)
        self.setVisible(bool(text))
        self.setFixedHeight(24 if text else 0)
        self.sync.setVisible(online and self._pending > 0)
        self.update.setVisible(online and has_update)

    def paintEvent(self, _event) -> None:
        if not self.height():
            return
        p = QPainter(self)
        p.fillRect(self.rect(), theme.pal().q("bg2"))
        p.fillRect(0, self.height() - 1, self.width(), 1, theme.pal().q("line"))


class ShellPage(QWidget):
    def __init__(self, window: "McWindow"):
        super().__init__()
        self.window = window

    def paintEvent(self, _event) -> None:
        QPainter(self).fillRect(self.rect(), theme.pal().q("bg"))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.window.position_overlays()


class McWindow(QMainWindow):
    def __init__(self, store: SessionStore, api: Api, repo: Repo, runner: Async,
                 player: PlayerEngine):
        super().__init__()
        self.store = store
        self.api = api
        self.repo = repo
        self.runner = runner
        self.player = player
        self.me: Optional[Me] = store.cached_me
        self.settings = Settings(theme=store.theme, accent=store.accent,
                                 volume=store.volume)
        self.route: tuple = ("home",)
        self.back_stack: list[tuple] = []
        self.current_screen: Optional[Screen] = None
        self.playlists: list[PlaylistRef] = []
        self._offline = False
        self._activity_sig = ""
        self._activity_at = 0.0
        self._last_remote_command = 0
        self._update_kind = ""
        self._update_url = ""
        self._notice = ""
        self._radio_busy = False

        self.setWindowTitle("mcmusic")
        self.resize(1280, 830)
        self.setMinimumSize(940, 620)

        self._search = ""
        self._device_timer = QTimer(self)
        self._device_timer.setInterval(30_000)
        self._device_timer.timeout.connect(self._heartbeat)
        self._publish_timer = QTimer(self)
        self._publish_timer.setInterval(10_000)
        self._publish_timer.timeout.connect(self._publish_playback)
        self._retry_timer = QTimer(self)
        self._retry_timer.setInterval(15_000)
        self._retry_timer.timeout.connect(self._retry_connection)
        self._remote_timer = QTimer(self)
        self._remote_timer.setInterval(3_000)
        self._remote_timer.timeout.connect(self._poll_remote)
        self._sleep_timer = QTimer(self)
        self._sleep_timer.setInterval(1_000)
        self._sleep_timer.timeout.connect(self._check_sleep_timer)

        self._build_pages()
        self._build_shortcuts()

        widgets.set_covers(self.settings.covers)
        widgets.set_density(self.settings.density)

        self.player.changed.connect(self._refresh_playback)
        self.player.tick.connect(self._refresh_progress)
        self.player.error.connect(self.toast)
        self.player.natural_end.connect(self._autoplay_radio)
        self.player.loading_changed.connect(lambda _busy: self._refresh_playback())
        self.player.changed.connect(self._update_window_title)
        self.player.changed.connect(self._publish_activity)

        self.apply_settings(self.settings, persist=False)
        try:
            QGuiApplication.styleHints().colorSchemeChanged.connect(
                self._system_appearance_changed
            )
        except (AttributeError, RuntimeError, TypeError):
            pass

        if self.me is not None and (self.api.cookies or self.api.token):
            self.stack.setCurrentWidget(self.splash)
            self.run(lambda: self.repo.me(force=True), self.after_login,
                     self._restore_failed)
        elif self.store.pending_token:
            # A mcmusic://oauth?token=… deep link arrived before any session.
            self.stack.setCurrentWidget(self.splash)
            self.run(self._restore_token_session, self.after_login,
                     self._token_restore_failed)
        else:
            self.show_login()

    def _restore_token_session(self) -> Me:
        token = self.store.pending_token
        me = self.repo.adopt_token(token)
        self.store.pending_token = ""
        self.store.reset_token = ""
        return me

    def _token_restore_failed(self, exc: Exception) -> None:
        offline = isinstance(exc, ApiError) and exc.offline
        if not offline:
            self.store.pending_token = ""
        self.show_login()
        if isValid(self) and hasattr(self, "login_page"):
            self.login_page._show_error(
                "Saved sign-in will be retried when the server is reachable"
                if offline else (str(exc) or "That sign-in link could not be used")
            )

    # ── construction ────────────────────────────────────────────────────
    def paintEvent(self, _event) -> None:
        """The window itself is the artwork-derived tint behind glass panes."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        p.fillRect(self.rect(), palette.q("bg"))
        grad = QLinearGradient(0, 0, 0, self.height())
        tint = palette.q("accent")
        tint.setAlpha(46)
        grad.setColorAt(0, tint)
        grad.setColorAt(0.55, palette.q("bg"))
        grad.setColorAt(1, palette.q("bg"))
        p.fillRect(self.rect(), grad)

    def _build_pages(self) -> None:
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.splash = SplashPage()
        self.stack.addWidget(self.splash)

        self.shell = ShellPage(self)
        root = QHBoxLayout(self.shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.rail = Rail(self)
        root.addWidget(self.rail)

        main = QWidget()
        main.setStyleSheet("background: transparent;")
        main_line = QVBoxLayout(main)
        main_line.setContentsMargins(0, 0, 0, 0)
        main_line.setSpacing(0)
        self.topbar = TopBar(self)
        main_line.addWidget(self.topbar)
        self.status_strip = StatusStrip(self)
        main_line.addWidget(self.status_strip)
        self.content_host = QWidget()
        self.content_host.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        main_line.addWidget(self.content_host, 1)
        self.deck = Deck(self)
        main_line.addWidget(self.deck)
        root.addWidget(main, 1)
        self.stack.addWidget(self.shell)

        self.scrim = Scrim(self)

        self.drawer = QueueDrawer(self)
        self.overlay = NowPlayingOverlay(self)

        self.toast_widget = widgets.Toast(self)

    def _text_focused(self) -> bool:
        focused = QApplication.focusWidget()
        return isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit))

    def _build_shortcuts(self) -> None:
        # Keep the old direct keys alongside the Ctrl bindings. Every shortcut
        # that could collide with typing is guarded so fields stay editable.
        shortcuts = [
            ("Ctrl+F", lambda: self.topbar.search.focus(), False),
            ("Ctrl+Space", self.player.toggle, True),
            ("Ctrl+Left", self.player.prev, True),
            ("Ctrl+Right", self.player.next, True),
            ("Ctrl+M", self.player.toggle_mute, True),
            ("Ctrl+Up", lambda: self.set_volume(self.player.volume + 0.05), True),
            ("Ctrl+Down", lambda: self.set_volume(self.player.volume - 0.05), True),
            ("Alt+Left", self.back, False),
            ("Escape", self.close_overlays, False),
            ("Space", self.player.toggle, True),
            ("Shift+Left", self.player.prev, True),
            ("Shift+Right", self.player.next, True),
            ("Up", lambda: self.set_volume(self.player.volume + 0.05), True),
            ("Down", lambda: self.set_volume(self.player.volume - 0.05), True),
            ("/", lambda: self.topbar.search.focus(), True),
            ("m", self.player.toggle_mute, True),
            ("l", self.like_current, True),
            ("q", self.toggle_queue, True),
            (QKeySequence(Qt.Key.Key_MediaPlay), self.player.toggle, True),
            (QKeySequence(Qt.Key.Key_MediaPause), self.player.pause, True),
            (QKeySequence(Qt.Key.Key_MediaNext), self.player.next, True),
            (QKeySequence(Qt.Key.Key_MediaPrevious), self.player.prev, True),
        ]
        self._shortcuts = []
        for keys, callback, guard in shortcuts:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.activated.connect(
                (lambda cb=callback, guarded=guard: self._run_shortcut(cb, guarded))
            )
            self._shortcuts.append(shortcut)

    def _run_shortcut(self, callback: Callable[[], None], guarded: bool) -> None:
        if guarded and self._text_focused():
            return
        callback()

    # ── session ─────────────────────────────────────────────────────────
    def show_login(self) -> None:
        self._device_timer.stop()
        self._publish_timer.stop()
        self._retry_timer.stop()
        self._remote_timer.stop()
        self._sleep_timer.stop()
        self._set_online(False, pending=self.api.pending_writes())
        if hasattr(self, "login_page") and self.login_page is not None:
            self.stack.removeWidget(self.login_page)
            self.login_page.deleteLater()
        self.login_page = LoginPage(self)
        self.login_page.succeeded.connect(self.after_login)
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)
        self.login_page.username.edit.setFocus()

    def after_login(self, me: Me) -> None:
        self.me = me
        self.store.cached_me = me
        self._offline = False
        self.rail.set_user(me)
        self.topbar.user.set_user(me.username)
        self.stack.setCurrentWidget(self.shell)
        self.back_stack = []
        self._set_online(True, pending=self.api.pending_writes())
        self._load_settings()
        self.refresh_playlists()
        self.navigate(("home",), push=False)
        self._restore_queue()
        self._device_timer.start()
        self._publish_timer.start()
        self._retry_timer.stop()
        self._remote_timer.start()
        self._sleep_timer.start()
        self.sync_outbox(quiet=True)
        self._verify_pending_token()
        self._check_updates()
        self.position_overlays()
        self.player.changed.emit()

    def _restore_failed(self, exc: Exception) -> None:
        if not isValid(self):
            return
        if isinstance(exc, ApiError) and exc.status == 401:
            self.toast("Session expired — please sign in again")
            self.sign_out()
            return
        if self.me is None:
            self.show_login()
            return
        # Transport error or 5xx: keep the cached identity and session alive.
        self._resume_offline(str(exc))

    def _resume_offline(self, reason: str = "") -> None:
        if self.me is None or not isValid(self):
            return
        self._offline = True
        self.rail.set_user(self.me)
        self.topbar.user.set_user(self.me.username)
        self.stack.setCurrentWidget(self.shell)
        self.back_stack = []
        self._set_online(False, pending=self.api.pending_writes())
        self.apply_settings(
            Settings.from_json({**self.settings.to_json(),
                                "theme": self.store.theme,
                                "accent": self.store.accent,
                                "iconStroke": self.store.icon_stroke,
                                "iconFilled": self.store.icon_filled,
                                "volume": self.store.volume}),
            persist=False,
        )
        if not isinstance(self.current_screen, Screen):
            self.navigate(("home",), push=False)
        self._restore_queue()
        self._device_timer.stop()
        self._publish_timer.stop()
        self._remote_timer.stop()
        self._retry_timer.start()
        self._sleep_timer.start()
        if reason:
            self.toast("Offline — using saved session")

    def _retry_connection(self) -> None:
        if self.me is None or not self._offline:
            self._retry_timer.stop()
            return
        self.run(lambda: self.repo.me(force=True), self._retry_ok,
                 self._restore_failed)

    def _retry_ok(self, me: Me) -> None:
        self.toast("Back online")
        self.after_login(me)

    def _set_online(self, online: bool, *, pending: int = 0,
                    notice: Optional[str] = None) -> None:
        if notice is not None:
            self._notice = notice
        self.rail.set_online(online)
        self.status_strip.set_state(
            online=online,
            pending=pending if online else self.api.pending_writes(),
            notice=self._notice if online else "",
            has_update=bool(self._update_url),
        )

    def open_update(self) -> None:
        if not self._update_url:
            return
        if not confirm(self, "Update available",
                       "Open the download page for this update in your browser?",
                       confirm_label="Open"):
            return
        QDesktopServices.openUrl(QUrl(self._update_url))

    def sign_out(self) -> None:
        def job() -> None:
            self.repo.logout()
            self.repo.app_logout()

        self.run(job, lambda _: None, lambda _exc: None)
        self.me = None
        self._offline = False
        self.store.clear_session()
        self.store.reset_token = ""
        self.api.cookies.clear()
        self.store.save_cookies({})
        self.ART_clear()
        self.player.clear()
        self.playlists = []
        self.rail.set_playlists([], None)
        self.rail.set_user(None)
        self.topbar.user.set_user("")
        self.topbar.search.set_text("")
        self._search = ""
        self.current_screen = None
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.stack.setCurrentWidget(self.login_page or self.splash)
        self.show_login()
        self.toast("Signed out")

    def ART_clear(self) -> None:
        ART.clear()
        self.update()

    def change_server(self, url: str) -> None:
        try:
            self.api.set_base(url)
        except Exception:
            self.toast("That server address is not valid")
            return
        self.api.cookies.clear()
        self.store.save_cookies({})
        ART.clear()

        def ok(me: Me) -> None:
            self.toast(f"Connected to {self.api.base_url}")
            self.after_login(me)

        def fail(exc: Exception) -> None:
            self.toast(str(exc) or "Can't reach that server")
            self.sign_out()

        self.run(lambda: self.repo.me(force=True), ok, fail)

    def _load_settings(self) -> None:
        local = Settings(theme=self.store.theme, accent=self.store.accent,
                         iconStroke=self.store.icon_stroke,
                         iconFilled=self.store.icon_filled,
                         volume=self.store.volume, room_url=self.store.room_url)
        self.apply_settings(local, persist=False)
        self.run(self.repo.settings, self._settings_loaded, lambda _exc: None)

    def _settings_loaded(self, remote: Settings) -> None:
        if remote.room_url:
            self.store.room_url = remote.room_url
        else:
            remote = replace(remote, room_url=self.store.room_url)
        self.apply_settings(remote, persist=False)

    # ── appearance ──────────────────────────────────────────────────────
    def _system_appearance_changed(self, *_args) -> None:
        """Bare family ids repaint when the OS switches light/dark."""
        if getattr(self, "settings", None) is not None:
            self.apply_settings(self.settings, persist=False)

    def apply_settings(self, settings: Settings, persist: bool = True) -> None:
        self.settings = settings
        theme.set_appearance(settings.theme, settings.accent)
        icons.set_icon_style(settings.iconStroke, settings.iconFilled)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.stylesheet())
            app.setPalette(theme.qpalette())
        widgets.set_covers(settings.covers)
        widgets.set_density(settings.density)
        self.store.theme = settings.theme
        self.store.accent = settings.accent
        self.store.icon_stroke = settings.iconStroke
        self.store.icon_filled = settings.iconFilled
        if settings.remember_volume:
            self.store.volume = settings.volume
            self.player.set_volume(settings.volume)
        widgets.refresh_theme(self)
        if self.current_screen is not None:
            self.current_screen.apply_settings(settings)
        self._refresh_deck()
        self._refresh_progress()
        if persist:
            def save() -> int:
                self.repo.save_settings(settings)
                return self.api.pending_writes()

            self.run(save, lambda pending: self._set_online(
                not self._offline, pending=pending), lambda _exc: None)

    def set_volume(self, value: float) -> None:
        value = min(1.0, max(0.0, value))
        self.player.set_volume(value)
        self.store.volume = value
        if self.settings.remember_volume:
            self.settings = replace(self.settings, volume=value)
        self.deck.volume.set_level(value, self.player.muted)
        self._refresh_deck()

    def toast(self, text: str) -> None:
        if not isValid(self):
            return
        self.toast_widget.show_message(str(text))
        self.toast_widget.raise_()

    # ── routing ─────────────────────────────────────────────────────────
    def navigate(self, route: tuple, push: bool = True) -> None:
        route = tuple(route)
        if push and route != self.route:
            self.back_stack.append(self.route)
        self.route = route
        self._show_route()

    def back(self) -> None:
        if self.back_stack:
            self.route = self.back_stack.pop()
            self._show_route()
            return
        if self.route != ("home",):
            self.route = ("home",)
            self._show_route()

    def _show_route(self) -> None:
        screen = self._make_screen(self.route)
        if self.current_screen is not None:
            self.content_layout.removeWidget(self.current_screen)
            self.current_screen.setParent(None)
            self.current_screen.deleteLater()
        self.current_screen = screen
        self.content_layout.addWidget(screen)
        self.rail.set_active(self.route)
        self.topbar.back.setVisible(bool(self.back_stack))
        screen.apply_settings(self.settings)

    def _make_screen(self, route: tuple) -> Screen:
        kind = route[0] if route else "home"
        if kind == "search":
            return SearchScreen(self, self.topbar.search.text())
        if kind == "library":
            tab = route[1] if len(route) > 1 else "songs"
            return LibraryScreen(self, tab)
        if kind == "album" and len(route) > 1:
            return CollectionScreen(self, route[1], "album")
        if kind == "artist" and len(route) > 1:
            return CollectionScreen(self, route[1], "artist")
        if kind == "likes":
            return LikesScreen(self)
        if kind == "playlists":
            return PlaylistsScreen(self)
        if kind == "playlist" and len(route) > 1:
            return PlaylistScreen(self, route[1])
        if kind == "requests":
            return RequestsScreen(self)
        if kind == "downloads":
            return DownloadsScreen(self)
        if kind == "devices":
            return DevicesScreen(self)
        if kind == "listening":
            return ListeningScreen(self)
        if kind == "settings":
            return SettingsScreen(self)
        if kind == "admin":
            return AdminScreen(self) if (self.me and self.me.is_admin) else HomeScreen(self)
        return HomeScreen(self)

    def on_search_text(self, text: str) -> None:
        self._search = text
        if not text.strip():
            if self.route[0] == "search" and self.current_screen is not None:
                self.current_screen.set_query("")
            return
        if self.route[0] != "search":
            self.navigate(("search",), push=True)
        elif self.current_screen is not None:
            self.current_screen.set_query(text)

    def on_search_submit(self, text: str) -> None:
        self.on_search_text(text)

    def refresh_playlists(self) -> None:
        self.run(self.repo.playlists, self._playlists_loaded, lambda _exc: None)

    def _playlists_loaded(self, playlists: list[PlaylistRef]) -> None:
        self.playlists = playlists
        active = self.route[1] if self.route[0] == "playlist" and len(self.route) > 1 else None
        self.rail.set_playlists(playlists, active)

    # ── playback ────────────────────────────────────────────────────────
    def _playable(self, tracks: Sequence[Track]) -> list[Track]:
        if self.settings.hide_explicit:
            return [t for t in tracks if not t.explicit]
        return list(tracks)

    def play_tracks(self, tracks: Sequence[Track], index: int = 0) -> None:
        playable = self._playable(tracks)
        if not playable:
            self.toast("Nothing to play")
            return
        target = tracks[index] if 0 <= index < len(tracks) else None
        at = 0
        if target is not None:
            at = next((i for i, t in enumerate(playable) if t.id == target.id), 0)
        self.player.play(playable, at)

    def shuffle_tracks(self, tracks: Sequence[Track]) -> None:
        playable = self._playable(tracks)
        if not playable:
            self.toast("Nothing to play")
            return
        self.player.play(playable, 0, shuffle_start=True)

    def play_album(self, name: str) -> None:
        self.run(lambda: self.repo.album(name),
                 lambda tracks: self.play_tracks(tracks, 0))

    def play_artist(self, name: str) -> None:
        self.run(lambda: self.repo.artist(name),
                 lambda tracks: self.play_tracks(tracks, 0))

    def play_playlist(self, playlist_id: int) -> None:
        self.run(lambda: self.repo.playlist(playlist_id),
                 lambda result: self.play_tracks(result[1], 0))

    def queue_next(self, track: Track) -> None:
        if not self.player.queue:
            self.play_tracks([track], 0)
            return
        self.player.add(track, next=True)
        self.toast("Playing next")

    def queue_add(self, track: Track) -> None:
        if not self.player.queue:
            self.play_tracks([track], 0)
            return
        self.player.add(track)
        self.toast("Added to queue")

    def start_radio(self, track: Track) -> None:
        def ok(rest: list[Track]) -> None:
            self.player.play([track] + rest, 0)
            self.toast("Radio started")

        self.run(lambda: self.repo.radio(track.id), ok)

    def _autoplay_radio(self, seed_id: int) -> None:
        """Refill from radio after the last track ends naturally (repeat off)."""
        seed = self.player.current
        if (seed is None or seed.id != seed_id or self._radio_busy
                or not self.settings.autoplay or self.player.repeat != "off"):
            return
        if self.player.index != len(self.player.queue) - 1:
            return
        self._radio_busy = True

        def ok(rest: list[Track]) -> None:
            self._radio_busy = False
            current = self.player.current
            if (current is None or current.id != seed_id or self.player.playing
                    or not self.settings.autoplay or self.player.repeat != "off"
                    or self.player.index != len(self.player.queue) - 1):
                return
            have = {t.id for t in self.player.queue}
            additions: list[Track] = []
            for track in rest:
                if track.id <= 0 or track.id in have:
                    continue
                have.add(track.id)
                additions.append(track)
                if len(additions) == 5:
                    break
            if not additions:
                return
            first_new = len(self.player.queue)
            self.player.queue.extend(additions)
            self.player.jump(first_new)

        def fail(_exc: Exception) -> None:
            self._radio_busy = False

        self.run(lambda: self.repo.radio(seed_id), ok, fail)

    def like_current(self) -> None:
        track = self.player.current
        if track is not None:
            self.toggle_like(track)

    def toggle_like(self, track: Track) -> None:
        def ok(result) -> None:
            if isinstance(result, dict) and result.get("queued"):
                self._like_done(track.id, not track.liked, "Saved offline — will sync")
                self._set_online(False)
            else:
                self._like_done(track.id, bool(result))

        self.run(lambda: self.repo.like(track.id), ok)

    def _like_done(self, track_id: int, liked: bool,
                   message: Optional[str] = None) -> None:
        self.player.mark_liked(track_id, liked)
        if self.current_screen is not None:
            self.current_screen.apply_like(track_id, liked)
        self.toast(message or ("Liked" if liked else "Removed from liked"))
        self._refresh_deck()

    def toggle_shuffle(self) -> None:
        self.player.toggle_shuffle()
        self._refresh_deck()
        if not self.player.shuffle:
            return
        current = self.player.current
        if current is None or len(self.player.queue) < 2:
            return

        def ok(ranked: list[int]) -> None:
            # Ignore a late answer if the user toggled shuffle off meanwhile.
            now = self.player.current
            if (not self.player.shuffle or now is None or now.id != current.id
                    or not self.player.apply_model_order(ranked)):
                return
            self._refresh_deck()

        self.run(lambda: self.repo.model_rank(current.id, self.player.queue_ids()),
                 ok, lambda _e: None)

    def toggle_explicit(self, track: Track) -> None:
        self.run(lambda: self.repo.set_explicit(track.id, not track.explicit),
                 lambda value: (self.player.mark_explicit(track.id, value),
                                self.toast("Updated"), self._refresh_deck()))

    def make_track_list(self, tracks: Sequence[Track], screen: Screen,
                        playlist_id: Optional[int] = None):
        track_list = widgets.TrackList(show_stats=self.settings.yt_stats)
        current = self.player.current
        track_list.set_tracks(tracks, current.id if current else None)
        track_list.play_requested.connect(lambda index: self.play_tracks(tracks, index))
        track_list.like_requested.connect(self.toggle_like)
        track_list.more_requested.connect(
            lambda track, index, pos: self.open_track_menu(track, index, pos, playlist_id)
        )
        return track_list

    # ── deck / overlays ─────────────────────────────────────────────────
    def _refresh_deck(self) -> None:
        if not hasattr(self, "deck"):
            return
        player = self.player
        track = player.current
        if track is None:
            self.deck.title.setText("Nothing playing right now")
            self.deck.artist.setText("Pick a song from your library")
            self.deck.like.setVisible(False)
            self.deck.art.set_cover(None)
        else:
            self.deck.title.setText(track.title)
            self.deck.artist.setText(
                "  ·  ".join(x for x in (track.artist, track.album) if x)
            )
            self.deck.like.setVisible(True)
            self.deck.like.set_active(track.liked)
            self.deck.like.set_fill(track.liked)
            self.deck.art.set_cover(track.id)
        self.deck.play.set_playing(player.playing)
        self.deck.shuffle.set_active(player.shuffle)
        self.deck.repeat.set_icon("repeat-1" if player.repeat == "one" else "repeat")
        self.deck.repeat.set_active(player.repeat != "off")
        self.deck.volume.set_level(player.volume, player.muted)
        self.deck.seek.set_values(player.position, player.duration)
        self.deck.pos.setText(fmt_time(player.position))
        self.deck.dur.setText(fmt_time(player.duration))

    def _refresh_progress(self) -> None:
        if not hasattr(self, "deck"):
            return
        player = self.player
        self.deck.seek.set_values(player.position, player.duration)
        self.deck.pos.setText(fmt_time(player.position))
        self.deck.dur.setText(fmt_time(player.duration))
        self.deck.play.set_playing(player.playing)
        if self.overlay.isVisible():
            self.overlay.pos.setText(fmt_time(player.position))
            self.overlay.dur.setText(fmt_time(player.duration))
            self.overlay.seek.set_values(player.position, player.duration)
            self.overlay.play.set_playing(player.playing)
        self._publish_activity()

    def _refresh_playback(self) -> None:
        self._refresh_deck()
        self._refresh_progress()
        if self.overlay.isVisible():
            self.overlay.refresh()
        if self.drawer.isVisible():
            self.drawer.refresh()
        self.rail.set_active(self.route)

    def _update_window_title(self) -> None:
        track = self.player.current
        if track is None:
            self.setWindowTitle("mcmusic")
        else:
            self.setWindowTitle(f"mcmusic — {track.title} · {track.artist}")

    def show_now_playing(self) -> None:
        self.drawer.hide()
        self.scrim.setVisible(False)
        self.overlay.setGeometry(self.shell.rect())
        self.overlay.refresh()
        self.overlay.show()
        self.overlay.raise_()
        self.toast_widget.raise_()

    def toggle_queue(self) -> None:
        if self.drawer.isVisible():
            self.close_overlays()
            return
        if self.me is None:
            return
        self.overlay.hide()
        self.position_overlays()
        self.drawer.refresh()
        self.scrim.setVisible(True)
        self.scrim.raise_()
        self.drawer.show()
        self.drawer.raise_()
        self.toast_widget.raise_()

    def close_overlays(self) -> None:
        self.drawer.hide()
        self.scrim.setVisible(False)
        self.overlay.hide()

    def position_overlays(self) -> None:
        if not hasattr(self, "scrim"):
            return
        self.scrim.setGeometry(self.shell.rect())
        self.drawer.setGeometry(self.shell.width() - 390, 0, 390, self.shell.height())
        self.overlay.setGeometry(self.shell.rect())
        if getattr(self, "toast_widget", None) is not None and self.toast_widget.isVisible():
            self.toast_widget._reposition()

    # ── menus and dialogs ───────────────────────────────────────────────
    def _menu_icon(self, name: str, token: str = "dim"):
        return icons.icon(name, getattr(theme.pal(), token), 16)

    def open_track_menu(self, track: Track, index: int = 0, pos=None,
                        playlist_id: Optional[int] = None) -> None:
        menu = QMenu(self)

        def add(icon_name: str, label: str, callback: Callable[[], None],
                *, token: str = "dim", shortcut: str = "") -> None:
            action = menu.addAction(self._menu_icon(icon_name, token), label)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)

        add("play", "Play now", lambda: self.play_tracks([track], 0))
        add("list-music", "Play next", lambda: self.queue_next(track))
        add("plus", "Add to queue", lambda: self.queue_add(track))
        add("folder-plus", "Add to playlist…",
            lambda: self._add_to_playlist_dialog(track))
        add("radio", "Start radio", lambda: self.start_radio(track))
        menu.addSeparator()
        if track.album:
            add("disc-3", "Go to album",
                lambda: self.navigate(("album", track.album)))
        if track.artist:
            add("users", "Go to artist",
                lambda: self.navigate(("artist", track.artist)))
        menu.addSeparator()
        add("heart", "Remove from liked" if track.liked else "Like",
            lambda: self.toggle_like(track),
            token="accent" if track.liked else "dim")
        add("info", "Track info", lambda: self._track_info(track))
        if playlist_id is not None:
            menu.addSeparator()
            add("trash-2", "Remove from playlist",
                lambda: self._remove_from_playlist(playlist_id, track), token="err")
        if self.me and self.me.is_admin:
            menu.addSeparator()
            add("triangle-alert",
                "Mark as clean" if track.explicit else "Mark as explicit",
                lambda: self.toggle_explicit(track))
        if pos is not None:
            menu.exec(pos)
        else:
            menu.exec(self.cursor().pos())

    def _remove_from_playlist(self, playlist_id: int, track: Track) -> None:
        def ok(_) -> None:
            self.toast("Removed from playlist")
            if (self.route[0] == "playlist" and len(self.route) > 1
                    and self.route[1] == playlist_id and self.current_screen is not None):
                self.current_screen.load()
            self.refresh_playlists()

        self.run(lambda: self.repo.remove_from_playlist(playlist_id, track.id), ok)

    def _track_info(self, track: Track) -> None:
        sheet = Sheet(self, "Track info")
        head = QHBoxLayout()
        head.setSpacing(12)
        art = Artwork(64, kind="track")
        art.set_cover(track.id)
        head.addWidget(art)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(3)
        text.addWidget(Txt(track.title, size=13, token="fg", weight=QFont.Weight.Medium))
        text.addWidget(Txt(" · ".join(x for x in (track.artist, track.album) if x),
                           size=11, token="dim2"))
        head.addLayout(text, 1)
        sheet.body.addLayout(head)
        sheet.body.addSpacing(10)

        rows = [
            ("Length", fmt_time(track.duration)),
            ("Track", str(track.track_no) if track.track_no else "—"),
            ("Year", track.year or "—"),
            ("Genre", track.genre or "—"),
            ("Explicit", "Yes" if track.explicit else "No"),
        ]
        if track.yt_channel:
            rows.append(("Channel", track.yt_channel))
        if track.yt_likes is not None:
            rows.append(("YT likes", fmt_count(track.yt_likes)))
        if track.yt_views is not None:
            rows.append(("YT views", fmt_count(track.yt_views)))
        if track.yt_date:
            rows.append(("Uploaded", track.yt_date))
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(7)
        for i, (key, value) in enumerate(rows):
            grid.addWidget(Txt(key.upper(), size=9, family="mono", token="dim2",
                               spacing=0.8), i, 0)
            grid.addWidget(Txt(value, size=13, token="fg"), i, 1)
        grid.setColumnStretch(1, 1)
        sheet.body.addLayout(grid)

        sheet.body.addSpacing(10)
        sheet.body.addWidget(Txt("SOURCES", size=9, family="mono", token="dim2",
                                 spacing=1.2))
        sources = Txt("Reading source metadata…", size=11, token="dim", wrap=True)
        sheet.body.addWidget(sources)

        def sources_ok(rows: list[dict]) -> None:
            if not isValid(sources):
                return
            if not rows:
                sources.setText("No source metadata recorded")
                return
            lines = []
            for row in rows[:10]:
                name = str(row.get("source") or row.get("kind") or "source")
                detail = row.get("url") or row.get("title") or row.get("id") or ""
                lines.append(f"{name}: {detail}")
            sources.setText("\n".join(lines))

        self.run(lambda: self.repo.track_sources(track.id), sources_ok,
                 error=lambda _e: sources.setText("Sources unavailable offline"))
        if track.yt_id:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
            sheet.body.addSpacing(8)
            open_yt = McButton("Open on YouTube", small=True, icon="arrow-up-right")
            open_yt.clicked.connect(lambda: QDesktopServices.openUrl(
                QUrl(f"https://www.youtube.com/watch?v={track.yt_id}")))
            sheet.body.addWidget(open_yt, 0, Qt.AlignmentFlag.AlignLeft)
        sheet.exec()

    def _add_to_playlist_dialog(self, track: Track) -> None:
        sheet = Sheet(self, "Add to playlist")
        list_host = QWidget()
        listing = QVBoxLayout(list_host)
        listing.setContentsMargins(0, 0, 0, 0)
        listing.setSpacing(1)
        sheet.body.addWidget(list_host)
        hint = Txt("No playlists yet — name one below.", size=11, token="dim2")
        hint.setVisible(False)
        sheet.body.addWidget(hint)

        def add_to(playlist: PlaylistRef) -> None:
            def ok(_) -> None:
                sheet.accept()
                self.toast("Added to playlist")
                self.refresh_playlists()

            self.run(lambda: self.repo.add_to_playlist(playlist.id, track.id), ok)

        for playlist in self.playlists:
            pick = PickRow(playlist)
            pick.clicked.connect(lambda _=False, p=playlist: add_to(p))
            listing.addWidget(pick)
        if not self.playlists:
            hint.setVisible(True)

        sheet.body.addSpacing(12)
        row = QHBoxLayout()
        row.setSpacing(8)
        name = QLineEdit()
        name.setPlaceholderText("New playlist name")
        name.setFixedHeight(34)
        row.addWidget(name, 1)
        create = McButton("Create", small=True)

        def create_and_add() -> None:
            value = name.text().strip()
            if not value:
                return
            create.setEnabled(False)

            def job() -> int:
                pid = self.repo.create_playlist(value)
                self.repo.add_to_playlist(pid, track.id)
                return pid

            def ok(_pid: int) -> None:
                sheet.accept()
                self.toast("Added to playlist")
                self.refresh_playlists()

            def fail(exc: Exception) -> None:
                create.setEnabled(True)
                self.toast(str(exc) or "Could not create playlist")

            self.run(job, ok, fail)

        create.clicked.connect(create_and_add)
        name.returnPressed.connect(create_and_add)
        row.addWidget(create)
        sheet.body.addLayout(row)
        name.setFocus()
        sheet.exec()

    def create_playlist(self) -> None:
        name = prompt(self, "New playlist", "Name", placeholder="Late night drives",
                      confirm="Create")
        if not name:
            return

        def ok(_pid: int) -> None:
            self.toast("Playlist created")
            self.refresh_playlists()
            if self.route[0] == "playlists" and self.current_screen is not None:
                self.current_screen.load()

        self.run(lambda: self.repo.create_playlist(name), ok)

    def add_current_to_playlist(self) -> None:
        track = self.player.current
        if track is not None:
            self._add_to_playlist_dialog(track)

    def show_lyrics(self) -> None:
        track = self.player.current
        if track is None:
            self.toast("Play a track to see its lyrics")
            return
        sheet = Sheet(self, "Lyrics")
        sheet.body.addWidget(Txt(f"{track.title} — {track.artist}", size=12,
                                 token="dim", wrap=True))
        visualizer = LyricVisualizer(self.player, sheet)
        sheet.body.addWidget(visualizer)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlaceholderText("No lyrics have been found for this track yet.")
        sheet.body.addWidget(view, 1)
        sheet.resize(560, 520)

        def ok(data: dict) -> None:
            if not isValid(view):
                return
            text = str(data.get("lyrics") or data.get("text") or "")
            source = str(data.get("source") or "")
            view.setPlainText(text or "No lyrics have been found for this track yet.")
            if source and hasattr(sheet, "setWindowTitle"):
                sheet.setWindowTitle("Lyrics · " + source)

        self.run(lambda: self.repo.lyrics(track.id), ok,
                 error=lambda _e: view.setPlaceholderText("Lyrics are unavailable offline"))
        sheet.finished.connect(lambda _result=0: visualizer.stop())
        sheet.exec()

    def show_sleep_menu(self, button: QWidget) -> None:
        menu = QMenu(self)
        for label, minutes in (
            ("Off", 0), ("5 minutes", 5), ("15 minutes", 15),
            ("30 minutes", 30), ("45 minutes", 45), ("60 minutes", 60),
        ):
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _=False, m=minutes: self.set_sleep_timer(m)
            )
        menu.exec(button.mapToGlobal(QPoint(0, button.height())))

    def set_sleep_timer(self, minutes: int) -> None:
        if minutes <= 0:
            self.store.sleep_timer = {}
            self.toast("Sleep timer off")
        else:
            self.store.sleep_timer = {
                "ends_at": time.time() + minutes * 60, "minutes": minutes,
            }
            self.toast(f"Sleep timer set for {minutes} minutes")
        if hasattr(self, "overlay"):
            self.overlay.refresh()

    def _check_sleep_timer(self) -> None:
        timer = self.store.sleep_timer
        if not timer:
            return
        try:
            ends = float(timer.get("ends_at", 0))
        except (TypeError, ValueError):
            self.store.sleep_timer = {}
            return
        if time.time() < ends:
            return
        self.store.sleep_timer = {}
        if self.player.playing:
            self.player.pause()
            self.toast("Sleep timer finished")
        if hasattr(self, "overlay"):
            self.overlay.refresh()

    def sync_outbox(self, quiet: bool = False) -> None:
        def job() -> tuple[int, int]:
            return self.api.flush_outbox()

        def ok(result: tuple[int, int]) -> None:
            sent, pending = result
            self._set_online(not self._offline, pending=pending)
            if sent and not quiet:
                self.toast(f"Synced {sent} offline change" + ("" if sent == 1 else "s"))

        def fail(exc: Exception) -> None:
            if isinstance(exc, ApiError) and exc.status == 401:
                self.sign_out()
            else:
                self._set_online(False)

        self.run(job, ok, fail)

    def _restore_queue(self) -> None:
        def ok(tracks: list[Track]) -> None:
            ids = {t.id for t in tracks}
            if self.player.restore_snapshot(ids):
                self._refresh_playback()

        def fail(_exc: Exception) -> None:
            if self.player.restore_snapshot():
                self._refresh_playback()

        self.run(self.repo.tracks, ok, fail)

    def _verify_pending_token(self) -> None:
        token = self.store.pending_token
        if not token:
            return

        def job() -> Me:
            self.repo.verify_token(token)
            return self.repo.adopt_token(token)

        def ok(me: Me) -> None:
            self.store.pending_token = ""
            self.toast("Rotur sign-in restored")

        def fail(exc: Exception) -> None:
            if isinstance(exc, ApiError) and exc.status == 401:
                self.store.pending_token = ""
            elif not (isinstance(exc, ApiError) and exc.offline):
                self.toast("Saved Rotur sign-in could not be verified")

        self.run(job, ok, fail)

    def _check_updates(self) -> None:
        def job() -> tuple[list, dict]:
            return self.repo.builds(), self.repo.version()

        def ok(result: tuple[list, dict]) -> None:
            builds, _version = result
            kinds = {
                "Darwin": ("macos-dmg", "macos"),
                "Windows": ("windows-zip", "windows"),
            }.get(platform.system(), ("linux-appimage", "linux-deb"))
            for build in builds:
                if getattr(build, "kind", "") in kinds and getattr(build, "available", False):
                    if getattr(build, "version", "") and build.version != VERSION:
                        self._update_kind = build.kind
                        self._update_url = self.repo.build_url(build.url)
                        self._set_online(not self._offline, pending=self.api.pending_writes(),
                                         notice=f"Update available · {build.label}")
                        return
            self._update_kind = ""
            self._update_url = ""
            self._set_online(not self._offline, pending=self.api.pending_writes(),
                             notice="")

        self.run(job, ok, lambda _exc: None)

    def _publish_activity(self) -> None:
        settings = self.settings
        track = self.player.current
        playing = self.player.playing
        bucket = int(self.player.position // 5)
        if not (settings.rotur_activity or settings.discord_activity):
            if self._activity_sig == "off":
                return
            self._activity_sig = "off"
            sig = (None, False, 0)
        else:
            sig = (track.id if track else None, playing, bucket)
            if sig == self._activity_sig:
                return
            now = time.time()
            if now - self._activity_at < 5:
                return
            self._activity_at = now
            self._activity_sig = sig

        track_id = sig[0] if settings.rotur_activity or settings.discord_activity else None
        position = self.player.position if sig[1] else 0.0
        is_playing = bool(sig[1]) if settings.rotur_activity or settings.discord_activity else False

        def job() -> None:
            if settings.rotur_activity or not is_playing:
                try:
                    self.repo.rotur_activity(track_id, position, is_playing)
                except ApiError:
                    pass
            if settings.discord_activity or not is_playing:
                try:
                    self.repo.discord_activity(track_id, position, is_playing)
                except ApiError:
                    pass

        self.run(job, lambda _: None, lambda _exc: None)

    def _clear_activity(self, *, sync: bool = False) -> None:
        self._activity_sig = ""
        if sync:
            for send in (self.repo.rotur_activity, self.repo.discord_activity):
                try:
                    send(None, 0.0, False)
                except Exception:
                    pass
        else:
            self.run(lambda: self.repo.rotur_activity(None, 0.0, False),
                     lambda _: None, lambda _exc: None)
            self.run(lambda: self.repo.discord_activity(None, 0.0, False),
                     lambda _: None, lambda _exc: None)

    def _poll_remote(self) -> None:
        if self.me is None:
            return
        self.run(self.repo.playback, self._apply_remote, lambda _exc: None)

    def _apply_remote(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        for command in data.get("commands") or []:
            if not isinstance(command, dict):
                continue
            try:
                cid = int(command.get("id") or 0)
            except (TypeError, ValueError):
                cid = 0
            if cid and cid <= self._last_remote_command:
                continue
            if cid:
                self._last_remote_command = cid
            action = str(command.get("action") or "")
            arg = command.get("arg") if isinstance(command.get("arg"), dict) else {}
            if action == "play":
                if not self.player.playing:
                    self.player.toggle()
            elif action == "pause":
                if self.player.playing:
                    self.player.pause()
            elif action == "toggle":
                self.player.toggle()
            elif action in ("next", "skip"):
                self.player.next()
            elif action == "prev":
                self.player.prev()
            elif action == "seek":
                try:
                    self.player.seek(float(arg.get("position") or 0))
                except (TypeError, ValueError):
                    pass
            elif action == "remove":
                try:
                    self.player.remove_at(int(arg.get("index") or 0))
                except (TypeError, ValueError):
                    pass
            elif action in ("enqueue", "play_track"):
                raw = arg.get("track")
                if isinstance(raw, dict):
                    track = Track.from_json(raw)
                    if action == "enqueue":
                        self.player.add(track)
                    else:
                        self.player.play([track], 0)
                    continue
                try:
                    tid = int(arg.get("track_id") or 0)
                except (TypeError, ValueError):
                    tid = 0
                if not tid:
                    continue

                def ok(track: Optional[Track], replace_queue=action == "play_track") -> None:
                    if track is None:
                        return
                    if replace_queue:
                        self.player.play([track], 0)
                    else:
                        self.player.add(track)

                self.run(lambda t=tid: self.repo.find_track(t), ok)

    # ── background sync ─────────────────────────────────────────────────
    def _heartbeat(self) -> None:
        if self.me is None:
            return
        track = self.player.current
        self.run(
            lambda: self.repo.heartbeat(
                self.store.device_hash, device_name(),
                track.id if track else None, self.player.position,
                not self.player.playing,
            ),
            lambda _: self._set_online(True, pending=self.api.pending_writes()),
            lambda _exc: self._set_online(False),
        )

    def _publish_playback(self) -> None:
        if self.me is None or not self.player.queue:
            return
        track = self.player.current
        self.run(
            lambda: self.repo.publish_playback(
                track.id if track else None, self.player.position,
                self.player.duration, self.player.playing, self.player.queue_ids(),
                self.store.device_hash,
            ),
            lambda _: self._set_online(True, pending=self.api.pending_writes()),
            lambda _exc: self._set_online(False),
        )

    def run(self, fn: Callable[[], Any], ok: Optional[Callable[[Any], None]] = None,
            error: Optional[Callable[[Exception], None]] = None) -> None:
        def safe_ok(value: Any) -> None:
            if isValid(self) and ok is not None:
                ok(value)

        def safe_error(exc: Exception) -> None:
            if not isValid(self):
                return
            if error is not None:
                error(exc)
            else:
                self.toast(str(exc) or "Something went wrong")

        self.runner.submit(fn, safe_ok, safe_error)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.position_overlays()

    def closeEvent(self, event) -> None:
        self._clear_activity(sync=True)
        try:
            self.api.flush_outbox()
        except Exception:
            pass
        self.player.shutdown()
        self.runner.shutdown()
        super().closeEvent(event)
