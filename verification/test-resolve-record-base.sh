#!/usr/bin/env bash
# Hermetic selftest for verification/resolve-record-base.sh: throwaway git
# repos under a temp dir, no network, no runner assumptions. The fixture is
# A <- B (HEAD of the fixture checkout) plus a side-branch commit C that is
# visible in the checkout but NOT an ancestor of B -- exactly the shape the
# resolver must refuse for a merge_group run.
#
# Covered contract:
#   pull_request: the PR base wins (even when a push "before" is also set)
#   pull_request: the literal "null" base falls through to the push before
#   push:         the "before" SHA is the base
#   push:         the zero SHA falls back to HEAD^ (unchanged behavior)
#   workflow_dispatch / any other event: falls back to HEAD^
#   merge_group:  a good base_sha is used
#   merge_group:  empty / "null" / zero / nonexistent / non-ancestor base
#                 each fails with ::error:: -- never a HEAD^ fallback

set -u

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
resolver="$script_dir/resolve-record-base.sh"

pass=0
fail=0

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

repo="$tmp/repo"
git init -q -b main "$repo"
git -C "$repo" -c user.name=t -c user.email=t@example.com commit --allow-empty -qm A
A="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" -c user.name=t -c user.email=t@example.com commit --allow-empty -qm B
B="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" -c user.name=t -c user.email=t@example.com checkout -qb side "$A"
git -C "$repo" -c user.name=t -c user.email=t@example.com commit --allow-empty -qm C
C="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" checkout -q "$B"

zero_sha="0000000000000000000000000000000000000000"
nonexistent="0123456789abcdef0123456789abcdef01234567"

# expect_base DESC EXPECTED_SHA VAR=VALUE...  -> resolver must print EXPECTED_SHA
expect_base() {
    local desc="$1" expected="$2"
    shift 2
    local out rc
    out="$(cd "$repo" && env "$@" bash "$resolver" 2>"$tmp/err")"
    rc=$?
    if [ "$rc" -eq 0 ] && [ "$out" = "$expected" ]; then
        pass=$((pass + 1))
        echo "ok: $desc"
    else
        fail=$((fail + 1))
        echo "FAIL: $desc (rc=$rc, got '${out:-<empty>}', want '$expected')"
        sed 's/^/      stderr: /' "$tmp/err"
    fi
}

# expect_fail DESC VAR=VALUE... -> resolver must exit non-zero citing ::error::
expect_fail() {
    local desc="$1"
    shift
    local out rc
    out="$(cd "$repo" && env "$@" bash "$resolver" 2>"$tmp/err")"
    rc=$?
    if [ "$rc" -ne 0 ] && grep -q '::error::' "$tmp/err"; then
        pass=$((pass + 1))
        echo "ok: $desc"
    else
        fail=$((fail + 1))
        echo "FAIL: $desc (rc=$rc, expected non-zero exit with a ::error:: line)"
        sed 's/^/      stderr: /' "$tmp/err"
    fi
}

# --- events whose behavior is unchanged from the pre-merge-queue logic ---
expect_base "pull_request: PR base wins over the push before" \
    "$A" EVENT=pull_request PR_BASE_SHA="$A" PUSH_BEFORE="$B"
expect_base "pull_request: literal null PR base falls through to the push before" \
    "$A" EVENT=pull_request PR_BASE_SHA=null PUSH_BEFORE="$A"
expect_base "push: the before SHA is the base" \
    "$A" EVENT=push PUSH_BEFORE="$A"
expect_base "push: zero before falls back to HEAD^ (unchanged)" \
    "$A" EVENT=push PUSH_BEFORE="$zero_sha"
expect_base "workflow_dispatch: falls back to HEAD^ (unchanged)" \
    "$A" EVENT=workflow_dispatch
expect_base "other event: falls back to HEAD^ (unchanged)" \
    "$A" EVENT=release

# --- merge_group: the base comes from the event payload or the gate refuses ---
expect_base "merge_group: a good base_sha is used" \
    "$A" EVENT=merge_group MG_BASE="$A"
expect_fail "merge_group: empty base fails" \
    EVENT=merge_group MG_BASE=
expect_fail "merge_group: literal null base fails" \
    EVENT=merge_group MG_BASE=null
expect_fail "merge_group: zero base fails" \
    EVENT=merge_group MG_BASE="$zero_sha"
expect_fail "merge_group: nonexistent base fails" \
    EVENT=merge_group MG_BASE="$nonexistent"
expect_fail "merge_group: non-ancestor base fails" \
    EVENT=merge_group MG_BASE="$C"

echo "----"
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
