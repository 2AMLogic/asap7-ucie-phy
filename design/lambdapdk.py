"""Pinned lambdapdk archive and Liberty cell-group merge, shared by design/synth/regen.py
and sta/regen.py (stdlib only).

Both scripts run as `python3 -I`, which drops the script directory from sys.path, so they
load this file by explicit path (importlib.util.spec_from_file_location), not `import`.
A pin bump is an edit to URL/SHA256 here and nowhere else (spec/asap7-bringup.md).
"""
import hashlib
import pathlib
import re
import sys
import urllib.request

URL = "https://github.com/siliconcompiler/lambdapdk/archive/refs/tags/v0.2.17.tar.gz"
SHA256 = "ac7e950c4d0394a829658b6e219fea4a4b0c61a998183d5520f8b9e38c6efff2"
ROOT = "lambdapdk-0.2.17/lambdapdk/asap7/"
NLDM = ROOT + "libs/asap7sc7p5t_rvt/nldm/"
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


def merged(texts):
    """Cell groups (`texts`: group name -> Liberty text) concatenated under the first
    header, plus any table template that another group's header defines and the first
    does not. The shipped groups do not share template names (SEQ uses
    delay_template_7x7, the others delay_template_7x7_x1); without them every SEQ timing
    table is dropped and nothing is constrained."""
    out = None
    have = set()
    for g in GROUPS:
        t = texts[g]
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
