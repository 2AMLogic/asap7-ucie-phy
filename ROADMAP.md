# Roadmap

A UCIe-class die-to-die PHY lane column at micro-bump pitch on ASAP7, a predictive PDK: layout, DRC,
LVS and timing evidence only, never fabricated.

Status as of 2026-11-13, `main` @ `f861ca2`. Every figure below is a tool result against a predictive
model. `WORK_PLAN.md` is the generated label view of the tracker; this file says what comes next.

## Where it stands

The verdict of record is `manifests/asap7-ucie-phy.signoff.json` (`klt signoff`, klayout-tools 0.9.1,
the pin in `.github/klt-version`): **9 of 22 T1 rows met, 1 not applicable, tier `null`**. The block is
mixed-signal, so each of the 11 T1 items is graded twice (analog = the four drawn TX/RX cells,
digital = `slice` and its submodules). Tracker: #3.

| T1 item | Analog | Digital | Evidence or owner |
|---|---|---|---|
| 1 Design sources | met | met | `evidence/item1.r7.json` |
| 2 Layout | met | met | `evidence/item2.r7.json` (17-lane column, pad check `pass`) |
| 3 DRC clean | unmet | unmet | #19, #64; `verification/drc/README.md` |
| 4 LVS clean | met | unmet (`check_failed`) | `evidence/item4-lvs/*.r2.report.json`; #20 |
| 5 Corner verification | unmet | unmet (`check_failed`) | `sta/slice.sta.r5.report.json`; #72 |
| 6 Monte Carlo | unmet (declared gap) | not applicable | decisions 0006, 0008 |
| 7 Post-layout verification | unmet | unmet | #23 |
| 8 Characterization report | unmet | unmet | #24 |
| 9 Testbenches shipped | met | met | `manifests/evidence/item9.r2.json` |
| 10 Repo hygiene | met | met | `manifests/t1-item10.envelope.json` |
| 11 Power delivery | unmet | unmet | #27, #66 |

What the unmet rows rest on today:

- **DRC (item 3).** The last recorded column run is 8,208 violations across 7 rules, all on slice
  instances, each family attributed to a filed tool gap (PR #67, #68). That run used klt 0.8.0 on a
  column stream that is no longer the committed one: the slice was re-routed (PR #115) and the column
  regenerated (PR #118) afterwards, and no DRC run exists on the current `layout/lane_column.gds`.
- **LVS (item 4, digital).** The four drawn cells match. The routed datapath is `mismatch` under
  klt 0.9.1 (r10, r11; PR #116): device totals are within 80 (29436 layout / 29356 reference), but the
  layout extracts 2 top-level pins against 266 in the reference and the cause is recorded as
  undetermined (`spec/asap7-bringup.md`, last section).
- **Timing (item 5, digital).** Pre-route `klt sta` at RVT TT/SS/FF: tt +0.030, ss -0.097, ff +0.085 ns
  (r5, PR #98). The functional suite passes at 16 and 8 lanes. Two ruled levers (decisions 0007, 0009)
  left ss negative.
- **Circuit simulation.** `tx_cell` has one logic-level BSIM-CMG run, passing at TT/SS/FF on ngspice 47
  (decision 0010, PR #129). `rx_cell` and the two clock cells have none.
- **Post-layout (item 7).** `layout/slice_routed.v` and `layout/slice_routed.sdf` are committed with a
  harness (PR #123); the SDF-annotated run does not complete under klt 0.9.1
  (`verification/functional-verification-sdf.report.json` records the refusal).
- **Power (item 11).** The M5/M6 straps were dropped to clear DRC families, so the slice's rows are tied
  only by M1/M2 followpin rails (`verification/drc/README.md`, issue #66); LVS `power_connectivity` is
  `unchecked`.

## Now

Can start today; one PR each. None of these changes the spec, waives a rule or needs a new tool release.

1. **Record a DRC run on the current committed column.** Done when a new append-only run record under
   `verification/drc/` reports `klt drc` at the pinned klt on the committed `layout/lane_column.gds` and
   `layout/slice_routed.gds` (input hashes in the record), with per-rule counts and the `coverage` block,
   and `verification/drc/README.md` gains a dated section comparing it with the 8,208 baseline. No issue
   yet; feeds #64 and #19.
2. **Find out why the routed slice extracts 2 top-level pins against 266.** Done when
   `spec/asap7-bringup.md` gains a dated section stating whether `layout/slice_routed.gds` carries port
   labels for the reference's top-level ports, on which layers, and what `klt lvs` reads as a pin; and
   either a new LVS record under `evidence/item4-lvs/` from a stream or request that fixes it, or a tool
   gap filed at klayout-tools and linked. Part of #20; no separate issue yet.
3. **Logic-level BSIM-CMG runs for `rx_cell`, `tx_clk_cell` and `rx_clk_cell`.** Done when each has an
   adapted netlist, testbench and `klt sim` request under `design/sim/` and a TT/SS/FF report under
   `sim/`, within the limits of decision 0010 (logic levels only, no delay or rate claim). No issue yet.
4. **Bring the README status in line with the verdict.** The Status paragraph, the maturity-ladder
   position, the simulation paragraph and the T1 section predate the drawn cells, the column, the
   analog LVS matches, STA r5 and decision 0010. Done when each of those statements matches
   `manifests/asap7-ucie-phy.signoff.json` and the item-10 envelope and verdict are regenerated and pass
   their `--check` commands (README is an inventoried file). No issue yet.
5. **Point the tracker at the verdict of record (#3).** Its checklist still reads 0 of 11 met; its own
   criterion says the body becomes a link to the committed `klt signoff` report. A tracker edit, not a PR.

## Next

Unblocked by a named item above or by a tool release.

- **Re-run routed-datapath LVS (#20)** once Now 2 identifies the pin cause. Done when a `klt lvs` report
  with `status: match` and `power_connectivity.status` not `mismatch` is cited by the manifest, or the
  failing report and its blocker are recorded.
- **SDF-annotated functional re-run (#23).** Waits on a published klayout-tools release containing the
  fix for klayout-tools#5296 (closed 2026-11-11; 0.9.1 is still the latest release) and a bump of
  `.github/klt-version`. Done when `verification/functional_verification_sdf.sh` writes a passing
  annotated report and the manifest cites it under `7.digital`.
- **Deck-clean power grid on the slice (#66).** Its recorded blocker (#64's baseline) now exists on
  `main`; re-scope it against the Now 1 record. Done when `layout/pnr/slice.pnr.report.json` reports
  power delivery other than `partial` and the column DRC shows no new strap-related families.
- **Clear the router-metal families and claim DRC (#64, then #19).** Waits on klayout-tools#4495
  (router V1 landing pads, open). Done when the Now 1 command reports `status: clean` on the committed
  column and the report is cited with its `coverage` fields quoted.
- **Power-delivery evidence (#27).** After #20 and #66. Done when a `klt erc` supply spec and report for
  the column are committed and `klt signoff` grades item 11 `met`.
- **Characterization report (#24).** After #72 and #23. Done when one per-spec-row report with its
  generic envelope is cited and item 8 is `met`.

## Later

Direction, each with the question to answer first.

- **Post-route timing closure at 16 GT/s (spec section 7).** Can the open flow produce parasitics for
  the routed ASAP7 slice at all? `klt place-and-route` refused post-route SPEF/SDF for this library
  (klayout-tools#4468, closed as an early rejection, not support).
- **Analog corner evidence (item 5 analog) and item 7 analog.** Which claims would a corner matrix be
  graded against, given that no ratified spec row is an analog performance row (decisions 0006, 0008)?
- **Status of the declared analog gaps after decision 0010.** `manifests/item5-analog-gap.json` and
  `manifests/item6-analog-gap.json` still give the ngspice 42 blocker as their reason; does one
  functional run change their status? Decision 0010 leaves this to a follow-up.
- **The bump interface.** The packaged deck does not check `PAD` (96/0); the pad-centre checker covers
  placement only. What, beyond centres, can be checked at the bump layer with the tools as they are?

## Blocked and waiting

- **#72 (item 5 digital): needs a ruling.** The issue carries a ranked decision on a third lever after
  r5 and r6 left ss at -0.097 ns: restructure the `empty` self-loop again, carry the result into
  post-route STA, or change the spec by decision record.
- **#19 / #64: needs a ruling as well as a tool fix.** 5,824 of the 8,208 recorded violations are
  `SDT.ACTIVE.AUX.2` inside shipped standard cells; klayout-tools#4496 was closed without a deck change,
  so under an unwaived deck the column is expected to stay `violations` even after #4495.
- **#134, #136:** proposals (merge the two cocotb runners; trim four superseded 38 MB LVS reports)
  awaiting approval. No open issue carries the ready label today; the Now items are the startable work.

## Not planned

- Fabrication, measurement, or any silicon rung: ASAP7 is predictive.
- UCIe compliance or interoperability claims, the protocol and adapter layers, the clock source, the
  package, and analog link margin of a real channel (README, Scope).
- Relaxing the ratified spec, or waiving or filtering deck rules, to make a row pass.
