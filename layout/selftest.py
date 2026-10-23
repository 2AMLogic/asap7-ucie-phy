#!/usr/bin/env python3
"""Self-test for check_pads.py: positive control plus negative controls.

Builds pads-only GDS files from the committed maps with klayout.db and runs the
checker on them. Exits 0 only if every expected outcome occurs.
"""
import os
import sys
import tempfile

import klayout.db as db

import check_pads

HERE = os.path.dirname(os.path.abspath(__file__))
PAD_UM = 25.0
TOP = "PADS"


def build(entries, path, mutate=None, subcell=False):
    ly = db.Layout()
    ly.dbu = 0.001
    top = ly.create_cell(TOP)
    host = ly.create_cell("SUB") if subcell else top
    if subcell:
        top.insert(db.CellInstArray(host.cell_index(), db.Trans()))
    li = ly.layer(check_pads.LAYER, check_pads.DATATYPE)
    half = round(PAD_UM / 2 / ly.dbu)
    pts = [(e["x"], e["y"]) for e in entries]
    if mutate:
        pts = mutate(pts)
    for x, y in pts:
        host.shapes(li).insert(db.Box(x - half, y - half, x + half, y + half))
    ly.write(path)


def run(name, entries, mpath, tmp, mutate, want, key=None, subcell=False):
    g = os.path.join(tmp, name + ".gds")
    build(entries, g, mutate, subcell)
    rec = check_pads.check(g, TOP, mpath)
    ok = rec["status"] == want
    if ok and key:
        ok = len(rec.get(key, [])) == 1
    print("  %-14s status=%-4s (want %s)%s %s" % (name, rec["status"], want,
          " %s=%d" % (key, len(rec.get(key, []))) if key else "", "ok" if ok else "FAIL"))
    if key and rec.get(key):
        print("    ", rec[key][0])
    return ok


def main():
    allok = True
    with tempfile.TemporaryDirectory() as tmp:
        for sl in ("target", "fallback"):
            mpath = os.path.join(HERE, "bump_map_%s.csv" % sl)
            entries = check_pads.read_map(mpath, 0.001)
            print("slice %s: %d bumps" % (sl, len(entries)))
            n = len(entries)
            mv = lambda d: (lambda p: [(x, y + d) if i == 5 else (x, y) for i, (x, y) in enumerate(p)])
            allok &= run(sl + "_good", entries, mpath, tmp, None, "pass")
            allok &= run(sl + "_sub", entries, mpath, tmp, None, "pass", subcell=True)
            allok &= run(sl + "_move1", entries, mpath, tmp, mv(1), "pass")
            allok &= run(sl + "_move2", entries, mpath, tmp, mv(2), "fail", "misplaced")
            allok &= run(sl + "_missing", entries, mpath, tmp, lambda p: p[:5] + p[6:], "fail", "missing")
            allok &= run(sl + "_extra", entries, mpath, tmp, lambda p: p + [(200000, -5000)], "fail", "extra")
            allok &= run(sl + "_empty", entries, mpath, tmp, lambda p: [], "fail")
        bad = check_pads.check(os.path.join(tmp, "nonexistent.gds"), TOP, mpath)
        print("  unreadable     status=%s" % bad["status"])
        allok &= bad["status"] == "fail"
    print("selftest: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
