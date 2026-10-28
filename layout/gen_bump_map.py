#!/usr/bin/env python3
"""Generate the committed bump map (spec section 3, decision 0002).

Conventions (recorded here and in layout/README.md):
  * One column: x = 0 um for every bump.
  * Bump k (k = 0 at the top) sits at y = -pitch * k um, so y decreases downward.
  * Each lane cell holds two bumps, TX then RX, top to bottom.
  * Lane cells run 0..N-1 top to bottom; the clock lane is the centre cell
    (index 8 of 17 for the target, 4 of 9 for the fallback). Data lanes d0..
    fill the remaining cells in order.
  * Signals: d<i>_tx, d<i>_rx, clk_tx, clk_rx. The CSV lane column is the
    lane-cell index.
  * x_um / y_um are written as %.3f so the file is byte-identical across runs
    and exact at 1 nm (the layouts use dbu 0.00025 um, 4 dbu = 1 nm).

This is a layout-evidence map, not a DRC artefact.
"""
import argparse
import csv
import os

SLICES = {
    "target": {"data_lanes": 16, "pitch_um": 45},
    "fallback": {"data_lanes": 8, "pitch_um": 55},
}


def build_map(slice_name):
    cfg = SLICES[slice_name]
    cells = cfg["data_lanes"] + 1
    clk_cell = cells // 2
    rows = []
    data = 0
    k = 0
    for lane in range(cells):
        if lane == clk_cell:
            names = ("clk_tx", "clk_rx")
        else:
            names = ("d%d_tx" % data, "d%d_rx" % data)
            data += 1
        for sig in names:
            rows.append((lane, sig, 0.0, -float(cfg["pitch_um"]) * k))
            k += 1
    return rows


def write_map(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["lane", "signal", "x_um", "y_um"])
        for lane, sig, x, y in rows:
            w.writerow([lane, sig, "%.3f" % (x + 0.0), "%.3f" % (y + 0.0)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slice", choices=sorted(SLICES), default="target")
    ap.add_argument("--out", help="output CSV (default layout/bump_map_<slice>.csv)")
    a = ap.parse_args()
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "bump_map_%s.csv" % a.slice)
    rows = build_map(a.slice)
    write_map(rows, out)
    print("wrote %s (%d bumps)" % (out, len(rows)))


if __name__ == "__main__":
    main()
