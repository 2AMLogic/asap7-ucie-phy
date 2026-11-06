#!/usr/bin/env python3
"""Self-test for regen.py --check-input (stdlib only; run as `python3 -I layout/pnr/test_check_input.py`).

Covers match (0), drift (3), missing or unparseable input (2), and pins
tie_constants output against a fixture hash so a change to it cannot go unnoticed."""
import hashlib
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

FIXTURE = """module top (a, y);
  input a;
  output y;
  FOO u0 (.A(a), .S(1'h1), .R(1'h0), .Y(y));
endmodule
"""
# sha256 of tie_constants(FIXTURE); update deliberately if tie_constants changes.
FIXTURE_HASH = "sha256:cd1222153d12f8d728bf16298e044b67448c0d7d26f90c3dc5bfe4468f91ec8f"

fails = []


def expect(name, got, want):
    if got != want:
        fails.append(f"{name}: got {got!r}, want {want!r}")


def run(netlist, recorded, report_text=None):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        if netlist is not None:
            (t / "n.v").write_text(netlist)
        (t / "req.json").write_text(json.dumps({"netlist": "n.v"}))
        rep = t / "rep.json"
        rep.write_text(report_text if report_text is not None else json.dumps(
            {"provenance": {"input": {"content_hash": recorded}}}))
        buf = io.StringIO()
        return regen.check_input(t / "req.json", rep, buf), buf.getvalue()


tied = regen.tie_constants(FIXTURE)
expect("tie_constants hash pin",
       "sha256:" + hashlib.sha256(tied.encode()).hexdigest(), FIXTURE_HASH)
expect("tie rewrites literals", "1'h" in tied, False)
rc, _ = run(FIXTURE, FIXTURE_HASH)
expect("match", rc, 0)
rc, msg = run(FIXTURE, "sha256:" + "0" * 64)
expect("drift", rc, 3)
expect("drift names both hashes", FIXTURE_HASH in msg and "0" * 64 in msg, True)
expect("drift names remedy", "regen.py" in msg, True)
rc, _ = run(None, FIXTURE_HASH)
expect("missing netlist", rc, 2)
rc, _ = run(FIXTURE, None, report_text="{not json")
expect("unparseable report", rc, 2)
rc, _ = run(FIXTURE, None, report_text="{}")
expect("missing hash key", rc, 2)

for f in fails:
    print("FAIL", f, file=sys.stderr)
sys.exit(1 if fails else 0)
