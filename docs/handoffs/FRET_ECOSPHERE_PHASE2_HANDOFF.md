# Fretboard Ecosphere — Phase 2 Developer Handoff

**Date:** 2026-04-29  
**Sprint:** FRET-A (Fretboard Ecosphere)  
**Phase 1 Status:** COMPLETE  
**Phase 2 Status:** NOT STARTED  
**Branch:** `sprint/fret-ecosphere-a`

---

## Executive Summary

Phase 1 delivered a canonical Pydantic-validated schema for fret geometry (`FretboardEcosphere`). Phase 2 should expose this via API endpoints and integrate with the existing fret slots router.

---

## What Was Delivered (Phase 1)

### New Files

| File | Lines | Purpose |
|------|-------|---------|
| `services/api/app/instrument_geometry/neck/fretboard_ecosphere.py` | 596 | Canonical schema |
| `services/api/tests/test_fretboard_ecosphere.py` | 320 | 24 passing tests |

### Schema Components

```
FretboardInput (Pydantic BaseModel)
├── scale_type: ScaleType (STANDARD | MULTISCALE)
├── scale_length_mm: float (primary/treble scale)
├── bass_scale_length_mm: Optional[float]
├── string_count: int (1-18)
├── fret_count: int (1-36)
├── perpendicular_fret: int (multiscale only)
├── temperament: TemperamentType (EQUAL_12, EQUAL_19, etc.)
├── nut_width_mm / heel_width_mm: float
├── radius: RadiusSpec (compound radius support)
├── intonation_offsets_mm: Dict[int, float]
└── extension_mm: float

FretboardEcosphere (computed output)
├── input_params: FretboardInput (echo for traceability)
├── fret_lines: List[FretLine] (each fret's geometry)
├── string_paths: List[StringPath] (nut-to-bridge paths)
├── outline_points: List[Tuple[float, float]]
├── total_length_mm / max_width_mm / max_fret_angle_deg
└── Methods:
    ├── compute(params) → FretboardEcosphere (factory)
    ├── perpendicular_distance(fret, string) → float
    ├── to_scala_intervals() → List[float]
    ├── get_fret_line(n) → FretLine
    └── get_string_path(n) → StringPath
```

### Key Design Decisions

1. **Immutable after compute** — All Pydantic models use `frozen = True`
2. **Self-contained math** — Schema has its own fret position calculations (see Known Issues)
3. **FretFind2D parity** — `perpendicular_distance()` and `to_scala_intervals()` implemented

---

## Known Issues / Technical Debt

### Math Duplication (SPRINTS.md entry exists)

The schema implements `_fret_position_temperament()` internally, duplicating logic from `fret_math.py::compute_fret_positions_mm()`.

**Current state:**
- Equal temperaments (12/19/24/31-TET) work correctly
- Non-equal temperaments (Pythagorean, Just, Meantone) silently fall back to 12-TET
- `scala_loader.py` does not exist

**Resolution paths:**
- **Path 1:** Extend `fret_math.py` with temperament support, create `scala_loader.py`, refactor schema to delegate
- **Path 2:** Document limitation in API responses, defer refactor

### No Integration with Existing Router

The existing `fret_slots_router.py` uses the old `FretboardSpec` dataclass. The new `FretboardEcosphere` is not yet wired in.

---

## Phase 2 Objectives

### Primary Goal
Expose `FretboardEcosphere` via REST API endpoints.

### Suggested Endpoints

```
POST /api/fretboard/compute
  Request: FretboardInput (JSON)
  Response: FretboardEcosphere (JSON)

GET /api/fretboard/presets
  Response: List of common configurations (Fender, Gibson, etc.)

POST /api/fretboard/export/dxf
  Request: FretboardInput
  Response: DXF file (binary)

POST /api/fretboard/export/scala
  Request: FretboardInput
  Response: .scl file (text)
```

### Integration Points

1. **New router:** Create `services/api/app/routers/fretboard_ecosphere_router.py`
2. **Register in:** `services/api/app/router_registry/manifest.py` (or loader)
3. **DXF export:** Use `app.cam.dxf_writer.DxfWriter` (R12 default)

---

## Existing Code to Understand

### Fret Math Kernel
```
services/api/app/instrument_geometry/neck/fret_math.py
├── compute_fret_positions_mm(scale, count) → List[float]
├── compute_fret_spacing_mm(scale, count) → List[float]
├── compute_multiscale_fret_positions_mm(...) → List[List[FanFretPoint]]
├── compute_fan_fret_positions(...) → List[FanFretPointLegacy]  # DEPRECATED
└── SCALE_LENGTHS_MM, RADIUS_VALUES_MM (presets)
```

### Existing Fret Slots Router
```
services/api/app/cam/routers/fret_slots_router.py
├── POST /fret_slots/preview
└── Uses: FretboardSpec (dataclass), generate_fret_slot_toolpaths()
```

### DXF Writer (use this for exports)
```
services/api/app/cam/dxf_writer.py
├── DxfWriter(layers, version="R12")
├── add_polyline(layer, points, closed)
├── add_line(layer, start, end)
├── to_bytes() → bytes
└── saveas(path)
```

---

## How to Run Tests

```bash
# From repo root, use Python 3.13 (3.14 has numpy issues)
cd services/api

# Run just the ecosphere tests
python -m pytest tests/test_fretboard_ecosphere.py -v

# Run all tests (takes ~45 min)
python -m pytest tests/ -v
```

**Python path (Windows):**
```
C:\Users\thepr\AppData\Local\Programs\Python\Python313\python.exe
```

---

## Branch State

```
sprint/fret-ecosphere-a
├── 9d37f1ea feat(fretboard): add FretboardEcosphere canonical schema
└── 3d5f0f30 docs(sprints): add FRET-A schema/kernel duplication backlog entry

2 commits ahead of main
```

### Baseline Test Results (post-PR-10 main)
- **35 failed** (pre-existing, not related to fret work)
- **4518 passed**
- **38 skipped**

---

## File Tree Reference

```
services/api/app/instrument_geometry/
├── neck/
│   ├── fretboard_ecosphere.py   ← NEW (Phase 1)
│   ├── fret_math.py             ← Existing kernel
│   └── neck_profiles.py         ← FretboardSpec dataclass
├── body/
│   └── fretboard_geometry.py    ← Outline/slot line functions
└── models.py                    ← InstrumentModelId enum

services/api/app/cam/
├── dxf_writer.py                ← Use for DXF export
└── routers/
    └── fret_slots_router.py     ← Existing CAM router

services/api/tests/
└── test_fretboard_ecosphere.py  ← NEW (Phase 1)
```

---

## Quick Start for Phase 2

1. **Read the schema:** `services/api/app/instrument_geometry/neck/fretboard_ecosphere.py`
2. **Run tests:** Verify 24 tests pass
3. **Create router:** New file at `services/api/app/routers/fretboard_ecosphere_router.py`
4. **Wire compute endpoint:** Accept `FretboardInput`, return `FretboardEcosphere.compute(params)`
5. **Add DXF export:** Use `DxfWriter` to draw fret lines and outline
6. **Register router:** Add to router registry

---

## Contacts / References

- **CLAUDE.md:** Project instructions and constraints
- **SPRINTS.md:** Backlog items including the math duplication issue
- **PR #10:** DXF dual-format resolution (merged 2026-04-29)

---

**Generated:** 2026-04-29
