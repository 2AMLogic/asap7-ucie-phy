# 0009: closing the pre-route setup failure on the CDC FIFO read-mux select

Status: **proposed** (needs a ruling). Date: 2026-10-29. Issue: #72. Evidence: `sta/worst-path-analysis.r2.md`.

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
