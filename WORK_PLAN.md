# Work Plan

Roadmap generated from current GitHub label state by the Guide triage role.
Edit only outside the markers.

<!-- guide:plan-body:start -->
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

- **#185**: config: wire buildGate to ./check.sh so pre-PR receipts are earned, not skipped

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists

## Important

`loom:important`; taken before unlabelled work.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md)
- **#19**: T1 item 3 (DRC clean): klt drc report on the assembled lane-column GDS with ASAP7 deck coverage gaps disclosed
- **#23**: T1 item 7 (post-layout verification): SDF-annotated functional re-run of the cocotb suite on the routed slice netlist
- **#64**: Layout: clear remaining router-metal and cell DRC violations on the assembled lane column
- **#72**: T1 item 5 (corner verification, digital): close CDC FIFO setup timing per the decision 0007 ruling and re-run klt sta at tt/ss/ff
- **#169**: Determine the r5–r13 net.split/net.merged LVS residue: per-net diff of the r13 extract against layout/slice_routed.v

## Ready

Human-approved issues ready for implementation (`loom:issue`).

- **#23**: T1 item 7 (post-layout verification): SDF-annotated functional re-run of the cocotb suite on the routed slice netlist
- **#184**: Item 10: stale inventory description, and no remediation path for an 'inventory itself changed' drift

## In Progress

Issues currently being built (`loom:building`).

- **#158**: Wire buildGate.command at ./check.sh so the pre-flight receipt is earned, not skipped
- **#163**: Bind design/sim/tx_cell.osdi.sp to a re-adapt check: nothing re-runs the klt adaptation that produces it, and its in-file provenance names the wrong generator
- **#169**: Determine the r5–r13 net.split/net.merged LVS residue: per-net diff of the r13 extract against layout/slice_routed.v

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#179**: feat(signoff): bind tx_cell.osdi.sp to a re-adapt check, attest item 1 as r8

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#185**: config: wire buildGate to ./check.sh so pre-PR receipts are earned, not skipped
- **#186**: evidence: per-net diff attributes the r5-r13 LVS residue to the layout supply/well domain; routed circuits correspond exactly

## Proposed

Issues carrying `loom:curated`.

- **#3**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#20**: T1 item 4 (LVS clean): klt lvs match for the drawn TX/RX cells and the routed datapath against item-1 netlists *(curated)*
- **#23**: T1 item 7 (post-layout verification): SDF-annotated functional re-run of the cocotb suite on the routed slice netlist *(curated)*
- **#158**: Wire buildGate.command at ./check.sh so the pre-flight receipt is earned, not skipped *(curated)*
- **#163**: Bind design/sim/tx_cell.osdi.sp to a re-adapt check: nothing re-runs the klt adaptation that produces it, and its in-file provenance names the wrong generator *(curated)*
- **#169**: Determine the r5–r13 net.split/net.merged LVS residue: per-net diff of the r13 extract against layout/slice_routed.v *(curated)*
- **#184**: Item 10: stale inventory description, and no remediation path for an 'inventory itself changed' drift *(curated)*

## Proposed (Architect / Hermit)

- **#134**: Consolidate the two cocotb runners in verification/ (run.sh + runner.py duplicate functional_verification.sh) *(hermit)*
- **#136**: Trim the mismatch lists from four superseded 38 MB LVS reports in evidence/item4-lvs (190 MB of a 203 MB checkout) *(hermit)*
- **#166**: Replace the two directory-scoped JSON-validity gates with `klt env-provenance lint-envelope` over the whole tracked record set *(hermit)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 1 |
| Very important | 1 |
| Important | 6 |
| Ready (`loom:issue`) | 2 |
| In Progress (`loom:building`) | 3 |
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 2 |
| Curated | 7 |
| Architect / Hermit proposals | 3 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
