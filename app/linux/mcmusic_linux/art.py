"""Cookie-authenticated cover-art cache (no web engine, no CDN)."""
from __future__ import annotations

from collections import OrderedDict
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage, QPixmap

from .api import Api, Async


class ArtLoader(QObject):
    """Fetches artwork on the network pool and keeps a small pixmap LRU."""

    loaded = Signal(int)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.api: Optional[Api] = None
        self.runner: Optional[Async] = None
        self._cache: "OrderedDict[int, QPixmap]" = OrderedDict()
        self._inflight: set[int] = set()
        self._limit = 260

    def bind(self, api: Api, runner: Async) -> None:
        self.api = api
        self.runner = runner

    def clear(self) -> None:
        self._cache.clear()
        self._inflight.clear()

    def cached(self, track_id: Optional[int]) -> Optional[QPixmap]:
        if not track_id:
            return None
        pm = self._cache.get(track_id)
        if pm is not None:
            self._cache.move_to_end(track_id)
        return pm

    def request(self, track_id: Optional[int]) -> Optional[QPixmap]:
        if not track_id:
            return None
        hit = self.cached(track_id)
        if hit is not None:
            return hit
        if self.api is None or self.runner is None or track_id in self._inflight:
            return None
        self._inflight.add(track_id)
        self.runner.submit(
            lambda: self.api.get_bytes(f"tracks/{track_id}/cover"),
            ok=lambda result, tid=track_id: self._store(tid, result),
            error=lambda _exc, tid=track_id: self._missing(tid),
        )
        return None

    def _store(self, track_id: int, result: tuple[bytes, str]) -> None:
        self._inflight.discard(track_id)
        data = result[0]
        image = QImage.fromData(data)
        if image.isNull():
            return
        pixmap = QPixmap.fromImage(image)
        self._cache[track_id] = pixmap
        while len(self._cache) > self._limit:
            self._cache.popitem(last=False)
        self.loaded.emit(track_id)

    def _missing(self, track_id: int) -> None:
        self._inflight.discard(track_id)


ART = ArtLoader()
