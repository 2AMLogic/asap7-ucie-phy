#!/usr/bin/env python3
"""r13 trace, netlist half: one-pin-net statistics for structural gate netlists.

The flawed r13 record cited reference-side figures ("6 nets with exactly one
cell pin", "1649 with exactly two") that this script cannot reproduce from the
committed netlist; the review asks for a committed counting script and a
committed extract netlist, so both sides are re-derived here. The script reads
structural Verilog (the committed reference layout/slice_routed.v) and SPICE
(the klt extract output, whose top circuit uses X-card instances).

Counting domain, stated explicitly:
- "cell pins" are instance connections (Verilog .P(NET), SPICE X-card nodes);
  module/subckt ports are not cell pins. A port bit that reaches no cell is a
  net with zero cell pins.
- vector ports/wires are expanded into one net per bit.
- `assign` aliasing, if a netlist contains any, is reported and its member
  nets are unioned before counting. SPICE has no assigns.
- the SPICE top circuit is the .SUBCKT with the most X-cards.

Usage: python3 slice_routed.r13.refnets.py <netlist> [<netlist2> ...]
Writes one JSON object per netlist to stdout.
"""

from __future__ import annotations

import collections
import json
import re
import sys

DECL = re.compile(r"^\s*(input|output|inout|wire)\b\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?(.+?)$", re.S)
ASSIGN = re.compile(r"^\s*assign\s+([^=;]+?)\s*=\s*([^;]+?)$", re.S)


def expand(name: str, msb: str | None, lsb: str | None) -> list[str]:
    if msb is None:
        return [name]
    hi, lo = int(msb), int(lsb)
    step = -1 if hi >= lo else 1
    return [f"{name}[{i}]" for i in range(hi, lo + step, step)]


def finish(path: str, fmt: str, top: str | None, instances: int,
           ports: set[str], cell_pins: collections.Counter, nets: set[str],
           assigns: list[tuple[str, str]]) -> dict:
    """Union assign aliases, then canonically count one/two/zero-pin nets."""
    alias: dict[str, str] = {}

    def find(x: str) -> str:
        alias.setdefault(x, x)
        while alias[x] != x:
            alias[x] = alias[alias[x]]
            x = alias[x]
        return x

    for a, b in assigns:
        ra, rb = find(a), find(b)
        if ra != rb:
            alias[rb] = ra
    pins: collections.Counter[str] = collections.Counter()
    for name, n in cell_pins.items():
        pins[find(name)] += n

    def canon_count(pred) -> tuple[int, int]:
        total = portbits = 0
        seen: set[str] = set()
        for name in nets:
            root = find(name)
            if root in seen or not pred(pins[root]):
                continue
            seen.add(root)
            total += 1
            if name in ports:
                portbits += 1
        return total, portbits

    one_cell_pin, one_cell_pin_port = canon_count(lambda n: n == 1)
    two_cell_pins, _ = canon_count(lambda n: n == 2)
    zero_cell_pins, zero_cell_pins_port = canon_count(lambda n: n == 0)

    return {
        "netlist": path,
        "format": fmt,
        "top": top,
        "instances": instances,
        "nets_total": len({find(n) for n in nets}),
        "port_bits": len(ports),
        "assign_statements": len(assigns),
        "nets_with_exactly_one_cell_pin": one_cell_pin,
        "of_which_port_bits": one_cell_pin_port,
        "nets_with_exactly_two_cell_pins": two_cell_pins,
        "nets_with_zero_cell_pins": zero_cell_pins,
        "zero_pin_of_which_port_bits": zero_cell_pins_port,
        "rx_clk_cell_pins": pins[find("rx_clk")],
    }


def parse_verilog(path: str) -> dict:
    text = re.sub(r"//[^\n]*", "", open(path).read())
    stmts = [s.strip() for s in text.split(";") if s.strip()]

    ports: set[str] = set()
    nets: set[str] = set()
    assigns: list[tuple[str, str]] = []
    conn_re = re.compile(r"\.\s*([A-Za-z_][\w$]*)\s*\(\s*([^()]*?)\s*\)")
    inst_re = re.compile(r"^\s*([A-Za-z_][\w$]*)\s+([\\]?[\w$.\[\]/<>]+)\s*\((.*)\)$", re.S)
    instances = 0
    cell_pins: collections.Counter[str] = collections.Counter()
    module = None

    for s in stmts:
        if module is None and s.startswith("module"):
            module = s.split()[1] if len(s.split()) > 1 else None
            continue
        m = DECL.match(s)
        if m and not s.startswith(("module", "endmodule")):
            kind, msb, lsb, names = m.group(1), m.group(2), m.group(3), m.group(4)
            # comma-separated identifier list; escaped ids keep their trailing space
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
            lhs = m.group(1).strip().lstrip("\\").rstrip()
            rhs = m.group(2).strip().lstrip("\\").rstrip()
            assigns.append((lhs, rhs))
            nets.update((lhs, rhs))
            continue
        m = inst_re.match(s)
        if m and m.group(1) not in ("module", "endmodule"):
            conns = conn_re.findall(m.group(3))
            if conns:
                instances += 1
                for _port, netexpr in conns:
                    for part in netexpr.split(","):
                        name = part.strip().lstrip("\\").rstrip()
                        if name:
                            nets.add(name)
                            cell_pins[name] += 1
            continue

    return finish(path, "verilog", module, instances, ports, cell_pins, nets, assigns)


def parse_spice(path: str) -> dict:
    # subckts[name] = list of X-card node token lists; ports[name] = header nodes
    subckts: dict[str, list[list[str]]] = collections.defaultdict(list)
    ports: dict[str, list[str]] = {}
    current = None
    header_open = False  # '+' lines still extend the .SUBCKT port list
    pending: list[str] = []

    def flush_x() -> None:
        joined = " ".join(pending).split()
        if current is not None and len(joined) >= 3:
            # X<name> <nodes...> <subckt name> -> nodes are the middle tokens
            subckts[current].append(joined[1:-1])

    for raw in open(path):
        line = raw.strip()
        if line.startswith("*") or not line:
            continue
        if line.startswith("+"):
            if header_open and current is not None:
                ports[current].extend(line[1:].split())
            else:
                pending.append(line[1:].strip())
            continue
        if pending:
            flush_x()
            pending = []
        low = line.lower()
        if low.startswith(".subckt"):
            parts = line.split()
            current = parts[1]
            ports[current] = parts[2:]
            header_open = True
            continue
        if low.startswith(".ends"):
            current = None
            header_open = False
            continue
        if current:
            header_open = False
            if line[0] in "Xx":
                pending.append(line)
    flush_x()

    # top = the subckt with the most X-cards
    top = max(subckts, key=lambda name: len(subckts[name]))
    cell_pins: collections.Counter[str] = collections.Counter()
    nets: set[str] = set()
    instances = 0
    for card in subckts[top]:
        instances += 1
        for node in card:
            nets.add(node)
            cell_pins[node] += 1
    nets.update(ports[top])
    return finish(path, "spice", top, instances, set(ports[top]), cell_pins,
                  nets, [])


def main() -> int:
    for path in sys.argv[1:]:
        probe = open(path).read(4096)
        if re.search(r"^\.subckt\b", probe, re.I | re.M) or re.match(r"^\*", probe):
            result = parse_spice(path)
        else:
            result = parse_verilog(path)
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
