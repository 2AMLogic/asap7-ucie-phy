# 0001: ASAP7 pin and `klt` bring-up

Status: accepted. Date: 2026-10-17. Issue: #2.

## Context

ASAP7 is not in the fleet's `open_pdks` store. No sibling canary had a merged pin
(`asap7-npu` has an open PR pinning a different source). klt's own ASAP7 deck docs pin
`siliconcompiler/lambdapdk` `v0.2.17`.

## Decision

Pin ASAP7 to lambdapdk `v0.2.17` (archive sha256 in `../asap7-bringup.md`), the same source
klt's deck is transcribed from, so deck, layer files and libraries agree. Bring-up evidence,
working commands and gaps are recorded in `../asap7-bringup.md`. Run klt's ASAP7 DRC deck through
`--engine klayout --deck-file` with the declared rule-id list.

## Consequences

- DRC smoke test passes on two shipped cells (0 violations). The `klt` used was a post-tag build, so
  the same run must be repeated against a released klt carrying the deck.
- LVS extraction works; a clean compare of a shipped cell against its CDL does not yet.
- When a sibling pin merges, a new record compares it with this one and adopts one.
