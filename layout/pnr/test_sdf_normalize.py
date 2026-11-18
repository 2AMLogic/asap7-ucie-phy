#!/usr/bin/env python3
"""Self-test for regen.py's SDF DATE normalization (stdlib only; run as `python3 -I layout/pnr/test_sdf_normalize.py`).

`sdf_without_date` is what lets `regen.py --check` gate the post-route SDF at
all: OpenROAD's STA writes `(DATE "...")` from the wall clock, so two regen
runs of the same stream differ only there (measured, issue #235), and the
comparison masks exactly that line while keeping every other byte gated. These
checks pin the properties the gate depends on: a DATE-only difference is
absorbed, a changed delay value still drifts, and a buffer with no DATE is
returned untouched. It also asserts exactly one substitution on the committed
`layout/slice_routed.sdf` -- the normalization may not touch any other line of
the file that `--check` compares.

Run with REGEN=<path> to exercise another copy of regen.py (used to confirm
these checks fail against a widened normalization)."""
import importlib.util
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "regen", os.environ.get("REGEN") or HERE / "regen.py")
regen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regen)

#: The committed SDF `--check` gates: the normalization may change only its
#: one DATE line, nothing else.
SDF = HERE.parent.parent / "layout" / "slice_routed.sdf"

# A faithful excerpt of the committed layout/slice_routed.sdf: the DELAYFILE
# header with its quoted fields (SDFVERSION, DESIGN, DATE, VENDOR, PROGRAM,
# VERSION, PROCESS) and unquoted ones, plus a CELL block with an INTERCONNECT
# and an IOPATH delay triple -- the values --check actually gates.
FIXTURE = (
    "(DELAYFILE\n"
    " (SDFVERSION \"3.0\")\n"
    " (DESIGN \"slice\")\n"
    " (DATE \"Wed Nov 18 03:30:21 2026\")\n"
    " (VENDOR \"Parallax\")\n"
    " (PROGRAM \"STA\")\n"
    " (VERSION \"3.1.0\")\n"
    " (DIVIDER .)\n"
    " (VOLTAGE 0.700::0.700)\n"
    " (PROCESS \"1.000::1.000\")\n"
    " (TEMPERATURE 25.000::25.000)\n"
    " (TIMESCALE 1ps)\n"
    " (CELL\n"
    "  (CELLTYPE \"slice\")\n"
    "  (INSTANCE)\n"
    "  (DELAY\n"
    "   (ABSOLUTE\n"
    "    (INTERCONNECT clk u_buf.A (0.012:0.018:0.024) (0.008:0.010:0.014))\n"
    "    (IOPATH A Z (0.100:0.110:0.120) (0.040:0.045:0.050))\n"
    "   )\n"
    "  )\n"
    " )\n"
    ")\n"
).encode()

fails = []


def expect(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


def expect_bytes_equal(name, got, want, window=48):
    """`expect` for whole-file bytes: a mismatch reports the first differing
    offset with a small window from each side, not both full reprs -- the
    committed SDF is ~2.5 MB, so one failed assertion must not bury the rest
    of the run under ~5 MB of repr (issue #250)."""
    if got == want:
        return
    n = min(len(got), len(want))
    i = next((k for k in range(n) if got[k] != want[k]), n)
    lo = max(0, i - window)
    hi = i + window
    fails.append(f"{name}: first difference at offset {i} "
                 f"(got {len(got)} B, want {len(want)} B)\n"
                 f"  got [{lo}:{hi}] = {got[lo:hi]!r}\n"
                 f"  want[{lo}:{hi}] = {want[lo:hi]!r}")


def with_date(text, date_line):
    """`text` with its DATE line replaced by `date_line`, computed locally.

    Deliberately independent of regen.py's own pattern: comparing its output
    against this single-line swap is what pins 'exactly one substitution'."""
    first = text.index(b"(DATE \"")
    end = text.index(b"\")", first) + len(b"\")")
    return text[:first] + date_line + text[end:]


MASKED = b"(DATE \"<regenerated>\")"

if not hasattr(regen, "sdf_without_date"):
    print("FAIL regen.py has no sdf_without_date: the SDF comparison has no "
          "DATE exception, so --check drifts on every run's wall-clock stamp "
          "(issue #235)", file=sys.stderr)
    sys.exit(1)

# The point of the change: two runs of the same stream differ only in the
# wall-clock DATE, and normalizing absorbs exactly that difference.
early = FIXTURE.replace(b"(DATE \"Wed Nov 18 03:30:21 2026\")",
                        b"(DATE \"Mon Mar  1 09:00:00 1999\")")
expect("DATE-only difference absorbed",
       regen.sdf_without_date(early), regen.sdf_without_date(FIXTURE))
expect("normalized form is the local DATE swap",
       regen.sdf_without_date(FIXTURE), with_date(FIXTURE, MASKED))
expect("normalization idempotent",
       regen.sdf_without_date(regen.sdf_without_date(FIXTURE)),
       regen.sdf_without_date(FIXTURE))

# The gate must keep gating: a changed delay value is the drift --check exists
# to catch, and masking the DATE line may not hide it.
late = FIXTURE.replace(b"(0.100:0.110:0.120)", b"(0.200:0.210:0.220)")
expect("changed delay still drifts",
       regen.sdf_without_date(late) != regen.sdf_without_date(FIXTURE), True)

# A buffer with no DATE is returned untouched: anything else the transform
# rewrites is a line --check gates byte-for-byte.
no_date = FIXTURE.replace(b" (DATE \"Wed Nov 18 03:30:21 2026\")\n", b"")
expect("buffer with no DATE untouched", regen.sdf_without_date(no_date), no_date)

# Exactly one substitution on the committed file: it carries exactly one DATE
# line, normalization swaps only that line and leaves every other byte alone.
data = SDF.read_bytes()
expect("committed SDF has exactly one DATE line", data.count(b"(DATE \""), 1)
expect_bytes_equal("committed SDF: exactly one substitution",
                   regen.sdf_without_date(data), with_date(data, MASKED))

for f in fails:
    print("FAIL", f, file=sys.stderr)
print("test_sdf_normalize: %s" % ("FAIL" if fails else "PASS"))
sys.exit(1 if fails else 0)
