# 0011: A .json evidence record may be a JSON document stream

Status: accepted. Date: 2026-11-16. Issue: #191. Directed by: operator ruling
2026-11-15 (@rjwalters, attended `/fleet:decide` round 20261111-r14, q103) — this
record implements the ruling; ratification is the review of this PR.

## Context

`evidence/item4-lvs/slice_routed.r13.refnets.json` is not one JSON document. It is
two pretty-printed JSON objects concatenated in one file, 785 bytes, exactly two
documents — and that form is the deliberate contract of both of its committed
sides. Its producer, `evidence/item4-lvs/slice_routed.r13.refnets.py` (usage at
`:20`, `<netlist> [<netlist2> ...]`), prints one `json.dumps(result, indent=2)` per
netlist argument (`:216`): two netlists in, two documents out. Its only consumer,
`evidence/item4-lvs/slice_routed.r13.netdiff.py`, reads the file with
`json.JSONDecoder().raw_decode()` in a loop (`:345-353`) and asserts on
`refnets_baseline[0]` and `refnets_baseline[1]` (`:770`, `:777`): a
single-document file would break it.

The extension `.json` therefore names a format the file intentionally is not, and
every single-document gate and consumer rejects it (`json.loads`:
`ValueError: Extra data: line 16 column 1 (char 383)`). The obvious repair —
renaming it `.jsonl` — edits a committed evidence record's name and strands the
hand-written pointer to it inside another committed record
(`evidence/item4-slice-attempt.r13.json:30`), which cannot be repaired by editing
that record. The rename conflicts with the repository's ratified append-only
clause, `spec/decisions/0005-signoff-definitions.md:20`: "Evidence records are
append-only; failures are kept."

The operator chose, from three dispositions, to write the convention down rather
than rename the file or carry a named exception forever. Decision #166's gate
(`verification/check-records-json.sh`) had carried exactly one such exception for
this path — a literal-path carve-out that self-retired if the file disappeared or
started parsing — which named around the gap instead of closing it.

## Decision

A tracked `.json` project record is valid iff its bytes are **one or more JSON
documents separated only by whitespace** — that is, a
`json.JSONDecoder().raw_decode()` loop consumes the file to its end. Both halves
of the statement are the ruling:

1. A record **may** be a JSON document stream (the n > 1 case is legitimate, not a
   defect).
2. Validity gates **must validate per document**, so a stream record is checked
   for exactly what it claims to be rather than excepted by name.

A single-document record is the `n = 1` case, so the rule is a strict
generalization of "is one JSON document": no existing record changes meaning, and
every tracked record satisfies it today. The extension stays `.json`; nothing is
renamed, so no committed pointer is stranded and 0005's append-only clause needs
no exception to hold. The single copy of the walk is
`verification/check-records-json.sh` (`--validate`, stdlib `raw_decode` per
document, git and python3 only); the default gate mode runs it first, then hands
`klt env-provenance lint-envelope` the single-document partition — klt cannot
read a stream ("Extra data: …", no per-document option at the 0.9.2 pin; filed
upstream as [`2AMLogic/klayout-tools#5887`](https://github.com/2AMLogic/klayout-tools/issues/5887)).

## Consequences

- #166's named `STREAM_EXCEPTION` path and its self-retire guard are removed from
  `verification/check-records-json.sh`; no literal record path remains in the gate.
- `check.sh`'s second, independent single-document `json.loads` loop is replaced
  by a call to the gate's `--validate` mode: one copy of the rule, three consumers
  (`--validate`, the default gate, `check.sh`).
- `manifests/t1-item10.envelope.json` is re-attested in the same commit as the
  gate edit — the gate is an item-10 inventory member, so editing it restales the
  envelope. Only the envelope changes; the inventory member list and check argv
  are untouched.
- **klt absolute-path coverage note**: a multi-document stream record gets the
  per-document validity verdict but is *not* scanned by `lint-envelope` for
  absolute host paths, because klt cannot read a stream (#5887). The partition
  site in the gate carries this note in a comment; #172 — which plans to make the
  gate findings-fatal on `lint-envelope` exit 3 — must decide how stream records
  are covered (splitting each into temp per-document files and remapping klt's
  diagnostics back to the real path is the known option) before shipping that
  gate, or a newly committed stream record could carry an absolute path and pass.
- 0005 is untouched. Its append-only clause now holds with no named exception
  anywhere in the gate.
- This record is not added to `manifests/t1-item10-inventory.json` here;
  decision records are bound later in a separate batched attest commit
  (`b4e34c1` is the precedent).
