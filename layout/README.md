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

## Drawn TX/RX cells

`gen_cells_gds.py` writes `cells/{tx,rx,tx_clk,rx_clk}_cell.gds` from the device lists in
`design/netlist/*.sp` (which `design/gen_cells.py` renders), so port names and widths follow
`rtl/README.md`. Serializer boundary (spec section 4): `tx_cell` holds the last 2:1 stages and the
output driver, `rx_cell` the input stage and sampler.

```
python3 layout/gen_cells_gds.py [--check | --report]   # needs klayout.db; --check exits 0 / 3 on drift
python3 layout/selftest_cells.py                       # run from layout/ or with it on the path
```

It is run with plain `python3`, not `-I`, because `-I` hides the user-site `klayout` package on
the worker. Output is byte-identical across runs (no GDS timestamps).

- **What is drawn**: per device a footprint (Fin 2/0, Active 11/0, N/P select 12/0 and 13/0, Gate 7/0,
  M1 19/0 source/drain strips) in an NMOS row and a PMOS row between VSS and VDD M1 rails. Each
  boundary port is an M1 pin square with a text label of the port name, for LVS (#20).
- **What is not**: no routing between devices, no contacts or vias, no wells. The drawing is a
  placement of the committed topology, not a finished cell. LVS will not compare clean until routing exists.
- **ASAP7 grid, fin and design rules are not checked until DRC (#19).** Fin pitch 27 nm and gate
  pitch 54 nm are used for spacing only; nothing here claims DRC cleanliness.
- **Budget**: `--report` prints each cell's bounding box against the spec section 4 lane-cell rows
  (45 x 90 um target, 55 x 110 um fallback). Those are geometric bounding-box areas only; the
  routed-slice share from the sibling P&R issue (#33) is not included. No sizing, rate or
  performance figure is implied (decision 0003).
