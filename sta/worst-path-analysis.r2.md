# Worst-path analysis of the second pre-route digital STA record

Issue #72. Analysis of `sta/slice.sta.r2.report.json` (klt 0.8.0), run on the netlist re-synthesized
from the option-1 RTL of decision 0007 with `clock_period_ns = 0.25`. It is appended beside
`sta/slice.sta.report.json` and `sta/worst-path-analysis.md`, which are not edited. Pre-route,
`geometry_source: "netlist_estimate"`, no wire load, no clock uncertainty, `rx_clk` undeclared (same
limits as `sta/README.md`). **Setup still fails at all three corners; 5.digital stays `unmet`
(`check_failed`). The 4 GHz rate row is not claimed closed.** No constraint, period or waiver was changed.

## 1. Result

| Corner | `timing_status` | Worst setup (ns), before -> after | Setup violations, before -> after | Worst hold (ns) | Hold violations | `fmax_mhz` |
|---|---|---|---|---|---|---|
| tt | constrained | -1.07218 -> -0.26934 | 72 -> 68 | 0.04663 | 0 | 1925.54 |
| ss | constrained | -1.88432 -> -0.52015 | 137 -> 137 | 0.06723 | 0 | 1298.46 |
| ff | constrained | -0.76986 -> -0.18046 | 72 -> 66 | 0.03083 | 0 | 2323.08 |

Hold is positive everywhere. Option 1 plus timing-driven mapping recovered about 0.8 ns at tt, but the
critical path still needs about 0.52 ns (tt), 0.77 ns (ss) and 0.43 ns (ff) against 0.25 ns. The
worst path is again identical at all corners [`worst_setup_path`]: `u_cdc/_3792_/QN` to `u_cdc/_3451_/D`,
both on `rclk`, which the slice ties to `clk`, so the missing `rx_clk` declaration does not distort it.

## 2. What the path is now

A read of the committed netlist (per-stage delays are not in the report). `_3792_` is a read-pointer
register (`rbin[2:0]`, QN fanout 10). Its QN, through `INVx1` and `NAND3xp33` terms, forms the one-hot
decode of the 8:1 read mux; each decode net drives about 64 mux loads (one per `rdata` bit). The path
runs through that 64-load decode into an `OAI222`/`OAI22` mux level and an `OR3x1` into `_3451_/D`
(`rdata`). The `empty` fanout that decision 0007 targeted is gone; the limiting structure moved to the
`mem[rbin]` read-mux select fanout. Whether more than one pointer bit is on the critical cone was not
traced beyond this.

## 3. What this does not establish

- It does not show that no mapping closes 0.25 ns; it shows this RTL does not, in this one synthesis run.
- The 528 unclocked `wclk` registers and 665 unconstrained endpoints (klayout-tools#4241) are unchanged,
  so `constrained` covers the checked subset only.
- Clock uncertainty (klayout-tools#4240) is still not applied; every slack is optimistic.

The next step is a new decision record (0009), as decision 0007 "Consequences" requires.
