#!/usr/bin/env bash
# Post-route, SDF-annotated cocotb loopback (T1 item 7, digital): the same
# test_slice bench as run.sh, but against layout/slice_routed.v (the routed gate
# netlist) with layout/slice_routed.sdf applied through `klt functional-verification`
# options.sdf. 16 lanes only: the netlist is the synthesized N=16 slice.
#   functional_verification_sdf.sh [--pdk-archive <lambdapdk tarball>]
# Exit 0 iff every test passes. The report is written either way (a timing-driven
# failure is a legitimate recorded result). The ASAP7 cell Verilog models come
# from the pinned lambdapdk archive (design/lambdapdk.py) and are unpacked into
# the gitignored verification/.sdf-models/; nothing from the archive is committed.
# Test clock: the bench's CLK_PS in test_slice.py (10 ns), not the 0.25 ns STA target.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/.."
PIN="$HERE/tool-versions.txt"
KLT_PIN="$(cat "$ROOT/.github/klt-version")"
pin() { sed -n "s/^$1=//p" "$PIN"; }
die() { echo "functional_verification_sdf.sh: $*" >&2; exit 2; }
ARCHIVE=""; [ "${1:-}" = "--pdk-archive" ] && ARCHIVE="${2:?--pdk-archive needs a path}"

check() { [ "$2" = "$(pin "$1")" ] || die "$1 is '$2' but $PIN pins '$(pin "$1")'; not changing host tools."; }
check iverilog "$(iverilog -V 2>/dev/null | head -1 | sed -n 's/.*version \([0-9.]*\).*/\1/p')"

SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT
python3 -I - "$ROOT" "$HERE/.sdf-models" "$ARCHIVE" "$SCRATCH" <<'PY'
import importlib.util, pathlib, sys, tarfile
root, dest, given, scratch = map(pathlib.Path, sys.argv[1:5])
spec = importlib.util.spec_from_file_location("lambdapdk", root / "design" / "lambdapdk.py")
L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
archive = L.fetch(scratch, str(given) if str(given) else None)
dest.mkdir(exist_ok=True)
prefix = L.ROOT + "libs/asap7sc7p5t_rvt/verilog/"
with tarfile.open(archive) as tar:
    for m in tar:
        if m.name.startswith(prefix) and m.name.endswith(".v"):
            (dest / pathlib.Path(m.name).name).write_bytes(tar.extractfile(m).read())
PY

export SEED="${SEED:-$(pin seed)}" LANES=16 NEG_CONTROL=0 SUMMARY_PATH="$SCRATCH/summary.json"
out="$HERE/functional-verification-sdf.report.json"
set +e
uvx --from "klayout-tools[functional-verification]==$KLT_PIN" klt functional-verification \
  "$HERE/functional-verification-sdf.json" -o "$SCRATCH/run" --format json >"$out" 2>"$SCRATCH/err"
krc=$?
set -e
# klt writes a refusal (no verdict) to stderr; keep it as the record, scratch paths redacted.
[ -s "$out" ] || sed "s|$SCRATCH|<scratch>|g; s|$(cd "$ROOT" && pwd)/||g" "$SCRATCH/err" >"$out"
echo "klt exit=$krc report=$out"
if [ -n "${KEEP_RUN:-}" ]; then cp -r "$SCRATCH/run" "$KEEP_RUN"; fi
exit $krc
