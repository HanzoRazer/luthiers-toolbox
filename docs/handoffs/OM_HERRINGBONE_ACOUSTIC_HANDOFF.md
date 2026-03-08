# Martin OM-28 Herringbone Acoustic — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-07  
**Status:** Design Complete — Pipeline Has 8 Identified Gaps  
**Priority:** High  
**Context:** Custom Martin OM-style acoustic with herringbone black/white binding and herringbone rosette ring. Exercises the acoustic guitar pipeline from body outline through binding/purfling and rosette fabrication to CNC output.  

---

## Executive Summary

This build stress-tests **two pipeline segments that don't exist yet**: binding/purfling geometry generation and herringbone rosette fabrication. The OM body itself is partially defined (volume calculator has dimensions, catalog references a 5451-point DXF) but the DXF files are missing from disk. The rosette traditional matrix system is production-quality and has a CAM pipeline — but the herringbone engine is scaffold-only (`apply_herringbone_stub` alternates a boolean, no real angle geometry).

**What works today:** The OM model is registered (`om_000`) with basic spec data. The `martin_om28.json` spec captures full body/neck/bracing/binding/rosette dimensions. Two Martin herringbone rosette presets now exist in the pattern library (`martin_herringbone_bw_6x9` and `martin_herringbone_bw_fine_8x13`). The rosette CAM pipeline can go from `MatrixFormula` → `StripCutList` → `AssemblyInstruction` → toolpath → G-code for non-herringbone patterns. Body volume calculations work.

**What breaks:** 8 gaps between the design spec and CNC output. The OM body DXF is missing from disk (only a 10-point simplified outline exists). The herringbone engine is a stub. No binding/purfling backend exists at all — frontend has stubs but backend has no geometry generator, no offset calculator, no channel routing CAM. The Martin acoustic headstock shape isn't in the headstock geometry library. And body perimeter profiling (as opposed to interior pocket clearing) has no toolpath mode.

> **Annotation:** This document is both a custom guitar design spec and a pipeline integration audit. Many gaps overlap with those identified in the J45 Vine of Life handoff — particularly body perimeter profiling, V-carve limitations, and missing acoustic headstock outlines. The unique contribution here is exercising the binding/purfling and herringbone subsystems.

---

## Part 1: Custom OM-28 Design Specification

### Base Instrument

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | Martin OM-28 Orchestra Model | `instrument_model_registry.json` → `om_000` |
| Scale length | 645.16 mm (25.4") | Registry + `om_000.py` |
| Frets | 20 (14 clear of body) | Martin OM standard |
| Tuning | Standard E | |
| Fretboard radius | 406.4 mm (16") | Martin standard radius |

### Body Specification

| Parameter | Value | Source |
|-----------|-------|--------|
| Lower bout | 384 mm (15.125") | `body_volume_calc.py` → `martin_om28` |
| Upper bout | 286 mm (11.25") | `body_volume_calc.py` |
| Waist | 241 mm (9.5") | `body_volume_calc.py` |
| Body length | 495 mm (19.5") | `martin_om28.json` |
| Lower depth | 108 mm (4.25") at endblock | `martin_om28.json` |
| Upper depth | 95 mm (3.75") at neck block | `martin_om28.json` |
| Soundhole | 101.6 mm (4") diameter | Martin OM standard |
| Top wood | Sitka Spruce, bookmatched | |
| Back & sides | Indian Rosewood | Style 28 specification |
| Bracing | Scalloped forward-shifted X-brace | |
| Bridge | Ebony, 6.5" (165.1 mm) string spacing, compensated saddle | |

> **Annotation:** The body_volume_calc has dimensional data for `martin_om28` but the catalog DXF reference (`om_000_body.dxf`, 5451 points) doesn't exist on disk. Only a 10-point simplified polygon in `body_outlines.json`. This is OM-GAP-01.

### Binding & Purfling Specification

This is the signature visual element — herringbone black/white binding wrapping the top edge.

| Layer | Material | Width (mm) | Notes |
|-------|----------|------------|-------|
| 1 (outermost) | Black fiber | 1.0 | Outer containment strip |
| 2 | White fiber | 0.5 | Spacer |
| 3 (center) | Herringbone B/W | 3.0 | Core decorative strip, 45° angle |
| 4 | White fiber | 0.5 | Spacer |
| 5 (innermost) | Black fiber | 1.0 | Inner containment strip |
| **Total** | | **6.0 mm** | 5-layer purfling sandwich |

Applied to: top perimeter, back perimeter. Side binding is plain ivoroid (1.5 mm).

**Herringbone strip fabrication:**
- Black and white maple veneer strips, 0.8 mm wide, 0.5 mm thick
- Glued at 45° alternating angle to create zigzag V-pattern
- Piece width (chip length): 1.0 mm — produces ~26 pieces per inch
- Traditional method: stack strips in a jig, angle-cut, flip alternating pieces

> **Annotation:** The BindingDesignerView.vue and PurflingDesignerView.vue exist as frontend stubs with herringbone presets defined, but there is NO backend: no geometry generator to compute binding offset curves, no purfling channel toolpath, no herringbone strip fabrication instructions. This is OM-GAP-03 + OM-GAP-04.

### Rosette Specification

5-ring concentric rosette stack around the soundhole:

| Ring | Material | Width (mm) | Notes |
|------|----------|------------|-------|
| 1 (outer) | Black fiber | 0.5 | Containment |
| 2 | White fiber | 1.0 | Spacer |
| 3 (center) | Herringbone B/W | 3.0 | `martin_herringbone_bw_6x9` preset |
| 4 | White fiber | 1.0 | Spacer |
| 5 (inner) | Black fiber | 0.5 | Containment |
| **Total** | | **6.0 mm** | Martin OM-28 standard stack |

- Inner diameter: soundhole radius + 0.5 mm clearance
- Outer diameter: inner + 12.0 mm (6.0 mm each side)
- Herringbone angle: 45° within the ring band
- Herringbone piece width: 1.0 mm

> **Annotation:** The solid/spacer rings (1, 2, 4, 5) can go through the existing rosette CAM pipeline today — `POST /api/cam/rosette/plan-toolpath` → `POST /api/cam/rosette/post-gcode`. The herringbone center ring (3) cannot — `apply_herringbone_stub()` only sets a boolean flag, does not generate real angle-based geometry. This is OM-GAP-05.

### Neck Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Profile | Modified low oval | Martin standard |
| Nut width | 44.5 mm (1.75") | Wider nut for fingerstyle |
| Depth at 1st | 21.8 mm | |
| Depth at 12th | 23.1 mm | |
| Fretboard wood | Ebony | |
| Fret wire | Standard medium (0.050" × 0.080") | Martin spec |
| Truss rod | Two-way adjustable | |

### Headstock Specification

| Parameter | Value |
|-----------|-------|
| Style | Martin solid slotted (OM standard) |
| Slotted variant | 3+3 with classical-style slots |
| Modern variant | Solid face with enclosed Grover Rotomatics |
| Overlay | Ebony or rosewood veneer |
| Logo | Martin decal, centered |

> **Annotation:** Neither slotted nor solid Martin headstock outlines exist in `neck_headstock_config.py`. The system currently has Fender Strat, Telecaster, Gibson, PRS, and generic outlines. This is OM-GAP-06.

### Side Profile (13 stations, endblock = 0)

| Station (mm) | Depth (mm) | Position |
|-------------|-----------|----------|
| 0 | 108.0 | Endblock |
| 41 | 107.0 | |
| 82 | 105.5 | |
| 124 | 103.5 | |
| 165 | 101.0 | |
| 206 | 99.0 | |
| 248 | 97.0 | |
| 289 | 95.0 | Waist |
| 330 | 94.0 | |
| 371 | 93.0 | |
| 413 | 92.0 | |
| 454 | 91.5 | |
| 495 | 95.0 | Neck block |

---

## Part 2: Pipeline Integration Audit

### Subsystem Status Matrix

| Subsystem | Status | Can Produce G-code? | Notes |
|-----------|--------|---------------------|-------|
| Body outline geometry | **Partial** | No | Catalog dimensions exist; DXF missing from disk |
| Body perimeter profiling | **Missing** | No | Only interior pocket clearing exists |
| Rosette (solid rings) | **Production** | Yes | Full OPERATION lane pipeline |
| Rosette (herringbone ring) | **Scaffold** | No | `apply_herringbone_stub` — boolean only |
| Rosette traditional matrix | **Production** | Yes | `MatrixFormula` → cut list → assembly |
| Herringbone presets | **NEW** | — | `martin_herringbone_bw_6x9`, `_fine_8x13` |
| Binding geometry | **Missing** | No | No backend at all |
| Purfling channel routing | **Missing** | No | No backend at all |
| Neck G-code | **Class only** | No | No HTTP endpoint |
| Martin headstock outline | **Missing** | No | Not in headstock config |
| Body volume calculator | **Production** | — | `martin_om28` entry works |
| Fret calculator | **Production** | — | Scale length → fret positions |
| Bridge placement | **Production** | — | Compensation calculator works |

### What Can Be CNC-Manufactured Today

1. **Rosette solid rings** (rings 1, 2, 4, 5) — full pipeline from spec to G-code
2. **Fret slots** — position math is production, slot cutting toolpath works
3. **Bridge pin holes** — drilling cycle generator works
4. **Soundhole boring** — circular pocket toolpath works

### What Cannot Be CNC-Manufactured Today

1. **Body perimeter** — no profiling toolpath mode (only pocket clearing)
2. **Herringbone rosette ring** — engine is a stub
3. **Binding channels** — no backend geometry or CAM
4. **Purfling channels** — no backend geometry or CAM
5. **Neck profile** — class exists, no API endpoint
6. **Headstock shape** — Martin outline not defined

---

## Part 3: Asset Inventory

### Created This Session

| Asset | Path | Status |
|-------|------|--------|
| OM-28 spec JSON | `instrument_geometry/specs/martin_om28.json` | **NEW** — full design spec with 2 variants |
| Martin herringbone preset | `cam/rosette/presets.py` → `martin_herringbone_bw_6x9` | **NEW** — 6×9 symmetric V-chevron |
| Martin fine herringbone preset | `cam/rosette/presets.py` → `martin_herringbone_bw_fine_8x13` | **NEW** — 8×13 premium tight weave |
| Registry update | `instrument_model_registry.json` → `om_000` | **UPDATED** — STUB→PARTIAL |

### Pre-Existing Assets

| Asset | Path | Status |
|-------|------|--------|
| OM model stub | `instrument_geometry/guitars/om_000.py` | Stub — basic InstrumentSpec |
| OM volume calc entry | `body_volume_calc.py` → `martin_om28` | Production — acoustic dimensions |
| OM catalog entry | `guitar_catalog.json` → `om_000` | References missing DXF |
| OM body outline (simplified) | `body_outlines.json` → OM entry | 10-point polygon only |
| Herringbone engine | `cam/rosette/herringbone.py` | Scaffold — boolean only |
| Hauser herringbone preset | `cam/rosette/presets.py` → `hauser_herringbone_8x13` | Production |
| BindingDesignerView.vue | Frontend | Stub — UI shell, no backend |
| PurflingDesignerView.vue | Frontend | Stub — UI shell, no backend |
| Rosette CAM pipeline | `cam/rosette/` | Production — plan-toolpath → post-gcode |
| Traditional pattern generator | `cam/rosette/pattern_generator.py` | Production |

### Missing Assets

| Asset | Expected Path | Notes |
|-------|---------------|-------|
| OM body DXF | `instrument_geometry/body/dxf/acoustic/om_000_body.dxf` | Catalog says 5451 points |
| Orchestra model clean DXF | `instrument_geometry/body/dxf/acoustic/orchestra_model_clean.dxf` | Referenced in catalog |
| Martin headstock outline | `generators/neck_headstock_config.py` | Neither slotted nor solid variant |
| Binding geometry generator | `app/cam/binding/` or similar | Entire subsystem missing |
| Purfling channel CAM | `app/cam/binding/purfling_cam.py` or similar | Entire subsystem missing |

---

## Part 4: Gap Registry

### OM-GAP-01: Body DXF Missing from Disk

- **Severity:** High
- **Category:** Asset
- **Description:** The guitar catalog references `om_000_body.dxf` with 5451 points (extracted from vectorizer phase 3), but the file doesn't exist in `instrument_geometry/body/dxf/acoustic/`. Only a 10-point simplified polygon is available in `body_outlines.json`. Without the full DXF, body profiling can't produce accurate G-code even when the profiling toolpath mode is built.
- **Resolution:** Re-run vectorizer phase 3 on the OM blueprint source, or reconstruct from the body_volume_calc dimensions using parametric generation. Place output in `dxf/acoustic/om_000_body.dxf`.
- **Blocked by:** Source blueprint availability
- **Blocks:** Body CNC profiling

### OM-GAP-02: Body Perimeter Profiling Toolpath Missing

- **Severity:** High
- **Category:** CAM
- **Description:** The CAM system has interior pocket clearing (roughing + finishing) but no perimeter profiling mode. Body outline routing requires following the outside contour with tabs, not clearing an interior pocket. This gap is shared with the J45 build (VINE-GAP-05).
- **Resolution:** Add a `ProfileToolpath` class to `app/cam/toolpath/` that follows a closed polyline with configurable tab placement, lead-in/lead-out arcs, and climb/conventional direction.
- **Blocked by:** Nothing
- **Blocks:** Any body outline CNC routing

### OM-GAP-03: No Binding Geometry Backend

- **Severity:** Critical (for this build)
- **Category:** Backend
- **Description:** The binding/purfling system has frontend stubs only (`BindingDesignerView.vue`, `PurflingDesignerView.vue` with herringbone presets) but zero backend. No offset curve generator, no layer-stack geometry, no channel depth/width calculator, no DXF export for binding channels. This is the most significant gap for the OM herringbone build.
- **Resolution:** Create `app/cam/binding/` module with:
  - `geometry.py` — offset the body outline inward by binding width to produce channel center-line, compute layer boundaries
  - `channel_spec.py` — dataclass for channel depth, width, corner radius, and layer stack definition
  - `binding_router.py` — API endpoints for binding channel preview and specifications
- **Blocked by:** OM-GAP-01 (needs body DXF for accurate offsets)
- **Blocks:** OM-GAP-04

### OM-GAP-04: No Purfling Channel CAM

- **Severity:** Critical (for this build)
- **Category:** CAM
- **Description:** Even with binding geometry (OM-GAP-03), there's no CAM module to generate purfling channel routing toolpaths. Purfling channels are narrow (typically 1.5–2.0 mm wide, 1.5–2.5 mm deep), routed along the body perimeter at a fixed inset. The herringbone strip is glued into this channel. CNC purfling routing needs a specialized toolpath that follows the body contour at precise depth and offset.
- **Resolution:** Create `app/cam/binding/purfling_cam.py` with:
  - Channel routing toolpath (follow body offset curve, fixed depth, single pass or step-down)
  - Corner handling (tight radius transitions at waist, bouts)
  - Multi-channel support (one channel per purfling layer if needed)
- **Blocked by:** OM-GAP-03
- **Blocks:** CNC purfling channel routing

### OM-GAP-05: Herringbone Engine is Scaffold Only

- **Severity:** High
- **Category:** CAM
- **Description:** `app/cam/rosette/herringbone.py` contains only `apply_herringbone_stub()`, which alternates a `herringbone_flip` boolean per slice. It stores `herringbone_angle_deg` but doesn't use it. Real herringbone requires computing angled strip boundaries within each matrix cell — rotating the chip geometry by ±45° (or configurable angle) and alternating direction per column. The Martin herringbone preset matrices (`martin_herringbone_bw_6x9`, `_fine_8x13`) define the correct row/column structure but the engine can't render them with actual angle geometry.
- **Resolution:** Upgrade `herringbone.py` to:
  - Accept a `MatrixFormula` and compute actual angled chip boundaries
  - Generate alternating ±angle strip segments per column
  - Produce either visual preview geometry (SVG/DXF) or fabrication instructions (cut angles, assembly sequence)
  - Integrate with `TraditionalPatternGenerator.generate_cut_list()` so herringbone presets produce real `StripCutList` with angle data
- **Blocked by:** Nothing — self-contained in rosette module
- **Blocks:** Herringbone rosette ring CNC fabrication

### OM-GAP-06: Martin Headstock Outline Missing

- **Severity:** Medium
- **Category:** Geometry
- **Description:** `neck_headstock_config.py` has Fender, Gibson (open-book electric), PRS, and generic headstock outlines, but no Martin headstock. The OM-28 has two variants: slotted (classical-style slots for open-gear tuners) and solid (modern enclosed tuners). Both require distinct outlines.
- **Resolution:** Add `MARTIN_SLOTTED` and `MARTIN_SOLID` entries to `HeadstockType` enum and corresponding point lists in `generate_headstock_outline()`. The slotted variant has three rectangular slots per side; the solid variant has a rounded paddle shape with a slight taper.
- **Blocked by:** Nothing
- **Blocks:** OM headstock CNC profiling, tuner hole drilling placement

### OM-GAP-07: Neck G-code Generator Has No HTTP Endpoint

- **Severity:** Medium
- **Category:** API
- **Description:** The neck G-code generation class exists in `app/cam/` but has no router endpoint. All other CAM operations (rosette, drilling, roughing) have API routes. This gap is shared with the J45 build (VINE-GAP-04).
- **Resolution:** Create a neck CAM router in `app/routers/` that wraps the existing neck G-code class. Register in `manifest.py`.
- **Blocked by:** Nothing
- **Blocks:** API-driven neck CNC manufacturing

### OM-GAP-08: Herringbone Strip Fabrication Instructions Missing

- **Severity:** Medium
- **Category:** Fabrication
- **Description:** The traditional matrix system produces `StripCutList` and `AssemblyInstruction` for rope/chevron patterns, but herringbone fabrication is different. Herringbone requires: (1) cutting veneer strips to width, (2) stacking and gluing at 45° angle in a jig, (3) cross-cutting the glued stack into slices, (4) flipping alternating slices to create the V-pattern. The current `AssemblyInstruction` model doesn't capture angle-cutting or flip-assembly steps.
- **Resolution:** Extend `AssemblyInstruction` (or create `HerringboneAssemblyInstruction`) to include:
  - `cut_angle_deg` — angle for the initial stack glue-up
  - `flip_pattern` — which slices to flip (typically every other one)
  - `slice_width_mm` — cross-cut width (equals chip_length from MatrixFormula)
  - Jig dimensions for the angled glue-up
- **Blocked by:** OM-GAP-05
- **Blocks:** Complete fabrication documentation for herringbone binding/rosette

---

## Part 5: Remediation Roadmap

### Phase 1: Foundation (enables body work)

| Gap | Task | Effort |
|-----|------|--------|
| OM-GAP-01 | Recover or regenerate OM body DXF (5451-point accuracy) | Medium |
| OM-GAP-02 | Build `ProfileToolpath` for body perimeter routing | High |
| OM-GAP-06 | Add Martin headstock outlines (slotted + solid) | Low |

### Phase 2: Herringbone Engine (enables rosette + binding strip fabrication)

| Gap | Task | Effort |
|-----|------|--------|
| OM-GAP-05 | Upgrade herringbone engine from stub to real angle geometry | High |
| OM-GAP-08 | Extend assembly instructions for angle-cut/flip fabrication | Medium |

### Phase 3: Binding/Purfling Pipeline (enables complete trim work)

| Gap | Task | Effort |
|-----|------|--------|
| OM-GAP-03 | Build binding geometry backend (offset curves, layer stack) | High |
| OM-GAP-04 | Build purfling channel routing CAM | High |
| OM-GAP-07 | Wrap neck G-code class in API router | Low |

### Cross-References

| This Gap | Related J45 Gap | Shared? |
|----------|-----------------|---------|
| OM-GAP-02 | VINE-GAP-05 (body perimeter profiling) | Yes — identical |
| OM-GAP-07 | VINE-GAP-04 (neck G-code endpoint) | Yes — identical |
| OM-GAP-06 | VINE-GAP-06 (Gibson acoustic headstock) | Similar — different manufacturer |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total gaps identified | 8 |
| Critical gaps | 2 (binding geometry, purfling CAM) |
| High gaps | 3 (body DXF, perimeter profiling, herringbone engine) |
| Medium gaps | 3 (headstock, neck API, fabrication instructions) |
| Gaps shared with J45 build | 2 (body profiling, neck endpoint) |
| Assets created this session | 4 (spec JSON, 2 presets, registry update) |
| Subsystems at production quality | 4 (rosette solid, fret calc, drilling, bridge placement) |
| Subsystems missing entirely | 2 (binding geometry, purfling CAM) |
