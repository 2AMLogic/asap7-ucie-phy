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
   *Note, 2026-11-02 (#93): superseded. klayout-tools#4482 was closed by klt PR #4484, which adds the request field
   `output_dbu_um`; `layout/pnr/slice.pnr.json` now sets it to 0.00025 and `layout/slice_routed.gds` is written at dbu
   0.00025 (`klt cells`; `gds_dbu_um` in `slice.pnr.report.json`). The sentence above is the record as of that run.
   The figures in this file were not re-measured on the regenerated stream.*
3. **Left on the slice (22,711 at dbu 0.00025), not fixed.** Router metal against the deck's auxiliary rules:
   `M4.AUX.1` 9,640 and `M4.AUX.2` 9,800 (point markers), `V4.M5.AUX.2` 1,248, `M5.AUX.*` 1,256,
   `M4.W.3` 146, `M6.AUX.*` 112, `M1.S.*` 131, `M3.S.2` 14, plus `SDT.ACTIVE.AUX.2` 364 inside shipped
   cells. No generator setting that maps to these was identified; they need a follow-up.

**Column after this change, measured** (on the column as it stood before the TX/RX cells were redrawn in #55; after
merging that change `layout/lane_column.gds` is sha256 `b033d2b8...` and this DRC run was not repeated, so the
column figures below do not describe the committed stream): `layout/lane_column.gds` (sha256 `d72c19c0...`, after #56 and the layer
map) is `status: violations`, 367,926 violations across 30 rules, down from 8,126,659. 85% of it is
`M4.AUX.1`/`M4.AUX.2` (16 slices x the slice counts). The cell-side families (`FIN.*`, `NSELECT.*`,
`PSELECT.*`, `GATE.ACTIVE.EX.2`, and the cell share of `M1.*`) are the part #55 redraws; see `cells.drc.run-record.json`. This run finished and
its `coverage` block is quoted in `slice.drc.run-record.json`: `layers_in_stream_without_rules` and
`rules_skipped` are empty, `PAD` (96/0) is unchecked, and 74 rules are listed `unmodeled_rules`. The 156 MB
envelope is not committed. The 8 million-violation run needed 3.9 GB because klt 0.8.0 has no summary-only
mode (existing gap: 2AMLogic/klayout-tools#4464).

`klt signoff` item 3 stays unmet.

## Issue #64: baseline, router and cell fixes, re-run

Records: `lane_column.r2.drc.run-record.json` (baseline and re-run, same command), `components.r2.drc.run-record.json`
(regenerated slice and the four cells). klt 0.8.0, same packaged deck and 263-id expectation file, no filtering, no waivers;
the earlier records are unedited. Still **not clean**; layout results against a predictive PDK. The envelopes are not
committed (the baseline is 175 MB).

**Baseline** (committed column before this change, sha256 `b033d2b8...`, after #55/#56): 408,004 violations across 35
rules. It was not 367,926: #55's redrawn cells carry 44,628 cell-side violations (408,004 - 16 x 22,711) (`ACTIVE.AUX.1`, `FIN.*`, `LIG.*`,
`SDT.*`, `*SELECT.ACTIVE.EN.*` ...) on top of the slice's 16 x 22,711 (router metal and shipped-cell `SDT.ACTIVE.AUX.2`).

**Re-run** (sha256 `2a70c6922bf2...`): **8,208 violations across 7 rules**, exactly 16 x the slice's 513, all on slice instances:

| Rule(s) | Count | Cause |
|---|---|---|
| `SDT.ACTIVE.AUX.2` | 5,824 | inside shipped standard-cell instances (OAI22, BUFx4, fillers), none on router geometry; 2AMLogic/klayout-tools#4496 |
| `M1.S.2` / `.3` / `.4` / `.5` | 2,272 | router V1 landing pads (they vanish when the M1 inside the router `VIA_*` cells is cleared); 2AMLogic/klayout-tools#4495 |
| `M4.AUX.2` / `M4.W.3` | 64 / 48 | router M4 stubs whose line ends are off the deck grid (4 / 3 per slice, one cluster); no request field moves them; 2AMLogic/klayout-tools#4501 |

`coverage`: the expectation is satisfied, `layers_in_stream_without_rules` and `rules_skipped` are empty, `PAD` (96/0) is unchecked.

What cleared the other 399,796:

1. **Track grid** (`layout/pnr/slice.pnr.json`): M4/M5 track offset 0.012 um and M6/M7 0.016 um. Router M4 wires were centred on 48 nm
   multiples, but the deck wants a minimum-width wire's edge on a 48 nm multiple, i.e. centres 12 nm off; `M4.AUX.1/2` (9,640 + 9,800 per
   slice) went to 936 / 1,096. 2AMLogic/klayout-tools#4493.
2. **PDN straps dropped** (same file): the M5/M6 strap via stacks left `V4.M5.AUX.2` 1,248, `M4.AUX.*` and `M5.AUX.1` per slice and no request field moves
   them (2AMLogic/klayout-tools#4494). **Cost: power delivery in the P&R report is now `partial`** (followpin rails only, no stripes); #66 tracks a
   deck-clean grid. Slice 22,711 -> 513.
3. **Slice placement** (`layout/assemble_column.py`): the slice origin is on a 192 nm multiple (lcm of the 48 and 64 nm M4-M7 pitches) in every lane; at the
   old -22 um / -66 um spot the column showed 10,240 `M5.AUX.1` + 10,240 `M5.AUX.2` + `M6.AUX.*` that the standalone slice did not.
4. **Cells** (`layout/gen_cells_gds.py`): 7 nm fins, dummy gate at 54 nm pitch, select enclosures, SDT/LISD/LIG sized to the deck. 0 violations per cell
   (was 840 / 1,932 / 408 / 348).

The re-attested stream is `evidence/item2.r5.json`; `klt signoff` item 3 stays unmet and the manifest does not cite these records.

**Status after the #64 attribution pass** (slice re-run at dbu 0.00025 on `layout/slice_routed.gds`, klt 0.8.0, same deck and
263-id expectation file, no filtering, no waivers): 513 violations across the same 7 rules as above, so the committed column's
8,208 (16 x 513) stands. Every remaining family is now attributed to a filed tool gap (`#4495`, `#4496`, `#4501`); none is cleared
by a generator change available today. The column is **not** clean, `klt signoff` item 3 stays unmet, and no GDS or evidence
revision changed in this pass.

## Issue #148: first run on the committed streams, at the pinned klt (2026-11-14)

Record: `lane_column.r3.drc.run-record.json`, with the summary-only envelopes
`slice_routed.r3.envelope.json` and `lane_column.r3.envelope.json` committed beside it. klt **0.9.1**
(the pin in `.github/klt-version`, via `uvx --from "klayout-tools==0.9.1"`, because the host `klt` is an
unreleased 0.9.2.dev build), `--engine klayout` with the packaged ASAP7 deck, the full **267**-id
rule-category expectation set, no `--rules`, no `--waivers`, nothing filtered or relaxed. The five
earlier records are unedited. Still **not clean**; layout results against a predictive PDK, not
measurements.

**Why this run exists.** Every earlier record measured a stream that is no longer committed. The slice was
re-routed from the re-synthesized netlist (#115) and the column reassembled (#118), and no record carried
either committed hash: `layout/slice_routed.gds` is sha256 `eae888dc...` and `layout/lane_column.gds` is
`4937a7bd...`, while the records hold `826cd283...`, `b033d2b8...`, `2a70c692...`, `ec3a639b...` and
`1183fa3e...`. The 8,208 figure #64 and the roadmap reason from was measured on `2a70c692...`.

**Measured now**, both runs completed, expectation satisfied (`missing_names` and `unexpected_names`
empty, 267 of 267 categories checked):

| Stream | sha256 | Status | Violations | Rules |
|---|---|---|---|---|
| `layout/slice_routed.gds` | `eae888dc...` | `violations` | **906** | 5 |
| `layout/lane_column.gds` | `4937a7bd...` | `violations` | **14,496** | 5 |

The column is exactly **16 x** the slice in every single rule count, as it was in the r2 pass (16 x 513 =
8,208). So every violation sits on a slice instance and the column assembly still adds none.

### Family by family against the 8,208 baseline

| Rule | Baseline (8,208) | Now (14,496) | Change | Filed gap | Still applies? |
|---|---|---|---|---|---|
| `SDT.ACTIVE.AUX.2` | 5,824 | **9,504** | +3,680 | [#4496](https://github.com/2AMLogic/klayout-tools/issues/4496) (closed) | **Yes** |
| `M1.S.4` | 400 | **3,120** | +2,720 | [#4495](https://github.com/2AMLogic/klayout-tools/issues/4495) (open) | **Yes** |
| `M1.S.5` | 960 | 1,008 | +48 | #4495 (open) | **Yes** |
| `M1.S.3` | 64 | 576 | +512 | #4495 (open) | **Yes** |
| `M1.S.2` | 848 | 288 | -560 | #4495 (open) | **Yes** |
| `M4.AUX.2` | 64 | **0** | -64 | [#4501](https://github.com/2AMLogic/klayout-tools/issues/4501) (closed) | **No** |
| `M4.W.3` | 48 | **0** | -48 | #4501 (closed) | **No** |

The total went **up**, from 8,208 to 14,496. Two families cleared completely and the rest grew.

- **`SDT.ACTIVE.AUX.2` (9,504, 66% of the total) did not clear.** #4496 is a *deck*-side gap closed
  upstream on 2026-10-28, and the deck did change between 0.8.0 and the pin, so this run exercises that
  fix directly rather than carrying old geometry past it. The family is still here and is larger. Closed
  upstream, still present here.
- **The `M1.S.*` family (4,992, 34%) is unchanged in kind.** #4495 is still open, and it is a
  place-and-route fix, so nothing in this issue could have moved it.
- **Only the `M4` family cleared** (112 -> 0). #4501 is closed, but closed-upstream is not why it is
  gone here, and this run cannot say what is — see the confound.

### The confound: two inputs changed, not one

The comparison against 8,208 is **not** a controlled one, and no movement above is attributed to a cause:

- the **deck** changed, sha256 `48ac590a...` (klt 0.8.0) -> `14f146f0...` (0.9.1);
- the **stream** changed, `2a70c692...` -> `4937a7bd...`.

The baseline stream is not committed, so the two cannot be separated by re-running. In particular the
`M4` family going to zero is consistent with either the newer router or the new deck, and `#4501` being
closed upstream does not settle it: that fix lands in `place-and-route`, and this issue did not
regenerate the stream.

The **engine version is not** a third variable. Both the baseline and this run used standalone KLayout
**0.30.12**. The envelopes' own `provenance.klayout_version` says `0.30.13` and sets
`klayout_version_mismatch: true`, but that is the `klayout` Python wheel inside the pinned `uvx`
environment, not the engine: `--engine klayout` shells out to `/usr/bin/klayout`, which is 0.30.12, and
`--min-klayout-version 0.30.12` probed it and passed. Re-running the slice with
`--klayout-binary /usr/bin/klayout` named explicitly still reported `0.30.13` and gave byte-identical
counts, so the field does not track the engine at all. Filed as
[#5660](https://github.com/2AMLogic/klayout-tools/issues/5660); the record carries the measured 0.30.12.

### Expectation set: 267 at the pin, not 263

The earlier records' 263-id file cannot be reused — `--expect-rule-categories-file` fails the run on any
missing or unexpected name even when the counts agree, and the pin declares 267. The list was regenerated
from `klayout_tools.decks.asap7_rules.RULE_IDS` at 0.9.1 and cross-checked against the deck script
independently: all 123 non-interpolated `.output("NAME")` categories in `asap7.drc` are members of
`RULE_IDS`, and the only two literal categories absent from it (`FIN.GRID.1`, `GATE.GRID.1`) are gated
behind the opt-in `$fin_y_origin_nm` / `$gate_x_origin_nm` deck globals, which this run does not set. The
rest are the parameterized metal/via families the deck emits by string interpolation.

### Coverage, and what is still not checked

Identical for both streams except where noted: `layers_in_stream_without_rules` and `rules_skipped` are
empty, 67 rules are listed `unmodeled_rules`, and **`PAD` (96/0) remains unchecked on the column** (it
does not appear on the slice, which carries no PAD shapes). The deck still reads PAD only as the layer
enclosing V9, so shapes drawn on it are not checked — the bump interface is still outside the deck's
reach.

New at 0.9.1: the coverage block now lists five `isolation_only_rules` (`FIN.W.2`, `GATE.S.3`,
`NSELECT.W.1`, `PSELECT.W.1`, `WELL.W.1`) whose findings are only meaningful on a cell checked alone.
The 0.8.0 envelopes carried no such disclosure.

### First checkable DRC evidence in this directory

Because `--max-violations 0` is summary-only — true `violation_count`, `rule_counts` and `status`, with
only the marker list dropped and `violations_truncated` marking it — the envelopes are ~30 KB instead of
the 175 MB and 3.9 GB that kept every earlier envelope out of the repo. Both are committed and both
verify:

```
$ uvx --from "klayout-tools==0.9.1" klt drc --check verification/drc/<stream>.r3.envelope.json
status: match
  [OK] provenance.input.content_hash
  [OK] provenance.deck.content_hash
```

Caveat: each envelope's top-level `deck` field is the deck's absolute path inside this host's `uv` cache
(existing gap [#2723](https://github.com/2AMLogic/klayout-tools/issues/2723)). `--check` matches on the
deck's *content hash*, so it re-verifies wherever the pinned env resolves the same deck bytes, but the
recorded path is host-specific. The envelopes are committed exactly as the tool emitted them.

### What this run could not establish

Under `--engine klayout` every marker returns `source_cell: null` (906 of 906 on the slice), so a
native-deck run cannot say which cell contains a violation without deleting geometry and re-running the
whole deck. The streams are hierarchical (99 and 121 cells), so the hierarchy is there and unused. The
family identities above are therefore **inherited** from the r2/components attribution, not re-derived
here. Filed as [#5661](https://github.com/2AMLogic/klayout-tools/issues/5661).

`klt signoff` item 3 stays **unmet**, the manifest is unchanged and cites no record in this directory, and
no GDS or evidence revision changed in this pass.
