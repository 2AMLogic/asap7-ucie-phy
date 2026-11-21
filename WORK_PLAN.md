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
- **#273**: LVS (digital): attribute the r17 routed-slice residue after the grid restore and tie the supply/well domain stream-side (child of #20)

## Important

`loom:important`; taken before unlabelled work.

- **#19**: T1 item 3 (DRC clean): klt drc report on the assembled lane-column GDS with ASAP7 deck coverage gaps disclosed *(held)*
- **#72**: T1 item 5 (corner verification, digital): close CDC FIFO setup timing per the decision 0007 ruling and re-run klt sta at tt/ss/ff *(held)*
- **#272**: layout: clear the four remaining DRC families on the lane column (successor to #228, for #19): r10 is 15,600 violations / 8 rules

## Ready

Human-approved issues (`loom:issue`) ready for implementation — excluding held (`loom:blocked`/`loom:operator`/`loom:frozen`), `loom:building`, and issues closed by an open `loom:pr` PR (listed under Approved).

- **#272**: layout: clear the four remaining DRC families on the lane column (successor to #228, for #19): r10 is 15,600 violations / 8 rules
- **#273**: LVS (digital): attribute the r17 routed-slice residue after the grid restore and tie the supply/well domain stream-side (child of #20)
- **#274**: T1 item 7 (digital): re-take the SDF-annotated run on the current routed slice, then bump the klt pin to the first release carrying klayout-tools#6075

## In Progress

Issues currently being built (`loom:building`).

- **#275**: T1 item 11: commit the klt erc supply spec and report for the drawn cells and the lane column now (the ERC half of #27 does not wait on LVS)
- **#277**: Draft the four-cell analog row definitions and verify the effect on digital item 6

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#281**: docs(spec): propose cell-level analog spec rows for the drawn cells (decision 0013)

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)* *(held)*
- **#272**: layout: clear the four remaining DRC families on the lane column (successor to #228, for #19): r10 is 15,600 violations / 8 rules *(curated)*
- **#273**: LVS (digital): attribute the r17 routed-slice residue after the grid restore and tie the supply/well domain stream-side (child of #20) *(curated)*
- **#274**: T1 item 7 (digital): re-take the SDF-annotated run on the current routed slice, then bump the klt pin to the first release carrying klayout-tools#6075 *(curated)*
- **#275**: T1 item 11: commit the klt erc supply spec and report for the drawn cells and the lane column now (the ERC half of #27 does not wait on LVS) *(curated)*
- **#277**: Draft the four-cell analog row definitions and verify the effect on digital item 6 *(curated)*

## Proposed (Architect / Hermit)

- **#134**: Consolidate the two cocotb runners in verification/ (run.sh + runner.py duplicate functional_verification.sh) *(hermit)* *(held)*
- **#136**: Trim the mismatch lists from four superseded 38 MB LVS reports in evidence/item4-lvs (190 MB of a 203 MB checkout) *(hermit)* *(held)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 2 |
| Important | 3 |
| Ready (`loom:issue`, net of holds/building/merge-pending) | 3 |
| In Progress (`loom:building`) | 2 |
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 0 |
| Curated | 7 |
| Architect / Hermit proposals | 2 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
