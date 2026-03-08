# Benedetto 17" Archtop — Spanish Rope Binding — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-07  
**Status:** Design Complete — Pipeline Has 9 Identified Gaps  
**Priority:** High  
**Context:** Custom Benedetto 17" archtop jazz guitar with continuous Spanish rope binding wrapping body perimeter, up the neck edges, and around the headstock. Exercises archtop-specific CAM (top/back carving, F-hole cutting) and the full binding/purfling pipeline that doesn't yet exist.  

---

## Executive Summary

The Benedetto 17" is **the most complete instrument model in the system** — `COMPLETE` status with DXF body outline, F-holes, and graduation map extracted from original blueprints via AI vision. This custom build adds a Spanish rope binding package that wraps continuously from body to neck to headstock, using the `classic_rope_5x9` matrix pattern (ebony/maple) from the traditional craftsman library.

**What works today:** The body outline DXF exists and is production-quality. F-hole DXFs are ready. The graduation map provides top-carving thickness data. The traditional matrix pattern system can fabricate rope binding strips — `MatrixFormula` → `StripCutList` → `AssemblyInstruction` is production-ready. Three new binding-specific rope presets (`spanish_rope_binding_5x9`, `_fine_4x7`, `_bold_6x9`) with thinner strips for tight-radius bending are now available.

**What breaks:** 9 gaps. The binding/purfling subsystem doesn't exist at all in the backend (frontend stubs only). Archtop-specific CAM (top graduation carving, F-hole routing) has API endpoint stubs but no toolpath generation. No body perimeter profiling toolpath. The existing rope matrix can fabricate the strip, but there's no geometry module to compute the binding channel path, handle the 3 miter joints (heel, nut, headstock tip), or generate the channel routing toolpath. The Benedetto headstock outline isn't in the headstock geometry library.

> **Annotation:** This build is the first to exercise **continuous binding across three zones** (body → neck → headstock). The 3 miter joints at zone transitions are a binding-specific challenge that no other design in the system has attempted. The rope pattern fabrication itself works via `presets.py` — the gap is in *applying* the fabricated strip to the instrument geometry.

---

## Part 1: Custom Benedetto Design Specification

### Base Instrument

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | Benedetto 17" carved archtop | `instrument_model_registry.json` → `benedetto_17` (COMPLETE) |
| Scale length | 647.7 mm (25.5") | `models/benedetto_17.json` |
| Frets | 22 (14 clear of body) | Benedetto standard |
| Tuning | Standard E | |
| Fretboard radius | 304.8 mm (12") | Archtop standard |
| Cutaway | Venetian | Benedetto signature |

### Body Specification

| Parameter | Value | Source |
|-----------|-------|--------|
| Lower bout | 431.8 mm (17") | `models/benedetto_17.json` |
| Upper bout | 279.4 mm (11") | Blueprint extraction |
| Waist | 228.6 mm (9") | Blueprint extraction |
| Body length | 482.6 mm (19") | Blueprint extraction |
| Rim depth | 82.55 mm (3.25") | Blueprint extraction |
| Cutaway depth | 76.2 mm (3") | Venetian cutaway |
| Top wood | European Spruce, hand-graduated | |
| Back & sides | European Maple, hand-graduated back | |
| F-holes | Traditional archtop, 101.6 mm (4") length | DXF available |
| Top apex thickness | 7.0 mm, edge 3.5 mm | Benedetto standard |
| Back apex thickness | 5.5 mm, edge 3.0 mm | Benedetto standard |

> **Annotation:** Body outline and F-hole DXFs exist on disk — the Benedetto 17" is one of only a few models with actual extracted DXF assets (COMPLETE status). Graduation map JSON also available for CNC rough-carving reference.

### Spanish Rope Binding Specification

The signature design element — continuous ebony/maple rope binding wrapping three zones:

**Zone 1: Body Perimeter**

| Layer | Material | Width (mm) | Notes |
|-------|----------|------------|-------|
| 1 (outer) | Maple | 1.5 | Outer containment strip |
| 2 (center) | Rope pattern | 4.0 | `classic_rope_5x9` matrix, ebony/maple |
| 3 (inner) | Ebony | 0.5 | Inner containment strip |
| **Total** | | **6.0 mm** | Top and back perimeter |

Channel specification:
- Width: 6.0 mm
- Depth: 2.0 mm
- Applied to: top perimeter, back perimeter
- Side binding: plain maple (1.5 mm) connecting top and back

**Zone 2: Neck Edges**

| Layer | Material | Width (mm) | Notes |
|-------|----------|------------|-------|
| 1 (outer) | Maple | 0.5 | Edge strip |
| 2 (center) | Rope pattern | 1.5 | `spanish_rope_binding_fine_4x7` preset |
| 3 (inner) | Ebony | 0.5 | Edge strip |
| **Total** | | **2.5 mm** | Both fretboard edges, nut to heel |

Channel specification:
- Width: 2.5 mm
- Depth: 1.5 mm
- Uses fine preset for tight bending around neck taper

**Zone 3: Headstock Perimeter**

| Layer | Material | Width (mm) | Notes |
|-------|----------|------------|-------|
| 1 (outer) | Maple | 0.5 | Edge strip |
| 2 (center) | Rope pattern | 1.5 | `spanish_rope_binding_fine_4x7` preset |
| 3 (inner) | Ebony | 0.5 | Edge strip |
| **Total** | | **2.5 mm** | Full headstock perimeter |

Channel specification:
- Width: 2.5 mm
- Depth: 1.5 mm
- Full perimeter wrap including headstock tip curve

**Miter Joints (3 critical transitions):**

| Joint | Location | Angle | Challenge |
|-------|----------|-------|-----------|
| MJ-1 | Heel cap | 45° miter | Body binding meets neck binding at heel. Grain direction change. |
| MJ-2 | Nut | 45° miter | Neck binding transitions to headstock binding. Masked by nut overhang. |
| MJ-3 | Headstock tip | Continuous bend | Tight radius (~20mm) around headstock tip. No joint if strip is flexible enough. |

**Rope Strip Fabrication (via traditional matrix system):**

The `classic_rope_5x9` and `spanish_rope_binding_fine_4x7` presets define the matrix. The existing `TraditionalPatternGenerator` can produce `StripCutList` and `AssemblyInstruction` for fabrication. The body rope uses the standard preset; neck/headstock use the fine preset with thinner strips for tight bending.

> **Annotation:** This is the key insight — the rope *strip fabrication* works today via the matrix system. What's missing is the binding *channel geometry* (where to cut on the body/neck/headstock) and the *channel routing CAM* (G-code for cutting the channels). The strip goes into the channel, but neither the channel path nor the channel-cutting toolpath exists.

### Neck Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Profile | Medium C | Archtop jazz standard |
| Nut width | 43.0 mm (1.693") | |
| Depth at 1st | 21.0 mm | |
| Depth at 12th | 23.0 mm | |
| Fretboard wood | Ebony | |
| Neck wood | Maple | Archtop standard |
| Neck angle | 3.5° | Required for archtop floating bridge height |
| Body join fret | 14th | |
| Truss rod | Two-way adjustable | |

### Headstock Specification

| Parameter | Value |
|-----------|-------|
| Style | Archtop classical (open-back tuners) |
| Angle | 14° |
| Length | 200 mm |
| Width | 88 mm |
| Overlay | Ebony veneer |
| Tuner layout | 3+3 open-back |
| Rope binding | Full perimeter wrap, continuous with neck |

### Bridge & Hardware

| Component | Specification |
|-----------|---------------|
| Bridge | Floating archtop, ebony, adjustable thumbwheel saddles |
| Tailpiece | Archtop trapeze, nickel |
| Pickguard | Floating elevated, tortoiseshell celluloid, bracket-mounted |
| Pickup | Single floating mini-humbucker on pickguard bracket |
| Tuners | Open-back, 3+3 |

> **Annotation:** Archtop architecture is fundamentally different from flat-top acoustics — floating bridge (no pin holes, no saddle slot), F-holes (no soundhole, no rosette), and body routing is primarily top/back carving plus F-hole cutting. The binding is the decorative focus here instead of a rosette.

---

## Part 2: Pipeline Integration Audit

### Subsystem Status Matrix

| Subsystem | Status | Can Produce G-code? | Notes |
|-----------|--------|---------------------|-------|
| Body outline DXF | **Production** | — | `benedetto_17/body_outline.dxf` exists |
| F-hole DXFs | **Production** | — | `benedetto_17/f_holes.dxf` exists |
| Graduation map | **Production** | — | `benedetto_17/graduation_map.json` exists |
| Body perimeter profiling | **Missing** | No | Only interior pocket clearing exists |
| Top/back archtop carving | **Stub** | No | API endpoints exist, no toolpath generation |
| F-hole routing toolpath | **Missing** | No | DXF exists, no CAM to cut it |
| Rope strip fabrication | **Production** | — | MatrixFormula → StripCutList → AssemblyInstruction |
| Binding-specific rope presets | **NEW** | — | 3 presets: standard, fine, bold |
| Binding geometry backend | **Missing** | No | No offset curves, no layer stack |
| Binding channel routing CAM | **Missing** | No | No purfling channel toolpath |
| Neck binding geometry | **Missing** | No | No fretboard edge offset computation |
| Headstock binding geometry | **Missing** | No | No headstock perimeter offset |
| Miter joint computation | **Missing** | No | No joint angle/position calculator |
| Archtop headstock outline | **Missing** | No | Not in `neck_headstock_config.py` |
| Neck G-code endpoint | **Missing** | No | Class exists, no HTTP route |
| Fret calculator | **Production** | — | Scale length → fret positions works |
| Bridge placement | **Production** | — | Archtop bridge preset works |
| Archtop contour endpoints | **Stub** | No | `/cam/archtop/contours/` planned |

### What Can Be CNC-Manufactured Today

1. **Rope binding strips** — Full traditional matrix → cut list → assembly pipeline
2. **Fret slot positions** — Fret math is production at 647.7mm scale
3. **Bridge compensation** — Archtop preset in bridge calculator works
4. **Body outline reference** — DXF can be used for manual CNC programming

### What Cannot Be CNC-Manufactured Today

1. **Body perimeter profile routing** — No profiling toolpath mode
2. **Top graduation carving** — No 3D contour toolpath from graduation map
3. **Back carving** — Same gap as top
4. **F-hole cutting** — DXF exists, no CAM to follow it
5. **Binding channels (body)** — No geometry, no CAM
6. **Binding channels (neck)** — No geometry, no CAM
7. **Binding channels (headstock)** — No geometry, no CAM
8. **Miter joints** — No computation
9. **Headstock perimeter** — No outline in system

---

## Part 3: Asset Inventory

### Created This Session

| Asset | Path | Status |
|-------|------|--------|
| Benedetto rope binding spec | `specs/benedetto_archtop_rope.json` | **NEW** — full design with 2 variants |
| Spanish rope binding preset | `cam/rosette/presets.py` → `spanish_rope_binding_5x9` | **NEW** — body binding, thin for bending |
| Fine rope binding preset | `cam/rosette/presets.py` → `spanish_rope_binding_fine_4x7` | **NEW** — neck/headstock, narrower |
| Bold rope binding preset | `cam/rosette/presets.py` → `spanish_rope_binding_bold_6x9` | **NEW** — wide archtop body |
| Registry update | `instrument_model_registry.json` → `benedetto_17` assets | **UPDATED** — added spec ref |

### Pre-Existing Assets (Benedetto 17" — COMPLETE)

| Asset | Path | Status |
|-------|------|--------|
| Body outline DXF | `benedetto_17/body_outline.dxf` | Production — vectorizer extracted |
| F-hole DXF | `benedetto_17/f_holes.dxf` | Production — vectorizer extracted |
| Graduation map | `benedetto_17/graduation_map.json` | Production — carving reference |
| Benedetto model spec | `models/benedetto_17.json` | Production — AI-extracted dimensions |
| Archtop generic stub | `guitars/archtop.py` | Stub — basic InstrumentSpec |
| ArchtopCalculator.vue | Frontend | Under development |
| F-hole soundhole preset | SoundholeDesignerView.vue | Available |
| Archtop bridge preset | bridgeCalculatorTypes.ts | Production |
| Classic rope 5x9 preset | `cam/rosette/presets.py` | Production — rosette pattern |
| Torres rope presets (×3) | `cam/rosette/presets.py` | Production — various sizes |
| BindingDesignerView.vue | Frontend | Stub — UI shell, no backend |
| PurflingDesignerView.vue | Frontend | Stub — rope pattern listed |

---

## Part 4: Gap Registry

### BEN-GAP-01: No Binding Geometry Backend

- **Severity:** Critical
- **Category:** Backend
- **Description:** The binding/purfling system has frontend stubs only. No backend module computes binding channel paths. For the Benedetto rope binding design, we need offset curves from the body outline DXF (inset by binding width), layer boundary positions, and channel cross-section dimensions. This is the same core gap as OM-GAP-03 but with the additional complexity of archtop curved (non-flat) surfaces.
- **Resolution:** Create `app/cam/binding/` module with:
  - `geometry.py` — offset body outline DXF inward by total binding width; compute channel center-line
  - `channel_spec.py` — dataclass for channel width, depth, layer stack, cross-section profile
  - `binding_router.py` — API endpoints for binding preview and channel specification
- **Blocked by:** Nothing — body DXF exists
- **Blocks:** BEN-GAP-02, BEN-GAP-04, BEN-GAP-05

### BEN-GAP-02: No Binding Channel Routing CAM

- **Severity:** Critical
- **Category:** CAM
- **Description:** Even with binding geometry (BEN-GAP-01), there's no CAM module for purfling channel routing toolpaths. A binding channel is routed along the body perimeter at fixed depth and offset — this requires a contour-following toolpath, not pocket clearing. For the Benedetto specifically, the archtop recurve adds complexity: the channel must follow the curved top surface at consistent depth below the recurve edge.
- **Resolution:** Create `app/cam/binding/channel_cam.py`:
  - Contour-following toolpath from offset curve
  - Configurable depth (2.0mm body, 1.5mm neck/headstock)
  - Corner handling for waist and cutaway tight radii
  - F-hole proximity avoidance
- **Blocked by:** BEN-GAP-01
- **Blocks:** CNC channel routing

### BEN-GAP-03: Body Perimeter Profiling Toolpath Missing

- **Severity:** High
- **Category:** CAM
- **Description:** No perimeter profiling toolpath mode exists — only interior pocket clearing. Body outline routing requires following the outside contour with tabs, lead-in/lead-out arcs. Shared gap with OM-GAP-02 and VINE-GAP-05.
- **Resolution:** Add `ProfileToolpath` class to `app/cam/toolpath/` — closed polyline follower with tab placement, climb/conventional direction, lead-in/lead-out arcs.
- **Blocked by:** Nothing
- **Blocks:** Body outline CNC routing

### BEN-GAP-04: Neck Binding Geometry Missing

- **Severity:** High
- **Category:** Geometry
- **Description:** No module computes fretboard edge binding paths. For the Benedetto, rope binding runs both edges of the fretboard from nut to heel. This requires: (1) fretboard outline from nut width, heel width, and fret count; (2) offset curves along both edges at 2.5mm width; (3) channel path that accounts for fretboard radius (the binding sits on the curved edge, not a flat surface).
- **Resolution:** Extend binding geometry module (BEN-GAP-01) to accept fretboard outline parameters and generate edge-binding channel paths. Must account for fretboard taper (43mm at nut → 56mm at heel).
- **Blocked by:** BEN-GAP-01
- **Blocks:** Neck binding CNC routing

### BEN-GAP-05: Headstock Binding Geometry Missing

- **Severity:** High
- **Category:** Geometry
- **Description:** No module computes headstock perimeter binding paths. The Benedetto headstock binding wraps the full perimeter — this requires a headstock outline (which doesn't exist for archtop style) offset inward by 2.5mm. The headstock tip curve (~20mm radius) is the tightest bend in the entire binding run.
- **Resolution:** (1) Add archtop headstock outline to `neck_headstock_config.py` (BEN-GAP-06), then (2) extend binding geometry module to offset headstock outlines for channel paths.
- **Blocked by:** BEN-GAP-01, BEN-GAP-06
- **Blocks:** Headstock binding CNC routing

### BEN-GAP-06: Archtop/Benedetto Headstock Outline Missing

- **Severity:** Medium
- **Category:** Geometry
- **Description:** `neck_headstock_config.py` has Fender, Gibson (open-book electric), PRS, and generic outlines but no archtop headstock. The Benedetto headstock is a rounded paddle shape, wider than most solid-body headstocks (88mm), with a classical aesthetic. Needed for both CNC profiling and binding path computation.
- **Resolution:** Add `ARCHTOP_CLASSICAL` entry to `HeadstockType` enum and corresponding point list in `generate_headstock_outline()`. The Benedetto shape is a rounded rectangle with slight taper, wider at the top.
- **Blocked by:** Nothing
- **Blocks:** BEN-GAP-05, headstock CNC profiling

### BEN-GAP-07: Miter Joint Geometry Computation Missing

- **Severity:** Medium
- **Category:** Geometry
- **Description:** The Benedetto design has 3 miter joints where binding zones transition: heel (MJ-1), nut (MJ-2), and headstock tip (MJ-3). No module computes miter angles, cut positions, or joint geometry. Miter joints require precise angle computation based on the meeting angle of the two binding paths. The heel joint is the most complex — the body curve meets the straight neck at a compound angle that includes the 3.5° neck angle.
- **Resolution:** Create `app/cam/binding/miter.py`:
  - `compute_miter_angle(path_a, path_b, junction_point)` — returns miter angle
  - `generate_miter_cut(binding_strip, angle, position)` — returns cut instructions
  - Handle compound angles at heel (neck angle + body curve tangent)
- **Blocked by:** BEN-GAP-01, BEN-GAP-04
- **Blocks:** Clean binding transitions at zone boundaries

### BEN-GAP-08: Archtop Top/Back Carving CAM

- **Severity:** High
- **Category:** CAM
- **Description:** The archtop's carved top and back are the defining construction detail. The graduation map (`benedetto_17/graduation_map.json`) provides thickness data, and API endpoint stubs exist (`/cam/archtop/contours/csv`, `/cam/archtop/contours/outline`), but no actual toolpath generation module converts graduation data into 3D contour carving toolpaths. This is archtop-specific — flat-top guitars don't need this.
- **Resolution:** Build `app/cam/archtop/` module:
  - `carving_toolpath.py` — generate parallel-plane contour passes from graduation map
  - Support both Mottola method (scaled concentric outline rings) and point-cloud Z-map
  - Roughing (large step-down, wide stepover) and finishing (fine step, tight stepover) strategies
- **Blocked by:** Nothing — graduation map exists
- **Blocks:** CNC archtop top/back rough carving

### BEN-GAP-09: F-Hole Routing CAM

- **Severity:** Medium
- **Category:** CAM
- **Description:** F-hole DXFs exist (`benedetto_17/f_holes.dxf`) but there's no CAM module to generate F-hole routing toolpaths. F-hole routing is a precision operation — the inside profile of the F must be cut through the carved top at exact positions, following the DXF outline. This requires a contour-following toolpath similar to body perimeter profiling but without tabs (the material inside the F-hole is scrap).
- **Resolution:** Adapt the `ProfileToolpath` (BEN-GAP-03) for F-hole cutting — follow DXF outline, full depth through top, no tabs needed, lead-in/lead-out at the F-hole endpoints.
- **Blocked by:** BEN-GAP-03 (shared profiling toolpath concept)
- **Blocks:** CNC F-hole cutting

---

## Part 5: Remediation Roadmap

### Phase 1: Foundation Geometry (enables body work + binding paths)

| Gap | Task | Effort |
|-----|------|--------|
| BEN-GAP-06 | Add archtop headstock outline to `neck_headstock_config.py` | Low |
| BEN-GAP-03 | Build `ProfileToolpath` for body/F-hole perimeter routing | High |
| BEN-GAP-01 | Build binding geometry backend (offset curves, layer stack, channel spec) | High |

### Phase 2: Binding Pipeline (enables the signature rope binding)

| Gap | Task | Effort |
|-----|------|--------|
| BEN-GAP-02 | Build binding channel routing CAM | High |
| BEN-GAP-04 | Extend binding geometry for neck fretboard edges | Medium |
| BEN-GAP-05 | Extend binding geometry for headstock perimeter | Medium |
| BEN-GAP-07 | Build miter joint geometry computation | Medium |

### Phase 3: Archtop-Specific CAM (enables complete CNC build)

| Gap | Task | Effort |
|-----|------|--------|
| BEN-GAP-08 | Build archtop top/back carving toolpath from graduation map | Very High |
| BEN-GAP-09 | Adapt profiling toolpath for F-hole cutting | Medium |

### Cross-References

| This Gap | Related Gap | Shared? |
|----------|-------------|---------|
| BEN-GAP-01 | OM-GAP-03 (binding geometry) | Yes — same core module |
| BEN-GAP-02 | OM-GAP-04 (purfling channel CAM) | Yes — same core module |
| BEN-GAP-03 | OM-GAP-02, VINE-GAP-05 (body profiling) | Yes — identical |
| BEN-GAP-06 | OM-GAP-06 (Martin headstock) | Similar — different shape |
| BEN-GAP-08 | None | Unique to archtop |
| BEN-GAP-09 | None | Unique to archtop |

---

## Part 6: Spanish Rope Binding — Technical Deep Dive

### Why Rope Binding on an Archtop?

Robert Benedetto's instruments typically use multi-ply plastic or wood binding. Adding Spanish rope binding is a premium custom upgrade that references classical Spanish guitar tradition — transplanting it onto a jazz archtop. The ebony/maple color scheme echoes the Benedetto's European maple body and ebony fretboard/pickguard.

### Traditional Matrix Fabrication (works today)

The rope strip itself is fabricated using the `TraditionalPatternGenerator`:

```
MatrixFormula ("classic_rope_5x9")
    ↓
StripCutList (cutting instructions for veneer strips)
    ↓
AssemblyInstruction (how to reassemble chips into rope pattern)
    ↓
Physical rope binding strip
```

This pipeline is production-ready. The 3 new binding-specific presets adjust strip dimensions for bendability:

| Preset | Use | Width | Thickness | Chip | For |
|--------|-----|-------|-----------|------|-----|
| `spanish_rope_binding_5x9` | Body | 0.8mm | 0.4mm | 1.5mm | Body perimeter (~1200mm path) |
| `spanish_rope_binding_fine_4x7` | Neck/Head | 0.6mm | 0.35mm | 1.2mm | Tight bends (~600mm path) |
| `spanish_rope_binding_bold_6x9` | Wide body | 0.8mm | 0.4mm | 1.5mm | Deep archtop rim (~1200mm path) |

### Bending Challenges by Location

| Location | Radius | Challenge | Mitigation |
|----------|--------|-----------|------------|
| Lower bout | ~215mm | Easy — gentle curve | Standard bending |
| Upper bout | ~140mm | Moderate | Pre-soak strips |
| Waist | ~50mm | Tight — tightest standard curve | Kerf inner surface |
| Venetian cutaway | ~15mm | Very tight — may fracture | Use fine preset or kerf heavily |
| Headstock tip | ~20mm | Tight | Use fine preset |
| Neck taper | Straight | No bending — straight run | Easiest section |

### Total Binding Length Estimate

| Zone | Length (mm) | Preset |
|------|-------------|--------|
| Body top perimeter | ~1200 | `spanish_rope_binding_5x9` |
| Body back perimeter | ~1200 | `spanish_rope_binding_5x9` |
| Neck (both edges × ~370mm) | ~740 | `spanish_rope_binding_fine_4x7` |
| Headstock perimeter | ~480 | `spanish_rope_binding_fine_4x7` |
| **Total rope strip needed** | **~3620 mm** | Plus 10% waste |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total gaps identified | 9 |
| Critical gaps | 2 (binding geometry, channel routing CAM) |
| High gaps | 4 (body profiling, neck binding, headstock binding, archtop carving) |
| Medium gaps | 3 (headstock outline, miter joints, F-hole routing) |
| Gaps shared with OM build | 3 (binding geometry, channel CAM, body profiling) |
| Gaps shared with J45 build | 1 (body profiling) |
| Archtop-unique gaps | 2 (top/back carving, F-hole routing) |
| Assets created this session | 5 (spec JSON, 3 binding presets, registry update) |
| Pre-existing assets (COMPLETE) | 4 (body DXF, F-holes DXF, graduation map, model spec) |
| Rope presets available | 6 (3 rosette + 3 binding-specific) |
