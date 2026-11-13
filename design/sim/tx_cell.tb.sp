* tx_cell logic-level testbench (ASAP7 RVT, BSIM-CMG via OSDI). Run through klt sim; see tx_cell.sim.json.
* Eight 300 ps phases. Phase k selects input s=k/2 (sel1=s&1, sel2=s>>1); the selected input
* carries p=k%2 and the other three carry 1-p, so a wrong mux path inverts the expected level.
* Expected pad = NOT p (three inversions after the 4:1 pass-gate mux). Logic levels only:
* no delay, rate, eye or jitter is measured or claimed.
.include tx_cell.osdi.sp
Vdd vdd 0 0.7
Vsel1 sel1 0 pwl(0p 0 600p 0 610p 0.7 1200p 0.7 1210p 0 1800p 0 1810p 0.7 2400p 0.7)
Vsel2 sel2 0 pwl(0p 0 1200p 0 1210p 0.7 2400p 0.7)
Va0 a0 0 pwl(0p 0 300p 0 310p 0.7 900p 0.7 910p 0 1200p 0 1210p 0.7 1500p 0.7 1510p 0 1800p 0 1810p 0.7 2100p 0.7 2110p 0 2400p 0)
Va1 a1 0 pwl(0p 0.7 300p 0.7 310p 0 900p 0 910p 0.7 1500p 0.7 1510p 0 1800p 0 1810p 0.7 2100p 0.7 2110p 0 2400p 0)
Vb0 b0 0 pwl(0p 0.7 300p 0.7 310p 0 600p 0 610p 0.7 900p 0.7 910p 0 1500p 0 1510p 0.7 2100p 0.7 2110p 0 2400p 0)
Vb1 b1 0 pwl(0p 0.7 300p 0.7 310p 0 600p 0 610p 0.7 900p 0.7 910p 0 1200p 0 1210p 0.7 1500p 0.7 1510p 0 2100p 0 2110p 0.7 2400p 0.7)
Xdut a0 a1 b0 b1 sel1 sel2 pad vdd 0 tx_cell
Cload pad 0 2f
