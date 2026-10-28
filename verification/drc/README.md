# verification/drc

T1 item 3 (DRC clean) on `layout/lane_column.gds`. **Not met.**

`lane_column.drc.run-record.json` records the one run made (2026-10-28, released klt 0.8.0,
`--engine klayout` with the packaged ASAP7 deck, deck hash `sha256:48ac590a...e7f`, the 263-id
rule-category expectation file): status `violations`, 8,126,659 violations across 65 rules,
dominated by `GATE.S.1`, `GATE.S.3`, `GATE.S.2`, `GATE.W.2`, `GCUT.AUX.2` and `GCUT.GATE.EX.1`.
The cells are unrouted placements (`layout/README.md`), so this is the expected kind of result;
it is a layout result against a predictive PDK, not a measurement.

The full envelope (~3.9 GB, every polygon inline) was not committed and its trailing `coverage`
block was not obtained, so no `coverage` fields are quoted here. Nothing was waived or filtered.
The manifest does not cite this record, and `klt signoff` item 3 stays unmet.
