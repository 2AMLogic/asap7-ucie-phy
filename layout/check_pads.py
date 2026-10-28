#!/usr/bin/env python3
"""Compare drawn pad centres (Pad, stream layer 96/0) with the committed bump map.

A layout check, never a DRC claim (spec section 3, decision 0002).

Centre = bounding-box centre of each 96/0 shape in the flattened top cell.
Matching is nearest-neighbour: a drawn pad within TOL_NM nm (inclusive) of a map
entry is matched; a leftover drawn pad within NEAR_PITCHES bump pitches of an
unmatched entry is `misplaced`; the rest are `missing` / `extra`.
An unreadable file, missing top cell or zero 96/0 shapes is `fail`.
"""
import argparse
import csv
import json
import sys

import klayout.db as db

LAYER, DATATYPE = 96, 0
TOL_NM = 1
NEAR_PITCHES = 3


def tol_dbu(dbu):
    """The tolerance in dbu for a layout at `dbu` um."""
    return max(0, round(TOL_NM / (dbu * 1000)))


def read_map(path, dbu):
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out.append({"lane": int(r["lane"]), "signal": r["signal"],
                        "x": round(float(r["x_um"]) / dbu),
                        "y": round(float(r["y_um"]) / dbu)})
    return out


def drawn_centres(gds, top):
    ly = db.Layout()
    ly.read(gds)
    cell = ly.cell(top) if ly.has_cell(top) else None
    if cell is None:
        raise ValueError("top cell %r not found" % top)
    li = ly.find_layer(LAYER, DATATYPE)
    pts = []
    if li is not None:
        it = cell.begin_shapes_rec(li)
        while not it.at_end():
            b = it.shape().bbox().transformed(it.trans())
            c = b.center()
            pts.append((c.x, c.y))
            it.next()
    return ly.dbu, pts


def compare(entries, pts, dbu):
    unmatched = list(range(len(pts)))
    matched = 0
    tol = tol_dbu(dbu)
    left = []
    for e in entries:
        best = None
        for i in unmatched:
            d = max(abs(pts[i][0] - e["x"]), abs(pts[i][1] - e["y"]))
            if d <= tol and (best is None or d < best[0]):
                best = (d, i)
        if best:
            unmatched.remove(best[1])
            matched += 1
        else:
            left.append(e)
    pitch = min([abs(entries[i]["y"] - entries[i + 1]["y"]) for i in range(len(entries) - 1)] or [0])
    near = NEAR_PITCHES * pitch
    um = lambda v: round(v * dbu, 6)
    misplaced, missing = [], []
    for e in left:
        cand = [i for i in unmatched
                if max(abs(pts[i][0] - e["x"]), abs(pts[i][1] - e["y"])) <= near]
        if cand:
            i = min(cand, key=lambda i: max(abs(pts[i][0] - e["x"]), abs(pts[i][1] - e["y"])))
            unmatched.remove(i)
            misplaced.append({"lane": e["lane"], "signal": e["signal"],
                              "expected_um": [um(e["x"]), um(e["y"])],
                              "drawn_um": [um(pts[i][0]), um(pts[i][1])]})
        else:
            missing.append({"lane": e["lane"], "signal": e["signal"],
                            "expected_um": [um(e["x"]), um(e["y"])]})
    extra = [{"drawn_um": [um(pts[i][0]), um(pts[i][1])]} for i in unmatched]
    return matched, missing, extra, misplaced


def check(gds, top, map_path):
    rec = {"gds": gds, "top": top, "map": map_path, "layer": "%d/%d" % (LAYER, DATATYPE),
           "tolerance_nm": TOL_NM}
    try:
        dbu, pts = drawn_centres(gds, top)
        rec["tolerance_dbu"] = tol_dbu(dbu)
        entries = read_map(map_path, dbu)
    except Exception as e:  # unreadable file, missing cell, bad map
        rec.update(status="fail", error=str(e))
        return rec
    if not pts:
        rec.update(status="fail", error="no shapes on %d/%d in %r" % (LAYER, DATATYPE, top),
                   counts={"map": len(entries), "drawn": 0, "matched": 0})
        return rec
    matched, missing, extra, misplaced = compare(entries, pts, dbu)
    ok = not (missing or extra or misplaced)
    rec.update(status="pass" if ok else "fail",
               counts={"map": len(entries), "drawn": len(pts), "matched": matched},
               missing=missing, extra=extra, misplaced=misplaced)
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gds", required=True)
    ap.add_argument("--top", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rec = check(a.gds, a.top, a.map)
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    print("%s: status=%s" % (a.gds, rec["status"]))
    return 0 if rec["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
