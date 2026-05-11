# Rosette CAM Normalization Blockers

**Date:** 2026-05-10  
**Auditor:** Claude (CAM Dev Order 5F)  
**Status:** Audit Complete

---

## Executive Summary

Before Rosette CAM can be normalized to governed preview standards (like 5C-5E), the following blockers must be resolved.

---

## Blocking Issues

### 1. Route Surface Ambiguity (BLOCKING)

**Issue:** Multiple preview routes exist. Which becomes canonical?

| Candidate | File | Generator | RMOS |
|-----------|------|-----------|------|
| `/rosette/designer/preview` | rosette_designer_routes.py | rosette_engine | No |
| `/api/art/rosette/preview` | rosette_jobs_routes.py | inline | No |
| `/rmos/rosette/preview` | rosette_cam_router.py | tile_segmentation | No |

**Blocker Type:** Ownership ambiguity

**Resolution Required:**
1. Decide canonical preview route
2. Deprecate non-canonical routes
3. Update frontend consumers

---

### 2. Missing Frontend Route Trace (BLOCKING)

**Issue:** Frontend references routes not found in backend audit.

| Frontend Reference | Status |
|--------------------|--------|
| `/art-studio/rosette/preview` | MISSING |
| `/art-studio/rosette/export-dxf` | MISSING |
| `/art-studio/rosette/presets` | MISSING |
| `/api/art/rosette/preview/svg` | MISSING |
| `/api/art/rosette/feasibility/batch` | MISSING |

**Blocker Type:** Unknown consumer breakage risk

**Resolution Required:**
1. Full trace of where these routes are mounted
2. Document actual route prefixes
3. Verify frontend/backend alignment

---

### 3. Ungovened G-code Export (BLOCKING)

**Issue:** `rosette_cam_router.py` exports G-code without RMOS governance.

```python
@router.post("/rosette/export-cnc")
def export_rosette_cnc(payload):
    # Direct G-code return, no run artifact
    return {"gcode": gcode, "job_id": job_id}
```

**Blocker Type:** Machine output governance violation

**Resolution Required:**
1. Add RMOS run artifact persistence
2. Add input/output hashing
3. Add safety policy check
4. Or quarantine endpoint

---

### 4. Coordinate System Documentation (BLOCKING)

**Issue:** No consistent coordinate system documentation across generators.

| Generator | Origin Documented | Z-Zero Documented |
|-----------|-------------------|-------------------|
| rosette_engine | No | N/A |
| rosette_cam_bridge | Partial | Yes |
| cnc_gcode_exporter | Yes | Yes |
| tile_segmentation | No | N/A |

**Blocker Type:** Governance compliance

**Resolution Required:**
1. Document coordinate system in each generator
2. Add `coordinate_system` field to responses (per CAM_PREVIEW_CONTRACT_STANDARD)

---

### 5. Postprocessor Fragmentation (MEDIUM)

**Issue:** Two separate postprocessor implementations.

| Postprocessor | Profiles | Location |
|---------------|----------|----------|
| `postprocess_toolpath_grbl()` | GRBL only | rosette_cam_bridge.py |
| `generate_gcode_from_toolpaths()` | GRBL, FANUC | cnc_gcode_exporter.py |

**Blocker Type:** Export consistency

**Resolution Required:**
1. Decide canonical postprocessor
2. Wire all G-code routes through single postprocessor
3. Ensure profile selection is consistent

---

### 6. Schema Consolidation (MEDIUM)

**Issue:** Multiple schema files define overlapping models.

**Resolution Required:**
1. Identify shared schema concepts
2. Consolidate into single source of truth
3. Update all consumers

---

## Non-Blocking Issues

### Preview Output Format Variance

**Issue:** Different generators produce different preview formats (SVG, paths, snapshot).

**Impact:** Frontend must handle multiple formats.

**Recommendation:** Document formats, defer consolidation.

---

### Prototype Code in Production Path

**Issue:** `rosette_pattern_routes.py` imports from `prototypes/herringbone_parametric.py`.

**Impact:** Experimental code in production route.

**Recommendation:** Tag as experimental or promote to production.

---

### Multiple Job Stores

**Issue:** `rosette_snapshot_store` and `art_studio_rosette_store` both persist rosette data.

**Impact:** Data fragmentation.

**Recommendation:** Document purpose distinction, defer consolidation.

---

## Resolution Priority Order

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | Missing frontend route trace | LOW | HIGH |
| 2 | Ungovened G-code export | LOW | HIGH |
| 3 | Route surface ambiguity | MEDIUM | HIGH |
| 4 | Coordinate documentation | LOW | MEDIUM |
| 5 | Postprocessor consolidation | MEDIUM | MEDIUM |
| 6 | Schema consolidation | MEDIUM | LOW |

---

## Recommended Normalization Path

### Phase 1: Trace and Document (No Code Changes)

1. Complete frontend route trace
2. Document all route prefixes
3. Document coordinate systems
4. Identify canonical preview route

### Phase 2: Governance Gates (Minimal Code Changes)

1. Add RMOS to rosette_cam_router.py G-code endpoints
2. Add coordinate_system field to preview responses
3. Wire governed preview to single canonical route

### Phase 3: Consolidation (Code Changes)

1. Deprecate non-canonical preview routes
2. Unify postprocessors
3. Consolidate schemas

---

## Prerequisites for Governed Preview (5F → 5G)

Before promoting Rosette to governed preview:

- [ ] Canonical preview route identified
- [ ] Frontend route trace complete
- [ ] Coordinate system documented
- [ ] G-code endpoints have RMOS governance
- [ ] Gate semantics defined for rosette-specific conditions

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| ROSETTE_CAM_ROUTE_MAP.md | Full route inventory |
| ROSETTE_CAM_OWNERSHIP_GRAPH.md | Generator ownership |
| ROSETTE_CAM_FRAGMENTATION_AUDIT.md | Overlap analysis |
| CAM_PREVIEW_CONTRACT_STANDARD.md | Target contract |
| CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md | G-code governance |

---

*Normalization blockers audit completed: 2026-05-10*
