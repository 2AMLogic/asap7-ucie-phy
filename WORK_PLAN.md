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

## Important

`loom:important`; taken before unlabelled work.

- **#19**: T1 item 3 (DRC clean): klt drc report on the assembled lane-column GDS with ASAP7 deck coverage gaps disclosed
- **#64**: Layout: clear remaining router-metal and cell DRC violations on the assembled lane column

## Ready

Human-approved issues ready for implementation (`loom:issue`).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#128**: Analog T1: add an ASAP7 ngspice deck and run it on the batch layer (fleet ngspice 47 is ready)

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#129**: feat(sim): ASAP7 BSIM-CMG logic-level deck for tx_cell, batch-run at TT/SS/FF

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)*
- **#23**: T1 item 7 (post-layout verification): SDF-annotated functional re-run of the cocotb suite on the routed slice netlist *(curated)*
- **#128**: Analog T1: add an ASAP7 ngspice deck and run it on the batch layer (fleet ngspice 47 is ready) *(curated)*

## Proposed (Architect / Hermit)

_None._

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 1 |
| Important | 2 |
| Ready (`loom:issue`) | 0 |
| In Progress (`loom:building`) | 1 |
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 0 |
| Curated | 4 |
| Architect / Hermit proposals | 0 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
