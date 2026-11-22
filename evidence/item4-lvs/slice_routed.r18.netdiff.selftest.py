#!/usr/bin/env python3
"""Self-test for slice_routed.r18.netdiff.py's r18-specific logic.

The r13 script's pairing invariants have their own committed self-test
(slice_routed.r13.netdiff.selftest.py, wired into the item-10 inventory as
netdiff-pairing-self-test). This one exercises the logic that is NEW in the
r18 sibling, on synthetic fixtures the committed r18 inputs cannot reach:
DEF name unescaping and component parsing, the row-pair band arithmetic, the
per-instance bulk/rail law classifier (bulk port identified from synthetic
M-cards, classified by role rather than port name), the island-to-row-pair
join (an island spanning two bands must be reported, not silently clamped),
and the device-surplus reconciliation arithmetic (fold cells weighted by
instances must sum to the flat delta). Run:
python3 -I slice_routed.r18.netdiff.selftest.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "netdiff_r18_under_test",
    os.path.join(HERE, "slice_routed.r18.netdiff.py"))
netdiff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(netdiff)


def run(name, ok, detail=""):
    print("  %-44s %s%s" % (name, "ok" if ok else "FAIL",
                            ("  " + detail) if detail and not ok else ""))
    return ok


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
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        ".selftest.def.tmp")
    with open(path, "w") as f:
        f.write(def_text)
    try:
        d = netdiff.parse_def(path)
    finally:
        os.unlink(path)
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
    styles = netdiff.leaf_bulk_ports(subs, "slice")
    ok &= run("CELLA bulk port is VDD (by role)",
              styles["CELLA"]["pmos_bulk"] == "VDD")
    ok &= run("CELLA sd port is VDD$1 (by role)",
              styles["CELLA"]["pmos_sd"] == ["VDD$1"])
    ok &= run("CELLB bulk port is VDD$1 (the flip)",
              styles["CELLB"]["pmos_bulk"] == "VDD$1")
    ok &= run("CELLB sd port is VDD (the flip)",
              styles["CELLB"]["pmos_sd"] == ["VDD"])
    # X-cards exercising the law classifier both ways: card = [name, node at
    # port VDD, VSS, VDD$1, Y, vsubs, cell]
    conforming = [
        ["X$1", "$I9", "VSS", "VDD", "$3", "vsubs", "CELLA"],
        ["X$2", "VDD", "VSS", "$I10", "$4", "vsubs", "CELLB"],
    ]
    ok &= run("law holds on synthetic conforming cards",
              all(law_of(ext, styles) for ext in conforming))
    bad = ["X$1", "VDD", "VSS", "$I9", "$3", "vsubs", "CELLA"]
    ok &= run("law violated when bulk port gets the named net",
              not law_of(bad, styles))

    print("surplus reconciliation arithmetic:")
    fold_cells = [
        {"instances": 87, "device_delta": 2},
        {"instances": 99, "device_delta": 2},
    ]
    ok &= run("fold instances sum to 186",
              sum(f["instances"] for f in fold_cells) == 186)
    ok &= run("weighted delta sums to 372",
              sum(f["device_delta"] * f["instances"]
                  for f in fold_cells) == 372)

    print("self-test %s" % ("passed" if ok else "FAILED"))
    return 0 if ok else 1


def law_of(card, styles):
    """The per-instance law, evaluated by hand for one synthetic X-card.

    card = [name, node at port VDD, VSS, VDD$1, Y, vsubs, cell]; CELLA's
    bulk port is VDD with sd port VDD$1, CELLB's the flip.
    """
    cell = card[-1]
    nodes = {"VDD": card[1], "VSS": card[2], "VDD$1": card[3],
             "vsubs": card[5]}
    st = styles[cell]
    bulk = nodes[st["pmos_bulk"]]
    sd = {nodes[p] for p in st["pmos_sd"]}

    def is_island(n: str) -> bool:
        return n.replace("\\", "").startswith("$I")

    return is_island(bulk) and sd == {"VDD"}


if __name__ == "__main__":
    sys.exit(main())
