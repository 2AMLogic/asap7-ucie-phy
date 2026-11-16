#!/usr/bin/env bash
# The committed-record gate. This is the single copy of that gate: both
# .github/workflows/signoff.yml and the attested records-json-valid check in
# manifests/t1-item10-inventory.json run this script (default mode), and
# check.sh takes its file list from `--list`. The record set is a rule, not a
# directory list, so a JSON record added anywhere is covered on arrival with
# no edit here.
#
# Two modes:
#
#   default             the whole tracked record set, validity-only: every
#                       committed record must parse. Absolute-path findings
#                       (exit 3) are tolerated -- they are the frozen history
#                       recorded in spec/decisions/0011-record-path-hygiene-
#                       gate.md, and #136/#20 own any edit or re-run of it
#                       (#166's contract, unchanged by #172).
#
#   --changed --base B  the forward-only gate (#172, decision 0011): every
#                       record ADDED OR CHANGED between base B and HEAD is
#                       gated on BOTH klt env-provenance checks --
#
#                         lint-envelope  with the class-2 prefix set
#                                        (--allow-prefix /usr/bin
#                                        --allow-prefix /usr/local/bin --
#                                        the measured minimal set)
#                         scan           the home-directory leak check
#
#                       exit 3 from either is fatal for a changed record,
#                       exit 1 (some record does not parse) is fatal. The
#                       whole-set run stays validity-only; this mode never
#                       re-lints frozen history.
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
#     3  all files valid, absolute paths present (frozen history, decision 0011)
#     1  some file unreadable or not valid JSON -- names the first and aborts
#     2  no FILE arguments (argparse usage error)
# `scan` shares the contract: 3 = leaks found, 0 = clean, 1 = unreadable.
#
# THE DECK EXCEPTION (decision 0011; 2AMLogic/klayout-tools#5709) -- read
# before loosening it. While #5709 is open every klt-generated DRC envelope
# records its deck as a bare absolute host path (a uv cache directory keyed
# by a build hash; measured again at the 0.9.2 pin -- a pin bump is not the
# remedy). A fresh envelope is the repo's primary evidence product, so the
# changed-record gate admits exactly one thing: the top-level `deck` field of
# a changed *.envelope.json -- the dotted field `deck` for lint-envelope, the
# single line carrying that field for scan (scan is text-matched, so the line
# is matched against the value the envelope itself declares). Nothing else is
# admitted: NOT --allow-prefix /home/..., which the tool's help rules out
# because a lint whose verdict depends on the linting machine cannot be
# trusted in CI. The exception is self-limiting -- once klt stops writing the
# absolute path, the finding it admits no longer exists. REMOVE it when
# #5709 is closed and .github/klt-version is at or past the fix, verified by
# regenerating a DRC envelope and confirming the top-level deck is no longer
# absolute.
#
# STREAM EXCEPTION (#191): this committed record is a deliberate
# two-document JSON stream (its producer prints one json.dumps per netlist;
# its consumer raw_decode()s them in a loop), so a single-document parser
# rejects it. It is excepted by exactly this one literal path -- never a
# glob, never a directory -- until #191 rules on its disposition. The
# exception self-retires: the gate fails if the path disappears or if the
# file starts parsing as a single JSON document, so the exception cannot
# outlive #191 silently. It is excluded from BOTH modes: the whole-set run
# (exit 1 dominates exit 3) and the changed-record run (a commit touching it
# would otherwise go red for a reason #191, not #172, owns).
#
# NO VACUOUS PASS. The changed-record list "cannot be computed" -- and the
# gate FAILS -- when the base is not a commit this checkout can see, when the
# base is not an ancestor of HEAD, when the base..HEAD range names no file at
# all, or when the record-set rule itself selects nothing on this tree. Only
# after all four validations is an empty changed-record list a computed
# result ("this range changes no tracked record"), reported loudly rather
# than silently; the whole-set validity gate still covered parsing.
#
# SCOPE -- read this before quoting an exit 0.
# `--list` prints the record set and uses only git and the shell -- never
# klt -- so check.sh (which must stay toolchain-free) can consume it. This
# script itself needs klt (default and --changed modes) and python3 (the
# stream-exception self-retire check and the decision-0011 deck-exception
# filters); it fails loudly when either is missing rather than reporting a
# vacuous pass.

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

# The stream exception (#191): see the header comment.
STREAM_EXCEPTION="evidence/item4-lvs/slice_routed.r13.refnets.json"

# The class-2 prefix set (decision 0011): machine-wide tool install prefixes
# that may legitimately appear in a committed record. Measured minimal at the
# pinned klt 0.9.2 -- adding /opt/pdk admits nothing at this tree and is
# deliberately absent. NEVER add /tmp (a per-run scratch path is the exact
# non-reproducible reference this lint exists to catch) and NEVER add a
# /home prefix (the tool's help rules it out; see the header comment).
CLASS2_PREFIXES=(/usr/bin /usr/local/bin)

record_set() {
    git ls-files '*.json' | grep -vE '^\.(loom|claude|agents|github)/'
}

fail() {
    echo "::error::check-records-json: $1" >&2
    exit 1
}

LIST_ONLY=0
CHANGED=0
BASE_SHA=""
case "${1:-}" in
    "") ;;
    --list) LIST_ONLY=1 ;;
    --changed)
        CHANGED=1
        [ "${2:-}" = "--base" ] || { echo "usage: $0 --changed --base <commit>" >&2; exit 2; }
        BASE_SHA="${3-}"
        [ -n "$BASE_SHA" ] || { echo "usage: $0 --changed --base <commit> (--base needs a commit)" >&2; exit 2; }
        ;;
    *) echo "usage: $0 [--list | --changed --base <commit>]" >&2; exit 2 ;;
esac

mapfile -t records < <(record_set | grep -vxF -- "$STREAM_EXCEPTION")
if [ "${#records[@]}" -eq 0 ]; then
    fail "the tracked JSON record set is empty -- the gate cannot run and must not look like it passed"
fi

if [ "$LIST_ONLY" -eq 1 ]; then
    printf '%s\n' "${records[@]}"
    exit 0
fi

command -v python3 >/dev/null 2>&1 || fail "python3 not found on PATH -- cannot run the stream-exception self-retire check or the decision-0011 deck-exception filters"
command -v klt >/dev/null 2>&1 || fail "klt not found on PATH -- install the pinned klayout-tools (.github/klt-version); a gate that cannot run must not look like one that passed"

# --- --changed --base B: the forward-only gate (#172, decision 0011) ---

if [ "$CHANGED" -eq 1 ]; then

    # The four validations whose failure means the changed-record list cannot
    # be computed. Each fails the gate; none can fall through to a pass.
    if ! git rev-parse --verify "${BASE_SHA}^{commit}" >/dev/null 2>&1; then
        fail "base $BASE_SHA is not a commit this checkout can see -- the changed-record list cannot be computed; give CI the history it needs (fetch-depth: 0) or pass a resolvable base"
    fi
    if ! git merge-base --is-ancestor "$BASE_SHA" HEAD 2>/dev/null; then
        fail "base $BASE_SHA is not an ancestor of HEAD -- the changed-record range cannot be trusted, so the gate refuses rather than guess"
    fi
    mapfile -t range_files < <(git diff --name-only --diff-filter=ACMR "$BASE_SHA" HEAD)
    if [ "${#range_files[@]}" -eq 0 ]; then
        fail "git diff $BASE_SHA HEAD names no file -- the changed-record list cannot be computed (empty range), and a gate with nothing to look at must not look like it passed"
    fi

    mapfile -t changed_records < <(printf '%s\n' "${range_files[@]}" \
        | grep -E '\.json$' \
        | grep -vE '^\.(loom|claude|agents|github)/' \
        | grep -vxF -- "$STREAM_EXCEPTION")
    if [ "${#changed_records[@]}" -eq 0 ]; then
        # A computed result, not a failure to compute: the four validations
        # above passed, the range names files, and none of them is a tracked
        # JSON record. Say so loudly and pass -- the whole-set validity gate
        # still covers every committed record.
        echo "records-json: changed-record gate: ${#range_files[@]} file(s) changed since ${BASE_SHA:0:12}, none is a tracked JSON record -- nothing to gate forward (the whole-set validity gate still ran)"
        exit 0
    fi
    echo "records-json: changed-record gate: ${#changed_records[@]} record(s) added or changed since ${BASE_SHA:0:12}: ${changed_records[*]}"

    lint_report="$(mktemp)"
    scan_report="$(mktemp)"
    trap 'rm -f "$lint_report" "$scan_report"' EXIT

    # lint-envelope over the changed records, with the class-2 prefix set.
    lint_args=(--format json)
    for p in "${CLASS2_PREFIXES[@]}"; do lint_args+=(--allow-prefix "$p"); done
    lint_rc=0
    klt env-provenance lint-envelope "${lint_args[@]}" "${changed_records[@]}" > "$lint_report" || lint_rc=$?
    case "$lint_rc" in
        0) echo "records-json: lint-envelope: ${#changed_records[@]} changed record(s) carry no absolute host path outside the declared prefixes" ;;
        3)
            # Post-filter the decision-0011 deck exception, then judge the
            # residual. A finding survives unless it is exactly the
            # top-level `deck` field of a changed *.envelope.json whose
            # value is the deck path that envelope itself declares.
            if ! python3 - "$lint_report" <<'PY'
import json, sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
residual = []
excepted = 0
for f in report.get("files", []):
    name = f.get("file", "")
    deck = None
    if name.endswith(".envelope.json"):
        try:
            with open(name, encoding="utf-8") as fh:
                deck = json.load(fh).get("deck")
        except Exception:
            deck = None
    for x in f.get("findings", []):
        if (name.endswith(".envelope.json") and isinstance(deck, str)
                and x.get("field") == "deck" and x.get("match") == deck):
            excepted += 1
            continue
        residual.append((name, x.get("field"), x.get("match")))
if residual:
    for name, field, match in residual:
        print(f"  {name} :: {field} = {match}", file=sys.stderr)
    print(f"lint-envelope: {len(residual)} finding(s) remain after the "
          f"decision-0011 deck exception ({excepted} excepted)", file=sys.stderr)
    sys.exit(3)
print(f"lint-envelope: only the decision-0011 deck exception applied "
      f"({excepted} excepted deck field(s)); nothing else")
PY
            then
                fail "a record added or changed by this range carries an absolute host path (findings above). The frozen history of decision 0011 (spec/decisions/0011-record-path-hygiene-gate.md) is not reopened by this gate: write repo-relative references or a content hash, and cite a deck by provenance.deck.content_hash, never by path"
            fi
            ;;
        1) fail "a record added or changed by this range does not parse (named above); every changed record must parse" ;;
        2) fail "lint-envelope usage error (exit 2) -- the changed-record invocation is broken" ;;
        *) fail "lint-envelope exited $lint_rc on the changed records (expected 0, 3, 1 or 2) -- treating as a failure" ;;
    esac

    # scan over the changed records: no home-directory path may arrive.
    # scan is line-matched and has no field or exception flag, so the deck
    # exception here is the single line carrying the top-level `deck` field,
    # matched against the value the envelope itself declares.
    scan_rc=0
    klt env-provenance scan --format json "${changed_records[@]}" > "$scan_report" || scan_rc=$?
    case "$scan_rc" in
        0) echo "records-json: scan: ${#changed_records[@]} changed record(s) name no home directory" ;;
        3)
            if ! python3 - "$scan_report" <<'PY'
import json, sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
residual = []
excepted = 0
for f in report.get("files", []):
    name = f.get("file", "")
    deck = None
    deck_line = None
    if name.endswith(".envelope.json"):
        try:
            with open(name, encoding="utf-8") as fh:
                deck = json.load(fh).get("deck")
            if isinstance(deck, str):
                with open(name, encoding="utf-8") as fh:
                    for i, line in enumerate(fh, 1):
                        if line.strip().startswith('"deck"'):
                            deck_line = i
                            break
        except Exception:
            deck = None
            deck_line = None
    for x in f.get("leaks", []):
        match = x.get("match", "")
        if (name.endswith(".envelope.json") and isinstance(deck, str)
                and deck_line is not None
                and x.get("line") == deck_line
                and match.startswith(deck) and match.rstrip('",') == deck):
            excepted += 1
            continue
        residual.append((name, x.get("kind"), x.get("line"), match))
if residual:
    for name, kind, line, match in residual:
        print(f"  {name}:{line} :: {kind} = {match}", file=sys.stderr)
    print(f"scan: {len(residual)} leak(s) remain after the decision-0011 "
          f"deck exception ({excepted} excepted deck line(s))", file=sys.stderr)
    sys.exit(3)
print(f"scan: only the decision-0011 deck exception applied "
      f"({excepted} excepted deck line(s)); nothing else")
PY
            then
                fail "a record added or changed by this range carries a home-directory path (leaks above). Decision 0011 (spec/decisions/0011-record-path-hygiene-gate.md) gates new records on scan: a run record cites a deck by provenance.deck.content_hash, never by path"
            fi
            ;;
        1) fail "scan could not read a record added or changed by this range (named above)" ;;
        *) fail "scan exited $scan_rc on the changed records (expected 0, 3 or 1) -- treating as a failure" ;;
    esac

    echo "records-json: changed-record gate: PASS -- ${#changed_records[@]} changed record(s) clean under lint-envelope (class-2 prefixes) and scan; deck exception per decision 0011 where it applied"
    exit 0
fi

# --- default mode: the whole-set validity gate ---

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
    3) echo "records-json: ${#records[@]} record(s) valid; lint-envelope reported absolute-path findings (pass -- frozen history per decision 0011, enforced forward-only by --changed)" ;;
    1) fail "a committed JSON record does not parse (named above); every tracked record must parse" ;;
    2) fail "lint-envelope usage error (exit 2) -- the record set invocation is broken" ;;
    *) fail "lint-envelope exited $rc (expected 0, 3, 1 or 2) -- treating as a failure" ;;
esac
