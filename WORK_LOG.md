# Work Log

Chronological record of merged PRs and closed issues. Maintained by the Guide
triage role; entries are newest first.

### 2026-10-27

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
