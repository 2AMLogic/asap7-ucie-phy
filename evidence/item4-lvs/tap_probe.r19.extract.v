* extracted by klt extract --deck asap7

* cell TAPCELL_ASAP7_75t_R
* pin VDD
* pin VSS
.SUBCKT TAPCELL_ASAP7_75t_R VDD VSS
.ENDS TAPCELL_ASAP7_75t_R

* cell PROBE
* pin VDD
* pin VSS
* pin vsubs
.SUBCKT PROBE VDD VSS vsubs
* cell instance $1 r0 *1 0,0
X$1 \$I2 VSS VDD vsubs AND2x2_ASAP7_75t_R
* cell instance $2 r0 *1 0.432,0
X$2 \$I2 VSS VDD vsubs AND2x2_ASAP7_75t_R
.ENDS PROBE

* cell AND2x2_ASAP7_75t_R
* pin VDD
* pin VSS
* pin VDD
* pin vsubs
.SUBCKT AND2x2_ASAP7_75t_R VDD VSS VDD$1 vsubs
* device instance $1 r0 *1 0,0.022 nmos_rvt
M$1 \$12 B \$5 vsubs nmos_rvt L=0.02U W=0.081U NFIN=3
* device instance $2 r0 *1 0,0.022 nmos_rvt
M$2 VSS A \$12 vsubs nmos_rvt L=0.02U W=0.081U NFIN=3
* device instance $3 r0 *1 0,0.022 nmos_rvt
M$3 Y \$5 VSS vsubs nmos_rvt L=0.02U W=0.162U NFIN=6
* device instance $4 r0 *1 0,0.022 pmos_rvt
M$4 \$5 B VDD$1 VDD pmos_rvt L=0.02U W=0.054U NFIN=2
* device instance $5 r0 *1 0,0.022 pmos_rvt
M$5 VDD$1 A \$5 VDD pmos_rvt L=0.02U W=0.054U NFIN=2
* device instance $6 r0 *1 0,0.022 pmos_rvt
M$6 Y \$5 VDD$1 VDD pmos_rvt L=0.02U W=0.162U NFIN=6
.ENDS AND2x2_ASAP7_75t_R
