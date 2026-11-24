"""Server-side bridge for the standalone `algo/` next-song MDL model.

For now this module is **learning only**. It turns each recorded play into one
observation and persists the model under DATA_DIR. Nothing here is consulted by
the radio endpoint, queue extension, shuffle, or any "what plays next" choice.
The only prediction made is an internal one used to score the click (exact hit
/ same artist / wrong), which is how the model learns.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

from config import DATA_DIR

from algo import STATUS_FLAGS, USER_COUNT, NextSongMDL, pack_state

MODEL_PATH = os.path.join(DATA_DIR, "next_song_mdl.json")
_LOCK = threading.RLock()
_MODEL: NextSongMDL | None = None


def _load() -> NextSongMDL:
    """Load the persisted model, keeping a corrupt file for inspection."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        if os.path.exists(MODEL_PATH):
            try:
                _MODEL = NextSongMDL.load_json(MODEL_PATH)
                return _MODEL
            except (OSError, ValueError, KeyError, TypeError) as exc:
                backup = MODEL_PATH + ".corrupt"
                try:
                    os.replace(MODEL_PATH, backup)
                except OSError:
                    pass
                # A bad snapshot must not stop the server; start learning fresh.
                print(f"next_song_model: ignoring unreadable model ({exc})")
        _MODEL = NextSongMDL()
        _save(_MODEL)
        return _MODEL


def _save(model: NextSongMDL) -> None:
    """Atomically replace the model snapshot so a crash never truncates it."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = MODEL_PATH + ".tmp"
    model.save_json(tmp)
    os.replace(tmp, MODEL_PATH)


def _occupancy(items: list[int], count: int) -> tuple[int, ...]:
    return tuple(1 if i < len(items) else 0 for i in range(count))


def _queue_context(c: Any, uid: int, previous_track: int) -> tuple[int, ...]:
    """Five-forward occupancy around the track that was playing before the click."""
    row = c.execute("select queue from playback where user_id=?", (uid,)).fetchone()
    if not row or not row["queue"]:
        return (0,) * 5
    try:
        queue = json.loads(row["queue"])
    except (TypeError, ValueError):
        return (0,) * 5
    if not isinstance(queue, list):
        return (0,) * 5
    ids: list[int] = []
    for value in queue[:200]:
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            continue
    if previous_track not in ids:
        return (0,) * 5
    start = ids.index(previous_track) + 1
    return _occupancy(ids[start:start + 5], 5)


def _status(previous_track: int, next_track: int, extra: int) -> int:
    flags = extra & 15
    if previous_track == next_track:
        flags |= STATUS_FLAGS["LOOP"]
    return flags


def observe_play(c: Any, uid: int, next_track: int, play_id: int, status: int = 0) -> bool:
    """Learn from one recorded play.

    Returns True when an observation was made. The first play for a user has no
    preceding song, so it cannot form a state and is skipped.
    """
    if not 0 < next_track < (1 << 24):
        return False
    history = c.execute(
        "select track_id from plays where user_id=? and id<? order by id desc limit 5",
        (uid, play_id),
    ).fetchall()
    if not history:
        return False
    previous = int(history[0]["track_id"] or 0)
    if not 0 < previous < (1 << 24):
        return False

    with _LOCK:
        model = _load()
        state = pack_state(
            uid % USER_COUNT,
            previous,
            _occupancy(history, 5),
            _queue_context(c, uid, previous),
            _status(previous, next_track, status),
        )
        meta = c.execute(
            "select id, artist, album from tracks where id in (?,?)",
            (previous, next_track),
        ).fetchall()
        by_id = {int(r["id"]): (r["artist"], r["album"]) for r in meta}
        previous_meta = by_id.get(previous, (None, None))
        next_meta = by_id.get(next_track, (None, None))

        # The prediction is only the learning signal. It is never returned to a
        # client and never changes playback, radio, shuffle or queue behavior.
        predicted = model.predict(state)
        model.observe(
            state,
            next_track,
            predicted=predicted,
            artist=next_meta[0] or previous_meta[0],
            album=next_meta[1] or previous_meta[1],
        )
        _save(model)
    return True


def algo_status() -> dict:
    """Read-only snapshot for the admin endpoint."""
    with _LOCK:
        model = _load()
        summary = model.summary()
    return {
        **summary,
        "learning_only": True,
        "model_file": "data/next_song_mdl.json",
        "used_for_choices": False,
    }
