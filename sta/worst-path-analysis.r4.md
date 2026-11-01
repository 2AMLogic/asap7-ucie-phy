# Fourth pre-route digital STA record: registered one-hot read-select

Issue #72, decision 0009 option 1 (accepted, operator ruling 2026-11-01). `sta/slice.sta.r4.report.json`
is appended beside r1-r3, which are not edited. Pre-route, `geometry_source: "netlist_estimate"`, no
wire load, no clock uncertainty, `rx_clk` undeclared (same limits as `sta/README.md`). **ss still fails
setup; tt and ff pass. 5.digital stays `unmet` (`check_failed`). The 4 GHz rate row is not claimed
closed.** Period (0.25 ns), `constraints.abc_constr` and all other constraints are unchanged.

## 1. Trace of the r3 worst path (done before the RTL change)

r3 worst setup path at tt/ss: `u_cdc/_4437_/QN` -> `u_cdc/_4095_/D`. Read from the r3 netlist
(`design/netlist/slice_asap7.v` at `fe976e3`): `_4437_`, `_4438_`, `_4439_` are the three low bits of
`rbin` (their `D` is the incrementer's XNOR output). Their outputs go through HB buffers and INV into
NAND3 gates (the 3-to-8 decode of `rbin[2:0]`), then more HB buffers, then OAI222 mux terms and an OR3
into `_4095_/D`, a bit of `rdata`. So the r3 path is the **read-select decode plus the 8:1 mux**, which
is what decision 0009 option 1 targets.

## 2. Change

`rtl/rx_cdc_fifo.v`: a registered one-hot read select `rsel` (reset to entry 0, rotated left on exactly the
cycles `rbin` advances) replaces the `mem[rbin[2:0]]` decode. `rdata` is the AND-OR of `mem[k]` with
`rsel[k]`. No port, interface or latency change. `rbin`/`rgray` stay for the `empty` compare. A `COPIES`
parameter replicates `rsel` (`keep`, so synthesis does not merge the copies). Cocotb at widths 16 and 8:
6 of 6 tests pass, bit-exact (`verification/run.sh`).

Tool: klt `0.8.1.dev1012+g31b24f439f3f` (`provenance.klt_git_commit` `31b24f439f3f5ba17a67a70a3b62ef8899fe189b`),
which includes `abc_constr` (PR #4665, `b8eaf053a`; r3 used `b8eaf053a` itself). The CI pin
`.github/klt-version` stays 0.8.0, so the synthesis freshness check stays `local_only`.

## 3. Result (committed: `COPIES = 1`)

| Corner | `timing_status` | Worst setup (ns), r3 -> r4 | Setup violations, r3 -> r4 | Worst hold (ns) | Hold violations | `fmax_mhz` |
|---|---|---|---|---|---|---|
| tt | constrained | -0.06761 -> +0.00308 | 66 -> 0 | 0.0467 | 0 | 4049.97 |
| ss | constrained | -0.23081 -> -0.12383 | 136 -> 145 | 0.0674 | 0 | 2675.03 |
| ff | constrained | +0.01455 -> +0.06286 | 0 -> 0 | 0.03099 | 0 | 5343.65 |

The new worst setup path at all three corners starts and ends in the `rbin` counter: ss
`u_cdc/_4464_/QN` -> `u_cdc/_4464_/D` (`rbin[3]`, whose next-state XNOR takes a NOR4 of `rbin[2:0]` and
the `!empty` enable, `empty` being the XNOR/NAND4 compare of `rgray` with `wgray_r2`); tt the same
start/end; ff `_4464_` -> `_4463_`. The read-select mux is no longer on the worst path. The limiting
structure is now the pointer increment gated by `empty`.

## 4. Trials made while choosing the committed form (not committed records)

Same RTL, only `COPIES` changed, re-synthesized and re-run with `sta/regen.py` (setup worst, ns; none are
committed records, reproduce by editing the parameter and running the two `regen.py` scripts):

| `COPIES` | tt | ss | ff |
|---|---|---|---|
| 1 (committed) | +0.00308 | -0.12383 | +0.06286 |
| 2 | -0.04461 | -0.20076 | +0.03449 |
| 4 | -0.01216 | -0.14884 | +0.05249 |
| 8 | -0.04793 | -0.20355 | +0.02894 |

Replication did not help: every copy adds flops to the `!empty` enable, which is the new limiter. The
ruling asked for a replicated select; `COPIES = 1` is what measured best, and the parameter keeps the
replicated form one edit away.

Option 2 (the pre-approved fallback) was measured the same way on top of `COPIES = 1`: an extra
`rdata_p`/`rvalid_p` stage between the mux and `rdata`. Result tt +0.00226, ss -0.12309, ff +0.06206 ns, the
same worst path (`rbin[3]` counter, ss `u_cdc/_4718_/QN` -> `u_cdc/_4717_/D`, i.e. unchanged in structure).
Because the pointer/`empty` path does not pass through the stage, it gains about 0.001 ns and does not close
ss, while costing one `rclk` of `rx_valid`/`rx_data` latency. **It was therefore not committed and no r5 record
was appended.** That is a deviation from the ruling's fallback step, made on measured numbers; the operator
can overrule it.

## 5. What this does not establish

- ss is -0.124 ns, so not every corner is non-negative and 5.digital's digital row is not claimed.
- These are single synthesis runs per parameter set; they do not show that no structure closes ss.
- Same coverage limits as r1-r3: unclocked `wclk` registers and unconstrained endpoints
  (klayout-tools#4241), no clock uncertainty (klayout-tools#4240), so every slack is optimistic.

The remaining lever is on the pointer/`empty` path (for example registering `empty`, or a different
increment structure), which is not in decision 0009 options 1-3 and needs a ruling.
