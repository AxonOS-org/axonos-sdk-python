# Security Policy

## Reporting

Report suspected vulnerabilities privately to **security@axonos.org**.
Please do not open public issues for security reports. We aim to acknowledge
within a few working days.

## Scope and trust model

This SDK speaks the AxonOS wire format and models the capability gate. It is a
**client-side** library: it does **not** enforce capabilities and does **not**
verify cryptographic attestation. Those are kernel responsibilities and must
not be assumed from this package. Attestation verification is on the roadmap
and is deliberately absent rather than stubbed as a no-op.

Treat any `IntentObservation` decoded by this library as untrusted input until
the kernel's attestation has been verified by the kernel itself.
