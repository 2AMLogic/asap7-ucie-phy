# Third pre-route digital STA record: buffering-constrained re-synthesis

Issue #72, decision 0009 option 3 (accepted, operator ruling 2026-10-30), run as a measurement.
`sta/slice.sta.r3.report.json` is appended beside r1 and r2, which are not edited. Pre-route,
`geometry_source: "netlist_estimate"`, no wire load, no clock uncertainty, `rx_clk` undeclared (same
limits as `sta/README.md`). **Setup still fails at tt and ss; ff passes. 5.digital stays `unmet`
(`check_failed`). The 4 GHz rate row is not claimed closed.** No RTL, period or waiver was changed.

## 1. What changed from r2

Only the synthesis request: `design/synth/slice.synth.json` gained
`constraints.abc_constr = {driving_cell: BUFx2_ASAP7_75t_R, load_ff: 3.898}`, so `klt synthesize`
passes `abc -constr` (load-driven sizing and buffering). Those two values are ORFS's own ASAP7
`ABC_DRIVER_CELL` / `ABC_LOAD_IN_FF`, taken from the ORFS platform config as remembered and not
re-checked against a fetched copy in this run; they were not varied. The clock period (0.25 ns) is
unchanged, and `rtl/` is untouched.

`design/synth/regen.py` also now adds the missing `;` to 37 `area : <x>` lines in its scratch copy of the
Liberty. klt's cell-list reader stopped at the first of them (43 of 202 cells visible) and rejected the
driving cell. No value changes; the same unterminated lines are still handed to `klt sta` unchanged.

Tool: klt `0.8.1.dev851+gb8eaf053a721` (klayout-tools `main` at `b8eaf053a`, PR #4665); published 0.8.0
has no `abc_constr` field. The CI pin in `.github/klt-version` stays 0.8.0, so the synthesis
freshness check is `local_only` as before and reproduces only with that commit or later.

## 2. Result

| Corner | `timing_status` | Worst setup (ns), r2 -> r3 | Setup violations, r2 -> r3 | Worst hold (ns) | Hold violations | `fmax_mhz` |
|---|---|---|---|---|---|---|
| tt | constrained | -0.26934 -> -0.06761 | 68 -> 66 | 0.0467 | 0 | 3148.5 |
| ss | constrained | -0.52015 -> -0.23081 | 137 -> 136 | 0.0674 | 0 | 2079.84 |
| ff | constrained | -0.18046 -> +0.01455 | 66 -> 0 | 0.03099 | 0 | 4247.2 |

The worst setup path at tt and ss is the same: `u_cdc/_4437_/QN` to `u_cdc/_4095_/D` (ff:
`_4437_/QN` to `u_cdc/_4142_/D`). Both ends are in `u_cdc`, so the missing `rx_clk` declaration does not
bear on them. Which structure that path crosses was not traced in this run.

## 3. What this does not establish

- Not every corner is non-negative, so 5.digital's digital row is not claimed.
- One synthesis parameter set was run. It does not show that no buffering setting closes tt and ss.
- Same coverage limits as r1/r2: 528 unclocked `wclk` registers and 665 unconstrained endpoints
  (klayout-tools#4241), no clock uncertainty (klayout-tools#4240). Every slack is optimistic.

The remaining gap is -0.068 ns (tt) and -0.231 ns (ss). The next lever is a ruling on decision 0009
option 1 or 2 on these measured numbers.
