#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Part of the AxonOS project - https://github.com/AxonOS-org
"""AxonOS — a runnable end-to-end demo on the real Python SDK.

    python examples/demo.py            # zero dependencies, no install needed

This is a **synthetic** session: it never touches a brain or any sensor. The
"signals" are generated numbers. What is *real* is everything the AxonOS SDK
actually does with them:

  * real `IntentObservation` records built through the SDK constructors,
  * the real RFC-0006 32-byte wire format (encode -> bytes -> decode), with the
    round-trip proven byte-for-byte on every event,
  * the real capability model: an app sees only the intent classes its manifest
    grants, and a request for raw brain data is rejected *structurally* — it is
    not a grantable capability, so the bytes never leave the kernel.

Edit the manifest near the bottom and watch which events get delivered.
"""

import random
import sys
from pathlib import Path

# Make the repo's `axonos` package importable without installing anything.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axonos import (  # noqa: E402
    Capability,
    CapabilitySet,
    Direction,
    IntentObservation,
    Load,
    Manifest,
    MonotonicTimestamp,
    ProhibitedCapability,
    Quality,
    to_raw,
)

# ---- tiny ANSI helpers (degrade gracefully if not a TTY) -------------------
_TTY = sys.stdout.isatty()
def _c(code, s):
    return f"\033[{code}m{s}\033[0m" if _TTY else s
def dim(s):   return _c("2", s)
def bold(s):  return _c("1", s)
def green(s): return _c("32", s)
def red(s):   return _c("31", s)
def cyan(s):  return _c("36", s)
def yellow(s):return _c("33", s)


def rule(title=""):
    line = "─" * 70
    print(f"\n{dim(line)}")
    if title:
        print(bold(title))


def hexdump(b: bytes) -> str:
    """32-byte record as two rows of hex, annotated by field offset."""
    h = b.hex()
    pairs = [h[i:i + 2] for i in range(0, len(h), 2)]
    row1 = " ".join(pairs[:16])
    row2 = " ".join(pairs[16:])
    return f"{row1}\n        {row2}"


def deliver_or_block(obs: IntentObservation, manifest: Manifest) -> bool:
    """The boundary check: the app only receives intent classes it was granted."""
    cap = obs.capability()
    if cap is not None and manifest.contains(cap):
        return True
    return False


def main() -> int:
    random.seed(7)  # deterministic, reproducible output

    print(bold("AxonOS — runnable demo") + dim("  (synthetic session; no brain, no sensor)"))
    print(dim("Every byte below is the real RFC-0006 wire format used by AxonOS."))

    # ---------------------------------------------------------------- step 1
    rule("[1] The application declares the capabilities it needs")
    manifest = Manifest(
        CapabilitySet.singleton(Capability.Navigation).with_(Capability.SessionQuality)
    )
    granted = ", ".join(c.name for c in manifest.capabilities)
    print(f"    requested : {cyan(granted)}")
    print(f"    bitfield  : {cyan(f'0x{manifest.capabilities.as_u32():08x}')}  "
          + dim("(little-endian u32, kernel-enforced)"))
    print(f"    {green('-> manifest accepted')}")

    # ---------------------------------------------------------------- step 2
    rule("[2] A different app asks for raw brain access")
    print(dim("    'raw EEG' is not one of the four catalogue capabilities, so it maps"))
    print(dim("    to a reserved bit. Building such a manifest must fail by construction:"))
    RAW_EEG_BIT = 1 << 5  # outside the catalogue (bits 0..3)
    try:
        Manifest(CapabilitySet(RAW_EEG_BIT))
        print(red("    -> ERROR: a prohibited manifest was accepted (should never happen)"))
        return 1
    except ProhibitedCapability as e:
        print(f"    {green('-> REJECTED')}: {e}")
        print(dim("       Raw signal is not a grantable capability — the bytes never"))
        print(dim("       leave the kernel. Privacy is structural, not a promise."))

    # ---------------------------------------------------------------- step 3
    rule("[3] Streaming synthetic intent observations  (wire round-trip + gate)")

    # A synthetic session: a sequence of (builder, label) producing real records.
    attest = bytes([0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7])  # demo attestation tag
    session_id = 0x0102030405060708
    t = MonotonicTimestamp(0)

    plan = [
        ("direction", Direction.Up,      0.93),
        ("quality",   Quality.High,      None),
        ("load",      Load.High,         0.71),
        ("direction", Direction.Right,   0.88),
        ("direction", Direction.Left,    0.40),   # low confidence
        ("load",      Load.Moderate,     0.55),
        ("quality",   Quality.Low,       None),
        ("direction", Direction.Down,    0.96),
    ]

    delivered = blocked = roundtrips = 0
    for i, (kind, value, conf) in enumerate(plan):
        t = t.saturating_add_micros(40_000)  # ~25 Hz cadence, just for the trace
        if kind == "direction":
            obs = IntentObservation.direction(t, value, to_raw(conf), session_id, attest)
        elif kind == "load":
            obs = IntentObservation.load(t, value, to_raw(conf), session_id, attest)
        else:
            obs = IntentObservation.quality(t, value, session_id, attest)

        # --- the real wire format: encode, then decode, and prove they match ---
        wire = obs.encode()
        back = IntentObservation.decode(wire)
        ok = (back == obs) and (len(wire) == 32)
        if ok:
            roundtrips += 1

        cap = obs.capability()
        cap_name = cap.name if cap is not None else "—"
        label = f"{obs.category}.{obs.kind.name if obs.kind is not None else '?'}"
        conf_txt = f"conf {obs.confidence:5.2f}"

        print(f"\n  {bold(f't=+{obs.timestamp_us:>7}µs')}  {label:<16} {conf_txt}  "
              f"cap {cyan(cap_name)}")
        print(dim(f"      wire(32B): {hexdump(wire)}"))
        print(dim(f"      decode   : {green('round-trip identical') if ok else red('MISMATCH')}"))

        if deliver_or_block(obs, manifest):
            delivered += 1
            print(f"      gate     : {green('GRANTED')} -> delivered to the app")
        else:
            blocked += 1
            print(f"      gate     : {yellow('BLOCKED')} "
                  + dim(f"(app was not granted {cap_name}) -> dropped at the boundary"))

    # ---------------------------------------------------------------- step 4
    rule("[4] Summary")
    n = len(plan)
    print(f"    {n} observations · "
          f"{green(f'{roundtrips}/{n} wire round-trips identical')} · "
          f"{green(f'{delivered} delivered')} · {yellow(f'{blocked} blocked')}")
    print(dim("    The blocked events carried valid intents — they were withheld purely"))
    print(dim("    because the app's manifest did not grant their capability class."))
    print()
    print("    Try it yourself: change the manifest in this file (e.g. add "
          + cyan("Capability.WorkloadAdvisory") + ")")
    print("    and re-run — the Load events will start being delivered.")
    print()
    print(dim("    This is a simulation of the real AxonOS data path, built on the"))
    print(dim("    same SDK that talks to the kernel. Learn more: ")
          + "https://github.com/AxonOS-org")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
