# sta

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
