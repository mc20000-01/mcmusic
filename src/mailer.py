"""Outgoing mail — plain SMTP from the standard library.

Password resets and password-change notices go out through the operator's own
mail account, so a self-hosted server needs no vendor signup and no extra
dependency. Set SMTP_HOST/PORT/USER/PASSWORD/FROM in the environment; while
SMTP_HOST is empty `configured()` is false and callers skip sending instead of
failing the request.
"""
import smtplib
import ssl
import os
from email.message import EmailMessage
from email.utils import formataddr

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS,
)


class MailError(RuntimeError):
    pass


def configured():
    return bool(SMTP_HOST and SMTP_FROM)


def send(to, subject, text):
    if not configured():
        raise MailError("SMTP is not configured")
    if not to:
        raise MailError("no recipient")

    msg = EmailMessage()
    msg["From"] = formataddr(("mcmusic", SMTP_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Auto-Submitted"] = "auto-generated"
    msg.set_content(text)

    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT, timeout=20,
                context=ssl.create_default_context(),
            )
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
        with server as s:
            s.ehlo()
            if SMTP_STARTTLS and SMTP_PORT != 465:
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        raise MailError(str(e)) from e


def send_with_attachment(to, subject, text, attachment_path=None, attachment_name=None,
                         mimetype=("application", "vnd.android.package-archive"),
                         html=None):
    """Send a message with a build attached.

    `mimetype` is a (maintype, subtype) pair so an APK, an AppImage, and a deb
    each arrive as themselves instead of as a generic blob. `html` is optional
    and becomes the rich alternative; plain text is always included, because a
    mail client that refuses the HTML is still a mail client.
    """
    if not configured():
        raise MailError("SMTP is not configured")
    if not to:
        raise MailError("no recipient")

    msg = EmailMessage()
    msg["From"] = formataddr(("mcmusic", SMTP_FROM))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Auto-Submitted"] = "auto-generated"
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            payload = f.read()
        maintype, subtype = mimetype
        msg.add_attachment(
            payload,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_name or os.path.basename(attachment_path),
        )

    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT, timeout=20,
                context=ssl.create_default_context(),
            )
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
        with server as s:
            s.ehlo()
            if SMTP_STARTTLS and SMTP_PORT != 465:
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASSWORD)
            s.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        raise MailError(str(e)) from e
