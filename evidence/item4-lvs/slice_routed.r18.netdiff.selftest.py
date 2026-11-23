#!/usr/bin/env python3
"""Self-test for slice_routed.r18.netdiff.py's r18-specific logic.

The r13 script's pairing invariants have their own committed self-test
(slice_routed.r13.netdiff.selftest.py, wired into the item-10 inventory as
netdiff-pairing-self-test). This one exercises the logic that is NEW in the
r18 sibling, on synthetic fixtures the committed r18 inputs cannot reach,
by calling the production top-level helpers themselves (r13's
anchor_pair/require_injective precedent: a re-implementation in here could
not fail when the production logic is mutated): DEF name unescaping and
component parsing, the row-pair band arithmetic, the per-instance bulk/rail
law classifier (check_bulk_rail_law; bulk port identified from synthetic
M-cards, classified by role rather than port name), the island-to-row-pair
join (join_islands_to_rows; an island spanning two bands must be reported,
not silently clamped), and the device-surplus reconciliation arithmetic
(reconcile_device_surplus; fold cells weighted by instances must sum to the
flat delta). Run: python3 -I slice_routed.r18.netdiff.selftest.py
"""
import collections
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "netdiff_r18_under_test",
    os.path.join(HERE, "slice_routed.r18.netdiff.py"))
netdiff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(netdiff)
r13 = netdiff._load_r13()

T = "slice"  # the extract's top subckt name; fixtures namespace nodes under it


def run(name, ok, detail=""):
    print("  %-56s %s%s" % (name, "ok" if ok else "FAIL",
                            ("  " + detail) if detail and not ok else ""))
    return ok


def parse_def_text(def_text):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "fixture.def")
        with open(path, "w") as f:
            f.write(def_text)
        return netdiff.parse_def(path)


def main() -> int:
    ok = True
    print("DEF name unescaping:")
    cases = [
        (r"g_lane\[0\].u_tx/_11_", "g_lane[0].u_tx/_11_"),
        (r"_06_", "_06_"),
        (r"a\[3\]", "a[3]"),
        (r"\g_lane\[1\].u_rx/_2_", "g_lane[1].u_rx/_2_"),
    ]
    for given, want in cases:
        got = netdiff.unescape_def_name(given)
        ok &= run(f"unescape {given!r}", got == want, f"got {got!r}")

    print("DEF component and row parsing:")
    def_text = (
        "VERSION 5.8 ;\n"
        "UNITS DISTANCE MICRONS 1000 ;\n"
        "DIEAREA ( 0 0 ) ( 100 100 ) ;\n"
        "ROW ROW_0 site 100 200 N DO 4 BY 1 STEP 54 0 ;\n"
        "ROW ROW_1 site 100 470 FS DO 4 BY 1 STEP 54 0 ;\n"
        "ROW ROW_2 site 100 740 N DO 4 BY 1 STEP 54 0 ;\n"
        "COMPONENTS 3 ;\n"
        "    - u1 CELL_A + PLACED ( 120 200 ) N ;\n"
        "    - g_lane\\[0\\].u_tx/_11_ CELL_B + SOURCE DIST + FIXED "
        "( 174 470 ) FS ;\n"
        "    - u3 CELL_A + PLACED ( 120 740 ) N ;\n"
        "END COMPONENTS\n")
    d = parse_def_text(def_text)
    ok &= run("units read", d["units"] == 1000)
    ok &= run("three components parsed", len(d["components"]) == 3)
    ok &= run("escaped name resolved",
              "g_lane[0].u_tx/_11_" in d["components"])
    ok &= run("three rows sorted", [r["y"] for r in d["rows"]] ==
              [200, 470, 740])

    print("row-pair band arithmetic:")
    ok &= run("N row origin -> pair 0",
              netdiff.row_pair_of(200, d["rows"]) == 0)
    ok &= run("FS row above -> same pair 0",
              netdiff.row_pair_of(470, d["rows"]) == 0)
    ok &= run("next N row -> pair 1",
              netdiff.row_pair_of(740, d["rows"]) == 1)

    print("leaf bulk/rail role classification:")
    subs = {
        "slice": {"ports": ["VDD", "VSS", "Y"], "xcards": [], "mcards": []},
        "CELLA": {"ports": ["VDD", "VSS", "VDD$1", "Y", "vsubs"],
                  "xcards": [], "mcards": [
                      # d g s b model -- pmos bulk on VDD, source on VDD$1
                      "M$1 $5 B VDD$1 VDD pmos_rvt L=0.02U W=0.054U".split(),
                      "M$2 VDD$1 A $5 VDD pmos_rvt L=0.02U W=0.054U".split(),
                  ]},
        "CELLB": {"ports": ["VSS", "Y", "VDD", "VDD$1", "vsubs"],
                  "xcards": [], "mcards": [
                      # d g s b model -- pmos bulk on VDD$1, drain on VDD
                      "M$1 $4 B Y VDD$1 pmos_rvt L=0.02U W=0.162U".split(),
                      "M$2 VDD A1 $4 VDD$1 pmos_rvt L=0.02U W=0.162U".split(),
                  ]},
    }
    styles = netdiff.leaf_bulk_ports(subs, T)
    ok &= run("CELLA bulk port is VDD (by role)",
              styles["CELLA"]["pmos_bulk"] == "VDD")
    ok &= run("CELLA sd port is VDD$1 (by role)",
              styles["CELLA"]["pmos_sd"] == ["VDD$1"])
    ok &= run("CELLB bulk port is VDD$1 (the flip)",
              styles["CELLB"]["pmos_bulk"] == "VDD$1")
    ok &= run("CELLB sd port is VDD (the flip)",
              styles["CELLB"]["pmos_sd"] == ["VDD"])

    print("per-instance bulk/rail law (production classifier):")

    def law_inst(idx, cell, vdd, vdd1):
        # conn keyed by folded port name; values are (top, node) pairs as
        # the extract parser produces
        return {"idx": idx, "base": cell, "cell": cell,
                "conn": {"vdd": vdd, "vdd$1": vdd1, "vss": (T, "VSS"),
                         "y": (T, "$1"), "vsubs": (T, "vsubs")}}

    law_insts = [
        # CELLA: bulk port VDD on the island, S/D port VDD$1 on the rail
        law_inst(0, "CELLA", (T, "\\$I7"), (T, "VDD")),
        # CELLB: the port-name flip -- S/D port VDD on the rail, bulk port
        # VDD$1 on the island
        law_inst(1, "CELLB", (T, "VDD"), (T, "\\$I8")),
        # CELLA with the bulk port on the named rail: law broken
        law_inst(2, "CELLA", (T, "VDD"), (T, "VDD")),
        # CELLB with the S/D port on an island: law broken the other way
        law_inst(3, "CELLB", (T, "\\$I9"), (T, "\\$I10")),
    ]
    law, viol = netdiff.check_bulk_rail_law(law_insts[:2], styles, T,
                                            r13.fold)
    ok &= run("law holds on both port-name flips",
              law == collections.Counter({(True, True): 2}) and not viol)
    law, viol = netdiff.check_bulk_rail_law(law_insts, styles, T, r13.fold)
    ok &= run("law violated when bulk port gets the named net",
              law[(False, True)] == 1)
    ok &= run("law violated when an S/D port sits on an island",
              law[(True, False)] == 1)
    ok &= run("violations sampled with cell and nodes",
              [v["idx"] for v in viol] == [2, 3]
              and viol[0]["cell"] == "CELLA"
              and viol[0]["bulk_node"] == "VDD"
              and viol[1]["sd_nodes"] == ["\\$I9"])

    print("island-to-row-pair join (production helper):")
    join_def = (
        "VERSION 5.8 ;\n"
        "UNITS DISTANCE MICRONS 1000 ;\n"
        "DIEAREA ( 0 0 ) ( 100 100 ) ;\n"
        "ROW ROW_0 site 100 200 N DO 4 BY 1 STEP 54 0 ;\n"
        "ROW ROW_1 site 100 470 FS DO 4 BY 1 STEP 54 0 ;\n"
        "ROW ROW_2 site 100 740 N DO 4 BY 1 STEP 54 0 ;\n"
        "ROW ROW_3 site 100 1010 FS DO 4 BY 1 STEP 54 0 ;\n"
        "COMPONENTS 4 ;\n"
        "    - u1 CELLA + PLACED ( 120 200 ) N ;\n"
        "    - u2 CELLA + PLACED ( 120 740 ) N ;\n"
        "    - u3 CELLB + PLACED ( 174 470 ) FS ;\n"
        "    - u4 CELLB + PLACED ( 120 200 ) N ;\n"
        "END COMPONENTS\n")
    jd = parse_def_text(join_def)
    join_insts = [{"idx": i, "base": c, "cell": c, "conn": {}}
                  for i, c in enumerate(
                      ["CELLA", "CELLA", "CELLB", "CELLB", "CELLA"])]
    full_members = {
        (T, "\\$IA"): [(0, "vdd"), (1, "vdd")],
        (T, "\\$IB"): [(2, "vdd$1"), (3, "vdd$1")],
        (T, "\\$IC"): [(4, "vdd")],
    }
    islands = {node: collections.Counter(p for _, p in members)
               for node, members in full_members.items()}
    rev_map = {0: "u1", 1: "u2", 2: "u3", 3: "u4", 4: "u_ghost"}
    irows, imembers, icells, unresolved = netdiff.join_islands_to_rows(
        islands, full_members, rev_map, join_insts, jd)
    ok &= run("island spanning two bands reported as two row pairs",
              irows["\\$IA"] == {0, 1}, "got %r" % (irows.get("\\$IA"),))
    ok &= run("single-band island joins to one row pair",
              irows["\\$IB"] == {0} and imembers["\\$IB"] == ["u3", "u4"])
    ok &= run("unresolved DEF name counted, not joined",
              unresolved == 1 and "\\$IC" not in irows
              and imembers.get("\\$IC", []) == [])
    ok &= run("island cells counted over full membership",
              icells["\\$IA"] == collections.Counter({"CELLA": 2})
              and icells["\\$IC"] == collections.Counter({"CELLA": 1}))

    print("surplus reconciliation (production helper):")

    def dev(model, d_, g, s, b):
        return ["M$1", d_, g, s, b, model, "L=0.02U", "W=0.081U"]

    rc_subs = {
        "slice": {"ports": ["VDD", "VSS", "Y"], "xcards": [], "mcards": []},
        "MATCH": {"ports": ["VDD", "VSS", "Y"], "xcards": [], "mcards": [
            dev("nmos_rvt", "a", "b", "c", "VSS"),
            dev("pmos_rvt", "VDD", "g", "s", "VDD"),
        ]},
        # the CDL folds this cell's stacks: the extract draws the nmos
        # series stack three times and the pmos twice
        "FOLD": {"ports": ["VDD", "VSS", "Y"], "xcards": [], "mcards": [
            dev("nmos_rvt", "a", "b", "c", "VSS"),
            dev("nmos_rvt", "a2", "b2", "c2", "VSS"),
            dev("nmos_rvt", "a3", "b3", "c3", "VSS"),
            dev("pmos_rvt", "VDD", "g", "s", "VDD"),
            dev("pmos_rvt", "VDD", "g2", "s2", "VDD"),
        ]},
        "GHOST": {"ports": ["VDD", "VSS", "Y"], "xcards": [], "mcards": []},
    }
    counts = collections.Counter({"MATCH": 3, "FOLD": 2})
    cdl = {"MATCH": (1, 1), "FOLD": (1, 1)}
    flat_layout, flat_cdl, fold_cells, fold_insts, fold_delta = \
        netdiff.reconcile_device_surplus(rc_subs, counts, cdl)
    ok &= run("flat layout devices weighted by instances",
              flat_layout == 2 * 3 + 5 * 2)
    ok &= run("flat CDL devices weighted by instances",
              flat_cdl == 2 * 3 + 2 * 2)
    ok &= run("surplus equals the weighted fold delta",
              flat_layout - flat_cdl == 6 and fold_delta == 6
              and fold_insts == 2)
    ok &= run("fold cell recorded with per-polarity counts",
              fold_cells == [{"cell": "FOLD", "layout_nmos": 3,
                              "cdl_nmos": 1, "layout_pmos": 2, "cdl_pmos": 1,
                              "instances": 2, "device_delta": 3}])
    caught = None
    try:
        netdiff.reconcile_device_surplus(
            rc_subs, collections.Counter({"GHOST": 1}), cdl)
    except SystemExit as e:
        caught = str(e)
    ok &= run("leaf missing from the CDL table hard-fails",
              caught is not None and "GHOST" in caught, repr(caught))

    print("self-test %s" % ("passed" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
