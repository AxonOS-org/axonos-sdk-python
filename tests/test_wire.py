# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""Wire-format and capability tests for the AxonOS Python SDK.

These check internal consistency *and* fidelity to the documented RFC-0006
layout. The cross-language vectors at the bottom are intended to be replayed
against the Rust ``axonos-sdk`` to confirm byte-for-byte equivalence.
"""

import struct
import unittest

from axonos import (
    Capability,
    CapabilitySet,
    Direction,
    IntentObservation,
    Load,
    Manifest,
    MonotonicTimestamp,
    ProhibitedCapability,
    Quality,
    to_float,
    to_raw,
)
from axonos.intent import OBSERVATION_SIZE


class TestWireLayout(unittest.TestCase):
    def test_size_is_32(self):
        obs = IntentObservation.direction(
            MonotonicTimestamp(0), Direction.Up, 0, 0, b"\x00" * 8
        )
        self.assertEqual(len(obs.encode()), 32)
        self.assertEqual(OBSERVATION_SIZE, 32)

    def test_field_offsets_little_endian(self):
        ts = MonotonicTimestamp(0x1122334455667788)
        obs = IntentObservation.direction(
            ts, Direction.Left, 0xABCD, 0xDEADBEEFCAFEF00D, bytes(range(8))
        )
        raw = obs.encode()
        # off 0..8  timestamp_us (u64 LE)
        self.assertEqual(struct.unpack_from("<Q", raw, 0)[0], 0x1122334455667788)
        # off 8..10 kind_tag (u16 LE) - Direction == 1
        self.assertEqual(struct.unpack_from("<H", raw, 8)[0], 1)
        # off 10..12 quality_raw (u16 LE)
        self.assertEqual(struct.unpack_from("<H", raw, 10)[0], 0xABCD)
        # off 12..16 payload; payload[0] == Direction discriminant (Left==3)
        self.assertEqual(raw[12], 3)
        self.assertEqual(raw[13:16], b"\x00\x00\x00")
        # off 16..24 session_id (u64 LE)
        self.assertEqual(struct.unpack_from("<Q", raw, 16)[0], 0xDEADBEEFCAFEF00D)
        # off 24..32 attestation (raw bytes, order preserved)
        self.assertEqual(raw[24:32], bytes(range(8)))

    def test_roundtrip_all_kinds(self):
        att = bytes([9, 8, 7, 6, 5, 4, 3, 2])
        cases = [
            IntentObservation.direction(
                MonotonicTimestamp(1000), Direction.Right, 49152, 0x55, att
            ),
            IntentObservation.load(
                MonotonicTimestamp(2000), Load.High, 32768, 0x66, att
            ),
            IntentObservation.quality(
                MonotonicTimestamp(3000), Quality.NoSignal, 0x77, att
            ),
        ]
        for obs in cases:
            again = IntentObservation.decode(obs.encode())
            self.assertEqual(again, obs)
            self.assertEqual(again.encode(), obs.encode())

    def test_bad_length_rejected(self):
        with self.assertRaises(ValueError):
            IntentObservation.decode(b"\x00" * 31)
        with self.assertRaises(ValueError):
            IntentObservation.decode(b"\x00" * 33)


class TestKindAndConfidence(unittest.TestCase):
    def test_quality_forces_full_confidence(self):
        obs = IntentObservation.quality(
            MonotonicTimestamp(0), Quality.High, 0, b"\x00" * 8
        )
        self.assertEqual(obs.confidence_raw, 65535)
        self.assertEqual(obs.confidence, 1.0)

    def test_kind_resolution(self):
        obs = IntentObservation.direction(
            MonotonicTimestamp(0), Direction.Down, 100, 0, b"\x00" * 8
        )
        self.assertEqual(obs.kind, Direction.Down)
        self.assertEqual(obs.category, "direction")

    def test_unknown_kind_tag_decodes_to_none(self):
        raw = bytearray(
            IntentObservation.direction(
                MonotonicTimestamp(0), Direction.Up, 0, 0, b"\x00" * 8
            ).encode()
        )
        struct.pack_into("<H", raw, 8, 0xFFFF)  # corrupt kind_tag
        obs = IntentObservation.decode(bytes(raw))
        self.assertIsNone(obs.kind)
        self.assertEqual(obs.category, "unknown")
        self.assertIsNone(obs.capability())

    def test_capability_mapping(self):
        d = IntentObservation.direction(
            MonotonicTimestamp(0), Direction.Up, 0, 0, b"\x00" * 8
        )
        load_obs = IntentObservation.load(
            MonotonicTimestamp(0), Load.Low, 0, 0, b"\x00" * 8
        )
        q = IntentObservation.quality(
            MonotonicTimestamp(0), Quality.High, 0, b"\x00" * 8
        )
        self.assertEqual(d.capability(), Capability.Navigation)
        self.assertEqual(load_obs.capability(), Capability.WorkloadAdvisory)
        self.assertEqual(q.capability(), Capability.SessionQuality)

    def test_q016_boundaries(self):
        self.assertEqual(to_float(0), 0.0)
        self.assertEqual(to_float(65535), 1.0)
        self.assertAlmostEqual(to_float(32768), 0.5000076, places=6)
        self.assertEqual(to_raw(0.0), 0)
        self.assertEqual(to_raw(1.0), 65535)
        self.assertEqual(to_raw(2.0), 65535)  # clamp
        self.assertEqual(to_raw(-1.0), 0)  # clamp


class TestTime(unittest.TestCase):
    def test_saturating_add(self):
        t = MonotonicTimestamp((1 << 64) - 10)
        self.assertEqual(t.saturating_add_micros(100).as_micros(), (1 << 64) - 1)

    def test_monotonic_compare(self):
        self.assertTrue(MonotonicTimestamp(1) < MonotonicTimestamp(2))


class TestCapability(unittest.TestCase):
    def test_bit_positions(self):
        self.assertEqual(Capability.Navigation.bit(), 1 << 0)
        self.assertEqual(Capability.WorkloadAdvisory.bit(), 1 << 1)
        self.assertEqual(Capability.SessionQuality.bit(), 1 << 2)
        self.assertEqual(Capability.ArtifactEvents.bit(), 1 << 3)

    def test_rate_limits(self):
        self.assertEqual(Capability.Navigation.kernel_rate_limit_hz(), 50)
        self.assertEqual(Capability.WorkloadAdvisory.kernel_rate_limit_hz(), 1)
        self.assertEqual(Capability.SessionQuality.kernel_rate_limit_hz(), 2)
        self.assertEqual(Capability.ArtifactEvents.kernel_rate_limit_hz(), 10)

    def test_set_build_and_contains(self):
        cs = CapabilitySet.singleton(Capability.Navigation).with_(
            Capability.SessionQuality
        )
        self.assertTrue(cs.contains(Capability.Navigation))
        self.assertTrue(cs.contains(Capability.SessionQuality))
        self.assertFalse(cs.contains(Capability.ArtifactEvents))
        self.assertEqual(len(cs), 2)

    def test_set_wire_little_endian_u32(self):
        cs = CapabilitySet.singleton(Capability.WorkloadAdvisory)  # bit 1 -> 0x02
        self.assertEqual(cs.encode(), b"\x02\x00\x00\x00")
        self.assertEqual(CapabilitySet.decode(cs.encode()), cs)

    def test_all_catalogue(self):
        allcaps = CapabilitySet.all()
        self.assertEqual(allcaps.as_u32(), 0b1111)
        self.assertFalse(allcaps.has_reserved_bits())

    def test_reserved_bits_detected(self):
        cs = CapabilitySet(1 << 5)
        self.assertTrue(cs.has_reserved_bits())


class TestManifest(unittest.TestCase):
    def test_contains(self):
        m = Manifest(CapabilitySet.singleton(Capability.Navigation))
        self.assertTrue(m.contains(Capability.Navigation))
        self.assertFalse(m.contains(Capability.ArtifactEvents))

    def test_reserved_rejected(self):
        with self.assertRaises(ProhibitedCapability):
            Manifest(CapabilitySet(1 << 7))

    def test_roundtrip(self):
        m = Manifest(CapabilitySet.all())
        self.assertEqual(Manifest.decode(m.encode()), m)


class TestCrossLanguageVectors(unittest.TestCase):
    """Deterministic vectors to replay against the Rust SDK."""

    def test_print_vectors(self):
        att = bytes([0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7])
        vectors = {
            "direction_up_full_conf": IntentObservation.direction(
                MonotonicTimestamp(1000), Direction.Up, 65535, 0x0102030405060708, att
            ),
            "load_high_half_conf": IntentObservation.load(
                MonotonicTimestamp(123456), Load.High, 32768, 0xAABBCCDD, att
            ),
            "quality_nosignal": IntentObservation.quality(
                MonotonicTimestamp(0), Quality.NoSignal, 0xDEADBEEF, att
            ),
        }
        print("\n--- RFC-0006 cross-language vectors (replay against Rust) ---")
        for name, obs in vectors.items():
            print(f"{name}: {obs.encode().hex()}")
            # sanity: every vector round-trips
            self.assertEqual(IntentObservation.decode(obs.encode()), obs)
        print("manifest{Navigation,SessionQuality}: "
              f"{Manifest(CapabilitySet.singleton(Capability.Navigation).with_(Capability.SessionQuality)).encode().hex()}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
