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
