#!/usr/bin/env bash
# Cold-start runner: checks pinned tools, builds a private cocotb venv, runs
# the slice loopback for 16 and 8 lanes, writes verification/runs/<stamp>.txt.
#   run.sh                    exit 0 iff every test passes
#   run.sh --negative-control exit 0 iff the deliberately broken check fails
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIN="$HERE/tool-versions.txt"
VENV="$HERE/.venv"
NEG=0
[ "${1:-}" = "--negative-control" ] && NEG=1

pin() { sed -n "s/^$1=//p" "$PIN"; }
die() { echo "run.sh: $*" >&2; exit 2; }

check() { # name installed
  local want; want="$(pin "$1")"
  [ "$2" = "$want" ] || die "$1 is '$2' but $PIN pins '$want'. Not changing host tools; fix the pin by a reviewed change or use the pinned tool."
}
check yosys "$(yosys -V 2>/dev/null | awk '{print $2}' | sed 's/+.*//')"
check verilator "$(verilator --version 2>/dev/null | awk '{print $2}')"
check iverilog "$(iverilog -V 2>/dev/null | head -1 | sed -n 's/.*version \([0-9.]*\).*/\1/p')"

if [ ! -x "$VENV/bin/python" ] || [ "$("$VENV/bin/python" -c 'import cocotb;print(cocotb.__version__)' 2>/dev/null)" != "$(pin cocotb)" ]; then
  uv venv --quiet "$VENV"
  uv pip install --quiet --python "$VENV/bin/python" "cocotb==$(pin cocotb)"
fi
check cocotb "$("$VENV/bin/python" -c 'import cocotb;print(cocotb.__version__)')"
export PATH="$VENV/bin:$PATH"

export SEED="${SEED:-$(pin seed)}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mode=run; [ "$NEG" = 1 ] && mode=negative-control
OUT="$HERE/runs/$mode-$STAMP.txt"
BUILD="$HERE/runs/build-$mode-$STAMP"
mkdir -p "$BUILD"

rc=0; tests=0; failed=0; words=0; lines=""
for lanes in 16 8; do
  d="$BUILD/lanes$lanes"; mkdir -p "$d"
  args=("$lanes" "$d"); [ "$NEG" = 1 ] && args+=(--negative-control)
  if ! "$VENV/bin/python" -I "$HERE/runner.py" "${args[@]}" >"$d/sim.log" 2>&1; then
    echo "run.sh: simulation for $lanes lanes did not complete; see $d/sim.log" >&2
    tail -20 "$d/sim.log" >&2; rc=1; continue
  fi
  read -r t f < <("$VENV/bin/python" -I - "$d/results.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
r = ET.parse(sys.argv[1]).getroot()
cases = list(r.iter("testcase"))
print(len(cases), sum(1 for c in cases if c.find("failure") is not None or c.find("error") is not None))
PY
)
  w="$("$VENV/bin/python" -I -c 'import json,sys;print(json.load(open(sys.argv[1]))["words_checked"])' "$d/summary.json" 2>/dev/null || echo 0)"
  tests=$((tests+t)); failed=$((failed+f)); words=$((words+w))
  lines+="lanes=$lanes tests=$t failed=$f words_checked=$w"$'\n'
  if [ "$NEG" = 1 ] && ! grep -qi "negative control" "$d/results.xml"; then
    echo "run.sh: negative control: failure not from the broken check; see $d" >&2; rc=1
  fi
done

if [ "$NEG" = 1 ]; then
  [ "$failed" -gt 0 ] || { echo "run.sh: negative control PASSED, so the check is not sensitive" >&2; rc=1; }
  verdict=$([ $rc = 0 ] && echo "NEGATIVE CONTROL OK (broken check failed as required)" || echo "NEGATIVE CONTROL NOT SATISFIED")
else
  [ "$failed" = 0 ] || rc=1
  verdict=$([ $rc = 0 ] && echo PASS || echo FAIL)
fi

{
  echo "mode=$mode"
  echo "date_utc=$STAMP"
  echo "seed=$SEED"
  echo "yosys=$(pin yosys) verilator=$(pin verilator) iverilog=$(pin iverilog) cocotb=$(pin cocotb)"
  printf '%s' "$lines"
  echo "total_tests=$tests total_failed=$failed total_passed=$((tests-failed)) words_checked=$words"
  echo "verdict=$verdict"
  echo "note=functional simulation only; simulator time units carry no rate or timing claim"
} | tee "$OUT"
exit $rc
