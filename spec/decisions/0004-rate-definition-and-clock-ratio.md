# 0004: rate definition and clock ratio

Status: accepted. Date: 2026-10-17. Issue: #2.

## Context

A "16 GT/s" row must be a timing-closure statement. The datapath clock ratio sets the period STA must close.

## Decision

The lane datapath is clocked at quarter rate: 4 GHz parallel clock (250 ps) for 16 GT/s, 1 GHz
for the 4 GT/s fallback, 8 GHz (125 ps) for the 32 GT/s stretch. A rate is met when post-route STA
closes setup and hold at that clock at every shipped RVT corner. The last 2:1 stage and the
driver/sampler sit in drawn cells (spec section 4).

Rejected: full-rate (62.5 ps period at 16 GT/s) and half-rate (125 ps) clocking of the datapath for
the target, because the shipped RVT flip-flops are unlikely to close them and the target must not be
chosen to fail; this is a judgement, not a measured result, and is revisited with STA data in the
lane-RTL rung.

## Consequences

Stretch keeps 4:1 at 8 GHz; an 8:1 stretch needs a new record. Clock-quality assumptions are STA
constraints (spec section 5).
