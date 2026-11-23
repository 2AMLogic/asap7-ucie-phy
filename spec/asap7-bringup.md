# ASAP7 bring-up under `klt`

Recorded 2026-10-17 on host `loom-worker-3`. Every figure below is a tool result
against a predictive model (ASAP7). Nothing here is, or implies, a fabricated part.

## Sibling-pin search

`spec/` of `2AMLogic/asap7-riscv-core` and `2AMLogic/asap7-stdcells` held only a
README on `main` on 2026-10-17. `2AMLogic/asap7-npu` has an **open, unmerged** PR
(#6, "draft proposed target spec, ASAP7 pin and memory decision") that pins a
different ASAP7 source (an upstream ASAP7 checkout, not lambdapdk). No sibling pin
was merged, so this repo does the bring-up and records its own pin. When a sibling pin
lands, a new decision record compares the two and adopts one; this pin is not
relaxed in the meantime.

## Pin

| Item | Value |
|---|---|
| Source | `siliconcompiler/lambdapdk`, tag `v0.2.17` (the tag klt's own ASAP7 deck docs pin) |
| Archive | `https://github.com/siliconcompiler/lambdapdk/archive/refs/tags/v0.2.17.tar.gz`, sha256 `ac7e950c4d0394a829658b6e219fea4a4b0c61a998183d5520f8b9e38c6efff2` |
| ASAP7 root in archive | `lambdapdk/asap7` (PDK release 1p7; DRM `base/docs/asap7_drm_201207a.pdf`) |
| License | BSD-3-Clause, Arizona State University |
| `klt` | `0.7.1.dev1757+ge7cca478ef21` (a post-tag build; **no released klt contains the deck this run used**, see below) |
| KLayout | 0.30.12 (standalone binary on `PATH`) |
| ngspice | 42 |

Pinned files used (sha256 of the file as extracted):

| File | sha256 |
|---|---|
| `libs/asap7sc7p5t_rvt/gds/asap7sc7p5t_28_R.gds.gz` | `75a7f40e6fa06fcb3d38c4e4a14db2ab715dc6bf382c58e9252ed5f4526777a6` |
| `libs/asap7sc7p5t_rvt/netlist/asap7sc7p5t_28_R.cdl` | `3e3e2548fb8f571c2e373dcbf565ecb0288e6433e803fbf06561cb16b70caf53` |
| `base/apr/asap7.layermap` | `2ce51d6dae7ed4f7ca3298d7a99a4b0d3d2b956b24cc4e092db8c29dd204a647` |
| `base/apr/asap7_tech.lef` | `830a032810b054d0dc24601c3f57c86073469e6c9cfb0314b2c82eb335b021d2` |

Shipped: technology (`base/setup/klayout/asap7.lyt`, `.lyp`), layer map and tech LEF
(`base/apr`), the 7.5-track library for RVT, LVT and SLVT (`libs/asap7sc7p5t_{rvt,lvt,slvt}`:
GDS, LEF, CDL, Liberty NLDM as `.lib.gz`), and HSPICE BSIM-CMG model cards
(`base/spice/hspice/7nm_{FF,SS,TT}_160803.pm`).

Routing stack (tech LEF, pitch in um): M1 0.036, M2 0.045/0.036, M3 0.036, M4 0.048,
M5 0.048, M6 0.064, M7 0.064, M8 0.08, M9 0.08, then V9 and `Pad` (a routing layer,
width 0.04, pitch 0.08). **ASAP7 does define a layer above M9**: `Pad`, reached through
V9 (`VIA9Pad`). The stream layer number it uses is inconsistent across the pinned
files; see Gaps.

## Commands that work

The scratch directory holds the extracted archive; nothing from it is committed.

```
klt pdk find --pdk-root <scratch>/lambdapdk-0.2.17/lambdapdk --pdk asap7 --format json
    -> resolves; assets.klayout and assets.libs_ref set; compatibility.status "unknown"
klt cells  <scratch>/asap7sc7p5t_28_R.gds        -> 212 cells, all top cells, dbu_um 0.00025
klt clip   <gds> --cell INVx1_ASAP7_75t_R -o <cell>.gds
klt drc <cell>.gds --engine klayout \
    --deck-file <klt site-packages>/klayout_tools/decks/asap7.drc \
    --expect-rule-categories-file <263 ids from decks/asap7_rules.RULE_IDS> --format json
    -> status clean, 0 violations (exit 0) for INVx1_ASAP7_75t_R and DFFHQNx1_ASAP7_75t_R
klt extract <cell>.gds --deck asap7 -o <cell>.ext.json --format json
    -> status extracted; INVx1: nmos_rvt 1, pmos_rvt 1 (nfin 3, l 0.02 um), 6 nets
```

DRC deck content hash reported in the run: `sha256:08dba3ee047a3ec68b3cd761f982809c62a0d128b8d34ef4e76a28f61221aa6a`
(`released: false`). `klt deck info` reports the released deck as
`sha256:30a8d86cc36f99ffc54b0c86ab69a737acd91ba0fd21f6de3c842f9fba9d2aaf` (0.7.0). The
two differ: the run used the dev build's deck. Re-run against a released klt
that carries the deck before treating DRC results as final evidence.

## What does not work, or is unverified

| Item | Result | Upstream |
|---|---|---|
| `klt drc --deck asap7` (curated engine) and `klt deck rules --deck asap7` | rejected as `unknown deck` although help lists `asap7` | 2AMLogic/klayout-tools#3783 |
| Locating the packaged deck file for `--deck-file` | no CLI way; path taken from site-packages | #3789 |
| `--engine klayout` on a multi-top stream, `--top` | raw KLayout error; `--top` unsupported. Worked around with `klt clip --cell` | #3788 |
| Coverage assertion count | docs state 263 and 232 in different places; 263 matched the declared ids | #3790 |
| Liberty as `.7z`, non-open_pdks tree for `klt synthesize` | not an issue for lambdapdk (`.lib.gz`); the unmerged sibling pin hits it | #3782 |
| BEOL rules needing track / net / corner predicates | 67 rules not implemented (see below) | #3147 |
| PAD layer number inconsistent; no PAD rules, no PAD coverage line | filed by this issue | #3807 |
| LVS of a shipped cell against the shipped CDL | **mismatch** for INVx1 and DFFHQNx1: `device.unmatched` on every device and `net.unmatched` on all nets, with `device.body_unverified` (bodies resolve to deck-synthesized `vsubs`) and `net.supply_fragmented` (VDD in two layout nets). Shipped cells carry no tap, so body and well nets cannot resolve. Tried `options.supply_nets` and `flatten_reference`; same result. Extraction itself works. | tracked by klayout-tools#2813 (open work on the LVS path); not re-filed |

LVS request used (shape the installed klt accepted): `{"layout":{"file":..,"deck":"asap7","top":..},
"reference":{"netlist":"asap7sc7p5t_28_R.cdl","top":..}}`. The LVS path is therefore
**established for extraction and not yet for a clean compare**. The spec's LVS acceptance
(decision 0005) is written to match.

## Rules the deck does not check

Source: `decks/asap7_rules.py` (`NOT_IMPLEMENTED`, 67 entries) and the deck header.

- **PAD layer**: no rule applies to PAD itself. Only `V9.PAD.EN.2` (V9 enclosed by PAD on two
  opposite sides, 20 nm) and `V9.AUX.1` (V9 inside M9 and PAD) read it, with PAD taken as
  stream layer 96/0. The deck states the PAD layer is "not checked" in its header. There is no
  PAD width, spacing, area, density or array/pitch rule.
- **Bump-related**: no bump or pad-array rule, no pitch rule, no pad-opening or passivation layer,
  no under-bump keep-out, no check that a pad sits over its V9/M9 stack beyond the two V9 rules,
  no density rule (the DRM states none; the tech LEF lists Pad min/max density 20/80 over a 100 um
  window, which the deck does not read).
- Routing-track-dependent: V0-V3 `S.1`-`S.4`, exact/paired enclosure `V0.M1.EN.1`, `V1.M1.EN.1`,
  `V1.M2.EN.2`, `V2.M3.EN.2`, `V0.LISD.EN.2/.3`, `V0.LIG.EN.4`, `V0.LIG.AUX.2`, `V*.M*.AUX.2` (#3147).
- M4-M7: `W.4`, `S.3`-`S.5`, `AUX.4` (track predicates); V4-V7 `S.2` (needs nets); V7 `W.1`,
  `V7.M8.AUX.2` (M8 direction).
- M8/M9 `S.4`-`S.8` (the DRM tables contradict each other under any consistent reading).
- `GATE.AUX.2`, `ACTIVE.AUX.3`, `ACTIVE.LUP.1` (latch-up).
- Mask colouring, and the metal-grid offset other than 0 nm.
- Density: the DRM states none, so none is checked.
- Shipped cells that deviate from the DRM: `SDT.ACTIVE.AUX.2` in AO33x2, BUFx2, BUFx4, BUFx4f,
  CKINVDCx9p33, ICGx2p67DC, ICGx4DC, ICGx5p33DC, ICGx6p67DC, OAI22xp33 (klt keeps the rule and
  leaves these cells out of its clean run). The two cells above are not in that list.

A DRC-clean verdict from this deck therefore means "no violation of the implemented rules",
never "meets the whole DRM".

## Liberty corners

All names are the shipped files under `libs/asap7sc7p5t_rvt/nldm/`, for the cell classes AO,
INVBUF, OA, SEQ, SIMPLE. Header values are read from each file:

| Corner | File suffix | nom_voltage | nom_temperature |
|---|---|---|---|
| TT | `_RVT_TT_nldm.lib.gz` | 0.7 | 25 |
| SS | `_RVT_SS_nldm.lib.gz` | 0.63 | 100 |
| FF | `_RVT_FF_nldm.lib.gz` | 0.77 | 0 |

**Anomaly**: `asap7sc7p5t_SIMPLE_RVT_FF_nldm.lib.gz` declares `nom_voltage 0.7` and
`nom_temperature 25` (the TT point), while the other four RVT FF files declare 0.77 V / 0 C.
STA at the FF corner would mix operating points across cell classes. This is recorded, not
worked around; the STA gate in decision 0005 requires the FF run to report the operating
condition of every Liberty it loads. LVT and SLVT libraries ship the same three corners and are
out of the corner set (decision 0005).

## BSIM-CMG in the open flow

See `decisions/0003-simulation-flow.md`. Short form: the Verilog-A source compiles to an
OSDI module with OpenVAF-Reloaded, and this host's ngspice 42 refuses to load it.

## Filed upstream

Already open when this was written: 2AMLogic/klayout-tools#3783, #3788, #3789, #3790, #3782,
#3147, #2813. Filed here: **#3807** (PAD layer number, rules and coverage).

## LVS under klt 0.8.1 (appended 2026-10-28, issue #20)

Recorded with `klt 0.8.1.dev506+g22ab89a42ad0`, KLayout 0.30.12, against the pinned lambdapdk
v0.2.17 files above. The rows in "What does not work" are left as written; this section
supersedes the shipped-cell LVS row only. Predictive-model tool results; nothing is fabricated.

- **Shipped-cell compare now matches** (klayout-tools#2813, fixed in klt v0.8.0): `INVx1_ASAP7_75t_R`
  and `DFFHQNx1_ASAP7_75t_R`, clipped from the pinned `asap7sc7p5t_28_R.gds`, against the pinned
  `asap7sc7p5t_28_R.cdl`, report `status: match`, engine `klayout`, `power_connectivity: unchecked`.
  The request carries `options.finfet_bulk {nmos: VSS, pmos: VDD}`, klt's disclosed comparison-side
  bulk policy for cells that draw no taps. Two cells only; the rest of the library was not run.
- **The block's own LVS has no report.** `klt lvs` refused every request before comparing, so item 4
  of T1 is unmet for both partitions (details and verbatim messages in `evidence/item4-attempts.json`):
  1. Drawn TX/RX cells: the committed GDS is at dbu 0.001 um, the `asap7` deck requires 0.00025 um and
     refuses to rescale. A scratch rewrite at 0.00025 um (same geometry, not a committed input) is then
     refused because the PMOS channels are not inside a well: the cells draw no wells, contacts or
     routing (`layout/README.md`).
  2. Routed datapath: a FinFET deck accepts only `reference.form: plain-element` (M cards with `nfin=`).
     The item-1 netlist is gate-level Verilog, which that form cannot take, so there is also no
     power-connectivity verdict for it.
  Nothing was waived or relaxed to get past these.
- Filed: 2AMLogic/klayout-tools#4462 (gate-level-verilog reference on a FinFET deck); this repo #52
  (drawn cells: dbu, wells, routing).

## LVS under klt 0.8.1.dev1073 (appended 2026-11-02, issue #20)

Recorded with `klt 0.8.1.dev1073+gbe5754378ff3`, KLayout 0.30.12. Earlier sections are left as
written. Predictive-model tool results only.

- **Drawn TX/RX cells: `status: match`** for `tx_cell`, `rx_cell`, `tx_clk_cell` and `rx_clk_cell`
  against `design/netlist/*.sp`, engine `klayout`, `power_connectivity: unchecked` (a plain-element
  schematic reference, so the power-connectivity check does not apply). Each report carries two
  `device.finfet_bulk_tied` warnings from the disclosed `options.finfet_bulk` policy (nmos bulk to
  VSS, pmos bulk to VDD). Reports: `evidence/item4-lvs/*_cell.r2.report.json`; `klt lvs --check`
  returns `match` for each. The `.report.json` files from 2026-10-28 are superseded, not edited:
  the cell GDS was redrawn afterwards (`83210e9`) and they no longer re-hash.
- **Routed datapath: no report.** The `gate-level-verilog` refusal is gone (klayout-tools#4462 is
  closed), but `layout/slice_routed.gds` is at dbu 0.001 um and the deck requires 0.00025 um, so
  `klt lvs` refuses before comparing. Recorded in `evidence/item4-slice-attempt.r2.json`. No rescaled
  copy was run and nothing was waived. Fix: emit the slice stream at dbu 0.00025 um, as the cells
  already are (P&R stream writer, outside this issue).
- **Grading:** `klt signoff --manifest` still reports item 4 `unmet` for both partitions
  (analog `stale_evidence` with no detail, although `klt signoff <report>` passes each report;
  digital `unrecognized_envelope`, the attempt record not being a klt envelope). Filed:
  2AMLogic/klayout-tools#4795.

## LVS under klt 0.8.1.dev1084 (appended 2026-11-02, issue #20)

Recorded with `klt 0.8.1.dev1084+g7eebf2d2d867`, KLayout 0.30.12. Earlier sections are left as
written. Predictive-model tool results only.

- **Routed datapath: still no report.** With `layout/slice_routed.gds` now at the deck's dbu, `klt lvs`
  gets past the dbu and `reference.form` refusals but stops reading the reference: the
  `gate-level-verilog` reader does not support the Yosys escaped module name
  `\$paramod\rx_cdc_fifo\W=s32'...1000000` in `design/netlist/slice_asap7.v`. No compare ran. Recorded in
  `evidence/item4-slice-attempt.r3.json` with the request in `evidence/item4-lvs/slice_routed.r3.request.json`.
  The netlist was not edited and nothing was waived. Filed: 2AMLogic/klayout-tools#4810.
- **Request note:** `reference.library` could not resolve pin order from the pinned lambdapdk tree
  (it looks for `spice/` or `cdl/` directories; the tree has `netlist/`), so the request names the CDL
  through `reference.pin_order_files`.
- Item 4 of T1 therefore stays **unmet** for the digital partition. The drawn-cell matches from the
  2026-11-02 section above are unchanged.

## LVS under klt 0.8.1.dev1115 (appended 2026-11-02, issue #20)

Recorded with `klt 0.8.1.dev1115+gb95f23605176` (throwaway `uvx` environment at klayout-tools
`b95f236`; the host `klt` is `dev1094`, predates the fix and still gives the previous refusal).
Earlier sections are left as written. Predictive-model tool results only.

- **Routed datapath: still no report.** The escaped-module-name refusal is gone (klayout-tools#4810
  closed by #4812). The reader now refuses on pin-name case: the synthesized netlist connects
  `RESETN`/`SETN` (Liberty spelling) on `DFFASRHQNx1_ASAP7_75t_R`, while the pin-order CDL declares
  `RESETn`/`SETn`. No compare ran. Recorded in `evidence/item4-slice-attempt.r4.json`, reusing
  `evidence/item4-lvs/slice_routed.r3.request.json`. The netlist was not edited and nothing was
  waived. Filed: 2AMLogic/klayout-tools#4815.
- Item 4 of T1 stays **unmet** for the digital partition. The drawn-cell matches are unchanged.

## LVS under klt 0.9.0 (appended 2026-11-05, issue #20)

Recorded with released `klt 0.9.0` (throwaway `uvx` environment; the host `klt` and the
`.github/klt-version` pin of 0.8.0 were not changed). Earlier sections are left as written.
Predictive-model tool results only.

- **Routed datapath: a compare now runs, and it is a `mismatch`.** The pin-name-case refusal from
  the previous section is gone (klayout-tools#4815 is closed; the reader now case-folds
  `RESETN`/`SETN` and says so as a warning). Report:
  `evidence/item4-lvs/slice_routed.r5.report.json`, record `evidence/item4-slice-attempt.r5.json`,
  request `evidence/item4-lvs/slice_routed.r5.request.json` (identical to r3). Counts: layout 0
  devices against 29356 in the reference, 2775 against 15718 nets, 201 against 266 pins, nothing
  matched; the top circuit `slice`/`SLICE` could not be paired; `net.supply_fragmented` on 84
  library-cell circuits. Why the layout extracts no devices was not investigated and is not
  claimed. The netlist, layout, deck and options were not edited and `power_connectivity` and
  `supply_nets` were not waived (decision 0005).
- **Drawn cells:** not re-run; the `r2` matches stand.
- **Signoff:** `manifests/asap7-ucie-phy.json` now cites the r5 report for `4.digital`. Under the
  0.8.0 pin `klt signoff` grades both item 4 rows `unmet` with reason `invalid_evidence` (the
  analog row was `invalid_evidence` before this change too); whether that is a pin/report-version
  mismatch was not determined. T1 item 4 stays **unmet**.

## klt pin bumped to 0.9.0; item 4 grading (appended 2026-11-05, issue #20)

`.github/klt-version` moves from 0.8.0 to the released 0.9.0, and `manifests/asap7-ucie-phy.signoff.json`
is regenerated with it. Earlier sections are left as written. Predictive-model tool results only.

- **Why the analog row read `stale_evidence` / `invalid_evidence`:** for an `lvs` citation the manifest
  `content_hash` pin is compared with the report's `provenance.input.content_hash` (the layout GDS
  hash), not with the report file's own hash. The four drawn-cell pins held other values. They are now
  set from each `r2` report's recorded input hash, which equals the committed GDS. No report was
  edited and the drawn-cell LVS was not re-run; the `r2` `match` results stand (`klt lvs --check`
  under 0.9.0 reports the layout and reference hashes OK and flags only the klt version as drifted).
- **Signoff under 0.9.0:** T1 item 4 **analog is `met`**; T1 met count 8 -> 9. No other item changed.
- **Item 4 digital stays `unmet` (`check_failed`):** the r5 report is a real `mismatch`, unchanged and
  not waived (decision 0005). Why the layout extracts no devices against the 29356-device reference
  was not investigated here. The digital pin was set to the r5 report's input hash for the same reason
  as above.

## Routed-datapath LVS: cause of "0 layout devices" (r6, appended 2026-11-05, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was edited to force
a match and `power_connectivity` / `supply_nets` were not waived (decision 0005).

- **Cause:** a hierarchy artifact, not missing geometry. `layout/slice_routed.gds` carries
  transistor-level geometry inside the placed standard-cell cells and the deck extracts it: the r5
  report's `device.finfet_bulk_tied` warnings account for 678 devices across 84 library-cell circuits.
  r5 left the layout hierarchical while the reference was flattened, so the top layout circuit `slice`
  holds no direct devices and counted 0 against 29356.
- **r6** (`evidence/item4-lvs/slice_routed.r6.request.json`, report `slice_routed.r6.report.json`,
  record `evidence/item4-slice-attempt.r6.json`; r5 request plus `options.flatten_layout: true`,
  klt 0.9.0, one local run): still `mismatch`. Devices 30714 layout / 29356 reference (43 matched),
  nets 16411 / 15718 (174 matched), pins 201 / 266; `power_connectivity.status` `unchecked`.
- **Remaining blocker:** 286 `device.unmerged_fingers` errors (two parallel layout fingers sum to the
  width of one reference device). The report names `options.combine_devices: true`, which klt 0.9.0
  refuses on the asap7 FinFET deck. Filed as 2AMLogic/klayout-tools#4954. The refused request produced
  no report, so none is committed.
- **Signoff:** `manifests/asap7-ucie-phy.json` now cites the r6 report and record; the regenerated
  `manifests/asap7-ucie-phy.signoff.json` (klt 0.9.0) still grades item 4 digital `unmet`
  (`check_failed`). T1 item 4 stays **unmet**. The drawn-cell `r2` matches stand.

## Routed-datapath LVS under klt 0.9.1 (r7, appended 2026-11-06, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was edited to force
a match and `power_connectivity` / `supply_nets` were not waived (decision 0005).

- **r7** (`evidence/item4-lvs/slice_routed.r7.request.json`, report `slice_routed.r7.report.json`,
  record `evidence/item4-slice-attempt.r7.json`; the r6 request unchanged, klt 0.9.1 via a throwaway
  `uvx` environment, one local run): still `mismatch`, with counts identical to r6 (devices 30714 /
  29356, 43 matched; nets 16411 / 15718, 174 matched; pins 201 / 266). `power_connectivity.status` is
  `unchecked`.
- **Upstream:** klayout-tools#4954 is closed and fixed in 0.9.1: `device.unmerged_fingers` no longer
  names `options.combine_devices` (`suggested_option` is null). The 286 unmerged-finger errors remain,
  and the message now says the groups differ in a net or length. Whether that is the layout or the
  reference was not determined here. No new upstream issue is filed because no tool defect is attributed.
- **Engine note:** klayout resolved to 0.30.13; klt warns this differs from the 0.30.12 it was tested
  against. The count categories matched r6 (0.30.12), so the verdict is not expected to depend on it.
- **Signoff:** `manifests/asap7-ucie-phy.json` now cites the r7 report and record. T1 item 4 digital
  stays **unmet**; the drawn-cell `r2` matches stand.

## Routed-datapath LVS: reading the r7 mismatch categories (appended 2026-11-06, issue #20)

Predictive-model tool results only; analysis of the committed `slice_routed.r7.report.json`, no new run.
Earlier sections are left as written; nothing was waived (decision 0005).

- `category_error_counts`: `device.unmatched` 58851, `net.split` 16154, `net.merged` 15461,
  `device.unmerged_fingers` 286, `hints.rejected` 68. Every `device.unmerged_fingers` entry reports
  summed finger width equal to the reference width (e.g. 2 x pmos_rvt, L 0.02 um, 0.081 um total), so the
  fingers are the right size; klt says the group "differs in a net or length".
- The dominant categories are net-level: 16154 reference nets divided across several layout nets and
  15461 collapsed together. With that much net disagreement, the unmerged fingers are most plausibly a
  downstream effect (fingers whose source/drain nets are split) rather than an independent defect. This is
  an inference from counts, not a traced cause.
- `hints.rejected` (68): `options.anchor_top_level_pins` asserted pairings (e.g. `CLK`) that the
  comparer did not confirm. Layout has 201 pins against 266 in the reference.
- **Next, not done here:** trace one split net (a single standard-cell output) through the routed layout
  to find the missing connection, and try one run with `options.anchor_top_level_pins: false`. Either
  would be a new numbered attempt. T1 item 4 digital stays **unmet**.

## Routed-datapath LVS with top-level pin anchoring off (r8, appended 2026-11-06, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was edited to force
a match and `power_connectivity` / `supply_nets` were not waived (decision 0005).

- **r8** (`evidence/item4-lvs/slice_routed.r8.request.json`, report `slice_routed.r8.report.json`,
  record `evidence/item4-slice-attempt.r8.json`; the r7 request plus `options.anchor_top_level_pins:
  false`, klt 0.9.1 via a throwaway `uvx` environment, one local run): still `mismatch`. Devices 30714
  layout / 29356 reference (38 matched, r7 43), nets 16411 / 15718 (160 matched, r7 174), pins 201 /
  266. `power_connectivity.status` is `unchecked`.
- **Result:** the option the r7 analysis proposed does not reduce the net-level disagreement
  (`net.split` 16244, `net.merged` 15551, both slightly above r7); anchoring was helping, not causing
  it. `hints.rejected` no longer appears, as no pin hints are applied. The 286 `device.unmerged_fingers`
  and 84 `net.supply_fragmented` are unchanged. The cause remains undetermined; the remaining step is
  tracing one split net by hand.
- **Signoff:** `manifests/asap7-ucie-phy.json` cites the r8 report and record. T1 item 4 digital stays
  **unmet**; the drawn-cell `r2` matches stand.

## Routed-datapath LVS: single library cell probe (r9, appended 2026-11-06, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was waived or edited
to force a match (decision 0005). This is a diagnostic probe, not a new attempt on the `slice` partition.

- **Probe** (`evidence/item4-lvs/and2x2_probe.r9.request.json`, report `and2x2_probe.r9.report.json`):
  the library `AND2x2_ASAP7_75t_R` layout from `asap7sc7p5t_28_R.gds.gz` against the same cell's
  subcircuit in `asap7sc7p5t_28_R.cdl` (lambdapdk 0.2.17, as in r5-r8), `finfet_bulk` as in r8, one local
  run. klt `0.9.2.dev103+g9f4cec35997a` (the host-installed tool, used read-only; r7/r8 used 0.9.1).
- **Result:** `match`. Devices 6 / 6, nets 7 / 7, pins 5 / 5, all matched. The one `net.supply_fragmented`
  (VDD in two layout nets inside the cell) is a warning and the cell still matches.
- **Reading:** the 84 `net.supply_fragmented` warnings in r7/r8 do not by themselves indicate broken
  cell-internal extraction, so the 16244 `net.split` / 15551 `net.merged` errors are not explained by
  the library cells extracting wrongly in isolation. This rules out one hypothesis; the cause is still
  undetermined and is more likely at the routed-block level (placement/routing connectivity or the flatten
  step). Tracing one split net through the routed layout remains the next step.
- **Reproducibility:** the probe inputs (library GDS/CDL) are not committed; the report records their
  hashes. The request paths are those of the scratch run. T1 item 4 digital stays **unmet**.

## Routed-datapath LVS: the routed stream is not the committed netlist (appended 2026-11-06, issue #20)

Predictive-model tool results only; analysis of committed files plus one throwaway cell census, no new
`klt lvs` run. Earlier sections are left as written; nothing was waived (decision 0005).

- **Method:** count standard-cell instances (with hierarchy multiplicity, `$VARn` variants folded) in
  `layout/slice_routed.gds` with the `klayout` Python module from a throwaway `uvx --with klayout`
  environment, and the same count over `design/netlist/slice_asap7.v` expanded through its modules.
  Compare the layout against `design/netlist/slice_asap7.v` as committed at each of its five revisions
  (`git log -- design/netlist/slice_asap7.v`), summing absolute per-cell count differences and leaving
  out `FILLER*`/`TAPCELL*`, which the netlist cannot contain.
- **Result:** the routed layout holds 2588 logic cells. Summed absolute per-cell difference against the
  netlist revision of each commit: `6f8f329` (2026-11-04, the current reference) 2211; `54b68cb`
  (2026-11-01) **293**; `c185347` (2026-10-31) 1768; `6703c31` (2026-10-27) 1967; `a807a50`
  (2026-10-29) 2639. The layout was routed from the 2026-11-01 synthesis. Against the current
  reference whole cell types differ by hundreds (e.g. `NAND5xp2` 448 in the layout against 1,
  `NOR3xp33` 2 against 450, `AOI21x1` 0 against 287).
- **Reading:** the r5-r8 net-level disagreement (`net.split` / `net.merged` in the tens of thousands) is
  what an LVS of a layout against a different synthesis result looks like; no tool defect is attributed.
  The residual 293 against the 2026-11-01 netlist is consistent with the clock-tree buffers
  (`BUFx4`, 17 in the layout against 0) and the sizing changes place-and-route adds. The layout/netlist
  pairing was not otherwise verified.
- **Consequence (tracked in #109):** a `match` for the digital half needs `layout/slice_routed.gds` re-routed from the
  current netlist (`python3 -I layout/pnr/regen.py`, about 10 minutes through the `openroad` wrapper), then
  an LVS run against a reference that is the netlist the layout implements. That re-route is layout work
  outside this issue and was not done here; no LVS was run against the 2026-11-01 netlist, since it is
  not the item-1 reference. T1 item 4 digital stays **unmet**; the drawn-cell `r2` matches stand.

## Routed datapath re-routed from the current netlist (appended 2026-11-06, issue #109)

Predictive-model tool results only; no `klt lvs` run here (that is #20). Earlier sections are left as written.

- **Run:** `python3 -I layout/pnr/regen.py` once, sequentially, on the committed `design/netlist/slice_asap7.v`
  (`6f8f329`), the pinned lambdapdk archive, OpenROAD 26Q3-1510. `regen.py --check` then exited 0.
  `layout/slice_routed.gds` is now sha256 `eae888dccce1e26e0416d3af0e2332127a9b1d39a172df7df95e32a466a96b13`
  (was `b264dd56...`); `layout/pnr/slice.pnr.report.json` regenerated.
- **Result:** stage reached `route`, `route_drc_violation_count` 0, `antenna_violation_count` 0, same as before;
  power delivery still `partial` (#66). Clock skew 0.00771 ns (was 0.00718).
- **Census** (same method as the section above, throwaway `uvx --with klayout`, `$VARn` folded, `FILLER*`/
  `TAPCELL*` left out): layout 2594 logic cells, netlist 2743, summed absolute per-cell difference **221**
  against 2211 for the previous stream (the old stream re-counted with this script gives 2211 again). Largest
  remaining differences: `BUFx2` 0 vs 83, `HB1xp67` 0 vs 68, `BUFx6f` 0 vs 28, `BUFx4` 17 vs 0, `CKINVDCx10` 6 vs 0:
  buffer sizing and clock-tree cells from place-and-route, plus the `TIEHI`/`TIELO` rewrite `regen.py` applies to
  a scratch copy (README, "Tie cells"). Nothing was waived.
- **Still open:** the LVS against this stream (#20) is not run. `layout/lane_column.gds` embeds the routed slice
  and no longer matches `assemble_column.py --check`; `attest/item2.r6.json` and `evidence/item4-lvs/` still
  pin the previous stream and are append-only, so they stay as the record of runs on it.

## Routed-datapath LVS on the re-routed stream (r10, r11, appended 2026-11-06, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was edited to force
a match and `power_connectivity` / `supply_nets` were not waived (decision 0005).

- **Inputs:** `layout/slice_routed.gds` sha256 `eae888dc...` (re-routed from the current netlist, #109) against
  `design/netlist/slice_asap7.v` sha256 `4d1baf35...`, `reference.form: gate-level-verilog`, lambdapdk 0.2.17 as in r5-r8.
- **Runs:** klt 0.9.1 (the repo pin) via a throwaway `uvx` environment, two single local runs of about 4 min.
  **r10** (`evidence/item4-lvs/slice_routed.r10.request.json`) is the r8 request (`anchor_top_level_pins: false`);
  **r11** is the r7 request (default anchoring). Record: `evidence/item4-slice-attempt.r10.json`.
- **Result:** both `mismatch`, with identical counts. Devices 29436 layout / 29356 reference (37 matched; the totals
  were 30714 / 29356 on the previous stream), nets 15803 / 15718 (34 matched), pins 2 / 266.
  `net.split` 15761, `net.merged` 15676, `device.unmatched` 56563, `device.unmerged_fingers` 620,
  `net.supply_fragmented` 84. `power_connectivity.status` is `unchecked`.
- **Reading:** re-routing closed the cell-census gap (#109) and brought the device totals within 80, but the net-level
  disagreement did not shrink. The layout extracts only 2 top-level pins against 266 in the reference, so the compare
  has almost no anchor for the net correspondence; no tool defect is attributed and the cause is undetermined.
- **Signoff:** the manifest cites the r10 report and record. T1 item 4 digital stays **unmet**; the drawn-cell `r2`
  matches stand. The analog half is unchanged.

## Item-1 signoff convention: reuse the inventory, revision only the evidence (appended 2026-11-14, issue #145)

Documentation-only convention; no tool run in this section. The item-1 signoff
**inventory is an input, not a measurement**: it holds a source list, a description
and the `--check` argv — no hash, no tool version, no timestamp and no result. The
measurement lives in the evidence output, which re-hashes the inventoried files and
therefore genuinely differs per revision.

**Convention:** for T1 signoff attestations, revision the evidence output, not the
inventory, unless the inventory's own content changes. Mint a further
`attest/item1.rN.json` only when the `sources` list or the declared `derived` checks
actually change; otherwise pass the unchanged inventory to
`klt signoff --attest 1 --inventory` and revision only the `-o`/`--check` evidence
record. Items 9 (`manifests/attest/item9.json` against `manifests/evidence/item9.json`
and `item9.r2.json`) and 10 (`manifests/t1-item10-inventory.json`, re-used across
revisions per `README.md`, "T1 evidence") already follow this; item 1 historically
did not — `attest/item1.r2.json` through `attest/item1.r7.json` are byte-identical
except for the r2 `sources` edit.

**Inventory of record:** `attest/item1.r7.json` is the item-1 inventory going
forward — `.github/workflows/signoff.yml` and the block manifest already cite it,
so nothing moves today. The existing r2-r7 copies stay as committed history: each
is pinned by content hash inside its append-only evidence record and is not edited
or deleted.

## Why the routed slice extracted 2 top-level pins, and the layer-map fix (r12, appended 2026-11-14, issue #149)

Predictive-model tool results only. Earlier sections are left as written; nothing was waived and the
reference netlist was not edited (decision 0005). Every number below was measured under the pinned klt
`0.9.1` (`.github/klt-version`) in a throwaway `uvx` environment, never the host's `0.9.2.dev`.

**The cause was not missing labels.** On the stream r10/r11 ran against
(`layout/slice_routed.gds` sha256 `eae888dc...`), top cell `slice`, `dbu` 0.00025:

| layer/datatype | deck role | top-cell texts | top-cell polygons |
|---|---|---|---|
| `40/251` | `M4.pin` | **266** | **266** |
| `20/251` | `M2.pin` | 2 (`VDD`, `VSS`) | 162 |
| `40/0` | `M4.drawing` | 0 | 3991 (flattened) |

All 266 reference top-level ports carried a label, each co-located with its own DEF `PINS`
rectangle at the east/west die edge. `30/251` and `50/251` were absent. (`20/251` carries 360
texts when counted recursively; 358 of those are standard-cell-internal M2 pin labels, not
top-level ports.)

**What `klt lvs`'s `asap7` deck reads as a top-level pin.** Read from the pinned deck source, not
inferred — `klayout_tools/decks/asap7.py` and `klayout_tools/extract_finfet.py`:

- the label layers are `metal_labels=tuple((layer, 251) for layer, _ in _METALS)`, paired
  **positionally** with the conductors `_METALS = ((19,0),(20,0),(30,0),(40,0),(50,0),(60,0),(70,0),(80,0),(90,0))`
  — so `M1=19`, `M2=20`, `M3=30`, **`M4=40`**, `M5=50` (`40/251` is `M4.pin`, not M3's);
- connectivity is built per pair by `l2n.connect(conductor, layers.texts(label_ld, name))` in
  `_connect_beol`, where `layers.texts` is `make_text_layer` — it takes the **texts** from
  `(metal, 251)` and nothing else.

Two consequences: the 266 pin **polygons** on `40/251` are read by nothing in the deck (its
conductors are `(metal, 0)` only), and a `40/251` text names a net only where a `40/0` shape
coincides with the text's own point.

**The two pins the extraction found were `VDD` and `VSS`** — the only labels whose text point lay on
conducting metal of their own declared layer (`M2.pin` text over `M2.drawing`, where the `M1`/`M2`
followpin rails run).

**Why no M4 port label coincided with M4, precisely.** Each DEF `PINS` rectangle is 336 x 96 dbu
(0.084 x 0.024 um, i.e. M4 minimum width tall) and KLayout draws the pin's name label at its
**centre**. Every one of the 266 rectangles *is* overlapped by `M4.drawing` — the router did reach
them — but only at one end: for `tx_a[21]`, rect x 95004–95340 dbu against M4 x 95004–95088. The
centre text point therefore sits on bare pin-purpose geometry, 72 dbu (66 labels) or 84 dbu (200
labels) clear of the nearest `40/0` edge. Probing each of the 268 labels declared by
`layout/pnr/slice.pnr.report.json` (266 on M4, 2 on M2) against a 1 dbu box at its text point:

| declared | metal present at the label's text point | count |
|---|---|---|
| M4 | M3 only | 170 |
| M4 | **nothing** | 93 |
| M4 | M2+M3 | 2 |
| M4 | M3+M6 | 1 |
| M2 | M1+M2 → extracted | 2 |

Predicted extractable top-level pins **2**; r10/r11 reported **2**.

**Not a stream regression to revert.** The previous stream (`53e4dc7`, sha256 `b264dd56...`) had an
identical label structure and reported 201 pins only because its router metal happened to cover the
rectangle centres; 65 of its 266 ports had no pin even then. `klt place-and-route` writes the DEF
`PINS` rectangle and its name label to the layer map's **pin** purpose (`M4 PIN 40 251`, `NAME
M4/PIN 40 251` in the pinned lambdapdk `base/apr/asap7.layermap`), which the same tool's ASAP7
extraction deck consumes as a label layer only. The two klt verbs disagree about what a top-level
pin is, so a klt-produced routed GDS has no reliably extractable top-level pin at all. **Filed
generically upstream as 2AMLogic/klayout-tools#5700** (tool gap only, no design detail).

**The fix, and what it did not fix.** `layout/pnr/regen.py` now stages the pinned layer map through
`pin_geometry_on_drawing()`, which adds a `PIN` entry on the metal's own drawing layer/datatype for
every LEF layer declaring both a `NET` and a `PIN` purpose (M1–M9; the via layers declare no `NET`,
so they are untouched). The pin rectangle becomes real routing metal under its own label — what a
top-level pin physically is — and the pin-purpose entry stays, so the change only adds geometry. The
KLayout map-file semantics behind it were confirmed on a minimal LEF/DEF fixture: `<M> PIN <l> 251`
alone puts rectangle and label on `251`; adding `<M> PIN <l> 0` puts the rectangle on both while
`NAME <M>/PIN <l> 251` keeps the label on the deck's label layer. Self-test: `python3 -I
layout/pnr/test_layermap.py`.

- **Stream:** `python3 -I layout/pnr/regen.py` (pinned klt 0.9.1, OpenROAD 26Q3-1510, one run),
  `layout/slice_routed.gds` now sha256 `27dbfd1d...`; `regen.py --check` exits 0 (byte-for-byte) and
  `--check-input` exits 0. `40/0` 3991 → 4257 flattened polygons (+266), `20/0` 40859 → 41021
  (+162); `40/251` unchanged. Placement and routing did not change: stage `route`,
  `route_drc_violation_count` 0, `antenna_violation_count` 0, clock skew 0.00771 ns, power delivery
  still `partial` (#66) — all identical to the previous report. All 268 top-level labels now lie on
  their own declared metal. `layout/lane_column.gds` was re-assembled (`--check` exits 0) and item 2
  re-attested as `attest/item2.r8.json` / `evidence/item2.r8.json`.
- **r12** (`evidence/item4-lvs/slice_routed.r12.request.json`, report `slice_routed.r12.report.json`,
  record `evidence/item4-slice-attempt.r12.json`): the r11 request verbatim apart from the scratch
  PDK paths, so the stream is the only variable. Verdict **`mismatch`**, exit 3 — the grade is
  unchanged. Pins **268** layout / 266 reference (r10/r11: 2 / 266) and 266 pin names anchored by
  name before comparing (`topology.top_level_pins_anchored`; r10/r11 anchored none). With an anchor
  the compare pairs far more: nets matched **352** (was 34), devices matched **199** (was 37). The
  residual net-level disagreement barely moved and still dominates: `net.split` 15331 (was 15761),
  `net.merged` 15246 (was 15676), `device.unmatched` 56195 (was 56563), `device.unmerged_fingers`
  621, `net.supply_fragmented` 84. `hints.rejected` returns at 68 because there are now pin hints to
  reject. `power_connectivity.status` is `unchecked` for the same reason r10/r11 record (the
  `gate-level-verilog` reference form puts supply connectivity in the ordinary compare) — not a
  waiver; `supply_nets` is untouched.
- **Reading:** the pin-extraction defect diagnosed above is fixed and measured, and it was not the
  cause of the net-level disagreement — removing it moved `net.split`/`net.merged` by under 3%. The
  residual ~15k split/merged nets remain **undetermined** and are now the only thing between this
  stream and a `match`; tracing one split net by hand is still the next step. No tool defect is
  attributed to that residue.
- **Signoff:** the manifest cites the r12 report and record, and `evidence/item2.r8.json` for item 2.
  T1 item 4 digital stays **unmet** and #20 stays open; the drawn-cell `r2` matches stand. The
  analog half is unchanged.

## The reference-netlist variable is closed; the r5–r13 residue remains undetermined (r13, appended 2026-11-14; tracing reworked after review, 2026-11-15, issue #20)

Predictive-model tool results only. Earlier sections are left as written; nothing was waived and no
netlist, deck or option was edited (decision 0005). Every number below was measured under the pinned
klt `0.9.1` (`.github/klt-version`) in a throwaway `uvx` environment.

- **r13** (`evidence/item4-lvs/slice_routed.r13.request.json`, report
  `slice_routed.r13.report.json`, record `evidence/item4-slice-attempt.r13.json`): the r12 request
  verbatim apart from the reference, which is now `layout/slice_routed.v` — the post-route netlist
  the committed stream was routed from, committed by the same flow. This closes the hypothesis the
  #109 analysis left open ("an LVS run against a reference that is the netlist the layout
  implements"). Verdict **`mismatch`**, exit 3. Nets matched 408 (r12, against the synthesis
  reference: 352), `net.split` 15269 (was 15331), `net.merged` 14967 (was 15246),
  `device.unmatched` 55444 (was 56195), pins 268/266 as in r12. The reference converts fine (15501
  nets / 28862 devices — post-route totals, against the synthesis reference's 15718 / 29356), so
  the reference is not the problem.
- **Reading:** the layout was placed and routed from this exact netlist, so a correct extraction of
  the stream must match it; it does not. The different-netlist hypothesis is refuted and the
  reference-netlist choice is eliminated as a variable.
- **Trace (reworked after review).** The first version of this section published a "determined
  cause" whose measurements did not survive review reproduction; the corrected trace commits every
  script and intermediate artifact it cites. Cell-internal extraction is correct — the r9
  single-cell probe stands, a two-instance abutment probe (two `BUFx4` at exact abutment, one
  further local `klt lvs` run) leaves the cells' internal `AN` nets separate, and `klt extract`
  reproduces every library cell's CDL topology hierarchically. At the top level the extract is
  chain-structured and close to the reference, not fragmented: the committed extract netlist
  (`evidence/item4-lvs/slice_routed.r13.extract.v`) and the committed counter
  (`slice_routed.r13.refnets.py`, output `.refnets.json`; counting domain stated in its docstring)
  give 2594 X instances, 199 one-cell-pin nets (all top-level port bits) against the reference's
  198 (likewise all port bits), 1801 two-cell-pin nets against the reference's 1801, and `rx_clk`
  at 528 cell pins against the reference's 528. The figures first published here (855 one-pin
  extract nets, `rx_clk` 179, 6/1649 reference figures) were not reproducible and are withdrawn.
- **No determined cause.** The die-spanning "one connected web" first published here was an
  artifact of the measurement: the scratch fill joined the M2–M6 metal layers wherever they
  overlap — a plain 2D union — and never consulted the via layers. The committed script
  (`slice_routed.r13.trace_geometry.py`, output `.trace_geometry.json`; `klayout`
  `LayoutToNetlist`, flattened, top circuit `slice`) measures both connectivities: metals-union
  reproduces the artifact (233 components, largest holding 99.397% of the stack's routing area at
  bbox (0,4696)–(95340,176744) dbu; merged M2 14361 and M3 7850 as first published), while
  via-aware connectivity (M2–V2–M3–V3–M4–V4–M5–V5–M6) yields 5485 components with the largest at
  2.95% of routing area, bbox (29428,4696)–(95340,176744) dbu — strap-scale, not die-spanning; the
  review's independent via-aware measurement (3949 components, largest 2.99%) agrees
  qualitatively. A sanity assertion is recorded in the script: the via layers change the component
  count, so the via-aware fill is via-mediated — and the published count surviving removal of the
  via layers is what proved the original fill never consulted them. The "sub-minimum-width M2"
  claim is also withdrawn: all 14361 merged M2 polygons on the stream have minimum dimension
  exactly 72 dbu = 0.018 um, the ASAP7 M2 drawn width at 1x. What remains is the r5–r13
  `net.split`/`net.merged` residue with no
  measured cause; the next step is a per-net diff of the extracted circuit against the reference,
  or attribution inside the place-and-route flow.
- **Not attributed further here.** No stream defect is asserted, so nothing is attributed to
  `regen.py`'s DEF or its DEF→GDS merge; `regen.py` re-runs the flow when a hypothesis exists.
  Stream fix and the r14 against a changed stream are **#169**, whose "one via-mediated web /
  global short" premise is withdrawn by this rework. The DRC record of record (#155) binds the
  previous stream `eae888dc...` and is stale for this one; item 3 is outside this issue.
- **Signoff:** the manifest cites the r13 report (r12's files stay, append-only). T1 item 4
  digital stays **unmet** and #20 stays open, parked on #169; the drawn-cell `r2` matches stand.
  The analog half is unchanged.

## The r5–r13 residue attributed: the routed circuits correspond exactly; the residue is the layout's supply/well domain (analysis of the committed r13 artifacts, no new run, appended 2026-11-15, issue #169)

Predictive-model tool results only. Earlier sections are left as written; nothing was waived and no
netlist, deck or option was edited (decision 0005). No new `klt` run was made: this section is
analysis of artifacts already committed (`slice_routed.r13.extract.v`, `slice_routed.r13.report.json`,
`layout/slice_routed.v`, `slice_routed.r13.refnets.json`), so it keeps the `slice_routed.r13.`
prefix per the repo's revision convention. Every figure below is reproduced by the committed script
and its committed output; a second run is byte-identical.

- **What ran.** `evidence/item4-lvs/slice_routed.r13.netdiff.py` (output `.netdiff.json`), a per-net
  diff extending the committed `…r13.refnets.py` parsers: both netlists are parsed into instances
  with named port connections (the extract's positional X-card nodes resolved through each leaf
  variant's own `.SUBCKT` header, `$N` names namespaced per subcircuit, cell variants folded to
  their base cell, pin names folded to lower case exactly as the report's
  `reference.gate_level_pin_case_folded` entries do). The diff runs on the top circuit of each
  side — module `slice` against the `.SUBCKT` with the most X-cards — and pairs instances by
  anchored propagation: net correspondences are seeded only where both sides use the same display
  name *and* the name's full membership profile agrees (202 such seeds, zero profile mismatches,
  zero ambiguities), then an instance pairs only when exactly one same-cell candidate agrees on
  every port whose reference net is already mapped, each pairing contributing new net
  correspondences, to a fixpoint. Display names are never themselves evidence of identity; every
  seed is membership-verified and everything the seeds cannot reach is reported as unpaired rather
  than forced. Ports neither side shares (the extract-only `VDD`, `VSS`, `VDD$1`, `vsubs`) are
  excluded from the pairing graph and characterised separately. The script hard-fails if any of 18
  committed baseline figures cannot be recovered (the r13 category counts, the report's `\$0`
  statistics, both tops at 2594 instances, `rx_clk` at 528 cell pins both sides, equal per-cell
  edge counts, the committed `refnets.json` baselines), so a silent parse regression fails instead
  of reporting zeros.
- **The routed circuits correspond exactly.** The propagation pairs **2594 of 2594** instances
  (100% coverage, 9 rounds) and all **2713** pairing-domain nets correspond **1:1** — zero splits,
  zero merges, zero partial nets, zero unmatched nets on either side; the net map at fixpoint is a
  bijection over 2713 names. The domains reconcile exactly: the reference's 2940 nets are the 2713
  connected nets plus the 227 zero-cell-pin nets `refnets.json` already counted (64 of them port
  bits), and the extract's 2955 distinct top-level node tokens are the same 2713 plus 242
  layout-only nets (below). The pairing-domain edge counts are equal per cell (9263 on each side).
  Every top-level port bit the reference actually connects (202 of 266; the other 64 — the
  `rx_a`/`rx_b` bits — connect to no cell pin on either side) pairs 1:1 with an extract net of the
  same case-folded name, so r13's 67 `hints.rejected` "unconfirmed" pin anchors are artifacts of
  the comparer's failed matching, not boundary topology disagreements. The r13 `topology.flattened`
  note "93 circuit(s) were collapsed into 9 top-level circuit(s)" is also explained: the 9 are
  `slice` plus the 8 unused empty `TAPCELL`/`FILLER` leaf variants (measured: exactly those 8 are
  never instantiated), which remain roots after flattening; the reference side's "50 → 1" is clean.
- **The layout-only domain is the supply/well netlist.** The 242 extract-only nets are 239
  anonymous fragments plus the three named nets `VDD`/`VSS`/`vsubs`: 157 fragments touch only the
  `VDD`/`VDD$1` positions (5160 terminals, largest 54), one more on `VDD`-only (10) and one on
  `VDD$1`-only (10); 80 fragments touch only the `VSS` position and hold **2593 of the 2594** `VSS`
  terminals — the net actually named `VSS` holds **1**; `vsubs` is a single net carrying all 2594
  nmos bulk terminals. The leaf bulk census (from the extract's own M-cards, weighted by instance
  counts) gives 1494 instances whose leaf bodies put the pmos bulk on the `VDD` port and 1100 on
  `VDD$1`, and names no cell with a bulk anywhere else; 10584 flat PMOS bodies land on a
  non-supply leaf net by this census. The reference side has no counterpart for any of this:
  module `slice` connects no `VDD`/`VSS`/well pins at all, and the reference conversion
  synthesises bulk connectivity from the library CDL under `options.finfet_bulk` — the report's
  own `device.finfet_bulk_tied` entries (168, 692 devices at circuit level) describe exactly that
  caller assertion, joining named bulk nets (`vsubs` onto `VSS`, `VDD` onto `VDD`) before
  comparing.
- **The r13 report corroborates the mechanism.** `device.body_unverified` (1 entry) says 14363
  PMOS device body terminals "were compared against an anonymous, KLayout-synthesized well net,
  not a real schematic net -- either no drawn or derived well-tap geometry exists, or the
  tap-connected net carries no name label (a body resolves only to a *named* net; label the
  tap-connected conductor, e.g. VDD, to resolve it)". That is consistent with the census above:
  the named `VDD`/`VSS` nets hold 8 and 1 terminals respectively, so nearly every flat PMOS body
  sits on an anonymous fragment — the leaf census puts the flat PMOS device count at 14431
  (`flat_pmos_body_count_from_extract`: 3847 with leaf bulk on the `VDD` port plus 10584 on
  `VDD$1`, its `flat_pmos_bodies_by_leaf_bulk_net` breakdown); the residual against the report's
  14363 is device bookkeeping this analysis cannot decompose from the committed report.
  `net.supply_fragmented` fired 84 times, every entry naming `VDD`. With the layout's supply/well
  terminals spread over ~240 nets where the reference asserts two named supplies, device matching
  — which pairs devices by terminal-net correspondence — collapses wholesale: 55444
  `device.unmatched` entries against 233 matched devices, and net correspondence inherits the
  collapse: 408 matched nets (199 pin-anchored entries whose layout name equals the reference
  name case-folded, plus 209 entries whose layout display name is anonymous — 182 of them the
  `\$0` collapse), 15269 `net.split` entries, 14967 `net.merged` entries — i.e. essentially
  every net on both sides is accused, on circuits whose routed connectivity this section measures
  as identical.
- **The `\$0` headline shape is a reporting artifact.** The `net.split` entries carry, on every
  entry, only `category`/`description`/`severity`/`side` and the display name: `net.reference` is
  null, `circuit`/`subcircuit`/`details` are null, and there is no id or pin-set field. 12812 of
  the 15269 entries (84%) name the layout net as the single string `\$0`; the remaining 2457
  entries have 2457 distinct names, each appearing exactly once. `\$0` is therefore the rendering
  of many distinct anonymous layout nets, not one giant net — the same artifact class as the
  metals-union claim r13 withdrew. The report alone cannot answer "how many distinct layout nets
  does the split list accuse": that identity had to be re-derived from the netlists by pin
  membership (this section). Filed generically at `2AMLogic/klayout-tools#5833` (no design
  detail); #3920 is the adjacent, already-addressed finding about the missing
  `net.supply_fragmented` signal itself.
- **Attribution.** Of the residue's four candidate homes: **(d) the reference** is eliminated
  (r13 — the layout was routed from this exact netlist and mismatches identically). **(a)
  extraction, at the routed-signal level this diff measures, is eliminated** — the committed
  extract reproduces the committed reference's routed connectivity exactly, net for net and
  instance for instance. **(c) the stream** is eliminated for the routed signal structure (r13's
  via-aware geometry trace plus the 1:1 netlist correspondence above), and **remains open for the
  supply/well domain only**: whether the ~240 supply/well fragments are real PDN geometry (rails
  and straps genuinely disjoint, tap conductors unlabelled — a `regen.py` DEF/PDN question, the
  fallback this issue named) or an extractor connect-chain/label handling gap is not decidable
  from the committed artifacts, because r13's geometry trace covered the M2–M6 signal routing
  only and `device.body_unverified`'s own text says the tool cannot distinguish absent tap
  geometry from an unlabelled conductor. **(b) the comparison/reporting layer** is where the
  residue manifests: the flat comparer's device matching collapses on the fragmented
  supply/well terminals and drags net correspondence with it, and the report then renders its own
  list unusable for attribution (`\$0` collapse, no stable identity — `2AMLogic/klayout-tools#5833`).
  The determined statement: **the r5–r13 `net.split`/`net.merged` residue is the layout
  extraction's supply/well domain — ~240 layout-only fragment nets where the reference asserts
  two named supplies — cascading through the flat comparer's device/net matching; the routed
  signal circuits themselves correspond exactly and no stream signal defect exists.** The next
  step for an item-4 `match` is one of: label/tie the tap-connected conductors and supply rails
  in the stream flow (stream fix, then an r14 — the fallback this issue named), or a klt-side
  change that lets the comparison bridge the anonymous well/supply fragments (tool side, to be
  discussed upstream under #5833's tracker).
- **Not done here.** No stream was regenerated, no new `klt lvs` run was made (there is no
  `r14`), the item-3 DRC record gap stays **#19**'s, and `evidence/item4-attempts.json` and the
  block manifest are untouched — an analysis-only landing. `python3 -I
  layout/pnr/regen.py --check-input` still exits 0 and the committed stream hash is unchanged.
- **Signoff:** the manifest still cites the r13 report (append-only). T1 item 4 digital stays
  **unmet** — nothing has matched; what changed is that the residue now has a measured cause and
  a named next step. #20 is parked on this issue; its park should be revisited when this lands:
  the attribution is in, the fix (stream-side or tool-side) is not. `spec/asap7-bringup.md` is a
  T1 item-10 hygiene inventory member, so the envelope (`manifests/t1-item10.envelope.json`) is
  regenerated and committed in the same commit as this edit (command in `README.md` § T1
  evidence); only the envelope changes.

## Correction: the item-1 r2–r7 chain is six byte-identical files (appended 2026-11-15, issue #178)

Documentation-only convention; no tool run in this section. The section appended
2026-11-14 (issue #145) closes with "`attest/item1.r2.json` through
`attest/item1.r7.json` are byte-identical except for the r2 `sources` edit",
which reads as carving `attest/item1.r2.json` out of the identical set. It does
not: `attest/item1.r2.json` through `attest/item1.r7.json` are **six
byte-identical files**, `r2` included (sha256 `78f71a7e...`, all six). The only
real edit in the chain is `attest/item1.json` -> `attest/item1.r2.json` — one
line, adding `design/lambdapdk.py` to `sources` — a step relative to a file that
sentence does not name. The convention that section records is unaffected and
stands: the inventory is an input, not a measurement; revision only the evidence
output; `attest/item1.r7.json` is the inventory of record. Earlier sections are
left as written.

## Item-1 inventory of record is now `attest/item1.r9.json` (appended 2026-11-15, issue #182)

Documentation-only pointer; the tool runs behind it are recorded in
`evidence/item1.r9.json`. The section appended 2026-11-14 (issue #145) names
`attest/item1.r7.json` as the inventory of record; that was superseded by
`attest/item1.r8.json` when #179 added the extracted OSDI netlist as a `derived`
member, and is superseded again now: `attest/item1.r9.json` adds
`design/sim/regen.py` — the script that backs the r8 inventory's newest
freshness check — to `sources`, so every generator of an inventoried `derived`
member is itself bound by a content hash. Per the #145 convention this is
exactly the case that mints a further revision (the `sources` list changed);
`.github/workflows/signoff.yml` and the block manifest cite r9, and the
committed evidence (`evidence/item1.r9.json`, 21/21 checks) is the record.
Earlier sections are left as written.

## The #178 tail section's r7 clause is likewise superseded (appended 2026-11-20, issue #202)

Documentation-only pointer; no tool run in this section. The correction
appended 2026-11-15 (issue #178) closes with "`attest/item1.r7.json` is the
inventory of record"; that clause is superseded by `attest/item1.r9.json`
(issue #182), exactly as the #145 section's clause was: the item-1 inventory
of record is `attest/item1.r9.json`, as enforced by
`.github/workflows/signoff.yml` and the block manifest. The substantive
finding of #178 — `attest/item1.r2.json` through `attest/item1.r7.json` are
six byte-identical files — is a statement about the attestation chain, not
about which revision is of record, and is unaffected. Earlier sections are
left as written.

## The r17 residue attributed after the grid restore: r18 on-pin, the fragment census, and the failing r19 of record (appended 2026-11-22, issue #273)

Predictive-model tool results only. Earlier sections are left as written; nothing was waived, no
netlist, deck or option was edited to force a match (decision 0005), and the routed stream is
byte-unchanged (`layout/pnr/regen.py --check-input` still exits 0), so the r8 re-attest chain (items
1, 2, 8, the column DRC re-take) is not triggered by this section.

- **r18, the on-pin re-take** (`evidence/item4-lvs/slice_routed.r18.{request,report}.json`, plus its
  `klt extract` output `slice_routed.r18.extract.v` — byte-reproduced from the committed stream the
  day this section was written): klt 0.9.2 via the pinned spec, klayout **0.30.12** on the pin, so
  `provenance.klayout_version_mismatch: false`; every other option identical to r17's
  (`flatten_layout`, `finfet_bulk` nmos `VSS` / pmos `VDD`). Result: **7,581 mismatches, the same
  counts as r17 in every category** — the off-pin klayout was record hygiene here, as the r16
  comparison already suggested. r17 stays as history.
- **The census** (`evidence/item4-lvs/slice_routed.r18.netdiff.py` + its committed output, pure
  `python3 -I`, parsers imported from the r13 script; and `slice_routed.r18.welldom.py` + output, the
  klayout geometry half; the netdiff self-test is wired into the item-10 inventory as
  `netdiff-r18-census-self-test`, and both scripts hard-fail on 34 resp. 9 committed figures). The
  routed signal circuits still correspond exactly: 2,591 of 2,591 instances pair by anchored
  propagation and all 2,710 pairing-domain nets match 1:1 — zero splits, merges or partials. The
  supply/well domain, re-measured: the extract's named `VDD` net holds **every** PMOS source/drain
  supply terminal (998 leaf `vdd` ports + 1,593 leaf `vdd$1` ports of 2,591 instances), `VSS` holds
  all 2,591 `vss` terminals and `vsubs` all 2,591 nmos bulk terminals, while **80 anonymous `$I`
  nets hold every PMOS-body (well) terminal** — per instance, the leaf port carrying the PMOS bulk is
  on an anonymous island and the port carrying PMOS supply source/drain terminals is on the named
  `VDD`, 2,591 of 2,591, no exception. (The leaf-internal census shows the bulk port is *named*
  `VDD` in 53 leaf variants and `VDD$1` in 26 — two in-leaf naming orders of the same physical
  split, so the census classifies by M-card role, not port name.) The DEF join places every island's
  instances in exactly one row pair — an N row and the FS row above it share one n-well strip — and
  the 80 islands map to 80 distinct pairs; `welldom.py`'s via-aware geometry census agrees: **161
  top-level M1 followpin rails, all 80 VDD-pitch rails in the component carrying the VDD label on
  M6.pin and all 81 VSS-pitch rails in the VSS one (zero orphans — the restored M5/M6 grid delivers),
  and the wells form exactly 80 disjoint full-width strips** (21.708 um wide, 0.27 um tall, 468.9
  um² total).
- **The attribution.** The metal power delivery of the routed slice is connected; the fragmentation
  is the well domain, and the only path from a well strip to its rail is the drawn tap geometry
  (TAPCELL p+ in well, SDT/LISD/V0, M1 — 320 taps are placed), which the pinned deck does not model:
  `FinFETExtractionDeck` declares no tap layer or implant pair, its own docstring says the well and
  the metal supply "are not joined … that is a connectivity *assumption* a comparison may choose to
  make", and `options.finfet_bulk` makes it per circuit only — enough for the single-cell r9 probe
  (`and2x2_probe.r9.report.json`: `match`), not for a multi-row block. **Filed generically as
  2AMLogic/klayout-tools#7182** (open, 2026-11-22), with a minimal reproducer and a verified
  fix experiment (`connect(nsd, well)` in the deck's FEOL wiring makes the bulk resolve to the rail);
  this repo's committed reproducer is `evidence/item4-lvs/tap_probe.r19.build.py` +
  `tap_probe.r19.extract.v`: three library cells in one row (logic, TAPCELL, logic) with labelled
  rails — both logic cells' PMOS-body ports land on one anonymous island while their supply ports
  land on the named `VDD`. The stream-side levers this issue's step 3 named are measured dead: labels
  name nets, they do not join them (the deck docstring, and #7182's "not a fix: draw more labels or
  more taps — the reproducer has both"), the taps already exist and the metal is already connected,
  so no `layout/pnr/` change can close this; the stream was not touched.
- **The device/net surplus, decomposed exactly.** The flat layout device count is 29,196 (the leaf
  census weighted by instances; equals the report's `counts.devices.layout`) against the reference's
  28,824 (equals the CDL expansion the report records; the per-cell CDL device counts are pinned
  inside the census script against the CDL's recorded sha256): a surplus of **exactly 372 = 2 × 186,
  and the 186 is AOI21x1_ASAP7_75t_R{,$VAR1}** — 87 + 99 instances drawing the A1/A2 nmos series
  stack twice at half width (two nfin=3 stacks where the CDL folds one nfin=6 stack; total fins
  16 = 16). The report's 186 `device.unmerged_fingers` entries are exactly those instances (every
  entry `nmos_rvt`, W=0.162 = 2 × 0.081). Not tap or filler: the TAPCELL/FILLER variants extract
  with zero devices and none is a netlist instance. The flat net surplus (+122) decomposes to the 80
  well islands plus the deck-synthesized `vsubs` global (81); the remaining 41 is flat-comparer
  bookkeeping the committed artifacts cannot decompose — stated, not smoothed over, r13's precedent.
  **Filed as #287** (this repo): even with #7182 closed, these 186 topology disagreements keep the
  routed-slice compare at `mismatch`, and resolving them (a klt-side series-stack fold, or an
  accepted recorded deviation) is a decision this issue does not own.
- **r19, the failing report of record** (`evidence/item4-lvs/slice_routed.r19.{request,report}.json`:
  the r18 request re-run on-pin, klayout 0.30.12, `klayout_version_mismatch: false`, same stream
  sha): still `mismatch`, 7,581 entries, now with every error category attributed to a named open
  issue — `device.unmatched` 4,528, `net.split` 1,328, `net.merged` 1,206, `hints.rejected` 64,
  `topology` 27, `net.supply_fragmented` 79 and `device.finfet_bulk_tied` 158 all cascade from the
  unmodelled well-tap path (**klayout-tools#7182**); `device.unmerged_fingers` 186 is the AOI21x1
  fold (**#287**); `reference.gate_level_pin_case_folded` 2 and the anchor/flattened notes are the
  benign bookkeeping the r13 section already explained. `klt signoff --manifest
  manifests/asap7-ucie-phy.json` grades item 4 digital **`unmet` / `check_failed`** citing r19 —
  the honest state until #7182 (and then #287) close.
- **Re-cites and hygiene.** Every record citing r17 now cites r19: the block manifest's `4.digital`,
  the item-8 attest inventory and its regenerated evidence envelope (43/43 checks pass, including
  the fresh `klt lvs --check` of r19), `verification/characterization-report.md`. The item-10
  inventory gained the census self-test, so item 10's `content_hash` is re-pinned and the envelope
  and verdict are regenerated in the same commit (t1_met_count 11 unchanged; `--check` reproduces).
  #20's park was re-pointed at this issue by the guide on 2026-11-21 and stands.

## The AOI21x1 fold cleared at the source: r20, the on-pin LVS record with zero unmerged fingers and a zero device surplus (appended 2026-11-23, issue #287)

Predictive-model tool results only. Earlier sections are left as written. Decision 0014 records the choice this section measures: excluding the 17 `klt` 0.9.2 `KNOWN_UNSUPPORTED_ASAP7_CELLS` masters at the source (`constraints.dont_use`, the #228 precedent extended from 10 to 27 masters) rather than waiving a `status: mismatch`, because `klt signoff` grades item 4 digital only on `status == "match"` and upstream had already declined stack normalisation (klayout-tools#4819 ruling; #6931's block-level `topology.known_limitation` disclosure is on `klt` `main` but not in PyPI 0.9.2).

- **The flow change.** `design/synth/slice.synth.json` `constraints.dont_use` now carries all 27 masters (the ten #228 `SDT.ACTIVE.AUX.2` deviators plus AND2x4, AND2x6, AOI21x1, AOI22x1, NAND3x2, NOR3x2, OAI21x1, OAI22x1, OR2x6, XNOR2x1, XOR2x1, A2O1A1O1Ixp25, AOI211xp5, OAI221xp5, SDFLx1, SDFLx2, SDFLx3, all `_ASAP7_75t_R`), and `layout/pnr/regen.py` stages `dont_use : true;` for that same list — read from the synthesis request, never re-typed — into the scratch Liberty handed OpenROAD, whose resizer has no other dont_use guard at the 0.9.2 request surface. `layout/pnr/test_check_input.py` covers the staging helper (named cell marked, un-named cell untouched, absent master an error). Re-synthesized, re-routed (same request geometry, seed 1), re-assembled: **zero instances of all 27 masters** in `design/netlist/slice_asap7.v` (2,504 instances) and `layout/slice_routed.v` (2,590 instances); the 186 `AOI21x1` re-mapped to 451 `AOI21xp5` + 5 `AOI21xp33` (both CDL-matching). Core area 937.786 -> 914.545 um².
- **r20, the report of record** (`evidence/item4-lvs/slice_routed.r20.{request,report}.json`: the r19 request re-run on the re-routed stream, klt 0.9.2, klayout 0.30.12, `klayout_version_mismatch: false`): still `mismatch` — 6,274 entries, 6,020 errors — but the AOI21x1 fold is gone: **`device.unmerged_fingers` 186 -> 0** and **device counts layout 28,784 == reference 28,784** (the +372 surplus is 0; the flat census expectation from the r18 section). Every remaining error family is the well-tap domain cascade attributed to klayout-tools#7182: `device.unmatched` 3,976, `net.merged` 1,022, `net.split` 958, `hints.rejected` 64, plus the non-error notes (`net.supply_fragmented` 79 -> 77, `device.finfet_bulk_tied` 158 -> 154, `topology` 27 -> 18, the same benign bookkeeping). r18/r19 stay byte-untouched (append-only); `klt lvs --check` re-verifies r20.
- **Timing re-taken on the new streams.** Pre-route `sta/slice.sta.r9.report.json` (same request, `netlist_estimate`, 0.25 ns clock): worst setup slack +0.02954 / −0.0969 / +0.08471 ns (0 / 156 / 0 violations — **ss still fails**), hold positive, Fmax 4535.92 / 2882.67 / 6049.89 MHz — equal to r8 at every reported digit (the exclusion re-mapped cells off the critical path; a measured result, mechanism not established), power 0.8552 -> 0.8452 mW tt (0.676 -> 0.6682 ss, 1.095 -> 1.082 ff). Routed `sta/slice.sta.routed.r3.report.json` (def-mode, committed DEF + SPEF, 0.5 ns P&R constraint): **0 setup / 0 hold violations at tt/ss/ff** (worst slack +0.24002 / +0.09434 / +0.30437 ns, hold +0.05157 / +0.07469 / +0.03454 ns), `annotation_complete: false` (2,519 of 2,713 nets — the standing net-name-coverage gap). r9 is the adopted pre-route record (`sta/regen.py --check-input` targets it).
- **DRC re-taken** (`verification/drc/`, r12 envelopes on the re-routed streams, klt 0.9.2 / klayout 0.30.12 on pin, same 267-id expectation set, no waivers, no filtering): routed slice 893 violations across the same 8 families as r11's 975 (M1.S.* 214, M3.S.2 14, M5.W.3 17, V4.M4.EN.1 636, V4.M5.EN.2 12); the column 14,288 across the same 8 (r11: 15,600). **`SDT.ACTIVE.AUX.2` stays 0** (absent from `rule_counts`), no new rule family appears, and item 3 stays `unmet` with the same open upstream dispositions.
- **Signoff consequence.** The netlist-bound chain moved atomically with the streams: items 1 (`evidence/item1.r13.json`, 21/21) and 2 (`attest/item2.r12.json` + `evidence/item2.r12.json`, 3/3) re-attested, item 8 re-pointed (r9 / routed r3 / r20 citations) and re-attested, the manifest re-pinned (`4.digital` -> r20, `1.*` -> r13, `2.*` -> r12, item 10 re-pinned for the 0014 inventory member) and the verdict regenerated. **Item 4 digital stays `unmet` / `check_failed`** — r20 is honestly `mismatch` — but its entire residue is now the single #7182 well-tap cause, so the in-repo half of the closure path is done: #20 owns the `.github/klt-version` bump to the PyPI release that carries #7182's deck fix, after which a fresh r21 is expected to close it. No claim of clean LVS today, no fabricated part, predictive PDK.

## Storing the next failing routed-slice LVS report (appended 2026-11-23, issue #136)

Operator ruling 2026-11-23 (#136, decision
[`0015-routed-lvs-report-storage.md`](decisions/0015-routed-lvs-report-storage.md)):
every LVS report and attempt record already committed keeps its path and bytes
(decision 0005); from now on a new failing flattened routed-slice compare is
committed as a **derived summary** unless it is the report a block-manifest
entry cites. When recording a run, generate the full comparison into scratch
space and commit the summary form, with distinct input and output paths:

```
jq '.mismatches = [] | .mismatches_omitted = true' "$full" > "$summary"
```

The summary keeps the tool's own `status`, `mismatch_count` / `error_count`,
`category_counts`, `category_error_counts`, `counts`, `options`, `environment`
and `provenance` — an empty `mismatches` list still reads as a failure, and the
`mismatches_omitted` marker discloses the omission — and the attempt record
names the file as a derived summary, not a `klt lvs` output. Commit the full
native output only when the block manifest will pin it by content hash; decide
that at recording time. r20 is that report of record today and stays full.
