# Work Plan

Roadmap generated from current GitHub label state by the Guide triage role.
Edit only outside the markers.

<!-- guide:plan-body:start -->
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

_None._

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(held)*

## Important

`loom:important`; taken before unlabelled work.

- **#19**: T1 item 3 (DRC clean): klt drc report on the assembled lane-column GDS with ASAP7 deck coverage gaps disclosed *(held)*
- **#72**: T1 item 5 (corner verification, digital): close CDC FIFO setup timing per the decision 0007 ruling and re-run klt sta at tt/ss/ff *(held)*

## Ready

Human-approved issues (`loom:issue`) ready for implementation — excluding held (`loom:blocked`/`loom:operator`/`loom:frozen`), `loom:building`, and issues closed by an open `loom:pr` PR (listed under Approved).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#308**: Share the JSON stream parser so split records preserve CRLF bytes

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#309**: fix(verification): unify JSON stream walker and preserve split bytes

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)* *(held)*
- **#274**: T1 item 7 (digital): re-take the SDF-annotated run on the current routed slice, then bump the klt pin to the first release carrying klayout-tools#6075 *(curated)* *(held)*
- **#318**: spec/README.md decision index stops at 0005; records 0006-0015 are missing *(curated)*
- **#319**: Nothing fails when a new spec/decisions/ record is left out of the item-10 hygiene inventory *(curated)*

## Proposed (Architect / Hermit)

- **#134**: Consolidate the two cocotb runners in verification/ (run.sh + runner.py duplicate functional_verification.sh) *(hermit)* *(held)*
- **#289**: Remove Cell.render_osdi() in design/gen_cells.py: unify all four design/sim/*.osdi.sp files on design/sim/regen.py *(hermit)* *(held)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 1 |
| Important | 2 |
| Ready (`loom:issue`, net of holds/building/merge-pending) | 0 |
| In Progress (`loom:building`) | 1 |
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 0 |
| Curated | 5 |
| Architect / Hermit proposals | 2 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
