# design

Sources and derived netlists for T1 item 1 (design sources), attested by
`attest/item1.r8.json` and `evidence/item1.r9.json`. Every figure is a tool result
against the predictive ASAP7 model; nothing here is a fabricated part.

| Path | Role |
|---|---|
| `gen_cells.py` | source of the drawn cells (`tx_cell`, `rx_cell`, `tx_clk_cell`, `rx_clk_cell`): device-level topology, ports as in `rtl/README.md`. Topology only; all four cells have a logic-level simulation (decision 0010 for `tx_cell`, the same route extended to the other three); no sizing or rate claim |
| `netlist/{tx,rx,tx_clk,rx_clk}_cell.sp` | derived SPICE from `gen_cells.py` |
| `synth/slice.synth.json` | `klt synthesize` request: top `slice`, N=16, ASAP7 RVT, TT, 0.25 ns clock target, `abc_constr` BUFx2 / 3.898 fF (decision 0009 option 3) |
| `synth/regen.py` | reproduces the synthesis netlist from the pinned lambdapdk archive |
| `sim/regen.py` | re-runs klt's BSIM-CMG netlist adaptation (`adapt_extracted_netlist`, decision 0010) so `tx_cell.osdi.sp` cannot drift from `netlist/tx_cell.sp` while `gen_cells.py --check` stays green |
| `sim/` | ASAP7 BSIM-CMG simulation of all four drawn cells: adapted netlists `<cell>.osdi.sp`, testbenches `<cell>.tb.sp`, corner lib `asap7_bsimcmg.lib`, `klt sim` requests `<cell>.sim.json`; reports in `../sim/<cell>.batch.report.json` (decision 0010 for `tx_cell`, same route extended to the other three). The adapted netlists are produced by klt's `adapt_extracted_netlist`: `tx_cell` is adapter-bound (`sim/regen.py --check` is its byte-for-byte drift gate and its committed header stays adapter-emitted, sha256-pinned by its batch report), while the other three are kept by hand under the truthful provenance line and drift-checked by `gen_cells.py --check` |
| `lambdapdk.py` | pinned lambdapdk URL/sha256 and Liberty cell-group merge, shared by `synth/regen.py` and `sta/regen.py` |
| `netlist/slice_asap7.v` | derived gate-level netlist of `slice` (generated, ~16k lines) |

## Regenerate / check

```
python3 -I design/gen_cells.py [--check]                      # needs nothing but python3
python3 -I design/synth/regen.py [--check] [--pdk-archive F]  # needs yosys and klt `main` >= b8eaf053a (`abc_constr`; 0.8.0 rejects the field)
python3 design/sim/regen.py [--check]                         # needs klayout_tools; no `-I`, which hides it (layout/README.md)
```

`--check` exits 0 when the committed `netlist/` files and the adapted `sim/`
netlists both reproduce, and 3 when either drifted.
`regen.py` downloads the archive pinned in `spec/asap7-bringup.md` (sha256
verified) unless `--pdk-archive` is given, and unpacks nothing into the repo.
It merges the five gzipped RVT TT Liberty cell-group files into one scratch
file because klt's resolver does not read lambdapdk's split, gzipped Liberty
(tool gap: 2AMLogic/klayout-tools#4184).

Attestation (record r9 supersedes the append-only records r1-r8, kept as history in
`attest/` and `evidence/`): `klt signoff --attest 1 --inventory attest/item1.r8.json
-o evidence/item1.r9.json`, then
`klt signoff --attest 1 --inventory attest/item1.r8.json --check evidence/item1.r9.json`.
The synthesis freshness command is `local_only` (CI has no Yosys or PDK); CI
re-hashes every inventoried file instead.
