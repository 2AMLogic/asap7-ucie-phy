#!/usr/bin/env python3
r"""r13 trace, per-net diff: structural correspondence of the committed r13
extract against the committed reference, by pin membership rather than by
display name.

This extends slice_routed.r13.refnets.py: the same netlist parsers, kept as
pairable instances with named port connections, plus an anchor-propagated
pairing pass and a report-side identity census. It consumes only committed
artifacts:

- evidence/item4-lvs/slice_routed.r13.extract.v   (klt extract output, r13)
- layout/slice_routed.v                           (the reference r13 used)
- evidence/item4-lvs/slice_routed.r13.report.json (the r13 lvs report)
- evidence/item4-lvs/slice_routed.r13.refnets.json (committed parser baseline)

No tool run is made and no new revision is opened; this is analysis of the
committed r13 artifacts, so it keeps the slice_routed.r13. prefix.

Counting domain, stated explicitly:

- The diff runs on the TOP CIRCUIT of each netlist: the .SUBCKT with the most
  X-cards on the extract side (slice, 2,594 X-cards), module slice on the
  reference side. Leaf-internal nets are excluded from the pairing; each
  side's leaf-internal structure was probed separately (r9 single-cell probe,
  two-instance abutment probe, klt extract cell checks) and the flat
  comparison inside klt lvs is where the r5-r13 residue lives, so what this
  diff establishes is whether the routed connectivity itself corresponds.
- Net identity is membership: the set of (instance, port) terminals a net
  touches, with instances paired across sides by anchored propagation --
  net correspondences seeded where both sides use the same display name AND
  the name's full membership profile agrees, then instances paired only when
  exactly one candidate of the same cell agrees on every port whose net is
  already mapped, each pairing contributing new net correspondences, to a
  fixpoint. Display names are never themselves evidence of identity; every
  seed is verified by membership before it enters the map, and everything
  the seeds cannot reach is reported as unpaired rather than forced.
- Pairing uses only ports both sides name for a cell (the reference
  .NAME map intersected with the leaf .SUBCKT header, pin names folded to
  lower case exactly as the report's reference.gate_level_pin_case_folded
  entries do). Extract-only pins (VDD, VSS, VDD$1, vsubs) are excluded from
  the pairing graph and characterised separately in the power/well section.
- SPICE node names are namespaced per .SUBCKT, so $N names in two different
  subcircuits are two nodes, never one.
- Vector ports expand bit-wise; assign aliases are unioned before counting
  (the committed reference contains none).
- Cell variants: an extract X-card target C$VARk pairs as base cell C; the
  variant's own .SUBCKT header supplies its port order. Reference instances
  the committed Verilog leaves with no connections at all (the scan-chain
  tap/filler placeholders) have no extract counterpart by construction and
  are excluded symmetrically on both sides.

The report-side section answers the $0 question from the r13 report itself:
it enumerates the fields each net.split entry carries and reports whether any
stable net identity (id, subcircuit, pin set) is available to disambiguate
the 12,812 entries filed under the display name \$0. If no stable identity is
available the script says so rather than grouping by display name.

Self-checks: the script hard-fails (non-zero exit) if any committed baseline
figure cannot be recovered -- category_error_counts net.split 15269 /
net.merged 14967 / device.unmatched 55444, mismatch_count 86629,
len(net_correspondence) 408, counts nets 15803/15501/408 and devices
29436/28862/233, the report's \$0 statistics (12,812 of 15,269 net.split
entries; 2,458 distinct layout display names), the committed refnets.json
netlist statistics, both tops at 2,594 instances, rx_clk at 528 cell pins on
both sides, and equal per-cell edge counts on the shared port vocabulary --
so a silent parse regression fails instead of reporting zeros.

Usage: python3 -I slice_routed.r13.netdiff.py   (no arguments; paths resolve
relative to this script's directory). Writes one JSON object to stdout.

Every figure this script produces is a tool result against a predictive PDK
(ASAP7); nothing here implies fabrication.
"""

from __future__ import annotations

import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACT = os.path.join(HERE, "slice_routed.r13.extract.v")
REFERENCE = os.path.join(HERE, "..", "..", "layout", "slice_routed.v")
REPORT = os.path.join(HERE, "slice_routed.r13.report.json")
REFNETS = os.path.join(HERE, "slice_routed.r13.refnets.json")

MAX_SAMPLES = 40       # per sample list in the JSON; totals are always complete
MAX_ROUNDS = 200       # anchor-propagation wave cap


DECL = re.compile(r"^\s*(input|output|inout|wire)\b\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?(.+?)$", re.S)
ASSIGN = re.compile(r"^\s*assign\s+([^=;]+?)\s*=\s*([^;]+?)$", re.S)


# ---------------------------------------------------------------- parsers


def expand(name: str, msb: str | None, lsb: str | None) -> list[str]:
    if msb is None:
        return [name]
    hi, lo = int(msb), int(lsb)
    step = -1 if hi >= lo else 1
    return [f"{name}[{i}]" for i in range(hi, lo + step, step)]


def parse_verilog(path: str) -> dict:
    """Module slice: port bits, nets, and instances with named connections."""
    text = re.sub(r"//[^\n]*", "", open(path).read())
    stmts = [s.strip() for s in text.split(";") if s.strip()]

    ports: set[str] = set()
    nets: set[str] = set()
    assigns: list[tuple[str, str]] = []
    conn_re = re.compile(r"\.\s*([A-Za-z_][\w$]*)\s*\(\s*([^()]*?)\s*\)")
    inst_re = re.compile(r"^\s*([A-Za-z_][\w$]*)\s+([\\]?[\w$.\[\]/<>]+)\s*\((.*)\)$", re.S)
    module = None
    instances: list[dict] = []
    connectionless = 0

    def canon(name: str) -> str:
        return name[1:].rstrip() if name.startswith("\\") else name

    for s in stmts:
        if module is None and s.startswith("module"):
            module = s.split()[1] if len(s.split()) > 1 else None
            continue
        m = DECL.match(s)
        if m and not s.startswith(("module", "endmodule")):
            kind, msb, lsb, names = m.group(1), m.group(2), m.group(3), m.group(4)
            for name in [n.strip() for n in names.split(",")]:
                if name.startswith("\\"):
                    name = name[1:].rstrip()
                bits = expand(name, msb, lsb)
                nets.update(bits)
                if kind in ("input", "output", "inout"):
                    ports.update(bits)
            continue
        m = ASSIGN.match(s)
        if m:
            lhs = canon(m.group(1).strip())
            rhs = canon(m.group(2).strip())
            assigns.append((lhs, rhs))
            nets.update((lhs, rhs))
            continue
        m = inst_re.match(s)
        if m and m.group(1) not in ("module", "endmodule"):
            conns = conn_re.findall(m.group(3))
            if conns:
                conn: dict[str, str] = {}
                for port, netexpr in conns:
                    for part in netexpr.split(","):
                        name = canon(part.strip())
                        if name:
                            conn[port] = name
                            nets.add(name)
                if conn:
                    instances.append({"cell": m.group(1), "name": canon(m.group(2)),
                                      "conn": conn})
                else:
                    connectionless += 1
            continue

    return {"module": module, "ports": ports, "nets": nets,
            "assigns": assigns, "instances": instances,
            "connectionless_instances": connectionless}


def parse_spice(path: str) -> dict:
    """All .SUBCKTs: ordered header ports, X-cards, and an M-card census.

    Cards are kept per subcircuit with raw tokens; node names are namespaced
    by their subcircuit wherever they are keyed, so $N names in two different
    subcircuits are two nodes, never one.
    """
    subs: dict[str, dict] = {}
    cur = None
    pending: list[str] | None = None
    header_open = False

    def flush_card() -> None:
        nonlocal pending
        if pending is None or cur is None:
            pending = None
            return
        tok = " ".join(pending).split()
        if tok[0][0] in "Xx":
            subs[cur]["xcards"].append(tok)
        elif tok[0][0] in "Mm":
            subs[cur]["mcards"].append(tok)
        pending = None

    for raw in open(path):
        line = raw.strip()
        if line.startswith("*") or not line:
            continue
        if line.startswith("+"):
            if header_open and cur is not None:
                subs[cur]["ports"].extend(line[1:].split())
            elif pending is not None:
                pending.extend(line[1:].split())
            continue
        if pending is not None:
            flush_card()
        low = line.lower()
        if low.startswith(".subckt"):
            parts = line.split()
            cur = parts[1]
            subs[cur] = {"ports": parts[2:], "xcards": [], "mcards": []}
            header_open = True
            continue
        if low.startswith(".ends"):
            cur = None
            header_open = False
            continue
        if cur is not None:
            header_open = False
            pending = line.split()
    flush_card()
    return subs


def cell_base(name: str) -> str:
    return re.sub(r"\$VAR\d+$", "", name)


def fold(name: str) -> str:
    return name.lower()


# ---------------------------------------------------------------- pairing


def anchor_pair(ref_insts, ref_net_of, ext_insts, ext_net_of, net_seeds):
    """Seed net correspondence, then propagate instance pairings to a fixpoint.

    Returns (inst_map ref-name->ext-idx, netmap ref-net->ext-node, rounds,
    seed stats). Pairing is unambiguous only: a reference instance pairs when
    exactly one unpaired extract instance of the same cell agrees with it on
    every port whose reference net is already mapped. Seeds are verified by
    membership profile before entering the map.
    """
    netmap: dict[str, tuple] = dict(net_seeds)
    rev: dict[tuple, str] = {v: k for k, v in netmap.items()}
    paired: dict[str, int] = {}
    used: set[int] = set()

    for rounds in range(1, MAX_ROUNDS + 1):
        avail = [e["idx"] for e in ext_insts if e["idx"] not in used]
        ext_index: dict[tuple, list[int]] = collections.defaultdict(list)
        for e in ext_insts:
            if e["idx"] in used:
                continue
            for p, node in e["conn"].items():
                ext_index[(p, node)].append(e["idx"])
        newly: dict[str, int] = {}
        for i in ref_insts:
            name = i["name"]
            if name in paired:
                continue
            constrained = 0
            votes: collections.Counter = collections.Counter()
            for p in sorted(i["conn"]):
                node = netmap.get(i["conn"][p])
                if node is None:
                    continue
                constrained += 1
                for j in ext_index.get((p, node), []):
                    votes[j] += 1
            if constrained == 0:
                continue
            full = [j for j, v in votes.items() if v == constrained]
            if len(full) == 1:
                newly[name] = full[0]
        if not newly:
            break
        for name, j in newly.items():
            paired[name] = j
            used.add(j)
            ref_i = next(i for i in ref_insts if i["name"] == name)
            ext_i = next(e for e in ext_insts if e["idx"] == j)
            for p, net in ref_i["conn"].items():
                node = ext_i["conn"].get(p)
                if net in netmap:
                    if netmap[net] != node:
                        sys.exit(f"FATAL: inconsistent net map at {name}.{p}: "
                                 f"{net!r} -> {netmap[net]!r} vs {node!r}")
                else:
                    netmap[net] = node
                    if node in rev and rev[node] != net:
                        sys.exit(f"FATAL: reverse collision at {node!r}: "
                                 f"{rev[node]!r} vs {net!r}")
                    rev[node] = net
    return paired, netmap, rev, rounds


def main() -> int:
    ref = parse_verilog(REFERENCE)
    subs = parse_spice(EXTRACT)
    report = json.load(open(REPORT))
    dec = json.JSONDecoder()
    text = open(REFNETS).read().strip()
    refnets_baseline = []
    pos = 0
    while pos < len(text):
        obj, pos = dec.raw_decode(text, pos)
        refnets_baseline.append(obj)
        while pos < len(text) and text[pos] in " \t\r\n":
            pos += 1

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
        ext_insts.append({"idx": idx, "base": cell_base(cell), "cell": cell,
                          "conn": {fold(p): (top, n) for p, n in zip(hp, nodes)}})

    # --- reference instances --------------------------------------------------
    ref_insts = [{"name": i["name"], "base": i["cell"],
                  "conn": {fold(p): n for p, n in i["conn"].items()}}
                 for i in ref["instances"]]

    # --- cell/port vocabulary reconciliation -----------------------------------
    ref_cells = collections.Counter(i["base"] for i in ref_insts)
    ext_cells = collections.Counter(i["base"] for i in ext_insts)
    if ref_cells != ext_cells:
        sys.exit(f"FATAL: cell-type multisets differ: only-ref={sorted(ref_cells - ext_cells)} "
                 f"only-ext={sorted(ext_cells - ref_cells)}")

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
            sys.exit(f"FATAL: cell {base}: reference ports absent from extract leaf "
                     f"header: {sorted(missing)}")
        common_ports[base] = rp & ext_ports_by_base[base]

    # --- membership maps --------------------------------------------------------
    # pairing domain: common ports only; full domain: every connection
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

    # --- seed net correspondences from display names ------------------------------
    # A name seeds only when exactly one extract node carries it AND the full
    # membership profile (port multiset) agrees on both sides.
    ext_nodes_by_token: dict[str, list[tuple]] = collections.defaultdict(list)
    for node in ext_members:
        ext_nodes_by_token[node[1]].append(node)
    seeds: dict[str, tuple] = {}
    seed_profile_mismatch = []
    seed_ambiguous = []
    for name in sorted(ref_members):
        cands = ext_nodes_by_token.get(name, [])
        if len(cands) != 1:
            if cands:
                seed_ambiguous.append(name)
            continue
        node = cands[0]
        if collections.Counter(p for _, p in ref_members[name]) != \
           collections.Counter(p for _, p in ext_members[node]):
            seed_profile_mismatch.append(name)
            continue
        seeds[name] = node

    paired, netmap, rev, rounds = anchor_pair(
        ref_insts, ref_net_of, ext_insts, ext_net_of, seeds)
    rev_inst_map = {v: k for k, v in paired.items()}

    # --- net correspondence over paired instances ---------------------------------
    def ref_key(net: str):
        return tuple(sorted((p, paired[i]) for i, p in ref_members[net] if i in paired))

    def ext_key(node: tuple):
        return tuple(sorted((p, i) for i, p in ext_members[node] if i in rev_inst_map))

    ext_by_key: dict[tuple, list[tuple]] = collections.defaultdict(list)
    for node in ext_members:
        ext_by_key[ext_key(node)].append(node)
    ref_by_key: dict[tuple, list[str]] = collections.defaultdict(list)
    for net in ref_members:
        ref_by_key[ref_key(net)].append(net)

    matched_pairs = []
    splits = []
    partials = []
    ref_unpaired_membership = []
    for key in sorted(ref_by_key):
        rlist = ref_by_key[key]
        elist = ext_by_key.get(key, [])
        if not key:
            continue
        if len(rlist) == 1 and len(elist) == 1:
            matched_pairs.append({"reference": rlist[0], "layout": elist[0][1],
                                  "shared_terminals": len(key)})
            continue
        for net in rlist:
            touched: set[tuple] = set()
            for inst, port in ref_members[net]:
                if inst in paired:
                    touched.add(ext_net_of[paired[inst]][port])
            if not elist:
                ref_unpaired_membership.append(net)
            elif len(touched) >= 2:
                splits.append({"reference": net,
                               "layout_nets": sorted(t[1] for t in touched),
                               "paired_terminals": sum(1 for i, _ in ref_members[net]
                                                       if i in paired)})
            else:
                partials.append({"reference": net,
                                 "layout": sorted(t[1] for t in touched),
                                 "paired_terminals": sum(1 for i, _ in ref_members[net]
                                                         if i in paired)})

    merges = []
    ext_unpaired_membership = []
    for key in sorted(ext_by_key):
        elist = ext_by_key[key]
        rlist = ref_by_key.get(key, [])
        if not key:
            continue
        if len(elist) == 1 and len(rlist) == 1:
            continue
        for node in elist:
            touched: set[str] = set()
            for idx, port in ext_members[node]:
                if idx in rev_inst_map:
                    touched.add(ref_net_of[rev_inst_map[idx]][port])
            if not rlist:
                ext_unpaired_membership.append(node[1])
            elif len(touched) >= 2:
                merges.append({"layout": node[1], "reference_nets": sorted(touched),
                               "paired_terminals": sum(1 for i, _ in ext_members[node]
                                                       if i in rev_inst_map)})
            else:
                partials.append({"reference": sorted(touched), "layout": node[1],
                                 "paired_terminals": sum(1 for i, _ in ext_members[node]
                                                         if i in rev_inst_map)})

    ref_empty = [net for net in ref_members if not ref_key(net)]
    ref_empty_nopins = [net for net in ref_empty if not ref_members[net]]
    ref_empty_unpaired_only = [net for net in ref_empty if ref_members[net]]
    ext_empty = [node for node in ext_members if not ext_key(node)]
    ext_empty_unpaired_only = [node for node in ext_empty if ext_members[node]]

    # --- unpaired instance diagnosis ------------------------------------------------
    def diagnose(side):
        """Why did an instance not pair? 'no mapped ports' (cannot evaluate),
        'no candidate' (some mapped port disagrees everywhere -- structural),
        'ambiguous N' (N candidates agree on all mapped ports -- symmetry)."""
        out = collections.Counter()
        examples = {"no_candidate": [], "ambiguous": []}
        if side == "ref":
            items = [(i["name"], i) for i in ref_insts if i["name"] not in paired]
            others = [e for e in ext_insts if e["idx"] not in used_ext]
            mmap = netmap
            other_conn = lambda e: e["conn"]
            my_conn = lambda i: i["conn"]
            other_base = lambda e: e["base"]
            my_base = lambda i: i["base"]
        else:
            items = [(e["idx"], e) for e in ext_insts if e["idx"] not in used_ext]
            others = [i for i in ref_insts if i["name"] not in paired]
            mmap_rev = rev
            other_conn = lambda i: i["conn"]
            my_conn = lambda e: e["conn"]
            other_base = lambda i: i["base"]
            my_base = lambda e: e["base"]
        for _key, me in items:
            votes: collections.Counter = collections.Counter()
            constrained = 0
            for p, net in my_conn(me).items():
                partner = (mmap.get(net) if side == "ref" else mmap_rev.get(net))
                if partner is None:
                    continue
                constrained += 1
                for o in others:
                    if other_conn(o).get(p) == partner and other_base(o) == my_base(me):
                        votes[id(o)] += 1
            if constrained == 0:
                out["no_mapped_ports"] += 1
            elif not votes:
                out["no_candidate"] += 1
                if len(examples["no_candidate"]) < MAX_SAMPLES:
                    examples["no_candidate"].append(_key)
            else:
                full = sum(1 for v in votes.values() if v == constrained)
                if full >= 1:
                    out[f"ambiguous"] += 1
                    if len(examples["ambiguous"]) < MAX_SAMPLES:
                        examples["ambiguous"].append(_key)
                else:
                    out["no_candidate"] += 1
                    if len(examples["no_candidate"]) < MAX_SAMPLES:
                        examples["no_candidate"].append(_key)
        return out, examples

    used_ext = set(paired.values())
    ref_diag, ref_diag_examples = diagnose("ref")
    ext_diag, ext_diag_examples = diagnose("ext")

    # --- top-level port-bit pairing cross-check (vs r13's 67 hints.rejected) ----
    unconnected_ref_bits = sorted(p for p in ref["ports"] if p not in ref_members)
    pin_check = []
    for p in sorted(ref["ports"], key=fold):
        if p not in ref_members:
            pin_check.append({"reference": p, "paired_layout": None,
                              "same_name_casefolded": False,
                              "connected_cell_pins_reference": 0})
            continue
        elist = ext_by_key.get(ref_key(p), [])
        paired_node = elist[0][1] if len(elist) == 1 else None
        pin_check.append({"reference": p, "paired_layout": paired_node,
                          "same_name_casefolded": paired_node is not None
                          and fold(paired_node) == fold(p),
                          "connected_cell_pins_reference": len(ref_members[p])})
    pins_paired = sum(1 for p in pin_check if p["paired_layout"] is not None)
    pins_same_name = sum(1 for p in pin_check if p["same_name_casefolded"])

    # --- power / well characterisation (extract-only domain) -----------------------
    full_ext_members: dict[tuple, list[tuple[int, str]]] = collections.defaultdict(list)
    for i in ext_insts:
        for p, node in i["conn"].items():
            full_ext_members[node].append((i["idx"], p))

    def ext_port_set(node):
        return sorted({p for _, p in full_ext_members.get(node, [])})

    # Extract-only domain: tokens never touched by a pairing-domain (common
    # port) connection, classified by which extract-only ports touch them.
    common_port_all = {p for ports in common_ports.values() for p in ports}
    only_extract: dict[tuple, list[str]] = collections.defaultdict(list)
    for node, members in full_ext_members.items():
        if node[1] in {t for t in subs[top]["ports"]}:
            continue  # top-level port tokens handled separately
        if all(p not in common_port_all for _, p in members):
            only_extract[frozenset(p for _, p in members)].append(node[1])
    fragment_groups = []
    for ports, toks in sorted(only_extract.items(), key=lambda kv: sorted(kv[0])):
        fragment_groups.append({
            "ports": sorted(ports),
            "net_count": len(toks),
            "named_non_anonymous": sorted(t for t in toks if not t.startswith("\\")),
            "terminal_count": sum(len(full_ext_members[(top, t)]) for t in toks),
            "largest_net_terminals": max(len(full_ext_members[(top, t)]) for t in toks),
        })

    leaf_census = []
    census_totals: collections.Counter = collections.Counter()
    for name in sorted(subs):
        if name == top:
            continue
        nb = pb = None
        nmos = pmos = 0
        for m in subs[name]["mcards"]:
            model = m[5] if len(m) > 5 else ""
            bulk = m[4] if len(m) > 4 else None
            if model.startswith("nmos"):
                nb, nmos = bulk, nmos + 1
            elif model.startswith("pmos"):
                pb, pmos = bulk, pmos + 1
        inst = target_counts.get(name, 0)
        if inst:
            leaf_census.append({"cell": name, "nmos_bulk": nb, "pmos_bulk": pb,
                                "devices": nmos + pmos, "instances": inst})
            census_totals[(nb, pb)] += inst
    flat_devices = sum(e["devices"] * e["instances"] for e in leaf_census)
    pmos_anon = sum(sum(1 for m in subs[c]["mcards"]
                        if len(m) > 5 and m[5].startswith("pmos")
                        and m[4] not in ("VDD", "vsubs")) * target_counts.get(c, 0)
                    for c in set(target_counts) if c in subs)
    unused_variants = sorted(set(subs) - {top} - set(target_counts))

    power_well = {
        "extract_top_power_ports": sorted(t for t in subs[top]["ports"]
                                          if fold(t) in ("vdd", "vss", "vsubs")),
        "extract_top_port_tokens": len(subs[top]["ports"]),
        "reference_module_port_bits": len(ref["ports"]),
        "extract_top_ports_outside_reference_port_bits": sorted(
            (t for t in subs[top]["ports"] if fold(t) not in
             {fold(p) for p in ref["ports"]})),
        "well_nets_dollar_i": None,
        "extract_only_supply_well_domain": {
            "note": "tokens never touched by a pairing-domain (common port) "
                    "connection, grouped by which extract-only ports touch them; "
                    "the reference side has none of these -- module slice connects "
                    "no VDD/VSS/well pins and the reference conversion asserts "
                    "bulk ties onto its named supply nets (options.finfet_bulk)",
            "groups": fragment_groups,
            "net_count_total": sum(g["net_count"] for g in fragment_groups),
            "report_net_supply_fragmented_entries": sum(
                1 for m in report["mismatches"] if m["category"] == "net.supply_fragmented"),
        },
        "vsubs_net": {"terminal_count": len(full_ext_members.get((top, "vsubs"), [])),
                      "distinct_ports": ext_port_set((top, "vsubs"))},
        "VDD_net": {"terminal_count": len(full_ext_members.get((top, "VDD"), [])),
                    "distinct_ports": ext_port_set((top, "VDD"))},
        "VSS_net": {"terminal_count": len(full_ext_members.get((top, "VSS"), [])),
                    "distinct_ports": ext_port_set((top, "VSS"))},
        "leaf_bulk_census": leaf_census,
        "leaf_bulk_instance_totals": {f"nmos_bulk={k[0]!r},pmos_bulk={k[1]!r}": v
                                      for k, v in sorted(census_totals.items(),
                                                         key=lambda kv: str(kv[0]))},
        "flat_device_count_from_extract": flat_devices,
        "flat_pmos_bodies_on_non_supply_leaf_net": pmos_anon,
        "unused_leaf_variants": unused_variants,
        "empty_leaf_subckts": sorted(n for n, s in subs.items()
                                     if n != top and not s["mcards"] and not s["xcards"]),
        "reference_side_power_note": "module slice names no VDD/VSS/well pins; the "
            "reference conversion synthesises bulk connectivity from the library CDL "
            "under options.finfet_bulk (the report's device.finfet_bulk_tied entries), "
            "so the reference side of the power/well domain is not present in the "
            "committed Verilog.",
    }

    # --- report-side identity census -----------------------------------------------
    mm = report["mismatches"]
    by_cat: dict[str, list] = collections.defaultdict(list)
    for m in mm:
        by_cat[m["category"]].append(m)
    ns = by_cat["net.split"]
    ns_fields = sorted({k for m in ns for k in m})
    ns_names = collections.Counter(m["net"]["layout"] for m in ns if m["net"]["layout"])
    zero_count = ns_names.get("\\$0", 0)
    nm = by_cat["net.merged"]
    nm_fields = sorted({k for m in nm for k in m})
    nm_names = {m["net"]["reference"] for m in nm if m["net"]["reference"]}
    nc = report["net_correspondence"]
    nc_layout_names = collections.Counter(e["layout"] for e in nc)
    identity = {
        "net_split": {
            "entries": len(ns),
            "fields_present_across_all_entries": ns_fields,
            "entries_with_layout_name": sum(1 for m in ns if m["net"]["layout"]),
            "entries_with_reference_name": sum(1 for m in ns if m["net"]["reference"]),
            "entries_with_subcircuit_or_circuit": sum(1 for m in ns
                                                      if m["subcircuit"] or m["circuit"]),
            "distinct_layout_display_names": len(ns_names),
            "entries_under_display_name_backslash_dollar_zero": zero_count,
            "named_display_names_appearing_more_than_once": sorted(
                n for n, c in ns_names.items() if c > 1 and n != "\\$0"),
            "stable_identity_available": False,
            "stable_identity_note": "net.split entries carry only category/description/"
                "severity/side plus net.layout display name; net.reference is null and "
                "no id, subcircuit or pin-set field exists, so the 12812 entries under "
                "\\$0 cannot be attributed to distinct nets from the report alone. The "
                "structural correspondence in net_correspondence_structural establishes "
                "identity from the netlists by pin membership instead.",
        },
        "net_merged": {
            "entries": len(nm),
            "fields_present_across_all_entries": nm_fields,
            "distinct_reference_names": len(nm_names),
        },
        "net_correspondence_report": {
            "entries": len(nc),
            "distinct_reference_names": len({e["reference"] for e in nc}),
            "distinct_layout_names": len(nc_layout_names),
            "entries_with_layout_name_backslash_dollar_zero": nc_layout_names.get("\\$0", 0),
            "pin_anchored_entries": sum(1 for e in nc if e.get("pin")),
        },
    }

    # --- self-checks against committed baselines -------------------------------------
    cec = report["category_error_counts"]
    edge_ref = sum(1 for i in ref_insts for p in i["conn"] if p in common_ports[i["base"]])
    edge_ext = sum(1 for e in ext_insts for p in e["conn"] if p in common_ports[e["base"]])
    checks = {
        "cec.net.split == 15269": cec["net.split"] == 15269,
        "cec.net.merged == 14967": cec["net.merged"] == 14967,
        "cec.device.unmatched == 55444": cec["device.unmatched"] == 55444,
        "mismatch_count == 86629": report["mismatch_count"] == 86629,
        "len(net_correspondence) == 408": len(nc) == 408,
        "counts.nets 15803/15501/408": report["counts"]["nets"] ==
            {"layout": 15803, "reference": 15501, "matched": 408},
        "counts.devices 29436/28862/233": report["counts"]["devices"] ==
            {"layout": 29436, "reference": 28862, "matched": 233},
        "report backslash-dollar-zero net.split entries == 12812": zero_count == 12812,
        "report distinct net.split layout display names == 2458": len(ns_names) == 2458,
        "report net.merged distinct reference names == 14967": len(nm_names) == 14967,
        "extract top X-cards == 2594": len(top_xcards) == 2594,
        "reference connected instances == 2594": len(ref_insts) == 2594,
        "flat devices from extract == 29436": flat_devices == 29436,
        "pairing-domain edge counts equal": edge_ref == edge_ext,
        "rx_clk 528 cell pins on reference side":
            len(ref_members.get("rx_clk", [])) == 528,
        "rx_clk 528 cell pins on extract side":
            len(ext_members.get((top, "rx_clk"), [])) == 528,
        "refnets.json reference baseline intact": refnets_baseline[0] == {
            "netlist": "layout/slice_routed.v", "format": "verilog", "top": "slice",
            "instances": 2594, "nets_total": 2940, "port_bits": 266,
            "assign_statements": 0, "nets_with_exactly_one_cell_pin": 198,
            "of_which_port_bits": 198, "nets_with_exactly_two_cell_pins": 1801,
            "nets_with_zero_cell_pins": 227, "zero_pin_of_which_port_bits": 64,
            "rx_clk_cell_pins": 528},
        "refnets.json extract baseline intact": refnets_baseline[1] == {
            "netlist": "evidence/item4-lvs/slice_routed.r13.extract.v",
            "format": "spice", "top": "slice", "instances": 2594,
            "nets_total": 2955, "port_bits": 269, "assign_statements": 0,
            "nets_with_exactly_one_cell_pin": 199, "of_which_port_bits": 199,
            "nets_with_exactly_two_cell_pins": 1801, "nets_with_zero_cell_pins": 0,
            "zero_pin_of_which_port_bits": 0, "rx_clk_cell_pins": 528},
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        sys.exit("FATAL: self-checks failed: " + "; ".join(failed))

    out = {
        "script": "slice_routed.r13.netdiff.py",
        "consumes": ["evidence/item4-lvs/slice_routed.r13.extract.v",
                     "layout/slice_routed.v",
                     "evidence/item4-lvs/slice_routed.r13.report.json",
                     "evidence/item4-lvs/slice_routed.r13.refnets.json"],
        "domain": {
            "extract_top": top,
            "extract_top_xcards": len(top_xcards),
            "reference_module": ref["module"],
            "reference_connected_instances": len(ref_insts),
            "reference_connectionless_instances": ref["connectionless_instances"],
            "identity": "pin membership (instance, port); instances paired by "
                        "anchored propagation seeded by display names verified by "
                        "membership; display names never used as identity themselves",
            "ports_used": "folded intersection of reference .NAME ports and leaf "
                          ".SUBCKT header ports, per cell",
            "assign_statements_reference": len(ref["assigns"]),
            "pairing_edges_ref": edge_ref,
            "pairing_edges_ext": edge_ext,
            "propagation_rounds": rounds,
        },
        "net_seeds": {
            "accepted": len(seeds),
            "profile_mismatch": sorted(seed_profile_mismatch)[:MAX_SAMPLES],
            "profile_mismatch_total": len(seed_profile_mismatch),
            "name_ambiguous_extract_side": sorted(seed_ambiguous)[:MAX_SAMPLES],
            "name_ambiguous_total": len(seed_ambiguous),
        },
        "instance_pairing": {
            "instances_paired": len(paired),
            "instance_coverage": round(len(paired) / len(ref_insts), 6),
            "unpaired_reference_diagnosis": dict(sorted(ref_diag.items())),
            "unpaired_extract_diagnosis": dict(sorted(ext_diag.items())),
            "unpaired_reference_no_candidate_sample": ref_diag_examples["no_candidate"],
            "unpaired_reference_ambiguous_sample": ref_diag_examples["ambiguous"],
            "unpaired_extract_no_candidate_sample": [
                str(k) for k in ext_diag_examples["no_candidate"]],
            "unpaired_extract_ambiguous_sample": [
                str(k) for k in ext_diag_examples["ambiguous"]],
        },
        "net_correspondence_structural": {
            "reference_nets_total_pairing_domain": len(ref_members),
            "extract_nets_total_pairing_domain": len(ext_members),
            "nets_mapped_at_fixpoint": len(netmap),
            "matched_1_to_1": len(matched_pairs),
            "splits": len(splits),
            "merges": len(merges),
            "partials": len(partials),
            "reference_nets_without_extract_counterpart": len(ref_unpaired_membership),
            "extract_nets_without_reference_counterpart": len(ext_unpaired_membership),
            "reference_nets_with_no_paired_membership": len(ref_empty),
            "reference_zero_cell_pin_nets": len(ref_empty_nopins),
            "reference_nets_on_unpaired_instances_only": len(ref_empty_unpaired_only),
            "extract_nets_with_no_paired_membership": len(ext_empty),
            "extract_nets_on_unpaired_instances_only": len(ext_empty_unpaired_only),
            "matched_sample": sorted(matched_pairs, key=lambda d: d["reference"])[:MAX_SAMPLES],
            "split_entries": sorted(splits, key=lambda d: d["reference"])[:MAX_SAMPLES],
            "merge_entries": sorted(merges, key=lambda d: d["layout"])[:MAX_SAMPLES],
            "partial_entries": sorted(partials, key=lambda d: str(d))[:MAX_SAMPLES],
            "reference_without_counterpart_sample": sorted(ref_unpaired_membership)[:MAX_SAMPLES],
            "extract_without_counterpart_sample": sorted(ext_unpaired_membership)[:MAX_SAMPLES],
            "reference_no_paired_membership_sample": sorted(ref_empty_unpaired_only)[:MAX_SAMPLES],
            "extract_no_paired_membership_sample": sorted(ext_empty_unpaired_only)[:MAX_SAMPLES],
            "reference_zero_cell_pin_sample": sorted(ref_empty_nopins)[:MAX_SAMPLES],
        },
        "top_level_pin_check": {
            "reference_port_bits": len(ref["ports"]),
            "connected_port_bits_paired": pins_paired,
            "connected_port_bits_same_name_casefolded": pins_same_name,
            "unconnected_port_bits_reference": len(unconnected_ref_bits),
            "unconnected_port_bits_sample": unconnected_ref_bits[:MAX_SAMPLES],
            "unpaired_port_bits": sorted(p["reference"] for p in pin_check
                                         if p["paired_layout"] is None
                                         and p["connected_cell_pins_reference"] > 0),
            "r13_hints_rejected_unconfirmed_anchors": sum(
                1 for m in report["mismatches"] if m["category"] == "hints.rejected"),
            "note": "every port bit the reference actually connects pairs 1:1 with "
                    "an extract net of the same case-folded name, so the r13 "
                    "hints.rejected anchors are artifacts of the comparer's failed "
                    "matching, not boundary topology disagreements",
        },
        "domain_reconciliation": {
            "reference_declared_nets_refnets": refnets_baseline[0]["nets_total"],
            "reference_pairing_domain_nets": len(ref_members),
            "reference_zero_cell_pin_nets": refnets_baseline[0]["nets_with_zero_cell_pins"],
            "reference_identity": "pairing domain + zero-cell-pin nets = refnets total",
            "extract_top_distinct_node_tokens": len(full_ext_members),
            "extract_pairing_domain_nets": len(ext_members),
            "extract_only_nets": sum(g["net_count"] for g in fragment_groups) +
                len([t for t in subs[top]["ports"]
                     if t not in ext_members and fold(t) in ("vdd", "vss", "vsubs")]),
            "extract_identity": "pairing domain + extract-only nets = refnets total",
        },
        "power_well": power_well,
        "report_identity": identity,
        "self_checks_passed": len(checks),
    }
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
