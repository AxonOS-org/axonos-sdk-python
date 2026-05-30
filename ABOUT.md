# About `axonos-sdk-python`

The Python edition of the AxonOS application boundary. It is a pure-Python,
dependency-free implementation of the RFC-0006 intent-observation wire format
and the capability model, byte-compatible with the reference Rust
[`axonos-sdk`](https://github.com/AxonOS-org/axonos-sdk) for
`KERNEL_ABI_VERSION == 1`.

It exists so that host-side tooling and Python application code can read
kernel observations, declare capability manifests, and round-trip the wire
format without reaching for the Rust toolchain. It does not enforce
capabilities or verify attestations — the kernel does that — and it does not
stub those paths as if it did.

Part of the AxonOS project. See the [organisation](https://github.com/AxonOS-org)
for the kernel, standard, and the rest of the stack.
