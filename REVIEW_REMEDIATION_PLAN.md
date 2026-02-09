# Review Remediation Plan

**Date:** 2026-02-09
**Based on:** `luthiers-toolbox-design-review.md` (5.41/10)
**Goal:** Raise score to 7.0+/10

---

## Current State (Verified)

| Metric | Review Claim | Actual | Target |
|--------|--------------|--------|--------|
| Root directory items | 38 | **78** | <20 |
| Files >500 lines | 19+ | **16** | 0 |
| Broad `except Exception` | 725 | ~225 safety-critical | 0 in safety paths |
| API routes | 992 | TBD | <300 core |
| .txt files at root | - | **22** | 0 |
| .jpg files at root | - | **14MB** | 0 |

### Safety-Critical Exception Sites

| Module | Count |
|--------|-------|
| rmos/ | 177 |
| saw_lab/ | 30 |
| cam/ | 15 |
| calculators/ | 3 |
| **Total** | **225** |

### Files Over 500 Lines

| File | Lines | Priority |
|------|-------|----------|
| adaptive_router.py | 1,481 | HIGH |
| blueprint_router.py | 1,318 | HIGH |
| geometry_router.py | 1,158 | HIGH |
| blueprint_cam_bridge.py | 971 | HIGH |
| main.py | 905 | CRITICAL |
| dxf_preflight_router.py | 792 | MEDIUM |
| probe_router.py | 782 | MEDIUM |
| check_boundary_imports.py | 745 | LOW (CI tool) |
| fret_router.py | 696 | MEDIUM |
| cam_metrics_router.py | 653 | MEDIUM |
| lespaul_gcode_gen.py | 593 | MEDIUM |
| calculators_consolidated_router.py | 577 | MEDIUM |
| test_e2e_workflow_integration.py | 567 | LOW (test) |
| ai_context_adapter/routes.py | 538 | MEDIUM |
| dxf_plan_router.py | 528 | MEDIUM |
| tooling_router.py | 513 | MEDIUM |

---

## Phase 7: Root Directory Cleanup

**Impact:** Aesthetics +2, Maintainability +1
**Effort:** 1 hour
**Risk:** None

### 7.1 — Delete development artifacts (22 .txt files)

```bash
git rm "4 CNC Graphics Design Prompts.txt"
git rm "AI_Realignment.txt"
git rm "Answer fret router Questions.txt"
git rm "Art Studio_ RMOS Binding Bundle_Spine-Locked to HEAD.txt"
git rm "Bundle 31.0.27 — Art Studio Run Orchestration.txt"
git rm "Bundle H3.4 — runs_v2 pagination.txt"
git rm "Clarification Questions.txt"
git rm "evaluate_feasibility.txt"
git rm "SG-SBX-0.1 — Smart Guitar.txt"
# ... and remaining .txt files
```

### 7.2 — Delete or move large images (14MB)

```bash
git rm "Benedetto Back.jpg"    # 4.6MB
git rm "Benedetto Front.jpg"   # 9.3MB
git rm "Screenshot 2026-01-15 033523.png"
git rm "Screenshot 2026-01-15 033954.png"
```

If needed for documentation, move to `docs/images/` first.

### 7.3 — Delete stray files

```bash
git rm 0                       # Empty file
git rm architecture_scan_phase1.patch
git rm boundary_spec.json      # If not referenced
```

### 7.4 — Update .gitignore

Add rules to prevent future accumulation:
```gitignore
# Development artifacts
*.txt
!requirements*.txt
*.jpg
*.png
!docs/images/**
```

**Acceptance:** Root directory has <25 items.

---

## Phase 8: Safety-Critical Exception Hardening

**Impact:** Safety +2, Reliability +2
**Effort:** 4-8 hours
**Risk:** Medium (behavior changes)

### 8.1 — Audit rmos/ exceptions (177 sites)

Priority order:
1. `feasibility/` — decision engine
2. `runs_v2/` — run lifecycle
3. `api/` — external surface
4. `validation/` — safety checks

For each site:
- Identify the specific exception types that can occur
- Replace `except Exception` with specific types
- Add logging for unexpected exceptions
- Ensure fail-closed behavior for safety paths

### 8.2 — Audit saw_lab/ exceptions (30 sites)

Focus on:
- G-code generation paths
- Blade validation
- Cut planning

### 8.3 — Audit cam/ exceptions (15 sites)

Focus on:
- Toolpath generation
- Feed/speed calculations
- Post-processor output

### 8.4 — Implement @safety_critical decorator

```python
def safety_critical(func):
    """Decorator that ensures fail-closed behavior.

    - Logs all exceptions with full context
    - Re-raises after logging (no silent swallowing)
    - Records to audit trail
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "Safety-critical function failed: %s",
                func.__name__,
                exc_info=True,
                extra={"args": args, "kwargs": kwargs}
            )
            raise
    return wrapper
```

Apply to all G-code generation, feasibility scoring, and risk gating functions.

**Acceptance:** 0 broad exceptions in safety-critical paths.

---

## Phase 9: God-Object Decomposition (Round 2)

**Impact:** Maintainability +2
**Effort:** 8-16 hours
**Risk:** Medium (refactoring)

### 9.1 — main.py (905 lines)

Current state: 25+ conditional router imports with try/except.

Target architecture:
```python
# main.py (target: <200 lines)
from .router_registry import load_routers, get_health_status

app = FastAPI()
routers = load_routers()
for router in routers:
    app.include_router(router)

# router_registry.py (new)
ROUTER_MANIFEST = [
    {"module": ".rmos.runs_v2.api_runs", "prefix": "/api/rmos/runs_v2", "required": True},
    {"module": ".saw_lab.batch_router", "prefix": "/api/saw/batch", "required": False},
    # ...
]

def load_routers() -> List[APIRouter]:
    """Load routers from manifest, tracking failures."""
    ...

def get_health_status() -> Dict[str, bool]:
    """Return which routers loaded successfully."""
    ...
```

### 9.2 — adaptive_router.py (1,481 lines)

Split into:
- `adaptive_router.py` — route definitions only (<200 lines)
- `adaptive_service.py` — business logic
- `adaptive_schemas.py` — request/response models
- `adaptive_gcode.py` — G-code generation

### 9.3 — blueprint_router.py (1,318 lines)

Split into:
- `blueprint_router.py` — routes
- `blueprint_service.py` — logic
- `blueprint_parser.py` — DXF/SVG parsing
- `blueprint_schemas.py` — models

### 9.4 — geometry_router.py (1,158 lines)

Split into:
- `geometry_router.py` — routes
- `geometry_service.py` — calculations
- `geometry_transforms.py` — coordinate transforms
- `geometry_schemas.py` — models

### 9.5 — Remaining files

Apply same pattern to:
- blueprint_cam_bridge.py (971)
- dxf_preflight_router.py (792)
- probe_router.py (782)
- fret_router.py (696)
- cam_metrics_router.py (653)

**Acceptance:** 0 files >500 lines (excluding tests and CI tools).

---

## Phase 10: Startup Health Validation

**Impact:** Reliability +1, Safety +1
**Effort:** 2 hours
**Risk:** Low

### 10.1 — Implement startup checks

```python
# health/startup.py
REQUIRED_MODULES = [
    "app.rmos.feasibility.engine",
    "app.rmos.runs_v2.store",
    "app.cam.gcode_generator",
    "app.saw_lab.batch_service",
]

def validate_startup() -> None:
    """Fail fast if safety-critical modules don't load."""
    failures = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except ImportError as e:
            failures.append(f"{module}: {e}")

    if failures:
        raise RuntimeError(
            f"Safety-critical modules failed to load:\n" +
            "\n".join(failures)
        )
```

### 10.2 — Add to FastAPI lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup()  # Fail here, not silently later
    yield
```

**Acceptance:** Server refuses to start if safety modules are missing.

---

## Phase 11: API Surface Documentation

**Impact:** User Fit +1, Purpose Clarity +1
**Effort:** 4 hours
**Risk:** None

### 11.1 — Implement /api/features endpoint

```python
@router.get("/api/features")
def get_features():
    """Return which features are currently available."""
    return {
        "rmos": {"enabled": True, "version": "2.0"},
        "saw_lab": {"enabled": True, "version": "1.0"},
        "art_studio": {"enabled": True, "version": "1.0"},
        "quick_cut": {"enabled": True, "version": "1.0"},
        # ...
    }
```

### 11.2 — Update README

Add sections:
- "Current State" — what works, what's in progress
- "What Works Today" — stable feature list
- "Quick Start by Use Case" — DXF→G-code, fret calculation, etc.

### 11.3 — Reconcile metrics

Update REMEDIATION_PLAN.md with accurate counts:
- Actual route count (not 262)
- Actual files >500 lines (not 0)

**Acceptance:** README reflects reality; /api/features works.

---

## Execution Order

| Phase | Priority | Effort | Impact |
|-------|----------|--------|--------|
| **7** Root Cleanup | P0 | 1h | Aesthetics, Maintainability |
| **10** Startup Validation | P1 | 2h | Safety, Reliability |
| **8** Exception Hardening | P1 | 4-8h | Safety, Reliability |
| **11** API Documentation | P2 | 4h | User Fit, Purpose |
| **9** God-Object Decomposition | P3 | 8-16h | Maintainability |

**Total estimated effort:** 19-31 hours

---

## Success Metrics

| Metric | Current | Target | Phase |
|--------|---------|--------|-------|
| Root items | 78 | <25 | 7 |
| Files >500 lines | 16 | 0 | 9 |
| Safety-critical broad exceptions | 225 | 0 | 8 |
| Startup validation | None | Fail-fast | 10 |
| /api/features endpoint | Missing | Implemented | 11 |
| Design review score | 5.41 | 7.0+ | All |

---

## Notes

1. **tap_tone_pi-main (5)/** — Already deleted (commit 83eb6a0)
2. **Bare except:** — Already at 1 (near complete from previous phases)
3. **Test coverage** — Not addressed in this plan; separate initiative
