#!/usr/bin/env python3
"""Self-test for regen.py's layer-map staging (stdlib only; run as `python3 -I layout/pnr/test_layermap.py`).

`pin_geometry_on_drawing` is what puts a top-level DEF `PINS` rectangle on its
metal's *drawing* purpose as well as its pin purpose, so the pin's own name label
coincides with a conductor and `klt lvs` can extract it as a top-level pin
(issue #149; mechanism and measurements in spec/asap7-bringup.md). These checks
pin the three properties the stream depends on: the entry is added for routing
metals, it is *not* added for via layers, and nothing in the pinned file is
removed or reordered.

Run with REGEN=<path> to exercise another copy of regen.py (used to confirm these
checks fail against the revision before the fix)."""
import importlib.util
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "regen", os.environ.get("REGEN") or HERE / "regen.py")
regen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regen)

# A faithful excerpt of the pinned lambdapdk base/apr/asap7.layermap: a routing
# metal with both purposes, a via layer with a PIN purpose and no NET purpose, the
# NAME pseudo-layer that places the pin's name label, and a commented-out line.
FIXTURE = (
    "# comment\n"
    "V3\t\tPIN\t\t35\t\t251\n"
    "M4\t\tNET\t        40\t\t0\n"
    "M4\t\tSPNET\t\t40\t\t0\n"
    "M4\t\tPIN\t\t40\t\t251\n"
    "M4\t\tLEFPIN\t\t40\t\t0\n"
    "M5\t\tNET\t\t50\t\t0\n"
    "M5\t\tPIN\t\t50\t\t251\n"
    "#M9\t\tNET\t\t90\t\t0\n"
    "#M9\t\tPIN\t\t90\t\t251\n"
    "NAME\t\tM4/PIN\t\t40\t\t251\n"
    "COMP\t\tALL\t\t101\t\t0\n"
)

fails = []


def expect(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


def entries(text):
    """{(lef_layer, purpose)} -> set of (gds_layer, gds_datatype) in `text`."""
    out = {}
    for line in text.splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) >= 4:
            out.setdefault((parts[0], parts[1]), set()).add((parts[-2], parts[-1]))
    return out


if not hasattr(regen, "pin_geometry_on_drawing"):
    print("FAIL regen.py has no pin_geometry_on_drawing: the DEF PINS rectangle "
          "is staged on the pin purpose only, so no top-level pin label names a "
          "conductor (issue #149)", file=sys.stderr)
    sys.exit(1)

staged = entries(regen.pin_geometry_on_drawing(FIXTURE))
original = entries(FIXTURE)

# The point of the change: the PINS rectangle also lands on the metal's own
# drawing layer/datatype, the one the ASAP7 extraction deck reads as a conductor.
expect("M4 PIN reaches the drawing purpose", ("40", "0") in staged[("M4", "PIN")], True)
expect("M5 PIN reaches the drawing purpose", ("50", "0") in staged[("M5", "PIN")], True)
# Derived from the file, not hardcoded: a via layer declares no NET purpose, so it
# must not acquire one -- V3 geometry on 35/0 would short routing to via cuts.
expect("V3 PIN is left alone", staged[("V3", "PIN")], {("35", "251")})
expect("commented-out M9 stays out", ("M9", "PIN") in staged, False)
# Purely additive: every original entry survives, and the label placement that
# puts the pin name on the deck's label layer is untouched.
for key, want in original.items():
    expect(f"{key[0]} {key[1]} preserved", want <= staged[key], True)
expect("pin purpose kept too", ("40", "251") in staged[("M4", "PIN")], True)
expect("NAME pseudo-layer untouched", staged[("NAME", "M4/PIN")], {("40", "251")})
expect("no entry dropped", set(original) <= set(staged), True)

# A map the transform cannot act on is a staging error, not a silent no-op: it
# would yield a stream with no extractable top-level pin at all.
try:
    regen.pin_geometry_on_drawing("V3\t\tPIN\t\t35\t\t251\n")
    expect("refuses a map with no NET+PIN pair", "returned", "SystemExit")
except SystemExit as e:
    expect("refusal names the cause", "NET+PIN" in str(e), True)

for f in fails:
    print("FAIL", f, file=sys.stderr)
print("test_layermap: %s" % ("FAIL" if fails else "PASS"))
sys.exit(1 if fails else 0)
