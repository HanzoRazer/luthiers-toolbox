# Architecture Invariants

**Luthier's Toolbox - Placement Constitution**
**Version:** 1.0
**Date:** December 20, 2025

---

## Read This First

This document defines **where code goes**. Before writing any new code, consult this 6-layer map. Violations will be caught by CI governance tests.

---

## The 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LUTHIER'S TOOLBOX ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 6: ROUTERS                                                           │
│  ─────────────────                                                          │
│  Location: app/routers/                                                     │
│  Purpose:  HTTP handling ONLY                                               │
│  Contains: Request parsing, response formatting, validation                 │
│  NEVER:    Math, business logic, database queries                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  @router.post("/calculate")                                          │   │
│  │  async def calculate(request: Request):                              │   │
│  │      result = service.do_calculation(request.params)  # DELEGATE     │   │
│  │      return {"result": result}                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  LAYER 5: ORCHESTRATION (services/)                                        │
│  ───────────────────────────────────                                        │
│  Location: app/services/                                                    │
│  Purpose:  Cross-domain coordination                                        │
│  Contains: Workflow orchestration, domain bridges                           │
│  NEVER:    Math formulas, HTTP handling                                    │
│                                                                             │
│  Examples:                                                                  │
│  • saw_lab_service.py      - Saw Lab → RMOS coordination                   │
│  • rmos_run_service.py     - Run artifact workflows                        │
│  • rosette_cam_bridge.py   - Art Studio → CAM bridge                       │
│                                                                             │
│                                    │                                        │
│                                    ▼                                        │
│  LAYER 4: DOMAIN MODULES                                                    │
│  ────────────────────────                                                   │
│  Location: app/rmos/, app/saw_lab/, app/cam/                               │
│  Purpose:  Self-contained domain logic                                      │
│  Contains: Domain schemas, stores, domain-specific calculations            │
│  NEVER:    Cross-domain imports (use services/ for that)                   │
│                                                                             │
│  Examples:                                                                  │
│  • rmos/runs_v2/           - Run artifact persistence                      │
│  • saw_lab/risk_evaluator  - Saw risk calculations                         │
│  • cam/biarc_math.py       - CAM-specific arc math                         │
│                                                                             │
│                                    │                                        │
│                                    ▼                                        │
│  LAYER 3: CALCULATORS                                                       │
│  ─────────────────────                                                      │
│  Location: app/calculators/                                                 │
│  Purpose:  Domain-specific calculation orchestration                        │
│  Contains: Calculator classes that combine math modules                     │
│  NEVER:    Duplicate formulas (delegate to math modules)                   │
│                                                                             │
│  Examples:                                                                  │
│  • fret_slots_cam.py       - Fret slot CAM calculations                    │
│  • inlay_calc.py           - Inlay position calculations                   │
│  • bracing_calc.py         - Bracing calculations                          │
│                                                                             │
│                                    │                                        │
│                                    ▼                                        │
│  LAYER 2: INSTRUMENT GEOMETRY                                               │
│  ─────────────────────────────                                              │
│  Location: app/instrument_geometry/                                         │
│  Purpose:  Instrument-specific pure math                                    │
│  Contains: Fret, bridge, body, neck calculations                           │
│  NEVER:    HTTP, database, cross-domain imports                            │
│                                                                             │
│  Examples:                                                                  │
│  • neck/fret_math.py       - Fret position formulas                        │
│  • body/parametric.py      - Body outline generation                       │
│  • bridge/geometry.py      - Bridge geometry                               │
│                                                                             │
│                                    │                                        │
│                                    ▼                                        │
│  LAYER 1: GEOMETRY (Pure Math)                                              │
│  ──────────────────────────────                                             │
│  Location: app/geometry/                                                    │
│  Purpose:  General-purpose pure math functions                              │
│  Contains: Arc, circle, point, vector operations                           │
│  NEVER:    Domain knowledge, HTTP, database                                │
│                                                                             │
│  Examples:                                                                  │
│  • arc_utils.py            - Arc tessellation, circle generation           │
│  • (future) vector_utils   - Vector operations                             │
│  • (future) transform      - Coordinate transformations                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Table

| Layer | Folder | What Goes Here | What NEVER Goes Here |
|-------|--------|----------------|---------------------|
| 6 | `routers/` | HTTP handling, request/response | Math, business logic |
| 5 | `services/` | Cross-domain orchestration | Math, HTTP handling |
| 4 | `rmos/`, `saw_lab/`, `cam/` | Domain logic, schemas | Cross-domain imports |
| 3 | `calculators/` | Calculation orchestration | Duplicate formulas |
| 2 | `instrument_geometry/` | Instrument math | HTTP, database |
| 1 | `geometry/` | Pure math functions | Domain knowledge |

---

## The 5 Hard Rules

These rules are enforced by CI tests in `tests/test_route_governance.py`.

### Rule 1: No Math in Routers (Fortran Rule)

```python
# WRONG - math in router
@router.post("/fret")
async def calculate(req):
    position = scale_length * (1 - 2 ** (-fret / 12))  # NO!
    return {"position": position}

# RIGHT - delegate to math module
@router.post("/fret")
async def calculate(req):
    position = fret_math.compute_fret_position(scale_length, fret)  # YES!
    return {"position": position}
```

**Enforcement:** `TestFortranRule.test_no_inline_math_in_routers`

---

### Rule 2: No Hardcoded Pi

```python
# WRONG
circumference = 2 * 3.14159 * radius  # NO!

# RIGHT
import math
circumference = 2 * math.pi * radius  # YES!
```

**Enforcement:** `TestFortranRule.test_no_hardcoded_pi`

---

### Rule 3: Cross-Domain Glue Goes in services/

```python
# WRONG - saw_lab importing rmos directly
# saw_lab/some_module.py
from ..rmos.runs_v2 import persist_run  # NO!

# RIGHT - use services/ for cross-domain
# services/saw_lab_service.py
from ..saw_lab.risk_evaluator import evaluate_risk
from ..rmos.runs_v2 import persist_run
# Orchestrate here
```

---

### Rule 4: Domain Modules Are Self-Contained

Each domain module (`rmos/`, `saw_lab/`, `cam/`) should:
- Own its schemas
- Own its storage
- Own its domain-specific calculations
- NOT import from other domain modules

---

### Rule 5: Required Invariants Enforced

RMOS run artifacts require:
- `hashes.feasibility_sha256` - Hash of server-computed feasibility
- `decision.risk_level` - Safety classification

Missing fields → BLOCKED artifact created (audit trail preserved).

**Enforcement:** `validate_and_persist()` in `rmos/runs_v2/store.py`

---

## Where Does My Code Go?

### Decision Tree

```
Is it pure math (sin, cos, arc, circle)?
├── YES → geometry/arc_utils.py (Layer 1)
│
└── NO → Is it instrument-specific math (fret, bridge, body)?
    ├── YES → instrument_geometry/{domain}/ (Layer 2)
    │
    └── NO → Is it a calculation that combines math modules?
        ├── YES → calculators/ (Layer 3)
        │
        └── NO → Is it domain-specific logic (RMOS, Saw Lab)?
            ├── YES → {domain}/ (Layer 4)
            │
            └── NO → Does it coordinate multiple domains?
                ├── YES → services/ (Layer 5)
                │
                └── NO → Is it HTTP request/response handling?
                    ├── YES → routers/ (Layer 6)
                    │
                    └── NO → Ask before proceeding
```

---

## Examples by Type

### Adding a New Math Function

**Scenario:** Need a function to calculate arc length from chord and height.

**Answer:** `geometry/arc_utils.py` (Layer 1)

```python
# geometry/arc_utils.py
def arc_length_from_chord_and_height(chord: float, height: float) -> float:
    """Calculate arc length from chord length and sagitta (height)."""
    # Pure math, no domain knowledge
    ...
```

---

### Adding a New Fret Calculation

**Scenario:** Need a function for multi-scale fret positions.

**Answer:** `instrument_geometry/neck/fret_math.py` (Layer 2)

```python
# instrument_geometry/neck/fret_math.py
def compute_multiscale_fret_positions(
    bass_scale_mm: float,
    treble_scale_mm: float,
    num_frets: int,
) -> List[Tuple[float, float]]:
    """Calculate fret positions for fanned fret layout."""
    # Instrument-specific math
    ...
```

---

### Adding a New API Endpoint

**Scenario:** Need endpoint for saw operation preview.

**Answer:** `routers/saw_router.py` (Layer 6) + `services/saw_lab_service.py` (Layer 5)

```python
# routers/saw_router.py
@router.post("/preview")
async def preview_saw_op(request: SawRequest):
    # ONLY HTTP handling
    result = saw_lab_service.evaluate_saw_operation(
        blade_diameter_mm=request.blade_diameter,
        ...
    )
    return {"feasibility": result}
```

---

### Adding Cross-Domain Integration

**Scenario:** Need to connect Art Studio rosette to CAM pipeline.

**Answer:** `services/rosette_cam_bridge.py` (Layer 5)

```python
# services/rosette_cam_bridge.py
from ..art_studio.rosette_calc import calculate_rosette
from ..cam.adaptive_core import generate_toolpath

def rosette_to_toolpath(rosette_params):
    """Bridge Art Studio rosette to CAM toolpath."""
    geometry = calculate_rosette(rosette_params)
    return generate_toolpath(geometry)
```

---

## Governance Tests

Run before every PR:

```bash
pytest tests/test_route_governance.py -v
```

| Test | What It Checks |
|------|----------------|
| `test_no_scattered_fret_routes` | Fret endpoints consolidated |
| `test_no_double_api_prefix` | No `/api/api/` bugs |
| `test_fret_design_consolidated` | No duplicate fret endpoints |
| `test_fret_router_paths_stable` | API stability |
| `test_no_inline_math_in_routers` | Fortran Rule enforcement |
| `test_no_hardcoded_pi` | No `3.14159` literals |

---

## Violation Resolution

If governance tests fail:

1. **Identify the layer** your code belongs in
2. **Move the code** to the correct location
3. **Update imports** in calling code
4. **Add to exceptions** only if grandfathered (with TODO)

```python
# test_route_governance.py
FORTRAN_RULE_EXCEPTIONS = {
    "legacy_router.py",  # TODO: Extract math to geometry/
}
```

---

## Summary

| Principle | Implementation |
|-----------|----------------|
| "All math in subroutines" | Layers 1-2 contain math |
| "Separation of concerns" | 6 distinct layers |
| "Single responsibility" | Each layer has one job |
| "Don't repeat yourself" | Canonical modules, no duplication |
| "Testable in isolation" | Pure functions in Layers 1-2 |

---

*This document is the source of truth for code placement.*
*Consult before adding new code. Update when architecture evolves.*
