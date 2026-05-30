# Changelog

All notable changes to `axonos-sdk-python` are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-30

### Added
- `IntentObservation` — 32-byte, little-endian RFC-0006 wire codec
  (`encode`/`decode`), byte-compatible with the Rust `axonos-sdk` for
  `KERNEL_ABI_VERSION == 1`. Layout: `timestamp_us` (u64), `kind_tag` (u16),
  `quality_raw` (Q0.16 u16), `payload` ([u8;4]), `session_id` (u64),
  `attestation` ([u8;8]).
- `Direction`, `Load`, `Quality` intent kinds; typed `kind` resolution and
  `capability()` mapping.
- `Capability`, `CapabilitySet` (little-endian u32 bitfield), `Manifest`
  with reserved-bit rejection.
- `MonotonicTimestamp` (saturating arithmetic) and Q0.16 helpers
  (`to_raw`, `to_float`).
- 21-test unit suite including cross-language byte vectors for validation
  against the Rust reference.

### Not yet implemented (roadmap, intentionally not stubbed)
- Cryptographic attestation verification.
- Typed observation stream and full mesh client.
