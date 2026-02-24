# Analyzer Module Boundary Specification

**Date:** 2026-02-23
**Status:** Enforced
**Location:** `services/api/app/analyzer/`

---

## The Principle

> **tap_tone_pi asks:** "What frequencies are present?"
> **toolbox analyzer asks:** "What does that mean for this build?"

If the code answers the first question → tap_tone_pi.
If the code answers the second question → toolbox analyzer.

---

## Boundary Rules

### ALLOWED Imports

```python
from app.core.*           # Shared types, math utilities
from app.calculators.*    # Domain calculations (fret math, etc.)
```

### FORBIDDEN Imports

```python
from app.cam.*            # CAM has no business here
from app.rmos.*           # RMOS consumes us, we don't consume it
from app.saw_lab.*        # Production, not analysis
from tap_tone_pi.*        # HARD BOUNDARY - contract only
import tap_tone           # FORBIDDEN
```

### Input Contract

The ONLY interface to tap_tone_pi is `viewer_pack_v1`:

```json
{
  "schema_version": "viewer_pack_v1",
  "measurement_only": true,
  "interpretation": "deferred",
  "specimen_id": "top_001",
  "peaks": [...],
  "transfer_function": [...],
  "wolf_metrics": {...},
  "mode_shapes": [...]
}
```

We NEVER import tap_tone_pi code. We consume its output contract.

---

## Module Structure

```
services/api/app/analyzer/
├── __init__.py              # Boundary rules documented
├── schemas.py               # ViewerPackV1, InterpretationResult
├── viewer_pack_loader.py    # ONLY interface to tap_tone_pi data
├── spectrum_service.py      # Visualization preparation
├── modal_visualizer.py      # Mode shape rendering
├── design_advisor.py        # Recommendations engine
├── router.py                # API endpoints
└── reference_library/       # Known-good instruments (future)
```

---

## What This Module Does (INTERPRETATION)

| Function | Example |
|----------|---------|
| Visualize spectrum | Format FFT data for chart.js |
| Annotate peaks | "165 Hz = E3, likely T1 mode" |
| Assess wolf risk | "WSI 0.12 suggests asymmetric bracing" |
| Compare to reference | "10% higher than Martin D-28 T1 mode" |
| Recommend actions | "Consider reducing top thickness by 0.3mm" |

---

## What This Module Does NOT Do (MEASUREMENT)

| Function | Belongs To |
|----------|------------|
| Capture audio | tap_tone_pi |
| Compute FFT | tap_tone_pi |
| Calculate transfer function | tap_tone_pi |
| Detect peaks | tap_tone_pi |
| Compute WSI number | tap_tone_pi |
| Export viewer_pack | tap_tone_pi |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    LUTHIERS-TOOLBOX                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  ANALYZER MODULE                        │   │
│  │                                                         │   │
│  │  viewer_pack_v1.json ──► Interpretation ──► Recommend   │   │
│  │                                                         │   │
│  │  "165 Hz peak"      ──► "Main top mode" ──► "Good"     │   │
│  │  "WSI = 0.15"       ──► "Wolf risk"     ──► "Fix it"   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  CAM / RMOS / Saw Lab can consume interpretation          │ │
│  │  but analyzer does NOT import them                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ viewer_pack_v1.json (file/HTTP)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│                       TAP_TONE_PI                               │
│                  (Measurement Instrument)                       │
│                                                                 │
│   Mic ──► DSP ──► Peaks ──► WSI ──► Export viewer_pack         │
│                                                                 │
│   NO visualization. NO interpretation. Just measurement.        │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/analyzer/interpret` | Full interpretation with recommendations |
| `POST /api/analyzer/interpret/upload` | Upload viewer_pack file |
| `POST /api/analyzer/spectrum/display` | Visualization-ready spectrum data |
| `POST /api/analyzer/modes/visualize` | Mode shape rendering data |
| `GET /api/analyzer/references` | List reference instruments |
| `GET /api/analyzer/health` | Module health check |

---

## CI Enforcement

Add to boundary checker:

```python
# ci/check_package_boundaries.py
ALLOWED_IMPORTS["analyzer"] = ["core", "calculators"]
FORBIDDEN_IMPORTS["analyzer"] = ["cam", "rmos", "saw_lab", "tap_tone_pi", "tap_tone"]
```

---

## Migration from tap_tone_pi

Code to move from tap_tone_pi → this module:

| Source | Target |
|--------|--------|
| `analyzer/` (27K LOC) | `app/analyzer/` |
| `analyzer/widgets/` (69K LOC) | `packages/client/components/analyzer/` |
| `analyzer/reports/` (28K LOC) | `app/analyzer/reports/` |
| Any "recommendation" logic | `app/analyzer/design_advisor.py` |

Code that stays in tap_tone_pi:

| Keep | Reason |
|------|--------|
| `tap_tone_pi/` core | Pure DSP |
| `modes/` | Capture modes |
| `tap_tone_pi/wolf/` | Computes WSI (the number) |
| `tap_tone_pi/transfer_function/` | Pure math |
| `contracts/viewer_pack_v1.schema.json` | The interface |

---

*Boundary specification enforced via code review and CI checks.*
