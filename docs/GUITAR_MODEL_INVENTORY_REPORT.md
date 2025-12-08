# Guitar Model Inventory Report

**Date:** January 2025  
**Branch:** `feature/client-migration`  
**Purpose:** Comprehensive inventory of all guitar models in codebase for library/calculator alignment

---

## Executive Summary

This report documents ALL guitar models found in the Luthier's Tool Box codebase. It covers:
- **Active Code:** Components, routers, calculators, presets currently in use
- **Active Assets:** DXF, STL, PDF files in working directories  
- **Documentation References:** Specs mentioned in docs but may not be implemented
- **Legacy References:** Files in `Lutherier Project/` (reference-only, DO NOT MODIFY)
- **Missing/Planned:** Documented features not yet created

### Guitar Models Identified

| Model | Active Code | Active Assets | Legacy Reference | Status |
|-------|-------------|---------------|------------------|--------|
| Stratocaster | ✅ Full router + presets | ✅ DXF/STL/PDF | ✅ Extensive | **Production** |
| Telecaster | ⚠️ Presets only | ❌ None | ❌ None | **Stub** |
| Les Paul | ✅ Neck generator + presets | ❌ None | ✅ Extensive | **Partial** |
| Dreadnought | ⚠️ Presets only | ❌ None | ✅ Martin 1937 | **Stub** |
| OM / 000 | ⚠️ Presets only | ❌ None | ✅ Gibson OM | **Stub** |
| J-45 | ❌ None | ✅ CAM Import Kit | ✅ Extensive | **Assets Only** |
| Jazz Bass | ⚠️ Presets only | ❌ None | ❌ None | **Stub** |
| Classical | ⚠️ Scale/rosette refs | ❌ None | ❌ None | **Reference** |
| Archtop | ⚠️ Bridge calc preset | ❌ None | ✅ Measurement kit | **Reference** |
| PRS | ⚠️ Scale refs only | ❌ None | ❌ None | **Reference** |
| SG | ⚠️ Doc refs only | ❌ None | ❌ None | **Planned** |

---

## 1. Stratocaster

### Status: ✅ **PRODUCTION** - Most Complete Model

### 1.1 Active Code

**Router:** `services/api/app/routers/stratocaster_router.py` (431 lines)
```python
# Full-featured router with:
# - POST /stratocaster/body/generate - Body geometry generation
# - POST /stratocaster/neck/generate - Neck geometry generation
# - POST /stratocaster/pickguard/generate - Pickguard geometry
# - GET /stratocaster/presets - Preset configurations
# - POST /stratocaster/export/dxf - DXF R12 export
```

**Presets in GuitarDimensionsForm.vue:**
```javascript
stratocaster: {
  bodyLength: 460,
  bodyWidthUpper: 320,
  bodyWidthLower: 320,
  waistWidth: 280,
  bodyDepth: 45,
  scaleLength: 648,      // 25.5"
  nutWidth: 42,
  bridgeSpacing: 52,
  fretCount: 22,
  neckAngle: 0
}
```

**BridgeCalculator.vue Preset:**
```javascript
{ id:'strat', label:'Strat/Tele (25.5")', scale_in:25.5, spread_mm:52.5, Ct_mm:2.0, Cb_mm:3.5, slotWidth_mm:3.0, slotLen_mm:75 }
```

**ArtStudioSidebar.vue Scale Preset:**
```javascript
fender_25_5: { scale: 648, nut: 42.8, heel: 56 }
```

**Instrument Geometry Presets:**
- `services/api/app/instrument_geometry/scale_length.py`: `"fender_standard": 647.7` (25.5")
- `services/api/app/instrument_geometry/radius_profiles.py`: `9.5" (241.3mm)` Fender vintage

### 1.2 Active Assets

**Location:** `Stratocaster/` (root level)

| File | Type | Description |
|------|------|-------------|
| `Stratocaster BODY(Top).dxf` | DXF | Body top view |
| `Stratocaster BODY(Bottom).dxf` | DXF | Body bottom view |
| `Stratocaster Body 3D.stl` | STL | 3D body model |
| `Stratocaster NECK.dxf` | DXF | Neck outline |
| `Stratocaster NECK.stl` | STL | 3D neck model |
| `Stratocaster FRETBOARD.dxf` | DXF | Fretboard outline |
| `Stratocaster FRETBOARD.stl` | STL | 3D fretboard |
| `Stratocaster PICKGUARD.dxf` | DXF | Pickguard outline |
| `Stratocaster PICKGUARD.stl` | STL | 3D pickguard |
| `Stratocaster TREMOLO COVER.dxf` | DXF | Tremolo cover |
| `Stratocaster TREMOLO COVER.stl` | STL | 3D tremolo cover |
| `Stratocaster-Guitar-Plan-01.pdf` | PDF | Full blueprint |
| `stratocaster_bom_price_sheet.csv` | CSV | Bill of materials |

**Nested Project:** `Stratocaster/Fender Stratocaster_Project/`
- Body, Fretboard, Neck, Pickguard, Tremolo cover subfolders with duplicate assets

### 1.3 Documentation References

- `docs/NECK_PROFILE_QUICKSTART.md`: References `strat_modern_c.json` (NOT YET CREATED)
- `docs/NECK_PROFILE_BUNDLE_ANALYSIS.md`: Planned neck profile JSON

### 1.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Fender Stratocaster_Project/`
- Subfolders: Body, Fretboard, Neck, Pickguard, Tremolo cover
- Contains original source DXF/STL files

### 1.5 Missing/Planned

- [ ] `strat_modern_c.json` neck profile config
- [ ] Neck profile data points for CAM operations
- [ ] Electronics cavity routing templates

---

## 2. Telecaster

### Status: ⚠️ **STUB** - Presets Only, No Router or Assets

### 2.1 Active Code

**NO DEDICATED ROUTER** - Unlike Stratocaster, no `telecaster_router.py` exists

**Presets in GuitarDimensionsForm.vue:**
```javascript
telecaster: {
  bodyLength: 470,
  bodyWidthUpper: 325,
  bodyWidthLower: 325,
  waistWidth: 320,
  bodyDepth: 45,
  scaleLength: 648,      // 25.5"
  nutWidth: 42,
  bridgeSpacing: 54,
  fretCount: 22,
  neckAngle: 0
}
```

**BridgeCalculator.vue:** Shares `strat` preset (same 25.5" scale)

### 2.2 Active Assets

**NONE** - No DXF, STL, or PDF files exist for Telecaster

### 2.3 Documentation References

- `docs/NECK_PROFILE_QUICKSTART.md`: References `tele_modern_c.json` (NOT YET CREATED)
- `docs/NECK_PROFILE_BUNDLE_ANALYSIS.md`: Planned neck profile JSON
- `templates/env/.env.parametric`: Lists "tele" as body style option

### 2.4 Legacy Reference

**NONE** - No Telecaster files in `Lutherier Project/`

### 2.5 Missing/Planned

- [ ] `telecaster_router.py` (per user: NOT creating model-specific routers)
- [ ] `tele_modern_c.json` neck profile config
- [ ] DXF/STL/PDF assets
- [ ] Body outline geometry
- [ ] Pickguard templates (single-coil, humbucker variants)

---

## 3. Les Paul

### Status: ⚠️ **PARTIAL** - Neck Generator + Presets, No Full Router

### 3.1 Active Code

**Dedicated Components:**
- `packages/client/src/components/toolbox/LesPaulNeckGenerator.vue` - Neck profile generator
- `packages/client/src/utils/neck_generator.ts` - Les Paul-specific neck math

**Presets in GuitarDimensionsForm.vue:**
```javascript
les_paul: {
  bodyLength: 475,
  bodyWidthUpper: 330,
  bodyWidthLower: 330,
  waistWidth: 280,
  bodyDepth: 55,
  scaleLength: 628,      // 24.75"
  nutWidth: 43,
  bridgeSpacing: 52,
  fretCount: 22,
  neckAngle: 4           // Neck angle unique to LP
}
```

**BridgeCalculator.vue Preset:**
```javascript
{ id:'lp', label:'Les Paul (24.75")', scale_in:24.75, spread_mm:52.0, Ct_mm:1.5, Cb_mm:3.0, slotWidth_mm:3.0, slotLen_mm:75 }
```

**Instrument Geometry Presets:**
- `services/api/app/instrument_geometry/scale_length.py`: `"gibson_standard": 628.65` (24.75")
- `services/api/app/instrument_geometry/radius_profiles.py`: `12" (305mm)` Gibson standard

**Neck Profile Presets (P2_1_NECK_GENERATOR_COMPLETE.md):**
```json
{
  "name": "Les Paul Standard",
  "scale_length_mm": 628.65,
  "nut_width_mm": 43.0,
  "fret_12_width_mm": 52.0
}
```

### 3.2 Active Assets

**NONE in active directories** - No DXF, STL, or PDF files in `packages/` or root

### 3.3 Documentation References

- `docs/NECK_PROFILE_QUICKSTART.md`: References `les_paul_59.json` (NOT YET CREATED)
- `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: Gibson 24.75" scale
- `P2_1_NECK_GENERATOR_COMPLETE.md`: Les Paul neck presets documented

### 3.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Les Paul_Project/`

**Extensive CAM Assets:**
| File/Folder | Description |
|-------------|-------------|
| `LesPaul_CAM_Closed_ALL.dxf` | CAM-ready closed polylines |
| `LesPaul_CAM_Closed.dxf` | CAM-ready body outline |
| `LesPaul_DXF_Verification_Packet.pdf` | Verification checklist |
| `LesPaul_Mach4_CAM_Starter_Kit/` | Mach4 CNC starter kit |
| `Source Files/Les Paul CNC Files.dxf` | Source CAD files |
| `09252025/Base_LP_Mach4_Package/` | Production Mach4 setup |
| `09252025/Smart_LP_*/` | Multiple smart guitar integration packages |
| `09252025/V6_CAM_Templates_Kit/` | Fusion 360 CAM templates |

**Smart Guitar Integration Files (09252025/):**
- `Smart_LP_Back_Cover_Vented_R12.dxf` - Electronics cover
- `Smart_LP_Pocket_Fit_Report*.pdf` - Pocket verification
- `Smart_LP_Side_Drill_Overlay_R12.dxf` - Side drilling templates
- `FusionSetup_Base_LP_Mach4.json` - Fusion 360 tool library
- `Tool_List_Base_LP.csv` - Tool inventory

### 3.5 Missing/Planned

- [ ] `les_paul_59.json` neck profile config
- [ ] Active DXF assets (currently only in legacy)
- [ ] Body cavity routing templates
- [ ] Control cavity templates
- [ ] Pickup routing templates (PAF humbucker)

---

## 4. Dreadnought

### Status: ⚠️ **STUB** - Presets Only, No Router

### 4.1 Active Code

**Presets in GuitarDimensionsForm.vue:**
```javascript
dreadnought: {
  bodyLength: 505,
  bodyWidthUpper: 280,
  bodyWidthLower: 390,
  waistWidth: 270,
  bodyDepth: 120,
  scaleLength: 648,      // 25.5"
  nutWidth: 43,
  bridgeSpacing: 56,
  fretCount: 20,
  neckAngle: 0
}
```

**BridgeCalculator.vue Preset:**
```javascript
{ id:'dread', label:'Dread (25.4")', scale_in:25.4, spread_mm:54.0, Ct_mm:2.0, Cb_mm:4.5, slotWidth_mm:3.2, slotLen_mm:80 }
```

**Instrument Geometry:**
- `services/api/app/instrument_geometry/profiles.py`: Dreadnought reference in scale lengths

### 4.2 Active Assets

**NONE** - No DXF, STL, or PDF files

### 4.3 Documentation References

- Referenced in BridgeCalculator preset descriptions

### 4.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/1937 Martin Drawings Plans/1937 D-28/`
- Contains Martin D-28 reference drawings (historical)

### 4.5 Missing/Planned

- [ ] Body outline DXF
- [ ] X-bracing pattern templates
- [ ] Rosette channel dimensions
- [ ] Bridge plate templates
- [ ] Soundhole dimensions

---

## 5. OM / Orchestra Model (000)

### Status: ⚠️ **STUB** - Presets Only, Legacy Assets Available

### 5.1 Active Code

**Presets in GuitarDimensionsForm.vue:**
```javascript
om: {
  bodyLength: 495,
  bodyWidthUpper: 280,
  bodyWidthLower: 380,
  waistWidth: 260,
  bodyDepth: 110,
  scaleLength: 648,      // 25.5"
  nutWidth: 43,
  bridgeSpacing: 54,
  fretCount: 20,
  neckAngle: 0
}
```

**BridgeCalculator.vue Preset:**
```javascript
{ id:'om', label:'OM Acoustic (25.4")', scale_in:25.4, spread_mm:54.0, Ct_mm:2.0, Cb_mm:4.2, slotWidth_mm:3.2, slotLen_mm:80 }
```

### 5.2 Active Assets

**NONE in active directories**

### 5.3 Documentation References

- Referenced in BridgeCalculator and GuitarDimensionsForm

### 5.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Gibson OM _Project/`

| File | Description |
|------|-------------|
| `OM MDF mod.dxf` | MDF mould template |
| `OM_acoustic_guitar (2).dxf` | Full body outline |
| `OM_acoustic_guitar_en (1).pdf` | English blueprint |
| `OM_CNC_Checklists_with_Blanks.pdf` | CNC operation checklist |
| `OM_Graduation_Back_grid.svg` | Back graduation map |
| `OM_Graduation_Top_grid.svg` | Top graduation map |
| `OM_Graduation_Maps.pdf` | Combined graduation reference |
| `OMmod_mould.dxf` | Mould outline |

### 5.5 Missing/Planned

- [ ] Active DXF assets (migrate from legacy)
- [ ] Bracing pattern templates
- [ ] Graduation thickness maps integration

---

## 6. Gibson J-45

### Status: ⚠️ **ASSETS ONLY** - No Active Code, CAM Kit Available

### 6.1 Active Code

**NONE** - No presets in GuitarDimensionsForm.vue or other components

### 6.2 Active Assets

**Location:** `Guitar Design HTML app/J45_CAM_Import_Kit/`

| File | Description |
|------|-------------|
| `J45_Master_Dimensions.csv` | Master dimension spreadsheet |
| `J45_Master_Layout_R12.dxf` | CAM-ready master layout |
| (others in kit) | Import templates |

**Location:** `Guitar Design HTML app/10-10-2025/J45_ToolBox_Pack/`
- `preflight_j45.yaml` - Preflight configuration
- Other preflight configs

### 6.3 Documentation References

- Referenced in `COMPARE_MODE_BUNDLE_ROADMAP.md` as preset name "J45"

### 6.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Gibson J 45_ Project/`

| File | Description |
|------|-------------|
| `ag_45_dwg_040409.dwg` | Source AutoCAD file |
| `ag_45_dxf_040409.dxf` | Source DXF |
| `J45 DIMS.dxf` | Dimensions drawing |
| `J45 DIMS_CAM_Closed.dxf` | CAM-ready closed |
| `J45 DIMS_CAM_Closed_Layers.dxf` | CAM-ready with layers |
| `J45_CAM_Split.dxf` | Split layer version |
| `Guitar_DXF_Cleaner_Pack.zip` | Cleaning scripts |
| `DETAILS & DIMS/B SIZE DWG.dwg` | Detail drawings |
| `guitar dwgs/*.pdf` | Assembly drawings |

**Cleaning Scripts:**
- `clean_cam_closed_any_dxf.py`
- `clean_cam_closed_gui.py`
- `clean_cam_closed_preserve_layers.py`
- `clean_cam_closed_split_layers.py`

### 6.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset
- [ ] BridgeCalculator.vue preset
- [ ] Integration with CAM Import Kit
- [ ] Body outline in active assets

---

## 7. Jazz Bass

### Status: ⚠️ **STUB** - Preset Only

### 7.1 Active Code

**Presets in GuitarDimensionsForm.vue:**
```javascript
jazz_bass: {
  bodyLength: 490,
  bodyWidthUpper: 330,
  bodyWidthLower: 355,
  waistWidth: 280,
  bodyDepth: 46,
  scaleLength: 864,      // 34" bass scale
  nutWidth: 38,
  bridgeSpacing: 62,
  fretCount: 20,
  neckAngle: 0
}
```

### 7.2 Active Assets

**NONE**

### 7.3 Documentation References

- Mentioned in dimension archives: 490×345mm body

### 7.4 Legacy Reference

**NONE** - No Jazz Bass files in `Lutherier Project/`

### 7.5 Missing/Planned

- [ ] BridgeCalculator.vue preset (34" scale)
- [ ] Body outline DXF
- [ ] Pickup routing templates (single-coil jazz bass)
- [ ] Control plate template
- [ ] Pickguard template

---

## 8. Classical Guitar

### Status: ⚠️ **REFERENCE** - Scale/Rosette References Only

### 8.1 Active Code

**Scale Length References:**
- `services/api/app/instrument_geometry/scale_length.py`: `"classical": 650.0` (25.6")
- `packages/client/src/api/art-studio.ts`: `{ name: "Classical (650mm)", mm: 650.0 }`

**ArtStudioSidebar.vue Preset:**
```javascript
classical: { scale: 650, nut: 52, heel: 62 }
```

**Rosette Presets:**
- `services/api/app/calculators/rosette_calc.py`:
  - `classical_simple`: Simple B-W-B rosette (85mm soundhole)
  - `classical_mosaic`: Traditional mosaic rosette

**Inlay Presets:**
- `services/api/app/calculators/inlay_calc.py`:
  - `CLASSICAL = "classical"` - Markers at 5, 7, 9, 12 only
  - `dot_classical`: Classical style markers preset

**Bracing References:**
- `services/api/app/art_studio/bracing_router.py`:
  - `ladder-classical`: Fan-style bracing preset

### 8.2 Active Assets

**NONE**

### 8.3 Documentation References

- `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: Classical 25.6" (650mm)
- `docs/KnowledgeBase/Instrument_Geometry/Bridge_Compensation_Notes.md`: Classical straight saddle
- `docs/MM_0_MIXED_MATERIAL_QUICKREF.md`: Classical rosette use case

### 8.4 Legacy Reference

**NONE**

### 8.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset
- [ ] Body outline DXF
- [ ] Fan bracing templates
- [ ] Tie block bridge template

---

## 9. Archtop

### Status: ⚠️ **REFERENCE** - Bridge Preset + Legacy Measurement Kit

### 9.1 Active Code

**BridgeCalculator.vue Preset:**
```javascript
{ id:'arch', label:'Archtop (25.0")', scale_in:25.0, spread_mm:52.0, Ct_mm:1.8, Cb_mm:3.2, slotWidth_mm:3.0, slotLen_mm:75 }
```

**Instrument Geometry:**
- `services/api/app/instrument_geometry/profiles.py`: `instrument_type: "archtop"` in ProfileSpec
- `services/api/app/instrument_geometry/bridge_geometry.py`: `compute_archtop_bridge_placement()`

**UI Reference:**
- `docs/UI_NAVIGATION_AUDIT.md`: Lists "Archtop Calculator" as planned component
- `ORPHANED_CLIENT_FILES_INVENTORY.md`: Lists `ArchtopCalculator.vue` in orphaned files

### 9.2 Active Assets

**NONE in active directories**

### 9.3 Documentation References

- `docs/Instrument_Geometry_Migration_Plan.md`: Archtop modules planned
- `PATCH_W_DESIGN_CAM_WORKFLOW.md`: Archtop Calculator → Relief Mapper workflow

### 9.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Archtop Measurements/`

**Extensive Measurement Kit:**
| File | Description |
|------|-------------|
| `A Method for Specifying Contours of an Arched Plate.pdf` | Theory document |
| `Archtop_Contour_Full_Set_With_Readme.zip` | Complete kit |
| `Archtop_Contour_Measurement_Kit.pdf` | Measurement guide |
| `Archtop_Field_Manual_Complete.pdf` | Field manual |
| `Archtop_Field_Manual_With_DAquisto_Example.pdf` | D'Aquisto example |
| `Archtop_Graduation_Map_400mm.svg` | Graduation map |
| `Benedetto Back.jpg` / `Benedetto Front.jpg` | Reference photos |
| `DAquisto-Measurements-2.jpg` | D'Aquisto measurements |
| `Luthier_Archtop_Contour_Kit_FULL.zip` | Full contour kit |
| `Luthier_CAM_Toolkit.zip` | CAM toolkit |

**Generator Scripts:**
- `archtop_contour_generator.py`
- `sample_back_points.csv` / `sample_top_points.csv`
- `sample_outline_oval.dxf`

### 9.5 Missing/Planned

- [ ] ArchtopCalculator.vue component (orphaned, needs migration)
- [ ] Integration with contour generator
- [ ] Floating bridge calculations
- [ ] F-hole templates

---

## 10. PRS

### Status: ⚠️ **REFERENCE** - Scale References Only

### 10.1 Active Code

**Scale Length References:**
- `services/api/app/instrument_geometry/scale_length.py`: `"prs_standard": 635.0` (25")
- `packages/client/src/api/art-studio.ts`: `{ name: 'PRS (25")', mm: 635.0 }`

**ArtStudioSidebar.vue Preset:**
```javascript
prs_25: { scale: 635, nut: 42.5, heel: 55.5 }
```

**Instrument Router Presets:**
- `services/api/app/routers/instrument_router.py`: `prs_25` preset

**Radius Reference:**
- `services/api/app/instrument_geometry/radius_profiles.py`: `10" (254mm)` PRS style

**Inlay Reference:**
- `services/api/app/calculators/inlay_calc.py`: `BIRDS = "birds"` PRS-style bird inlays

### 10.2 Active Assets

**NONE**

### 10.3 Documentation References

- `docs/NECK_PROFILE_QUICKSTART.md`: PRS Wide Fat / Wide Thin mentioned
- `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: PRS 25" (635mm)
- `docs/KnowledgeBase/Instrument_Geometry/Radius_Theory_Compound.md`: 10"-16" PRS compound

### 10.4 Legacy Reference

**NONE**

### 10.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset
- [ ] BridgeCalculator.vue preset
- [ ] Body outline templates
- [ ] Bird inlay DXF templates
- [ ] 10"-16" compound radius integration

---

## 11. SG (Gibson)

### Status: ⚠️ **PLANNED** - Documentation Only

### 11.1 Active Code

**Neck Generator Preset (P2_1_NECK_GENERATOR_COMPLETE.md):**
```json
{
  "name": "SG (24.75\")",
  "scale_length_mm": 628.65,
  "nut_width_mm": 43.0,
  "fret_12_width_mm": 52.0
}
```

### 11.2 Active Assets

**NONE**

### 11.3 Documentation References

- `UNRESOLVED_TASKS_INVENTORY.md`: Body shape presets (Strat, Tele, LP, SG)
- `templates/env/.env.parametric`: Lists "sg" as body style option
- `PHASE_1_EXECUTION_PLAN.md`: SG (double-cutaway) mentioned
- `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: Gibson 24.75" scale

### 11.4 Legacy Reference

**NONE**

### 11.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset
- [ ] Body outline DXF
- [ ] Double-cutaway geometry
- [ ] Control cavity templates

---

## 12. Other Models (Brief References)

### ES-335 / Semi-Hollow
- **Reference:** `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: Gibson 24.75" scale
- **Status:** Name mentioned only, no implementation

### Explorer / Flying V / Firebird
- **Reference:** `templates/env/.env.parametric`: Listed as body style options
- **Status:** Name mentioned only, no implementation

### Soprano Ukulele
- **Reference:** `Lutherier Project/Lutherier Project/Soprano_Ukulele Project/`
- **Status:** Legacy reference only

### L-00 (Gibson)
- **Reference:** `Lutherier Project/Lutherier Project/Gibson OO_Project/`
- **Status:** Legacy reference only

### 00 (Gibson)
- **Reference:** `Lutherier Project/Lutherier Project/Gibson OO_Project/`
- **Status:** Legacy reference only

---

## Summary: Implementation Priority

### Tier 1: Production Ready
- ✅ **Stratocaster** - Full router, assets, presets

### Tier 2: Near Complete (Need Asset Migration)
- ⚠️ **Les Paul** - Has neck generator, extensive legacy assets
- ⚠️ **J-45** - Has CAM import kit, extensive legacy assets
- ⚠️ **OM** - Has graduation maps in legacy

### Tier 3: Stub Only (Need Full Implementation)
- ⚠️ **Telecaster** - Presets only
- ⚠️ **Dreadnought** - Presets only
- ⚠️ **Jazz Bass** - Presets only

### Tier 4: Reference Only (Need Everything)
- ⚠️ **Classical** - Scale/rosette references
- ⚠️ **Archtop** - Bridge preset, orphaned calculator
- ⚠️ **PRS** - Scale references
- ⚠️ **SG** - Doc references only

---

## Central Preset Location: GuitarDimensionsForm.vue

**File:** `packages/client/src/components/toolbox/GuitarDimensionsForm.vue`

**Current Presets (6 total):**
1. `dreadnought`
2. `om`
3. `les_paul`
4. `stratocaster`
5. `telecaster`
6. `jazz_bass`

**Missing from Presets:**
- `j45` (has CAM assets but no preset)
- `classical`
- `archtop`
- `prs`
- `sg`

---

## Neck Profile JSONs Status

**Documented but NOT CREATED:**
- `services/api/app/data/neck_profiles/strat_modern_c.json`
- `services/api/app/data/neck_profiles/tele_modern_c.json`
- `services/api/app/data/neck_profiles/les_paul_59.json`

**Directory Status:** `services/api/app/data/neck_profiles/` does NOT exist

---

## Recommendations

### Immediate Actions
1. **Create missing neck profile JSONs** per NECK_PROFILE_QUICKSTART.md spec
2. **Add J-45 preset** to GuitarDimensionsForm.vue (assets already exist)
3. **Migrate ArchtopCalculator.vue** from orphaned files

### Wave 14 Considerations (Per User Direction)
- NO model-specific routers like `telecaster_router.py`
- New scaffolding structure to be defined
- Library/calculator alignment is the goal

### Asset Migration Candidates
1. Les Paul DXF files from `Lutherier Project/` → active assets
2. J-45 DXF files from legacy → active assets  
3. OM graduation maps from legacy → active assets

---

**Report Generated:** January 2025  
**For:** Library/Calculator Alignment - Wave 14 Planning
