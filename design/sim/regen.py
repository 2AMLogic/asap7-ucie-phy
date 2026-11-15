#!/usr/bin/env python3
"""Regenerate design/sim/tx_cell.osdi.sp with klt's BSIM-CMG netlist adapter.

Re-runs the OSDI adaptation decision 0010 records for the drawn TX cell
(`klayout_tools.asap7_bsimcmg.adapt_extracted_netlist`, the same call that
produced the committed file): design/netlist/tx_cell.sp in,
design/sim/tx_cell.osdi.sp out. Without it the adapted netlist is bound to no
drift check -- `gen_cells.py --check` re-renders only design/netlist/*.sp --
so tx_cell.osdi.sp would keep an outdated topology if tx_cell moved while
`sim/tx_cell.batch.report.json` still reads as recorded evidence.

Needs `klayout_tools` importable: run as plain `python3`, not `-I` (-I hides
the package, on the worker and in the klt interpreter alike; see
layout/README.md).

    regen.py            overwrite design/sim/tx_cell.osdi.sp
    regen.py --check    exit 0 if it reproduces byte-for-byte, 3 if it drifted
"""
import argparse
import pathlib
import sys

from klayout_tools.asap7_bsimcmg import adapt_extracted_netlist

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
SOURCE = REPO / "design" / "netlist" / "tx_cell.sp"
TARGET = HERE / "tx_cell.osdi.sp"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    fresh = adapt_extracted_netlist(SOURCE.read_text())
    if args.check:
        if not TARGET.is_file() or TARGET.read_text() != fresh:
            print(f"drifted: {TARGET}", file=sys.stderr)
            return 3
        return 0
    TARGET.write_text(fresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
