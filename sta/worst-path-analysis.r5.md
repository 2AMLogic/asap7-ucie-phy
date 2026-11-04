# Fifth and sixth pre-route digital STA records: registered `empty`, then the latency step

Issue #72, operator ruling r5-q41 (2026-11-04). `sta/slice.sta.r5.report.json` and
`sta/slice.sta.r6.report.json` are appended beside r1-r4, which are not edited. Pre-route,
`geometry_source: "netlist_estimate"`, no wire load, no clock uncertainty, `rx_clk` undeclared (same
limits as `sta/README.md`). **ss still fails setup with and without the extra `rclk` of latency; tt and ff
pass. 5.digital stays `unmet` (`check_failed`). The 4 GHz rate row is not claimed closed.** Period
(0.25 ns), `constraints.abc_constr`, constraints and waivers are unchanged. Per the ruling, no third lever
was tried.

Tool: klt `0.8.1.dev1315+g90cea94010c4` (`provenance.klt_git_commit`
`90cea94010c4c004a087c3661b93adb8b9300a07`; r4 used `31b24f439f3f`). The CI pin `.github/klt-version`
stays 0.8.0, so the synthesis freshness check stays `local_only`. `manifests/asap7-ucie-phy.signoff.json`
was rendered with the 0.8.0 pin.

## 1. Trace of the r4 ss worst path (done before the RTL change)

r4 ss worst setup path: `u_cdc/_4464_/QN` -> `u_cdc/_4464_/D`, read from the r4 netlist as the `rbin[3]`
flop. Its next-state XNOR takes a NOR4 of `rbin[2:0]` and the `!empty` enable, and `empty` was the
combinational compare `rgray == wgray_r2` (XNOR per bit, then NAND4). So the structure is the pointer
increment gated by a 4-bit Gray compare: `rgray`/`wgray_r2` -> compare -> enable -> counter XNOR.

## 2. Change (restructure, no latency change): r5

`rtl/rx_cdc_fifo.v`:

- `empty` is a registered flop (reset 1) with `empty_n = empty ? (rgray == wgray_r1) : (rgray_nx == wgray_r1)`.
  This equals the old `rgray == wgray_r2` on every cycle: `wgray_r2` takes `wgray_r1` on the next edge and
  `rgray` takes its next value only when `!empty`. The old `wgray_r2` register is removed (it fed nothing
  else). The pointer enable, `rvalid` and the `rsel` rotate now start at a flop output.
- `rgray_nx` is a registered Gray code of `rbin + 1`, advanced with the pointer (`rgray_n2` from `rbin + 2`).
  The first attempt without it (below) put the incrementer carry chain in front of the compare.
- `COPIES` default 1 -> 2, the best measured value (section 4). No port, interface or latency change.

Cocotb at widths 16 and 8: 6 of 6 pass, same 4955 words checked as r4 (`verification/run.sh`).

| Corner | `timing_status` | Worst setup (ns), r4 -> r5 | Setup violations, r4 -> r5 | Worst hold (ns) | Hold violations | `fmax_mhz` |
|---|---|---|---|---|---|---|
| tt | constrained | +0.00308 -> +0.02954 | 0 -> 0 | 0.05125 | 0 | 4535.92 |
| ss | constrained | -0.12383 -> **-0.0969** | 145 -> 156 | 0.0742 | 0 | 2882.67 |
| ff | constrained | +0.06286 -> +0.08471 | 0 -> 0 | 0.03431 | 0 | 6049.89 |

New ss worst path: `u_cdc/_4679_/QN` -> `u_cdc/_4679_/D`, the `empty` flop's own loop: HB buffer -> AOI21 ->
XNOR2 -> NOR4 -> `empty_n`. The synthesizer folded the hold/advance select into the compare, so the loop is
flop, buffer, three gates. The pointer increment and the read-select mux are no longer the worst path.

## 3. Latency step: r6 (`RPIPE = 1`)

The restructure alone did not close ss, so the ruling's one extra `rclk` was used: a read-pipeline stage
(`rdata_p`/`rvalid_p`) between the 8:1 mux and `rdata`/`rvalid`, behind a `RPIPE` parameter (default 0).
Same RTL and `COPIES = 2` as r5 apart from `RPIPE`.

| Corner | `timing_status` | Worst setup (ns), r5 -> r6 | Setup violations | Worst hold (ns) | `fmax_mhz` |
|---|---|---|---|---|---|
| tt | constrained | +0.02954 -> +0.0293 | 0 | 0.0467 | 4531.06 |
| ss | constrained | -0.0969 -> **-0.09729** | 156 | 0.0674 | 2879.44 |
| ff | constrained | +0.08471 -> +0.08452 | 0 | 0.03099 | 6042.88 |

The ss worst path is the same `empty` loop (`u_cdc/_5159_/QN` -> `u_cdc/_5159_/D`, same four-cell structure).
The extra stage does not touch that loop, so it buys nothing (-0.0004 ns), at one `rclk` more
`rx_valid`/`rx_data` latency. Cocotb at both widths passed with `RPIPE = 1` (6 of 6, 4943 words), so the
valid-only RX interface tolerates the latency; it is **not adopted** because it does not close ss. The
committed default is `RPIPE = 0`, and the committed netlist is the `RPIPE = 0` synthesis (r5).

## 4. Trials made while choosing the committed form (not committed records)

Same flow, only the named change; setup worst (ns). Reproduce by editing the parameter and running
`design/synth/regen.py` then `sta/regen.py`.

| Variant | tt | ss | ff | ss worst path |
|---|---|---|---|---|
| registered `empty` only (compare from `rbin + 1` combinationally), `COPIES` 1 | +0.00634 | -0.13000 | +0.06605 | `rbin` low bit -> incrementer carry -> Gray -> XNOR -> NOR4 -> `empty_n` |
| + registered `rgray_nx`, `COPIES` 1 | +0.01461 | -0.10546 | +0.07816 | `rsel` flop (fanout 64) -> HB -> OAI222 -> OR3 -> `rdata` |
| + registered `rgray_nx`, `COPIES` 2 (committed) | +0.02954 | -0.0969 | +0.08471 | `empty` loop |
| + registered `rgray_nx`, `COPIES` 4 | -0.0127 | -0.15494 | +0.06412 | not traced |
| + registered `rgray_nx`, `COPIES` 8 | +0.02969 | -0.0943 | +0.08303 | not traced |
| `COPIES` 1 + `RPIPE` 1 | +0.00742 | -0.133 | +0.06827 | `empty` loop |
| `COPIES` 1 + `RPIPE` 1 + `(* keep *)` on the two compares | +0.00742 | -0.133 | +0.06827 | same; `keep` changed nothing |

`COPIES` 8 is within 0.003 ns of `COPIES` 2; 2 is committed because it uses fewer flops. These are single
synthesis runs, so differences of a few picoseconds are inside run-to-run structure noise.

## 5. What this does not establish

- ss is -0.0969 ns (-0.0973 ns with the latency step), so not every corner is non-negative and 5.digital's
  digital row is not claimed.
- The remaining limiter is the `empty` self-loop (flop to `empty_n`). It is a four-cell loop at 0.25 ns in
  the ss library; a further restructure of it would be a third lever, which the ruling says needs its own
  ruling.
- Same coverage limits as r1-r4: unclocked `wclk` registers and unconstrained endpoints
  (klayout-tools#4241), no clock uncertainty (klayout-tools#4240), so every slack is optimistic.
