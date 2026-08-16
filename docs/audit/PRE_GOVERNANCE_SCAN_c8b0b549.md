# Pre-Governance Boundary Scan

**Scan base:** `origin/main` @ `c8b0b549` · **Posture:** READ-ONLY (classifies, fixes nothing) ·
**Method:** boundary read from git log (not assumed); candidates separated by reachability on `main`
(merged = reconciled) then classified by namespace/authority relevance.

---

## 1. The witnessed boundary (established from the log, not from memory)

The governance sprint's constitutional boundary is a fact in the history. Three boundaries, each with its SHA:

| Boundary | Date | SHA(s) | What it is |
|---|---|---|---|
| **Soft start** | 2026-05-11 | `64ad3a57` (MRP-1A enforcement infra), `c9da01bd` (MRP governance framework) | Sprint underway — governance infrastructure begins landing |
| *(ramp milestone)* | 2026-05-12 | `7a57555b` (GOV-2 topology + authority hierarchy), `825d2af2` (GOV-3 → CLAUDE.md authority section) | Authority hierarchy **documented** — but not yet the constitutional baseline |
| **Baseline landed** | **2026-05-18** | **`c597c8a7`** (C0 C1 constitutional foundation baseline), **`c12a9485`** (C2 constitutional arbitration framework A–E) | Constitutional rules **in force** |
| **Merged to main** | 2026-05-18 | `e9644dc6` (Merge PR #16, `fix/wood-shrinkage-data-integrity`) | Baseline became `main` |

All five SHAs verified reachable on `origin/main`.

### ⚠️ Correction — "remembered May 12" is NOT the baseline
A remembered "May 12" boundary maps to **GOV-2 / GOV-3** (`7a57555b` / `825d2af2`, 2026-05-12) — the
governance **topology + authority-hierarchy documents**. Those are a soft-start *ramp* milestone, not the
constitutional baseline. **The baseline is 2026-05-18 (`c597c8a7` + `c12a9485`), six days later.** Trust the
log: rules were not "in force" until the C0/C1/C2 commits landed via PR #16 on May 18.

> Note on the broader governance arc: governance *docs* began much earlier (canonical contracts from
> 2025-12-16; CBSP21 protocol/enforcement from 2026-01-01→01-03). Those belong to an earlier era. The
> **constitutional (C0–C2) sprint** — the one carrying namespace-authority rules and the CONV-002 failure
> mode — is the May-2026 arc bounded above.

---

## 2. Transition zone — the high-risk set (2026-05-11 → 2026-05-18)

Governance partial, constitutional rules not yet final. This window is **dense** — ~60 commits on `main`,
all authored *before* the baseline was in force:

| Workstream | Representative commits | Count (approx) |
|---|---|---|
| CAM governed export lifecycle | `eb8b28aa` 6A → `bf3764e4` 6I | ~9 |
| CAM translator boundary/registry | `ac83025c` 7B → `46dc43ba` 7M | ~13 |
| MRP (morphology/acoustic/CAD) | `c9da01bd`, `c971d7a4` (spine 2C/2D), `56ac95e4` (5G) | ~10 |
| IBG (BOE + morphology harvest + Body Grid) | `956533c6` (2A BOE), `70a0d3ee` (2B), `de98455d`/`e0cbb747` (harvest 1A/1B), `099397fe` (Body Grid 1A) | ~6 |
| Governance enforcement | `3beda14f` GOV-1, `7a57555b` GOV-2, `825d2af2` GOV-3, `7a220441` tier system | ~5 |
| Vectorizer / DXF | `778394c7` (V2_RAW recovery), `9b7630b9` (dxf_compat enforce) | ~4 |

**Classification of the zone as a whole:** these are **reconciled-by-merge but governance-partial-at-authorship**.
They are on `main`, so they are not *unreconciled* — but they were written before the C0–C2 rules existed, so
they are the highest-yield set for a *retroactive* namespace/authority spot-check. None is an open defect on
its face; each is a lead.

---

## 3. Dormant branches (last activity before the 2026-05-18 baseline)

17 remote refs predate the baseline. **The decisive discriminator is commits-ahead-of-main:** a branch that
is 0-ahead is fully merged — a stale *pointer*, not unreconciled work.

| Last activity | Ahead of main | Branch | Class |
|---|--:|---|---|
| 2025-10-31 | **5** | `copilot/bridge-luthiery-digital-fabrication` | **STALE (dead orphan origin)** |
| 2025-11-06 | 1 | `gh-pages` | SAFE (pages artifact, not code) |
| 2025-11-06 | 0 | `…/public_badges` | SAFE (pages) |
| 2025-11-09 | 0 | `feature/blueprint-lab-ui` | SAFE (merged / stale pointer) |
| 2025-12-07 | 0 | `feature/rmos-2-0-skeleton` | SAFE (0-ahead — RMOS work fully on main) |
| 2025-12-15 | 0 | `feature/client-migration` | SAFE (stale pointer) |
| 2025-12-27 | 0 | `backup-sdk-h8-2-1` | SAFE (backup ref) |
| 2026-01-02 | 0 | `feature/cnc-saw-labs` | SAFE (0-ahead — saw_lab work fully on main) |
| 2026-01-14 | 0 | `feat/ai-context-adapter` | SAFE (stale pointer) |
| 2026-01-14 | 0 | `feat/design-first-workflow` | SAFE (stale pointer) |
| 2026-01-16 | 0 | `feat/wave-6a-6b1-linked-cursor-wsi` | SAFE (stale pointer) |
| 2026-01-21 | 0 | `feature/ingest-audit-log` | SAFE (merged PR #12) |
| 2026-01-21 | **1** | `feature/adapter-guide` | **NEEDS RECONCILIATION** |
| 2026-01-21 | **1** | `feature/mesh-pipeline-scaffold` | **CONV-002 / TIER-D CANDIDATE** |
| 2026-04-29 | 0 | `feat/dxf-r2000-paid-tier-resolution` | SAFE (R2000 policy on main) |
| 2026-04-30 | 0 | `feat/grbl-spindle-emission-sprint-a` | SAFE (merged PR #11) |
| 2026-04-30 | 0 | `sprint/fret-ecosphere-a` | SAFE (0-ahead — fret ecosphere on main) |

**13 of 17 are 0-ahead** (fully reconciled; the branch refs are just uncleaned pointers). The 3 I initially
suspected as namespace risks — `rmos-2-0-skeleton`, `cnc-saw-labs`, `fret-ecosphere-a` — are **0-ahead: their
work is already on `main` and reconciled.** Only 4 refs carry unmerged commits; only 3 are code.

---

## 4. Per-candidate classification (the unreconciled set)

### `feature/mesh-pipeline-scaffold` — **CONV-002 / TIER-D CANDIDATE** (strongest lead)
- 1 unmerged commit `f6cf2911` (2026-01-21) "scaffold v0.1.0 — retopo adapters, fields integration, CAM policy export".
- Touches **`services/api/app/retopo/`** (new namespace, `__init__.py` + adapters) **and `contracts/schema_registry.json`** — a schema/authority artifact.
- **CONV-002 test result:** `services/api/app/retopo/` is **ABSENT from `main`** — the namespace was scaffolded pre-governance and never landed. It touches the governed `contracts/schema_registry.json`. This is exactly the shape CONV-002 names: a pre-governance namespace + authority-artifact edit that never met the constitutional rules. **Lead — confirm with the retopo/schema-registry sanity check before acting.**

### `feature/adapter-guide` — **NEEDS PROMOTION / RECONCILIATION**
- 1 unmerged commit `b05281d0` (2026-01-21) "adapter guide + hardened shims for QRM/MIQ".
- Touches the same **`app/retopo/`** namespace (subset of mesh-pipeline-scaffold — the retopo adapters without the schema_registry/CAM-policy layer).
- Real work in a namespace absent from `main`. Either superseded by `mesh-pipeline-scaffold` or an independent retopo effort. **Reconcile the two retopo branches against each other and against current governance before any promotion.**

### `copilot/bridge-luthiery-digital-fabrication` — **STALE (dead orphan origin)**
- 5 unmerged commits (2025-10-31): "Initial commit / Initial plan / Implement complete Luthier's Toolbox".
- Layout is a **completely different project** (`src/`, `pyproject.toml`, `examples/` — not `services/api/app/`). Shares **no namespace** with the current codebase; it's a from-scratch parallel origin that never merged.
- **Not a CONV-002 conflict** (no shared namespace to collide). Archival/deletion candidate — flag for branch hygiene, not governance reconciliation.

### `gh-pages` / `…/public_badges` — **SAFE**
- Pages/badge artifacts, no application namespace or authority surface.

---

## 5. The BOE row (called out specifically)

| Field | Value |
|---|---|
| Last pre-baseline BOE commit | **`956533c6` (2026-05-12)** "docs(ibg): IBG-2A BOE integration boundary audit" (+ `70a0d3ee` IBG-2B production infra enablement, same day) |
| Position vs baseline | **6 days before** the 2026-05-18 constitutional baseline — squarely in the transition zone |
| Reachable on `main`? | **Yes** — BOE/IBG work is merged; `body_outline` namespace is present and actively used on `main` |
| Unmerged BOE branch? | **None** — no dormant branch carries unreconciled BOE work (all BOE/IBG commits are on `main`) |
| **CONV-002 status** | **RECONCILED-BY-MERGE (governance-partial-at-authorship).** BOE landed under partial governance (authority hierarchy documented 05-12, but C0–C2 not in force until 05-18). It is not unreconciled work, but it is a **retroactive spot-check candidate**: the IBG provenance posture is intentionally `BLOCKED_PROVENANCE` (governance prep before implementation), so the BOE↔IBG authority boundary authored on 05-12 should be re-witnessed against the C0–C2 rules that landed 05-18. Lead, not defect. |

---

## 6. Summary & method notes

- **Boundary is witnessed, not remembered:** baseline = `c597c8a7` + `c12a9485` (2026-05-18), merged `e9644dc6` (PR #16). The "May 12" figure is GOV-2/3 authority docs — a ramp milestone, corrected here.
- **The transition zone (05-11→05-18) is the high-risk set** — ~60 governance-partial commits, all on `main` (reconciled-by-merge). Highest yield for a retroactive authority spot-check.
- **Dormant-branch risk is far smaller than the count suggests:** 13/17 refs are 0-ahead (stale pointers, SAFE). The genuinely unreconciled pre-governance work is **2 retopo branches** (`mesh-pipeline-scaffold`, `adapter-guide`) scaffolding a namespace (`app/retopo/`) that never landed, plus **1 dead orphan origin** (`copilot/bridge-…`).
- **The single strongest CONV-002/TIER-D lead** is `feature/mesh-pipeline-scaffold` — a pre-governance `app/retopo/` namespace + an edit to the governed `contracts/schema_registry.json`.

**Guardrail compliance:** read-only. Nothing was modified. Every classification above is a *lead*; the CONV-002
candidates in §4 require running the actual namespace/authority sanity check to confirm before treating any as a
defect. Branch-hygiene candidates (stale 0-ahead pointers, the dead orphan origin) are observations, not actions.

---

## 7. Amendment (recovery-archaeology pass) — see companion

The asset-recovery pass ([`PRE_GOVERNANCE_ASSET_RECOVERY_c8b0b549.md`](PRE_GOVERNANCE_ASSET_RECOVERY_c8b0b549.md))
witnessed the retopo specimen more deeply and amends this record:

- **§4/§6 correction — retopo is not a schema-registry authority conflict.** The deeper dig found
  `feature/mesh-pipeline-scaffold`'s `contracts/schema_registry.json` is **byte-identical to `main`'s**, and the
  retopo `presets/`/`examples/` **already landed on `main`** (via `f288065b`). The stranded remainder is the
  **`app/retopo/` code namespace only** — a *partial landing*, not a competing authority artifact. `ADR-002`
  (**Accepted**, 2025-12-28) already blesses the coupling layer, so the leading verdict is
  DECLARED_EXTENSION/NOVEL_VALID, **provisional** pending the authority check.
- **CONV-002 provenance pinned.** CONV-002's Dev Order is **Lab-side**; only its TD-1 is a production defect (BR-042).
  New specimens here are TIER-D-*shaped*, **not** members of CONV-002's TD set.
- **Provisional-status upgrade (formal amendment):** *The inability to deliberately rerun the namespace/authority
  sanity check is promoted from a scan caveat to an independent tooling deficiency. CONV-002 branch findings remain
  provisional until that deficiency is corrected or an equivalent deterministic authority check is identified.* The
  detector requirement is technically actionable (`authority_chain_registry.json`, `governance_manifest.json` exist);
  its implementation and ownership remain outside this audit.
