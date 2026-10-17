# 0005: what DRC, LVS and STA "clean" mean

Status: accepted. Date: 2026-10-17. Issue: #2.

## Decision

- **DRC clean**: zero violations from klt's ASAP7 deck for the implemented rules, with the rule-id
  list asserted, reported together with the unchecked-rule list (`../asap7-bringup.md`). Never
  stated as meeting the whole DRM; PAD and bump geometry are unchecked.
- **LVS**: `klt lvs` zero errors on the drawn cells and the lane column against reference netlists.
  Warnings listed. Standard cells join once the shipped-cell compare is clean (bring-up gap).
- **STA**: post-route, setup and hold slack of at least 0 at TT, SS and FF of the shipped RVT
  Liberty files, with every Liberty's declared operating condition reported. A run that loads a
  library whose declared condition differs from the corner name (the SIMPLE FF file) is flagged, not
  silently accepted.
- **Corner set**: RVT TT, SS, FF only. LVT and SLVT are out.

## Consequences

Evidence records are append-only; failures are kept. Adding a corner or library is a new record.
