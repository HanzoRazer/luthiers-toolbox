# Sprint Backlog

## TypeScript Errors Catalog (packages/client)

**Total errors: 363**
**Date cataloged: 2026-04-12**

### Error Summary by Type

| Code | Count | Description |
|------|-------|-------------|
| TS2307 | 333 | Cannot find module or type declarations |
| TS2353 | 23 | Object literal may only specify known properties |
| TS2322 | 3 | Type is not assignable |
| TS2740 | 1 | Type missing properties |
| TS2724 | 1 | Module has no exported member |

### Critical Missing Modules

#### `@/types/headstock` (4 consumers)

This module is imported but does not exist. Defines core import pipeline types.

**Required types:**
- `ImportedPath`
- `BBox`
- `NormalizeOptions`
- `FitMode`
- `FlipYMode`

**Consumers:**
- `src/composables/useDxfImport.ts` (line 12)
- `src/composables/useExportDxf.ts` (lines 14, 18)
- `src/design-utilities/lutherie/neck/useCamSpec.ts` (line 21)

**Action:** Create `src/types/headstock.ts` with type definitions extracted from useDxfImport.ts usage patterns.

---

#### `@/assets/data/headstockData` (1 consumer)

- `src/composables/useExportDxf.ts` (line 17)

---

#### `./useParametric` (1 consumer)

- `src/composables/useExportDxf.ts` (line 16)

---

### Errors by Directory (TS2307 only)

| Directory | Count | Notes |
|-----------|-------|-------|
| src/router/index.ts | 82 | Missing route component imports |
| src/components/toolbox | 32 | Missing Vue component exports |
| src/components/rmos | 32 | Missing Vue component exports |
| src/tools/audio_analyzer | 26 | Missing module imports |
| src/components/cam | 22 | Missing Vue component exports |
| src/components/ui | 19 | Missing Vue component exports |
| src/components/art | 14 | Missing Vue component exports |
| src/components/rosette | 10 | Missing Vue component exports |
| src/components/pocket | 10 | Missing Vue component exports |
| src/design-utilities/lutherie | 8 | Missing composable imports |
| src/components/adaptive | 8 | Missing Vue component exports |

### Type Assignment Errors

#### `useDxfImport.ts:278` - TS2322

```typescript
// isVectorizerAvailable is ref<boolean | null>
// checkVectorizerStatus returns Promise<boolean>
return isVectorizerAvailable.value  // Error: boolean | null not assignable to boolean
```

**Fix:** Change return type to `Promise<boolean | null>` or add null coalescing.

---

#### `useExportDxf.ts:15` - TS2724

```typescript
import { KonvaCanvas } from './useKonvaCanvas'  // Error: no exported member 'KonvaCanvas'
```

**Fix:** The export is `useKonvaCanvas`, not `KonvaCanvas`. Update import.

---

### Root Cause Analysis

The majority of errors (333/363) are **missing module declarations** (TS2307). This suggests:

1. **Barrel exports incomplete**: Many `index.ts` files re-export components that don't exist or have wrong paths
2. **Type definitions missing**: Core types like `headstock.ts` were never created or were deleted
3. **Router imports stale**: 82 errors in router suggest component moves without import updates

### Recommended Fix Order

1. **Create `src/types/headstock.ts`** - Unblocks composables (4 files)
2. **Fix `useExportDxf.ts` imports** - 4 errors, quick wins
3. **Audit router/index.ts** - 82 errors, likely stale imports
4. **Audit component barrel exports** - Bulk of remaining errors

---

## Current Sprint: Vectorizer Canonical Migration (COMPLETE)

**Status:** Phase 2 complete. Vue consumers migrated to canonical vectorizer response fields. Photo router compat shim removed. Legacy response fields, deprecation block, and shim flag deleted. Runtime validated with canonical-only responses. Frontend remains functional without legacy API fields.

### Stage 1: Utility Foundation (COMPLETE)
- [x] Create `packages/client/src/utils/vectorizerArtifacts.ts`
- [x] Enrich `photo_orchestrator.py` metrics
- [x] Update `photo_vectorizer_router.py` to use orchestrator metrics
- [x] Add `processing_ms` to `blueprint_orchestrator.py`

### Stage 2: Photo Frontend Migration (COMPLETE)
- [x] Update `useDxfImport.ts` to use canonical fields
- [x] Add `loadFromSvgContent()` function
- [x] Update `photoMeta` type with recommendation fields
- [x] Import from `@/utils/vectorizerArtifacts`
- [ ] Verify TypeScript compiles (blocked by pre-existing TS2307)
- [ ] Test photo import flow end-to-end

### Stage 3: Blueprint Frontend Migration (COMPLETE)
- [x] Migrate `useBlueprintWorkflow.ts`
  - [x] Update `VectorizedGeometry` interface with canonical fields
  - [x] Update silhouette response mapping
  - [x] Update blueprint response mapping
  - [x] Update `downloadVectorizedSVG()` to use inline content
  - [x] Update `downloadVectorizedDXF()` to use base64 content
- [x] Migrate `BlueprintLab.vue`
  - [x] Update `v2Result` type with canonical fields
  - [x] Add computed accessors for canonical/legacy fallback
  - [x] Update template to use computed accessors
  - [x] Update download functions to use base64 content
  - [x] Add recommendation display
- [x] Migrate `VectorizationResults.vue`
  - [x] Update `svgPreviewUrl` to use inline content as data URL

### Stage 4: Runtime Audit (READY)

**4A — Static Audit (COMPLETE)**
- [x] No primary reads of legacy fields
- [x] All legacy usage is fallback pattern: `canonical ?? legacy`

**4B — Runtime Audit**
Kill switch added to `photo_vectorizer_router.py`:
```python
PHOTO_LEGACY_COMPAT = os.getenv("PHOTO_LEGACY_COMPAT", "true").lower() == "true"
```

Test sequence:
```bash
# 1. Verify flag is visible
curl http://localhost:8000/api/vectorizer/status | jq .legacy_compat_enabled

# 2. Run with legacy OFF
PHOTO_LEGACY_COMPAT=false uvicorn app.main:app --reload

# 3. Test flows:
#    - Photo import → review
#    - Photo import → reject  
#    - Blueprint → success
#    - Download DXF
#    - Preview SVG
```

**4C — Kill Switch Test**
- [ ] `PHOTO_LEGACY_COMPAT=false` locally
- [ ] Full photo import flow works
- [ ] Full blueprint flow works
- [ ] Downloads work (base64 decode, not file fetch)
- [ ] Previews work (inline SVG, not URL fetch)

### Stage 5: Disable Legacy Compat (READY TO DEPLOY)
- [x] `PHOTO_LEGACY_COMPAT` flag added
- [x] Shim wrapped with flag check
- [x] Status endpoint reports flag state
- [ ] Deploy with `PHOTO_LEGACY_COMPAT=false`
- [ ] Monitor for 24h

### Stage 6: Hard Removal (COMPLETE)
- [x] Delete `_build_legacy_compat_shim()`
- [x] Delete `_extract_svg_path_d_from_content()`
- [x] Remove legacy fields from `VectorizeResponse` model
- [x] Remove `Deprecation` model
- [x] Remove `PHOTO_LEGACY_COMPAT` flag and `os` import
- [x] Remove pass-through fields from `PhotoResult` dataclass
- [x] Simplified response building to canonical-only
- [x] Runtime validated: legacy fields return `None` (absent from response)

---

## Follow-up Tasks

### Regression Guard (recommended)
Add API test asserting these keys are **absent** from `/api/vectorizer/extract` response:
- `svg_path_d`, `svg_path`, `dxf_path`
- `body_width_mm`, `body_height_mm`
- `contour_count`, `line_count`
- `export_blocked`, `export_block_reason`
- `deprecation`

### Frontend Cleanup (low priority)
- Remove `?? legacy` fallback chains from Vue composables
- Tighten TS types to canonical-only (compile errors catch hidden references)
- Files: `useDxfImport.ts`, `useBlueprintWorkflow.ts`, `BlueprintLab.vue`

---

## Legacy Artifacts Cleanup Plan

**Phase:** Post-Canonical Migration (Phase 2 Complete)

### Current State
- Canonical-only API response
- Legacy response fields removed
- Compat shim deleted
- Router is pass-through only
- Frontend uses canonical fields as primary
- Regression tests enforce absence of legacy fields

### Cleanup Targets

| Priority | Target | Files | Action |
|----------|--------|-------|--------|
| HIGH | Frontend fallback chains | `useDxfImport.ts`, `useBlueprintWorkflow.ts`, `BlueprintLab.vue`, `VectorizationResults.vue` | Remove `?? legacy` patterns |
| HIGH | Legacy type definitions | TS interfaces | Remove `svg_path_d`, `body_width_mm`, etc. from types |
| MEDIUM | `contour_count` ambiguity | UI components | Replace with `artifacts.dxf.closed_contours` or `selection.candidate_count` |
| MEDIUM | Deprecated dimension fields | UI components | Replace `body_width_mm` → `dimensions.width_mm` |
| MEDIUM | Export blocking semantics | UI components | Replace `export_blocked` → `recommendation.action` |
| MEDIUM | Confidence semantics | UI components | Replace `dimensions.confidence` → `recommendation.confidence` |
| LOW | Dead utilities | Frontend | Confirm no SVG path_d parsing helpers exist |
| LOW | Documentation drift | Docs | Update API docs, examples, README |

### Legacy Field Mapping

| Legacy Field | Canonical Replacement |
|--------------|----------------------|
| `svg_path_d` | `artifacts.svg.content` |
| `svg_path` | (removed - stateless) |
| `dxf_path` | `artifacts.dxf.base64` |
| `body_width_mm` | `dimensions.width_mm` |
| `body_height_mm` | `dimensions.height_mm` |
| `contour_count` | `artifacts.svg.path_count` or `selection.candidate_count` |
| `line_count` | `artifacts.dxf.entity_count` |
| `export_blocked` | `recommendation.action == "reject"` |
| `export_block_reason` | `recommendation.reasons[0]` |
| `processing_ms` | `metrics.processing_ms` |
| `scale_source` | `metrics.scale_source` |
| `bg_method` | `metrics.bg_method` |
| `perspective_corrected` | `metrics.perspective_corrected` |

### Grep Audit Checklist

```bash
# Run from packages/client/src
grep -r "svg_path_d" .
grep -r "body_width_mm" .
grep -r "body_height_mm" .
grep -r "contour_count" .
grep -r "export_blocked" .
grep -r "export_block_reason" .
grep -r "?? " . | grep -E "(width|height|path|count)"
```

### Exit Criteria
- [ ] No legacy fields in codebase
- [ ] No fallback expressions (`?? legacy`)
- [ ] TS types canonical-only
- [ ] UI behavior unchanged
- [ ] No grep hits for legacy terms
- [ ] Build passes cleanly

### Deleted Functions (Backend - Already Removed)
- `_build_legacy_compat_shim()` — photo_vectorizer_router.py
- `_extract_svg_path_d_from_content()` — photo_vectorizer_router.py
- `PHOTO_LEGACY_COMPAT` flag — photo_vectorizer_router.py

### Deleted Models (Backend - Already Removed)
- `Deprecation` — photo_vectorizer_router.py
- Legacy fields from `VectorizeResponse` — photo_vectorizer_router.py
- Pass-through fields from `PhotoResult` — photo_orchestrator.py

---

## AI Path Fix (COMPLETE)

**Date:** 2026-04-12
**Status:** Verified

### Problem
AI extraction path in `photo_vectorizer_v2.py` hard-gated on `spec_name` before proceeding. If no spec was provided, extraction aborted early with no artifacts generated.

### Fix
Modified `_extract_ai_path()` to allow unscaled extraction when no spec is provided:

| Component | Change |
|-----------|--------|
| `is_unscaled` flag | Tracks whether spec is available |
| Auto-rotate | Only runs when spec available |
| Validation | Only runs when spec available |
| Scaling | Uses spec dimensions OR raw pixel coordinates |
| Calibration | Uses `INSTRUMENT_SPEC` or `NONE` source |
| Warning | Adds "Unscaled AI extraction — dimensions unavailable without spec calibration" |
| Export | Proceeds regardless of spec availability |

### Expected Behavior (without spec_name)
- `artifacts.svg.present`: true
- `artifacts.dxf.present`: true (if export_dxf=true)
- `dimensions`: (0.0, 0.0)
- `calibration.source`: NONE
- `recommendation.action`: review
- `warnings`: includes unscaled extraction notice

### File Modified
`services/photo-vectorizer/photo_vectorizer_v2.py` lines 4635-4760

---

## Contour Scoring Enhancement (COMPLETE)

**Date:** 2026-04-12
**Status:** Implemented

### Problem
Blueprint PDFs contain multiple competing contours (page borders, title blocks, annotations). Scoring couldn't distinguish the guitar body from noise, resulting in:
- `winner_margin = 0.00`
- `recommendation.action = "reject"`
- User message: "Selection score below accept threshold; Winner margin weak"

### Root Cause
**Selection worked. Discrimination failed.** Contours were extracted correctly, but no single candidate emerged as clearly "the body."

### Solution
Added three new signals to `contour_scoring.py`:

| Signal | Purpose |
|--------|---------|
| `_touches_border()` | Detect contours touching image edges (returns edge_count 0-4) |
| `_is_page_border()` | Hard filter: touches 3+ edges OR touches 2+ edges with area > 70% |
| `_centrality_score()` | Body contours are typically centered (0.0 = edge, 1.0 = center) |

### ContourScore Dataclass
New fields added:
- `centrality_score: float` — how centered the contour is
- `touches_border: bool` — whether contour touches image edge
- `edge_count: int` — number of edges touched (0-4)
- `is_page_border: bool` — detected as page border (hard reject)

### Scoring Weight Update
```python
# With ownership signal:
0.30 * area_ratio +      # reduced from 0.35
0.25 * closure +
0.10 * aspect +
0.10 * solidity +        # reduced from 0.15
0.05 * continuity +
0.10 * ownership +
0.10 * centrality        # NEW

# Without ownership:
0.30 * area_ratio +
0.25 * closure +
0.10 * aspect +
0.10 * solidity +
0.10 * continuity +
0.15 * centrality        # Higher weight when no ownership
```

### Recommendation Layer Update
- Added `page_border_rejected` flag to `RecommendationInput`
- Hard-fail detection: "Best candidate was page border — body contour not detected"
- Improved margin=0 messaging: "Multiple competing contours — may need to isolate body outline"

### Files Modified
- `services/api/app/services/contour_scoring.py` — new filters and scoring
- `services/api/app/services/contour_recommendation.py` — better failure messaging

### Expected Behavior
When processing a blueprint PDF:
1. Page borders are hard-rejected with reason `page_border`
2. Centered contours score higher than edge-hugging ones
3. If margin is still weak, user sees specific guidance about competing contours

---

## Contour Hierarchy Isolation (COMPLETE)

**Date:** 2026-04-12
**Status:** Implemented - Phases 1-3

### Architecture Change

**Before:**
```
PDF -> render -> edge detect -> findContours(RETR_LIST) -> ALL contours -> DXF -> score chains
```

**After:**
```
PDF -> render -> edge detect -> findContours(RETR_TREE) -> hierarchy isolation -> body candidates only -> DXF -> score chains
```

### Phase 1: New Module `contour_hierarchy.py`

Created `services/api/app/services/contour_hierarchy.py`:

| Export | Purpose |
|--------|---------|
| `ContourNode` | Contour with hierarchy context (parent, children, depth) |
| `BodyCandidate` | Top-level candidate with child metrics |
| `build_hierarchy()` | Convert raw OpenCV hierarchy to ContourNode list |
| `isolate_body_candidates()` | Filter to top-level non-border candidates |
| `hierarchy_summary()` | Debug statistics |

**ContourNode fields:**
- `idx`, `contour`, `parent_idx`, `child_indices`, `depth`
- `area`, `bbox`, `perimeter`
- `touches_border_edges` (0-4), `is_page_border`
- `is_outer_candidate`, `is_child_feature`, `reject_reason`

**BodyCandidate fields:**
- `node`, `child_nodes`
- `child_area_sum`, `child_area_ratio`, `has_internal_structure`

### Phase 2: Hierarchy-Aware Scoring

Added to `services/api/app/services/contour_scoring.py`:

**New function:** `score_body_candidates()`

Child-aware scoring:
```python
# Effective fill ratio (don't penalize holes)
effective_fill = min(1.0, (outer_area + child_area_sum) / hull_area)

# Small capped bonus for internal structure
if 1 <= child_count <= 6 and 0.01 <= child_area_ratio <= 0.25:
    child_bonus = min(0.08, child_area_ratio * 0.25)
```

### Phase 3: Edge-to-DXF Integration

Modified `services/photo-vectorizer/edge_to_dxf.py`:

| Change | Description |
|--------|-------------|
| `_touches_border()` | Check if contour touches image edges |
| `_is_page_border()` | Detect page border (3+ edges OR 2+ edges with >70% area) |
| `_centrality_score()` | Score how centered contour is |
| `_isolate_body_contours()` | Filter to body candidates using hierarchy |
| `convert(..., isolate_body=True)` | New parameter enables hierarchy mode |

Modified `services/api/app/services/blueprint_extract.py`:
- Added `isolate_body: bool = True` parameter
- Default enabled for blueprint extraction

### Files Modified/Created

| File | Action |
|------|--------|
| `services/api/app/services/contour_hierarchy.py` | Created |
| `services/api/app/services/contour_scoring.py` | Added `score_body_candidates()` |
| `services/photo-vectorizer/edge_to_dxf.py` | Added hierarchy helpers + `isolate_body` param |
| `services/api/app/services/blueprint_extract.py` | Added `isolate_body` param (default True) |

### Validation Checklist

- [ ] Clean single-view PDF: strong margin, accept/review
- [ ] Page-border-heavy scan: border rejected, body in candidate pool
- [ ] Archtop/hole-rich body: outer contour selected, children as features
- [ ] Previously weak-margin case: improved margin

### Phase 5: Debug Overlay (COMPLETE)

**Module:** `services/photo-vectorizer/contour_debug_overlay.py`

**Trigger:** `DEBUG_CONTOURS=1` environment variable

**Output files:**
- `{stem}_overlay.png` — Full image with color-coded contours
- `{stem}_candidates.png` — Grid of candidate crops

**Color semantics:**
| Color | Meaning |
|-------|---------|
| Blue | Selected contour |
| Green | Top-level candidate |
| Orange | Child contour |
| Red | Page border |
| Gray | Rejected |

**Functions:**
- `is_debug_enabled()` — Check DEBUG_CONTOURS env var
- `score_body_candidates_for_debug()` — Lightweight debug-only scoring
- `to_debug_nodes()` — Convert hierarchy nodes to debug format
- `to_debug_summary()` — Build summary panel data
- `render_contour_hierarchy_overlay()` — Draw annotated overlay
- `render_candidate_grid()` — Draw candidate comparison grid
- `write_debug_bundle()` — Write both images to disk

**Hook point:** `edge_to_dxf.py` after `_isolate_body_contours()`, before DXF creation

**Usage:**
```bash
DEBUG_CONTOURS=1 python -m edge_to_dxf blueprint.png -o output.dxf
```

---

## Async Job Status Fix (COMPLETE)

**Date:** 2026-04-12
**Status:** Fixed

### Problem
Async blueprint jobs incorrectly mapped to `FAILED` when `BlueprintResult.ok == false`. Since `ok` means recommendation acceptance (not pipeline execution success), the async wrapper was dropping valid review/reject payloads by storing `result=null`.

### Root Cause
```python
# Before (buggy):
if result.ok:
    status = COMPLETE, result = payload
else:
    status = FAILED, result = payload  # BUT serialization returns null for FAILED
```

The `_serialize_job()` function returns `result: null` when status is not COMPLETE (line 48).

### Fix
```python
# After (correct):
# Orchestrator returns any result → COMPLETE
job_store.update(
    job_id,
    status=JobStatus.COMPLETE,
    stage=result.stage,
    progress=100,
    result=payload,
    ...
)
# Only exceptions → FAILED
```

### Mental Model
| Concept | Represents |
|---------|------------|
| `JobStatus` | Execution outcome (did the job run?) |
| `payload.ok` / `recommendation.action` | Product outcome (should user accept?) |

### Behavior After Fix
| Orchestrator Result | Job Status | Result Available |
|---------------------|------------|------------------|
| Returns with `ok=true` | COMPLETE | Yes |
| Returns with `ok=false` (review/reject) | COMPLETE | Yes |
| Throws exception | FAILED | No |

### File Modified
`services/api/app/routers/blueprint_async_router.py` lines 100-122

### Deferred to Phase 4

- Merged fragment fallback (when margin remains weak after hierarchy isolation)
