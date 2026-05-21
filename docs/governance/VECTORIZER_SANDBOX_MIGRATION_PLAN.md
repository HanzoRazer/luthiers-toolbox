# Vectorizer Semantic Incubation — Migration Plan

**Date:** 2026-05-20 (revised)  
**Status:** PROPOSED — requires explicit approval before execution  
**Authority:** `SEMANTIC_INCUBATION_ARCHITECTURE.md`, `VECTORIZER_COMPONENT_LIFECYCLE.md`  
**Prerequisite:** Remediation sprint PR-2 → PR-1 → PR-3 complete; no production behavior change until Phase 4 gates pass

**Target cognition repo (existing):** https://github.com/HanzoRazer/vectorizer-sandbox  
**Local workspace clone:** sibling `../vectorizer-sandbox/` (`local/README.md`, `local/clone-vectorizer-sandbox.ps1`)

---

## 1. Purpose — controlled semantic incubation

Separate **semantic cognition research** from the **governed operational spine** without losing lineage or blocking R&D velocity.

```text
ORPHANED  ≠  delete
ORPHANED  =  re-home to semantic cognition layer + document + grep-gate re-import

sandbox discovers  →  production ratifies
```

**This plan is NOT:**

- Merging unstable sandbox snapshots into `luthiers-toolbox` production
- Creating a second “archaeology graveyard” repo (`vectorizer-archaeology` **cancelled**)
- Promoting `agentic_supervisor` or sandbox `vectorizer_phase3` to ACTIVE by copy-paste

**This plan IS:**

- Expanding **`vectorizer-sandbox`** into the semantic cognition ecosystem
- Moving Tier A cognitive/grid lineage from main → sandbox
- Preserving Wave 1–2 sandbox work (calibration, multi-agent supervision) in place
- Enforcing the [constitutional graduation bridge](SEMANTIC_INCUBATION_ARCHITECTURE.md#4-constitutional-graduation-bridge) for any future production adoption

---

## 2. Repository roles

| Repository | Layer | Responsibility |
|------------|-------|----------------|
| **`luthiers-toolbox`** | Semantic runtime spine + constitutional runtime | Governed intake, provenance, deterministic topology handling, `refined` / `edge_to_dxf`, IBG gates, trusted execution |
| **`vectorizer-sandbox`** | Semantic cognition layer | Topology cognition, contour intelligence, occupancy semantics, multi-agent extraction, primitive experimentation, archaeological lineage |

### What already lives in `vectorizer-sandbox` (2026-04 audit)

| Asset | Role in cognition layer |
|-------|-------------------------|
| `agentic_supervisor.py` | Multi-pass supervision prototype (Loop 1 analogue) |
| `vectorizer_enhancements.py` | Wave 1 feature-first calibration (ahead of main on LOC) |
| `vectorizer_phase3.py` | Extraction experiments (**behind main** on scale validation — do not back-merge) |
| `phase4/` | Dimension linking R&D (standalone) |
| `DEVELOPER_HANDOFF.md` | Wave 3 multi-view / layered DXF scope |
| Explorer golden fixtures | Evidence replay for cognition experiments |

### What moves from `luthiers-toolbox` → sandbox

Tier A archaeological semantic lineage (see §3.1) into `src/archaeology/` and `src/semantic/`.

### What stays in `luthiers-toolbox`

Tier C production extraction runtime (see §3.3). No change to Blueprint Reader default (`CleanupMode.REFINED`).

### Optional later: `ibg-research-sandbox`

Lane 4 morphology interpretation — separate charter; may share org with `vectorizer-sandbox` but not merged into one undifferentiated bucket.

---

## 3. Migration inventory

### 3.1 Tier A — Re-home to sandbox (zero production imports)

| Path (main repo) | LOC (approx) | Sandbox destination |
|------------------|--------------|---------------------|
| `services/photo-vectorizer/cognitive_extractor.py` | ~1470 | `src/semantic/cognitive_extractor.py` |
| `services/photo-vectorizer/cognitive_extraction_engine.py` | ~1503 | `src/semantic/cognitive_extraction_engine.py` |
| `services/photo-vectorizer/extract_body_grid.py` | ~349 | `src/archaeology/extract_body_grid.py` |
| `services/photo-vectorizer/extract_body_grid_v2.py` – `v5.py` | ~1290 | `src/archaeology/` |
| `services/blueprint-import/vectorizer_phase2.py` | ~1684 | `src/archaeology/vectorizer_phase2.py` |

**Supporting docs (mirror or excerpt):**

- `docs/governance/VECTORIZER_ARCHAEOLOGY_HARVEST.md` → sandbox `docs/harvest/`
- Adapted `verify_vectorizer_audit.ps1` → sandbox `scripts/`

### 3.2 Tier B — Coupled: decouple before move

| Path | Coupling | Resolution |
|------|----------|------------|
| `march_pipeline_restore.py` | Imported by `photo_vectorizer_v2.py` | Extract production subset → main; move research CLI to sandbox |
| `light_line_body_extractor.py` | Imported by `photo_vectorizer_v2.py` | Same split pattern |
| `vectorizer_phase2.py` | `blueprint/constants.py` reference | Stub dev route → sandbox docs before Tier A phase2 move |

Reclassify `march_pipeline_restore` → **PARTIAL** until Tier B resolved.

### 3.3 Tier C — Stay in runtime spine (do not migrate)

| Path | Reason |
|------|--------|
| `edge_to_dxf.py` | Canonical `refined` path |
| `photo_vectorizer_v2.py` | CANONICAL_PRODUCTION photo pipeline |
| `vectorizer_phase3.py` (main) | Production Phase 3 + `validate_scale_before_export` |
| `blueprint_orchestrator.py` | MVP orchestrator |
| `body_isolation_stage.py`, `geometry_coach_v2.py` | Active photo pipeline |
| `services/api/app/instrument_geometry/**` | Constitutional IBG |

### 3.4 Sandbox-native (already external — do not pull into main without graduation)

| Path | Notes |
|------|-------|
| `agentic_supervisor.py` | Incubation only until graduation bridge |
| Sandbox `vectorizer_enhancements.py` | Diff-and-port selective ideas via ADR |
| `phase4/` in sandbox | Keep in sandbox; wire to main only after intake gate |

---

## 4. Phased execution

### Phase 0 — Preconditions (main repo, no migration)

| # | Task | Done when |
|---|------|-----------|
| 0.1 | PR-2 grouping telemetry on `refined` | `debug.grouping_fallback_*` live |
| 0.2 | PR-1 SIMPLE → EXPORT_SAFE | Unit test green |
| 0.3 | PR-3 lifecycle + 501 gates | Registry current |
| 0.4 | `VECTORIZER_ARCHAEOLOGY_HARVEST.md` draft | ≥5 concept entries |
| 0.5 | `check_semantic_sandbox_imports.py` | Precommit gate; fails on `cognitive_extract*`, `extract_body_grid*` in `services/` |
| 0.6 | Ross approval | §10 sign-off |

**Gate:** Phase 1 does not start until 0.5 passes.

---

### Phase 1 — Expand `vectorizer-sandbox` (not a new repo)

| # | Task |
|---|------|
| 1.1 | Add `GOVERNANCE.md` — semantic cognition rules; no implied ACTIVE / commercial status |
| 1.2 | Add `SEMANTIC_INCUBATION.md` (copy or link to main `SEMANTIC_INCUBATION_ARCHITECTURE.md`) |
| 1.3 | Scaffold `src/semantic/`, `src/archaeology/`, `docs/harvest/`, `fixtures/` |
| 1.4 | Move committed `__pycache__` out of git; add `.gitignore` |
| 1.5 | Relocate root PDFs/PNGs into `fixtures/reference_blueprints/` |
| 1.6 | CI: `pytest test_calibration_sources.py` + import smoke for Tier A after Phase 2 |
| 1.7 | README: two-layer purpose (cognition vs runtime spine link) |

---

### Phase 2 — Tier A re-home (main → sandbox)

| # | Task |
|---|------|
| 2.1 | Copy Tier A with `MIGRATION_MANIFEST.json` (source SHAs from `luthiers-toolbox`) |
| 2.2 | Tag sandbox `v0.2.0-semantic-lineage-import` |
| 2.3 | Main repo PR: remove Tier A files; add stub pointers → `vectorizer-sandbox` |
| 2.4 | Lifecycle: **RELOCATED_EXTERNAL** → `github.com/HanzoRazer/vectorizer-sandbox` |
| 2.5 | `check_semantic_sandbox_imports.py` green on main |

**Rollback:** Revert main PR; sandbox tag preserved.

---

### Phase 3 — Tier B decoupling

Same as prior plan §3.2 — extract production minimal modules before moving research bodies to sandbox `src/archaeology/`.

**Gate:** Cuatro golden + Blueprint Reader smoke unchanged on main.

---

### Phase 4 — Runtime spine hardening (main)

| # | Task |
|---|------|
| 4.1 | Pre-commit / CI: semantic import grep |
| 4.2 | Update `MANIFEST_INDEX.md`, duplication matrix, `CLAUDE.md` agent rule |
| 4.3 | **No git submodule** from main → sandbox |
| 4.4 | Document graduation template in `docs/adr/ADR-template-semantic-promotion.md` (optional) |

---

### Phase 5 — Harvest & graduation proposals (ongoing)

| # | Task |
|---|------|
| 5.1 | Per grid/cognitive file: hypothesis, failure mode, harvestable idea |
| 5.2 | Promotion proposals → ADRs in **main** only |
| 5.3 | Lane 4 informed by harvest; not driven by bulk restore |

---

### Phase 6 — `ibg-research-sandbox` (deferred)

Separate charter after PR-2 telemetry + IBG intake documentation.

---

## 5. Target `vectorizer-sandbox` layout (after Phase 1–2)

```text
vectorizer-sandbox/
├── README.md
├── GOVERNANCE.md
├── SEMANTIC_INCUBATION.md
├── MIGRATION_MANIFEST.json
├── requirements.txt
├── docs/
│   ├── harvest/VECTORIZER_ARCHAEOLOGY_HARVEST.md
│   └── handoffs/DEVELOPER_HANDOFF.md
├── fixtures/
│   └── reference_blueprints/    # Explorer PDFs/PNGs (moved from root)
├── scripts/
│   └── verify_sandbox.py
├── src/
│   ├── incubation/              # Active R&D (Wave 1–3)
│   │   ├── agentic_supervisor.py
│   │   ├── vectorizer_phase3.py   # sandbox fork — not production canonical
│   │   ├── vectorizer_enhancements.py
│   │   └── phase4/
│   ├── semantic/                # Tier A cognition
│   │   ├── cognitive_extractor.py
│   │   └── cognitive_extraction_engine.py
│   └── archaeology/             # Tier A grid + phase2
│       ├── extract_body_grid.py … v5.py
│       └── vectorizer_phase2.py
├── experiments/                 # New work only; no direct main import
└── tests/
    ├── test_calibration_sources.py
    └── test_import_smoke.py
```

**Dependency policy:**

- Sandbox must **not** depend on `luthiers-toolbox` as installable package
- Main must **not** import from sandbox (grep CI)
- Shared utils: copy minimal or extract to published package later — not v1 scope

---

## 6. Graduation checklist (sandbox → runtime spine)

Use before any production PR sourced from sandbox:

| Step | Requirement |
|------|-------------|
| 1 | Evidence: golden/regression diff or structured failure taxonomy |
| 2 | Provenance: sandbox commit SHA + experiment notes in ADR |
| 3 | Determinism: bounded outputs, telemetry, fail-closed on fab-bound paths |
| 4 | Governance: lifecycle state change (e.g. SANDBOX → ACTIVE) + Ross sign-off where required |
| 5 | Implementation: **new** code in `services/` — not restore of relocated files |
| 6 | Intake: IBG / Blueprint Reader contract updated if semantics affect fabrication |

---

## 7. CI and governance

### Main (`luthiers-toolbox`)

| Check | Behavior |
|-------|----------|
| `check_semantic_sandbox_imports.py` | Fail if cognition/archaeology modules imported under `services/` |
| `verify_vectorizer_audit.ps1` | Tier A paths absent from main |
| Protected paths | Migration must not alter `blueprint_orchestrator` default extraction |

### Sandbox (`vectorizer-sandbox`)

| Check | Behavior |
|-------|----------|
| Calibration tests | `test_calibration_sources.py` |
| Import smoke | Tier A + incubation modules import without `services.api` |
| README lint | No “production” or “ACTIVE” claims without graduation note |

---

## 8. Risk register

| Risk | Mitigation |
|------|------------|
| Treating sandbox as production-adjacent | Graduation bridge + grep gate + no submodule |
| Back-merging stale sandbox `phase3` | Main is canonical for phase3; sandbox fork labeled in README |
| Loss of cognitive lineage | Tier A in `src/semantic/` + harvest doc |
| `march_pipeline_restore` break | Tier B extract-before-move |
| Confusion: incubation vs runtime | `SEMANTIC_INCUBATION_ARCHITECTURE.md` |

---

## 9. Success criteria

| Criterion | Measure |
|-----------|---------|
| Two-repo equilibrium documented | Architecture + migration plan approved |
| Tier A re-homed | Files in sandbox; pointers in main |
| Zero cognition imports in main `services/` | Grep CI green |
| `refined` stable | Cuatro golden unchanged post-migration |
| Sandbox self-contained | Tests + smoke pass |
| Graduation path defined | Checklist §6 referenced in lifecycle doc |

---

## 10. Approval sign-off

```text
Program: Semantic incubation — vectorizer-sandbox as cognition layer
Approved by: _______________________
Date: _____________________________
Expand existing vectorizer-sandbox (not new archaeology repo): [ ] APPROVED  [ ] DEFERRED
Tier A re-home from main: [ ] APPROVED  [ ] DEFERRED
Tier B decoupling: [ ] extract-first  [ ] defer march move
Graduation bridge mandatory for all promotions: [ ] ACKNOWLEDGED
```

---

## 11. Related documents

- `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`
- `docs/governance/VECTORIZER_COMPONENT_LIFECYCLE.md`
- `docs/governance/VECTORIZER_CANONICAL_PATHS.md`
- `docs/governance/BLUEPRINT_READER_PROTECTION_RULES.md`
- `Safe Remediation Lane.md`

---

*The operational repo matures into a stable semantic runtime spine; the sandbox evolves as an independent semantic cognition layer. Capabilities graduate only through provenance and intake — never by silent merge.*
