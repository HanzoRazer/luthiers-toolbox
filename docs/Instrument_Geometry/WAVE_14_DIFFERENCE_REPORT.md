# Wave 14 Difference Report: Existing vs Proposed Structure

**Generated:** 2025-01-XX  
**Purpose:** Compare existing `instrument_geometry/` implementation with Wave 14 skeleton  
**Decision Required:** Approve migration strategy before implementation

---

## Executive Summary

| Aspect | Existing (L.0) | Wave 14 Proposed | Migration Strategy |
|--------|----------------|------------------|-------------------|
| **Files** | 6 files (1,131 lines) | 30+ files (~2,500+ lines) | **Extend & Reorganize** |
| **Models** | 0 (type-agnostic) | 19 guitar models | **Add new** |
| **Enums** | 0 | 2 (`InstrumentModelId`, `InstrumentModelStatus`) | **Add new** |
| **Registry** | None | JSON-backed with caching | **Add new** |
| **Subfolders** | None | 5 (`guitars/`, `neck/`, `body/`, `bracing/`, `bridge/`) | **Add new** |
| **Router** | None | `instrument_geometry_router.py` | **Add new** |

**Recommendation:** The existing code is **complementary** to Wave 14, not conflicting. Existing functions (fret math, radius profiles, bridge geometry) should be **preserved and organized** into Wave 14's subfolder structure.

---

## Existing Structure Analysis

### Current Directory: `services/api/app/instrument_geometry/`

```
instrument_geometry/
├── __init__.py           (33 lines) - Package exports
├── scale_length.py       (259 lines) - Fret position math
├── profiles.py           (220 lines) - InstrumentSpec, FretboardSpec, BridgeSpec, RadiusProfile
├── fretboard_geometry.py (178 lines) - Outline, slots, string spacing
├── radius_profiles.py    (233 lines) - Compound radius, arc points, drops
├── bridge_geometry.py    (219 lines) - Bridge location, saddle positions, compensation
└── __pycache__/
```

**Total:** 6 files, ~1,131 lines of production code

---

## Detailed Existing Code Inventory

### 1. `__init__.py` (33 lines)
**Purpose:** Package exports  
**Exports:**
- `InstrumentSpec`, `FretboardSpec`, `BridgeSpec` (from profiles.py)
- `compute_fret_positions_mm`, `compute_fret_spacing_mm`, `compute_compensated_scale_length_mm` (from scale_length.py)

**Wave 14 Impact:** Will need updates to export new models/registry  
**Action:** ✏️ **Modify** - Add Wave 14 exports

---

### 2. `scale_length.py` (259 lines)
**Purpose:** Equal-tempered fret position calculations  
**Key Functions:**
| Function | Purpose | Keep? |
|----------|---------|-------|
| `compute_fret_positions_mm()` | Fret distances from nut | ✅ Keep |
| `compute_fret_spacing_mm()` | Inter-fret spacing | ✅ Keep |
| `compute_compensated_scale_length_mm()` | Saddle compensation | ✅ Keep |
| `compute_fret_to_bridge_mm()` | Fret-to-bridge distance | ✅ Keep |
| `compute_multiscale_fret_positions_mm()` | Fanned fret support | ✅ Keep |

**Constants:**
- `SEMITONE_RATIO` = 2^(1/12)
- `SCALE_LENGTHS_MM` dict (fender, gibson, prs, classical, etc.)
- `RADIUS_VALUES_MM` dict (vintage_fender, modern_fender, gibson, etc.)

**Wave 14 Impact:** This is **core fret math** - should move to `neck/fret_math.py`  
**Action:** 📁 **Move** to `neck/fret_math.py`

---

### 3. `profiles.py` (220 lines)
**Purpose:** High-level dataclasses for instrument descriptions  
**Key Classes:**
| Class | Purpose | Keep? |
|-------|---------|-------|
| `InstrumentSpec` | High-level instrument description | ✅ Keep |
| `FretboardSpec` | Fretboard geometric parameters | ✅ Keep |
| `BridgeSpec` | Bridge parameters (flat-top, archtop) | ✅ Keep |
| `RadiusProfile` | Single/compound radius description | ✅ Keep |

**Wave 14 Impact:** These are **generic specs** - Wave 14 adds **model-specific** registry on top  
**Action:** ✅ **Keep in place** - Wave 14's `models.py` adds enums, these remain as dataclasses

---

### 4. `fretboard_geometry.py` (178 lines)
**Purpose:** Fretboard outline and slot calculations  
**Key Functions:**
| Function | Purpose | Keep? |
|----------|---------|-------|
| `compute_fretboard_outline()` | 2D outline polygon | ✅ Keep |
| `compute_width_at_position_mm()` | Width at any position | ✅ Keep |
| `compute_fret_slot_lines()` | Slot start/end points | ✅ Keep |
| `compute_string_spacing_at_position()` | String Y-positions | ✅ Keep |

**Wave 14 Impact:** This is **neck geometry** - should move to `neck/` subfolder  
**Action:** 📁 **Move** to `neck/fret_geometry.py` (rename for clarity)

---

### 5. `radius_profiles.py` (233 lines)
**Purpose:** Radius arc calculations and compound radius support  
**Key Functions:**
| Function | Purpose | Keep? |
|----------|---------|-------|
| `compute_compound_radius_at_fret()` | Radius at specific fret | ✅ Keep |
| `compute_radius_arc_points()` | Arc point generation | ✅ Keep |
| `compute_radius_drop_mm()` | Height drop at offset | ✅ Keep |
| `compute_fret_crown_height_mm()` | Crown height calculation | ✅ Keep |
| `compute_string_height_at_fret()` | String height w/ radius | ✅ Keep |
| `generate_compound_radius_profile()` | RadiusProfile factory | ✅ Keep |
| `inches_to_mm()` / `mm_to_inches()` | Unit conversion | ✅ Keep |

**Wave 14 Impact:** This is **neck profile math** - should move to `neck/neck_profiles.py`  
**Action:** 📁 **Move** to `neck/neck_profiles.py`

---

### 6. `bridge_geometry.py` (219 lines)
**Purpose:** Bridge placement and saddle compensation  
**Key Functions:**
| Function | Purpose | Keep? |
|----------|---------|-------|
| `compute_bridge_location_mm()` | Theoretical bridge position | ✅ Keep |
| `compute_saddle_positions_mm()` | Per-string saddle positions | ✅ Keep |
| `compute_bridge_height_profile()` | Radiused bridge heights | ✅ Keep |
| `compute_archtop_bridge_placement()` | Archtop-specific placement | ✅ Keep |
| `compute_compensation_estimate()` | Intonation estimation | ✅ Keep |

**Constants:**
- `STANDARD_6_STRING_COMPENSATION` dict
- `STANDARD_4_STRING_BASS_COMPENSATION` dict

**Wave 14 Impact:** This is **bridge math** - should move to `bridge/` subfolder  
**Action:** 📁 **Move** to `bridge/compensation.py` and `bridge/placement.py`

---

## Wave 14 Proposed Structure (Document 3 - Canonical)

```
instrument_geometry/
├── __init__.py                    # Updated exports
├── models.py                      # 🆕 InstrumentModelId (19), InstrumentModelStatus enums
├── registry.py                    # 🆕 JSON-loading registry with caching
├── instrument_model_registry.json # 🆕 Model metadata database
│
├── guitars/                       # 🆕 19 model stub files
│   ├── __init__.py
│   ├── strat.py
│   ├── tele.py
│   ├── les_paul.py
│   ├── dreadnought.py
│   ├── om_000.py
│   ├── j_45.py
│   ├── jazz_bass.py
│   ├── classical.py
│   ├── archtop.py
│   ├── prs.py
│   ├── sg.py
│   ├── jumbo_j200.py
│   ├── ukulele.py
│   ├── gibson_l_00.py
│   ├── flying_v.py
│   ├── es_335.py
│   ├── explorer.py
│   ├── firebird.py
│   └── moderne.py
│
├── neck/                          # 🆕 (reorganized from existing)
│   ├── __init__.py
│   ├── fret_math.py              # ← from scale_length.py
│   ├── fret_geometry.py          # ← from fretboard_geometry.py
│   └── neck_profiles.py          # ← from radius_profiles.py
│
├── body/                          # 🆕 
│   ├── __init__.py
│   └── outlines.py               # Body outline primitives
│
├── bracing/                       # 🆕 
│   ├── __init__.py
│   ├── x_brace.py                # X-bracing patterns
│   └── fan_brace.py              # Fan bracing patterns
│
└── bridge/                        # 🆕 (reorganized from existing)
    ├── __init__.py
    ├── placement.py              # ← from bridge_geometry.py (placement funcs)
    └── compensation.py           # ← from bridge_geometry.py (compensation funcs)
```

---

## Migration Strategy: Side-by-Side Comparison

### What's NEW (Add):
| Component | Source | Lines (est.) |
|-----------|--------|--------------|
| `models.py` | Wave 14 Doc 3 | ~80 |
| `registry.py` | Wave 14 Doc 3 | ~120 |
| `instrument_model_registry.json` | Wave 14 Doc 2 | ~200 |
| `guitars/__init__.py` | New | ~40 |
| `guitars/*.py` (19 stubs) | Wave 14 Doc 1 | ~950 (50 each) |
| `body/__init__.py` | New | ~10 |
| `body/outlines.py` | Wave 14 Doc 1 | ~80 |
| `bracing/__init__.py` | New | ~10 |
| `bracing/x_brace.py` | Wave 14 Doc 1 | ~50 |
| `bracing/fan_brace.py` | Wave 14 Doc 1 | ~50 |
| `neck/__init__.py` | New | ~20 |
| `bridge/__init__.py` | New | ~20 |

### What's MOVED (Reorganize):
| Old Location | New Location | Lines |
|--------------|--------------|-------|
| `scale_length.py` | `neck/fret_math.py` | 259 |
| `fretboard_geometry.py` | `neck/fret_geometry.py` | 178 |
| `radius_profiles.py` | `neck/neck_profiles.py` | 233 |
| `bridge_geometry.py` (placement) | `bridge/placement.py` | ~110 |
| `bridge_geometry.py` (compensation) | `bridge/compensation.py` | ~110 |

### What's KEPT (No change):
| File | Reason |
|------|--------|
| `profiles.py` | Generic dataclasses, used by Wave 14 models |

### What's UPDATED:
| File | Changes |
|------|---------|
| `__init__.py` | Add Wave 14 exports (models, registry) |

---

## Conflict Analysis

### ✅ No Conflicts Detected

The existing code and Wave 14 are **complementary**:

1. **Existing code = Math functions** (pure geometry calculations)
2. **Wave 14 = Model registry** (which guitar models exist, their specs)

Wave 14's 19 guitar stubs will **use** existing functions:
```python
# In guitars/strat.py
from ..neck.fret_math import compute_fret_positions_mm
from ..neck.neck_profiles import compute_compound_radius_at_fret

def get_spec() -> InstrumentSpec:
    return InstrumentSpec(
        instrument_type="electric",
        scale_length_mm=648.0,  # 25.5" Fender
        fret_count=22,
        # ... uses existing dataclasses
    )
```

---

## Recommended Implementation Order

### Phase 1: Add Wave 14 Core (No Breaking Changes)
1. Create `models.py` with 19-model enum + status enum
2. Create `registry.py` with JSON-loading
3. Create `instrument_model_registry.json`
4. Update `__init__.py` to export new modules

### Phase 2: Create Subfolders & Stubs
1. Create `guitars/` folder with 19 stub files
2. Create `body/`, `bracing/` folders with minimal stubs
3. Create `neck/`, `bridge/` folders (empty initially)

### Phase 3: Reorganize Existing Code (Optional)
1. Move `scale_length.py` → `neck/fret_math.py`
2. Move `fretboard_geometry.py` → `neck/fret_geometry.py`
3. Move `radius_profiles.py` → `neck/neck_profiles.py`
4. Split `bridge_geometry.py` → `bridge/placement.py` + `bridge/compensation.py`
5. Update all imports throughout codebase

### Phase 4: Router & Documentation
1. Create `instrument_geometry_router.py`
2. Create `docs/Instrument_Geometry/Wave_14_Instrument_Geometry_Core.md`

---

## Decision Points

### Option A: Full Reorganization (Recommended for Long-Term)
- Move existing files into subfolders
- Clean directory structure
- **Risk:** Breaking imports in RMOS/Art Studio

### Option B: Add-Only (Safe, Minimal Disruption)
- Keep existing files in place
- Add Wave 14 files alongside
- Create subfolders but leave as wrappers importing from root
- **Risk:** Slightly messier structure

### Option C: Hybrid (Recommended)
- Add Wave 14 core (`models.py`, `registry.py`, JSON, `guitars/`)
- Create subfolders but use **re-exports** from existing files
- Defer full move to a future refactor wave

---

## Questions for User

1. **Reorganization depth:** Should we move existing files into subfolders now, or add Wave 14 alongside existing structure?

2. **Import compatibility:** Are there external imports (RMOS, Art Studio) that depend on current paths like `from .scale_length import ...`?

3. **Phase 3 timing:** Should we defer the file moves to a separate "cleanup wave" after Wave 14 core is working?

---

## Summary Table

| Category | Count | Action |
|----------|-------|--------|
| Files to **create** | 28 | New Wave 14 files |
| Files to **keep** | 1 | `profiles.py` |
| Files to **move** (optional) | 5 | Reorganize into subfolders |
| Files to **update** | 1 | `__init__.py` |
| Enums to add | 2 | `InstrumentModelId`, `InstrumentModelStatus` |
| Guitar stubs to create | 19 | All 19 models |

---

**Awaiting user approval to proceed with implementation.**
