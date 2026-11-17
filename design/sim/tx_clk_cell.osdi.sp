* tx_clk_cell: forwarded-clock lane: gate (tx_fwd_en) and driver
* Adapted from design/netlist/tx_clk_cell.sp by klt adapt_extracted_netlist (spec/decisions/0010); drift-checked by gen_cells.py --check.
.subckt tx_clk_cell clk fwd_en pad VDD VSS
N1 g clk n0 VSS nmos_rvt L=20n NFIN=3
N2 n0 fwd_en VSS VSS nmos_rvt L=20n NFIN=3
N3 g clk VDD VDD pmos_rvt L=20n NFIN=3
N4 g fwd_en VDD VDD pmos_rvt L=20n NFIN=3
N5 d1 g VSS VSS nmos_rvt L=20n NFIN=3
N6 d1 g VDD VDD pmos_rvt L=20n NFIN=3
N7 d2 d1 VSS VSS nmos_rvt L=20n NFIN=6
N8 d2 d1 VDD VDD pmos_rvt L=20n NFIN=6
N9 pad d2 VSS VSS nmos_rvt L=20n NFIN=12
N10 pad d2 VDD VDD pmos_rvt L=20n NFIN=12
.ends
