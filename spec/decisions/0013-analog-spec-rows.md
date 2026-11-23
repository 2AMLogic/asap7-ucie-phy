# 0013: proposed cell-level analog spec rows for the four drawn cells

Status: proposed. Date: 2026-11-20. Issue: #277. Part of: #276.

Not ratified by merge. An operator ratifies or amends this record in a follow-up (#279 files it);
until then it binds nothing, grades nothing and changes no verdict. The follow-up is **#306**,
filed with the provisional four-cell results and both probes' outcomes.

## Context

T1 items 5, 6 and 7 grade `unmet / no_evidence` on the analog partition because the ratified spec
has no analog performance row (decisions 0006, 0008): there is no target for a PVT matrix, a Monte
Carlo campaign or a schematic-versus-extracted delta. The operator ruling on
2AMLogic/klayout-tools#4183 names the discharge path: add the missing rows through a decision the
operator ratifies, then supply the evidence. Circuit simulation is no longer the blocker: decision
0010 supersedes the ngspice 42 failure of decision 0003, and `sim/` holds logic-level TT/SS/FF runs
of all four cells on ngspice 47.

This record proposes the rows and binds their PVT tuples, loads, stimulus, limits and bench paths.
It owns no measurement: #278 measures the data-cell rows and probes `klt yield`; #279 measures the
clock-cell rows, probes `klt pex` and files the operator follow-up.

## Rows

Row IDs are final for the consumers: #278 measures a1-a6, #279 measures a7-a10. Limits are set from
the ratified section 2 rate rows and the committed bump map, never from a measured value. Decision
0010's TT reports do hold level readings (`vpad_ph0` = 0.7 V in `sim/tx_cell.batch.report.json`,
`vrxa0_hold1` = 0.7 V in `sim/rx_cell.batch.report.json`): functional pass/fail assertions at
0.7 V / 25 C flat, on the historical benches. They are not measurements of a1-a10 under the
definitions below (§6 tuples, the conventions B1-B3, the worst-case edge rules), and the limits here
were set independently of them. No transition time, delay, duty error, trip point or offset has
been measured. Fractions of the budget that the ratified inputs do not determine are stated in the
assumption ledger.

### Data cells (measured by #278)

| ID | Cell | Quantity (unit) | Measurement definition | Stimulus / load | PVT | Proposed limit |
|---|---|---|---|---|---|---|
| `a1-tx-pad-levels` | `tx_cell` | pad high and low level (V) | steady-state `v(pad)` after the selected input settles; selected input at 0 and at 1, all four mux selections walked | data/select inputs full-swing 0/VDD, linear 10 ps ramps (B1); 2 fF on `pad` to VSS (L1); polarity per B2: pad = NOT selected input | §6 tuples | high ≥ 0.9·VDD, low ≤ 0.1·VDD |
| `a2-tx-pad-transition` | `tx_cell` | pad rise/fall time, 20-80% (ps) | 20%-80% time of `v(pad)` for each rising and each falling `pad` edge produced by a selected-input step (selected input falling → pad rising, rising → pad falling), on each of the four mux selections; the limit bounds the worst of the eight | same as a1 | §6 tuples | ≤ 15.625 ps (target) / 62.5 ps (fallback) |
| `a3-tx-mux-to-pad-delay` | `tx_cell` | input-to-pad delay (ps) | 50% crossing of the driving input edge to the 50% crossing of the resulting `v(pad)` edge, one measurement per path and edge pair: each data input, selected, steps rising (pad falls) and falling (pad rises); each of `sel1` and `sel2` rising and falling, with the other select held and the newly selected input at the level that makes `pad` rise in one measurement and fall in the other, the old selected input at the opposite level. The limit bounds the worst of all measurements, rising and falling pad edges both | same as a1 | §6 tuples | ≤ 31.25 ps (target) / 125 ps (fallback) |
| `a4-rx-sampler-levels` | `rx_cell` | sampler output level (V) | `v(rx_a[0])`, `v(rx_a[1])`, `v(rx_b[0])`, `v(rx_b[1])` read at one fixed sample instant t_s (B3) for each phase, with `pad` held at 0 and at 1 through t_s; a level that reaches its window only after t_s fails | `pad` driven full-swing 0/VDD, 20 ps transition (L2); `ph[k]` pulses and t_s per B3; 2 fF on each of the four outputs to VSS (L5) | §6 tuples | high ≥ 0.9·VDD, low ≤ 0.1·VDD |
| `a5-rx-input-threshold` | `rx_cell` | input-stage trip point (V) | DC sweep of `v(pad)`; trip = `v(pad)` at which the input-stage output (internal net `i2` of `design/netlist/rx_cell.sp`) crosses VDD/2, mismatch-free | `pad` DC source; sampler quiescent | §6 tuples | VDD/2 ± 0.1·VDD |
| `a6-rx-sampler-offset-sigma` | `rx_cell` | input-referred sampler offset, 3σ (V) | **statistical**. Per draw, `ph[0]` held high (sampler transparent), `pad` swept: offset = `v(pad)` at which `rx_a[0]` crosses VDD/2, minus the a5 trip. The limit bounds 3·std of the offset distribution over draws, not a corner reading | same as a4 (including L5 and B3), per-draw mismatch per M1 | §6 tuples; ≥ 100 draws per tuple, recorded seed, nominal control | 3σ ≤ 0.1·VDD |

### Clock cells (measured by #279)

| ID | Cell | Quantity (unit) | Measurement definition | Stimulus / load | PVT | Proposed limit |
|---|---|---|---|---|---|---|
| `a7-txclk-duty` | `tx_clk_cell` | pad duty-cycle error (ps) | high time of `v(pad)` (50% VDD rising crossing to the next 50% VDD falling crossing) minus T/2, averaged over ≥ 10 periods, `fwd_en` high | `clk` at the forwarded-clock rate, 50% duty, 20 ps transition (L3); 2 fF on `pad` (L4) | §6 tuples | within ± 12.5 ps (target) / ± 50 ps (fallback) |
| `a8-txclk-delay` | `tx_clk_cell` | clk-to-pad delay (ps) | 50% VDD crossing of `v(clk)` to the 50% VDD crossing of `v(pad)`, measured separately for the rising and for the falling edge; the limit bounds the worse of the two | same as a7 | §6 tuples | ≤ 62.5 ps (target) / 250 ps (fallback) |
| `a9-rxclk-duty` | `rx_clk_cell` | forwarded duty-cycle error (ps) | high time of `v(rx_clk)` (50% VDD rising crossing to the next 50% VDD falling crossing) minus T/2 minus the high time of `v(pad)` measured the same way minus T/2 (the source's own duty error), averaged over ≥ 10 periods | `pad` driven as a7 drives `clk` (L3); 2 fF on `rx_clk` to VSS (L6) | §6 tuples | within ± 12.5 ps (target) / ± 50 ps (fallback) |
| `a10-rxclk-delay` | `rx_clk_cell` | pad-to-rx_clk delay (ps) | 50% VDD crossing of `v(pad)` to the 50% VDD crossing of `v(rx_clk)`, measured separately for the rising and for the falling edge; the limit bounds the worse of the two | same as a9 | §6 tuples | ≤ 62.5 ps (target) / 250 ps (fallback) |

**PVT binding.** Every row binds the section 6 corner tuples — TT 0.70 V / 25 °C, SS 0.63 V /
100 °C, FF 0.77 V / 0 °C (the ratified Liberty headers) — on the decision 0010 model cards
(`7nm_{TT,SS,FF}_160803.pm`, lambdapdk v0.2.17). The rows bind the section 6 tuples, not decision
0010's flat 0.7 V / 25 °C, so the analog matrix and the digital STA corner set agree; 0010's runs
remain the historical functional baseline. The statistical row binds all three tuples because its
evidence must be combined with, not instead of, the process corners (tier item-6 discipline).

**Intended bench paths** (created by the consumers; names distinct from the historical reports):
`design/sim/<cell>.rows.tb.sp` plus `design/sim/<cell>.rows.sim.json`, reporting to
`sim/<cell>.rows.batch.report.json`, for `tx_cell` and `rx_cell` (#278) and for `tx_clk_cell` and
`rx_clk_cell` (#279).

## Budget trace and assumption ledger

Section 2 fixes: 16 GT/s → 62.5 ps per transfer (UI), 4 GHz parallel → 250 ps cycle, 4:1 →
4 × 62.5 ps = 250 ps, consistent; fallback 4 GT/s → 250 ps UI, 1 GHz → 1000 ps, 4 × 250 ps.

| Allocation | Target | Fallback | Source |
|---|---|---|---|
| UI | 62.5 ps | 250 ps | ratified §2 |
| Parallel cycle | 250 ps | 1000 ps | ratified §2 |
| Forwarded-clock period T | 250 ps (4 GHz) | 1000 ps (1 GHz) | assumption C1 |
| TX pad transition (a2) | 0.25·UI = 15.625 ps | 62.5 ps | UI × assumption F1 |
| TX cell delay (a3) | 0.5·UI = 31.25 ps | 125 ps | UI × assumption F2 |
| Clock-cell delay (a8, a10) | 0.25·T = 62.5 ps | 250 ps | T × assumption F3 |
| Duty error (a7, a9) | 5% of T = 12.5 ps | 50 ps | §5's 5%-of-period figure, reused as F4 |
| Level windows (a1, a4) | 0.9·VDD / 0.1·VDD | same | decision 0010's levels (F5) |
| RX trip window (a5) | VDD/2 ± 0.1·VDD | same | assumption F6 |
| Offset statistic (a6) | 3σ ≤ 0.1·VDD | same | assumption F7 |

- **C1 (forwarded-clock rate).** The spec names the forwarded-clock lane (§1) but not its rate. The
  drawn 4-phase sampler (`rx_cell` `ph[0..3]`) takes one sample per phase per period, so at
  16 GT/s the forwarded clock runs at the parallel rate, 4 GHz. Proposed; ratification should state
  the rate in §2.
- **F1-F3 (fractions).** Quarter-UI transition, half-UI cell delay, quarter-period clock-cell
  delay. The fractions are engineering assumptions, not ratified numbers; each leaves the remainder
  of its budget to the synthesized path and the sampling window.
- **F4 (duty).** §5 fixes 5 percent of the period (12.5 ps at 4 GHz) as the parallel clock's setup
  uncertainty; the same figure is proposed as the forwarded clock's duty budget. Reuse, not
  derivation.
- **F5 (levels).** Decision 0010's functional assertion levels, already the accepted logic-level
  criterion.
- **F6/F7 (windows).** A symmetric front end should trip near mid-supply and resolve small inputs;
  10 percent of VDD bounds both the nominal trip window and the 3σ offset. Assumptions.

Loads, voltages, stimulus and conventions the ratified inputs do not determine:

- **B1 (TX stimulus ramps).** Every ideal TX data and select source is a piecewise-linear step with
  a 10 ps 0-100% ramp, the edge time of the historical bench `design/sim/tx_cell.tb.sp`. Edge time
  is part of the row: a slower ramp changes the measured pad slew and delay, so a bench may not
  substitute one. The other three data inputs carry the complement of the selected input.
- **B2 (TX polarity).** `tx_cell` inverts: three inversions follow the 4:1 pass-gate mux, so the
  expected `pad` level is NOT the selected input (a1: selected 0 → pad ≥ 0.9·VDD, selected 1 →
  pad ≤ 0.1·VDD), as in the historical bench.
- **B3 (RX sampling plan).** Each `ph[k]` is a pulse with 10 ps ramps, high (latch transparent) for
  one UI (62.5 ps target / 250 ps fallback) and closing on its falling edge; the four phases are
  exercised one at a time. `pad` settles at its level at least 2 UI before the active `ph[k]` falling
  edge and holds through t_s. The sample instant t_s is the 50% VDD crossing of that falling edge plus
  one UI. Outputs map to phases as in `design/gen_cells.py` (d0..d3 → `rx_a[0]`, `rx_b[0]`,
  `rx_a[1]`, `rx_b[1]`), not by port order.

- **L1 (TX data bench load).** 2 fF on `pad` to VSS — decision 0010's TX bench load, kept. One TX
  bump per lane cell (§3; the bump maps `layout/bump_map_{target,fallback}.csv` carry
  `lane,signal,x_um,y_um` and fix the geometry, not a capacitance).
- **L2 (RX data stimulus).** Ideal source on `pad`, full swing 0/VDD, 20 ps transition. §5's 20 ps
  input-transition limit is the core-side precedent, not a ratified bump-side input.
- **L3 (clock stimulus).** Ideal source at the forwarded-clock rate (C1), 50% duty, 20 ps
  transition, at `clk` (a7-a8) or `pad` (a9-a10).
- **L4 (TX clock bench load).** 2 fF on `pad`, mirroring L1 for the clock bump.
- **L5 (RX sampler output load).** 2 fF to VSS on each of `rx_a[0..1]` and `rx_b[0..1]`, the load
  of the historical bench `design/sim/rx_cell.tb.sp`, kept as an assumption: no ratified input fixes
  the core-side capacitance a sampler output drives.
- **L6 (RX clock output load).** 2 fF to VSS on `rx_clk`, the load of
  `design/sim/rx_clk_cell.tb.sp`, kept on the same basis.
- **M1 (assumed mismatch model for a6).** ASAP7 ships no mismatch models. Assumed: independent
  per-transistor Gaussian Vt offset, σ_Vth = A_VT/√(W·L) with A_VT = 2 mV·µm, on every device of
  `rx_cell`; all else at the §6 tuple. The label "assumed" is part of the row. Upstream
  2AMLogic/klayout-tools#5486 (`klt sim` monte_carlo mismatch curated to two PDK families) may
  block the campaign for ASAP7; #278 records the probe. Sample count ≥ 100 per tuple, recorded
  seed, deterministic nominal control.

## Ratification delta (nothing below is done in this PR)

**Preamble.** Ratification amends this sentence of the `spec/ucie-phy.md` preamble:

> Every row is a layout, DRC, LVS or timing target checked by a tool run against the pinned ASAP7
> source (`asap7-bringup.md`).

Proposed replacement:

> Every row is a layout, DRC, LVS, timing or cell-level circuit-simulation target checked by a tool
> run against the pinned ASAP7 source (`asap7-bringup.md`). The analog rows are cell-level simulated
> targets against a predictive model; no row is a channel, eye, jitter or link-margin claim.

**Decisions 0006 and 0008.** Both self-withdraw on a new statistical row: 0006 ("a new statistical
row would withdraw this record") and 0008 ("A future ratified decision may add analog performance
rows; that would withdraw this record"). Ratification replaces them with this record at status
accepted (with the operator's amendments, if any): 0006's "no ratified spec row is statistical"
becomes false for the analog rows — its digital claim stands, every digital row of sections 1-7
remains deterministic — and 0008's route-B analog declaration retires, the analog partition then
needing Monte Carlo evidence per the ruling on 2AMLogic/klayout-tools#4183.

**The digital-only item 6 declaration, probed.** Question: at the repo pin, does
`klt signoff --manifest` still grade `6.digital` `not_applicable` once the spec carries a
statistical row bound to the analog partition? **No.** Recorded run, on a disposable copy of the
repository (a fresh clone; nothing committed as a record of the block):

- Command: `uvx --from "klayout-tools==0.9.2" klt signoff --manifest manifests/asap7-ucie-phy.json --format json`
- Version: klt 0.9.2 (the `.github/klt-version` pin); grading ruleset
  `sha256:2b5ecfa0c14c8cde59e16d6955130ba040938a82e42b77381d5c355fdcb67af0`, identical in baseline
  and variants.
- Baseline: the fresh run on the untouched copy reproduces the committed verdict of record exactly
  (11 met, 1 not applicable; items 5, 6, 7 analog `unmet / no_evidence`; `6.digital`
  `not_applicable`).
- Changed inputs (variant A): the copy's `manifests/spec-rows.json` gains
  `{"id": "a6-rx-sampler-offset-sigma"}`; the copy's `manifests/item6-na-statement.json` gains the
  matching statement row; both content hashes refreshed in the copy's block manifest, so a stale
  input cannot explain the outcome.
- Result: `6.digital` flips to `unmet`, reason `not_applicable_statistical_row`, detail
  `{"row": "a6-rx-sampler-offset-sigma", "field": "id", "document": "spec"}` plus the
  `reviewed_not_statistical` waiver hint; every other item unchanged. Variant B — all ten rows
  added, hashes refreshed — grades identically.
- Reading: the refusal is spec-global. The not-applicable scan refuses when any row of the one
  cited spec is statistical, with no partition scoping, and the `reviewed_not_statistical` waiver
  asserts a row is *not* statistical, so it cannot honestly carry a6. This is
  2AMLogic/klayout-tools#6938 (open as of 2026-11-20), already filed generically upstream with
  0.8.0 and 0.9.2 observations; this probe re-confirms it at this repo's pin, so no new upstream
  issue is filed.
- Consequence: ratification must withdraw the manifest's `6.digital` `not_applicable` entry (or
  accept `6.digital` `unmet / not_applicable_statistical_row` until #6938 lands a per-partition
  form). Keeping the entry as-is is not an option: the statement "no row is statistical" is false
  the day a6 is ratified, and the grader refuses it. The operator decides in the follow-up.

**Bound-record refresh.** Ratification refreshes `manifests/spec-rows.json` (26 → 36 rows, the ten
a-ids, source re-pinned to the amended spec commit) and retires or rewrites
`manifests/item6-na-statement.json` (its claim covers every spec row, and with a6 present it can no
longer be honestly written in the form the `not_applicable` grade requires — see the probe). The
verdict of record is regenerated after both.

**Gap declarations at 0.9.2, probed.** Also on the disposable copy: a top-level `spec_rows` key
carrying `{"id": ..., "gap": ...}` rows for `5.analog` and `6.analog`, with no citation, now grades
`unmet / partial_coverage` with the gaps listed under `detail.declared_gaps` — the klt 0.8.0
behavior recorded in decisions 0006/0008 and the two gap files ("declaration ignored without a
citation", 2AMLogic/klayout-tools#4190) is gone at this pin. The gap files' not-in-manifest
rationale is corrected in this PR to the pin's actual behavior; the declarations stay out of the
manifest of record because the rows exist only here (`ratified: false` spec_rows rows keep evidence
provisional at this pin) and because the verdict of record must keep grading
`unmet / no_evidence`.

## What this record does not do

- It ratifies nothing. Merging this PR leaves this decision proposed; every limit above binds only
  after the operator follow-up (#279) ratifies or amends it.
- It edits no ratified file: `spec/ucie-phy.md`, `manifests/spec-rows.json`,
  `manifests/item6-na-statement.json` and the manifest's item 5/6/7 entries are untouched; the
  verdict of record still reproduces and items 5, 6, 7 analog still grade `unmet / no_evidence`.
- It claims no measurement and makes no delay, rate, eye, jitter, power or link-margin statement:
  every figure above is a proposed limit derived from ratified inputs or a labelled assumption,
  against a predictive PDK, and this block is never fabricated.

## Consequences

The two gap declarations are corrected to the current blocker and pin
(`manifests/item5-analog-gap.json`, `manifests/item6-analog-gap.json`; status and expected grade
unchanged). #278 and #279 measure the rows above provisionally, keep the limits fixed, commit any
miss as a failing measurement with a bounded design-iteration issue, and hand the ratification
request to the operator.
