# CAM-Ready R2000 Verification

**Date:** 2026-04-29  
**Test Input:** El Cuatro 1.pdf → Phase 3 vectorizer → export_cam_ready_dxf(dxf_version='R2000')  
**Output:** /tmp/cuatro_cam_ready_R2000_test.dxf

---

## DXF Inventory

| Metric | Value |
|--------|-------|
| DXF Version | AC1015 (R2000) |
| Total Entities | 37 |
| Entity Type | LWPOLYLINE (100%) |
| Closed Flag Set | 37/37 (100%) |

### Point Count Distribution

| Range | Count |
|-------|-------|
| 2 points | 0 |
| 3-9 points | 15 |
| 10-99 points | 19 |
| 100+ points | 3 |

### Layer Breakdown

| Layer | Entities | Closed | Point Distribution |
|-------|----------|--------|-------------------|
| BODY_OUTLINE | 1 | 1 | 100+ pts |
| BODY_OUTLINE_CANDIDATE | 1 | 1 | 100+ pts |
| PICKGUARD | 5 | 5 | 4×(3-9), 1×(100+) |
| SMALL_FEATURE | 10 | 10 | 7×(3-9), 3×(10-99) |
| TEXT | 10 | 10 | 2×(3-9), 8×(10-99) |
| UNKNOWN | 10 | 10 | 2×(3-9), 8×(10-99) |

---

## GRBL Pipeline Result

| Layer | HTTP | ok | G-code Lines |
|-------|------|-----|--------------|
| BODY_OUTLINE | 200 | ✅ true | 2260 |
| PICKGUARD | 200 | ✅ true | 11 |
| SMALL_FEATURE | 200 | ✅ true | 47 |

---

## Outcome

**Hypothesis A confirmed.**

The contour data arriving at `export_cam_ready_dxf` is already ordered, multi-point, and loop-aware. The 2-point LINE output observed in the previous investigation was purely an artifact of R12 serialization via `dxf_compat.add_polyline()`.

Switching to R2000 produces multi-point closed LWPOLYLINEs without any other code changes. The GRBL pipeline successfully generates G-code from all tested layers.

**Fix required:** Pass `dxf_version='R2000'` from vectorizer_phase3.py:3584 to `export_cam_ready_dxf()`. No loop-assembly work needed.
