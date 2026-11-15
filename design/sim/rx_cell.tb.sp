* rx_cell logic-level testbench (ASAP7 RVT, BSIM-CMG via OSDI). Run through klt sim; see rx_cell.sim.json.
* Phase k of the sampler maps to output k per design/gen_cells.py (order d0,d1,d2,d3 ->
* rx_a[0],rx_b[0],rx_a[1],rx_b[1]), NOT to the k-th output port. Ideal PWL drives on pad and
* ph[0..3] and a 2 fF load on each output keep this a logic-level check only: no delay, rate,
* eye or jitter is measured or claimed.
* 12 assertions: an init window opens all four phases with pad high (no defined initial latch
* state), then four mutually distinguishing values are loaded one phase at a time (ph0:1, ph1:0,
* ph2:1, ph3:0), all phases close, and all four outputs are sampled with pad at the opposite
* level (expect 1,0,1,0 - a closed latch must not follow pad). The complement load (0,1,0,1) and
* a second all-output sample assert every output at both levels, so a swapped ph1/ph2 mapping
* fails instead of passing on a symmetric pattern. One transparency assertion per slice samples
* an output while its own phase is high at the level that latch does not hold.
.include rx_cell.osdi.sp
Vdd vdd 0 0.7
Vpad pad 0 pwl(0p 0.7 600p 0.7 610p 0 900p 0 910p 0.7 1200p 0.7 1210p 0 2100p 0 2110p 0.7 2400p 0.7 2410p 0 2700p 0 2710p 0.7 3600p 0.7 3610p 0 3900p 0 3910p 0.7 4200p 0.7 4210p 0 4500p 0)
Vph0 ph0 0 pwl(0p 0.7 290p 0.7 300p 0 310p 0.7 590p 0.7 600p 0 1800p 0 1810p 0.7 2090p 0.7 2100p 0 3300p 0 3310p 0.7 3590p 0.7 3600p 0)
Vph1 ph1 0 pwl(0p 0.7 290p 0.7 300p 0 600p 0 610p 0.7 890p 0.7 900p 0 2100p 0 2110p 0.7 2390p 0.7 2400p 0 3600p 0 3610p 0.7 3890p 0.7 3900p 0)
Vph2 ph2 0 pwl(0p 0.7 290p 0.7 300p 0 900p 0 910p 0.7 1190p 0.7 1200p 0 2400p 0 2410p 0.7 2690p 0.7 2700p 0 3900p 0 3910p 0.7 4190p 0.7 4200p 0)
Vph3 ph3 0 pwl(0p 0.7 290p 0.7 300p 0 1200p 0 1210p 0.7 1490p 0.7 1500p 0 2700p 0 2710p 0.7 2990p 0.7 3000p 0 4200p 0 4210p 0.7 4490p 0.7 4500p 0)
Xdut pad ph0 ph1 ph2 ph3 rxa0 rxa1 rxb0 rxb1 vdd 0 rx_cell
Cload0 rxa0 0 2f
Cload1 rxa1 0 2f
Cload2 rxb0 0 2f
Cload3 rxb1 0 2f
