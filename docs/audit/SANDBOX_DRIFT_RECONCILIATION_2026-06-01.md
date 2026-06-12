# Sandbox Drift — Three-Audit Reconciliation & Index

**Created:** 2026-06-01 · **By:** forensic reconciliation pass (read-only; not committed)
**Purpose:** Single reference tying together the three audits run this session, so a fourth audit
can cross-reference durable anchors (SHAs / branches / tags / paths) instead of re-deriving them.
This doc is itself untracked-by-design.

---

## 0. Common anchor (shared by all three audits)

| | |
|---|---|
| **Governance sprint** | GOV-CONVERGE ("May 2026 governance sprint tail") |
| **Anchor commit** | `464920f1` — *"docs: add GOV-CONVERGE parking lot to SPRINTS"* |
| **Anchor date** | **2026-05-28 15:30 -0500** |
| **Window** | **[2026-05-14 → 2026-05-28]** |
| **Repo** | `C:\Users\thepr\Downloads\luthiers-toolbox` (siblings: `CNC-Production-Shop`, `ltb-woodworking-studio`; sandboxes via junctions: `vectorizer-sandbox`, `tap_tone_pi`, `CAM-Assist-Blueprint`) |

## 0.1 The common mechanism (the through-line)

The governance sprint — plus a parallel reconstruction/replay expansion — **displaced original-mission
work across three lanes.** The displacement took different shapes, producing two opposite narrative errors:

- **Narrative says DONE, git says STRANDED** → CAM-intent lane (audit 2).
- **Narrative says UNDONE, git says SHIPPED** → Measurement-Lab lane (audit 3).
- **Unsourced "approved" provenance accreted in instructions** → vectorizer three-loop/AGE (audit 1).

In every lane the *canonical spine landed on `main`*; what stranded or got misreported were the *limbs*
(operation lanes, side-edits) and the *provenance* (what was actually approved / actually built).

---

## 1. Audit 1 — Pre-Governance Forensic (durable: full doc on disk)

**Full doc:** `docs/audit/PRE_GOVERNANCE_FORENSIC_2026-06-01.md` (+ appended Cross-Verification Addendum).

Key durable findings:
- **Dangling census:** **42 dangling commits total; 32 in-window; ~23 truly ORPHANED** (not on any branch,
  not in current stash reflog) — gc-eligible. (An early single pass saw only 6 due to a `head -40`
  truncation; the addendum is authoritative.)
- **Three in-window sprint lines, by build discipline:** CI-RED (`CI-RED-001…016`, tightest, ~highest
  landing rate) → DXF-lifecycle/IBG (`DO_75…80`, high documented rigor, leaky "wip-unrelated" edges) →
  Governance-inventory (lowest — real work, no durable dev-order doc, mostly un-landed; re-booted as
  GOV-CONVERGE at the anchor).
- **NOT FOUND (git-unrecoverable):** `PR77_RECOVERY.md`, `create_boe_pr.ps1`,
  `docs/handoffs/CI_RED_015D_COMMIT_HANDOFF.md`, `docs/handoffs/DEV_HANDOFF_2026-05-30_CI_REMEDIATION.md`
  — untracked at session start, now absent from disk, never git-tracked.
- **Off-state break:** three-loop/AGE "APPROVED DESIGN" conflation (corrected PR #77/#78/#80); stream
  conflation sank **PR #79** (no merge commit exists). Disentangled into PRs #81–#85 on 05-31.
- **Open action:** additively tag the ~23 orphaned commits before any `git gc`.

---

## 2. Audit 2 — CAM-Intent Convergence DNA (durable: this doc only)

**Mission:** Design → `CamIntentV1` → operation engine → toolpath → machine.

**Canonical spine — ON `main` (durable):**
- `services/api/app/rmos/cam/schemas_intent.py` → `class CamIntentV1`
- `services/api/app/rmos/cam/normalize_intent.py` → `normalize_cam_intent_v1()`
- `services/api/app/routers/rmos_cam_intent_router.py`

**Origin DNA:** H-namespace (`H7`/`H7.2`/`H8.3`) — `d235453e` (CAM intent schema), `2186a412`
(`normalize_cam_intent_v1` type coercion). Prior silent-deletion event: `545fccad` deleted 25 routers;
restored by `cb3b94b1` / PR #46.

**Stranded operation lanes (NOT on `main`):**
- `b0f88a73` — **8G V-Carve** intent migration (+1208 lines: router/adapter/schema/tests)
- `a9634ab1` — **8H Profile** intent migration (+1604 lines)
- Both live **only on branch `feat/confidence-envelope-interoperability`** (104 ahead / 6 behind `main`,
  **unmerged**). Working tree shows only orphaned `.pyc` for `cam/routers/{vcarve,profiling,drilling,pocketing}/intent_router`.

**Never existed (claim refuted):** **8I drilling** and **8J pocket** intent routers — no commit on any
branch. Drilling has only legacy routers; `pocketing/` has no source.

**Verdict:** Contract 100% landed; lane migration **0% on `main`** (2 lanes built-but-stranded, 2 unbuilt).
True completion ≈ **30–40%**, *not* the claimed "95%". Biggest risk = loss of already-built 8G/8H.

**Recovery target (not yet done):** cherry-pick 8G/8H intent files from
`feat/confidence-envelope-interoperability` onto a clean branch off `main` (without dragging the 104
governance commits); then build 8I/8J; verify all lanes route through `normalize_cam_intent_v1()`.

---

## 3. Audit 3 — Measurement-Lab / Experimental Session DNA (durable: this doc + git tags)

**Mission:** Measurement Lab experiment continuity (session identity, chronology, archive/variant grouping).

**Continuity object — SHIPPED, ON `main` (refutes "never completed"):**
- `packages/client/src/types/acoustics/experimentalSession.ts` → `ExperimentalSessionRecord` (schema
  `experimental-session.v1`; fields: sessionId, title, objective?, archiveIds, variantIds, startedAt)
- `packages/client/src/utils/acoustics/experimentalSession.ts` → `createExperimentalSession`,
  `appendArchiveToSession`, `sortSessionArchives`, `buildSessionSummary`, `linkVariantToSession`
- `packages/client/src/utils/acoustics/__tests__/experimentalSession.test.ts` → **23 tests**
- `packages/client/src/components/acoustics/ExperimentalSessionPanel.vue` → **wired into**
  `views/art-studio/ApertureWorkspace.vue` (re-export `components/shared/acoustics/index.ts:73`)
- **Commits:** `c672f9f4` (add **DO85** types/utils/panel) + `88e7a42b` (wire into Measurement Lab) — PR #49/#50.

**Timeline vs governance:** last landed acoustics commit `88e7a42b` = **2026-05-26**, i.e. **2 days
before** the anchor, at a *completed* milestone. Acoustics DO track (its own sequence):
**1–9 → 16–45 → 48–52 → correlation(`50ff5463`) → 70/71/72 → 85.** Numeric DO namespace is **shared**
with DXF (75) and IBG (78–80) — "Mixed".

**Claim refuted:** proposed **"DO 83 — build ExperimentalSession"** would re-create shipped DO85 code.
Feared drift framework (`ReconstructionSessionRecord`, `ReplayLineageGraph`, `replayBundle`) **does not
exist in this repo**; the session object is clean of replay/lineage. Continuity mission ≈ **100%**, not 10%.

**Genuinely stranded acoustics work — NOW TAGGED (gc-safe):**
| Tag (local) | Commit | Unique-vs-`main` content |
|---|---|---|
| `salvage/topology-1790f6bb` | `1790f6bb` (05-21, research/wave-1c) | `topologyVariant.ts` +138 util, `topologyVariant.test.ts` +377 test |
| `salvage/aperture-c817e9cb` | `c817e9cb` (05-20, governance-execution-alignment) | `ApertureComparisonPanel.vue` +141, `ApertureWorkspace.vue` +89, status doc +289 |

**Stale signpost:** `docs/architecture/APERTURE_WORKSPACE_REFACTOR_STATUS.md` "Next Dev Order" still reads
**"Dev Order 5 — ApertureWorkspace Frontend Shell"** (frozen at 05-06; never updated through DO70/72/85).
No accurate next-step pointer exists → real continuation = define DO 86+ from DO85-complete state.

---

## 4. Quick reference — durable anchors by lane

| Lane | Spine (on main) | Stranded | Never-built / refuted | Tag/Doc |
|---|---|---|---|---|
| **Governance-inventory** (A1) | GOV-CONVERGE parking lot | ~23 orphaned commits (43b07017, d1677e98, …) | three-loop/AGE "approved" | `PRE_GOVERNANCE_FORENSIC_2026-06-01.md` |
| **CAM-intent** (A2) | `rmos/cam/normalize_intent.py`, `schemas_intent.py` | 8G `b0f88a73`, 8H `a9634ab1` (on `feat/confidence-envelope-interoperability`) | 8I drilling, 8J pocket | (this doc) |
| **Measurement-Lab** (A3) | DO85 `experimentalSession.*`, panel | `1790f6bb`, `c817e9cb` | proposed "DO 83" (redundant) | `salvage/topology-1790f6bb`, `salvage/aperture-c817e9cb` |

## 5. Discipline note

All three audits were read-only except: (a) audit 1's forensic doc (created, not committed), (b) this
reconciliation doc (created, not committed), (c) two additive `salvage/*` git tags (non-destructive).
No commits, stash pops/drops, branch deletions, `gc`, or `prune` were performed. The fourth audit should
treat sections 1–3 as the established ground truth for those lanes and verify any new claims against the
repo, not against narrative.

---

## 6. Audit 4 — "Acoustic Native Re-Entry" DNA chain (durable: this doc)

**Claim under audit:** native acoustic/plate work is *displaced, unstarted, ~30–40%*; the smallest native
step is to "add one plate-design smoke test to prove native work resumed"; DNA chain =
DO70→71→72 → MRP-5E→5F→5G→5H→**5I→5J→5K** → Runtime Spine → CAM-8G→8J → Acoustic Native Re-Entry.

**Verdict: best-aimed of the four proposals (it targets real code) but premise is false three ways.**

- **Target EXISTS (good):** `services/api/app/calculators/plate_design/` is real and substantial —
  `rayleigh_ritz.py` (`solve_rayleigh_ritz`, `OrthotropicPlate`, stiffness/mass matrices),
  `brace_prescription.py`, `coupled_2osc.py`, `inverse_solver.py`, `archtop_graduation.py`,
  `calibration.py`, `gamma_calibration.py`, `alpha_beta.py`. Plus `acoustic_body_volume.py`,
  `acoustic_bridge_calc.py`, `soundhole_*` family.
- **FALSE — "native work unstarted / first test not yet started":** ~20+ acoustic tests already exist,
  including ones that ARE the proposed smoke test: `test_archtop_graduation.py` (imports
  `plate_design.archtop_graduation`, tests real freqs/boundaries/raises/`to_dict`),
  `test_inverse_brace_sizing.py`, `test_acoustic_body_generator_smoke.py`,
  `test_build_sequence_acoustic_chain.py`, 10× `test_soundhole_*`. The proposed acceptance criteria are
  **already satisfied**.
- **FALSE — "displaced by CAM/governance":** plate_design was built **2026-03-18** (`3855579c`
  *port plate design math from tap-tone-pi, PORT-001*; ARCH-003) — **~2 months BEFORE** the governance
  anchor (05-28). It predates the sweep; it was never in contention with it.
- **MISDRAWN DNA chain:** `plate_design/*.py` imports **nothing** from `rmos`/runtime-spine/`cam`/
  governance (verified clean). It is standalone math, NOT downstream of MRP-5x or CAM. The chain's
  "→ Runtime Spine → CAM → Acoustic Re-Entry" wiring is architecturally wrong. Real acoustic DNA root =
  PORT-001 (`3855579c`) + the acoustics UI chain (DO70/72/85), independent of the runtime spine.
- **Fabricated/mislabeled chain links:** **MRP-5I / 5J / 5K do not exist** as numbered orders (real:
  5A,5B,5E,5F,5G,5H,5M–5Y; "kernel adapter" exists only as `cam/topology_builder/kernel_adapters/`
  code, not an order). **CAM-8I/8J never existed** (re-asserting audit-2 §2). **DO 83 is not
  "Governance Convergence"** (audit-3: DO83 unused; governance = GOV-CONVERGE `464920f1`; DO85 = acoustics).

**Non-redundant residue (if a fresh native test is still wanted):** target a plate_design module that has
**no** dedicated test — `rayleigh_ritz.py` (`solve_rayleigh_ritz`), `coupled_2osc.py`, `inverse_solver.py`,
`calibration.py`/`gamma_calibration.py`, `alpha_beta.py` — not `archtop_graduation`/`brace`/`inverse-brace`
(already covered). That would be genuinely additive; a generic "plate design smoke test" would duplicate
`test_archtop_graduation.py`.

**Pattern confirmed across all 4 audits:** every narrative overstates displacement and misattributes
lineage; the spines landed, and the "missing native work" is largely already present and tested. Audit 4
is the audit-3 shape — *narrative says UNDONE/displaced, git says SHIPPED-and-TESTED (since March)*.
