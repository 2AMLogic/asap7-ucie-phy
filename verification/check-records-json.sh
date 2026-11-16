#!/usr/bin/env bash
# The JSON-validity gate over the repository's committed record set. This is
# the single copy of that gate: both .github/workflows/signoff.yml and the
# attested records-json-valid check in manifests/t1-item10-inventory.json run
# this script, and check.sh takes its verdict from `--validate`. The record
# set is a rule, not a directory list, so a JSON record added anywhere is
# covered on arrival with no edit here.
#
# Record set: every tracked *.json file, minus the four tool directories
# (.loom/, .claude/, .agents/, .github/ -- vendored tool configuration, not
# project records):
#
#     git ls-files '*.json' | grep -vE '^\.(loom|claude|agents|github)/'
#
# Validity rule (spec/decisions/0011-json-document-stream.md): a tracked
# .json project record is valid iff its bytes are one or more JSON documents
# separated only by whitespace -- a json.JSONDecoder().raw_decode() loop
# consumes the file to its end. A single-document record is the n == 1 case,
# so the rule is a strict generalization of "is one JSON document". The walk
# is stdlib python3, never klt.
#
# `--validate` runs only that walk: git and python3, never the signoff
# toolchain, so check.sh (which must stay toolchain-free) can consume it and
# the verdict is the same on any host with python3.
#
# Default mode runs the walk first, then hands `klt env-provenance
# lint-envelope` the SINGLE-DOCUMENT partition of the record set -- klt
# cannot read a document stream (it rejects one with "Extra data: ...",
# measured on the 0.9.2 pin; filed upstream as
# 2AMLogic/klayout-tools#5887), so the per-document walk above is the
# validity verdict and klt is kept for what it adds. klt's exit contract
# (measured on 0.9.1 and 0.9.2):
#     0  all files valid, no absolute host paths
#     3  all files valid, absolute paths present (pre-existing findings, #172)
#     1  some file unreadable or not valid JSON -- names the first and aborts
#     2  no FILE arguments (argparse usage error)
# This gate passes on 0 and 3 and fails on 1, 2 and anything else: exit 1
# dominates exit 3. Enforcing the absolute-path findings (exit 3) is #172,
# not this gate.

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

record_set() {
    git ls-files '*.json' | grep -vE '^\.(loom|claude|agents|github)/'
}

fail() {
    echo "::error::check-records-json: $1" >&2
    exit 1
}

# The per-document validity walk: reads the record set from stdin (one path
# per line) and prints "path<TAB>document-count" per file. Fails -- exit 3,
# this caller's own "invalid record" code -- on any file whose bytes are not
# a clean document stream: zero bytes, whitespace only, or a parse error
# before end of input are all invalid, and every failure names its file.
# One copy of the rule, used by both --validate and default mode.
validate_stream() {
    python3 -c '
import json, sys
bad = 0
dec = json.JSONDecoder()
ws = " \t\n\r"
for path in (line.rstrip("\n") for line in sys.stdin if line.strip()):
    count = 0
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        if len(data) == 0:
            print("not a valid JSON document stream (zero bytes): %s" % path, file=sys.stderr)
            bad += 1
        else:
            text = data.decode("utf-8")
            idx = 0
            while True:
                while idx < len(text) and text[idx] in ws:
                    idx += 1
                if idx >= len(text):
                    break
                _, idx = dec.raw_decode(text, idx)
                count += 1
            if count == 0:
                print("not a valid JSON document stream (no document, whitespace only): %s" % path, file=sys.stderr)
                bad += 1
    except (ValueError, UnicodeDecodeError) as exc:
        print("not a valid JSON document stream: %s: %s" % (path, exc), file=sys.stderr)
        bad += 1
    print("%s\t%d" % (path, count))
sys.exit(3 if bad else 0)
'
}

LIST_ONLY=0
VALIDATE_ONLY=0
case "${1:-}" in
    "") ;;
    --list) LIST_ONLY=1 ;;
    --validate) VALIDATE_ONLY=1 ;;
    *) echo "usage: $0 [--list|--validate]" >&2; exit 2 ;;
esac

mapfile -t records < <(record_set)
if [ "${#records[@]}" -eq 0 ]; then
    fail "the tracked JSON record set is empty -- the gate cannot run and must not look like it passed"
fi

if [ "$LIST_ONLY" -eq 1 ]; then
    printf '%s\n' "${records[@]}"
    exit 0
fi

command -v python3 >/dev/null 2>&1 || fail "python3 not found on PATH -- cannot run the per-document validity walk; a gate that cannot run must not look like one that passed"

# --- the per-document walk (both modes) ---

walk_rc=0
counts="$(printf '%s\n' "${records[@]}" | validate_stream)" || walk_rc=$?
if [ "$walk_rc" -ne 0 ]; then
    fail "a committed JSON record is not a valid JSON document stream (named above); every tracked record must be one or more whitespace-separated JSON documents (spec/decisions/0011-json-document-stream.md)"
fi

total_docs="$(awk -F'\t' '{ s += $2 } END { print s + 0 }' <<<"$counts")"

if [ "$VALIDATE_ONLY" -eq 1 ]; then
    echo "records-json --validate: ${#records[@]} record(s) valid as JSON document streams ($total_docs document(s) total)"
    exit 0
fi

# --- default mode: the gate (per-document verdict above, then klt) ---

# klt is fed the single-document partition only. COVERAGE GAP -- #172 owns
# closing it: because klt cannot read a document stream (filed upstream as
# 2AMLogic/klayout-tools#5887), the files handed to lint-envelope are the
# single-document subset computed here (document count == 1), and a
# multi-document stream record is NOT scanned by klt for absolute host
# paths -- it gets the per-document validity verdict only. #172 plans to
# make this gate findings-fatal on lint-envelope exit 3; before that can
# ship it must decide how stream records are covered (splitting each into
# temp per-document files and remapping klt's diagnostics back to the real
# path is the known option), or a newly committed stream record could carry
# an absolute path and pass. This comment sits at the partition site on
# purpose: do not build the findings-fatal gate without meeting it.
partition="$(awk -F'\t' '$2 == 1 { print $1 }' <<<"$counts")"
if [ -z "$partition" ]; then
    fail "the single-document partition handed to lint-envelope is empty (every record is a stream) -- the klt leg would be a vacuous pass, so failing loudly"
fi
mapfile -t single_doc <<<"$partition"

command -v klt >/dev/null 2>&1 || fail "klt not found on PATH -- install the pinned klayout-tools (.github/klt-version); a gate that cannot run must not look like one that passed"

rc=0
klt env-provenance lint-envelope "${single_doc[@]}" || rc=$?
case "$rc" in
    0) echo "records-json: clean: ${#records[@]} record(s) valid ($total_docs document(s) total), no absolute paths" ;;
    3) echo "records-json: ${#records[@]} record(s) valid ($total_docs document(s) total); lint-envelope reported absolute-path findings (pass -- #172 owns making those fatal)" ;;
    1) fail "a committed JSON record does not parse (named above); every tracked record must parse" ;;
    2) fail "lint-envelope usage error (exit 2) -- the record set invocation is broken" ;;
    *) fail "lint-envelope exited $rc (expected 0, 3, 1 or 2) -- treating as a failure" ;;
esac
