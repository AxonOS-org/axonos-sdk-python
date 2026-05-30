# Contributing

Thanks for your interest in `axonos-sdk-python`.

## Ground rules

- The wire format is **normative**. Any change to `IntentObservation`,
  `CapabilitySet`, or the Q0.16 / timestamp encoding must remain byte-for-byte
  compatible with the Rust `axonos-sdk` and the kernel's RFC-0006, or be
  accompanied by a coordinated ABI-version bump.
- No runtime dependencies. Standard library only.
- Never stub a security path (e.g. attestation) so that it appears present.
  An unimplemented guarantee is documented as unimplemented.

## Local checks (the same as CI)

```bash
pip install ruff==0.15.15
ruff check axonos tests
python -m unittest discover -s tests -v
pip install build && python -m build
```

## Cross-language fidelity

If you touch the wire format, regenerate the vectors in
`tests/test_wire.py::TestCrossLanguageVectors` and confirm the same bytes are
produced by the Rust reference before opening a pull request.
