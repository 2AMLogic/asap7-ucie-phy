#!/usr/bin/env python3
"""Self-test for gen_cells_gds.py: positive control plus negative controls.

Checks the committed cell GDS against the netlists (cells, ports as pin labels,
device and layer counts), that --check passes, and that a drifted file and a
missing file are caught. Exits 0 only if every expected outcome occurs.
"""
import os
import re
import shutil
import sys
import tempfile

import klayout.db as db

import gen_cells_gds as g


def labels(path, top):
    ly = db.Layout()
    ly.read(path)
    cell = ly.cell(top)
    li = ly.find_layer(*g.M1)
    return sorted(s.text.string for s in cell.shapes(li).each() if s.is_text()), ly, cell


def main():
    ok = True

    def expect(what, cond):
        nonlocal ok
        print("  %-44s %s" % (what, "ok" if cond else "FAIL"))
        ok &= bool(cond)

    for name in g.CELL_NAMES:
        path = str(g.OUT / (name + ".gds"))
        ports, devs = g.read_cell(name)
        got, ly, cell = labels(path, name)
        expect(name + " pin labels = ports + rails", got == sorted(ports + ["VDD", "VSS"]))
        expect(name + " one gate stripe per device", cell.shapes(ly.find_layer(*g.GATE)).size() == len(devs))
        nfin = sum(d[2] for d in devs)
        expect(name + " one fin line per fin", cell.shapes(ly.find_layer(*g.FIN)).size() == nfin)
        expect(name + " one top cell", len(ly.top_cells()) == 1)
    # serializer boundary (spec section 4): TX has the 2:1 stages + driver, RX input stage + sampler
    txp, _ = g.read_cell("tx_cell")[0], None
    expect("tx_cell ports include sel1/sel2/pad", {"sel1", "sel2", "pad"} <= set(txp))
    expect("rx_cell ports include pad and 4 phases", {"pad", "ph[0]", "ph[3]"} <= set(g.read_cell("rx_cell")[0]))
    expect("--check on committed files exits 0", g.main(["--check"]) == 0)
    # negative controls on a scratch copy
    orig = g.OUT
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(orig, os.path.join(tmp, "cells"))
        g.OUT = g.pathlib.Path(tmp) / "cells"
        with open(g.OUT / "tx_cell.gds", "ab") as f:
            f.write(b"\0")
        expect("drifted file detected (exit 3)", g.main(["--check"]) == 3)
        os.remove(g.OUT / "rx_cell.gds")
        expect("missing file detected (exit 3)", g.main(["--check"]) == 3)
        g.main([])
        expect("regeneration restores (exit 0)", g.main(["--check"]) == 0)
        g.OUT = orig
    print("selftest: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
