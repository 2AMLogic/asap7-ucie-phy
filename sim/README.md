# sim

Holds **timing (STA) results** for the lane datapath and for characterized cell models, plus four
**circuit-simulation reports**: logic-level functional runs of all four drawn cells
(`tx_cell`, `rx_cell`, `tx_clk_cell`, `rx_clk_cell`) at TT/SS/FF on ngspice 47 via the batch fleet.
`tx_cell` is the run recorded in `../spec/decisions/0010-analog-simulation-flow.md` (which
supersedes the ngspice 42 blocker in decision 0003); the other three extend that same route to the
cells 0010 named as not covered — their decks and reports are listed below, and no decision record
amends 0010 here. Decks and requests: `../design/sim/` (`<cell>.tb.sp`, `<cell>.sim.json`,
`<cell>.osdi.sp`). The OSDI module is built locally into `sim/build/` (gitignored), not committed.
Every assertion is a logic level only (above 0.9 VDD or below 0.1 VDD at a stated sample point):
no delay, rate, eye, jitter or power claim comes from these runs. Every result here is a tool
result against a predictive model.

| Report | Cell | Assertions | Batch job |
|---|---|---|---|
| `tx_cell.batch.report.json` | `tx_cell` (2:1 mux + driver) | 8 meas × 3 corners = 24, all pass | `klt-sim-7911111351c7` |
| `rx_cell.batch.report.json` | `rx_cell` (input stage + 4-phase sampler) | 12 meas × 3 corners = 36, all pass | `klt-sim-b75bd058b119` |
| `tx_clk_cell.batch.report.json` | `tx_clk_cell` (fwd-clock gate + driver) | 4 meas × 3 corners = 12, all pass | `klt-sim-992dfd8a081f` |
| `rx_clk_cell.batch.report.json` | `rx_clk_cell` (fwd-clock input buffer) | 2 meas × 3 corners = 6, all pass | `klt-sim-53d8e84389e0` |

