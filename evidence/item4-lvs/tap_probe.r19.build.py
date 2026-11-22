#!/usr/bin/env python3
r"""Build the minimal well-tap probe GDS for the r19 attribution (issue #273).

Generic reproducer for the extraction gap filed at 2AMLogic/klayout-tools:
three library cells in one standard-cell row -- logic cell, TAPCELL, logic
cell -- with M1 followpin rails on both row boundaries and one supply label
per rail. The cells are taken from the committed routed stream
(layout/slice_routed.gds), which carries the library masters; nothing else
is drawn. The point under test: the TAPCELL's drawn tap (p+ diffusion in the
n-well, contacted through SDT/LISD/V0 to the M1 rail) is the only geometry
joining the row's n-well strip to the VDD rail, so what the extractor does
with it decides whether the PMOS bodies of the row resolve to VDD.

Expected (measured, committed as tap_probe.r19.extract.v): both logic
cells' PMOS-body ports land on ONE anonymous '$I' island net (the merged
well strip, joined across the TAPCELL's own well), while their PMOS
source/drain supply ports land on the labelled net VDD -- the drawn tap does
not join the well to the rail. The single-cell contrast
(evidence/item4-lvs/and2x2_probe.r9.request.json) matches, because there
options.finfet_bulk bridges per circuit; with more than one instance the
well strip is a top-level net no per-circuit join can reach.

Usage (pinned):
  uvx --with klayout==$(cat ../../.github/klayout-version) \
      --from klayout-tools==$(cat ../../.github/klt-version) \
      python3 tap_probe.r19.build.py <source-gds> <out-gds>
Then: klt extract <out-gds> --deck asap7 --top PROBE
Predictive-model geometry only (ASAP7); nothing here implies fabrication.
"""

from __future__ import annotations

import sys

import klayout.db as db

LOGIC = "AND2x2_ASAP7_75t_R"
TAP = "TAPCELL_ASAP7_75t_R"
#: ASAP7 RVT site pitch (0.324 um logic, 0.108 um tap/endcap width).
LOGIC_W_UM = 0.324
TAP_W_UM = 0.108


def main() -> int:
    src, out = sys.argv[1], sys.argv[2]
    ly = db.Layout()
    ly.read(src)
    if not ly.has_cell(LOGIC) or not ly.has_cell(TAP):
        sys.exit(f"FATAL: {src} does not carry the {LOGIC}/{TAP} masters")
    probe = ly.create_cell("PROBE")
    m1 = ly.find_layer(19, 0)
    m1_pin = ly.find_layer(19, 251)
    dbu = ly.dbu
    li = ly.cell_by_name(LOGIC)
    ti = ly.cell_by_name(TAP)

    probe.insert(db.CellInstArray(li, db.Trans(db.Point(0, 0))))
    probe.insert(db.CellInstArray(
        ti, db.Trans(db.Point(int(LOGIC_W_UM / dbu), 0))))
    probe.insert(db.CellInstArray(
        li, db.Trans(db.Point(int((LOGIC_W_UM + TAP_W_UM) / dbu), 0))))
    span = 2 * LOGIC_W_UM + TAP_W_UM

    def rail(y1, y2):
        probe.shapes(m1).insert(db.Box(
            int(-0.05 / dbu), int(y1 / dbu),
            int((span + 0.05) / dbu), int(y2 / dbu)))

    rail(-0.009, 0.009)     # bottom boundary: VSS rail
    rail(0.261, 0.279)      # top boundary (the well side): VDD rail
    probe.shapes(m1_pin).insert(db.Text(
        "VDD", db.Trans(db.Point(int((span / 2) / dbu), int(0.270 / dbu)))))
    probe.shapes(m1_pin).insert(db.Text(
        "VSS", db.Trans(db.Point(int((span / 2) / dbu), int(0.0 / dbu)))))

    keep = {LOGIC, TAP, "PROBE"}
    doom = [c.cell_index() for c in ly.each_cell() if c.name not in keep]
    for ci in doom:
        if ly.is_valid_cell_index(ci):
            ly.delete_cell(ci)
    ly.write(out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
