# Instrument Geometry Migration Plan  
**Scope:** Fret/scale/bridge/radius math for all instruments (flat-top, archtop, electric, etc.)  
**Owner:** Ross / ToolBox Core  
**Status:** Phase 2 Complete ✅

---

## 1. Purpose

This document defines how to migrate all **instrument geometry math** (fret positions, scale length, bridge location, radii, related calculators) into a **single, well-defined subsystem** inside the Luthier's ToolBox architecture.

Goals:

1. **Centralize** all instrument geometry formulas that are currently scattered across:
   - `neck_router.py`
   - Archtop modules
   - legacy `server/pipelines/` code
   - ad-hoc calculators and snippets
2. Define a dedicated `instrument_geometry` package with **pure math APIs** that can be used by:
   - RMOS 2.0
   - Art Studio
   - CAM / Toolpath engine
3. Create a **technical knowledge base** where underlying theory, references, and vendor/academic notes are stored and linked to the code.
   - Example: the saw-blade geometry article you found that explains how blade physics is derived from geometry.

---

## 2. Target Architecture (End State)

### 2.1 Package Layout ✅ IMPLEMENTED

```text
services/api/app/instrument_geometry/
  __init__.py              ✅ Package entry point with exports

  scale_length.py          ✅ fret positions, intonation offsets, spacing
  fretboard_geometry.py    ✅ outline, taper, slot lines, string spacing
  bridge_geometry.py       ✅ bridge location, height, compensation, saddle positions
  radius_profiles.py       ✅ radius curves, compound radius, arc points
  profiles.py              ✅ InstrumentSpec, FretboardSpec, BridgeSpec, RadiusProfile
```

### 2.2 Knowledge Base ✅ IMPLEMENTED

```text
docs/KnowledgeBase/
  README.md                                    ✅ Index and guidelines

  Instrument_Geometry/
    Fret_Scale_Theory.md                       ✅ 12th root of 2, equal temperament
    Bridge_Compensation_Notes.md               ✅ Intonation, saddle setback
    Radius_Theory_Compound.md                  ✅ Fretboard radius math
    Fretboard_Geometry.md                      (TODO: Phase 3)

  Saw_Physics/
    Saw_Blade_Geometry_Reference.md            (TODO: Phase 4)
    Vendor_Blade_Physics_Notes.md              (TODO: Phase 4)

  Materials/
    Wood_Properties_Tables.md                  (TODO: Phase 4)

  CAM/
    Feeds_Speeds_Theory.md                     (TODO: Phase 4)
```

---

## 3. API Reference

### scale_length.py

```python
compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]
compute_fret_spacing_mm(scale_length_mm: float, fret_count: int) -> List[float]
compute_compensated_scale_length_mm(scale_length_mm: float, saddle_comp_mm: float, nut_comp_mm: float = 0.0) -> float
compute_fret_to_bridge_mm(scale_length_mm: float, fret_number: int) -> float
compute_multiscale_fret_positions_mm(bass_scale_mm: float, treble_scale_mm: float, fret_count: int, string_count: int, perpendicular_fret: int = 0) -> List[List[Tuple[float, float]]]

# Constants
SCALE_LENGTHS_MM = {"fender_standard": 648.0, "gibson_standard": 628.65, ...}
RADIUS_VALUES_MM = {"vintage_fender": 184.15, "modern_fender": 241.3, ...}
```

### fretboard_geometry.py

```python
compute_fretboard_outline(nut_width_mm: float, heel_width_mm: float, scale_length_mm: float, fret_count: int, extension_mm: float = 0.0) -> List[Tuple[float, float]]
compute_width_at_position_mm(nut_width_mm: float, heel_width_mm: float, scale_length_mm: float, fret_count: int, position_mm: float) -> float
compute_fret_slot_lines(spec: FretboardSpec) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]
compute_string_spacing_at_position(...) -> List[float]
```

### bridge_geometry.py

```python
compute_bridge_location_mm(scale_length_mm: float) -> float
compute_saddle_positions_mm(scale_length_mm: float, compensations_mm: Dict[str, float]) -> Dict[str, float]
compute_bridge_height_profile(width_mm: float, string_count: int, radius_mm: Optional[float], base_height_mm: float) -> List[Tuple[float, float]]
compute_compensation_estimate(string_gauge_mm: float, is_wound: bool, action_mm: float = 2.0) -> float

# Constants
STANDARD_6_STRING_COMPENSATION = {"E6": 2.5, "A5": 2.0, ...}
STANDARD_4_STRING_BASS_COMPENSATION = {...}
```

### radius_profiles.py

```python
compute_compound_radius_at_fret(fret_index: int, total_frets: int, start_radius_mm: float, end_radius_mm: float) -> float
compute_radius_arc_points(radius_mm: float, width_mm: float, num_points: int = 50) -> List[Tuple[float, float]]
compute_radius_drop_mm(radius_mm: float, offset_mm: float) -> float
compute_string_height_at_fret(fretboard_radius_mm: float, string_position_mm: float, action_center_mm: float) -> float
```

### profiles.py (Dataclasses)

```python
@dataclass
class InstrumentSpec:
    instrument_type: str
    scale_length_mm: float
    fret_count: int
    string_count: int
    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None
    tuning: Optional[List[str]] = None
    multiscale: bool = False
    bass_scale_length_mm: Optional[float] = None
    treble_scale_length_mm: Optional[float] = None

@dataclass
class FretboardSpec:
    nut_width_mm: float
    heel_width_mm: float
    scale_length_mm: float
    fret_count: int
    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None
    extension_mm: float = 0.0

@dataclass
class BridgeSpec:
    scale_length_mm: float
    intonation_offsets_mm: Dict[str, float]
    base_height_mm: float
    radius_mm: Optional[float] = None
    is_floating: bool = False

@dataclass
class RadiusProfile:
    base_radius_mm: float
    end_radius_mm: Optional[float] = None
    custom_radii: Optional[Dict[int, float]] = None
```

---

## 4. Tests ✅ IMPLEMENTED

Test file: `services/api/app/tests/instrument_geometry/test_instrument_geometry.py`

**32 tests covering:**
- Fret positions (12th fret at half scale)
- Fret spacing (monotonically decreasing)
- Scale length compensation
- Profile dataclasses (compound radius detection, multiscale)
- Fretboard outline geometry
- Radius calculations (compound, drop, arc points)
- Bridge compensation

---

## 5. Phased Migration Strategy

### Phase 1 — Discovery & Inventory ✅ COMPLETE
- Identified scattered math in `neck_router.py`, Archtop modules, pipelines
- Created inventory of instrument-geometry-relevant files

### Phase 2 — Define API & Profiles ✅ COMPLETE
- Created `instrument_geometry` package with pure math functions
- Defined dataclasses for InstrumentSpec, FretboardSpec, BridgeSpec
- Created KnowledgeBase with theory documentation
- Added 32 comprehensive tests

### Phase 3 — Extract & Move Math (TODO)
- Replace inline formulas in `neck_router.py` with calls to instrument_geometry
- Update Archtop modules to use new APIs
- Remove legacy duplicate implementations

### Phase 4 — Integrate With RMOS 2.0 & Art Studio (TODO)
- Wire instrument_geometry into Art Studio instrument configuration
- Use in RMOS for design scoring and constraints
- Document directional workflow integration

---

## 6. Definition of Done

✅ All fret/scale/bridge/radius math lives in `services/api/app/instrument_geometry/`
✅ `docs/KnowledgeBase/Instrument_Geometry/*` contains the theory, with references
✅ Tests exist for scale length, fretboard outline, bridge compensation, radius profiles
⬜ `neck_router.py` and Archtop modules call into this package
⬜ RMOS 2.0 and Art Studio workflows use these APIs

---

## 7. Files Created

### Package Files
- `services/api/app/instrument_geometry/__init__.py`
- `services/api/app/instrument_geometry/profiles.py`
- `services/api/app/instrument_geometry/scale_length.py`
- `services/api/app/instrument_geometry/fretboard_geometry.py`
- `services/api/app/instrument_geometry/bridge_geometry.py`
- `services/api/app/instrument_geometry/radius_profiles.py`

### Knowledge Base
- `docs/KnowledgeBase/README.md`
- `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`
- `docs/KnowledgeBase/Instrument_Geometry/Bridge_Compensation_Notes.md`
- `docs/KnowledgeBase/Instrument_Geometry/Radius_Theory_Compound.md`

### Tests
- `services/api/app/tests/instrument_geometry/__init__.py`
- `services/api/app/tests/instrument_geometry/test_instrument_geometry.py`
