#!/usr/bin/env python3
"""Self-test for gen_cells_gds.py: positive control plus negative controls.

Checks the committed cell GDS against the netlists (cells, ports as pin labels, well and
route presence through klt's asap7 extraction, so run it in the klt interpreter,
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
from klayout_tools.decks import get_extraction_deck
from klayout_tools.extract_finfet import FinFETGeometryError, extract_finfet_netlist

DECK = get_extraction_deck("asap7")


def extract(ly, name):
    """(device count, net count) of the klt asap7 extraction, or None if it refuses the geometry."""
    try:
        netlist, _ = extract_finfet_netlist(ly, ly.cell(name), DECK)
    except FinFETGeometryError:
        return None
    circuit = netlist.circuit_by_name(name)
    return sum(1 for _ in circuit.each_device()), sum(1 for _ in circuit.each_net())


def expected(name):
    ports, devs = g.read_cell(name)
    nets = {n for d in devs for n in d[3:6]} | set(ports)
    return len(devs), len(nets) + 2  # plus the synthesized vsubs and the well net


def without(path, name, layer):
    """The cell with every shape on `layer` removed."""
    ly = db.Layout()
    ly.read(path)
    ly.cell(name).shapes(ly.layer(*layer)).clear()
    return ly


def labels(path, top):
    ly = db.Layout()
    ly.read(path)
    cell = ly.cell(top)
    li = ly.find_layer(*g.M1_LABEL)
    return sorted(s.text.string for s in cell.shapes(li).each() if s.is_text()), ly, cell


def well_ok(ly, cell):
    well = db.Region(cell.begin_shapes_rec(ly.find_layer(*g.WELL)))
    pchan = (db.Region(cell.begin_shapes_rec(ly.find_layer(*g.ACTIVE)))
             & db.Region(cell.begin_shapes_rec(ly.find_layer(*g.PSEL)))
             & db.Region(cell.begin_shapes_rec(ly.find_layer(*g.GATE))))
    return not pchan.is_empty() and pchan.not_inside(well).is_empty()


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
        expect(name + " one gate stripe and one dummy per device", cell.shapes(ly.find_layer(*g.GATE)).size() == 2 * len(devs))
        nfin = sum(d[2] for d in devs)
        expect(name + " one fin line per fin", cell.shapes(ly.find_layer(*g.FIN)).size() == nfin)
        expect(name + " one top cell", len(ly.top_cells()) == 1)
        expect(name + " well encloses every PMOS channel", well_ok(ly, cell))
        expect(name + " extracts to the netlist's devices and nets", extract(ly, name) == expected(name))
        expect(name + " no well: extraction refused", extract(without(path, name, g.WELL), name) is None)
        for lay, what in ((g.M2, "M2 track"), (g.V1, "V1"), (g.V0, "V0"), (g.LIG, "LIG"), (g.SDT, "SDT")):
            if cell.shapes(ly.find_layer(*lay)).size():
                got = extract(without(path, name, lay), name)
                expect(name + " no " + what + ": extraction differs", got != expected(name))
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
