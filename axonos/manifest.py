# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""Application capability manifests.

A :class:`Manifest` is an application's declared set of required capability
classes. The kernel rejects a manifest that references anything outside the
catalogue (any reserved bit set), so a policy mismatch is caught at
construction rather than at runtime - mirroring the Rust ``Manifest``.
"""

from .capability import Capability, CapabilitySet


class ManifestError(Exception):
    """Base class for manifest construction failures."""


class ProhibitedCapability(ManifestError):
    """A manifest referenced a reserved / out-of-catalogue capability bit."""


class Manifest:
    """An immutable, validated set of required capabilities."""

    __slots__ = ("_capabilities",)

    def __init__(self, capabilities: CapabilitySet) -> None:
        if capabilities.has_reserved_bits():
            raise ProhibitedCapability(
                f"manifest sets reserved bits: {capabilities.as_u32():#010x}"
            )
        self._capabilities = capabilities

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    def contains(self, capability: Capability) -> bool:
        """True if the application declared ``capability``."""
        return self._capabilities.contains(capability)

    def encode(self) -> bytes:
        """Encode the manifest as a little-endian ``u32`` bitfield."""
        return self._capabilities.encode()

    @classmethod
    def decode(cls, data: bytes) -> "Manifest":
        """Decode and validate a manifest from its 4-byte wire form."""
        return cls(CapabilitySet.decode(data))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Manifest)
            and other._capabilities == self._capabilities
        )

    def __repr__(self) -> str:
        return f"Manifest({self._capabilities!r})"
