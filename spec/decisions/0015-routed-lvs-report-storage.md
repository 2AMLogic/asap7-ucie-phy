# 0015: how a future failing routed-slice LVS report is stored

Status: accepted. Date: 2026-11-23. Issue: #136. Directed by: operator ruling
2026-11-23 (@rjwalters, attended `/fleet:decide` round 20261121-r19, q213,
slate s18) — this record implements the ruling; ratification is the review of
its PR.

## Context

Item 4's digital partition is an open failing compare (#20). Every failing
flattened routed-slice `klt lvs` run so far committed its full report, and the
report's `mismatches` array is effectively the whole file: r6-r8 and r11 are
37.6-38.4 MB each, and r10's 88,881 entries are 28.2 MB of a 37.6 MB file. The
five `slice_routed` reports committed before this record total about 190 MB of
a roughly 203 MB checkout. Decision 0005 keeps evidence append-only and keeps
failures, so whether already-committed reports could be trimmed was escalated
to the operator in #136. The ruling chose **future-only**: leave existing
evidence untouched; commit trimmed reports from now on.

## Decision

From the ruling's date forward, the person recording a new failing flattened
routed-slice compare (item 4 digital) commits a **derived summary** rather
than the full report — unless that report is selected for a block-manifest
citation at recording time.

- **Unpinned (the default).** Generate the full comparison into scratch space
  first, then write the summary from it with distinct input and output paths:

  ```
  jq '.mismatches = [] | .mismatches_omitted = true' "$full" > "$summary"
  ```

  The summary keeps every other field as the tool wrote it: the original
  `status`, the exact `mismatch_count` and `error_count` totals,
  `category_counts`, `category_error_counts`, `counts`, `options`,
  `environment` and `provenance`. An empty `mismatches` list still reads as a
  failure through `status`, the counts and the category totals; the
  `mismatches_omitted: true` marker is what discloses that the detail list was
  left out. The attempt record names the committed file as a derived summary,
  not as a `klt lvs` output — a summary has not passed native LVS replay and
  is not evidence of one.
- **Pinned.** A report the block manifest cites
  (`manifests/asap7-ucie-phy.json`, `evidence["4.digital"]`) is committed in
  full — the native `klt lvs` output — and pinned by its actual content hash.
  Whether a run is pinned is determined at recording time, not afterwards.
- **Existing evidence.** Every LVS report and attempt record already committed
  keeps its path and bytes (decision 0005). No retrospective trimming,
  compression, renaming, deduplication or history rewriting follows from this
  record.

The repo pin `klt` 0.9.2 (`.github/klt-version`) has no `--omit-mismatches`
(`klt lvs --help`), so the jq copy-out above is the recipe at this pin. The
native flag landed upstream in
[2AMLogic/klayout-tools#5836](https://github.com/2AMLogic/klayout-tools/pull/5836);
adopting it is a pin bump, not a change to this rule — a native compact output
that keeps the same totals and the same explicit omission contract satisfies
this record without jq.

## Consequences

- Checkout growth per further failing unpinned compare is kilobytes, not
  ~38 MB. Measured on r10 with the recipe above: 37,589,304 bytes in, 7,555
  bytes out, with `status: "mismatch"`, `mismatch_count` 88,881, `error_count`
  88,620, the category counts, `options`, `environment` and `provenance`
  round-tripping identically and the parsed objects equal after excluding only
  the detail list and its new marker.
- The per-entry detail of an unpinned failing compare lives in scratch space
  only. If the entries themselves will be analysed — the r7 category reading in
  `../asap7-bringup.md` is the precedent — record the run in the pinned, full
  form instead; that choice is made at recording time.
- Scripts that iterate `mismatches` of a committed report keep working
  unchanged for every report committed before this record and for pinned
  reports after it; an unpinned summary's empty list is exactly what its
  `mismatches_omitted` marker discloses.
