# Dead Code Recovery Assessment

**Generated:** 2026-02-27
**Commits Analyzed:** `b5f48a4c` (21 dormant routers), `520f3ea3` (Phase 4 cleanup)
**Total Lines Deleted:** ~4,000+ across both commits

---

## Executive Summary

During aggressive dead-code cleanup, several functional modules were incorrectly deleted.
**All items have now been restored or fixed (Wave 27.1).**

### Recovery Status (All Complete)

| Priority | File | Lines | Status |
|----------|------|-------|--------|
| **P0-CRITICAL** | `app/post_injection_helpers.py` | 488 | ✅ **FIXED** - Import chain repaired |
| **P1-HIGH** | `app/routers/cam_dxf_adaptive_router.py` | 147 | ✅ **RESTORED** - Wired in manifest |
| **P1-HIGH** | `app/routers/cam_relief_router.py` | 160 | ✅ **RESTORED** - Wired in manifest |
| **P1-HIGH** | `app/cam_core/saw_lab/queue.py` | 265 | ✅ **RESTORED** |
| **P2-MEDIUM** | `app/routers/cnc_production/presets_router.py` | 77 | ✅ **RESTORED** - Wired in manifest |
| **P2-MEDIUM** | `app/websocket/monitor.py` | 131 | ✅ **RESTORED** |
| **P2-MEDIUM** | `app/schemas/job_log.py` | 81 | ✅ **RESTORED** |
| **P2-MEDIUM** | `app/services/rmos_stores.py` | 130 | ✅ **RESTORED** |
| **P3-LOW** | `app/ai/prompts/templates.py` | 235 | ✅ **RESTORED** |
| **P3-LOW** | `app/art_studio/services/workflow_schemas.py` | 181 | ✅ **RESTORED** |
| **OK** | `app/routers/pipeline_router.py` | 108 | ✅ Migrated to RMOS — no action needed |

**Total Restored:** 1,407 lines across 9 files

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

### 3. HIGH: DXF → Adaptive Pocket Router

**Status:** ❌ MISSING

**File Deleted:** `app/routers/cam_dxf_adaptive_router.py` (147 lines)

**Functionality Lost:**
- `POST /cam/dxf_adaptive_plan_run` - Upload DXF → Extract polylines → Generate adaptive pocket toolpath
- `_dxf_to_adaptive_request()` - Convert DXF closed polylines to adaptive pocket plan request
- Bridge between DXF geometry and `/api/cam/pocket/adaptive/plan`
- Used by BridgeLab UI for direct DXF-to-toolpath workflow

**Current State:**
- `app/cam/routers/export/__init__.py` tries to import it (gracefully fails to `None`)
- The DXF → Adaptive workflow is **completely broken**
- No endpoint exists to convert DXF geometry to adaptive pocket toolpaths

**Recovery:** RESTORE - Real functionality loss affecting BridgeLab UI

---

### 4. HIGH: Full CAM Relief Router

**Status:** ❌ MISSING (services exist but are orphaned)

**File Deleted:** `app/routers/cam_relief_router.py` (160 lines)

**Functionality Lost:**
- `POST /cam/relief/map_from_heightfield` - heightmap → Z grid conversion
- `POST /cam/relief/roughing` - multi-pass roughing toolpath
- `POST /cam/relief/finishing` - scallop-based finishing toolpath
- `POST /cam/relief/sim_bridge` - mesh simulation bridge

**Current State:**
- `app/art_studio/relief_router.py` exists but is **PREVIEW ONLY** (no CAM output)
- `app/services/relief_kernels.py` has `plan_relief_roughing()` and `plan_relief_finishing()` — **ORPHANED**
- These service functions exist but **NO ROUTER CALLS THEM**
- The services are unreachable via any API endpoint

**Recovery:** RESTORE - Services exist, just need the router to expose them

---

### 5. MEDIUM: CNC Production Presets Router

**Status:** ❌ MISSING (may have replacement)

**File Deleted:** `app/routers/cnc_production/presets_router.py` (77 lines)

**Functionality Lost:**
- `GET /cnc/presets` - List all CNC presets
- `GET /cnc/presets/{id}` - Get preset by ID
- `POST /cnc/presets` - Create preset
- `PATCH /cnc/presets/{id}` - Update preset
- `DELETE /cnc/presets/{id}` - Delete preset
- Used `preset_store.py` for persistence

**Current State:**
- `app/services/pipeline_preset_store.py` exists (different pattern)
- `app/cam/routers/utility/settings_router.py` has some preset management
- May have been replaced by new preset architecture

**Recovery:** VERIFY if new preset stores cover this use case before restoring

---

### 6. OK: Pipeline Router (Migrated)

**Status:** ✅ MIGRATED - No action needed

**File Deleted:** `app/routers/pipeline_router.py` (108 lines)

**Original Functionality:**
- `POST /cam/pipeline/run` - DXF upload through full CAM pipeline

**Current State:**
- Functionality **moved** to `app/rmos/pipeline/services_execution.py`
- `app/routers/cam_pipeline_preset_run_router.py` wraps it with preset support
- Pipeline execution now part of RMOS architecture

**Recovery:** None needed - this was an intentional migration

---

### 7. MEDIUM: WebSocket Real-Time Monitor

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
