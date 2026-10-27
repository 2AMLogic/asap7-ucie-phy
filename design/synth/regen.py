#!/usr/bin/env python3
"""Regenerate design/netlist/slice_asap7.v with `klt synthesize` (stdlib only; run as `python3 -I`).

Needs `yosys` and `klt` on PATH (override with $KLT) and the pinned lambdapdk
archive (spec/asap7-bringup.md): pass --pdk-archive, or it is downloaded to a
scratch directory. Nothing from the archive is written into the repo.

klt's PDK resolver cannot read lambdapdk's ASAP7 Liberty directly: it ships
gzipped and split into five cell-group files whose headers differ (library
name, date), which klt's own list-merge refuses. This script unpacks the RVT
TT files, concatenates the cell groups under the first header, and points a
klt-pdk.json descriptor at the result, in a scratch directory.

    regen.py            overwrite the committed netlist
    regen.py --check    exit 0 if it reproduces byte-for-byte, 3 if it drifted
"""
import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
REQUEST = HERE / "slice.synth.json"
NETLIST = REPO / "design" / "netlist" / "slice_asap7.v"

URL = "https://github.com/siliconcompiler/lambdapdk/archive/refs/tags/v0.2.17.tar.gz"
SHA256 = "ac7e950c4d0394a829658b6e219fea4a4b0c61a998183d5520f8b9e38c6efff2"
NLDM = "lambdapdk-0.2.17/lambdapdk/asap7/libs/asap7sc7p5t_rvt/nldm/"
GROUPS = ["AO", "INVBUF", "OA", "SEQ", "SIMPLE"]


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


def merged_liberty(archive):
    want = {f"{NLDM}asap7sc7p5t_{g}_RVT_TT_nldm.lib.gz": g for g in GROUPS}
    texts = {}
    with tarfile.open(archive) as tar:
        for m in tar:
            if m.name in want:
                texts[want[m.name]] = gzip.decompress(tar.extractfile(m).read()).decode()
    if set(texts) != set(GROUPS):
        sys.exit("pinned archive is missing RVT TT liberty groups")
    out = None
    for g in GROUPS:
        t = texts[g]
        end = t.rstrip().rfind("}")
        if out is None:
            out = t[:end]
        else:
            out += t[re.search(r"^\s*cell\s*\(", t, re.M).start():end]
    return out + "}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdk-archive")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="slice-synth-") as tmp:
        scratch = pathlib.Path(tmp)
        archive = fetch(scratch, args.pdk_archive)
        root = scratch / "pdk"
        (root / "lib").mkdir(parents=True)
        (root / "lib" / "asap7sc7p5t_rvt_TT.lib").write_text(merged_liberty(archive))
        (root / "klt-pdk.json").write_text(json.dumps({
            "schema_version": 1, "variant": "asap7",
            "liberty": {"asap7sc7p5t_rvt": {"tt": "lib/asap7sc7p5t_rvt_TT.lib"}}}))
        req = json.loads(REQUEST.read_text())
        req["sources"] = [str((HERE / s).resolve()) for s in req["sources"]]
        req["outputs"] = {"dir": str(scratch / "run")}
        (scratch / "request.json").write_text(json.dumps(req))
        cp = subprocess.run(
            shlex.split(os.environ.get("KLT", "klt")) + ["synthesize", str(scratch / "request.json"),
             "--pdk-root", str(root), "--format", "json"],
            capture_output=True, text=True, cwd=REPO)
        if cp.returncode != 0:
            sys.exit(f"klt synthesize exited {cp.returncode}:\n{cp.stdout}{cp.stderr}")
        fresh = (scratch / "run" / "slice_synth.v").read_bytes()
    if args.check:
        if not NETLIST.is_file() or NETLIST.read_bytes() != fresh:
            print(f"drifted: {NETLIST}", file=sys.stderr)
            return 3
        return 0
    NETLIST.parent.mkdir(exist_ok=True)
    NETLIST.write_bytes(fresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
