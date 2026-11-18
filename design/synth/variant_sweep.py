#!/usr/bin/env python3
"""Trial-synthesize slice with variant `constraints` and take the pre-route `klt sta` sweep (issue #236).

Scratch only: nothing is written into the repo. Run as
    KLT='uvx --from klayout-tools==0.9.2 klt' PDK_ARCHIVE=<lambdapdk-0.2.17.tar.gz> \
        python3 -I design/synth/variant_sweep.py variants.json out.json
variants.json maps a name to a full `constraints` object (see design/synth/slice.synth.json).
Needs yosys and openroad on PATH. Reuses design/lambdapdk.py and sta/regen.py.
"""
import sys, json, pathlib, subprocess, tempfile, importlib.util, os, shlex, re
sys.dont_write_bytecode = True
REPO = pathlib.Path(__file__).resolve().parents[2]
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
L = load(REPO/"design/lambdapdk.py", "lp")
SR = load(REPO/"sta/regen.py", "sr")
KLT = shlex.split(os.environ.get("KLT", "uvx --from klayout-tools==0.9.2 klt"))
ARCH = os.environ.get("PDK_ARCHIVE")  # pinned lambdapdk archive; None downloads to a scratch dir
variants = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = {}
for name, constraints in variants.items():
    with tempfile.TemporaryDirectory(prefix="s236-") as tmp:
        t = pathlib.Path(tmp)
        arch = L.fetch(t, ARCH)
        # synth
        r = t/"spdk"; (r/"lib").mkdir(parents=True)
        lib = re.sub(r"^area : ([0-9.]+)$", r"area : \1;", L.merged_liberty(arch), flags=re.M)
        (r/"lib"/"asap7sc7p5t_rvt_TT.lib").write_text(lib)
        (r/"klt-pdk.json").write_text(json.dumps({"schema_version":1,"variant":"asap7","liberty":{"asap7sc7p5t_rvt":{"tt":"lib/asap7sc7p5t_rvt_TT.lib"}}}))
        req = json.loads((REPO/"design/synth/slice.synth.json").read_text())
        req["sources"] = [str((REPO/"design/synth"/s).resolve()) for s in req["sources"]]
        req["outputs"] = {"dir": str(t/"run")}
        req["constraints"] = constraints
        (t/"req.json").write_text(json.dumps(req))
        cp = subprocess.run(KLT+["synthesize", str(t/"req.json"), "--pdk-root", str(r), "--format", "json"], capture_output=True, text=True, cwd=REPO)
        if cp.returncode: out[name] = {"synth_error": (cp.stdout+cp.stderr)[-500:]}; continue
        net = (t/"run"/"slice_synth.v").read_text()
        bad = ["AO33x2","OAI22xp33","BUFx4f","CKINVDCx9p33","BUFx4","BUFx2","ICGx5p33DC","ICGx4DC","ICGx6p67DC","ICGx2p67DC"]
        dev = {m: len(re.findall(rf"^\s*{m}_ASAP7_75t_R\s", net, re.M)) for m in bad}
        dev = {k:v for k,v in dev.items() if v}
        # sta
        libs, others = SR.read_members(arch)
        rr = t/"pdk"; (rr/"lib").mkdir(parents=True); (rr/"lef").mkdir()
        liberty = {}
        for c in SR.CORNERS:
            (rr/"lib"/f"asap7sc7p5t_rvt_{c}.lib").write_text(L.merged({g: libs[(c,g)] for g in L.GROUPS})); liberty[c.lower()] = f"lib/asap7sc7p5t_rvt_{c}.lib"
        views = {}
        for key, nm in SR.LEFS.items():
            (rr/"lef"/pathlib.Path(nm).name).write_bytes(others[nm]); views[key] = f"lef/{pathlib.Path(nm).name}"
        views["tech_lef"] = {"nom": views["tech_lef"]}
        (rr/"klt-pdk.json").write_text(json.dumps({"schema_version":1,"variant":"asap7","liberty":{"asap7sc7p5t_rvt":liberty},"views":{"asap7sc7p5t_rvt":views}}))
        (t/"slice_synth.v").write_text(net)
        sreq = json.loads((REPO/"sta/slice.sta.json").read_text()); sreq["verilog"] = str(t/"slice_synth.v")
        (t/"sta.json").write_text(json.dumps(sreq))
        cp = subprocess.run(KLT+["sta", str(t/"sta.json"), "--pdk-root", str(rr), "--format", "json"], capture_output=True, text=True, cwd=REPO)
        rep = json.loads(cp.stdout)
        out[name] = {"deviating_cells_in_netlist": dev, "cells_total": len(re.findall(r"^\s*\w+_ASAP7_75t_R\s", net, re.M)),
            "corners": [{k: c.get(k) for k in ("corner","fmax_mhz","worst_slack_ns","setup_violation_count","hold_violation_count","worst_hold_slack_ns")} for c in rep.get("corners", [])],
            "keys": sorted(rep["corners"][0].keys()) if rep.get("corners") else None}
    print(name, json.dumps(out[name]), flush=True)
pathlib.Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
