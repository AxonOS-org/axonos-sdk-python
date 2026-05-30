# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""Unsigned Q0.16 fixed-point, byte-identical to the Rust ``axonos-sdk``.

Confidence / score values are carried on the wire as a ``u16`` where::

    value_float = raw / 65535.0

so ``0`` is ``0.0`` and ``65535`` (``u16::MAX``) is ``1.0``. This eliminates
the cross-architecture floating-point non-determinism that a raw ``f32``
would introduce between the Cortex-M front-end and an x86_64 host.
"""

#: ``u16::MAX`` - the fixed-point representation of ``1.0``.
Q016_ONE: int = 65535


def to_float(raw: int) -> float:
    """Decode a Q0.16 ``raw`` value into a float in ``[0.0, 1.0]``.

    Matches the Rust ``IntentObservation::confidence_f32`` exactly.
    """
    if not 0 <= raw <= Q016_ONE:
        raise ValueError(f"Q0.16 raw out of range [0, {Q016_ONE}]: {raw}")
    return raw / Q016_ONE


def to_raw(value: float) -> int:
    """Encode a float in ``[0.0, 1.0]`` into a Q0.16 ``raw`` value.

    Values outside the range are clamped (never panics, mirroring the
    SDK's saturating philosophy). Rounds to nearest.
    """
    if value <= 0.0:
        return 0
    if value >= 1.0:
        return Q016_ONE
    return round(value * Q016_ONE)
