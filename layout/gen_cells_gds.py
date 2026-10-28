#!/usr/bin/env python3
"""Generator of the drawn TX/RX cell GDS (needs klayout.db; run as `python3`).

Reads the device-level topology that design/gen_cells.py renders to
design/netlist/{tx,rx,tx_clk,rx_clk}_cell.sp and writes one GDS per cell to
layout/cells/. Each device is drawn (fin, active, select, gate, S/D trench
contact and LISD, gate LIG) in an NMOS row and a PMOS row between VSS and VDD M1
rails, under one well over the PMOS row. Each net is routed: V0 and M1 verticals
to an M2 track per net in the channel between the rows (V1), supplies to the M1
rails. Each boundary port is named by a text label on M1 (19/251).

ASAP7 grid, fin and design rules are not checked until DRC (#19), and the
extraction (#20) is whatever `klt lvs` reports, recorded as it comes. Nothing
here is sized, simulated or rated (spec/decisions/0003).

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
# ASAP7 stream layers as read by klt's deck (klayout_tools/decks/asap7.py).
WELL, FIN, GATE, ACTIVE, NSEL, PSEL = (1, 0), (2, 0), (7, 0), (11, 0), (12, 0), (13, 0)
LIG, LISD, V0, M1, M2, V1, SDT = (16, 0), (17, 0), (18, 0), (19, 0), (20, 0), (21, 0), (88, 0)
M1_LABEL = (19, 251)  # the deck reads net names from M1 text on 19/251, not 19/0
LAYERS = (WELL, FIN, GATE, ACTIVE, NSEL, PSEL, LIG, LISD, V0, M1, M2, V1, SDT, M1_LABEL)
FIN_PITCH = 27  # nm (all constants below, and the drawing arithmetic, are nm)
GATE_W, ACT_W, SD_W = 20, 108, 44  # nm: gate stripe, active island, source/drain side
SLOT = 36  # nm, M1 vertical pitch and M2 track pitch
WIRE = 18  # nm, M1/M2/V0/V1 drawn width
COL_PITCH = 6 * SLOT  # device pitch within a row; adjacent islands never abut
PMOS_SHIFT = 3 * SLOT  # PMOS row offset, so no M1 vertical of either row shares an x
RAIL_H, MARGIN, GATE_EXT, PAD_SZ, WELL_EN = 60, 54, 36, 24, 54  # nm
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
    """Place each device, then route every net: M1 verticals from the device
    terminals to an M2 track per net in the channel between the rows; VSS and
    VDD terminals go straight to their M1 rail."""
    ports, devs = read_cell(name)
    ly = db.Layout()
    ly.dbu = DBU_UM
    cell = ly.create_cell(name)
    sh = {k: cell.shapes(ly.layer(*k)) for k in LAYERS}
    rows = {"nmos_rvt": [d for d in devs if d[1] == "nmos_rvt"],
            "pmos_rvt": [d for d in devs if d[1] == "pmos_rvt"]}
    cols = max(len(r) for r in rows.values())
    width = 2 * MARGIN + cols * COL_PITCH + PMOS_SHIFT
    row_h = max(d[2] for d in devs) * FIN_PITCH
    # nets that need an M2 track: not a rail, and more than one terminal
    count = {}
    for _, _, _, d, g, s in devs:
        for net in (d, g, s):
            count[net] = count.get(net, 0) + 1
    tracks = sorted(n for n, c in count.items() if c > 1 and n not in ("VDD", "VSS"))
    y_n = RAIL_H + MARGIN
    y_ch = y_n + row_h + GATE_EXT + PAD_SZ  # channel floor
    y_p = y_ch + (len(tracks) + 1) * SLOT + GATE_EXT + PAD_SZ
    y_vdd = y_p + row_h + MARGIN
    height = y_vdd + RAIL_H
    ty = {n: y_ch + (i + 1) * SLOT for i, n in enumerate(tracks)}
    rail_y = {"VSS": (0, RAIL_H), "VDD": (y_vdd, y_vdd + RAIL_H)}
    for label, (y0, y1) in rail_y.items():
        box(sh[M1], 0, y0, width, y1)
        sh[M1_LABEL].insert(db.Text(label, db.Trans(width // 2 * NM, (y0 + y1) // 2 * NM)))
    # one well over the whole PMOS row (body net of every PMOS)
    box(sh[WELL], 0, y_p - WELL_EN, width, y_p + row_h + WELL_EN)
    stubs, labelled = {}, set()  # net -> [(x centre, y of its V0 centre)]
    for kind, y0, sel, shift in (("nmos_rvt", y_n, NSEL, 0), ("pmos_rvt", y_p, PSEL, PMOS_SHIFT)):
        up = kind == "nmos_rvt"  # NMOS wires leave upward to the channel, PMOS downward
        for i, (dev, _, nfin, d, g, s) in enumerate(rows[kind]):
            bx = MARGIN + shift + i * COL_PITCH
            h = nfin * FIN_PITCH
            box(sh[ACTIVE], bx, y0, bx + ACT_W, y0 + h)
            box(sh[sel], bx, y0, bx + ACT_W, y0 + h)
            for f in range(nfin):
                yc = y0 + f * FIN_PITCH + FIN_PITCH // 2
                box(sh[FIN], bx, yc - 3, bx + ACT_W, yc + 3)
            gx = bx + SD_W
            box(sh[GATE], gx, y0 - GATE_EXT, gx + GATE_W, y0 + h + GATE_EXT)
            terms = ((s, bx + SLOT // 2, "sd"), (g, bx + 3 * SLOT // 2, "g"), (d, bx + 5 * SLOT // 2, "sd"))
            for net, xc, role in terms:
                x0, x1 = xc - WIRE // 2, xc + WIRE // 2
                if role == "sd":
                    sx0 = bx if xc < gx else gx + GATE_W
                    box(sh[LISD], sx0 + 2, y0, sx0 + SD_W - 2, y0 + h)
                    box(sh[SDT], sx0 + 4, y0 + 2, sx0 + SD_W - 4, y0 + h - 2)
                    vy = y0 + 4  # V0 at the bottom of the diffusion
                else:
                    # gate contact in the stripe's extension, on the channel side
                    ly0 = y0 + h + 6 if up else y0 - 6 - PAD_SZ
                    box(sh[LIG], gx, ly0, gx + GATE_W, ly0 + PAD_SZ)
                    vy = ly0 + (PAD_SZ - WIRE) // 2
                box(sh[V0], x0, vy, x1, vy + WIRE)
                yv = vy + WIRE // 2
                if net in rail_y:
                    if (net == "VSS") != up:
                        raise SystemExit(f"{name}: {dev} {kind} terminal on {net} is not routable by rail")
                    ry = RAIL_H // 2 if net == "VSS" else y_vdd + RAIL_H // 2
                    box(sh[M1], x0, min(yv, ry) - WIRE // 2, x1, max(yv, ry) + WIRE // 2)
                elif net in ty:
                    ya, yb = sorted((yv, ty[net]))
                    box(sh[M1], x0, ya - WIRE // 2, x1, yb + WIRE // 2)
                    box(sh[V1], x0, ty[net] - WIRE // 2, x1, ty[net] + WIRE // 2)
                    stubs.setdefault(net, []).append(xc)
                else:  # single-terminal net: a short M1 pad
                    box(sh[M1], x0, yv - WIRE // 2, x1, yv + WIRE // 2 + SLOT)
                if net in ports and net not in labelled:
                    labelled.add(net)
                    sh[M1_LABEL].insert(db.Text(net, db.Trans(xc * NM, yv * NM)))
    for net, xs in stubs.items():
        box(sh[M2], min(xs) - WIRE // 2, ty[net] - WIRE // 2, max(xs) + WIRE // 2, ty[net] + WIRE // 2)
    missing = [p for p in ports if p not in labelled]
    if missing:
        raise SystemExit(f"{name}: ports with no device terminal: {missing}")
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
