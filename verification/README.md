# verification

cocotb + Icarus testbench for `rtl/` (tracker #3, item 9, digital partition).

    verification/run.sh                      # exit 0 iff all tests pass
    verification/run.sh --negative-control   # exit 0 iff the deliberately broken check fails

`run.sh` checks `yosys`, `verilator`, `iverilog` against `tool-versions.txt` (it refuses to run
on a mismatch and never changes host tools), creates a private venv at `verification/.venv` with
the pinned `cocotb`, runs 16 and 8 lanes, and writes `verification/runs/<mode>-<stamp>.txt`
(gitignored) with the pins, seed, and pass/fail counts. `SEED=<n>` overrides the pinned seed.

`test_slice.py` loops the TX boundary through a behavioural model of the drawn stages (kept
here, never under `rtl/`) onto a forwarded clock with a different period and phase from `clk`:
each scenario holds the forwarded clock idle for its stated offset before replaying its first
word, so the three scenarios cross the boundary at three distinct alignments. It checks
in-order delivery, no loss or duplication under `valid`/`ready` stalls, `tx_ready` timing,
`tx_fwd_en` per accepted word, no RX overflow, long valid-low runs, reset mid-stream, and that
the forwarded clock carries the stated offset — measured at `rx_clk` and reported per scenario
in the simulation log, not assumed. Simulator time units carry no rate or timing claim.

Lint and synthesis checks from the issue:

    verilator --lint-only -Wall rtl/*.v
    yosys -p 'read_verilog rtl/*.v; chparam -set N 8 slice; synth -top slice'

`functional_verification_sdf.sh` runs the same bench against the routed gate netlist
(`layout/slice_routed.v`) with `layout/slice_routed.sdf` applied (T1 item 7, digital).
It needs the pinned lambdapdk archive for the ASAP7 cell models. As of klt 0.9.1 it does
not complete: Icarus rejects the SDF's `COND` arcs and four INTERCONNECT entries, and klt
refuses to report a zero-delay run as annotated (klayout-tools#5296). The refusal is
recorded in `functional-verification-sdf.report.json`; it is not a pass or a test failure,
and no manifest entry cites it.
