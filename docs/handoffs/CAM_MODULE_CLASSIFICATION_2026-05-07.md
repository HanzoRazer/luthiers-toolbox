# CAM Module Classification — 2026-05-07

**Date:** 2026-05-07  
**Auditor:** Claude (CAM Dev Order 4A)  
**Scope:** All CAM, export, and machine-adjacent modules

---

## Classification Definitions

| Classification | Definition |
|----------------|------------|
| **Canonical** | Production code, actively maintained, documented coordinate system |
| **Candidate** | Working code, potential for production, needs governance review |
| **Legacy** | Old code, superseded or deprecated, may still be imported |
| **Experimental** | Sandbox/prototype, not for production use |
| **Library** | Utility code with no coordinate assumptions |
| **Unknown** | Classification pending deeper investigation |

---

## Tier 1 Deep Audit — Nut Slot CAM

### `services/api/app/cam/nut_slot_cam.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | 667 |
| Units | mm only |
| Coordinate system | Documented (origin: left face of nut, Z-zero: top of stock) |
| Output format | Toolpath JSON (preview only) |
| Safety model | GREEN/YELLOW/RED gates, structured issues |
| Tests | 78 tests in `test_nut_slot_cam.py` |
| Ownership | CAM Dev Order 1 + 2B |

**Evidence:**
- Docstring lines 8-14 document coordinate system explicitly
- Gate evaluation covers depth, tool, positions, spacing
- Integrity validation checks move sequences
- Status field explicitly marks as "experimental"

---

### `services/api/app/routers/cam/nut_slot_router.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | 47 |
| Endpoint | `POST /api/cam/nut-slot/preview` |
| Units | Inherited from nut_slot_cam.py |
| Coordinate system | Documented in endpoint docstring |
| Tests | Covered by test_nut_slot_cam.py endpoint tests |

---

### `services/api/app/calculators/nut_slot_calc.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | 261 |
| Purpose | Slot depth calculation from string gauge + fret crown |
| Units | mm (internal), inches (gauge input) |
| Coordinate system | N/A (calculator, not toolpath) |
| Tests | None dedicated (should add) |

---

## Tier 1 Deep Audit — Router Manifest

### `services/api/app/router_registry/manifests/cam_manifest.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | 262 |
| Router count | 41 CAM-related routers |
| Categories | cam_core, cam, config, saw_lab, misc, consolidated, cnc |

**Key entries:**
- `nut_slot_router` — registered at `/api/cam` prefix
- `fret_slots_router` — registered at `/api/cam` prefix
- `simulation_consolidated_router` — registered at `/api/cam/sim`
- `gcode_consolidated_router` — registered at `/cam/gcode`
- `saw_lab` — registered with empty prefix (self-prefixed)

---

## Tier 2 Classification — G-code Utilities

### `services/api/app/util/gcode/simulator.py`

| Property | Value |
|----------|-------|
| **Classification** | **LIBRARY** |
| Lines | 375 |
| Purpose | G-code state machine, travel calculation, backplot |
| Units | Supports mm (G21) and inch (G20) via modal state |
| Coordinate system | Passthrough — no assumptions imposed |
| Tests | 28 tests in `test_gcode_simulate.py` |

---

### `services/api/app/util/gcode/lexer.py`

| Property | Value |
|----------|-------|
| **Classification** | **LIBRARY** |
| Lines | 62 |
| Purpose | G-code line parsing |
| Coordinate system | N/A (parser, not generator) |

---

### `services/api/app/util/gcode/types.py`

| Property | Value |
|----------|-------|
| **Classification** | **LIBRARY** |
| Lines | 94 |
| Purpose | Shared type definitions (Move, Summary, Modal) |
| Coordinate system | Default modal uses mm |

---

### `services/api/app/util/gcode/geometry.py`

| Property | Value |
|----------|-------|
| **Classification** | **LIBRARY** |
| Purpose | Arc interpolation, distance calculations |

---

## Tier 2 Classification — Simulation Router

### `services/api/app/routers/simulation_consolidated_router.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | 273 |
| Endpoints | `/sim/gcode`, `/sim/upload`, `/sim/metrics` |
| Purpose | G-code simulation and metrics |
| Coordinate system | Passthrough — simulates whatever G-code provides |
| Tests | 8 xfail tests (metrics endpoint bug) |

**Note:** Metrics endpoint has known bug (schema mismatch). Working endpoints: `/sim/gcode`, `/sim/upload`.

---

### `services/api/app/routers/gcode_consolidated_router.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | ~100 |
| Endpoints | `/cam/gcode/plot.svg`, `/cam/gcode/estimate`, `/cam/gcode/simulate` |
| Purpose | Visualization and estimation |
| Coordinate system | Passthrough |

---

## Tier 2 Classification — Fret Slot CAM

### `services/api/app/cam/fret_slots_from_ecosphere.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | ~150 |
| Purpose | Bridge between FretboardEcosphere and CAM generators |
| Units | mm |
| Coordinate system | Inherited from ecosphere |
| Tests | `test_fret_slots_from_ecosphere.py` |

**Note:** Sprint FRET-CONSOLIDATION-1 deliverable. Canonical source for fret geometry.

---

### `services/api/app/calculators/fret_slots_cam.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Standard fret slot toolpath generation |
| Units | mm |
| Coordinate system | Documented (fretboard nut end origin) |

---

### `services/api/app/calculators/fret_slots_fan_cam.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Fan fret / multiscale slot toolpath generation |
| Units | mm |
| Coordinate system | Documented |

---

### `services/api/app/cam/routers/fret_slots_router.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Endpoints | Fret slot preview endpoints |
| Registered | Yes, in cam_manifest.py |

---

## Tier 2 Classification — DXF Utilities

### `services/api/app/cam/dxf_writer.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Lines | ~150 |
| Purpose | Central DXF output, dual-format (R12/R2000) |
| Coordinate precision | 3dp |
| Tests | Implicit via consumers |

---

### `services/api/app/util/dxf_compat.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANONICAL** |
| Purpose | Version-aware entity creation (LINE vs LWPOLYLINE) |
| Cross-ref | `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` |

---

### `services/api/app/services/layered_dxf_writer.py`

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Multi-layer DXF generation |

---

## Tier 2 Classification — Saw Lab

### `services/api/app/saw_lab/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Files | 65 Python files |
| Purpose | Bandsaw operation planning, risk evaluation, batch processing |
| Units | mm |
| Safety model | Risk evaluator, physics calculators |

**Notable components:**
- `risk_evaluator.py` — Safety risk scoring
- `toolpath_builder.py` — Saw toolpath generation
- `batch_gcode_router.py` — G-code batch generation
- `calculators/` — Physics (bite load, deflection, heat, kickback, rimspeed)

**Governance note:** Saw lab generates G-code via `batch_gcode_router.py`. This requires governance review before production use.

---

### `services/api/app/cam_core/saw_lab/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Files | 14 Python files |
| Purpose | Saw blade registry, learning, queue |

---

## Tier 2 Classification — Other CAM Modules

### `services/api/app/cam/rosette/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Rosette pattern generation, CNC toolpaths |
| Files | ~25 files |

---

### `services/api/app/cam/vcarve/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | V-carving toolpaths |

---

### `services/api/app/cam/profiling/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Profile toolpaths with holding tabs |

---

### `services/api/app/cam/binding/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Binding channel toolpaths |

---

### `services/api/app/cam/drilling/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Peck drilling cycles, drill patterns |

---

### `services/api/app/cam/headstock/` (directory)

| Property | Value |
|----------|-------|
| **Classification** | **CANDIDATE** |
| Purpose | Headstock inlay CAM |

---

## Summary Table

| Module | Classification | Units | Coord System | Tests |
|--------|---------------|-------|--------------|-------|
| nut_slot_cam.py | CANONICAL | mm | Documented | 78 |
| nut_slot_router.py | CANONICAL | mm | Documented | Yes |
| nut_slot_calc.py | CANONICAL | mm | N/A | None |
| fret_slots_from_ecosphere.py | CANONICAL | mm | Inherited | Yes |
| fret_slots_router.py | CANONICAL | mm | Documented | Yes |
| simulation_consolidated_router.py | CANONICAL | Passthrough | Passthrough | 8 xfail |
| gcode_consolidated_router.py | CANONICAL | Passthrough | Passthrough | Yes |
| dxf_writer.py | CANONICAL | mm | N/A | Implicit |
| util/gcode/*.py | LIBRARY | Both | Passthrough | 28 |
| fret_slots_cam.py | CANDIDATE | mm | Documented | TBD |
| fret_slots_fan_cam.py | CANDIDATE | mm | Documented | TBD |
| saw_lab/ | CANDIDATE | mm | TBD | TBD |
| rosette/ | CANDIDATE | mm | TBD | TBD |
| vcarve/ | CANDIDATE | mm | TBD | TBD |
| profiling/ | CANDIDATE | mm | TBD | TBD |
| binding/ | CANDIDATE | mm | TBD | TBD |
| drilling/ | CANDIDATE | mm | TBD | TBD |

---

## Risks Identified

### 1. Saw Lab G-code Generation

`batch_gcode_router.py` appears to generate G-code. Requires governance review before production.

### 2. Metrics Endpoint Bug

`simulation_consolidated_router.py` has 8 xfail tests for `/sim/metrics` endpoint. Schema mismatch needs fixing or endpoint removal.

### 3. CANDIDATE Modules Without Tests

Multiple CANDIDATE modules lack dedicated test coverage. Coordinate system documentation varies.

### 4. Coordinate System Variance

Not all CANDIDATE modules document their coordinate systems explicitly. Needs standardization.

---

## Recommendations

1. **Immediate:** Run existing CAM tests to verify baseline
2. **Short-term:** Add coordinate system metadata to all CANDIDATE modules
3. **Medium-term:** Add dedicated tests for CANDIDATE modules
4. **Long-term:** Implement governance gates before promoting CANDIDATE → CANONICAL

---

## Verification Commands

```bash
# Run all CAM tests
cd services/api
pytest tests/cam/ -v

# Count CAM router registrations
grep -c "RouterSpec" app/router_registry/manifests/cam_manifest.py

# Find G-code generators
grep -rn "def.*gcode\|gcode.*=\|G0\|G1" app/cam/ --include="*.py" | head -50

# Verify nut slot coordinate documentation
grep -n "Coordinate\|Origin\|Z-zero" app/cam/nut_slot_cam.py
```

---

*Classification completed: 2026-05-07*
