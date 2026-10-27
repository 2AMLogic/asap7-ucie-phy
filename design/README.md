# design

Sources and derived netlists for T1 item 1 (design sources), attested by
`attest/item1.json` and `evidence/item1.json`. Every figure is a tool result
against the predictive ASAP7 model; nothing here is a fabricated part.

| Path | Role |
|---|---|
| `gen_cells.py` | source of the drawn cells (`tx_cell`, `rx_cell`, `tx_clk_cell`, `rx_clk_cell`): device-level topology, ports as in `rtl/README.md`. Topology only: not simulated (decision 0003), no sizing or rate claim |
| `netlist/{tx,rx,tx_clk,rx_clk}_cell.sp` | derived SPICE from `gen_cells.py` |
| `synth/slice.synth.json` | `klt synthesize` request: top `slice`, N=16, ASAP7 RVT, TT, no clock target |
| `synth/regen.py` | reproduces the synthesis netlist from the pinned lambdapdk archive |
| `netlist/slice_asap7.v` | derived gate-level netlist of `slice` (generated, ~16k lines) |

## Regenerate / check

```
python3 -I design/gen_cells.py [--check]                      # needs nothing but python3
python3 -I design/synth/regen.py [--check] [--pdk-archive F]  # needs klt >= 0.8.0 and yosys
```

`--check` exits 0 when the committed file reproduces and 3 when it drifted.
`regen.py` downloads the archive pinned in `spec/asap7-bringup.md` (sha256
verified) unless `--pdk-archive` is given, and unpacks nothing into the repo.
It merges the five gzipped RVT TT Liberty cell-group files into one scratch
file because klt's resolver does not read lambdapdk's split, gzipped Liberty
(tool gap: 2AMLogic/klayout-tools#4184).

Attestation: `klt signoff --attest 1 --inventory attest/item1.json -o evidence/item1.json`,
then `klt signoff --attest 1 --inventory attest/item1.json --check evidence/item1.json`.
The synthesis freshness command is `local_only` (CI has no Yosys or PDK); CI
re-hashes every inventoried file instead.
