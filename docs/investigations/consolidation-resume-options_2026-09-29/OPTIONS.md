# Program options (mutually exclusive)

Three mutually exclusive next-program options. Each names effort, risk, dependencies, and an explicit "not included" list. Exactly one is recommended in `RECOMMENDATION.md`. No implementation is authorized by this increment.

Mutual exclusivity (CRO-015): A continues CF2 containment; B resumes a dormant consolidation feature; C retires proven duplicate/dead code. They touch disjoint surfaces and pursue different goals; only one should be the next dev order.

---

## Option A — Continue CF2 containment (Saw Lab toolpaths cluster)

Contain the two genuinely-ungoverned Saw Lab emitters behind RMOS manufacturing-output authority, mirroring the proven Rosette pattern.

- **Exact routes:** `POST /api/saw/batch/toolpaths/from-decision`, `POST /api/saw/compare/toolpaths` (ledger CF2-03).
- **Shared implementation surface:** both call `generate_toolpaths_from_decision` in `services/api/app/services/saw_lab_toolpaths_from_decision_service.py` — one authority derivation covers both.
- **Why they belong together:** identical service + subsystem (Saw Lab), both derive toolpaths from a saw *decision*, no governed sibling exists (unlike geometry/polygon draft lanes).
- **Expected inventory movement:** `LIVE_UNGOVERNED` 13 → 11; `PERMITTED_BY_AUTHORITY` stays 0 (true-A classifier contract).
- **Likely file count:** ~6–8 (router(s) + summary/authority helper reuse from `rmos/rosette_output_authority` pattern or a saw-local pure helper + tests + inventory JSON/MD + CBSP21 manifest).
- **Principal safety risk:** saw batch/compare produce cut toolpaths; refusal-before-generation and single-artifact persistence must be exact (directly testable, mirrors Rosette RDS/REX suites).
- **Effort:** medium-low (proven template). **Risk:** low-medium. **Dependencies:** none beyond the merged Rosette authority services.
- **Not included:** geometry/radius-dish/inlay/headstock/rmos/vision rows; any generator/physics change; the draft-lane rows (polygon_offset.nc, export_gcode).

## Option B — Resume a dormant consolidation feature (Art design-first workflow)

Connect the existing but disconnected Art Studio design-first workflow (client SDK/store/panels present; backend HTTP contract absent).

- **Exact feature:** `/api/art/design-first-workflow/*` backend contract for the existing client assets (ledger CONS-09).
- **Current code assets:** client `sdk/endpoints/artDesignFirstWorkflow*.ts`, `stores/artDesignFirstWorkflowStore.ts`, `DesignFirstWorkflowPanel(V2).vue`; skipped contract test `test_art_studio_promotion_intent_export_contract.py`.
- **Missing connection:** backend routes (tests skipped "Routes … not implemented"); panels are unwired (zero imports outside themselves).
- **User-visible benefit:** activates a design-first authoring flow already half-built on the client.
- **Authoritative implementation boundary:** Art Studio workflow package + a new router; must respect ornament-authority scope gate and FEATURE_PARITY_MIGRATION_POLICY.
- **Why it could precede more CF2:** completes stranded investment rather than adding new surface.
- **Effort:** medium-high (new backend contract + wiring). **Risk:** medium (new production routes; scope-gate compliance). **Dependencies:** Art Studio schemas, ornament-authority scope gate.
- **Not included:** CF2 containment; ApertureWorkspace parity (CONS-10); any manufacturing-output change.

## Option C — Retirement / duplication cleanup (superseded backend cluster)

Retire a proven `DUPLICATE_SUPERSEDED` cluster whose canonical survivors are mounted and live.

- **Canonical survivors / retirement targets:**
  - `cam_core/api/saw_lab_router.py` (CONS-03) → survivor `app.saw_lab.__init_router__` (manifested).
  - `routers/instrument_geometry_router.py` monolith (CONS-08) → survivor split package `app.routers.instrument_geometry`.
  - `rmos/acoustics/router.py` aggregator (CONS-07) → survivor `runs_v2/acoustics_router.py` + direct imports.
  - `core/features.py` `register_all_features` (CONS-05) → survivor `router_registry`.
  - (Optional, surgical) the dead HTTP surface in `rmos/api/rmos_feasibility_router.py` (CONS-04) — **keep the live `compute_feasibility_internal` library**.
- **Import/route/build proof:** each target is unmounted (not in any manifest / commented out / `= None`), while its survivor is manifested; `check_manifest_discipline.py` baseline + `include_router` census are the proof surface.
- **Rollback method:** pure deletions of unmounted code; rollback = `git revert` (no runtime path changes to reverse since targets are unreachable).
- **Expected simplification:** removes several unmounted/parallel router shells; shrinks the 103-entry unmanifested baseline; clarifies canonical vs legacy.
- **Effort:** medium (proof-per-target + baseline updates). **Risk:** low for the clearly-unmounted targets; medium for CONS-04 (shared module hosting the live evaluator) — treat separately/surgically.
- **Not included:** CF2 containment; the design-first feature; `api_v1` (live, client-depended — not a retirement target); anything reachable; `DEAD_CONFIRMED` vectorizer FeedbackSystem (governed-dead; needs a separate owner ruling per CLAUDE.md).

---

## Cross-option notes
- `DEFERRED_AUTHORIZED` draft lanes (polygon_offset.nc, export_gcode) are excluded from A by design; treat via a documentation/policy decision, not containment.
- `PROTOTYPE_EXPLICIT` items (cam/rosette/prototypes, phase4, vectorizer three-loop/AGE) are out of all three options — isolated, documented, not to be retired on age.
- `api_v1` dual-surface (CONS-17) is a documentation/convergence topic, not A/B/C.
