# verification/drc

T1 item 3 (DRC clean) on `layout/lane_column.gds`. **Not met.**

`lane_column.drc.run-record.json` records the one run made (2026-10-28, released klt 0.8.0,
`--engine klayout` with the packaged ASAP7 deck, deck hash `sha256:48ac590a...e7f`, the 263-id
rule-category expectation file): status `violations`, 8,126,659 violations across 65 rules,
dominated by `GATE.S.1`, `GATE.S.3`, `GATE.S.2`, `GATE.W.2`, `GCUT.AUX.2` and `GCUT.GATE.EX.1`.
The cells are unrouted placements (`layout/README.md`), so this is the expected kind of result;
it is a layout result against a predictive PDK, not a measurement.

The full envelope (~3.9 GB, every polygon inline) was not committed and its trailing `coverage`
block was not obtained, so no `coverage` fields are quoted here. Nothing was waived or filtered.
The manifest does not cite this record, and `klt signoff` item 3 stays unmet.

## Attribution of the 8,126,659 (issue #57)

Records: `slice.drc.run-record.json`, `cells.drc.run-record.json` (klt 0.8.0, same packaged deck and
263-id expectation file, no filtering, no waivers; `lane_column.drc.run-record.json` is unedited).
Still **not clean**; layout results against a predictive PDK.

| Component | Violations | Instances in the baseline column | Share of 8,126,659 |
|---|---|---|---|
| `slice_routed.gds` (as on main before this change) | 507,461 | 16 | 8,119,376 (99.9%) |
| `tx_cell` / `rx_cell` (dbu 0.001, pre-#56) | 148 / 294 | 16 each | 2,368 / 4,704 |
| `tx_clk_cell` + `rx_clk_cell` (pre-#56) | 116 + 110 | 1 | 226 |

The components sum to 8,126,674, 15 above the recorded total; all 65 rules match exactly except
`V2.AUX.1` (16 predicted, 1 recorded), which is unexplained. The drawn cells were a rounding error in
the total; the hypothesis that placement-only cells dominate is refuted. The slice did.

Causes on the slice, in order of effect:

1. **Layer map (fixed here).** `slice.pnr.report.json` recorded `layer_map: {path: null, resolution: none}`,
   so klt's DEF->GDS merge numbered routing layers and vias sequentially (6/0, 8/0, 10/0 ...), on top of the
   deck's Gate (7), Gcut (10), Active (11) and select layers. `layout/pnr/regen.py` now stages the pinned
   lambdapdk `asap7.layermap` for klt (`resolution: exact`; M1 on 19/0 ... M7 on 70/0). Slice:
   507,461 -> 125,470. Filed as 2AMLogic/klayout-tools#4481 (the silent fallback).
2. **dbu (fixed at the assembly by #56).** The P&R stream is at dbu 0.001, the deck is written for 0.00025.
   Shipped `INVx1` / `DFFHQNx1` are clean at 0.00025 and show 7 / 45 `GATE.S.1` / `GATE.S.3` violations
   after a coordinate/4 rescale to 0.001. The regenerated slice drops from 125,470 to 22,711 under a lossless
   x4 upscale (all of `GATE.S.3`, 102,517, and `GATE.S.1`). `klt place-and-route` has no output-dbu
   option (2AMLogic/klayout-tools#4482), so `layout/slice_routed.gds` run directly still shows them.
3. **Left on the slice (22,711 at dbu 0.00025), not fixed.** Router metal against the deck's auxiliary rules:
   `M4.AUX.1` 9,640 and `M4.AUX.2` 9,800 (point markers), `V4.M5.AUX.2` 1,248, `M5.AUX.*` 1,256,
   `M4.W.3` 146, `M6.AUX.*` 112, `M1.S.*` 131, `M3.S.2` 14, plus `SDT.ACTIVE.AUX.2` 364 inside shipped
   cells. No generator setting that maps to these was identified; they need a follow-up.

**Column after this change, measured:** `layout/lane_column.gds` (sha256 `d72c19c0...`, after #56 and the layer
map) is `status: violations`, 367,926 violations across 30 rules, down from 8,126,659. 85% of it is
`M4.AUX.1`/`M4.AUX.2` (16 slices x the slice counts). The cell-side families (`FIN.*`, `NSELECT.*`,
`PSELECT.*`, `GATE.ACTIVE.EX.2`, and the cell share of `M1.*`) are the part #55 redraws; see `cells.drc.run-record.json`. This run finished and
its `coverage` block is quoted in `slice.drc.run-record.json`: `layers_in_stream_without_rules` and
`rules_skipped` are empty, `PAD` (96/0) is unchecked, and 74 rules are listed `unmodeled_rules`. The 156 MB
envelope is not committed. The 8 million-violation run needed 3.9 GB because klt 0.8.0 has no summary-only
mode (existing gap: 2AMLogic/klayout-tools#4464).

`klt signoff` item 3 stays unmet.
