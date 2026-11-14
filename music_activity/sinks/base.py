"""Sink contract plus a reconnect helper shared by the two sinks."""
from __future__ import annotations

import threading
from typing import Protocol

from music_activity.state import PlayerState


class Sink(Protocol):
    def connect(self) -> None: ...
    def publish(self, state: PlayerState) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


class Backoff:
    """Monotonic exponential backoff with a cap, reset on success."""

    def __init__(self, base: float = 1.0, cap: float = 30.0) -> None:
        self.base = base
        self.cap = cap
        self.value = base

    def reset(self) -> None:
        self.value = self.base

    def next(self) -> float:
        wait = self.value
        self.value = min(self.value * 2, self.cap)
        return wait


def safe_call(log, name: str, fn, *args) -> None:
    """A dead sink must never take the player (or another sink) down."""
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001 - sink autonomy is the point
        log(f"{name}: {exc}")


def daemon_thread(name: str, target) -> threading.Thread:
    t = threading.Thread(target=target, name=name, daemon=True)
    t.start()
    return t
