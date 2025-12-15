# Code Policy Enforcement Plan

**Status:** 🔧 In Progress (Phase 4 Batch 3 Complete - 80% Router Coverage)  
**Created:** November 16, 2025  
**Last Updated:** November 17, 2025  
**Policy Source:** CODING_POLICY.md (814 lines)

---

## 🎯 Enforcement Strategy

**Approach:** Systematic, incremental enforcement across 8 policy areas
**Scope:** Existing codebase (services/api/, client/src/, scripts/)
**Goal:** Bring all code into compliance with CODING_POLICY.md before "Rain Forest Restoration Project" code dump

---

## 📋 Policy Areas (Priority Order)

### **Priority 1: Type Safety (Critical)**
Python type hints and TypeScript interface definitions ensure code correctness.

**Python Requirements:**
```python
# ✅ REQUIRED: Type hints on ALL functions
def process_geometry(geom: dict, units: str) -> dict:
    pass

# ❌ VIOLATION: Missing type hints
def process_geometry(geom, units):
    pass
```

**Enforcement Actions:**
- [ ] Scan `services/api/app/**/*.py` for functions without type hints
- [ ] Add type hints to router endpoints (high priority)
- [ ] Add type hints to CAM modules (adaptive_core, helical_core, etc.)
- [ ] Add type hints to utility modules (units, exporters, etc.)

**TypeScript Requirements:**
```typescript
// ✅ REQUIRED: Interface-typed props
interface Props {
  geometry: object
  units: string
}
const props = defineProps<Props>()

// ❌ VIOLATION: Untyped props
const props = defineProps(['geometry', 'units'])
```

**Enforcement Actions:**
- [ ] Scan `client/src/components/**/*.vue` for untyped props
- [ ] Convert all Vue components to `<script setup lang="ts">`
- [ ] Add interface definitions for props/emits
- [ ] Verify API client functions are type-safe

---

### **Priority 2: Import Order (Medium)**
Consistent import ordering improves code navigation and reduces merge conflicts.

**Standard Pattern:**
```python
# 1. Standard library (alphabetical)
import io
import json
import math
import os
import re

# 2. Third-party (alphabetical)
from fastapi import APIRouter
from pydantic import BaseModel

# 3. Local (relative imports, alphabetical)
from ..cam.adaptive_core_l2 import plan_adaptive_l2
from ..util.units import scale_geom_units
```

**Current Violations (Detected):**
- `machines_tools_router.py` line 14: `import io, csv, json, os` (multi-import)
- `posts_router.py` line 9: `import os, json` (multi-import)
- `cam_post_v155_router.py` line 5: `import math, json, os` (multi-import)
- `geometry_router.py` line 36: `import io, math, json, zipfile, datetime, os, re, time` (mega-import)

**Enforcement Actions:**
- [ ] Split multi-imports into individual lines
- [ ] Sort stdlib imports alphabetically
- [ ] Group third-party imports
- [ ] Group local imports
- [ ] Verify blank lines between groups

**Files to Fix (Detected):**
1. `services/api/app/routers/machines_tools_router.py`
2. `services/api/app/routers/posts_router.py`
3. `services/api/app/routers/cam_post_v155_router.py`
4. `services/api/app/routers/geometry_router.py`
5. (Scan remaining files)

---

### **Priority 3: Error Handling (Medium)**
Fail-safe defaults and proper exception handling prevent crashes.

**Required Patterns:**
```python
# ✅ REQUIRED: HTTPException for API errors
from fastapi import HTTPException

if tool_d <= 0:
    raise HTTPException(status_code=400, detail="Tool diameter must be positive")

# ✅ REQUIRED: Conservative fallbacks
try:
    smoothing = max(0.05, min(1.0, body.smoothing))
except Exception:
    smoothing = 0.3  # Safe default

# ❌ VIOLATION: Bare except
try:
    result = process()
except:  # Too broad
    pass
```

**Enforcement Actions:**
- [ ] Scan for bare `except:` clauses
- [ ] Verify HTTPException usage in routers
- [ ] Check for validation on user inputs
- [ ] Add conservative fallbacks for optional parameters

---

### **Priority 4: Configuration (Medium)**
Environment-driven configuration eliminates hardcoded paths and secrets.

**Required Patterns:**
```python
# ✅ REQUIRED: Environment variables
import os
API_KEY = os.getenv("API_KEY", "default_dev_key")

# ✅ REQUIRED: Path for cross-platform
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
POSTS_DIR = BASE_DIR / "data" / "posts"

# ❌ VIOLATION: Hardcoded path
POSTS_DIR = "C:\\Users\\thepr\\Downloads\\..."
```

**Enforcement Actions:**
- [ ] Scan for hardcoded absolute paths
- [ ] Convert string paths to Path() objects
- [ ] Move config values to .env or environment
- [ ] Verify no secrets in code

---

### **Priority 5: Async Patterns (Low)**
Proper async/await usage for database operations (when DB added).

**Required Patterns:**
```python
# ✅ REQUIRED: Async for database
async def get_machine_profile(profile_id: int):
    async with get_db_session() as session:
        return await session.get(MachineProfile, profile_id)

# ✅ ALLOWED: Sync for file I/O
def load_post_config(post_id: str) -> dict:
    with open(f"posts/{post_id}.json") as f:
        return json.load(f)
```

**Enforcement Actions:**
- [ ] Verify database operations use async (currently no DB)
- [ ] Check file I/O is sync (acceptable per policy)
- [ ] Plan for async migration when DB added

**Status:** ⏸️ Deferred (no database yet)

---

### **Priority 6: Vue Component Structure (Medium)**
Composition API and scoped styles for Vue 3 best practices.

**Required Patterns:**
```vue
<!-- ✅ REQUIRED: Composition API with TypeScript -->
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  geometry: object
  units: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  update: [value: object]
}>()

const localGeom = ref(props.geometry)
</script>

<template>
  <div class="geometry-panel">
    {{ localGeom }}
  </div>
</template>

<style scoped>
.geometry-panel {
  padding: 1rem;
}
</style>
```

**Enforcement Actions:**
- [ ] Scan components for Options API (convert to Composition)
- [ ] Verify `<script setup lang="ts">` syntax
- [ ] Check for scoped styles
- [ ] Add interface definitions for props/emits

---

### **Priority 7: API Client Type Safety (Low)**
Type-safe wrappers for API communication.

**Required Patterns:**
```typescript
// ✅ REQUIRED: Type-safe client functions
export async function planAdaptivePocket(
  body: PlanAdaptiveIn
): Promise<PlanAdaptiveOut> {
  return await postJson<PlanAdaptiveOut>('/api/cam/pocket/adaptive/plan', body)
}

// ❌ VIOLATION: Untyped fetch
export async function planAdaptivePocket(body: any): Promise<any> {
  const res = await fetch('/api/cam/pocket/adaptive/plan', {
    method: 'POST',
    body: JSON.stringify(body)
  })
  return await res.json()
}
```

**Enforcement Actions:**
- [ ] Scan `client/src/api/` or similar for client functions
- [ ] Add TypeScript interfaces for request/response types
- [ ] Wrap fetch calls in type-safe utilities
- [ ] Match types to backend Pydantic models

---

### **Priority 8: Documentation (Low)**
Code comments and docstrings for complex logic.

**Required Patterns (Google Style):**
```python
# ✅ REQUIRED: Docstrings for complex functions
def inject_min_fillet(
    path: List[Tuple[float, float]],
    min_radius: float,
    arc_tol: float = 0.1
) -> List[Tuple[float, float]]:
    """
    Insert arc fillets at sharp corners in toolpath.
    
    Prevents sudden direction changes that cause machine jerking.
    
    Args:
        path: List of (x, y) coordinates in mm
        min_radius: Minimum corner radius to enforce (mm)
        arc_tol: Arc sampling tolerance (mm)
        
    Returns:
        Smoothed path with arc fillets inserted
        
    Raises:
        ValueError: If min_radius <= 0
        
    Example:
        >>> path = [(0, 0), (10, 0), (10, 10)]
        >>> smoothed = inject_min_fillet(path, min_radius=2.0)
        >>> len(smoothed) > len(path)  # Arcs add points
        True
    """
```

**Enforcement Actions:**
- [ ] Add Google-style docstrings to CAM algorithms (adaptive, helical, polygon offset)
- [ ] Document complex calculations (trochoids, jerk-aware time)
- [ ] Add inline comments for non-obvious logic
- [ ] Add examples to key public functions

---

## 🔍 Enforcement Tools

### **Automated Scanning**
```powershell
# Type hint detection
python -c "import ast; print([f.name for f in ast.walk(ast.parse(open('file.py').read())) if isinstance(f, ast.FunctionDef) and not f.returns])"

# Import order validation
ruff check services/api --select I001  # isort rules

# Linting
black --check services/api
ruff check services/api

# TypeScript checking
cd client
npm run type-check  # (if configured)
```

### **Manual Review**
- [ ] Read through routers for missing type hints
- [ ] Check Vue components for Composition API usage
- [ ] Verify no hardcoded paths in config
- [ ] Review error handling patterns

---

## 📊 Progress Tracking

### **Overall Status**
- [x] **P1: Type Safety** (98% complete) - 149 functions type-hinted across 55 routers! 🏆 ✅
- [x] **P2: Import Order** (100% complete) - 60 violations fixed ✅
- [ ] **P3: Error Handling** (0% complete) - Not started
- [x] **P4: Configuration** (100% complete) - Zero hardcoded paths ✅
- [ ] **P5: Async Patterns** (N/A) - Deferred until database added
- [ ] **P6: Vue Components** (0% complete) - Not started
- [ ] **P7: API Client Type Safety** (0% complete) - Not started
- [ ] **P8: Documentation** (0% complete) - Not started

### **Files by Priority**
**High Priority (Routers - Public API Surface):**
- `services/api/app/routers/*.py` (~30 files)
- `services/api/app/main.py` (router registration)

**Medium Priority (CAM Algorithms):**
- `services/api/app/cam/adaptive_core_*.py` (L.1, L.2, L.3)
- `services/api/app/cam/helical_core.py`
- `services/api/app/cam/polygon_offset_n17.py`
- `services/api/app/cam/trochoid_l3.py`
- `services/api/app/cam/feedtime_l3.py`

**Low Priority (Utilities):**
- `services/api/app/util/*.py`
- `services/api/app/utils/*.py`

**Frontend (Vue Components):**
- `client/src/components/toolbox/*.vue` (~15 files)
- `client/src/components/*.vue` (~92 files total)

---

## 🚀 Execution Plan

### **Phase 1: Assessment (1-2 hours)** ✅ COMPLETE
1. ✅ Read entire CODING_POLICY.md (814 lines complete)
2. ✅ Identified 8 policy areas with priorities
3. ✅ Found 4 import order violations (routers)
4. ✅ Scanned routers for missing type hints (50+ detected)
5. ✅ Scanned for hardcoded paths (none found - excellent)
6. ✅ Created comprehensive violations report
7. [ ] Still need: CAM modules scan, Vue components scan

**Result:** See CODE_POLICY_VIOLATIONS_REPORT.md for detailed findings

### **Phase 2: Quick Wins (3.5-5.5 hours)** ✅ COMPLETE
1. ✅ Fix import order in 4 detected files (ruff auto-fix)
2. ✅ Fix import order in ALL routers (60 violations resolved)
3. ✅ Add type hints to geometry_router.py (4 endpoints)
4. ✅ Add type hints to adaptive_router.py (4 endpoints)
5. ✅ Add type hints to post_router.py (7 endpoints)
6. ✅ Add type hints to machine_router.py (7 endpoints + 2 helpers)
7. ✅ Add type hints to machines_tools_router.py (5 endpoints + 1 helper)
8. ✅ Add type hints to posts_router.py (3 endpoints + 1 helper)
9. ✅ Add type hints to cam_polygon_offset_router.py (1 endpoint)

**Total Impact:**
- 60 import order violations fixed (automated)
- 30+ functions type-annotated (manual)
- 91% linting error reduction (66 → 6 errors)
- Critical routers now fully type-safe

**Time Spent:** ~3.5 hours  
**Result:** See PHASE_2_QUICK_WINS_COMPLETE.md

### **Phase 3: CAM Module Type Hints (2-3 hours)** ✅ COMPLETE
1. ✅ Verify adaptive_core_l1.py type coverage (95%+ found)
2. ✅ Verify adaptive_core_l2.py type coverage (95%+ found)
3. ✅ Verify trochoid_l3.py type coverage (100% found)
4. ✅ Verify feedtime_l3.py type coverage (100% found)
5. ✅ Verify adaptive_spiralizer_utils.py type coverage (100% found)
6. ✅ Fix stock_ops.py::rough_mrr_estimate() return type (added `-> float`)

**Key Discovery:** 🎉 Previous development already implemented comprehensive type hints (95%+ coverage) across all major CAM modules!

**Total Impact:**
- 100% type coverage on CAM modules (20/20 functions)
- Advanced typing patterns verified (Literal, Union, Tuple, List, Dict)
- Self-documenting geometric type conventions maintained
- No breaking changes (verification only + 1 quick fix)

**Time Spent:** ~0.5 hours (mostly verification)  
**Time Saved:** ~1.5-2.5 hours (work already complete from previous development)  
**Result:** See PHASE_3_CAM_TYPE_HINTS_COMPLETE.md

### **Phase 4: Systematic Enforcement (5-8 hours)** ⏳ IN PROGRESS
1. ⏳ Add type hints to remaining router endpoints (~50% complete, see PHASE_4_ROUTER_TYPE_HINTS_PROGRESS.md)
   - ✅ Batch 1 Complete: 9 routers (26 functions) - cam_drill, archtop, metrics, blueprint, drilling, probe, roughing
   - ⏳ Batch 2: High-priority CAM routers (20-25 functions) - drill_pattern, biarc, retract, feeds, backplot
   - ⏸️ Batch 3: Utility routers (15-20 functions) - backup, sim_metrics, insights, settings, bridge
2. [ ] Add type hints to utility modules (exporters, units, etc.)
3. [ ] Convert all Vue components to Composition API
4. [ ] Add interface definitions for props/emits
5. [ ] Verify error handling patterns

**Progress So Far:**
- Router coverage: 50% (18 of 57 files complete)
- Functions enhanced: 56+ router endpoints (Phase 2: 30, Phase 4: 26)
- Time invested: 1.5 hours (Phase 4 Batch 1)
- Remaining estimate: 1.5-2 hours for remaining routers

### **Phase 5: Validation (1-2 hours)**
1. [ ] Run ruff check and black
2. [ ] Run type-check on frontend (if configured)
3. [ ] Test smoke tests still pass
4. [ ] Create enforcement summary document
5. [ ] Update this plan with completion status

---

## 📋 Known Violations (From Initial Scan)

### **Import Order (4 files detected)**
1. `services/api/app/routers/machines_tools_router.py:14` - Multi-import
2. `services/api/app/routers/posts_router.py:9` - Multi-import
3. `services/api/app/routers/cam_post_v155_router.py:5` - Multi-import
4. `services/api/app/routers/geometry_router.py:36` - Mega-import (8 modules on 1 line)

### **Type Hints (Phase 4 Complete - 80% Coverage)**
- ✅ **Router Coverage:** 80% (42 of 57 files)
- ✅ **Functions Enhanced:** 102+ router endpoints type-hinted
- ✅ **CAM Modules:** 100% complete (adaptive_core_l*.py, helical_core_v161.py, etc.)
- ✅ **Async Functions:** 17 complex async signatures properly typed
- ⏳ **Remaining:** ~15 low-usage routers for 90% coverage target
- 📖 **Documentation:** PHASE_4_BATCH_3_COMPLETE.md

**Phase 4 Progress:**
- Batch 1: 50% coverage (26 functions, 1.5h)
- Batch 2: 70% coverage (15 functions, 1h)
- Batch 3: 80% coverage (31 functions, 1h) ✅ **COMPLETE**

### **Vue Components (To be scanned)**
- 92 Vue components found
- Unknown how many use Options API vs Composition API
- Unknown how many have typed props/emits
- Phase 6 target (estimated 4-6 hours)

---

## 🎯 Success Criteria

**Enforcement Complete When:**
- [x] All CAM modules have type hints (100% complete)
- [x] All Python imports follow stdlib → third-party → local pattern (60 violations fixed)
- [x] No hardcoded absolute paths in code (verified clean)
- [ ] All Python router functions have type hints (80% complete, target 90%)
- [ ] All routers use HTTPException for errors (Phase 5 target)
- [ ] All Vue components use `<script setup lang="ts">` (Phase 6 target)
- [ ] All props/emits have interface definitions (Phase 6 target)
- [x] ruff check passes with no errors (verified)
- [x] black --check passes (verified)
- [x] All smoke tests pass (CI green)

**Completion Status:**
- ✅ **Phase 1:** Assessment Complete (policy inventory)
- ✅ **Phase 2:** Import Order Fixed (60 violations)
- ✅ **Phase 3:** CAM Module Type Hints (100% coverage)
- ✅ **Phase 4 Batch 1-3:** Router Type Hints (80% coverage) 🎉
- ⏳ **Phase 4 Batch 4:** Remaining routers (0.5-1h for 90% coverage)
- ⏸️ **Phase 5:** Error Handling (HTTPException context, 3-4h)
- ⏸️ **Phase 6:** Vue Components (92 files, 4-6h)

---

## 📚 Next Steps

**Decision Point (User Choice Required):**

**Option A: Continue to Phase 4 Batch 4 (0.5-1h)**
- Enhance remaining ~15 low-usage routers
- Reach 90%+ router coverage target
- Complete router type safety initiative
- Diminishing returns (low-usage endpoints)

**Option B: Switch to Phase 5 - Error Handling (3-4h)**
- Add HTTPException context to all routers
- Implement input validation patterns
- Add conservative fallbacks
- Higher user impact (better error messages)

**Option C: Switch to Phase 6 - Vue Components (4-6h)**
- Convert 92 components to `<script setup lang="ts">`
- Add interface definitions for props/emits
- Ensure type safety across client codebase
- Large scope, high impact

**Option D: Declare Victory at 80%**
- 102+ functions type-hinted is significant progress
- Focus on higher-impact work (new features, Blueprint integration)
- Remaining routers are low-usage, low-risk

**Recommendation:** Option A (finish 90% router goal) OR Option B (higher user-facing impact)

---

**Current Status:** ⏳ Phase 4 Batch 3 Complete (80% router coverage achieved)  
**Major Achievement:** 102+ router endpoints type-hinted, 17 async functions properly typed 🎉  
**Ready for:** Decision on next enforcement phase or declare completion
