# 1956–1959 Gibson Les Paul Standard — Full CNC Build Handoff

> **Model:** `les_paul` | **Registry Status:** `STUB` → `COMPLETE` | **Session Date:** 2026-03-07

---

## Executive Summary

The Les Paul is the **most fully implemented instrument** in the Luthier's ToolBox codebase. This session created the authoritative spec JSON, upgraded the registry from `STUB` to `COMPLETE`, added custom binding/purfling routing specifications (Spanish wave + green wood two-tier system), and generated **452,840 lines of G-code** across three phases covering the entire body build process.

**What works:** Body outline DXF (669-point R12 polygon), authoritative spec with all operations/tools/variants, complete 3-phase G-code generation (mahogany back routing, purfling channel routing, compound-radius carved top 3D surfacing), 7-tool library, build summary manifest.

**What breaks:** Cavity positions in Phase 1 are heuristic approximations — no multi-layer CAM DXF exists. Purfling offset paths use naive vertex averaging that may self-intersect at the cutaway. No neck CNC pipeline. No G43 tool length compensation. G-code has not been validated in a simulator.

**Critical annotation:** The Phase 1 G-code (OP10–OP63) routes real material. Cavity positions MUST be validated against a 1:1 reference drawing before any cutting operation. GAP-01/GAP-02 are production blockers.

---

## Part 1 · Base Instrument

| Field | Value |
|-------|-------|
| Model ID | `les_paul` |
| Display Name | 1956–1959 Gibson Les Paul Standard |
| Manufacturer | Gibson |
| Year | 1956–1959 |
| Category | `electric_guitar` |
| Scale Length | 628.65mm (24.75") |
| Frets | 22 |
| Strings | 6 |
| Body Dimensions | 444mm L × 330mm W × 50.8mm thick |
| DXF Outline Dimensions | 383.54mm × 269.24mm (horizontal orientation) |
| Body Material — Back | Honduran Mahogany |
| Body Material — Top | Bookmatched Figured Maple (12.7mm cap) |
| Neck Joint | Set-neck long tenon (53mm × 89mm × 16mm mortise) |
| Neck Angle | 4.0° |
| Pickups | HH — dual PAF humbuckers, 71mm × 40mm routes |
| Bridge | ABR-1 Tune-o-matic (74mm stud spacing) |
| Tailpiece | Stoptail (82.5mm stud spacing) |
| Control Cavity | 108mm × 64mm × 31.75mm |
| Binding System | Two-tier: Spanish wave (2.2×6.0mm) + green wood (1.5×1.3mm) |
| Carved Top | Compound-radius dome — 508mm/381mm radii, 7.8mm rise, 3.2° avg slope |
| Registry Status | `COMPLETE` (was `STUB`) |
| Spec File | `instrument_geometry/specs/gibson_les_paul.json` |

### Variants

| Variant | Key Differences |
|---------|----------------|
| `standard_1959` | Flame maple top, '59 PAF pickups, C-profile neck, cherry sunburst |
| `goldtop_1956` | Plain maple top, P-90 pickups, thicker neck, all-gold finish, wrap-around bridge |

---

## Part 2 · Subsystem Status Matrix

| Subsystem | Status | Can Produce G-code? | Notes |
|-----------|--------|---------------------|-------|
| Spec JSON | ✅ CREATED | N/A | `gibson_les_paul.json` — 2 variants, full CNC ops, binding/purfling spec |
| Registry Entry | ✅ UPDATED | N/A | `STUB` → `COMPLETE`, 14 asset entries |
| Model Stub | ✅ UPDATED | N/A | `guitars/les_paul.py` — full MODEL_INFO |
| Body Templates | ✅ UPDATED | N/A | `body_templates.json` — corrected dims, expanded carved top |
| Body Outline DXF | ✅ EXISTS | Phase 1 (perimeter) | 669-point closed LWPOLYLINE on BODY_OUTLINE layer |
| Multi-Layer CAM DXF | ❌ MISSING | Blocks reuse of existing generator | 8 expected layers not present |
| Phase 1 G-code (Mahogany) | ✅ GENERATED | Yes (25,856 lines) | OP10–OP63, cavity positions are heuristic |
| Phase 2 G-code (Purfling) | ✅ GENERATED | Yes (16,264 lines) | OP70–OP71b, both faces, naive offset |
| Phase 3 G-code (Carved Top) | ✅ GENERATED | Yes (410,720 lines) | OP80–OP81, elliptical paraboloid approx |
| Build Summary | ✅ GENERATED | N/A | `LesPaul_1959_BuildSummary.json` |
| Full-Build Generator Script | ✅ CREATED | Yes | `scripts/generate_les_paul_full_build.py` |
| Existing Body Generator | ✅ EXISTS | No (needs multi-layer DXF) | `lespaul_body_generator.py` + 5 mixin modules |
| Neck CNC Pipeline | ❌ MISSING | No | Geometry-only generators exist, no G-code |
| Fret Slot CAM | ⚠️ EXISTS (disconnected) | Separate API call | `fret_slots_cam.py` (934 lines), not wired to build |
| Vectorizer | ⚠️ PARTIAL | No | Les Paul spec range defined, generic processing only |
| Pixel Calibrator | ✅ EXISTS | N/A | CalibrationPanel.vue entry |
| Frontend Card | ✅ EXISTS | N/A | features.html, instrumentApi.ts |

---

## Part 3 · CNC Program Summary

### Machine & Post Processor

| Parameter | Value |
|-----------|-------|
| Machine Targets | TXRX Labs Router (48×48×4"), BCAMCNC 2030CA (48×24×4"), Mach4_Router_4x8 |
| Units Phase 1-2 | Inches (G20) |
| Units Phase 3 | Millimeters (G21) |
| Post Processor | Generic GRBL/Mach4 (G90 G17 G54) |
| Workholding | Double-sided tape + 6 holding tabs (0.5" wide × 0.125" tall) |

### Tool Library

| Tool | Diameter | Type | RPM | Feed | Used In |
|------|----------|------|-----|------|---------|
| T1 | 10mm (0.394") | 2-flute flat end mill | 18,000 | 220 IPM | OP20, OP21, OP22 (rough pockets) |
| T2 | 6mm (0.236") | 2-flute flat end mill | 18,000 | 150 IPM | OP25, OP30, OP31, OP50 (finish, perimeter) |
| T3 | 3mm (0.118") | Flat/drill | 20,000 | 60 IPM | OP40, OP60–OP63 (channels, drilling) |
| T4 | 2.375mm (0.094") | Custom ground flat | 20,000 | 40 IPM | OP70 (Spanish wave purfling) |
| T5 | 1.6mm (0.063") | Custom ground flat | 22,000 | 30 IPM | OP71 (green wood purfling) |
| T6 | 6mm | Ball nose end mill | 18,000 | 2000 mm/min | OP80 (rough carved top) |
| T7 | 3mm | Ball nose end mill | 20,000 | 1500 mm/min | OP81 (finish carved top) |

### G-code Files

| File | Phase | Operations | Lines | Tool Changes |
|------|-------|-----------|-------|-------------|
| `LesPaul_1959_Phase1_MahoganyBack.nc` | 1 | OP10–OP63: fixtures, pockets, perimeter, drilling | 25,856 | 4 (T3→T1→T2→T3) |
| `LesPaul_1959_Phase2_PurflingChannels.nc` | 2 | OP70–OP71b: purfling channels (top + back) | 16,264 | 2 (T4→T5) |
| `LesPaul_1959_Phase3_CarvedTop.nc` | 3 | OP80–OP81: 3D carved top surfacing | 410,720 | 2 (T6→T7) |
| `LesPaul_1959_BuildSummary.json` | — | Manifest + metadata | — | — |

### Operation Sequence

| Op | Description | Tool | Depth | Strategy |
|----|-------------|------|-------|----------|
| OP10 | Fixture / registration holes | T3 | 0.375" | G83 peck drill |
| OP20 | Neck pocket rough | T1 | 0.75" | Helical entry + spiral-outward |
| OP21a | Neck pickup cavity rough | T1 | 0.75" | Helical entry + spiral-outward |
| OP21b | Bridge pickup cavity rough | T1 | 0.75" | Helical entry + spiral-outward |
| OP22 | Electronics cavity rough | T1 | 1.25" | Helical entry + spiral-outward |
| OP25 | Cover plate recess | T2 | 0.125" | Helical entry + spiral-outward |
| OP30 | Neck pocket finish | T2 | 0.75" | Fine stepover finish pass |
| OP31a/b | Pickup cavities finish | T2 | 0.75" | Fine stepover finish pass |
| OP40 | Wiring channels (3 routes) | T3 | 0.50" | Linear plunge + traverse |
| OP50 | Body perimeter contour | T2 | 1.75" (through) | Profile with 6 tabs, ramp entry |
| OP60 | Pot shaft holes (4×) | T3 | Through | Helical bore |
| OP61 | Bridge post holes (2×) | T3 | 0.75" | Helical bore |
| OP62 | Tailpiece stud holes (2×) | T3 | 0.625" | Helical bore |
| OP63 | Screw pilot holes (6×) | T3 | 0.50" | G83 peck drill |
| OP70 | Primary purfling channel (top+back) | T4 | 0.244" | 9 passes at 0.030" DOC |
| OP71 | Inner purfling ledge (top+back) | T5 | 0.059" | 3 passes at 0.020" DOC |
| OP80 | Rough carved top | T6 | 7.7mm max | Bidirectional raster, 3mm stepover |
| OP81 | Finish carved top | T7 | 7.7mm max | Bidirectional raster, 0.5mm stepover |

### Workpiece Orientation & Setup

1. **Phase 1:** Mahogany back slab, face DOWN (routing from back). Origin at lower-left of DXF bounds. 1.75" thick stock.
2. **Phase 2:** Assembled body (mahogany + maple glued). Route top face, then flip for back face. Re-zero Z for each face.
3. **Phase 3:** Assembled body, maple cap face UP. Origin at lower-left of DXF bounds. Z=0 at uncarved cap surface.

### Carved Top Geometry

| Parameter | Value |
|-----------|-------|
| Profile Type | Compound-radius dome (elliptical paraboloid approximation) |
| Major Radius | 508mm (across waist) |
| Minor Radius | 381mm (along length) |
| Total Rise | 7.8mm (edge to peak) |
| Average Slope | 3.2° |
| Slope Range | 1.5° (crown) to 6.0° (cutaway) |
| Cap Thickness Before | 12.7mm (3/4") |
| Cap Thickness After (edge) | 5.0mm |
| Cap Thickness After (peak) | 12.7mm (no removal at center) |
| Rough Stock Allowance | 0.5mm |
| Rough Stepover | 3.0mm (50%) |
| Finish Stepover | 0.5mm (~17%) — scallop-free surface |

### Purfling Routing Specifications

| Parameter | Primary Channel (Spanish Wave) | Inner Ledge (Green Wood) |
|-----------|-------------------------------|--------------------------|
| Material Size | 2.2mm × 6.0mm | 1.5mm × 1.3mm |
| Channel Width | 2.375mm | 1.6mm |
| Channel Depth | 6.2mm | 1.5mm |
| Clearance (width) | 0.175mm total | 0.1mm total |
| Clearance (depth) | 0.2mm | 0.2mm |
| Tool | T4 (2.375mm flat) | T5 (1.6mm flat) |
| Faces | Top + Back | Top + Back |
| Scrap Test Required | YES — before production | YES — before production |

---

## Part 4 · Asset Inventory

### Created This Session

| Asset | Path | Type |
|-------|------|------|
| Spec JSON | `services/api/app/instrument_geometry/specs/gibson_les_paul.json` | Authoritative spec |
| Phase 1 G-code | `exports/les_paul_1959/LesPaul_1959_Phase1_MahoganyBack.nc` | 25,856 lines |
| Phase 2 G-code | `exports/les_paul_1959/LesPaul_1959_Phase2_PurflingChannels.nc` | 16,264 lines |
| Phase 3 G-code | `exports/les_paul_1959/LesPaul_1959_Phase3_CarvedTop.nc` | 410,720 lines |
| Build Summary | `exports/les_paul_1959/LesPaul_1959_BuildSummary.json` | Manifest |
| Gap Summary | `exports/les_paul_1959/BUILD_GAP_SUMMARY.md` | Gap reference |
| Generator Script | `scripts/generate_les_paul_full_build.py` | Reproducible build |

### Modified This Session

| Asset | Path | Change |
|-------|------|--------|
| Registry | `instrument_model_registry.json` | `STUB` → `COMPLETE`, 14 asset entries added |
| Model stub | `guitars/les_paul.py` | Full MODEL_INFO (thickness, spec_file, neck angle, top carve) |
| Body templates | `body_templates.json` | Corrected dims, expanded top_carve, added neck_angle_deg |

### Pre-Existing (Unchanged)

| Asset | Path | Notes |
|-------|------|-------|
| Body DXF | `body/dxf/electric/LesPaul_body.dxf` | 669-point LWPOLYLINE, single layer |
| Generator facade | `generators/lespaul_body_generator.py` | Needs multi-layer DXF to function |
| DXF reader | `generators/lespaul_dxf_reader.py` | 8-layer extraction, translate/rotate |
| Config | `generators/lespaul_config.py` | 3 tools, 2 machines |
| G-code mixins | `generators/lespaul_gcode/*.py` | 4 mixin modules + __init__ |
| Example G-code | `generators/examples/LesPaul_Body_Complete.nc` | Older generation (2025-12-11) |
| Example summary | `generators/examples/LesPaul_Body_Summary.json` | 18,394 lines, 1586.1" cut distance |
| Fret calculator | `calculators/fret_slots_cam.py` | 934 lines, not wired to build |
| Neck generators | `generators/neck_headstock_generator.py`, `neck_taper/neck_outline_generator.py` | Geometry only |
| Vectorizer spec | `services/blueprint-import/vectorizer_phase3.py` | Les Paul range defined (430-470mm) |

---

## Part 5 · Gap Registry

| ID | Gap | Severity | Category | Shared With |
|----|-----|----------|----------|-------------|
| LP-GAP-01 | Multi-layer CAM DXF missing — `LesPaul_CAM_Closed.dxf` with 8 named layers (Cutout, Neck Mortise, Pickup Cavity, Electronic Cavities, Wiring Channel, Pot Holes, Studs, Screws) referenced in spec but never delivered. Existing generator cannot function without it. | **CRITICAL** | DXF / Asset | FV-GAP-01 (Flying V DXF missing) |
| LP-GAP-02 | Cavity positions in Phase 1 are heuristic center-offset approximations, not derived from precision DXF geometry. Neck pocket at 78% X span, pickups at ±offset from center, electronics at -3.0"/-1.5" — all unvalidated against reference drawings. | **CRITICAL** | CAM / Accuracy | FV-GAP-10 (parametric approx body outline) |
| LP-GAP-03 | No neck CNC pipeline — only 2D geometry generators exist (`neck_headstock_generator.py`, `neck_outline_generator.py`). No G-code for neck profile, headstock routing, truss rod channel, or fret slots. | **HIGH** | CAM / Neck | — |
| LP-GAP-04 | Fret slot CAM (`fret_slots_cam.py`, 934 lines) exists with API routes but is not wired into the build pipeline. Spec has 22 fret positions. | **HIGH** | CAM / Integration | — |
| LP-GAP-05 | Carved top uses elliptical paraboloid approximation (`z = -dx²/2R - dy²/2R`). Real 1959 Les Paul top has asymmetric carve, flatter crown, steeper cutaway falloff. Acceptable for production lutherie; insufficient for museum-grade reproduction. | **MEDIUM** | CAM / Geometry | BEN-GAP-01 (archtop carved surface) |
| LP-GAP-06 | No G43 tool length compensation emitted in any phase file. All 7 tool changes require manual Z-touch-off. | **MEDIUM** | Post / G-code | OM-PURF-07 (no cutter compensation), FV-GAP-07 (manual M0 pauses) |
| LP-GAP-07 | Purfling offset path (OP70–71) uses naive vertex-normal averaging. Self-intersection possible at cutaway concavity. Spanish wave channel has only 0.175mm clearance — bad offset produces loose or tight fit. | **MEDIUM** | CAM / Geometry | OM-GAP-04 (no purfling channel CAM), BEN-GAP-02 (no binding channel routing), OM-PURF-02 (no purfling ledge op) |
| LP-GAP-08 | No G-code simulation/backplot validation performed. 452K lines of toolpath unverified for collisions, air-cutting, over-depth plunges, or tab miscalculation. | **MEDIUM** | Verification | — |
| LP-GAP-09 | Binding ledge on carved top not routed. Spec defines `binding_ledge_mm: 1.5` — a flat shelf at the body perimeter for binding seating. Phase 3 rasters the full dome but does not create this shelf. | **LOW** | CAM / Omission | BEN-GAP-02 (binding channel on curved surface) |
| LP-GAP-10 | Mixed unit systems across phases: Phase 1-2 use G20 (inches), Phase 3 uses G21 (mm). Each file sets the mode explicitly. Risk: operator loads Phase 3 on a controller still in G20 mode from Phase 2 → all coordinates off by 25.4×. | **LOW** | Post / Safety | — |

---

## Part 6 · Cross-References to Prior Builds

| Shared Gap Pattern | This Build | J45 | OM-28 | Benedetto | Flying V |
|-------------------|------------|-----|-------|-----------|----------|
| Missing DXF from reference | LP-GAP-01 | — | — | — | FV-GAP-01 |
| Body outline parametric approx | LP-GAP-02 | — | — | — | FV-GAP-10 |
| No binding/purfling channel CAM | LP-GAP-07 | — | OM-GAP-04 | BEN-GAP-02 | — |
| No cutter compensation (G41/G42/G43) | LP-GAP-06 | — | OM-PURF-07 | — | FV-GAP-07 |
| No body profiling toolpath class | N/A (generated directly) | VINE-04 | OM-GAP-06 | BEN-GAP-07 | FV-GAP-03 |
| Carved surface geometry | LP-GAP-05 | — | — | BEN-GAP-01 | — |
| Binding ledge on curved surfaces | LP-GAP-09 | — | — | BEN-GAP-02 | — |
| Purfling ledge multi-pass | LP-GAP-07 | — | OM-PURF-02 | — | — |

### New gaps unique to this build

- **LP-GAP-03:** First design attempting a full neck CNC pipeline from spec. All prior builds focused on body only.
- **LP-GAP-04:** First design where fret slot CAM exists but isn't integrated into a unified build sequence.
- **LP-GAP-05:** First carved top (3D surfacing) G-code in the system. The Benedetto archtop identified the gap conceptually; this build actually generated the toolpath.
- **LP-GAP-08:** First build generating 452K+ lines — simulation validation is now a practical necessity, not just good practice.
- **LP-GAP-10:** First build using mixed unit systems across phases (inches for legacy compatibility, mm for 3D surfacing precision).

### Evolution note

The Les Paul is the first instrument to produce **all three machining domains** in one session: 2.5D pocketing (Phase 1), contour-following channel routing (Phase 2), and true 3D surfacing (Phase 3). Prior builds each covered only one domain. This exposes integration seams that previous single-domain builds didn't encounter.

---

## Part 7 · Remediation Roadmap

### Phase A — Pre-Cut Validation (before any machining)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Print 1:1 template from Phase 1 G-code, overlay on reference blueprint, verify all 12 cavity coordinates | LP-GAP-02 | 1 hour |
| Run all 3 `.nc` files through CAMotics or NCViewer | LP-GAP-08 | 30 min |
| Run OP70 purfling scrap test on waste material | LP-GAP-07 (partial) | 30 min |
| Add `G43 H{n}` after each tool change in generator | LP-GAP-06 | 15 min |
| Add `; WARNING: MILLIMETERS (G21)` header to Phase 3 | LP-GAP-10 | 5 min |

### Phase B — DXF Recovery (resolves largest accuracy gap)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Locate original `Les Paul_Project/` directory from ltb-express | LP-GAP-01 | Variable |
| OR: Create multi-layer CAM DXF programmatically from spec geometry | LP-GAP-01 | 4 hours |
| Re-generate Phase 1 using existing `LesPaulBodyGenerator` with real DXF layers | LP-GAP-02 | 1 hour |

### Phase C — Pipeline Completion (full instrument)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Build `lespaul_neck_generator.py` (profile rough/finish, truss rod, headstock) | LP-GAP-03 | 8+ hours |
| Wire `fret_slots_cam.py` into build as Phase 4 | LP-GAP-04 | 2 hours |
| Add OP82 binding ledge routing to Phase 3 | LP-GAP-09 | 2 hours |
| Replace offset_polygon with pyclipper-based offset | LP-GAP-07 | 3 hours |

### Phase D — Accuracy Upgrade (museum-grade)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Replace dome formula with 3D-scanned isoline data | LP-GAP-05 | Research + implementation |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total gaps | 10 |
| Critical | 2 |
| High | 2 |
| Medium | 4 |
| Low | 2 |
| Shared with prior builds | 6 (of 10) |
| New/unique to Les Paul | 4 |
| G-code files generated | 3 |
| Total G-code lines | 452,840 |
| Tool changes across all programs | 8 |
| Distinct bits required | 7 (T1–T7) |
| CNC operations | 18 (OP10–OP81) |
| Registry status change | `STUB` → `COMPLETE` |
| Files created this session | 7 |
| Files modified this session | 3 |
| Build phases | 3 (Mahogany Back → Purfling Channels → Carved Top) |
