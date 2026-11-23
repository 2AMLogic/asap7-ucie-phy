#!/usr/bin/env python3
r"""r18 trace, per-net diff and supply/well census: the post-grid-restore state
of the routed slice's LVS residue, from the committed r18 artifacts.

This is the r18 sibling of slice_routed.r13.netdiff.py (issue #169's method):
the same parsers and the same anchor-propagated pairing, imported from the
committed r13 script rather than duplicated, re-pointed at the r18 artifacts
and extended with the census issue #273 asks for. It consumes only committed
artifacts:

- evidence/item4-lvs/slice_routed.r18.extract.v  (klt extract output, r18)
- layout/slice_routed.v                          (the reference r18/r19 used)
- evidence/item4-lvs/slice_routed.r18.report.json (the r18 lvs report)
- layout/slice_routed.def                         (placement, for the row join)
- evidence/item4-lvs/slice_routed.r13.netdiff.py  (parsers and anchor_pair)
- CDL_DEVICE_COUNTS below                         (derived, see the note)

No tool run is made and no new revision is opened; this is analysis of the
committed r18 artifacts, so it keeps the slice_routed.r18. prefix.

Counting domain: identical to the r13 script (top circuit of each side,
identity by pin membership, instances paired by anchored propagation seeded by
membership-verified display names). Nothing here is re-derived differently.

What is NEW beyond the r13 script, and why: between r13 and r18 the stream
changed three times (the M5/M6 grid restore #66, the cell swap #228, the
re-synthesis #253), the residue fell from 86,629 to 7,581 mismatches, and the
question changed from "is the routed signal connectivity intact?" (r13: yes,
measured) to "what exactly is the remaining 7,581, and is it the stream's or
the tool's?" This script answers that from the netlists alone:

- The supply/well census (power_well below): the extract's top-level supply
  domain after the grid restore. The named nets VDD/VSS/vsubs hold every rail
  terminal (998 'vdd' + 1593 'vdd$1' + 2591 'vss' + 2591 'vsubs'), and exactly
  80 anonymous '$I' nets hold every PMOS-body (well) terminal -- per instance,
  the leaf port carrying the PMOS bulk is on an anonymous island and the leaf
  port carrying PMOS source/drain supply terminals is on the named VDD, 2591
  of 2591 instances, with no exception. The leaf-internal census shows the
  bulk port is named 'VDD' in 53 leaf variants (1593 instances) and 'VDD$1'
  in 26 (998) -- two in-leaf naming orders for the same physical split, so
  the port NAME is not the classifier; the census classifies by M-card role.
- The DEF row join (def_row_join below): island membership joined to
  placement. All instances of one island sit in one DEF row pair (an N row
  and the FS row above it share one n-well strip); 80 islands map to 80
  distinct row pairs. The geometry half of that statement (80 full-width
  well strips, both metal supply grids fully connected via-aware) is
  measured by the committed slice_routed.r18.welldom.py, which needs
  klayout; this script needs only python3 -I.
- The surplus attribution (surplus_attribution below): the flat layout device
  count is 29,196 (leaf census weighted by instances; equals the report's
  counts.devices.layout) against the reference's 28,824 (equals the CDL
  expansion the report records), a surplus of exactly 372 = 2 x 186, and the
  186 is AOI21x1_ASAP7_75t_R{,$VAR1}: 87 + 99 instances, each drawing its
  A1/A2 nmos series stack twice at half width (two nfin=3 stacks where the
  CDL folds one nfin=6 stack; total fins 16 = 16). The report's 186
  device.unmerged_fingers entries are exactly those instances (every entry
  nmos_rvt, W=0.162 = 2 x 0.081). The flat net surplus (+122) decomposes to
  the 80 well islands plus the deck-synthesized vsubs global (81); the
  remaining 41 is flat-comparer bookkeeping the committed artifacts cannot
  decompose -- stated, not smoothed over.

CDL_DEVICE_COUNTS note: the per-cell (nmos, pmos) device counts of the pinned
library CDL (siliconcompiler/lambdapdk v0.2.17,
asap7/libs/asap7sc7p5t_rvt/netlist/asap7sc7p5t_28_R.cdl, sha256
3e3e2548fb8f571c2e373dcbf565ecb0288e6433e803fbf06561cb16b70caf53 -- the same
resolve the r15-r19 requests name by the $PDK_ROOT token, provenance recorded
in verification/drc/README.md's r15 addendum). Derived once by counting
M-cards per .SUBCKT in that file (the CDL is not committed, so the counts are
committed here instead, r13's refnets.json precedent); only the 79 instantiated
leaf variants are kept. The self-checks pin the weighted total to 28,824, the
report's own reference device count, so a wrong table cannot pass silently.

Self-checks: the script hard-fails (non-zero exit) if any committed baseline
figure cannot be recovered -- the r18 category counts (error and warning),
mismatch_count 7581, counts nets 15604/15482/13826, devices 29196/28824/26466,
pins 268/266/268, len(net_correspondence) 13826, both tops at 2591 instances,
rx_clk at 528 cell pins on both sides, flat devices 29196, the CDL table's
weighted total 28824, the island census (80 islands; VDD/VSS/vsubs terminal
profiles; the per-instance bulk/rail law at 2591/2591), the DEF join (2591
names resolved, 80 row-pair bands, no island spanning two bands), the
supply_fragmented circuit set equal to the leaves-with-PMOS set, the
finfet_bulk_tied circuit set equal to it too, and the unmerged_fingers entries
all (nmos_rvt, W=0.162). A silent parse regression fails instead of reporting
zeros.

Usage: python3 -I slice_routed.r18.netdiff.py   (no arguments; paths resolve
relative to this script's directory). Writes one JSON object to stdout.

Every figure this script produces is a tool result against a predictive PDK
(ASAP7); nothing here implies fabrication.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

EXTRACT = os.path.join(HERE, "slice_routed.r18.extract.v")
REFERENCE = os.path.join(HERE, "..", "..", "layout", "slice_routed.v")
REPORT = os.path.join(HERE, "slice_routed.r18.report.json")
DEF = os.path.join(HERE, "..", "..", "layout", "slice_routed.def")
R13_NETDIFF = os.path.join(HERE, "slice_routed.r13.netdiff.py")

MAX_SAMPLES = 40       # per sample list in the JSON; totals are always complete


def _load_r13():
    spec = importlib.util.spec_from_file_location("netdiff_r13", R13_NETDIFF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: (nmos, pmos) M-card counts per .SUBCKT of the pinned library CDL, for the
#: 79 leaf variants the r18 extract instantiates. See the module docstring
#: for the derivation and the pin.
CDL_DEVICE_COUNTS = {
    "AND2x2_ASAP7_75t_R": (3, 3),
    "AND2x2_ASAP7_75t_R$VAR1": (3, 3),
    "AND5x1_ASAP7_75t_R": (6, 6),
    "AO21x1_ASAP7_75t_R": (4, 4),
    "AOI21x1_ASAP7_75t_R": (3, 3),
    "AOI21x1_ASAP7_75t_R$VAR1": (3, 3),
    "AOI21xp33_ASAP7_75t_R": (3, 3),
    "AOI21xp33_ASAP7_75t_R$VAR1": (3, 3),
    "AOI21xp5_ASAP7_75t_R": (3, 3),
    "AOI21xp5_ASAP7_75t_R$VAR1": (3, 3),
    "AOI311xp33_ASAP7_75t_R": (5, 5),
    "AOI31xp33_ASAP7_75t_R": (4, 4),
    "BUFx3_ASAP7_75t_R": (2, 2),
    "BUFx3_ASAP7_75t_R$VAR1": (2, 2),
    "BUFx5_ASAP7_75t_R": (2, 2),
    "BUFx5_ASAP7_75t_R$VAR1": (2, 2),
    "CKINVDCx10_ASAP7_75t_R": (7, 7),
    "CKINVDCx10_ASAP7_75t_R$VAR1": (7, 7),
    "CKINVDCx11_ASAP7_75t_R": (7, 7),
    "CKINVDCx6p67_ASAP7_75t_R": (7, 7),
    "CKINVDCx6p67_ASAP7_75t_R$VAR1": (7, 7),
    "CKINVDCx8_ASAP7_75t_R": (7, 7),
    "CKINVDCx8_ASAP7_75t_R$VAR1": (7, 7),
    "DFFASRHQNx1_ASAP7_75t_R": (16, 16),
    "DFFASRHQNx1_ASAP7_75t_R$VAR1": (16, 16),
    "DFFHQNx1_ASAP7_75t_R": (12, 12),
    "DFFHQNx1_ASAP7_75t_R$VAR1": (12, 12),
    "INVx11_ASAP7_75t_R": (1, 1),
    "INVx1_ASAP7_75t_R": (1, 1),
    "INVx1_ASAP7_75t_R$VAR1": (1, 1),
    "INVx5_ASAP7_75t_R": (1, 1),
    "INVx8_ASAP7_75t_R": (1, 1),
    "INVxp33_ASAP7_75t_R": (1, 1),
    "INVxp33_ASAP7_75t_R$VAR1": (1, 1),
    "INVxp67_ASAP7_75t_R": (1, 1),
    "INVxp67_ASAP7_75t_R$VAR1": (1, 1),
    "NAND2xp33_ASAP7_75t_R": (2, 2),
    "NAND2xp33_ASAP7_75t_R$VAR1": (2, 2),
    "NAND2xp5_ASAP7_75t_R": (2, 2),
    "NAND2xp5_ASAP7_75t_R$VAR1": (2, 2),
    "NAND3xp33_ASAP7_75t_R": (3, 3),
    "NAND5xp2_ASAP7_75t_R": (5, 5),
    "NOR2xp33_ASAP7_75t_R": (2, 2),
    "NOR2xp33_ASAP7_75t_R$VAR1": (2, 2),
    "NOR3xp33_ASAP7_75t_R": (3, 3),
    "NOR3xp33_ASAP7_75t_R$VAR1": (3, 3),
    "NOR4xp25_ASAP7_75t_R": (4, 4),
    "O2A1O1Ixp33_ASAP7_75t_R": (4, 4),
    "O2A1O1Ixp33_ASAP7_75t_R$VAR1": (4, 4),
    "OA211x2_ASAP7_75t_R": (5, 5),
    "OA21x2_ASAP7_75t_R": (4, 4),
    "OA21x2_ASAP7_75t_R$VAR1": (4, 4),
    "OA222x2_ASAP7_75t_R": (7, 7),
    "OA222x2_ASAP7_75t_R$VAR1": (7, 7),
    "OAI211xp5_ASAP7_75t_R": (4, 4),
    "OAI211xp5_ASAP7_75t_R$VAR1": (4, 4),
    "OAI21xp33_ASAP7_75t_R": (3, 3),
    "OAI21xp33_ASAP7_75t_R$VAR1": (3, 3),
    "OAI21xp5_ASAP7_75t_R": (3, 3),
    "OAI21xp5_ASAP7_75t_R$VAR1": (3, 3),
    "OAI222xp33_ASAP7_75t_R": (6, 6),
    "OAI222xp33_ASAP7_75t_R$VAR1": (6, 6),
    "OAI22xp5_ASAP7_75t_R": (4, 4),
    "OAI22xp5_ASAP7_75t_R$VAR1": (4, 4),
    "OAI311xp33_ASAP7_75t_R": (5, 5),
    "OAI311xp33_ASAP7_75t_R$VAR1": (5, 5),
    "OAI31xp33_ASAP7_75t_R": (4, 4),
    "OR2x2_ASAP7_75t_R": (3, 3),
    "OR2x2_ASAP7_75t_R$VAR1": (3, 3),
    "OR3x1_ASAP7_75t_R": (4, 4),
    "OR3x1_ASAP7_75t_R$VAR1": (4, 4),
    "OR4x1_ASAP7_75t_R": (5, 5),
    "OR4x1_ASAP7_75t_R$VAR1": (5, 5),
    "TIEHIx1_ASAP7_75t_R": (1, 1),
    "TIEHIx1_ASAP7_75t_R$VAR1": (1, 1),
    "XNOR2xp5_ASAP7_75t_R": (5, 5),
    "XNOR2xp5_ASAP7_75t_R$VAR1": (5, 5),
    "XOR2xp5_ASAP7_75t_R": (5, 5),
    "XOR2xp5_ASAP7_75t_R$VAR1": (5, 5),
}


# ---------------------------------------------------------------- DEF parsing


DEF_COMP = re.compile(
    r"^\s*-\s+(\S+)\s+(\S+)\s+.*?\(\s*(-?\d+)\s+(-?\d+)\s*\)\s+(\w+)\s*;",
    re.M,
)
DEF_ROW = re.compile(
    r"^\s*ROW\s+(\S+)\s+(\S+)\s+(-?\d+)\s+(-?\d+)\s+(\w+)\s+DO\s+(\d+)\s+BY\s+(\d+)\s+STEP\s+(\d+)\s+(\d+)",
    re.M,
)


def unescape_def_name(name: str) -> str:
    """DEF escapes [ ] in names with backslashes; the reference Verilog writes
    the same identifier with a single leading backslash instead."""
    out = name.replace("\\[", "[").replace("\\]", "]")
    return out[1:] if out.startswith("\\") and len(out) > 1 else out


def parse_def(path: str) -> dict:
    text = open(path).read()
    m = re.search(r"UNITS\s+DISTANCE\s+MICRONS\s+(\d+)\s*;", text)
    units = int(m.group(1)) if m else 1000
    comps = {}
    for name, master, x, y, orient in DEF_COMP.findall(text):
        comps[unescape_def_name(name)] = {
            "master": master,
            "x": int(x),
            "y": int(y),
            "orient": orient,
        }
    rows = []
    for _n, site, x, y, orient, nx, ny, sx, sy in DEF_ROW.findall(text):
        rows.append({"x": int(x), "y": int(y), "orient": orient})
    rows.sort(key=lambda r: r["y"])
    return {"units": units, "components": comps, "rows": rows}


def row_pair_of(y: int, rows: list[dict]) -> int | None:
    """Index of the DEF row pair (an N row plus the FS row above it, which
    share one n-well strip) containing a placement origin at coordinate y."""
    if not rows:
        return None
    pitch = rows[1]["y"] - rows[0]["y"] if len(rows) > 1 else 1
    k = (y - rows[0]["y"]) // pitch if pitch else None
    return None if k is None or k < 0 else k // 2


# ---------------------------------------------------------------- leaf styles


def leaf_bulk_ports(subs: dict, top: str) -> dict:
    """leaf name -> {polarity: bulk node} plus the PMOS S/D supply ports.

    The bulk node of a leaf's M-cards is the 5th node token; for PMOS it is
    the well piece and the source/drain supply port is the other one of
    {VDD, VDD$1} that appears as a source/drain terminal.
    """
    out = {}
    for name, s in subs.items():
        if name == top or not s["mcards"]:
            continue
        pmos_bulk = None
        for m in s["mcards"]:
            if len(m) > 5 and m[5].startswith("pmos"):
                pmos_bulk = m[4]
        if pmos_bulk is None:
            continue
        sd = set()
        for m in s["mcards"]:
            if len(m) > 5 and m[5].startswith("pmos") and m[1] in ("VDD", "VDD$1"):
                sd.add(m[1])
            if len(m) > 5 and m[5].startswith("pmos") and m[3] in ("VDD", "VDD$1"):
                sd.add(m[3])
        sd.discard(pmos_bulk)
        out[name] = {"pmos_bulk": pmos_bulk, "pmos_sd": sorted(sd)}
    return out


def check_bulk_rail_law(ext_insts, styles, top, fold,
                        max_samples=MAX_SAMPLES):
    """Per-instance bulk/rail law over the extract's top-level instances.

    For every instance of a leaf with a PMOS style: the leaf port carrying
    the PMOS bulk (the well piece) is on an anonymous $I island net and the
    leaf ports carrying PMOS source/drain supply terminals are on the named
    top-level net VDD (the metal rail grid). Returns (law, violations): a
    Counter keyed (bulk_ok, rail_ok) plus up to max_samples violation
    records. fold is the port-name normalizer (r13.fold).
    """
    law = collections.Counter()
    law_violations = []
    for i in ext_insts:
        st = styles.get(i["cell"])
        if not st:
            continue
        bulk_node = i["conn"][fold(st["pmos_bulk"])]
        sd_nodes = {i["conn"][fold(p)] for p in st["pmos_sd"]}
        bulk_ok = bulk_node[1].startswith("\\$I")
        rail_ok = sd_nodes == {(top, "VDD")}
        law[(bulk_ok, rail_ok)] += 1
        if not (bulk_ok and rail_ok) and len(law_violations) < max_samples:
            law_violations.append({"idx": i["idx"], "cell": i["cell"],
                                   "bulk_node": bulk_node[1],
                                   "sd_nodes": sorted(n[1] for n in sd_nodes)})
    return law, law_violations


def join_islands_to_rows(islands, full_ext_members, rev_inst_map, ext_insts,
                         def_data):
    """Join island membership to DEF placement rows.

    Each island's member instances are resolved through the instance
    pairing to reference names, looked up in the DEF components, and mapped
    to the row pair (an N row plus the FS row above it, which share one
    n-well strip) their placement origin falls in -- so an island spanning
    two bands shows two row pairs instead of being clamped to one. Returns
    (island_rows, island_members, island_cells, unresolved_def): island
    net name -> row-pair set, -> member reference names, -> per-cell
    instance Counter, and the count of member names the DEF could not
    resolve.
    """
    island_rows: dict[str, set[int]] = {}
    island_members: dict[str, list[str]] = collections.defaultdict(list)
    island_cells: dict[str, collections.Counter] = {}
    unresolved_def = 0
    for node in islands:
        name = node[1]
        island_cells[name] = collections.Counter()
        for idx, _p in full_ext_members[node]:
            ref_name = rev_inst_map.get(idx)
            cell = ext_insts[idx]["cell"]
            island_cells[name][cell] += 1
            if ref_name is None:
                continue
            comp = def_data["components"].get(ref_name)
            if comp is None:
                unresolved_def += 1
                continue
            rp = row_pair_of(comp["y"], def_data["rows"])
            if rp is not None:
                island_rows.setdefault(name, set()).add(rp)
            island_members[name].append(ref_name)
    return island_rows, island_members, island_cells, unresolved_def


def reconcile_device_surplus(subs, target_counts, cdl_counts):
    """Reconcile the flat layout device count against the CDL expansion.

    Layout devices are the extract's leaf M-cards weighted by top-level
    instance counts; reference devices are the pinned CDL's per-cell
    (nmos, pmos) counts weighted the same way. A leaf whose extract M-card
    counts differ from the CDL's is a fold cell. Returns (flat_leaf_devices,
    flat_cdl_devices, fold_cells, fold_instances, fold_delta); hard-fails
    if an instantiated leaf is missing from the CDL table.
    """
    flat_leaf_devices = sum(len(subs[n]["mcards"]) * target_counts[n]
                            for n in target_counts)
    flat_cdl_devices = sum((cn + cp) * target_counts[n]
                           for n, (cn, cp) in
                           ((n, cdl_counts[n]) for n in target_counts
                            if n in cdl_counts))
    fold_cells = []
    for n in sorted(target_counts):
        if n not in cdl_counts:
            sys.exit(f"FATAL: leaf {n} missing from CDL_DEVICE_COUNTS")
        en = sum(1 for m in subs[n]["mcards"] if not m[5].startswith("pmos"))
        ep = sum(1 for m in subs[n]["mcards"] if m[5].startswith("pmos"))
        cn, cp = cdl_counts[n]
        if (en, ep) != (cn, cp):
            fold_cells.append({"cell": n, "layout_nmos": en, "cdl_nmos": cn,
                               "layout_pmos": ep, "cdl_pmos": cp,
                               "instances": target_counts[n],
                               "device_delta": (en + ep) - (cn + cp)})
    fold_instances = sum(f["instances"] for f in fold_cells)
    fold_delta = sum(f["device_delta"] * f["instances"] for f in fold_cells)
    return (flat_leaf_devices, flat_cdl_devices, fold_cells, fold_instances,
            fold_delta)


# ---------------------------------------------------------------- main


def main() -> int:
    r13 = _load_r13()
    ref = r13.parse_verilog(REFERENCE)
    subs = r13.parse_spice(EXTRACT)
    report = json.load(open(REPORT))
    d = parse_def(DEF)

    top = max(subs, key=lambda n: len(subs[n]["xcards"]))
    top_xcards = subs[top]["xcards"]
    target_counts = collections.Counter(card[-1] for card in top_xcards)

    # --- extract instances: positional nodes -> port names via leaf headers ---
    ext_insts = []
    for idx, card in enumerate(top_xcards):
        cell = card[-1]
        hp = subs[cell]["ports"]
        nodes = card[1:-1]
        if len(nodes) != len(hp):
            sys.exit(f"FATAL: X-card {idx} has {len(nodes)} nodes for "
                     f"{len(hp)}-port cell {cell}")
        ext_insts.append({"idx": idx, "base": r13.cell_base(cell), "cell": cell,
                          "conn": {r13.fold(p): (top, n)
                                   for p, n in zip(hp, nodes)}})

    ref_insts = [{"name": i["name"], "base": i["cell"],
                  "conn": {r13.fold(p): n for p, n in i["conn"].items()}}
                 for i in ref["instances"]]

    # --- cell/port vocabulary reconciliation --------------------------------
    ref_cells = collections.Counter(i["base"] for i in ref_insts)
    ext_cells = collections.Counter(i["base"] for i in ext_insts)
    if ref_cells != ext_cells:
        sys.exit(f"FATAL: cell-type multisets differ: only-ref="
                 f"{sorted(ref_cells - ext_cells)} only-ext="
                 f"{sorted(ext_cells - ref_cells)}")
    ext_ports_by_base: dict[str, set[str]] = collections.defaultdict(set)
    for i in ext_insts:
        ext_ports_by_base[i["base"]].update(i["conn"])
    ref_ports_by_base: dict[str, set[str]] = collections.defaultdict(set)
    for i in ref_insts:
        ref_ports_by_base[i["base"]].update(i["conn"])
    common_ports: dict[str, set[str]] = {}
    for base, rp in ref_ports_by_base.items():
        missing = rp - ext_ports_by_base[base]
        if missing:
            sys.exit(f"FATAL: cell {base}: reference ports absent from extract "
                     f"leaf header: {sorted(missing)}")
        common_ports[base] = rp & ext_ports_by_base[base]

    # --- membership maps (pairing domain: common ports only) -----------------
    ref_members: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    ref_net_of: dict[str, dict[str, str]] = {}
    for i in ref_insts:
        ref_net_of[i["name"]] = {}
        for p, net in i["conn"].items():
            if p in common_ports[i["base"]]:
                ref_members[net].append((i["name"], p))
                ref_net_of[i["name"]][p] = net
    ext_members: dict[tuple, list[tuple[int, str]]] = collections.defaultdict(list)
    ext_net_of: dict[int, dict[str, tuple]] = {}
    for i in ext_insts:
        ext_net_of[i["idx"]] = {}
        for p, node in i["conn"].items():
            if p in common_ports[i["base"]]:
                ext_members[node].append((i["idx"], p))
                ext_net_of[i["idx"]][p] = node

    # --- seed and pairing ------------------------------------------------------
    ext_nodes_by_token: dict[str, list[tuple]] = collections.defaultdict(list)
    for node in ext_members:
        ext_nodes_by_token[node[1]].append(node)
    seeds: dict[str, tuple] = {}
    for name in sorted(ref_members):
        cands = ext_nodes_by_token.get(name, [])
        if len(cands) != 1:
            continue
        node = cands[0]
        if collections.Counter(p for _, p in ref_members[name]) != \
           collections.Counter(p for _, p in ext_members[node]):
            continue
        seeds[name] = node

    paired, netmap, rev, rounds = r13.anchor_pair(
        ref_insts, ref_net_of, ext_insts, ext_net_of, seeds)
    rev_inst_map = {v: k for k, v in paired.items()}

    # --- net correspondence over paired instances -------------------------------
    def ref_key(net: str):
        return tuple(sorted((p, paired[i]) for i, p in ref_members[net]
                            if i in paired))

    def ext_key(node: tuple):
        return tuple(sorted((p, i) for i, p in ext_members[node]
                            if i in rev_inst_map))

    ext_by_key: dict[tuple, list[tuple]] = collections.defaultdict(list)
    for node in ext_members:
        ext_by_key[ext_key(node)].append(node)
    ref_by_key: dict[tuple, list[str]] = collections.defaultdict(list)
    for net in ref_members:
        ref_by_key[ref_key(net)].append(net)

    matched_pairs = []
    splits = []
    merges = []
    partials = []
    ref_unpaired = []
    ext_unpaired = []
    for key in sorted(ref_by_key):
        if not key:
            continue
        rlist = ref_by_key[key]
        elist = ext_by_key.get(key, [])
        if len(rlist) == 1 and len(elist) == 1:
            matched_pairs.append({"reference": rlist[0],
                                  "layout": elist[0][1],
                                  "shared_terminals": len(key)})
            continue
        for net in rlist:
            if not elist:
                ref_unpaired.append(net)
            else:
                splits.append(net)
    for key in sorted(ext_by_key):
        if not key:
            continue
        elist = ext_by_key[key]
        rlist = ref_by_key.get(key, [])
        if len(elist) == 1 and len(rlist) == 1:
            continue
        for node in elist:
            if not rlist:
                ext_unpaired.append(node[1])
            else:
                merges.append(node[1])

    # --- full-domain supply census ------------------------------------------------
    full_ext_members: dict[tuple, list[tuple[int, str]]] = collections.defaultdict(list)
    for i in ext_insts:
        for p, node in i["conn"].items():
            full_ext_members[node].append((i["idx"], p))

    def ext_port_counter(node):
        return collections.Counter(p.lower() for _, p in full_ext_members[node])

    named = {n: ext_port_counter((top, n))
             for n in ("VDD", "VSS", "vsubs")}
    islands = {node: ext_port_counter(node)
               for node in full_ext_members
               if node != top and node[1].startswith("\\$I")}

    # --- per-instance bulk/rail law ------------------------------------------------
    styles = leaf_bulk_ports(subs, top)
    law, law_violations = check_bulk_rail_law(ext_insts, styles, top,
                                              r13.fold)

    # --- island census with DEF row join ---------------------------------------------
    island_rows, island_members, island_cells, unresolved_def = \
        join_islands_to_rows(islands, full_ext_members, rev_inst_map,
                             ext_insts, d)

    # --- leaf bulk census (port-name flip) --------------------------------------------
    leaf_census = []
    census_totals: collections.Counter = collections.Counter()
    for name in sorted(styles):
        inst = target_counts.get(name, 0)
        if inst:
            leaf_census.append({"cell": name,
                                "pmos_bulk_port": styles[name]["pmos_bulk"],
                                "instances": inst})
            census_totals[styles[name]["pmos_bulk"]] += inst

    # --- flat device census and CDL comparison ------------------------------------------
    flat_leaf_devices, flat_cdl_devices, fold_cells, fold_instances, \
        fold_delta = reconcile_device_surplus(subs, target_counts,
                                              CDL_DEVICE_COUNTS)

    # --- report-side identity and category attribution -------------------------------------
    mm = report["mismatches"]
    by_cat: dict[str, list] = collections.defaultdict(list)
    for m in mm:
        by_cat[m["category"]].append(m)

    ns = by_cat["net.split"]
    ns_names = collections.Counter(m["net"]["layout"] for m in ns
                                   if m["net"]["layout"])
    nm = by_cat["net.merged"]
    nm_names = {m["net"]["reference"] for m in nm if m["net"]["reference"]}
    nc = report["net_correspondence"]
    nc_layout_names = collections.Counter(e["layout"] for e in nc)

    sf = by_cat["net.supply_fragmented"]
    sf_circuits = {m["circuit"]["layout"] for m in sf}
    fb = by_cat["device.finfet_bulk_tied"]
    fb_circuits = {(m["details"]["polarity"], m["details"]["circuit"])
                   for m in fb}
    uf = by_cat["device.unmerged_fingers"]
    uf_shapes = collections.Counter()
    for m in uf:
        w = re.search(r"W=([\d.]+)", m["description"])
        c = re.search(r"class '(\w+)'", m["description"])
        uf_shapes[(c.group(1) if c else None, w.group(1) if w else None)] += 1
    un = by_cat["device.unmatched"]
    un_by = collections.Counter()
    for m in un:
        dev = m.get("device") or {}
        un_by[(m.get("side"), dev.get("class"))] += 1

    leaves_with_pmos = set(styles)
    cec = report["category_error_counts"]

    # --- self-checks against committed baselines ---------------------------------------------
    edge_ref = sum(1 for i in ref_insts for p in i["conn"]
                   if p in common_ports[i["base"]])
    edge_ext = sum(1 for e in ext_insts for p in e["conn"]
                   if p in common_ports[e["base"]])
    bands = sorted({rp for s in island_rows.values() for rp in s})
    checks = {
        "cec.net.split == 1328": cec["net.split"] == 1328,
        "cec.net.merged == 1206": cec["net.merged"] == 1206,
        "cec.device.unmatched == 4528": cec["device.unmatched"] == 4528,
        "cec.device.unmerged_fingers == 186":
            cec["device.unmerged_fingers"] == 186,
        "mismatch_count == 7581": report["mismatch_count"] == 7581,
        "counts.nets 15604/15482/13826": report["counts"]["nets"] ==
            {"layout": 15604, "reference": 15482, "matched": 13826},
        "counts.devices 29196/28824/26466": report["counts"]["devices"] ==
            {"layout": 29196, "reference": 28824, "matched": 26466},
        "counts.pins 268/266/268": report["counts"]["pins"] ==
            {"layout": 268, "reference": 266, "matched": 268},
        "len(net_correspondence) == 13826": len(nc) == 13826,
        "category net.supply_fragmented == 79": len(sf) == 79,
        "category device.finfet_bulk_tied == 158": len(fb) == 158,
        "extract top X-cards == 2591": len(top_xcards) == 2591,
        "reference connected instances == 2591": len(ref_insts) == 2591,
        "reference connectionless instances == 0":
            ref["connectionless_instances"] == 0,
        "flat devices from extract == 29196": flat_leaf_devices == 29196,
        "flat devices from CDL table == 28824": flat_cdl_devices == 28824,
        "instances paired == 2591 of 2591": len(paired) == 2591,
        "pairing-domain edge counts equal": edge_ref == edge_ext,
        "rx_clk 528 cell pins on reference side":
            len(ref_members.get("rx_clk", [])) == 528,
        "rx_clk 528 cell pins on extract side":
            len(ext_members.get((top, "rx_clk"), [])) == 528,
        "named VDD profile vdd=998 vdd$1=1593":
            named["VDD"] == collections.Counter({"vdd$1": 1593, "vdd": 998}),
        "named VSS profile vss=2591": named["VSS"] ==
            collections.Counter({"vss": 2591}),
        "named vsubs profile vsubs=2591": named["vsubs"] ==
            collections.Counter({"vsubs": 2591}),
        "island count == 80": len(islands) == 80,
        "island terminals cover all PMOS bulk ports 2591":
            law.get((True, True), 0) == 2591 and len(law) == 1,
        "DEF row join resolved 2591 island instances":
            sum(len(v) for v in island_members.values()) == 2591,
        "DEF row join: no unresolved reference name": unresolved_def == 0,
        "DEF row join: 80 islands on 80 distinct single row pairs":
            len(island_rows) == 80 and len(bands) == 80 and
            all(len(s) == 1 for s in island_rows.values()),
        "leaf bulk census 53 VDD / 26 VDD$1 variants":
            census_totals == collections.Counter({"VDD": 1593, "VDD$1": 998}),
        "supply_fragmented circuits == leaves with pmos":
            sf_circuits == leaves_with_pmos,
        "finfet_bulk circuits == leaves with pmos (both polarities)":
            {c for pol, c in fb_circuits} == leaves_with_pmos and
            len(fb_circuits) == 2 * len(leaves_with_pmos),
        "unmerged_fingers all nmos_rvt W=0.162":
            set(uf_shapes) == {("nmos_rvt", "0.162")},
        "device surplus == 372 == AOI21x1 folds only":
            flat_leaf_devices - flat_cdl_devices == 372 and
            fold_delta == 372 and fold_instances == 186 and
            {f["cell"] for f in fold_cells} ==
            {"AOI21x1_ASAP7_75t_R", "AOI21x1_ASAP7_75t_R$VAR1"},
        "structural correspondence is a bijection (no splits/merges)":
            not splits and not merges and not partials and
            not ref_unpaired and not ext_unpaired,
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        sys.exit("FATAL: self-checks failed: " + "; ".join(failed))

    # --- output ---------------------------------------------------------------------------
    island_table = []
    for node in sorted(islands, key=lambda n: -len(full_ext_members[n])):
        island_table.append({
            "net": node[1],
            "terminals": len(full_ext_members[node]),
            "port_profile": dict(sorted(islands[node].items())),
            "instances": len(island_members.get(node[1], [])),
            "distinct_cells": len(island_cells[node[1]]),
            "row_pair": sorted(island_rows.get(node[1], [])),
            "member_sample": sorted(island_members.get(node[1], []))[:5],
        })

    out = {
        "script": "slice_routed.r18.netdiff.py",
        "consumes": ["evidence/item4-lvs/slice_routed.r18.extract.v",
                     "layout/slice_routed.v",
                     "evidence/item4-lvs/slice_routed.r18.report.json",
                     "layout/slice_routed.def",
                     "evidence/item4-lvs/slice_routed.r13.netdiff.py"],
        "domain": {
            "extract_top": top,
            "extract_top_xcards": len(top_xcards),
            "reference_module": ref["module"],
            "reference_connected_instances": len(ref_insts),
            "reference_connectionless_instances": ref["connectionless_instances"],
            "identity": "pin membership; instances paired by anchored "
                        "propagation (parsers and anchor_pair imported from "
                        "the committed r13 script)",
            "propagation_rounds": rounds,
        },
        "instance_pairing": {
            "instances_paired": len(paired),
            "instance_coverage": round(len(paired) / len(ref_insts), 6),
        },
        "net_correspondence_structural": {
            "reference_nets_total_pairing_domain": len(ref_members),
            "extract_nets_total_pairing_domain": len(ext_members),
            "matched_1_to_1": len(matched_pairs),
            "splits": len(splits),
            "merges": len(merges),
            "partials": len(partials),
            "reference_nets_without_extract_counterpart": len(ref_unpaired),
            "extract_nets_without_reference_counterpart": len(ext_unpaired),
            "note": "the routed signal circuits still correspond exactly "
                    "after the grid restore, the cell swap and the "
                    "re-synthesis; every pairing-domain net matches 1:1",
        },
        "power_well": {
            "named_nets": {n: dict(sorted(c.items())) for n, c in named.items()},
            "island_count": len(islands),
            "islands": island_table[:MAX_SAMPLES],
            "island_totals": {
                "terminals": sum(len(full_ext_members[node])
                                 for node in islands),
                "instances": sum(len(v) for v in island_members.values()),
                "by_port": dict(sorted(collections.Counter(
                    p for node in islands
                    for _, p in full_ext_members[node]).items())),
            },
            "per_instance_bulk_rail_law": {
                "statement": "for every instance, the leaf port carrying the "
                             "PMOS bulk (the well piece) is on an anonymous "
                             "$I island net and the leaf port carrying PMOS "
                             "source/drain supply terminals is on the named "
                             "top-level net VDD (the metal rail grid)",
                "instances_obeying": law.get((True, True), 0),
                "violations": law_violations,
            },
            "leaf_bulk_port_census": {
                "by_port_name_totals": dict(sorted(census_totals.items())),
                "leaves": leaf_census,
                "note": "the port NAME flips between leaf variants (53 "
                        "variants name the bulk port 'VDD', 26 name it "
                        "'VDD$1'); both are the same physical split, so the "
                        "census classifies by M-card role, not port name",
            },
            "def_row_join": {
                "def_rows": len(d["rows"]),
                "islands_on_distinct_row_pairs": len(bands),
                "note": "an N row and the FS row above it share one n-well "
                        "strip; each island's members sit in exactly one such "
                        "row pair, and the 80 islands map to 80 distinct "
                        "pairs. The geometry half (80 full-width well "
                        "strips; both metal supply grids connected "
                        "via-aware) is slice_routed.r18.welldom.py's output.",
            },
        },
        "surplus_attribution": {
            "devices": {
                "flat_layout_from_extract": flat_leaf_devices,
                "flat_reference_from_cdl_table": flat_cdl_devices,
                "surplus": flat_leaf_devices - flat_cdl_devices,
                "fold_cells": fold_cells,
                "fold_instances": fold_instances,
                "statement": "the whole 372-device layout surplus is "
                             "AOI21x1_ASAP7_75t_R{,$VAR1}: 87 + 99 "
                             "instances drawing the A1/A2 nmos series stack "
                             "twice at half width (two nfin=3 stacks where "
                             "the CDL folds one nfin=6 stack; total fins "
                             "16 = 16), i.e. the pinned library's own "
                             "CDL-vs-GDS series-stack fold the deck "
                             "docstring records; not tap or filler cells "
                             "(TAPCELL/FILLER variants extract with no "
                             "devices and none is instantiated as a "
                             "netlist instance)",
            },
            "unmerged_fingers": {
                "entries": len(uf),
                "shapes": {f"{c}/W={w}": n for (c, w), n in
                           sorted(uf_shapes.items())},
                "attributed_to": "the same 186 AOI21x1 instances (87 N + 99 "
                                 "FS); one group per instance, 2 x 0.081 = "
                                 "0.162",
            },
            "nets": {
                "report_flat_surplus": 15604 - 15482,
                "decomposable_from_committed_artifacts": {
                    "well_islands": len(islands),
                    "vsubs_global": 1,
                },
                "remainder": 15604 - 15482 - len(islands) - 1,
                "note": "the remainder is flat-comparer bookkeeping the "
                        "committed report cannot decompose (the unmerged-"
                        "finger groups' net handling); stated, not smoothed "
                        "over -- r13's precedent for report bookkeeping it "
                        "could not decompose",
            },
            "unmatched_by_side_class": {f"{s}/{c}": n
                                        for (s, c), n in sorted(un_by.items())},
        },
        "report_identity": {
            "net_split": {
                "entries": len(ns),
                "entries_with_layout_name": sum(1 for m in ns
                                                if m["net"]["layout"]),
                "distinct_layout_display_names": len(ns_names),
                "entries_under_display_name_backslash_dollar_zero":
                    ns_names.get("\\$0", 0),
            },
            "net_merged": {
                "entries": len(nm),
                "distinct_reference_names": len(nm_names),
            },
            "net_correspondence_report": {
                "entries": len(nc),
                "entries_with_anonymous_layout_name": sum(
                    1 for e in nc if e["layout"].startswith("\\")),
            },
            "supply_fragmented_circuits": len(sf_circuits),
            "finfet_bulk_tied_circuits": len(fb_circuits),
        },
        "self_checks_passed": len(checks),
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
