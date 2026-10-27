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
import importlib.util
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
REQUEST = HERE / "slice.synth.json"
NETLIST = REPO / "design" / "netlist" / "slice_asap7.v"

def _load_lambdapdk():
    path = REPO / "design" / "lambdapdk.py"
    spec = importlib.util.spec_from_file_location("lambdapdk", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _load_lambdapdk()


def merged_liberty(archive):
    want = {f"{L.NLDM}asap7sc7p5t_{g}_RVT_TT_nldm.lib.gz": g for g in L.GROUPS}
    texts = {}
    with tarfile.open(archive) as tar:
        for m in tar:
            if m.name in want:
                texts[want[m.name]] = gzip.decompress(tar.extractfile(m).read()).decode()
    if set(texts) != set(L.GROUPS):
        sys.exit("pinned archive is missing RVT TT liberty groups")
    return L.merged(texts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdk-archive")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="slice-synth-") as tmp:
        scratch = pathlib.Path(tmp)
        archive = L.fetch(scratch, args.pdk_archive)
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
