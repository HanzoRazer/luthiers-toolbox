# Dead Code Recovery Assessment

**Generated:** 2026-02-27
**Commits Analyzed:** `b5f48a4c` (21 dormant routers), `520f3ea3` (Phase 4 cleanup)
**Total Lines Deleted:** ~4,000+ across both commits

---

## Executive Summary

During aggressive dead-code cleanup, several functional modules were incorrectly deleted:
- **7 files remain MISSING** from Phase 4 cleanup
- **4 routers** still missing from dormant router cleanup
- **1 CRITICAL BUG**: `app/util/post_injection_helpers.py` has broken import chain

### Priority Recovery Items

| Priority | File | Lines | Impact |
|----------|------|-------|--------|
| **P0-CRITICAL** | `app/post_injection_helpers.py` | 488 | CAM routers using fallback no-ops |
| **P1-HIGH** | `app/cam_core/saw_lab/queue.py` | 265 | Saw Lab batch queue missing |
| **P1-HIGH** | `app/routers/cam_relief_router.py` | ~80 | Full relief CAM router deleted |
| **P2-MEDIUM** | `app/websocket/monitor.py` | 131 | Real-time monitoring unavailable |
| **P2-MEDIUM** | `app/schemas/job_log.py` | 81 | Job log schema types missing |
| **P2-MEDIUM** | `app/services/rmos_stores.py` | 130 | Pattern/Job stores orphaned |
| **P3-LOW** | `app/ai/prompts/templates.py` | 235 | AI prompt templating system |
| **P3-LOW** | `app/art_studio/services/workflow_schemas.py` | 181 | Workflow request/response models |

---

## Detailed Analysis

### 1. CRITICAL: Post Injection Helpers (BROKEN)

**Status:** ❌ **BROKEN IMPORT CHAIN**

**File Deleted:** `app/post_injection_helpers.py` (488 lines)

**Current State:**
- `app/util/post_injection_helpers.py` exists as a wrapper
- It tries to import `build_post_context_all` and `wrap_with_post_all` from the deleted file
- Falls back to NO-OP functions when import fails
- CAM routers (`drill_router.py`, `pattern_router.py`, `biarc_router.py`, `roughing_router.py`) call these functions

**Impact:**
- Post-processor context (tool, feeds, spindle, etc.) NOT being injected into G-code headers
- `quick_context_basic()`, `quick_context_standard()`, `quick_context_rich()` - ALL MISSING
- `build_post_response()`, `build_post_response_custom()` - ALL MISSING

**Recovery:** RESTORE immediately - this is actively breaking CAM output quality

---

### 2. HIGH: Saw Lab Queue System

**Status:** ❌ MISSING

**File Deleted:** `app/cam_core/saw_lab/queue.py` (265 lines)

**Functionality Lost:**
- `SawLabQueue` class - persistent job queue for saw operations
- FIFO queue semantics backed by SQLite joblog store
- Job state management: pending → running → completed/failed
- Methods: `enqueue()`, `dequeue()`, `complete()`, `fail()`, `snapshot()`

**Modern Equivalent:** None found - job queuing is done differently now (batch_router patterns)

**Recovery:** Consider architectural decision - restore or document removal

---

### 3. HIGH: Full CAM Relief Router

**Status:** ❌ MISSING (partial replacement exists)

**File Deleted:** `app/routers/cam_relief_router.py` (~80 lines)

**Functionality Lost:**
- `POST /cam/relief/map_from_heightfield` - heightmap → Z grid conversion
- `POST /cam/relief/roughing` - multi-pass roughing toolpath
- `POST /cam/relief/finishing` - scallop-based finishing toolpath
- `POST /cam/relief/sim_bridge` - mesh simulation bridge

**Current State:**
- `app/art_studio/relief_router.py` exists but is **PREVIEW ONLY** (no CAM output)
- It explicitly states: "DXF export moved to CAM: POST /api/cam/toolpath/relief/export-dxf"
- BUT that CAM endpoint may not exist

**Recovery:** Verify if `/api/cam/toolpath/relief/export-dxf` exists, otherwise restore full router

---

### 4. MEDIUM: WebSocket Real-Time Monitor

**Status:** ❌ MISSING

**File Deleted:** `app/websocket/monitor.py` (131 lines)

**Functionality Lost:**
- `ConnectionManager` class for WebSocket connections
- Real-time event broadcasting: `job:created`, `job:updated`, `job:completed`, `job:failed`
- Pattern/material events: `pattern:created`, `material:updated`
- `metrics:snapshot` periodic stats push
- MM-6 fragility context integration for job events

**Current State:**
- `app/websocket/` directory exists but is empty (only `__pycache__`)

**Recovery:** Restore for real-time monitoring capability

---

### 5. MEDIUM: Job Log Schema Types

**Status:** ❌ MISSING

**File Deleted:** `app/schemas/job_log.py` (81 lines)

**Functionality Lost:**
- `RiskGrade` type literal ("GREEN", "YELLOW", "RED")
- `SliceRiskSummary` model (per-slice risk for saw jobs)
- `BaseJobLog` model (common job log fields)
- `SawBatchJobLog` model (saw cutting job logs)
- `RosettePlanJobLog` model (planning job logs)
- `JobLogEntry` union type

**Modern Equivalent:** Some of this may be duplicated in `app/saw_lab/` schemas

**Recovery:** Check for duplication before restoring

---

### 6. MEDIUM: RMOS Pattern/Job Stores

**Status:** ❌ MISSING

**File Deleted:** `app/services/rmos_stores.py` (130 lines)

**Functionality Lost:**
- `PatternRecord` dataclass
- `JobLogRecord` dataclass
- `PatternStore` class (in-memory pattern store)
- `JobLogStore` class (in-memory job log store)

**Modern Equivalent:** May have been replaced by SQLite-backed stores in `app/stores/`

**Recovery:** Verify if functionality exists elsewhere before restoring

---

### 7. LOW: AI Prompt Templates

**Status:** ❌ MISSING

**File Deleted:** `app/ai/prompts/templates.py` (235 lines)

**Functionality Lost:**
- `PromptTemplate` dataclass with variable substitution
- `ROSETTE_SYSTEM_PROMPT` and `ROSETTE_USER_TEMPLATE`
- `RosettePromptBuilder` class (builder pattern for prompts)

**Modern Equivalent:** Check `app/vision/prompt_engine.py` and `app/vision/vocabulary.py`

**Recovery:** Low priority - AI prompt patterns may have evolved

---

### 8. LOW: Workflow Integration Schemas

**Status:** ❌ MISSING

**File Deleted:** `app/art_studio/services/workflow_schemas.py` (181 lines)

**Functionality Lost:**
- `CreateFromPatternRequest`, `CreateFromGeneratorRequest`, `CreateFromSnapshotRequest`
- `EvaluateFeasibilityRequest`, `ApproveSessionRequest`, `RejectSessionRequest`
- `RequestRevisionRequest`, `UpdateDesignRequest`, `SaveSnapshotRequest`

**Modern Equivalent:** Check if these schemas exist in `app/art_studio/schemas/`

**Recovery:** Verify if workflow API still uses these request types

---

## Files Successfully Restored (No Action Needed)

These were deleted but have since been restored:

| File | Status |
|------|--------|
| `app/cam_core/tools/models.py` | ✅ RESTORED |
| `app/ltb_calculators/luthier_calculator.py` | ✅ RESTORED |
| `app/art_studio/bracing_router.py` | ✅ RESTORED |
| `app/art_studio/inlay_router.py` | ✅ RESTORED |
| `app/art_studio/relief_router.py` | ✅ RESTORED (preview only) |
| `app/art_studio/vcarve_router.py` | ✅ RESTORED |
| `app/routers/music/temperament_router.py` | ✅ RESTORED |
| `app/routers/instruments/guitar/registry_router.py` | ✅ RESTORED |
| `app/routers/instruments/guitar/assets_router.py` | ✅ RESTORED |

---

## Recommended Actions

### Immediate (P0)
1. **FIX** `app/util/post_injection_helpers.py` import chain
   - Option A: Restore `app/post_injection_helpers.py`
   - Option B: Rewrite wrapper to use `app/post_injection_dropin.py` functions

### Short-term (P1-P2)
2. **VERIFY** `/api/cam/toolpath/relief/export-dxf` endpoint exists
3. **RESTORE** WebSocket monitor if real-time features are needed
4. **AUDIT** job log schemas for duplication

### Long-term (P3)
5. **DOCUMENT** intentionally removed features in CHANGELOG
6. **CREATE** architectural decision records for queue system changes

---

## Git Recovery Commands

To view deleted file content:
```bash
# View post_injection_helpers.py from before deletion
git show 520f3ea3^:services/api/app/post_injection_helpers.py

# View cam_relief_router.py from before deletion
git show b5f48a4c^:services/api/app/routers/cam_relief_router.py

# Restore a file from before deletion
git checkout 520f3ea3^ -- services/api/app/post_injection_helpers.py
```

---

## Appendix: Full Deletion History

### Commit `b5f48a4c` - 21 Dormant Routers
- 85 routes deleted across 21 router files
- Most have been restored
- 4 routers still missing (cam_relief, pipeline, cnc_production/presets, cam_dxf_adaptive)

### Commit `520f3ea3` - Phase 4 Cleanup
- 9 files deleted (-2502 lines)
- 2 files restored (tools/models.py, luthier_calculator.py)
- 7 files still missing (listed above)
