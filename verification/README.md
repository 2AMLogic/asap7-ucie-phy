# verification

cocotb + Icarus testbench for `rtl/` (tracker #3, item 9, digital partition).

    verification/run.sh                      # exit 0 iff all tests pass
    verification/run.sh --negative-control   # exit 0 iff the deliberately broken check fails

`run.sh` checks `yosys`, `verilator`, `iverilog` against `tool-versions.txt` (it refuses to run
on a mismatch and never changes host tools), creates a private venv at `verification/.venv` with
the pinned `cocotb`, runs 16 and 8 lanes, and writes `verification/runs/<mode>-<stamp>.txt`
(gitignored) with the pins, seed, and pass/fail counts. `SEED=<n>` overrides the pinned seed.

`test_slice.py` loops the TX boundary through a behavioural model of the drawn stages (kept
here, never under `rtl/`) onto a forwarded clock with a different period and phase from `clk`.
It checks in-order delivery, no loss or duplication under `valid`/`ready` stalls, `tx_ready`
timing, `tx_fwd_en` per accepted word, no RX overflow, long valid-low runs, and reset mid-stream.
Simulator time units carry no rate or timing claim.

Lint and synthesis checks from the issue:

    verilator --lint-only -Wall rtl/*.v
    yosys -p 'read_verilog rtl/*.v; chparam -set N 8 slice; synth -top slice'
