# 0006: no ratified spec row is statistical

Status: accepted. Date: 2026-10-27. Issue: #22.

## Decision

T1 item 6 of klayout-tools `docs/design-evidence-tiers.md` requires Monte Carlo evidence for any
accuracy, offset or matching spec row, and requires a block with no such row to say so. **No row of
the ratified `spec/ucie-phy.md` (sections 1-7) is statistical.** Every row is a layout dimension, a
DRC or LVS result, a static-timing slack at a named Liberty corner, an architectural choice, or a
cocotb handshake check. The spec preamble already limits rows to layout, DRC, LVS and timing targets.

The ratified spec is not edited. `manifests/spec-rows.json` lists the 26 row ids (spec commit
`2b9030f`) and `manifests/item6-na-statement.json` gives each its class and reason; the block manifest
cites both by content hash under item 6. A change to `spec/ucie-phy.md` must refresh both files, and
a new statistical row would withdraw this record.

## Rows

| Row id | Class | Why it is deterministic |
|---|---|---|
| `s1-data-lanes` | layout-geometry | Lane count is read from the drawn lane column; a count, not a distribution. |
| `s1-clock-lanes` | layout-geometry | Forwarded-clock lane count is read from the drawn lane column. |
| `s1-spare-lanes` | layout-geometry | Spare-lane count is read from the drawn column; LVS also compares the lane netlist. |
| `s2-rate-per-lane` | sta-timing | Rate row is met by post-route STA setup and hold slack at three named Liberty corners; each corner is one deterministic run. |
| `s2-parallel-clock` | sta-timing | Parallel clock is an STA constraint; slack is computed at each named corner. |
| `s2-serialization-ratio` | architectural-choice | 4:1 is fixed by decision 0004 and checked in STA and layout, not sampled. |
| `s3-bump-pitch` | layout-geometry | Pitch is read from drawn pad centres against the committed bump map. |
| `s3-bumps-per-lane` | layout-geometry | Bump count per lane cell is counted in the layout. |
| `s3-bump-assignment` | layout-geometry | Lane-to-bump order is compared against the committed bump map as data. |
| `s3-bump-representation` | layout-geometry | Pad shape and V9/M9 stack are checked by DRC (V9 rules) and by layout inspection. |
| `s4-cell-width` | layout-geometry | Cell width is a drawn dimension. |
| `s4-cell-height` | layout-geometry | Cell height is a drawn dimension. |
| `s4-area-budget` | layout-geometry | Area is width times height of the drawn cell, computed from the layout. |
| `s4-drawn-cells` | lvs-equivalence | Drawn TX and RX cells are checked by DRC and by LVS against reference netlists. |
| `s4-serializer-boundary` | lvs-equivalence | Boundary is a netlist partition checked by LVS and by STA through characterized timing models. |
| `s5-width` | architectural-choice | Interface width is a fixed port count in the RTL. |
| `s5-clock-domain` | sta-timing | Single parallel clock is an STA constraint; the domain crossing is timed, not sampled. |
| `s5-handshake` | handshake-simulation | valid/ready behaviour is a cocotb testbench with directed, deterministic checks. |
| `s5-clock-source-interface` | sta-timing | Clock uncertainty and input transition are fixed STA constraints, not a jitter claim. |
| `s6-corner-tt` | sta-timing | Named shipped Liberty file at one fixed voltage and temperature. |
| `s6-corner-ss` | sta-timing | Named shipped Liberty file at one fixed voltage and temperature. |
| `s6-corner-ff` | sta-timing | Named shipped Liberty file at one fixed voltage and temperature. |
| `s7-drc-clean` | drc-geometry | Zero violations from the pinned deck on the final GDS; a rule check, not a distribution. |
| `s7-lvs` | lvs-equivalence | Zero LVS errors against reference netlists. |
| `s7-sta` | sta-timing | Slack of at least 0 at each named corner; deterministic tool result. |
| `s7-bump-map` | layout-geometry | Drawn pad centres are compared to the committed bump map within one database unit. |

## Consequences

No Monte Carlo or `klt yield` run is claimed or needed for this spec. Statistical evidence for
the analog partition is not fabricated; see the PR for how the tool grades that partition.
