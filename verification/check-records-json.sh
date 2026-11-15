#!/usr/bin/env bash
# The JSON-validity gate over the repository's committed record set. This is
# the single copy of that gate: both .github/workflows/signoff.yml and the
# attested records-json-valid check in manifests/t1-item10-inventory.json run
# this script, and check.sh takes its file list from `--list`. The record set
# is a rule, not a directory list, so a JSON record added anywhere is covered
# on arrival with no edit here.
#
# Record set: every tracked *.json file, minus the four tool directories
# (.loom/, .claude/, .agents/, .github/ -- vendored tool configuration, not
# project records):
#
#     git ls-files '*.json' | grep -vE '^\.(loom|claude|agents|github)/'
#
# The validity check itself is `klt env-provenance lint-envelope`, not a
# repo-local json.loads loop: klt ships it, it is a strict superset of a
# json.loads walk, and the pinned klt is what CI installs. Its exit contract
# (measured on 0.9.1 and 0.9.2):
#     0  all files valid, no absolute host paths
#     3  all files valid, absolute paths present (pre-existing findings, #172)
#     1  some file unreadable or not valid JSON -- names the first and aborts
#     2  no FILE arguments (argparse usage error)
# This gate passes on 0 and 3 and fails on 1, 2 and anything else: exit 1
# dominates exit 3, so "exit 1" is exactly "some tracked record does not
# parse", which is the property this gate exists to enforce. Enforcing the
# absolute-path findings (exit 3) is #172, not this gate.
#
# SCOPE -- read this before quoting an exit 0.
# `--list` prints the record set and uses only git and the shell -- never
# klt -- so check.sh (which must stay toolchain-free) can consume it. This
# script itself needs klt (default mode) and python3 (the stream exception
# self-retire check below); it fails loudly when either is missing rather
# than reporting a vacuous pass.

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

# The stream exception (#191): this committed record is a deliberate
# two-document JSON stream (its producer prints one json.dumps per netlist;
# its consumer raw_decode()s them in a loop), so a single-document parser
# rejects it. It is excepted by exactly this one literal path -- never a
# glob, never a directory -- until #191 rules on its disposition. The
# exception self-retires: the gate fails if the path disappears or if the
# file starts parsing as a single JSON document, so the exception cannot
# outlive #191 silently.
STREAM_EXCEPTION="evidence/item4-lvs/slice_routed.r13.refnets.json"

record_set() {
    git ls-files '*.json' | grep -vE '^\.(loom|claude|agents|github)/'
}

fail() {
    echo "::error::check-records-json: $1" >&2
    exit 1
}

LIST_ONLY=0
case "${1:-}" in
    "") ;;
    --list) LIST_ONLY=1 ;;
    *) echo "usage: $0 [--list]" >&2; exit 2 ;;
esac

mapfile -t records < <(record_set | grep -vxF -- "$STREAM_EXCEPTION")
if [ "${#records[@]}" -eq 0 ]; then
    fail "the tracked JSON record set is empty -- the gate cannot run and must not look like it passed"
fi

if [ "$LIST_ONLY" -eq 1 ]; then
    printf '%s\n' "${records[@]}"
    exit 0
fi

# --- default mode: the gate ---

command -v python3 >/dev/null 2>&1 || fail "python3 not found on PATH -- cannot run the self-retire check for the stream exception"
command -v klt >/dev/null 2>&1 || fail "klt not found on PATH -- install the pinned klayout-tools (.github/klt-version); a gate that cannot run must not look like one that passed"

# Self-retire the stream exception (#191).
if [ ! -f "$STREAM_EXCEPTION" ]; then
    fail "stream exception is stale: $STREAM_EXCEPTION is gone -- remove the exception (see #191)"
fi
if python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$STREAM_EXCEPTION" 2>/dev/null; then
    fail "stream exception is stale: $STREAM_EXCEPTION now parses as a single JSON document -- remove the exception (see #191)"
fi

rc=0
klt env-provenance lint-envelope "${records[@]}" || rc=$?
case "$rc" in
    0) echo "records-json: clean: ${#records[@]} record(s) valid, no absolute paths" ;;
    3) echo "records-json: ${#records[@]} record(s) valid; lint-envelope reported absolute-path findings (pass -- #172 owns making those fatal)" ;;
    1) fail "a committed JSON record does not parse (named above); every tracked record must parse" ;;
    2) fail "lint-envelope usage error (exit 2) -- the record set invocation is broken" ;;
    *) fail "lint-envelope exited $rc (expected 0, 3, 1 or 2) -- treating as a failure" ;;
esac
