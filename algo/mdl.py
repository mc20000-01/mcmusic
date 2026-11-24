"""Minimum Description Length next-song model.

The model is a small hierarchy of predictors ("experts"). Each expert sees the
same 44-bit state but at a different specificity:

    global          no context at all
    user            which of the 64 possible users
    user+context    user + 5-back/5-forward occupancy + status
    user+song       user + current song
    full            everything

Every expert is a Dirichlet process with a uniform base over the 2**24 possible
songs, so a never-before-seen song costs ~24 bits to describe and a familiar one
gets cheaper each time it is observed. An expert's total cost is its sequential
codelength plus the MDL cost of the contexts it has memorised. Predictions mix
the experts with weights proportional to 2**-(cost), which is context-tree
weighting applied to this ladder; "correct" clicks also nudge each expert's
trust score so a level that keeps being right gets heard more.

Learning is online: one ``observe`` call per click, no training phase needed.
"""

from __future__ import annotations

import json
import math
import os

from . import encoding as enc

SONG_COUNT = enc.SONG_COUNT
LOG2_SONG_COUNT = enc.SONG_BITS

# expert ladder: (name, mask over the packed 44-bit state)
EXPERT_SPECS = (
    ("global", 0),
    ("user", enc.USER_MASK),
    ("user+context", enc.CONTEXT_MASK),
    ("user+song", enc.USER_MASK | enc.SONG_MASK),
    ("full", enc.ALL_MASK),
)


class _Expert:
    """One context granularity: a set of sparse categorical distributions."""

    __slots__ = ("name", "mask", "counts", "totals", "codelength", "trust")

    def __init__(self, name: str, mask: int) -> None:
        self.name = name
        self.mask = mask
        self.counts: dict[int, dict[int, int]] = {}
        self.totals: dict[int, int] = {}
        self.codelength = 0.0
        self.trust = 0.0

    def key(self, state: int) -> int:
        return state & self.mask

    def prob(self, state: int, song: int, alpha: float) -> float:
        """Dirichlet-process predictive probability, before observing ``song``."""
        key = self.key(state)
        bucket = self.counts.get(key)
        n = bucket.get(song, 0) if bucket else 0
        total = self.totals.get(key, 0)
        return (n + alpha / SONG_COUNT) / (total + alpha)

    def top(self, state: int) -> int | None:
        """This expert's own most likely song for the state, or None if empty."""
        bucket = self.counts.get(self.key(state))
        if not bucket:
            return None
        return max(sorted(bucket), key=lambda song: bucket[song])

    def update(self, state: int, song: int, alpha: float, length_decay: float) -> float:
        """Add one observation; return the codelength in bits of that song."""
        key = self.key(state)
        p = self.prob(state, song, alpha)
        bits = -math.log2(p)
        self.codelength = length_decay * self.codelength + bits
        if key not in self.counts:
            self.counts[key] = {}
        self.counts[key][song] = self.counts[key].get(song, 0) + 1
        self.totals[key] = self.totals.get(key, 0) + 1
        return bits

    def candidates(self, state: int) -> set[int]:
        return set(self.counts.get(self.key(state), ()))

    def model_cost(self, log2_experts: float, active_key_cost: float) -> float:
        """MDL price of choosing this expert and its memorised contexts."""
        return log2_experts + active_key_cost * math.log2(1 + len(self.counts))


class NextSongMDL:
    """Online next-song predictor with per-user, preference-learning statistics.

    Parameters
    ----------
    alpha:
        Concentration of the uniform-base Dirichlet process. Higher values make
        new songs cheaper to "try" and slow down specialisation.
    trust_beta:
        Bits added to an expert's weight per unit of recent click reward.
    trust_decay:
        Forgetting factor applied to each expert's trust score per click.
    active_key_cost:
        Bits charged per memorised context (log growth), discouraging the more
        specific experts from splitting into sparse, over-fit buckets.
    length_decay:
        Forgetting factor on each expert's codelength. 1.0 is plain cumulative
        MDL; below 1 gives a discounted code so the model can re-adapt when a
        user's preferences change (0.999 has a half-life of ~700 clicks).
    """

    VERSION = 1

    def __init__(
        self,
        alpha: float = 1.0,
        trust_beta: float = 0.75,
        trust_decay: float = 0.98,
        active_key_cost: float = 0.5,
        trust_limit: float = 16.0,
        length_decay: float = 0.999,
    ) -> None:
        if alpha <= 0 or not 0.0 <= trust_decay <= 1.0 or not 0.0 < length_decay <= 1.0:
            raise ValueError("alpha must be > 0, decays in 0..1 (length_decay > 0)")
        self.alpha = float(alpha)
        self.trust_beta = float(trust_beta)
        self.trust_decay = float(trust_decay)
        self.active_key_cost = float(active_key_cost)
        self.trust_limit = float(trust_limit)
        self.length_decay = float(length_decay)
        self._log2_experts = math.log2(len(EXPERT_SPECS))
        self.experts = [_Expert(name, mask) for name, mask in EXPERT_SPECS]
        # song id -> (artist, album); optional, only used to score "meh" clicks
        self.metadata: dict[int, tuple[str | None, str | None]] = {}
        self.stats = {
            "observations": 0,
            "reward_sum": 0.0,
            "correct": 0,
            "meh": 0,
            "wrong": 0,
        }

    # ------------------------------------------------------------------ predict

    def predict(self, state: int, candidates: set[int] | None = None) -> int:
        """Return the predicted next song id as a 24-bit integer.

        With no data at all there is nothing to prefer, so ``0`` (null / no
        song) is returned. Pass ``candidates`` to restrict the choice, e.g. to
        the songs currently available in the library. Song ``0`` is never
        returned as a pick.
        """
        ranked = self.predict_ranked(state, k=1, candidates=candidates)
        return ranked[0][0] if ranked else 0

    def predict_ranked(
        self, state: int, k: int = 5, candidates: set[int] | None = None
    ) -> list[tuple[int, float]]:
        """Rank candidate songs by blended MDL probability (highest first)."""
        if k <= 0:
            return []
        pool = self._candidate_set(state, candidates)
        if not pool:
            return []
        weights = self._weights(state)
        scored: list[tuple[int, float]] = []
        for song in pool:
            p = sum(
                w * expert.prob(state, song, self.alpha)
                for expert, w in zip(self.experts, weights)
            )
            scored.append((song, p))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[:k]

    def _candidate_set(self, state: int, override: set[int] | None) -> set[int]:
        if override is not None:
            return {s for s in override if enc.SONG_MIN <= s < SONG_COUNT}
        pool: set[int] = set()
        for expert in self.experts:
            pool |= expert.candidates(state)
        return pool

    def _weights(self, state: int) -> list[float]:
        log_weights = [
            -expert.codelength
            - expert.model_cost(self._log2_experts, self.active_key_cost)
            + self.trust_beta * expert.trust
            for expert in self.experts
        ]
        peak = max(log_weights)
        raw = [2.0 ** (lw - peak) for lw in log_weights]
        total = sum(raw)
        return [r / total for r in raw]

    # ------------------------------------------------------------------ observe

    def observe(
        self,
        state: int,
        actual_next: int,
        predicted: int | None = None,
        reward: float | None = None,
        artist: str | None = None,
        album: str | None = None,
    ) -> float:
        """Learn from one click and return the reward for that click.

        ``reward`` is +1 for the exact predicted song, 0 for "meh" (same artist
        or album as the prediction), -1 for a different song. If it is omitted,
        the reward is derived from ``predicted`` (or this model's own prediction
        when that is omitted too). Artist/album metadata is only needed for the
        "meh" case; register it with ``set_metadata`` or pass it here.
        """
        if not 0 <= actual_next < SONG_COUNT:
            raise ValueError(f"song id must be 24-bit, got {actual_next}")
        # 0 is allowed here: a clickless event is a real observation, but it
        # never becomes a prediction candidate (see _candidate_set).
        if artist is not None or album is not None:
            self.set_song_metadata(actual_next, artist, album)
        if predicted is None:
            predicted = self.predict(state)
        if reward is None:
            reward = self.reward(predicted, actual_next)

        for expert in self.experts:
            own_pick = expert.top(state)  # prediction made before this click
            expert.update(state, actual_next, self.alpha, self.length_decay)
            if own_pick is None:
                own_reward = 0.0  # no opinion yet: neither credit nor blame
            else:
                own_reward = self.reward(own_pick, actual_next)
            expert.trust = max(
                -self.trust_limit,
                min(
                    self.trust_limit,
                    self.trust_decay * expert.trust + own_reward,
                ),
            )

        self.stats["observations"] += 1
        self.stats["reward_sum"] += float(reward)
        if reward > 0:
            self.stats["correct"] += 1
        elif reward == 0:
            self.stats["meh"] += 1
        else:
            self.stats["wrong"] += 1
        return float(reward)

    def reward(self, predicted: int, actual: int) -> float:
        """+1 exact hit, 0 for same artist/album, -1 otherwise."""
        if predicted == actual:
            return 1.0
        if self.same_artist_or_album(predicted, actual):
            return 0.0
        return -1.0

    def same_artist_or_album(self, a: int, b: int) -> bool:
        left = self.metadata.get(a)
        right = self.metadata.get(b)
        if not left or not right:
            return False
        return (
            (left[0] is not None and left[0] == right[0])
            or (left[1] is not None and left[1] == right[1])
        )

    def set_song_metadata(
        self, song: int, artist: str | None, album: str | None
    ) -> None:
        if not 0 <= song < SONG_COUNT:
            raise ValueError(f"song id must be 24-bit, got {song}")
        self.metadata[song] = (artist, album)

    def set_metadata(self, mapping: dict[int, tuple[str | None, str | None]]) -> None:
        """Bulk-register ``song id -> (artist, album)``."""
        for song, meta in mapping.items():
            self.set_song_metadata(song, meta[0], meta[1])

    # ------------------------------------------------------------------ io

    def summary(self) -> dict:
        """Read-only view of how the model is doing."""
        return {
            **self.stats,
            "experts": [
                {
                    "name": e.name,
                    "contexts": len(e.counts),
                    "codelength_bits": round(e.codelength, 3),
                    "trust": round(e.trust, 3),
                }
                for e in self.experts
            ],
        }

    def to_dict(self) -> dict:
        return {
            "version": self.VERSION,
            "alpha": self.alpha,
            "trust_beta": self.trust_beta,
            "trust_decay": self.trust_decay,
            "active_key_cost": self.active_key_cost,
            "trust_limit": self.trust_limit,
            "length_decay": self.length_decay,
            "experts": [
                {
                    "name": e.name,
                    "mask": e.mask,
                    "counts": {
                        str(key): {str(song): n for song, n in bucket.items()}
                        for key, bucket in e.counts.items()
                    },
                    "totals": {str(key): n for key, n in e.totals.items()},
                    "codelength": e.codelength,
                    "trust": e.trust,
                }
                for e in self.experts
            ],
            "metadata": {str(s): list(m) for s, m in self.metadata.items()},
            "stats": dict(self.stats),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NextSongMDL":
        if data.get("version") != cls.VERSION:
            raise ValueError(f"unsupported model version: {data.get('version')}")
        model = cls(
            alpha=data["alpha"],
            trust_beta=data["trust_beta"],
            trust_decay=data["trust_decay"],
            active_key_cost=data["active_key_cost"],
            trust_limit=data["trust_limit"],
            length_decay=data["length_decay"],
        )
        for expert, saved in zip(model.experts, data["experts"]):
            if expert.name != saved["name"]:
                raise ValueError("expert ladder does not match saved model")
            expert.counts = {
                int(key): {int(song): n for song, n in bucket.items()}
                for key, bucket in saved["counts"].items()
            }
            expert.totals = {int(key): n for key, n in saved["totals"].items()}
            expert.codelength = float(saved["codelength"])
            expert.trust = float(saved["trust"])
        model.metadata = {
            int(song): (meta[0], meta[1]) for song, meta in data["metadata"].items()
        }
        model.stats = dict(data["stats"])
        return model

    def save_json(self, path: str | os.PathLike) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, separators=(",", ":"))

    @classmethod
    def load_json(cls, path: str | os.PathLike) -> "NextSongMDL":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
