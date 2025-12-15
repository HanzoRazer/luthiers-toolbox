# Wave 16 – Tier 1 Real Geometry (Strat / Les Paul / Dreadnought)

**Status:** ✅ Implemented  
**Date:** December 2024

**Goal:** Replace placeholder values with real, usable geometry for:

- Stratocaster
- Les Paul
- Dreadnought acoustic

So that these three can act as fully "real" Tier 1 reference models for:

- RMOS 2.0 feasibility calculations
- Art Studio overlays
- CAM toolpath planning

---

## 1. Scope

This wave updates:

1. `models.py`
   - Extended `NeckProfileSpec` with model_id, radius fields, description
   - Extended `ScaleLengthSpec` with model_id, description

2. `neck/neck_profiles.py`
   - Added `get_default_neck_profile(model_id)` function
   - Real nut/heel widths
   - Real thicknesses (approx)
   - Real fretboard radii

3. `registry.py`
   - Added `get_default_scale(model_id)` function
   - Real scale lengths
   - Real fret counts

We intentionally *do not*:

- Change router behavior
- Change Saw Lab
- Change bracing or bridge physics yet

---

## 2. Reference Specs (Nominal)

### 2.1 Stratocaster (modern C)

| Attribute | Value |
|-----------|-------|
| Scale length | **25.5" ≈ 648.0 mm** |
| Nut width | **42.0 mm** |
| 12th-fret width | **52.0 mm** |
| Thickness @ 1st fret | **~21.0 mm** |
| Thickness @ 12th fret | **~23.0 mm** |
| Fingerboard radius | **9.5" ≈ 241.3 mm** (uniform) |

### 2.2 Les Paul ('59-ish style)

| Attribute | Value |
|-----------|-------|
| Scale length | **24.75" ≈ 628.65 mm** |
| Nut width | **43.0 mm** |
| 12th-fret width | **52.0 mm** |
| Thickness @ 1st fret | **~22.0 mm** |
| Thickness @ 12th fret | **~24.0 mm** |
| Fingerboard radius | **12" ≈ 304.8 mm** |

### 2.3 Dreadnought (Martin-style)

| Attribute | Value |
|-----------|-------|
| Scale length | **25.4" ≈ 645.0 mm** |
| Nut width | **44.5 mm** |
| 12th-fret width | **55.5 mm** |
| Thickness @ 1st fret | **~21.0 mm** |
| Thickness @ 12th fret | **~23.0 mm** |
| Fingerboard radius | **16" ≈ 406.4 mm** |

Values are nominal and can be refined later from Vibe Sandbox and measurement data.

---

## 3. Implementation

### 3.1 models.py Changes

**NeckProfileSpec** now includes:
- `model_id: Optional[InstrumentModelId]`
- `twelve_fret_width_mm` (replaces heel_width_mm)
- `thickness_1st_mm`, `thickness_12th_mm`
- `radius_nut_mm`, `radius_12th_mm`
- `description`
- Backward compat properties for old field names

**ScaleLengthSpec** now includes:
- `model_id: Optional[InstrumentModelId]`
- `scale_length_mm` (primary field)
- `num_frets` (primary field)
- `description`
- Backward compat properties: `length_mm`, `fret_count`

### 3.2 neck_profiles.py – get_default_neck_profile()

```python
from ..models import InstrumentModelId, NeckProfileSpec

def get_default_neck_profile(model_id: InstrumentModelId) -> NeckProfileSpec:
    # Tier 1: Stratocaster
    if model_id == InstrumentModelId.STRAT:
        return NeckProfileSpec(
            model_id=model_id,
            nut_width_mm=42.0,
            twelve_fret_width_mm=52.0,
            thickness_1st_mm=21.0,
            thickness_12th_mm=23.0,
            radius_nut_mm=241.3,   # 9.5"
            radius_12th_mm=241.3,
            description="Stratocaster: modern C, 9.5\" radius",
        )
    # ... (Les Paul, Dreadnought, fallbacks)
```

### 3.3 registry.py – get_default_scale()

```python
from .models import ScaleLengthSpec

def get_default_scale(model_id: InstrumentModelId) -> ScaleLengthSpec:
    # Fender family
    if model_id in (InstrumentModelId.STRAT, InstrumentModelId.TELE, ...):
        return ScaleLengthSpec(
            model_id=model_id,
            scale_length_mm=648.0,  # 25.5"
            num_frets=21,
            description="Fender-style scale length",
        )
    # ... (Gibson, acoustics, fallbacks)
```

---

## 4. Usage

```python
from instrument_geometry.models import InstrumentModelId
from instrument_geometry.registry import get_default_scale
from instrument_geometry.neck.neck_profiles import get_default_neck_profile

# Get Strat scale length
strat_scale = get_default_scale(InstrumentModelId.STRAT)
print(f"Strat scale: {strat_scale.scale_length_mm} mm")  # 648.0 mm

# Get Les Paul neck profile
lp_neck = get_default_neck_profile(InstrumentModelId.LES_PAUL)
print(f"LP nut width: {lp_neck.nut_width_mm} mm")  # 43.0 mm
print(f"LP radius: {lp_neck.radius_nut_mm} mm")    # 304.8 mm (12")
```

---

## 5. Acceptance Criteria

Wave 16 is complete when:

1. ✅ `neck_profiles.py` returns real-world neck specs for:
   - `STRAT`
   - `LES_PAUL`
   - `DREADNOUGHT`

2. ✅ `registry.get_default_scale()` returns realistic scale lengths for all Tier 1 models and other Fender/Gibson/acoustic families.

3. ✅ No existing imports break (Option A shim modules still in place until cleanup).

These three instruments then become the canonical Tier 1 references that later waves (DXF import, Art Studio overlays, RMOS feasibility tuning) can rely on.

---

## 6. Scale Length Reference (All 19 Models)

| Model | Scale (mm) | Scale (in) | Frets |
|-------|------------|------------|-------|
| Stratocaster | 648.0 | 25.5" | 21 |
| Telecaster | 648.0 | 25.5" | 21 |
| Jazz Bass | 648.0 | 25.5" | 21 |
| Les Paul | 628.65 | 24.75" | 22 |
| SG | 628.65 | 24.75" | 22 |
| ES-335 | 628.65 | 24.75" | 22 |
| Flying V | 628.65 | 24.75" | 22 |
| Explorer | 628.65 | 24.75" | 22 |
| Firebird | 628.65 | 24.75" | 22 |
| Moderne | 628.65 | 24.75" | 22 |
| PRS | 635.0 | 25" | 22 |
| Dreadnought | 645.0 | 25.4" | 20 |
| OM/000 | 645.0 | 25.4" | 20 |
| J-45 | 645.0 | 25.4" | 20 |
| Jumbo J-200 | 645.0 | 25.4" | 20 |
| Gibson L-00 | 645.0 | 25.4" | 20 |
| Classical | 650.0 | 25.6" | 19 |
| Archtop | 648.0 | 25.5" | 20 |
| Ukulele | 349.0 | 13.75" | 15 |

---

## 7. See Also

- [Wave 14 – Instrument Geometry Core](./Wave_14_Instrument_Geometry_Core.md)
- [Wave 15 – Data Migration Plan](./Wave_15_Instrument_Geometry_Data_Migration.md)
- [GUITAR_MODEL_INVENTORY_REPORT.md](../GUITAR_MODEL_INVENTORY_REPORT.md)
