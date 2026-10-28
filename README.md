# asap7-ucie-phy

A UCIe-class die-to-die PHY — a wide, parallel, forwarded-clock link laid
out at micro-bump pitch — on [ASAP7](https://github.com/The-OpenROAD-Project/asap7),
a **predictive** 7 nm FinFET PDK, laid out by AI agents driving
[klayout-tools](https://github.com/2AMLogic/klayout-tools) and the
open-source cocotb + Icarus, Yosys and OpenROAD flow.

**ASAP7 is a predictive PDK, not a foundry process.** It models a 7 nm
FinFET node for research and teaching; no fab manufactures it. This block is
**layout, DRC and timing only, and it is never fabricated.** Every result in
this repo is a tool result against a predictive model — there is no silicon,
no shuttle and no measurement at the end of the ladder.

**Status: spec ratified, ASAP7 brought up, lane RTL and its testbench in place, pad-centre checker in place.** The drawn TX/RX cells, the lane column, DRC/LVS and post-route STA are not done. The committed T1 verdict reports each item as `met` or `unmet` (see "T1 evidence"); this is not a claim of any tier.

**Built agent-native.** Every specification, decision record, testbench, and
line of documentation here is produced by AI agents working from a ratified
spec and an append-only evidence trail — not human-authored work that agents
merely assisted with. Verification is the product: every claim traces to a
recorded result. Where the agents hit friction with the open-source tooling —
most often [klayout-tools](https://github.com/2AMLogic/klayout-tools) — that
friction is filed as a public issue against the tool itself, so the fix
benefits everyone using ASAP7, not just this repo.

## Why this block, on this PDK

A die-to-die PHY is a layout problem as much as a circuit problem. Each lane
— transmitter, receiver, and its share of the forwarded clock — has to fit
under a bump, and a module is a rigid column of those lane cells matched to
the bump map. That makes the block a test of things the fleet's core-block
canaries do not exercise: **bump-pitch-matched placement**, a regular lane
array whose
geometry is set by the package rather than by the logic, and the seam
between the lane array, the bump layer and the core-side interface.

On ASAP7 that geometry is demanding: a dense nine-metal BEOL stack (M1–M9)
under an advanced-package micro-bump pitch. Two facts set the scope from the
start:

- klayout-tools ships an ASAP7 DRC deck covering FEOL, MOL and BEOL M1–M9 /
  V0–V9, and its own documentation states that rules needing the PAD layer
  are not checked. The bump interface is therefore where the tools are
  expected to be weakest — finding out exactly how is part of the job.
- ASAP7's device models are BSIM-CMG. Whether the open simulation flow can
  run them was answered in `spec/decisions/0003-simulation-flow.md`: the model compiles but
  the current worker's ngspice cannot load it, so analog behaviour of the
  driver and receiver is not simulated here. Timing claims for the lane datapath come from static
  timing analysis against the ASAP7 libraries.

ASAP7 is not in the fleet's `open_pdks` store, so bringing it up under `klt`
is part of the work. If a sibling ASAP7 canary has already done that
bring-up, take its pinned setup rather than building a second one.

## Scope

- **In scope**: the lane datapath (serializer/deserializer, lane framing as
  far as the PHY owns it), the forwarded-clock path, the TX driver and RX
  front-end cells as drawn layout, the lane-cell column, and its placement
  against a micro-bump map. Signoff is DRC, LVS and post-route STA.
- **Not in scope**: the protocol and die-to-die adapter layers above the
  PHY, the clock source (specify the interface to it, including the clock
  quality this block assumes, and stop), the package, and any claim about
  the analog link margin of a real channel.

## Target specification

The ratified target specification is [`spec/ucie-phy.md`](spec/ucie-phy.md): every
parameter as target, fallback and stretch, each with its rationale and the kind of
tool run that settles it. Decisions are in [`spec/decisions/`](spec/decisions/) and the
ASAP7 bring-up under `klt` is in [`spec/asap7-bringup.md`](spec/asap7-bringup.md).
All figures are layout, DRC, LVS or timing-closure targets, not link-performance claims.

Headline rows, all layout, DRC, LVS or timing-closure targets (the full table, with rationale and
evidence type per row, is in [`spec/ucie-phy.md`](spec/ucie-phy.md)):

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Data lanes per direction | 16 | 8 | full-width module (64) |
| Rate per lane (equivalent to) | 16 GT/s | 4 GT/s | 32 GT/s |
| Parallel (core-side) clock | 4 GHz | 1 GHz | 8 GHz |
| Serialization ratio | 4:1 | 4:1 | 4:1 |
| Bump pitch the lane column matches | 45 um | 55 um | 25 um |
| Lane cell (width x height) | 45 x 90 um | 55 x 110 um | 25 x 50 um |
| PVT corners | TT, SS, FF (RVT) | same | same |

Maturity ladder: ASAP7 brought up under `klt` → spec ratified → lane RTL
verified → lane cell DRC/LVS-clean → lane column placed against the bump map
→ module slice DRC/LVS-clean → post-route STA closed. **Current position:
spec ratified, ASAP7 brought up.** There is no silicon rung.

## On UCIe, and what may be said

UCIe is a specification published by the UCIe Consortium. This block is
**UCIe-class**: it takes the physical shape of that kind of link — parallel
lanes, forwarded clock, micro-bump pitch — as its design target. Do not
describe it as UCIe-compliant or interoperable, do not use the consortium's
marks, and do not reproduce specification text in this repo.

## T1 evidence

The block's T1 evidence state is machine-readable. The block manifest
([`manifests/asap7-ucie-phy.json`](manifests/asap7-ucie-phy.json)) cites the
evidence; the verdict of record
([`manifests/asap7-ucie-phy.signoff.json`](manifests/asap7-ucie-phy.signoff.json))
is the committed output of `klt signoff` against it. Items 1, 9 and 10 (repo hygiene, cited from
[`manifests/t1-item10.envelope.json`](manifests/t1-item10.envelope.json)) are `met` (item 6's digital
partition is `not_applicable`; its analog partition is a declared gap, `unmet` / `no_evidence`, not evidence — see [decision 0008](spec/decisions/0008-item6-analog-declared-gap.md)). Item 5's digital partition cites a pre-route `klt sta` report
([`sta/`](sta/README.md)) and two `klt functional-verification` reports; it is `unmet` because
setup slack is negative at all three corners. Every other item is `unmet` and the tier is `null`. CI re-checks the verdict against the manifest
with the `klayout-tools` version pinned in `.github/klt-version`. To
regenerate the verdict, and the item-10 envelope after changing any inventoried file:

```
uvx --from "klayout-tools==$(cat .github/klt-version)" klt signoff --manifest manifests/asap7-ucie-phy.json --format json > manifests/asap7-ucie-phy.signoff.json
uvx --with klayout --from "klayout-tools==$(cat .github/klt-version)" klt signoff --attest 10 --inventory manifests/t1-item10-inventory.json -o manifests/t1-item10.envelope.json
```

## Reproduce

Each command below is a recorded tool run; none is a silicon or measured result.

```
# RTL: lint, synthesis check and cocotb testbench (needs the yosys, verilator and
# iverilog versions in verification/tool-versions.txt; it refuses on a mismatch)
verification/run.sh
verification/run.sh --negative-control   # exit 0 iff the deliberately broken check fails

# Functional-verification reports (T1 item 5): same pins and seed as run.sh
verification/functional_verification.sh
verification/functional_verification.sh --negative-control   # exit 0 iff the broken check fails

# Pre-route STA report (T1 item 5; needs openroad on PATH)
KLT="uvx --from klayout-tools==$(cat .github/klt-version) klt" python3 -I sta/regen.py

# Pad check: drawn pad centres vs the committed bump map (needs the `klayout` pip package)
python3 layout/selftest.py

# T1 item 10 (repo hygiene): re-check the committed attestation envelope
uvx --with klayout --from "klayout-tools==$(cat .github/klt-version)" klt signoff --attest 10 \
    --inventory manifests/t1-item10-inventory.json --check manifests/t1-item10.envelope.json

# T1 verdict of record: re-check it against the block manifest
uvx --from "klayout-tools==$(cat .github/klt-version)" klt signoff \
    --manifest manifests/asap7-ucie-phy.json --check manifests/asap7-ucie-phy.signoff.json
```

CI (`.github/workflows/signoff.yml`) runs the JSON validity check, the pad-checker
self-test and the two `--check` commands above. It does not run `verification/run.sh`,
which needs a toolchain the CI runner lacks.

## Repo layout

```
spec/          ratified spec + decision records
rtl/           lane datapath and clocking logic
verification/  cocotb testbenches
design/        TX driver / RX front-end cell netlists
sim/           timing (STA) results, and circuit sim if the models run
layout/        GDS + DRC/LVS reports, lane column and bump map
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
