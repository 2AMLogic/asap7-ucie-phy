#!/usr/bin/env bash
# The committed-record gate. This is the single copy of that gate: both
# .github/workflows/signoff.yml and the attested records-json-valid check in
# manifests/t1-item10-inventory.json run this script (default mode). The
# record set is a rule, not a directory list, so a JSON record added anywhere
# is covered on arrival with no edit here.
#
# Three modes:
#
#   default             the whole tracked record set, validity-only: every
#                       committed record must be a valid JSON document stream
#                       (spec/decisions/0011-json-document-stream.md), and
#                       lint-envelope runs over the single-document partition
#                       with absolute-path findings tolerated -- they are the
#                       frozen history recorded in spec/decisions/0012-
#                       record-path-hygiene-gate.md, and #136/#20 own any
#                       edit or re-run of it (#166's contract).
#
#   --validate          the per-document stream walk only, no klt -- what
#                       check.sh consumes (stdlib-only scope).
#
#   --changed --base B  the forward-only gate (#172, decision 0012): every
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
# The validity check itself is a repo-local raw_decode walk, not klt: a
# document stream is valid committed evidence (decision
# 0011-json-document-stream) and klt cannot read one (filed upstream as
# 2AMLogic/klayout-tools#5887). klt's own exit contract, measured on the
# 0.9.1 and 0.9.2 pins:
#     0  all files valid, no absolute host paths
#     3  all files valid, absolute paths present (frozen history, decision
#        0012 in default mode; fatal in --changed mode)
#     1  some file unreadable or not valid JSON -- names the first and aborts
#     2  no FILE arguments (argparse usage error)
# `scan` shares the contract: 3 = leaks found, 0 = clean, 1 = unreadable.
#
# STREAM COVERAGE -- read before touching the changed-record klt leg. klt
# cannot read a document stream (#5887), so a stream record handed to it
# whole would be a hole: a newly changed stream record could carry an
# absolute path and never be seen. The --changed mode closes that by
# splitting each multi-document record into per-document temp files (exact
# byte slices, so content is unchanged) and remapping klt's diagnostics back
# to the real record path and line before the deck-exception filter judges
# them. Default mode stays findings-tolerant (validity-only) and hands klt
# the single-document partition only -- a stream record gets the per-document
# validity verdict there, and its absolute paths are covered forward-only by
# --changed.
#
# THE DECK EXCEPTION (decision 0012; 2AMLogic/klayout-tools#5709) -- read
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
# trusted in CI. The post-filter reconciles what it classified against the
# report's own schema_version and total (finding_count / leak_count) and
# refuses to pass on any mismatch, so a report-schema change under pin drift
# fails loudly instead of silently voiding the exception walk. The exception
# is self-limiting -- once klt stops writing the absolute path, the finding
# it admits no longer exists. REMOVE it when #5709 is closed and
# .github/klt-version is at or past the fix, verified by regenerating a DRC
# envelope and confirming the top-level deck is no longer absolute.
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
# --validate is the mode check.sh consumes: git and python3 only, never klt,
# so check.sh stays off the signoff toolchain. This script itself needs
# python3 in every mode (the per-document validity walk; the stream splitter
# and the decision-0012 deck-exception filter too in --changed) and klt in
# default and --changed modes; it fails loudly when either is missing rather
# than reporting a vacuous pass.

set -uo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || exit 1

# The class-2 prefix set (decision 0012): machine-wide tool install prefixes
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

# The per-document validity walk: reads the record set from stdin (one path
# per line) and prints "path<TAB>document-count" per file. Fails -- exit 3,
# this caller's own "invalid record" code -- on any file whose bytes are not
# a clean document stream: zero bytes, whitespace only, or a parse error
# before end of input are all invalid, and every failure names its file.
# One copy of the rule, used by every mode.
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

# The stream splitter (--changed mode only): reads multi-document record
# paths from $1/multi.txt (stdin carries the Python program below), writes
# each document as an exact byte slice into
# $1/<flattened>.doc<N>.json, and writes $1/mapping.json mapping each part
# path to {"path": <real record>, "offset": <1-based line where the document
# starts in the original>}. Prints one part path per line. The deck-exception
# filter remaps klt's diagnostics (file, line) back to the real record before
# judging them.
split_stream() {
    python3 - "$1" <<'PY'
import json, os, sys
tmp = sys.argv[1]
dec = json.JSONDecoder()
ws = " \t\n\r"
mapping = {}
parts = []
with open(os.path.join(tmp, "multi.txt"), encoding="utf-8") as list_fh:
    for line in list_fh:
        path = line.rstrip("\n")
        if not path.strip():
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        i = 0
        doc = 0
        while True:
            while i < len(text) and text[i] in ws:
                i += 1
            if i >= len(text):
                break
            start = i
            _, i = dec.raw_decode(text, i)
            doc += 1
            part = os.path.join(tmp, "%s.doc%d.json" % (path.replace("/", "__"), doc))
            with open(part, "w", encoding="utf-8") as fh:
                fh.write(text[start:i])
            offset = text.count("\n", 0, start) + 1
            mapping[part] = {"path": path, "offset": offset}
            parts.append(part)
with open(os.path.join(tmp, "mapping.json"), "w", encoding="utf-8") as fh:
    json.dump(mapping, fh)
for p in parts:
    print(p)
PY
}

# The decision-0012 deck-exception post-filter -- one copy for both klt legs
# of --changed mode. kind ($1) selects the leg: "lint-envelope" judges
# findings (field-matched), "scan" judges leaks (line-matched); $2 is that
# leg's klt JSON report, $3 the stream-split mapping ({} when none was
# split). Shared contract: refuse on a report schema_version other than 1 or
# on a finding_count/leak_count reconciliation mismatch; remap split-part
# file/line back to the real record; except exactly the top-level `deck`
# field of a changed *.envelope.json (the value the envelope itself
# declares); exit 3 on any residual, exit 0 when only the exception applied.
filter_deck_exception() {
    python3 - "$1" "$2" "$3" <<'PY'
import json, sys

kind = sys.argv[1]
report = json.load(open(sys.argv[2], encoding="utf-8"))
mapping = json.load(open(sys.argv[3], encoding="utf-8"))
scan = kind == "scan"
items, total_key = ("leaks", "leak_count") if scan else ("findings", "finding_count")
noun, unit = ("leak", "deck line") if scan else ("finding", "deck field")

def refuse(msg):
    print(f"{kind}: {msg} -- the report schema is not what this filter "
          f"expects; refusing to pass", file=sys.stderr)
    sys.exit(3)

def remap(name, line):
    m = mapping.get(name)
    if m is None or not isinstance(line, int):
        return name, line
    return (m["path"], m["offset"] + line - 1) if scan else (m["path"], line)

def deck_declared(name):
    # The top-level `deck` of a changed *.envelope.json as the envelope
    # itself declares it, plus (scan only) the 1-based line carrying the
    # field. raw_decode, not json.load: a record may be a document stream
    # (decision 0011-json-document-stream); the deck lives in doc 1.
    if not name.endswith(".envelope.json"):
        return None, None
    try:
        with open(name, encoding="utf-8") as fh:
            text = fh.read()
        deck = json.JSONDecoder().raw_decode(text)[0].get("deck")
        if scan and isinstance(deck, str):
            for i, line in enumerate(text.split("\n"), 1):
                if line.strip().startswith('"deck"'):
                    return deck, i
        return deck, None
    except Exception:
        return None, None

if report.get("schema_version") != 1:
    refuse(f"report schema_version {report.get('schema_version')!r} is not 1")
residual = []
excepted = 0
for f in report.get("files", []):
    name, _ = remap(f.get("file", ""), 0)
    deck, deck_line = deck_declared(name)
    for x in f.get(items, []):
        if scan:
            match = x.get("match", "")
            _, real_line = remap(f.get("file", ""), x.get("line"))
            is_deck = (isinstance(deck, str) and deck_line is not None
                       and real_line == deck_line
                       and match.startswith(deck) and match.rstrip('",') == deck)
            entry = (name, x.get("kind"), real_line, match)
        else:
            is_deck = (isinstance(deck, str) and x.get("field") == "deck"
                       and x.get("match") == deck)
            entry = (name, x.get("field"), x.get("match"))
        if is_deck:
            excepted += 1
        else:
            residual.append(entry)
total = report.get(total_key)
if total != excepted + len(residual):
    refuse(f"report accounting mismatch: klt reported {total!r} {noun}(s), "
           f"the filter classified {excepted + len(residual)}")
if residual:
    for e in residual:
        if scan:
            print(f"  {e[0]}:{e[2]} :: {e[1]} = {e[3]}", file=sys.stderr)
        else:
            print(f"  {e[0]} :: {e[1]} = {e[2]}", file=sys.stderr)
    print(f"{kind}: {len(residual)} {noun}(s) remain after the decision-0012 "
          f"deck exception ({excepted} excepted {unit}(s))", file=sys.stderr)
    sys.exit(3)
print(f"{kind}: only the decision-0012 deck exception applied "
      f"({excepted} excepted {unit}(s)); nothing else")
PY
}

VALIDATE_ONLY=0
CHANGED=0
BASE_SHA=""
case "${1:-}" in
    "") ;;
    --validate) VALIDATE_ONLY=1 ;;
    --changed)
        CHANGED=1
        [ "${2:-}" = "--base" ] || { echo "usage: $0 --changed --base <commit>" >&2; exit 2; }
        BASE_SHA="${3-}"
        [ -n "$BASE_SHA" ] || { echo "usage: $0 --changed --base <commit> (--base needs a commit)" >&2; exit 2; }
        ;;
    *) echo "usage: $0 [--validate | --changed --base <commit>]" >&2; exit 2 ;;
esac

mapfile -t records < <(record_set)
if [ "${#records[@]}" -eq 0 ]; then
    fail "the tracked JSON record set is empty -- the gate cannot run and must not look like it passed"
fi

command -v python3 >/dev/null 2>&1 || fail "python3 not found on PATH -- cannot run the per-document validity walk, the stream splitter or the decision-0012 deck-exception filter; a gate that cannot run must not look like one that passed"

# --- the per-document walk (every mode) ---

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

command -v klt >/dev/null 2>&1 || fail "klt not found on PATH -- install the pinned klayout-tools (.github/klt-version); a gate that cannot run must not look like one that passed"

# --- --changed --base B: the forward-only gate (#172, decision 0012) ---

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
        | grep -Fxf <(printf '%s\n' "${records[@]}"))
    if [ "${#changed_records[@]}" -eq 0 ]; then
        # A computed result, not a failure to compute: the four validations
        # above passed, the range names files, and none of them is a tracked
        # JSON record. Say so loudly and pass -- the whole-set validity gate
        # still covers every committed record.
        echo "records-json: changed-record gate: ${#range_files[@]} file(s) changed since ${BASE_SHA:0:12}, none is a tracked JSON record -- nothing to gate forward (the whole-set validity gate still ran)"
        exit 0
    fi
    echo "records-json: changed-record gate: ${#changed_records[@]} record(s) added or changed since ${BASE_SHA:0:12}: ${changed_records[*]}"

    # Partition the changed records by document count (the walk above already
    # counted every tracked record). Multi-document streams are split into
    # per-document temp files so klt sees every document (see STREAM
    # COVERAGE); the filter remaps diagnostics back to the real path/line.
    single_doc=()
    multi_doc=()
    for r in "${changed_records[@]}"; do
        n="$(awk -F'\t' -v p="$r" '$1 == p { print $2; exit }' <<<"$counts")"
        if [ "${n:-0}" -gt 1 ]; then
            multi_doc+=("$r")
        else
            single_doc+=("$r")
        fi
    done

    workdir="$(mktemp -d)"
    lint_report="$workdir/lint.json"
    scan_report="$workdir/scan.json"
    mapping="$workdir/mapping.json"
    trap 'rm -rf "$workdir"' EXIT
    printf '{}' > "$mapping"

    klt_inputs=("${single_doc[@]}")
    if [ "${#multi_doc[@]}" -gt 0 ]; then
        printf '%s\n' "${multi_doc[@]}" > "$workdir/multi.txt"
        mapfile -t parts < <(split_stream "$workdir")
        if [ "${#parts[@]}" -eq 0 ] || [ ! -s "$mapping" ]; then
            fail "the stream splitter produced no parts for ${multi_doc[*]} -- the klt leg would silently skip those documents, so refusing rather than guessing"
        fi
        klt_inputs+=("${parts[@]}")
    fi
    if [ "${#klt_inputs[@]}" -eq 0 ]; then
        fail "the klt leg has no inputs -- a gate with nothing to look at must not look like it passed"
    fi

    # lint-envelope over the changed records (streams as per-document parts),
    # with the class-2 prefix set.
    lint_args=(--format json)
    for p in "${CLASS2_PREFIXES[@]}"; do lint_args+=(--allow-prefix "$p"); done
    lint_rc=0
    klt env-provenance lint-envelope "${lint_args[@]}" "${klt_inputs[@]}" > "$lint_report" || lint_rc=$?
    case "$lint_rc" in
        0) echo "records-json: lint-envelope: ${#changed_records[@]} changed record(s) carry no absolute host path outside the declared prefixes" ;;
        3)
            # Post-filter the decision-0012 deck exception (with the stream
            # split remapped back to real paths), then judge the residual.
            # A finding survives unless it is exactly the top-level `deck`
            # field of a changed *.envelope.json whose value is the deck path
            # that envelope itself declares.
            if ! filter_deck_exception lint-envelope "$lint_report" "$mapping"; then
                fail "a record added or changed by this range carries an absolute host path (findings above). The frozen history of decision 0012 (spec/decisions/0012-record-path-hygiene-gate.md) is not reopened by this gate: write repo-relative references or a content hash, and cite a deck by provenance.deck.content_hash, never by path"
            fi
            ;;
        1) fail "a record added or changed by this range does not parse (named above); every changed record must parse" ;;
        2) fail "lint-envelope usage error (exit 2) -- the changed-record invocation is broken" ;;
        *) fail "lint-envelope exited $lint_rc on the changed records (expected 0, 3, 1 or 2) -- treating as a failure" ;;
    esac

    # scan over the changed records: no home-directory path may arrive.
    # scan is line-matched and has no field or exception flag, so the deck
    # exception here is the single line carrying the top-level `deck` field,
    # matched against the value the envelope itself declares (lines remapped
    # out of split parts first).
    scan_rc=0
    klt env-provenance scan --format json "${klt_inputs[@]}" > "$scan_report" || scan_rc=$?
    case "$scan_rc" in
        0) echo "records-json: scan: ${#changed_records[@]} changed record(s) name no home directory" ;;
        3)
            # Post-filter the decision-0012 deck exception for the scan leg
            # (line-matched -- see above), then judge the residual.
            if ! filter_deck_exception scan "$scan_report" "$mapping"; then
                fail "a record added or changed by this range carries a home-directory path (leaks above). Decision 0012 (spec/decisions/0012-record-path-hygiene-gate.md) gates new records on scan: a run record cites a deck by provenance.deck.content_hash, never by path"
            fi
            ;;
        1) fail "scan could not read a record added or changed by this range (named above)" ;;
        *) fail "scan exited $scan_rc on the changed records (expected 0, 3 or 1) -- treating as a failure" ;;
    esac

    echo "records-json: changed-record gate: PASS -- ${#changed_records[@]} changed record(s) clean under lint-envelope (class-2 prefixes) and scan; deck exception per decision 0012 where it applied"
    exit 0
fi

# --- default mode: the whole-set validity gate, then klt over the partition ---

# klt is fed the single-document partition only. COVERAGE NOTE: because klt
# cannot read a document stream (2AMLogic/klayout-tools#5887), a
# multi-document stream record gets the per-document validity verdict above
# only -- its absolute paths are NOT linted here. That is the settled
# validity-only contract of default mode (#166); the forward-only gate
# (--changed, decision 0012) covers every document of every changed record by
# splitting streams into per-document files and remapping the diagnostics
# back, so a changed record cannot use the stream format to smuggle an
# absolute path past this script.
partition="$(awk -F'\t' '$2 == 1 { print $1 }' <<<"$counts")"
if [ -z "$partition" ]; then
    fail "the single-document partition handed to lint-envelope is empty (every record is a stream) -- the klt leg would be a vacuous pass, so failing loudly"
fi
mapfile -t single_doc <<<"$partition"

rc=0
klt env-provenance lint-envelope "${single_doc[@]}" || rc=$?
case "$rc" in
    0) echo "records-json: clean: ${#records[@]} record(s) valid ($total_docs document(s) total), no absolute paths" ;;
    3) echo "records-json: ${#records[@]} record(s) valid ($total_docs document(s) total); lint-envelope reported absolute-path findings (pass -- frozen history per decision 0012, enforced forward-only by --changed)" ;;
    1) fail "a committed JSON record does not parse (named above); every tracked record must parse" ;;
    2) fail "lint-envelope usage error (exit 2) -- the record set invocation is broken" ;;
    *) fail "lint-envelope exited $rc (expected 0, 3, 1 or 2) -- treating as a failure" ;;
esac
