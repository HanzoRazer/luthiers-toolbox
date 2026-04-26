# Instrument Model Coverage Audit

**Date**: 2026-04-26  
**Methodology**: Production paths only — excluded `sandbox/`, `docs/archive/recovered/`, `__pycache__/`, `node_modules/`, `.git/`, `services/api/test_temp/`. Live grep on current codebase. Documentation claims cross-referenced against actual code presence.

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total instrument models identified | 24 |
| COMPLETE END-TO-END | 2 |
| DESIGN ONLY (Stages A-D) | 3 |
| CAM PARTIAL | 7 |
| GENERATOR ONLY | 5 |
| SPEC ONLY | 4 |
| NAMED ONLY (no implementation) | 3 |

**Key finding**: Only **2 instruments** (Les Paul, Smart Guitar) have verified complete end-to-end pipelines. The remaining 22 instruments break down at various stages, with CAM and build documentation being the most common gaps.

---

## 1. Instrument Model Inventory

### 1.1 Electric Solid-Body Guitars

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **Stratocaster** | `instrument_specs.py`, `fender_stratocaster.json` (222 lines) | `stratocaster_body_generator.py` | `stratocaster_cam_router.py` | InstrumentGeometryPanel, StratocasterNeckGenerator |
| **Les Paul** | `instrument_specs.py`, `gibson_les_paul.json` (592 lines, 669-pt polygon) | `lespaul_body_generator.py`, `lespaul_dxf_reader.py` | `body_gcode_router.py` (18,394 G-code lines) | LesPaulNeckGenerator |
| **Telecaster** | `instrument_specs.py`, `fender_telecaster.json` | `electric_body_generator.py` | Generic | InstrumentGeometryPanel |
| **Gibson SG** | `instrument_specs.py`, `gibson_sg.json` | `electric_body_generator.py` (4502-pt DXF) | Generic | None |
| **Flying V** | `instrument_specs.py`, `gibson_flying_v_1958.json` | `electric_body_generator.py`, `flying_v_cam_router.py` | `pocket_generator.py` | None |
| **Gibson Explorer** | `instrument_specs.py`, `gibson_explorer.json` (241 lines) | `electric_body_generator.py` (24-pt outline) | Generic | None |
| **Melody Maker** | `instrument_specs.py`, `gibson_melody_maker.json` | None (referenced only) | None | None |
| **Harmony H44** | `outlines.py` (DXF reference) | `electric_body_generator.py` | None | None |
| **JS1000** | `outlines.py` (DXF reference, 345 pts) | `electric_body_generator.py` | None | None |

### 1.2 Electric Semi-Hollow Guitars

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **ES-335** | `instrument_specs.py`, `gibson_es_335.json` | None | None | None |
| **EDS-1275** | None (phantom entry) | None | None | None |

### 1.3 Smart/Digital Guitars

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **Smart Guitar v1** | `smart_guitar_v1.json` (1027 lines, 16 cavities, Pi 5 + Teensy) | `smart_guitar_dxf.py` (layered CAM) | Layer-based cavity routing | Smart Guitar DXF router |

### 1.4 Acoustic Flat-Top Guitars

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **Dreadnought** | `instrument_specs.py`, `martin_d28_1937.json/.py` | `acoustic_body_generator.py`, `bezier_body.py` | `acoustic_cam_router.py` | GuitarDimensionsForm |
| **OM/000** | `instrument_specs.py`, `martin_om28.json` | `acoustic_body_generator.py`, `bezier_body.py` | `om_cam_router.py` | GuitarDimensionsForm |
| **Jumbo** | `instrument_specs.py`, `carlos_jumbo.json` (outline pending) | `acoustic_body_generator.py`, `bezier_body.py` | Generic | SpiralSoundholeDesigner |
| **Parlor** | `bezier_body.py` (preset only) | `bezier_body.py` | None | None |
| **J-45** | `instrument_specs.py` | `acoustic_body_generator.py` | Generic | None |
| **Classical** | `instrument_specs.py`, `outlines.py` DXF | `acoustic_body_generator.py` | None | GuitarDimensionsForm |
| **Gibson L-00** | `instrument_specs.py`, `outlines.py` DXF | `acoustic_body_generator.py` (fallback to Parlor) | None | None |

### 1.5 Archtop Guitars

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **Jumbo Archtop** | `instrument_specs.py` | None | `archtop_cam_router.py` | ArchtopCalculator |
| **Benedetto 17"** | `instrument_specs.py`, `BENEDETTO_17_ARCHTOP_SPECS.md` | None | None | ArchtopCalculator |
| **Selmer-Maccaferri** | `selmer_maccaferri_dhole.py` | None | None | None |

### 1.6 Other String Instruments

| Model | Spec Location | Generator Location | CAM Location | Frontend |
|-------|--------------|-------------------|--------------|----------|
| **Cuatro Venezolano** | `instrument_specs.py`, `ibg/instrument_body_generator.py` | `InstrumentBodyGenerator` | None | None |
| **Cuatro Puertorriqueño** | `guitars/cuatro_puertorriqueno.py` (partial) | None | None | None |
| **Bass 4-String** | `instrument_specs.py` (placeholder) | None | None | None |
| **Soprano Ukulele** | `outlines.py` (DXF, 176.9×200mm) | None | None | None |
| **Concert Ukulele** | `outlines.py` (DXF, 203.1×393.7mm) | None | None | None |
| **Mandolin** | `outlines.py` (DXF reference) | None | None | None |
| **Octave Mandolin** | `outlines.py` (DXF, 280×350mm) | None | None | None |

---

## 2. Pipeline Stage Coverage Matrix

### Legend
- **A** = Specification (JSON/Pydantic/dataclass)
- **B** = Body Outline Generation (DXF output)
- **C** = Neck/Headstock Generation
- **D** = Cavity/Component Geometry
- **E** = CAM Pipeline (toolpaths)
- **F** = G-code Output
- **G** = Build Documentation

| Instrument | A | B | C | D | E | F | G | Classification |
|------------|---|---|---|---|---|---|---|----------------|
| **Les Paul** | FULL | PARAMETRIC | FULL | FULL | FULL | FULL (18k lines) | PARTIAL | **COMPLETE E2E** |
| **Smart Guitar** | FULL (1027 lines) | PARAMETRIC | N/A (headless) | FULL (16 cavities) | FULL (layered) | FULL | PARTIAL | **COMPLETE E2E** |
| **Stratocaster** | FULL | PARAMETRIC | FULL | FULL | PARTIAL | PARTIAL | NONE | **CAM PARTIAL** |
| **Dreadnought** | FULL | PARAMETRIC | PARTIAL | PARTIAL | PARTIAL | PARTIAL | NONE | **CAM PARTIAL** |
| **Telecaster** | FULL | REFERENCE | PARTIAL | PARTIAL | GENERIC | GENERIC | NONE | **CAM PARTIAL** |
| **Flying V** | FULL | REFERENCE | NONE | PARTIAL | PARTIAL | PARTIAL | NONE | **CAM PARTIAL** |
| **Explorer** | FULL (24-pt) | REFERENCE | NONE | NONE | GENERIC | GENERIC | NONE | **CAM PARTIAL** |
| **OM/000** | FULL | PARAMETRIC | PARTIAL | PARTIAL | PARTIAL | PARTIAL | NONE | **CAM PARTIAL** |
| **Jumbo Archtop** | PARTIAL | NONE | NONE | NONE | PARTIAL | PARTIAL | NONE | **CAM PARTIAL** |
| **SG** | FULL | REFERENCE | NONE | NONE | NONE | NONE | NONE | **GENERATOR ONLY** |
| **J-45** | PARTIAL | REFERENCE | NONE | NONE | NONE | NONE | NONE | **GENERATOR ONLY** |
| **Classical** | PARTIAL | REFERENCE | NONE | NONE | NONE | NONE | NONE | **GENERATOR ONLY** |
| **Gibson L-00** | PARTIAL | FALLBACK | NONE | NONE | NONE | NONE | NONE | **GENERATOR ONLY** |
| **JS1000** | NONE | REFERENCE | NONE | NONE | NONE | NONE | NONE | **GENERATOR ONLY** |
| **ES-335** | FULL | NONE | NONE | NONE | NONE | NONE | NONE | **SPEC ONLY** |
| **Benedetto 17"** | FULL (doc) | NONE | NONE | NONE | NONE | NONE | NONE | **SPEC ONLY** |
| **Cuatro Venezolano** | PARTIAL | SOLVER | NONE | NONE | NONE | NONE | NONE | **SPEC ONLY** |
| **Selmer-Maccaferri** | PARTIAL | NONE | NONE | NONE | NONE | NONE | NONE | **SPEC ONLY** |
| **Melody Maker** | PARTIAL | NONE | NONE | NONE | NONE | NONE | NONE | **NAMED ONLY** |
| **Harmony H44** | NONE | REFERENCE | NONE | NONE | NONE | NONE | NONE | **NAMED ONLY** |
| **EDS-1275** | NONE | NONE | NONE | NONE | NONE | NONE | NONE | **NAMED ONLY** |
| **Bass 4-String** | PLACEHOLDER | NONE | NONE | NONE | NONE | NONE | NONE | **NAMED ONLY** |
| **Cuatro PR** | PARTIAL | NONE | NONE | NONE | NONE | NONE | NONE | **SPEC ONLY** |
| **Ukuleles** | NONE | REFERENCE | NONE | NONE | NONE | NONE | NONE | **NAMED ONLY** |

---

## 3. Detailed Stage Analysis

### Stage A: Specification Completeness

**Canonical System** (`instrument_specs.py`):
- 18 instruments with `BodyDimensions` (body_length_mm, upper/lower bout width, waist width, waist_y_norm, family)
- Only 8 instruments with `FeatureRoutes` (neck_pocket, pickup_routes, bridge_route, control_cavity, soundhole, f_holes)
- **44% feature route coverage** — Missing for: classical, j45, flying_v, sg, explorer, melody_maker, om_000, jumbo, cuatro, benedetto, bass

**JSON Spec Tiers**:
| Tier | Instruments | Completeness |
|------|-------------|--------------|
| COMPLETE (all build data) | Les Paul, Smart Guitar, Stratocaster, Explorer, ES-335, Telecaster, Flying V, SG | Body + neck + hardware + CNC ops |
| PARTIAL (dimensions only) | Dreadnought, J-45, OM, Jumbo, Classical | Body dimensions, missing hardware |
| REFERENCE (documentation) | Benedetto 17" | Markdown doc, no JSON |
| PLACEHOLDER | Bass 4-String, EDS-1275 | Listed but no data |

### Stage B: Body Outline Generation

**Types identified**:
- **PARAMETRIC**: Bezier curves from spec parameters (Dreadnought, OM, Parlor, Jumbo, Stratocaster via StratocasterBodyGenerator)
- **REFERENCE**: Static DXF files with extracted points (Les Paul, Telecaster, SG, Explorer, Flying V, J-45, Classical)
- **SOLVER**: BodyContourSolver completes partial outlines (Cuatro Venezolano)
- **TRACED**: BOE-captured outlines (Smart Guitar v1 — 78 points, 7 voids)

**DXF Files Available** (19 files in `outlines.py`):
- Electric: Stratocaster (322×458mm), Les Paul (383×269mm), JS1000 (450×314mm), Explorer (556×434mm), Flying V (486×607mm), H44 (390×270mm), Smart Guitar variants
- Acoustic: Dreadnought (404×510mm), J45 (398×504mm), Jumbo (474×385mm), Classical (371×490mm), OM (397×499mm), L-00 (376×500mm)
- Other: Soprano ukulele (176×200mm), Concert ukulele (203×393mm), Octave mandolin (280×350mm)

**DXF Writer Compliance**:
- `dxf_writer.py` exists (R12 standard, LINE entities only)
- Compliant: BezierBodyGenerator, BodyContourSolver, ArcReconstructor
- Non-compliant: Les Paul (direct ezdxf), Smart Guitar (direct ezdxf), neck/headstock routers (direct ezdxf)

### Stage C: Neck/Headstock Generation

**Generators**:
- `NeckGCodeGenerator` (lines 29-315): Complete G-code for truss rod, headstock outline, tuner holes, profile roughing
- `NeckGenerator` (lines 322-394): Main interface with preset support
- `generate_headstock_outline()`: 9 hardcoded headstock shapes (Gibson open/solid, Fender Strat/Tele, PRS, Classical, Martin, Benedetto, Paddle)
- `generate_neck_profile_points()`: C, D, V shapes parametric; U, Asymmetric, Compound fallback to C

**CAM Pipeline** (`cam/neck/orchestrator.py`):
- OP10: Truss rod channel
- OP40: Profile roughing (ball-end)
- OP45: Profile finishing
- OP50: Fret slots (12-TET formula)

**Instrument Coverage**:
- Stratocaster: Full (generator + presets + CAM)
- Les Paul: Full (generator + presets + CAM)
- Other electric: Partial (generic presets)
- Acoustic: Partial (classical/Martin presets only)

### Stage D: Cavity/Component Geometry

**Pickup Routes** (8 instruments have FeatureRoutes):
- Stratocaster: SSS, HSS, HSH, HH configurations
- Les Paul: HH with full CNC operations (71×40×19mm per pocket)
- Telecaster: SS standard
- Smart Guitar: Dual humbucker with Pi 5 electronics bay

**Control Cavities**:
- Les Paul: 108×64×31.75mm, 4 pots
- Smart Guitar: 16 distinct cavities including USB-C, antenna recess, wiring channels

**Missing**: Classical, J-45, OM, Jumbo, Flying V (listed but no routes defined)

### Stage E: CAM Pipeline

**Generic Operations Available** (all instruments can use):
| Operation | Router | Output |
|-----------|--------|--------|
| Roughing | `roughing_router.py` | G-code |
| Profiling | `profile_router.py` | G-code + tabs |
| V-Carving | `production_router.py` | G-code |
| Adaptive pocketing | `adaptive/gcode_router.py` | Spiral G-code |
| Binding channel | `binding_router.py` | G-code |
| Drilling | `drilling_consolidated_router.py` | G81/G83 |
| Helical plunge | `helical_router.py` | G2/G3 arcs |

**Instrument-Specific CAM**:
- `stratocaster_cam_router.py` — Body profile, pickup cavities, tremolo
- `body_gcode_router.py` — Les Paul carved top, pickups, controls
- `flying_v_cam_router.py` — Body profile, heel pocket
- `acoustic_cam_router.py` — Body outline, f-holes, bracing
- `archtop_cam_router.py` — Graduated thickness surfaces
- `om_cam_router.py` — Small body profile

### Stage F: G-code Output

**Post-Processors Available**:
| Controller | G43 | G41/42 | Arcs | Notes |
|------------|-----|--------|------|-------|
| GRBL | Yes | Yes | IJ/R | Default hobbyist |
| Mach4 | Yes | Yes | IJ/R | Commercial 3-axis |
| LinuxCNC | Yes | Yes | IJ/R | Path blending (G64) |
| Haas | Yes | Yes | IJ | Industrial |
| FANUC | Yes | Yes | IJ | O-program numbers |

**Machine Presets** (7 machines):
- BCAM 2030A (lutherie-specific): 600×900×120mm, VFD spindle, probe-enabled
- Shapeoko 3/XXL, X-Carve, Avid Pro, Laguna IQ, Haas VF-2

**Verified G-code Output**:
- Les Paul: 18,394 lines, 1586.1" cut distance, 10.6 min estimate
- Smart Guitar: Layer-based CAM with depth annotations
- Others: Generic profile/pocket operations only

### Stage G: Build Documentation

**Current State**: No instrument has complete build documentation.

**Partial Coverage**:
- Les Paul: CNC operation sequence documented in JSON spec
- Smart Guitar: Software stack documented (sg-agentd, zt_band, bundle format)
- Benedetto 17": Reference documentation in Markdown

**Missing for All**:
- Assembly instructions
- Bill of Materials (BOM)
- Fixturing/setup procedures
- Quality checkpoints

---

## 4. Gap Classification Summary

### COMPLETE END-TO-END (2)

**Les Paul**
- Spec: 592-line JSON with 669-point polygon, variants (1959, 1956)
- Body: Reference DXF + parametric carved top
- Neck: Full generator with C-profile
- Cavities: HH pickups (71×40×19mm), control cavity (108×64×31.75mm)
- CAM: 12 operations (OP20-OP63), tool library (T1-T3)
- G-code: 18,394 lines verified
- Build doc: Partial (CNC sequence only)

**Smart Guitar v1**
- Spec: 1027-line JSON with 16 cavities, embedded computing spec
- Body: 78-point traced outline, 7 voids
- Neck: N/A (headless design, locking clamp nut)
- Cavities: Complete (Pi 5 + Teensy, USB-C, antenna, wiring channels)
- CAM: Layer-based with depth annotations
- G-code: Per-cavity operations
- Build doc: Partial (software stack documented)

### DESIGN ONLY (3)

**ES-335**
- Blocker: No body generator — semi-hollow construction requires center block geometry
- Path to complete: Create dedicated generator with center block + f-hole routing

**Benedetto 17"**
- Blocker: No DXF extraction — detailed Markdown spec exists but no geometry
- Path to complete: Trace body outline from plans, implement graduated carving

**Cuatro PR**
- Blocker: Scale length error (documented as 420mm, should be 556.5mm per SPRINTS.md)
- Path to complete: Fix spec, use BodyContourSolver pattern from Venezuelan variant

### CAM PARTIAL (7)

**Stratocaster**
- Present: Body generator, 3 variants (vintage/modern/24fret), pickup configs
- Missing: Complete CNC operation sequence (only roughing/profiling available)
- Blocker: No carved contour CAM (belly cut, arm contour)

**Dreadnought**
- Present: Parametric body (Bezier), acoustic generator, soundhole routing
- Missing: Bracing pocket CAM, binding channel implementation
- Blocker: Bracing patterns not parametric

**Telecaster**
- Present: Body outline DXF, generic CAM
- Missing: Instrument-specific pickup routing (single-coil, bridge plate)
- Blocker: No dedicated cam router

**Flying V**
- Present: Body outline, heel pocket geometry
- Missing: Complete cavity routing (pickups, electronics)
- Blocker: `pocket_generator.py` exists but not wired to router

**Explorer**
- Present: Body outline (24 points — needs refinement)
- Missing: Cavity routing, neck pocket
- Blocker: Low-resolution outline

**OM/000**
- Present: Parametric body, acoustic generator
- Missing: Specific bracing patterns, binding
- Blocker: Same as Dreadnought

**Jumbo Archtop**
- Present: Archtop CAM router
- Missing: Body outline DXF, graduated thickness map
- Blocker: No source geometry

### GENERATOR ONLY (5)

**SG, J-45, Classical, Gibson L-00, JS1000**
- Present: Body outline DXF in `outlines.py`
- Missing: All downstream stages (cavities, CAM, G-code, docs)
- Common blocker: No feature routes defined in `instrument_specs.py`

### SPEC ONLY (4)

**Cuatro Venezolano, Selmer-Maccaferri**
- Present: Spec definitions, solver support (Venezolano)
- Missing: Body generators, CAM pipeline
- Blocker: Niche instruments, low priority

### NAMED ONLY (3)

**Melody Maker, EDS-1275, Bass 4-String**
- Present: Name references in documentation or placeholder entries
- Missing: All pipeline stages
- Blocker: No implementation work started

---

## 5. Frontend Coverage Analysis

### Full Design Path (7 instruments)

| Instrument | UI Component | Params Exposed | DXF Download | G-code Download |
|------------|--------------|----------------|--------------|-----------------|
| Stratocaster | InstrumentGeometryPanel, StratocasterNeckGenerator | Full (scale, frets, radius, profile, pickup config) | Yes | Yes |
| Les Paul | LesPaulNeckGenerator | Full (scale, neck angle, profile) | Yes | Yes |
| Telecaster | InstrumentGeometryPanel | Partial | Yes | Yes |
| Dreadnought | GuitarDimensionsForm | Full body dimensions | Yes | Yes |
| Classical | GuitarDimensionsForm | Body dimensions only | Yes | Partial |
| OM/000 | GuitarDimensionsForm | Body dimensions | Yes | Partial |
| Archtop | ArchtopCalculator | Bridge height, arch profile | Partial | No |

### Partial UI (3 instruments)

| Instrument | UI Component | Gap |
|------------|--------------|-----|
| Jumbo | SpiralSoundholeDesigner | Body outline not exposed |
| PRS | InstrumentGeometryPanel | Listed as preset only |
| Carlos Jumbo | SpiralSoundholeDesigner | Spiral soundhole only |

### No UI (14 instruments)

SG, Flying V, Explorer, ES-335, Melody Maker, J-45, Gibson L-00, Benedetto 17", Selmer-Maccaferri, Cuatro variants, Bass, Ukuleles, Mandolins, Smart Guitar (has dedicated router but no design UI)

---

## 6. Blockers by Category

### Infrastructure Blockers (affects all)

1. **dxf_writer.py migration incomplete**
   - 10 generators still use direct ezdxf
   - CLAUDE.md marks as "blocking — ranks equal to Smart Guitar first article"
   - Affected: Les Paul reader, Smart Guitar DXF, all neck/headstock routers

2. **Feature routes incomplete** (44% coverage)
   - 10 instruments missing cavity definitions
   - Blocks: Cavity CAM generation

3. **Build documentation system absent**
   - No BOM generator
   - No assembly instruction templates
   - No fixturing documentation

### Per-Instrument Blockers

| Instrument | Primary Blocker |
|------------|-----------------|
| Stratocaster | Belly/arm contour CAM not implemented |
| ES-335 | Semi-hollow center block geometry not modeled |
| Explorer | 24-point outline too coarse for CNC |
| Flying V | pocket_generator.py not wired to router |
| Benedetto 17" | No DXF extraction from reference plans |
| Cuatro PR | Scale length error in spec (420mm should be 556.5mm) |
| Bracing (all acoustic) | Patterns not parametric, manual placement only |

---

## 7. Recommendations

### Priority 1: Complete Near-Complete Instruments (3)

**Stratocaster** (→ COMPLETE E2E)
- Add contour carving CAM (belly cut, arm contour)
- Wire existing generators to complete operation sequence
- Effort: ~2 sprints

**Dreadnought** (→ COMPLETE E2E)
- Parametrize bracing patterns
- Implement binding channel routing
- Add top graduation for X-brace
- Effort: ~3 sprints

**Telecaster** (→ CAM PARTIAL → COMPLETE)
- Add dedicated cam router for single-coil + bridge plate routing
- Effort: ~1 sprint

### Priority 2: Infrastructure (affects all)

**dxf_writer.py migration** (blocking)
- Refactor Les Paul reader to use central writer
- Refactor Smart Guitar DXF to use central writer
- Refactor neck/headstock routers
- Effort: ~1 sprint

**Feature routes completion**
- Add FeatureRoutes for all 18 canonical instruments
- Auto-generate cavity geometry from routes
- Effort: ~2 sprints

### Priority 3: Documentation System

**BOM generator**
- Extract materials from spec JSON
- Generate purchase lists
- Effort: ~1 sprint

**Assembly documentation templates**
- Standard sections per instrument family
- Photo placeholder system
- Effort: ~2 sprints

### Priority 4: Low-Hanging Fruit

| Instrument | Action | Effort |
|------------|--------|--------|
| Explorer | Refine outline to 100+ points from source DXF | 1 day |
| Flying V | Wire pocket_generator.py to router | 1 day |
| Cuatro PR | Fix scale length to 556.5mm | 1 hour |
| Classical | Add feature routes | 2 days |
| J-45 | Add feature routes | 2 days |

### Not Recommended (defer)

- **EDS-1275**: Double-neck complexity, zero implementation, low demand
- **Bass 4-String**: Different scale entirely, separate design system needed
- **Ukuleles/Mandolins**: Different instrument family, low priority for guitar platform

---

## 8. Summary Statistics

| Classification | Count | % |
|----------------|-------|---|
| COMPLETE END-TO-END | 2 | 8% |
| DESIGN ONLY | 3 | 13% |
| CAM PARTIAL | 7 | 29% |
| GENERATOR ONLY | 5 | 21% |
| SPEC ONLY | 4 | 17% |
| NAMED ONLY | 3 | 13% |
| **Total** | **24** | |

**Closest to complete** (1-2 sprints to E2E):
1. Stratocaster — contour CAM only missing
2. Telecaster — dedicated router only missing
3. Flying V — wiring pocket_generator only

**Furthest from complete** (defer):
1. EDS-1275 — zero implementation
2. Bass 4-String — different instrument family
3. Selmer-Maccaferri — niche archtop, spec only

---

## Appendix A: File Inventory

### Body Generators
- `services/api/app/generators/body_generator.py` — Unified dispatcher
- `services/api/app/generators/stratocaster_body_generator.py` — Parametric Strat (223 lines)
- `services/api/app/generators/lespaul_body_generator.py` — DXF-based Les Paul (131 lines)
- `services/api/app/generators/acoustic_body_generator.py` — Parametric acoustic (350 lines)
- `services/api/app/generators/bezier_body.py` — Bezier curve acoustic (474 lines)
- `services/api/app/generators/electric_body_generator.py` — Reference outline retrieval (258 lines)
- `services/api/app/instrument_geometry/body/smart_guitar_dxf.py` — Smart Guitar layers (300+ lines)
- `services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py` — Constraint solver (293 lines)

### Neck/Headstock Generators
- `services/api/app/generators/neck_headstock_generator.py` — G-code generator (397 lines)
- `services/api/app/generators/neck_headstock_geometry.py` — Outline generation (481 lines)
- `services/api/app/generators/neck_headstock_presets.py` — Presets (223 lines)
- `services/api/app/routers/neck/neck_profile_export.py` — DXF export (404 lines)
- `services/api/app/routers/neck/headstock_transition_export.py` — Transition zone (343 lines)
- `services/api/app/routers/headstock/dxf_export.py` — SVG→DXF (530 lines)
- `services/api/app/cam/neck/orchestrator.py` — CAM pipeline (200 lines)

### CAM Infrastructure
- `services/api/app/cam/machines.py` — Machine specs, BCAM 2030A (339 lines)
- `services/api/app/cam/post_processor.py` — Post-processor framework (540 lines)
- `services/api/app/cam/dxf_writer.py` — Central DXF writer (R12 standard)

### Instrument Specs
- `services/api/app/instrument_geometry/instrument_specs.py` — Canonical 18-instrument system
- `services/api/app/instrument_geometry/specs/*.json` — 17 detailed JSON specs
- `services/api/app/instrument_geometry/body/specs/smart_guitar_v1.json` — 1027 lines
- `services/api/app/instrument_geometry/guitars/*.py` — 24 model loaders

### Frontend Components
- `packages/client/src/components/InstrumentGeometryPanel.vue`
- `packages/client/src/components/generators/neck/StratocasterNeckGenerator.vue`
- `packages/client/src/components/generators/neck/LesPaulNeckGenerator.vue`
- `packages/client/src/components/toolbox/GuitarDesignHub.vue`
- `packages/client/src/components/toolbox/GuitarDimensionsForm.vue`
- `packages/client/src/components/toolbox/ArchtopCalculator.vue`
- `packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue`
