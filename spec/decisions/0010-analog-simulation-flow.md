# 0010: ASAP7 circuit simulation of the drawn TX cell runs on ngspice 47

Status: accepted. Date: 2026-11-13. Issue: #128. Supersedes: decision 0003 (the circuit-simulation
blocker only; its STA and layout-deliverable statements stand).

## Context

Decision 0003 found that ngspice 42 could not load the OSDI v0.4 BSIM-CMG module, and said a new
record supersedes it once a worker with ngspice 44 or later exists. The fleet now runs ngspice 47 on
the dispatch workers and in the Spot batch image (2AMLogic/2am#6391).

## What was run

One `klt sim` request (`design/sim/tx_cell.sim.json`), submitted with `--backend batch
--wait-for-capacity 600`, three process corners (TT, SS, FF), VDD 0.7 V, 25 C, one drawn cell
(`tx_cell`, ASAP7 RVT) with a 2 fF load on `pad`. The testbench (`design/sim/tx_cell.tb.sp`) walks
all four mux selections with the selected input at 0 and at 1 (8 phases of 300 ps; the three
unselected inputs carry the opposite level, so a wrong path inverts the expected value). The
assertions are logic levels only: `pad` above 0.9 VDD when the selected input is 0, below 0.1 VDD
when it is 1 (the cell inverts, three stages).

Result, report `sim/tx_cell.batch.report.json`: all 3 corners `pass`, all 24 assertions within
limits. ngspice 47 (`environment.engine_version`), batch job `klt-sim-7911111351c7`
(`environment.remote.job_id`). Low levels read 9.3e-8 to 1.2e-7 V, high levels 0.700 V.

## Provenance

| Item | Value |
|---|---|
| BSIM-CMG Verilog-A | dwarning/VA-Models `6099b4e12e6f66ff530f59b8d01fb909094be85a`, `code/bsimcmg/vacode111` |
| Compiler | OpenVAF-Reloaded `osdi_0.4-153-g2e066436`, built on the worker into the worktree, not committed |
| `bsimcmg.osdi` sha256 | `4e755d14e901a84600124be5cb73e36302117b6cfc694e52ffc17640945cd9e3` (matches klt's reference build; staged with the job, runner reports the same hash) |
| Model cards | lambdapdk `v0.2.17` (archive sha256 as in `spec/asap7-bringup.md`) `7nm_TT_160803.pm` `684708eec0f7d5960be1df6a045de811c8dd2d6b0e1ed7d0f805a3f697f262fc`, `7nm_SS_160803.pm` `ae06193a1a31e72d759a852dabda5b4c02b631068a34a02731e7285fa7e7b302`, `7nm_FF_160803.pm` `cdb1f67e81cbfb49cd9f570c276dcdbab860cd1f06deb1878d0e1137911c5b56` |
| Adapted corner library | `design/sim/asap7_bsimcmg.lib`, sha256 `c0478207ccf23686f2585c91f45d5e54d988560397ed8516219ee45b099c0280` |
| Adapted netlist | `design/sim/tx_cell.osdi.sp`, from `design/netlist/tx_cell.sp` |

Adaptation used `klayout_tools.asap7_bsimcmg` (`adapt_model_cards`, `corner_library`,
`adapt_extracted_netlist`) in klt 0.9.2.dev885; the one-call `adapt` request key was not used
because it is refused on `batch`. The `tx_cell.sp` `M` cards (lowercase `nfin=`, `w=`/`l=` in
`n`) were accepted by the adapter without change. The OSDI module path in the request points at
`sim/build/osdi/`, which is gitignored; rebuild it with klt's `scripts/fetch-asap7-sim-toolchain.sh`
(`OPENVAF_R_BIN` and `KLT_ASAP7_SIM_STORE` set) and check the sha256 above.

## What this does and does not show

- It shows the open flow can simulate the drawn TX cell end to end against the ASAP7 BSIM-CMG
  cards, on the batch fleet, and that the mux and three-stage inversion are logically right at
  three process corners.
- It is a model-level functional check against a predictive model. It makes no delay, rate, eye,
  jitter, power or Fmax statement, adds no spec row (decisions 0006, 0008), and says nothing about a
  fabricated part: this block is never fabricated.
- Not covered: `rx_cell`, the clock cells, Monte Carlo, any pad or bump parasitics.
- `manifests/item5-analog-gap.json` and `manifests/item6-analog-gap.json` are not edited here. A
  follow-up decides whether one functional run changes their status; this record does not argue it.

## Consequences

`sim/` now holds one circuit-simulation report. Decision 0003 is left as written (it is
inventoried in `manifests/t1-item10-inventory.json`); this record supersedes its blocker.
