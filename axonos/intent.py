# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""The RFC-0006 intent-observation wire format.

:class:`IntentObservation` is the 32-byte record the kernel emits through the
capability gate. This module is a pure-Python, byte-for-byte port of the Rust
``axonos-sdk`` ``intent`` module, stable for ``KERNEL_ABI_VERSION == 1``.

Layout (little-endian, no padding - matches ``#[repr(C, align(8))]``)::

    off  size  field
      0     8  timestamp_us   (u64)  - microseconds since session start
      8     2  kind_tag       (u16)  - 1=Direction, 2=Load, 3=Quality
     10     2  quality_raw    (u16)  - Q0.16 confidence
     12     4  payload        ([u8;4]) - payload[0] is the kind discriminant
     16     8  session_id     (u64)
     24     8  attestation    ([u8;8]) - truncated HMAC-SHA256
                                          total = 32 bytes
"""

import struct
from enum import IntEnum
from typing import Optional, Union

from .q016 import Q016_ONE, to_float
from .time import MonotonicTimestamp

#: Size of the on-wire record, in bytes.
OBSERVATION_SIZE: int = 32

#: ``struct`` format: little-endian, naturally packed to the RFC-0006 layout.
_WIRE = "<QHH4sQ8s"
assert struct.calcsize(_WIRE) == OBSERVATION_SIZE


class _KindTag:
    DIRECTION = 0x0001
    LOAD = 0x0002
    QUALITY = 0x0003


class Direction(IntEnum):
    """Directional intent for cursor / menu control (Navigation capability)."""

    Up = 0
    Right = 1
    Down = 2
    Left = 3
    Neutral = 4


class Load(IntEnum):
    """Cognitive-load advisory level (WorkloadAdvisory capability)."""

    Low = 0
    Moderate = 1
    High = 2


class Quality(IntEnum):
    """Signal-quality level (SessionQuality capability)."""

    High = 0
    Moderate = 1
    Low = 2
    NoSignal = 3


def _safe(enum_cls, value: int):
    try:
        return enum_cls(value)
    except ValueError:
        return None


class IntentObservation:
    """A single 32-byte intent observation."""

    __slots__ = (
        "timestamp_us",
        "kind_tag",
        "quality_raw",
        "payload",
        "session_id",
        "attestation",
    )

    def __init__(
        self,
        timestamp_us: int,
        kind_tag: int,
        quality_raw: int,
        payload: bytes,
        session_id: int,
        attestation: bytes,
    ) -> None:
        if not 0 <= timestamp_us <= (1 << 64) - 1:
            raise ValueError("timestamp_us out of u64 range")
        if not 0 <= kind_tag <= 0xFFFF:
            raise ValueError("kind_tag out of u16 range")
        if not 0 <= quality_raw <= Q016_ONE:
            raise ValueError(f"quality_raw out of Q0.16 range [0, {Q016_ONE}]")
        if not 0 <= session_id <= (1 << 64) - 1:
            raise ValueError("session_id out of u64 range")
        payload = bytes(payload)
        attestation = bytes(attestation)
        if len(payload) != 4:
            raise ValueError("payload must be 4 bytes")
        if len(attestation) != 8:
            raise ValueError("attestation must be 8 bytes")
        self.timestamp_us = int(timestamp_us)
        self.kind_tag = int(kind_tag)
        self.quality_raw = int(quality_raw)
        self.payload = payload
        self.session_id = int(session_id)
        self.attestation = attestation

    # -- constructors -----------------------------------------------------

    @classmethod
    def direction(
        cls,
        timestamp: MonotonicTimestamp,
        direction: Direction,
        confidence_raw: int,
        session_id: int,
        attestation: bytes,
    ) -> "IntentObservation":
        return cls(
            timestamp.as_micros(),
            _KindTag.DIRECTION,
            confidence_raw,
            bytes([int(direction), 0, 0, 0]),
            session_id,
            attestation,
        )

    @classmethod
    def load(
        cls,
        timestamp: MonotonicTimestamp,
        load: Load,
        confidence_raw: int,
        session_id: int,
        attestation: bytes,
    ) -> "IntentObservation":
        return cls(
            timestamp.as_micros(),
            _KindTag.LOAD,
            confidence_raw,
            bytes([int(load), 0, 0, 0]),
            session_id,
            attestation,
        )

    @classmethod
    def quality(
        cls,
        timestamp: MonotonicTimestamp,
        quality: Quality,
        session_id: int,
        attestation: bytes,
    ) -> "IntentObservation":
        # Quality observations always carry full confidence (u16::MAX),
        # matching the Rust ``new_quality`` constructor.
        return cls(
            timestamp.as_micros(),
            _KindTag.QUALITY,
            Q016_ONE,
            bytes([int(quality), 0, 0, 0]),
            session_id,
            attestation,
        )

    # -- codec ------------------------------------------------------------

    def encode(self) -> bytes:
        """Encode to the 32-byte RFC-0006 wire record (little-endian)."""
        return struct.pack(
            _WIRE,
            self.timestamp_us,
            self.kind_tag,
            self.quality_raw,
            self.payload,
            self.session_id,
            self.attestation,
        )

    @classmethod
    def decode(cls, data: bytes) -> "IntentObservation":
        """Decode a 32-byte RFC-0006 wire record."""
        if len(data) != OBSERVATION_SIZE:
            raise ValueError(
                f"observation must be {OBSERVATION_SIZE} bytes, got {len(data)}"
            )
        ts, kind_tag, quality_raw, payload, session_id, attestation = struct.unpack(
            _WIRE, data
        )
        return cls(ts, kind_tag, quality_raw, payload, session_id, attestation)

    # -- accessors --------------------------------------------------------

    def timestamp(self) -> MonotonicTimestamp:
        return MonotonicTimestamp(self.timestamp_us)

    @property
    def confidence_raw(self) -> int:
        """Q0.16 confidence as the raw ``u16``."""
        return self.quality_raw

    @property
    def confidence(self) -> float:
        """Q0.16 confidence as a float in ``[0.0, 1.0]``."""
        return to_float(self.quality_raw)

    @property
    def category(self) -> str:
        """``"direction"`` / ``"load"`` / ``"quality"`` / ``"unknown"``."""
        return {
            _KindTag.DIRECTION: "direction",
            _KindTag.LOAD: "load",
            _KindTag.QUALITY: "quality",
        }.get(self.kind_tag, "unknown")

    @property
    def kind(self) -> Optional[Union[Direction, Load, Quality]]:
        """Typed kind value, or ``None`` for an unknown / malformed record."""
        if self.kind_tag == _KindTag.DIRECTION:
            return _safe(Direction, self.payload[0])
        if self.kind_tag == _KindTag.LOAD:
            return _safe(Load, self.payload[0])
        if self.kind_tag == _KindTag.QUALITY:
            return _safe(Quality, self.payload[0])
        return None

    def capability(self):
        """The :class:`~axonos.capability.Capability` that gates this kind.

        Direction -> Navigation, Load -> WorkloadAdvisory,
        Quality -> SessionQuality. ``None`` for unknown kinds.
        """
        from .capability import Capability

        return {
            _KindTag.DIRECTION: Capability.Navigation,
            _KindTag.LOAD: Capability.WorkloadAdvisory,
            _KindTag.QUALITY: Capability.SessionQuality,
        }.get(self.kind_tag)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IntentObservation):
            return NotImplemented
        return self.encode() == other.encode()

    def __hash__(self) -> int:
        return hash(self.encode())

    def __repr__(self) -> str:
        return (
            f"IntentObservation(kind={self.kind!r}, "
            f"confidence={self.confidence:.4f}, "
            f"session_id={self.session_id:#018x}, "
            f"t={self.timestamp_us}us)"
        )
