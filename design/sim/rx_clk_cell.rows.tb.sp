* rx_clk_cell bench for the proposed clock rows a9-a10 (spec/decisions/0013-analog-spec-rows.md).
* Supply-referenced by construction: the pad source is written by the request's
* declarative stimulus block (rx_clk_cell.rows.<tuple>.sim.json) with levels that
* are fractions of corners.supply_v.vdd, so no input amplitude is hardcoded in
* this file and the stimulus swing always equals the tuple supply. Vdd itself is
* altered per corner by klt sim from corners.supply_v.
* Stimulus per 0013 L3 (forwarded-clock rate C1: 4 GHz, T = 250 ps, 50% duty,
* 20 ps ramps) on pad, standing in for the a7 pad waveform per the a9 definition.
* Load L6: 2 fF on rx_clk to VSS.
* Logic-level predecessor: rx_clk_cell.tb.sp (kept, unmodified).
.include rx_clk_cell.osdi.sp
Vdd vdd 0 0.7
Xdut pad rx_clk vdd 0 rx_clk_cell
Cload rx_clk 0 2f
