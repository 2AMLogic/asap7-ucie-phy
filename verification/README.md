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
in the simulation log, not assumed. That offset is measured as a residue on the replay grid
`gcd(period // 4, period // 2)`, so a new scenario's phase must leave a non-zero remainder on
that grid (or be exactly 0, claiming no offset); `Link.__init__` asserts it, because a phase
that is a non-zero whole multiple of the grid would measure as 0 and so read the same as no
offset at all. Simulator time units carry no rate or timing claim.

Lint and synthesis checks from the issue:

    verilator --lint-only -Wall rtl/*.v
    yosys -p 'read_verilog rtl/*.v; chparam -set N 8 slice; synth -top slice'

`functional_verification_sdf.sh` runs the same bench against the routed gate netlist
(`layout/slice_routed.v`) with `layout/slice_routed.sdf` applied (T1 item 7, digital).
It needs the pinned lambdapdk archive for the ASAP7 cell models. Under klt 0.9.2 the
`COND` arcs that caused the 0.9.1 refusal (klayout-tools#5296, COND half) are dropped
by klt before annotation and so carry no timing; the surviving arcs annotate normally.
The run still refuses, now only on the four INTERCONNECT entries of
the one-modpath-per-bit-selected-net cap (klayout-tools#5705, re-measured 2026-11-20 on an
internal bit-selected net, all four entries rejected). The refusal is recorded in
`functional-verification-sdf.report.json`; it is not a pass or a test failure, and no
manifest entry cites it.

Fidelity of that 0.9.2 annotation, re-measured 2026-11-20 under the pinned klt 0.9.2
(`.github/klt-version`, on the currently committed `layout/slice_routed.v` and
`layout/slice_routed.sdf`): the `COND` drop discards 10193 of the 16362 `IOPATH`
entries (`iopath_cond_expression` normalization; 6169 survive to be annotated), so
most cell arcs in this SDF are left with no back-annotated timing. Of the 6813
`INTERCONNECT` entries, klt drops 576 at the `bus_port_source` step; a further 128
bus-port entries are not dropped but split into a second SDF
(`klt_sdf_deferred_bus_ports.sdf`) that the run annotates via a second
`$sdf_annotate` call (measured: all 128 carry zero delay, and no diagnostic names
that file), so the attempted `INTERCONNECT` count is 6813 − 576 = 6237 — 6109 via
`klt_sdf_safe.sdf` plus 128 via the deferred file. klt
itself exits 1 (the refusal above). The intermediates are discarded on a refusal, so
re-measure by keeping the run and counting entries along the normalization chain:

    KEEP_RUN=/tmp/sdf-run ./verification/functional_verification_sdf.sh   # klt exit=1 expected
    grep -c "(IOPATH" layout/slice_routed.sdf /tmp/sdf-run/klt_sdf_cond_expression_dropped.sdf \
      /tmp/sdf-run/klt_sdf_safe.sdf                  # 16362 / 6169 / 6169
    grep -c "(INTERCONNECT" layout/slice_routed.sdf /tmp/sdf-run/klt_sdf_bus_port_source_dropped.sdf \
      /tmp/sdf-run/klt_sdf_safe.sdf /tmp/sdf-run/klt_sdf_deferred_bus_ports.sdf
                                                   # 6813 / 6237 / 6109 / 128
