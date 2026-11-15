"""First-run / signed-out screen."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QRadialGradient
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .api import ApiError
from .icons import draw_icon, draw_mark
from .models import Me
from .widgets import (
    Glyph,
    LabeledField,
    McButton,
    Rule,
    Segmented,
    Spinner,
    Txt,
)


class SplashPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.addWidget(Txt("mcmusic", size=26, family="display", token="fg",
                             align=Qt.AlignmentFlag.AlignHCenter))
        spinner = Spinner(18)
        layout.addWidget(spinner, 0, Qt.AlignmentFlag.AlignHCenter)

    def paintEvent(self, _event) -> None:
        QPainter(self).fillRect(self.rect(), theme.pal().q("bg"))


class LoginPage(QWidget):
    succeeded = Signal(object)

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._mode = "in"
        self._busy = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.addStretch(1)

        center = QHBoxLayout()
        center.addStretch(1)
        self.card = QWidget()
        self.card.setObjectName("loginCard")
        self.card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.card.setFixedWidth(380)
        center.addWidget(self.card)
        center.addStretch(1)
        outer.addLayout(center)
        outer.addStretch(1)

        form = QVBoxLayout(self.card)
        form.setContentsMargins(28, 26, 28, 26)
        form.setSpacing(13)

        brand = QHBoxLayout()
        brand.setSpacing(9)
        mark = Glyph("music", 30, "accent_fg")
        mark.setStyleSheet("")
        self._mark = _BrandMark()
        brand.addWidget(self._mark)
        brand.addWidget(Txt("mcmusic", size=24, family="display", token="fg"))
        brand.addStretch(1)
        form.addLayout(brand)
        form.addWidget(Txt("Your library, your room, your rules.", size=13, token="dim2"))

        self.seg = Segmented([("in", "Sign in"), ("up", "Create account")], "in")
        self.seg.changed.connect(self._set_mode)
        form.addWidget(self.seg, 0, Qt.AlignmentFlag.AlignHCenter)

        self.username = LabeledField("Username", "your username")
        self.password = LabeledField("Password", "••••••••", password=True)
        self.invite = LabeledField("Invite code", "optional on open servers")
        self.invite.setVisible(False)
        form.addWidget(self.username)
        form.addWidget(self.password)
        form.addWidget(self.invite)

        self.error = Txt("", size=11, token="err", wrap=True)
        self.error.setVisible(False)
        form.addWidget(self.error)

        self.submit = McButton("Sign in", solid=True)
        self.submit.setFixedHeight(38)
        self.submit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.submit.setMinimumWidth(0)
        self.submit.clicked.connect(self._submit)
        form.addWidget(self.submit)

        form.addWidget(Rule())

        self.server = LabeledField("Server", "https://mcmusic.sdisk.us", leading="cast")
        self.server.set_text(window.api.base_url)
        form.addWidget(self.server)

        form.addWidget(Txt(
            "Sign in with your mcmusic account. The desktop app talks to the same "
            "server API as the web player.",
            size=11, token="dim2", wrap=True,
        ))

        self.password.edit.returnPressed.connect(self._submit)
        self.username.edit.returnPressed.connect(lambda: self.password.edit.setFocus())
        self.invite.edit.returnPressed.connect(self._submit)
        self._apply_style()

    # ── appearance ──────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        p = theme.pal()
        self.card.setStyleSheet(
            f"QWidget#loginCard{{background:{p.bg2};border:1px solid {p.line2};"
            f"border-radius:12px;}}"
        )

    def refresh_theme(self) -> None:
        self._apply_style()
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        palette = theme.pal()
        p.fillRect(self.rect(), palette.q("bg"))
        glow = QRadialGradient(self.width() * 0.5, -40, self.width() * 0.9)
        soft = palette.q("accent")
        soft.setAlpha(46)
        glow.setColorAt(0.0, soft)
        clear = QColor(soft)
        clear.setAlpha(0)
        glow.setColorAt(0.7, clear)
        p.fillRect(self.rect(), glow)

    # ── behaviour ───────────────────────────────────────────────────────
    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        self.invite.setVisible(mode == "up")
        self.submit.set_text("Create account" if mode == "up" else "Sign in")
        self._show_error("")

    def _show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.setVisible(bool(message))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.submit.setEnabled(not busy)
        self.submit.set_text(
            "Please wait…" if busy else ("Create account" if self._mode == "up" else "Sign in")
        )

    def _submit(self) -> None:
        if self._busy:
            return
        username = self.username.text().strip()
        password = self.password.text()
        signup = self._mode == "up"
        if not username or not password:
            self._show_error("Enter a username and password")
            return
        if signup and len(password) < 6:
            self._show_error("Password must be 6+ characters")
            return
        self._show_error("")
        self._set_busy(True)
        server = self.server.text().strip()
        invite = self.invite.text().strip()
        try:
            self.window.api.set_base(server)
        except Exception:
            self._set_busy(False)
            self._show_error("That server address is not valid")
            return

        def job() -> Me:
            if signup:
                return self.window.repo.register(username, password, invite)
            return self.window.repo.login(username, password)

        def ok(me: Me) -> None:
            self._set_busy(False)
            self.succeeded.emit(me)

        def fail(exc: Exception) -> None:
            self._set_busy(False)
            self._show_error(str(exc) or "Sign in failed")

        self.window.run(job, ok, fail)


class _BrandMark(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_mark(p, QRectF(self.rect()), theme.pal().q("accent"))
