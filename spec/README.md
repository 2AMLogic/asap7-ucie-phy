# spec

The ratified target specification and its decision records. The spec's PR is ratified when it is
Judge-approved and merged; later changes go through a new decision record.

| Document | Content |
|---|---|
| [`ucie-phy.md`](ucie-phy.md) | Target / fallback / stretch for every parameter, with rationale and evidence type. |
| [`asap7-bringup.md`](asap7-bringup.md) | ASAP7 pin, `klt` commands that work, unchecked rules, gaps filed upstream. |
| [`decisions/0001-asap7-pin-and-bringup.md`](decisions/0001-asap7-pin-and-bringup.md) | The ASAP7 pin. |
| [`decisions/0002-bump-layer-representation.md`](decisions/0002-bump-layer-representation.md) | How bumps are drawn and checked. |
| [`decisions/0003-simulation-flow.md`](decisions/0003-simulation-flow.md) | BSIM-CMG in the open flow; what `sim/` holds. |
| [`decisions/0004-rate-definition-and-clock-ratio.md`](decisions/0004-rate-definition-and-clock-ratio.md) | What a rate row means. |
| [`decisions/0005-signoff-definitions.md`](decisions/0005-signoff-definitions.md) | DRC, LVS, STA acceptance. |
| [`decisions/0006-no-statistical-spec-rows.md`](decisions/0006-no-statistical-spec-rows.md) | No ratified spec row is statistical. |
| [`decisions/0007-cdc-fifo-read-enable-timing.md`](decisions/0007-cdc-fifo-read-enable-timing.md) | Closing the pre-route setup failure on the CDC FIFO read enable. |
| [`decisions/0008-item6-analog-declared-gap.md`](decisions/0008-item6-analog-declared-gap.md) | T1 item 6, analog partition, is a declared gap (route B). |
| [`decisions/0009-cdc-fifo-read-mux-select-timing.md`](decisions/0009-cdc-fifo-read-mux-select-timing.md) | Closing the pre-route setup failure on the CDC FIFO read-mux select. |
| [`decisions/0010-analog-simulation-flow.md`](decisions/0010-analog-simulation-flow.md) | Circuit simulation of the drawn TX cell runs on ngspice 47. |
| [`decisions/0011-json-document-stream.md`](decisions/0011-json-document-stream.md) | A `.json` evidence record may be a JSON document stream. |
| [`decisions/0012-record-path-hygiene-gate.md`](decisions/0012-record-path-hygiene-gate.md) | Record-path hygiene gate (forward-only). |
| [`decisions/0013-analog-spec-rows.md`](decisions/0013-analog-spec-rows.md) | Proposed cell-level analog spec rows for the four drawn cells. |
| [`decisions/0014-asap7-lvs-unsupported-cells-dont-use.md`](decisions/0014-asap7-lvs-unsupported-cells-dont-use.md) | Exclude klt's known-unsupported ASAP7 cell masters at the source rather than waive the LVS mismatch. |
| [`decisions/0015-routed-lvs-report-storage.md`](decisions/0015-routed-lvs-report-storage.md) | How a future failing routed-slice LVS report is stored. |
