# Critical Systems Design Review: luthiers-toolbox

**Review Date:** 2026-03-18  
**Reviewer:** Critical Systems Design Reviewer (Top 1%)  
**Methodology:** Source code analysis, documentation review (README, PRODUCT_DEFINITION, BOUNDARY_RULES, SYSTEM_EVALUATION, TESTING_STRATEGY, DEPLOYMENT_VALIDATION), safety/CAM/rmos code and tests, router registry, client dashboard/nav.

---

## Score chronicle (for tracking change over time)

| Date       | Document / Snapshot              | Overall score | Notes |
|------------|----------------------------------|---------------|--------|
| (earlier)  | luthiers-toolbox-design-review   | 5.41/10       | Baseline (D+) |
| 2026-02-09 | luthiers-toolbox-16-design-review | 6.68/10       | Weighted average; Snapshot 16 |
| 2026-02-23 | SYSTEM_DESIGN_REVIEW_2026-02-23  | 5.0/10        | Reliability 3/10 critical |
| 2026-02-28 | DESIGN_REVIEW_2026-02-28         | 6.6/10        | Safety 8/10 |
| **2026-03-18** | **CRITICAL_SYSTEMS_REVIEW_2026-03-18** | **6.1/10** | Unweighted average of category scores below |

*To chronicle future reviews:* Add a row to this table and keep the document filename dated (e.g. `CRITICAL_SYSTEMS_REVIEW_YYYY-MM-DD.md`).

---

## Related documents (traceability)

Future development teams can trace evaluation and remediation progress using these six documents (paths relative to repo root):

1. **[docs/SYSTEM_EVALUATION.md](../SYSTEM_EVALUATION.md)** — Living full-stack audit: architecture, backend, frontend, testing, observability, security, CNC safety, edge cases, dashboard, UX. Deep-dive reference; no single overall score in header.
2. **[docs/REVIEW_REMEDIATION_PLAN.md](../REVIEW_REMEDIATION_PLAN.md)** — Score history (5.41 → 6.68), goal 7.0+, remediation phases, and metric tables. Based on Snapshot 16; gap to target.
3. **[docs/SCORE_7_PLAN.md](../SCORE_7_PLAN.md)** — Path to 7/10: current ~6.4, target 7.0, exit gates. Active plan.
4. **[docs/TOOLBOX_EVALUATION.md](../TOOLBOX_EVALUATION.md)** — Shorter evaluation; overall 7.5/10. Different methodology/scope.
5. **[docs/REMEDIATION_PLAN_v2.md](../REMEDIATION_PLAN_v2.md)** — Follow-on remediation plan based on Snapshot 16 (6.68); goal 7.0+.
6. **Dated snapshot reviews** (this folder) — Previous scored reviews for chronicling; link to the specific file when updating the score chronicle table above:
   - [luthiers-toolbox-design-review.md](luthiers-toolbox-design-review.md) — Baseline 5.41/10
   - [luthiers-toolbox-16-design-review.md](luthiers-toolbox-16-design-review.md) — Snapshot 16, 6.68/10 (weighted)
   - [SYSTEM_DESIGN_REVIEW_2026-02-23.md](SYSTEM_DESIGN_REVIEW_2026-02-23.md) — 5.0/10
   - [DESIGN_REVIEW_2026-02-28.md](DESIGN_REVIEW_2026-02-28.md) — 6.6/10
   - [DESIGN_REVIEW_SNAPSHOT_19.md](DESIGN_REVIEW_SNAPSHOT_19.md)
   - [DESIGN_REVIEW_2026-02-22.md](DESIGN_REVIEW_2026-02-22.md)
   - [DESIGN_REVIEW_2026-02-18.md](DESIGN_REVIEW_2026-02-18.md)

*This document* is a dated snapshot review for chronicling; it does not replace SYSTEM_EVALUATION.md. When adding a new review, add a row to the **Score chronicle** table and link to this doc from REVIEW_REMEDIATION_PLAN or SCORE_7_PLAN if using it for remediation tracking.

---

## Status of similar artifacts in the repo

| Artifact | Purpose | Status |
|----------|---------|--------|
| [SYSTEM_EVALUATION.md](../SYSTEM_EVALUATION.md) | Living full-stack audit (architecture, backend, frontend, testing, observability, security, CNC safety, edge cases, dashboard, UX). No single overall score in header; deep-dive reference. | Authoritative long-form evaluation; referenced by UNFINISHED_REMEDIATION_EFFORTS, TESTING_STRATEGY. |
| [REVIEW_REMEDIATION_PLAN.md](../REVIEW_REMEDIATION_PLAN.md) | Tracks score history (5.41 → 6.68), goal 7.0+, phases, and metric tables. | Based on Snapshot 16; gap 0.32 to target. |
| [SCORE_7_PLAN.md](../SCORE_7_PLAN.md) | Path to 7/10; current ~6.4, target 7.0; exit gates. | Active plan. |
| [TOOLBOX_EVALUATION.md](../TOOLBOX_EVALUATION.md) | Shorter evaluation; overall 7.5/10. | Different methodology/scope. |
| [REMEDIATION_PLAN_v2.md](../REMEDIATION_PLAN_v2.md) | Based on Snapshot 16 (6.68); goal 7.0+. | Pending. |
| [docs/reviews/](.) (this folder) | Dated snapshot reviews with category scores and overall score. | DESIGN_REVIEW_2026-02-28 (6.6), SYSTEM_DESIGN_REVIEW_2026-02-23 (5.0), luthiers-toolbox-16-design-review (6.68), DESIGN_REVIEW_SNAPSHOT_19, DESIGN_REVIEW_2026-02-22, DESIGN_REVIEW_2026-02-18. |

---

## Stated assumptions

1. **Context:** CNC guitar lutherie platform (design → CAM → G-code) with RMOS safety layer; self-hosted/single-tenant; primary users are luthiers/shop operators.
2. **Scope:** Full stack (Vue 3 client, FastAPI backend, SQLite + file storage), including RMOS, CAM, Art Studio, Saw Lab, calculators.
3. **Criticality:** G-code and feasibility paths can cause physical harm or machine damage; safety and correctness in those paths are treated as critical.
4. **Evidence:** README, PRODUCT_DEFINITION, BOUNDARY_RULES, SYSTEM_EVALUATION, TESTING_STRATEGY, DEPLOYMENT_VALIDATION, safety/cam/rmos code and tests, router registry, client dashboard/nav.
5. **Bias:** Fail-closed safety, clear boundaries, testability, and operational clarity favored over feature count or UI polish alone.

---

## 1. Purpose clarity — 8/10

**Justification:** PRODUCT_DEFINITION states the one core job (“design files → safe, machine-ready G-code with verified geometry and pre-cut validation”) and tiers (Core / Supporting / Optional / Deprecated). README and docs consistently describe a CNC guitar CAM + safety platform, not a generic CAD/CAM or cloud product. Boundaries (ToolBox vs Analyzer, what the product is/is not) are explicit. Minor gaps: no single “product one-pager” for stakeholders; “Production Shop” vs “Luthiers-Toolbox” naming is mixed in docs.

**Improvements:**
- Add a one-page **Product one-pager** (problem, one-sentence mission, Tier 1 success metrics, primary user journeys, out-of-scope) and link it from README and PRODUCT_DEFINITION.
- Standardize naming: pick “The Production Shop” or “Luthiers-Toolbox” as the official product name and use it everywhere (README, docs, UI, API titles).
- In README “What Works Today”, add one sentence per module stating the user outcome (e.g. “RMOS: block unsafe jobs before they reach the machine”).

---

## 2. User fit — 7/10

**Justification:** Primary journeys (DXF → G-code, parametric → DXF → G-code) match luthiers/shop operators. Calculators (frets, bridge, rosette) and machine posts (GRBL, Mach4, LinuxCNC, PathPilot, MASSO) are domain-appropriate. Art Studio, inlay, binding, neck/headstock, Smart Guitar are coherent extensions. No evidence of formal user research, personas, or success metrics per journey; CCEX gaps deferred “until reference measurements” shows awareness of expert data needs but no clear path to capture them.

**Improvements:**
- Define 2–3 **personas** (e.g. “one-off builder”, “small shop”, “CNC-first shop”) and map Tier 1/2 features and journeys to them.
- Add **journey success metrics** (e.g. “Journey 1: &lt; 5 min for experienced user”) to PRODUCT_DEFINITION and track in sprint/backlog.
- Document a **CCEX data capture plan**: who captures reference measurements, format (e.g. JSON schema), and where they live (e.g. `instrument_geometry/` or a separate ref-data repo).

---

## 3. Usability — 5/10

**Justification:** Backend API surface is rich and documented (Swagger, feature catalog). Frontend has a clear module nav (Design, Art Studio, CAM, Shop Floor, Smart Guitar), CAM Workspace wizard, and design tokens. SYSTEM_EVALUATION reports serious UX issues: Tailwind-like classes without Tailwind (broken styles), duplicate toasts, widespread `window.confirm()`, SDK bypass in stores, no global error boundary, weak loading/empty/auth-consistent patterns, no tooltips/shortcuts/accessibility strategy. That matches a “backend-first, frontend functional but inconsistent” state.

**Improvements:**
- **Fix Tailwind:** Either add Tailwind (and a small design-system pass) or remove all Tailwind-like utility classes and replace with existing design-token CSS so production styling is consistent.
- **Unify notifications:** Pick one toast system (e.g. vue-toastification), migrate all call sites, remove the other; use a single `useToast()` composable.
- **Replace `window.confirm()`:** Use one confirmation pattern (e.g. SmallModal or a dedicated ConfirmModal) for all destructive actions; add a composable `useConfirm()`.
- **Add global error boundary:** Implement `app.config.errorHandler` and an error-boundary component for route-level failures; log to console and show a “Something went wrong” view with request-id.
- **Auth and empty states:** Add route guards and empty-state components for key views (e.g. CAM Workspace, Job Queue, Manufacturing Runs) so “no data” is explicit and guarded routes are consistent.

---

## 4. Reliability — 6/10

**Justification:** Strengths: request-id propagation, atomic RMOS writes (temp + `os.replace`), safety-critical decorator with fail-closed (re-raise), startup validation of safety-critical modules, 773+ tests and golden G-code tests. Weaknesses: ~20% backend coverage with no `--cov-fail-under`; try/except router loading can hide missing routes; no retry in critical I/O paths; singleton in-memory stores (e.g. constraint_profiles, learned_overrides) make multi-instance deployment unsafe; no artifact/temp-file cleanup (disk growth).

**Improvements:**
- **Coverage gate:** Add a coverage floor in CI (e.g. `pytest --cov-fail-under=25`) and raise incrementally; focus first on `app/rmos/`, `app/cam/`, `app/safety/`, `app/core/safety.py`.
- **Router loading:** On router load failure, log at ERROR/CRITICAL, include failed module in health check (e.g. `startup.safety_critical` style) so “missing routes” is visible; consider failing startup if a required router fails.
- **Retries:** Introduce limited retries (with backoff) for file and DB operations in RMOS run save/load and CAM artifact write; keep safety paths fail-closed (no silent swallow).
- **Singletons:** Document “single-instance only” in deployment docs until addressed; then replace module-level singletons with explicit injectables (e.g. FastAPI dependencies or a small container) so multi-instance can be supported later.
- **Cleanup:** Add a scheduled or on-start job to delete orphaned temp files and failed-run artifacts older than N days, with a configurable retention policy.

---

## 5. Manufacturability / maintainability — 7/10

**Justification:** Router registry and domain manifests (cam, art_studio, rmos, etc.) keep main.py small and routers discoverable. Boundary rules and fence checks (e.g. ToolBox vs Analyzer, RMOS vs CAM) are enforced in CI. Decomposition work (job_queue, presets, manifest) shows good modularization. Duplicate safety entry points (`app.safety` vs `app.core.safety`) and mixed imports (`from app.safety` vs `from app.core.safety`) create confusion and risk of divergent behavior; `cam_cutting_evaluator_fixed.py` suggests legacy/copy debt. Large app (1,200+ Python files, 88 routers) with no high-level “domain map” makes onboarding harder.

**Improvements:**
- **Single safety module:** Keep one canonical implementation (e.g. `app.core.safety`) and re-export from `app.safety` with a deprecation notice; migrate all call sites to `app.core.safety` and remove the duplicate implementation.
- **Domain map:** Add a single **ARCHITECTURE.md** section or doc (e.g. “Domain map”) listing top-level domains (RMOS, CAM, Art Studio, Saw Lab, Calculators, Safety), their entry routers, and one sentence each; link from README and onboarding.
- **Remove or merge fixed/legacy:** Either fold `cam_cutting_evaluator_fixed.py` into `cam_cutting_evaluator.py` with tests, or delete the duplicate and route callers to the canonical module; add a short “no duplicate implementations” rule to DECOMPOSITION_GUIDELINES or BOUNDARY_RULES.
- **Dependency injection:** Introduce a small DI or “app context” for stores and RMOS dependencies so tests and future multi-instance deployments don’t rely on global state.

---

## 6. Cost — 6/10

**Justification:** No explicit cost model in the reviewed docs. Stack (Vue, FastAPI, SQLite, file storage) is low-cost and self-hosted. Cost attribution exists in code (e.g. `test_cost_attribution_mapper_unit`) but isn’t tied to user-facing features or run-based costing. Resource use (CPU/memory for long CAM runs, disk for artifacts) is not documented; unbounded artifact growth can drive storage cost. License (MIT) and lack of SaaS pricing keep cost predictable for adopters.

**Improvements:**
- **Run/artifact cost:** Document “cost of a run” (storage per run, retention, recommended disk and backup) in DEPLOYMENT_VALIDATION or a new “Operations guide”; link retention/cleanup to that.
- **Resource guidance:** Add a “Resource sizing” section (e.g. “single instance: N GB RAM, M vCPU for typical CAM workload”) based on existing or new benchmarks.
- **Cost attribution:** If cost attribution is used for internal billing or reporting, expose it in a single place (e.g. API or admin view) and document the model in BUSINESS_SUITE_SPEC or a short cost doc.

---

## 7. Safety — 8/10

**Justification:** RMOS feasibility layer with GREEN/YELLOW/RED and 22+ rules; `@safety_critical` used on feasibility, G-code generation, feeds/speeds, and critical CAM paths with fail-closed (log + re-raise). Startup validation blocks if safety-critical modules don’t load. G38.2 probe cycle, preflight gates, and CNC safety validator show awareness of physical risk. G-code validation/linting and Saw Lab advisory/override are present. Gaps: two implementations of `safety_critical` (audit trail differs); no explicit “safety manual” or operator checklist; no formal verification that every G-code-emitting path is behind RMOS or an equivalent gate.

**Improvements:**
- **Single safety decorator:** Consolidate on one `safety_critical` (see Maintainability); ensure one audit contract (e.g. CRITICAL on failure, optional DEBUG on entry/exit).
- **Safety manual:** Add a short **SAFETY.md** or “Operator safety” section: what RMOS blocks, meaning of GREEN/YELLOW/RED, that the system does not replace machine guarding or operator responsibility, and link to machine-specific safety docs.
- **G-code path audit:** List every endpoint or code path that emits G-code; verify each is either behind RMOS feasibility or an explicit “no RMOS” justification (e.g. probe/setup-only); add a CI or fence check that new G-code-emitting routes are registered.
- **Probe and preflight:** Document G38.2 and channel-depth probe behavior (intent, limits, failure handling) in cam docs so operators and maintainers know what “safe” means for probing.

---

## 8. Scalability — 5/10

**Justification:** Single FastAPI process, no message queue, no distributed locking, no cache layer; concurrency is process-local. Fine for single-shop, single-instance use. SYSTEM_EVALUATION and main.py confirm no service mesh, no background task queue for long CAM jobs. Many routers and routes can handle moderate request volume, but long toolpath generation blocks a worker; singleton stores and file-based RMOS runs make horizontal scaling unsafe. Docker Compose and Nginx support one production instance.

**Improvements:**
- **Document scale assumptions:** In DEPLOYMENT_VALIDATION or ARCHITECTURE, state “Designed for single-instance deployment; multi-instance not supported until singletons and run storage are refactored.”
- **Async CAM for long jobs:** For long-running CAM (e.g. full guitar toolpath), add an optional background task (e.g. FastAPI BackgroundTasks or a minimal queue) and poll/SSE status so the HTTP worker isn’t blocked for minutes.
- **Read-only scaling:** If needed later, consider read replicas for calculator and catalog endpoints only, with writes still on a single instance; document as a future option once storage and singletons are addressed.

---

## 9. Aesthetics — 5/10

**Justification:** Design tokens (colors, spacing, typography, breakpoints) and a coherent nav structure give a base for a consistent UI. SYSTEM_EVALUATION and code show Tailwind-like classes without Tailwind (so many “intended” styles don’t apply), duplicate toasts, and mixed confirmation patterns, which hurt perceived polish and consistency. No shared illustration set or empty-state art; accessibility and responsive behavior are not systematized. Aesthetics are “functional, inconsistent” rather than a differentiator.

**Improvements:**
- **Fix styling first:** Resolving the Tailwind/utility-class issue (see Usability) will immediately improve visual consistency.
- **Design tokens:** Publish a one-pager (or Storybook) showing primary components (buttons, cards, inputs, modals) using only design tokens so new screens stay on-brand.
- **Empty and error states:** Introduce a small set of illustrations or icons for “no data”, “error”, “loading” and use them in key views (CAM Workspace, Job Queue, Runs).
- **Accessibility:** Add a minimal a11y standard (e.g. ARIA where needed, focus order, one keyboard-navigable flow for DXF → G-code) and one automated check (e.g. axe-core in CI for critical routes).

---

## Summary scorecard

| Category            | Score | Priority  |
|---------------------|-------|-----------|
| Purpose clarity     | 8/10  | Low       |
| User fit            | 7/10  | High      |
| Usability           | 5/10  | High      |
| Reliability         | 6/10  | High      |
| Manufacturability   | 7/10  | Medium    |
| Cost                | 6/10  | Medium    |
| Safety              | 8/10  | Critical  |
| Scalability         | 5/10  | Medium    |
| Aesthetics          | 5/10  | Low       |

**Overall (unweighted average): 6.1/10**

*Weighted scoring (e.g. Safety 2.0, Usability/User fit 1.5) would raise the overall slightly; use the same weighting as Snapshot 16 for comparable trend.*

---

## Top 5 critical improvements (ranked)

1. **Unify safety module and add coverage gate** — Single `safety_critical` implementation; `--cov-fail-under` in CI for safety/CAM/rmos paths.
2. **Fix frontend consistency** — Tailwind or design-token-only styling; one toast system; one confirm pattern; global error boundary.
3. **Router loading and health** — Fail or degrade health when a router fails to load; no silent missing routes.
4. **Document operator safety and G-code paths** — SAFETY.md; audit every G-code-emitting path against RMOS/gates.
5. **Retention and cleanup** — Configurable artifact/temp retention; document “cost of a run” and single-instance scale assumptions.

---

## Codebase / doc snapshot (at review time)

| Metric | Value |
|--------|--------|
| Backend tests | 773+ (README); 1,069 (SYSTEM_EVALUATION) |
| Backend coverage | ~20% (no fail-under) |
| Routers | 88 (manifest); 262 routes (SYSTEM_EVALUATION) |
| Python files (app) | 1,200+ |
| @safety_critical sites | 26+ (REVIEW_REMEDIATION_PLAN); multiple files use `app.safety` vs `app.core.safety` |
| Key docs | PRODUCT_DEFINITION, BOUNDARY_RULES, SYSTEM_EVALUATION, TESTING_STRATEGY, DEPLOYMENT_VALIDATION, SPRINT_BOARD |
