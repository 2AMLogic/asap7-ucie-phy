# 0008: T1 item 6, analog partition, is a declared gap (route B)

Status: accepted. Date: 2026-10-28. Issue: #71. Refines: decision 0006 (digital partition only).

## Context

Decision 0006 records that no ratified spec row is statistical, and the manifest cited it under
a single item-6 `not_applicable` entry. klt's tier doc allows that outcome to a digital partition
only: an analog partition always needs Monte Carlo evidence. The verdict therefore graded the
analog half `unmet` with reason `not_applicable_wrong_partition`, which described a manifest
mistake rather than the real state.

## Options

- **A: add statistical spec rows for the drawn cells and run `klt yield`.** Rejected. No ratified
  row defines TX/RX electrical behaviour, so rows would extend the ratified spec without a
  ratified decision, and they could not be evidenced because ngspice 42 on the worker cannot load
  the BSIM-CMG OSDI model (decision 0003).
- **B (chosen): cite the `not_applicable` outcome for the digital partition only and declare the
  analog partition a gap.** The manifest key `6` becomes `6.digital`; the hashes of
  `manifests/spec-rows.json` and `manifests/item6-na-statement.json` are unchanged.

## Tool result

Tried first: `spec_rows."6.analog"` with a `gap` row and no citation, graded with
`klt signoff --manifest manifests/asap7-ucie-phy.json` at klt 0.8.0. Item 6 analog grades
`unmet` with reason `no_evidence`, not `partial_coverage`: the declaration is ignored without a
citation, the same behaviour as item 5 (`manifests/item5-analog-gap.json`;
`2AMLogic/klayout-tools#4190` is closed on the tool side, but this repo stays on the pinned 0.8.0
and this decision does not bump it). The declaration is therefore recorded in
`manifests/item6-analog-gap.json`, uncited and not hash-bound. Item 6 digital grades
`not_applicable`.

## Consequences

The analog cells are not characterized and no statistical claim is made. A future ratified
decision may add analog performance rows; that would withdraw this record and need `klt yield`
evidence.
