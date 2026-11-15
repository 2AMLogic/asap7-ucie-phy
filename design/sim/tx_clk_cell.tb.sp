* tx_clk_cell logic-level testbench (ASAP7 RVT, BSIM-CMG via OSDI). Run through klt sim; see tx_clk_cell.sim.json.
* Full (clk, fwd_en) truth table: pad = clk AND fwd_en (nand2 then three inverters), held low
* when fwd_en=0. clk toggles across the fwd_en=0 window so the gated-off case is driven, not
* idle. Ideal PWL drives and a 2 fF load on pad keep this a logic-level check only: no delay,
* rate, eye or jitter is measured or claimed.
.include tx_clk_cell.osdi.sp
Vdd vdd 0 0.7
Vclk clk 0 pwl(0p 0 600p 0 610p 0.7 850p 0.7 860p 0 1100p 0 1110p 0.7 1180p 0.7 1190p 0 1800p 0 1810p 0.7 2400p 0.7)
Vfwd fwd_en 0 pwl(0p 0 1800p 0 1810p 0.7 2400p 0.7)
Xdut clk fwd_en pad vdd 0 tx_clk_cell
Cload pad 0 2f
