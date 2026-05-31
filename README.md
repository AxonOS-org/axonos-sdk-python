# AxonOS SDK for Python

A pure-Python, dependency-free port of the AxonOS application boundary: the
RFC-0006 intent-observation wire format, the capability model, and the
deterministic Q0.16 / monotonic-time primitives. It is **byte-compatible**
with the reference Rust [`axonos-sdk`](https://github.com/AxonOS-org/axonos-sdk)
for `KERNEL_ABI_VERSION == 1`.

## Scope, honestly

This package lets host-side and Python application code **read** kernel
observations, **declare** capability manifests, and work with the wire format.
It does **not** enforce capabilities or verify attestations — the kernel does
that, and a client cannot be trusted to. Cryptographic attestation
verification is on the roadmap and is deliberately **not** stubbed as if it
were present.

It is a clean-room implementation of the same RFC-0006 §4.1 wire format the
Rust crate implements; the two are validated against shared byte vectors
(`tests/test_wire.py`), not by sharing code.

## Wire format (`IntentObservation`, 32 bytes, little-endian)

| Offset | Size | Field | Type |
|:---|:---|:---|:---|
| 0 | 8 | `timestamp_us` | `u64` — µs since session start |
| 8 | 2 | `kind_tag` | `u16` — 1=Direction, 2=Load, 3=Quality |
| 10 | 2 | `quality_raw` | `u16` — Q0.16 confidence (`65535` = 1.0) |
| 12 | 4 | `payload` | `[u8; 4]` — `payload[0]` is the kind discriminant |
| 16 | 8 | `session_id` | `u64` |
| 24 | 8 | `attestation` | `[u8; 8]` — truncated HMAC-SHA256 |

## Install

```bash
pip install -e .        # from a checkout
```

No runtime dependencies. Python 3.8+.

## Quick start

```python
from axonos import IntentObservation, Manifest, CapabilitySet, Capability

# 1. Declare what the application needs.
manifest = Manifest(
    CapabilitySet.singleton(Capability.Navigation).with_(Capability.SessionQuality)
)

# 2. Decode a 32-byte observation from the kernel IPC.
obs = IntentObservation.decode(raw_bytes)

# 3. Check capability before acting.
if obs.capability() is not None and manifest.contains(obs.capability()):
    print(obs.kind, obs.confidence)   # e.g. Direction.Up 0.93
```

## Run the demo

See it work end-to-end in one command — no install, no dependencies:

```bash
python examples/demo.py
```

It runs a synthetic session (no brain, no sensor) that builds real
`IntentObservation` records, proves the 32-byte wire round-trip on every event,
and runs the capability gate — including rejecting raw-signal access by
construction. See [`examples/`](examples/).

## Cross-language fidelity

`tests/test_wire.py` prints deterministic byte vectors (`direction_up_full_conf`,
`load_high_half_conf`, `quality_nosignal`). Replay the same constructor inputs
through the Rust `axonos-sdk` and compare the encoded bytes to confirm the two
implementations agree exactly.

```bash
python -m unittest discover -s tests -v
```

## Status

`v0.1.0` — first Python module of a planned multi-language SDK. Implemented:
intent wire codec, capability set / manifest, Q0.16, monotonic time. Tracked
next, gradually: typed observation stream, mesh client, and attestation
verification (the last to land only as a real implementation, never a no-op).

---

**The AxonOS Project** · [axonos.org](https://axonos.org) · connect@axonos.org · security@axonos.org
[medium.com/@AxonOS](https://medium.com/@AxonOS) · [github.com/AxonOS-org](https://github.com/AxonOS-org)
Licensed under Apache-2.0 OR MIT.
