# Luthier's ToolBox: Path to 7/10

**Goal**: Raise overall score from 5.9/10 to >7.0/10
**Strategy**: Focus on highest-impact improvements in weakest categories

## Current State vs Target

| Category | Current | Target | Delta | Priority |
|----------|---------|--------|-------|----------|
| Maintainability | 4 | 7 | +3 | P0 |
| Usability | 5 | 7 | +2 | P1 |
| Scalability | 5 | 7 | +2 | P1 |
| User Fit | 6 | 7 | +1 | P2 |
| Reliability | 6 | 7 | +1 | P2 |
| Aesthetics | 6 | 7 | +1 | P3 |
| Purpose Clarity | 7 | 7 | 0 | Done |
| Cost | 7 | 7 | 0 | Done |
| Safety | 7 | 7 | 0 | Done |

**Math**: Current total = 53/90. Target = 63/90 (7.0 avg). Need +10 points.

---

## Phase 1: Maintainability Blitz (4→7)

**Timeline**: 1-2 weeks
**Impact**: +3 points (biggest single improvement)

### 1.1 Dead Code Purge (WP-0)

```bash
# Delete these tracked artifacts
git rm -r --cached \
  client/ \
  streamlit_demo/ \
  services/api/app/.archive_app_app_20251214/ \
  **/__ARCHIVE__/ \
  **/__REFERENCE__/ \
  **/*_backup_*.vue \
  **/*.bak

# Update .gitignore
echo "*_backup_*" >> .gitignore
echo "*.bak" >> .gitignore
echo "__ARCHIVE__/" >> .gitignore
```

**Exit Gate**: `git ls-files | grep -iE 'backup|archive|\.bak|^client/|^streamlit' | wc -l` = 0

### 1.2 File Size Enforcement

Create `ci/file_size_gate.py`:

```python
#!/usr/bin/env python3
"""CI gate: enforce file size limits with ratchet baseline."""

import sys
from pathlib import Path

PYTHON_LIMIT = 500
VUE_LIMIT = 800

# Grandfathered files (ratchet down over time)
BASELINE = {
    "services/api/app/saw_lab/batch_router.py": 2724,
    "services/api/app/rmos/runs_v2/api_runs.py": 1845,
    "services/api/app/rmos/runs_v2/store.py": 1733,
    # ... add all current violations
}

def check_file(path: Path) -> tuple[bool, int]:
    lines = len(path.read_text(encoding="utf-8").splitlines())
    limit = VUE_LIMIT if path.suffix == ".vue" else PYTHON_LIMIT
    baseline = BASELINE.get(str(path.relative_to(Path.cwd())), limit)
    return lines <= baseline, lines

def main():
    violations = []
    for pattern in ["services/api/app/**/*.py", "packages/client/src/**/*.vue"]:
        for f in Path.cwd().glob(pattern):
            ok, lines = check_file(f)
            if not ok:
                violations.append((f, lines))

    if violations:
        print("File size violations:")
        for f, lines in violations:
            print(f"  {f}: {lines} lines")
        sys.exit(1)
    print("All files within limits")

if __name__ == "__main__":
    main()
```

### 1.3 Split Top 5 God Files

| File | Lines | Action |
|------|-------|--------|
| `saw_lab/batch_router.py` | 2,724 | Split into `batch_crud.py`, `batch_query.py`, `batch_actions.py` |
| `rmos/runs_v2/api_runs.py` | 1,845 | Extract `runs_query.py`, `runs_mutations.py` |
| `rmos/runs_v2/store.py` | 1,733 | Extract `store_read.py`, `store_write.py`, `store_index.py` |
| `ManufacturingCandidateList.vue` | 2,987 | Split into `CandidateTable.vue`, `CandidateFilters.vue`, `CandidateActions.vue` |
| `AdaptivePocketLab.vue` | 2,418 | Extract `PocketSettings.vue`, `PocketPreview.vue`, `PocketExport.vue` |

**Exit Gate**: No file >1,500 lines (50% reduction from worst)

### 1.4 Router Consolidation

```bash
# Current: 199 router files, 1,060 route decorators
# Target: <100 router files, <500 route decorators

# Step 1: Identify duplicate routes
grep -r "@router\." services/api/app --include="*.py" | \
  sed 's/.*@router\.\(get\|post\|put\|delete\|patch\)("\([^"]*\)".*/\1 \2/' | \
  sort | uniq -c | sort -rn | head -20

# Step 2: Merge routers by domain
# rmos/ -> single rmos_router.py with sub-routers
# cam/ -> single cam_router.py with sub-routers
```

**Exit Gate**: <100 router files, <600 route decorators

---

## Phase 2: Usability + User Fit (5→7, 6→7)

**Timeline**: 1 week
**Impact**: +3 points

### 2.1 Curated API v1

Create `services/api/app/api_v1/__init__.py`:

```python
"""Curated API v1 - 40 essential endpoints for the golden path."""

from fastapi import APIRouter

v1 = APIRouter(prefix="/api/v1", tags=["v1"])

# DXF -> G-code workflow (5 endpoints)
# POST /v1/dxf/upload
# POST /v1/dxf/validate
# POST /v1/cam/plan
# POST /v1/cam/gcode
# GET  /v1/cam/posts

# Fret calculations (3 endpoints)
# POST /v1/frets/positions
# POST /v1/frets/slots
# GET  /v1/frets/temperaments

# RMOS safety (5 endpoints)
# POST /v1/rmos/check
# GET  /v1/rmos/rules
# POST /v1/rmos/runs
# GET  /v1/rmos/runs/{id}
# POST /v1/rmos/runs/{id}/approve

# ... (total 40 endpoints)
```

### 2.2 Guided Workflow Component

Create `packages/client/src/components/guided/GuidedWorkflow.vue`:

```vue
<template>
  <div class="guided-workflow">
    <StepIndicator :steps="steps" :current="currentStep" />
    <component :is="currentComponent" @next="next" @back="back" />
    <NavigationButtons :can-back="currentStep > 0" :can-next="canProceed" />
  </div>
</template>
```

Implement for:
- DXF to G-code (5 steps)
- Fret slot cutting (4 steps)
- Rosette design (6 steps)

### 2.3 Error Recovery UI

Replace silent failures with actionable modals:

```typescript
// services/api/app/core/errors.py
class ToolBoxError(Exception):
    """Base error with user-facing message and recovery hint."""
    def __init__(self, message: str, hint: str, code: str):
        self.message = message
        self.hint = hint
        self.code = code

// packages/client/src/components/ErrorRecovery.vue
// Shows: What happened, Why, What to do next
```

**Exit Gate**: Zero silent failures in top 10 workflows

---

## Phase 3: Reliability + Scalability (6→7, 5→7)

**Timeline**: 1-2 weeks
**Impact**: +3 points

### 3.1 Exception Hardening (WP-1 completion)

```bash
# Current: 460 except Exception blocks
# Target: <100 (safety paths = 0)

# Priority files (safety-critical):
grep -l "except Exception" services/api/app/rmos/**/*.py
grep -l "except Exception" services/api/app/cam/**/*.py
grep -l "except Exception" services/api/app/calculators/**/*.py
```

Replace pattern:
```python
# Before
try:
    result = compute_something()
except Exception:
    return None

# After
try:
    result = compute_something()
except (ValueError, TypeError) as e:
    logger.warning(f"Computation failed: {e}")
    raise ToolBoxError("Calculation failed", "Check input values", "CALC_001")
```

**Exit Gate**: 0 `except Exception` in rmos/, cam/, calculators/

### 3.2 Coverage Push

```bash
# Target: 80% on safety-critical modules
pytest tests/ --cov=app/rmos --cov=app/cam --cov=app/calculators \
  --cov-fail-under=80
```

Add tests for:
- All 22 RMOS feasibility rules
- All G-code post processors
- All calculator functions

### 3.3 Async Job Queue

```python
# services/api/app/jobs/queue.py
from rq import Queue
from redis import Redis

redis_conn = Redis()
job_queue = Queue(connection=redis_conn)

def enqueue_gcode_generation(params: dict) -> str:
    """Queue G-code generation, return job ID."""
    job = job_queue.enqueue(generate_gcode, params)
    return job.id

# Endpoint change:
# POST /v1/cam/gcode -> returns {job_id: "xxx"}
# GET /v1/jobs/{id} -> returns {status: "complete", result: {...}}
```

**Exit Gate**: G-code generation is async with progress polling

---

## Phase 4: Aesthetics Polish (6→7)

**Timeline**: 3-5 days
**Impact**: +1 point

### 4.1 Component Library Standardization

```bash
npm install @primevue/core @primevue/themes
```

Migrate top 20 components to PrimeVue:
- Buttons, Inputs, Tables, Modals, Toasts

### 4.2 Design Tokens

```css
/* packages/client/src/styles/tokens.css */
:root {
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-rmos-green: #16a34a;
  --color-rmos-yellow: #ca8a04;
  --color-rmos-red: #dc2626;
  --spacing-unit: 4px;
  --radius-sm: 4px;
  --radius-md: 8px;
}
```

### 4.3 Dark Mode Completion

Audit and fix all components for dark mode support.

**Exit Gate**: Lighthouse accessibility score >90

---

## Execution Order

```
Week 1:
  [x] Phase 1.1: Dead code purge (1 day)
  [x] Phase 1.2: File size gate CI (1 day)
  [ ] Phase 1.3: Split top 3 god files (3 days)

Week 2:
  [ ] Phase 1.4: Router consolidation (2 days)
  [ ] Phase 2.1: API v1 curation (2 days)
  [ ] Phase 3.1: Exception hardening (1 day)

Week 3:
  [ ] Phase 2.2: Guided workflows (3 days)
  [ ] Phase 2.3: Error recovery UI (2 days)

Week 4:
  [ ] Phase 3.2: Coverage push (3 days)
  [ ] Phase 3.3: Async job queue (2 days)

Week 5:
  [ ] Phase 4.1-4.3: Aesthetics polish (5 days)
```

---

## Success Criteria

| Metric | Before | After |
|--------|--------|-------|
| God files (>500 lines) | 25+ | <10 |
| Router files | 199 | <100 |
| Route decorators | 1,060 | <500 |
| `except Exception` | 460 | <100 |
| Test coverage (safety) | ~19% | >80% |
| API v1 endpoints | 0 | 40 |
| Guided workflows | 0 | 3 |

**Final Score Projection**: 7.2/10

---

## Risks

1. **God file splits may break imports** - Mitigate with re-exports
2. **Router consolidation may break clients** - Mitigate with deprecation warnings
3. **Coverage push finds hidden bugs** - This is a feature, not a bug

---

## Not In Scope (Deferred)

- Database migration (file-based is fine for v1)
- Multi-tenancy (single-shop focus)
- Mobile UI (desktop-first)
- New features (subtraction > addition)
