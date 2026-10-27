#!/usr/bin/env python3
"""Regenerate sta/slice.sta.report.json with `klt sta` (stdlib only; run as `python3 -I`).

Pre-route record: `klt sta` links design/netlist/slice_asap7.v with no placement or
routing (geometry_source "netlist_estimate"). Needs `openroad` on PATH and `klt` (override
with $KLT, e.g. 'uvx --from klayout-tools==0.8.0 klt'). The pinned lambdapdk archive
(spec/asap7-bringup.md) is passed with --pdk-archive or downloaded to a scratch directory;
nothing from it is written into the repo.

For each RVT corner (tt, ss, ff) the five Liberty cell groups are concatenated under the
first header, as design/synth/regen.py does for TT, because klt's list-merge refuses the
differing headers. The merged file therefore takes the AO group's operating condition;
the per-file nom_voltage/nom_temperature of every loaded group is read from the originals
and written to sta/operating-conditions.json, which is what the FF anomaly report cites.

    regen.py            overwrite the committed report and operating-conditions record
"""
import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
REQUEST = HERE / "slice.sta.json"
REPORT = HERE / "slice.sta.report.json"
OPCOND = HERE / "operating-conditions.json"

URL = "https://github.com/siliconcompiler/lambdapdk/archive/refs/tags/v0.2.17.tar.gz"
SHA256 = "ac7e950c4d0394a829658b6e219fea4a4b0c61a998183d5520f8b9e38c6efff2"
ROOT = "lambdapdk-0.2.17/lambdapdk/asap7/"
NLDM = ROOT + "libs/asap7sc7p5t_rvt/nldm/"
GROUPS = ["AO", "INVBUF", "OA", "SEQ", "SIMPLE"]
CORNERS = ["TT", "SS", "FF"]
LEFS = {"cell_lef": ROOT + "libs/asap7sc7p5t_rvt/lef/asap7sc7p5t_28_R.lef",
        "tech_lef": ROOT + "base/apr/asap7_tech.lef"}


def fetch(scratch, given):
    path = pathlib.Path(given) if given else scratch / "lambdapdk.tar.gz"
    if not path.is_file():
        urllib.request.urlretrieve(URL, path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != SHA256:
        sys.exit(f"{path}: sha256 {h.hexdigest()} != pinned {SHA256}")
    return path


def header_value(text, key):
    m = re.search(rf"^\s*{key}\s*:\s*([0-9.]+)\s*;", text, re.M)
    return float(m.group(1)) if m else None


def read_members(archive):
    want = {f"{NLDM}asap7sc7p5t_{g}_RVT_{c}_nldm.lib.gz": (c, g) for c in CORNERS for g in GROUPS}
    libs = {}
    others = {}
    with tarfile.open(archive) as tar:
        for m in tar:
            if m.name in want:
                c, g = want[m.name]
                libs[(c, g)] = gzip.decompress(tar.extractfile(m).read()).decode()
            elif m.name in LEFS.values():
                others[m.name] = tar.extractfile(m).read()
    if len(libs) != len(CORNERS) * len(GROUPS) or set(others) != set(LEFS.values()):
        sys.exit("pinned archive is missing RVT Liberty groups or LEF")
    return libs, others


def template_blocks(header):
    """(name, text) of every top-level table template group in a Liberty header."""
    out = []
    for m in re.finditer(r"^[ \t]*(\w*template\w*)\s*\(\s*(\w+)\s*\)\s*\{", header, re.M):
        depth, i = 1, m.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(header[i], 0)
            i += 1
        out.append((m.group(1) + "(" + m.group(2) + ")", header[m.start():i]))
    return out


def merged(libs, corner):
    """Cell groups concatenated under the first header, plus any table template that
    another group's header defines and the first does not. The shipped groups do not
    share template names (SEQ uses delay_template_7x7, the others delay_template_7x7_x1);
    without them every SEQ timing table is dropped and nothing is constrained."""
    out = None
    have = set()
    for g in GROUPS:
        t = libs[(corner, g)]
        end = t.rstrip().rfind("}")
        first_cell = re.search(r"^\s*cell\s*\(", t, re.M).start()
        if out is None:
            out = t[:end]
            have = {k for k, _ in template_blocks(t[:first_cell])}
            at = re.search(r"^[ \t]*cell\s*\(", out, re.M).start()
            out_head, out_cells = out[:at], out[at:]
            continue
        for key, block in template_blocks(t[:first_cell]):
            if key not in have:
                have.add(key)
                out_head += block + "\n"
        out_cells += t[first_cell:end]
    return out_head + out_cells + "}\n"


def operating_conditions(libs):
    rec = {}
    for c in CORNERS:
        files = {}
        for g in GROUPS:
            t = libs[(c, g)]
            files[f"asap7sc7p5t_{g}_RVT_{c}_nldm.lib.gz"] = {
                "nom_voltage": header_value(t, "nom_voltage"),
                "nom_temperature": header_value(t, "nom_temperature")}
        points = {(v["nom_voltage"], v["nom_temperature"]) for v in files.values()}
        rec[c] = {"files": files, "uniform": len(points) == 1}
    return {"schema": "asap7-ucie-phy.sta.operating-conditions/1",
            "source": f"lambdapdk v0.2.17 sha256:{SHA256}",
            "note": "read from each original Liberty header; the merged Liberty handed to "
                    "klt sta carries the AO group's header only",
            "corners": rec}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdk-archive")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="slice-sta-") as tmp:
        scratch = pathlib.Path(tmp)
        libs, others = read_members(fetch(scratch, args.pdk_archive))
        root = scratch / "pdk"
        (root / "lib").mkdir(parents=True)
        (root / "lef").mkdir()
        liberty = {}
        for c in CORNERS:
            (root / "lib" / f"asap7sc7p5t_rvt_{c}.lib").write_text(merged(libs, c))
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
