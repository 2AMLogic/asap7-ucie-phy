# 0011: committed evidence records carry absolute host paths only as frozen history; records added or changed are gated forward-only

Status: accepted. Date: 2026-11-16. Issue: #172.

## Context

132 tracked JSON records (the `verification/check-records-json.sh --list` set,
at `origin/main` @ `2591f33` under the `.github/klt-version` pin 0.9.2) carry
63 absolute host path findings (`klt env-provenance lint-envelope`): 48 `/tmp`
scratch paths in 19 files, 8 machine-wide tool prefixes in 6 files, and 7
leaked `/home/ubuntu/...` paths in 7 files — which `klt env-provenance scan`
independently reports as `leak_count: 7`, every finding `kind: home-path`, in
exactly those 7 files. Every one is a committed evidence record, and evidence
records are append-only (decision 0005), so "edit the record" is not available
here: that axis is #136's, parked with the operator, and this record does not
reopen it. The measured argument for a gate rather than another documentation
pass is that three of the seven home-path leaks landed *after* the class was
first documented — the curation comment recording "four leaked paths" posted
2026-11-15 00:29 UTC, and commits `26abef2` (00:35) and `7577199` (09:07) added
three more the same day. Nothing caught them; this gate is the thing that
would have.

## Decision

1. **Class 2 — machine-wide prefixes: declared, not edited.** The measured
   minimal set is `--allow-prefix /usr/bin --allow-prefix /usr/local/bin`
   (63 → 55; adding `/opt/pdk` admits nothing at this tree and is deliberately
   absent). Never add `/tmp`: a per-run scratch path is the canonical
   non-reproducible reference the lint exists to catch, and declaring it would
   make the gate assert nothing. Never add a `/home` prefix: the tool's own
   help rules out a verdict that depends on the linting machine.
2. **Class 1 — `/tmp` scratch: frozen history.** No edit, no re-run. Edits
   belong to #136 (append-only axis); re-runs belong to #20 (item 4 LVS),
   and each failing compare adds ~38 MB (#136).
3. **Class 3 — `/home/ubuntu` leaks: caught going forward.**
   `verification/check-records-json.sh --changed --base <commit>` gates every
   record added or changed by the commit range on BOTH `klt env-provenance
   lint-envelope` (with the class-2 prefix set) and `klt env-provenance scan`;
   exit 3 from either, or exit 1 (a changed record that does not parse),
   fails. The whole-set run stays validity-only — #166's contract is not
   reversed by this record.
4. **The deck exception.** While `2AMLogic/klayout-tools#5709` is open, every
   klt-generated DRC envelope records its deck as a bare absolute host path (a
   uv cache directory keyed by a build hash; measured again at the 0.9.2 pin —
   a fresh envelope still carries it, so a pin bump is not the remedy). A
   fresh envelope is the repo's primary evidence product, so the
   changed-record gate admits exactly one thing: the top-level `deck` field of
   a changed `*.envelope.json` — the dotted field `deck` for lint-envelope,
   the single line carrying that field for scan (scan is line-matched and has
   no exception flag), each matched against the value the envelope itself
   declares. It is a field exception, not a prefix; a run record's prose cites
   `provenance.deck.content_hash`, never a path. Both filters reconcile what
   they classified against the report's own `schema_version` and total
   (`finding_count` / `leak_count`) and fail on any mismatch, so a
   report-schema change under pin drift cannot silently void the exception
   walk. The exception is
   self-limiting — once klt stops writing the absolute path, the finding it
   admits no longer exists — and is REMOVED once #5709 is closed and
   `.github/klt-version` is at or past the fix, verified by regenerating a DRC
   envelope and confirming the top-level `deck` is no longer absolute.
5. **Baseline, recorded so drift is visible.** At `origin/main` @ `2591f33`,
   pin 0.9.2: 132 tracked records, 63 findings (48 `/tmp` in 19 files,
   8 machine-prefix in 6 files, 7 `/home` in 7 files), **55 residual under
   the class-2 prefix set**, `scan` `leak_count` 7. Reproduced unchanged at
   `769cc1f`, the parent tip this record lands on.

The gate fails — it cannot look like it passed — when the base is not a commit
the checkout can see, when the base is not an ancestor of HEAD, when the
base..HEAD range names no file at all, or when the record-set rule selects
nothing on the tree. After those validations, a range that genuinely changes
no tracked record is a computed result reported loudly; the whole-set
validity gate still covered parsing. CI supplies the base from the event
(`pull_request.base.sha`, then `push`'s `before`; `workflow_dispatch` diffs
the last commit) and checks out with `fetch-depth: 0` so the base is
fetchable on both triggers the job runs under.

## Consequences

- A record that arrives with a new absolute path fails the `signoff` job with
  the finding named, on both triggers. The seven historical `/home/ubuntu`
  paths stay in the public history; a history rewrite would actually un-leak
  them and is explicitly **not** taken — it is a larger operator call than
  #136's.
- Fresh DRC envelopes stay committable while #5709 is open: only their
  top-level `deck` field is admitted, and any second leak in the same
  envelope still fails.
- The exception and the prefix set live in the single copy of the gate,
  `verification/check-records-json.sh`; the attested `records-json-valid`
  check runs the same script in its unchanged default mode, and `check.sh`
  keeps consuming `--list`, which is unchanged.
- This record settles how one class of evidence is gated; it does not edit any
  committed evidence record, and it does not resolve #136, #191 or #20.
