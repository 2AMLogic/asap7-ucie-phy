# sta

> **Update (#72, r5/r6):** `slice.sta.r5.report.json` (registered `empty`, no latency change) and
> `slice.sta.r6.report.json` (plus one `rclk` of read-pipeline latency, `RPIPE = 1`, not adopted) are the
> fifth and sixth records. r5: tt +0.030, ss -0.097, ff +0.085 ns; r6: ss -0.097 ns. Still `unmet` (ss); see
> `worst-path-analysis.r5.md`. Needs klt `main` at or after `b8eaf053a`.
>
> **Update (#72, r4):** `slice.sta.r4.report.json` is the fourth record, after the registered one-hot
> read-select (decision 0009 option 1): tt +0.003, ss -0.124, ff +0.063 ns, so still `unmet` (ss); see
> `worst-path-analysis.r4.md`. Needs klt `main` at or after `b8eaf053a`.
>
> **Update (#72, r3):** `slice.sta.r3.report.json` is the third record, from a re-synthesis with
> `abc -constr` and no RTL change (decision 0009 option 3): tt -0.068, ss -0.231, ff +0.015 ns, so still
> `unmet`; see `worst-path-analysis.r3.md`. Needs klt `main` at or after `b8eaf053a`.
>
> **Update (#72):** `slice.sta.r2.report.json` is the second pre-route record, taken after the
> decision 0007 option-1 RTL change and a 0.25 ns timing-driven synthesis. It still fails setup
> (tt -0.269, ss -0.520, ff -0.180 ns); see `worst-path-analysis.r2.md` and decision 0009. The tables
> below describe the first record (`slice.sta.report.json`), which is kept unedited as history;
> `regen.py --report <name>` writes an appended record without touching it.

T1 item 5, digital partition, timing half (tracker #3, issue #21). One `klt sta` run of the
synthesized slice netlist across the three RVT Liberty corners. **The result is a failing
record**: setup slack is negative at every corner. Nothing was tuned to change that.

| File | Role |
|---|---|
| `slice.sta.json` | The request, and the only committed constraint artifact. `klt sta` has no SDC input |
| `slice.sta.report.json` | The `klt sta` report (klt 0.8.0), cited by `manifests/asap7-ucie-phy.json` under `5.digital` |
| `operating-conditions.json` | `nom_voltage` / `nom_temperature` read from every original Liberty header |
| `regen.py` | Rebuilds the report and the operating-conditions record from the pinned lambdapdk archive |

    KLT='uvx --from klayout-tools==0.8.0 klt' python3 -I sta/regen.py   # needs openroad on PATH

## What was run

- **Geometry**: `design/netlist/slice_asap7.v`, linked with no placement and no routing, so the
  report says `geometry_source: "netlist_estimate"`. **This is a pre-route estimate, not a
  post-route number.** No wire-load model is set, so wire parasitics are zero. The post-route
  record is a separate, later file (#18).
- **Constraints**: `clk` at 0.25 ns (the spec section 2 target period), `input_transition_ns` 0.02
  (spec section 5). No input or output delays.
- **Corners**: `tt`, `ss`, `ff` of `asap7sc7p5t_rvt`, from lambdapdk v0.2.17
  (`spec/asap7-bringup.md`).

| Corner | `timing_status` | Worst setup slack (ns) | Worst hold slack (ns) | Setup violations | Hold violations |
|---|---|---|---|---|---|
| tt | constrained | -1.07218 | 0.04663 | 72 | 0 |
| ss | constrained | -1.88432 | 0.06723 | 137 | 0 |
| ff | constrained | -0.76986 | 0.03083 | 72 | 0 |

The worst setup path at every corner runs `u_cdc/_3932_/QN` to `u_cdc/_3860_/D`, inside the CDC
FIFO (`u_cdc`). `klt signoff` grades this citation `unmet` / `check_failed`
because setup slack is negative; the functional-verification citations are `met`.

## Limits of this record, stated plainly

- **Clock uncertainty was not applied.** Spec section 5 fixes 5 percent of the period for setup
  and 2 percent for hold. `klt sta` has no field for it (filed as
  [klayout-tools#4240](https://github.com/2AMLogic/klayout-tools/issues/4240)). Every slack above
  is therefore optimistic against the ratified assumption, and **the 4 GHz rate row is not
  claimed closed**. The period was not shortened to emulate it: that cannot cover hold, and the
  spec is not relaxed here.
- **Only one clock is declared.** `rx_clk` (the forwarded clock) has no field in `klt sta`
  (filed as [klayout-tools#4241](https://github.com/2AMLogic/klayout-tools/issues/4241)).
  528 registers (the 20 sampled in the report are all under `u_cdc`) are reported under
  `constraint_completeness.unclocked_registers`, 665 endpoints are unconstrained, and the
  domain crossing is not timed. `timing_status: "constrained"` holds only for the checked
  subset, so the table above is not a whole-block statement.
- **Unconstrained sentinel**: no slack in the report is the `1e+39` sentinel. The first run of
  this request read `1e+39` in every corner (see the merge note below), so the sentinel is a
  real failure mode here, not a theoretical one.
- **FF Liberty anomaly (decision 0005)**: `asap7sc7p5t_SIMPLE_RVT_FF_nldm.lib.gz` declares
  0.7 V / 25 C (the TT point); the other four FF groups declare 0.77 V / 0 C. The FF row mixes
  operating points across cell classes. `operating-conditions.json` lists all fifteen headers
  (`"uniform": false` for FF only). The merged Liberty handed to `klt sta` carries the AO
  group's header, so this file, not the merged header, is the record of what was loaded.
- **Liberty merge**: `klt` refuses to list-merge the five cell groups (headers differ,
  [klayout-tools#4242](https://github.com/2AMLogic/klayout-tools/issues/4242)), so `regen.py`
  concatenates them. The SEQ group defines `delay_template_7x7` and `power_template_7x7`, which
  no other header defines; merging under the first header alone drops every SEQ timing table
  and leaves the block unconstrained. `regen.py` carries the union of the table templates.
  `design/synth/regen.py` uses the same merge (`design/lambdapdk.py`); with it the synthesis
  netlist is byte-identical to the earlier first-header-only merge.

## Issue #228 step 1: r7 (pre-route, re-synthesized netlist) and the first post-route sweep (2026-11-18)

The #228 step-1 cell swap (`constraints.dont_use` excluding the ten `SDT.ACTIVE.AUX.2`-deviating
masters, CTS buffer `BUFx4` → `BUFx3`; see the r8 record under `verification/drc/`) re-synthesized
the netlist, so the pre-route record was re-taken and the first post-route corner sweep was added.

- **`slice.sta.r7.report.json`** — the append-only pre-route successor to r5 (`--report
  slice.sta.r7.report.json`, same request, same corners, `netlist_estimate`): tt −0.09705 /
  ss −0.28538 / ff −0.01117 ns worst setup slack (8 / 158 / 1 setup violations), hold positive
  everywhere. An honestly **worse** estimate than r5 (+0.030 / −0.097 / +0.085): `dont_use` removed
  the fast BUFx2/OAI22xp33 mappings ABC had chosen. r7 replaces r5 as the adopted record
  (`regen.py --check-input` now targets it); r5 stays in the tree as history.
- **`slice.sta.routed.json` + `slice.sta.routed.report.json`** — the first post-route corner sweep:
  `klt sta` def-mode over the routed DEF (`layout/slice_routed.def`) with the run's post-route SPEF
  (`layout/slice_routed.spef`), corners tt/ss/ff at the P&R's 0.5 ns constraint. **Setup and hold
  0 violations at every corner** (worst setup slack +0.26174 / +0.13136 / +0.31933 ns; hold
  +0.05185 / +0.07512 / +0.03471 ns; `timing_status: constrained` everywhere). Two honest caveats,
  recorded in the report: `annotation_complete: false` (2,518 of 2,712 nets named by the SPEF —
  the known net-name-coverage gap; the in-flow `spef_sta` block shows the same at 2,523 of 2,717),
  and the sweep runs at the P&R's 0.5 ns constraint, **not** the section-2 0.25 ns clock — the rate
  row stays as the older sections here record it (not claimed closed; clock uncertainty still not
  applied, klayout-tools#4240).

`layout/pnr/regen.py` persists the routed DEF and post-route SPEF beside the GDS/SDF so this
record's inputs are committed, hashed files.

> **Update (#236):** `design/synth/variant-sweep.r1.md` records a pre-route variant sweep of the
> synthesis constraints. Setting `abc_constr.driving_cell` to a non-excluded buffer (BUFx3) instead of
> the excluded BUFx2 reproduces r5's pre-route Fmax and slack with zero deviating masters. It is a trial
> netlist only: not adopted, no record here changed.

## Issue #253: r8 (pre-route) and routed r2 (2026-11-18)

`design/synth/slice.synth.json` named `BUFx2_ASAP7_75t_R` as `abc_constr.driving_cell` while the same
file's `dont_use` excludes BUFx2. Issue #236's variant sweep (`design/synth/variant-sweep.r1.md`)
measured that moving it to a non-excluded buffer recovers the r5 pre-route timing; #253 applies
`BUFx3_ASAP7_75t_R` and re-synthesizes. The netlist has 0 instances of the ten excluded masters
(a per-master `grep` over `design/netlist/slice_asap7.v`). The mechanism inside ABC is not established;
this is a measured dependence.

- **`slice.sta.r8.report.json`**: pre-route successor to r7 (`regen.py --report slice.sta.r8.report.json`,
  same request, `netlist_estimate`, 0.25 ns clock). Worst setup slack tt +0.02954 / ss −0.0969 /
  ff +0.08471 ns (0 / 156 / 0 violations, so **ss still fails**); hold +0.05125 / +0.0742 /
  +0.03431 ns, 0 violations. Fmax 4535.92 / 2882.67 / 6049.89 MHz. Matches #236's prediction and r5 to
  the reported digits. r8 is now the adopted record (`regen.py --check-input` targets it).
- **`slice.sta.routed.r2.report.json`**: post-route successor to `slice.sta.routed.report.json`
  (same request `slice.sta.routed.json`, over the re-routed DEF/SPEF, 0.5 ns constraint). Setup slack
  +0.22524 / +0.07487 / +0.29353 ns, hold +0.05179 / +0.07505 / +0.03468 ns, 0 / 0 violations at tt / ss / ff.
  Caveats as before: `annotation_complete: false` (2,520 of 2,714 nets), 0.5 ns is not the section 2
  clock, clock uncertainty unapplied (klayout-tools#4240).
