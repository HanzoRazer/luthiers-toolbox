# Project Instructions

## Overview
Luthiers Toolbox — CAD/CAM platform for guitar builders. FastAPI backend + Vue.js frontend.

## Code Style
- Python: PEP 8, type hints, dataclasses for data models
- Vue: Composition API, TypeScript
- Tests: pytest with TestClient for API endpoints

## Architecture

### Soundhole Type System (commit 985e2ad7)

Spiral soundhole is ONE OPTION in a dropdown, not a standalone tool.

**SoundholeType enum** (`app/calculators/soundhole_facade.py`):
- `ROUND` — traditional circular (default)
- `OVAL` — Selmer/Maccaferri elliptical
- `SPIRAL` — logarithmic spiral slot (Williams 2019)
- `FHOLE` — archtop f-holes

**SpiralParams dataclass** (`app/calculators/soundhole_facade.py`):
```python
@dataclass
class SpiralParams:
    slot_width_mm: float = 14.0      # 14-20mm optimal
    start_radius_mm: float = 10.0    # r0
    growth_rate_k: float = 0.18      # per radian
    turns: float = 1.1
    rotation_deg: float = 0.0
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
```

**Physics**:
- Spiral: `r(θ) = r0 × e^(k×θ)`
- P:A ratio: `2/slot_width` (closed form, independent of k/turns)
- Williams threshold: P:A > 0.10 mm⁻¹ for acoustic efficiency

**Endpoints**:
- `POST /api/instrument/soundhole` — `soundhole_type` field selects type
- `GET /api/instrument/soundhole/types` — returns types + spiral presets

**Presets** (`app/calculators/soundhole_presets.py`):
- `SPIRAL_PRESETS`: standard_14mm, compact_12mm, wide_18mm, carlos_jumbo_upper/lower
- `STANDARD_DIAMETERS_MM`: includes `carlos_jumbo: 102.0`
- `STANDARD_POSITION_FRACTION`: includes `carlos_jumbo: 0.52`

## Development Guidelines
- Use Python via Bash if Edit tool fails with "file unexpectedly modified"
- Run `pytest tests/test_soundhole*.py` to verify soundhole changes

## Testing
- 161 soundhole tests in `tests/test_soundhole*.py`
- Coverage threshold: 20%

## BLOCKING INFRASTRUCTURE — resolve before new DXF work

### DXF output standard (highest priority after Smart Guitar)

Every DXF generator in the repo calls ezdxf directly
with inconsistent settings. This caused Fusion 360 to
freeze and require a hard reset on smart_guitar_front_v3.dxf.

Required: services/api/app/cam/dxf_writer.py
  A single central DXF writer that ALL generators call.

Standards to enforce:
  - Format: AC1024 (R2010) minimum — never R2000
  - Entities: SPLINE or LINE only — never LWPOLYLINE
  - Header: valid EXTMIN/EXTMAX from actual geometry
  - Units: INSUNITS=4 (mm), MEASUREMENT=1 (metric)
  - Layers: named layers only, no geometry on layer 0

Existing generators that must be refactored to use it:
  - app/instrument_geometry/bridge/archtop_floating_bridge.py
  - app/instrument_geometry/soundhole/spiral_geometry.py
  - Any body outline or CAM generator using ezdxf directly

Rule: No new DXF generator may be built until
dxf_writer.py exists and existing generators are
refactored to use it.

Status: NOT STARTED
Priority: Blocking — ranks equal to Smart Guitar first article
