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

- **#136**: Document how to store future failing routed-slice LVS reports
- **#279**: Measure forwarded-clock rows, probe TX extraction and assemble the ratification handoff
- **#297**: TX mux-to-pad delay misses the 16 GT/s target at SS: a3 select-path delay 34.7 ps vs 31.25 ps (fallback clears)
- **#308**: Share the JSON stream parser so split records preserve CRLF bytes

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#304**: analog: upsize the tx_cell stage-1 select path to close row a3 at SS
- **#305**: docs(spec): record the future-only storage rule for failing routed-slice LVS reports
- **#307**: feat(sim): measure proposed clock rows a7-a10 at the 0013 PVT tuples; record the tx_cell PEX probe and file the ratification handoff
- **#309**: fix(verification): unify JSON stream walker and preserve split bytes

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)* *(held)*
- **#136**: Document how to store future failing routed-slice LVS reports *(curated)*
- **#274**: T1 item 7 (digital): re-take the SDF-annotated run on the current routed slice, then bump the klt pin to the first release carrying klayout-tools#6075 *(curated)* *(held)*
- **#279**: Measure forwarded-clock rows, probe TX extraction and assemble the ratification handoff *(curated)*
- **#297**: TX mux-to-pad delay misses the 16 GT/s target at SS: a3 select-path delay 34.7 ps vs 31.25 ps (fallback clears) *(curated)*

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
| In Progress (`loom:building`) | 4 |
| PRs awaiting review | 4 |
| Approved PRs awaiting merge | 0 |
| Curated | 6 |
| Architect / Hermit proposals | 2 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
