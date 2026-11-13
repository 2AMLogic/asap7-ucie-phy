# sim

Holds **timing (STA) results** for the lane datapath and for characterized cell models, plus one
**circuit-simulation report**: `tx_cell.batch.report.json`, a logic-level functional run of the drawn
`tx_cell` at TT/SS/FF on ngspice 47 via the batch fleet (`../spec/decisions/0010-analog-simulation-flow.md`,
which supersedes the ngspice 42 blocker in decision 0003). Deck and request: `../design/sim/`. The OSDI
module is built locally into `sim/build/` (gitignored), not committed. The run makes no delay, rate,
eye or jitter claim; the other cells have no circuit-simulation result. Every result here is a tool
result against a predictive model.
