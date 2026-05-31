# Examples

## `demo.py` — runnable end-to-end demo

```bash
python examples/demo.py
```

Zero dependencies, no install required. It runs a **synthetic** AxonOS session —
no brain and no sensor are ever read — to show, on the *real* SDK:

- real `IntentObservation` records built through the SDK constructors;
- the real **RFC-0006 32-byte wire format** (`encode` → bytes → `decode`), with
  the round-trip proven byte-for-byte on every event and the bytes printed as a
  hexdump you can verify against the spec;
- the real **capability model** — an app receives only the intent classes its
  `Manifest` grants, and a request for raw brain data is rejected *by
  construction* (raw signal is not a grantable capability), so those bytes never
  leave the kernel.

Edit the manifest near the bottom of `demo.py` (for example, add
`Capability.WorkloadAdvisory`) and re-run to watch which events get delivered
versus dropped at the boundary.

It doubles as living documentation for the wire format and the capability gate.
