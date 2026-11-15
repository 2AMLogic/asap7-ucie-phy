#!/usr/bin/env python3
"""r13 trace, geometry half: via-aware connectivity of the routed stream's M2-M6 stack.

Reworks the flawed r13 measurement (a 2D union that joined metal layers wherever
they overlap, reported in evidence/item4-slice-attempt.r13.json as "via cuts").
Two variants, both on klayout's LayoutToNetlist engine (the same engine klt lvs
extracts with), flattened, top circuit = top cell:

- metals_union: M2..M6 pairwise-connected on geometric overlap -- connectivity
  equivalent to the flawed 2D-union fill (vias never consulted).
- via_aware: M2-V2-M3-V3-M4-V4-M5-V5-M6 -- two metals conduct only where a
  via cut joins them.

Intra-layer connectivity is automatic in this engine (touching/overlapping
polygons of one registered region join); only the inter-layer links below are
declared, and layers left out of the links (the vias in metals_union) produce
no nets of their own.

Sanity assertion (process note from the r13 review): if the via layers do not
change the component count, connectivity was not via-mediated.

Layer map from klt's pinned asap7 deck (klayout_tools/decks/asap7.py):
M2 20/0, V2 25/0, M3 30/0, V3 35/0, M4 40/0, V4 45/0, M5 50/0, V5 55/0,
M6 60/0.  dbu 0.00025 um.

Usage: uvx --with klayout --from klayout-tools==<ver> python3 slice_routed.r13.trace_geometry.py <gds>
Writes the result JSON to stdout.
"""

from __future__ import annotations

import importlib.metadata
import json
import sys

import klayout.db as db

# (layer, datatype) -> role, routing stack M2..M6 inclusive with the via cuts
# between consecutive metals, from the pinned klt asap7 deck.
STACK = [
    ("M2", (20, 0)),
    ("V2", (25, 0)),
    ("M3", (30, 0)),
    ("V3", (35, 0)),
    ("M4", (40, 0)),
    ("V4", (45, 0)),
    ("M5", (50, 0)),
    ("V5", (55, 0)),
    ("M6", (60, 0)),
]
STACK_ROLES = [role for role, _ in STACK]


def run_variant(lay: db.Layout, top: db.Cell, variant: str) -> dict:
    """Component stats of the M2-M6 stack under a connectivity variant."""
    if variant == "metals_union":
        links = [("M2", "M3"), ("M3", "M4"), ("M4", "M5"), ("M5", "M6")]
    elif variant == "via_aware":
        links = [("M2", "V2"), ("V2", "M3"), ("M3", "V3"), ("V3", "M4"),
                 ("M4", "V4"), ("V4", "M5"), ("M5", "V5"), ("V5", "M6")]
    else:
        raise ValueError(variant)

    l2n = db.LayoutToNetlist(top.name, lay.dbu)
    layer_index = {}
    merged_counts = {}
    for role in STACK_ROLES:
        n, d = dict(STACK)[role]
        region = db.Region(top.begin_shapes_rec(lay.find_layer(n, d))).merged()
        merged_counts[role] = region.count()
        layer_index[role] = l2n.register(region, role)
    for a, b in links:
        l2n.connect(l2n.layer_by_name(a), l2n.layer_by_name(b))
    l2n.extract_netlist()

    circuit = l2n.netlist().circuit_by_name(top.name)
    components = []
    for net in circuit.each_net():
        area = 0
        bbox = None
        for role in STACK_ROLES:
            polygons = l2n.polygons_of_net(net, layer_index[role]).merged()
            area += polygons.area()
            nb = polygons.bbox()
            if not nb.empty():
                bbox = nb if bbox is None else db.Box(
                    min(bbox.left, nb.left), min(bbox.bottom, nb.bottom),
                    max(bbox.right, nb.right), max(bbox.top, nb.top))
        components.append({"area_dbu2": area,
                           "bbox_dbu": None if bbox is None else
                           [bbox.left, bbox.bottom, bbox.right, bbox.top]})
    components.sort(key=lambda c: c["area_dbu2"], reverse=True)
    total_area = sum(c["area_dbu2"] for c in components)

    return {
        "merged_polygon_counts": merged_counts,
        "components": len(components),
        "total_area_dbu2": total_area,
        "largest_area_dbu2": components[0]["area_dbu2"],
        "largest_share_of_area": round(components[0]["area_dbu2"] / total_area, 5)
        if total_area else None,
        "largest_bbox_dbu": components[0]["bbox_dbu"],
        "top5_area_dbu2": [c["area_dbu2"] for c in components[:5]],
    }


def main() -> int:
    gds = sys.argv[1]
    lay = db.Layout()
    lay.read(gds)
    top = lay.top_cell()

    result = {
        "kind": "r13-trace-geometry",
        "gds": gds,
        "dbu_um": lay.dbu,
        "top_cell": top.name,
        "stack": {role: f"{n}/{d}" for role, (n, d) in STACK},
        "engine": "klayout.LayoutToNetlist",
        "klayout_version": importlib.metadata.version("klayout"),
        "variants": {
            "metals_union": run_variant(lay, top, "metals_union"),
            "via_aware": run_variant(lay, top, "via_aware"),
        },
    }

    m = result["variants"]["metals_union"]
    v = result["variants"]["via_aware"]
    result["sanity"] = {
        "component_counts_differ": m["components"] != v["components"],
        "note": ("component counts are identical, so the metals_union fill never "
                 "consulted vias -- any fill whose count survives removing the "
                 "via layers is not via-mediated"
                 if m["components"] == v["components"] else
                 "via layers change the component count, so the via_aware fill "
                 "is via-mediated"),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
