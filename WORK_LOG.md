# Work Log

Chronological record of merged PRs and closed issues. Maintained by the Guide
triage role; entries are newest first.

### 2026-10-28

- **PR #50**: feat(layout): assemble the 17-lane bump-pitch column and attest T1 item 2
- **Issue #35** (closed): T1 item 2c: lane-column assembly, pad check record and item-2 envelope
- **Issue #18** (closed): T1 item 2 (layout): routed lane-datapath GDS from a committed P&R flow plus drawn TX/RX cell GDS placed in the bump-pitch lane column

### 2026-10-27

- **PR #48**: fix: load pinned lambdapdk module directly in PnR regen script
- **Issue #47** (closed): Remove duplicate Liberty merge in layout/pnr/regen.py; it still calls names db763e1 moved
- **PR #46**: chore: ignore negative-control functional-verification reports
- **Issue #38** (closed): Gitignore verification/*.negative-control.report.json written by functional_verification.sh
- **PR #44**: refactor: share lambdapdk pin, fetch and Liberty merge between synth and STA regen
- **Issue #40** (closed): Consolidate duplicated lambdapdk fetch and Liberty merge in the two regen scripts
- **PR #43**: feat: add committed place-and-route flow and routed GDS for the synthesized slice
- **Issue #33** (closed): T1 item 2a: P&R flow and routed GDS of the slice datapath
- **PR #42**: docs: analyse pre-route setup failure and propose CDC FIFO read-enable decision
- **Issue #39** (closed): Diagnose pre-route setup violations in the CDC FIFO (negative slack at tt/ss/ff) and propose a closure path
- **PR #41**: docs(manifest): record analog half of item 5 as a declared gap
- **PR #37**: feat(evidence): record pre-route STA and functional-verification reports for item 5 digital
- **Issue #21** (closed): T1 item 5 (corner verification): klt sta at RVT TT/SS/FF plus a klt functional-verification report for the lane datapath
- **PR #36**: feat: add generator and GDS for drawn TX/RX cell footprints
- **Issue #34** (closed): T1 item 2b: drawn TX/RX cell GDS generator within the lane-cell budget
- **PR #31**: docs: add item-10 hygiene inventory, attestation envelope and README reproduce section
- **Issue #26** (closed): T1 item 10 (repo hygiene): hygiene inventory and klt signoff --attest 10 envelope
- **PR #30**: feat(signoff): attest T1 item 9 testbenches and gate drift in CI
- **Issue #25** (closed): T1 item 9 (testbenches shipped): testbench inventory and klt signoff --attest 9 envelope
- **PR #29**: feat(design): attest T1 item 1 with synthesized slice netlist and drawn-cell SPICE
- **Issue #17** (closed): T1 item 1 (design sources): synthesized ASAP7 gate-level netlist for rtl/slice.v plus TX-driver/RX-front-end schematic netlists
- **PR #28**: docs(spec): record that no ratified spec row is statistical (T1 item 6)
- **Issue #22** (closed): T1 item 6 (Monte Carlo): record that no ratified spec row is statistical

### 2026-10-23

- **PR #15**: feat(rtl): add lane serializer/deserializer slice with cocotb loopback testbench
- **PR #14**: feat(layout): bump map generator, pad-centre checker and self-test
- **Issue #12** (closed): Lane datapath RTL (4:1 serializer/deserializer to the drawn-cell boundary) with a cold-start cocotb testbench (T1 items 1, 9)
- **Issue #13** (closed): Commit the bump map and a pad-centre checker with a negative control (spec section 3, decision 0002)

### 2026-10-21

- **PR #10**: Bump Repo Skills 0.24.3 -> 0.24.7

### 2026-10-20

- **PR #5**: ci: add klt signoff manifest, verdict of record and drift gate
- **Issue #4** (closed): T1 item 10: add CI and a klt signoff block manifest as the verdict of record

### 2026-10-17

- **PR #6**: docs(spec): ratify target spec, record ASAP7 bring-up and decisions
- **Issue #2** (closed): Draft and ratify the target spec
- **PR #1**: chore(loom): Install Loom 0.19.1180
