#!/usr/bin/env bash
# Single cold-start command for the T1 item 9 attestation
# (manifests/attest/item9.json): the cocotb slice bench, then the pad-checker
# self-test under the klayout.db that the pinned klt ships. Exit 0 iff both pass.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KLT_PIN="$(cat "$ROOT/.github/klt-version")"
"$ROOT/verification/run.sh"
uvx --from "klayout-tools==$KLT_PIN" python "$ROOT/layout/selftest.py"
