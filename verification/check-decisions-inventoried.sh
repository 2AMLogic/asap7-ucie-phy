#!/usr/bin/env bash
# Gate: every git-tracked spec/decisions/*.md record must be listed in the
# .hygiene array of manifests/t1-item10-inventory.json. The T1 item-10 envelope
# binds only the files listed there, so a decision record missing from the list
# is unbound -- it can change freely while the signoff job stays green (#319;
# omissions were caught after the fact in #141, #311 and #315).
#
# Exit 0: every tracked record is inventoried. Exit 1: at least one is not (each
# is printed as ::error::). Exit 2: usage or environment error (no jq, no
# inventory, no git checkout) -- never a vacuous pass.
#
# Test hooks (used by verification/test-check-decisions-inventoried.sh):
#   REPO_ROOT  checkout to inspect (default: the parent of this script's dir)
#   INVENTORY  inventory path relative to REPO_ROOT
#              (default: manifests/t1-item10-inventory.json)
set -euo pipefail

root="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
inventory="${INVENTORY:-manifests/t1-item10-inventory.json}"

command -v jq >/dev/null 2>&1 || { echo "::error::jq is required" >&2; exit 2; }
[[ -f "$root/$inventory" ]] || { echo "::error::inventory not found: $inventory" >&2; exit 2; }

if ! tracked="$(git -C "$root" ls-files -- 'spec/decisions/*.md')"; then
  echo "::error::git ls-files failed in $root" >&2
  exit 2
fi
if [[ -z "$tracked" ]]; then
  echo "::error::no tracked spec/decisions/*.md records found -- refusing a vacuous pass" >&2
  exit 2
fi

listed="$(jq -r '.hygiene[]' "$root/$inventory")"

missing=0
while IFS= read -r rec; do
  if ! grep -Fxq -- "$rec" <<<"$listed"; then
    echo "::error::$rec is not listed in .hygiene of $inventory (unbound by the item-10 envelope)"
    missing=$((missing + 1))
  fi
done <<<"$tracked"

if (( missing > 0 )); then
  echo "$missing decision record(s) missing from the item-10 inventory" >&2
  exit 1
fi
echo "ok: all $(wc -l <<<"$tracked") tracked decision records are in the item-10 inventory"
