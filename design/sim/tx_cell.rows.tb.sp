* tx_cell bench for the proposed data-cell rows a1-a3 (spec/decisions/0013-analog-spec-rows.md).
* Supply-referenced by construction: every data/select source is written by the
* request's declarative stimulus block (tx_cell.rows.<tuple>.sim.json) with
* levels that are fractions of corners.supply_v.vdd, so no input amplitude is
* hardcoded in this file and the stimulus swing always equals the tuple supply.
* Vdd itself is altered per corner by klt sim from corners.supply_v.
* Stimulus per 0013 B1 (10 ps ramps) and B2 (pad = NOT selected input, three
* inversions after the 4:1 pass-gate mux); the other three data inputs carry
* the complement of the selected input. Load L1: 2 fF on pad to VSS.
* Logic-level predecessor: tx_cell.tb.sp (kept, unmodified).
.include tx_cell.osdi.sp
Vdd vdd 0 0.7
Xdut a0 a1 b0 b1 sel1 sel2 pad vdd 0 tx_cell
Cload pad 0 2f
