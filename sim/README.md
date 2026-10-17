# sim

Holds **timing (STA) results** for the lane datapath and for characterized cell models. It holds no
circuit-simulation results: on the current worker ngspice 42 cannot load the compiled BSIM-CMG module
(`../spec/decisions/0003-simulation-flow.md`), so the drawn TX/RX cells are layout, DRC and LVS
deliverables with Liberty-based timing. Every result here is a tool result against a predictive model.
