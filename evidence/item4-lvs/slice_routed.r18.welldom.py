#!/usr/bin/env python3
r"""r18 trace, well-domain half: via-aware geometry census of the routed
stream's supply delivery, complementing slice_routed.r18.netdiff.py.

The netlist census (netdiff) measures the extract's top-level supply domain
with the deck's own extraction; this script measures the GEOMETRY directly,
independently of the deck's connect decisions, to answer the question the
extract cannot: is the remaining VDD fragmentation a property of the drawn
stream (rails or straps genuinely disjoint) or of the extraction (drawn
connectivity the deck does not model)?

Method: the M1..M6 metal stack of layout/slice_routed.gds, flattened, with
V1..V5 bridging consecutive metals where a via cut overlaps both -- the same
via-aware rule slice_routed.r13.trace_geometry.py used for M2..M6, extended
down to M1 and driven by a spatial index so the full stack runs in one pass.
Connected components are computed by union-find over merged per-layer
polygons; nothing outside the metal stack participates (in particular the
well layer never joins a metal, which is the deck's own rule and the point
of the measurement). The well layer (1/0) is censused separately as flat
merged components.

Layer numbers are the pinned asap7 deck's (klayout_tools/decks/asap7.py,
LAYER_NAMES): M1 19/0 .. M6 60/0, V1 21/0, V2 25/0, V3 35/0, V4 45/0,
V5 55/0, well 1/0. dbu 0.00025 um.

Self-checks: the script hard-fails unless the committed r18 figures are
recovered -- 161 top-level M1 followpin rails, all 80 VDD-pitch rails in the
component carrying the VDD label on M6.pin and all 81 VSS-pitch rails in the
VSS one (zero orphan rails: the metal delivery grid is connected), exactly 80
well components, each spanning the full core width, and the two labels on
distinct components. A silent geometry regression fails instead of reporting
zeros.

Usage (pinned, like trace_geometry):
  uvx --with klayout==$(cat ../../.github/klayout-version) \
      --from klayout-tools==$(cat ../../.github/klt-version) \
      python3 slice_routed.r18.welldom.py <gds>
Writes one JSON object to stdout. Every figure is a tool result against the
predictive ASAP7 model; nothing here implies fabrication.
"""

from __future__ import annotations

import collections
import sys

import klayout.db as db

METALS = {"M1": (19, 0), "M2": (20, 0), "M3": (30, 0), "M4": (40, 0),
          "M5": (50, 0), "M6": (60, 0)}
VIAS = {"V1": (21, 0), "V2": (25, 0), "V3": (35, 0), "V4": (45, 0),
        "V5": (55, 0)}
WELL = (1, 0)
M6_PIN = (60, 251)

#: the two supply labels the committed stream draws on M6.pin (klt
#: place-and-route writes one text per primary supply net; measured).
VDD_LABEL = ("VDD", 11.88, 1.808)
VSS_LABEL = ("VSS", 11.88, 1.424)

CELL = 4000  # spatial-index cell in dbu (1 um)


class DisjointSet:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def region(ly, top, layer):
    li = ly.find_layer(*layer)
    r = db.Region()
    if li is None:
        return r
    it = top.begin_shapes_rec(li)
    while not it.at_end():
        s = it.shape()
        if s.is_polygon:
            r.insert(s.polygon.transformed(it.trans()))
        elif s.is_box:
            r.insert(s.box.transformed(it.trans()))
        elif s.is_path:
            r.insert(s.path.polygon.transformed(it.trans()))
        it.next()
    return r


def component_of_point(polys, merged_m6, ds, x_um, y_um, dbu):
    p = db.Point(int(x_um / dbu), int(y_um / dbu))
    for i in merged_m6:
        if polys[i][1].bbox().contains(p):
            return ds.find(i)
    return None


def main() -> int:
    gds = sys.argv[1]
    ly = db.Layout()
    ly.read(gds)
    top = ly.top_cell()
    dbu = ly.dbu

    metals = {n: region(ly, top, l) for n, l in METALS.items()}
    vias = {n: region(ly, top, l) for n, l in VIAS.items()}
    well = region(ly, top, WELL)

    ds = DisjointSet()
    polys = {}
    pid = 0
    merged = {n: [] for n in METALS}
    for n, r in metals.items():
        for p in r.merged().each():
            polys[pid] = (n, p)
            merged[n].append(pid)
            pid += 1

    grid: dict[tuple, list] = collections.defaultdict(list)
    for i, (n, p) in polys.items():
        b = p.bbox()
        for gx in range(b.left // CELL, (b.right // CELL) + 1):
            for gy in range(b.bottom // CELL, (b.top // CELL) + 1):
                grid[(gx, gy)].append(i)

    def near(p):
        b = p.bbox()
        out = set()
        for gx in range((b.left - CELL) // CELL, (b.right + CELL) // CELL + 1):
            for gy in range((b.bottom - CELL) // CELL,
                            (b.top + CELL) // CELL + 1):
                out.update(grid.get((gx, gy), ()))
        return out

    for vn, vr in vias.items():
        lo = "M" + vn[1]
        hi = "M" + str(int(vn[1]) + 1)
        for vp in vr.merged().each():
            vreg = db.Region([vp])
            cand = [i for i in near(vp)
                    if polys[i][0] in (lo, hi)
                    and not vreg.interacting(db.Region([polys[i][1]])).is_empty()]
            for x in cand[1:]:
                ds.union(cand[0], x)

    # top-level followpin rails: the stream's own M1 shapes (not cells')
    li_m1 = ly.find_layer(*METALS["M1"])
    rails = []
    for sh in top.shapes(li_m1).each():
        b = sh.bbox()
        rails.append(b)

    vdd_comp = component_of_point(polys, merged["M6"], ds,
                                  VDD_LABEL[1], VDD_LABEL[2], dbu)
    vss_comp = component_of_point(polys, merged["M6"], ds,
                                  VSS_LABEL[1], VSS_LABEL[2], dbu)

    rail_class = []
    for b in sorted(rails, key=lambda b: b.bottom):
        c = db.Point((b.left + b.right) // 2, (b.bottom + b.top) // 2)
        comp = None
        for i in merged["M1"]:
            if polys[i][1].bbox().contains(c):
                comp = ds.find(i)
                break
        rail_class.append("VDD" if comp == vdd_comp else
                          "VSS" if comp == vss_comp else "OTHER")

    well_comps = []
    for p in well.merged().each():
        b = p.bbox()
        well_comps.append({"left_um": round(b.left * dbu, 3),
                           "bottom_um": round(b.bottom * dbu, 3),
                           "right_um": round(b.right * dbu, 3),
                           "top_um": round(b.top * dbu, 3),
                           "area_um2": round(p.area() * dbu * dbu, 3)})

    # --- self-checks against the committed r18 figures -----------------------
    seq_runs = [(k, len(list(g))) for k, g in
                __import__("itertools").groupby(rail_class)]
    checks = {
        "161 top-level M1 rails": len(rails) == 161,
        "80 rails in the VDD-labelled component":
            rail_class.count("VDD") == 80,
        "81 rails in the VSS-labelled component":
            rail_class.count("VSS") == 81,
        "zero orphan rails": rail_class.count("OTHER") == 0,
        "rails alternate VSS/VDD from the bottom":
            [k for k, _ in seq_runs[:4]] == ["VSS", "VDD", "VSS", "VDD"]
            and len(seq_runs) == 161,
        "labels on distinct components":
            vdd_comp is not None and vss_comp is not None
            and vdd_comp != vss_comp,
        "80 well components": len(well_comps) == 80,
        "every well component spans the full core width":
            len({(w["left_um"], w["right_um"]) for w in well_comps}) == 1,
        "well components are one row tall":
            all(0.25 <= w["top_um"] - w["bottom_um"] <= 0.29
                for w in well_comps),
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        sys.exit("FATAL: self-checks failed: " + "; ".join(failed))

    out = {
        "script": "slice_routed.r18.welldom.py",
        "consumes": ["layout/slice_routed.gds"],
        "method": "via-aware M1..M6 connected components (V1..V5 bridge "
                  "consecutive metals on cut overlap; the well layer never "
                  "joins a metal -- the deck's own rule, and the point of "
                  "the measurement); well layer censused as flat merged "
                  "components",
        "labels": {"VDD": {"layer": "60/251", "x_um": VDD_LABEL[1],
                           "y_um": VDD_LABEL[2]},
                   "VSS": {"layer": "60/251", "x_um": VSS_LABEL[1],
                           "y_um": VSS_LABEL[2]}},
        "rails": {
            "top_level_m1_rails": len(rails),
            "in_vdd_component": rail_class.count("VDD"),
            "in_vss_component": rail_class.count("VSS"),
            "orphan": rail_class.count("OTHER"),
            "statement": "every followpin rail of both nets reaches the "
                         "labelled strap component through the drawn via "
                         "stack: the metal power delivery grid is connected",
        },
        "well": {
            "components": len(well_comps),
            "total_area_um2": round(sum(w["area_um2"] for w in well_comps), 1),
            "width_um": round(well_comps[0]["right_um"] -
                              well_comps[0]["left_um"], 3),
            "heights_um": sorted({round(w["top_um"] - w["bottom_um"], 3)
                                  for w in well_comps}),
            "statement": "the wells form 80 disjoint full-width strips, one "
                         "per DEF row pair; the only path from a strip to "
                         "the VDD rail is the drawn tap geometry "
                         "(TAPCELL p+ in well, SDT/LISD/V0, M1), which the "
                         "deck's extraction does not model -- see the tap "
                         "probe record beside this file",
        },
        "self_checks_passed": len(checks),
    }
    import json
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
