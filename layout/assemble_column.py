#!/usr/bin/env python3
"""Assemble the lane column GDS (needs klayout.db; run as `python3`).

Instances the routed `slice` (layout/slice_routed.gds) and the drawn TX/RX cells
(layout/cells/*.gds) into one lane cell per bump-map lane index, and draws the
bump pads on Pad (stream layer 96/0) at the centres in layout/bump_map_target.csv.

    assemble_column.py            write layout/lane_column.gds
    assemble_column.py --check    exit 0 if the committed file matches, 3 if it drifts

Layout geometry only: a placement of committed streams under a bump grid. The
drawn cells are unrouted (see layout/README.md), the slice is not connected to
them, and no DRC or LVS result is claimed (spec section 3). ASAP7 is predictive.

Lane cell i is 45 um wide and 90 um tall (spec section 4 target row); its two
pads (TX at local y 0, RX at local y -45 um) are drawn inside the lane cell, so
the pad check must flatten the hierarchy. Lane i is placed at y = -90 um * i.
The clock lane (index 8) holds the clock cells only, no slice.
"""
import csv
import pathlib
import sys
import tempfile

import klayout.db as db

HERE = pathlib.Path(__file__).resolve().parent
MAP = HERE / "bump_map_target.csv"
OUT = HERE / "lane_column.gds"
TOP = "lane_column"
DBU_UM = 0.00025  # klt's asap7 deck requires this dbu
SLICE_DBU_UM = 0.001  # klt place-and-route output; converted on import
UM = 4000  # dbu per um
PITCH = 45 * UM
CELL_H = 2 * PITCH
CELL_W = 45 * UM
PAD = 25 * UM
PAD_LAYER = (96, 0)
CLOCK_INDEX = 8
LANES = 17

# Placement inside a lane cell, lower-left corners in dbu, local frame where the
# lane's TX pad is at (0, 0) and its RX pad at (0, -PITCH).
SLICE_AT = (-22 * UM, -66 * UM)
TX_AT = (2 * UM, -22 * UM)
RX_AT = (2 * UM, -50 * UM)
CLK_TX_AT = (-20 * UM, -40 * UM)
CLK_RX_AT = (2 * UM, -40 * UM)


def load(path, dbu_um):
    ly = db.Layout()
    ly.read(str(path))
    if abs(ly.dbu - dbu_um) > 1e-12:
        raise SystemExit("%s: dbu %g, expected %g" % (path, ly.dbu, dbu_um))
    return ly


def import_tree(dst, path, name, dbu_um=DBU_UM):
    src = load(path, dbu_um)
    top = src.cell(name)
    new = dst.create_cell(name)
    new.copy_tree(top)  # rescales physical geometry when dbu differs
    return new


def build():
    entries = list(csv.DictReader(open(MAP, newline="")))
    if len(entries) != 2 * LANES:
        raise SystemExit("bump map has %d rows, expected %d" % (len(entries), 2 * LANES))
    ly = db.Layout()
    ly.dbu = DBU_UM
    slice_c = import_tree(ly, HERE / "slice_routed.gds", "slice", SLICE_DBU_UM)
    cells = {n: import_tree(ly, HERE / "cells" / (n + ".gds"), n)
             for n in ("tx_cell", "rx_cell", "tx_clk_cell", "rx_clk_cell")}
    pad = ly.layer(*PAD_LAYER)

    def lane_cell(name, parts):
        c = ly.create_cell(name)
        for cell, (x, y) in parts:
            c.insert(db.CellInstArray(cell.cell_index(), db.Trans(x, y)))
        h = PAD // 2
        for y in (0, -PITCH):
            c.shapes(pad).insert(db.Box(-h, y - h, h, y + h))
        return c

    data = lane_cell("lane_cell", [(slice_c, SLICE_AT), (cells["tx_cell"], TX_AT),
                                   (cells["rx_cell"], RX_AT)])
    clk = lane_cell("lane_cell_clk", [(cells["tx_clk_cell"], CLK_TX_AT),
                                      (cells["rx_clk_cell"], CLK_RX_AT)])
    top = ly.create_cell(TOP)
    for i in range(LANES):
        c = clk if i == CLOCK_INDEX else data
        top.insert(db.CellInstArray(c.cell_index(), db.Trans(0, -CELL_H * i)))
    # The bump map is the authority: every pad drawn must sit on a map row.
    want = sorted((round(float(e["x_um"]) * UM), round(float(e["y_um"]) * UM)) for e in entries)
    got = []
    it = top.begin_shapes_rec(pad)
    while not it.at_end():
        c = it.shape().bbox().transformed(it.trans()).center()
        got.append((c.x, c.y))
        it.next()
    if sorted(got) != want:
        raise SystemExit("assembled pads do not match %s" % MAP.name)
    return ly


def write(ly, path):
    opt = db.SaveLayoutOptions()
    opt.format = "GDS2"
    opt.gds2_write_timestamps = False
    opt.gds2_libname = "asap7_ucie_phy_lane_column"
    ly.write(str(path), opt)


def main(argv):
    ly = build()
    if "--check" in argv:
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp) / OUT.name
            write(ly, t)
            if not OUT.is_file() or OUT.read_bytes() != t.read_bytes():
                print("drifted: %s" % OUT, file=sys.stderr)
                return 3
        return 0
    write(ly, OUT)
    bb = ly.cell(TOP).bbox()
    print("%s: %d lane cells, bbox %.3f x %.3f um" % (OUT.name, LANES, bb.width() * DBU_UM, bb.height() * DBU_UM))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
