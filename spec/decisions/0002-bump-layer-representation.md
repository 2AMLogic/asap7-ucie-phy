# 0002: how the bump map is represented and checked

Status: accepted. Date: 2026-10-17. Issue: #2.

## Context

Open question: does ASAP7 define a layer klt can use for micro-bumps? It does define `Pad` above
M9 (tech LEF, reached by V9), but the pinned files give it different stream numbers and klt's deck
checks only `V9.PAD.EN.2` and `V9.AUX.1` (klayout-tools#3807).

## Decision

1. A bump is one drawn shape on `Pad`, at stream layer **96/0** (the number the klt deck reads), over
   a V9/M9 stack that satisfies the deck's V9 rules.
2. The bump map is committed data (lane, signal, x, y in um) under `layout/`, and is the reference
   for the pitch (45 um target), origin and lane order.
3. The check that drawn pad centres equal the map is a layout check, recorded as such. DRC does not
   check pitch or the pad layer, and no DRC-clean claim is made about pads.

## Consequences

- Moving the stream number to match another pinned file is a new record (and a deck change upstream).
- If klt gains a pad-array check (#3807 item 4) this record is superseded by one that adopts it.
