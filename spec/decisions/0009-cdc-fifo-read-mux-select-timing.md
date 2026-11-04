# 0009: closing the pre-route setup failure on the CDC FIFO read-mux select

Status: **accepted** (option 1, fallback option 2 pre-approved; operator ruling by rjwalters, 2026-11-01, https://github.com/2AMLogic/asap7-ucie-phy/issues/72; earlier ruling 2026-10-30 accepted option 3 as a measurement). Option 3 and option 1 did not close; see the outcomes below. Date: 2026-10-29. Issue: #72. Evidence: `sta/worst-path-analysis.r2.md`.

## Context

Decision 0007 option 1 (accepted, #72) decoupled `rdata` from `empty` and the netlist was
re-synthesized at 0.25 ns. The new record `sta/slice.sta.r2.report.json` still fails setup at tt, ss and ff
(-0.26934, -0.52015, -0.18046 ns; hold positive). The worst path is now the read-pointer decode that
selects `mem[rbin[2:0]]`: about 64 loads per decode net, one per `rdata` bit. Nothing here relaxes
section 2 or section 5, and no constraint is tuned. As in 0007, the fanout figures are a netlist read, not a
re-derived pin count.

## Options

1. **Register a one-hot (or buffered, replicated) read-select.** Keep a registered one-hot copy of the read
   pointer so the decode is a flop output per entry, replicated so each copy drives a subset of the 64 bits.
   No interface or latency change; costs flops and a Gray/one-hot consistency check. Candidate for the first
   attempt.
2. **Add a read-pipeline stage between `mem` and `rdata`.** Splits the mux from the output register. Adds one
   `rclk` cycle of latency to `rx_valid`/`rx_data`, which must be checked against the valid-only RX interface
   and the testbench.
3. **Timing-driven re-synthesis with buffering constraints only, no RTL change.** Run as a measurement;
   the 0.25 ns run already set the period, so a gain is unlikely without a structural change.
4. **Spec change (fall back to the 4 GT/s row) or tuning/waiving constraints.** Rejected for the same reasons as 0007
   options 4 and 5: relaxes the ratified spec.

## Consequences if accepted

- A follow-up RTL issue implements the chosen option and appends a new STA record; the failing records stay.
- 5.digital stays `unmet` until a record shows every corner `constrained` with non-negative setup and hold slack.
- The 4 GHz row stays unclaimed until post-route STA (#23) with clock uncertainty and `rx_clk` declared
  (klayout-tools#4240, #4241) passes at every corner.

## Outcome of option 3 (#72)

Re-synthesis at 0.25 ns with `abc -constr` (`sta/worst-path-analysis.r3.md`): `sta/slice.sta.r3.report.json`
gives setup tt -0.06761, ss -0.23081, ff +0.01455 ns, hold positive everywhere. tt and ss still fail, so
5.digital stays `unmet`. Options 1 and 2 stay in this record as the next levers; neither is ruled.

## Outcome of option 1 (#72)

Option 1 was built (`rtl/rx_cdc_fifo.v`: registered one-hot read-select `rsel`, `COPIES` parameter, committed
at 1) after tracing the r3 worst path to the `rbin[2:0]` decode and mux (`sta/worst-path-analysis.r4.md`).
`sta/slice.sta.r4.report.json`: setup tt +0.00308, ss -0.12383, ff +0.06286 ns, hold positive. ss still fails,
so 5.digital stays `unmet`. The new worst path is the `rbin[3]` counter increment gated by `empty`, not the
mux. Replicating `rsel` (`COPIES` 2, 4, 8) was worse, because each copy loads the `!empty` enable. Option 2 was
measured (not committed, no r5 record): ss -0.12309 ns, the same limiting path, for one `rclk` more latency,
so it was not adopted. The next lever is on the pointer/`empty` path and is not ruled.

## Outcome of the pointer/`empty` restructure and the latency step (#72, operator ruling r5-q41)

Ruled 2026-11-04: restructure the read-pointer / `empty` path first with no latency change, then, only if that
does not close every corner, allow one extra `rclk` of latency on `rx_valid`/`rx_data`; stop and report if
neither closes ss. Both steps were run (`sta/worst-path-analysis.r5.md`).

- **Restructure (r5):** `empty` registered and computed from the next-state pointers, plus a registered Gray
  code of `rbin + 1` (`rtl/rx_cdc_fifo.v`), `COPIES = 2`. `sta/slice.sta.r5.report.json`: setup tt +0.02954,
  ss -0.0969, ff +0.08471 ns, hold positive. ss improved from -0.12383 but still fails.
- **Latency step (r6):** a read-pipeline stage behind `RPIPE = 1`. `sta/slice.sta.r6.report.json`: ss -0.09729 ns.
  The limiter is the `empty` flop's own loop, which the stage does not touch. The cocotb suite passes with the
  extra cycle (the valid-only RX interface tolerates it), but it was **not adopted** (`RPIPE` default 0)
  because it costs a cycle for no timing gain.
- 5.digital stays `unmet`. Per the ruling no third lever was tried. The remaining path is the four-cell
  `empty` loop; any further change to it needs a new ruling. Option 4 and any constraint, period or waiver
  change stay rejected.
