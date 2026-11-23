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
`1183fa3e...`. The 8,208 figure that #64 and the roadmap reason from was measured on `2a70c692...`.

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

### First checkable DRC evidence in this directory — the input assertion

Because `--max-violations 0` is summary-only — true `violation_count`, `rule_counts` and `status`, with
only the marker list dropped and `violations_truncated` marking it — the envelopes are ~30 KB instead of
the 175 MB and 3.9 GB that kept every earlier envelope out of the repo. Both are committed, so for the
first time in this directory a tool can re-verify the evidence rather than only read it.

**What re-verifies anywhere is the input assertion**, `provenance.input.content_hash`: the stream it names
is committed in-repo and the envelope records it as a portable `{"path": ..., "scope": "repo"}` locator, so
`--check` re-hashes it from any checkout. **The deck assertion does not** — see the caveat below. So what
this directory now has is a checkable *input* assertion, not a checkable whole envelope.

On the **authoring host**, where the deck is still present at the absolute path the envelope recorded, both
envelopes report a full match:

```
$ uvx --from "klayout-tools==0.9.1" klt drc --check verification/drc/<stream>.r3.envelope.json
status: match
  [OK] provenance.input.content_hash
  [OK] provenance.deck.content_hash
exit 0
```

That transcript is the authoring host's result only. On **a second host** of the same fleet at the same
pin, both envelopes give (2026-11-14):

```
$ uvx --from "klayout-tools==0.9.1" klt drc --check verification/drc/<stream>.r3.envelope.json
status: drifted
  [OK] provenance.input.content_hash
  [DRIFTED] provenance.deck.content_hash
      expected: sha256:14f146f02cd731de3e0b59452eadfdab9c2c947724a219a1002a31b5e0f12d13
      actual:   None
exit 3
```

The second result is the portable truth, and it is itself useful evidence: the input half holds off the
authoring host, the deck half does not.

**Caveat — the mechanism.** Each envelope's top-level `deck` field is the deck's absolute path inside the
authoring host's `uv` cache. `--check` resolves the deck by **dereferencing that recorded absolute path**,
so the deck assertion re-verifies **only where that exact path exists** — not merely wherever the pinned
env resolves the same deck bytes. Where the path is absent the deck cannot be hashed at all and the field
reports `actual: None`, a non-resolving locator rather than a content mismatch, which still reads as
`drifted` and exits 3. Same pinned env plus byte-identical deck is **not** sufficient: on the second host
the pin resolves `asap7.drc` to a different cache path whose sha256 is exactly the recorded `14f146f0...`
and `--check` still reports `None`, and passing that deck explicitly with `--deck-file` alongside `--check`
is accepted without error and changes nothing. The recorded path also embeds the env's Python minor version
(`python3.13`, where the same pin now resolves `python3.14`), so it is unlikely to survive a cache rebuild
even on the authoring host. Filed generically as
[#5709](https://github.com/2AMLogic/klayout-tools/issues/5709);
[#2723](https://github.com/2AMLogic/klayout-tools/issues/2723) is the closed background gap on absolute
paths in reports. The envelopes are committed exactly as the tool emitted them.

### What this run could not establish

Under `--engine klayout` every marker returns `source_cell: null` (906 of 906 on the slice), so a
native-deck run cannot say which cell contains a violation without deleting geometry and re-running the
whole deck. The streams are hierarchical (99 and 121 cells), so the hierarchy is there and unused. The
family identities above are therefore **inherited** from the r2/components attribution, not re-derived
here. Filed as [#5661](https://github.com/2AMLogic/klayout-tools/issues/5661).

`klt signoff` item 3 stays **unmet**, the manifest is unchanged and cites no record in this directory, and
no GDS or evidence revision changed in this pass.

## Issue #64: re-run at the current pin, on the currently committed streams (r4, 2026-11-16)

Record: `lane_column.r4.drc.run-record.json`, with the summary-only envelopes
`slice_routed.r4.envelope.json` and `lane_column.r4.envelope.json` committed beside it. klt **0.9.2**
(the pin in `.github/klt-version`, via `uvx --from "klayout-tools==0.9.2"`), `--engine klayout` with the
packaged ASAP7 deck, the same **267**-id expectation file as r3 (byte-identical: 0.9.2 declares the same
`RULE_IDS`), no `--rules`, no `--waivers`, nothing filtered or relaxed. The six earlier records are
unedited. Still **not clean**; layout results against a predictive PDK, not measurements.

**Why this run exists.** Two things changed after the r3 record, and no DRC record carried either
current input:

1. **The streams changed.** The DEF-PINS fix (commit `9494c37`, 2026-11-14) re-staged top-level pin
   geometry on the metal drawing layer: `layout/slice_routed.gds` is now sha256 `27dbfd1d...` (r3
   measured `eae888dc...`) and `layout/lane_column.gds` is `6e1df816...` (r3 measured `4937a7bd...`;
   the new column hash is attested as `evidence/item2.r8.json`).
2. **The pin moved.** `.github/klt-version` is now 0.9.2 (r3 ran 0.9.1, and #64's Revision 2 ordered one
   measurement at the pin on the committed column). The packaged deck changed with the release:
   sha256 `14f146f0...` -> `fa303c03...`.

Issue #64's earlier framing ("wait for klayout-tools#4495/#4501, then expect improvement") is
overtaken by events: #4501 closed docs-only, #4495 closed 2026-11-16 as a **no-op** (the closing note
says `via_pad_trim` already existed on `origin/main` and the live before/after DRC was not performed),
and #4496 was already docs-only. None of the three families had a pending tool fix, so the open
question was purely what the current pin measures on the current streams. Measured now.

**Measured now**, both runs completed, expectation satisfied (`missing_names` and `unexpected_names`
empty, 267 of 267 categories checked, `PAD` 96/0 unchecked on the column):

| Stream | sha256 | Status | Violations | Rules |
|---|---|---|---|---|
| `layout/slice_routed.gds` | `27dbfd1d...` | `violations` | **906** | 5 |
| `layout/lane_column.gds` | `6e1df816...` | `violations` | **14,496** | 5 |

The column is again exactly **16 x** the slice in every rule count.

### Nothing moved

Every per-rule count is **byte-identical to r3**, despite both the stream and the deck changing between
the two runs:

| Rule | r3 (0.9.1) | r4 (0.9.2) | Change |
|---|---|---|---|
| `SDT.ACTIVE.AUX.2` | 9,504 | 9,504 | 0 |
| `M1.S.4` | 3,120 | 3,120 | 0 |
| `M1.S.3` | 576 | 576 | 0 |
| `M1.S.5` | 1,008 | 1,008 | 0 |
| `M1.S.2` | 288 | 288 | 0 |
| `M4.AUX.2` / `M4.W.3` | 0 / 0 | 0 / 0 | 0 |

Read together with the r3 table against the 8,208 baseline, the deltas stand as recorded there; this
run adds no movement and no attribution. Two honest statements about what this identity does and does
not establish:

- The DEF-PINS regeneration did not change this layout's DRC outcome: the staged pin geometry trips no
  deck rule on either stream. The slice's own hash changed and its counts did not.
- The 0.9.1 -> 0.9.2 deck change produced no rule-outcome difference on this layout. This is one layout
  at one pin pair, not a statement about the deck generally; the deck hash changed and what else it
  affects is not probed here.

### What remains, per rule (unchanged, now measured at the pin)

- **`SDT.ACTIVE.AUX.2` — 9,504 (66%).** Shipped standard-cell retained deviations (OAI22, BUFx4,
  fillers); [#4496](https://github.com/2AMLogic/klayout-tools/issues/4496) closed docs-only. Stays in a
  deck-unwaived run unless the layout stops using those cells — a design decision, out of scope here.
- **`M1.S.2/.3/.4/.5` — 4,992 (34%).** Router V1 landing pads;
  [#4495](https://github.com/2AMLogic/klayout-tools/issues/4495) closed as a no-op. Measured for the
  first time since that closure: the family is unchanged, and the committed stream was produced with
  the trim active (`layout/pnr/slice.pnr.report.json` carries `via_pad_trim` `status: trimmed`), so the
  closure moved nothing here — now measured, not inferred.
- **`M4.AUX.2` / `M4.W.3` — 0.** Cleared since r2; [#4501](https://github.com/2AMLogic/klayout-tools/issues/4501)
  closed docs-only.

No new tool gap surfaced in this pass. The two known envelope quirks stand unchanged at 0.9.2 and are
recorded in the r4 record: `provenance.klayout_version` still reports the uvx wheel instead of the
engine binary ([#5660](https://github.com/2AMLogic/klayout-tools/issues/5660)), and `klt drc --check`
still resolves the deck by the envelope's absolute uv-cache path, so the deck assertion does not
re-verify off the authoring host ([#5709](https://github.com/2AMLogic/klayout-tools/issues/5709);
authoring-host `--check` on the r4 envelope: `match`, exit 0).

`klt signoff` item 3 stays **unmet** — the run is `violations`, not `clean` — and the manifest cites no
record in this directory. No GDS was regenerated and no evidence revision was created in this pass; the
committed column hash remains attested as `evidence/item2.r8.json`. Whether this issue closes as
completed-with-limitations, and whether the shipped cells that trip `SDT.ACTIVE.AUX.2` should be
replaced, are Champion/human calls and are not made here.

## Issue #66: the M5/M6 power grid restored with the shipped ASAP7 recipe (r5, 2026-11-17)

Record: `lane_column.r5.drc.run-record.json`, with the summary-only envelopes
`slice_routed.r5.envelope.json` and `lane_column.r5.envelope.json` committed beside it. klt **0.9.2**
(the pin, via `uvx --from "klayout-tools==0.9.2"`), `--engine klayout` with the packaged ASAP7 deck,
the same **267**-id expectation file as r3/r4 (byte-identical, re-hashed), no `--rules`, no `--waivers`,
nothing filtered or relaxed. The seven earlier records are unedited. Still **not clean**; layout results
against a predictive PDK, not measurements.

**Why this run exists.** #64 cleared the router-metal families by dropping the M5/M6 PDN straps, which
left power delivery `partial` (followpin rails only, 0 stripe segments). This issue restores the grid
with klt's own `asap7sc7p5t` recipe (M5 w 0.216 / M6 w 0.288, `M2<->M5` `max_columns 1 ongrid {M3 M4}`,
`M5<->M6` `max_columns 1`) transcribed **explicitly** into `slice.pnr.json`, because the shipped
`power.preset` form is unreachable in this request: the preset validates `pdk.cell_library` as
`asap7sc7p5t_28` while `post_route_spef`/`post_route_sdf` validate it as `asap7sc7p5t_rvt`, and this
request needs the post-route SDF. Both exact errors are quoted in the record; filed generically as
[#6029](https://github.com/2AMLogic/klayout-tools/issues/6029). One number deviates from the recipe on
purpose, measured: the **M5 strap offset is 0.306 µm, not the recipe's 0.312**, because the deck's
`Mx.AUX.1` grids are absolute (offset 0) while pdngen offsets are core-origin relative, and this
floorplan's core origin x (1.026 µm ≡ 18 mod 24) put every M5 strap edge 6 nm off the 24 nm grid at the
recipe value. The M6 offset already lands on the 32 nm grid here and is kept. The P&R report now grades
**power delivery `complete`** (1,016 VDD / 1,021 VSS `STRIPE` segments), and the routed netlist and
placement are unchanged (byte-identical `slice_routed.v`; only the routed metal moved).

**Measured now**, both runs completed, expectation satisfied (267 of 267 categories checked; `PAD`
96/0 unchecked on the column). This comparison **is** deck-controlled against r4 — same pin, same deck
bytes, same expectation file; the one changed input is the stream:

| Stream | sha256 | Status | Violations | Rules |
|---|---|---|---|---|
| `layout/slice_routed.gds` | `cc4a7c72...` | `violations` | **1,620** | 9 |
| `layout/lane_column.gds` | `66179d88...` | `violations` | **25,920** | 9 |

Again exactly **16 x** the slice in every rule count: the assembly adds nothing.

### The prohibited families are zero; four new families are not

The families that made #64 drop the straps — `V4.M5.AUX.2`, `M4.AUX.*`, `M5.AUX.*` — are **all zero**
with the grid restored. The acceptance criteria's prohibited set is clean, and power is `complete`.
What the grid does add, reported by name and count (the grid is therefore **not** deck-clean, and no
claim here says otherwise):

| Rule | Slice | Column | Cause | Filed |
|---|---|---|---|---|
| `V4.M4.EN.1` | 648 | 10,368 | the recipe's wide-V4 bar has zero M4 enclosure by design; count = stack crossings exactly | documented in [#4499](https://github.com/2AMLogic/klayout-tools/issues/4499) ("no existing request field changes that") |
| `V4.M5.EN.2` | 12 | 192 | same recipe family (M5 enclosure of the wide bar) | documented in #4499 (tool PR measured ~13 on its tiny block) |
| `M3.S.2` | 15 | 240 | pdngen's M2<->M5 stack M3 stubs closer than 40 nm along-track at some rail pitches; markers all sit inside strap columns at rail crossings | new: [#6030](https://github.com/2AMLogic/klayout-tools/issues/6030) |
| `M5.W.3` | 46 | 736 | router, not pdngen: across-track extents 336/384/432 nm (even × 24 nm), none at a strap edge — TritonRoute landing patches under the strap-congested route | recipe residual family, already noted in the tool docs |

Per-rule against r4 (slice counts; the column is 16× in every row): `M1.S.2` 18→16, `M1.S.3` 36→32,
`M1.S.4` 195→193, `M1.S.5` 63→64 (single-digit router pin-access movement around the new blockages),
`SDT.ACTIVE.AUX.2` 594→594 (byte-identical), plus the four new families above.

**Signoff consequence.** Unlike r3/r4, both committed streams changed, so the item 2 attestation moved:
`evidence/item2.r9.json` + `attest/item2.r9.json` (34/34 pad centres re-checked, record byte-identical),
manifest re-pinned, verdict regenerated (`--check`: match, exit 0, `t1_met_count` 11 unchanged, no
`stale_evidence` rows). Item 3 stays **unmet**. The manifest still cites no record in this directory.

## Issue #66, addendum: the routed-slice LVS re-take (r15) and its PDK provenance (2026-11-17)

The grid restoration regenerated the routed stream (`cc4a7c72...`), so the routed-slice LVS had to be
re-taken. This is the recorded decision for that re-take; the committed pair is
`evidence/item4-lvs/slice_routed.r15.{request,report}.json` (the prior routed-slice record r13 stays in
the tree as history, not citable as current evidence).

**Why r15 exists (request forms tried).** The first re-take on the regenerated stream named the reference
pin-order CDL by absolute, machine-local paths (`/tmp/lambdapdk-r14/...`), exactly as r13 had before it
(`/tmp/lambdapdk-r13/...`), both resolves of the pinned `siliconcompiler/lambdapdk v0.2.17`. The record
gate refuses absolute paths (decision 0012 §1), so that form was re-taken as r15: `portable_paths: true`,
`reference.pdk: asap7`, and the request naming the CDL by the `$PDK_ROOT` token
(`$PDK_ROOT/asap7/libs/asap7sc7p5t_rvt/netlist/asap7sc7p5t_28_R.cdl`). Only the two committed forms
existed: absolute (gate-refused) and portable (committed).

**What the r15 report records.** Under portable paths the tool deliberately records no host location:
`provenance.pdk` and `reference_conversion.pdk_root` are `null`, and the pin-order source is
`{"path": null, "scope": "external"}` with `cells: 209` consumed. That the token resolved at run time is
measured by the recorded cell count; the host tree it resolved against is the extracted release below
(the tree the gate-refused takes had named by absolute path).

**The provenance is recoverable, recorded here (decision 0012 §3's remedy: repo-relative references or a
content hash).** Three repo-side facts reconstruct the reference side of `s7-lvs`:

1. The PDK release is pinned in [`evidence/item4-attempts.json`](../../evidence/item4-attempts.json):
   `siliconcompiler/lambdapdk v0.2.17, archive sha256 ac7e950c...` — re-measured 2026-11-17 on the
   extracted tree's archive copy:
   `ac7e950c4d0394a829658b6e219fea4a4b0c61a998183d5520f8b9e38c6efff2` (228,891,082 bytes).
2. Inside that release, the file at the request token's relative path
   (`asap7/libs/asap7sc7p5t_rvt/netlist/asap7sc7p5t_28_R.cdl`) is 146,201 bytes,
   `sha256 3e3e2548fb8f571c2e373dcbf565ecb0288e6433e803fbf06561cb16b70caf53` (re-measured 2026-11-17).
3. The committed r15 report consumed 209 pin-order cells from that file and records the compare outcome
   (8,333 mismatches / 8,043 errors — materially better than r13's 86,629 / 86,371 on the pre-grid
   stream, which the restored supply grid plausibly explains; no claim beyond the recorded counts).

So a reader of `s7-lvs` can reconstruct: lambdapdk v0.2.17 (archive `ac7e950c...`) →
`asap7/libs/asap7sc7p5t_rvt/netlist/asap7sc7p5t_28_R.cdl` (sha256 `3e3e2548...`, 209 cells). If a future
take should have the tool itself record the reference hash, that is a tool request, not a gate edit; the
compare was not re-run to test alternative request shapes (decision 0012 §2 — re-runs belong to #20).

## Issue #228: the grid families are recipe-inherent, not a stale preset (r6, 2026-11-17)

Record: `lane_column.r6.drc.run-record.json`. klt **0.9.2** (the pin), `--engine klayout` with the
packaged ASAP7 deck (bytes identical to r5's, deck-controlled), the same **267**-id expectation file as
r3/r4/r5 (byte-identical, re-hashed), no `--rules`, no `--waivers`, nothing filtered or relaxed. The
eight earlier records are unedited. **No committed file changed in this pass**: both committed streams
still hash to r5's inputs (`cc4a7c72...` slice, `66179d88...` column) and r5 remains their measurement
of record; this pass measured a **scratch** routed slice and records only its hashes and counts. Still
**not clean**; layout results against a predictive PDK, not measurements.

**Why this run exists.** Issue #228 (step 3 of the Curator's order, measurement first) asks one question
about the four grid families r5 reported — `V4.M4.EN.1` 648, `V4.M5.EN.2` 12, `M3.S.2` 15, `M5.W.3` 46
on the slice: are they inherent to the shipped `asap7sc7p5t` PDN recipe, or the stale transcription of
an older one? klayout-tools#4499 merged that preset on 2026-10-28, five days before r5 transcribed it;
whether the committed grid matches what actually shipped had not been traced.

**Static answer: the committed grid is the shipped recipe.** The committed `power.straps`/`connects`
equal the 0.9.2 preset table value for value, except the one deviation r5 records on purpose: the M5
strap offset **0.306, not the preset's 0.312**. That deviation is the tool's own documented adjustment —
the pin's preset docs state pdngen offsets are core-origin relative, the edge-grid result was measured
at core origin 0.96 µm, and *other origins can leave `M5.AUX.1`/`M6.AUX.1` hits (adjust
`power.straps` explicitly in that case)*. This floorplan's core origin x is 1.026 µm; r5 measured the
strap edges off-grid at 0.312 and on-grid at 0.306. (The preset form itself remains unreachable with
`post_route_sdf` at this pin: klayout-tools#6029 is open.)

**Measured answer: the recipe-inherent families do not move, and the recipe-exact offset is worse.** A
full place-and-route re-run of the same netlist with the same seed, changing only the M5 offset to the
preset's 0.312, routed to a scratch stream (`5548c041...`) and measured at the pin. The routed netlist
is byte-identical to the committed one; power delivery is segment-for-segment and via-for-via identical
(VDD 1,016 / VSS 1,021 stripe segments, 1,085 / 1,089 vias, `complete`); report fmax (3,731.41 MHz) and
hold/setup violation counts (0 / 0) are identical. DRC, 267 of 267 categories checked:

| Rule (slice) | r5 committed (off 0.306) | preset-exact (off 0.312) | |
|---|---|---|---|
| `V4.M4.EN.1` | 648 | 648 | byte-identical |
| `V4.M5.EN.2` | 12 | 12 | byte-identical |
| `M3.S.2` | 15 | 15 | byte-identical |
| `SDT.ACTIVE.AUX.2` | 594 | 594 | byte-identical |
| `M1.S.2` | 16 | 16 | byte-identical |
| `M1.S.3/.4/.5` | 32 / 193 / 64 | 34 / 190 / 62 | pin-access wiggle |
| `M5.AUX.1` | 0 | **32** | off-grid strap edges |
| `M5.W.3` | 46 | **0** | route-dependent |

Totals: 1,620 → 1,603 — not a fix. A marker-serializing rerun attributes every one of the 32 new
`M5.AUX.1` markers: all sit at M5 strap edges **6 nm off the 24 nm grid** (16 edge positions across the
four strap columns), exactly what r5 derived from the floorplan DEF and the preset docs warn for this
core origin. `M6.AUX.1` stays 0. And `M5.W.3` is **route-dependent, not strap-geometry-bound**: the
same netlist routed with zero `M5.W.3` under the shifted strap blockages — but that route is the one
this core origin cannot use, because it carries the off-grid family. The two families trade through the
one field that positions the straps; neither setting clears both.

**Verdict per family, with the upstream disposition each now carries:**

- `V4.M4.EN.1` (648) / `V4.M5.EN.2` (12): recipe-inherent — counts byte-identical under both offsets,
  and the count is the M2↔M5 stack crossings exactly. The tech LEF's wide V4 bar
  (`VIARULE M5_M4widePWR0p864`, the only wide V4 for the recipe's 0.216 M5) has zero M4 enclosure.
  [#4499](https://github.com/2AMLogic/klayout-tools/issues/4499) shipped the preset with this
  documented; the pin's own preset docs state *no existing request field changes that*.
- `M3.S.2` (15): recipe-inherent — byte-identical under both offsets; pdngen's M2↔M5 stack M3 stubs sit
  closer than the deck's 40 nm along-track spacing at some rail pitches.
  [#6030](https://github.com/2AMLogic/klayout-tools/issues/6030) closed completed 2026-11-17 (*no
  connect tuning moves them*), with the residual documented post-pin by
  [#6180](https://github.com/2AMLogic/klayout-tools/issues/6180) (merged after the 0.9.2 cut, so the
  pin's docs do not carry it yet).
- `M5.W.3` (46): route-dependent, not recipe-inherent — but not clearable by the preset form either
  (the offset that removes it is the one this core origin cannot use). Filed generically from this
  trace as [#6453](https://github.com/2AMLogic/klayout-tools/issues/6453): TritonRoute M5 landing
  patches can exceed the `M5.W.3` width buckets under PDN-strap congestion; no request field moves
  them.

For issue #228 this settles its step 3: the grid families stand as recorded, by name and count, with
upstream issues; no in-flow change to the committed grid clears them, and the alternative to the grid —
dropping the straps — is the #66 trade this issue's own acceptance criteria prohibit. The envelope
consequence: no committed stream changed, so item 2's attestation (`evidence/item2.r9.json`) stays
current, `klt signoff` item 3 stays **unmet**, and the manifest still cites no record in this
directory. No envelope is committed for the scratch stream (its input hash names a deliberately
discarded file, so `klt drc --check` could not re-verify it off the authoring host); the summary,
coverage and marker attribution an envelope would carry are recorded inline in the r6 record. Issue
#228's step 2 (`M1.S.*`) and step 1 (`SDT.ACTIVE.AUX.2`) are separate measurements, not taken here.

## Issue #228 step 2: `via_pad_trim` cannot touch the `M1.S.*` family (r7, 2026-11-17)

Record: `lane_column.r7.drc.run-record.json`, with the summary envelopes
`slice_routed.r7.envelope.json` and `lane_column.r7.envelope.json` committed beside it. klt **0.9.2**
(the pin), `--engine klayout` with the packaged ASAP7 deck (bytes identical to r5/r6's,
`fa303c03...`), the same **267**-id expectation file as r3–r6 (byte-identical, re-hashed), no
`--rules`, no `--waivers`, nothing filtered or relaxed. The nine earlier records are unedited. One
environment note: the pinned package was installed into a throwaway venv on the host python 3.12
rather than via `uvx` — `uvx` resolution hangs on this worker because the uv-managed cpython 3.11
it selects is a broken shim (an infinite exec loop left by an earlier step, a host defect). The
equivalence chain to the pin is exact: same dist-info version (0.9.2), same `klt_git_commit`
`046ba746...` r6 records, same deck bytes. Both committed envelopes re-verify `klt drc --check`:
`match`, exit 0 (input and deck hashes).

**Committed streams re-measured, byte-identical to r5.** Slice `cc4a7c72...` → 1,620 violations /
9 rules; column `66179d88...` → 25,920 / 9, exactly 16× the slice in every rule count as at r4/r5.
This pass therefore becomes the committed streams' current measurement of record (r5's counts,
re-run rather than inherited — the marker attribution below is derived from the same pass, so
summary count and marker count are one measurement).

**Why the family survives: the trim has nothing left it is allowed to do.** Issue #228's step 2 asks
why the P&R flow's `via_pad_trim` pass (klayout-tools#4495's post-route `VIA_*` M1 pad trim) leaves
`M1.S.2/.3/.4/.5` (4,880 on the column, 305 on the slice) in place. Measured on the committed slice
against the pinned module:

- The pass already did its one possible edit on this stream: the committed report carries
  `via_pad_trim` `status: trimmed`, `cells_touched: 1`, `pads_trimmed: 1`, `pads_shrunk: 0`,
  `pads_left: 1`. Of the slice's 8 `VIA_*` cells exactly one still carries M1 landing-pad geometry —
  `VIA_VIA12`, the router's standard V1 via cell, one 18 × 22 nm pad at 8,905 placements. The
  dropped pad is the power via array's merged M1 pad (fully wire-covered in all placements), the
  only cell the pass rewrote.
- **Drop test fails at 92.5% of placements.** The surviving pad protrudes past routed M1 at 8,237
  of its 8,905 placements — precisely the wire-endpoint placements where the pad *is* the
  connection. The pass may drop a pad only when every placement is fully wire-covered, so this pad
  is not redundant.
- **Shrink test fails by construction.** The pass's shrink floor is the V1 cut (18 × 18 nm) sized by
  its 5 nm enclosure bound on all four sides = 28 × 28 nm. The pad (18 × 22 nm) is a strict *subset*
  of that floor: `pad & (cut sized 5 nm) == pad`, so the pass's own strict-reduction test rejects any
  change. The shipped pad already sits at the LEF VIARULE minimum; no smaller deck-legal pad exists
  for the pass to produce. (The 5 nm bound is the deck's `V1.M1.EN.1` side value — a rule the deck
  itself lists as unmodeled, so the floor is the pass's convention, not a checked constraint.)
- **The violations are placement-specific and invisible to both tests.** A marker-serializing slice
  run at the pin serialized all 1,620 markers; the 305 `M1.S.*` markers match the summary counts
  byte-identically (16 / 32 / 193 / 64). 270 of the 305 marker bboxes interact with a surviving pad
  placement; 35 are pad-free routed-wire tip pairs. The buckets are tip-topology pairs per the
  deck's Table 3.12.1 (`S.4` tip-to-tip both < 24 nm dominates at 193). Both trim tests are uniform
  across every placement of a cell and neither reads deck spacing, so a pad that is required at one
  placement and too close to a neighbor at another cannot be edited at all; edits are per-cell
  master shapes, never per-instance.

**Upstream disposition.** The standing gap is
[#4508](https://github.com/2AMLogic/klayout-tools/issues/4508) (open): *trim protruding `VIA_*` M1
pad tips to clear `M1.S.2`-`M1.S.5`*, the successor to the closed-as-no-op #4495 the r2–r4 records
cite. Two measured facts from this pass sharpen #4508's acceptance criteria and were posted there
generically (2026-11-17): (1) the pin's `trim_via_pads` already implements #4508's
shrink-to-minimum-enclosure fallback, and it is a mathematical no-op for a pad already inside the
floor — the remaining upstream work is the protruding-tip policy, not the shrink; (2) the family's
markers are placement-specific, so any per-cell-uniform policy (including protruding-tip trimming of
the master cell) fixes a placement's violation only where the same edit is connectivity-safe at
every placement of that cell. From this record on, #4508 is the family's live disposition; the
#4495 citations in the r2–r4 sections above are historical.

For issue #228 this settles its step 2. Envelope consequence: no committed file changed in this
pass, so item 2's attestation (`evidence/item2.r9.json`) stays current, `klt signoff` item 3 stays
**unmet**, and the manifest still cites no record in this directory. Step 1 (`SDT.ACTIVE.AUX.2`,
9,504) is a separate measurement, not taken here.



## Issue #228 step 1: the `SDT.ACTIVE.AUX.2` family is cleared at the source (r8, 2026-11-18)

Record: `lane_column.r8.drc.run-record.json`, with the summary envelopes `slice_routed.r8.envelope.json`
and `lane_column.r8.envelope.json` committed beside it. klt **0.9.2** (the pin, installed into a
throwaway venv on the host python 3.12 — the same uvx-hangs host defect r7 records), `--engine klayout`
with the packaged ASAP7 deck (bytes identical to r5–r7's, `fa303c03...`), the same **267**-id
expectation file as r3–r7 (re-derived from `RULE_IDS` at the pin, byte-identical to r7's), no
`--rules`, no `--waivers`, nothing filtered or relaxed. The eleven earlier records are unedited. The
committed **streams changed** this pass — this record is their new measurement of record, replacing
r7. Still **not clean**; layout results against a predictive PDK, not measurements. Both committed
envelopes re-verify `klt drc --check`: `match`, exit 0 (this host holds the deck at the recorded
absolute path, so unlike r7's envelopes both halves re-verify here).

**The measurement first.** Every leaf cell of the shipped `asap7sc7p5t_28_R.gds` (212 cells) was
placed once on a wide-spaced 40 × 20 µm grid and run through the full deck at the pin;
`SDT.ACTIVE.AUX.2` markers attributed by grid position flag **exactly ten masters**
(AO33x2, OAI22xp33, BUFx4f, CKINVDCx9p33, BUFx4, BUFx2, ICGx5p33DC, ICGx4DC, ICGx6p67DC,
ICGx2p67DC — all `_ASAP7_75t_R`; 23 markers). The rule fires on real shipped-cell geometry (SDT
horizontal edges that coincide with no ACTIVE horizontal edge, deck Table 3.8.1), so **no deck bug**
— nothing filed upstream for this family; the r2–r5 citations of the closed #4496 were deck-side.

**The swap.** The ten masters are excluded from synthesis (`constraints.dont_use` in
`design/synth/slice.synth.json`; ABC re-maps OAI22xp33 → OAI22xp5, BUFx2 → BUFx3/BUFx12f) and the
CTS buffer moves `BUFx4 → BUFx3` in `layout/pnr/slice.pnr.json` because BUFx4 is one of the ten;
everything else in the request is unchanged (same straps, floorplan, tracks, seed 1). The netlist
was re-synthesized, the slice re-routed, the column re-assembled. The routed netlist re-introduces
no deviator (resizer included). One note: `constraints.abc_constr.driving_cell` stays BUFx2 although
BUFx2 is dont_use'd — the driving cell is ABC's input-delay model, not a mapping candidate; no BUFx2
appears in either netlist.

| Rule (slice) | r7 | r8 | | Rule (column) | r7 | r8 |
|---|---|---|---|---|---|---|
| `SDT.ACTIVE.AUX.2` | 594 | **0** | | `SDT.ACTIVE.AUX.2` | 9,504 | **0** |
| `V4.M4.EN.1` | 648 | 644 | | `V4.M4.EN.1` | 10,368 | 10,304 |
| `V4.M5.EN.2` | 12 | 16 | | `V4.M5.EN.2` | 192 | 256 |
| `M1.S.2/.3/.4/.5` | 16/32/193/64 | 24/33/187/50 | | `M1.S.2/.3/.4/.5` | 256/512/3,088/1,024 | 384/528/2,992/800 |
| `M3.S.2` | 15 | 10 | | `M3.S.2` | 240 | 160 |
| `M5.W.3` | 46 | 19 | | `M5.W.3` | 736 | 304 |
| `M4.AUX.1/.2` | 0/0 | **4/4** | | `M4.AUX.1/.2` | 0/0 | **64/64** |
| **Total** | 1,620 | **991** | | **Total** | 25,920 | **15,856** |

The column is again exactly **16 ×** the slice in every rule — the assembly still adds nothing.

**Dispositions.** `SDT.ACTIVE.AUX.2`: cleared. `M1.S.*`: standing #4508 (open). `V4.M4.EN.1` /
`V4.M5.EN.2`: recipe-inherent per r6 (#4499). `M3.S.2`: recipe-inherent per r6 (#6030 closed
completed, residual documented by #6180). `M5.W.3`: route-dependent per r6 (#6453). The one new
family, `M4.AUX.1/2`, is the **off-grid router-M4-line-end mode** r2 attributed to the closed #4501:
a marker-serializing slice run puts all 8 slice markers at two x-positions, both off the deck's
48 nm M4 grid (offsets 37 / 25 nm mod 48) — one cluster per slice. Re-filed generically from this
pass as [#6596](https://github.com/2AMLogic/klayout-tools/issues/6596) (no open issue covered the
mode; r2's measurement that no request field moves it still stands).

**Post-route STA (AC 2).** With the cell swap the routed artifacts changed, so the timing chain was
re-taken append-only: `sta/slice.sta.r7.report.json` (pre-route successor to r5 on the re-synthesized
netlist — honestly worse: setup −0.097 / −0.285 / −0.011 ns at tt/ss/ff, hold positive) and a new
post-route record `sta/slice.sta.routed.report.json` — `klt sta` def-mode over the routed DEF with
the run's post-route SPEF at tt/ss/ff: **setup and hold 0 violations at every corner** at the P&R's
0.5 ns constraint (worst setup slack +0.262 / +0.131 / +0.319 ns). The routed report carries
`annotation_complete: false` (2,518 of 2,712 nets named by the SPEF) — the known net-name-coverage
gap, recorded with the numbers. `regen.py` now also persists the routed DEF and post-route SPEF
beside the GDS/SDF so the record's inputs are committed, hashed files.

**Power delivery (AC 3).** Not regressed: same recipe over a **1.3 % smaller core**
(945.994 → 933.12 µm²); VDD 1,016 → 1,004 stripe segments and 1,085 → 1,072 vias, VSS 1,021 → 1,016
and 1,089 → 1,085, followpins 243 → 240 (VSS 243 unchanged), `missing` 0 before and after — every
delta proportional to the core shrink. `fmax_mhz` 3,731.41 → 4,274.54; setup/hold 0/0 before and
after.

**Signoff consequence.** Both streams changed, so the chain moved with this pass: item 1 re-attested
(`evidence/item1.r11.json`), item 2 re-attested (`evidence/item2.r10.json` over the new column,
companion inventory `attest/item2.r10.json`; `layout/pad_check_record.json` re-ran 34/34
byte-identical), routed-slice LVS re-taken as r16 on the new stream (`evidence/item4-lvs/
slice_routed.r16.*` — still `mismatch`, recorded honestly), item 8 re-pointed and re-attested,
manifest re-pinned, verdict regenerated: `t1_met_count` 11 unchanged. `klt signoff` item 3 stays
**unmet** and the manifest still cites no record in this directory.

## r9: lane column after the #253 `driving_cell` re-synthesis (2026-11-18)

`lane_column.r9.envelope.json`: `klt drc --engine klayout` (klt 0.9.2 pin, packaged `asap7.drc`, the 267-id
expectation set of the r8 envelope, no waivers, no filtering) on the committed `layout/lane_column.gds`
(`sha256:4b7c1aaf...`), which embeds the slice re-routed after `abc_constr.driving_cell` moved to
`BUFx3_ASAP7_75t_R`. Status `violations`, **15,600** violations across 8 rules, coverage assertion
satisfied. **`SDT.ACTIVE.AUX.2`: 0**, from this fresh run. Counts: M1.S.2 576, M1.S.3 528, M1.S.4 2,544,
M1.S.5 704, M3.S.2 160, M5.W.3 528, V4.M4.EN.1 10,304, V4.M5.EN.2 256. `M4.AUX.1/2` (64+64 at r8) are
absent. Versus r8 (15,856): the route-dependent families moved with the re-route. Not clean, and item 3
stays unmet. The routed slice alone was **not** re-run, and `klt drc --check` was **not** run on the
envelope. Its deck is recorded by a machine-local path under a throwaway venv (`/tmp/...`), the same
limitation as the earlier `--engine klayout` records. Layout results against a predictive PDK.

## r10: lane column re-taken on the klayout pin, superseding r9 (2026-11-18, issue #257)

`lane_column.r10.envelope.json`: the same measurement as r9, re-run because **r9 was off-pin**. r9 was taken
with klayout **0.30.13** against the `.github/klayout-version` pin of **0.30.12** and flagged this itself
(`klayout_version_mismatch: true`). r10 pins both: `klayout-tools==0.9.2` and `klayout==0.30.12`
(`uv run --no-project --with ... --with ... klt drc`, the `signoff.yml` invocation), `--engine klayout`,
packaged `asap7.drc` (`fa303c03...`, unchanged), the same 267-id expectation set as r9 (satisfied), no
waivers, no filtering, on the unchanged committed `layout/lane_column.gds` (`sha256:4b7c1aaf...`).
Provenance reads `klayout_version` 0.30.12, `klayout_version_mismatch: false`, `klt_version` 0.9.2.
Result: **15,600** violations across the same 8 rules with identical per-rule counts to r9, and
**`SDT.ACTIVE.AUX.2`: 0** (absent from `rule_counts`), so on this deck and layout 0.30.12 and 0.30.13 agree.
That is one measurement, not a general equivalence claim. r9 is kept unedited (append-only); r10 supersedes
it as the record of the committed column. The deck is recorded by a machine-local uv-cache path, the same
limitation as the earlier `--engine klayout` records; `klt drc --check` was not run. The routed slice alone
was not re-run. Still not clean; layout results against a predictive PDK.

## r11: the in-flow levers measured and the two route-dependent families attributed (2026-11-22, issue #272)

Record: `lane_column.r11.drc.run-record.json`, with `lane_column.r11.envelope.json` (the committed column, summary-only) and
`slice_routed.r11.envelope.json` (the committed routed slice, every marker serialized). klt **0.9.2** (the pin, installed into a
throwaway venv inside the issue worktree), `--engine klayout`, packaged `asap7.drc` (`fa303c03...`, unchanged), the same **267**-id
expectation set as r3–r10 (re-derived at the pin and compared name for name with r10's), no `--rules`, no `--waivers`, nothing filtered
or relaxed. OpenROAD is klt's pinned docker image (`26Q3-1510-g6cb3f2b704`, the engine the committed report records). Both new
envelopes record their deck through a path relative to the checkout and re-verify `klt drc --check` on this host: `match`, exit 0
(the deck leg resolves wherever klt 0.9.2 is installed at that same relative path; elsewhere only the input leg re-verifies). The earlier records are
unedited. **No committed stream changed in this pass.** Still **not clean**; layout results against a predictive PDK, not measurements.

**Control.** `layout/pnr/slice.pnr.json` unmodified, through the same scratch harness `regen.py` uses, reproduces the committed stream
byte for byte: GDS `b961426a...`, DEF, netlist and SPEF identical, SDF different only at its wall-clock DATE line, with the committed
report's fmax, setup/hold 0/0 and every PDN segment and via count. The sweep is measured against that baseline.

**Committed streams re-measured.** Slice `b961426a...` → **975** violations / 8 rules, the routed slice alone under the full deck for
the first time since r8 and exactly one sixteenth of the column in every rule. Column `4b7c1aaf...` → **15,600** / 8 with per-rule
counts identical to r9/r10. `klt drc --check` on r10's own envelope re-hashes the input but reports the deck leg `actual: None`, because
r10 records its deck at a machine-local uv-cache path; the r11 envelopes carry the same deck hash through a path that re-verifies here.

**Sweep (step 1): no in-flow setting clears a family.** Ten place-and-route runs, serially: the control and nine points, each on a
scratch copy of the request that changes only the named fields, routed to scratch and measured at the pin with all markers serialized.
The ninth point, `m1.10off`, keeps a margin-1.10 route whose M5 strap offset was left at the committed value and is off-grid at that core
origin; it is kept because it re-measures the r6 trade exactly. Slice counts; the column has
been exactly 16 × the slice in every rule at every measurement since r2, so slice counts are read as column ÷ 16. The sweep points run
without the post-route extraction pass, which executes after the route stage and rewrites nothing; their timing is the in-flow
post-route estimate (the control ran the full flow and matches the committed `spef_sta` block).

| Point | Request delta | Core origin (nm) | `M1.S.2/.3/.4/.5` | `M3.S.2` | `M5.W.3` | `V4.M4.EN.1` / `V4.M5.EN.2` | New families | Total (Δ) | Setup / hold, power |
|---|---|---|---|---|---|---|---|---|---|
| committed | — | 1026, 1080 | 36/33/159/44 | 10 | 33 | 644 / 16 | — | **975** | 0 / 0, complete |
| `seed2` | `seed` 2 | 1026, 1080 | 26/36/165/34 | 16 | 20 | 644 / 16 | `M4.AUX.1` 4, `M4.AUX.2` 4 | 965 (-10) | 0 / 0, complete |
| `seed3` | `seed` 3 | 1026, 1080 | 30/39/144/56 | 9 | 14 | 644 / 16 | `M4.AUX.1` 4, `M4.AUX.2` 8, `M4.W.3` 2 | 966 (-9) | 0 / 0, complete |
| `seed4` | `seed` 4 | 1026, 1080 | 18/39/159/46 | 15 | 41 | 644 / 16 | — | 978 (+3) | 0 / 0, complete |
| `u35` | `utilization_pct` 35 | 1026, 1080 | 20/44/168/51 | 21 | 46 | 860 / 15 | `M4.AUX.1` 4, `M4.AUX.2` 4 | 1233 (+258) | 0 / 0, not captured |
| `u45` | `utilization_pct` 45 | 1026, 1080 | 18/27/162/52 | 12 | 29 | 608 / 16 | — | 924 (-51) | 0 / 0, complete |
| `m0.95` | `core_margin_um` 0.95 + M5 strap `offset_um` 0.312 | 972, 1080 | 22/29/164/53 | 17 | 16 | 644 / 16 | — | 961 (-14) | 0 / 0, complete |
| `m1.05` | `core_margin_um` 1.05 + M5 strap `offset_um` 0.300 | 1080, 1080 | 27/33/173/52 | 10 | 40 | 648 / 12 | — | 995 (+20) | 0 / 0, complete |
| `m1.10off` | `core_margin_um` 1.10 + M6 `offset_um` 0.330, M5 offset left at 0.306 (off-grid there) | 1134, 1350 | 68/0/102/82 | 6 | 0 | 644 / 16 | `M5.AUX.1` 32 | 950 (-25) | 0 / 0, complete |
| `m1.10` | `core_margin_um` 1.10 + M5 `offset_um` 0.318 + M6 `offset_um` 0.330 | 1134, 1350 | 67/0/98/81 | 6 | 57 | 644 / 16 | — | 969 (-6) | 0 / 0, complete |

Per lever:

- **`seed`** moves only the route-dependent families. Seeds 2 and 3 lower the total but re-introduce the closed-#6596 off-grid
  router-M4 mode (`M4.AUX.1/2`, and `M4.W.3` at seed 3): rejected by the adoption gate. Seed 4 keeps the eight families and raises the
  total by 3: rejected.
- **`utilization_pct` 35** grows the core and with it the recipe-inherent `V4.M4.EN.1` (644 → 860) and adds the M4 mode: rejected. **45** shrinks the core (`V4.M4.EN.1` → 608) and is the lowest total of the sweep
  (924, −51) with the same eight rules, in-flow setup/hold 0/0 and power delivery `complete`: it meets the adoption gate and clears nothing.
- **`core_margin_um`** moves the core origin onto other site phases; each margin is paired with the M5 strap offset (and at 1.10 the M6
  offset) that puts every strap edge back on the deck grid, checked on each routed DEF (`M5` edges ≡ 0 mod 24 nm, `M6` edges ≡ 0 mod
  32 nm; no `M5.AUX.1`/`M6.AUX.1` on any of them). 0.95 (961, −14) and 1.10 (969, −6, with `M1.S.3` absent) are gate-eligible; 1.05 raises the total. `m1.10off` is the r6 trade measured again: `M5.AUX.1` 32 against `M5.W.3` 0, which is also the deck-side reading of `M5.W.3` below (off-grid strap edges cannot pair with an on-grid signal shape).
- **`M5.W.3` is not cleared anywhere**: 20 (`seed2`), 14 (`seed3`), 41 (`seed4`), 46 (`u35`), 29 (`u45`), 16 (`m0.95`), 40 (`m1.05`), 57 (`m1.10`) on the on-grid points, and 0 on the one off-grid point. The r6 observation stands: the
  only offset that ever drove it to zero is the one that puts the strap edges off the grid and buys `M5.AUX.1` instead.

No setting is adopted. The three gate-eligible points lower the total by 5.2 %, 1.4 % and 0.6 % without changing any family's disposition or item 3; adopting one changes the committed streams and pulls the
whole r8 chain (re-route, column re-assembly, LVS re-take, item 2 and 8 re-attest, manifest re-pin, verdict regenerate, post-route STA
re-take), which is not worth landing inside a measurement pass. Recorded as #290 for a decision.

**`M1.S.*` (step 2): every marker is the router's `VIA_VIA12` landing pad, including the 40 "pad-free" boxes.** The r7 split re-taken on
the committed slice reproduces klayout-tools#6992's baseline on the same stream: 40 of 272 marker boxes have no interaction, boundary
contact included, with the M1 of any placed `VIA_*` cell (`M1.S.2` 5, `M1.S.3` 33, `M1.S.4` 0, `M1.S.5` 2). Attribution goes further:

- *Pad removal.* Deleting the single M1 shape of the `VIA_VIA12` cell in a scratch copy of the stream and re-running the full deck gives
  **0** `M1.S.2`–`M1.S.5` markers (from 36 / 33 / 159 / 44) with `M3.S.2`, `M5.W.3`, `V4.M4.EN.1` and `V4.M5.EN.2` unchanged
  (`V1.AUX.1` appears only because V1 is no longer enclosed). The whole family is that pad.
- *No router wire is involved.* The request routes signals on M2–M7 (`set_routing_layers -signal M2-M7`); the routed DEF carries no M1
  signal segment, and the only top-level M1 is the followpin rail. r7's "pad-free routed-wire tip pairs" was an inference from the box
  predicate, not a trace.
- *How a box becomes "pad-free".* In all 33 `M1.S.3` cases (one tie-high master) the pad overlaps the cell's own M1 pin shape 31 nm
  (edge to edge) from the marker. The merged polygon's 77 nm edge, a "side", is split into two tip-length edges (32 and 27 nm), and one
  of them now pairs 25 nm away with a tip edge of the same cell under the 27 nm tip-to-tip limit. In the isolated master that edge stays
  77 nm long, the same pair is a 25 nm side-to-tip pair exactly at the `M1.S.2` limit, and nothing fires: every one of the 212 masters
  of the pinned library placed once on a wide-spaced grid gives **0** `M1.S.*` markers under the full deck (40 violations, the r8
  per-cell result: 23 `SDT.ACTIVE.AUX.2` and 17 isolation-only FEOL findings). The marker box is the 1 nm projection overlap of the two
  edges and lands where neither edge belongs to the pad. The 5 `M1.S.2` boxes (one NOR master, pad 16–27 nm away) and the 2 `M1.S.5`
  boxes (one clocked-inverter master, pad 7 nm away) follow the same pattern.
- *No request field can move them.* The 0.9.2 request has no pin-access or detailed-route field (its routing-adjacent keys are `seed`,
  also passed as `detailed_route -or_seed`, `route_critical_nets_percentage`, `route_congestion_iterations`,
  `route_allow_congestion`, `max_antenna_repair_iterations`, `placement_density`, `io.layer_h`/`layer_v` and `library.route_layers`);
  the generated route stage calls `detailed_route` with `-output_drc`, `-output_maze` and `-or_seed` only and never calls `pin_access`.
  The generic finding is posted on klayout-tools#6992 (its pad-free population is empty on this design once attribution is by geometry).

Upstream state moved while this was measured: #4508 closed completed 2026-11-22 after a before/after on an inverter-chain fixture that
did not reduce the count; its residual #7122 closed completed the same day through PR #7142 (*repair opposing ASAP7 M1 landing pads
without reducing cut coverage*), which is on main but in no published release (latest v0.9.2, 2026-11-15). Whether PR #7142 clears this
block's 272 is **not measured**: this record measures at the pin. From this pass on the family's live dispositions are
klayout-tools#6930 (open: cut the release that carries the unreleased pad fixes) and klayout-tools#6992.

**`M5.W.3`: a deck-side cross-polygon edge pair, not a landing-patch width.** Every `M5.W.3` marker of the committed slice and of all
nine sweep points was attributed against the merged M5 geometry, and in every case the marker box spans two different polygons
(committed 33/33, seed2 20/20, seed3 14/14, seed4 41/41, u35 46/46, u45 29/29, m0.95 16/16, m1.05 40/40, m1.10 57/57); `m1.10off` has no `M5.W.3` marker at all. One
vertical edge belongs to a PDN strap and the facing edge to a separate 24 nm signal landing shape in the gap between two straps,
exactly 336, 384, 432 or 480 nm apart (14, 16, 18 or 20 × 24 nm: strap 216 + router clearance 96/144/192/240 + signal 24). No M5 polygon of that
width exists and no marker box lies inside a single polygon. The cause is the deck: `W.3` is
`track_edges(m, dir).width((w + 0.25).nm, projection)` over the merged layer's edge set, which has no polygon context, so a strap's
outer edge and a signal shape's far edge pair across the empty gap between them. Reproduced on a three-shape layout with the deck's own
expression (KLayout 0.30.12): a 216 nm shape and a separate 24 nm shape 96 nm away next to a real 336 nm shape give two edge pairs, the
real width and the cross-polygon pair; the polygon-aware `m.width(...)` on the same merged region gives the real width only. The count
is route-dependent only through which on-track signal shapes land an even number of tracks from a strap edge, which is also why r6's
off-grid strap offset drove it to zero without touching any signal geometry. Filed as klayout-tools#7226; klayout-tools#6453 (open,
docs-only) keeps the route-dependent count but its landing-patch attribution is superseded.

**Each remaining family, with its open disposition (issue #272 acceptance criterion 2):**

| Family | Column (r11) | Cause | Open issue |
|---|---|---|---|
| `V4.M4.EN.1` / `V4.M5.EN.2` | 10,304 / 256 | PDN wide-V4 stack, recipe-inherent (r6); count = the M2↔M5 stack crossings, so it moves only with core size | 2AMLogic/klayout-tools#6909 |
| `M3.S.2` | 160 | pdngen M2↔M5 stack stubs (r6); same stack | 2AMLogic/klayout-tools#6909 |
| `M1.S.2`–`M1.S.5` | 4,352 | the router's `VIA_VIA12` M1 landing pad merged with cell pin metal (this pass) | 2AMLogic/klayout-tools#6930 (release carrying PR #7142) and #6992 |
| `M5.W.3` | 528 | deck `W.3` cross-polygon edge pair (this pass) | 2AMLogic/klayout-tools#7226 |

Closed or docs-only issues that are history, not dispositions: klayout-tools#4508 and #7122 (closed completed 2026-11-22), #6030
(closed), #6596 (closed; the `M4.AUX.*` mode is absent from the committed column) and #6453 (open, docs-only).

**Signoff consequence.** No file that an attestation or the manifest binds changed (`layout/`, `manifests/`, `sta/` and the item-10
inventory members are untouched), so the item 1, 2 and 8 attestations, the manifest pins, the verdict and the item-10 envelope stay
current. Two envelopes are added here and cited from no manifest entry. `klt signoff` item 3 stays **unmet**, the manifest still cites no
record in this directory, and #19 (the clean-run deliverable) is parked on the four open upstream issues above. A pin bump to a release
that carries the pad repair and the `W.3` fix is the next in-repo step: bump `.github/klt-version`, re-route, re-take the column, update
the table.

## r12: slice and column after the #287 dont_use-27 re-synthesis (2026-11-23)

`slice_routed.r12.envelope.json` and `lane_column.r12.envelope.json`: `klt drc --engine klayout`
(klt 0.9.2 pin, packaged `asap7.drc` `fa303c03...`, the same 267-id expectation set as r11 — satisfied on
both runs, `missing_names`/`unexpected_names` empty — no waivers, no filtering, no `--rules`) on the
re-routed streams of issue #287 / decision 0014 (`constraints.dont_use` extended from 10 to 27 masters:
the 17 klt `KNOWN_UNSUPPORTED_ASAP7_CELLS` joined the ten #228 deviators; the 186 `AOI21x1` instances
re-mapped to `AOI21xp5`/`AOI21xp33`, core 937.786 -> 914.545 um²). The slice envelope serializes every
marker (as r11 did); the column envelope is summary-only (`--max-violations 0`, as r11 was). Both were
taken with klt and klayout on their pin files (`klt_version_mismatch: false`), and both re-verify
`klt drc --check` on this host (deck recorded by the worktree-relative `.venv/...` path).

- **Routed slice** (`layout/slice_routed.gds` `c848a459...`): `violations`, **893** violations across the
  same 8 rule families as r11's 975 — M1.S.2 16, M1.S.3 47, M1.S.4 109, M1.S.5 42, M3.S.2 14, M5.W.3 17,
  V4.M4.EN.1 636, V4.M5.EN.2 12. **`SDT.ACTIVE.AUX.2`: 0** (absent from `rule_counts`). No new family
  appears and none clears; the deltas are the re-route moving the route-dependent counts.
- **Lane column** (`layout/lane_column.gds` `94aef664...`): `violations`, **14,288** violations across the
  same 8 families — M1.S.2 256, M1.S.3 752, M1.S.4 1,744, M1.S.5 672, M3.S.2 224, M5.W.3 272,
  V4.M4.EN.1 10,176, V4.M5.EN.2 192 (r11: 15,600). **`SDT.ACTIVE.AUX.2`: 0**, from this fresh run.
- **Dispositions unchanged.** Every family's cause and open upstream issue is the r11 table above:
  `V4.M4.EN.1`/`V4.M5.EN.2`/`M3.S.2` recipe-inherent (#6909), `M1.S.*` the router's VIA_VIA12 landing pad
  (#6930/#6992), `M5.W.3` the deck's cross-polygon edge pair (#7226). Nothing was waived, filtered or
  re-scoped; r1-r11 are unedited.

**Signoff consequence.** The streams changed, so the netlist-bound chain moved with this pass (items 1, 2,
8 re-attested; LVS re-taken as r20; manifest re-pinned; verdict regenerated — see issue #287). `klt signoff`
item 3 stays **unmet** and the manifest still cites no record in this directory; the two r12 envelopes are
cited from no manifest entry, as before. Layout results against a predictive PDK, not measurements.
