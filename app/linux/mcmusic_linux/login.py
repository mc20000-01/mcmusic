"""First-run / signed-out screen."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPainter
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
    prompt,
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

        self.seg = Segmented(
            [("in", "Sign in"), ("up", "Create account"), ("reset", "Reset")], "in"
        )
        self.seg.changed.connect(self._set_mode)
        form.addWidget(self.seg, 0, Qt.AlignmentFlag.AlignHCenter)

        self.username = LabeledField("Username", "your username")
        self.password = LabeledField("Password", "••••••••", password=True)
        self.invite = LabeledField("Invite code", "optional on open servers")
        self.invite.setVisible(False)
        self.email = LabeledField("Account email", "you@example.com")
        self.reset_token = LabeledField("Reset code", "paste the code from your email")
        self.new_password = LabeledField("New password", "at least 6 characters",
                                         password=True)
        for field in (self.email, self.reset_token, self.new_password):
            field.setVisible(False)
        form.addWidget(self.username)
        form.addWidget(self.password)
        form.addWidget(self.invite)
        form.addWidget(self.email)
        form.addWidget(self.reset_token)
        form.addWidget(self.new_password)

        self.forgot = McButton("Forgot password?", small=True, ghost=True)
        self.forgot.clicked.connect(
            lambda: (self.seg.set_selected("reset"), self._set_mode("reset"))
        )
        form.addWidget(self.forgot, 0, Qt.AlignmentFlag.AlignLeft)

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

        self.rotur = McButton("Sign in with RoturLink", ghost=True, icon="link")
        self.rotur.clicked.connect(self._rotur_sign_in)
        form.addWidget(self.rotur)

        self.password.edit.returnPressed.connect(self._submit)
        self.username.edit.returnPressed.connect(lambda: self.password.edit.setFocus())
        self.invite.edit.returnPressed.connect(self._submit)
        self.email.edit.returnPressed.connect(self._submit)
        self.reset_token.edit.returnPressed.connect(
            lambda: self.new_password.edit.setFocus()
        )
        self.new_password.edit.returnPressed.connect(self._submit)
        self.reset_token.set_text(window.store.reset_token)
        self._set_mode("in")
        self._apply_style()

    # ── appearance ──────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        p = theme.pal()
        self.card.setStyleSheet(
            f"QWidget#loginCard{{background:{p.bg2};border:1px solid {p.line2};"
            f"border-radius:10px;}}"
        )

    def refresh_theme(self) -> None:
        self._apply_style()
        self.update()

    def paintEvent(self, _event) -> None:
        QPainter(self).fillRect(self.rect(), theme.pal().q("bg"))

    # ── behaviour ───────────────────────────────────────────────────────
    def _button_text(self) -> str:
        if self._mode == "up":
            return "Create account"
        if self._mode == "reset":
            return "Reset password" if self.reset_token.text().strip() else "Send reset code"
        return "Sign in"

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        signing_in = mode in ("in", "up")
        self.username.setVisible(signing_in)
        self.password.setVisible(signing_in)
        self.invite.setVisible(mode == "up")
        self.forgot.setVisible(mode == "in")
        self.rotur.setVisible(signing_in)
        for field in (self.email, self.reset_token, self.new_password):
            field.setVisible(mode == "reset")
        self.submit.set_text(self._button_text())
        self._show_error("")

    def _show_error(self, message: str) -> None:
        self.error.setText(message)
        self.error.setVisible(bool(message))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.submit.setEnabled(not busy)
        self.rotur.setEnabled(not busy)
        self.submit.set_text("Please wait…" if busy else self._button_text())

    def _apply_server(self) -> bool:
        try:
            self.window.api.set_base(self.server.text().strip())
            return True
        except Exception:
            self._show_error("That server address is not valid")
            return False

    def _submit(self) -> None:
        if self._busy:
            return
        if self._mode == "reset":
            self._submit_reset()
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
        if not self._apply_server():
            return
        self._set_busy(True)
        invite = self.invite.text().strip()

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

    def _submit_reset(self) -> None:
        token = self.reset_token.text().strip() or self.window.store.reset_token
        email = self.email.text().strip()
        password = self.new_password.text()
        self._show_error("")
        if not self._apply_server():
            return
        if not token:
            if not email or "@" not in email:
                self._show_error("Enter the email for your account")
                return
            self._set_busy(True)

            def request_code() -> dict:
                return self.window.repo.request_reset(email)

            def sent(data: dict) -> None:
                self._set_busy(False)
                message = ""
                if isinstance(data, dict):
                    message = str(data.get("message") or "")
                self.window.toast(message or "If that email has an account, a code is on its way.")

            def failed(exc: Exception) -> None:
                self._set_busy(False)
                self._show_error(str(exc) or "Could not request a reset code")

            self.window.run(request_code, sent, failed)
            return

        if len(password) < 6:
            self._show_error("New password must be 6+ characters")
            return
        self.window.store.reset_token = token
        self._set_busy(True)

        def confirm() -> None:
            self.window.repo.check_reset(token)
            self.window.repo.confirm_reset(token, password)

        def done(_) -> None:
            self.window.store.reset_token = ""
            self.reset_token.set_text("")
            self.new_password.set_text("")
            self.username.set_text(email)
            self.password.set_text("")
            self._set_busy(False)
            self.seg.set_selected("in")
            self._set_mode("in")
            self.window.toast("Password updated — sign in with the new one")

        def failed(exc: Exception) -> None:
            self._set_busy(False)
            self._show_error(str(exc) or "That reset code could not be used")

        self.window.run(confirm, done, failed)

    def _rotur_sign_in(self) -> None:
        self._show_error("")
        if not self._apply_server():
            return
        QDesktopServices.openUrl(QUrl(self.window.repo.rotur_authorize_url(
            self.window.store.device_hash
        )))
        token = prompt(
            self, "RoturLink sign-in", "Access token",
            placeholder="Paste the token from the browser",
            confirm="Sign in",
        )
        if not token:
            return
        token = token.strip()
        self.window.store.pending_token = token
        self._set_busy(True)

        def job() -> Me:
            self.window.repo.verify_token(token)
            return self.window.repo.adopt_token(token)

        def ok(me: Me) -> None:
            self.window.store.pending_token = ""
            self._set_busy(False)
            self.succeeded.emit(me)

        def failed(exc: Exception) -> None:
            self._set_busy(False)
            offline = isinstance(exc, ApiError) and exc.offline
            self._show_error(
                "Token saved — it will be verified when the server is reachable"
                if offline else (str(exc) or "That token could not be verified")
            )

        self.window.run(job, ok, failed)


class _BrandMark(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_mark(p, QRectF(self.rect()), theme.pal().q("accent"))
