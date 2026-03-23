# Guitar Assembly & Design Tools — Complete Inventory

**Project:** The Production Shop  
**Date:** 2026-03-15  
**Purpose:** Full map of every calculator, designer, and tool related to guitar assembly.  
Extends the original remediation document which only captured the CalculatorHub gap.

---

## How to read this document

**Status codes:**
- `✅ Frontend + Backend` — both sides exist and are connected
- `⚡ Backend only` — calculator exists, no frontend component consuming it
- `🖼 Frontend only` — UI component exists, no backend (all client-side math)
- `🔗 Partial` — exists but scoped or incomplete (noted inline)
- `📦 Recovered` — in `__RECOVERED__/` — may be useful reference, not in active codebase

---

## 1. SCALE LENGTH & FRET GEOMETRY

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Scale Length Designer | `components/toolbox/ScaleLengthDesigner.vue` + `scale-length/` subfolder | 🖼 Frontend only | 4-tab tool: Scale Presets, String Tension, Intonation, Multi-Scale |
| Scale Presets | `scale-length/ScalePresetsTab.vue` + `ScalePresetsPanel.vue` | 🖼 Frontend only | Preset library with scale selection |
| String Tension (original) | `scale-length/TensionCalculatorTab.vue` + `TensionCalculatorPanel.vue` | 🖼 Frontend only | Older tension calculator inside ScaleLengthDesigner — **superseded by new StringTensionPanel.vue** |
| Intonation | `scale-length/IntonationTab.vue` + `IntonationPanel.vue` | 🖼 Frontend only | Saddle compensation / intonation offsets |
| Multi-Scale / Fan-Fret | `scale-length/MultiScaleTab.vue` + `MultiscalePanel.vue` | 🖼 Frontend only | Fan-fret geometry, per-string scale lengths |
| Fret Math (backend) | `services/api/app/instrument_geometry/neck/fret_math.py` | ⚡ Backend only | `FanFretPoint`, perpendicular fret geometry, full fan-fret math. No frontend. |
| Fret Math API | `services/api/app/api_v1/fret_math.py` | ⚡ Backend only | REST endpoint wrapping fret_math.py |
| Alternative Temperaments | `services/api/app/calculators/alternative_temperaments.py` | ⚡ Backend only | Just, Pythagorean, Meantone, 12-TET fret positions. No frontend. |
| Fret Slot CAM | `services/api/app/calculators/fret_slots_cam.py` + `fret_slots_fan_cam.py` | ✅ Frontend + Backend | Feeds `/cam/fret-slots` view (`FretSlottingView.vue`) |
| Fretboard Preview SVG | `components/FretboardPreviewSvg.vue` | 🖼 Frontend only | Visual fretboard with scale/radius inputs |
| Inlay Fret Positions | `components/art/art_studio_inlay/composables/useInlayFrets.ts` | 🖼 Frontend only | Fret position table embedded in inlay designer |
| Fret Position Table | `components/art/art_studio_inlay/FretPositionTable.vue` | 🖼 Frontend only | Display component for fret positions |

---

## 2. NECK GEOMETRY

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Neck Generator (Les Paul) | `components/generators/neck/LesPaulNeckGenerator.vue` + `les_paul_neck/` composables | ✅ Frontend + Backend | Neck angle, fretboard radius, heel profile, exports DXF |
| Neck Taper / Outline | `services/api/app/instrument_geometry/neck_taper/api_router.py` | ⚡ Backend only | `POST /instrument/neck_taper/outline` — tapered neck outline as coordinate list. No frontend. |
| Neck Router (models) | `services/api/app/routers/neck_router.py` + `routers/neck/` | ✅ Frontend + Backend | Strat, Tele, PRS, Les Paul neck models + nut break angle endpoint |
| Neck Angle (data field) | `components/toolbox/composables/useGuitarDimensions.ts` | 🖼 Frontend only | Stored as raw field, no dedicated calculator — **see R-6 in remediation doc** |
| Neck Geometry | `services/api/app/routers/neck/geometry.py` | ⚡ Backend only | Neck profile cross-sections |
| Nut Break Angle | `services/api/app/calculators/headstock_break_angle.py` | ⚡ Backend only | Full calculator with angled + flat headstock modes. Endpoint at `POST /neck/break-angle`. **No frontend component.** |
| Fretboard Compound Radius | `components/toolbox/FretboardCompoundRadius.vue` | 🖼 Frontend only | Compound radius fretboard spec calculator |
| Neck Generator utility | `packages/client/src/utils/neck_generator.ts` | 🖼 Frontend only | Fret position math, neck taper geometry — used internally by CAM pipeline |
| Overhang Channel | `services/api/app/calculators/overhang_channel_calc.py` | ⚡ Backend only | 24-fret fretboard overhang channel routing geometry (GAP-05). No frontend. |

---

## 3. BRIDGE & SADDLE

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Bridge Calculator (toolbox) | `components/toolbox/BridgeCalculator.vue` + `composables/useBridgeGeometry.ts` + `useBridgePresets.ts` + `useBridgeUnits.ts` | 🖼 Frontend only | Saddle compensation (Ct/Cb), saddle angle, slot polygon, SVG preview, presets. No structural outputs. |
| Bridge Calculator Panel | `components/bridge_calculator_panel/BridgeCalculatorPanel.vue` + `composables/useBridgeState.ts` | 🖼 Frontend only | Second bridge calculator implementation — seeds geometry for Bridge Lab, exports DXF. Separate from above. |
| Bridge Lab View | `views/BridgeLabView.vue` | ✅ Frontend + Backend | Full bridge design lab |
| Bridge Break Angle | `services/api/app/calculators/bridge_break_angle.py` | ⚡ Backend only | **v1 — needs R-7 correction.** Endpoint at `POST /bridge/break-angle`. No frontend except break angle input in StringTensionPanel (manual mode). |
| Bridge Presets Router | `services/api/app/routers/bridge_presets_router.py` | ✅ Frontend + Backend | Serves bridge family presets + break angle endpoint |
| Archtop Bridge Fit | `services/api/app/routers/cam/guitar/` + `__RECOVERED__/C_archtop_pipeline/archtop_cam_router.py` | 🔗 Partial | Archtop calculator frontend (`ArchtopCalculator.vue`) exists; backend fit endpoint implemented but bridge/saddle DXF generators are stubs |
| Bridge Location | **MISSING** | ❌ Not found | No dedicated "where does the saddle line go" calculator surfaced anywhere. The math is inside `useBridgeGeometry.ts` (`scale + compensation`) but not a standalone tool. |
| Intonation Panel | `components/toolbox/scale-length/IntonationPanel.vue` | 🖼 Frontend only | Compensation offsets — related to bridge location |

---

## 4. BODY GEOMETRY & DIMENSIONS

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Guitar Body Dimensions | `views/GuitarDimensionsView.vue` → `components/toolbox/GuitarDimensionsForm.vue` | 🖼 Frontend only | Body length, bout widths, waist, depth, scale, nut width, bridge spacing, fret count, neck angle — parametric input |
| Guitar Body Preview (SVG) | `components/toolbox/guitar-dimensions/GuitarBodyPreview.vue` | 🖼 Frontend only | SVG body outline from dimension inputs |
| Guitar Design Hub | `views/GuitarDesignHubView.vue` → `components/toolbox/GuitarDesignHub.vue` | 🖼 Frontend only | Hub landing page for body outline generator, archtop, bracing, etc. |
| Instrument Design (per model) | `views/InstrumentDesignView.vue` (route `/design/:instrumentId`) | ✅ Frontend + Backend | Per-instrument spec page with DXF export |
| Body Outline Generator | `services/api/app/instrument_geometry/body/parametric.py` | ⚡ Backend only | Parametric body outline geometry |
| Strat Body Generator | `services/api/app/generators/stratocaster_body_generator.py` | ⚡ Backend only | Stratocaster body geometry generator |
| Les Paul Body Generator | `services/api/app/generators/lespaul_body_generator.py` | ⚡ Backend only | Les Paul body geometry generator |
| Electric Body Router | `services/api/app/routers/instruments/guitar/electric_body_router.py` | ✅ Frontend + Backend | Electric body outline endpoints |
| Body Volume | `services/api/app/calculators/acoustic_body_volume.py` | ⚡ Backend only | Reverse-engineers acoustic body volume from bout dimensions. Validated vs Martin D-28. No frontend. |
| Blueprint Lab | `views/BlueprintLab.vue` | ✅ Frontend + Backend | Photo-to-vector pipeline, body outline extraction from photos |
| Instrument Geometry | `views/InstrumentGeometryView.vue` → `components/InstrumentGeometryPanel.vue` | 🖼 Frontend only | Scale length, fan-fret, fret CAM, fretboard radius — CAM-oriented |
| Center Line / Body Center | **MISSING** | ❌ Not found | No dedicated body centerline or reference datum calculator found |

---

## 5. PICKUP ROUTING & HARDWARE LAYOUT

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Pickup Position Calculator | `services/api/app/calculators/pickup_position_calc.py` + `routers/instruments/guitar/pickup_calculator_router.py` | ⚡ Backend only | Full calculator: Strat SSS, LP HH, HSS, custom. Endpoint at `POST /instruments/guitar/pickup-calculator/calculate`. **No frontend component.** |
| Hardware Layout | `components/toolbox/HardwareLayout.vue` | 🖼 Frontend only | File exists; appears scaffolded — no meaningful grep hits for bridge/tuner/pickup placement content |
| Wiring Workbench | `components/toolbox/WiringWorkbench.vue` | 🖼 Frontend only | Output impedance, RC tone cutoff, treble bleed calculator, switch validator, tone cap calculator |
| Neck Pocket / Joint | **MISSING** | ❌ Not found | No dedicated neck pocket dimension or neck-to-body joint calculator |
| Tremolo / Floyd Routing | **MISSING** | ❌ Not found | No tremolo spring cavity or Floyd Rose routing calculator |
| Control Cavity | **MISSING** | ❌ Not found | No control cavity layout tool found |

---

## 6. BRACING & TOP GEOMETRY

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Bracing Calculator (toolbox) | `components/toolbox/BracingCalculator.vue` | 🔗 Partial | Component exists; scope unclear without full read |
| Art Studio Bracing | `components/art/ArtStudioBracing.vue` + `art/bracing/` (6 files) | ✅ Frontend + Backend | Full bracing suite: BraceBatchPanel, BraceSinglePanel, BraceResultsPanel, useBraceBatch, useSingleBrace, useBracingPresets |
| Bracing Calc (backend) | `services/api/app/calculators/bracing_calc.py` | ✅ Frontend + Backend | Façade over `pipelines/bracing/bracing_calc.py` — parabolic, scalloped, triangular profiles |
| Bracing Presets | `services/api/app/art_studio/bracing_presets_bridge.py` | ✅ Frontend + Backend | Preset patterns fed to frontend |
| Radius Dish Designer | `components/toolbox/RadiusDishDesigner.vue` + `radius-dish/` subfolder | 🖼 Frontend only | 4-panel tool: RadiusDishCalculator, RadiusDishCncSetup, RadiusDishDesign, RadiusDishDocs |
| Enhanced Radius Dish | `components/toolbox/EnhancedRadiusDish.vue` | 🖼 Frontend only | Advanced compound curve radius dish |
| Fretboard Compound Radius | `components/toolbox/FretboardCompoundRadius.vue` | 🖼 Frontend only | Compound radius fretboard (conical) calculations |

---

## 7. ART STUDIO — DECORATIVE & CNC DESIGN

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Rosette Designer | `components/toolbox/RosetteDesigner.vue` + `components/art/ArtStudioRosette.vue` | ✅ Frontend + Backend | Full rosette pipeline with channel routing G-code |
| Rosette Calculator | `services/api/app/calculators/rosette_calc.py` | ✅ Frontend + Backend | Rosette geometry math |
| Soundhole Designer | `views/art-studio/SoundholeDesignerView.vue` | ✅ Frontend + Backend | Soundhole layout + CAM |
| Binding Designer | `views/art-studio/BindingDesignerView.vue` | ✅ Frontend + Backend | Binding channel geometry |
| Purfling Designer | `views/art-studio/PurflingDesignerView.vue` | ✅ Frontend + Backend | Purfling strip layout |
| Headstock Designer | `views/art-studio/HeadstockDesignerView.vue` | ✅ Frontend + Backend | Headstock shape design |
| Inlay Designer | `views/art-studio/InlayDesignerView.vue` + `components/art/art_studio_inlay/` | ✅ Frontend + Backend | Full inlay design suite with fret position integration |
| Inlay Patterns | `views/art-studio/InlayPatternView.vue` | ✅ Frontend + Backend | Pattern library |
| Fret Markers | `views/art-studio/FretMarkersView.vue` | ✅ Frontend + Backend | Fret marker layout and CAM |
| Inlay Calculator | `services/api/app/calculators/inlay_calc.py` | ✅ Frontend + Backend | Dot, diamond inlay geometry |
| Relief Carving | `views/art-studio/ReliefCarvingView.vue` | ✅ Frontend + Backend | Relief carving CAM |
| V-Carve | `views/art-studio/VCarveView.vue` | ✅ Frontend + Backend | V-carve toolpath generation |

---

## 8. FINISH & ELECTRONICS

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Finish Planner | `components/toolbox/FinishPlanner.vue` | 🖼 Frontend only | Finish schedule planning and tracking |
| Finishing Designer | `components/toolbox/FinishingDesigner.vue` + `finishing/` subfolder | 🖼 Frontend only | Burst controls, finish types, labor input/results |
| Wiring Workbench | `components/toolbox/WiringWorkbench.vue` | 🖼 Frontend only | Output impedance, treble bleed, switch validator, tone cap |
| Wiring Calculator suite | `services/api/app/calculators/wiring/` | ⚡ Backend only | Wiring math — unclear if connected to frontend |

---

## 9. CAM OPERATIONS (guitar-specific)

| Tool | Location | Status | Notes |
|------|----------|--------|-------|
| Fret Slot CAM | `views/cam/FretSlottingView.vue` | ✅ Frontend + Backend | |
| Contour Cutting | `views/cam/ContourCuttingView.vue` | ✅ Frontend + Backend | |
| Pocket Clearing | `views/cam/PocketClearingView.vue` | ✅ Frontend + Backend | |
| Surfacing | `views/cam/SurfacingView.vue` | ✅ Frontend + Backend | |
| Drilling | `views/cam/DrillingView.vue` | ✅ Frontend + Backend | |
| Toolpath Simulator | `views/cam/ToolpathSimulatorView.vue` | ✅ Frontend + Backend | |
| CAM Advisor | `views/cam/CamAdvisorView.vue` | ✅ Frontend + Backend | |
| DXF → G-code | `views/DxfToGcodeView.vue` | ✅ Frontend + Backend | |
| Binding Offset Geometry | `services/api/app/cam/binding/offset_geometry.py` | ⚡ Backend only | |

---

## 10. KEY GAPS — NO TOOL EXISTS ANYWHERE

These are operations every builder performs that have no calculator in the codebase:

| Gap | What it would calculate |
|-----|------------------------|
| **Body centerline / datum setup** | Reference datum from body edge, centerline from lower bout, bridge pin hole reference grid |
| **Bridge location** | Saddle line position = nut to scale length + average compensation; pin hole spacing from centerline |
| **Neck pocket dimensions** | Pocket depth from desired neck angle + bridge height + action target; pocket width/length from heel spec |
| **Pickup routing dimensions** | Rout dimensions per pickup type (SC, HB, P90) + clearance; rout centers from bridge saddle line |
| **Control cavity layout** | Cavity dimensions, pot spacing, jack location by body type |
| **Tremolo / Floyd routing** | Spring cavity depth, block pocket, stud spacing by model |
| **Nut slot depths** | Per-string nut slot depth from string gauge and desired action at first fret |
| **Alternative temperament frontend** | `alternative_temperaments.py` exists and is complete — no frontend |
| **Body volume frontend** | `acoustic_body_volume.py` validated and complete — no frontend |
| **Pickup position frontend** | `pickup_position_calc.py` complete with full router — no frontend |
| **Overhang channel frontend** | `overhang_channel_calc.py` complete — no frontend |

---

## 11. DUPLICATE / OVERLAPPING TOOLS

These do similar things and should be reconciled during unification:

| Overlap | Files | Recommendation |
|---------|-------|----------------|
| Two bridge calculators | `toolbox/BridgeCalculator.vue` vs `bridge_calculator_panel/BridgeCalculatorPanel.vue` | Consolidate — BridgeCalculatorPanel is newer, feeds Bridge Lab |
| Two tension calculators | `scale-length/TensionCalculatorTab.vue` vs new `string-tension/StringTensionPanel.vue` | Retire TensionCalculatorTab; StringTensionPanel is the authoritative version |
| Two ScientificCalculator versions | `ScientificCalculator.vue` vs `ScientificCalculatorV2.vue` | V2 appears to be a refactor in progress — determine which is active |
| Bracing in two places | `toolbox/BracingCalculator.vue` vs `art/ArtStudioBracing.vue` | ArtStudio version is fully developed; toolbox version may be scaffold |

---

*This inventory supersedes the tools list in `calculator-unification-remediation.md` section 1.*  
*Cross-reference with remediation tasks R-1 through R-7 for prioritization.*
