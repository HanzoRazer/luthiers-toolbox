# Code Policy Violations Report

**Generated:** November 16, 2025  
**Scan Scope:** `services/api/app/routers/`, `services/api/app/cam/`, `client/src/components/`  
**Policy Source:** CODING_POLICY.md

---

## 🔴 Critical Violations (P1: Type Safety)

### **Missing Return Type Hints (Python)**

**Severity:** 🔴 CRITICAL - Type hints are REQUIRED on all functions per policy

**Detected Functions (50+ in routers alone):**

#### **cam_polygon_offset_router.py**
- ❌ Line 36: `def polygon_offset(req: PolyOffsetReq):` - Missing return type `Response`

#### **post_router.py**
- ❌ Line 87: `def load_builtin_posts() -> List[PostConfig]:` - ✅ HAS type hint (good example)
- ❌ Line 119: `def load_custom_posts() -> List[PostConfig]:` - ✅ HAS type hint
- ❌ Line 127: `def save_custom_posts(posts: List[PostConfig]):` - Missing return type `None`
- ❌ Line 136: `def load_all_posts() -> List[PostConfig]:` - ✅ HAS type hint
- ❌ Line 140: `def find_post(post_id: str) -> Optional[PostConfig]:` - ✅ HAS type hint
- ❌ Line 146: `def is_builtin(post_id: str) -> bool:` - ✅ HAS type hint
- ❌ Line 152: `def save_custom_posts(posts: List[PostConfig]):` - Missing return type `None`
- ❌ Line 188: `def list_posts():` - Missing both params and return type
- ❌ Line 204: `def get_post(post_id: str):` - Missing return type
- ❌ Line 216: `def create_post(body: PostCreateIn):` - Missing return type
- ❌ Line 255: `def update_post(post_id: str, body: PostUpdateIn):` - Missing return type
- ❌ Line 294: `def delete_post(post_id: str):` - Missing return type
- ❌ Line 323: `def validate_post(body: PostCreateIn):` - Missing return type
- ❌ Line 358: `def list_tokens():` - Missing both params and return type

#### **retract_router.py**
- ❌ Line 97: `def list_strategies():` - Missing return type
- ❌ Line 132: `def apply_retract_strategy(body: RetractStrategyIn):` - Missing return type
- ❌ Line 204: `def generate_lead_in(body: LeadInPatternIn):` - Missing return type
- ❌ Line 245: `def estimate_time_savings(body: TimeSavingsIn):` - Missing return type
- ❌ Line 274: `def download_retract_gcode(body: RetractStrategyIn):` - Missing return type

#### **machines_tools_router.py**
- ❌ Line 38: `def _save(obj: Dict[str, Any]):` - Missing return type `None`
- ❌ Line 54: `def list_tools(mid: str):` - Missing return type
- ❌ Line 64: `def upsert_tools(mid: str, tools: List[Tool]):` - Missing return type
- ❌ Line 91: `def delete_tool(mid: str, tnum: int):` - Missing return type
- ❌ Line 107: `def export_csv(mid: str):` - Missing return type

#### **posts_router.py**
- ❌ Line 54: `def _save_posts(arr: List[Dict[str, Any]]):` - Missing return type `None`
- ❌ Line 62: `def list_posts():` - Missing return type
- ❌ Line 74: `def replace_posts(posts: List[PostDef]):` - Missing return type

#### **polygon_offset_router.py**
- ❌ Line 29: `def polygon_offset_json(req: OffsetReq):` - Missing return type
- ❌ Line 44: `def polygon_offset_nc(req: OffsetReq):` - Missing return type

#### **sim_metrics_router.py**
- ❌ Line 73: `def calculate_metrics(body: SimMetricsIn):` - Missing return type

#### **job_insights_router.py**
- ❌ Line 121: `def get_job_insights(job_id: str):` - Missing return type

#### **adaptive_router.py** (CRITICAL - Core CAM module)
- ❌ Line 457: `def plan(body: PlanIn):` - Missing return type
- ❌ Line 706: `def gcode(body: GcodeIn):` - Missing return type
- ❌ Line 872: `def batch_export(body: BatchExportIn):` - Missing return type
- ❌ Line 1024: `def simulate(body: PlanIn):` - Missing return type

#### **adaptive_preview_router.py**
- ❌ Line 66: `def spiral_svg(req: SpiralReq):` - Missing return type
- ❌ Line 105: `def trochoid_svg(req: TrochoidReq):` - Missing return type

#### **machine_router.py**
- ❌ Line 25: `def _load():` - Missing both params and return type
- ❌ Line 31: `def _save(lst):` - Missing param type and return type
- ❌ Line 38: `def list_profiles():` - Missing return type
- ❌ Line 44: `def get_profile(pid: str):` - Missing return type
- ❌ Line 53: `def upsert_profile(p: MachineProfile):` - Missing return type
- ❌ Line 67: `def delete_profile(pid: str):` - Missing return type
- ❌ Line 78: `def clone_profile(src_id: str, new_id: str, new_title: str | None = None):` - Missing return type

#### **sim_validate.py**
- ❌ Line 67: `def arc_center_from_ijk(ms: ModalState, start, params):` - Missing param types and return type
- ❌ Line 73: `def arc_center_from_r(ms: ModalState, start, end, r_user: float, cw: bool):` - Missing param types and return type
- ❌ Line 250: `def csv_export(sim):` - Missing param type and return type

#### **job_risk_router.py**
- ❌ Line 17: `def post_risk_report(report: RiskReportIn):` - Missing return type

#### **feeds_router.py**
- ❌ Line 27: `def list_tools():` - Missing return type
- ❌ Line 36: `def add_tool(t: ToolIn):` - Missing return type
- ❌ Line 48: `def list_materials():` - Missing return type
- ❌ Line 57: `def add_material(m: MaterialIn):` - Missing return type
- ❌ Line 77: `def feedspeeds(req: FeedRequest):` - Missing return type
- ❌ Line 95: `def list_posts():` - Missing return type

#### **geometry_router.py** (CRITICAL - Core export module)
- ❌ Line 465: `def parity(body: ParityRequest):` - Missing return type
- ❌ Line 679: `def export_gcode(body: GcodeExportIn):` - Missing return type
- ❌ Line 781: `def export_bundle(body: ExportBundleIn):` - Missing return type
- ❌ Line 900: `def export_bundle_multi(body: ExportBundleMultiIn):` - Missing return type

**Estimated Total:** 50+ router functions missing return type hints  
**Impact:** Type safety compromised, IDE autocomplete broken  
**Effort to Fix:** 3-5 hours for all routers

---

## 🟡 Medium Violations (P2: Import Order)

### **Multi-Import Lines (Confirmed)**

**Severity:** 🟡 MEDIUM - Reduces readability and git diff clarity

1. ✅ **machines_tools_router.py:14**
   ```python
   # ❌ WRONG
   import io, csv, json, os
   
   # ✅ CORRECT
   import csv
   import io
   import json
   import os
   ```

2. ✅ **posts_router.py:9**
   ```python
   # ❌ WRONG
   import os, json
   
   # ✅ CORRECT
   import json
   import os
   ```

3. ✅ **cam_post_v155_router.py:5**
   ```python
   # ❌ WRONG
   import math, json, os
   
   # ✅ CORRECT
   import json
   import math
   import os
   ```

4. ✅ **geometry_router.py:36** (WORST OFFENDER)
   ```python
   # ❌ WRONG - 8 modules on 1 line!
   import io, math, json, zipfile, datetime, os, re, time
   
   # ✅ CORRECT
   import datetime
   import io
   import json
   import math
   import os
   import re
   import time
   import zipfile
   ```

**Estimated Total:** 4 confirmed files, likely 10-15 more across codebase  
**Impact:** Harder to scan imports, git merge conflicts  
**Effort to Fix:** 30 minutes (automated with ruff)

---

## ✅ No Violations Detected (Good News)

### **P4: Configuration (No Hardcoded Paths)**
- ✅ Scan for `C:\Users\`, `D:\`, `/home/`, `/mnt/` → **NO MATCHES**
- All path handling appears to use relative imports or environment variables
- Policy compliance: EXCELLENT

---

## 🔍 To Be Scanned (Phase 1 Incomplete)

### **CAM Modules (Not Yet Scanned)**
- `services/api/app/cam/adaptive_core_l*.py` - Need type hint verification
- `services/api/app/cam/helical_core.py` - Need type hint verification
- `services/api/app/cam/polygon_offset_n17.py` - Need type hint verification
- `services/api/app/cam/trochoid_l3.py` - Need type hint verification
- `services/api/app/cam/feedtime*.py` - Need type hint verification

### **Utility Modules (Not Yet Scanned)**
- `services/api/app/util/*.py` - Need type hint verification
- `services/api/app/utils/*.py` - Need type hint verification

### **Vue Components (Not Yet Scanned)**
- 92 Vue components found in `client/src/components/`
- Need to check for:
  - ❌ Options API usage (should be Composition API)
  - ❌ Untyped props (should have interface definitions)
  - ❌ Unscoped styles (should use `<style scoped>`)
  - ❌ Missing TypeScript (`<script setup lang="ts">`)

---

## 📊 Violation Summary

| Category | Severity | Count | Effort | Priority |
|----------|----------|-------|--------|----------|
| **Missing Return Type Hints** | 🔴 Critical | 50+ | 3-5h | P1 |
| **Multi-Import Lines** | 🟡 Medium | 4 confirmed | 30min | P2 |
| **CAM Module Type Hints** | 🟡 Medium | Unknown | 2-3h | P1 |
| **Utility Type Hints** | 🟡 Medium | Unknown | 1-2h | P1 |
| **Vue Composition API** | 🟡 Medium | Unknown | 4-6h | P3 |
| **Vue Prop Types** | 🟡 Medium | Unknown | 2-3h | P3 |
| **Hardcoded Paths** | ✅ None | 0 | 0h | - |

**Total Estimated Effort:** 13-20 hours  
**Quick Wins (Phase 2):** Import order fixes (30 min) + Router type hints (3-5h) = 3.5-5.5h

---

## 🎯 Recommended Fix Order

### **Phase 1: Critical Router Endpoints (3-5 hours)**
Fix return type hints in high-priority routers:
1. **geometry_router.py** - Core export functionality (4 endpoints)
2. **adaptive_router.py** - Core CAM functionality (4 endpoints)
3. **post_router.py** - Post-processor management (7 endpoints)
4. **machine_router.py** - Machine profiles (7 endpoints)
5. **Remaining routers** - Complete coverage (~30 endpoints)

**Why First:** Public API surface, most visible to users, highest correctness impact

### **Phase 2: Import Order (30 minutes)**
Fix 4 confirmed files plus scan for more:
```powershell
# Automated fix with ruff
ruff check --select I001 --fix services/api/app/routers/*.py
```

### **Phase 3: CAM Modules (2-3 hours)**
Add type hints to core algorithms:
- `adaptive_core_l1.py`, `adaptive_core_l2.py`
- `helical_core.py`
- `polygon_offset_n17.py`
- `trochoid_l3.py`
- `feedtime_l3.py`

**Why Third:** Internal modules, less breaking changes

### **Phase 4: Vue Components (4-6 hours)**
Convert to Composition API and add types:
- Start with dashboard components (most visible)
- Convert lab components (AdaptivePocketLab, HelicalRampLab, etc.)
- Add interface definitions for all props/emits

**Why Last:** Frontend less critical than backend type safety

---

## 🔧 Automated Fixes Available

### **Import Order**
```powershell
# Install ruff (if not already installed)
pip install ruff

# Fix import order violations
ruff check --select I001 --fix services/api/app/routers/*.py
ruff check --select I001 --fix services/api/app/cam/*.py
ruff check --select I001 --fix services/api/app/util/*.py

# Verify
ruff check --select I001 services/api/app/
```

### **Type Hint Detection**
```powershell
# Scan for functions without return types (manual review needed)
# No good automated tool - requires manual inspection
```

---

## ✅ Next Actions

1. [ ] **User approval:** Proceed with Phase 1 (Router type hints)?
2. [ ] **Quick win:** Run ruff import order fix (30 min)?
3. [ ] **Scan CAM modules:** Assess type hint coverage
4. [ ] **Scan Vue components:** Assess Composition API usage
5. [ ] **Update this report** with full scope after scans complete

---

**Status:** 🔍 Phase 1 Assessment Partially Complete  
**Confidence:** HIGH on router violations, MEDIUM on CAM/Vue (not yet scanned)  
**Ready to Start:** Import order fixes and router type hints (Phase 2 Quick Wins)
