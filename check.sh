#!/usr/bin/env bash
# Host-independent repo gate: the checks that run anywhere python3 runs.
#
# This is what `npm run check:ci` / `check:all` / `test` resolve to
# (package.json). Those names are what the agent roles in .loom/roles/ are
# instructed to call as a build gate, so they must verify something real: a
# gate that exits 0 without running a check is a false-green verification
# signal, which CLAUDE.md forbids ("no claim without a testbench or a recorded
# tool run") and .loom/CLAUDE.md restates for CI ("a check that cannot run must
# never look like one that passed").
#
# SCOPE -- read this before quoting an exit 0.
#
# Every check below is stdlib-only python3: no klayout-tools CLI, no klayout
# module, no OpenROAD, no yosys, no iverilog, no PDK archive, no network. The
# JSON-validity check additionally needs git and a working checkout of this
# repo, because its file list comes from `verification/check-records-json.sh
# --list` (git ls-files); outside a checkout it fails closed rather than
# passing vacuously. That is the point -- it is the same verdict on any host,
# so there is no "tool missing, so skipped, so passed" path. The cost is that
# it is NOT T1 signoff and NOT the functional testbench. An exit 0 here says
# the committed cell netlists, the routed-stream input tie-off and the
# committed JSON records have not drifted. It says nothing about DRC, LVS,
# STA, the cocotb bench or the signoff verdict. Those need the toolchain and
# are listed under "Reproduce" in README.md; CI runs the attestation --check
# commands in .github/workflows/signoff.yml.
#
# Adding a check here: it must run unconditionally. Never guard one behind
# `command -v <tool>` and fall through to success when the tool is absent --
# that reintroduces exactly the vacuous pass this script replaced. A check that
# needs a toolchain belongs in README.md's Reproduce list or the signoff
# workflow, not here.

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
    echo "check.sh: python3 not found on PATH -- cannot run any check" >&2
    echo "check.sh: FAILING rather than reporting a vacuous pass" >&2
    exit 1
fi

RAN=0
FAILED=0

# Run one check. Non-zero (any code -- the regen scripts use 3 for drift and 2
# for bad input) is a failure.
run_check() {
    local name="$1"
    shift
    RAN=$((RAN + 1))
    printf '==> %s\n' "$name"
    if "$@"; then
        printf '    PASS  %s\n' "$name"
    else
        local rc=$?
        printf '    FAIL  %s (exit %d)\n' "$name" "$rc"
        FAILED=$((FAILED + 1))
    fi
}

# Committed TX/RX cell netlists still reproduce from their generator.
run_check "design/gen_cells.py --check" \
    python3 -I design/gen_cells.py --check

# The tied netlist still hashes to the provenance recorded in the routed
# report, i.e. the committed stream was routed from the committed input.
run_check "layout/pnr/regen.py --check-input" \
    python3 -I layout/pnr/regen.py --check-input

# Self-test of that --check-input gate: match, drift, bad input, and the
# tie_constants fixture hash. A gate nobody tests is the defect this file fixes.
run_check "layout/pnr/test_check_input.py" \
    python3 -I layout/pnr/test_check_input.py

# Every committed JSON project record parses. The file list comes from the
# single copy of the record-set rule, verification/check-records-json.sh
# --list (git + shell only, never the signoff toolchain), and the validator
# here stays stdlib-only so this check keeps the same verdict on any host with
# python3 and no signoff toolchain. Covers the whole tracked record set --
# evidence/, attest/, sta/, verification/, sim/, design/ and manifests/ alike
# -- so a malformed record outside manifests/ fails here too rather than only
# in CI.
run_check "committed JSON records parse (whole tracked record set)" \
    python3 -I -c '
import json, subprocess, sys
res = subprocess.run(["bash", "verification/check-records-json.sh", "--list"],
                     capture_output=True, text=True)
if res.returncode != 0:
    sys.stderr.write(res.stderr)
    sys.exit(res.returncode)
paths = sorted(p for p in res.stdout.splitlines() if p)
if not paths:
    print("    empty record set -- the gate cannot run and must not look like it passed")
    sys.exit(1)
bad = 0
for p in paths:
    try:
        json.loads(open(p, encoding="utf-8").read())
    except ValueError as e:
        print("    not valid JSON: %s: %s" % (p, e))
        bad += 1
print("    %d records checked" % len(paths))
sys.exit(1 if bad else 0)
'

# Structural guard on this script itself, not a comment asking nicely: if the
# check list is ever emptied or every invocation is edited away, exit non-zero
# instead of inheriting FAILED=0 and reporting the vacuous pass that issue #153
# removed.
if [ "$RAN" -eq 0 ]; then
    echo "check.sh: no checks ran -- refusing to report a pass" >&2
    exit 1
fi

echo
if [ "$FAILED" -ne 0 ]; then
    printf 'check.sh: %d of %d checks FAILED\n' "$FAILED" "$RAN" >&2
    exit 1
fi

printf 'check.sh: %d checks passed (stdlib-only scope -- not T1 signoff)\n' "$RAN"
