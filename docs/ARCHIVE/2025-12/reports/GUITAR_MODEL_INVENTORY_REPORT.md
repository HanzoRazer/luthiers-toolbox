you# Guitar Model Inventory Report

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
| Telecaster | ⚠️ Presets only | ❌ None | ✅ Plans PDF | **Stub** |
| Les Paul | ✅ Neck generator + presets | ❌ None | ✅ Extensive | **Partial** |
| Dreadnought | ⚠️ Presets only | ❌ None | ✅ Martin 1937 | **Stub** |
| OM / 000 | ⚠️ Presets only | ❌ None | ✅ Gibson OM | **Stub** |
| J-45 | ❌ None | ✅ CAM Import Kit | ✅ Extensive | **Assets Only** |
| Jazz Bass | ⚠️ Presets only | ❌ None | ❌ None | **Stub** |
| Classical | ⚠️ Scale/rosette refs | ❌ None | ✅ Plans PDF/DXF | **Reference** |
| Archtop | ⚠️ Bridge calc preset | ❌ None | ✅ Measurement kit | **Reference** |
| PRS | ⚠️ Scale refs only | ❌ None | ❌ None | **Reference** |
| SG | ⚠️ Doc refs only | ❌ None | ✅ Plans DXF/PDF | **Planned** |
| **Jumbo (J-200)** | ❌ None | ❌ None | ✅ DXF/PDF | **Legacy** |
| **Ukulele** | ❌ None | ✅ DXF (16+ files) | ✅ Soprano project | **Assets Only** |
| **Gibson OO/L-00** | ⚠️ Test scripts | ❌ None | ✅ DXF/PDF | **Test Ref** |
| **Flying V** | ❌ None | ❌ None | ✅ DWG/PDF | **Legacy** |
| **ES-335** | ❌ None | ❌ None | ✅ PDF (7 files) | **Legacy** |
| **Explorer** | ❌ None | ❌ None | ✅ PDF (5 files) | **Legacy** |
| **Firebird** | ❌ None | ❌ None | ✅ PDF | **Legacy** |
| **Moderne** | ❌ None | ❌ None | ✅ DXF/PDF | **Legacy** |

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

## 12. Jumbo (J-200 Style)

### Status: ⚠️ **LEGACY ASSETS** - DXF/PDF Available, No Active Code

### 12.1 Active Code

**NONE** - No presets in GuitarDimensionsForm.vue or other components

### 12.2 Active Assets

**NONE in active directories**

### 12.3 Documentation References

- `Guitar Design HTML app/_G_ Thang - Acoustic Guitar Design Tool_files/`: References "Jumbo (J-200) style SS Guitar"
- `ScaleLengthDesigner.vue`: Mentions "jumbos" in fret height context (medium jumbo frets)

### 12.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Guitar Plans/`

| File | Description |
|------|-------------|
| `Guitar-Jumbo-MM.dxf` | Jumbo body outline (metric) |
| `Guitar-Jumbo-MM-A4.pdf` | A4 format blueprint |
| `Guitar-Jumbo-MM-A0.pdf` | A0 format blueprint |
| `JUMBO-CARLOS-1-3.pdf` | Carlos Jumbo page 1 |
| `JUMBO-CARLOS-2-3.pdf` | Carlos Jumbo page 2 |
| `JUMBO-CARLOS-3-3.pdf` | Carlos Jumbo page 3 |

### 12.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset
- [ ] BridgeCalculator.vue preset
- [ ] Body outline in active assets
- [ ] Soundhole dimensions (larger than dreadnought)

---

## 13. Ukulele (Soprano/Concert/Tenor/Baritone)

### Status: ⚠️ **ACTIVE ASSETS** - DXF Files Available, No Code Integration

### 13.1 Active Code

**NONE** - No presets in any calculator

### 13.2 Active Assets

**Location:** `Soprano Ukuele/` (root level - note typo in folder name)

| File | Description |
|------|-------------|
| `Soprano_ukulele (1).dxf` | Soprano body outline |
| `Soprano_ukulele - Copy (2-16).dxf` | Multiple copies (16+ DXF files) |

### 13.3 Documentation References

- `Guitar Design HTML app/_G_ Thang - Acoustic Guitar Design Tool_files/`: References Soprano, Concert, Tenor, Baritone sizes
- `__ARCHIVE__/docs_historical/LEGACY_PIPELINE_DISCOVERY_SUMMARY.md`: "Ukuleles (Soprano, Concert)"

### 13.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Soprano_Ukulele Project/`

| File | Description |
|------|-------------|
| `Soprano_ukulele.dxf` | Master DXF |
| `Soprano_ukulele (1).dxf` | Copy |
| `Soprano_ukulele_en.pdf` | English blueprint |
| `Soprano_ukulele_en (1).pdf` | Blueprint copy |

**Location:** `Lutherier Project/Lutherier Project/Guitar Plans/`

| File | Description |
|------|-------------|
| `Soprano_ukulele.dxf` | DXF copy |
| `Soprano_ukulele_en.pdf` | PDF copy |
| `Soprano-Ukelele-MM.dxf` | Metric version |
| `Soprano-Ukelele-MM.pdf` | Metric PDF |
| `Ukelele-Concert-MM.pdf` | Concert size PDF |
| `Ukulele+Crown+Sander.zip` | Crown sander jig |

### 13.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue presets (soprano, concert, tenor, baritone)
- [ ] Scale length presets (soprano: 345mm, concert: 380mm, tenor: 430mm, baritone: 510mm)
- [ ] Consolidate active folder name (fix "Ukuele" typo)

---

## 14. Gibson OO / L-00

### Status: ⚠️ **LEGACY ASSETS + TEST INTEGRATION** - Used in Blueprint Tests

### 14.1 Active Code

**Test Integration:**
- `test_real_blueprint_gibson_l00.py`: Full blueprint test using Gibson L-00
- `test_contour_reconstruction.ps1`: LINE + SPLINE chaining test with L-00

### 14.2 Active Assets

**NONE in active directories** (used via legacy path in tests)

### 14.3 Documentation References

- `PHASE3_2_QUICKREF.md`: Gibson L-00 as test reference file
- `PHASE3_3_QUICKSTART.md`: "Test with Gibson L-00 DXF"
- Multiple test scripts reference `Gibson_L-00.dxf`

### 14.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Gibson OO_Project/`

| File | Description |
|------|-------------|
| `1940 Gibson L-00.pdf` | Historical 1940 spec |
| `Acoustic_guitar_00 (2).dxf` | Body outline |
| `Acoustic_guitar_00_en (1).pdf` | English blueprint |
| `Gibson_L-00 (2).dxf` | L-00 outline |
| `Gibson_L-00_en (1).pdf` | L-00 blueprint |
| `L-OO mould.dxf` | Mould template |

**Location:** `Lutherier Project/Lutherier Project/Guitar Plans/`

| File | Description |
|------|-------------|
| `Gibson_L-00.dxf` | L-00 outline |
| `Gibson_L-00_en.pdf` | L-00 blueprint |
| `Gibson-L00-MM.dxf` | Metric version |
| `Gibson-L0-IN.pdf` | Inch version |
| `Acoustic_guitar_00.dxf` | 00 body outline |
| `Acoustic_guitar_00_en.pdf` | 00 blueprint |

### 14.5 Missing/Planned

- [ ] GuitarDimensionsForm.vue preset (L-00 is smaller than OM)
- [ ] Migrate DXF to active assets (used in tests)
- [ ] Document body dimensions (~ 380mm lower bout)

---

## 15. Flying V

### Status: ⚠️ **LEGACY ASSETS** - DWG/PDF Available

### 15.1 Active Code

**NONE** - No presets or components

### 15.2 Active Assets

**NONE**

### 15.3 Documentation References

- `templates/env/.env.parametric`: Lists "explorer, flying_v, firebird" as body style options

### 15.4 Legacy Reference

**Location:** `Lutherier Project/Lutherier Project/Guitar Plans/`

| File | Description |
|------|-------------|
| `59_Flying_V.dwg` | 1959 Flying V AutoCAD |
| `Flying_V_11.dwg` | Flying V variant |
| `Gibson58FlyingV.pdf` | 1958 Flying V blueprint |
| `Gibson83FlyingV.pdf` | 1983 Flying V blueprint |

### 15.5 Missing/Planned

- [ ] Convert DWG to DXF (CAM-ready)
- [ ] GuitarDimensionsForm.vue preset
- [ ] Body outline in active assets
- [ ] Note: Unusual body shape requires special handling

---

## 16. Gibson (General Brand References)

### Status: 📋 **INDEX** - References to Multiple Gibson Models

The "Gibson" brand appears extensively across the codebase. Key Gibson models documented separately:
- **Les Paul** - Section 3 (Partial implementation)
- **SG** - Section 11 (Planned)
- **J-45** - Section 6 (Assets only)
- **L-00 / OO** - Section 14 (Legacy + tests)
- **ES-335** - Section 17 (Reference only)

### 16.1 Gibson-Specific Legacy Assets

**Location:** `Lutherier Project/Lutherier Project/Guitar Plans/`

| Category | Files |
|----------|-------|
| **SG Series** | `00-Gibson-1963-SG-JR.pdf`, `01-Gibson-SG-Complete-Template.pdf`, `02-Gibson-SG-Pickguard.pdf`, `03-Gibson-SG-Body-Headstock.pdf`, `04-Gibson-SG-Plans.pdf`, `05-Gibson-SG-full-assembled.pdf`, `DWG-00-Gibson-SG.dwg`, `DXF-00-Gibson-SG.dxf`, `Gibson-SG-Custom.pdf`, `Gibson-SG-Pickguard.pdf` |
| **ES-335 Series** | `Gibson-335-Body-Front.pdf`, `Gibson-335-Dot-Complete.pdf`, `Gibson-335-Front-Contour.pdf`, `Gibson-335-Front-Pickups-Bridge.pdf`, `Gibson-335-Full-1.pdf`, `Gibson-335-Neck-Headstock-Side.pdf`, `Photoshop-Gibson-335-Full.psd` |
| **Les Paul Series** | `Gibson-Les-Paul-1950s.pdf`, `Gibson-Les-Paul-59-Complete.pdf`, `Gibson-Les-Paul-59-Front-Body-Headstock.pdf`, `Gibson-Les-Paul-Custom.pdf`, `Gibson-Les-Paul-Isolines.pdf`, `Gibson-Les-Paul-Junior-Double-Cut.pdf`, `Gibson-Les-Paul-Junior-Single-Cut.pdf`, `Les-Paul-*.pdf` (multiple) |
| **Explorer/Moderne/Firebird** | `Gibson-Explorer-00-1958.pdf`, `Gibson-Explorer-01.pdf` through `05`, `Gibson-Firebird-Studio.pdf`, `Gibson-Moderne-01.pdf` through `03` |
| **Double Neck** | `Gibson-Double-Neck-esd1275.pdf` |
| **Melody Maker** | `Gibson-Melody-Maker.pdf` |

### 16.2 Gibson Scale Length Standard

- **24.75" (628.65mm)**: Les Paul, SG, ES-335, Explorer, Flying V, Firebird
- Defined in: `services/api/app/instrument_geometry/scale_length.py`: `"gibson_standard": 628.65`

---

## 17. Other Models (Brief References)

### ES-335 / Semi-Hollow
- **Reference:** `docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md`: Gibson 24.75" scale
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-335-*.pdf` (7 files)
- **Status:** Extensive legacy blueprints, no active code

### Explorer
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-Explorer-*.pdf` (5 files)
- **Status:** Legacy blueprints only

### Firebird
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-Firebird-Studio.pdf`
- **Status:** Single PDF reference

### Moderne
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-Moderne-*.pdf` (3 files), `Gibson-Moderne-01.dxf`
- **Status:** DXF available, no active code

### Melody Maker
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-Melody-Maker.pdf`
- **Status:** Single PDF reference

### Double Neck (EDS-1275)
- **Legacy Assets:** `Lutherier Project/Guitar Plans/Gibson-Double-Neck-esd1275.pdf`
- **Status:** Single PDF reference

---

## Summary: Implementation Priority

### Tier 1: Production Ready
- ✅ **Stratocaster** - Full router, assets, presets

### Tier 2: Near Complete (Need Asset Migration)
- ⚠️ **Les Paul** - Has neck generator, extensive legacy assets
- ⚠️ **J-45** - Has CAM import kit, extensive legacy assets
- ⚠️ **OM** - Has graduation maps in legacy
- ⚠️ **Gibson L-00/OO** - Used in blueprint tests, legacy assets
- ⚠️ **Ukulele (Soprano)** - Active DXF assets exist

### Tier 3: Stub Only (Need Full Implementation)
- ⚠️ **Telecaster** - Presets only
- ⚠️ **Dreadnought** - Presets only
- ⚠️ **Jazz Bass** - Presets only
- ⚠️ **Jumbo** - Legacy DXF/PDF available

### Tier 4: Reference Only (Need Everything)
- ⚠️ **Classical** - Scale/rosette references
- ⚠️ **Archtop** - Bridge preset, orphaned calculator
- ⚠️ **PRS** - Scale references
- ⚠️ **SG** - Extensive legacy PDFs, DXF available
- ⚠️ **Flying V** - Legacy DWG/PDF available
- ⚠️ **ES-335** - Extensive legacy PDFs

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
