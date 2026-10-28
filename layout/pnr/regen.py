#!/usr/bin/env python3
"""Regenerate layout/slice_routed.gds with `klt place-and-route` (stdlib only; run as `python3 -I`).

Needs `openroad` and `klt` on PATH (override with $KLT) and the pinned lambdapdk
archive (spec/asap7-bringup.md): pass --pdk-archive, or it is downloaded to a
scratch directory. Nothing from the archive is written into the repo.

klt's PDK resolver cannot read lambdapdk's ASAP7 collateral directly: the
Liberty ships gzipped and split into five cell-group files whose headers differ
(see design/lambdapdk.py), and the LEF and GDS use lambdapdk's own naming.
This script unpacks the RVT TT collateral into a scratch directory and points a
klt-pdk.json descriptor (liberty, views) at it. The per-library CTS, routing,
tapcell, filler and power-pin inputs klt has no built-in ASAP7 table for come
from the `library` block of slice.pnr.json.

    regen.py            overwrite the committed routed GDS and report
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
import importlib.util

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent

def _load_lambdapdk():
    path = REPO / "design" / "lambdapdk.py"
    spec = importlib.util.spec_from_file_location("lambdapdk", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _load_lambdapdk()

REQUEST = HERE / "slice.pnr.json"
GDS = REPO / "layout" / "slice_routed.gds"
REPORT = HERE / "slice.pnr.report.json"

ASAP7 = L.ROOT
RVT = ASAP7 + "libs/asap7sc7p5t_rvt/"
FILES = {  # archive member -> scratch path under the PDK root
    ASAP7 + "base/apr/asap7_tech.lef": "lef/asap7_tech.lef",
    RVT + "lef/asap7sc7p5t_28_R.lef": "lef/asap7sc7p5t_28_R.lef",
    RVT + "gds/asap7sc7p5t_28_R.gds.gz": "gds/asap7sc7p5t_28_R.gds",
    # LEF layer -> stream layer/datatype. Without it klt's DEF->GDS merge numbers the
    # routing layers sequentially (Via1 on 8/0, Via2 on 10/0, ...), which are the ASAP7
    # Gate, Gcut and Active-adjacent stream layers (verification/drc/README.md).
    ASAP7 + "base/apr/asap7.layermap": "klayout/tech/asap7.map",
}


def tie_constants(text):
    """Drive every bare 1'h1 / 1'h0 connection from a tie cell (scratch copy only).

    klt synthesize has no ASAP7 tie-cell entry, so the committed netlist ties
    async-set pins to literals; OpenROAD types such a net POWER and TritonRoute
    refuses to route it (DRT-0305). One TIEHI/TIELO per module that uses them."""
    out = []
    for mod in re.split(r"(?<=endmodule\n)", text):
        hi, lo = "1'h1" in mod, "1'h0" in mod
        if hi or lo:
            head = re.search(r"\);\n", mod).end()
            add = ""
            if hi:
                add += "  wire tie_hi_n;\n  TIEHIx1_ASAP7_75t_R tie_hi (.H(tie_hi_n));\n"
            if lo:
                add += "  wire tie_lo_n;\n  TIELOx1_ASAP7_75t_R tie_lo (.L(tie_lo_n));\n"
            mod = mod[:head] + add + mod[head:]
            mod = mod.replace("1'h1", "tie_hi_n").replace("1'h0", "tie_lo_n")
        out.append(mod)
    return "".join(out)


def patch_diode(lef):
    """Give the stand-in antenna-diode cell a nonzero ANTENNADIFFAREA (scratch copy only).

    The ASAP7 LEF carries no antenna data and no ANTENNACELL, yet klt requires
    library.antenna_diode and OpenROAD refuses a zero-area diode (GRT-0244).
    TIEHIx1 stands in; the area is a placeholder, not a PDK value. With no
    antenna rules in the LEF no net can violate, so no diode is ever inserted
    (the placed-cell counts in the report confirm it)."""
    old = "  PIN H\n    DIRECTION OUTPUT ;\n    USE SIGNAL ;\n"
    i = lef.index("MACRO TIEHIx1_ASAP7_75t_R")
    j = lef.index(old, i)
    return lef[:j] + old + "    ANTENNADIFFAREA 0.1 LAYER M1 ;\n" + lef[j + len(old):]


def unpack(archive, root):
    with tarfile.open(archive) as tar:
        for m in tar:
            if m.name in FILES:
                data = tar.extractfile(m).read()
                if m.name.endswith(".gz"):
                    data = gzip.decompress(data)
                dest = root / FILES[m.name]
                if m.name.endswith("_R.lef"):
                    data = patch_diode(data.decode()).encode()
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    missing = [p for p in FILES.values() if not (root / p).is_file()]
    if missing:
        sys.exit(f"pinned archive is missing {missing}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdk-archive")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="slice-pnr-") as tmp:
        scratch = pathlib.Path(tmp)
        archive = L.fetch(scratch, args.pdk_archive)
        root = scratch / "pdk"
        (root / "lib").mkdir(parents=True)
        (root / "lib" / "asap7sc7p5t_rvt_TT.lib").write_text(L.merged_liberty(archive))
        unpack(archive, root)
        (root / "klt-pdk.json").write_text(json.dumps({
            "schema_version": 1, "variant": "asap7",
            "assets": {"klayout": "klayout"},
            "liberty": {"asap7sc7p5t_rvt": {"tt": "lib/asap7sc7p5t_rvt_TT.lib"}},
            "views": {"asap7sc7p5t_rvt": {
                "cell_lef": "lef/asap7sc7p5t_28_R.lef",
                "tech_lef": {"nom": "lef/asap7_tech.lef"},
                "gds": "gds/asap7sc7p5t_28_R.gds"}}}))
        # klt writes .klt/place-and-route/ next to the request: run from a copy.
        run = scratch / "run"
        run.mkdir()
        req = json.loads(REQUEST.read_text())
        netlist = run / "slice_tied.v"
        netlist.write_text(tie_constants((HERE / req["netlist"]).read_text()))
        req["netlist"] = str(netlist)
        (run / "request.json").write_text(json.dumps(req))
        cp = subprocess.run(
            shlex.split(os.environ.get("KLT", "klt")) + ["place-and-route", str(run / "request.json"),
             "--pdk-root", str(root), "--format", "json"],
            capture_output=True, text=True, cwd=REPO)
        if cp.returncode != 0:
            sys.exit(f"klt place-and-route exited {cp.returncode}:\n{cp.stdout}{cp.stderr}")
        report = json.loads(cp.stdout)
        fresh = pathlib.Path(report["gds_path"]).read_bytes()
        # Scratch paths are not evidence: keep the verdict fields, redact the rest.
        text = json.dumps(report, indent=2, sort_keys=True).replace(str(scratch), "<scratch>")
        text = text.replace(str(REPO), "<repo>") + "\n"
    if args.check:
        if not GDS.is_file() or GDS.read_bytes() != fresh:
            print(f"drifted: {GDS}", file=sys.stderr)
            return 3
        return 0
    GDS.write_bytes(fresh)
    REPORT.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
