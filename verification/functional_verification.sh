#!/usr/bin/env bash
# Wrap the cocotb slice bench in `klt functional-verification` (T1 item 5, digital
# partition): one report per lane count, written next to this script.
#   functional_verification.sh                 exit 0 iff every test passes
#   functional_verification.sh --negative-control   exit 0 iff the broken check fails
# Same pins and seed as run.sh (tool-versions.txt); never changes host tools. The klt
# wheel and its cocotb come from uvx, so no private venv is needed.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/.."
PIN="$HERE/tool-versions.txt"
KLT_PIN="$(cat "$ROOT/.github/klt-version")"
pin() { sed -n "s/^$1=//p" "$PIN"; }
die() { echo "functional_verification.sh: $*" >&2; exit 2; }
NEG=0; [ "${1:-}" = "--negative-control" ] && NEG=1

check() { [ "$2" = "$(pin "$1")" ] || die "$1 is '$2' but $PIN pins '$(pin "$1")'; not changing host tools."; }
check yosys "$(yosys -V 2>/dev/null | awk '{print $2}' | sed 's/+.*//')"
check verilator "$(verilator --version 2>/dev/null | awk '{print $2}')"
check iverilog "$(iverilog -V 2>/dev/null | head -1 | sed -n 's/.*version \([0-9.]*\).*/\1/p')"

export SEED="${SEED:-$(pin seed)}"
export NEG_CONTROL="$NEG"
SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT
rc=0
for lanes in 16 8; do
  export LANES="$lanes" SUMMARY_PATH="$SCRATCH/summary-$lanes.json"
  suffix=report; [ "$NEG" = 1 ] && suffix=negative-control.report
  out="$HERE/functional-verification-$lanes.$suffix.json"
  set +e
  uvx --from "klayout-tools[functional-verification]==$KLT_PIN" klt functional-verification \
    "$HERE/functional-verification-$lanes.json" -o "$SCRATCH/run-$lanes" --format json >"$out"
  krc=$?
  set -e
  echo "lanes=$lanes klt exit=$krc report=$out"
  if [ "$NEG" = 1 ]; then [ "$krc" != 0 ] || { echo "negative control PASSED; the check is not sensitive" >&2; rc=1; }
  else [ "$krc" = 0 ] || rc=1; fi
done
exit $rc
