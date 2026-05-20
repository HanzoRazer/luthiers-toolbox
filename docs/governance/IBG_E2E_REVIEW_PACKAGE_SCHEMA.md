# IBG E-2-E Review Package Schema

**Date:** 2026-05-17
**Sprint:** IBG E-2-E Functional Spine
**Status:** Implemented

---

## Overview

The BOE Review Package is a JSON structure produced by the E-2-E spine that contains all information needed for human review of morphology extraction and reconstruction.

---

## Schema Definition

```json
{
  "source_file": "string — original PDF/image filename",
  "source_mode": "string — 'pdf' or 'photo'",
  "run_id": "string — unique E-2-E run identifier",
  "timestamp": "string — ISO 8601 timestamp",

  "svg_artifact_path": "string | null — path to extracted SVG preview",
  "dxf_artifact_path": "string | null — path to extracted DXF artifact",

  "body_evidence_summary": {
    "outline_points_count": "int — total points extracted",
    "contour_segments_count": "int — number of separate contour chains",
    "landmarks_count": "int — landmarks detected",
    "source_type": "string — evidence source enum value",
    "bounding_box_mm": "[min_x, min_y, max_x, max_y] | null",
    "centerline_x_mm": "float | null"
  },

  "body_grid_result": {
    "success": "bool — whether Body Grid analysis completed",
    "morphology_class": "string | null — classified body type",
    "confidence": "float — 0.0 to 1.0"
  },

  "morphology_descriptor": {
    "morphology_class": "string | null",
    "confidence": "float",
    "centerline_x_mm": "float | null",
    "asymmetry_score": "float",
    "is_symmetric": "bool",
    "zone_coverage": {
      "centerline": "float",
      "upper_bout": "float",
      "waist": "float",
      "lower_bout": "float",
      "...": "other zones"
    },
    "primitives_count": "int"
  },

  "ibg_reconstruction_status": "string — 'complete', 'failed', 'not_attempted', 'not_callable_yet'",
  "ibg_result": {
    "status": "string",
    "spec_used": "string | null — instrument spec used for reconstruction",
    "confidence": "float | null",
    "outline_points": "int | null",
    "error": "string | null — if failed"
  },

  "failures": ["string — list of failure messages"],
  "uncertainties": ["string — list of uncertainty notes"],
  "review_notes_placeholder": "string — for human reviewer notes",
  "review_status": "string — 'pending', 'needs_review', 'ready', 'approved', 'rejected'"
}
```

---

## Field Descriptions

### Source Identification

| Field | Type | Description |
|-------|------|-------------|
| `source_file` | string | Original filename of the PDF or image |
| `source_mode` | string | "pdf" for blueprints, "photo" for images |
| `run_id` | string | Unique identifier for this E-2-E run (e.g., "e2e_abc123") |
| `timestamp` | string | ISO 8601 timestamp of when the run started |

### Artifacts

| Field | Type | Description |
|-------|------|-------------|
| `svg_artifact_path` | string | Absolute path to extracted SVG preview for visual review |
| `dxf_artifact_path` | string | Absolute path to extracted DXF for reconstruction |

### Body Evidence Summary

| Field | Type | Description |
|-------|------|-------------|
| `outline_points_count` | int | Total number of coordinate points extracted |
| `contour_segments_count` | int | Number of separate contour chains/polylines |
| `landmarks_count` | int | Semantic landmarks detected (butt_center, neck_center, etc.) |
| `source_type` | string | Evidence source: "vectorizer_dxf", "photo_extraction", etc. |
| `bounding_box_mm` | array | [min_x, min_y, max_x, max_y] in millimeters |
| `centerline_x_mm` | float | Detected or computed centerline X coordinate |

### Body Grid Analysis

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether Body Grid analysis completed without error |
| `morphology_class` | string | Classified body type (slab_body, rounded_single_cut, etc.) |
| `confidence` | float | Classification confidence (0.0 - 1.0) |

### Morphology Descriptor

| Field | Type | Description |
|-------|------|-------------|
| `morphology_class` | string | Same as body_grid_result, from variant match |
| `confidence` | float | Overall descriptor confidence |
| `centerline_x_mm` | float | Centerline used for normalization |
| `asymmetry_score` | float | 0.0 = symmetric, higher = more asymmetric |
| `is_symmetric` | bool | Whether body is considered symmetric |
| `zone_coverage` | object | Coverage ratio per body zone |
| `primitives_count` | int | Number of morphology primitives detected |

### IBG Reconstruction

| Field | Type | Description |
|-------|------|-------------|
| `ibg_reconstruction_status` | string | Overall status code |
| `ibg_result.status` | string | Detailed status: "complete", "failed", "no_dxf_artifact" |
| `ibg_result.spec_used` | string | Instrument spec used for completion |
| `ibg_result.confidence` | float | Reconstruction confidence score |
| `ibg_result.outline_points` | int | Points in completed outline |
| `ibg_result.error` | string | Error message if failed |

### Review Status

| Field | Type | Description |
|-------|------|-------------|
| `failures` | array | List of error messages from any stage |
| `uncertainties` | array | Non-fatal issues requiring review |
| `review_notes_placeholder` | string | Empty field for human reviewer |
| `review_status` | string | Current review state |

---

## Review Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Initial state, not yet reviewed |
| `needs_review` | Has uncertainties or low confidence |
| `ready` | All stages complete, no errors |
| `approved` | Human reviewer approved |
| `rejected` | Human reviewer rejected |

---

## Output Location

Review packages are written to:

```
services/api/app/instrument_geometry/body/ibg/morphology_harvest/outputs/e2e_spine/{run_id}/
├── artifact.svg          # Visual preview
├── artifact.dxf          # DXF extraction
├── boe_review_package.json  # This schema
└── e2e_result.json       # Full E2ESpineResult
```

This directory is gitignored as generated staging output.

---

## Usage

```python
from app.instrument_geometry.body.ibg.morphology_harvest.e2e_spine_runner import E2ESpineRunner

runner = E2ESpineRunner()
result = runner.run_pdf("path/to/blueprint.pdf")

# BOE package is at:
print(result.boe_package_path)
```

---

## Future Extensions

The schema is designed to support:

1. **Three-loop feedback** — `extraction_strategy`, `correction_pending` fields
2. **BOE UI integration** — `review_notes_placeholder` for human input
3. **Batch review** — consistent schema across all instruments
4. **Quality tracking** — `confidence` and `uncertainties` for triage
