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
- Signals: `d<i>_tx`, `d<i>_rx`, `clk_tx`, `clk_rx`. Values are `%.3f` um, i.e. whole nm; the layouts are written at dbu 0.00025 um (4 dbu = 1 nm), the
  dbu klt's asap7 deck requires.
- Bumps are shapes on `Pad`, stream layer 96/0.

## Pad-centre check

```
python3 layout/check_pads.py --gds F.gds --top CELL --map layout/bump_map_target.csv --out record.json
```

Centres are bounding-box centres of every 96/0 shape in the flattened top cell. A pad within 1 nm
(inclusive; 4 dbu at the 0.00025 um layout dbu, derived from the layout) of a map entry matches. The JSON record has `status`, `counts` (map, drawn, matched) and
`missing`, `extra`, `misplaced`. Exit 0 on pass only; an unreadable file, missing top cell or zero
96/0 shapes is `fail`.

## Self-test

```
python3 layout/selftest.py
```

Needs `klayout.db` (e.g. the klt tool interpreter or a venv). Builds pads-only GDS files from both
maps: the good layout and a pad moved 1 nm must pass; a pad moved 2 nm (`misplaced`), a deleted pad
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
the worker. `selftest_cells.py` also imports `klayout_tools` (it runs klt's asap7 extraction, with the well
or a route layer deleted as negative controls), so run it in the klt tool interpreter. Output is byte-identical across runs (no GDS timestamps).

- **What is drawn**: per device a footprint (Fin 2/0, Active 11/0, N/P select 12/0 and 13/0, Gate 7/0) with
  its own active island (islands never abut, so no diffusion is shared), a dummy gate one 54 nm pitch to the
  left of the gate (the deck wants every gate to have a neighbour), 7 nm fins on a 27 nm pitch, one N or P
  select per row, S/D trench contact SDT 88/0 inside LISD 17/0, and a LIG 16/0 gate contact in the gate
  stripe's extension, offset right so the three M1 verticals keep a 36 nm pitch. NMOS and PMOS rows sit between VSS
  and VDD M1 rails, one Well 1/0 rectangle covers the PMOS row. Every net is routed: V0 18/0 and an M1
  vertical per terminal, V1 21/0 to one M2 20/0 track per multi-terminal net in the channel between the rows;
  VSS/VDD terminals go straight to their rail on M1. Each boundary port and rail is named by a text label on
  M1 text 19/251, the layer klt's deck reads net names from (19/0 text is not read).
- **What is not**: no tap or bulk tie (NMOS body is klt's synthesized `vsubs`, PMOS body the well net; the
  LVS requests use klt's `finfet_bulk` comparison-side policy, which klt reports as a warning), no
  well-to-VDD contact, no sizing. Cell dimensions are a placement choice, not tuned. The drawn cells are not connected to the slice in the column.
- **DRC (#64)**: the four cells run clean (0 violations) against the packaged ASAP7 deck, klt 0.8.0, 263-id
  expectation file, nothing waived (`verification/drc/components.r2.drc.run-record.json`). That is a rule check on
  these cells standing alone, not a column-level or LVS claim; the deck does not check `Pad`, and 67 rules are
  listed `unmodeled_rules` in the run's `coverage` block.
- **Budget**: `--report` prints each cell's bounding box against the spec section 4 lane-cell rows
  (45 x 90 um target, 55 x 110 um fallback). Those are geometric bounding-box areas only; the
  routed-slice share from the sibling P&R issue (#33) is not included. No sizing, rate or
  performance figure is implied (decision 0003).

All drawn streams (`cells/*.gds`, `lane_column.gds`) are at dbu 0.00025 um, which `klt lvs --deck asap7`
requires. The routed slice below is klt output at 0.001 um; `assemble_column.py` converts it on import
(physical geometry preserved) and `slice_routed.gds` itself is not edited.

## LVS of the drawn cells (issue #55)

`klt lvs --deck asap7` of each cell GDS against its committed `design/netlist/*.sp`, one local run per cell
(klt 0.8.1.dev511, KLayout 0.30.12). Requests and reports are in `evidence/item4-lvs/`; each request carries
`options.finfet_bulk {nmos: VSS, pmos: VDD}`.

| cell | status | devices (layout/reference/matched) | nets (layout/reference/matched) |
|---|---|---|---|
| `rx_clk_cell` | match | 8/8/8 | 7/7/7 |
| `tx_clk_cell` | match | 10/10/10 | 9/9/9 |
| `tx_cell` | match | 22/22/22 | 16/16/16 |
| `rx_cell` | match | 52/52/52 | 29/29/29 |

The only mismatch entries are two `device.finfet_bulk_tied` warnings per report: the bulk connectivity is a
caller assertion, not drawn geometry. `power_connectivity` is `unchecked`. No netlist or deck was edited to get
here. This is a tool result for the four cells alone: no DRC claim (#19), no LVS of the routed datapath
(2AMLogic/klayout-tools#4462), and nothing fabricated or measured.

Area (`gen_cells_gds.py --report`, geometric bounding boxes): `tx_cell` 3.98 um^2, `rx_cell` 9.80 um^2,
`tx_clk_cell` 1.66 um^2, `rx_clk_cell` 1.31 um^2, about 0.1 + 0.24 + 0.04 + 0.03 percent of the 4050 um^2
target lane cell; the 3035 um^2 left after the routed slice is not overrun.

## Routed `slice` (place and route)

`klt place-and-route` of the synthesized `design/netlist/slice_asap7.v` against ASAP7 RVT TT, through
OpenROAD (`openroad` here is the klt Docker wrapper, pinned by image digest). **Layout geometry only:
ASAP7 is predictive and nothing here is fabricated.**

- `pnr/slice.pnr.json` is the request: floorplan, tapcell/endcap, PDN (`M1`/`M2` followpins only), CTS, route
  `M2`-`M7`, seed 1. The `library` block carries what klt has no built-in ASAP7 table for. The M4-M7 track
  offsets (12 nm for M4/M5, 16 nm for M6/M7) put the routed wires on the grid the deck checks
  (2AMLogic/klayout-tools#4493); with offset 0 they sit 12/16 nm off it.
- `pnr/regen.py` rebuilds `slice_routed.gds` and `pnr/slice.pnr.report.json` from the committed netlist and the
  pinned lambdapdk archive (`spec/asap7-bringup.md`); `regen.py --check` exits 0 if the stream reproduces
  byte-for-byte, 3 if it drifted. Run it as `python3 -I layout/pnr/regen.py`; it takes about 10 minutes, nearly
  all in the route stage. It stages the pinned `asap7.layermap` so klt's DEF->GDS merge puts routing on the ASAP7
  stream numbers (without it: sequential numbers on top of Gate/Gcut/Active; `verification/drc/README.md`). Run from the repo root with `$TMPDIR` under a path the `openroad` wrapper mounts.
- Result (report `slice.pnr.report.json`, OpenROAD 26Q3-1510): stage reached `route`, `route_drc_violation_count` 0,
  `antenna_violation_count` 0, 310 tap/endcap cells, power delivery **`partial`**: the `M5`/`M6` straps were
  dropped (#64) because their via stacks fail the deck and no request field moves them
  (2AMLogic/klayout-tools#4494), so only the `M1`/`M2` followpin rails remain; restoring a grid is #66.
  Footprint 23.033 um x 44.066 um (`klt stats`), 1015 um^2, against the 45 um x 90 um / 4050 um^2 lane-cell budget (spec section 4): about
  3035 um^2 is left for the drawn TX/RX cells.

Assumptions and workarounds, all inputs to the flow and none a PDK-supplied value or a sign-off claim:

- **Wire RC** is ORFS's published ASAP7 signal-layer figure (`flow/platforms/asap7/setRC.tcl`, master as of
  2026-10-27: 2.65684e-2 kohm/um, 1.6579e-1 fF/um, entered as pF), because the pinned tech LEF has no `RESISTANCE`.
  It steers placement-time repair only; timing numbers come from post-route STA (#21), not from this report.
- **Antenna diode**: the ASAP7 LEF has no antenna data and no `ANTENNACELL`, but klt requires one and OpenROAD
  rejects a zero-area diode. `regen.py` names `TIEHIx1` and gives it a placeholder `ANTENNADIFFAREA` in a scratch
  copy of the LEF. With no antenna rules no net can violate, so no diode is inserted; the committed stream
  contains no PDK change.
- **Tie cells**: klt synthesize has no ASAP7 tie-cell entry, so the committed netlist ties 102 async-set pins to
  `1'h1`, which TritonRoute will not route. `regen.py` rewrites them to `TIEHIx1`/`TIELOx1` in a scratch copy;
  the committed netlist is unchanged, so the routed stream's netlist differs from it by those tie cells.
- **Liberty**: the merge in `design/synth/regen.py` drops the SEQ group's `delay_template_7x7` and
  `power_template_7x7`, so OpenSTA discards every flop timing arc. `pnr/regen.py` adds the missing templates.
  The synthesis merge is left as is (it does not read those tables).
- Tapcell distance 25 um, filler `FILLER`/`FILLERxp5` and CTS buffer `BUFx4` are ORFS's ASAP7 choices; none is tuned.

Tool gaps filed at `2AMLogic/klayout-tools`: no ASAP7 tie-cell entry (#4273), no way to route a library with no
antenna cell (#4274), `wire_rc` capacitance unit documented wrongly (#4275), Liberty template loss on a hand merge
(comment on #4242), no ASAP7 track offsets matching the deck grid (#4493), PDN straps that fail the deck (#4494),
router V1 pads that fail the M1 tip rules (#4495), `SDT.ACTIVE.AUX.2` inside shipped cells (#4496).

## Lane column (assembly and item-2 attestation)

`assemble_column.py` writes `lane_column.gds` (top `lane_column`): 17 lane cells at 90 um pitch
(16 data lanes plus the clock lane at index 8), 34 pads of 25 um on `Pad` 96/0 at the
`bump_map_target.csv` centres (45 um bump pitch). A data lane cell holds the routed `slice` and the
`tx_cell`/`rx_cell`; the clock lane cell holds `tx_clk_cell`/`rx_clk_cell`. Pads live inside the lane
cells, so `check_pads.py` finds them only by flattening. Each data lane cell (`lane_cell_<i>`) places the slice
on a multiple of 192 nm (lcm of the 48 nm and 64 nm M4-M7 pitches) in x and y, so the router metal keeps the
deck's grid origin: the 90 um lane pitch is not a multiple of 192 nm, so the slice sits up to 96 nm from its
nominal spot in some lanes. `--check` exits 0 / 3 on drift; run it with
`python3` (needs `klayout.db`), output is byte-identical across runs.

**Layout geometry only.** The slice and the drawn cells are placed, not connected to each other, and no DRC-clean
or column-level LVS result is claimed (the cell-level LVS is above; the DRC record is
`verification/drc/lane_column.r2.drc.run-record.json`: 8,208 violations remain). The 34-pad `pad_check_record.json`
(`status: pass`) is a pad-centre comparison against the bump map, not a rule check: klt's ASAP7 deck
does not check `Pad` (2AMLogic/klayout-tools#3807), and abutment of the lane-cell seam is not DRC-checked
(2AMLogic/klayout-tools#4226 covers a single tileable cell, not this column). Nothing is fabricated.

```
python3 layout/check_pads.py --gds layout/lane_column.gds --top lane_column \
  --map layout/bump_map_target.csv --out layout/pad_check_record.json
klt signoff --attest 2 --input layout/lane_column.gds --generator "python3 layout/assemble_column.py" \
  --regenerated-hash sha256:<hash of a fresh assemble> -o evidence/item2.json
```

`attest/item2.json` pins the column and its input streams by sha256. `evidence/item2.json` was produced
with klt `0.8.1.dev497+g74e41260c360`: the pinned `0.8.0` has no `--attest 2` producer, but it grades the
envelope (`klt signoff --manifest`) the same way, and the committed verdict was rendered with `0.8.0`.
