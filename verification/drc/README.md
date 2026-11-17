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

