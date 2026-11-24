#!/usr/bin/env bash
# Hermetic selftest for verification/check-decisions-inventoried.sh: a throwaway
# git repo, no network. Covers: all inventoried -> 0; a tracked record absent
# from .hygiene -> 1 naming it; no tracked records -> 2 (no vacuous pass); a
# missing inventory -> 2.
set -u
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate="$script_dir/check-decisions-inventoried.sh"
pass=0; fail=0
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
git init -q -b main "$repo"
mkdir -p "$repo/spec/decisions" "$repo/manifests"
: > "$repo/spec/decisions/0001-a.md"
: > "$repo/spec/decisions/0002-b.md"
echo '{"hygiene":["spec/decisions/0001-a.md","spec/decisions/0002-b.md"]}' > "$repo/manifests/t1-item10-inventory.json"
git -C "$repo" add -A
git -C "$repo" -c user.name=t -c user.email=t@example.com commit -qm init

check() { # name expected_rc [expected_stdout_substring]
  local name="$1" want="$2" sub="${3:-}" out rc
  out="$(REPO_ROOT="$repo" bash "$gate" 2>&1)"; rc=$?
  if [[ "$rc" == "$want" && ( -z "$sub" || "$out" == *"$sub"* ) ]]; then
    pass=$((pass + 1)); echo "ok   $name"
  else
    fail=$((fail + 1)); echo "FAIL $name (rc=$rc want=$want): $out"
  fi
}

check "all inventoried passes" 0

: > "$repo/spec/decisions/9999-x.md"
git -C "$repo" add spec/decisions/9999-x.md
check "tracked record missing from inventory fails naming it" 1 "spec/decisions/9999-x.md"

git -C "$repo" rm -qf spec/decisions/9999-x.md
check "after removal passes again" 0

git -C "$repo" rm -qf spec/decisions/0001-a.md spec/decisions/0002-b.md
check "no tracked records refuses vacuous pass" 2

git -C "$repo" reset -q --hard HEAD
mv "$repo/manifests/t1-item10-inventory.json" "$tmp/inv.bak"
check "missing inventory is an error" 2
mv "$tmp/inv.bak" "$repo/manifests/t1-item10-inventory.json"

echo "$pass passed, $fail failed"
[[ "$fail" == 0 ]]
