# Custom Fretboard & Headstock Inlay System — Developer Handoff

**Document Type:** Annotated Executive Summary  
**Created:** 2026-03-07  
**Status:** Assessment Complete — Partially Production, Partially Planned  
**Priority:** Medium  
**Context:** User wants continuous inlay design flowing from fretboard onto headstock for a Stratocaster  

---

## Executive Summary

The Luthier's Toolbox has a **production-ready fretboard inlay designer** with 8 pattern types, 6 presets, SVG preview, and DXF R12 export. It also has two separate CAM systems (V-Carve and Relief) that can convert custom SVG artwork into CNC pocket-routing programs.

**What works today:** A user can design standard fretboard inlays (dots, blocks, diamonds, crowns) and export CNC-ready DXF files. Separately, they can feed custom SVG artwork through the V-Carve or Relief pipeline to produce headstock inlay pocket G-code.

**What's missing:** These are **two disconnected workflows**. There is no unified pipeline for designing a continuous inlay that flows from the 1st fret through the 22nd fret and onto the headstock as a single coordinated design. The headstock inlay router endpoint is also not wired — the prompt library and frontend stub exist but lack an API connection.

> **Annotation:** The inlay system is the strongest of the decorative feature set. The gap is integration, not capability. All the underlying engines (parametric geometry, SVG parsing, pocket routing, DXF export) are production-grade. The work is stitching them into a unified design surface.

---

## Inventory of Existing Assets

### Tier 1: Production-Ready ✅

#### Fretboard Inlay Designer

| Component | Location | Status |
|-----------|----------|--------|
| Inlay calculation engine | `app/calculators/inlay_calc.py` | ✅ Production |
| Inlay API router | `app/art_studio/inlay_router.py` | ✅ Production |
| Inlay Designer UI | `packages/client/src/views/art-studio/InlayDesignerView.vue` | ✅ Production |
| Client SDK | `packages/client/src/api/art-studio.ts` | ✅ Production |

> **Annotation:** This is a complete vertical slice — UI, API, calculation engine, and export all working. Accessed at `/art-studio/inlay` in the frontend.

**8 Supported Pattern Types:**

| Pattern | Shape | Typical Use |
|---------|-------|-------------|
| `dot` | Circle | Fender standard, classical |
| `diamond` | Rotated square | Jazz guitars |
| `block` | Rectangle | Gibson Les Paul Custom |
| `parallelogram` | Slanted rectangle | Gibson SG, ES-335 |
| `split_block` | Split rectangle | PRS style |
| `crown` | Crown/fan shape | Decorative markers |
| `snowflake` | Radial pattern | Custom decorative |
| `custom` | User-defined SVG | Any shape |

**6 Built-in Presets:**

| Preset | Pattern | Target Instrument |
|--------|---------|-------------------|
| `dot_standard` | Dot | Modern electric (Fender) |
| `dot_vintage` | Dot | Vintage Fender |
| `dot_classical` | Dot | Classical guitar |
| `diamond_jazz` | Diamond | Archtop/jazz |
| `block_gibson` | Block | Gibson Custom |
| `trapezoid_es` | Parallelogram | Gibson ES series |

**API Endpoints (all under `/api/art-studio/inlay/`):**

| Endpoint | Method | Purpose | Output |
|----------|--------|---------|--------|
| `/preview` | POST | Calculate positions + render SVG preview | JSON + SVG |
| `/export-dxf` | POST | Generate CNC-ready DXF file | DXF R12 download |
| `/presets` | GET | List all available presets | JSON array |
| `/presets/{name}` | GET | Load specific preset parameters | JSON |
| `/pattern-types` | GET | List supported pattern types | JSON array |
| `/dxf-versions` | GET | List supported DXF export versions | JSON array |

**Parametric Controls:**

| Parameter | Range | Default | Purpose |
|-----------|-------|---------|---------|
| Scale length | Any (mm) | 648mm (Strat 25.5") | Fret position calculation |
| Fret selection | Any combination | 3,5,7,9,12,15,17,19,21 | Which frets get markers |
| Marker diameter | 2–20mm | 6mm (dots), varies by type | Inlay size |
| Block width/height | Custom | Varies by preset | Block/parallelogram dimensions |
| Rotation | 0–360° | 0° | Marker orientation |
| Pocket depth | 0.5–5mm | 1.5mm | CNC routing depth |
| Side dots | On/off | On | Edge-of-fretboard position dots |
| Double marker at 12th | On/off | On | Octave double-dot convention |

> **Annotation:** The key Stratocaster parameter is already the default — 648mm scale length. The `dot_standard` preset with frets 3,5,7,9,12,15,17,19,21 matches the standard Fender inlay pattern. A user can generate a Strat-correct inlay DXF in about 3 clicks.

---

#### V-Carve Routing System

| Component | Location | Status |
|-----------|----------|--------|
| V-Carve router | `app/cam/routers/toolpath/vcarve_router.py` | ✅ Production |
| SVG ingest service | `app/art_studio/svg_ingest_service.py` | ✅ Production |

**Endpoint:** `POST /api/cam/toolpath/vcarve/gcode`

> **Annotation:** This is an OPERATION lane endpoint (governed execution with feasibility gate and audit trail). It accepts SVG input, generates 3D V-carve toolpaths with depth variation, and produces G-code. Ideal for custom inlay pocket routing where the inlay shell/MOP has varying thickness or where you want a chamfered pocket edge.

**Capabilities:**
- SVG path parsing → toolpath generation
- Raster and contour infill modes
- Variable depth based on line width
- Feasibility checking (tool fits in pocket geometry)
- Run artifact persistence for traceability

---

#### Relief Carving Export

| Component | Location | Status |
|-----------|----------|--------|
| Relief export router | `app/cam/routers/toolpath/relief_export_router.py` | ✅ Production |

**Endpoint:** `POST /api/cam/toolpath/relief/export-dxf`

> **Annotation:** Also an OPERATION lane endpoint. Takes SVG input, converts to DXF with polyline geometry stats. Better suited for flat-bottom inlay pockets (constant depth) compared to V-Carve's variable depth. For most shell/MOP inlays on a fretboard, flat-bottom pockets are standard.

---

#### Rosette Design System

| Component | Location | Status |
|-----------|----------|--------|
| Rosette jobs routes | `app/art_studio/api/rosette_jobs_routes.py` | ✅ Production |
| Rosette Pipeline UI | `packages/client/src/views/RosettePipelineView.vue` | ✅ Production |

> **Annotation:** Relevant for acoustic guitar soundhole inlays but not directly applicable to fretboard/headstock inlay. The ring-based design logic could potentially be reused for circular inlay elements (dots, rosette-style markers). Listed for completeness.

---

### Tier 2: Scaffolded / Partial 🚧

#### Headstock Inlay System

| Component | Location | Status |
|-----------|----------|--------|
| Inlay prompt library | `app/cam/headstock/inlay_prompts.py` | ✅ Data complete |
| Headstock Designer UI (stub) | `packages/client/src/views/art-studio/HeadstockDesignerView.vue` | ⚠️ Stub |
| Headstock inlay API endpoint | — | ❌ Not wired |

> **Annotation:** The prompt library is rich — 11 headstock styles, 20+ inlay designs, 20+ wood color descriptions. The `generate_headstock_prompt()` function produces high-quality text prompts for AI image generation. But there's no API router that accepts headstock + inlay parameters and returns a DXF. The UI exists as a frontend stub but has no backend to call.

**Prompt Library Contents:**

**Headstock Styles (11):**
Les Paul, Stratocaster, Telecaster, Classical, Acoustic, PRS, Explorer, Flying V, SG, Jazz, Custom

**Inlay Designs (20+):**

| Category | Designs |
|----------|---------|
| Birds | Hummingbird, Dove, Eagle, Phoenix |
| Florals | Rose, Vine, Tree of Life, Lotus |
| Geometric | Diamond, Crown, Celtic Knot |
| Other | Dragon, Koi, Skull |

**Wood Colors (20+):**
Ebony, Rosewood, Maple, Mahogany, Walnut, etc. — used to generate contextually accurate AI prompts

> **Annotation:** The AI → inlay workflow is: (1) generate prompt from parameters, (2) send to DALL-E/Midjourney for concept art, (3) vectorize the result (Potrace/Inkscape), (4) feed SVG to V-Carve or Relief pipeline. Steps 1 and 4 are automated. Steps 2–3 require manual intervention. Automating the vectorization step would close this loop.

---

#### Other Art Studio Stubs

| Component | Location | Status | Relevance to Inlay |
|-----------|----------|--------|-------------------|
| Binding Designer | `views/art-studio/BindingDesignerView.vue` | ⚠️ Stub | Low — edge binding, not inlay |
| Purfling Designer | `views/art-studio/PurflingDesignerView.vue` | ⚠️ Stub | Medium — purfling lines adjacent to inlay |
| Soundhole Designer | `views/art-studio/SoundholeDesignerView.vue` | ⚠️ Stub | Low — acoustic only |
| Fret Markers View | `views/art-studio/FretMarkersView.vue` | ⚠️ Stub | High — overlaps with inlay designer |

> **Annotation:** `FretMarkersView.vue` is a separate stub from `InlayDesignerView.vue`. There may be feature overlap — the inlay designer already handles fret markers. Check whether this stub should be deprecated in favor of the production inlay designer or if it serves a distinct purpose (e.g., side dots only).

---

### Tier 3: Not Built ❌

| Capability | Current Workaround | Effort to Build |
|-----------|-------------------|-----------------|
| **Unified fretboard-to-headstock inlay canvas** | Combine two DXF files manually in CAM software | High — needs shared coordinate space |
| **Headstock inlay API endpoint** | Use V-Carve/Relief endpoints directly with SVG | Low — wire existing prompt library to a router |
| **Continuous flowing artwork generator** (vine from nut to headstock) | Draw manually in Inkscape, export SVG | High — algorithmic vine/pattern generation |
| **Automated AI image → SVG vectorization** | Manual Potrace/Inkscape trace | Medium — integrate Potrace or OpenCV vectorizer |
| **Inlay material library** (shell thickness, cut parameters per material) | Manual feed/speed entry | Low — data file + UI dropdown |
| **Inlay fit simulation** (preview inlay in pocket before cutting) | Visual DXF overlay | Medium — canvas-based overlay preview |

---

## Architecture Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND (Vue 3)                                │
│                                                                             │
│  ┌───────────────────────┐  ┌─────────────────────┐  ┌──────────────────┐  │
│  │ InlayDesignerView.vue │  │ HeadstockDesigner   │  │ FretMarkersView  │  │
│  │      ✅ PRODUCTION     │  │    ⚠️ STUB           │  │    ⚠️ STUB        │  │
│  │                       │  │                     │  │                  │  │
│  │ • Pattern selector    │  │ • Style picker      │  │ • (TBD)         │  │
│  │ • Fret picker         │  │ • Inlay design pick │  │                  │  │
│  │ • Size/depth controls │  │ • Wood selector     │  │                  │  │
│  │ • SVG live preview    │  │ • AI prompt display │  │                  │  │
│  │ • Export DXF button   │  │ • (no backend call) │  │                  │  │
│  └──────────┬────────────┘  └──────────┬──────────┘  └──────────────────┘  │
│             │ SDK call                 │ ❌ no endpoint                      │
│             ▼                          ▼                                    │
└─────────────┼──────────────────────────┼────────────────────────────────────┘
              │                          │
   POST /api/art-studio/inlay/*         (not wired)
              │                          │
┌─────────────┼──────────────────────────┼────────────────────────────────────┐
│             ▼           BACKEND (FastAPI)                                    │
│  ┌──────────────────────┐  ┌─────────────────────────────────┐              │
│  │ inlay_router.py      │  │ inlay_prompts.py                │              │
│  │ ✅ PRODUCTION         │  │ ✅ DATA COMPLETE (no router)     │              │
│  │                      │  │                                 │              │
│  │ /preview             │  │ • 11 headstock styles           │              │
│  │ /export-dxf          │  │ • 20+ inlay designs             │              │
│  │ /presets             │  │ • 20+ wood color descriptions   │              │
│  │ /pattern-types       │  │ • generate_headstock_prompt()   │              │
│  └──────────┬───────────┘  └─────────────────────────────────┘              │
│             │                                                               │
│  ┌──────────▼───────────┐                                                   │
│  │ inlay_calc.py        │  Calculation Engine                               │
│  │ ✅ PRODUCTION         │                                                   │
│  │                      │  • 12-TET fret position math                      │
│  │ • 8 pattern types    │  • Parametric shape generation                    │
│  │ • 6 presets          │  • SVG path construction                          │
│  │ • DXF R12 export     │  • DXF entity generation                         │
│  └──────────────────────┘                                                   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │              CAM SYSTEMS (for custom artwork → CNC)              │       │
│  │                                                                  │       │
│  │  ┌─────────────────────┐     ┌──────────────────────────────┐   │       │
│  │  │ V-Carve Router      │     │ Relief Export Router          │   │       │
│  │  │ ✅ PRODUCTION        │     │ ✅ PRODUCTION                  │   │       │
│  │  │                     │     │                              │   │       │
│  │  │ SVG → G-code        │     │ SVG → DXF                    │   │       │
│  │  │ Variable depth      │     │ Constant depth pockets       │   │       │
│  │  │ Raster + contour    │     │ Polyline geometry            │   │       │
│  │  │ Feasibility gate    │     │ Safety policy                │   │       │
│  │  │                     │     │                              │   │       │
│  │  │ OPERATION lane      │     │ OPERATION lane               │   │       │
│  │  └─────────────────────┘     └──────────────────────────────┘   │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                             │
│                          ▼ OUTPUT ▼                                         │
│  ┌────────────────────────────────────────────────────────┐                 │
│  │  .dxf  — Inlay pocket outlines (R12 AC1009, CNC-ready) │                 │
│  │  .nc   — G-code (V-Carve pocket routing program)       │                 │
│  │  .svg  — Preview artwork (browser display)              │                 │
│  │  .json — Inlay positions + dimensions (data exchange)   │                 │
│  └────────────────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Workflow: Stratocaster Custom Inlay (Today)

### Path A — Standard Fretboard Inlays (Fully Automated)

```
Step 1: Open Inlay Designer (/art-studio/inlay)
        └─ Select preset: "dot_standard" (or start custom)
        └─ Scale length: 648mm (default = Strat)

Step 2: Customize
        └─ Pattern: dot / block / diamond / crown / custom
        └─ Frets: [3, 5, 7, 9, 12, 15, 17, 19, 21]
        └─ Size: 6mm dots (or 12×4mm blocks, etc.)
        └─ Pocket depth: 1.5mm (standard for shell/MOP)
        └─ Double dot at 12th fret: yes

Step 3: Preview
        └─ SVG preview shows fretboard with markers positioned

Step 4: Export
        └─ POST /api/art-studio/inlay/export-dxf
        └─ Downloads: inlay_pockets.dxf (R12)

Step 5: CNC
        └─ Load DXF into CNC controller (GRBL/Mach4)
        └─ Set tool: 1/16" ball end mill
        └─ Set depth: 1.5mm
        └─ Run program → pockets routed
        └─ Glue inlay material, sand flush, finish
```

> **Annotation:** This path is end-to-end automated. The DXF contains properly positioned closed polylines for each inlay pocket. No manual CAD work needed for standard patterns.

### Path B — Custom Artwork Extending to Headstock (Semi-Manual)

```
Step 1: Design the artwork
        ├─ Option A: Draw in Inkscape/Fusion 360
        │   └─ Create continuous vine/pattern from fret 1 → headstock
        │   └─ Export as SVG
        │
        ├─ Option B: AI-assisted concept
        │   └─ Use inlay_prompts.py to generate AI prompt
        │   └─ Feed to DALL-E or Midjourney → concept image
        │   └─ Trace/vectorize to SVG (Inkscape: Path > Trace Bitmap)
        │
        └─ Option C: Use fretboard inlay designer + hand-drawn headstock extension
            └─ Generate standard markers via Inlay Designer
            └─ Draw headstock portion manually in CAD
            └─ Combine into single SVG

Step 2: Split artwork into two zones
        └─ Fretboard zone: fret 1 through fret 22 (within fretboard width taper)
        └─ Headstock zone: nut to headstock tip (within headstock outline)
        └─ This split is manual today (⚠️ gap)

Step 3: Generate pocket toolpaths
        ├─ Fretboard pockets:
        │   └─ POST /api/cam/toolpath/relief/export-dxf  (SVG → DXF)
        │   └─ OR POST /api/cam/toolpath/vcarve/gcode    (SVG → G-code)
        │
        └─ Headstock pockets:
            └─ Same endpoints, separate SVG input

Step 4: Combine outputs
        └─ Manual: overlay DXF files in CAM software
        └─ Align using nut position as shared datum point

Step 5: CNC
        └─ Route fretboard pockets (fretboard clamped on CNC)
        └─ Route headstock pockets (may be same setup or separate)
        └─ Glue inlay material, sand, finish
```

> **Annotation:** The manual steps are: (1) artwork creation, (2) splitting artwork into fretboard/headstock zones, and (3) combining the DXF outputs with correct alignment. A unified pipeline would eliminate steps 2 and 3 by working in a shared coordinate space where the fretboard and headstock are positioned relative to each other.

---

## Gap Analysis: Unified Fretboard-to-Headstock Inlay Pipeline

The user's request — a continuous inlay flowing from fretboard onto headstock — requires a unified design surface. Here's what that pipeline would need:

### Required New Components

| # | Component | Purpose | Depends On |
|---|-----------|---------|-----------|
| 1 | **Shared coordinate space model** | Place fretboard and headstock in correct relative position | Neck geometry (exists), headstock outline (Les Paul exists, Strat gap) |
| 2 | **Combined canvas component** | Single Vue canvas showing fretboard + headstock with correct taper and transition | Coordinate model |
| 3 | **Artwork placement tool** | Position/scale/rotate SVG artwork across the combined surface | Canvas component |
| 4 | **Zone-aware DXF export** | Export a single DXF with inlay pockets positioned relative to a shared datum | Coordinate model + artwork positions |
| 5 | **Headstock inlay router** | API endpoint accepting headstock style + inlay SVG → DXF | `inlay_prompts.py` data + V-Carve/Relief pipeline |

### Coordinate Space Definition

```
                    Headstock                    Fretboard
    ◄───── 178mm ─────►◄── nut ──►◄────────── 648mm (to bridge) ──────────►
    
    ┌─────────────────┐┌─┐
    │                 ││ │╲
    │   HEADSTOCK     ││N│  ╲
    │   ZONE          ││U│    ╲──────────────────────────────────────────┐
    │                 ││T│     │           FRETBOARD ZONE                │
    │   (89mm wide)   ││ │     │           (42.9mm → 57mm taper)        │
    │                 ││ │    ╱──────────────────────────────────────────┘
    │                 ││ │  ╱
    └─────────────────┘└─┘╱
    
    X = 0 at nut face
    X negative = toward headstock tip
    X positive = toward bridge
    Y = 0 at centerline
```

> **Annotation:** The nut is the natural datum point — it's where the fretboard meets the headstock. All fret positions are already computed as distance from the nut (positive X). Headstock coordinates would be negative X from the nut. This shared coordinate space makes it trivial to position a continuous flowing inlay across both surfaces.

---

## Inlay Material Reference (for CNC Parameters)

> **Annotation:** These cutting parameters matter for the DXF/G-code export. The inlay calculator supports pocket depth as a parameter but doesn't yet have a material library that auto-selects feed rates based on the inlay material. Including this for CNC operator reference.

| Material | Thickness (typical) | Pocket Depth | Tool | Feed Rate | Notes |
|----------|-------------------|-------------|------|-----------|-------|
| Mother of Pearl (MOP) | 1.5mm | 1.6mm | 1/16" ball end | 150 mm/min | Brittle — slow plunge |
| Abalone | 1.5mm | 1.6mm | 1/16" ball end | 120 mm/min | Very brittle — climb cut |
| Black acrylic (dots) | 2.0mm | 2.1mm | 1/16" flat end | 300 mm/min | Easy to cut |
| Maple (contrast) | 1.5mm | 1.6mm | 1/16" flat end | 200 mm/min | Wood — standard feeds |
| Turquoise (crushed) | 1.5mm | 1.8mm | 1/16" ball end | 100 mm/min | Fill pocket, pour resin |
| Luminlay (glow) | 2.0mm | 2.1mm | 1/16" flat end | 250 mm/min | Plastic family |

---

## Implementation Priorities

### Quick Wins (Wire Existing Assets)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | **Wire headstock inlay router** — connect `inlay_prompts.py` to a new API endpoint that accepts headstock style + inlay design → returns AI prompt + (optionally) triggers image generation | Low | Completes the headstock AI workflow |
| 2 | **Add Stratocaster preset** to inlay designer — `strat_standard` and `strat_vintage` with correct fret selection and dot sizes | Low | Strat users get one-click inlay DXF |
| 3 | **Add material presets** to DXF export — pocket depth auto-selected from material choice (MOP 1.6mm, Abalone 1.6mm, Acrylic 2.1mm) | Low | Fewer user errors |

### Medium Term (New Integration)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 4 | **Shared coordinate space model** — define fretboard + headstock relative positioning from neck geometry | Medium | Foundation for unified inlay |
| 5 | **Headstock outline for Fender** — generate the Strat headstock silhouette as a closed polyline (prerequisite for headstock inlay placement) | Medium | Enables headstock inlay positioning |
| 6 | **Combined inlay canvas** — single Vue component showing fretboard + headstock with SVG artwork overlay | Medium | Visual design surface |

### Longer Term (Full Pipeline)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 7 | **Artwork placement tool** — drag/drop/resize SVG elements across the combined fretboard+headstock surface | High | Interactive inlay design |
| 8 | **Zone-aware DXF export** — single export with correct datum, handles the fretboard/headstock transition | Medium | One-click CNC-ready output |
| 9 | **Algorithmic pattern generators** — vine, tree of life, geometric tessellation that auto-flow from fretboard to headstock | High | "One-click vine inlay" |

---

## File Map

### Production Files (Inlay System)

| File | Layer | Purpose |
|------|-------|---------|
| `services/api/app/calculators/inlay_calc.py` | Engine | Fret position math, shape generation, DXF export |
| `services/api/app/art_studio/inlay_router.py` | API | HTTP endpoints for preview, export, presets |
| `packages/client/src/views/art-studio/InlayDesignerView.vue` | UI | Interactive inlay design component |
| `packages/client/src/api/art-studio.ts` | SDK | Client-side API caller |

### Production Files (CAM — Custom Artwork Routing)

| File | Layer | Purpose |
|------|-------|---------|
| `services/api/app/cam/routers/toolpath/vcarve_router.py` | CAM | SVG → G-code (variable depth pockets) |
| `services/api/app/cam/routers/toolpath/relief_export_router.py` | CAM | SVG → DXF (flat pockets) |
| `services/api/app/art_studio/svg_ingest_service.py` | Service | Shared SVG path parsing |

### Partial / Stub Files (Headstock + Decorative)

| File | Layer | Status |
|------|-------|--------|
| `services/api/app/cam/headstock/inlay_prompts.py` | Data | ✅ Complete data, ❌ no router |
| `packages/client/src/views/art-studio/HeadstockDesignerView.vue` | UI | ⚠️ Stub (no backend) |
| `packages/client/src/views/art-studio/FretMarkersView.vue` | UI | ⚠️ Stub (may overlap with inlay designer) |
| `packages/client/src/views/art-studio/BindingDesignerView.vue` | UI | ⚠️ Stub |
| `packages/client/src/views/art-studio/PurflingDesignerView.vue` | UI | ⚠️ Stub |

### Files to Create (for unified pipeline)

| # | File | Purpose |
|---|------|---------|
| 1 | `app/art_studio/headstock_inlay_router.py` | API endpoint for headstock inlay generation |
| 2 | `app/instrument_geometry/neck/inlay_coordinate_space.py` | Shared fretboard + headstock coordinate model |
| 3 | `packages/client/src/views/art-studio/UnifiedInlayDesigner.vue` | Combined fretboard + headstock inlay canvas |
| 4 | `packages/client/src/composables/useInlayCoordinateSpace.ts` | Frontend coordinate space logic |

---

## Boundary Compliance

> **Annotation:** All inlay work stays within the Art Studio domain (`app/art_studio/`, `app/calculators/`) and CAM domain (`app/cam/routers/toolpath/`). No RMOS↔CAM cross-imports. SVG ingest is a shared service within Art Studio. DXF export uses the established `dxf_compat.py` pattern.

- **Inlay calculator → DXF export:** `app/calculators/` → `dxf_compat` ✅
- **V-Carve/Relief → G-code/DXF:** `app/cam/routers/toolpath/` ✅ (OPERATION lane)
- **Headstock prompts:** `app/cam/headstock/` → stays within CAM domain ✅
- **Frontend:** `views/art-studio/` → `api/art-studio.ts` → backend ✅
- **No cross-domain violations anticipated**

---

## GAP REGISTRY — Trackable Code & Architecture Deficits

> **Purpose:** Each gap has a unique ID, the exact file where the problem lives, what's broken, what "fixed" looks like, dependencies, and test expectations. A remediation team can work through these top-to-bottom.

### Summary Dashboard

| ID | Area | Severity | Effort | Status | Blocks |
|----|------|----------|--------|--------|--------|
| INLAY-01 | Headstock inlay backend route | **Critical** | Low | ❌ Missing | INLAY-02 |
| INLAY-02 | HeadstockDesignerView.vue wiring | **High** | Low | ⚠️ Stub (no API calls) | — |
| INLAY-03 | FretMarkersView.vue overlap | **Medium** | Low | ⚠️ Stub overlaps InlayDesignerView | — |
| INLAY-04 | Unified coordinate space model | **Medium** | Medium | ❌ Missing | INLAY-06 |
| INLAY-05 | inlay_prompts.py orphaned | **Low** | Trivial | ⚠️ Data exists, no router imports it | INLAY-01 |
| INLAY-06 | Unified inlay canvas component | **High** | Medium–High | ❌ Missing | — |

---

### INLAY-01: No Headstock Inlay Router

**Severity:** Critical — the entire headstock inlay workflow has no API surface  
**Status:** `inlay_prompts.py` contains 11 headstock styles and 20+ inlay designs, but no router exposes them. The file is orphaned.  

**Where the problem is:**
- **Expected file:** `services/api/app/art_studio/headstock_inlay_router.py` — does not exist
- **Data source:** `services/api/app/cam/headstock/inlay_prompts.py` — contains `generate_headstock_prompt()`, `HEADSTOCK_STYLES` dict, `INLAY_DESIGNS` dict. Complete data, zero API wiring.
- **Registration:** No entry in `services/api/app/router_registry/manifest.py` or `services/api/app/main.py` for headstock inlay
- **Comparison:** `services/api/app/art_studio/inlay_router.py` (fretboard inlay) is fully wired and registered — use as template

**What's there now:**
```python
# inlay_prompts.py — data module, never imported by any router
HEADSTOCK_STYLES = {
    "fender_stratocaster": {...},
    "fender_telecaster": {...},
    "gibson_les_paul": {...},
    # ... 11 total styles
}
INLAY_DESIGNS = {
    "mother_of_pearl_dot": {...},
    "abalone_block": {...},
    # ... 20+ designs
}
def generate_headstock_prompt(style: str, design: str) -> str: ...
```

**What "fixed" looks like:**
Create `services/api/app/art_studio/headstock_inlay_router.py`:
```python
router = APIRouter()

@router.get("/styles")
def list_headstock_styles() -> list[dict]:
    """Return available headstock styles with metadata."""

@router.get("/designs")
def list_inlay_designs() -> list[dict]:
    """Return available inlay designs with previews."""

@router.post("/generate-prompt")
def generate_prompt(req: HeadstockInlayRequest) -> HeadstockInlayResponse:
    """Accept style + design → return AI prompt text."""

@router.post("/preview")
def preview_headstock_inlay(req: HeadstockInlayPreviewRequest) -> HeadstockInlayPreviewResponse:
    """Return SVG preview of inlay on headstock outline."""
```
Register in `main.py`: `app.include_router(headstock_inlay_router, prefix="/api/art-studio/headstock-inlay", tags=["ArtStudio"])`

**Test expectations:**
- `GET /api/art-studio/headstock-inlay/styles` returns ≥11 styles
- `GET /api/art-studio/headstock-inlay/designs` returns ≥20 designs
- `POST /generate-prompt` with valid style + design returns non-empty prompt string
- Invalid style returns 422 validation error (not 500)

**Dependencies:** Blocks INLAY-02 (frontend has no backend to call)  
**Blocked by:** INLAY-05 should be resolved first (wire the import)

---

### INLAY-02: HeadstockDesignerView.vue Is a Non-Functional Stub

**Severity:** High — users navigate to the headstock designer and find an empty page  
**Status:** Vue component exists but has no API calls, no reactivity, no output. Contains commented-out planned endpoint references.  

**Where the problem is:**
- **File:** `packages/client/src/views/art-studio/HeadstockDesignerView.vue`
- **Current state:** Renders static placeholder text. Contains `<!-- TODO: Wire to headstock inlay API -->` comments. No `<script setup>` logic, no SDK imports, no Pinia store.
- **Comparison:** `InlayDesignerView.vue` is fully production-wired with SDK calls to `/api/art-studio/inlay/*` — use as template

**What "fixed" looks like:**
Wire the component to call the new headstock inlay router (INLAY-01):
1. Import SDK endpoints for headstock inlay styles/designs
2. Add reactive state for selected style, selected design, preview SVG
3. On mount: fetch available styles + designs
4. On generate: call `/generate-prompt`, display result
5. On preview: call `/preview`, render SVG inline
6. Export button: download SVG or DXF

**Test expectations (Vitest):**
- Component mounts without errors
- On mount, calls styles and designs endpoints
- Selecting a style + design enables "Generate" button
- Generate action triggers API call with correct payload
- Preview SVG renders in the DOM

**Dependencies:** None downstream  
**Blocked by:** INLAY-01 (backend endpoint must exist)

---

### INLAY-03: FretMarkersView.vue Overlaps InlayDesignerView

**Severity:** Medium — two views do the same thing, confusing navigation and split maintenance  
**Status:** `FretMarkersView.vue` describes itself as a "simplified version" of `InlayDesignerView.vue`. Both handle fret marker placement on fretboards.  

**Where the problem is:**
- **File:** `packages/client/src/views/art-studio/FretMarkersView.vue`
- **Self-described:** "Simplified version of InlayDesignerView for standard dot markers"
- **Problem:** Users reach this view from navigation and get a stripped-down experience. The full InlayDesignerView already supports dots, blocks, and custom shapes. Maintaining two views means bugs get fixed in one but not the other.

**What "fixed" looks like:**
Two valid approaches:
- **Option A (Recommended):** Remove `FretMarkersView.vue` entirely. Add a "Quick Dots" preset mode to `InlayDesignerView.vue` that pre-selects standard dot markers — same simplicity, single code path.
- **Option B:** Promote `FretMarkersView.vue` to a thin wrapper that embeds `InlayDesignerView` with preset props (dot pattern, standard frets) and hides advanced controls.

**Test expectations:**
- Standard dot marker workflow accessible from both navigation paths
- No dead-end navigation to a stub page
- Single source of truth for dot placement logic

**Dependencies:** None  
**Blocked by:** Nothing — can be done independently

---

### INLAY-04: No Unified Coordinate Space Model

**Severity:** Medium — fretboard and headstock inlays use disconnected coordinate systems, preventing unified placement  
**Status:** Does not exist. Fretboard inlays use fret-relative coordinates (fret number + offset). Headstock inlays would need absolute mm coordinates. No model bridges the two.  

**Where the problem is:**
- **Expected file:** `services/api/app/instrument_geometry/neck/inlay_coordinate_space.py` — does not exist
- **Fretboard system:** `inlay_calc.py` places inlays by fret number + relative offset within the fret span
- **Headstock system:** No coordinate system exists. `inlay_prompts.py` references styles but has no spatial model.
- **Gap:** When the fretboard meets the headstock at the nut, there's no model for how coordinates transition. A vine inlay flowing from fret 1 up to the headstock would need this.

**What "fixed" looks like:**
Create a coordinate space module that:
```python
class InlayCoordinateSpace:
    """Unified coordinate space from headstock tip to last fret."""
    
    def __init__(self, neck_geometry: NeckGeometry):
        self.origin_mm = (0, 0)  # headstock tip
        self.nut_position_mm: float  # where fretboard begins
        self.fret_positions_mm: list[float]  # absolute positions
        self.headstock_bounds: BoundingBox
        self.fretboard_bounds: BoundingBox
    
    def fret_to_absolute(self, fret: int, offset_x: float, offset_y: float) -> tuple[float, float]:
        """Convert fret-relative coordinate to absolute mm."""
    
    def absolute_to_zone(self, x: float, y: float) -> str:
        """Return 'headstock' | 'nut_transition' | 'fretboard'."""
    
    def export_zones_dxf(self) -> bytes:
        """Export zone boundaries as DXF for CNC datum alignment."""
```

**Test expectations:**
- `fret_to_absolute(12, 0, 0)` returns position at half scale length + headstock offset
- `absolute_to_zone()` correctly classifies points in headstock vs fretboard
- Coordinates are continuous across the nut boundary (no gap or overlap)
- DXF export produces valid R12 AC1009

**Dependencies:** Blocks INLAY-06 (canvas needs coordinate math)  
**Blocked by:** Nothing — can be built from existing neck geometry data

---

### INLAY-05: `inlay_prompts.py` Is Orphaned

**Severity:** Low — the data is complete and correct but unreachable from any endpoint  
**Status:** File exists at `services/api/app/cam/headstock/inlay_prompts.py` with rich data. No module imports it. Not registered in any router or manifest.  

**Where the problem is:**
- **File:** `services/api/app/cam/headstock/inlay_prompts.py`
- **Verification:** `grep -r "inlay_prompts" services/api/app/` returns zero matches outside the file itself
- **The data is good:** 11 headstock styles, 20+ inlay designs, `generate_headstock_prompt()` function — all tested manually

**What "fixed" looks like:**
Import and use in the new headstock inlay router (INLAY-01):
```python
# In headstock_inlay_router.py
from app.cam.headstock.inlay_prompts import (
    HEADSTOCK_STYLES,
    INLAY_DESIGNS,
    generate_headstock_prompt,
)
```

> **Boundary note:** `inlay_prompts.py` lives in `app/cam/headstock/` (CAM domain). The new router in `app/art_studio/` (Art Studio domain) importing from CAM would be a **boundary fence violation** per `FENCE_REGISTRY.json`. Two options:
> - **Option A:** Move `inlay_prompts.py` to `app/art_studio/` before importing
> - **Option B:** Expose prompt data via an artifact contract (JSON file) that both domains can read
>
> Check `FENCE_REGISTRY.json` profile for `art_studio ↔ cam` before deciding.

**Test expectations:**
- `from app.cam.headstock.inlay_prompts import HEADSTOCK_STYLES` succeeds
- `generate_headstock_prompt("fender_stratocaster", "mother_of_pearl_dot")` returns non-empty string
- Boundary import check passes (`python -m app.ci.check_boundary_imports`)

**Dependencies:** Feeds into INLAY-01  
**Blocked by:** Nothing

---

### INLAY-06: No Unified Inlay Canvas Component

**Severity:** High — the current fretboard-only view can't show artwork flowing from fretboard to headstock  
**Status:** Does not exist. `InlayDesignerView.vue` renders fretboard inlays only. No component handles the combined fretboard + headstock surface.  

**Where the problem is:**
- **Expected file:** `packages/client/src/views/art-studio/UnifiedInlayDesigner.vue` — does not exist
- **Current:** `InlayDesignerView.vue` renders fretboard only (fret 1 through last fret)
- **Headstock:** `HeadstockDesignerView.vue` is a stub (INLAY-02)
- **Gap:** No canvas shows both regions with correct relative positioning

**What "fixed" looks like:**
Create a combined canvas component that:
1. Renders headstock outline + fretboard outline as continuous surface
2. Uses `InlayCoordinateSpace` (INLAY-04) for correct positioning
3. Supports SVG artwork overlay with drag/drop/resize
4. Shows zone boundaries (headstock / nut transition / fretboard) as dashed lines
5. Export: single DXF with zone markers for CNC datum alignment

**Test expectations (Vitest):**
- Canvas renders both headstock and fretboard regions
- SVG artwork placed at fret 3 appears at correct absolute position
- SVG artwork dragged to headstock region snaps to headstock coordinate space
- DXF export includes zone boundary markers
- Component handles missing headstock outline gracefully (fretboard-only fallback)

**Dependencies:** None downstream  
**Blocked by:** INLAY-04 (coordinate space), INLAY-02 (headstock view must be wired)

---

### REMEDIATION SEQUENCE

```
Phase 1: Data Wiring (no dependencies)
├── INLAY-05: Wire inlay_prompts.py import (check boundary fence first)
├── INLAY-03: Consolidate FretMarkersView into InlayDesignerView
└── INLAY-04: Create InlayCoordinateSpace model                     ← can start in parallel

Phase 2: Backend (depends on Phase 1)
└── INLAY-01: Create headstock_inlay_router.py + register in main.py

Phase 3: Frontend (depends on Phase 2)
├── INLAY-02: Wire HeadstockDesignerView.vue to new API
└── INLAY-06: Build UnifiedInlayDesigner.vue                        ← depends on INLAY-04

Phase 4: Integration
└── End-to-end: fretboard + headstock inlay placement → DXF export
```

> **Annotation:** INLAY-05 (orphaned data) and INLAY-03 (view overlap) are quick wins that clean up the codebase before building new features. INLAY-04 (coordinate space) is the architecture prerequisite for the unified canvas. INLAY-01 (backend router) is the critical path for headstock inlays.

### Files to Create

| File | Gap(s) |
|------|--------|
| `services/api/app/art_studio/headstock_inlay_router.py` | INLAY-01 |
| `services/api/app/instrument_geometry/neck/inlay_coordinate_space.py` | INLAY-04 |
| `packages/client/src/views/art-studio/UnifiedInlayDesigner.vue` | INLAY-06 |
| `packages/client/src/composables/useInlayCoordinateSpace.ts` | INLAY-06 |

### Files to Modify

| File | Gap(s) | Change |
|------|--------|--------|
| `services/api/app/art_studio/headstock_inlay_router.py` (new) | INLAY-01, INLAY-05 | Import from `inlay_prompts.py`, expose styles/designs/generate-prompt/preview |
| `services/api/app/main.py` | INLAY-01 | Register headstock inlay router |
| `packages/client/src/views/art-studio/HeadstockDesignerView.vue` | INLAY-02 | Wire to headstock inlay API via SDK |
| `packages/client/src/views/art-studio/FretMarkersView.vue` | INLAY-03 | Remove or convert to thin wrapper over InlayDesignerView |
| `packages/client/src/views/art-studio/InlayDesignerView.vue` | INLAY-03 | Add "Quick Dots" preset mode |

---

*End of handoff. All dimensions in mm. DXF output is R12 (AC1009). Pocket depths assume standard inlay shell thickness (1.5mm) with 0.1mm clearance.*
