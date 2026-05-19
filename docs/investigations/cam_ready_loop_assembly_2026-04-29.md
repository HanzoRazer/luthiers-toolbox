# CAM-Ready Loop Assembly Investigation

**Date:** 2026-04-29  
**Test Input:** El Cuatro 1.pdf → Phase 3 vectorizer with `cam_ready=True`  
**Output:** /tmp/el_cuatro_test_cam.dxf

---

## DXF Inventory

| Metric | Value |
|--------|-------|
| DXF Version | AC1009 (R12) |
| Total Entities | 556 |
| Entity Type | LINE (100%) |
| LWPOLYLINE | 0 |
| Closed Polylines | 0 |

### Point Distribution

| Points per Entity | Count |
|-------------------|-------|
| 2 | 556 |
| ≥3 | 0 |
| ≥10 | 0 |

### Layer Breakdown

| Layer | Entities | Point Counts | Closed |
|-------|----------|--------------|--------|
| BODY_OUTLINE | 218 | 2-point only | 0 |
| BODY_OUTLINE_CANDIDATE | 101 | 2-point only | 0 |
| PICKGUARD | 119 | 2-point only | 0 |
| SMALL_FEATURE | 118 | 2-point only | 0 |

---

## CAM Pipeline Result

| Layer | Status | G-code Lines |
|-------|--------|--------------|
| BODY_OUTLINE | ❌ FAILED | 0 |
| BODY_OUTLINE_CANDIDATE | ❌ FAILED | 0 |
| PICKGUARD | ❌ FAILED | 0 |
| SMALL_FEATURE | ❌ FAILED | 0 |
| 0 (all layers) | ❌ FAILED | 0 |

Error message: "No closed polylines found on layer 'X'"

---

## Root Cause

Two gaps combine to produce unusable output:

1. **dxf_compat.py:131-140**: R12 version outputs individual LINE segments, not polylines
2. **mvp_router.py:83-96**: GRBL pipeline only processes LWPOLYLINE/POLYLINE entities

The `export_cam_ready_dxf` function defaults to R12 (`dxf_version='R12'`) and does not receive the vectorizer's dxf_version setting. Even contours with 50+ points become 50 separate 2-point LINE entities instead of one closed polyline.

---

## Outcome

**Loop assembly is missing.**

The `cam_ready=True` path produces per-segment 2-point LINE entities, identical to the gap found in the manually-converted test files. The paid-tier wiring plan requires an additional loop-assembly step before this output is CAM-usable.
