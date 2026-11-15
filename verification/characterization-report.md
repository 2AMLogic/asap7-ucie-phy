# Slice characterization report (T1 item 8)

One aggregated, current record of per-spec-row performance across conditions for
the `asap7-ucie-phy` block, with the committed evidence behind every verdict.
This is the artifact T1 item 8 ("Characterization report") grades: the machine
check is `klt signoff --attest 8 --inventory manifests/attest/item8.json --check
manifests/evidence/item8.json`, whose inventory cites exactly the records this
report links.

**Every figure below is a tool result against the predictive ASAP7 model.** No
part of this block is or can be fabricated: ASAP7 is a predictive PDK, there is
no silicon, no measurement and no tape-out, and nothing here is a link-rate or
interoperability claim. "UCIe-class" names the design target, not compliance
with any specification. Failing rows are recorded as failing, not smoothed.

## Where the numbers come from

| Record | Role | Basis, stated |
|---|---|---|
| [`sta/slice.sta.r5.report.json`](sta/slice.sta.r5.report.json) | Fmax and power per corner, hold slack, setup slack | Pre-route `klt sta` sweep, `geometry_source: "netlist_estimate"`: no placement, no routing, zero wire parasitics. Every Fmax/power figure below is a **pre-route estimate**, not a post-route number. Clock constrained at 0.25 ns (the section 2 target parallel clock). |
| [`layout/pnr/slice.pnr.report.json`](layout/pnr/slice.pnr.report.json) | Routed-slice area, post-route tt timing | OpenROAD place-and-route of the synthesized slice at the **tt** corner only, clock constrained at **0.5 ns** (2 GHz — not the section 2 target). Its integrated post-route STA is single-corner. |
| [`layout/pad_check_record.json`](layout/pad_check_record.json) | Pad-centre vs bump-map comparison | `layout/check_pads.py` on the committed column: drawn 96/0 pad centres vs `layout/bump_map_target.csv`, tolerance 1 nm. A layout check, never a DRC claim (decision 0002). |
| [`evidence/item1.r7.json`](evidence/item1.r7.json) | Design sources attested (RTL, cell netlists) | `klt signoff --attest 1` envelope: presence + content hashes + freshness of every inventoried source. |
| [`evidence/item2.r8.json`](evidence/item2.r8.json) | Committed layout streams attested | `klt signoff --attest 2` envelope over `layout/lane_column.gds` and its inputs; the assembled column's data-lane count, clock-lane index, bump pitch and pad count are recorded in its inventory [`attest/item2.r8.json`](attest/item2.r8.json). |
| [`evidence/item4-lvs/*.report.json`](evidence/item4-lvs/) | LVS records | `klt lvs` records: drawn cells and routed slice vs reference netlists. |
| [`verification/drc/*.envelope.json`](verification/drc/README.md) | DRC records (**stale**) | Last recorded DRC runs. **Both are stale against the committed layout**: they ran on the pre-#149 column geometry, and their `--engine klayout` deck is recorded as a machine-local absolute path, so `klt drc --check` cannot re-verify them off-host (filed upstream; see "Stale records" below). They are linked here as history, not cited as current envelopes. |
| [`verification/functional-verification-16.report.json`](verification/functional-verification-16.report.json) | Functional pass at 16 lanes | Pre-route cocotb bench, cited by item 5. Linked as context; not cited as an item-8 envelope (no freshness command exists for it — filed upstream). |

Power basis, carried by every power figure from the STA record
(`corners.<i>.power_basis`): `activity: null`, `activity_source:
"engine_default"`, `parasitics: "estimate_only"` — an **engine estimate at
default activity against estimated parasitics**, not an annotated power run.
Predictive-model estimate only.

## Per-corner metrics (digital partition)

Bound mechanically in [`manifests/attest/item8.json`](manifests/attest/item8.json)
(`metrics[corner][metric] -> {envelope, field}`); the envelope re-reads these
fields on every re-attest, so a stale record fails the check rather than a
stale number being reprinted here.

| Metric | TT | SS | FF | Bound to | Basis |
|---|---|---|---|---|---|
| Fmax (MHz) | 4535.92 | 2882.67 | 6049.89 | `sta/slice.sta.r5.report.json` → `corners.<0/1/2>.fmax_mhz` | Pre-route estimate at the 0.25 ns target clock. Judged against the section 2 rate row: target 16 GT/s at 4:1 needs a 4 GHz parallel clock — met by the estimate at tt/ff, **not** at ss (setup -0.0969 ns, 156 violations). |
| Power (mW) | 0.8697 | 0.6873 | 1.1144 | `corners.<0/1/2>.estimated_power_mw` | Engine estimate at default activity, estimated parasitics (see basis above). No power budget row exists in the spec; this is recorded, not graded. |
| Area (um^2) | 945.994 | 945.994 | 945.994 | `layout/pnr/slice.pnr.report.json` → `core_area_um2` | The **routed slice** (synthesized datapath, tt corner run; area is corner-independent). Corner-independent, so the same field binds all three corners. |

Post-route context (single corner, from the P&R record, not part of the
per-corner bindings): tt fmax **3731.41 MHz**, power 0.6889 mW, worst slack
+0.232 ns at the 0.5 ns constraint, 0 setup / 0 hold violations, clock skew
0.00771 ns. Real parasitics cut the tt Fmax from the 4535.92 MHz pre-route
estimate to 3731.41 MHz — below the 4 GHz parallel clock the 16 GT/s target
needs.

Area caveat: the spec's `s4-area-budget` row budgets a **lane cell** (bump
pitch x two pitches = 45 x 90 um = 4050 um^2 at target). `core_area_um2` is
the routed slice's core area — a different quantity for a different artifact.
The `s4-area-budget` row below is judged against the lane-cell geometry; the
slice figure is recorded alongside, not substituted.

## Section 1 — Module slice

Spec: [`spec/ucie-phy.md` § 1](spec/ucie-phy.md). Target: 16 data lanes +
1 forwarded-clock lane per direction, no spare lanes.

| Row | Target | Recorded | Verdict | Evidence |
|---|---|---|---|---|
| `s1-data-lanes` | 16 per direction | 16 data lanes; the assembled column holds 17 lane cells (16 data + 1 clock, `data_lanes: 16`, `lane_cells: 17`) and the RTL instantiates the same | **pass** | [item1.r7](evidence/item1.r7.json), [item2.r8](evidence/item2.r8.json) |
| `s1-clock-lanes` | 1 per direction | 1 forwarded-clock lane per column, at the centre (`clock_lane_index: 8` of 17) | **pass** | [item1.r7](evidence/item1.r7.json), [item2.r8](evidence/item2.r8.json) |
| `s1-spare-lanes` | none | none present — no spare/redundancy lane in the column or the RTL | **pass** | [item1.r7](evidence/item1.r7.json), [item2.r8](evidence/item2.r8.json) |

## Section 2 — Data rate and clock ratio

Spec: [`spec/ucie-phy.md` § 2](spec/ucie-phy.md). A rate row is met when
**post-route** STA closes setup and hold at the parallel clock, at **every**
section 6 corner, with the section 4 serializer boundary. Full/half-rate
clocking rejected for the target (decision 0004).

| Row | Target | Recorded | Verdict | Evidence |
|---|---|---|---|---|
| `s2-rate-per-lane` | 16 GT/s (fallback 4) | Pre-route estimate closes 4 GHz (16 GT/s equivalent) at tt/ff but **fails at ss** (-0.0969 ns setup). The only post-route datum is tt-only (P&R integrated STA, 0.5 ns constraint): Fmax 3731.41 MHz — under the 4 GHz the target needs. No post-route corner sweep exists (item 7 `unmet`). Neither the target nor the fallback (1 GHz parallel clock) is proven post-route at all corners. | **fail** | [sta r5](sta/slice.sta.r5.report.json) |
| `s2-parallel-clock` | 4 GHz (fallback 1) | Committed as the 0.25 ns constraint in [`sta/slice.sta.json`](sta/slice.sta.json), but the highest parallel clock with post-route support is the tt-only P&R estimate, 3731.41 MHz — below target. | **fail** | [sta r5](sta/slice.sta.r5.report.json) |
| `s2-serialization-ratio` | 4:1 (quarter-rate) | `rtl/lane_tx_ser.v` takes a 4-bit parallel word per clock and shifts two 2-bit streams to the drawn-cell boundary; `rtl/lane_rx_des.v` mirrors it; full/half-rate clocking rejected by decision 0004 | **pass** | [item1.r7](evidence/item1.r7.json), [sta r5](sta/slice.sta.r5.report.json) |

## Section 3 — Bump map

Spec: [`spec/ucie-phy.md` § 3](spec/ucie-phy.md). Pad centres vs the committed
map are a layout-evidence check (decision 0002), never "DRC clean": the DRC
deck checks no PAD/bump rule (klayout-tools#3807).

| Row | Target | Recorded | Verdict | Evidence |
|---|---|---|---|---|
| `s3-bump-pitch` | 45 um | 45 um (`bump_pitch_um: 45`); drawn pad centres match the 45 um map 34/34 within 1 nm | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |
| `s3-bumps-per-lane` | 2 (one TX, one RX) | 34 pads over 17 lane cells = 2 per cell | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |
| `s3-bump-assignment` | one column, lane order = bump order, clock at centre | 34/34 matched, 0 missing/extra/misplaced; clock lane at column centre (index 8) | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |
| `s3-bump-representation` | drawn pad shape on ASAP7 `Pad` over V9/M9 + committed map file | Pads drawn on stream 96/0 (decision 0002 — the number the klt deck reads; pinned files disagree, klayout-tools#3807); map committed as [`layout/bump_map_target.csv`](layout/bump_map_target.csv). **PAD-layer rules are not DRC-checked** — this row is layout evidence only. | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |

## Section 4 — Lane cell

Spec: [`spec/ucie-phy.md` § 4](spec/ucie-phy.md). The boundary puts the
highest-rate logic in drawn cells timed through Liberty models, not synthesis.

| Row | Target | Recorded | Verdict | Evidence |
|---|---|---|---|---|
| `s4-cell-width` | 45 um (1 bump pitch) | 45 um — the column is a rigid row of cells at the 45 um bump pitch | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |
| `s4-cell-height` | 90 um (2 bump pitches) | 90 um — one cell spans two bump rows of the committed map | **pass** | [item2.r8](evidence/item2.r8.json), [pad record](layout/pad_check_record.json) |
| `s4-area-budget` | 4050 um^2 per lane | Lane cell = 45 x 90 um = 4050 um^2, exactly the target budget (the budget derives from the pitch rows). The routed **slice** core is 945.994 um^2 at 40.4467% utilization — recorded for completeness, a different basis (see caveat above), not substituted for the lane-cell figure. | **pass** | [item2.r8](evidence/item2.r8.json), [P&R record](layout/pnr/slice.pnr.report.json) |
| `s4-drawn-cells` | TX driver, RX front-end | Four drawn cells committed as GDS with reference netlists: `tx_cell`, `rx_cell`, `tx_clk_cell`, `rx_clk_cell` — all `klt lvs` **match**, 0 errors | **pass** | [item1.r7](evidence/item1.r7.json), [item2.r8](evidence/item2.r8.json), [tx_cell LVS](evidence/item4-lvs/tx_cell.r2.report.json) |
| `s4-serializer-boundary` | synthesized 4:1 ser/des; last 2:1 stage + output driver in the drawn TX cell; input stage + sampler in the drawn RX cell | Boundary-port table in [`rtl/README.md`](rtl/README.md) (`lane_tx_ser.v` stops at the drawn-cell boundary; the RX path enters the drawn cell and the deserializer resumes inside); cell-level LVS matches | **pass** | [item1.r7](evidence/item1.r7.json), [tx_cell LVS](evidence/item4-lvs/tx_cell.r2.report.json), [slice LVS](evidence/item4-lvs/slice_routed.r13.report.json), [sta r5](sta/slice.sta.r5.report.json) |

## Section 7 — Signoff

Spec: [`spec/ucie-phy.md` § 7](spec/ucie-phy.md). "Results are append-only
evidence; a failing run is recorded, not replaced."

| Row | Meaning | Recorded | Verdict | Evidence |
|---|---|---|---|---|
| `s7-drc-clean` | `klt drc`, zero violations on the final GDS + expectations satisfied + unchecked-rule list stated | **Not clean, and the records are stale**: last runs recorded 14496 violations (lane column) and 906 (routed slice) — both on the pre-#149 column geometry, and both decks are recorded as machine-local paths so `klt drc --check` cannot re-verify them off-host (see "Stale records"). Item 3 is `unmet` / `no_evidence` on both partitions. The unchecked-rule list (PAD, bump, 67 others) is stated in [`spec/asap7-bringup.md`](spec/asap7-bringup.md). | **fail** | [item2.r8](evidence/item2.r8.json) (current layout the records must be re-taken against), [DRC records](verification/drc/README.md) (stale, linked as history) |
| `s7-lvs` | drawn cells **and** lane column match by `klt lvs`, zero errors | Drawn cells: `match`, 0 errors (all four). Routed slice ([`slice_routed.r13.report.json`](evidence/item4-lvs/slice_routed.r13.report.json)): **`mismatch`**, 86371 errors (`device.unmatched` 55444 dominant — the shipped-cell compare bring-up gap). Item 4: analog `met`, digital `unmet` / `check_failed`. | **fail** | [tx_cell LVS](evidence/item4-lvs/tx_cell.r2.report.json), [slice LVS](evidence/item4-lvs/slice_routed.r13.report.json) |
| `s7-sta` | post-route setup and hold slack >= 0 at every corner, at the section 2 clock, section 5 constraints recorded | Pre-route corner sweep (`netlist_estimate`): setup **fails at ss** (-0.0969 ns, 156 violations; tt +0.02954, ff +0.08471); hold passes everywhere (+0.03431..+0.0742). Post-route: tt-only P&R STA closes at 0.5 ns (not the section 2 clock) with Fmax 3731.41 MHz. The SDF-annotated post-route run is a recorded refusal, not a pass: back-annotation "did not fully apply: 8 diagnostic(s)" ([functional-verification-sdf.report.json](verification/functional-verification-sdf.report.json)) — item 7 `unmet` / `no_evidence`. Clock uncertainty is not applied by `klt sta` (klayout-tools#4240), stated in [sta/README.md](sta/README.md). | **fail** | [sta r5](sta/slice.sta.r5.report.json), [P&R record](layout/pnr/slice.pnr.report.json) |
| `s7-bump-map` | drawn pad centres equal the committed map within one database unit | `status: "pass"`, 34/34 matched, tolerance 4 dbu (1 nm at the deck dbu), 0 missing / extra / misplaced | **pass** | [pad record](layout/pad_check_record.json) |

**Score: 12 pass, 7 fail.** The failing rows — rate/parallel-clock closure,
DRC, LVS (digital), STA — are the open work tracked as T1 items 3, 4, 5 and 7
(issues #19, #20, #27, #72). This report records them; it does not fix them.

## Stale records, stated plainly

- **DRC (both records)**: taken before the #149 pin-geometry re-assembly of
  `layout/lane_column.gds`, so their violation counts describe geometry that is
  no longer committed; and each `--engine klayout` record names its deck by an
  absolute, machine-local path, so `klt drc --check` drifts on any other host.
  Fresh DRC runs against the committed column are item 3's outstanding work
  (#19). This is why `s7-drc-clean` cites the current-layout attestation
  ([item2.r8](evidence/item2.r8.json)) as its item-8 envelope, and links the
  DRC records as history only.
- **`sta/slice.sta.r6.report.json`** is **not** the current STA record: it
  carried the RPIPE=1 read-pipeline variant that was not adopted, and its
  recorded input hash no longer matches the committed netlist. The current
  record is r5 (the one the block manifest cites for item 5), and
  `python3 -I sta/regen.py --check-input` enforces exactly that match.
- **Power** is an engine estimate at default activity against estimated
  parasitics, never an annotated run (see basis above).
- **`verification/functional-verification-16.report.json`** and the -8 report
  are cited by item 5 and linked above as context; they have no freshness
  command today, so they are not item-8 envelopes.

## Machine check

```
klt signoff --attest 8 --inventory manifests/attest/item8.json --check manifests/evidence/item8.json
klt signoff --manifest manifests/asap7-ucie-phy.json --check manifests/asap7-ucie-phy.signoff.json
```

The inventory (`kind: t1-attestation-inventory`, `t1_item: 8`) declares this
report, the 19 ratified rows of sections 1-4 and 7, the citation map above, a
freshness command per cited envelope, and the per-corner metric bindings. The
envelope (`kind: generic`) is minted by `--attest 8` and re-reads every cited
record on every check: a stale record fails the check rather than this report
quietly outliving its evidence.
