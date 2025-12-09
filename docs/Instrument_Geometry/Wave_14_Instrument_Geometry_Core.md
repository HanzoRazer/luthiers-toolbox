# Wave 14: Instrument Geometry Core

**Status:** ✅ Implemented  
**Date:** January 2025  
**Branch:** `feature/client-migration`

---

## 🎯 Overview

Wave 14 delivers a comprehensive **19-model instrument geometry architecture** with:

- **Full directory reorganization** (Option A migration pattern)
- **InstrumentModelId enum** with 19 guitar/bass/ukulele models
- **JSON-based model registry** with caching and status tracking
- **Per-model stub files** ready for expansion with real geometry data
- **FastAPI router** with model listing, status, and geometry calculation endpoints
- **Backward-compatible shims** preserving all existing imports

---

## 📁 New Directory Structure

```
services/api/app/instrument_geometry/
├── __init__.py              # Wave 14 exports + backward compat
├── models.py                # InstrumentModelId (19 models) + InstrumentModelStatus enums
├── registry.py              # JSON-loading registry with caching
├── instrument_model_registry.json   # Model metadata (267 lines)
│
├── neck/                    # Neck calculations
│   ├── __init__.py
│   ├── fret_math.py         # (moved from scale_length.py)
│   ├── neck_profiles.py     # (moved from profiles.py)
│   └── radius_profiles.py   # (moved)
│
├── body/                    # Body geometry
│   ├── __init__.py
│   ├── fretboard_geometry.py  # (moved)
│   └── outlines.py          # Body outline generation (Wave 14 new)
│
├── bridge/                  # Bridge/saddle calculations
│   ├── __init__.py
│   ├── geometry.py          # (moved from bridge_geometry.py)
│   ├── placement.py         # Bridge placement (Wave 14 new)
│   └── compensation.py      # Intonation compensation (Wave 14 new)
│
├── bracing/                 # Acoustic bracing patterns
│   ├── __init__.py
│   ├── x_brace.py           # X-bracing for steel-string
│   └── fan_brace.py         # Fan bracing for classical
│
├── guitars/                 # Per-model stub files (19 total)
│   ├── __init__.py
│   ├── strat.py             # Fender Stratocaster
│   ├── tele.py              # Fender Telecaster
│   ├── les_paul.py          # Gibson Les Paul
│   ├── sg.py                # Gibson SG
│   ├── es_335.py            # Gibson ES-335
│   ├── flying_v.py          # Gibson Flying V
│   ├── explorer.py          # Gibson Explorer
│   ├── firebird.py          # Gibson Firebird
│   ├── moderne.py           # Gibson Moderne
│   ├── prs.py               # PRS Custom 24
│   ├── dreadnought.py       # Martin D-28 style
│   ├── om_000.py            # Martin OM/000
│   ├── j_45.py              # Gibson J-45
│   ├── jumbo_j200.py        # Gibson J-200
│   ├── gibson_l_00.py       # Gibson L-00
│   ├── classical.py         # Classical/Spanish
│   ├── jazz_bass.py         # Fender Jazz Bass
│   ├── archtop.py           # Jazz Archtop
│   └── ukulele.py           # Soprano Ukulele
│
└── [Compatibility Shims - root level]
    ├── scale_length.py      # → re-exports from neck.fret_math
    ├── profiles.py          # → re-exports from neck.neck_profiles
    ├── fretboard_geometry.py # → re-exports from body.fretboard_geometry
    ├── radius_profiles.py   # → re-exports from neck.radius_profiles
    └── bridge_geometry.py   # → re-exports from bridge.geometry
```

---

## 🎸 The 19 Models

### Electric Guitars (10)
| Model | ID | Manufacturer | Status |
|-------|-----|--------------|--------|
| Stratocaster | `stratocaster` | Fender | STUB |
| Telecaster | `telecaster` | Fender | STUB |
| Les Paul | `les_paul` | Gibson | STUB |
| SG | `sg` | Gibson | STUB |
| ES-335 | `es_335` | Gibson | STUB |
| Flying V | `flying_v` | Gibson | STUB |
| Explorer | `explorer` | Gibson | STUB |
| Firebird | `firebird` | Gibson | STUB |
| Moderne | `moderne` | Gibson | STUB |
| PRS Custom 24 | `prs` | PRS | STUB |

### Acoustic Guitars (6)
| Model | ID | Manufacturer | Status |
|-------|-----|--------------|--------|
| Dreadnought | `dreadnought` | Martin | STUB |
| OM/000 | `om_000` | Martin | STUB |
| J-45 | `j_45` | Gibson | STUB |
| Jumbo J-200 | `jumbo_j200` | Gibson | STUB |
| L-00 | `gibson_l_00` | Gibson | STUB |
| Classical | `classical` | Various | STUB |

### Other (3)
| Model | ID | Category | Status |
|-------|-----|----------|--------|
| Jazz Bass | `jazz_bass` | Bass | STUB |
| Archtop | `archtop` | Electric | STUB |
| Ukulele | `ukulele` | Other | STUB |

---

## 🔌 API Endpoints

**Base URL:** `/api/instrument_geometry`

### Model Registry

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/models` | GET | List all models (optional filters: `status`, `category`) |
| `/models/{model_id}` | GET | Get detailed model info |
| `/status` | GET | Summary of model implementation status |
| `/enums/model_ids` | GET | List all InstrumentModelId enum values |
| `/enums/statuses` | GET | List all InstrumentModelStatus enum values |

### Geometry Calculations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/frets/positions` | POST | Calculate fret positions for scale length |
| `/fretboard/outline` | POST | Generate fretboard outline polygon |
| `/bridge/placement` | POST | Calculate bridge and saddle positions |
| `/radius/at_fret` | POST | Compound radius at specific fret |

---

## 🚀 Usage Examples

### List All Models
```bash
curl http://localhost:8000/api/instrument_geometry/models
```

**Response:**
```json
{
  "count": 19,
  "models": [
    {"id": "stratocaster", "name": "Fender Stratocaster", "category": "electric", "status": "STUB"},
    {"id": "telecaster", "name": "Fender Telecaster", "category": "electric", "status": "STUB"},
    ...
  ]
}
```

### Filter by Category
```bash
curl "http://localhost:8000/api/instrument_geometry/models?category=acoustic"
```

### Get Model Details
```bash
curl http://localhost:8000/api/instrument_geometry/models/les_paul
```

**Response:**
```json
{
  "id": "les_paul",
  "name": "Gibson Les Paul",
  "category": "electric",
  "subcategory": "solid_body",
  "manufacturer": "Gibson",
  "status": "STUB",
  "description": "Iconic solid-body electric with set neck and dual humbuckers",
  "spec": {
    "scale_length_mm": 628.65,
    "nut_width_mm": 43.05,
    "num_frets": 22
  }
}
```

### Calculate Fret Positions
```bash
curl -X POST http://localhost:8000/api/instrument_geometry/frets/positions \
  -H "Content-Type: application/json" \
  -d '{"scale_length_mm": 648.0, "num_frets": 22}'
```

**Response:**
```json
{
  "scale_length_mm": 648.0,
  "num_frets": 22,
  "compensation_mm": 0.0,
  "positions_mm": [36.3867, 70.6155, 102.8265, ...],
  "spacings_mm": [36.3867, 34.2288, 32.2110, ...]
}
```

### Status Summary
```bash
curl http://localhost:8000/api/instrument_geometry/status
```

**Response:**
```json
{
  "total_models": 19,
  "by_status": {"PRODUCTION": 0, "PARTIAL": 0, "STUB": 19},
  "by_category": {"electric": 10, "acoustic": 6, "bass": 1, "other": 2}
}
```

---

## 📦 Backward Compatibility

All existing imports continue to work via compatibility shims:

```python
# Old import paths (still work)
from instrument_geometry.profiles import InstrumentSpec
from instrument_geometry.scale_length import compute_fret_positions_mm
from instrument_geometry.bridge_geometry import compute_bridge_location_mm

# New import paths (preferred)
from instrument_geometry.neck import InstrumentSpec
from instrument_geometry.neck import compute_fret_positions_mm
from instrument_geometry.bridge import compute_bridge_location_mm
```

---

## 🧪 Smoke Test

```powershell
# Start API server
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Test endpoints
Invoke-RestMethod -Uri "http://localhost:8000/api/instrument_geometry/models" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/instrument_geometry/status" -Method GET
Invoke-RestMethod -Uri "http://localhost:8000/api/instrument_geometry/models/stratocaster" -Method GET
```

---

## 🎯 Model Status Legend

| Status | Description |
|--------|-------------|
| `PRODUCTION` | Fully implemented with real geometry data |
| `PARTIAL` | Some geometry implemented, others pending |
| `STUB` | Placeholder with minimal default values |
| `DEPRECATED` | Being phased out |
| `EXPERIMENTAL` | Under active development |

---

## 🔧 Extending a Model

To upgrade a stub to production:

1. **Edit the guitar file** (e.g., `guitars/strat.py`)
2. **Add real dimensions** to `MODEL_INFO["default_spec"]`
3. **Update status** to `PARTIAL` or `PRODUCTION`
4. **Update JSON registry** (`instrument_model_registry.json`)

Example:
```python
# guitars/strat.py
MODEL_INFO = {
    "id": "stratocaster",
    "status": "PRODUCTION",  # Changed from STUB
    "default_spec": {
        "scale_length_mm": 648.0,        # Real value
        "nut_width_mm": 42.86,           # Real value (1.687")
        "width_at_12th_fret_mm": 52.39,  # Real value
        "num_frets": 22,
        "nut_radius_mm": 241.3,          # 9.5" radius
        "heel_radius_mm": 355.6,         # 14" compound
    }
}
```

---

## 📋 Implementation Checklist

- [x] Create new folders (`neck/`, `body/`, `bridge/`, `bracing/`, `guitars/`)
- [x] Move existing files to new locations
- [x] Create compatibility shims at old paths
- [x] Create `models.py` with 19-model enum
- [x] Create `registry.py` with JSON-loading and caching
- [x] Create `instrument_model_registry.json` (267 lines)
- [x] Create all 19 guitar stub files
- [x] Create Wave 14 new modules (`outlines.py`, `placement.py`, `compensation.py`, `x_brace.py`, `fan_brace.py`)
- [x] Create `instrument_geometry_router.py`
- [x] Register router in `main.py`
- [x] Create documentation
- [ ] Git commit

---

## 📚 See Also

- [WAVE_14_DIFFERENCE_REPORT.md](./WAVE_14_DIFFERENCE_REPORT.md) - Migration analysis
- [copilot-instructions.md](../../.github/copilot-instructions.md) - Project coding standards
- [AGENTS.md](../../AGENTS.md) - Codex agent guidance

---

**Status:** ✅ Wave 14 Implementation Complete  
**Models:** 19 (all STUB, ready for expansion)  
**Backward Compatible:** Yes (via shims)
