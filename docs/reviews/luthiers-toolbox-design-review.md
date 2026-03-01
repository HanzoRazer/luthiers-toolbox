# luthiers-toolbox — 1% Critical Design Review

**Reviewer posture:** Skeptical outside evaluator. No credit for intent — only what the artifact proves.

**Date:** 2026-02-09  
**Artifact:** `luthiers-toolbox-main` (snapshot 15, ~32 MB)  
**Stack:** FastAPI + Vue 3 + SQLite/PostgreSQL  
**Quantitative profile:**
- 253,034 lines of Python across 1,555 files
- 30,492 lines of tests across 183 test files (12% test ratio)
- 992 API route decorators
- 88 router files
- 725 broad `except Exception` blocks
- 1 bare `except:` clause

---

## Stated Assumptions

1. **This is a CNC G-code generation platform for guitar lutherie** — the core domain is parametric design, CAM workflows, and manufacturing safety controls.

2. **The project is under active remediation.** A `REMEDIATION_PLAN.md` exists with 6 phases, and a `CHIEF_ENGINEER_HANDOFF.md` documents the starting state. I'm evaluating the current snapshot against both the original issues and the remediation progress.

3. **The "1,069 tests passing" claim in README** reflects CI status at some point; I cannot verify test execution in this environment.

4. **The Smart Guitar product** is a downstream consumer, with contracts in `contracts/` and telemetry/export schemas enforcing governance boundaries.

5. **This is a single-developer project** that has grown organically over significant time, accumulating both domain expertise and technical debt.

---

## Category Scores

### 1. Purpose Clarity — 7/10

**What's good:** The README clearly states the purpose:

> "A CNC guitar lutherie platform with parametric design tools, CAM workflows, and manufacturing safety controls."

The core features are well-defined:
- **RMOS (Run Manufacturing Operations System):** Feasibility analysis, risk-based gating
- **CAM Workflows:** DXF import, adaptive pocketing, multi-post support
- **Art Studio:** Rosette patterns, relief mapping, SVG-to-toolpath
- **Saw Lab:** Batch sawing with advisory signals

The governance documentation is extensive — `docs/governance/` contains 10+ contracts defining architectural boundaries, trust relationships, and safety constraints.

**What's wrong:** The project has identity fragmentation:
- `CHIEF_ENGINEER_HANDOFF.md` (36KB) is a detailed technical audit
- `REMEDIATION_PLAN.md` (28KB) is an active work plan
- `ROUTER_MAP.md` (34KB) documents API surface
- But the README is only 3KB and doesn't explain the current state

A newcomer cannot tell: Is this a working product? A project under construction? An abandoned codebase being rescued?

The remediation plan claims "262 routes" but I count 992 route decorators. The plan claims "0 files >500 lines" but I count 19+ Python files exceeding 500 lines.

**Concrete improvements:**
- Update README to reflect current state: "Under active remediation. Core CAM functionality is stable. See REMEDIATION_PLAN.md for status."
- Reconcile the metrics discrepancy — either the plan is aspirational or the counts use different methodology.
- Add a "What Works Today" section to README showing the stable feature set.

---

### 2. User Fit — 6/10

**What's good:** The domain expertise is authentic and deep. The codebase contains:
- Rule of 18 vs equal temperament fret calculations
- Chipload physics and tool deflection analysis
- Multi-post G-code generation (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
- Saw kerf accounting
- Risk-based feasibility scoring (GREEN/YELLOW/RED)

The "Quick Cut" mode mentioned in the remediation plan targets the 80% use case: "I have a DXF, I want G-code."

**What's wrong:** The API surface is unusable for any external consumer. 992 routes across 88 router files means:
- No clear entry point
- Overlapping functionality (multiple routes for similar operations)
- Discovery is impossible without reading thousands of lines of code

The Vue frontend (`packages/client/`) exists but its relationship to the API is unclear. The README mentions it but doesn't explain what features are available in the UI vs API-only.

**Concrete improvements:**
- Create a "Core API" subset: the 20-30 routes that cover 80% of use cases.
- Document which features are UI-accessible vs API-only.
- Add OpenAPI examples for the most common workflows (DXF → G-code, fret slot calculation).

---

### 3. Usability — 5/10

**What's good:** The Quick Start in README is clear:
```bash
cd services/api
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The Makefile (11KB) provides automation for common tasks. Docker support exists with compose files for development and production.

**What's wrong:** The `main.py` is 905 lines with 25 try/except blocks for conditional router imports. This creates silent degradation — features may or may not be available depending on which imports succeed.

Example from `main.py`:
```python
try:
    from .rmos.runs_v2.router_query import router as rmos_runs_v2_query_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_v2_query_router (%s)", e)
    rmos_runs_v2_query_router = None
```

This pattern appears 25+ times. A user has no way to know what's actually available without checking logs.

**Nested duplicate directory:** `tap_tone_pi-main (5)/` is 1.6MB of unrelated code sitting in the root. This is either a merge artifact or a failed import.

**Root directory clutter:** 38 items including screenshots (`Screenshot 2026-01-15 033523.png`), text files (`SG-SBX-0.1 — Smart Guitar.txt` at 244KB), and development artifacts.

**Concrete improvements:**
- Add a `/api/features` endpoint that returns what's actually loaded (the plan mentions this but it's not implemented).
- Delete `tap_tone_pi-main (5)/` — this is clearly misplaced.
- Move screenshots and `.txt` dumps out of root.
- Convert conditional router imports to a declarative registry with explicit enable/disable.

---

### 4. Reliability — 5/10

**What's good:** The remediation effort has made significant progress:
- Bare `except:` reduced from 97 to 1 (nearly complete)
- Exception handling audit in progress
- `@safety_critical` decorator concept defined (though implementation status unclear)
- Contract schemas with SHA-256 checksums for integrity

The RMOS system has a mature safety architecture concept:
- Feasibility scoring before G-code generation
- Risk bucketing (GREEN/YELLOW/RED)
- Audit trail for manufacturing runs

**What's wrong:** 725 broad `except Exception` blocks remain. The handoff document identified 278 in safety-critical modules (rmos, cam, saw_lab, calculators). These modules control CNC machinery — a swallowed exception can produce unsafe G-code.

The test ratio is 12% (30,492 test lines / 253,034 production lines). The README claims "1,069 tests passing" but provides no coverage percentage.

The `main.py` import pattern means any ImportError silently disables features. There's no health check that verifies all expected features loaded.

**Concrete improvements:**
- Complete the `except Exception` audit for safety-critical paths (278 sites identified).
- Add a startup health check that fails loudly if safety-critical imports fail.
- Implement the `@safety_critical` decorator and apply to all G-code generation functions.
- Publish actual test coverage percentage, not just pass count.

---

### 5. Maintainability — 4/10

**What's good:** The remediation effort shows awareness:
- Phase 0 (Dead Code Purge) appears complete — no `__ARCHIVE__/`, `__REFERENCE__/`, or stale `client/` directory
- Documentation reduced from 685 files to 30 files
- Router consolidation in progress (88 files, down from 107)

The contract system (`contracts/`) with versioned schemas and SHA-256 checksums is good practice.

**What's wrong:** The codebase is still massive (253,034 lines) with significant structural issues:

**Files over 500 lines (partial list):**
| File | Lines |
|------|-------|
| `adaptive_router.py` | 1,481 |
| `blueprint_router.py` | 1,318 |
| `geometry_router.py` | 1,158 |
| `blueprint_cam_bridge.py` | 971 |
| `main.py` | 905 |
| `dxf_preflight_router.py` | 792 |
| `probe_router.py` | 782 |

The remediation plan claims "0 files >500 lines" — this is not accurate for the current snapshot.

**Nested duplicate:** The `tap_tone_pi-main (5)/` directory (1.6MB) is a complete copy of another project embedded in this repo.

**Development artifacts at root:**
- `Screenshot 2026-01-15 033523.png` (138KB)
- `Screenshot 2026-01-15 033954.png` (174KB)
- `SG-SBX-0.1 — Smart Guitar.txt` (244KB)

**Concrete improvements:**
- Delete `tap_tone_pi-main (5)/` immediately.
- Move screenshots to `docs/images/` or delete.
- Continue god-object decomposition for files over 500 lines.
- Add CI gate that blocks new files over the limit.

---

### 6. Cost (Resource Efficiency) — 6/10

**What's good:** Dependencies are reasonable for the scope:
- FastAPI, Pydantic (web framework)
- NumPy, Shapely, PyClipper (geometry)
- SQLAlchemy, Alembic (database)
- WeasyPrint, ReportLab (PDF generation)

No heavyweight ML frameworks or cloud-specific dependencies in core.

**What's wrong:** The repo is 32MB, which is large for a monorepo. Contributors include:
- 1.6MB nested `tap_tone_pi-main (5)/`
- 312KB of screenshots
- 244KB Smart Guitar text file
- 48KB `architecture_scan.json` report

The 1,555 Python files and 992 routes suggest significant code that could be pruned.

**Concrete improvements:**
- Clean up the artifacts mentioned above (~2.2MB savings).
- Audit routes for duplicates — 992 is excessive for any application.
- Consider splitting into smaller packages if the monorepo is intentional.

---

### 7. Safety — 6/10

**What's good:** The RMOS architecture is designed for safety:
- Feasibility analysis before G-code generation
- Risk-based decision gating (GREEN/YELLOW/RED)
- Audit trail for manufacturing runs
- `@safety_critical` decorator concept (fail-closed behavior)

The governance contracts define trust boundaries between manufacturing (G-code, toolpaths) and consumer-facing products (Smart Guitar telemetry).

The telemetry schema explicitly blocks user data:
```json
"not": {
  "anyOf": [
    { "required": ["player_id"] },
    { "required": ["midi"] },
    { "required": ["audio"] }
  ]
}
```

**What's wrong:** The 725 `except Exception` blocks undermine the safety architecture. From the handoff:

> "These modules control CNC machinery — a swallowed exception here can produce unsafe G-code."

The 278 safety-critical sites identified (rmos: 197, cam: 35, saw_lab: 32, calculators: 14) are still using broad exception handling.

The silent import failure pattern in `main.py` means safety features could be disabled without explicit notification.

**Concrete improvements:**
- Prioritize the 278 safety-critical exception sites.
- Implement startup validation that fails if safety modules don't load.
- Add integration tests that verify the full safety pipeline (feasibility → generation → validation).
- Document the threat model: what happens if each safety gate fails?

---

### 8. Scalability — 5/10

**What's good:** The architecture supports horizontal concerns:
- SQLite/PostgreSQL options for persistence
- Run-based audit trail (each manufacturing job is a "run" with artifacts)
- Contract versioning for schema evolution

**What's wrong:** The 992-route API surface doesn't scale for consumers. Any external integration would need to:
- Discover which routes exist
- Understand which are stable vs experimental
- Handle silent feature degradation

The monolithic `main.py` with conditional imports doesn't support modular deployment.

**Concrete improvements:**
- Implement the route classification from the remediation plan (Core/Power/Internal/Cull).
- Add API versioning (`/api/v1/`, `/api/v2/`).
- Support feature flags for optional modules.

---

### 9. Aesthetics (Design Quality) — 4/10

**What's good:** The governance documentation is well-organized. The contract schemas follow consistent patterns. The Makefile targets are clearly named.

**What's wrong:** The root directory is cluttered:
- 38 items including screenshots, text dumps, nested project
- Multiple `.code-workspace` files
- Development artifacts mixed with configuration

The codebase has accumulated naming inconsistencies:
- `cam/` vs `cam_core/` vs `routers/cam/`
- `rmos/runs/` vs `rmos/runs_v2/`
- `art_studio/` vs `routers/art/`

**Concrete improvements:**
- Clean root directory to <20 items.
- Consolidate duplicate directory structures.
- Standardize naming: one pattern for modules, one for routers.

---

## Summary Scorecard

| Category | Score | Weight | Weighted |
|---|---|---|---|
| Purpose Clarity | 7/10 | 1.0 | 7.0 |
| User Fit | 6/10 | 1.5 | 9.0 |
| Usability | 5/10 | 1.5 | 7.5 |
| Reliability | 5/10 | 1.5 | 7.5 |
| Maintainability | 4/10 | 1.5 | 6.0 |
| Cost / Resource Efficiency | 6/10 | 1.0 | 6.0 |
| Safety | 6/10 | 2.0 | 12.0 |
| Scalability | 5/10 | 0.5 | 2.5 |
| Aesthetics | 4/10 | 0.5 | 2.0 |
| **Weighted Average** | | | **5.41/10** |

---

## Comparison to Related Projects

| Dimension | luthiers-toolbox | sg-spec | string_master | tap_tone_pi |
|---|---|---|---|---|
| Lines of Python | 253,034 | 18,928 | 48,488 | 20,834 |
| Test ratio | 12% | 14% | 28% | 24% |
| Bare excepts | 1 | 0 | 0 | 0 |
| Broad excepts | 725 | 20 | 0 | 34 |
| API routes | 992 | N/A | N/A | N/A |
| Weighted score | **5.41** | **7.59** | **7.45** | **7.68** |

Luthiers-toolbox is the largest and lowest-scoring project in the ecosystem. The other projects demonstrate that focused scope produces maintainable systems. The domain expertise in luthiers-toolbox is exceptional, but it's buried under accumulated complexity.

---

## Progress Since Previous Review

The project has improved from the baseline documented in `CHIEF_ENGINEER_HANDOFF.md`:

| Metric | Baseline | Current | Status |
|--------|----------|---------|--------|
| Bare `except:` | 97 | 1 | ✅ Nearly complete |
| Documentation files | 685 | 30 | ✅ Complete |
| Stale directories | 5 | 1 | 🔶 One remaining |
| Router files | 107 | 88 | 🔶 In progress |
| Broad `except Exception` | 1,622 | 725 | 🔶 In progress |
| Files >500 lines | 30+ | 19+ | 🔶 In progress |

The remediation is working but not complete. The score improved from ~4.7 (corrected baseline) to 5.41.

---

## Top 5 Actions (Ranked by Impact)

1. **Delete the nested duplicate.** `tap_tone_pi-main (5)/` is 1.6MB of unrelated code. This is the highest-priority cleanup.

2. **Complete safety-critical exception hardening.** The 278 sites in rmos/cam/saw_lab/calculators need specific exception types, not broad handlers. This is a safety issue.

3. **Add startup health validation.** The silent import failure pattern must be replaced with explicit health checks that fail loudly if safety features don't load.

4. **Continue god-object decomposition.** 19+ files over 500 lines remain. Prioritize routers (adaptive_router, blueprint_router, geometry_router).

5. **Implement `/api/features` endpoint.** Users need to know what's actually available. The current silent degradation is unacceptable for a manufacturing system.

---

## Assessment

**Score: 5.41/10** — a D+ grade, improved from ~4.7 baseline.

The domain expertise in this project is exceptional — fret mathematics, chipload physics, multi-post G-code generation, and safety gating represent real engineering depth. The remediation effort has made meaningful progress, particularly on bare `except:` blocks and documentation cleanup.

However, the project remains too large (253K lines), too complex (992 routes), and too fragile (725 broad exception handlers) for its single-developer context. The path forward is aggressive subtraction: fewer routes, smaller files, explicit feature boundaries.

The nested `tap_tone_pi-main (5)/` directory is a symptom — it suggests the project boundary is unclear even to its maintainer. Fixing that confusion, both technically and conceptually, is the key to reaching a shippable state.
