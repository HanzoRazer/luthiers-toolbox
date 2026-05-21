# Vectorizer Component Lifecycle Registry

**Date:** 2026-05-20  
**Last updated:** 2026-05-20 (semantic incubation architecture; sandbox as cognition layer)  
**Status:** ACTIVE GOVERNANCE  
**Authority:** Single source of truth for vectorizer-adjacent component states and promotion rules.

---

## Governing protocols (read first)

| Protocol | Location | Use |
|----------|----------|-----|
| **Path classification** | `docs/governance/VECTORIZER_CANONICAL_PATHS.md` | CANONICAL_PRODUCTION vs RECOVERY vs ORPHAN vs ABANDONED |
| **Blueprint Reader freeze** | `docs/governance/BLUEPRINT_READER_PROTECTION_RULES.md` | LOCKED extraction on MVP; telemetry-only exempt |
| **Ground-truth verification** | `scripts/governance/verify_vectorizer_audit.ps1` → `verify_vectorizer_audit_results.txt` | Re-run after code or registry changes |
| **Debt severity** | `docs/governance/VECTORIZER_TECHNICAL_DEBT_INVENTORY.md` | CRITICAL/HIGH items; cross-ref lifecycle here |
| **Safe remediation sequence** | `Safe Remediation Lane.md` (repo root) | PR-2 live → PR-1 pre-promotion → PR-3 gates |

**Rule:** Any component **not** on a canonical production path (`hostinger/blueprint-reader.html` default or documented CANONICAL_PRODUCTION mode) must be listed in this registry. **`ACTIVE` (production) may not be assigned without the promotion rules below.**

**Distinction (critical):**

```text
ORPHANED / unwired     ≠  architecturally worthless
ORPHANED / unwired     =  not connected to current operational flow
```

Unwired cognitive/grid lineage may still encode topology, occupancy, or interpretation ideas the current pipeline never re-integrated. Treat per [ARCHAEOLOGICAL_RESEARCH](#archaeological_research-lineage) — do not conflate with **DEAD** intake paths or janitorial deletion.

---

## Three semantic generations (repo archaeology)

| Generation | Era | Characteristics | Operational role today |
|------------|-----|-----------------|------------------------|
| **Early cognitive / grid** | Pre-constitutional | Semantic occupancy, topology cognition, primitive heuristics | **ARCHAEOLOGICAL_RESEARCH** — not wired |
| **Mid vectorizer recovery** | 2026 recovery sprint | DXF recovery, contour chaining, `refined` / `edge_to_dxf`, Phase 3 raw | **ACTIVE** / **SANDBOX** recovery modes |
| **Constitutional runtime** | IBG + governance | Provenance, authority gating, deterministic intake, `ibg_intake_gate` | **ACTIVE** enforcement layer |

**Risk the audit surfaced:** the newer stack may be **operationally safer** while **semantically poorer** (e.g. `slab_body` collapse, primitive starvation, weak confidence on Les Paul). That is a **Lane 4 interpretation** problem, not proof that cognitive code should be re-wired into production without review.

**Engineering discipline split:**

```text
vector extraction   ≠   semantic interpretation
```

Production repo priority: constitutional stability, determinism, bounded authority. Semantic R&D belongs isolated — see [Future repository separation](#future-repository-separation-target).

---

## Lifecycle states (definitions)

| State | Meaning | May appear on Blueprint Reader default? | May auto-feed IBG fabrication? |
|-------|---------|------------------------------------------|--------------------------------|
| **ACTIVE** | Wired on canonical production path; defined contract; golden/regression obligations met | Yes (if listed as canonical mode) | Only if intake gate + recommendation allow |
| **PARTIAL** | Code exists; narrow or side-route use only | No (unless explicit `mode=` / flag) | Review-only unless provenance satisfied |
| **SANDBOX** | Callable for experiments; not commercially certified | No | No (human review / debug export only) |
| **EXPORT_SAFE** | Export landmine fixed (non-empty when contours exist; fail-closed for fab-bound) | No | No — not sufficient for commercial viability |
| **DISABLED** | Explicitly off in production (flag default false) | No | No |
| **DEAD** | No instantiation and no production API contract | No | No |
| **FUTURE** | Designed; not scheduled; not wired to orchestrator | No | No |
| **ORPHAN** | On disk; zero imports; no known research value documented | No | No |
| **ABANDONED** | Superseded by another implementation; safe to retire after parity check | No | No |
| **ARCHAEOLOGICAL_RESEARCH** | Unwired; potentially informative semantics/topology lineage; **not** production | No | No — harvest/review only |
| **RELOCATED_EXTERNAL** | Moved to `vectorizer-sandbox` (semantic cognition layer) per migration plan | No | No |
| **INCUBATING_EXTERNAL** | Active R&D in `vectorizer-sandbox`; not graduated to runtime spine | No | No |

### ARCHAEOLOGICAL_RESEARCH lineage

**Meaning:** Not operational, not canonical, not currently wired — but **potentially architecturally informative**. Unresolved semantic research artifacts, not “failed code” to delete casually.

| Allowed | Forbidden (without harvest + governance) |
|---------|------------------------------------------|
| Read, document, cite in handoffs | Wire into `BlueprintOrchestrator` default path |
| Extract concepts into specs / Lane 4+ design | Import from `services/` production routers |
| Freeze directory; add README pointer | Delete ~5.8k LOC “janitorial” PR |
| Copy to `vectorizer-sandbox` (`src/semantic/`, `src/archaeology/`) | Re-enable via implicit import in CI production path |
| Graduate via [constitutional bridge](SEMANTIC_INCUBATION_ARCHITECTURE.md#4-constitutional-graduation-bridge) only | Copy-paste sandbox snapshot into `services/` |
| Sandbox experiments **outside** operational repo | Treat as ACTIVE or EXPORT_SAFE |

**Janitorial policy (2026-05-20):** Do **not** delete cognitive/grid v1–v5 in the current remediation sprint. After PR-1–3: optional **relocate** or **mirror** to archaeology repo with grep gate preventing re-import — not bulk deletion.

### Strict rule: `ACTIVE` vs `EXPORT_SAFE`

- **PR-1** (SIMPLE export integrity) may move `ExtractionMode.SIMPLE` from **BROKEN** → **EXPORT_SAFE**. That is **not** promotion to **ACTIVE**.
- **`ACTIVE`** requires passing the [SIMPLE Commercial Readiness Gate](#simple-commercial-readiness-gate) (for SIMPLE) or equivalent gate for other modes, **plus** explicit sign-off (see [Promotion sign-off](#promotion-sign-off)).
- **Commercial viability** for Blueprint Reader remains **`CleanupMode.REFINED`** until a separate baseline and governance reactivation approve otherwise (`BLUEPRINT_READER_PROTECTION_RULES.md`).

---

## Canonical production surface (reference)

| Consumer | Endpoint | Default backend | Lifecycle owner |
|----------|----------|-----------------|-----------------|
| `hostinger/blueprint-reader.html` (Blueprint) | `POST /api/blueprint/vectorize/async` | `CleanupMode.REFINED` → `extract_blueprint_to_dxf()` → `edge_to_dxf.py` | **ACTIVE** |
| `hostinger/blueprint-reader.html` (Photo) | `POST /api/vectorizer/extract` | `PhotoOrchestrator` → `photo_vectorizer_v2.py` | **ACTIVE** |
| Sync twin (same orchestrator) | `POST /api/blueprint/vectorize` | Same as async | **ACTIVE** |

**Not canonical for Hostinger MVP:** Phase 2 `POST /api/blueprint/vectorize-geometry` (`extraction_mode=simple` → Phase 2 only), Phase 3 `ExtractionMode.SIMPLE`, unimplemented `CleanupMode.VECTORIZER_V2_SIMPLE`.

---

## Component registry

States reflect verification run **2026-05-20** (`scripts/governance/verify_vectorizer_audit_results.txt`). Update this table when wiring or promotion changes.

### Extraction and orchestration

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `BlueprintOrchestrator` + `CleanupMode.REFINED` | CANONICAL_PRODUCTION | **ACTIVE** | HTML default; accuracy baseline in protection rules |
| `extract_blueprint_to_dxf()` | CANONICAL_PRODUCTION | **ACTIVE** | Body isolation + grouping (PR-2 telemetry target) |
| `edge_to_dxf.py` grouping | CANONICAL_PRODUCTION | **ACTIVE** (degraded observability) | Fallback exists; PR-2 adds visibility |
| `CleanupMode.BASELINE` / `RESTORED_BASELINE` | CANONICAL_PRODUCTION | **ACTIVE** | Explicit `mode=` only |
| `CleanupMode.V2_RAW` | CANONICAL_RECOVERY | **SANDBOX** | Protected; not default (`MRP_1C`) |
| `CleanupMode.PHOTO_V2` / `PHOTO_REFINED` | CANONICAL_RECOVERY | **SANDBOX** | Photo/blueprint recovery; explicit `mode=` |
| `CleanupMode.ENHANCED` / `LAYERED_DUAL_PASS` | EXPERIMENTAL | **SANDBOX** | Not MVP default |
| `CleanupMode.CAM_READY_R2000` | PRODUCTION (paid) | **ACTIVE** | Auth-gated; Phase 3 R2000 |
| `CleanupMode.VECTORIZER_V2_SIMPLE` | FUTURE (handoff only) | **FUTURE** | **Unwired** — do not implement without gate + governance |
| `ExtractionMode.SMART` (Phase 3) | CANONICAL (via v2_raw / cam_ready branches) | **ACTIVE** | When orchestrator routes to Phase 3 |
| `ExtractionMode.SIMPLE` (Phase 3) | ORPHAN (no production caller) | **BROKEN** → **EXPORT_SAFE** after PR-1 | Not commercially viable after PR-1 alone |
| `vectorizer_phase2.py` | ABANDONED | **ABANDONED** | Dev `/vectorize-geometry` only |
| Phase 2 `extraction_mode=simple` | DEVELOPMENT_ONLY | **SANDBOX** | Not Phase 3 SIMPLE |

### Photo pipeline

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `PhotoVectorizerV2.extract()` | CANONICAL_PRODUCTION | **ACTIVE** | Photo mode on blueprint-reader.html |
| `geometry_coach_v2.py` | ACTIVE | **ACTIVE** | Retry/coaching |
| `geometry_coach.py` v1 | Superseded | **ABANDONED** | Deprecate when convenient |

### Calibration, feedback, learning

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `calibration_integration` / `EnhancedCalibrationPipeline` | PARTIAL | **PARTIAL** | `calibration_router`, `phase2_router`, `constants` — not main vectorize |
| `FeedbackSystem.record_classification` | PARTIAL | **PARTIAL** | One call @ `vectorizer_phase3.py:3673`; SMART + `enable_feedback` |
| `FeedbackSystem.submit_correction` | DEAD | **DEAD** | Zero call sites; expose as **501** if routed (PR-3) |
| `TrainingDataCollector` | DEAD | **DEAD** | Never instantiated |
| `enable_feedback` (orchestrator factory) | DISABLED default | **DISABLED** | Verify default **False** (PR-3) |

### Archaeological research lineage (preserve — do not delete)

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `cognitive_extractor.py` | ORPHAN (unwired) | **ARCHAEOLOGICAL_RESEARCH** | ~1470 LOC; occupancy / semantic experimentation |
| `cognitive_extraction_engine.py` | ORPHAN (unwired) | **ARCHAEOLOGICAL_RESEARCH** | ~1503 LOC; parallel cognition engine |
| `extract_body_grid.py` | ABANDONED (unwired) | **ARCHAEOLOGICAL_RESEARCH** | v1 grid primitive experiments |
| `extract_body_grid_v2.py` – `v5.py` | ABANDONED (unwired) | **ARCHAEOLOGICAL_RESEARCH** | Generations of grid extraction heuristics |
| `march_pipeline_restore.py` | PARTIAL import | **PARTIAL** → Tier B migration | `photo_vectorizer_v2` imports layer export helpers — extract before external move |

**Harvest before delete (future gate):** Document extracted concepts (topology assumptions, grouping ideas, occupancy rules) in `docs/governance/` or handoff; sign-off that no unique semantics remain before any deletion or external move.

### Superseded operational code (not archaeological)

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `vectorizer_phase2.py` | ABANDONED | **ABANDONED** | Superseded by Phase 3 + orchestrator; dev `/vectorize-geometry` only |
| `calibration_integration` (main vectorize) | Not wired | **FUTURE** (orchestrator unify) | Strategic P2, not sprint P0 |

### DXF and governance

| Component | Path classification | Lifecycle state | Notes |
|-----------|---------------------|-----------------|-------|
| `dxf_compat.create_document()` | CANONICAL | **ACTIVE** | Required for all DXF |
| `validate_scale_before_export()` | LOCKED | **ACTIVE** | Protection rules |
| `ibg_intake_gate.py` | CANONICAL | **ACTIVE** | Blocks bad provenance; respects `ok=false` |
| Phase 4 dimension linker | STANDALONE | **FUTURE** | Not integrated |

---

## SIMPLE Commercial Readiness Gate

**Purpose:** Prevent assigning **ACTIVE** or routing `CleanupMode.VECTORIZER_V2_SIMPLE` until SIMPLE is commercially defensible — not merely non-empty DXF.

**Prerequisite:** PR-1 complete (`ExtractionMode.SIMPLE` at least **EXPORT_SAFE**).

### Gate checklist (all required for PRODUCTION_ACTIVE)

| # | Criterion | Evidence required | Owner |
|---|-----------|-------------------|-------|
| G1 | Export integrity | PR-1 test: SIMPLE path → ≥1 LINE entity; fab-bound → `validation_passed=false` on zero export | Engineering |
| G2 | No fabrication-bound SIMPLE without explicit product label | API/UI: experimental or `recommendation.action=reject` default | Product |
| G3 | Body semantics | At least one defensible `BODY_OUTLINE` **or** documented reject when body not inferable | Engineering |
| G4 | Scale parity | Golden asset (Cuatro): width/height within protection-table tolerance vs `refined` baseline | QA |
| G5 | Entity volume bounded | Max entities / simplification policy documented; no 100k+ unreviewed dumps | Engineering |
| G6 | Topology provenance | `topology_provenance` (or debug equivalent) for SIMPLE pipeline failures | Engineering |
| G7 | IBG contract | Written rule: SIMPLE-sourced DXF → review-only vs auto; intake gate tested | IBG / governance |
| G8 | Regression suite | Dedicated tests; CI job; no regression on `refined` golden bytes | CI |
| G9 | Governance approval | Ross explicit approval to add mode or change MVP default (`BLUEPRINT_READER_PROTECTION_RULES.md`) | Ross |
| G10 | Lifecycle doc updated | This registry row → **ACTIVE** with date + sign-off | Engineering |

**Until G1–G10 pass:** lifecycle state for `ExtractionMode.SIMPLE` remains **EXPORT_SAFE** or **SANDBOX** (maximum).

### Explicit non-goals (SIMPLE is not a substitute for)

- Fixing Les Paul `slab_body` @ low confidence (Lane 4 — morphology interpretation)
- Replacing `refined` on `blueprint-reader.html` default
- Satisfying Cuatro golden DXF parity without measurement
- Enabling Loop 3 learning (`submit_correction`, `TrainingDataCollector`)

---

## Promotion sign-off

### To assign **ACTIVE** (production)

1. Component listed in [Component registry](#component-registry) with proposed state.
2. Path classification matches `VECTORIZER_CANONICAL_PATHS.md`.
3. For **SIMPLE** or new **CleanupMode**: [SIMPLE Commercial Readiness Gate](#simple-commercial-readiness-gate) complete (or mode-specific gate added to this doc).
4. `verify_vectorizer_audit.ps1` → 0 FAIL; results file committed or archived in PR description.
5. No change to locked MVP extraction behavior unless step 3 + governance reactivation obtained.
6. Sign-off block filled:

```text
Component: _______________________
New state: ACTIVE
Date: _____________________________
Approved by: ______________________
PR / commit: ______________________
Golden assets verified: ___________
IBG intake rule: __________________
```

### To assign **EXPORT_SAFE** (SIMPLE only, post–PR-1)

- PR-1 merged with unit test.
- Registry row: `ExtractionMode.SIMPLE` → **EXPORT_SAFE**.
- **Do not** wire `VECTORIZER_V2_SIMPLE` or Hostinger default.

### To assign **SANDBOX** (recovery / experimental modes)

- Listed in `BLUEPRINT_READER_PROTECTION_RULES.md` Protected Experimental Recovery Modes **or** documented in capability map.
- Explicit `mode=` / query param required; never HTML default.

---

## Remediation sprint alignment (2026-05-20)

| PR | Lifecycle outcome | Does not imply |
|----|-------------------|----------------|
| PR-2 | `edge_to_dxf` fallback visible; debug `grouping_fallback_*` | SIMPLE commercial viability; cognitive re-integration |
| PR-1 | SIMPLE → **EXPORT_SAFE** | SIMPLE → **ACTIVE** |
| PR-3 | DEAD/PARTIAL truth; 501 on `submit_correction`; doc cross-links | Learning loop enabled |

**Explicitly out of sprint:** Deletion or bulk archive of **ARCHAEOLOGICAL_RESEARCH** files (~5.8k LOC cognitive/grid). Operational freeze only.

---

## Semantic incubation — two-repository model (approved direction)

**Architecture:** `docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`

```text
sandbox discovers  →  production ratifies
```

| Repository | Layer | Role |
|------------|-------|------|
| **luthiers-toolbox** (this repo) | Semantic runtime spine + constitutional runtime | Deterministic extraction, provenance, intake gates, `refined`, IBG — **not** speculative cognition R&D |
| **vectorizer-sandbox** (existing) | Semantic cognition layer | Topology/occupancy research, multi-agent incubation, archaeological lineage — **not** production-adjacent without graduation |
| **ibg-research-sandbox** (optional later) | Lane 4 morphology R&D | Separate charter |

**Graduation:** Sandbox capabilities become production only through evidence → provenance → instrumentation → governance → intake → **new** implementation in `services/`. Never bulk restore or merge unstable sandbox snapshots.

**Incubating in sandbox today (do not promote by import):** `agentic_supervisor.py`, Wave 1 calibration experiments, Wave 3 multi-view handoff scope.

Until Tier A re-home completes: keep archaeological code **in-tree**, **frozen**, with CI grep preventing production imports.

**Migration plan:** `docs/governance/VECTORIZER_SANDBOX_MIGRATION_PLAN.md` → expand https://github.com/HanzoRazer/vectorizer-sandbox (not a separate archaeology graveyard repo).

---

## Maintenance

- Re-run `scripts/governance/verify_vectorizer_audit.ps1` after any vectorizer change.
- Update registry when adding `CleanupMode`, wiring Phase 3 modes, or **relocating** (not deleting) archaeological files.
- Stale debt inventory sections must match this doc (`VECTORIZER_TECHNICAL_DEBT_INVENTORY.md`).
- New lifecycle state assignments for research lineage: **ARCHAEOLOGICAL_RESEARCH** only with one-line “what semantics might live here” in registry notes.

---

*Vectorizer Component Lifecycle Registry — governs promotion of ACTIVE, listing of non-canonical systems, and preservation of archaeological semantic research.*
