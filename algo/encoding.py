"""The 44-bit wire format used by the next-song MDL model.

Bit string layout (bit 0 below is the most significant bit of the integer)::

    0 .. 5    user id, plain 6-bit unsigned binary counter
              user 0 -> 000000 , user 1 -> 000001 , ... user 63 -> 111111
    6 .. 29   current song / sid, 24-bit unsigned big endian
              0 = null / no song; real songs start at 1
    30 .. 34  played-before window, 5 bits (5 back), 1 = slot occupied
    35 .. 39  queue window, 5 bits (5 forward), 1 = slot occupied
    40 .. 43  status, 4 bits (see STATUS_FLAGS)

The window bits are occupancy flags, not song ids: the spec only says "ones for
all in the queue and played before", so each slot contributes a single 1 or 0.
The 5 history bits are ordered oldest -> newest; the 5 queue bits are ordered
now -> furthest ahead.
"""

from __future__ import annotations

USER_BITS = 6
SONG_BITS = 24
HISTORY_SLOTS = 5
QUEUE_SLOTS = 5
STATUS_BITS = 4
STATE_BITS = USER_BITS + SONG_BITS + HISTORY_SLOTS + QUEUE_SLOTS + STATUS_BITS

USER_COUNT = 1 << USER_BITS
SONG_COUNT = 1 << SONG_BITS
SONG_MIN = 1  # 0 means null / no song

# bit positions inside the 44-character bit string
_USER = (0, USER_BITS)
_SONG = (USER_BITS, USER_BITS + SONG_BITS)
_HIST = (_SONG[1], _SONG[1] + HISTORY_SLOTS)
_QUEUE = (_HIST[1], _HIST[1] + QUEUE_SLOTS)
_STATUS = (_QUEUE[1], _QUEUE[1] + STATUS_BITS)

STATUS_FLAGS = {
    "LOOP": 1 << 0,          # looping playback
    "FIRST_CLICKED": 1 << 1,  # first click of the session
    "REPEAT_ONE": 1 << 2,     # repeat the current song
    "SHUFFLE": 1 << 3,        # shuffled queue
}


def _slice_mask(start: int, end: int) -> int:
    """Mask selecting bit-string positions ``[start, end)`` in the packed int."""
    width = end - start
    shift = STATE_BITS - end
    return ((1 << width) - 1) << shift


# integer masks over the packed state, for the MDL expert ladder
ALL_MASK = (1 << STATE_BITS) - 1
USER_MASK = _slice_mask(*_USER)
SONG_MASK = _slice_mask(*_SONG)
HISTORY_MASK = _slice_mask(*_HIST)
QUEUE_MASK = _slice_mask(*_QUEUE)
STATUS_MASK = _slice_mask(*_STATUS)
CONTEXT_MASK = USER_MASK | HISTORY_MASK | QUEUE_MASK | STATUS_MASK


def encode_user(user: int) -> str:
    """Return the 6-bit plain binary code: user 0 = ``000000``, user 1 = ``000001``."""
    return _binary(user, USER_BITS)


def _binary(value: int, width: int, minimum: int = 0) -> str:
    if not minimum <= value < (1 << width):
        raise ValueError(f"value must be {minimum}..{(1 << width) - 1}, got {value}")
    return format(value, f"0{width}b")


def _occupancy(bits: tuple[int, ...] | list[int], name: str) -> str:
    if len(bits) != 5:
        raise ValueError(f"{name} needs exactly 5 slots, got {len(bits)}")
    out = []
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError(f"{name} slots must be 0 or 1, got {bit}")
        out.append(str(bit))
    return "".join(out)


def pack_state(
    user: int,
    song: int,
    played_before: tuple[int, ...] | list[int] = (0,) * HISTORY_SLOTS,
    in_queue: tuple[int, ...] | list[int] = (0,) * QUEUE_SLOTS,
    status: int = 0,
) -> int:
    """Pack one observation into the 44-bit integer state.

    ``song`` must be a real song id (>= 1); 0 is the null/no-song sentinel.
    ``played_before`` is 5 back (oldest first), ``in_queue`` is 5 forward
    (nearest first), both as 0/1 occupancy flags.
    """
    bits = (
        encode_user(user)
        + _binary(song, SONG_BITS, minimum=SONG_MIN)
        + _occupancy(played_before, "played_before")
        + _occupancy(in_queue, "in_queue")
        + _binary(status, STATUS_BITS)
    )
    return int(bits, 2)


def state_to_bits(state: int) -> str:
    """Render a packed state as its 44-character bit string."""
    if not 0 <= state <= ALL_MASK:
        raise ValueError(f"state must be a {STATE_BITS}-bit unsigned integer")
    return format(state, f"0{STATE_BITS}b")


def unpack_state(state: int) -> dict:
    """Decode a packed state into named fields."""
    bits = state_to_bits(state)
    return {
        "user": int(bits[_USER[0]:_USER[1]], 2),
        "song": int(bits[_SONG[0]:_SONG[1]], 2),
        "played_before": tuple(int(b) for b in bits[_HIST[0]:_HIST[1]]),
        "in_queue": tuple(int(b) for b in bits[_QUEUE[0]:_QUEUE[1]]),
        "status": int(bits[_STATUS[0]:_STATUS[1]], 2),
    }


def mask_key(state: int, mask: int) -> int:
    """Project a full state onto one expert's context mask."""
    return state & mask
