# Supply ERC (T1 item 11, ERC half)

`klt erc` supply-spec runs for the drawn TX/RX cells and the assembled lane column. Every figure is a
tool result against the predictive ASAP7 model: layout and ERC only, nothing fabricated or measured.

- Specs, append-only: [`supply.r1.json`](supply.r1.json) (original: one `ties[]` entry, the VDD well tie) and
  [`supply.r2.json`](supply.r2.json) (current). Both declare VDD and VSS `kind: "supply"`, stackup Gate (7/0), LISD,
  M1..M6 with their `*/251` label layers, V0..V5. `r2` declares both physical tap classes in `ties[]`:
  `nwell_tie` (Well 1/0; tap = Active 11/0 inside Nselect 12/0 and the source/drain trench contact SDT 88/0;
  connected through LISD to VDD) and `substrate_tie` (`well_layer: null`, `well_complement_of: ["1/0"]`, i.e. the
  die outside the well; tap = Active 11/0 inside Pselect 13/0 and SDT 88/0; connected through LISD to VSS).
- Pins: klt 0.9.2 (`.github/klt-version`) and KLayout 0.30.12 (`.github/klayout-version`), run from the repo root
  with repo-relative inputs. The `r1` reports were generated without pinning KLayout (they record 0.30.13 in
  `provenance.klayout_version`); the `r2` reports record 0.30.12.

```
K="uv run --no-project --with klayout-tools==$(cat .github/klt-version) --with klayout==$(cat .github/klayout-version) klt"
$K erc --validate-spec verification/erc/supply.r2.json
$K erc layout/lane_column.gds verification/erc/supply.r2.json --findings-only --omit-antenna-tables --format json > verification/erc/lane_column.r2.report.json
$K erc layout/cells/tx_cell.gds verification/erc/supply.r2.json --findings-only --omit-antenna-tables --format json > verification/erc/tx_cell.r2.report.json
# likewise rx_cell, tx_clk_cell, rx_clk_cell
$K erc --check verification/erc/<stream>.r2.report.json --rerun   # status: match for all five
```

The reports are committed as they came out, findings included; each replays `match` at both pins. The `r1`
spec and reports are kept unchanged as the original evidence (replay them with the same command, `r1` for `r2`;
their report hashes were recorded at KLayout 0.30.13, so the pinned KLayout shows a `provenance.klayout_version`
drift note beside `status: match`). The tables below are the `r2` runs.

## Results

| Stream | VDD islands | VSS islands | `missing_tie` (`nwell_tie` / `substrate_tie`) | `unconnected_net` | `floating_gate` |
| --- | --- | --- | --- | --- | --- |
| `layout/cells/tx_cell.gds` | 1 of 1 | 1 of 1 | 3 (1 / 2) | 0 | 44 |
| `layout/cells/rx_cell.gds` | 1 of 1 | 1 of 1 | 3 (1 / 2) | 0 | 104 |
| `layout/cells/tx_clk_cell.gds` | 1 of 1 | 1 of 1 | 3 (1 / 2) | 0 | 20 |
| `layout/cells/rx_clk_cell.gds` | 1 of 1 | 1 of 1 | 3 (1 / 2) | 0 | 16 |
| `layout/lane_column.gds` | 50 (expected 1) | 50 (expected 1) | 34 (34 / 0) | 2 (VDD, VSS) | 8836 |

(The `r1` spec declared only the VDD tie: 1 `missing_tie` per cell, 34 on the column; island, `unconnected_net`
and `floating_gate` counts are unchanged.)

`erc_status` is `violations` on every stream; both tie classes were evaluated (`missing_tie_checked` true) and
`erc_coverage.skipped` is empty. No `erc.supply_short` finding appears on any stream, but on every stream
`erc_coverage.inapplicable` carries `erc.supply_short` as `substrate_isolation_undecidable` (missing: a
`--deck` naming the PDK family, or asserted `ties[].isolation_boxes`) — the substrate-isolation half of the
short check was not evaluated, matching the two-tap fixture in 2AMLogic/klayout-tools#6948.

`erc_coverage.layers_in_stream_without_declaration` (the layers this stream draws that the spec declares
nowhere): `2/0` (Fin) and `16/0` (LIG) on each cell; the column adds `1/251`, `3/251`, `10/0`, `96/0`, `100/0`,
`235/5`. Per `layout/gen_cells_gds.py`, 16/0 is the gate contact (landing on the gate stripe, `LIG`) and 88/0 is the
source/drain trench contact (SDT), which `r2` now uses in the tap selectors; Fin 2/0 is not a conductor the supply
moves onto. The gate contact is the one undeclared level that can carry a net, and it is exactly what the
`erc.floating_gate` limitation below concerns. The column's extra levels (`1/251`, `3/251` labels, `10/0`, `100/0`,
`235/5` marker/text, `96/0` PAD) are not routing levels; `96/0` is the same uncovered layer the DRC record already
notes. `provenance.deck` is `null`: the run used no curated deck.

The inverse direction — stackup entries whose declared `label_layer` carries no text anywhere in the analysed
stream — cannot be read from the committed JSON (the report has no `warnings` field), so it is disclosed here from
the stderr of the replay command above (`$K erc --check verification/erc/<stream>.r2.report.json --rerun
2>stderr`, distinct warnings counted at klt 0.9.2 + KLayout 0.30.12, all five streams replaying `match`):
M2, M3, M4, M5 and M6 on every per-cell stream — `tx_cell`, `rx_cell`, `tx_clk_cell`, `rx_clk_cell` (5 warnings
each; only M1's `19/251` carries the rail text, `layout/gen_cells_gds.py`) — and M3 and M5 on
`layout/lane_column.gds` (2; the column's other declared label layers M1, M2, M4 and M6 do carry text there).
The warning is interpretation-relevant: a net matched *through* a textless layer would resolve zero islands
(`erc.unconnected_net`) and read `gates[].net: null`. No committed number is affected — VDD and VSS match through
the label layers that do carry text and resolve the island counts in the table above (1 of 1 per cell, 50 on the
column) — and the stderr capture is the evidence of record: the warnings are reproducible only by re-running the
command, not from the report JSON.

## Findings and owners

- **`erc.missing_tie`** (3 per cell: 1 `nwell_tie` on VDD, 2 `substrate_tie` on VSS; 34 `nwell_tie` and no
  `substrate_tie` on the column): the drawn cells have neither a well-to-VDD tap (`layout/README.md` documents the
  absent well-to-VDD contact and tap/bulk ties) nor the two substrate-to-VSS taps the spec's selectors look for.
  These are reported as failing records, not waived. Owner: #27 (item 11).
- **`erc.unconnected_net`, 50 islands each for VDD and VSS on the column**: the column assembler places the cells without
  routing them to the slice, so each placed instance's rail is its own island. This is a count of labelled islands, not
  a stream-side attribution within the routed slice; that attribution was #273 (closed) under #20 (open). Owner: #27, with #20 for the digital slice.
- **`erc.floating_gate`**: klt documents this rule as not meaningful on ASAP7 (`docs/cli/erc.md`, "ASAP7:
  `erc.floating_gate` and `erc.unconnected_net` are not meaningful yet"): the spec model cannot express LIG landing
  directly on the gate. Not a layout verdict; not declared away with `floating_gate_allowed`. Owner: #27.
- **Substrate tie**: `r2` declares `substrate_tie` (VSS), measured above; the substrate-isolation half of
  `erc.supply_short` is inapplicable-undecidable in these committed reports themselves (see above), not
  only in the minimal two-tap fixture: 2AMLogic/klayout-tools#6948 (closed on the tracker; at the 0.9.2 pin the cell runs, including TX with `--deck asap7`, still read
  undecidable). Owner: #27 (item 11) for the tap geometry.
- 2AMLogic/klayout-tools#5745 (`ties[]` fabricating `erc.supply_short`): no `supply_short` appeared at the 0.9.2 pin,
  so the fix being absent from the tag did not matter for these runs.

## Grading

These reports are not cited in `manifests/asap7-ucie-phy.json`. All five carry findings and the pinned
item-11 grader keeps one report per evidence kind, so it could not represent four per-cell records as a
partition-wide pass in any case. Item 11 stays `unmet` on both partitions; 11.digital also needs the item-4
digital LVS match (#20).
