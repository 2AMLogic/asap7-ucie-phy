# 0003: circuit simulation scope for `sim/`

Status: accepted. Date: 2026-10-17. Issue: #2.

## Context

Can the BSIM-CMG models in ASAP7 be simulated in the open flow?

Probe, run once locally (`ngspice -b`, no grid):

1. BSIM-CMG Verilog-A source: `dwarning/VA-Models` `code/bsimcmg/vacode111/bsimcmg.va`, commit
   `6099b4e12e6f66ff530f59b8d01fb909094be85a` (module `bsimcmg_va`, BSIM-CMG 111).
2. OpenVAF-Reloaded (`openvaf-r`, present in a host cache; its bundled libLLVM link was dangling, so
   it was run with `LD_LIBRARY_PATH` set to the cached libLLVM 21 directory, read only) compiled the
   source to `bsimcmg_va.osdi` in 6.6 s.
3. ngspice 42 `pre_osdi bsimcmg_va.osdi` failed: `NGSPICE only supports OSDI v0.3 but ... targets
   v0.4!`. klt documents the same limit (an OpenVAF-Reloaded module needs ngspice 44 or later) and has
   an adaptation layer for ASAP7 BSIM-CMG cards (`klayout_tools/asap7_bsimcmg.py`).

## Decision

On the current worker, circuit simulation of the drawn TX/RX cells is **not possible**: the model
compiles, but this ngspice cannot load it. Answer: **partial**. Therefore:

- `sim/` holds STA results for the lane datapath and for characterized cell models. It holds no
  circuit-simulation results until a worker with ngspice 44 or later (or a v0.3 OpenVAF) exists.
- TX/RX cells are **layout, DRC and LVS deliverables** with timing from Liberty models; no analog
  behaviour is claimed.
- Not tested: a simulation with the ASAP7 `.pm` cards end to end. The result above does not show
  that it would work on a newer ngspice, only that the host is the blocker at the first step.

## Consequences

A worker-spec change (ngspice 44 or later) is the follow-up, filed as a note on the PR, because host
tools are not changed from a sweep. This record is superseded by a new one if that happens.
