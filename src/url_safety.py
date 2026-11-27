"""Shared scheme checks for outbound HTTP requests made by the server.

Every URL accepted from configuration or a request body is validated before it
reaches ``urllib``. Requiring an absolute HTTPS URL keeps file:/ and custom
schemes out and prevents credentials or downloaded bytes from crossing a
plaintext network.
"""
from __future__ import annotations

from urllib.parse import urlsplit


def require_https(url: str) -> str:
    """Return ``url`` unchanged when it is an absolute HTTPS URL.

    Raises ``ValueError`` otherwise. Callers should do this before building a
    ``Request`` so Bandit's B310 warning can be annotated with a proven guard.
    """
    parts = urlsplit(str(url or ""))
    if parts.scheme.lower() != "https" or not parts.netloc:
        raise ValueError(f"refusing non-HTTPS URL: {url!r}")
    return url
