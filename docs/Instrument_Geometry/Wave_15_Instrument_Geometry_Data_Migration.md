# Wave 15 – Instrument Geometry Data Migration & Asset Canon

**Goal:** Populate the new Instrument Geometry Core (Wave 14) with *real data* from:
- DXF/DWG templates
- Vibe sandbox guitar specs
- Legacy Lutherier Project assets

This wave turns the skeleton into a living library of actual guitar models.

---

## 1. Scope

This wave covers:

1. Mapping **instrument_model_registry.json** entries to:
   - Concrete asset roots (DXF/DWG/stl/pdf)
   - Concrete geometry implementations (body, neck, bridge)

2. Promoting **legacy assets → canonical assets**:
   - From scattered folders and old sandboxes
   - Into `assets/instrument_templates/<model_id>/...`

3. Wiring real numbers into:
   - `neck/neck_profiles.py`
   - `neck/radius_profiles.py`
   - `body/outlines.py`
   - `bridge/geometry.py` / `bridge/placement.py`

This wave does **not**:
- Change RMOS 2.0 APIs
- Change Saw Lab
- Change calculators architecture

---

## 2. Inputs

### 2.1 Registry

- `services/api/app/instrument_geometry/instrument_model_registry.json`  
  (canonical model list + status)

### 2.2 Legacy Specs

- GUITAR_MODEL_INVENTORY_REPORT.md
- Vibe sandbox docs that specify:
  - Scale lengths
  - Nut/heel widths
  - Typical radii
  - Body dimensions

### 2.3 DXF/DWG Assets

Target future layout:

```text
assets/
  instrument_templates/
    stratocaster/
      body_outline.dxf
      pickguard.dxf
      neck_pocket.dwg

    les_paul/
      body_outline.dxf
      carve_map.dxf

    dreadnought/
      top_outline.dxf
      brace_layout.dwg

    j_45/
      top_outline.dxf
      brace_layout.dwg

    ukulele/
      soprano_body_outline.dxf
      neck_profile.dxf
```

---

## 3. Implementation Plan

### 3.1 Add Asset Roots to Registry (Optional Extension)

Extend each `models[]` entry in `instrument_model_registry.json` with:

```json
"asset_root": "assets/instrument_templates/stratocaster",
"notes": "Imported from Vibe sandbox + legacy Lutherier Project"
```

This is optional in Wave 15, but recommended.

### 3.2 Populate Neck Profiles

File: `services/api/app/instrument_geometry/neck/neck_profiles.py`

For each model:

Replace placeholder values with real data from:
- Vibe sandbox specs
- Measurement notes
- Historical plans

Example:

```python
if model_id == InstrumentModelId.STRAT:
    return NeckProfileSpec(
        model_id=model_id,
        nut_width_mm=42.0,
        twelve_fret_width_mm=52.0,
        thickness_1st_mm=21.0,
        thickness_12th_mm=23.0,
        radius_nut_mm=241.3,
        radius_12th_mm=241.3,
        description="Strat: modern C, 9.5\" radius (real spec from Vibe sandbox)",
    )
```

### 3.3 Populate Scale Lengths

File: `services/api/app/instrument_geometry/registry.py`

Replace generic values in `get_default_scale()` with:
- Strat / Tele / Jazz Bass: real Fender scales
- Les Paul / SG / etc.: real Gibson scales
- Dread / OM / J-45 / L-00 / J-200: real acoustic scales
- Classical: 650 mm
- Ukulele: per specific instrument (soprano / concert)

### 3.4 Populate Body Outlines

File: `services/api/app/instrument_geometry/body/outlines.py`

**Short term:**
- Hard-code coarse outlines from measurements / plans for:
  - Strat
  - Les Paul
  - Dreadnought
  - OM / J-45
  - Ukulele

**Long term (future wave):**
- Add DXF import helpers that:
  - Read `body_outline.dxf`
  - Convert polylines/splines → `List[Point2D]`
  - Cache that into JSON or a simple cache layer

### 3.5 Bridge Geometry & Placement

Files:
- `services/api/app/instrument_geometry/bridge/geometry.py`
- `services/api/app/instrument_geometry/bridge/placement.py`
- `services/api/app/instrument_geometry/bridge/compensation.py`

Tasks:
- Wire existing math from legacy `bridge_geometry.py` into the new structure.
- Ensure:
  - Les Paul / Strat / Tele bridge placement respects:
    - Scale length
    - Compensation offsets
  - Acoustic bridge placement uses:
    - Scale length
    - Typical saddle setback per string group

---

## 4. Priority Order (By Tier)

### Tier 1 – Production Baseline

- **Stratocaster**
- **Les Paul**
- **Dreadnought**

Tasks:
- Fully populate:
  - `NeckProfileSpec`
  - `ScaleLengthSpec`
  - `BodyOutlineSpec`
  - `BridgePlacementSpec`

These become the "golden path" models for RMOS & Art Studio.

### Tier 2 – Near Production

- **J-45**
- **OM / 000**
- **Ukulele (soprano)**

Tasks:
- At least: real scale lengths + neck profiles.
- Preferable: real body outlines from DXF.

### Tier 3 – Reference & Legacy

- Jazz Bass
- Jumbo (J-200)
- Gibson L-00
- Flying V, ES-335, Explorer, Firebird, Moderne
- Classical, Archtop, PRS, SG

Tasks:
- Record real scale lengths.
- Mark status appropriately in registry.
- Defer detailed outlines/bridges to future waves.

---

## 5. Acceptance Criteria

Wave 15 is done when:

1. **InstrumentModelId + instrument_model_registry.json + geometry core are consistent:**
   - All IDs match.
   - All Tier 1/Tier 2 models have real scale/neck/bridge data.

2. **For Strat, Les Paul, Dreadnought:**
   - `GET /api/instrument-geometry/scale-length/{model_id}` returns real values.
   - `GET /api/instrument-geometry/neck-profile/{model_id}` returns real neck dims.
   - `GET /api/instrument-geometry/body-outline/{model_id}` returns a plausible outline.
   - `GET /api/instrument-geometry/bridge-placement/{model_id}` returns plausible placement.

3. **GUITAR_MODEL_INVENTORY_REPORT.md is updated:**
   - Status fields for Tier 1 models reflect their upgraded reality (PARTIAL → PRODUCTION, etc.).

---

## 6. Next Waves After 15 (Preview)

**Wave 16 – DXF Import Pipeline**
- `instrument_geometry/dxf_import/`
- R12-safe outline import, scaling, and cache.

**Wave 17 – Art Studio Geometry Overlay**
- Frontend overlays instrument outlines + rosette/relief design.

**Wave 18 – RMOS Integration**
- RMOS uses instrument geometry for feasibility + CAM context.
