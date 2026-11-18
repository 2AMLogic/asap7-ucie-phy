#!/usr/bin/env bash
# Fail if WORK_PLAN.md's guide:plan-body region contains a line starting
# "_Generated:". The region is rendered by the Guide's render_plan_body, which
# emits no timestamp; such a line defeats the byte-for-byte "current" skip.
# Usage: check-work-plan-region.sh [path/to/WORK_PLAN.md]
set -euo pipefail

file="${1:-WORK_PLAN.md}"
start='<!-- guide:plan-body:start -->'
end='<!-- guide:plan-body:end -->'

[[ -f "$file" ]] || { echo "ERROR: $file not found" >&2; exit 2; }

hits=$(tr -d '\r' < "$file" | awk -v f="$file" -v s="$start" -v e="$end" '
  $0 == s { if (seen_s) dup = 1; seen_s = 1; inr = 1; next }
  $0 == e { seen_e = 1; inr = 0; next }
  inr && /^_Generated:/ { printf "%s:%d: %s\n", f, NR, $0; bad = 1 }
  END {
    if (!seen_s || !seen_e) { print "MARKERS_MISSING"; exit 0 }
    if (inr) { print "MARKERS_MISSING"; exit 0 }
  }')

if [[ "$hits" == *MARKERS_MISSING* ]]; then
  echo "ERROR: $file lacks a complete $start ... $end marker pair" >&2
  exit 2
fi
if [[ -n "$hits" ]]; then
  echo "ERROR: _Generated: line inside guide:plan-body region of $file:" >&2
  echo "$hits" >&2
  echo "render_plan_body never emits it; remove the line (see #262)." >&2
  exit 1
fi
echo "OK: no _Generated: line inside guide:plan-body region of $file"
