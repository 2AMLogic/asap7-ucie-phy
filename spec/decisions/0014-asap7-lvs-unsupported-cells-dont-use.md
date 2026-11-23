# 0014: exclude klt's KNOWN_UNSUPPORTED_ASAP7_CELLS masters at the source instead of waiving the LVS topology mismatch

Status: accepted. Date: 2026-11-23. Issue: #287.

## Context

The routed-slice LVS residue was attributed exactly by the r18 census (issue
#273): of the 7,581 r18/r19 mismatches, everything except the well-tap domain
cascade (klayout-tools#7182) reduced to **one library cell** —
`AOI21x1_ASAP7_75t_R{,$VAR1}`, 186 instances, whose drawn A1/A2 nmos series
stack is folded twice at half width where the library CDL folds one stack
(total fins 16 = 16: a topology fold, not a sizing disagreement). Those 186
instances carried the whole +372-device layout-vs-reference surplus and all
186 `device.unmerged_fingers` entries.

`AOI21x1` is not alone: `klt` 0.9.2's own `KNOWN_UNSUPPORTED_ASAP7_CELLS`
table (`lvs_known_limits.py`) lists 17 RVT masters whose drawn transistor
topology differs from the library CDL — 11 `folded-stack` (AND2x4, AND2x6,
AOI21x1, AOI22x1, NAND3x2, NOR3x2, OAI21x1, OAI22x1, OR2x6, XNOR2x1, XOR2x1)
and 6 `series-order` (A2O1A1O1Ixp25, AOI211xp5, OAI221xp5, SDFLx1, SDFLx2,
SDFLx3), all `_ASAP7_75t_R`. Upstream has ruled on this class twice:
klayout-tools#4819 (operator ruling, option (a)) keeps the documented limit —
`status` stays `mismatch` — and declined stack normalisation as out of scope,
and klayout-tools#6931 added the block-level `topology.known_limitation`
disclosure on `klt` `main`. Neither is in the PyPI `0.9.2` this repo pins.

A recorded `status: mismatch` deviation cannot close T1 item 4 digital
(#20): `klt signoff` (`signoff.py`, `_check_passed`) grades item 4 `met` only
on `status == "match"` and ignores `spec_rows` / `justified_gaps`, so leaving
the cell in the netlist keeps item 4 `unmet` even after `.github/klt-version`
advances past #7182.

## Decision

Exclude the 17 masters at the source, extending the #228 precedent (the ten
`SDT.ACTIVE.AUX.2` deviators, `constraints.dont_use` since `8025f0a`):

1. `design/synth/slice.synth.json` `constraints.dont_use` grows from 10 to 27
   masters (the ten #228 deviators plus the 17
   `KNOWN_UNSUPPORTED_ASAP7_CELLS`), so neither Yosys nor ABC maps any of
   them. ABC already had CDL-matching alternatives: the 186 `AOI21x1`
   instances re-map to `AOI21xp5`/`AOI21xp33`.
2. `layout/pnr/regen.py` stages `dont_use : true;` for the same list — read
   from `slice.synth.json`, never re-typed — into the scratch Liberty it
   hands OpenROAD, because `klt place-and-route` (0.9.2) has no request-level
   `dont_use` constraint and the resizer would otherwise be free to swap an
   excluded master back in. The unit test
   `layout/pnr/test_check_input.py` covers the staging helper.
3. The routed-slice LVS report of record is re-taken on the re-routed stream
   (`slice_routed.r20`) and the manifest re-cites it. r18/r19 stay untouched
   (append-only, decision 0005).

This is source exclusion, not a waiver: no `ignore_mos_bulk`, no
`finfet_bulk` drop, no reference edit, no deck edit, and no ratified spec row
is relaxed (decision 0005's constraints stand). It is also not a claim of
clean LVS today: the well-tap domain cascade (klayout-tools#7182) remains at
the `0.9.2` pin, so r20 still records `mismatch` — with
`device.unmerged_fingers` 0 and equal layout/reference device counts, the
entire remaining error set attributed to #7182. Item 4 digital closes only
when a PyPI release carrying #7182 is pinned (#20 owns that bump); this
record is the in-repo half of that path.

## Consequences

- Zero instances of all 27 excluded masters in `design/netlist/slice_asap7.v`
  and `layout/slice_routed.v` (per-master search; the r20 evidence chain
  re-derives it).
- LVS r20 (`evidence/item4-lvs/slice_routed.r20.report.json`, klt 0.9.2 /
  klayout 0.30.12 on pin): `device.unmerged_fingers` 186 -> **0**; device
  counts layout 28,784 == reference 28,784 (surplus +372 -> **0**); remaining
  errors 6,020 across the #7182 families only.
- Post-route STA r3 (0.5 ns P&R constraint): 0 setup / 0 hold violations at
  tt/ss/ff; pre-route r9: 0 setup violations at tt/ff (ss fails as before,
  156 violations — the rate row stays open and is not claimed).
- The area shrinks 937.786 -> 914.545 um² (core) with the re-mapping; DRC
  r12: `SDT.ACTIVE.AUX.2` stays 0, no new rule family appears on the slice or
  the column.
- Sizing cost: `AOI21xp5` is a wider drive than `AOI21x1`; power moved
  0.8552 -> 0.8452 mW (pre-route tt estimate) — the exclusion did not cost
  power at the reported digits and the critical-path timing is unchanged
  (r9 == r8 slacks to the reported digits; same critical path, a measured
  result, mechanism not established).
