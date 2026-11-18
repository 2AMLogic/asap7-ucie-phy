# slice synthesis variant sweep, r1 (issue #236)

Append-only record. Pre-route `klt sta` (`geometry_source: netlist_estimate`, zero wire parasitics),
0.25 ns section-2 clock, tt/ss/ff of `asap7sc7p5t_rvt`, klt 0.9.2 (the repo pin), lambdapdk 0.2.17,
single local runs via [`variant_sweep.py`](variant_sweep.py). Each row is a trial netlist synthesized
from `design/synth/slice.synth.json` with only the stated `constraints` change; **no committed file
was changed and the committed netlist is not one of these**. Predictive-model figures only.

"Deviating" = instances of the ten SDT.ACTIVE.AUX.2 masters (`constraints.dont_use`) in the trial
netlist, counted from the netlist text. The baseline rows reproduce r5 and r7 exactly.

| Variant | Cells | Deviating | Fmax tt / ss / ff (MHz) |
|---|---|---|---|
| no `dont_use` (= r5 config) | 2503 | OAI22xp33 112, BUFx2 83 | 4535.92 / 2882.67 / 6049.89 |
| committed (`dont_use`, `driving_cell` BUFx2) = r7 | 2449 | 0 | 2881.42 / 1867.82 / 3828.98 |
| committed, `clock_period_ns` 0.20 / 0.15 / 0.10 / 1.0 | 2449 | 0 | identical to r7 at every value |
| committed, `load_ff` 1.0 | 2442 | 0 | 3060.31 / 1991.59 / 4085.16 |
| committed, `load_ff` 8.0 | 3047 | 0 | 2982.93 / 1993.16 / 4058.88 |
| committed, `driving_cell` **BUFx3** | 2504 | 0 | **4535.92 / 2882.67 / 6049.89** |
| committed, `driving_cell` BUFx12f | 2504 | 0 | 4535.92 / 2882.67 / 6049.89 |
| `driving_cell` BUFx3, `load_ff` 8.0, 0.10 ns | 3102 | 0 | 4387.65 / 2903.15 / 5945.20 |

Worst setup slack, `driving_cell` BUFx3: tt +0.02954 / ss -0.0969 / ff +0.08471 ns (0 / 156 / 0
violations); hold +0.05125 / +0.0742 / +0.03431 (0 violations). r5 was +0.030 / -0.097 / +0.085.

## Findings

- **Candidate 2 (exclude only the masters that survive) has nothing to recover.** Of the ten excluded
  masters only OAI22xp33 and BUFx2 appear in the pre-swap netlist (112 and 83); the other eight are
  used zero times with or without the exclusion, and both used masters carry markers.
- **Candidate 3 (tighter ABC target) does nothing.** `clock_period_ns` 1.0 through 0.10 gives a
  byte-identical result; ABC's mapping is not timing-limited by it here.
- **The loss is not irreducible.** The committed `abc_constr.driving_cell` is `BUFx2`, one of the
  excluded masters. Replacing it with a non-excluded buffer (BUFx3 or BUFx12f) recovers the r5
  pre-route Fmax and slack to the reported digits with zero deviating masters. The mechanism inside
  ABC is **not established** by this run; the measurement shows the dependence, not the cause.
- **Candidate 1 (substitution table) is not expressible**: the pinned klt's `synthesize` request has
  `dont_use` and `abc_constr` (`driving_cell`, `load_ff`) and no substitution field.

## Not established

- The BUFx3 netlist was **not adopted** and its DRC was **not re-run**. Adopting it changes
  `design/netlist/slice_asap7.v`, which invalidates the P&R, SDF, LVS and DRC records that bind it.
  Zero SDT.ACTIVE.AUX.2 markers on a placed column is expected from the per-cell measurement
  (no deviating master is instantiated) but is not shown here.
- Pre-route estimate only; the ss corner still fails setup at 0.25 ns, as in r5.
- Post-route timing of the variant, and the 0.5 ns P&R constraint, were not run.
