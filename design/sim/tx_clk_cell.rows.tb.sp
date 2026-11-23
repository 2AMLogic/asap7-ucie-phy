* tx_clk_cell bench for the proposed clock rows a7-a8 (spec/decisions/0013-analog-spec-rows.md).
* Supply-referenced by construction: the clk and fwd_en sources are written by the
* request's declarative stimulus block (tx_clk_cell.rows.<tuple>.sim.json) with
* levels that are fractions of corners.supply_v.vdd, so no input amplitude is
* hardcoded in this file and the stimulus swing always equals the tuple supply.
* Vdd itself is altered per corner by klt sim from corners.supply_v.
* Stimulus per 0013 L3 (forwarded-clock rate C1: 4 GHz, T = 250 ps, 50% duty,
* 20 ps ramps) on clk; fwd_en enabled once before the first clk edge and held
* high per the a7 definition. Load L4: 2 fF on pad to VSS.
* Logic-level predecessor: tx_clk_cell.tb.sp (kept, unmodified).
.include tx_clk_cell.osdi.sp
Vdd vdd 0 0.7
Xdut clk fwd_en pad vdd 0 tx_clk_cell
Cload pad 0 2f
