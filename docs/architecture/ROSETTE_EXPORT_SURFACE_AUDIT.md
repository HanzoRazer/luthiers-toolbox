# Rosette Export Surface Audit

**Dev Order:** 5G  
**Date:** 2026-05-10  
**Status:** Audit Complete

---

## Export Routes Identified

### Route 1: `/api/rmos/rosette/export-cnc` (QUARANTINED)

**File:** `rmos/rosette_cam_router.py:296`  
**Generator:** `cnc_gcode_exporter.generate_gcode_from_toolpaths`  
**Method:** POST

#### Output Analysis

```python
return {
    "ok": True,
    "gcode": gcode,           # MACHINE OUTPUT
    "job_id": job_id,
    "ring_id": ring.ring_id,
    "segment_count": len(export_bundle.toolpaths.segments),
    "estimated_runtime_sec": simulation.estimated_runtime_sec,
    "safety": {...},          # Has safety decision
    "metadata": export_bundle.metadata,
}
```

#### Governance Audit

| Check | Status | Evidence |
|-------|--------|----------|
| Produces G-code | YES | `gcode` field in response |
| RMOS artifact persistence | NO | No `put_bytes_attachment` call |
| Input hashing | NO | Not implemented |
| Output hashing | NO | Not implemented |
| Safety gate | PARTIAL | Returns safety decision but doesn't block |
| Coordinate metadata | NO | Not in response |
| Machine profile explicit | YES | `machine_profile` parameter |

#### Risk Assessment

| Risk | Level | Evidence |
|------|-------|----------|
| Ungoverned machine output | HIGH | G-code returned without RMOS artifact |
| No audit trail | HIGH | Job ID generated but not persisted to RMOS |
| Safety bypass possible | MEDIUM | Safety decision returned but not enforced |
| Coordinate ambiguity | MEDIUM | No coordinate_system in response |

**Classification:** `QUARANTINED_EXPORT`

**Required Governance Gates:**
1. RMOS run artifact creation
2. Input/output hash persistence
3. Safety gate enforcement (block on RED)
4. Coordinate system declaration
5. Tool validation

---

### Route 2: `/api/cam/rosette/post-gcode` (GOVERNED)

**File:** `cam/routers/rosette/rosette_toolpath_router.py:268`  
**Generator:** `rosette_cam_bridge.postprocess_toolpath_grbl`  
**Method:** POST

#### Governance Audit

| Check | Status | Evidence |
|-------|--------|----------|
| Produces G-code | YES | Response contains G-code |
| RMOS integration | YES | Under RMOS-governed path |
| Safety semantics | YES | Uses rosette_cam_bridge |
| Coordinate docs | PARTIAL | Bridge has partial docs |

**Classification:** `GOVERNED_EXPORT`

**Remaining Requirements:**
1. Verify RMOS artifact persistence is complete
2. Add coordinate_system to response

---

### Route 3: `/rosette/designer/export/svg` (UNTRACKED)

**File:** `art_studio/api/rosette_designer_routes.py`  
**Generator:** `rosette_engine.render_preview_svg`  
**Method:** POST

#### Governance Audit

| Check | Status | Evidence |
|-------|--------|----------|
| Produces machine output | NO | SVG only |
| RMOS integration | NO | Not integrated |
| Export semantics | YES | Named "export" |

**Classification:** `UNTRACKED_EXPORT` (SVG, low risk)

---

### Route 4: `/pipelines/rosette/export-gcode` (LEGACY)

**File:** `utils/api.ts` (frontend reference)  
**Backend:** Unknown/Legacy

#### Status

| Check | Status |
|-------|--------|
| Backend exists | UNKNOWN |
| Active use | UNLIKELY |
| Documentation | NONE |

**Classification:** `LEGACY_EXPORT`

---

### Route 5: `/pipelines/rosette/export-dxf` (LEGACY)

**File:** `utils/api.ts` (frontend reference)  
**Backend:** Unknown/Legacy

**Classification:** `LEGACY_EXPORT`

---

## Export Classification Summary

| Route | Classification | Machine Output | RMOS | Action |
|-------|----------------|----------------|------|--------|
| `/api/rmos/rosette/export-cnc` | QUARANTINED_EXPORT | YES | NO | Add governance |
| `/api/cam/rosette/post-gcode` | GOVERNED_EXPORT | YES | YES | Verify complete |
| `/rosette/designer/export/svg` | UNTRACKED_EXPORT | NO | NO | Low priority |
| `/pipelines/rosette/export-gcode` | LEGACY_EXPORT | UNKNOWN | NO | Deprecate |
| `/pipelines/rosette/export-dxf` | LEGACY_EXPORT | NO | NO | Deprecate |

---

## Quarantine Actions for `/api/rmos/rosette/export-cnc`

### Immediate (5G)

1. **Document as QUARANTINED** in manifest
2. **No behavior changes** — quarantine is classification only

### Future (5H+)

1. Add RMOS run artifact creation
2. Add input hash to artifact
3. Add output hash to artifact
4. Enforce safety gate (block if RED)
5. Add `coordinate_system` to response
6. Add deprecation header pointing to `/api/cam/rosette/post-gcode`

---

## Machine Output Governance Requirements

Per CAM_MACHINE_OUTPUT_QUARANTINE_POLICY, any route that produces G-code must:

| Requirement | `/export-cnc` | `/post-gcode` |
|-------------|---------------|---------------|
| RMOS run artifact | MISSING | VERIFY |
| Input hash | MISSING | UNKNOWN |
| Output hash | MISSING | UNKNOWN |
| Safety gate | PARTIAL | YES |
| Coordinate metadata | MISSING | PARTIAL |
| Tool validation | UNKNOWN | UNKNOWN |

---

*Export audit completed: 2026-05-10*
