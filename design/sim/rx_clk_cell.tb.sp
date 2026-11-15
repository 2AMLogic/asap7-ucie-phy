* rx_clk_cell logic-level testbench (ASAP7 RVT, BSIM-CMG via OSDI). Run through klt sim; see rx_clk_cell.sim.json.
* Four-inverter buffer: rx_clk follows pad, non-inverting. Both levels are asserted because an
* odd-stage-count error inverts and a single level would not catch it. Ideal PWL drive and a
* 2 fF load on rx_clk keep this a logic-level check only: no delay, rate, eye or jitter is
* measured or claimed.
.include rx_clk_cell.osdi.sp
Vdd vdd 0 0.7
Vpad pad 0 pwl(0p 0 1200p 0 1210p 0.7 2400p 0.7)
Xdut pad rx_clk vdd 0 rx_clk_cell
Cload rx_clk 0 2f
