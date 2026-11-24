"""Next-song prediction for mcmusic using a Minimum Description Length model.

Nothing here touches the running server yet; it is a standalone, standard-library
only module that can be wired in later.

Public API:
    encode.pack_state / encode.unpack_state  -- build and read the 44-bit state
    mdl.NextSongMDL                          -- the learning model
"""

from .encoding import (
    STATE_BITS,
    SONG_BITS,
    USER_BITS,
    USER_COUNT,
    SONG_MIN,
    HISTORY_SLOTS,
    QUEUE_SLOTS,
    STATUS_BITS,
    STATUS_FLAGS,
    pack_state,
    unpack_state,
    encode_user,
    state_to_bits,
)
from .mdl import NextSongMDL

__all__ = [
    "STATE_BITS",
    "SONG_BITS",
    "USER_BITS",
    "USER_COUNT",
    "SONG_MIN",
    "HISTORY_SLOTS",
    "QUEUE_SLOTS",
    "STATUS_BITS",
    "STATUS_FLAGS",
    "pack_state",
    "unpack_state",
    "encode_user",
    "state_to_bits",
    "NextSongMDL",
]
