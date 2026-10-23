# layout

Bump map and pad-centre check for the lane column (spec section 3, decision 0002).
**This is a layout check, not a DRC claim.** ASAP7 is predictive; nothing here is fabricated.

## Bump-map conventions

- `bump_map_target.csv` (34 bumps, 45 um pitch, 16 data lanes + clock) and
  `bump_map_fallback.csv` (18 bumps, 55 um pitch, 8 data lanes + clock) are the output of
  `gen_bump_map.py`; regenerate with `gen_bump_map.py [--slice fallback]`. Output is byte-identical across runs.
- Columns: `lane,signal,x_um,y_um`; the lane column is the lane-cell index.
- One column, x = 0. Bump k (k = 0 at the top) is at y = -pitch * k um, so y decreases downward.
- Two bumps per lane cell, TX then RX, top to bottom. Lane cells run top to bottom with the
  clock lane at the centre index (8 of 17 target, 4 of 9 fallback), so the clock bumps are symmetric
  about the column midpoint.
- Signals: `d<i>_tx`, `d<i>_rx`, `clk_tx`, `clk_rx`. Values are `%.3f` um; 1 dbu = 1 nm.
- Bumps are shapes on `Pad`, stream layer 96/0.

## Pad-centre check

```
python3 layout/check_pads.py --gds F.gds --top CELL --map layout/bump_map_target.csv --out record.json
```

Centres are bounding-box centres of every 96/0 shape in the flattened top cell. A pad within 1 dbu
(inclusive) of a map entry matches. The JSON record has `status`, `counts` (map, drawn, matched) and
`missing`, `extra`, `misplaced`. Exit 0 on pass only; an unreadable file, missing top cell or zero
96/0 shapes is `fail`.

## Self-test

```
python3 layout/selftest.py
```

Needs `klayout.db` (e.g. the klt tool interpreter or a venv). Builds pads-only GDS files from both
maps: the good layout and a pad moved 1 dbu must pass; a pad moved 2 dbu (`misplaced`), a deleted pad
(`missing`), an extra pad (`extra`) and an empty layout must fail; pads in a subcell are found.
Exits 0 only if every outcome occurs.
