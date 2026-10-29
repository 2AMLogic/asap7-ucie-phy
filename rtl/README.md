# rtl

Digital half of the lane datapath (tracker #3, items 1 and 9). Synthesizable Verilog-2001;
the drawn TX/RX cells are not here. No rate or timing claim: rate is an STA statement (spec
section 2).

| File | Role |
|---|---|
| `slice.v` | Slice wrapper: `N` data lanes (default 16; 8 also elaborates) plus one forwarded-clock lane, handshake, CDC |
| `lane_tx_ser.v` | Per-lane TX: 4-bit word to two 2-bit streams, stops at the drawn-cell boundary |
| `lane_rx_des.v` | Per-lane RX: two 2-bit streams from the drawn cell back to a 4-bit word |
| `rx_cdc_fifo.v` | 8-entry gray-pointer async FIFO from the forwarded-clock domain into the parallel clock |

## Drawn-cell boundary ports (spec section 4)

Line order within a lane is `d[0], d[1], d[2], d[3]`. Stream `a` carries `d[0]` then `d[2]`;
stream `b` carries `d[1]` then `d[3]`; index `[0]` of a 2-bit stream is first. The drawn TX cell
does the remaining 2:1 stages and the driver; the drawn RX cell does the input stage and the
sampler. Lane `i` uses bits `[2*i +: 2]`.

| Port | Dir | Width | Meaning |
|---|---|---|---|
| `tx_a`, `tx_b` | out | `2*N` each | per-lane TX streams to the drawn TX cell, registered on `clk` |
| `tx_fwd_en` | out | 1 | forwarded-clock lane: gate open for the word presented this cycle |
| `rx_a`, `rx_b` | in | `2*N` each | per-lane RX streams from the drawn RX cell, captured on `rx_clk` |
| `rx_clk` | in | 1 | forwarded clock at the parallel frequency; toggles once per word, only while a word is on the link |

Core side: `clk` (parallel clock), `rst_n`, `rx_rst_n` (asserted asynchronously, deassert
assumed synchronous to its own clock), `link_ready` (link state, out of scope), TX
`tx_valid`/`tx_ready`/`tx_data[4*N-1:0]`, RX `rx_valid`/`rx_data[4*N-1:0]` (valid only, no
back-pressure; `rx_data` is undefined while `rx_valid` is low), `rx_overflow` (sticky status, forwarded-clock domain).

## Choices to know about

- **Word validity rides on the forwarded clock.** The data lanes carry no valid bit; the clock
  lane's gate (`tx_fwd_en`) opens only for accepted words, and every `rx_clk` edge is one word.
  This is this design's reading of "RX `valid` only"; a different in-band scheme is a spec change.
- **Clock offset tolerance is bounded.** If `rx_clk` runs faster than `clk` the FIFO fills during
  a continuous burst; a burst longer than the 8-entry FIFO absorbs sets `rx_overflow` and drops
  words (no back-pressure exists). The clock source and burst length are the sender's contract.
- `tx_ready` is the registered `link_ready`; the lane registers load only on `valid & ready`.
