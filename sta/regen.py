#!/usr/bin/env python3
"""Regenerate sta/slice.sta.report.json with `klt sta` (stdlib only; run as `python3 -I`).

Pre-route record: `klt sta` links design/netlist/slice_asap7.v with no placement or
routing (geometry_source "netlist_estimate"). Needs `openroad` on PATH and `klt` (override
with $KLT, e.g. 'uvx --from klayout-tools==0.8.0 klt'). The pinned lambdapdk archive
(spec/asap7-bringup.md) is passed with --pdk-archive or downloaded to a scratch directory;
nothing from it is written into the repo.

For each RVT corner (tt, ss, ff) the five Liberty cell groups are concatenated under the
first header (design/lambdapdk.py, shared with design/synth/regen.py), because klt's list-merge refuses the
differing headers. The merged file therefore takes the AO group's operating condition;
the per-file nom_voltage/nom_temperature of every loaded group is read from the originals
and written to sta/operating-conditions.json, which is what the FF anomaly report cites.

    regen.py            overwrite the committed report and operating-conditions record
"""
import argparse
import gzip
import importlib.util
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
REQUEST = HERE / "slice.sta.json"
REPORT = HERE / "slice.sta.report.json"
OPCOND = HERE / "operating-conditions.json"

def _load_lambdapdk():
    path = REPO / "design" / "lambdapdk.py"
    spec = importlib.util.spec_from_file_location("lambdapdk", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _load_lambdapdk()

CORNERS = ["TT", "SS", "FF"]
LEFS = {"cell_lef": L.ROOT + "libs/asap7sc7p5t_rvt/lef/asap7sc7p5t_28_R.lef",
        "tech_lef": L.ROOT + "base/apr/asap7_tech.lef"}


def header_value(text, key):
    m = re.search(rf"^\s*{key}\s*:\s*([0-9.]+)\s*;", text, re.M)
    return float(m.group(1)) if m else None


def read_members(archive):
    want = {f"{L.NLDM}asap7sc7p5t_{g}_RVT_{c}_nldm.lib.gz": (c, g) for c in CORNERS for g in L.GROUPS}
    libs = {}
    others = {}
    with tarfile.open(archive) as tar:
        for m in tar:
            if m.name in want:
                c, g = want[m.name]
                libs[(c, g)] = gzip.decompress(tar.extractfile(m).read()).decode()
            elif m.name in LEFS.values():
                others[m.name] = tar.extractfile(m).read()
    if len(libs) != len(CORNERS) * len(L.GROUPS) or set(others) != set(LEFS.values()):
        sys.exit("pinned archive is missing RVT Liberty groups or LEF")
    return libs, others


def operating_conditions(libs):
    rec = {}
    for c in CORNERS:
        files = {}
        for g in L.GROUPS:
            t = libs[(c, g)]
            files[f"asap7sc7p5t_{g}_RVT_{c}_nldm.lib.gz"] = {
                "nom_voltage": header_value(t, "nom_voltage"),
                "nom_temperature": header_value(t, "nom_temperature")}
        points = {(v["nom_voltage"], v["nom_temperature"]) for v in files.values()}
        rec[c] = {"files": files, "uniform": len(points) == 1}
    return {"schema": "asap7-ucie-phy.sta.operating-conditions/1",
            "source": f"lambdapdk v0.2.17 sha256:{L.SHA256}",
            "note": "read from each original Liberty header; the merged Liberty handed to "
                    "klt sta carries the AO group's header only",
            "corners": rec}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdk-archive")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="slice-sta-") as tmp:
        scratch = pathlib.Path(tmp)
        libs, others = read_members(L.fetch(scratch, args.pdk_archive))
        root = scratch / "pdk"
        (root / "lib").mkdir(parents=True)
        (root / "lef").mkdir()
        liberty = {}
        for c in CORNERS:
            (root / "lib" / f"asap7sc7p5t_rvt_{c}.lib").write_text(L.merged({g: libs[(c, g)] for g in L.GROUPS}))
            liberty[c.lower()] = f"lib/asap7sc7p5t_rvt_{c}.lib"
        views = {}
        for key, name in LEFS.items():
            (root / "lef" / pathlib.Path(name).name).write_bytes(others[name])
            views[key] = f"lef/{pathlib.Path(name).name}"
        views["tech_lef"] = {"nom": views["tech_lef"]}
        (root / "klt-pdk.json").write_text(json.dumps({
            "schema_version": 1, "variant": "asap7",
            "liberty": {"asap7sc7p5t_rvt": liberty},
            "views": {"asap7sc7p5t_rvt": views}}))
        cp = subprocess.run(
            shlex.split(os.environ.get("KLT", "klt")) + ["sta", str(REQUEST),
             "--pdk-root", str(root), "--format", "json"],
            capture_output=True, text=True, cwd=REPO)
        if not cp.stdout.strip():
            sys.exit(f"klt sta exited {cp.returncode} with no report:\n{cp.stderr}")
        report = json.loads(cp.stdout)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    OPCOND.write_text(json.dumps(operating_conditions(libs), indent=2) + "\n")
    print(f"klt sta exit {cp.returncode}; wrote {REPORT.name}, {OPCOND.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
