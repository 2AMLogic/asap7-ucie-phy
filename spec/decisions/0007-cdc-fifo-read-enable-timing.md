# 0007: closing the pre-route setup failure on the CDC FIFO read enable

Status: **proposed** (needs a ruling). Date: 2026-10-27. Issue: #39. Evidence: `sta/worst-path-analysis.md`.

## Context

The pre-route record `sta/slice.sta.report.json` fails setup at tt, ss and ff (-1.07218, -1.88432,
-0.76986 ns at 0.25 ns). The worst path is a same-domain `clk` path from the read Gray pointer through
`empty` to the 64-bit `rdata` enable, where one `INVx1` drives a fanout of 94 and the synthesis request set
no clock period. The analysis does not depend on the undeclared `rx_clk`. The 1 GHz fallback row would also
fail on this netlist (tt needs 1.32 ns). Nothing here relaxes section 2 or section 5, and no constraint is
tuned.

## Options

1. **Recommended: decouple the data path from `empty`, then re-synthesize timing-driven.** In
   `rtl/rx_cdc_fifo.v`, load `rdata` from `mem[rbin]` every `rclk` edge and let `rvalid` (already registered from
   `!empty`) mark the word, so `!empty` drives only the 4-bit pointers and `rvalid` (roughly 10 loads by count of those registers, not 94; not re-synthesized).
   Then re-run `design/synth/regen.py` with `clock_period_ns` set to the spec's 0.25 ns and re-run `klt sta`
   as a new appended record. This removes the offending fanout structurally and lets mapping buffer what
   remains. Costs: `rx_data` is undefined while `rx_valid` is low, which must be checked against the
   interface in `rtl/README.md` (valid-only RX), and the cocotb testbench updated; this is an RTL change, not a spec change.
2. **Timing-driven re-synthesis only, no RTL change.** Smallest change, but it leaves a 94-load enable in a
   0.25 ns path and relies on the mapper building a buffer tree inside about 0.17 ns of usable budget (period
   minus clock-to-q, setup and the 12.5 ps setup uncertainty not yet applied). Likely to need option 1 anyway.
   Worth running first as a measurement.
3. **Registered `empty` computed from next-state pointers.** Standard fix, same effect on the XOR/NOR4 depth,
   but the enable still fans out to 64 `rdata` bits, so the fanout problem remains.
4. **Spec change: fall back to the 4 GT/s (1 GHz) row.** Rejected: the tt path needs 1.32 ns and the ss path
   2.13 ns, so 1 GHz also fails; it also changes the ratified target without removing the cause.
5. **Tuning constraints, a shorter period, or waiving the failing paths.** Rejected: relaxes or games
   the ratified spec (CLAUDE.md), and a shorter period cannot cover hold.

## Consequences if accepted

- A follow-up RTL issue implements option 1; this record lands no RTL, constraint or spec change.
- The follow-up appends a new STA record beside `sta/slice.sta.report.json` and keeps the failing one.
- The 4 GHz row stays unclaimed until post-route STA (#18) with clock uncertainty and `rx_clk` declared
  (klayout-tools#4240, #4241) passes at every corner.
- If option 1 still fails after re-synthesis, the next record will show whether a deeper RTL or architecture
  change is needed; that would be a new decision record.
