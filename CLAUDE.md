# asap7-ucie-phy — agent instructions

Open-source canary block: a UCIe-class die-to-die PHY at micro-bump pitch on
ASAP7, laid out and verified by AI agents. **Mixed-signal in layout** — a
synthesized lane datapath plus drawn TX/RX cells — so both flows apply.

- **ASAP7 is a predictive PDK. This block is layout, DRC and timing only,
  and it is never fabricated.** No silicon, no shuttle, no measurement. Never
  write anything that implies a tape-out, a measured result or a
  manufacturable part; every figure here is a tool result against a
  predictive model.
- **PDK and flows**: ASAP7 (predictive 7 nm FinFET; BSD-3-Clause, Arizona
  State University). Digital: cocotb + Icarus, Yosys, OpenROAD (STA against
  the ASAP7 libraries). Analog cells: netlists in `design/`; xschem + ngspice
  only if the BSIM-CMG models can be run in the open flow, which is an open
  question. Layout, DRC and LVS through klayout-tools (`klt`) in both cases.
- **ASAP7 bring-up comes first.** ASAP7 is not in the fleet's `open_pdks`
  store. If a sibling ASAP7 canary already has a pinned bring-up, adopt it
  and record the pin; otherwise do it here and record it. klt ships its own
  ASAP7 DRC deck, drawn at 1x; it does not support 4x-drawn layouts.
- **The bump interface is the point, and the risk.** The lane array's
  geometry is set by the micro-bump map, and klt's ASAP7 deck does not check
  the PAD layer today. Bump-pitch-matched placement, the lane-column seam and
  whatever ASAP7 does or does not define above M9 are where the tools are
  expected to be weakest. Expect friction there and file it.
- **Scope discipline.** No `consumes:` edge is declared. The clock source,
  the protocol layers above the PHY and the package are out of scope:
  specify the interface to each, including the clock quality this block
  assumes, and stop. If a sibling canary builds a sub-block you need, take
  it by a pinned reference (`REUSE.md` in `2AMLogic/2am`) rather than
  designing a second one.
- **UCIe-class, not UCIe.** Do not claim compliance or interoperability, do
  not use the consortium's marks, and do not reproduce specification text.
- **Friction protocol (the canary's job)**: every time klayout-tools is
  awkward, missing a capability, or wrong for what you need, file an issue at
  `2AMLogic/klayout-tools` describing the tool gap generically — that tracker
  is scoped to the tool, so keep design-specific detail out of it and describe
  the gap, not the design.
- **Verification is the product**: no claim without a testbench or a
  recorded tool run. Timing claims come from post-route STA at named library
  corners; recorded results are append-only evidence.
- Spec changes go through `spec/` with a decision record; agents do not relax
  the ratified spec to make results pass.
- **16 GT/s STA closure is the target.** 4 GT/s is the fallback and 32 GT/s
  a stretch. Do not let the stretch drive architecture before the target
  closes.

<!-- BEGIN LOOM ORCHESTRATION -->
This repository uses [Loom](https://github.com/rjwalters/loom) for AI-powered development orchestration — see the Loom repository for the full guide (roles, labels, worktrees, configuration). When installed, Loom also writes a locally-substituted copy of that guide to `.loom/CLAUDE.md`.

Work is coordinated through `loom:` labels on issues and pull requests, and the same roles run either under `loom-daemon` or by hand in an attended session — daemon mode is optional. Create the labels once with `.loom/scripts/sync-labels.sh` (an install ships `.github/labels.yml` but does not create the labels on the forge). A pull request ready for review carries `loom:review-requested`; Judge reviews it and applies `loom:pr` (approved) or `loom:changes-requested`; Doctor fixes a `loom:changes-requested` pull request and returns it to `loom:review-requested`. Only a `loom:pr` pull request gets merged, and always via this repo's merge script (`.loom/scripts/merge-pr.sh`) — never a raw forge merge command such as `gh pr merge`. Full state machine: `.loom/docs/label-state-machine.md`.
<!-- END LOOM ORCHESTRATION -->

<!-- BEGIN REPO-SKILLS -->
This repository has [Repo Skills](https://github.com/rjwalters/repo) v0.24.3 installed —
general repository hygiene and environment commands invoked as `/repo:<command>`. Run
`/repo:help` for the command list, or see `.claude/skills/repo/SKILL.md` for the full
guide. Hygiene commands apply safe, reversible fixes by default and report each
change; run with `--ask` to review first, and `--prune` to allow irreversible
removals. Managed by `install.sh` — edit outside the markers only.
<!-- END REPO-SKILLS -->
