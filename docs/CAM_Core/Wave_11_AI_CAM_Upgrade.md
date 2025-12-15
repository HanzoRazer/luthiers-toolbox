# Wave 11 — AI-Assisted CAM + G-Code Explainer 2.0

This wave completes the intelligence layer of CAM Core.

**Status:** ✅ Implemented  
**Date:** December 7, 2025  
**Module:** AI-CAM (Wave 11)

---

## Overview

Wave 11 introduces two major systems:

1. **AI-Assisted CAM Advisor** — Analyzes operations → warns → suggests → optimizes
2. **G-Code Explainer 2.0** — Reads G-code → annotates → identifies danger → communicates clearly

Both run on top of:
- RMOS 2.0 context
- The Calculator Spine
- The Wave 10 CAM infrastructure
- The Tool & Material library
- Art Studio → RMOS → Toolpath chain

---

## Subsystems Added

### 1. CAMAdvisor

Analyzes toolpaths using Calculator Spine:
- **Chipload** — Range validation with warnings
- **Heat** — Temperature risk assessment (COLD/WARM/HOT)
- **Deflection** — Tool deflection safety (GREEN/YELLOW/RED)
- **Rim Speed** — Surface speed validation
- **Kickback** — Saw blade kickback risk (LOW/MEDIUM/HIGH)

Produces warnings, errors, and recommended parameter changes.

**File:** `services/api/app/ai_cam/advisor.py`

### 2. G-Code Explainer 2.0

Reads raw G-code and explains:
- Motion semantics (G0 rapid, G1 cut, G2/G3 arcs)
- Coordinate changes (X, Y, Z, F, S)
- Z-height safety analysis
- Feed/RPM change detection
- Risk annotations per line

**File:** `services/api/app/ai_cam/explain_gcode.py`

### 3. CAMOptimizer

Stub for parameter optimization using physics feedback:
- Searches ±10% variations in feed and RPM
- Scores candidates based on physics results
- Returns ranked list with best recommendation

**File:** `services/api/app/ai_cam/optimize.py`

### 4. AI-CAM FastAPI Router

Endpoints:
- `POST /api/ai-cam/analyze-operation` — Cut operation analysis
- `POST /api/ai-cam/explain-gcode` — G-code explanation
- `POST /api/ai-cam/optimize` — Parameter optimization
- `GET /api/ai-cam/health` — Health check

**File:** `services/api/app/routers/ai_cam_router.py`

### 5. Art Studio Integration Hooks

UI receives:
- Advisories (info/warning/error)
- Recommended feed/RPM
- Annotated G-code

---

## File Structure

```
services/api/app/
├── ai_cam/
│   ├── __init__.py          # Module exports
│   ├── models.py             # Data models (CAMAdvisory, GCodeExplanation)
│   ├── advisor.py            # CAMAdvisor class
│   ├── explain_gcode.py      # GCodeExplainer class
│   └── optimize.py           # CAMOptimizer class
└── routers/
    └── ai_cam_router.py      # FastAPI endpoints
```

---

## API Reference

### POST /api/ai-cam/analyze-operation

Analyze a cut operation for physics-based advisories.

**Request:**
```json
{
  "tool_id": "endmill-6mm",
  "material_id": "hardwood-maple",
  "tool_kind": "router_bit",
  "feed_mm_min": 1000,
  "rpm": 12000,
  "depth_of_cut_mm": 1.5,
  "width_of_cut_mm": 3.0,
  "machine_id": "shapeoko-3"
}
```

**Response:**
```json
{
  "advisories": [
    {
      "message": "Chipload is out of range: 0.0042 mm/tooth",
      "severity": "warning",
      "context": {"chipload": 0.0042}
    }
  ],
  "recommended_changes": {
    "feed_mm_min": null,
    "rpm": null,
    "depth_of_cut_mm": null,
    "note": "AI tuning stub — real tuning arrives in Wave 11.2"
  },
  "physics": {
    "chipload": {"chipload_mm": 0.0042, "in_range": false},
    "heat": {"category": "WARM", "heat_risk": 0.45},
    "deflection": {"deflection_mm": 0.02, "risk": "GREEN"}
  }
}
```

### POST /api/ai-cam/explain-gcode

Explain G-code line by line.

**Request:**
```json
{
  "gcode_text": "G21\nG90\nG0 X0 Y0\nG1 Z-1.5 F500",
  "safe_z": 5.0
}
```

**Response:**
```json
{
  "overall_risk": "low",
  "explanations": [
    {"line_number": 1, "raw": "G21", "explanation": "Units: Millimeters", "risk": null},
    {"line_number": 2, "raw": "G90", "explanation": "Absolute positioning mode", "risk": null},
    {"line_number": 3, "raw": "G0 X0 Y0", "explanation": "Rapid move (non-cutting) — [X=0, Y=0]", "risk": null},
    {"line_number": 4, "raw": "G1 Z-1.5 F500", "explanation": "Linear cutting move — [Z=-1.5, F=500]", "risk": null}
  ]
}
```

### POST /api/ai-cam/optimize

Search for optimized cutting parameters.

**Request:**
```json
{
  "tool_id": "endmill-6mm",
  "material_id": "hardwood-maple",
  "tool_kind": "router_bit",
  "feed_mm_min": 1000,
  "rpm": 12000,
  "depth_of_cut_mm": 1.5,
  "search_pct": 0.10
}
```

**Response:**
```json
{
  "candidates": [
    {
      "feed_mm_min": 1100.0,
      "rpm": 12000,
      "depth_of_cut_mm": 1.5,
      "score": 95.2,
      "physics": {...},
      "notes": ["✓ Chipload in range", "✓ Heat: COLD (optimal)"]
    }
  ],
  "best": {...}
}
```

---

## Summary — What Wave 11 Achieves

| Subsystem | Effect |
|-----------|--------|
| **CAM** | Gains intelligence, not just path generation |
| **RMOS** | Gains optimization tuning input |
| **Art Studio** | Gains warnings + live physics panel |
| **Saw Lab** | Gains kickback modeling + advisory |
| **G-Code** | Gains human-readable explanations |
| **Operators** | Gain safer, more predictable machining |

This is the first wave where the ToolBox becomes a **real CNC advisor**, not just a generator.

---

## See Also

- [Wave 12 — AI-CAM UI](./Wave_12_AI_CAM_UI.md)
- [Calculator Spine](../Calculator_Spine_Overview.md)
- [RMOS 2.0](../../RMOS_2_0_ARCHITECTURE.md)
