#!/usr/bin/env bash
# Hermetic selftest for the JSON stream walker inside
# verification/check-records-json.sh -- walk_stream and its validate_stream /
# split_stream wrappers, plus the fail-closed splitter leg of --changed.
# These are the checks #308 ran as throwaway scratch fixtures and PR #309
# landed; this file commits them (issue #324) so a byte-exactness regression
# in the splitter cannot land with CI green: the split leg only runs for
# *changed* multi-document records, and no committed check re-ran it.
#
# Covered contract:
#   sourcing        defines the walker functions with no working-directory
#                   side effect and without running the CLI (the
#                   BASH_SOURCE guard in check-records-json.sh)
#   validate_stream exact "path<TAB>document-count" lines; exit 3 on zero
#                   bytes, whitespace only, invalid UTF-8, a malformed
#                   trailing document (LF and CRLF) and a mixed
#                   valid+malformed batch
#   split_stream    byte-for-byte *.docN.json parts and the mapping.json
#                   path / 1-based source-line offset for LF and CRLF
#                   streams carrying 2-, 3- and 4-byte UTF-8, plus the #308
#                   CRLF fixture (18-byte doc 1, 2-byte doc 2); exit 3 with
#                   zero part files and no mapping.json on every invalid
#                   shape, including for the valid member of a mixed batch
#   --changed       a changed multi-document record reaches klt as exact
#                   per-document slices, and a non-zero splitter exit fails
#                   the gate closed ("the stream splitter failed") rather
#                   than passing with no parts
#
# Stdlib only: bash, git, python3 and a stubbed klt on PATH. No network, no
# runner assumptions, no real klayout-tools; everything lives under one
# mktemp -d removed on EXIT.

set -u

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate="$script_dir/check-records-json.sh"

pass=0
fail=0

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

ok() {
    pass=$((pass + 1))
    echo "ok: $1"
}

not_ok() {
    fail=$((fail + 1))
    echo "FAIL: $1"
}

assert_eq() {
    local desc="$1" got="$2" want="$3"
    if [ "$got" = "$want" ]; then
        ok "$desc"
    else
        not_ok "$desc (got '$got', want '$want')"
    fi
}

# --- sourcing: the walker functions only, no working-directory side effect ---

pre_pwd="$(pwd)"
# shellcheck disable=SC1090
. "$gate"
if [ "$(pwd)" = "$pre_pwd" ]; then
    ok "sourcing defines the walkers without moving the working directory"
else
    not_ok "sourcing moved the working directory to $(pwd)"
    cd "$pre_pwd" || exit 1
fi

# --- fixtures (written as raw bytes so multibyte and CRLF survive exactly) ---

fx="$tmp/fx"
expect="$tmp/expect"
mkdir -p "$fx" "$expect"
python3 - "$fx" "$expect" <<'PY'
import os
import sys

fx, expect = sys.argv[1], sys.argv[2]


def w(dirpath, name, data):
    with open(os.path.join(dirpath, name), "wb") as fh:
        fh.write(data)


# LF and CRLF streams whose documents carry 2-, 3- and 4-byte UTF-8
# sequences: the split slices must survive the multibyte boundaries.
docs = [b'{"s2": "\xc3\xa9"}',      # U+00E9, 2-byte
        b'{"s3": "\xe3\x81\x82"}',  # U+3042, 3-byte
        b'{"s4": "\xf0\x9f\x98\x80"}']  # U+1F600, 4-byte
for name, sep in (("lf_utf8", b"\n"), ("crlf_utf8", b"\r\n")):
    w(fx, name + ".json", sep.join(docs) + sep)
    for i, d in enumerate(docs, 1):
        w(expect, "%s.doc%d.bin" % (name, i), d)

# The #308 fixture: doc 1 is the 18-byte CRLF-indented object, doc 2 the
# bare {} -- the regression was the splitter emitting 16 of doc 1's 18 bytes.
n308 = [b'{\r\n  "value": 1\r\n}', b"{}"]
assert len(n308[0]) == 18 and len(n308[1]) == 2
w(fx, "crlf308.json", b"\r\n".join(n308) + b"\r\n")
for i, d in enumerate(n308, 1):
    w(expect, "crlf308.doc%d.bin" % i, d)

# Invalid shapes: exit 3 in both modes, no split artifacts.
w(fx, "bad_trail_lf.json", b'{"a": 1}\n{"b": ')
w(fx, "bad_trail_crlf.json", b'{"a": 1}\r\n{"b": ')
w(fx, "zero.json", b"")
w(fx, "ws_only.json", b" \n\t\r\n")
w(fx, "bad_utf8.json", b'{"a": "\xff\xfe"}')
w(fx, "mixed_ok.json", b'{"ok": 1}')
w(fx, "mixed_bad.json", b'{"bad": [')

# The --changed fixture repo's single-document record.
w(expect, "one.bin", b'{"single": true}\n')
PY

# --- validate_stream: exact document counts ----------------------------------

counts="$(cd "$fx" && printf '%s\n' \
    lf_utf8.json crlf_utf8.json crlf308.json mixed_ok.json | validate_stream)"
assert_eq "validate_stream counts the LF UTF-8 stream's documents" \
    "$(awk -F'\t' '$1 == "lf_utf8.json" { print $2 }' <<<"$counts")" "3"
assert_eq "validate_stream counts the CRLF UTF-8 stream's documents" \
    "$(awk -F'\t' '$1 == "crlf_utf8.json" { print $2 }' <<<"$counts")" "3"
assert_eq "validate_stream counts the #308 fixture as 2 documents" \
    "$(awk -F'\t' '$1 == "crlf308.json" { print $2 }' <<<"$counts")" "2"
assert_eq "validate_stream counts a single-document record" \
    "$(awk -F'\t' '$1 == "mixed_ok.json" { print $2 }' <<<"$counts")" "1"

# --- split_stream: byte-exact parts and the mapping contract -----------------

hex_of() {
    python3 -c 'import sys; sys.stdout.write(open(sys.argv[1], "rb").read().hex())' "$1"
}

map_get() { # DIR PART KEY -> the mapping.json value for that part
    python3 -c 'import json, sys
m = json.load(open(sys.argv[1]))
print(m[sys.argv[2]][sys.argv[3]])' "$1/mapping.json" "$2" "$3"
}

# split_case DESC FIXTURE N_OFFSETS... -- N offset args, one 1-based source
# line per document. Asserts the printed part list, byte-for-byte equality
# of every part against expect/FIXTURE.docN.bin, and mapping.json's path and
# offset for every part (including document 2).
split_case() {
    local desc="$1" fixture="$2"
    shift 2
    local offsets=("$@") d rc i part want_list=""
    d="$tmp/split_$fixture"
    mkdir -p "$d"
    printf '%s\n' "$fixture.json" > "$d/multi.txt"
    rc=0
    split_out="$(cd "$fx" && split_stream "$d")" || rc=$?
    assert_eq "$desc: splitter exits 0" "$rc" "0"
    for i in $(seq 1 "${#offsets[@]}"); do
        want_list+="$d/$fixture.json.doc$i.json"$'\n'
    done
    assert_eq "$desc: splitter prints one part path per document" \
        "$split_out" "${want_list%$'\n'}"
    for i in $(seq 1 "${#offsets[@]}"); do
        part="$d/$fixture.json.doc$i.json"
        if cmp -s "$part" "$expect/$fixture.doc$i.bin"; then
            ok "$desc: doc $i is a byte-exact slice of the original"
        else
            not_ok "$desc: doc $i differs from the original slice ($part)"
        fi
        assert_eq "$desc: mapping.json path for doc $i" \
            "$(map_get "$d" "$part" path)" "$fixture.json"
        assert_eq "$desc: mapping.json 1-based source line for doc $i" \
            "$(map_get "$d" "$part" offset)" "${offsets[i-1]}"
    done
}

split_case "LF stream with 2/3/4-byte UTF-8" lf_utf8 1 2 3
split_case "CRLF stream with 2/3/4-byte UTF-8" crlf_utf8 1 2 3
split_case "the #308 CRLF fixture" crlf308 1 4
assert_eq "#308 doc 1 slice is 18 bytes" \
    "$(wc -c < "$tmp/split_crlf308/crlf308.json.doc1.json" | tr -d ' ')" "18"
assert_eq "#308 doc 2 slice is 2 bytes" \
    "$(wc -c < "$tmp/split_crlf308/crlf308.json.doc2.json" | tr -d ' ')" "2"

# --- invalid shapes: exit 3 in both modes, zero parts, no mapping.json -------

# expect_invalid DESC FILE
expect_invalid() {
    local desc="$1" f="$2" d rc parts
    rc=0
    ( cd "$fx" && printf '%s\n' "$f" | validate_stream ) >/dev/null 2>"$tmp/err" || rc=$?
    assert_eq "validate_stream rejects $desc (exit 3)" "$rc" "3"
    d="$tmp/neg_$f"
    mkdir -p "$d"
    printf '%s\n' "$f" > "$d/multi.txt"
    rc=0
    ( cd "$fx" && split_stream "$d" ) >/dev/null 2>>"$tmp/err" || rc=$?
    assert_eq "split_stream rejects $desc (exit 3)" "$rc" "3"
    parts="$(find "$d" -name '*.doc*.json' 2>/dev/null | wc -l | tr -d ' ')"
    assert_eq "split_stream emits zero part files for $desc" "$parts" "0"
    if [ -e "$d/mapping.json" ]; then
        not_ok "split_stream wrote a mapping.json for $desc"
    else
        ok "split_stream writes no mapping.json for $desc"
    fi
}

expect_invalid "a malformed trailing document (LF)" bad_trail_lf.json
expect_invalid "a malformed trailing document (CRLF)" bad_trail_crlf.json
expect_invalid "a zero-byte record" zero.json
expect_invalid "a whitespace-only record" ws_only.json
expect_invalid "invalid UTF-8 bytes" bad_utf8.json

# A mixed batch: one valid + one malformed record fails the whole batch and
# suppresses every part, including the valid member's.
d="$tmp/neg_mixed"
mkdir -p "$d"
printf 'mixed_ok.json\nmixed_bad.json\n' > "$d/multi.txt"
rc=0
( cd "$fx" && printf '%s\n' mixed_ok.json mixed_bad.json | validate_stream ) \
    >/dev/null 2>>"$tmp/err" || rc=$?
assert_eq "validate_stream rejects a mixed valid+malformed batch (exit 3)" "$rc" "3"
rc=0
( cd "$fx" && split_stream "$d" ) >/dev/null 2>>"$tmp/err" || rc=$?
assert_eq "split_stream rejects a mixed valid+malformed batch (exit 3)" "$rc" "3"
parts="$(find "$d" -name '*.doc*.json' 2>/dev/null | wc -l | tr -d ' ')"
assert_eq "split_stream emits zero parts for a mixed batch (not even the valid member's)" \
    "$parts" "0"
if [ -e "$d/mapping.json" ]; then
    not_ok "split_stream wrote a mapping.json for a mixed batch"
else
    ok "split_stream writes no mapping.json for a mixed batch"
fi

# --- --changed: exact slices handed to klt, and the fail-closed splitter leg -
#
# A throwaway git repo whose verification/ is the real gate (its
# BASH_SOURCE-relative cd targets the fixture repo) and whose PATH carries a
# klt stub: a clean env-provenance verdict plus a log of every input file's
# exact bytes, so the test can prove what the splitter handed to klt.

repo="$tmp/repo"
git init -q -b main "$repo"
mkdir -p "$repo/verification" "$repo/data" "$tmp/bin"
cp "$gate" "$repo/verification/check-records-json.sh"

cat > "$tmp/bin/klt" <<'STUB'
#!/usr/bin/env python3
import os
import sys

with open(os.environ["KLT_STUB_LOG"], "a", encoding="utf-8") as out:
    for a in sys.argv[1:]:
        if os.path.isfile(a):
            with open(a, "rb") as fh:
                out.write("file\t%s\t%s\n" % (a, fh.read().hex()))
print('{"schema_version": 1, "finding_count": 0, "leak_count": 0, "files": []}')
STUB
chmod +x "$tmp/bin/klt"

echo "# fixture" > "$repo/README.md"
git -C "$repo" add -A
git -C "$repo" -c user.name=t -c user.email=t@example.com commit -qm base
base="$(git -C "$repo" rev-parse HEAD)"

python3 - "$repo" <<'PY'
import os
import sys

data = os.path.join(sys.argv[1], "data")
with open(os.path.join(data, "one.json"), "wb") as fh:
    fh.write(b'{"single": true}\n')
with open(os.path.join(data, "stream.json"), "wb") as fh:
    fh.write(b'{\r\n  "value": 1\r\n}\r\n{}\r\n')
PY
git -C "$repo" add -A
git -C "$repo" -c user.name=t -c user.email=t@example.com commit -qm records

# Passing case: a changed single-document record plus a changed
# multi-document stream, both clean.
stublog="$tmp/klt-stub.log"
: > "$stublog"
rc=0
( cd "$repo" && PATH="$tmp/bin:$PATH" KLT_STUB_LOG="$stublog" \
    bash verification/check-records-json.sh --changed --base "$base" ) \
    > "$tmp/chg.out" 2> "$tmp/chg.err" || rc=$?
assert_eq "--changed exits 0 on a clean changed set" "$rc" "0"
if grep -q "changed-record gate: PASS" "$tmp/chg.out"; then
    ok "--changed reports PASS over the split records"
else
    not_ok "--changed did not report PASS: $(cat "$tmp/chg.out" "$tmp/chg.err")"
fi

# stub_hex NEEDLE -> hex of the bytes klt received for the one logged input
# whose path contains NEEDLE (the log line is "file\t<path>\t<hex>"; part
# paths arrive as <workdir>/<flattened-record>.docN.json).
stub_hex() {
    grep -F "$1" "$stublog" | head -n 1 | cut -f3
}

assert_eq "klt receives the single-document record byte-for-byte" \
    "$(stub_hex "data/one.json")" "$(hex_of "$expect/one.bin")"
assert_eq "klt receives the #308 doc 1 slice byte-for-byte (18 bytes)" \
    "$(stub_hex "/data__stream.json.doc1.json")" "$(hex_of "$expect/crlf308.doc1.bin")"
assert_eq "klt receives the #308 doc 2 slice byte-for-byte (2 bytes)" \
    "$(stub_hex "/data__stream.json.doc2.json")" "$(hex_of "$expect/crlf308.doc2.bin")"

# Failing case: a non-zero splitter exit must fail --changed closed rather
# than pass with no parts. The gate resolves its workdir with mktemp -d
# between the whole-set validate_stream and split_stream, so a mktemp
# wrapper on PATH corrupts the changed stream record at exactly that point
# -- no test-only hook in the gate itself.
real_mktemp="$(command -v mktemp)"
mkdir -p "$tmp/bin2"
cat > "$tmp/bin2/mktemp" <<STUB
#!/usr/bin/env bash
out="\$("$real_mktemp" "\$@")" || exit \$?
printf '{"trailing": ' >> "$repo/data/stream.json"
printf '%s\n' "\$out"
STUB
chmod +x "$tmp/bin2/mktemp"

rc=0
( cd "$repo" && PATH="$tmp/bin2:$tmp/bin:$PATH" KLT_STUB_LOG="$stublog" \
    bash verification/check-records-json.sh --changed --base "$base" ) \
    > "$tmp/chg2.out" 2> "$tmp/chg2.err" || rc=$?
assert_eq "--changed exits 1 when the splitter fails" "$rc" "1"
if grep -q "the stream splitter failed" "$tmp/chg2.err"; then
    ok "--changed cites 'the stream splitter failed' on stderr"
else
    not_ok "--changed failed without citing the splitter: $(cat "$tmp/chg2.err")"
fi

echo "----"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
