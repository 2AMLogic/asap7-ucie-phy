# Supply ERC (T1 item 11, ERC half)

`klt erc` supply-spec runs for the drawn TX/RX cells and the assembled lane column. Every figure is a
tool result against the predictive ASAP7 model: layout and ERC only, nothing fabricated or measured.

- Spec: [`supply.r1.json`](supply.r1.json): VDD and VSS declared `kind: "supply"`, stackup Gate (7/0), LISD,
  M1..M6 with their `*/251` label layers, V0..V5, and one `ties[]` entry (`nwell_tie`: Well 1/0, tap =
  Active 11/0 inside Nselect 12/0, connected through LISD to VDD).
- Pins: klt 0.9.2 (`.github/klt-version`), KLayout 0.30.12, run from the repo root with repo-relative inputs.

```
K="uvx --from klayout-tools==$(cat .github/klt-version) klt"
$K erc --validate-spec verification/erc/supply.r1.json
$K erc layout/lane_column.gds verification/erc/supply.r1.json --findings-only --omit-antenna-tables --format json > verification/erc/lane_column.r1.report.json
$K erc layout/cells/tx_cell.gds verification/erc/supply.r1.json --findings-only --omit-antenna-tables --format json > verification/erc/tx_cell.r1.report.json
# likewise rx_cell, tx_clk_cell, rx_clk_cell
$K erc --check verification/erc/<stream>.r1.report.json --rerun   # status: match for all five
```

The reports are committed as they came out, findings included; each replays `match`.

## Results

| Stream | VDD islands | VSS islands | `missing_tie` | `unconnected_net` | `floating_gate` |
| --- | --- | --- | --- | --- | --- |
| `layout/cells/tx_cell.gds` | 1 of 1 | 1 of 1 | 1 | 0 | 44 |
| `layout/cells/rx_cell.gds` | 1 of 1 | 1 of 1 | 1 | 0 | 104 |
| `layout/cells/tx_clk_cell.gds` | 1 of 1 | 1 of 1 | 1 | 0 | 20 |
| `layout/cells/rx_clk_cell.gds` | 1 of 1 | 1 of 1 | 1 | 0 | 16 |
| `layout/lane_column.gds` | 50 (expected 1) | 50 (expected 1) | 34 | 2 (VDD, VSS) | 8836 |

`erc_status` is `violations` on every stream; the tie check was evaluated (`missing_tie_checked` true) and
`erc_coverage.skipped` is empty. No `erc.supply_short` finding appears on any stream, but on every stream
`erc_coverage.inapplicable` carries `erc.supply_short` as `substrate_isolation_undecidable` (missing: a
`--deck` naming the PDK family, or asserted `ties[].isolation_boxes`) — the substrate-isolation half of the
short check was not evaluated, matching the two-tap fixture in 2AMLogic/klayout-tools#6948.

`erc_coverage.layers_in_stream_without_declaration` (the layers this stream draws that the spec declares
nowhere): `2/0`, `13/0`, `16/0`, `88/0` on each cell; the column adds `1/251`, `3/251`, `10/0`, `96/0`,
`100/0`, `235/5`. All are implant/marker/label/pad/text levels — none is a routing level the supply could
move onto — and `96/0` (PAD) is the same uncovered layer the DRC record already notes. `provenance.deck` is
`null`: the run used no curated deck.

## Findings and owners

- **`erc.missing_tie`** (1 per cell, 34 on the column): the drawn cells have no well-to-VDD tap
  (documented in `layout/README.md`). Owner: #27 (item 11).
- **`erc.unconnected_net`, 50 islands each for VDD and VSS on the column**: the column assembler places the cells without
  routing them to the slice, so each placed instance's rail is its own island. This is a count of labelled islands, not
  a stream-side attribution within the routed slice; that attribution belongs to #273 under #20. Owner: #27, with #273/#20 for the digital slice.
- **`erc.floating_gate`**: klt documents this rule as not meaningful on ASAP7 (`docs/cli/erc.md`, "ASAP7:
  `erc.floating_gate` and `erc.unconnected_net` are not meaningful yet"): the spec model cannot express LIG landing
  directly on the gate. Not a layout verdict; not declared away with `floating_gate_allowed`. Owner: #27.
- **Substrate tie**: no substrate tie class is declared here, and the substrate-isolation half of
  `erc.supply_short` is inapplicable-undecidable in these committed reports themselves (see above), not
  only in the minimal two-tap fixture: 2AMLogic/klayout-tools#6948. Owner: #27 (item 11) for the tap
  geometry, klayout-tools#6948 for the undecidable isolation measurement.
- 2AMLogic/klayout-tools#5745 (`ties[]` fabricating `erc.supply_short`): no `supply_short` appeared at the 0.9.2 pin,
  so the fix being absent from the tag did not matter for these runs.

## Grading

These reports are not cited in `manifests/asap7-ucie-phy.json`. All five carry findings and the pinned
item-11 grader keeps one report per evidence kind, so it could not represent four per-cell records as a
partition-wide pass in any case. Item 11 stays `unmet` on both partitions; 11.digital also needs the item-4
digital LVS match (#20).
