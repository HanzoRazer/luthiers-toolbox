# Luthier's ToolBox — 1% Critical Design Review

**Reviewer posture:** Skeptical outside evaluator. No credit for intent — only what the artifact proves.

**Date:** 2026-02-05  
**Artifact:** `luthiers-toolbox-main` (commit snapshot, ~45 MB zipped)  
**Stack:** FastAPI (Python 3.11) + Vue 3/Vite (TypeScript) + SQLite + Docker  

---

## Stated Assumptions

Before scoring, I'm declaring what I'm assuming so you can challenge any premise:

1. **Target user is a solo/small-shop luthier** who also operates a CNC router and possibly a saw station. They are technical enough to install Docker or use a web deployment, but they are *not* software engineers. Their primary job is building guitars.

2. **"Production-ready" means a real person could load this today**, import a DXF of a guitar body, configure a machine profile, and get safe, machinable G-code out the other end — without reading 11 MB of internal developer docs.

3. **The Smart Guitar IoT integration is a secondary product** embedded inside this codebase rather than a separate concern. I'm evaluating it as scope creep unless it's cleanly bounded.

4. **The codebase represents a single-developer project** with extensive AI-assisted development (evidenced by session logs, AI context adapters, CBSP21 protocol docs, and AI sandbox tooling). I'm evaluating the *output*, not the method.

5. **The 37,000+ lines claimed elsewhere are now ~227,000 lines of Python and ~146,000 lines of TypeScript/Vue.** I'm evaluating the actual artifact, not the earlier description.

---

## Category Scores

### 1. Purpose Clarity — 5/10

**What's good:** The README's opening paragraph nails it: "A comprehensive CNC guitar lutherie platform combining parametric design, structural analysis, CAM workflows, and Smart Guitar integration." The feature list is exhaustive and the badge wall communicates active development.

**What's wrong:** The project tries to be *everything* simultaneously — a CAD parametric modeler, a CAM toolpath generator, a multi-post G-code post-processor, an AI-assisted design advisor, a rosette art studio, an acoustic analysis platform, a CNC simulation lab, a Smart Guitar IoT backend, a materials database, a financial calculator for luthiers, a blueprint AI reader, a telemetry system, and a learning/analytics engine. There are 727 API routes. That is not a tool — that is an operating system for a domain that has maybe 10,000 practitioners worldwide.

The `docs/` directory is **11 MB** across **685 markdown files**. There are governance documents, architecture decision records, fence registries, canonical state analyses, session logs, audit reports, and handoff documents — the apparatus of a 50-person enterprise team applied to a one-person project. The documentation *about the system* is more complex than most systems.

**Concrete improvements:**
- Write a single-page "What This Actually Does Today" document with 3 user stories that a luthier could complete end-to-end, with screenshots.
- Kill the README badge wall and replace it with a 30-second demo GIF.
- Separate the vision document (what this *will* do) from the status document (what this *does* today, reliably).

---

### 2. User Fit — 4/10

**What's good:** The domain modeling is genuinely deep. Fret slot calculations comparing Rule of 18 vs. equal temperament, chipload physics, deflection analysis, saw kerf accounting — this is the work of someone who actually builds guitars and understands the manufacturing constraints. The Streamlit demo (`streamlit_demo/app.py` at 2,358 lines) suggests an attempt at an accessible entry point.

**What's wrong:** The actual user-facing surface is a Vue SPA with 53 views, 205 components, and 29 client-side routes that map to 727 backend routes. The home page lands on `RosettePipelineView` — an RMOS (Ross's Manufacturing Operating System) workflow that presupposes the user understands manufacturing pipeline concepts. There is no onboarding flow, no "build your first guitar neck" wizard, no progressive disclosure.

The frontend includes components like `RiskDashboardCrossLab.vue` (2,062 lines), `ManufacturingCandidateList.vue` (2,987 lines), and `ScientificCalculator.vue` (1,609 lines). These are power-user tools with no beginner ramp. A luthier who wants to cut a rosette channel will encounter feasibility scoring, constraint profiles, directional workflow modes (design-first vs. constraint-first vs. AI-assisted), and governance gates before they get G-code.

**Concrete improvements:**
- Implement a "Quick Cut" mode: upload DXF → pick machine → get G-code. Three clicks. No pipeline abstraction.
- User-test with 3 actual luthiers who have never seen the system. Record where they get stuck.
- Move RMOS, governance, analytics, and AI advisory features behind a "Pro Mode" toggle.

---

### 3. Usability — 3/10

**What's good:** The multi-post support (GRBL, Mach4, LinuxCNC, PathPilot, MASSO) is a genuine differentiator. The lab pages (`/lab/cam-essentials`, `/lab/drilling`, `/lab/polygon-offset`) suggest interactive exploration tools. Docker deployment with a single `docker compose up` is the right approach.

**What's wrong:** 727 API endpoints is an unusable API surface for any consumer — human or machine. The `ROUTER_MAP.md` is 34 KB. The `ENDPOINT_TRUTH_MAP.md` is 40 KB. There are consolidated routers and legacy routers and utility-lane routers and operation-lane routers. The backend has **107 router files** in `services/api/app/routers/` alone, plus sub-routers nested in `cam/`, `cnc_production/`, `instruments/`, `music/`, and `art/` directories.

`main.py` is **1,297 lines**, most of which is conditional router registration wrapped in try/except blocks. There are ~20 try/except import blocks that silently downgrade to `None` when routers fail to import. This means the system's API surface changes depending on which optional dependencies happen to be installed. A user hitting a 404 has no way to know if the feature doesn't exist or if it failed to load.

The frontend has a `SimLab_BACKUP_Enhanced.vue` committed to the repository. Backup files in source control are a usability red flag for any contributor.

**Concrete improvements:**
- Reduce the public API surface to ≤50 endpoints. Everything else becomes internal or gets cut.
- Replace conditional router imports with an explicit feature-flag system that reports what's enabled at `/api/features`.
- Delete `main.py`'s router registration and replace it with auto-discovery from a declarative manifest (`routes.yaml`).
- Remove all backup/archive files from the main branch.

---

### 4. Reliability — 4/10

**What's good:** There are 232 test files with ~39,000 lines of test code. The test/code ratio (~17%) is non-trivial. There are safety gates (`app/rmos/gates/policy.py`), feasibility scoring with risk bucketing, and a replay gate policy that blocks drift. The CI guard (`guard_no_legacy_vision_imports.sh`) demonstrates defense-in-depth thinking. Schema contracts have SHA-256 checksums. There is only 1 bare `except:` in the codebase — good discipline.

**What's wrong:** There are **700 broad `except Exception` blocks** across the Python backend. This is the single most dangerous reliability pattern in the codebase. Broad exception handling masks bugs, swallows data corruption, and makes debugging nearly impossible. When a feasibility scorer catches `Exception`, a bad float in a chipload calculation silently returns a fallback value instead of crashing loudly.

The try/except import pattern in `main.py` and `feasibility_scorer.py` (where `rosette_compute`, `DirectionalMode`, and `RosetteParamSpec` all have graceful fallback to `None`) means the system is designed to run in a degraded state *as a normal operating mode*. There is no health check that reports "these 4 features are unavailable because imports failed."

The README claims "100% Test Coverage" and "100% Backend Coverage" but with 227K lines of production Python and 39K lines of tests, the actual line coverage is likely well under 30%. The claim is misleading.

**Concrete improvements:**
- Audit and replace all 700 `except Exception` blocks. Each one should catch the specific exception type or, at minimum, log the full traceback and re-raise in development mode.
- Add a `/api/health/detailed` endpoint that reports the load status of every router and feature module.
- Run `pytest --cov` and publish the actual coverage number. If it's under 40%, admit it and set a target.
- Replace the "100% Test Coverage" badge with the real number.

---

### 5. Maintainability — 3/10

**What's good:** The monorepo structure (`services/api`, `packages/client`, `contracts/`) is sound. The governance framework (ADRs, fence architecture, schema versioning with changelogs) shows intent to manage complexity. The `LEGACY_CODE_STATUS.md` is honest and tracks technical debt with counts. The recent January 2026 cleanup deleted 19 legacy routers and ~4,000 lines — someone is actively fighting entropy.

**What's wrong:** The codebase has metastasized. 227K lines of Python across 1,126 files with 16 files named `schemas.py`, 13 named `store.py`, 12 named `models.py`, and 6 named `service.py`. Navigating this codebase requires reading a 34 KB router map. There is an archived directory (`app/.archive_app_app_20251214`) committed to the repo.

The `docs/` directory contains 685 markdown files including session logs (`SESSION_2026-01-14.md`), AI interaction records (`Spine Bundle_AI Runtime_ Provenance Envelope.txt` at 98 KB), and process documents that are artifacts of the development method rather than documentation of the product. The docs-to-code ratio is pathological: 11 MB of docs for a system that a new developer would struggle to build and run.

The largest Python file (`saw_lab/batch_router.py`) is 2,724 lines. The largest Vue component (`ManufacturingCandidateList.vue`) is 2,987 lines. Both are god-objects that combine data models, business logic, API handlers, and presentation in a single file.

The `CBSP21.md` file (44 KB) defines a "Claude-Based Software Protocol" — a meta-process for AI-assisted development. Whatever its value during development, its presence in the shipped artifact is confusing to any external contributor.

**Concrete improvements:**
- Set a hard file-size limit: no Python file over 500 lines, no Vue component over 800 lines. Refactor the 12 files that exceed this.
- Delete all session logs, AI protocol documents, and development-method artifacts from the repository. Move them to a separate `dev-journal` repo if you want to keep them.
- Consolidate the 16 `schemas.py` files into a single `schemas/` package with domain-based submodules.
- Create a `CONTRIBUTING.md` that lets a new developer run the full test suite in under 5 minutes.

---

### 6. Cost (Resource Efficiency) — 5/10

**What's good:** SQLite as the primary data store is the right choice for a single-user or small-deployment system — zero operational overhead. The Docker setup avoids cloud lock-in. Railway deployment config is included. FastAPI + Uvicorn is a lean stack. No Kubernetes, no message queues, no unnecessary infrastructure.

**What's wrong:** The system loads up to ~70+ routers on startup, each potentially initializing database connections, loading preset files, and registering middleware. For a tool that one person uses at a workbench, this is an engine-block-sized solution for a hand-drill problem. The 87 KB Streamlit demo (`app.py`) duplicates functionality that already exists in the Vue frontend — two UIs for the same backend.

The AI integration (Anthropic API for blueprint analysis, design advisory, and context adapters) adds API cost and latency for features whose value proposition to a luthier at a CNC machine is unclear. The telemetry system, cost attribution module, and smart guitar export pipeline all add complexity without obvious user value in the current state.

**Concrete improvements:**
- Profile startup time. If it's over 5 seconds, lazy-load non-critical routers.
- Pick one frontend (Vue or Streamlit) and delete the other.
- Make AI features opt-in with a clear cost indicator ("This analysis will use ~2K tokens ≈ $0.01").

---

### 7. Safety — 7/10

**What's good:** This is the strongest area. The RMOS feasibility scoring with risk bucketing (the system categorizes operations as safe/caution/danger before generating G-code) is exactly right for a system that controls CNC machinery. The saw safety gate, replay gate policy with drift detection, and CamIntentV1 schema freeze demonstrate real engineering maturity around the part of the system that *can hurt someone*.

The feeds-and-speeds calculations incorporate chipload physics, tool deflection, and material properties. The multi-post system generates machine-specific G-code rather than generic output, reducing the risk of sending unsupported commands to a CNC controller.

**What's wrong:** The 700 broad `except Exception` blocks undermine the safety architecture. If a safety gate calculation throws an unexpected error and gets caught by a broad handler, the system may return a "safe" result for an operation that should have been flagged. Safety-critical code paths must fail *loud* and fail *closed*.

There is no explicit "emergency stop" or "dry run" mode documented in the user-facing interface. G-code preview/simulation exists (`/api/cam/sim`), but it's unclear if users are *required* to simulate before cutting.

**Concrete improvements:**
- Mark all safety-critical code paths (feasibility scoring, G-code generation, feeds calculation) with a `@safety_critical` decorator that disables broad exception handling and enforces fail-closed behavior.
- Add a mandatory simulation step before G-code export, or at minimum a prominent warning dialog.
- Add physical limit validation: if generated G-code commands a feed rate or spindle speed outside the machine profile's declared limits, block the export.

---

### 8. Scalability — 5/10

**What's good:** The monorepo structure and contract-based schema system (`contracts/` with versioned JSON schemas) would support team growth. The governance framework (ADRs, endpoint lifecycle lanes, deprecation registry) is enterprise-grade infrastructure that would serve a team of 5–15 developers well. Pydantic models provide runtime validation. The fence architecture constrains module boundaries.

**What's wrong:** SQLite is a single-writer database. If this system ever serves concurrent users (e.g., a shared workshop or a SaaS deployment), every write serializes. The 10+ SQLite files spread across different modules (data_registry, rmos_db, tool_db, cam_logs, saw_lab queue, pattern_store, workflow sessions, art_studio_rosette_store) would all need migration to Postgres simultaneously.

The monolithic FastAPI application with 727 routes cannot be horizontally scaled — you'd need to decompose into services first. The tight coupling between routers and shared state (multiple stores importing from each other) makes extraction difficult.

**Concrete improvements:**
- Abstract all SQLite access behind a `Repository` interface so the storage backend can be swapped without touching business logic.
- Identify the 3 modules that would need to scale independently first (likely: G-code generation, AI advisory, telemetry) and draw hard dependency boundaries around them now.
- Add a `docker-compose.postgres.yml` variant that proves the system works with Postgres, even if SQLite remains the default.

---

### 9. Aesthetics (UI/UX Design) — 4/10

**What's good:** The lab pages suggest interactive, visual tools — SVG previews for polygon offset, backplot visualization for G-code, and rosette pattern generators. The Vue + Vite stack with modern component composition is the right foundation.

**What's wrong:** Without being able to run the frontend, I can only evaluate from the code. The largest components (2,987-line `ManufacturingCandidateList.vue`, 2,062-line `RiskDashboardCrossLab.vue`) are monolithic single-file components that almost certainly have dense, hard-to-navigate UIs. There is a `RiskDashboardCrossLab_Phase28_16.vue` alongside `RiskDashboardCrossLab.vue` — version-numbered component files suggest iterative redesign without cleanup.

The 53 views and 205 components with no design system, no shared component library documentation, and no Storybook suggest visual inconsistency across the application. A luthier switching between the Rosette Pipeline, Saw Lab, Blueprint Lab, and Preset Hub likely encounters different interaction patterns in each.

**Concrete improvements:**
- Create a shared design system with ≤20 base components (Button, Card, DataTable, Form, Modal, etc.) and require all views to compose from these.
- Add Storybook or Histoire for visual component documentation.
- Delete the phase-numbered component duplicate and establish a single source of truth per view.
- Commission a UX review from a designer who builds things with their hands (woodworker, machinist, etc.) — someone who understands tool UIs.

---

## Summary Scorecard

| Category | Score | Weight | Weighted |
|---|---|---|---|
| Purpose Clarity | 5/10 | 1.0 | 5.0 |
| User Fit | 4/10 | 1.5 | 6.0 |
| Usability | 3/10 | 1.5 | 4.5 |
| Reliability | 4/10 | 1.5 | 6.0 |
| Maintainability | 3/10 | 1.5 | 4.5 |
| Cost / Resource Efficiency | 5/10 | 1.0 | 5.0 |
| Safety | 7/10 | 2.0 | 14.0 |
| Scalability | 5/10 | 0.5 | 2.5 |
| Aesthetics | 4/10 | 0.5 | 4.0 |
| **Weighted Average** | | | **5.15/10** |

---

## Top 5 Actions (Ranked by Impact)

1. **Kill 80% of the API surface.** 727 routes → ≤80. If a route hasn't been called by the frontend in 30 days, delete it. This single action improves usability, maintainability, reliability, and cost simultaneously.

2. **Replace all 700 `except Exception` blocks** with specific exception types. In safety-critical paths (feasibility, G-code, feeds), make failures loud and closed. This is a safety and reliability imperative.

3. **Build a "Quick Cut" onboarding flow.** DXF in → machine selected → G-code out. Three screens. No pipeline abstraction, no governance, no feasibility scoring for the first-time user. Let them graduate to RMOS later.

4. **Separate documentation from development archaeology.** Move session logs, AI protocol documents, and audit artifacts out of the main repo. Reduce `docs/` to ≤20 files that a new user or contributor actually needs.

5. **Enforce file-size limits and delete dead code.** No file over 500 lines (Python) / 800 lines (Vue). Delete backup files, archived directories, and phase-numbered duplicates from the main branch.

---

*This review is intentionally harsh because that's what 1% reviewers do. The domain expertise embedded in this system — the fret math, the chipload physics, the multi-post G-code generation, the safety gates — is genuinely excellent work. The core engineering problem is that the system has grown without pruning, and the governance infrastructure built to manage that growth has itself become a source of complexity. The path forward is subtraction, not addition.*
