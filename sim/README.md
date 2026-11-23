# sim

Holds **timing (STA) results** for the lane datapath and for characterized cell models, plus
**circuit-simulation reports** in three groups: the logic-level functional runs of all four drawn
cells (the historical baseline), the **proposed data-cell row measurements** of decision 0013
(issue #278), and the **proposed clock-cell row measurements** of the same decision (issue #279),
plus the single-cell **`klt pex` probe** record (#279). `tx_cell` is the run recorded in
`../spec/decisions/0010-analog-simulation-flow.md` (which supersedes the ngspice 42 blocker in
decision 0003); the other three extend that same route to the cells 0010 named as not covered.
Decks and requests: `../design/sim/` (`<cell>.tb.sp`, `<cell>.sim.json`, `<cell>.osdi.sp`; rows
benches `<cell>.rows.tb.sp`, `<cell>.rows.<tuple>.sim.json`, `<cell>.a6.mc.sim.json`). The OSDI
module is built locally into `sim/build/` (gitignored), not committed. Every result here is a
tool result against a predictive model.

## Logic-level baseline (decision 0010, historical — unchanged)

Every assertion is a logic level only (above 0.9 VDD or below 0.1 VDD at a stated sample point):
no delay, rate, eye, jitter or power claim comes from these runs.

| Report | Cell | Assertions | Batch job |
|---|---|---|---|
| `tx_cell.batch.report.json` | `tx_cell` (2:1 mux + driver) | 8 meas × 3 corners = 24, all pass | `klt-sim-7911111351c7` |
| `rx_cell.batch.report.json` | `rx_cell` (input stage + 4-phase sampler) | 12 meas × 3 corners = 36, all pass | `klt-sim-b75bd058b119` |
| `tx_clk_cell.batch.report.json` | `tx_clk_cell` (fwd-clock gate + driver) | 4 meas × 3 corners = 12, all pass | `klt-sim-992dfd8a081f` |
| `rx_clk_cell.batch.report.json` | `rx_clk_cell` (fwd-clock input buffer) | 2 meas × 3 corners = 6, all pass | `klt-sim-53d8e84389e0` |

These four reports are the append-only baseline: byte-identical to the build base of issue #278.

## Proposed data-cell rows a1-a6 (decision 0013, issue #278) — provisional

**Every figure in this section is provisional against the predictive model, and the rows
themselves are still proposed** (decision 0013 is not ratified; no bound here grades anything).
Rows a1-a3 measure `tx_cell`, a4-a6 `rx_cell`, on the decision-0010 batch flow (ngspice 47 via
`klt sim`, OSDI BSIM-CMG) at the three matched PVT tuples 0013 binds — TT 0.70 V / 25 °C,
SS 0.63 V / 100 °C, FF 0.77 V / 0 °C — with per-tuple stimulus swing taken from the tuple supply
(declarative `stimulus` levels as `frac_of` fractions of `corners.supply_v.vdd`), 10 ps data/select
ramps (B1), 20 ps pad transitions (L2), the B3 sampling plan (ph pulses, one UI, t_s = falling-edge
50 % + one UI), 2 fF loads (L1/L5), and pad = NOT selected input (B2). Each tuple runs as its own
batch-set member request (`<cell>.rows.<tuple>.sim.json`) because file-scope `.meas` thresholds,
`.dc` sweep endpoints and `measurements[].limits` are parse-time literals that cannot scale with a
swept supply; `corners.units` (explicit non-crossed point list) exists at the pin and was checked,
and the limits side of that is filed generically upstream as 2AMLogic/klayout-tools#7370.

Reports of record: the aggregate envelope `tx_cell.rows.batch.report.json` /
`rx_cell.rows.batch.report.json` (one `klt sim --batch-set` per cell) plus the member reports the
envelopes reference, committed as `<cell>.rows.<tuple>.batch.report.json`. Each envelope's
per-request `report` field is the repo-relative path of that committed member report
(`sim/<cell>.rows.<tuple>.batch.report.json`). klt emits that field as an absolute path into the
submitting client's scratch directory (2AMLogic/klayout-tools#7381), so the committed envelopes
carry repo-relative paths rather than the value klt writes as-run.

Environment (identical across all six member reports): engine ngspice 47, client klt 0.9.2
(`.github/klt-version` pin), runner klt 0.9.0 (batch fleet), model library
`design/sim/asap7_bsimcmg.lib` sha256 `c0478207ccf23686f2585c91f45d5e54d988560397ed8516219ee45b099c0280`
(lambdapdk v0.2.17 cards, per decision 0010), OSDI module `bsimcmg.osdi` sha256
`4e755d14e901a84600124be5cb73e36302117b6cfc694e52ffc17640945cd9e3` (decision 0010's reference
build, rebuilt locally with klt's `fetch-asap7-sim-toolchain.sh` and hash-checked).

### Row-to-report table

Worst case per row and tuple over the row's measurement set (a1/a4: 8 measurements; a2: 8; a3: 16;
a5: 1). Verdicts are recomputed from the reported value against the proposed bound; the member
reports also carry tool-side limits (target bounds; per-tuple literals). "Target" is the 16 GT/s
budget, "fallback" the 4 GT/s budget (0013 § budget trace).

| Row | Tuple | Worst value | Proposed bound | Target | Fallback | Report / job |
|---|---|---|---|---|---|---|
| `a1-tx-pad-levels` | TT | hi 0.700 V / lo 0.11 µV | hi ≥ 0.63, lo ≤ 0.07 | pass | pass | `tx_cell.rows.tt.batch.report.json` / `klt-sim-5c8fb30de0ff` |
| | SS | hi 0.630 V / lo 3.7 µV | hi ≥ 0.567, lo ≤ 0.063 | pass | pass | `tx_cell.rows.ss.batch.report.json` / `klt-sim-2a9d6fbe11f7` |
| | FF | hi 0.770 V / lo 26 nV | hi ≥ 0.693, lo ≤ 0.077 | pass | pass | `tx_cell.rows.ff.batch.report.json` / `klt-sim-4ccacb054145` |
| `a2-tx-pad-transition` | TT | 4.14 ps (s1 rise) | ≤ 15.625 ps / 62.5 ps | pass | pass | as a1, per tuple |
| | SS | 6.56 ps (s2 rise) | ≤ 15.625 ps / 62.5 ps | pass | pass | |
| | FF | 2.93 ps (s1 rise) | ≤ 15.625 ps / 62.5 ps | pass | pass | |
| `a3-tx-mux-to-pad-delay` | TT | 24.65 ps (`a3_s1f_pr`) | ≤ 31.25 ps / 125 ps | pass | pass | as a1, per tuple |
| | SS | **34.69 ps (`a3_s1f_pr`)** | ≤ 31.25 ps / 125 ps | **fail** | pass | design iteration: #297 |
| | FF | 19.12 ps (`a3_s1f_pr`) | ≤ 31.25 ps / 125 ps | pass | pass | |
| `a4-rx-sampler-levels` | TT | hi 0.69999 V / lo 0.21 µV | hi ≥ 0.63, lo ≤ 0.07 | pass | pass | `rx_cell.rows.tt.batch.report.json` / `klt-sim-4ebeb2c1b436` |
| | SS | hi 0.62871 V / lo 31 µV | hi ≥ 0.567, lo ≤ 0.063 | pass | pass | `rx_cell.rows.ss.batch.report.json` / `klt-sim-4d9e4239612d` |
| | FF | hi 0.77000 V / lo 35 nV | hi ≥ 0.693, lo ≤ 0.077 | pass | pass | `rx_cell.rows.ff.batch.report.json` / `klt-sim-dab12e22e18b` |
| `a5-rx-input-threshold` | TT | 0.3475 V | 0.28-0.42 (VDD/2 ± 0.1 VDD) | pass | pass | as a4, per tuple |
| | SS | 0.3225 V | 0.252-0.378 | pass | pass | |
| | FF | 0.3760 V | 0.308-0.462 | pass | pass | |
| `a6-rx-sampler-offset-sigma` | all | **not measurable at the pin** | 3σ ≤ 0.1·VDD | — | — | refusal recorded below |

The single miss: **a3 at SS** — the two `sel1` select-step paths (`a3_s1r_pf` 34.08 ps,
`a3_s1f_pr` 34.69 ps) exceed the 31.25 ps target and clear the 125 ps fallback; every data-input
path at SS clears the target (worst 28.6 ps). Committed as measured; bounded design-iteration
issue: #297. The bounds are unchanged from 0013.

a5 is measured in the same request as a4 via `analysis_steps`: a transient step (the a4 sampler
trials) then a `reset` DC-sweep step of `pad` (0 → VDD, 1 mV steps) reading the internal
input-stage output `v(xdut.i2)` per 0013; the trip is where `v(xdut.i2)` crosses VDD/2.

### The statistical row a6: refused at the pin, no corner substitution

`a6-rx-sampler-offset-sigma` is **statistical** (3σ of the input-referred sampler offset over ≥ 100
mismatch draws per tuple under assumed model M1: independent per-transistor Gaussian Vt offset,
σ_Vth = A_VT/√(W·L), A_VT = 2 mV·µm, on every device of `rx_cell`). A corner reading cannot
establish it (0013), so none is substituted.

Attempted as declared in `design/sim/rx_cell.a6.mc.sim.json` — TT member of the three-tuple
campaign, `monte_carlo: {n: 100, seed: 20261123, vary: mismatch, mismatch_scale: 1.0}`, per-draw
measurement the `rx_a[0]` VDD/2 crossing with `ph[0]` held high (offset = crossing − a5 trip).
Refused at request validation, before any corner ran, with the exact output:

```
$ uvx --from "klayout-tools==0.9.2" klt sim design/sim/rx_cell.a6.mc.sim.json --backend local
klt sim: request.monte_carlo.mismatch_scale is only supported for PDK families with a verified
multiplicative mismatch switch (gf180mcu, sky130); models.pdk None resolves to family None
(exit 1, klt 0.9.2)
```

This is 2AMLogic/klayout-tools#5486 (open as of 2026-11-23): both mismatch-control mechanisms
resolve the PDK's mismatch switch from a table curated to sky130 and gf180mcu, and ASAP7's
vendored BSIM-CMG cards ship no mismatch section at all — the third mechanism (`monte_carlo.injected`)
writes `mc_inj_*` parameters a read-only netlist must itself reference. **a6 is therefore not
measurable at the repository pin; its row reads "no measured statistic", linking #5486.** The
assumed model M1, the declared seed (20261123) and the declared sample count (100 per tuple) are
recorded above for whenever the campaign becomes runnable.

### `klt yield` dry run at the pin

One dry run for the a6 row shape, recorded per the issue (synthetic placeholder samples — see the
`_probe_note` in `rx_cell.a6.yield-probe.samples.json`; no measured sample set exists):

```
$ uvx --from "klayout-tools==0.9.2" klt yield sim/rx_cell.a6.yield-probe.samples.json --format json
error: ... the klt_yield_native extension is not installed ... (exit 1, klt 0.9.2)
$ uvx --from "klayout-tools[yield]==0.9.2" klt yield sim/rx_cell.a6.yield-probe.samples.json --format json
```

The second invocation (version klt 0.9.2, `klt_yield_native` 0.1.0, Linux x86-64 prebuilt wheel)
succeeds: full output committed as `rx_cell.a6.yield-probe.report.json` — status `reported`
(no `target_yield` declared, so nothing fails), normal-delta and Clopper-Pearson yield estimates
with confidence intervals, Cpk/sigma-to-spec, and an explicit "N = 20 is insufficient for ±0.01"
sample-size verdict. Two caveats for the eventual a6 campaign: `klt yield` answers a **per-sample
yield fraction against min/max limits**, while row a6 bounds **3σ of the offset distribution** —
a different statistic (the report's `distribution.stddev` is the closer quantity) — and the probe
declares no `negative_control`, which a gradable campaign would need. The tool works at the pin;
the missing input is the refused Monte Carlo above.

## Proposed clock rows a7-a10 (decision 0013, issue #279) — provisional

**Every figure in this section is provisional against the predictive model, and the rows
themselves are still proposed** (decision 0013 is not ratified; no bound here grades anything).
Rows a7-a8 measure `tx_clk_cell`, a9-a10 `rx_clk_cell`, on the same decision-0010 batch flow
(ngspice 47 via `klt sim`, OSDI BSIM-CMG) at the three matched PVT tuples 0013 binds — TT
0.70 V / 25 °C, SS 0.63 V / 100 °C, FF 0.77 V / 0 °C — with per-tuple stimulus swing taken from
the tuple supply (declarative `stimulus` levels as `frac_of` fractions of `corners.supply_v.vdd`).
Stimulus per L3 at the target forwarded-clock rate (C1: 4 GHz, T = 250 ps, 50 % duty, 20 ps
ramps): `clk` driven for a7-a8 with `fwd_en` enabled once before the first measured period and
held high, `pad` driven for a9-a10; loads L4/L6: 2 fF on the measured output to VSS. The
`.meas` 50 % thresholds are VDD/2 per tuple (0.35 / 0.315 / 0.385 V). Each tuple runs as its own
batch-set member request (`<cell>.rows.<tuple>.sim.json`) for the same parse-time-literal reason
as a1-a6 (2AMLogic/klayout-tools#7370). Measured periods: clock cycles 4-13 (zero-based 3-12),
satisfing 0013's "averaged over ≥ 10 periods" after three settle cycles; tran 1p 3500p.

Reports of record: the aggregate envelopes `tx_clk_cell.rows.batch.report.json` /
`rx_clk_cell.rows.batch.report.json` (one `klt sim --batch-set` per cell) plus the member reports
the envelopes reference, committed as `<cell>.rows.<tuple>.batch.report.json` with repo-relative
`report` fields (2AMLogic/klayout-tools#7381, as for the data rows).

Environment (identical across all six member reports): engine ngspice 47, client klt 0.9.2
(`.github/klt-version` pin), runner klt 0.9.0 (batch fleet), model library
`design/sim/asap7_bsimcmg.lib` sha256 `c0478207ccf23686f2585c91f45d5e54d988560397ed8516219ee45b099c0280`
(lambdapdk v0.2.17 cards, per decision 0010). OSDI module `bsimcmg.osdi` sha256
`5d7425d56df0d1e14d6b95ce7ba9d5c71c309d603cf6ce4348bddaf72c294318`: rebuilt locally with klt's
`fetch-asap7-sim-toolchain.sh` from the same pinned source (VA-Models `6099b4e`) and compiler
(OpenVAF-Reloaded `osdi_0.4-153-g2e066436`) as decision 0010's reference module, but **not
bit-identical to it** (0010 records `4e755d14…`): the pinned-tag compiler binary fetched today
produces a different, itself-deterministic, module. It loads and preflights clean on ngspice 47,
and the `klt pex` probe below re-ran the committed `tx_cell` TT request with this module and
reproduced #278's committed a1-a3 TT values exactly at report precision — the recorded
cross-check that the two builds agree on the measured quantities.

### Row-to-report table

Worst case per row and tuple over the row's measurement set (a7: 10 periods; a8/a10: 10 periods
× 2 edge directions, worst edge; a9: 10 periods × both nets). Row verdicts are recomputed from
the reported values against the proposed bound per the 0013 definitions — the duty rows bound
the **average** high-time deviation, the delay rows the **worse** edge — while the member
reports carry tool-side per-measurement limits as target-bound guards (high time within
T/2 ± 12.5 ps per period; delay ≤ 62.5 ps). "Target" is the 16 GT/s budget, "fallback" the
4 GT/s budget (0013 § budget trace).

| Row | Tuple | Worst value | Proposed bound | Target | Fallback | Report / job |
|---|---|---|---|---|---|---|
| `a7-txclk-duty` | TT | −1.887 ps (avg high 123.113 ps) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `tx_clk_cell.rows.tt.batch.report.json` / `klt-sim-2205955c08e3` |
| | SS | −2.811 ps (avg high 122.189 ps) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `tx_clk_cell.rows.ss.batch.report.json` / `klt-sim-9cc2d7af0488` |
| | FF | −1.513 ps (avg high 123.487 ps) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `tx_clk_cell.rows.ff.batch.report.json` / `klt-sim-3f9aeb5c04d4` |
| `a8-txclk-delay` | TT | 21.885 ps (rising) | ≤ 62.5 ps / 250 ps | pass | pass | as a7, per tuple |
| | SS | 30.132 ps (rising) | ≤ 62.5 ps / 250 ps | pass | pass | |
| | FF | 17.058 ps (rising) | ≤ 62.5 ps / 250 ps | pass | pass | |
| `a9-rxclk-duty` | TT | +0.855 ps (rx 125.855, pad 125.000) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `rx_clk_cell.rows.tt.batch.report.json` / `klt-sim-b9d50476113a` |
| | SS | +1.288 ps (rx 126.288, pad 125.000) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `rx_clk_cell.rows.ss.batch.report.json` / `klt-sim-c496d86ceeb2` |
| | FF | +0.670 ps (rx 125.670, pad 125.000) | \|err\| ≤ 12.5 ps / 50 ps | pass | pass | `rx_clk_cell.rows.ff.batch.report.json` / `klt-sim-51491f26b46a` |
| `a10-rxclk-delay` | TT | 20.176 ps (falling) | ≤ 62.5 ps / 250 ps | pass | pass | as a9, per tuple |
| | SS | 27.467 ps (falling) | ≤ 62.5 ps / 250 ps | pass | pass | |
| | FF | 15.815 ps (falling) | ≤ 62.5 ps / 250 ps | pass | pass | |

All twelve row × tuple verdicts pass at both budgets: no miss, so unlike a3 at SS (#278) no
design-iteration issue is owed. a9's pad-side duty error — the source's own error the definition
subtracts — measured 0.000 ps at every tuple (ideal L3 source), so the transfer equals the
`rx_clk` duty error; both halves are measured and recorded per the definition.

## Single-cell `klt pex` probe on `tx_cell` (issue #279) — provisional

One pinned probe, recorded per the issue: can the extracted-versus-schematic route produce a
real single-cell delta at the repository pin? **Yes.** Full envelope committed as
`tx_cell.pex-probe.report.json`. Command of record (client klt 0.9.2, git `046ba74652fc`,
klayout 0.30.14, deck `asap7` content-hash
`sha256:5c58a50e5f6a9099810b3fde37eaa8d93b0897653cb6597a831baac1f5ebee76`, batch backend):

```
$ uvx --from "klayout-tools==0.9.2" klt pex layout/cells/tx_cell.gds \
      design/sim/tx_cell.rows.tt.sim.json --deck asap7 --top tx_cell \
      --pins 'tx_a[0],tx_a[1],tx_b[0],tx_b[1],sel1,sel2,pad,VDD,VSS' \
      --tie-net '\$39=VDD' --outdir design/pex279 \
      -o <scratch>/tx_cell.pex.spice --envelope-out <scratch>/tx_cell.pex.envelope.json \
      --backend batch --wait-for-capacity 600 --format json
status: pass   delta rows: 32 passed / 0 failed / 0 errored   (exit 0)
```

Outcome: all 32 delta rows of the TT `tx_cell` request (a1-a3) computed; worst degradation
**+6.358 %** (`a3_s1r_pf`, schematic 24.021 ps → extracted 25.549 ps; a1 ≤ +6.252 %, a2 ≤
+3.523 %). Extraction: 22 devices / 18 nets against the schematic's 22 (the LVS-matched pairing
of `evidence/item4-lvs/tx_cell.r2.request.json`), `parasitic_integrity` clean, `model_mismatch`
null, extracted legs BSIM-CMG-adapted (`extraction.netlist_adaptation:
asap7_bsimcmg.adapt_extracted_netlist`). Every number is a tool result against a predictive
model, and the run carries klt's asap7 fidelity warning verbatim (same-level coupled-wiring
delay error −97.8 % to −87.8 % versus the mom reference in the measured range — treat extracted
delay as a lower bound; `warnings[]` in the record).

Three limitations hit and cleared on the way, all recorded here because they bound any graded
item-7-analog campaign:

1. **First run: `pin_count_mismatch`** — flat extraction promotes the synthesized substrate net
   `vsubs` as a 10th top-level pin against the schematic's 9. Cleared with `--pins` (the
   documented demotion); the dctie resistor stays inside the `.SUBCKT` body.
2. **Second run: `singular_matrix` on the extracted leg** — the 11 PMOS bodies land on the
   anonymous, untied nwell net `\$39` (the reported-unbiased case of
   2AMLogic/klayout-tools#1983). Cleared with the documented `--tie-net '\$39=VDD'`, disclosed
   in the record as `body_bias.status: "tied"`; the name is per-extraction and must be re-read
   from `unbiased_nets` after any re-layout.
3. **`options.osdi_preload` is request-relative, and the swapped extracted-side request resolves
   it against the pex artifact root, not the request's directory** — the #1395 `models.lib`
   rewrite covers only `models.lib`. Worked around by placing `--outdir` two levels under the
   repo root so the relative path re-resolves to the same file; filed generically upstream as
   2AMLogic/klayout-tools#7485. The `--outdir design/pex279` in the command of record is that
   workaround (the directory is run scratch, removed after; the envelope records the committed
   request unmodified).

Two fields are sanitised in the committed envelope, both disclosed: `client_ngspice_binary`
dropped from both sides (decision 0012 §3, same as the rows records) and
`worker_environment.pdk` dropped from both sides — the remote-worker PDK-root observation trips
the changed-record lint because the #5133 skip is anchored at the envelope root and does not
know the pex envelope's `testbenches[].sides[].environment.remote.worker_environment` shape;
filed generically upstream as 2AMLogic/klayout-tools#7484.

Checks the issue named before filing anything new: #6559 (no runset-engine route, closed) does
**not** apply to this cell at the 0.9.2 pin — the curated `asap7` deck recognised all 22 FinFETs
(`model_mismatch: null`), so no runset engine was needed; #5494 (multi-top) is not exercised by
a single-cell probe; #5735 (anonymous-net handles, closed) was not hit — the measurements probe
top-level nets only; the one anonymous net that mattered (`\$39`) is exactly the documented
`--tie-net` case.

The probe is **not** graded evidence: it is one cell, one tuple (TT), the target-rate bench,
against rows that are still proposed. Item 7 analog evidence — the full four-cell campaign — is
assigned to the operator follow-up (#306), contingent on ratification.
