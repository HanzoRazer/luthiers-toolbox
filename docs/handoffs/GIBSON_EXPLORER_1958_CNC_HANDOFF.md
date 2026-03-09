# 1958 Gibson Explorer — Full CNC Build Handoff

> **Model:** `explorer` | **Registry Status:** `STUB` → `PARTIAL` | **Session Date:** 2026-03-08

---

## Executive Summary

The Gibson Explorer build completes the CNC program for the third Gibson body in the The Production Shop fleet (after Les Paul and Flying V). This is the **first 1958 Modernistic-series build** — the Explorer and Flying V were launched together as Gibson's futuristic line and share the same korina material, hardware platform (ABR-1 + stoptail + PAF humbuckers), and Gibson 24.75" scale. This session created the authoritative spec JSON with 2 variants and 18 CNC operations, the full-build G-code generator script, and produced **9,401 lines of G-code** across two phases covering the complete body routing and perimeter profile.

**What works:** Body outline DXF exists (24-point polygon), authoritative spec with all operations/tools/variants, 2-phase G-code generation (rear cavity routing + perimeter profile), 3-tool library, build summary manifest, standalone build macro JSON with 10 gap annotations.

**What breaks:** The DXF outline is a coarse 24-point approximation with no curves — production CNC requires 200+ points. DXF is AC1024 format instead of required R12 (AC1009). DXF extents (556.5×434.7mm) don't match spec dimensions (475×460mm) — non-uniform scaling applied as workaround. Cavity positions for pickups, control cavity, and toggle switch are estimated from general Gibson specs — not verified against factory Explorer drawings.

**Critical annotation:** The Phase 1 G-code (OP10–OP65) routes real material. Cavity positions MUST be validated against a 1:1 reference drawing before any cutting operation. EX-GAP-01 and EX-GAP-02 are production blockers.

---

## Part 1 · Base Instrument

| Field | Value |
|-------|-------|
| Model ID | `explorer` |
| Display Name | 1958 Gibson Explorer |
| Manufacturer | Gibson |
| Year | 1958 |
| Category | `electric_guitar` |
| Scale Length | 628.65mm (24.75") |
| Frets | 22 |
| Strings | 6 |
| Body Dimensions | 460mm L × 475mm W × 44.45mm thick |
| DXF Outline Dimensions | 556.5mm × 434.7mm (needs rescaling) |
| Body Material | Korina (African Limba) |
| Body Material (alt) | Mahogany |
| Construction | Flat-top solidbody (single slab, no carved top) |
| Neck Joint | Set-neck long tenon (55mm × 95mm × 16mm mortise) |
| Neck Angle | 4.5° |
| Pickups | HH — dual PAF humbuckers, 71mm × 40mm routes |
| Bridge | ABR-1 Tune-o-matic (74mm stud spacing) |
| Tailpiece | Stoptail (82.5mm stud spacing) |
| Control Layout | 3-knob (2V + 1T), toggle on upper horn |
| Control Cavity | 108mm × 64mm × 31.75mm (rear-routed) |
| Registry Status | `STUB` → `PARTIAL` |
| Spec File | `instrument_geometry/specs/gibson_explorer.json` |

### Variants

| Variant | Key Differences |
|---------|----------------|
| `original_1958` | Korina body, PAF humbuckers, split-V headstock, gold hardware, dot inlays |
| `reissue_76` | Mahogany body, pointed headstock, slimmer neck profile, no binding |

---

## Part 2 · Subsystem Status Matrix

| Subsystem | Status | Can Produce G-code? | Notes |
|-----------|--------|---------------------|-------|
| Spec JSON | ✅ CREATED | N/A | `gibson_explorer.json` — 2 variants, 18 ops, full hardware spec |
| Registry Entry | ✅ UPDATED | N/A | `STUB` → `PARTIAL`, 7 asset entries added |
| Model Stub | ✅ EXISTS | N/A | `guitars/explorer.py` — basic MODEL_INFO |
| Body Outline DXF | ⚠️ EXISTS (COARSE) | Phase 2 (perimeter) | 24-point polygon, AC1024 format, needs refinement |
| Body Outlines JSON | ❌ MISSING | No | No `explorer` entry in body_outlines.json |
| Phase 1 G-code (Rear Routing) | ✅ GENERATED | Yes (8,480 lines) | OP10–OP65, cavity positions are estimates |
| Phase 2 G-code (Perimeter) | ✅ GENERATED | Yes (921 lines) | OP50, 8 tabs, DXF scaled to spec |
| Build Summary | ✅ GENERATED | N/A | `Explorer_1958_BuildSummary.json` |
| Build Macro | ✅ CREATED | N/A | `Explorer_1958_BuildMacro.json` — standalone, 10 gap annotations |
| Full-Build Generator Script | ✅ CREATED | Yes | `scripts/generate_explorer_full_build.py` |
| Neck CNC Pipeline | ❌ MISSING | No | No Explorer neck geometry |
| Headstock Generator | ❌ MISSING | No | Split-V headstock not implemented |
| Vectorizer | ❌ MISSING | No | No Explorer spec range or vectorizer config |
| Frontend Card | ❌ MISSING | No | No Explorer UI component |

---

## Part 3 · CNC Program Summary

### Tool Library

| Tool | Name | Diameter | RPM | Feed | Plunge | DOC | Role |
|------|------|----------|-----|------|--------|-----|------|
| T1 | 10mm Flat End Mill | 10.0mm | 18,000 | 5,000 mm/min | 800 mm/min | 5.0mm | Roughing |
| T2 | 6mm Flat End Mill | 6.0mm | 18,000 | 3,500 mm/min | 600 mm/min | 1.5mm | Finishing / Perimeter |
| T3 | 3mm Flat/Drill | 3.0mm | 20,000 | 1,500 mm/min | 400 mm/min | 1.0mm | Drilling / Channels |

### Phase 1 — Rear Face Routing (8,480 lines)

Body face-down, rear face up. Z=0 at rear surface. All internal routing.

| OP | Name | Tool | Depth | Strategy |
|----|------|------|-------|----------|
| OP10 | Fixture / Registration Holes (4x) | T3 | 10.0mm | Peck drill |
| OP20 | Neck Pocket Rough | T1 | 16.0mm | Helical entry + spiral out |
| OP21 | Neck Pickup Cavity Rough | T1 | 19.05mm | Helical entry + spiral out |
| OP22 | Bridge Pickup Cavity Rough | T1 | 19.05mm | Helical entry + spiral out |
| OP23 | Control Cavity Rough | T1 | 31.75mm | Helical entry + spiral out |
| OP25 | Neck Pocket Finish | T2 | 16.0mm | Helical entry + spiral out |
| OP26 | Neck Pickup Cavity Finish | T2 | 19.05mm | Helical entry + spiral out |
| OP27 | Bridge Pickup Cavity Finish | T2 | 19.05mm | Helical entry + spiral out |
| OP28 | Control Cavity Finish | T2 | 31.75mm | Helical entry + spiral out |
| OP35 | Cover Plate Recess | T2 | 3.175mm | Helical entry + spiral out |
| OP40 | Wiring Channels (3 routes) | T3 | 12.7mm | Linear slot milling |
| OP60 | Pot Shaft Holes (3x 9.53mm) | T3 | 44.45mm | Helical bore (through) |
| OP61 | Bridge Post Holes (2x 11.1mm) | T3 | 19.05mm | Helical bore |
| OP62 | Tailpiece Stud Holes (2x 7.14mm) | T3 | 15.88mm | Helical bore |
| OP63 | Toggle Switch Hole (12.7mm) | T3 | 44.45mm | Helical bore (through) |
| OP64 | Output Jack Bore (12.7mm) | T3 | 25.0mm | Helical bore |
| OP65 | Cover Screw Pilot Holes (4x) | T3 | 12.7mm | Peck drill |

### Phase 2 — Perimeter Profile (921 lines)

Body flipped, front face up. Z=0 at front surface. Full-depth profile cut.

| OP | Name | Tool | Depth | Strategy |
|----|------|------|-------|----------|
| OP50 | Body Perimeter Contour | T2 | 44.45mm | Contour with 8 tabs (12mm wide, 3mm tall) |

### Workpiece Orientation

| Phase | Face Up | Z=0 | Workholding |
|-------|---------|-----|-------------|
| Phase 1 | Rear | Rear surface | Double-sided tape + registration pins |
| Phase 2 | Front | Front surface | Registration pins + clamps |

---

## Part 4 · Asset Inventory

### Created This Session

| Asset | Path | Size | Notes |
|-------|------|------|-------|
| Explorer Spec JSON | `services/api/app/instrument_geometry/specs/gibson_explorer.json` | ~9 KB | Full instrument specification, 2 variants |
| Build Script | `scripts/generate_explorer_full_build.py` | ~28 KB | 2-phase build generator |
| Phase 1 G-code | `exports/explorer_1958/Explorer_1958_Phase1_RearRouting.nc` | 8,480 lines | Rear cavity routing |
| Phase 2 G-code | `exports/explorer_1958/Explorer_1958_Phase2_Perimeter.nc` | 921 lines | Perimeter profile |
| Build Summary | `exports/explorer_1958/Explorer_1958_BuildSummary.json` | ~3 KB | Machine-readable summary |
| Build Macro | `exports/explorer_1958/Explorer_1958_BuildMacro.json` | ~14 KB | Standalone macro, 10 gap annotations |
| This Handoff | `docs/handoffs/GIBSON_EXPLORER_1958_CNC_HANDOFF.md` | — | Build documentation |

### Pre-Existing Assets

| Asset | Path | Notes |
|-------|------|-------|
| Body Outline DXF | `body/dxf/electric/gibson_explorer_body.dxf` | 24-point coarse polygon, AC1024 |
| DXF (Guitar Plans) | `Guitar Plans/Recovered_DXF_Assets/electric/gibson_explorer_body.dxf` | Duplicate of above |
| Model Stub | `instrument_geometry/guitars/explorer.py` | Wave 14, basic MODEL_INFO |
| Registry Entry | `instrument_model_registry.json` → `explorer` | Status: STUB, empty assets |

---

## Part 5 · Gap Registry

| ID | Gap | Severity | Category | Shared With |
|----|-----|----------|----------|-------------|
| EX-GAP-01 | **DXF outline is a coarse 24-point approximation.** Only 24 vertices — straight segments, no curves. Real Explorer has complex compound curves at the waist, horn tips, and lower bout transition. The angular aesthetic requires precise horn geometry. Build script uses this polygon directly for Phase 2 perimeter contour. Production CNC requires 200+ point outline with arc-interpolated curves to avoid faceting visible to the eye. | **CRITICAL** | DXF / Asset | LP-GAP-01 (multi-layer CAM DXF missing), FV-GAP-01 (Flying V DXF missing), SG-GAP-01 (DXF dims stale) |
| EX-GAP-02 | **DXF is AC1024 format (AutoCAD 2010), not R12 (AC1009).** Project convention requires R12 DXF with closed LWPolylines only. Current DXF uses AC1024 features. Build script loads it successfully via `ezdxf` but the file cannot be consumed by older CAM pipelines or validated against the project's DXF constraint checker. | **CRITICAL** | DXF / Format | — |
| EX-GAP-03 | **DXF extents do not match spec body dimensions.** DXF measures 556.5×434.7mm vs spec 475×460mm — the DXF is 17.1% wider and 5.5% shorter. Build script computes non-uniform scale factors (`scale_x = 475/556.5 = 0.854`, `scale_y = 460/434.7 = 1.058`) and applies them to every perimeter vertex. This distorts the Explorer shape — waist angles change, horn proportions shift. The DXF must be regenerated at correct dimensions. | **HIGH** | DXF / Geometry | LP-GAP-02 (heuristic cavity positions), SG-GAP-02 (DXF centerline offset) |
| EX-GAP-04 | **Pickup cavity positions derived from general Gibson specs.** Neck pickup `y_from_top=220mm` and bridge pickup `y_from_top=350mm` are calculated from standard PAF spacing on a 24.75" scale. The Explorer's angular body makes these positions less predictable than on the symmetrical Les Paul — horn geometry affects where the neck pickup sits relative to the body edge. Positions must be verified against factory Explorer drawings or a reference instrument. | **HIGH** | CAM / Accuracy | LP-GAP-02 (heuristic cavity positions), SG-GAP-04 (pickup y_from_bridge inconsistency) |
| EX-GAP-05 | **Control cavity position is estimated.** `y_from_top=370mm` places the 3-knob control cavity in the lower body. On the Explorer, the control layout changed between years — the 1958 original had a shallow angled control plate, while reissues typically use a rear-routed cavity. Build script assumes rear-routed. Exact position needs factory drawing verification. | **MEDIUM** | CAM / Accuracy | — |
| EX-GAP-06 | **Toggle switch position on upper horn is estimated.** `x_center=50mm` (offset from centerline toward treble), `y_from_top=90mm` places the toggle at the base of the upper horn. This is the Explorer's signature control feature — the toggle is visible from the audience side. Location varies between production years (1958–1963 vs post-1976 reissues). No factory template available. | **MEDIUM** | CAM / Accuracy | — |
| EX-GAP-07 | **Bridge and tailpiece stud positions use standard Gibson spacing — not verified for Explorer.** ABR-1 bridge at 74mm stud spacing and stoptail at 82.5mm spacing are standard Gibson dimensions shared with the Les Paul. However, the Explorer's wider body and different geometry may use slightly different mounting positions relative to the centerline. Stud depths (11.1mm bridge, 7.14mm tailpiece) also need verification. | **MEDIUM** | CAM / Accuracy | — |
| EX-GAP-08 | **Neck pocket tenon dimensions are estimated from Les Paul patterns.** 55×95×16mm set-neck pocket at fret 22. The Les Paul tenon is 53×89×16mm at fret 16 — the Explorer's deeper neck join (6 frets further into body) may use a wider or differently shaped tenon. Gibson's set-neck geometry varied between models in the 1958 era. | **MEDIUM** | CAM / Accuracy | LP-GAP-02 (general position heuristics) |
| EX-GAP-09 | **Pot layout is simplified 3-knob arrangement.** 30mm spacing between 2V+1T pots is estimated. The Explorer's 3-knob control plate geometry is different from the Les Paul's 4-knob layout. Need factory control plate template or a reference instrument measurement. Wiring channel routes (3 paths between cavities) use simplified straight-line paths that may intersect structural wood or other features. | **LOW** | Spec / Accuracy | SG-GAP-06 (wiring channels no coordinates) |
| EX-GAP-10 | **Output jack position on lower bout edge is estimated.** Explorer traditionally has an edge-mounted jack plate on the lower bout, angled at approximately 15–20° from perpendicular. Build script drills a vertical 12.7mm bore at `x=50mm, y_from_top=430mm` — no angle applied. Actual mounting method (edge plate vs through-body) and angle need verification. | **LOW** | Spec / Accuracy | SG-GAP-03 (output jack bore angle undefined) |
| EX-GAP-11 | **No body_outlines.json entry for Explorer.** Outline data available only via the DXF file, not in the shared JSON outline catalog used by other subsystems (vectorizer, frontend preview). Other models have entries in `body_outlines.json` enabling DXF-free preview rendering. | **LOW** | Asset / Integration | — |
| EX-GAP-12 | **No G-code simulation/backplot validation performed.** 9,401 lines of toolpath across 2 phases unverified for collisions, air-cutting, over-depth plunges, or tab miscalculation. | **LOW** | Verification | LP-GAP-08 (452K unverified lines), SG-GAP-13 (11.9K unverified lines) |
| EX-GAP-13 | **No G43 tool length compensation emitted.** All 3 tool changes require manual Z-touch-off. No `G43 H{n}` commands in either phase file. | **LOW** | Post / G-code | LP-GAP-06, SG-GAP-14, FV-GAP-07 |

---

## Part 6 · Cross-References to Prior Builds

### Gap-Sharing Matrix

| Shared Gap Pattern | This Build | Les Paul | Smart Guitar | Flying V |
|-------------------|------------|----------|--------------|----------|
| DXF outline coarse/stale/missing | EX-GAP-01 | LP-GAP-01 | SG-GAP-01 | FV-GAP-01 |
| DXF geometry doesn't match spec | EX-GAP-03 | — | SG-GAP-02 | — |
| Cavity positions heuristic/estimated | EX-GAP-04, EX-GAP-08 | LP-GAP-02 | SG-GAP-04, SG-GAP-05 | FV-GAP-10 |
| Wiring channel routing simplified | EX-GAP-09 | — | SG-GAP-06 | — |
| Output jack angle undefined | EX-GAP-10 | — | SG-GAP-03 | — |
| No cutter compensation (G43) | EX-GAP-13 | LP-GAP-06 | SG-GAP-14 | FV-GAP-07 |
| No simulation validation | EX-GAP-12 | LP-GAP-08 | SG-GAP-13 | — |

### New gaps unique to this build

- **EX-GAP-02:** First build to encounter a DXF format violation (AC1024 vs R12). Prior builds either had R12 DXFs or no DXF at all.
- **EX-GAP-05:** First rear-routed control cavity on a model where the historical production used a front-mount control plate. Les Paul and Smart Guitar both have unambiguous rear-routed controls.
- **EX-GAP-06:** First design with the toggle switch on a horn tip rather than in the upper bout. Position is uniquely sensitive to horn geometry — a gap that doesn't exist on symmetrical body shapes.
- **EX-GAP-07:** First build where bridge/tailpiece stud spacing needs per-model verification. Les Paul specs are well-documented; Explorer stud positions are less certain in the literature.
- **EX-GAP-11:** First build to expose the missing `body_outlines.json` integration gap. Prior builds either had entries or didn't need them.

### Evolution note

The Explorer is the **simplest solidbody build** in the fleet — flat-top, no carved surface, no purfling, no binding, no IoT electronics. This makes it an ideal **reference build for the CNC pipeline**: if the DXF and cavity position gaps are resolved, the Explorer becomes the first model where the full body can be CNC-machined with only 3 tools in 2 phases. It exposes the minimum viable gap set that all Gibson-platform builds share (DXF quality, cavity position verification, missing G43), without the additional complexity layers that Les Paul (carved top, purfling) and Smart Guitar (IoT cavities, 4th-axis) introduce.

### Comparison Tables

#### vs. Les Paul 1959

| Dimension | Explorer | Les Paul | Notes |
|-----------|----------|----------|-------|
| Body Shape | Angular asymmetric | Single cutaway | Completely different perimeter geometry |
| Construction | Flat-top solidbody | Carved maple top on mahogany | Explorer is simpler — no 3D surfacing needed |
| Phases | 2 | 3 (+ purfling + carved top) | Explorer has no purfling or carved top |
| G-code Lines | 9,401 | 452,840 | Explorer is dramatically less complex |
| Tools | 3 (T1–T3) | 7 (T1–T7) | Explorer needs only basic flat/drill tools |
| Control Layout | 3 knobs + toggle on horn | 4 knobs + toggle in upper bout | Different wiring channel routing |
| Neck Joint | Set-neck at fret 22 | Set-neck at fret 16 | Explorer neck extends further into body |
| Material | Korina (Limba) | Mahogany + Maple | Different density/hardness affects feeds |
| Bridge | ABR-1 (same) | ABR-1 (same) | Identical stud spacing and depth |
| Tailpiece | Stoptail (same) | Stoptail (same) | Identical stud spacing and depth |

#### vs. Smart Guitar v1.1

| Dimension | Explorer | Smart Guitar | Notes |
|-----------|----------|-------------|-------|
| Body Shape | Angular Explorer | Explorer-Klein hybrid | Smart Guitar derived from Explorer concept |
| Construction | Traditional | IoT (dual-board) | Explorer has no electronics pockets |
| Phases | 2 | 2 | Similar structure but different operations |
| G-code Lines | 9,401 | 11,967 | Smart Guitar has more rear-face cavities |
| Neck | Set-neck | Headless bolt-on | Completely different neck joint approach |
| Electronics | Passive (pots/switch) | Active (Pi 5 + Arduino) | Explorer has simple wiring |
| Scale | 628.65mm (24.75") | 628.65mm (24.75") | Same Gibson scale |

#### vs. Flying V 1958

| Dimension | Explorer | Flying V | Notes |
|-----------|----------|----------|-------|
| Era | 1958 Modernistic | 1958 Modernistic | Same product family — launched together |
| Material | Korina | Korina | Same factory material specification |
| Body Shape | Angular horns | V-shaped | Different angular aesthetics |
| Scale | 628.65mm | 628.65mm | Identical |
| Hardware | ABR-1 + Stoptail | ABR-1 + Stoptail | Shared hardware platform |
| Controls | 3 knobs, horn toggle | 3 knobs (on pickguard) | Different control placement |

---

## Part 7 · Remediation Roadmap

### Phase A — Pre-Cut Validation (before any machining)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Print 1:1 template from Phase 1 G-code, overlay on reference blueprint or photograph, verify all cavity coordinates | EX-GAP-04, EX-GAP-05, EX-GAP-06, EX-GAP-08 | 1 hour |
| Run both `.nc` files through CAMotics or NCViewer, verify no collisions or over-depth plunges | EX-GAP-12 | 30 min |
| Add `G43 H{n}` after each tool change in generator script | EX-GAP-13 | 15 min |

### Phase B — DXF Refinement (resolves largest accuracy gap)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Obtain or digitize high-resolution Explorer body outline (200+ points) from a factory template, reissue drawing, or 1:1 photograph tracing | EX-GAP-01 | 2–4 hours |
| Export as R12 (AC1009) DXF with closed LWPOLYLINE at correct scale (475×460mm body, 490×490mm stock) | EX-GAP-02 | 30 min |
| Replace `gibson_explorer_body.dxf` in `body/dxf/electric/` | EX-GAP-01, EX-GAP-02 | 5 min |
| Verify new DXF extents match spec dimensions exactly — eliminate non-uniform scaling | EX-GAP-03 | 30 min |
| Extract outline points and add `explorer` entry to `body_outlines.json` | EX-GAP-11 | 30 min |
| Re-run build script and validate perimeter cut quality in simulator | EX-GAP-01, EX-GAP-12 | 30 min |

### Phase C — Factory Drawing Verification (cavity positions)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Source Gibson Explorer factory drawings, exploded diagrams, or reissue templates | EX-GAP-04, EX-GAP-05, EX-GAP-06, EX-GAP-07, EX-GAP-08 | Variable (research) |
| Verify and update: pickup positions (y_from_top for neck and bridge PAF) | EX-GAP-04 | 30 min |
| Verify and update: control cavity location (y_from_top, rear vs front mount) | EX-GAP-05 | 30 min |
| Verify and update: toggle switch position on upper horn (x_center, y_from_top) | EX-GAP-06 | 30 min |
| Verify and update: bridge/tailpiece stud spacing and hole depths | EX-GAP-07 | 30 min |
| Verify and update: neck pocket tenon dimensions from factory neck/body join specs | EX-GAP-08 | 30 min |
| Verify and update: pot spacing and control plate template | EX-GAP-09 | 30 min |
| Verify output jack mounting method (edge-mounted plate vs through-body bore) and angle | EX-GAP-10 | 30 min |
| Update spec JSON and re-generate G-code after all verified positions | All medium gaps | 1 hour |

### Phase D — Registry and Integration (production readiness)

| Action | Closes Gap | Effort |
|--------|-----------|--------|
| Update `instrument_model_registry.json` status: `PARTIAL` → `COMPLETE` after Phase B+C | — | 15 min |
| Update model stub `guitars/explorer.py` with corrected body dimensions (475×460mm vs current 420×460mm) | — | 15 min |
| Add Explorer to `body_templates.json` | — | 30 min |
| Create vectorizer spec range for Explorer body shape recognition | — | 2 hours |
| Wire frontend card for Explorer model display | — | 2 hours |

---

## Part 8 · Summary Statistics

| Metric | Value |
|--------|-------|
| Total gaps | 13 |
| Critical | 2 |
| High | 2 |
| Medium | 4 |
| Low | 5 |
| Shared with prior builds | 8 (of 13) |
| New/unique to Explorer | 5 |
| G-code files generated | 2 |
| Total G-code lines | 9,401 |
| Phase 1 (Rear Routing) | 8,480 lines |
| Phase 2 (Perimeter) | 921 lines |
| Tool changes across all programs | 3 |
| Distinct bits required | 3 (T1–T3) |
| CNC operations | 18 (OP10–OP65 + OP50) |
| Registry status change | `STUB` → `PARTIAL` |
| Files created this session | 7 |
| Assets pre-existing | 4 files |
| Build phases | 2 (Rear Face Routing → Perimeter Profile) |
| Body outline points | 24 (coarse — needs refinement to 200+) |
| Stock dimensions | 490mm × 490mm × 44.45mm |
| Material | Korina (African Limba) |
| First Modernistic-series build | ✅ Yes |
| Simplest solidbody in fleet | ✅ Yes (flat-top, no carve, no binding, 2 phases, 3 tools) |
