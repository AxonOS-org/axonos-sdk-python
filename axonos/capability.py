# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""Capability classes and the capability-set bitfield.

A capability is an unforgeable token naming a permitted operation. An
application declares the classes it needs in a :class:`~axonos.manifest.Manifest`;
the kernel - not the client - enforces it. The wire encoding is a
little-endian ``u32`` bitfield, identical to the Rust ``CapabilitySet``::

    bit 0: Navigation        bit 2: SessionQuality
    bit 1: WorkloadAdvisory  bit 3: ArtifactEvents
    bits 4..31: reserved (must be zero)
"""

import struct
from enum import IntEnum

#: Total number of capability variants (bitfield-width invariant).
CAPABILITY_COUNT: int = 4

#: Mask of the valid (non-reserved) bits: bits 0..3.
VALID_MASK: int = (1 << CAPABILITY_COUNT) - 1  # 0xF


class Capability(IntEnum):
    """A single capability class. The value is its wire ``u8`` discriminant
    and its bit position in :class:`CapabilitySet`."""

    Navigation = 0
    WorkloadAdvisory = 1
    SessionQuality = 2
    ArtifactEvents = 3

    def bit(self) -> int:
        """Bit position of this capability in the :class:`CapabilitySet`."""
        return 1 << int(self)

    def kernel_rate_limit_hz(self) -> int:
        """Kernel-enforced maximum event rate for this class, in Hz."""
        return _RATE_LIMIT_HZ[self]

    @classmethod
    def from_u8(cls, value: int) -> "Capability | None":
        """Decode a wire discriminant, or ``None`` if unknown."""
        try:
            return cls(value)
        except ValueError:
            return None


_RATE_LIMIT_HZ = {
    Capability.Navigation: 50,
    Capability.WorkloadAdvisory: 1,
    Capability.SessionQuality: 2,
    Capability.ArtifactEvents: 10,
}


class CapabilitySet:
    """A zero-allocation ``u32`` bitfield of :class:`Capability` values."""

    __slots__ = ("_bits",)

    def __init__(self, bits: int = 0) -> None:
        self._bits = int(bits) & 0xFFFFFFFF

    @classmethod
    def singleton(cls, capability: Capability) -> "CapabilitySet":
        """A set containing exactly one capability."""
        return cls(capability.bit())

    @classmethod
    def all(cls) -> "CapabilitySet":
        """The full catalogue - every defined capability."""
        bits = 0
        for c in Capability:
            bits |= c.bit()
        return cls(bits)

    def with_(self, capability: Capability) -> "CapabilitySet":
        """Return a new set with ``capability`` added (immutable style)."""
        return CapabilitySet(self._bits | capability.bit())

    def contains(self, capability: Capability) -> bool:
        """True if ``capability`` is present."""
        return (self._bits & capability.bit()) != 0

    def as_u32(self) -> int:
        """The raw bitfield value."""
        return self._bits

    def has_reserved_bits(self) -> bool:
        """True if any reserved bit (4..31) is set - an invalid wire value."""
        return (self._bits & ~VALID_MASK) != 0

    def __iter__(self):
        for c in Capability:
            if self.contains(c):
                yield c

    def __len__(self) -> int:
        return bin(self._bits & VALID_MASK).count("1")

    def is_empty(self) -> bool:
        return self._bits == 0

    def encode(self) -> bytes:
        """Encode as a little-endian ``u32`` (4 bytes)."""
        return struct.pack("<I", self._bits)

    @classmethod
    def decode(cls, data: bytes) -> "CapabilitySet":
        """Decode from a little-endian ``u32`` (4 bytes)."""
        if len(data) != 4:
            raise ValueError(f"CapabilitySet wire length must be 4, got {len(data)}")
        (bits,) = struct.unpack("<I", data)
        return cls(bits)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CapabilitySet) and other._bits == self._bits

    def __hash__(self) -> int:
        return hash(self._bits)

    def __repr__(self) -> str:
        names = ", ".join(c.name for c in self)
        return f"CapabilitySet({{{names}}})"
