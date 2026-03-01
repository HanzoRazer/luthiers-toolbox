# luthiers-toolbox — 1% Critical Design Review (Snapshot 16)

**Reviewer posture:** Skeptical outside evaluator. No credit for intent — only what the artifact proves.

**Date:** 2026-02-09  
**Artifact:** `luthiers-toolbox-main` (snapshot 16, ~30 MB)  
**Stack:** FastAPI + Vue 3 + SQLite/PostgreSQL  
**Quantitative profile:**
- 253,510 lines of Python across 1,411 files
- 30,492 lines of tests across 158 test files (12% test ratio)
- 994 API route decorators
- 92 router files
- 691 broad `except Exception` blocks (down from 725)
- 1 bare `except:` clause
- main.py: 207 lines (down from 905)

---

## Stated Assumptions

1. **This is a CNC G-code generation platform for guitar lutherie** with parametric design tools, CAM workflows, and manufacturing safety controls.

2. **Active remediation is ongoing.** Comparing to snapshot 15 to evaluate progress.

3. **The "1,069 tests passing" claim** in the remediation plan reflects CI status; I cannot verify execution.

4. **Smart Guitar product** is a downstream consumer with governance contracts.

5. **Single-developer project** that has grown organically, now under disciplined cleanup.

---

## Delta from Snapshot 15

| Metric | Snapshot 15 | Snapshot 16 | Change |
|--------|-------------|-------------|--------|
| Total size | 32 MB | 30 MB | ✅ -6% |
| Python files | 1,555 | 1,411 | ✅ -144 files |
| main.py lines | 905 | 207 | ✅ -77% |
| Broad `except Exception` | 725 | 691 | ✅ -34 |
| Root items | 38 | 33 | ✅ -5 |
| Nested tap_tone_pi | 1.6 MB | Deleted | ✅ Removed |
| Screenshots at root | 2 files | 0 | ✅ Cleaned |
| detailed_outlines.py | 2,088 lines | 25 lines | ✅ JSON refactor |
| Router registry | None | Implemented | ✅ New |
| Startup validation | None | Implemented | ✅ New |
| @safety_critical decorator | Concept | 6 call sites | ✅ Deployed |
| /api/features endpoint | None | Implemented | ✅ New |

**Significant architectural improvements since snapshot 15.**

---

## Category Scores

### 1. Purpose Clarity — 8/10 (↑ from 7)

**What's good:** The purpose remains clear and the project identity is stabilizing:

> "CAM system for guitar builders - DXF templates, G-code generation, manufacturing orchestration"

The router registry (`router_registry.py`) now provides a declarative manifest of all API capabilities organized by category:
- `core` (required)
- `cam_core` (11 routers)
- `rmos` (4 routers)
- `art_studio`, `calculators`, `machine_config`, etc.

The `/api/features` and `/api/features/catalog` endpoints make available functionality discoverable.

**What's still wrong:** The REMEDIATION_PLAN.md claims "0 files >500 lines" but I count 14+ files exceeding 500 lines. Either the plan uses different methodology or hasn't been updated.

**Concrete improvements:**
- Reconcile remediation plan metrics with actual codebase state.
- Update README to point users to `/api/features` for capability discovery.

---

### 2. User Fit — 7/10 (↑ from 6)

**What's good:** The domain expertise remains exceptional, and it's now more accessible:
- `/api/features` endpoint shows what's available
- Router categories in the manifest make functionality findable
- Startup validation ensures users know if safety features loaded

The `detailed_outlines.py` refactor demonstrates good data-vs-code separation — 2,041 coordinate points moved to JSON, Python wrapper is 25 lines.

**What's still wrong:** 994 routes is still overwhelming. The remediation plan targeted <300 routes; this hasn't been achieved.

**Concrete improvements:**
- Continue route consolidation toward the 300 target.
- Add usage examples to `/api/features/catalog` for top 10 workflows.

---

### 3. Usability — 7/10 (↑ from 5)

**What's good:** Major improvements:

**main.py refactored from 905 → 207 lines.** The 25+ try/except import blocks are replaced with a declarative router registry:

```python
# Before (snapshot 15):
try:
    from .rmos.runs_v2.router_query import router as rmos_runs_v2_query_router
except ImportError as e:
    _log.warning("Optional router unavailable: rmos_runs_v2_query_router (%s)", e)
    rmos_runs_v2_query_router = None

# After (snapshot 16):
for router, prefix, tags in load_all_routers():
    app.include_router(router, prefix=prefix, tags=tags)
```

**Startup validation implemented.** Safety-critical modules are verified at startup:
```python
@app.on_event("startup")
def _startup_safety_validation() -> None:
    strict_mode = os.getenv("RMOS_STRICT_STARTUP", "1") != "0"
    validate_startup(strict=strict_mode)
```

**Health endpoints report loaded features:**
- `/health` — basic CI compatibility
- `/api/health` — router summary + AI status
- `/api/features` — loaded API features
- `/api/features/catalog` — feature catalog with use cases

**What's still wrong:** Root directory still has 33 items (target was <20). Development artifacts like `AGENT_SESSION_BOOKMARK.md` and `REVIEW_REMEDIATION_PLAN.md` remain.

**Concrete improvements:**
- Move session/review artifacts to `docs/internal/`.
- Target <25 root items.

---

### 4. Reliability — 6/10 (↑ from 5)

**What's good:** Significant safety infrastructure deployed:

**@safety_critical decorator implemented and deployed:**
```python
@safety_critical
def compute_feasibility(...):
    ...  # Never swallows exceptions, logs CRITICAL, always re-raises
```

Decorator applied to 6 critical call sites:
- `rmos/feasibility/engine.py`
- `rmos/operations/cam_adapter.py` (2 sites)
- `rmos/operations/saw_adapter.py` (2 sites)
- `cam/rosette/cnc/cnc_gcode_exporter.py`

**Specific exception types defined:**
- `FeasibilityError`, `FeasibilityInputError`, `FeasibilityRuleError`
- `GCodeGenerationError`, `ToolpathError`
- `MaterialError`, `MachineConfigError`
- `RunArtifactError`, `AuditTrailError`
- `SawLabError`, `DecisionIntelligenceError`

**Startup validation ensures safety modules load:**
```
STARTUP BLOCKED: 2 safety-critical module(s) failed to load:
  - app.rmos.feasibility.engine: No module named 'app.rmos.feasibility.engine'
  - app.saw_lab.batch_router: No module named 'app.saw_lab.batch_router'

The server cannot start without these modules.
```

**What's still wrong:** 691 broad `except Exception` blocks remain. The handoff identified 278 in safety-critical paths — progress has been made (725 → 691) but ~200 safety-critical sites likely still need attention.

Test ratio remains at 12%. No coverage percentage published.

**Concrete improvements:**
- Complete exception hardening for remaining safety-critical paths.
- Expand @safety_critical coverage to all G-code generation functions.
- Publish test coverage percentage in CI.

---

### 5. Maintainability — 6/10 (↑ from 4)

**What's good:** Substantial structural improvements:

**Nested duplicate removed:** `tap_tone_pi-main (5)/` deleted (1.6MB savings).

**detailed_outlines.py refactored:** From 2,088 lines of Python data to 25-line loader + 80KB JSON file. This follows the pattern recommended in the WP-3 handoff.

**Router registry centralizes loading:** Single manifest for all 92 routers with category, required flag, and health tracking.

**Root directory cleaned:** Screenshots and text dumps removed. 38 → 33 items.

**What's still wrong:** 14+ Python files still exceed 500 lines:

| File | Lines |
|------|-------|
| `adaptive_router.py` | 1,244 |
| `blueprint_router.py` | 1,236 |
| `geometry_router.py` | 1,100 |
| `blueprint_cam_bridge.py` | 937 |
| `dxf_preflight_router.py` | 792 |
| `probe_router.py` | 782 |
| `fret_router.py` | 696 |
| `cam_metrics_router.py` | 653 |

The remediation plan claims "Phase 3 COMPLETE: 0 files >500 lines" — this is not accurate for the current snapshot.

**Concrete improvements:**
- Continue god-object decomposition for the 14+ remaining large files.
- Update REMEDIATION_PLAN.md to reflect accurate current state.
- Add CI gate blocking new files >500 lines.

---

### 6. Cost (Resource Efficiency) — 7/10 (↑ from 6)

**What's good:** Repo size reduced from 32MB to 30MB:
- Nested duplicate removed (1.6MB)
- Screenshots deleted (312KB)
- Code files reduced by 144

The `detailed_outlines.py` refactor moved data to JSON (80KB) while reducing Python code by 2,063 lines.

**What's still wrong:** 253K lines of Python is still large. Route count (994) suggests significant consolidation opportunity.

**Concrete improvements:**
- Continue route consolidation.
- Audit for more data-vs-code separation opportunities.

---

### 7. Safety — 7/10 (↑ from 6)

**What's good:** Safety architecture is now implemented, not just designed:

**Fail-fast startup validation:**
- 4 safety-critical modules verified at boot
- Server refuses to start if any fail
- Configurable via `RMOS_STRICT_STARTUP` env var

**@safety_critical decorator:**
- Never swallows exceptions
- Logs CRITICAL with full traceback
- Always re-raises (fail-closed)
- Sync and async versions

**Specific exception hierarchy:**
- 11 domain-specific exception types
- Enables targeted error handling without broad catches

**What's still wrong:** Only 6 functions decorated with @safety_critical. The safety-critical surface is larger — all G-code generation, feeds/speeds calculation, and risk bucketing functions should be covered.

The 691 remaining broad exception handlers include sites in safety-critical modules.

**Concrete improvements:**
- Audit all G-code generation paths for @safety_critical coverage.
- Add @safety_critical to feeds/speeds calculations.
- Continue reducing broad exception handlers in rmos/, cam/, calculators/.

---

### 8. Scalability — 6/10 (↑ from 5)

**What's good:** The router registry enables better modularity:
- Categories allow selective loading
- `required` flag distinguishes core from optional
- Health reporting shows what's actually available

The `/api/features` endpoint scales for discovery.

**What's still wrong:** 994 routes doesn't scale for external consumers. The architecture still encourages monolithic deployment.

**Concrete improvements:**
- Implement route classification (Core/Power/Internal/Cull) from remediation plan.
- Consider splitting into smaller, deployable packages.

---

### 9. Aesthetics (Design Quality) — 5/10 (↑ from 4)

**What's good:** Root directory improved from 38 to 33 items. Screenshots removed.

The router registry manifest is well-organized by category with clear comments.

**What's still wrong:** Still 33 root items (target was <20). Development artifacts remain:
- `AGENT_SESSION_BOOKMARK.md`
- `REVIEW_REMEDIATION_PLAN.md`
- `FENCE_REGISTRY.json`
- Two `.code-workspace` files (redundant?)

Directory naming remains inconsistent:
- `cam/` vs `cam_core/`
- `rmos/runs/` vs `rmos/runs_v2/`

**Concrete improvements:**
- Move development artifacts to `docs/internal/`.
- Consolidate duplicate directory structures.
- Target <25 root items.

---

## Summary Scorecard

| Category | Snap 15 | Snap 16 | Weight | Weighted |
|---|---|---|---|---|
| Purpose Clarity | 7 | 8/10 | 1.0 | 8.0 |
| User Fit | 6 | 7/10 | 1.5 | 10.5 |
| Usability | 5 | 7/10 | 1.5 | 10.5 |
| Reliability | 5 | 6/10 | 1.5 | 9.0 |
| Maintainability | 4 | 6/10 | 1.5 | 9.0 |
| Cost / Resource Efficiency | 6 | 7/10 | 1.0 | 7.0 |
| Safety | 6 | 7/10 | 2.0 | 14.0 |
| Scalability | 5 | 6/10 | 0.5 | 3.0 |
| Aesthetics | 4 | 5/10 | 0.5 | 2.5 |
| **Weighted Average** | **5.41** | | | **6.68/10** |

---

## Progress Assessment

**Score improved from 5.41 to 6.68 (+1.27 points, +23%).**

This is meaningful progress. Key wins:
1. **main.py refactored** — 77% reduction, declarative router loading
2. **Startup validation** — fail-fast for safety-critical modules
3. **@safety_critical deployed** — 6 call sites, specific exception types
4. **Nested duplicate removed** — 1.6MB cleanup
5. **detailed_outlines.py refactored** — 99% reduction via JSON extraction
6. **/api/features implemented** — capability discovery endpoint

The remediation is working. The project is on track from D+ (5.41) to C+ (6.68).

---

## Ecosystem Comparison (Updated)

| Project | Score | Key Insight |
|---------|-------|-------------|
| tap_tone_pi | 7.68 | Focused scope, good tests |
| sg-spec | 7.59 | Strong governance, scope creep starting |
| string_master | 7.45 | Excellent theory, root dir chaos |
| **luthiers-toolbox (16)** | **6.68** | Improving, safety deployed |
| luthiers-toolbox (15) | 5.41 | Pre-remediation baseline |

The gap to the other projects has closed from 2.0+ points to ~1.0 point.

---

## Top 5 Actions (Ranked by Impact)

1. **Complete god-object decomposition.** 14+ files still exceed 500 lines. Prioritize the largest routers (adaptive_router, blueprint_router, geometry_router).

2. **Expand @safety_critical coverage.** Currently 6 call sites. All G-code generation and feeds/speeds functions need coverage.

3. **Continue exception hardening.** 691 → target <200. Focus on rmos/, cam/, calculators/ modules.

4. **Reduce route count.** 994 → target 300. Implement the Core/Power/Internal/Cull classification.

5. **Update REMEDIATION_PLAN.md.** Current metrics don't match claims. Accurate status tracking enables better prioritization.

---

## Assessment

**Score: 6.68/10** — a C+ grade, improved from 5.41 (D+).

The remediation is working. The project has made substantial architectural improvements:
- main.py is now maintainable (207 lines)
- Safety infrastructure is deployed, not just designed
- Feature discovery is implemented
- Data files are properly separated from code

The remaining work is execution: continue the patterns that are working (exception hardening, god-object decomposition, route consolidation) until the metrics match the targets.

**Path to 7.0+:** Complete the 14 large file decompositions + expand @safety_critical to all G-code paths + reduce routes to <500. This is achievable in the next 1-2 snapshots.
