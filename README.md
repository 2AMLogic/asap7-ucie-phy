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

**Status: just opened, specification phase.** Nothing is designed yet.

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
  run them at all is an open question for the spec (see issue #1), so
  analog behaviour of the driver and receiver is not assumed to be
  simulatable here. Timing claims for the lane datapath come from static
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

## Target specification (DRAFT — engineering to ratify, see issue #1)

All figures are targets. The rate rows are timing-closure targets for the
lane datapath under STA, not link-performance claims.

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Lanes per module slice | 16 data + forwarded clock | 8 data | full-width module |
| Data rate per lane (STA closure) | 16 GT/s | 4 GT/s | 32 GT/s |
| Micro-bump pitch the lane column matches | 45 µm | 55 µm | 25 µm |
| Signaling | single-ended, forwarded clock | — | — |
| Signoff | DRC + LVS clean, post-route STA at the shipped library corners | — | — |

Maturity ladder: ASAP7 brought up under `klt` → spec ratified → lane RTL
verified → lane cell DRC/LVS-clean → lane column placed against the bump map
→ module slice DRC/LVS-clean → post-route STA closed. **Current position:
pre-spec.** There is no silicon rung.

## On UCIe, and what may be said

UCIe is a specification published by the UCIe Consortium. This block is
**UCIe-class**: it takes the physical shape of that kind of link — parallel
lanes, forwarded clock, micro-bump pitch — as its design target. Do not
describe it as UCIe-compliant or interoperable, do not use the consortium's
marks, and do not reproduce specification text in this repo.

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
