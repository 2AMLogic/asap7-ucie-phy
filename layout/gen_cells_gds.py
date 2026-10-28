#!/usr/bin/env python3
"""Generator of the drawn TX/RX cell GDS (needs klayout.db; run as `python3`).

Reads the device-level topology that design/gen_cells.py renders to
design/netlist/{tx,rx,tx_clk,rx_clk}_cell.sp and writes one GDS per cell to
layout/cells/. Each device is a footprint (fin, active, select, gate, M1
source/drain strips) placed in an NMOS row and a PMOS row between VSS and VDD
M1 rails; each boundary port is an M1 pin with a text label of the same name.

This is placement only. Nets are not routed, and ASAP7 grid, fin and design
rules are not checked until DRC (#19); LVS (#20) will not compare clean until
routing exists. Nothing here is sized, simulated or rated (spec/decisions/0003).

    gen_cells_gds.py            write layout/cells/*.gds
    gen_cells_gds.py --check    exit 0 if the committed files match, 3 if they drift
    gen_cells_gds.py --report   print each cell's bounding-box area against spec section 4
"""
import pathlib
import re
import sys
import tempfile

import klayout.db as db

HERE = pathlib.Path(__file__).resolve().parent
NETLIST = HERE.parent / "design" / "netlist"
OUT = HERE / "cells"
CELL_NAMES = ["tx_cell", "rx_cell", "tx_clk_cell", "rx_clk_cell"]

DBU_UM = 0.00025  # klt's asap7 deck requires this dbu
NM = 4  # dbu per nm; geometry below is in nm and scaled at insertion
# ASAP7 stream layers as read by klt's deck (klayout_tools/decks/asap7.drc).
FIN, ACTIVE, GATE, NSEL, PSEL, M1 = (2, 0), (11, 0), (7, 0), (12, 0), (13, 0), (19, 0)
FIN_PITCH, GATE_PITCH = 27, 54  # nm (all constants below, and the drawing arithmetic, are nm)
GATE_W, SD_W = 20, 34  # nm, footprint strip widths
RAIL_H, ROW_GAP, MARGIN = 60, 120, 54  # nm
PIN = 40  # nm, pin square
BUDGET_UM = {"target": (45.0, 90.0), "fallback": (55.0, 110.0)}  # spec section 4

DEV = re.compile(r"^(M\d+) (\S+) (\S+) (\S+) (\S+) (nmos_rvt|pmos_rvt) l=\S+ w=\S+ nfin=(\d+)$")


def read_cell(name):
    ports, devs = [], []
    for line in (NETLIST / f"{name}.sp").read_text().splitlines():
        if line.startswith(".subckt"):
            ports = [p for p in line.split()[2:] if p not in ("VDD", "VSS")]
        m = DEV.match(line)
        if m:
            devs.append((m.group(1), m.group(6), int(m.group(7)), m.group(2), m.group(3), m.group(4)))
    return ports, devs


def box(shapes, x0, y0, x1, y1):
    shapes.insert(db.Box(x0 * NM, y0 * NM, x1 * NM, y1 * NM))


def draw(name):
    ports, devs = read_cell(name)
    ly = db.Layout()
    ly.dbu = DBU_UM
    cell = ly.create_cell(name)
    lay = {k: ly.layer(*k) for k in (FIN, ACTIVE, GATE, NSEL, PSEL, M1)}
    n = lambda kind: [d for d in devs if d[1] == kind]
    cols = max(len(n("nmos_rvt")), len(n("pmos_rvt")))
    width = 2 * MARGIN + cols * GATE_PITCH
    fins = max(d[2] for d in devs)
    row_h = fins * FIN_PITCH
    # bottom to top: VSS rail, NMOS row, gap, PMOS row, VDD rail
    y_vss = 0
    y_n = RAIL_H + MARGIN
    y_p = y_n + row_h + ROW_GAP
    y_vdd = y_p + row_h + MARGIN
    height = y_vdd + RAIL_H
    pins = {}
    rails = [("VSS", y_vss), ("VDD", y_vdd)]
    for label, y in rails:
        box(cell.shapes(lay[M1]), 0, y, width, y + RAIL_H)
        cell.shapes(lay[M1]).insert(db.Text(label, db.Trans(width // 2 * NM, (y + RAIL_H // 2) * NM)))
    for kind, y0, sel in (("nmos_rvt", y_n, NSEL), ("pmos_rvt", y_p, PSEL)):
        for i, (dev, _, nfin, d, g, s) in enumerate(n(kind)):
            x = MARGIN + i * GATE_PITCH
            h = nfin * FIN_PITCH
            box(cell.shapes(lay[ACTIVE]), x, y0, x + GATE_PITCH, y0 + h)
            box(cell.shapes(lay[sel]), x, y0, x + GATE_PITCH, y0 + h)
            for f in range(nfin):
                yc = y0 + f * FIN_PITCH + FIN_PITCH // 2
                box(cell.shapes(lay[FIN]), x, yc - 3, x + GATE_PITCH, yc + 3)
            gx = x + (GATE_PITCH - GATE_W) // 2
            box(cell.shapes(lay[GATE]), gx, y0 - 10, gx + GATE_W, y0 + h + 10)
            box(cell.shapes(lay[M1]), x, y0, x + SD_W // 2, y0 + h)
            box(cell.shapes(lay[M1]), x + GATE_PITCH - SD_W // 2, y0, x + GATE_PITCH, y0 + h)
            for net in (d, g, s):
                if net in ports and net not in pins:
                    pins[net] = (x + GATE_PITCH // 2, y0 + h // 2)
    # any port with no device terminal found would be a netlist/generator mismatch
    missing = [p for p in ports if p not in pins]
    if missing:
        raise SystemExit(f"{name}: ports with no device terminal: {missing}")
    for p in ports:
        x, y = pins[p]
        box(cell.shapes(lay[M1]), x - PIN // 2, y - PIN // 2, x + PIN // 2, y + PIN // 2)
        cell.shapes(lay[M1]).insert(db.Text(p, db.Trans(x * NM, y * NM)))
    return ly


def write(ly, path):
    opt = db.SaveLayoutOptions()
    opt.format = "GDS2"
    opt.gds2_write_timestamps = False
    opt.gds2_libname = "asap7_ucie_phy_cells"
    ly.write(str(path), opt)


def area_rows():
    rows = []
    for name in CELL_NAMES:
        ly = draw(name)
        bb = ly.cell(name).bbox()
        w, h = bb.width() * ly.dbu, bb.height() * ly.dbu
        rows.append((name, w, h, w * h))
    return rows


def main(argv):
    if "--report" in argv:
        tw, th = BUDGET_UM["target"]
        fw, fh = BUDGET_UM["fallback"]
        print(f"lane cell budget: target {tw}x{th} um = {tw * th:.0f} um^2, "
              f"fallback {fw}x{fh} um = {fw * fh:.0f} um^2 (spec section 4)")
        for name, w, h, a in area_rows():
            print(f"{name}: {w:.3f} x {h:.3f} um = {a:.3f} um^2 "
                  f"({100 * a / (tw * th):.4f}% of target; geometric, bounding box only)")
        return 0
    check = "--check" in argv
    drift = 0
    OUT.mkdir(exist_ok=True)
    for name in CELL_NAMES:
        ly = draw(name)
        path = OUT / f"{name}.gds"
        if check:
            with tempfile.TemporaryDirectory() as tmp:
                t = pathlib.Path(tmp) / path.name
                write(ly, t)
                if not path.is_file() or path.read_bytes() != t.read_bytes():
                    print(f"drifted: {path}", file=sys.stderr)
                    drift += 1
        else:
            write(ly, path)
    return 3 if drift else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
