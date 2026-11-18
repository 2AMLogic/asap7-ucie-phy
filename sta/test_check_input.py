#!/usr/bin/env python3
"""Self-test for regen.py --check-input (stdlib only; run as `python3 -I sta/test_check_input.py`).

Covers match (0), drift (3), missing or unparseable input (2), and pins the
default record (--check-input with no --report) to the current adopted one so a
record rotation cannot go unnoticed."""
import importlib.util
import io
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("regen", HERE / "regen.py")
regen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regen)

import hashlib

NETLIST = """module slice (clk, a, y);
  input clk;
  input a;
  output y;
  FOO u0 (.A(a), .CK(clk), .Y(y));
endmodule
"""
NETLIST_HASH = "sha256:" + hashlib.sha256(NETLIST.encode()).hexdigest()

fails = []


def expect(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


def run(netlist, recorded, report_text=None, report=None):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        if netlist is not None:
            (t / "n.v").write_text(netlist)
        (t / "req.json").write_text(json.dumps({"verilog": "n.v"}))
        rep = t / "rep.json"
        rep.write_text(report_text if report_text is not None else json.dumps(
            {"provenance": {"input": {"content_hash": recorded}}}))
        buf = io.StringIO()
        rc = regen.check_input(t / "req.json", report or rep, buf)
        return rc, buf.getvalue()


rc, _ = run(NETLIST, NETLIST_HASH)
expect("match", rc, 0)
rc, msg = run(NETLIST, "sha256:" + "0" * 64)
expect("drift", rc, 3)
expect("drift names both hashes", NETLIST_HASH in msg and "0" * 64 in msg, True)
expect("drift names remedy", "regen.py" in msg, True)
rc, _ = run(None, NETLIST_HASH)
expect("missing netlist", rc, 2)
rc, _ = run(NETLIST, None, report_text="{not json")
expect("unparseable report", rc, 2)
rc, _ = run(NETLIST, None, report_text="{}")
expect("missing hash key", rc, 2)
rc, _ = run(NETLIST, None, report_text=json.dumps({"provenance": {"input": {}}}))
expect("empty input block", rc, 2)

expect("default record is the current one", regen.CURRENT_RECORD, "slice.sta.r7.report.json")
expect("current record exists", (HERE / regen.CURRENT_RECORD).is_file(), True)

for f in fails:
    print("FAIL", f, file=sys.stderr)
sys.exit(1 if fails else 0)
