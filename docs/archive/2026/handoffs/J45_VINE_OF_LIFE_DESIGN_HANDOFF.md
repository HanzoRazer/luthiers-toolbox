# Gibson J45 Vine of Life — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-07  
**Status:** Design Complete — Pipeline Has 6 Identified Gaps  
**Priority:** High  
**Context:** Custom Gibson J-45 with continuous vine-of-life inlay flowing from fretboard onto headstock. Exercises the full design→geometry→format→CAM→G-code pipeline.  

---

## Executive Summary

This build is a **full-stack integration test** for the The Production Shop. A custom Gibson J-45 round-shoulder dreadnought with a 51-piece mother-of-pearl and abalone vine-of-life inlay that flows continuously from fret 1 through the nut and onto the headstock.

**What works today:** The J45 body outline is production-ready (30-point CNC-accurate data with arc bulge). Fret position math, fretboard width interpolation, and inlay shape DXF export are all functional. The rosette and soundhole boring pipelines go from design to G-code in a single governed flow. The SVG art generator can create vine artwork from AI prompts.

**What breaks:** The pipeline has **6 gaps** between design and CNC output — mostly at format boundaries (SVG↔DXF) and geometry→CAM handoffs. The inlay calculator produces DXF shapes but there's no auto-bridge to pocket milling G-code. The V-carve G-code generator is self-described as "not production CAM." The neck G-code class exists but has no HTTP endpoint. Body perimeter profiling doesn't exist (only interior pocket clearing). And fretboard + headstock inlays are in completely separate coordinate systems with no registration.

> **Annotation:** This document is both a custom guitar design spec and a pipeline integration audit. The J45 build is the vehicle; the real deliverable is identifying and prioritizing the 6 gaps that prevent any custom acoustic guitar from going design → CNC without manual intervention at format boundaries.

---

## Part 1: Custom J45 Design Specification

### Base Instrument

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | Gibson J-45 round-shoulder dreadnought | |
| Scale length | 628.65 mm (24.75") | `services/api/app/instrument_geometry/body/j45_bulge.py` |
| Frets | 20 (14 clear of body) | Gibson standard acoustic |
| Tuning | Standard E | |
| Fretboard radius | 304.8 mm (12") | Gibson standard single radius |

### Body Specification

| Parameter | Value | Source |
|-----------|-------|--------|
| Lower bout | 412 mm (16.22") | `body_templates.json` |
| Upper bout | ~292 mm (11.5") | Outline data |
| Waist | ~267 mm (10.5") | Outline data |
| Body depth (tail) | 123.82 mm (4 7/8") | J45 DIMS.dxf extraction |
| Body depth (neck) | 98.43 mm (3 7/8") | J45 DIMS.dxf extraction |
| Overall envelope | 398.5 × 504.8 mm | `j45_bulge.py` — 30-point CNC outline |
| Soundhole | 101.6 mm diameter (R2.000") | J45 DIMS.dxf extraction |
| Bracing | Scalloped X-brace (8 top / 4 back), 6.35 × 12.70 mm cross-section | `gibson_j45.json` spec |
| Top wood | Sitka Spruce, bookmatched | |
| Back & sides | Figured Walnut — dark grain contrasts with pearl vine | |
| Binding | Aged white ivoroid, single-ply, top and back | |
| Purfling | Wood or plastic, 3.18 mm (1/8") | J45 DIMS.dxf cross-section |
| Kerf lining | Mahogany or basswood, all around | J45 DIMS.dxf cross-section |
| Rosette | 3-ring concentric — abalone/maple/abalone | |

> **Annotation:** The J45 body is one of the most complete geometry assets in the system — 30-point outline with arc bulge data preserved from the original DXF extraction. This is CNC-accurate as-is. The bulge values encode arc curvature between points, which is critical for smooth body routing. Full construction data (bracing, cross-section, fret positions) extracted from J45 DIMS.dxf on 2026-03-07.

### Neck Specification

| Parameter | Value | Notes |
|-----------|-------|-------|
| Profile | Rounded C, '50s medium | `gibson_50s` preset in `neck_headstock_config.py` |
| Nut width | 43.0 mm (1.693") | Slightly wider than standard 42.86 for fingerstyle |
| Depth at 1st | 21.6 mm (0.85") | |
| Depth at 12th | 23.4 mm (0.92") | |
| Fretboard wood | Ebony — dark ground for max vine contrast | |
| Fret wire | Jescar FW43080, gold EVO | Warm color, complements vine theme |
| Headstock angle | 17° | Gibson standard |

### Headstock Specification

| Parameter | Value |
|-----------|-------|
| Style | Gibson solid-face acoustic |
| Overlay | Ebony — continuous visual field with fretboard |
| Tuners | Gotoh 510 butterbean, aged gold |
| Logo | Centered above vine terminus, pearl script |

> **Annotation:** The system currently only has `GIBSON_OPEN` (open-book electric) headstock outline in `neck_headstock_config.py`. Gibson acoustic guitars use a solid-face headstock — a different shape entirely. This is GAP-VINE-06 below.

### Bracing Specification (Extracted from J45 DIMS.dxf)

All bracing data extracted from the original AutoCAD construction drawing on 2026-03-07.
Authoritative spec: `instrument_geometry/specs/gibson_j45.json`

#### Back Braces (BB-1 through BB-4)

All 1/4" × 1/2" (6.35 × 12.70 mm) rectangular cross-section, lateral (perpendicular to centerline).

| Brace | Position from Endpin | Position (inches) | Location |
|-------|---------------------|--------------------|----------|
| BB-1 | 22.23 mm | 7/8" | Near endpin, lower bout |
| BB-2 | 101.60 mm | 4" | Lower bout |
| BB-3 | 200.02 mm | 7 7/8" | Near waist |
| BB-4 | 298.45 mm | 11 3/4" | Upper bout |

#### Top Braces (TB-1 through TB-8)

Scalloped X-brace pattern, same 6.35 × 12.70 mm cross-section. Soundhole R2.000" (50.80 mm radius, 101.6 mm diameter). Nominal span 152.40 mm (6").

| Brace | Role |
|-------|------|
| TB-1 | X-brace left arm |
| TB-2 | X-brace right arm |
| TB-3 | Upper transverse brace |
| TB-4 | Tone bar, bass side |
| TB-5 | Tone bar, treble side |
| TB-6 | Lower face brace, bass |
| TB-7 | Lower face brace, treble |
| TB-8 | Upper face / finger brace |

#### Cross-Section Detail

| Component | Material | Dimension |
|-----------|----------|-----------|
| Purfling | Wood or plastic | 3.18 mm (1/8") |
| Kerf lining | Mahogany or basswood | All around |
| Side depth (tail) | — | 123.82 mm (4 7/8") |
| Side depth (neck) | — | 98.43 mm (3 7/8") |

> **Annotation:** Bracing geometry is now fully captured in `gibson_j45.json`, `j45_bulge.py` (data constants), `x_brace.py` (`get_j45_bracing()` preset), and the extracted DXFs (`J45_DIMS_Layered.dxf`, `J45_Bracing_Only.dxf`). The bracing pipeline stage is upgraded from "bracing_router → DXF" to "gibson_j45.json → DXF (layered)".

#### Extracted DXF Assets

| File | Layers | Entities | Format |
|------|--------|----------|--------|
| `J45_DIMS_Layered.dxf` | 10 (BODY_OUTLINE, BACK_BRACING, TOP_BRACING, etc.) | 1,222 | R2000, mm |
| `J45_Bracing_Only.dxf` | 4 (BODY_OUTLINE, BACK_BRACING, TOP_BRACING, SOUNDHOLE) | 785 | R2000, mm |

---

## Part 2: Vine of Life Inlay Design

The vine flows as a **single continuous composition** from fret 1 through the headstock. The nut is the design's equator — growth radiates outward from it in both directions.

**Material:** Mother of Pearl primary vine + Abalone accent leaves  
**Total pieces:** ~51

### Fretboard Zone (Frets 1–20)

Each vine element is positioned using `fret_midpoint_mm(fret, 628.65)` from `inlay_calc.py` and bounded by `interpolate_width()` for the tapering fretboard width.

| Fret Zone | X from nut (mm) | Width (mm) | Vine Element |
|-----------|-----------------|------------|--------------|
| 1–3 | 0–103 | 43.0–46.2 | Single stem emerges from nut, first tendril curls right |
| 3 | 86.6 | 45.5 | First leaf pair — small, tight, MoP |
| 5 | 138.8 | 47.8 | Stem splits: primary center, secondary tendril reaches left edge |
| 7 | 184.2 | 49.8 | Leaf cluster with one abalone accent leaf, vine thickens |
| 9 | 223.4 | 51.5 | Opposing tendril pair, small bud |
| 10–11 | 240–270 | 52–53 | Running tendrils, no large elements (fret spacing tightens) |
| **12** | **280.6** | **53.4** | **Centerpiece: Full flower bloom.** Double-dot positions become two open blossoms. Abalone petals with pearl center. Widest element (~38mm). |
| 14 | 314.3 | 54.5 | Body join — vine narrows |
| 15 | 329.4 | 55.0 | Two small leaves, inward-curling tendrils |
| 17 | 356.7 | 55.9 | Final leaf pair |
| 19 | 380.0 | 56.6 | Single terminal bud |
| 20 | 389.8 | 57.0 | Vine tip — thin tendril reaching toward bridge |

### Nut Transition

The vine's stem crosses the nut as a single 3mm-wide MoP strip inlaid into the nut slot area. The nut itself is bone; the vine appears to pass beneath it.

> **Annotation:** This is the critical visual bridge and the hardest handoff in the coordinate system. The fretboard uses fret-position-referenced X coordinates; the headstock uses its own origin. The nut is X=0 for both, but the Y-axis orientation flips. This is GAP-VINE-05.

### Headstock Zone

The vine reverses growth direction above the nut, branching into the headstock's ebony overlay (~89mm wide × ~178mm tall).

| Zone | Distance above nut | Element |
|------|-------------------|---------|
| Root | 0–25 mm | Stem emerges from nut, splits into 3 branches |
| Left branch | 25–90 mm | Sweeps toward bass-side tuners, 4 leaves, 2 tendrils wrapping tuner holes |
| Center branch | 25–140 mm | Rises up center, largest leaf cluster (5 leaves fanning outward) |
| Right branch | 25–110 mm | Mirrors left with slight asymmetry — 3 leaves, 1 abalone grape cluster |
| Crown | 120–160 mm | All branches converge into a tree canopy. Small pearl berries in gaps. |
| Logo zone | 145–170 mm | Vine frames but does not intersect logo position |

### Inlay Piece Summary

| Region | Pieces | Material |
|--------|--------|----------|
| Fretboard stem | 1 continuous | Mother of Pearl |
| Fretboard leaves | 14 individual | MoP |
| Fretboard accent leaves | 4 | Abalone |
| 12th fret blossoms | 2 (16 petals total) | Abalone petals + MoP centers |
| Tendrils | 8 thin curves | MoP |
| Headstock branches | 3 | MoP |
| Headstock leaves | 12 | MoP |
| Headstock grape cluster | 1 | Abalone |
| Headstock crown berries | 6 | MoP |
| **Total** | **~51 pieces** | |

### CNC Pocket Specification

| Parameter | Value |
|-----------|-------|
| Pocket depth | 1.5 mm (pearl standard) |
| Tool | 1/32" (0.8mm) tapered ball-nose, 15° taper |
| Stepover | 0.2 mm (25% of tool) |
| Feed rate | 600 mm/min |
| Plunge rate | 200 mm/min |
| Material clearance | 0.05 mm radial (epoxy fill gap) |
| Export format | DXF R12 (AC1009), closed LWPolylines |

---

## Part 3: Design-to-Toolpath Pipeline Audit

### Stage Map

```
DESIGN          GEOMETRY            FORMAT          CAM                 MACHINE
─────────────── ─────────────────── ─────────────── ─────────────────── ──────────
Body outline  → J45 bulge data    → DXF export   → ??? perimeter     → G-code
Neck profile  → neck_router       → DXF export   → NeckGCodeGen      → G-code
Fretboard     → inlay_calc        → DXF export   → ??? pocket        → G-code
Vine artwork  → SVG generator     → SVG          → VCarve CAM        → G-code
Headstock art → SVG generator     → SVG          → VCarve CAM        → G-code
Rosette       → rosette gen       → plan-toolpath→ post-gcode        → G-code  ✅
Bracing       → gibson_j45.json   → DXF (layered)→ ??? contours    → ??? pocket  → G-code
Soundhole     → (rosette)         → helical CAM  → helical_router    → G-code  ✅
```

### Stage-by-Stage Assessment

| # | Stage | Status | Working Link | Gap |
|---|-------|--------|-------------|-----|
| 1 | Body outline → DXF | **Working** | `j45_bulge.py` → `outlines.py` → body generator DXF export | — |
| 2 | Body DXF → G-code | **GAP** | Generic `cam_dxf_adaptive_router.py` exists | No perimeter profiling mode — adaptive pocket does interior clearing, not outside-contour routing with tabs |
| 3 | Neck profile → DXF | **Working** | `neck_router.py` `/export_dxf` endpoint | — |
| 4 | Neck → G-code | **GAP** | `NeckGCodeGenerator` class exists, produces full CNC program | Not wired to any HTTP endpoint — standalone class |
| 5 | Inlay shapes → DXF | **Working** | `inlay_router.py` `/export-dxf` → DXF R12 | — |
| 6 | Inlay DXF → pocket G-code | **GAP** | — | Pipeline dead-ends at DXF. No auto-bridge to pocket milling CAM |
| 7 | Vine SVG → generation | **Working** | `svg/generator.py` — AI → potrace/vtracer → SVG | — |
| 8 | SVG → V-carve G-code | **Partial** | CAM `vcarve_router.py` `/gcode` calls `svg_to_naive_gcode()` | Self-described as "not production CAM" — ignores cutter compensation, chipload, stepdown |
| 9 | SVG → DXF conversion | **MISSING** | — | Art Studio outputs SVG; adaptive pocket CAM consumes DXF. No converter bridges them |
| 10 | Rosette → G-code | **Working** | `rosette/cam_router.py` two-stage OPERATION pipeline | — |
| 11 | Soundhole → G-code | **Working** | `helical_router.py` `/gcode` — circular pocket milling | — |
| 12 | Headstock inlay coord system | **GAP** | Inlay calc assumes fretboard taper | No headstock-shaped bounding region or coordinate transform |
| 13 | Fretboard↔headstock canvas | **MISSING** | — | Separate workflows, no shared coordinate space, no registration |
| 14 | Bracing router reachable | **DEAD** | `bracing_router.py` has 4 endpoints | Not mounted in `main.py` — unreachable (VINE-08) |
| 15 | Bracing DXF → closed contours | **GAP** | `J45_Bracing_Only.dxf` has raw lines/arcs | 0 closed polylines — can’t enter CAM pipeline (VINE-09) |
| 16 | Back bracing geometry | **MISSING** | Position data in `gibson_j45.json` only | No geometry generator, no BracePattern output (VINE-10) |
| 17 | Bracing presets ↔ instrument specs | **GAP** | Hardcoded generic presets in router | No awareness of `gibson_j45.json` or `get_j45_bracing()` (VINE-11) |

### What Goes Design-to-G-code Today

| Operation | Full pipeline? |
|---|---|
| Rosette design → plan → G-code | **Yes** — full OPERATION lane |
| Soundhole boring (helical) | **Yes** |
| Drilling patterns (tuner holes, bridge pins) | **Yes** |
| Roughing a rectangular pocket | **Yes** |
| SVG artwork → preview geometry | **Yes** (preview only, no G-code) |
| Inlay fret markers → DXF shapes | **Yes** (DXF only, no G-code) |
| Bracing spec → layered DXF | **Partial** (spec + DXF extraction done; raw lines/arcs, not closed contours; router unreachable) |

> **Annotation:** Only the rosette and drilling pipelines complete the full loop from design intent to machine-executable governed G-code. Everything else breaks at a format boundary (DXF↔SVG) or at the geometry→CAM handoff. The bracing pipeline advanced significantly with the J45 DIMS.dxf extraction (spec, layered DXF, X-brace preset), but has two new blockers: the bracing router isn't mounted (VINE-08) and the extracted geometry is raw lines/arcs that need contour assembly before CAM consumption (VINE-09).

---

## Part 4: Pipeline Assets Inventory

### Production-Ready

| Asset | File | What It Does |
|-------|------|-------------|
| J45 body outline (30-pt with bulge) | `app/instrument_geometry/body/j45_bulge.py` | CNC-accurate body perimeter + bracing constants |
| J45 bracing spec | `app/instrument_geometry/specs/gibson_j45.json` | Full construction spec (bracing, cross-section, frets) |
| J45 X-brace preset | `app/instrument_geometry/bracing/x_brace.py` | `get_j45_bracing()` — 8-brace scalloped X pattern |
| J45 layered construction DXF | `Guitar Plans/J 45 Plans/J45_DIMS_Layered.dxf` | 10-layer DXF (1,222 entities, mm) |
| J45 bracing-only DXF | `Guitar Plans/J 45 Plans/J45_Bracing_Only.dxf` | 4-layer DXF (785 entities, mm) |
| J45 body in outline registry | `app/instrument_geometry/body/outlines.py` L42 | `get_body_outline("j_45")` |
| J45 catalog entry | `app/instrument_geometry/body/catalog.json` L77 | Master body catalog |
| J45 body DXF | `instrument_geometry/body/dxf/acoustic/J45_body_outline.dxf` | R12 export |
| Fret position math (24.75") | `app/instrument_geometry/neck/fret_math.py` | `compute_fret_positions_mm()` |
| Fretboard outline generator | `app/instrument_geometry/body/fretboard_geometry.py` | `compute_fretboard_outline()` — linear nut→heel taper |
| Fretboard width interpolation | `app/calculators/inlay_calc.py` | `interpolate_width()` — per-fret width |
| Inlay shape DXF export | `app/art_studio/inlay_router.py` | `/export-dxf` — R12, INLAY_OUTLINE layer |
| 8 inlay pattern types | `app/calculators/inlay_calc.py` | dot, diamond, block, parallelogram, split_block, crown, snowflake, custom |
| Gibson headstock outline | `app/generators/neck_headstock_config.py` | `GIBSON_OPEN` — open-book electric style |
| Vine/ToL prompt library | `app/cam/headstock/inlay_prompts.py` | 20+ designs with material/wood descriptions |
| SVG art generator | `app/art_studio/svg/generator.py` | AI image → potrace/vtracer → SVG |
| V-carve preview | `app/art_studio/vcarve_router.py` | SVG → geometry stats (preview only) |
| V-carve G-code (demo) | `app/cam/routers/toolpath/vcarve_router.py` | SVG → G-code (non-production quality) |
| SVG → polyline parse | `app/art_studio/svg_ingest_service.py` | `parse_svg_to_polylines()` |
| Neck G-code generator class | `app/generators/neck_headstock_generator.py` | `NeckGCodeGenerator` — full CNC program |
| DXF → adaptive pocket | `app/routers/cam_dxf_adaptive_router.py` | Generic DXF contour → pocket toolpath |
| Rosette full pipeline | `app/cam/routers/rosette/cam_router.py` | `/plan-toolpath` → `/post-gcode` OPERATION lane |
| Helical boring | `app/cam/routers/toolpath/helical_router.py` | Circular pocket milling G-code |
| Roughing G-code | `app/cam/routers/toolpath/roughing_router.py` | Rectangular pocket G-code, OPERATION lane |
| Drilling patterns | `app/cam/routers/drilling/drill_router.py` | Pin/hole G-code |
| Gibson scale constant | `packages/client/src/constants/dimensions.ts` L17 | `GIBSON_SCALE_LENGTH_MM = 628.65` |

### Scaffolded / Partial

| Asset | File | State |
|-------|------|-------|
| Headstock inlay prompts | `app/cam/headstock/inlay_prompts.py` | Data-complete, not wired to a router |
| HeadstockDesignerView | `packages/client/src/views/art-studio/HeadstockDesignerView.vue` | Frontend stub |
| FretMarkersView | `packages/client/src/views/art-studio/FretMarkersView.vue` | Frontend stub |
| SVG → naive G-code | `app/toolpath/vcarve_toolpath.py` | `svg_to_naive_gcode()` — works but ignores chipload/cutter comp |
| Gibson solid headstock | `neck_headstock_config.py` | `GIBSON_SOLID` enum value exists, outline not fully detailed for acoustic |
| Bracing router | `app/art_studio/bracing_router.py` | DXF export; J45-specific data now in `gibson_j45.json` + `get_j45_bracing()` preset; **not mounted in main.py** (VINE-08); no CAM integration |

### Not Built

| Capability | Why It Matters for This Build |
|------------|------------------------------|
| SVG → DXF converter | Vine artwork (SVG) can't enter the adaptive pocket pipeline (DXF) |
| Inlay DXF → pocket G-code bridge | 51 inlay pieces have outlines but no automated pocket clearing |
| Production V-carve (cutter comp) | Demo-quality V-carve won't produce safe toolpaths for MoP |
| Gibson acoustic headstock outline | Current outline is electric open-book, not solid-face acoustic |
| Unified inlay canvas | Fretboard and headstock are separate systems |
| Body perimeter profiling | Adaptive pocket does interior clearing, not outside-contour routing |
| Bracing contour assembly | Extracted DXF has raw lines/arcs (460 entities, 0 closed polylines) — can’t enter CAM pocket pipeline (VINE-09) |
| Back bracing geometry module | No generator for lateral back braces — data-only in `gibson_j45.json` (VINE-10) |
| Instrument-specific bracing presets | Router presets are generic; no bridge to measured specs (VINE-11) |

---

## GAP REGISTRY — Trackable Code & Architecture Deficits

> **Purpose:** Each gap has a unique ID, the files involved, what's broken, what "fixed" looks like, and what it blocks. A dev team should be able to work through these in priority order.

### Summary Dashboard

| ID | Area | Severity | Effort | Status | Blocks |
|----|------|----------|--------|--------|--------|
| VINE-01 | Inlay DXF → pocket G-code bridge | **Critical** | Medium | ✅ Resolved | VINE-03 |
| VINE-02 | SVG → DXF format converter | **Critical** | Medium | ✅ Resolved | VINE-01 |
| VINE-03 | Production V-carve (cutter comp) | **High** | High | ⚠️ Demo only | — |
| VINE-04 | Neck G-code generator HTTP endpoint | **High** | Low | ✅ Resolved | — |
| VINE-05 | Unified fretboard↔headstock canvas | **High** | High | ❌ Missing | VINE-06 |
| VINE-06 | Gibson acoustic solid headstock outline | **Medium** | Medium | ⚠️ Stub | VINE-05 |
| VINE-07 | Body perimeter profiling mode | **Medium** | Medium | ❌ Missing | — |
| VINE-08 | Bracing router not mounted in main.py | **High** | Low | ✅ Resolved | — |
| VINE-09 | Bracing DXF has raw lines, not closed contours | **Critical** | Medium | ❌ Missing | VINE-01 |
| VINE-10 | No back bracing geometry module | **Medium** | Medium | ❌ Missing | VINE-09 |
| VINE-11 | Bracing presets disconnected from instrument specs | **Medium** | Low | ⚠️ Hardcoded | VINE-08 |
| VINE-12 | Extracted DXFs are R2000 vs repo R12 convention | **Low** | Low | ⚠️ Known deviation | — |

---

### VINE-01: Inlay DXF → Pocket Milling G-code Bridge

**Severity:** Critical — 51 inlay pieces produce DXF shapes, but the pipeline dead-ends there  
**Status:** Not built. The inlay router at `app/art_studio/inlay_router.py` exports DXF files with `INLAY_OUTLINE` and `INLAY_CENTER` layers, but nothing consumes those DXFs to produce pocket-clearing G-code.

**Where the gap is:**
- **Producer:** `app/art_studio/inlay_router.py` → `POST /export-dxf` returns DXF R12 file
- **Would-be consumer:** `app/routers/cam_dxf_adaptive_router.py` accepts DXF → adaptive pocket toolpath
- **Missing link:** No orchestrator that takes inlay DXF output, parses the `INLAY_OUTLINE` layer contours, and feeds each pocket to the adaptive milling engine with inlay-specific parameters (1.5mm depth, 0.8mm tool, 0.2mm stepover)

**What "fixed" looks like:**
- A new endpoint (or extension to `inlay_router.py`) that accepts `InlayCalcResult` + tool parameters and returns pocket-clearing G-code for every inlay shape
- Uses the existing adaptive pocket engine internally
- Respects the 0.05mm radial clearance for epoxy fill gap
- Multi-pocket batching — all 51 pockets in one coordinated G-code program with tool-change blocks between fretboard and headstock operations
- Output is governed OPERATION-lane G-code with audit trail

**Dependencies:** VINE-02 (if vine artwork is SVG rather than parametric DXF, needs SVG→DXF first)  
**Blocked by:** VINE-02 for custom shapes; can work independently for standard inlay patterns (dot, block, diamond)

**Test expectations:**
- Given a standard `InlayCalcResult` with 10 dot inlays, endpoint returns valid G-code
- G-code contains correct pocket depth (Z-1.5), correct feed rates, tool retract between pockets
- G-code header declares G21 (mm), G90 (absolute), safe Z height

---

### VINE-02: SVG → DXF Format Converter

**Severity:** Critical — the Art Studio produces SVG; the production CAM pipeline consumes DXF  
**Status:** Not built. No module anywhere in the codebase converts SVG polylines/paths to DXF LWPolylines.

**Where the gap is:**
- **SVG side:** `app/art_studio/svg_ingest_service.py` has `parse_svg_to_polylines()` which converts SVG → internal polyline representation
- **DXF side:** Multiple DXF exporters exist (`instrument_geometry/neck_taper/dxf_exporter.py`, `inlay_calc.py`'s `generate_inlay_dxf_string()`, `pipelines/rosette/rosette_to_dxf.py`)
- **Missing:** A function that takes SVG polylines → DXF LWPolylines using `ezdxf`

**What "fixed" looks like:**
- A utility function: `svg_polylines_to_dxf(polylines: List[List[Point2D]], layer: str = "ARTWORK") -> bytes`
- Uses `ezdxf` to create R12 (AC1009) DXF with closed LWPolylines
- Follows the same pattern as `generate_inlay_dxf_string()` in `inlay_calc.py`
- Optionally exposed as an endpoint: `POST /art-studio/convert/svg-to-dxf`

**Dependencies:** None — this is a pure format bridge  
**Blocked by:** Nothing

**Test expectations:**
- Round-trip: parse SVG → convert to DXF → re-parse DXF → polylines match original (within tolerance)
- Output passes DXF R12 validation
- Closed polylines remain closed (first vertex == last vertex)

---

### VINE-03: Production-Quality V-Carve G-code

**Severity:** High — the existing V-carve is explicitly labeled "not production CAM"  
**Status:** `app/toolpath/vcarve_toolpath.py` function `svg_to_naive_gcode()` works but its docstring says: *"not production CAM — ignores chipload, stepdown, cutter diameter."*

**Where the problem is:**
- **File:** `app/toolpath/vcarve_toolpath.py`
- **Function:** `svg_to_naive_gcode(svg_text, params)`
- **Pipeline:** `parse_svg_to_polylines()` → `normalize_polylines()` → `polylines_to_mlpaths()` → `mlpaths_to_naive_gcode()`
- **What it ignores:** Cutter radius compensation, V-bit angle geometry (depth = width / 2·tan(angle/2)), multi-pass stepdown for deep pockets, chipload-based feed rate, lead-in/lead-out moves

**What "fixed" looks like:**
- A production `svg_to_vcarve_gcode()` function that:
  - Computes cut depth from V-bit angle and desired line width
  - Applies cutter compensation (G41/G42) or geometric offset
  - Supports multi-pass stepdown for depths > single-pass safe limit
  - Calculates feed rate from chipload × flutes × RPM
  - Adds lead-in arcs to avoid plunge marks
  - Produces governed OPERATION-lane output with run_id and SHA256 hash
- Exposed via the existing CAM V-carve router at `app/cam/routers/toolpath/vcarve_router.py`

**Dependencies:** None  
**Blocked by:** Nothing — the naive version provides the architectural skeleton

**Test expectations:**
- Given a simple SVG square + V-bit angle 60° + depth 2mm, output G-code has correct Z depths
- Feed rates are non-zero and plausible for wood (100–1200 mm/min range)
- Multi-pass: if max stepdown is 0.5mm and depth is 2mm, expect 4 passes at increasing Z
- Output includes M3/M5 spindle control

---

### VINE-04: Neck G-code Generator — No HTTP Endpoint

**Severity:** High — the generator class works but is unreachable from the API  
**Status:** `app/generators/neck_headstock_generator.py` contains `NeckGCodeGenerator` which produces a complete CNC program with tool changes, spindle RPM, safe start blocks, and coordinate system setup. But no router imports or calls it.

**Where the problem is:**
- **Generator:** `app/generators/neck_headstock_generator.py` — `NeckGCodeGenerator` class
- **Nearest router:** `app/routers/neck_router.py` — has geometry endpoints (`/generate`, `/export_dxf`, `/generate/stratocaster`) but no G-code endpoint
- **Missing:** An endpoint like `POST /neck/gcode` that instantiates the generator and returns G-code

**What "fixed" looks like:**
- New endpoint in `neck_router.py`: `POST /gcode` (or `POST /gcode/j45` for model-specific)
- Accepts neck parameters + machine profile ID + tool configuration
- Instantiates `NeckGCodeGenerator(dims, style, profile, tools)`
- Returns G-code Response (text/plain) with proper `X-Request-Id` header
- Classified as OPERATION lane (machine-executable output)

**Dependencies:** None  
**Blocked by:** Nothing — the generator class is the hard part, and it's done

**Test expectations:**
- Endpoint returns G-code with `G20` (inches) header
- G-code includes tool change blocks (`T1 M6`, etc.)
- G-code includes spindle start/stop (`M3 S...` / `M5`)
- Response includes `X-Request-Id` header

---

### VINE-05: Unified Fretboard ↔ Headstock Coordinate Canvas

**Severity:** High — the vine design crosses from fretboard to headstock as a single composition  
**Status:** The fretboard inlay system (`inlay_calc.py`) uses fret-position-referenced X coordinates with Y bounded by fretboard taper width. The headstock has its own coordinate system from `generate_headstock_outline()`. There is no shared origin, no coordinate transform, and no way to design a continuous element that spans both.

**Where the gap is:**
- **Fretboard coords:** Origin at nut, X increases toward bridge, Y bounded by `interpolate_width()`
- **Headstock coords:** Origin at nut (by convention), but Y extends in the opposite direction (toward tuners), bounded by `generate_headstock_outline()` which returns raw points relative to its own origin
- **No transform:** Nothing computes the coordinate mapping between these two spaces, especially accounting for the 17° headstock angle on a Gibson

**What "fixed" looks like:**
- A `UnifiedInlayCanvas` class or module that:
  - Accepts fretboard parameters (scale, nut width, heel width, fret count)
  - Accepts headstock parameters (style, dimensions, angle)
  - Provides a single coordinate system with nut at origin (X=0)
  - Fretboard extends in +X direction
  - Headstock extends in -X direction, rotated by headstock angle
  - Exposes `get_bounding_contour_at_x(x_mm) -> (y_min, y_max)` for any X position
  - Handles the nut transition zone
- Used by both fretboard inlay calc and headstock inlay calc
- DXF export produces a single drawing with both regions

**Dependencies:** VINE-06 (needs Gibson acoustic headstock outline)  
**Blocked by:** VINE-06

**Test expectations:**
- `canvas.get_bounding_contour_at_x(0)` returns nut width
- `canvas.get_bounding_contour_at_x(100)` returns wider fretboard width
- `canvas.get_bounding_contour_at_x(-50)` returns headstock width at 50mm above nut
- Continuous vine polyline crossing X=0 is correctly represented in both regions

---

### VINE-06: Gibson Acoustic Solid-Face Headstock Outline

**Severity:** Medium — blocks VINE-05 for Gibson acoustic builds  
**Status:** `neck_headstock_config.py` has `HeadstockStyle.GIBSON_SOLID` in the enum, and the `GIBSON_OPEN` branch has a full 21-point open-book electric outline. But Gibson acoustic guitars use a **solid-face** (no diamond cutout) headstock with different proportions — narrower, more tapered, slightly longer.

**Where the problem is:**
- **File:** `app/generators/neck_headstock_config.py`
- **Function:** `generate_headstock_outline()` — the `GIBSON_SOLID` branch
- **Lines:** Check whether `GIBSON_SOLID` has a proper outline or falls through to paddle default

**What "fixed" looks like:**
- `GIBSON_SOLID` branch returns a proper ~18-point outline for Gibson acoustic headstock:
  - ~89mm wide at widest × ~178mm tall
  - Gentle crown curve (less dramatic than open-book)
  - Straight-ish sides tapering from crown to nut
  - Flat bottom edge at nut width
- Reference: Gibson J-45 headstock drawings (available in `GUITAR_PLANS_REFERENCE.md` — 4 J45 DXF files listed)
- Also add `gibson_j45_acoustic` to `NECK_PRESETS` with acoustic-correct params (20 frets, 43mm nut, 17° angle, solid headstock)

**Dependencies:** None  
**Blocked by:** Nothing — can use J45 DXF reference drawings

**Test expectations:**
- `generate_headstock_outline(HeadstockStyle.GIBSON_SOLID, j45_dims)` returns >10 points (not paddle)
- Max width ~89mm, max length ~178mm
- Outline is closed polyline
- Narrower than `GIBSON_OPEN` (electric open-book is ~95mm wide)

---

### VINE-07: Body Perimeter Profiling Mode

**Severity:** Medium — body outline exists as DXF but can't be CNC-routed  
**Status:** The adaptive pocket system at `cam_dxf_adaptive_router.py` does **interior pocket clearing**. Body routing needs **outside-contour profiling** — following the perimeter of the body outline with material tabs to hold the workpiece during cutting. These are fundamentally different toolpath strategies.

**Where the gap is:**
- **Existing:** `app/routers/cam_dxf_adaptive_router.py` — DXF → adaptive pocket interior clearing
- **Missing:** A profiling/contouring mode that:
  - Follows the outside of a closed DXF contour
  - Applies cutter radius offset (tool runs outside the line)
  - Generates holding tabs at configurable intervals
  - Supports multi-pass depth stepping for thick stock (J45 body is 121mm deep)

**What "fixed" looks like:**
- New endpoint or mode flag in the DXF adaptive router: `profile_mode: "pocket" | "contour"`
- Contour mode generates outside-offset toolpath with tabs
- Tab parameters: width (default 6mm), height (default 3mm), count (default 4 for body-sized workpieces), evenly distributed
- Multi-pass: configurable stepdown (e.g., 3mm per pass × 40 passes for 121mm body depth)

**Dependencies:** None  
**Blocked by:** Nothing

**Test expectations:**
- Given a simple rectangle DXF + contour mode + 6mm tool, output G-code offset is 3mm outside the rectangle
- Tabs appear in the toolpath (Z doesn't go full depth at tab positions)
- Multi-pass: 121mm depth with 3mm stepdown produces ~40 depth passes

---

### VINE-08: Bracing Router Not Mounted in main.py

**Severity:** High — 4 bracing endpoints exist but are unreachable  
**Status:** Dead code. `app/art_studio/bracing_router.py` defines `POST /preview`, `POST /batch`, `GET /presets`, and `POST /export-dxf` under `/art-studio/bracing/`. The router is exported in `app/art_studio/__init__.py` but **no `include_router()` call exists in `main.py`**.

**Where the gap is:**
- **Router:** `app/art_studio/bracing_router.py` — complete with request/response models, presets, DXF export
- **Missing:** One-line registration in `app/main.py`

**What "fixed" looks like:**
- Add `app.include_router(bracing_router, prefix="/api/art-studio/bracing", tags=["Art Studio - Bracing"])` to `main.py`
- Verify the router's internal `prefix=` doesn't double-stack with the mount path

**Dependencies:** None  
**Blocked by:** Nothing — trivial fix

**Test expectations:**
- `GET /api/art-studio/bracing/presets` returns 200 with preset list
- `POST /api/art-studio/bracing/preview` accepts `BracingPreviewRequest` and returns section + mass

---

### VINE-09: Bracing DXF Contains Raw Lines/Arcs, Not Closed Contours

**Severity:** Critical — bracing geometry cannot enter the CAM pipeline without contour assembly  
**Status:** The extracted `J45_Bracing_Only.dxf` contains BACK_BRACING (116 lines + 9 arcs, **0 closed polylines**) and TOP_BRACING (344 lines + 69 arcs, **0 closed polylines**). The original AutoCAD drawing stored brace cross-sections and plan views as collections of individual line/arc entities, not as closed outlines. The adaptive pocket CAM pipeline (`cam_dxf_adaptive_router.py`) requires closed LWPolylines to define pocket boundaries.

**Where the gap is:**
- **Current state:** Bracing geometry is discrete LINE and ARC entities representing brace outlines, cross-hatching, dimension leaders, and profile shapes — all mixed together on the same layer
- **Required for CAM:** Closed LWPolyline outlines defining each individual brace's plan-view footprint (the shape you'd rout a pocket for)
- **Missing:** A contour assembly step that groups co-located lines/arcs into connected chains and converts them to closed polylines

**What "fixed" looks like:**
- A utility function (likely in `scripts/` or `instrument_geometry/bracing/`) that:
  - Reads lines/arcs from a bracing layer
  - Groups by spatial proximity (each brace is a cluster of entities)
  - Chains connected endpoints within tolerance (~0.1mm)
  - Outputs one closed LWPolyline per brace footprint
- Output: `J45_Bracing_CAM.dxf` with one closed polyline per brace on named layers (`BB_1`, `BB_2`, `TB_1`, etc.)
- Alternative approach: generate brace footprint polylines parametrically from `get_j45_bracing()` dimensions rather than assembling from raw DXF

**Dependencies:** Blocks VINE-01 (inlay/pocket G-code bridge applies to bracing pockets too)  
**Blocked by:** Nothing

**Test expectations:**
- Each brace footprint is a single closed LWPolyline
- Back brace footprints: 4 closed polylines, widths ~6.35mm, lengths matching body width at brace position
- Top brace footprints: 8 closed polylines with X-brace crossing geometry

---

### VINE-10: No Back Bracing Geometry Module

**Severity:** Medium — back bracing is data-only, no generated geometry  
**Status:** `x_brace.py` generates top X-bracing patterns (with `get_j45_bracing()` producing 8 top braces). `fan_brace.py` generates classical fan patterns. There is **no back bracing generator**. The 4 J45 back braces (BB-1 through BB-4) exist only as position data in `gibson_j45.json` and `j45_bulge.py` (`J45_BACK_BRACES`). There's no `BracePattern` output, no DXF export, and no way to compute back brace endpoints from body outline geometry.

**Where the gap is:**
- **Data exists:** `gibson_j45.json` has positions from endpin (22.23, 101.60, 200.02, 298.45 mm) and cross-section (6.35 × 12.70 mm)
- **Missing:** A `get_back_brace_pattern(body_outline, positions)` function that generates lateral brace endpoints by intersecting position lines with the body outline contour
- **Missing:** Integration with `bracing_router.py` to make back braces part of the batch/preset flow

**What "fixed" looks like:**
- New file: `app/instrument_geometry/bracing/back_brace.py`
- Function: `get_back_brace_pattern(body_outline, brace_positions, cross_section)` → `BracePattern`
- Each brace runs perpendicular to centerline, spanning edge-to-edge of the body at its Y position
- Brace endpoints computed by intersecting horizontal lines with the body outline polyline

**Dependencies:** VINE-09 (contour output needed for CAM)  
**Blocked by:** Nothing for the geometry module itself

**Test expectations:**
- Given J45 body outline + 4 positions, returns 4 braces
- Each brace span matches body width at that Y position
- BB-1 (near endpin) is shorter than BB-3 (near waist, widest point)

---

### VINE-11: Bracing Presets Disconnected from Instrument Specs

**Severity:** Medium — UI shows generic presets, not instrument-specific data  
**Status:** The bracing router's `GET /presets` endpoint returns **3 hardcoded generic presets** (Standard X-Brace, Classical Ladder, Scalloped X) with approximate dimensions (12mm × 8mm × 280mm). It has no awareness of `gibson_j45.json`, `get_j45_bracing()`, or any instrument-specific bracing data. A luthier selecting "J45 bracing" in the UI gets generic numbers, not the measured 6.35 × 12.70 mm cross-sections from the construction drawing.

**Where the gap is:**
- **Preset source:** Hardcoded in `bracing_router.py` `get_bracing_presets()` function
- **Instrument data:** `gibson_j45.json` (authoritative spec), `get_j45_bracing()` (computed X-brace), `J45_BACK_BRACES` (position data)
- **No bridge:** Presets don't reference instrument specs; specs don't feed into the preset system

**What "fixed" looks like:**
- `GET /presets` reads from `instrument_geometry/specs/*.json` to build instrument-specific presets
- Or: a new endpoint `GET /presets/{instrument_id}` returning braces from the instrument spec
- J45 preset includes all 12 braces (8 top + 4 back) with measured cross-sections

**Dependencies:** VINE-08 (router must be mounted first)  
**Blocked by:** VINE-08

**Test expectations:**
- `GET /presets` includes a "Gibson J-45" preset
- J45 preset brace dimensions are 6.35 × 12.70 mm (not 12 × 8 mm generic)
- Preset brace count matches spec (8 top + 4 back = 12)

---

### VINE-12: Extracted DXFs Are R2000, Not R12 (Convention Tension)

**Severity:** Low — known deviation from repo DXF R12 convention  
**Status:** The repo convention (per `copilot-instructions.md`) is "DXF R12 (AC1009) with closed LWPolylines only." The J45 construction DXFs (`J45_DIMS_Layered.dxf`, `J45_Bracing_Only.dxf`) are **R2000 (AC1015)** because R12 does not support LWPOLYLINE entities. This is a necessary and correct choice — the source AutoCAD drawing uses LWPOLYLINEs for body outlines (30-point with bulge arcs), soundhole shapes, and kerf lining details. Downgrading to R12 would lose this geometry.

**Where the tension is:**
- **Convention:** R12 everywhere, enforced by DXF export utilities (`dxf_compat.py`)
- **Reality:** LWPolyline (which R12 doesn't support) is the correct entity for curved brace outlines and body contours with arc bulge
- **Risk:** Low — downstream consumers that call `ezdxf.readfile()` handle R2000 transparently. The convention exists to ensure maximum compatibility with simple CNC controllers, which is irrelevant for intermediate design files.

**What "fixed" looks like:**
- Document the convention as "R12 for CAM output / CNC controller consumption; R2000 acceptable for intermediate design and construction DXFs"
- Or: update the DXF export utilities to support R2000 output as an option alongside R12
- No code change urgently needed

**Dependencies:** None  
**Blocked by:** Nothing

---

## Prioritized Remediation Sequence

```
Phase 0 — Quick Wins (unblocks bracing pipeline)
  VINE-08: Mount bracing router in main.py   [Low effort, High]    ← 1 line fix
  VINE-12: Document R2000 convention for design DXFs [Low effort, Low]

Phase 1 — Format Bridges (unblocks everything)
  VINE-02: SVG → DXF converter              [Medium effort, Critical]
  VINE-04: Neck G-code HTTP endpoint         [Low effort, High]

Phase 2 — Pipeline Completion (enables full J45 build)
  VINE-01: Inlay DXF → pocket G-code bridge  [Medium effort, Critical]  (needs VINE-02)
  VINE-06: Gibson acoustic headstock outline  [Medium effort, Medium]
  VINE-09: Bracing contour assembly           [Medium effort, Critical]  (blocks bracing CAM)
  VINE-11: Instrument-specific bracing presets [Low effort, Medium]  (needs VINE-08)

Phase 3 — Production Quality
  VINE-03: Production V-carve G-code          [High effort, High]
  VINE-05: Unified fretboard↔headstock canvas [High effort, High]  (needs VINE-06)
  VINE-07: Body perimeter profiling           [Medium effort, Medium]
  VINE-10: Back bracing geometry module        [Medium effort, Medium]  (needs VINE-09)
```

> **Annotation:** Phase 0 is new — two trivial tasks discovered during J45 DIMS.dxf extraction (2026-03-07). VINE-08 (mounting the bracing router) is literally one line in main.py and unblocks the entire bracing UI. VINE-09 (contour assembly) is the most impactful new gap — without converting raw lines/arcs into closed polylines, the extracted bracing geometry can't enter any CAM pipeline. Phase 2 now includes bracing-specific work alongside the original inlay pipeline completion.

---

## Cross-References

| Related Handoff | Relevant Gaps |
|----------------|---------------|
| `CUSTOM_INLAY_FRETBOARD_HEADSTOCK_HANDOFF.md` | INLAY-03 (unified canvas) = VINE-05 |
| `STRATOCASTER_NECK_DESIGN_HANDOFF.md` | NECK-04 (API endpoint pattern) informs VINE-04 |
| `24_FRET_STRATOCASTER_DESIGN_HANDOFF.md` | GAP-01 (headstock outline) pattern informs VINE-06 |
| `ROUTER_CONSOLIDATION_ROADMAP.md` | Router count impact — VINE-04 adds 1 endpoint to existing router (net zero new routers); VINE-08 mounts existing router (net +1 registered router) |
| `REMEDIATION_PLAN.md` | Phase 2 (API Surface Reduction) — VINE-01 should be an extension, not a new router; VINE-08 adds a router to main.py (confirm desired during remediation) |
| `BLUEPRINT_VECTORIZER_INTEGRATION_HANDOFF.md` | VEC-GAP-03 (contour assembly from raw geometry) is the same class of problem as VINE-09 |
| `OM_PURFLING_CNC_HANDOFF.md` | DXF format convention (R12 vs R2000) tension documented in VINE-12 applies to OM assets too |
