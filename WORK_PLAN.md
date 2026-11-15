# Work Plan

Roadmap generated from current GitHub label state by the Guide triage role.
Edit only outside the markers.

<!-- guide:plan-body:start -->
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

_None._

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists
- **#149**: Diagnose why the routed slice extracts 2 top-level pins against 266 in the LVS reference

## Important

`loom:important`; taken before unlabelled work.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md)
- **#19**: T1 item 3 (DRC clean): klt drc report on the assembled lane-column GDS with ASAP7 deck coverage gaps disclosed
- **#64**: Layout: clear remaining router-metal and cell DRC violations on the assembled lane column
- **#72**: T1 item 5 (corner verification, digital): close CDC FIFO setup timing per the decision 0007 ruling and re-run klt sta at tt/ss/ff
- **#148**: Record a klt drc run on the current committed lane column (no run exists since the re-route)
- **#151**: README status and T1 section contradict the committed verdict (drawn cells, column, analog LVS, STA r5, decision 0010)

## Ready

Human-approved issues ready for implementation (`loom:issue`).

- **#149**: Diagnose why the routed slice extracts 2 top-level pins against 266 in the LVS reference

## In Progress

Issues currently being built (`loom:building`).

- **#148**: Record a klt drc run on the current committed lane column (no run exists since the re-route)
- **#152**: verification: guard against a vacuous forwarded-clock phase check (phase % quantum == 0)
- **#153**: Stop package.json's four exit-0 stub gates from reporting a vacuous pass

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#156**: feat: replace package.json's exit-0 stub gates with a real stdlib-only check script
- **#161**: test: reject a scenario phase that is a whole multiple of the replay grid

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#147**: docs: roadmap as of 2026-11-13

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)*
- **#23**: T1 item 7 (post-layout verification): SDF-annotated functional re-run of the cocotb suite on the routed slice netlist *(curated)*
- **#148**: Record a klt drc run on the current committed lane column (no run exists since the re-route) *(curated)*
- **#149**: Diagnose why the routed slice extracts 2 top-level pins against 266 in the LVS reference *(curated)*
- **#150**: Logic-level ASAP7 BSIM-CMG simulation of rx_cell, tx_clk_cell and rx_clk_cell (decision 0010 method) *(curated)*
- **#151**: README status and T1 section contradict the committed verdict (drawn cells, column, analog LVS, STA r5, decision 0010) *(curated)*
- **#152**: verification: guard against a vacuous forwarded-clock phase check (phase % quantum == 0) *(curated)*
- **#154**: The documented item-10 re-attest command leaves klayout unpinned; CI pins it to 0.30.12 *(curated)*

## Proposed (Architect / Hermit)

- **#134**: Consolidate the two cocotb runners in verification/ (run.sh + runner.py duplicate functional_verification.sh) *(hermit)*
- **#136**: Trim the mismatch lists from four superseded 38 MB LVS reports in evidence/item4-lvs (190 MB of a 203 MB checkout) *(hermit)*
- **#145**: Stop copying an unchanged item-1 inventory per re-attestation: attest/item1.r2-r7 are six byte-identical files *(hermit)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 2 |
| Important | 6 |
| Ready (`loom:issue`) | 1 |
| In Progress (`loom:building`) | 3 |
| PRs awaiting review | 2 |
| Approved PRs awaiting merge | 1 |
| Curated | 9 |
| Architect / Hermit proposals | 3 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
