# Stratocaster Neck Design — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-07  
**Status:** Assessment Complete — Ready for Implementation  
**Priority:** High  
**Scope:** Backend geometry + CAM + Frontend UI for Stratocaster neck production  

---

## Executive Summary

The The Production Shop has **substantial neck design infrastructure** already in place — geometry models, fret math, taper generators, G-code emitters, DXF exporters, and a working Les Paul neck UI. The Stratocaster is **registered in the model enum** and has **Fender presets defined** in the config, but the pieces are not connected into a dedicated workflow.

**Current capability:** A developer who knows the system can manually hit 3–4 API endpoints with Strat-specific parameters and produce **CNC-ready fret slot G-code + neck taper DXF** today. No new code required.

**What's missing:** A unified Stratocaster neck endpoint, the 6-inline headstock outline generator, and a dedicated frontend UI. The Les Paul implementation is a proven template for all three.

> **Annotation:** This is a "last mile" integration problem, not a fundamental engineering gap. The math, the CAM engine, and the export pipeline are production-grade. The work is wiring Strat-specific parameters through the existing architecture.

---

## Inventory of Existing Assets

### Production-Ready (No Changes Needed)

| Module | Location | What It Does | Strat-Ready? |
|--------|----------|-------------|--------------|
| Fret math engine | `app/instrument_geometry/neck/fret_math.py` | Equal temperament fret positions, multi-scale support | ✅ 648mm scale works as-is |
| FretboardSpec | `app/instrument_geometry/neck/neck_profiles.py` | Nut width, heel width, scale length, compound radius | ✅ Accept Strat values |
| Compound radius | `app/instrument_geometry/neck/radius_profiles.py` | Start→end radius interpolation, arc point generation | ✅ 9.5"→12" Strat compound |
| Fret slot CAM | `app/calculators/fret_slots_cam.py` | Full toolpath + DXF + G-code for fret slots | ✅ Production |
| Fan-fret CAM | `app/calculators/fret_slots_fan_cam.py` | Multi-scale angled fret slots | ✅ Production |
| Neck taper generator | `app/instrument_geometry/neck_taper/` | 2D polyline outline from nut→heel dimensions | ✅ Any scale length |
| Neck taper DXF export | `app/instrument_geometry/neck_taper/dxf_exporter.py` | R12 DXF download of neck blank outline | ✅ Production |
| Taper API endpoints | `POST /instrument/neck_taper/outline[.dxf]` | HTTP access to taper generation | ✅ Production |
| Fret position API | `POST /api/frets/positions` | Calculate fret distances from nut | ✅ Production |

> **Annotation:** This is the strength of the system — the core math and CAM modules are instrument-agnostic. They take parameters (scale length, nut width, fret count, radius) and produce output. The Stratocaster is just a specific parameter set.

### Partially Ready (Needs Extension)

| Module | Location | Current State | Gap |
|--------|----------|--------------|-----|
| NeckGCodeGenerator | `app/generators/neck_headstock_generator.py` | Full G-code generator with tool changes, profile carving | Headstock outline is Les Paul focused (angled, 3+3) |
| Neck config presets | `app/generators/neck_headstock_config.py` | Has `fender_vintage` and `fender_modern` presets | Presets exist but not exposed through a Strat-specific API |
| HeadstockStyle enum | Same file | `FENDER_STRAT` value defined | Generator logic for 6-inline outline not implemented |
| NeckProfile enum | Same file | `C_SHAPE`, `D_SHAPE`, `V_SHAPE`, `U_SHAPE`, `ASYMMETRIC`, `COMPOUND` | All shapes defined — Strat uses Modern C (subset of `C_SHAPE`) |
| Neck router | `app/routers/neck_router.py` | `POST /api/neck/generate` + `export_dxf` | Defaults are Les Paul (24.75" scale, 14° headstock angle). Accepts override params but no Strat presets wired |
| InstrumentModelId | `app/instrument_geometry/models.py` | `STRAT = "stratocaster"` registered | Status is STUB — no linked spec data |

> **Annotation:** The generator class already accepts `headstock_style=HeadstockStyle.FENDER_STRAT` as a parameter. The enum value exists. What's missing is the actual geometry generation code inside the generator that draws the Fender headstock shape. The Les Paul headstock has full outline generation; the Strat path is a no-op or fallback.

### Not Built (Implementation Required)

| Component | Needed For | Estimated Effort |
|-----------|-----------|-----------------|
| `stratocaster.json` spec file | Canonical Strat dimensions (geometry reference) | Low — 1 file, known specs |
| Fender 6-inline headstock outline | Headstock DXF + G-code generation | Medium — geometry + tuner hole layout |
| Stratocaster CAM router | Dedicated `/api/cam/stratocaster/neck/*` endpoints | Medium — template from Les Paul router |
| `StratocasterNeckGenerator.vue` | Frontend design UI | Medium — mirror Les Paul component structure |
| Strat neck composables | State management, presets, actions | Medium — follow `les_paul_neck/` pattern |

> **Annotation:** The Les Paul implementation is the template for everything here. The frontend follows the exact same pattern: Vue component → composables (state + actions + presets) → SDK endpoint → backend router → generator. Copy the structure, swap the parameters.

---

## Architecture Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Vue 3)                               │
│                                                                         │
│  ┌─────────────────────────┐     ┌──────────────────────────────┐      │
│  │ LesPaulNeckGenerator.vue│     │ StratocasterNeckGenerator.vue│      │
│  │         ✅ EXISTS        │     │        ❌ TO BUILD           │      │
│  └──────────┬──────────────┘     └──────────────┬───────────────┘      │
│             │                                    │                      │
│  ┌──────────▼──────────────┐     ┌──────────────▼───────────────┐      │
│  │ les_paul_neck/          │     │ strat_neck/                  │      │
│  │  useLesPaulNeckState    │     │  useStratNeckState           │      │
│  │  useLesPaulNeckActions  │     │  useStratNeckActions         │      │
│  │  useLesPaulNeckPresets  │     │  useStratNeckPresets         │      │
│  │         ✅ EXISTS        │     │        ❌ TO BUILD           │      │
│  └──────────┬──────────────┘     └──────────────┬───────────────┘      │
│             │                                    │                      │
│             └──────────────┬─────────────────────┘                      │
│                            │ SDK: cam.neckGenerate(params)              │
│                            ▼                                            │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                    POST /api/neck/generate
                             │
┌────────────────────────────┼────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                               │
│                            ▼                                            │
│  ┌──────────────────────────────────────────┐                           │
│  │ neck_router.py                           │                           │
│  │  POST /api/neck/generate                 │  ✅ EXISTS (Les Paul      │
│  │  POST /api/neck/export_dxf               │     defaults, accepts     │
│  │  GET  /api/neck/neck/presets             │     any params)           │
│  └──────────────────┬───────────────────────┘                           │
│                     │                                                   │
│  ┌──────────────────▼───────────────────────┐                           │
│  │ NeckGCodeGenerator                       │                           │
│  │  headstock_style = FENDER_STRAT ✅ enum  │                           │
│  │  profile = C_SHAPE             ✅ enum   │                           │
│  │  dims = fender_modern preset   ✅ config │                           │
│  │  _generate_headstock_outline() ⚠️ LP only│                           │
│  └──────────────────┬───────────────────────┘                           │
│                     │                                                   │
│  ┌──────────────────▼──────────────┐  ┌──────────────────────────────┐ │
│  │ Geometry Modules                │  │ CAM Modules                  │ │
│  │  fret_math.py        ✅        │  │  fret_slots_cam.py     ✅   │ │
│  │  neck_profiles.py    ✅        │  │  fret_slots_fan_cam.py ✅   │ │
│  │  radius_profiles.py  ✅        │  │  neck_taper/           ✅   │ │
│  │  taper_math.py       ✅        │  │  dxf_exporter.py       ✅   │ │
│  └─────────────────────────────────┘  └──────────────────────────────┘ │
│                                                                         │
│                        ▼ OUTPUT ▼                                       │
│              ┌────────────────────────┐                                 │
│              │  .dxf (R12 AC1009)     │                                 │
│              │  .nc  (G-code)         │                                 │
│              │  .json (geometry data) │                                 │
│              └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Stratocaster Neck Specifications (Reference)

> **Annotation:** These are the canonical Fender Stratocaster dimensions. The `fender_vintage` and `fender_modern` presets in `neck_headstock_config.py` already contain most of these values. A dedicated `stratocaster.json` spec file should codify all of them.

### Neck Geometry

| Parameter | Vintage (pre-1970) | Modern (2010+) | Units |
|-----------|-------------------|-----------------|-------|
| Scale length | 648.0 (25.5") | 648.0 (25.5") | mm |
| Nut width | 41.3 (1.625") | 42.9 (1.6875") | mm |
| Heel width (at body) | ~56 (2.2") | ~57 (2.25") | mm |
| Fret count | 21 | 22 | — |
| Fretboard radius | 184.2 (7.25") | 241.3→304.8 (9.5"→12") | mm (compound) |
| Neck depth at 1st fret | 20.8 (0.82") | 19.8 (0.78") | mm |
| Neck depth at 12th fret | 23.4 (0.92") | 22.4 (0.88") | mm |
| Neck profile | Soft V / C-shape | Modern C | — |
| Headstock angle | 0° (flat) | 0° (flat) | degrees |
| Truss rod | Vintage-style (walnut plug) | Bi-flex | — |

### Headstock (Fender 6-Inline)

| Parameter | Value | Units |
|-----------|-------|-------|
| Headstock length | ~178 (7") | mm |
| Headstock width (max) | ~89 (3.5") | mm |
| Headstock angle | 0° (flat, string trees used) | degrees |
| Tuner layout | 6-in-line (bass side) | — |
| Tuner hole diameter | 9.5 (0.375") | mm |
| Tuner hole spacing | ~27 (1.0625") | mm |
| String trees | 2 (B/E and D/G) | — |

> **Annotation:** The 0° headstock angle is a key difference from Gibson (14°). The Fender headstock is flat — the string break angle comes from string trees, not the headstock tilt. This simplifies the CNC program (no compound angle machining for the headstock transition).

### Fret Slot Cutting Parameters

| Parameter | Recommended | Units |
|-----------|-------------|-------|
| Slot width | 0.58 (0.023") | mm |
| Slot depth | 3.0–3.5 | mm |
| Saw kerf (blade) | 0.6 (0.024") | mm |
| Fret tang width | 0.53 (0.021") | mm |
| Feed rate (maple) | 100–200 | mm/min |
| Plunge rate | 50–100 | mm/min |

> **Annotation:** The fret slot CAM module (`fret_slots_cam.py`) already handles all of these parameters. Maple is the standard Strat fretboard material — the material-aware feedrate logic adjusts for wood density automatically.

---

## What a User Can Produce Today (No New Code)

### Workflow Using Existing Endpoints

```
Step 1: Calculate fret positions
─────────────────────────────────
POST /api/frets/positions
{
  "scale_length_mm": 648.0,
  "fret_count": 22
}
→ Returns: [36.37, 70.69, 103.10, ..., 618.40] mm from nut

Step 2: Generate neck taper outline
────────────────────────────────────
POST /instrument/neck_taper/outline.dxf
{
  "scale_length_mm": 648.0,
  "nut_width_mm": 42.9,
  "end_width_mm": 57.0,
  "end_fret": 22,
  "taper_type": "linear"
}
→ Downloads: neck_taper.dxf (R12, CNC-ready outline)

Step 3: Generate fret slot G-code
──────────────────────────────────
POST /api/frets/slots
{
  "scale_length_mm": 648.0,
  "fret_count": 22,
  "slot_depth_mm": 3.2,
  "slot_width_mm": 0.58,
  "fretboard_width_nut_mm": 42.9,
  "fretboard_width_heel_mm": 57.0,
  "material": "maple"
}
→ Returns: { dxf_content, gcode_content, statistics }

Step 4: Generate neck profile (using Les Paul endpoint with Strat params)
──────────────────────────────────────────────────────────────────────────
POST /api/neck/generate
{
  "scale_length": 25.5,
  "nut_width": 1.6875,
  "heel_width": 2.25,
  "fretboard_radius": 9.5,
  "num_frets": 22,
  "headstock_angle": 0.0,
  "thickness_1st_fret": 0.78,
  "thickness_12th_fret": 0.88,
  "units": "in"
}
→ Returns: profile_points, fret_positions, centerline (headstock will be wrong shape)
```

> **Annotation:** Steps 1–3 produce genuinely CNC-ready output for a Stratocaster neck. The fret slot program alone is high-value — precision fret slotting is tedious by hand and error-prone. Step 4 works for the neck profile but generates a Les Paul headstock outline, not a Fender shape. The headstock is the primary gap.

### Output Files Producible Today

| Output | Format | CNC-Ready? | Quality |
|--------|--------|-----------|---------|
| Fret slot positions | JSON | N/A (reference data) | ✅ Production — verified equal temperament |
| Fret slot cutting program | `.nc` G-code | ✅ Yes | ✅ Production — GRBL/Mach4/LinuxCNC |
| Fret slot layout drawing | `.dxf` R12 | ✅ Yes (CAM import) | ✅ Production |
| Neck blank taper outline | `.dxf` R12 | ✅ Yes (CNC routing) | ✅ Production |
| Neck cross-section profile | JSON points | ⚠️ Needs post-processing | ✅ Correct math, manual export |
| Headstock outline | `.dxf` R12 | ❌ Wrong shape | ❌ Les Paul only |
| Full neck carving program | `.nc` G-code | ⚠️ Partial | Profile carving works; headstock wrong |

---

## Implementation Plan

### Phase 1: Stratocaster Spec File (Low Effort)

**Create:** `services/api/app/instrument_geometry/specs/stratocaster.json`

> **Annotation:** This is a data file — no logic, just the canonical Stratocaster dimensions in JSON. Referenced by the model registry and used as defaults for API endpoints.

```json
{
  "model_id": "stratocaster",
  "manufacturer": "Fender",
  "category": "electric",
  "scale_length_mm": 648.0,
  "fret_count": 22,
  "string_count": 6,
  "neck": {
    "nut_width_mm": 42.9,
    "heel_width_mm": 57.0,
    "depth_1st_fret_mm": 19.8,
    "depth_12th_fret_mm": 22.4,
    "profile": "modern_c",
    "fretboard_radius_start_mm": 241.3,
    "fretboard_radius_end_mm": 304.8,
    "fretboard_material": "maple",
    "truss_rod_type": "bi_flex"
  },
  "headstock": {
    "style": "fender_strat",
    "angle_deg": 0.0,
    "length_mm": 178.0,
    "width_mm": 89.0,
    "tuner_layout": "6_inline",
    "tuner_hole_diameter_mm": 9.5,
    "tuner_hole_spacing_mm": 27.0,
    "string_trees": 2
  }
}
```

**Files to modify:**
- `app/instrument_geometry/models.py` — update STRAT status from STUB to PARTIAL

---

### Phase 2: Fender Headstock Outline Generator (Medium Effort)

**Modify:** `services/api/app/generators/neck_headstock_generator.py`

> **Annotation:** The generator already branches on `headstock_style`. The Les Paul path generates a Gibson-style angled headstock with 3+3 tuner holes. The Fender path needs to generate a flat headstock silhouette with 6-inline tuner holes. The outline is a closed polyline — approximately 20 coordinate pairs defining the classic Fender contour.

**Key geometry differences from Les Paul:**

| Feature | Les Paul (Current) | Stratocaster (Needed) |
|---------|-------------------|----------------------|
| Angle | 14° back-angle | 0° (flat) |
| Tuner layout | 3+3 (bilateral) | 6-inline (bass side only) |
| Outline shape | Rounded, symmetric | Asymmetric contour (wider on bass side) |
| String nut → tuner path | Angled down | Flat, string trees for break angle |
| Headstock transition | Scarf joint or carved angle | Simple flat continuation |

**Implementation approach:**
1. Define Fender headstock outline as a coordinate array (vertices of the silhouette polygon) in `neck_headstock_config.py`
2. Add `_generate_fender_headstock()` method to `NeckGCodeGenerator` that emits the outline + 6 tuner holes at correct spacing
3. Branch inside existing `_generate_headstock_outline()` based on `self.headstock_style`
4. DXF export: closed LWPOLYLINE for outline + CIRCLE entities for tuner holes

> **Annotation:** The Fender headstock outline can be defined as normalized coordinates (0–1 range) scaled by headstock length/width. This makes it resolution-independent and allows parameter-driven resizing. Several well-documented reference dimensions exist for the classic '60s Strat headstock shape.

---

### Phase 3: Stratocaster Neck API Endpoint (Medium Effort)

**Option A (Recommended):** Extend existing `neck_router.py` with a preset loader

```python
@router.post("/generate/stratocaster")
def generate_stratocaster_neck(
    variant: str = "modern",  # "vintage" | "modern"
    overrides: Optional[NeckParameters] = None
) -> NeckGeometryOut:
    """Generate Stratocaster neck with Fender presets."""
    base = NECK_PRESETS[f"fender_{variant}"]
    # Apply any user overrides
    params = merge_with_overrides(base, overrides)
    # Force Fender headstock style
    generator = NeckGCodeGenerator(
        dims=params,
        headstock_style=HeadstockStyle.FENDER_STRAT,
        profile=NeckProfile.C_SHAPE
    )
    return generator.generate()
```

> **Annotation:** Option A is simpler — one new endpoint on the existing router with Strat presets pre-loaded. The user can still override individual parameters. This avoids creating an entire new router file for what is fundamentally the same generation logic with different defaults.

**Option B (If scope grows):** Create dedicated `stratocaster_neck_router.py` with full Strat-specific endpoints (generate, export_dxf, presets, preview_svg). Follow this path if Strat necks need additional logic beyond parameter changes (e.g., volute carving, heel contour differences).

**Register in main.py:**
```python
# Already registered if using Option A (extends existing neck_router)
# For Option B:
app.include_router(strat_neck_router, prefix="/api/neck/stratocaster", tags=["neck", "stratocaster"])
```

---

### Phase 4: Frontend UI (Medium Effort)

**Create:** Mirror the Les Paul structure exactly.

| New File | Template From | Changes |
|----------|--------------|---------|
| `components/generators/neck/StratocasterNeckGenerator.vue` | `LesPaulNeckGenerator.vue` | Swap defaults, add compound radius UI, 6-inline headstock preview |
| `components/generators/neck/strat_neck/useStratNeckState.ts` | `les_paul_neck/useLesPaulNeckState.ts` | Strat default values (25.5" scale, 0° headstock, etc.) |
| `components/generators/neck/strat_neck/useStratNeckActions.ts` | `les_paul_neck/useLesPaulNeckActions.ts` | Call Strat endpoint variant |
| `components/generators/neck/strat_neck/useStratNeckPresets.ts` | `les_paul_neck/useLesPaulNeckPresets.ts` | Vintage '60s, Modern, American Professional presets |
| `components/generators/neck/strat_neck/stratNeckTypes.ts` | `les_paul_neck/lesPaulNeckTypes.ts` | Add compound radius fields |

> **Annotation:** The Les Paul component is the proven pattern. The Strat version adds two UI elements the Les Paul doesn't have: (1) compound radius start/end selector, and (2) a flat headstock preview instead of the angled Gibson preview. Everything else — fret count slider, nut width input, profile shape selector, export buttons — is structurally identical.

**Strat-specific UI additions:**

| Field | Control Type | Default |
|-------|-------------|---------|
| Compound radius start | Dropdown or slider (7.25", 9.5", 10", 12") | 9.5" |
| Compound radius end | Dropdown or slider (12", 14", 16") | 12" |
| Fretboard material | Toggle (Maple / Rosewood / Pau Ferro) | Maple |
| Vintage/Modern toggle | Radio buttons | Modern |
| String tree positions | Checkbox (include in headstock DXF) | On |

---

## Dependency Chain

```
Phase 1 (spec file) ← no dependencies, start immediately
     │
     ▼
Phase 2 (headstock generator) ← needs spec for dimensions
     │
     ▼
Phase 3 (API endpoint) ← needs headstock generator working
     │
     ▼
Phase 4 (frontend UI) ← needs API endpoint to call
```

> **Annotation:** Phases 1 and 2 can overlap. Phase 3 is testable without the frontend. Phase 4 is pure UI once the API exists. Fret slot G-code and neck taper DXF work TODAY — they don't need any of these phases.

---

## Testing Checklist

### Geometry Validation

| Test | Expected Result | Verification Method |
|------|----------------|-------------------|
| 22-fret positions at 648mm scale | 1st fret: 36.37mm, 12th fret: 324.0mm (half scale) | Compare against Fender spec sheet |
| Neck taper: 42.9mm nut → 57mm heel | Linear taper, symmetric about centerline | DXF visual inspection |
| Compound radius 9.5" → 12" | Radius at nut = 241.3mm, radius at last fret = 304.8mm | `radius_profiles.py` unit test |
| Headstock outline | Closed polyline, 6 tuner holes at correct spacing | DXF overlay against Fender template |
| Fret slot depth at compound radius | Slot bottom follows curved surface | Cross-section plot validation |

### G-code Validation

| Test | Expected Result |
|------|----------------|
| Fret slot G-code loads without error | GRBL, Mach4, LinuxCNC parsers accept output |
| Estimated cut time reasonable | 22 slots × ~3 sec each ≈ 1–2 min total |
| Feed rates within maple safe range | 100–200 mm/min cut, 50–100 mm/min plunge |
| No rapids through material | All G0 moves at safe Z height |
| Units consistent | All mm internally, converted at API boundary |

### Frontend Tests (Vitest)

| Test | Validates |
|------|-----------|
| Strat presets load correctly | `useStratNeckPresets` returns vintage + modern |
| Default values match spec | Scale 648mm, nut 42.9mm, 22 frets |
| Generate action calls correct endpoint | SDK hits `/api/neck/generate/stratocaster` |
| Export DXF triggers download | Browser download initiated with correct filename |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Headstock outline coordinates inaccurate | Medium | Medium — cosmetic, not structural | Validate against scanned Fender headstock template |
| Compound radius math edge case at 0th fret | Low | High — affects fret seating | Unit test radius at fret 0, 12, and 22 specifically |
| G-code crashes CNC controller | Low | High — can damage blank | Test on GRBL simulator before cutting. Golden snapshot after validation |
| Les Paul router changes break Strat path | Low | Medium | Separate composable files, shared types only |

---

## GAP REGISTRY — Trackable Code & Architecture Deficits

> **Purpose:** Each gap has a unique ID, the exact file where the problem lives, what's broken, what "fixed" looks like, dependencies, and test expectations. A remediation team can work through these top-to-bottom.

### Summary Dashboard

| ID | Area | Severity | Effort | Status | Blocks |
|----|------|----------|--------|--------|--------|
| NECK-01 | Strat headstock outline generator | **Critical** | Medium | ⚠️ Incomplete stub | NECK-04, NECK-05 |
| NECK-02 | Stratocaster JSON spec file | **Medium** | Low | ❌ Missing | NECK-03 |
| NECK-03 | Strat model status in registry | **Low** | Trivial | ⚠️ Enum only (STUB) | — |
| NECK-04 | Strat-specific API endpoint | **High** | Low | ❌ Missing | NECK-05 |
| NECK-05 | Strat frontend UI components | **High** | Medium | ❌ Missing | — |

---

### NECK-01: Strat Headstock Outline Generator — Incomplete Stub

**Severity:** Critical — the Strat headstock is the #1 reason the neck workflow fails for Fender guitars  
**Status:** `HeadstockStyle.FENDER_STRAT` enum exists, but the generator branch is incomplete and falls through to paddle headstock  

**Where the problem is:**
- **File:** `services/api/app/generators/neck_headstock_config.py`
- **Function:** `generate_headstock_outline(style, dims)` — lines ~160–200
- **Branch:** `elif style == HeadstockStyle.FENDER_STRAT:` — computes `half_width` but does not return the 6-inline outline points. Falls through to default paddle headstock.
- **Comparison:** Gibson branches (`GIBSON_OPEN`, `GIBSON_SOLID`) at lines ~100–140 are fully implemented with proper 3+3 geometry.

**What's there now:**
```python
elif style == HeadstockStyle.FENDER_STRAT:
    # Fender 6-in-line
    half_width = dims.nut_width_in / 2
    points = [  # ← STUB — incomplete, falls through to paddle
```

**What "fixed" looks like:**
The `FENDER_STRAT` branch returns a `List[Tuple[float, float]]` of ~20 coordinate pairs defining the classic Fender 6-inline silhouette:
- Total outline: ~178mm long × ~89mm wide
- Asymmetric shape (wider on bass side)
- Flat (0° angle — no scarf joint transition)
- String tree mounting points included

Also fix `generate_tuner_positions()` in the same file — verify it handles 6-inline layout (all tuners on bass side, ~27mm spacing) not just 3+3 Gibson layout.

**Test expectations:**
- `generate_headstock_outline(HeadstockStyle.FENDER_STRAT, fender_dims)` returns >10 points (not paddle fallback)
- Outline is a closed polyline (first point == last point)
- Max dimensions: width ~89mm, length ~178mm
- All points positive (no flipped geometry)
- DXF export of outline produces valid R12 AC1009 closed LWPOLYLINE
- Tuner positions: 6 holes, all on one side, ~27mm apart

**Dependencies:** Blocks NECK-04 (API can't produce correct Strat DXF), NECK-05 (frontend shows wrong headstock)  
**Blocked by:** Nothing — implement first

---

### NECK-02: No `stratocaster.json` Spec File

**Severity:** Medium — no canonical dimension reference, each endpoint re-hardcodes Strat values  
**Status:** File does not exist. No `specs/` directory found under `instrument_geometry/`.  

**Where the problem is:**
- **Expected file:** `services/api/app/instrument_geometry/specs/stratocaster.json` — does not exist
- **Existing presets:** `neck_headstock_config.py` has `fender_vintage` and `fender_modern` in `NECK_PRESETS` dict (~lines 87–130) but these are Python objects, not a shared JSON spec

**What "fixed" looks like:**
Create `services/api/app/instrument_geometry/specs/stratocaster.json` containing canonical Fender dimensions:
```json
{
  "model_id": "stratocaster",
  "scale_length_mm": 648.0,
  "fret_count": 22,
  "neck": {
    "nut_width_mm": 42.9,
    "heel_width_mm": 57.0,
    "depth_1st_fret_mm": 19.8,
    "depth_12th_fret_mm": 22.4,
    "profile": "modern_c",
    "fretboard_radius_start_mm": 241.3,
    "fretboard_radius_end_mm": 304.8
  },
  "headstock": {
    "style": "fender_strat",
    "angle_deg": 0.0,
    "length_mm": 178.0,
    "width_mm": 89.0,
    "tuner_layout": "6_inline",
    "tuner_hole_diameter_mm": 9.5,
    "tuner_hole_spacing_mm": 27.0,
    "string_trees": 2
  }
}
```

**Test expectations:**
- File is valid JSON, loadable by `json.load()`
- `model_id` matches `InstrumentModelId.STRAT` value
- Scale length, nut width, and fret count match standard Fender specs

**Dependencies:** Feeds into NECK-03 (model registry update) and NECK-04 (API defaults)  
**Blocked by:** Nothing

---

### NECK-03: Strat Model Status Is STUB in Registry

**Severity:** Low — cosmetic / metadata, but incorrect status confuses downstream code  
**Status:** Enum value `STRAT = "stratocaster"` exists at `app/instrument_geometry/models.py` line ~39. No linked spec data.  

**Where the problem is:**
- **File:** `services/api/app/instrument_geometry/models.py` — line ~39
- **Current state:** `STRAT = "stratocaster"` — enum value only, no implementation linked

**What "fixed" looks like:**
Update status from STUB to PARTIAL (after NECK-02 spec file exists), then to COMPLETE (after NECK-01 headstock is implemented). Link the spec file so the model registry knows where to find Strat dimensions.

**Test expectations:**
- Model registry query for `"stratocaster"` returns spec data (not `None` or empty)
- Status field reflects actual implementation level

**Dependencies:** None downstream  
**Blocked by:** NECK-02 (spec file must exist to link)

---

### NECK-04: No Strat-Specific API Endpoint

**Severity:** High — users must manually construct Les Paul endpoint params with Strat values  
**Status:** Only generic `/api/neck/generate` exists, documented as "Les Paul Style" in file header  

**Where the problem is:**
- **File:** `services/api/app/routers/neck_router.py`
- **Line ~361:** `@router.post("/generate", response_model=NeckGeometryOut)` — generic endpoint
- **File header (lines 1–7):** `"Neck Generator Router - Les Paul Style Neck with DXF Export"` — Les Paul is the documented target
- **No Strat route:** grep for "stratocaster" or "strat" in `neck_router.py` returns zero matches

**What "fixed" looks like:**
Add a Strat-specific endpoint to the existing router (Option A from handoff):
```python
@router.post("/generate/stratocaster")
def generate_stratocaster_neck(
    variant: str = "modern",  # "vintage" | "modern"
    overrides: Optional[NeckParameters] = None
) -> NeckGeometryOut:
    base = NECK_PRESETS[f"fender_{variant}"]
    params = merge_with_overrides(base, overrides)
    generator = NeckGCodeGenerator(
        dims=params,
        headstock_style=HeadstockStyle.FENDER_STRAT,
        profile=NeckProfile.C_SHAPE
    )
    return generator.generate()
```

Also add: `POST /api/neck/generate/stratocaster/dxf` for direct DXF download (mirror existing `/export_dxf`).

**Test expectations:**
- `POST /api/neck/generate/stratocaster` with no body returns Modern Strat defaults (648mm scale, 22 frets, 42.9mm nut)
- `POST /api/neck/generate/stratocaster?variant=vintage` returns Vintage Strat (41.3mm nut, 7.25" single radius)
- Overrides are applied correctly (e.g., `fret_count=24` works if passed)
- Response includes valid fret positions, taper outline, and headstock outline
- Headstock outline is Fender 6-inline (not Gibson/paddle fallback)
- DXF export endpoint returns valid R12 AC1009 file

**Dependencies:** Blocks NECK-05 (frontend needs an endpoint to call)  
**Blocked by:** NECK-01 (headstock must be implemented for correct output)

---

### NECK-05: No Strat Frontend UI Components

**Severity:** High — users have no dedicated Strat design interface  
**Status:** Does not exist. Les Paul equivalent (`LesPaulNeckGenerator.vue` + `les_paul_neck/` directory) is the proven template.  

**Where the problem is:**
- **Expected files (all missing):**
  - `packages/client/src/components/generators/neck/StratocasterNeckGenerator.vue`
  - `packages/client/src/components/generators/neck/strat_neck/useStratNeckState.ts`
  - `packages/client/src/components/generators/neck/strat_neck/useStratNeckActions.ts`
  - `packages/client/src/components/generators/neck/strat_neck/useStratNeckPresets.ts`
  - `packages/client/src/components/generators/neck/strat_neck/stratNeckTypes.ts`
- **Existing template to copy:**
  - `packages/client/src/components/generators/neck/LesPaulNeckGenerator.vue` ✅
  - `packages/client/src/components/generators/neck/les_paul_neck/` directory ✅

**What "fixed" looks like:**
Mirror the Les Paul 1:1 with these Strat-specific changes:
1. Default values swap to Fender (648mm scale, 42.9mm nut, 0° headstock, Modern C profile)
2. Compound radius UI: start and end radius dropdowns (Les Paul has single radius)
3. Headstock preview shows flat 6-inline shape (not angled 3+3)
4. Preset selector: `Vintage '60s`, `Modern`, `American Professional`
5. Fretboard material selector: Maple (default), Rosewood, Pau Ferro
6. SDK calls hit `/api/neck/generate/stratocaster` (not generic `/generate`)

**Test expectations (Vitest):**
- `useStratNeckPresets` exports at least 2 presets (vintage, modern)
- Default state has `scaleLengthMm === 648`, `nutWidthMm === 42.9`, `fretCount === 22`
- Generate action calls `cam.neckGenerateStratocaster()` (or equivalent SDK function)
- DXF export triggers browser download with filename containing "stratocaster"

**Dependencies:** None downstream  
**Blocked by:** NECK-04 (API endpoint must exist)

---

### REMEDIATION SEQUENCE

```
Phase 1: Foundation (no dependencies)
├── NECK-02: Create stratocaster.json spec file              ← trivial
├── NECK-03: Update model registry status                    ← trivial
└── NECK-01: Complete Fender headstock outline generator      ← START HERE (critical path)

Phase 2: API (depends on Phase 1)
└── NECK-04: Add /generate/stratocaster endpoint

Phase 3: Frontend (depends on Phase 2)
└── NECK-05: Create StratocasterNeckGenerator.vue + composables
```

> **Annotation:** NECK-01 is the critical path. Everything else is wiring. The headstock outline is the only piece that requires real geometry engineering — the rest is parameter swapping and UI scaffolding.

### Files to Create

| File | Gap(s) |
|------|--------|
| `services/api/app/instrument_geometry/specs/stratocaster.json` | NECK-02 |
| `packages/client/src/components/generators/neck/StratocasterNeckGenerator.vue` | NECK-05 |
| `packages/client/src/components/generators/neck/strat_neck/index.ts` | NECK-05 |
| `packages/client/src/components/generators/neck/strat_neck/stratNeckTypes.ts` | NECK-05 |
| `packages/client/src/components/generators/neck/strat_neck/useStratNeckState.ts` | NECK-05 |
| `packages/client/src/components/generators/neck/strat_neck/useStratNeckActions.ts` | NECK-05 |
| `packages/client/src/components/generators/neck/strat_neck/useStratNeckPresets.ts` | NECK-05 |

### Files to Modify

| File | Gap(s) | Change |
|------|--------|--------|
| `services/api/app/generators/neck_headstock_config.py` | NECK-01 | Complete FENDER_STRAT branch in `generate_headstock_outline()` |
| `services/api/app/instrument_geometry/models.py` | NECK-03 | Update STRAT status from STUB |
| `services/api/app/routers/neck_router.py` | NECK-04 | Add `/generate/stratocaster` endpoint |

---

*End of handoff. All measurements in mm unless noted. DXF output is R12 (AC1009). G-code targets GRBL/Mach4/LinuxCNC.*
