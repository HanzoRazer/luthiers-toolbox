# Rosette Canonical Route Proposal

**Dev Order:** 5G  
**Date:** 2026-05-10  
**Status:** Recommendation Only (No Implementation)

---

## Canonical Preview Candidates

### Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Frontend alignment | HIGH | Has active frontend consumers |
| Generator ownership | HIGH | Single clear generator |
| Export coupling | HIGH | Does NOT produce machine output |
| RMOS integration | MEDIUM | Has or can have governance |
| Coordinate documentation | MEDIUM | Origin/units explicit |

---

### Candidate 1: `/api/art/rosette/preview/svg`

**File:** `art_studio/api/preview_routes.py`  
**Generator:** rosette_engine (inferred)  
**Output:** SVG string

| Criterion | Score | Notes |
|-----------|-------|-------|
| Frontend alignment | GOOD | Used by artPreviewClient.ts |
| Generator ownership | GOOD | Single generator |
| Export coupling | GOOD | SVG only, no G-code |
| RMOS integration | NONE | Not integrated |
| Coordinate docs | UNKNOWN | Not documented |

**Recommendation:** CANDIDATE_PREVIEW  
**Action Required:** Document coordinate system, add RMOS metadata

---

### Candidate 2: `/api/rmos/rosette/preview`

**File:** `rmos/rosette_cam_router.py`  
**Generator:** tile_segmentation.build_preview_snapshot  
**Output:** Snapshot payload with rings

| Criterion | Score | Notes |
|-----------|-------|-------|
| Frontend alignment | GOOD | Used by useRosetteDesignerStore |
| Generator ownership | GOOD | Single generator |
| Export coupling | PARTIAL | Same router has export-cnc |
| RMOS integration | PARTIAL | Under RMOS prefix but no artifacts |
| Coordinate docs | UNKNOWN | Not documented |

**Recommendation:** CANDIDATE_PREVIEW  
**Action Required:** Separate from export-cnc, document coordinates

---

### Candidate 3: `/api/art/rosette/preview`

**File:** `art_studio/api/rosette_jobs_routes.py`  
**Generator:** Inline (generate_circle_points)  
**Output:** Path points + bbox

| Criterion | Score | Notes |
|-----------|-------|-------|
| Frontend alignment | GOOD | Used by RosettePipelineView |
| Generator ownership | POOR | Inline geometry, not reusable |
| Export coupling | GOOD | No G-code |
| RMOS integration | NONE | Not integrated |
| Coordinate docs | UNKNOWN | Not documented |

**Recommendation:** LEGACY  
**Reason:** Inline generator not suitable for canonical

---

### Candidate 4: `/api/art/rosette/project`

**File:** `art_studio/api/rosette_manufacturing_routes.py`  
**Generator:** rosette_cam_bridge.plan_per_ring_toolpath  
**Output:** Toolpath data

| Criterion | Score | Notes |
|-----------|-------|-------|
| Frontend alignment | UNKNOWN | No traced consumer |
| Generator ownership | GOOD | Uses rosette_cam_bridge |
| Export coupling | MEDIUM | Toolpath is export-adjacent |
| RMOS integration | NONE | Not integrated |
| Coordinate docs | PARTIAL | Bridge has partial docs |

**Recommendation:** CANDIDATE_PREVIEW (for CAM preview)  
**Action Required:** Clarify toolpath vs preview semantics

---

## Canonical Recommendation

### For Design Preview (Visual)

**Recommended:** `/api/art/rosette/preview/svg`

**Rationale:**
- Produces SVG (pure visual, no machine semantics)
- Single generator ownership
- No export coupling
- Frontend consumer exists

**Prerequisites for promotion:**
1. Document coordinate system
2. Add `coordinate_system` field to response
3. Add RMOS metadata (optional for preview)

---

### For CAM Preview (Geometry Validation)

**Recommended:** `/api/rmos/rosette/preview`

**Rationale:**
- Under RMOS prefix (governance-aware path)
- Uses tile_segmentation (CNC-aware geometry)
- Frontend consumer exists (useRosetteDesignerStore)

**Prerequisites for promotion:**
1. Separate physically from export-cnc
2. Document coordinate system
3. Add gate semantics
4. Ensure NO G-code emitted

---

### For Governed Export

**Recommended:** `/api/cam/rosette/post-gcode`

**Rationale:**
- Already RMOS integrated
- Uses rosette_cam_bridge.postprocess_toolpath_grbl
- Clear export semantics

**Prerequisites for promotion:**
1. Verify RMOS artifact persistence
2. Add coordinate_system to response
3. Document safety gate

---

## Routes NOT Recommended for Canonical

| Route | Reason |
|-------|--------|
| `/api/art/rosette/preview` | Inline generator |
| `/api/rmos/rosette/export-cnc` | Ungoverned export |
| `/pipelines/rosette/*` | Legacy, no governance |
| `/api/art/rosette/pattern/*` | Experimental |

---

## Future Canonicalization Sequence

```
5H — Select canonical preview (SVG for design, RMOS for CAM)
5I — Implement governed preview contract
5J — Separate export boundary
5K — Promote governed export
```

---

*Proposal created: 2026-05-10*  
*Classification: Recommendation Only*
