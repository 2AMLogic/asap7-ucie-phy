* rx_cell bench for the proposed data-cell rows a4-a6 (spec/decisions/0013-analog-spec-rows.md).
* Supply-referenced by construction: the pad and ph[0..3] sources are written by
* the request's declarative stimulus block (rx_cell.rows.<tuple>.sim.json) with
* levels that are fractions of corners.supply_v.vdd, so no input amplitude is
* hardcoded in this file and the stimulus swing always equals the tuple supply.
* Vdd itself is altered per corner by klt sim from corners.supply_v.
* Stimulus per 0013: L2 (pad full-swing, 20 ps transition) and B3 (ph pulses,
* 10 ps ramps, one phase at a time; sample instant t_s per trial). Loads L5:
* 2 fF on each sampler output. a5/a6 read the internal input-stage output as
* v(xdut.i2) / the sampler output as v(rxa0) per 0013.
* Logic-level predecessor: rx_cell.tb.sp (kept, unmodified).
.include rx_cell.osdi.sp
Vdd vdd 0 0.7
Xdut pad ph0 ph1 ph2 ph3 rxa0 rxa1 rxb0 rxb1 vdd 0 rx_cell
Cload0 rxa0 0 2f
Cload1 rxa1 0 2f
Cload2 rxb0 0 2f
Cload3 rxb1 0 2f
