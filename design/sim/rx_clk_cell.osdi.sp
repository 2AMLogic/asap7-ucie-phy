* rx_clk_cell: forwarded-clock lane: input stage to rx_clk
* Adapted from design/netlist/rx_clk_cell.sp by klt adapt_extracted_netlist (spec/decisions/0010); drift-checked by gen_cells.py --check.
.subckt rx_clk_cell pad rx_clk VDD VSS
N1 i1 pad VSS VSS nmos_rvt L=20n NFIN=3
N2 i1 pad VDD VDD pmos_rvt L=20n NFIN=3
N3 i2 i1 VSS VSS nmos_rvt L=20n NFIN=6
N4 i2 i1 VDD VDD pmos_rvt L=20n NFIN=6
N5 i3 i2 VSS VSS nmos_rvt L=20n NFIN=6
N6 i3 i2 VDD VDD pmos_rvt L=20n NFIN=6
N7 rx_clk i3 VSS VSS nmos_rvt L=20n NFIN=12
N8 rx_clk i3 VDD VDD pmos_rvt L=20n NFIN=12
.ends
