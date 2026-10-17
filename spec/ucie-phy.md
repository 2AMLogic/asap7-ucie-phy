# Target specification: UCIe-class PHY on ASAP7

**Status: ratified when this spec's PR is Judge-approved and merged.** After that, a change
goes through a new record in `decisions/`; nothing here is relaxed to make a result pass.

ASAP7 is a predictive PDK and this block is never fabricated. Every row is a layout, DRC, LVS or
timing target checked by a tool run against the pinned ASAP7 source (`asap7-bringup.md`). No row is
a silicon, measured or link-margin claim. The block is UCIe-class: it is not claimed to comply with
or interoperate with any specification, and no specification text is reproduced here.

The word **target** is the goal the ladder works to; **fallback** is what is accepted when the target
does not close; **stretch** is pursued only after the target closes and never drives architecture
(`CLAUDE.md`). "Evidence" names the recorded tool run that settles each row.

## 1. Module slice

| | Target | Fallback | Stretch | Evidence |
|---|---|---|---|---|
| Data lanes per direction | 16 | 8 | full-width module (64) | layout |
| Forwarded-clock lanes per direction | 1 | 1 | 1 | layout |
| Spare / redundancy lanes | none | none | 2 per slice | layout, LVS |

Signaling is single-ended with a forwarded clock in every column (layout evidence).

Rationale: 16 data lanes plus one forwarded clock is the slice named by the README draft and is a
size one column of lane cells can carry. Redundancy is a stretch because it adds muxing on the lane
path that the target does not need to close timing. Direction: each lane cell holds one TX and one RX
path (section 4), so a slice is 17 lane cells per direction.

## 2. Data rate and clock ratio

| | Target | Fallback | Stretch | Evidence |
|---|---|---|---|---|
| Rate per lane (equivalent to) | 16 GT/s | 4 GT/s | 32 GT/s | STA |
| Parallel (core-side) clock | 4 GHz | 1 GHz | 8 GHz | STA |
| Serialization ratio | 4:1 (quarter-rate) | 4:1 | 4:1 | STA, layout |

Definition: a rate row is met when post-route STA of the lane datapath closes **setup and hold**
at the parallel clock in the table, at every corner in section 6, with the serializer boundary of
section 4. It is a timing-closure target of synthesized logic and drawn-cell timing models, not a link
rate. Full- and half-rate clocking of the datapath are rejected for the target (decision 0004). The
stretch reuses the 4:1 ratio at 8 GHz; moving it to 8:1 needs a new record.

## 3. Bump map

| | Target | Fallback | Stretch | Evidence |
|---|---|---|---|---|
| Bump pitch the lane column matches | 45 um | 55 um | 25 um | layout |
| Bumps per lane cell | 2 (one TX, one RX) | 2 | 2 | layout |
| Bump assignment | one column, lane order = bump order top to bottom, clock lane at the column centre | same | same | layout |
| Bump representation | a drawn pad shape on ASAP7's `Pad` layer over a V9/M9 stack, plus a committed bump-map file | same | same | DRC (V9 rules only), layout |

The bump layer: ASAP7 defines `Pad` above M9 (tech LEF), with the stream number inconsistent
across pinned files (klayout-tools#3807). Decision 0002 draws pads on `Pad` at 96/0, which is the number the klt deck reads, and
records the bump map as data (lane, signal, x, y) in `layout/`. The pitch, origin and lane-to-bump
assignment are **not** checked by the DRC deck; they are checked by comparing the drawn pad
centres to the bump map, and that check is a layout-evidence row, never "DRC clean".

## 4. Lane cell

| | Target | Fallback | Stretch | Evidence |
|---|---|---|---|---|
| Width | 1 bump pitch (45 um) | 55 um | 25 um | layout |
| Height | 2 bump pitches (90 um) | 110 um | 50 um | layout |
| Area budget per lane | 4050 um^2 | 6050 um^2 | 1250 um^2 | layout |
| Drawn cells | TX driver, RX front-end | same | same | DRC, LVS |
| Serializer boundary | synthesized 4:1 serializer/deserializer up to its last two stages; the last 2:1 stage and the output driver are the drawn TX cell, the input stage and sampler are the drawn RX cell | same | same | LVS, STA |

Rationale: the budget is bump pitch times two bump pitches, derived from the pitch row, so it
tracks that row. A 7.5-track ASAP7 cell is 0.27 um tall, so the budget holds a large number of
standard cells; area is not the constraint. Matching the pitch with wiring and keeping the
column rigid is. The boundary puts the highest-rate logic in drawn cells, which are timed through
characterized models (Liberty) rather than synthesized.

## 5. Core-side interface (specified, not designed)

- **Width**: 4 bits per lane per parallel-clock cycle, so 64 bits (target), 32 (fallback).
- **Clock domain**: one clock, the parallel clock of section 2, supplied by the clock source. The
  TX side is synchronous to it. The RX side crosses from the forwarded-clock domain to it inside the PHY.
- **Handshake**: TX is `valid`/`ready` per slice; RX is `valid` only (no back-pressure into the link).
- **Clock-source interface** (out of scope, stated so STA is reproducible): the PHY receives one
  single-ended clock at the parallel frequency. Assumed quality, expressed as STA constraints and not as
  a jitter claim: clock uncertainty 5 percent of the period (12.5 ps at 4 GHz) for setup and 2 percent
  for hold, input transition at most 20 ps. A different assumption is a spec change.
- The protocol layers above, the clock source and the package are out of scope.

Evidence: STA (constraints recorded with the run), cocotb for the handshake.

## 6. PVT corners

Named by shipped Liberty file (`asap7-bringup.md`, "Liberty corners"). Only these exist; none is invented.

| Corner | Files (`libs/asap7sc7p5t_rvt/nldm/`) | Voltage / temperature (file headers) |
|---|---|---|
| TT | `asap7sc7p5t_{AO,INVBUF,OA,SEQ,SIMPLE}_RVT_TT_nldm.lib.gz` | 0.70 V / 25 C |
| SS | `asap7sc7p5t_{AO,INVBUF,OA,SEQ,SIMPLE}_RVT_SS_nldm.lib.gz` | 0.63 V / 100 C |
| FF | `asap7sc7p5t_{AO,INVBUF,OA,SEQ,SIMPLE}_RVT_FF_nldm.lib.gz` | 0.77 V / 0 C (SIMPLE file declares 0.70 V / 25 C: recorded anomaly) |

RVT only. LVT and SLVT libraries ship but are not in the corner set; using one is a spec change.
Setup and hold are both judged at all three corners (decision 0005).

## 7. Signoff

| Signoff | Meaning | Evidence |
|---|---|---|
| DRC clean | `klt drc` with the pinned ASAP7 deck, zero violations on the final GDS, with `--expect-rule-categories-file` satisfied, **and** the unchecked-rule list in `asap7-bringup.md` stated alongside. It does not mean the DRM is met: PAD, bump and 67 other rules are unchecked. | DRC |
| LVS | the drawn TX/RX cells and the lane column match their reference netlists by `klt lvs` with zero errors; warnings are listed. Standard-cell-only blocks are compared in the same way once the shipped-cell compare is clean (bring-up gap). | LVS |
| STA | post-route setup and hold slack of at least 0 at every corner in section 6, at the clock of section 2, with the constraints of section 5 recorded. | STA |
| Bump map | drawn pad centres equal the committed bump map within one database unit. | layout |

Results are append-only evidence; a failing run is recorded, not replaced.
