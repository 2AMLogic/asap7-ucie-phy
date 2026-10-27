# Worst-path analysis of the pre-route digital STA record

Issue #39. Analysis of `sta/slice.sta.report.json` (klt 0.8.0, committed by #21) against
`design/netlist/slice_asap7.v` and `rtl/rx_cdc_fifo.v`. **No new STA run was made**; every figure is
a field of the committed report (named in brackets) or a read of the committed netlist. Pre-route,
`geometry_source: "netlist_estimate"`, no wire load, no clock uncertainty. This is a diagnosis of a
failing record, not a closure claim. The 4 GHz rate row is not claimed closed.

## 1. What the report says

| Corner | `worst_slack_ns` | `setup_violation_count` | `fmax_mhz` | 0.25 ns minus slack (ns) | 1000 / `fmax_mhz` (ns) |
|---|---|---|---|---|---|
| tt | -1.07218 | 72 | 756.328 | 1.32218 | 1.32218 |
| ss | -1.88432 | 137 | 468.533 | 2.13432 | 2.13432 |
| ff | -0.76986 | 72 | 980.528 | 1.01986 | 1.01986 |

`fmax_mhz` agrees with the period (`sta/slice.sta.json` `clock_period_ns` 0.25) minus the worst slack,
so the critical path needs about 1.32 ns at tt, 2.13 ns at ss and 1.02 ns at ff. That is 5.3x, 8.5x and
4.1x the 0.25 ns target. Hold is positive at all three (`worst_hold_slack_ns` 0.04663, 0.06723,
0.03083; `hold_violation_count` 0). `total_negative_slack_ns` is -62.8663 (tt), -116.131 (ss), -45.131 (ff).

The worst setup path is identical at all corners [`worst_setup_path.startpoint` `u_cdc/_3932_/QN`,
`.endpoint` `u_cdc/_3860_/D`, `.consistent_with_aggregate` true].

## 2. Does the unclocked `rx_clk` distort the worst path? No.

Both end registers of the worst path are clocked by `rclk`, and the slice ties `rclk` to `clk`
(`design/netlist/slice_asap7.v`, `u_cdc` instance: `.rclk(clk)`, `.wclk(rx_clk)`; `_3932_` and `_3860_`
both have `.CLK(rclk)`). So the worst path is a same-domain `clk`-to-`clk` path on the declared
clock, not a domain crossing, and the missing `rx_clk` declaration does not change its slack.

What the missing declaration does hide is separate. 528 registers are unclocked
[`constraint_completeness.unclocked_registers.count`] and 665 endpoints are unconstrained
[`unconstrained_endpoints.count`]; all 528 are the `wclk` registers (the netlist has 528 `wclk` and 80
`rclk` flops in `u_cdc`). Paths launched by those registers and captured on `clk` are not timed: the
`wgray` to `wgray_r1` synchronizer input and the FIFO memory read into `rdata`. The reported slack
is therefore optimistic or unaffected, never pessimistic, with respect to the missing clock. Fixing
this is a tool gap (klayout-tools#4241), not a design change.

## 3. Why the path exceeds 0.25 ns

Trace of the committed netlist (a netlist read; per-stage delays are not in the report, see section 5).
`_3932_` is a read-side Gray-pointer register (`rgray`), compared with the synchronized write pointer
by `empty = (rgray == wgray_r2)` in `rtl/rx_cdc_fifo.v`. The path found from `_3932_/QN` to `_3860_/D`:

    _3932_/QN (fanout 4) -> XOR2 _2154_ -> NOR4xp25 _2155_ (net _1209_, fanout 94)
                         -> AOI22 _3223_ A2 -> _3860_/D

Net `_1209_` is the `.Y` of `NOR4xp25 _2155_` (netlist L2458-L2463), a weak `xp25` cell. The NOR4 of the
per-bit XOR terms is the equality `rgray == wgray_r2`, so `_1209_` is **`empty`**, not `!empty`. It has one
driver and 94 loads (counted by pin over the netlist): 56 `AOI21xp33.A2`, 11 `NAND2xp33.B`, 11
`OAI21xp33.A1`, 9 `NOR5xp2.A`, and 7 others including the inverter below. By the RTL, `empty` gates the load of `rdata`, `rbin` and
`rgray` and feeds `rvalid`; the mapping of each load to a register was not traced. The path goes from the NOR4 output straight
into `AOI22xp33 _3223_ .A2(_1209_)` and then `.Y(_1012_)` into `_3860_/D` (L9884, L13857); no inverter is on
it. `INVx1 _2156_` takes `.A(_1209_)` and drives `.Y(_0000_)`, i.e. `!empty`, which has 48 loads (41
`OAI221xp5.C`, 4 `OAI21xp33.B`, 3 others) and is a separate branch: `_0000_` is in the fan-in cone of
`_3860_/D`, but the traced worst path does not pass through it. Whether the `_0000_` branch is also
critical is not established by the report (no per-stage delay).

With no wire load the delay of the NOR4 stage is pure pin capacitance: a weak `xp25` NOR4 drives 94
pins, and it is the only high-fanout net on the traced path (the other nets on it have fanout 1 to 4).
The logic is three cells deep on the traced path (XOR2, NOR4, AOI22); the 1.32 ns at tt cannot come from depth, so the high-fanout `empty` net is
the cause the netlist points to.

Cause class: **fanout and loading on the single `empty` net, same domain.** It is not logic depth,
and not a crossing artefact. Contributing: the synthesis request sets `"clock_period_ns": null`
(`design/synth/slice.synth.json`), so the mapping was not timing-driven and no buffer tree was built
for `_1209_`.

## 4. The 72, 137 and 72 violations

The report gives counts, not endpoint lists (only `worst_setup_path` is recorded). The 72 at tt and ff is
consistent with the 64 `rdata` endpoints plus 8 pointer/status endpoints that share the `empty` control,
but that grouping is an inference and is not established by the report. The ss count of 137 exceeds the 80
`rclk` flops in `u_cdc`, so at ss other registers on `clk` outside `u_cdc` (the TX serializers, `slice.v`)
also fail; which ones is not recoverable from the committed report. A split by endpoint group needs a new
run with endpoint reporting, which klt 0.8.0 does not expose (the report has no per-endpoint list).

## 5. What is not established

- Per-stage delays and the fanout delay share: the report has one path per corner with no stage detail.
- The CDC FIFO versus slice split of the violations (section 4).
- Any number with clock uncertainty (5 percent setup, 2 percent hold, spec section 5) applied; klt has no
  field (klayout-tools#4240), so every slack here is optimistic against the ratified assumption.
- Any post-route figure (#18).

## 6. Consequence for the fallback row

The 1 GHz fallback row (spec section 2) is a 1.0 ns period. The tt critical path needs 1.32 ns and the ss
path 2.13 ns (section 1), so falling back to 1 GHz would still fail at tt and ss on this netlist. The
fallback row is not a way to turn this record green; the design change below is needed at every row.

See `spec/decisions/0007-cdc-fifo-read-enable-timing.md` for the recommended option.
