# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""AxonOS SDK for Python.

A pure-Python, dependency-free port of the AxonOS application boundary: the
RFC-0006 intent-observation wire format, the capability model, and the
deterministic Q0.16 / monotonic-time primitives. It is byte-compatible with
the reference Rust ``axonos-sdk`` for ``KERNEL_ABI_VERSION == 1``.

Scope: this package speaks the wire format and models the capability gate so
that host-side and Python application code can read kernel observations and
declare manifests. It does **not** itself enforce capabilities or verify
attestations - the kernel does that. Attestation verification is on the
roadmap and is intentionally not stubbed as if present.
"""

from .capability import CAPABILITY_COUNT, Capability, CapabilitySet
from .intent import (
    OBSERVATION_SIZE,
    Direction,
    IntentObservation,
    Load,
    Quality,
)
from .manifest import Manifest, ManifestError, ProhibitedCapability
from .q016 import Q016_ONE, to_float, to_raw
from .time import MonotonicTimestamp

#: Kernel ABI version this SDK targets.
KERNEL_ABI_VERSION = 1

__version__ = "0.1.0"

__all__ = [
    "KERNEL_ABI_VERSION",
    "__version__",
    # intent
    "IntentObservation",
    "OBSERVATION_SIZE",
    "Direction",
    "Load",
    "Quality",
    # capability / manifest
    "Capability",
    "CapabilitySet",
    "CAPABILITY_COUNT",
    "Manifest",
    "ManifestError",
    "ProhibitedCapability",
    # primitives
    "MonotonicTimestamp",
    "Q016_ONE",
    "to_float",
    "to_raw",
]
