# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""Monotonic, session-relative timestamps.

A :class:`MonotonicTimestamp` is microseconds since the start of a session,
guaranteed monotonic within that session. No wall-clock time is exposed -
that is a privacy boundary in AxonOS, not an oversight. Arithmetic is
*saturating*: it never overflows and never raises, matching the Rust
``MonotonicTimestamp``.
"""

#: ``u64::MAX`` - the saturation ceiling for microsecond arithmetic.
U64_MAX: int = (1 << 64) - 1


class MonotonicTimestamp:
    """Microseconds since session start. Saturating, never-panicking."""

    __slots__ = ("_micros",)

    def __init__(self, micros: int) -> None:
        if not 0 <= micros <= U64_MAX:
            raise ValueError(f"timestamp out of u64 range: {micros}")
        self._micros = int(micros)

    @classmethod
    def from_micros(cls, micros: int) -> "MonotonicTimestamp":
        """Construct from a microsecond count."""
        return cls(micros)

    def as_micros(self) -> int:
        """Microseconds since session start."""
        return self._micros

    def saturating_add_micros(self, delta: int) -> "MonotonicTimestamp":
        """Add ``delta`` microseconds, saturating at ``u64::MAX``."""
        if delta < 0:
            raise ValueError("delta must be non-negative")
        return MonotonicTimestamp(min(self._micros + delta, U64_MAX))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MonotonicTimestamp) and other._micros == self._micros

    def __lt__(self, other: "MonotonicTimestamp") -> bool:
        return self._micros < other._micros

    def __hash__(self) -> int:
        return hash(self._micros)

    def __repr__(self) -> str:
        return f"MonotonicTimestamp({self._micros} us)"
