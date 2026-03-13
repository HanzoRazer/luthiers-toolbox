# Design Review: vine_girih_generator.html & inlay_designer.html

> **Date:** 2026-02-12
> **Reviewer:** AI Design Audit
> **Scope:** Two standalone HTML prototypes at project root
> **Cross-reference:** [INLAY_PATTERN_GENERATORS_REVIEW.md](./INLAY_PATTERN_GENERATORS_REVIEW.md), [ART_ENGINE_EXECUTIVE_SUMMARY.md](./ART_ENGINE_EXECUTIVE_SUMMARY.md)

---

## File Inventory

| File | Lines | Tabs/Modes | Motif Data | Generator Math | Export Formats |
|------|------:|------------|-----------|----------------|---------------|
| `vine_girih_generator.html` | 1,861 | 4 tabs | 5 SVG motifs (hand-drawn Bezier art) | Parametric vine, Girih-5 tessellation, binding flow | SVG mm, OpenSCAD, BOM CSV |
| `inlay_designer.html` | 755 | 1 viewport + 6 panels | 7+ embedded motifs (lotus, 2 rosettes, celtic knots, tree of life) | Scale/aspect-ratio, material assignment | SVG mm, OpenSCAD, clipboard |

---

## 1. Purpose Statement & Assumed Goals

### vine_girih_generator.html

**Purpose:** A four-tool CNC inlay design suite for organic vine motifs and Islamic geometric (Girih) tessellations, targeting guitar rosettes, fretboard inlays, headstock decoration, and body binding.

**Assumed goals:**
- Provide a self-contained parametric design tool for vine scrollwork and Girih-5 rosette patterns
- Let luthiers preview material combinations (10 tonewoods/shells) before committing to CNC
- Generate export files (SVG in mm, OpenSCAD modules) ready for CAM toolpath generation
- Bridge the gap between decorative art design and CNC manufacturing with offset layers
- Document the binding flow pipeline architecture for future integration

### inlay_designer.html

**Purpose:** A motif-library-driven inlay design tool for celtic knots, floral patterns, and rosette art, with click-to-assign multi-material regions and CNC layer visualization.

**Assumed goals:**
- Provide a catalog of pre-drawn motifs (celtic, floral, rosette) with per-region material assignment
- Enable precise mm scaling with aspect-ratio lock for physical inlay sizing
- Visualize CNC layers (centerline, male/inlay cut, pocket/wood cut) with configurable offsets
- Export production-ready SVG with separate CNC layers and OpenSCAD stub modules

---

## 2. Primary Users & Jobs-to-Be-Done

### Who uses these tools

| User Persona | Job-to-Be-Done | Primary Tool |
|-------------|----------------|--------------|
| **CNC Luthier** (intermediate–advanced) | Design rosette inlay patterns with precise material placement before committing shell/wood stock | Both |
| **Art Designer / Prototyper** | Experiment with parametric vine scrollwork and Girih geometric patterns | vine_girih Tab 2–3 |
| **Binding Specialist** | Wrap vine decoration along guitar body contour for purfling channels | vine_girih Tab 4 |
| **Production Shop Owner** | Generate SVG files for CNC import with proper offset layers and BOM for ordering materials | Both |
| **Hobbyist / Learner** | Browse pre-drawn motifs, apply material colors, understand CNC layer concepts | inlay_designer |

### Where the tools are used

- **Workshop desktop browser** — offline-capable standalone HTML files, no server required
- **Pre-production planning** — before committing to material cutting
- **Alongside CAM software** — exported SVG imported into toolpath generators

### Constraints

| Constraint | Impact |
|-----------|--------|
| **Budget:** Shell materials (MOP, abalone, paua) are expensive | BOM estimation and material preview reduce waste |
| **Safety:** CNC router operation requires correct offsets | Offset accuracy is manufacturing-critical |
| **Time:** Rosette inlay is a multi-hour manual process | Previewing before cutting saves full rebuild cycles |
| **Environment:** Workshop PCs may be older, offline | Standalone HTML with no dependencies is ideal |
| **Precision:** Inlay tolerances are ±0.05mm | Offset computation method determines whether exports are CNC-usable |

---

## 3. Key Requirements

### Must Have (MoSCoW)

| # | Requirement | vine_girih | inlay_designer | Status |
|---|------------|:----------:|:--------------:|--------|
| M1 | Geometrically correct CNC offsets (not visual stroke expansion) | ⚠️ Partial | ❌ No | **Critical gap in both** |
| M2 | Export SVG in true mm coordinates | ✅ Yes | ✅ Yes | Both use `width="Xmm"` viewBox scaling |
| M3 | Material preview with real tonewood/shell colors | ✅ 10 materials | ✅ 8 materials | Both have rich palettes |
| M4 | Separate CNC layers in export (centerline, male, pocket) | ✅ Yes | ✅ Yes | Both structure SVG with layer groups |
| M5 | Scale-to-physical-size with mm readout | ✅ Presets + slider | ✅ Width/Height + lock | Both functional |

### Should Have

| # | Requirement | vine_girih | inlay_designer | Status |
|---|------------|:----------:|:--------------:|--------|
| S1 | DXF R12 export (AC1009 with closed LWPOLYLINE) | ❌ No | ❌ No | Neither exports DXF — critical for professional CAM |
| S2 | Per-region material assignment for multi-piece inlays | ❌ No (global per tab) | ✅ Click-to-assign | inlay_designer only |
| S3 | Girih tile BOM with piece counts and area estimates | ✅ CSV export | N/A | vine_girih Tab 3 |
| S4 | Aspect-ratio lock on scaling | ❌ Single "max dim" slider | ✅ Linked W/H with toggle | inlay_designer only |
| S5 | Parametric generation (not just static library) | ✅ 6-slider vine + 5-tile Girih | ❌ Static motif library only | vine_girih only |

### Could Have

| # | Requirement | Status |
|---|------------|--------|
| C1 | Undo/redo for material assignments | ❌ Neither |
| C2 | Import custom SVG motifs from file | ❌ Neither (inlay_designer has static library only) |
| C3 | Save/load project state | ❌ Neither |
| C4 | Compound motif composition (layer multiple patterns) | ❌ Neither |
| C5 | Direct CNC machine connection / G-code generation | ❌ Neither (deferred to backend CAM) |

---

## 4. How Well Current Design Serves Purpose

### Strengths

#### vine_girih_generator.html

1. **Girih-5 tessellation engine is mathematically sound.** The `makePoly()` function correctly computes polygon vertices from interior angle sequences. The five Girih tile types (decagon, pentagon, elongated hexagon, bowtie, rhombus) use proper circumradius formulas and edge-walk construction. The `buildGirihRosette()` function places tiles by edge-adjacency with correct center-to-center distances based on apothem sums — this is real computational geometry, not visual approximation.

2. **Parametric vine generation is genuinely parametric.** Six interdependent parameters (curl, leaves, growth, phase, vine width, leaf size) produce meaningfully different vine scrollwork via iterative angle accumulation (`a += Math.sin(i*0.38) * curl * 0.4`). The four presets (binding band, headstock, rosette arms, JEM fretboard) demonstrate real luthier knowledge — each preset includes application-specific notes with physical specs.

3. **Binding flow pipeline architecture is complete.** The Catmull-Rom spline implementation is textbook-correct (cubic Hermite interpolation with 0.5 tension). The `sampleSpline()` → normal-vector offset → vine wrapping pipeline is fully coded. Only the input data (Strat body contour) is stubbed. The developer handoff notes are unusually thorough — they specify exact format, winding order, point count, and source files.

4. **Rich material system.** 10 materials with both base color and grain color, correctly applied throughout all four tabs. Material names use real luthier terminology (MOP, paua abalone, bloodwood).

5. **BOM export for Girih rosettes.** The CSV export includes per-tile-type piece counts, areas (using correct polygon area formulas), and material assignments — directly useful for ordering shell blanks.

6. **Application presets encode luthier domain knowledge.** The four vine presets contain non-obvious specifications (e.g., "N=48 tiles around full body for binding band", "1.2mm wide × 120mm long for JEM fretboard") that would be hard for a generalist to reconstruct.

#### inlay_designer.html

1. **Click-to-assign material regions.** Left-click assigns the active material to an SVG path; right-click clears it. This is the only tool in the prototype suite that supports true multi-material inlay design where each piece can be a different material.

2. **Motif quality is production-grade.** The rosette_v2 motif contains thousands of coordinate points defining a complex concentric pattern with triangle fans, petal rings, and fine inner detail — this is not placeholder art. The celtic_cross, triquetra, and tree_of_life are similarly detailed.

3. **CNC layer visualization is well-structured.** Centerline (gold #ffd700), male/inlay (cyan #00ccff), and pocket/wood (orange #ff6633) layers use standard CNC visualization conventions. The offset values are user-adjustable (0–0.5mm in 0.01mm steps).

4. **Export SVG is properly layered.** The `buildExportSVG()` function outputs SVG with `<g id="design">`, `<g id="centerline">`, `<g id="male_cut">`, and `<g id="pocket_cut">` groups — these can be individually selected in downstream CAM software.

5. **Collapsible panel UI.** Six independently collapsible control panels keep the interface manageable despite significant control surface area.

6. **Clean separation of rendering and export.** The display rendering and export SVG generation use separate code paths, allowing display to use visual effects (shadows, glow) while exports remain clean vector.

### Weaknesses

#### CRITICAL: CNC Offset Computation Is Not Geometrically Correct

**This is the same fundamental flaw found in V1/V2 of INLAY_PATTERN_GENERATORS.txt.**

Both tools use **stroke-width expansion** to visualize CNC offsets, not geometric path offsetting:

**vine_girih_generator.html:**
- Tab 1 (Vine Motifs): Export SVG uses `stroke-width` on path copies for male/pocket layers — pure visual, not computed offsets
- Tab 2 (Parametric Vine): CNC male layer is `stroke-width="${(segW/SCALE*1.1+vineOffMM*2)}"` — just a thicker stroke, not a true offset path
- Tab 3 (Girih): The `drawTile()` function does compute simple polygon vertex offsets via normal vectors (`expanded = verts.map(...)` using perpendicular displacement), which is geometrically meaningful for convex polygons. However, this offset is only rendered to canvas — it is **not included in the SVG export** (`exportGirihSVG()` exports un-offset tile paths only)
- Tab 4 (Binding): Outer binding stripe uses normal-vector offset for display but the SVG export is a near-empty stub

**inlay_designer.html:**
- `renderViewport()` uses `stroke-width="${sw * maleOffVb * 2}"` for CNC overlay — this visually expands the stroke around each path, not a true parallel curve
- `buildExportSVG()` exports the male_cut layer as `stroke-width="${maleOffVb*2}" stroke-linejoin="round"` — a cosmetic representation, not a toolpath-usable offset

**Impact:** Any CNC operator importing these SVGs and expecting the "male cut" or "pocket cut" layers to be offset geometry will get incorrect toolpaths. The visual stroke expansion does not handle:
- Concave path segments (self-intersection)
- Sharp corners (miter vs. round vs. bevel decisions)
- Cusps in Bezier curves
- Path topology changes (inner loops collapsing at tight offsets)

**Exception:** The Girih Tab 3 tile offset is the one place where real vertex-normal offset is computed—but only for canvas display, not export.

#### Other Weaknesses

| # | Weakness | Severity | Affected |
|---|----------|----------|----------|
| W2 | No DXF export | High | Both — professional CNC workflows require DXF R12 (AC1009), not SVG |
| W3 | No SVG import capability | Medium | Both — users can't add their own motifs without editing source |
| W4 | Girih grid mode has simplistic tile placement | Medium | vine_girih Tab 3 — grid mode cycles through tile types sequentially (`phase = (c+r*2)%5`) rather than using proper Penrose/Girih tiling rules. Only the rosette mode uses edge-adjacency |
| W5 | Binding flow permanently uses oval stub | Medium | vine_girih Tab 4 — even selecting "Strat" body uses `guitarContours['oval']` (line: `const contour=guitarContours[isStub?'oval':'oval']`) — both branches return oval |
| W6 | No state persistence | Medium | Both — reload loses all material assignments and parameter settings |
| W7 | Vine scroll leaf Bezier is visually thin | Low | Tab 2 — leaf shapes use simple symmetric Bezier with control points only ±0.2 of leaf size, producing very narrow leaf silhouettes |
| W8 | Strapwork lines are simplified | Low | Girih Tab 3 — `getStrapwork()` uses edge-third-point connections as a rough approximation; true Girih strapwork requires precise bisector-angle construction |
| W9 | No mm grid overlay on canvas tabs | Low | vine_girih Tabs 2–4 use pixel grid (50px intervals) with a scale bar, not a true mm grid |

---

## 5. Failure Modes & Risks

### Manufacturing Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **CNC operator treats stroke-expanded "offset" as real offset geometry** | High | **Ruined inlay pieces + wasted shell material** | Must either compute real offsets or add prominent warnings that layers are visual-only |
| **Girih tile gaps at small edge sizes** | Medium | Visible gaps between rosette tiles | The `buildGirihRosette()` placement math uses idealized distances — real CNC kerf needs per-edge compensation, not per-vertex |
| **BOM underestimates material** | Medium | Insufficient shell ordered | Area estimates use ideal polygon formulas without waste factor or kerf loss |
| **Binding flow exported with stub data** | Low (obvious) | Non-functional output | Stub warnings are clear in both UI and SVG comments |

### Software Risks

| Risk | Type | Detail |
|------|------|--------|
| **No XSS vulnerability** | Security ✅ | Neither tool imports external SVG — all motif data is hardcoded. `DOMParser` is used only on internal SVG strings in `inlay_designer.html`, not user input |
| **Memory pressure from large motif SVGs** | Performance | rosette_v2 alone contains thousands of coordinate pairs in a string literal. On low-memory devices this could cause slow initial parse |
| **Canvas resolution on high-DPI displays** | Display | Neither tool uses `devicePixelRatio` scaling — canvas content will appear blurry on Retina/4K displays |
| **No input validation on sliders** | Robustness | Slider `min`/`max` attributes provide bounds but there's no JS-side validation if values are programmatically set |
| **No error handling on clipboard API** | UX | `copyClipboard()` in inlay_designer has a try/catch but vine_girih's `copyVineSVG()` does not handle rejection |

### Integration Risks

| Risk | Detail |
|------|--------|
| **Duplication with backend art_studio** | `services/api/app/art_studio/` already has rosette generators, inlay pattern code, and material systems. These HTML prototypes overlap significantly but share no code |
| **Duplication with INLAY_PATTERN_GENERATORS** | The V1/V2/V3 React components in `INLAY_PATTERN_GENERATORS.txt` cover similar ground (pattern generation + SVG export + CNC offsets) with the same stroke-expansion flaw |
| **No path to backend integration** | These are standalone HTML files with no API calls, no SDK usage, no shared data formats with the Vue frontend |

---

## 6. Alternatives & Tradeoffs

### Architecture Alternatives

| Alternative | Pros | Cons | Recommendation |
|-------------|------|------|---------------|
| **A: Keep as standalone HTML prototypes** | Zero dependencies, works offline, fast iteration | No code sharing, no backend integration, duplicates art_studio logic | Short-term only — useful for design experimentation |
| **B: Port generators to Python backend (art_studio)** | Leverages existing ArtSpec protocol, can use Shapely/clipper for real offsets, integrates with DXF exporter | Loses instant visual feedback, requires Vue frontend for preview | **Recommended for CNC-critical code** (offset computation, DXF export) |
| **C: Port to Vue frontend components** | Integrates with SDK, stores, and existing UI framework | Still needs backend for offset computation and DXF export | **Recommended for preview/design UI** |
| **D: Hybrid — keep HTML for rapid prototyping, port proven generators** | Best of both worlds — prototype freely, promote to production when validated | Requires discipline to track what's prototype vs. production | **Best overall approach** |

### CNC Offset Alternatives

| Approach | Accuracy | Complexity | Used By |
|----------|---------|-----------|---------|
| **Stroke expansion (current)** | Visual only — not CNC-usable | Zero | V1/V2 prototypes, both HTML files |
| **SVG `offset(r=X)` in OpenSCAD** | Correct for extrusion | Requires OpenSCAD pipeline | Both files' OpenSCAD exports (deferred to OpenSCAD) |
| **Clipper/Shapely polygon offset in Python** | Production-grade, handles all edge cases | Medium | Backend art_studio should use this |
| **Per-vertex normal offset (Girih Tab 3 canvas)** | Correct for convex polygons only | Low | vine_girih drawTile() — but not exported |
| **True Bezier curve offset (Tiller-Hanson)** | Mathematically exact for curves | High | V3 spiral in INLAY_PATTERN_GENERATORS.txt uses this approach |

### Generator Math Assessment

| Generator | Math Quality | Portable to Python? | Notes |
|-----------|-------------|--------------------|----|
| Girih-5 tile construction (`makePoly`, `GIRIH_TILES`) | Excellent | Yes — pure geometry | Interior-angle polygon construction is textbook correct |
| Girih rosette placement (`buildGirihRosette`) | Good | Yes | Edge-adjacency via apothem sums is geometrically sound |
| Parametric vine (`drawVineScroll`) | Good | Yes | Iterative angle accumulation is simple but effective |
| Catmull-Rom spline (`catmullRom`) | Excellent | Yes — standard algorithm | Drop-in replacement for `scipy.interpolate.CubicSpline` |
| Normal-vector offset strip | Fair | Yes — but needs Clipper for production | Only handles simple cases |
| Click-to-assign material regions | Good | N/A (UI pattern) | Maps to ArtSpec `MaterialRegion` concept |

---

## 7. Recommendations

### Quick Wins (1–3 days each)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| Q1 | **Add prominent "VISUAL ONLY" warning on CNC offset layers** in both files | Prevents manufacturing errors | 1 hour |
| Q2 | **Fix binding flow branch** — change `guitarContours[isStub?'oval':'oval']` to `guitarContours[bodyKey]` so the strat stub data at least renders | Enables testing of the full pipeline | 10 minutes |
| Q3 | **Include Girih tile offset in SVG export** — the drawTile() offset math already works; wire it into `exportGirihSVG()` | Makes Girih the one export with real offsets | 2 hours |
| Q4 | **Add `devicePixelRatio` scaling** to all three canvas tabs | Fixes blurry rendering on modern displays | 1 hour |
| Q5 | **Extract Strat body contour** from `assets/bodies/strat_body.dxf` or `.svg` and populate `guitarContours.strat` | Activates the entire binding flow pipeline | 2–4 hours |

### Medium Term (1–2 weeks each)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| M1 | **Port Girih-5 tile geometry to Python** (`art_studio/generators/girih.py`) — the `makePoly()`, `GIRIH_TILES`, and `buildGirihRosette()` functions are clean and directly translatable | Enables backend DXF export and Shapely-based offsets | 3–5 days |
| M2 | **Port parametric vine generator to Python** — iterative angle + Bezier leaf construction → `art_studio/generators/vine_scroll.py` | Integrates with ArtSpec protocol and material catalog | 3–5 days |
| M3 | **Implement real path offsets via Clipper** in the Python port | Solves the core CNC offset flaw for all generators | 3–5 days |
| M4 | **Add DXF R12 export** to ported generators using the existing `art_studio` DXF exporter | Enables professional CAM workflow | 2–3 days |
| M5 | **Build Vue component wrappers** for the inlay_designer preview UI — motif gallery, click-to-assign regions, CNC layer toggles | Integrates with frontend SDK and stores | 5–7 days |
| M6 | **Add localStorage persistence** to both HTML prototypes for parameter state and material assignments | Prevents data loss on page reload | 1–2 days |

### Long Term (1+ months)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| L1 | **Consolidate all inlay generators** (INLAY_PATTERN_GENERATORS V1/V2/V3 + vine_girih + inlay_designer) into a unified `art_studio/inlay/` module governed by the ArtSpec protocol | Eliminates 5-way duplication, single source of truth | 4–6 weeks |
| L2 | **Implement Girih tiling rules** — replace grid-mode sequential cycling with proper matching rules (edge decoration compatibility) for mathematically valid Girih tilings | Enables production of large-area tessellations for guitar tops | 2–3 weeks |
| L3 | **Build parametric binding flow as a backend operation** — body contour DXF input → Catmull-Rom resampling → vine distribution → CNC offset strip → DXF/G-code output | Fully automated binding channel CAM | 3–4 weeks |
| L4 | **Implement composite motif layering** — allow combining vine generator output with Girih tiles and library motifs in a single design viewport | Enables complex multi-technique rosettes (e.g., Girih center + vine border) | 4+ weeks |

### Migration Priority

```
vine_girih Tab 3 (Girih-5)  ──→  art_studio/generators/girih.py     [HIGHEST — unique, clean math]
vine_girih Tab 2 (Vine)     ──→  art_studio/generators/vine_scroll.py [HIGH — parametric, presets]
vine_girih Tab 4 (Binding)  ──→  art_studio/generators/binding.py    [HIGH — complete pipeline]
inlay_designer (motif lib)  ──→  art_studio/motifs/library.py        [MEDIUM — static data]
vine_girih Tab 1 (motifs)   ──→  merge into motif library            [LOW — overlaps with library]
```

---

## 8. Open Questions & Data Needed

### Design Questions

| # | Question | Why It Matters | Who Can Answer |
|---|---------|---------------|----------------|
| Q1 | Are these tools actively used in the shop today, or are they prototypes for evaluation? | Determines urgency of CNC offset fixes vs. treating as reference implementations | Shop owner / production team |
| Q2 | What CAM software receives the exported SVGs? | Different CAM tools handle SVG layers differently — some ignore stroke-based "offsets," others interpret them | CNC operator |
| Q3 | Is the Girih-5 rosette a customer-requested pattern or speculative? | Determines priority of Girih port vs. other generators | Product manager |
| Q4 | Should the binding flow pipeline support body shapes beyond Strat? | The architecture supports it (contour array input) but only one stub exists | Product manager |
| Q5 | What is the target offset range for production inlays? | Current default is 0.10mm — is this correct for the shop's CNC router and bit diameters? | CNC operator |

### Technical Data Needed

| # | Data | Source | Blocks |
|---|------|--------|--------|
| D1 | Strat body contour point array (40–60 points, CCW, normalized) | `assets/bodies/strat_body.dxf` or `.svg` | Binding flow pipeline activation |
| D2 | Actual CNC kerf width for 1/16" and 1/32" end mills on MOP, abalone, rosewood | Shop measurement | Correct default offset values |
| D3 | Customer demand data for Girih vs. Celtic vs. vine patterns | Sales/request history | Migration priority ordering |
| D4 | Existing `art_studio` material catalog format | `services/api/app/art_studio/` source | Material system consolidation |
| D5 | Whether `art_studio/generators/` already has any vine or Girih code | Backend codebase exploration | Avoid re-implementing existing generators |

### Architectural Decisions Required

| # | Decision | Options | Impact |
|---|---------|---------|--------|
| A1 | Where should CNC offset computation live? | (a) Browser-side with Clipper.js, (b) Backend with Shapely, (c) Defer to OpenSCAD `offset()` | Determines whether HTML exports are CNC-usable or require post-processing |
| A2 | Should motif SVG data be served from backend or bundled in frontend? | (a) Embedded in HTML (current), (b) JSON API, (c) Static asset files | rosette_v2 alone is ~50KB of path data — bundling concerns |
| A3 | Should the HTML prototypes be preserved alongside production code? | (a) Archive, (b) Keep as rapid prototyping tools, (c) Delete after port | Prototypes enable faster design iteration than a full backend round-trip |

---

## Appendix A: Code Cross-Reference with INLAY_PATTERN_GENERATORS

| Capability | INLAY_PATTERN_GENERATORS | vine_girih_generator | inlay_designer |
|-----------|------------------------|---------------------|---------------|
| Pattern types | 6 geometric (V1), spiral (V3) | Vine parametric, Girih-5, binding | Celtic, floral, rosette |
| CNC offsets | Stroke-based (V1/V2), normal-vector (V3 spiral) | Stroke-based (Tabs 1/2/4), vertex-normal (Tab 3 canvas) | Stroke-based only |
| SVG import | V2 has DXF/SVG/CSV import | None | None |
| Material system | V1/V2 have 6 materials | 10 materials with grain colors | 8 materials with custom color picker |
| Per-region material | V2 clip-masking | Tab 3 per-tile (A/B/C cycle) | Click-to-assign per SVG path |
| DXF export | None | None | None |
| Framework | React JSX (V1/V2/V3) | Vanilla JS + Canvas/SVG | Vanilla JS + SVG |
| Generation type | Parametric (sliders) | Parametric + library | Library only |
| Unique capability | True CNC offset (V3 spiral only) | Girih-5 tessellation, Catmull-Rom binding pipeline | Multi-material click assignment |

## Appendix B: Girih-5 Tile Geometry Verification

The five Girih tile definitions were verified against published Islamic geometry references:

| Tile | Interior Angles | Edge Count | Construction Method | Verified |
|------|----------------|-----------|--------------------|----|
| Decagon | 10 × 144° | 10 | Circumradius formula `r = 1/(2·sin(π/10))` | ✅ Correct |
| Pentagon | 5 × 108° | 5 | Circumradius formula `r = 1/(2·sin(π/5))` | ✅ Correct |
| Elongated Hexagon | 108°, 108°, 144°, 108°, 108°, 144° | 6 | `makePoly()` edge-walk | ✅ Correct angles |
| Bowtie | 72°, 72°, 216°, 72°, 72°, 216° | 6 | Hand-computed vertices (non-convex) | ✅ Valid topology |
| Rhombus | 72°, 108°, 72°, 108° | 4 | `makePoly()` edge-walk | ✅ Correct |

The rosette layout (`buildGirihRosette`) places:
- 1 central decagon
- 10 pentagons (edge-adjacent at apothem-sum distance, 36° spacing)
- 5 rhombuses (between alternate pentagons)
- 5 bowties (outer ring, even positions)
- 5 elongated hexagons (outer ring, odd positions)

Total: 26 tiles per rosette. This matches the standard first-ring Girih rosette construction.

## Appendix C: Summary Verdict

| Dimension | vine_girih | inlay_designer | Score |
|-----------|-----------|---------------|-------|
| Generator math quality | Excellent | N/A (library) | 9/10 |
| CNC offset accuracy | ❌ Visual only (export) | ❌ Visual only | 3/10 |
| Export quality (SVG mm) | Good (layered, commented) | Good (layered, commented) | 7/10 |
| Export quality (DXF) | Missing | Missing | 0/10 |
| Material system | Rich, accurate | Rich, click-to-assign | 8/10 |
| UI/UX | Good 4-tab layout | Good collapsible panels | 7/10 |
| Documentation (in-code) | Excellent handoff notes | Adequate | 8/10 |
| Integration readiness | Low (standalone HTML) | Low (standalone HTML) | 2/10 |
| Unique value | Girih-5 + binding pipeline | Multi-region material assignment | 8/10 |

**Overall:** Both tools contain valuable domain-specific geometry and design logic. The Girih-5 tessellation engine and binding flow pipeline are the most valuable code assets — their math is clean and directly portable to the Python backend. The critical flaw shared across the entire prototype suite (including INLAY_PATTERN_GENERATORS V1/V2) remains the same: **CNC offsets are visual representations, not geometric computations.** This must be solved at the backend level with Shapely/Clipper before any export can be called production-ready. The HTML prototypes should be preserved as rapid design tools while their generator math is ported to `art_studio/`.
