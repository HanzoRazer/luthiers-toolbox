# Morphology Harvest Adapter Wiring Report

**Date:** 2026-05-17
**Sprint:** IBG Morphology Harvest 1B-FIX
**Status:** REWIRED — Using canonical blueprint_reader.html pipeline

---

## Summary

Corrected adapter wiring to use the canonical blueprint_reader.html pipeline instead of the incomplete Phase 4 R&D asset.

### Critical Correction

**Phase 4 is NOT the canonical extraction pipeline.**

Phase 4 (`services/blueprint-import/phase4/`) is an incomplete R&D asset for dimension-to-geometry association. Its technology has not been fully implemented or integrated into production.

The canonical pipeline is **blueprint_reader.html** which uses:
- Raw edge extractor (PDF → DXF): `/api/blueprint/vectorize/async`
- Edge to DXF (photo → DXF): `/api/vectorizer/extract`

---

## Adapter Status

| Adapter | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| BlueprintVectorizerAdapter | WIRED | `/api/blueprint/vectorize/async` | PDF → DXF extraction |
| PhotoVectorizerAdapter | WIRED | `/api/vectorizer/extract` | Image → DXF extraction |
| CalibrationMetadataAdapter | WIRED | (embedded) | Calibration in vectorizer response |
| BodyGridAdapter | AVAILABLE | (local) | Same service, relative import |

---

## Architecture

### Canonical Data Flow

```
PDF Blueprint
    │
    ▼
POST /api/blueprint/vectorize/async
    │
    ├── Submit job → job_id
    │
    ▼
GET /api/blueprint/vectorize/status/{job_id}
    │
    ├── Poll until complete
    │
    ▼
Response:
    {
      "ok": true,
      "dimensions": {"width_mm": 350, "height_mm": 450},
      "artifacts": {
        "svg": {"present": true, "content": "..."},
        "dxf": {"present": true, "base64": "..."}
      }
    }
    │
    ▼
Morphology Harvest
    │
    ├── Extract dimensions → body_length_mm, lower_bout_width_mm
    ├── Store SVG/DXF artifacts
    │
    ▼
Body Grid Analysis (if evidence sufficient)
```

### Photo Path

```
Photo/Image
    │
    ▼
POST /api/vectorizer/extract
    {
      "image_b64": "...",
      "source_type": "auto",
      "export_svg": true,
      "export_dxf": true
    }
    │
    ▼
Response:
    {
      "ok": true,
      "body_width_mm": 350,
      "body_height_mm": 450,
      "svg_content": "...",
      "dxf_base64": "..."
    }
```

---

## API Reference

### Blueprint Vectorizer (PDF → DXF)

**Submit Job:**
```
POST /api/blueprint/vectorize/async
Content-Type: multipart/form-data

file: <PDF file>
target_height_mm: 500
min_contour_length_mm: 50
close_gaps_mm: 1.0
```

**Response:**
```json
{"job_id": "abc123..."}
```

**Poll Status:**
```
GET /api/blueprint/vectorize/status/{job_id}
```

**Response (complete):**
```json
{
  "status": "complete",
  "result": {
    "ok": true,
    "dimensions": {"width_mm": 350.5, "height_mm": 450.2},
    "artifacts": {
      "svg": {"present": true, "content": "<svg>...</svg>"},
      "dxf": {"present": true, "base64": "..."}
    }
  }
}
```

### Photo Vectorizer (Image → DXF)

```
POST /api/vectorizer/extract
Content-Type: application/json

{
  "image_b64": "<base64 encoded image>",
  "source_type": "auto",
  "export_svg": true,
  "export_dxf": true,
  "spec_name": "les_paul"  // optional
}
```

**Response:**
```json
{
  "ok": true,
  "body_width_mm": 350.5,
  "body_height_mm": 450.2,
  "contour_count": 12,
  "scale_source": "body_heuristic",
  "svg_content": "<svg>...</svg>",
  "dxf_base64": "..."
}
```

---

## Files Modified

- `services/api/app/instrument_geometry/body/ibg/morphology_harvest/adapters.py`
  - Replaced Phase4DimensionAssociationAdapter with BlueprintVectorizerAdapter
  - Added PhotoVectorizerAdapter
  - Updated CalibrationMetadataAdapter (now notes calibration is embedded)
  - Added backwards-compatible `get_phase4_adapter()` deprecation shim

- `services/api/app/instrument_geometry/body/ibg/morphology_harvest/harvest_coordinator.py`
  - Updated to use `get_blueprint_adapter()` instead of `get_phase4_adapter()`
  - Updated upstream_sources keys to `blueprint_vectorizer`
  - Added svg_content and dxf_base64 storage on HarvestRecord

---

## Lesson Learned

**Always verify the canonical data flow before wiring integrations.**

Phase 4 was an R&D prototype that was never integrated into production. The canonical pipeline was always blueprint_reader.html, which uses REST API endpoints for extraction.

The correct approach:
1. Identify the canonical production pipeline (blueprint_reader.html)
2. Understand what endpoints it uses
3. Wire adapters to those endpoints
4. Do NOT assume internal Python modules are the authority

---

## Next Steps

1. Run validation on 10 representative instruments using canonical pipeline
2. Verify dimensions are extracted correctly
3. Test Body Grid morphology classification with real SVG/DXF data
4. Document results in VALIDATION_1B_FIX_RESULTS.md
