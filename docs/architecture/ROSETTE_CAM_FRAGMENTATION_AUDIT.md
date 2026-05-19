# Rosette CAM Fragmentation Audit

**Date:** 2026-05-10  
**Auditor:** Claude (CAM Dev Order 5F)  
**Status:** Audit Complete

---

## Executive Summary

Rosette CAM exhibits **HIGH fragmentation** across all measured dimensions:
- 11 route files with overlapping purposes
- 7+ distinct generators producing similar outputs
- 3+ preview implementations
- 2+ G-code generation paths
- Mixed preview/export semantics

---

## Fragmentation Categories

### 1. Route Surface Fragmentation

**Signal:** Multiple routes with overlapping purpose

| Purpose | Routes Found | Overlap Severity |
|---------|--------------|------------------|
| Preview | 3 endpoints across 3 files | HIGH |
| G-code export | 2 endpoints across 2 files | MEDIUM |
| Pattern generation | 2 endpoints across 2 files | MEDIUM |
| Job persistence | 2 stores, 2 route files | MEDIUM |
| BOM calculation | 2 implementations | LOW |

---

### 2. Preview Fragmentation (Critical)

**Finding:** Frontend requests hit inconsistent preview paths

| Frontend Client | Expected Route | Actual Implementation |
|-----------------|----------------|----------------------|
| `artStudioApi.ts` | `/art-studio/rosette/preview` | Not found in route audit |
| `artPreviewClient.ts` | `/api/art/rosette/preview/svg` | Not found in route audit |
| `rosettePresets.ts` | Multiple | Uses multiple paths |

**Backend Preview Routes:**

| Route | File | Generator | Output |
|-------|------|-----------|--------|
| `/rosette/designer/preview` | rosette_designer_routes.py | rosette_engine | SVG |
| `/api/art/rosette/preview` | rosette_jobs_routes.py | inline | Paths + bbox |
| `/rmos/rosette/preview` | rosette_cam_router.py | tile_segmentation | Snapshot |

**Root Cause:** Art Studio consolidation left orphaned frontend paths.

---

### 3. G-code Generator Fragmentation

**Finding:** Multiple postprocessors with different profiles

| Generator | Location | Profiles | RMOS? |
|-----------|----------|----------|-------|
| `postprocess_toolpath_grbl()` | rosette_cam_bridge.py | GRBL only | Yes |
| `generate_gcode_from_toolpaths()` | cnc_gcode_exporter.py | GRBL, FANUC | No |
| `simulate_build_and_cnc()` | herringbone_parametric.py | GRBL | No |

**Impact:** 
- No unified postprocessor interface
- Profile selection fragmented
- RMOS governance inconsistent

---

### 4. Schema Fragmentation

**Finding:** Multiple schema files defining similar concepts

| Concept | Defined In | Overlap |
|---------|------------|---------|
| Ring definition | rosette_designer.py, models.py, rosette_pattern.py | 3 definitions |
| Preview request | rosette_designer.py, art-studio.ts | Diverged |
| BOM response | rosette_designer.py, rosette_manufacturing_routes.py | 2 definitions |
| Job/Snapshot | rosette_snapshot.py, rosette_jobs_routes.py | Overlap |

---

### 5. Coordinate System Fragmentation

**Finding:** Coordinate assumptions vary by generator

| Generator | Origin | Z-Zero | Units | Documented |
|-----------|--------|--------|-------|------------|
| rosette_engine | soundhole center | N/A | mm | No |
| rosette_cam_bridge | user-specified | safe_z | mm | Partial |
| cnc_gcode_exporter | jig alignment | safe_z | mm | Yes |
| tile_segmentation | ring center | N/A | mm | No |

**Impact:** No consistent coordinate system governance.

---

### 6. Preview/Export Semantic Mixing

**Finding:** Some endpoints mix preview and export responsibilities

| Endpoint | File | Mixing Evidence |
|----------|------|-----------------|
| `/rosette/export-cnc` | rosette_cam_router.py | Returns G-code directly (export) but no RMOS |
| `/rosette/post-gcode` | rosette_toolpath_router.py | Export with RMOS (correct) |
| `/api/art/rosette/pattern/export` | rosette_pattern_routes.py | Export stub, incomplete |
| `/rosette/designer/export/svg` | rosette_designer_routes.py | Export, no RMOS |

**Impact:** Inconsistent governance boundaries.

---

## Fragmentation Status by Subsystem

| Subsystem | Status | Primary Issues |
|-----------|--------|----------------|
| rosette_designer | ACTIVE | Well-contained but no governed preview |
| rosette_jobs | ACTIVE | Overlaps with snapshots |
| rosette_snapshots | ACTIVE | Good RMOS, overlaps with jobs |
| rosette_compare | ACTIVE | Standalone, well-contained |
| rosette_pattern | ACTIVE | Imports experimental code |
| rosette_manufacturing | ACTIVE | Complex dependencies |
| rosette_toolpath | ACTIVE | Good RMOS, single-profile postprocessor |
| rosette_cam (RMOS) | ACTIVE | Direct G-code export (governance risk) |
| rosette_pdf | CANDIDATE | Not audited |

---

## Frontend/Backend Route Mismatch

**Finding:** Frontend API clients reference routes not found in backend audit

| Frontend Reference | Backend Route | Status |
|--------------------|---------------|--------|
| `/art-studio/rosette/preview` | Not found | MISSING |
| `/art-studio/rosette/export-dxf` | Not found | MISSING |
| `/art-studio/rosette/presets` | Not found | MISSING |
| `/api/art/rosette/preview/svg` | Not found | MISSING |
| `/api/art/rosette/feasibility/batch` | Not found | MISSING |

**Possible Causes:**
1. Routes exist but not in audited files
2. Routes were removed but frontend not updated
3. Routes are mounted under different prefixes

**Recommendation:** Needs deeper trace to resolve.

---

## Duplicate Functionality Matrix

| Function | rosette_engine | rosette_cam_bridge | pattern_generator | tile_segmentation | cnc_gcode |
|----------|----------------|--------------------|--------------------|-------------------|-----------|
| Preview SVG | **Yes** | No | Yes (optional) | No | No |
| Preview geometry | No | No | Yes | **Yes** | No |
| Toolpath planning | No | **Yes** | No | No | No |
| G-code generation | No | **Yes** | No | No | **Yes** |
| BOM calculation | **Yes** | No | No | No | No |
| Manufacturing plan | No | No | No | No | No |
| Feasibility | **Yes** | No | No | No | No |

**Observation:** Pattern generator and tile_segmentation produce similar preview outputs.

---

## Consolidation Opportunity Assessment

| Consolidation Target | Difficulty | Impact | Recommended |
|---------------------|------------|--------|-------------|
| Merge preview generators | HIGH | Moderate | No (defer) |
| Unify postprocessors | MEDIUM | High | Yes |
| Consolidate schemas | MEDIUM | Moderate | Yes |
| Wire governed preview | LOW | High | **Yes (5F follow-up)** |
| Add RMOS to rosette_cam_router | LOW | High | **Yes** |
| Remove frontend orphans | LOW | Low | Yes |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking unknown frontend consumers | HIGH | Full route trace before changes |
| G-code without governance | HIGH | Add RMOS to rosette_cam_router |
| Coordinate system divergence | MEDIUM | Document and enforce standards |
| Preview response shape divergence | MEDIUM | Governed preview normalization |
| Schema drift | LOW | Consolidate shared schemas |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| ROSETTE_CAM_ROUTE_MAP.md | Full route inventory |
| ROSETTE_CAM_OWNERSHIP_GRAPH.md | Generator ownership |
| ROSETTE_CAM_NORMALIZATION_BLOCKERS.md | Prerequisites |
| CAM_POSTPROCESSOR_BOUNDARY.md | Export governance |

---

*Fragmentation audit completed: 2026-05-10*
