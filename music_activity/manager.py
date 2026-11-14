"""Event intake, 500 ms debounce, fan-out to independent sinks."""
from __future__ import annotations

import threading
import time
import traceback
from typing import Callable

from music_activity.sinks.base import Sink
from music_activity.state import PlayerState


class Manager:
    """`on_event` may be called from any thread (Flask request, watcher)."""

    def __init__(
        self,
        sinks: list[Sink],
        debounce: float = 0.5,
        log: Callable[[str], None] = print,
    ) -> None:
        self.sinks = sinks
        self.debounce = debounce
        self.log = log
        self._cond = threading.Condition()
        self._pending: PlayerState | None = None
        self._closed = False
        self._thread = threading.Thread(target=self._loop, name="music-activity", daemon=True)
        self._thread.start()

    def on_event(self, state: PlayerState) -> None:
        with self._cond:
            if self._closed:
                return
            self._pending = state
            self._cond.notify()

    def _loop(self) -> None:
        while True:
            with self._cond:
                while self._pending is None and not self._closed:
                    self._cond.wait()
                if self._closed:
                    return
            # Coalesce bursts: play -> seek -> loop arrives as one push.
            if self.debounce:
                time.sleep(self.debounce)
            with self._cond:
                state, self._pending = self._pending, None
                if state is None:
                    continue
            self._dispatch(state)

    def _dispatch(self, state: PlayerState) -> None:
        for sink in self.sinks:
            name = sink.__class__.__name__
            try:
                if state.track is None:
                    sink.clear()
                else:
                    sink.publish(state)
            except Exception:  # noqa: BLE001
                self.log(f"{name} failed:\n{traceback.format_exc(limit=2)}")

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify()
        for sink in self.sinks:
            try:
                sink.close()
            except Exception:  # noqa: BLE001
                pass
