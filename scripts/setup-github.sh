#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Set the GitHub "About" (description + homepage) and topics for this repo.
# Requires the GitHub CLI (`gh`) authenticated with repo-admin rights.
#
#   ./scripts/setup-github.sh
#
set -euo pipefail

REPO="AxonOS-org/axonos-sdk-python"

DESCRIPTION="Python SDK for AxonOS — RFC-0006 intent wire format and capability model, byte-compatible with the Rust reference."
HOMEPAGE="https://axonos.org"

gh repo edit "$REPO" \
  --description "$DESCRIPTION" \
  --homepage "$HOMEPAGE" \
  --add-topic axonos \
  --add-topic bci \
  --add-topic brain-computer-interface \
  --add-topic neurotechnology \
  --add-topic python \
  --add-topic sdk \
  --add-topic real-time \
  --add-topic rfc-0006 \
  --add-topic wire-format

echo "About + topics set for $REPO"
