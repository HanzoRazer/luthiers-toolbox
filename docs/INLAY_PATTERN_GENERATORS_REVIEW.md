# Design Review: INLAY_PATTERN_GENERATORS.txt

**Reviewed:** March 12, 2026  
**File:** `INLAY_PATTERN_GENERATORS.txt` (project root, ~2000 lines)  
**Format:** Three standalone React JSX components stored in a single `.txt` file

---

## 1. Purpose Statement & Assumed Goals

The file contains **three progressive iterations** of an inlay/marquetry pattern generator for The Production Shop. Each builds on the last:

| Iteration | Lines | Title | Focus |
|-----------|-------|-------|-------|
| **V1** | 1–610 | "Inlay Pattern Generator / Marquetry Module" | 6 pattern generators + SVG export + OpenSCAD output + tile repeat engine |
| **V2** | 620–1410 | "Inlay Pattern Generator" (with ingestion layer) | Adds DXF/SVG/CSV file import, clip path masking, 12 materials |
| **V3** | 1420–2000 | "Spiral Inlay Generator" | Spiral-only deep dive with true normal-vector offset paths for CNC toolpaths |

**Assumed goals:**

1. Let a luthier visually design marquetry/inlay patterns at real-world mm scale
2. Export geometry as SVG with true mm dimensions for downstream CAM (Fusion 360, Inkscape → DXF, JSCut)
3. Provide OpenSCAD code as a secondary export-to-DXF path
4. Support file import (DXF ring boundaries, SVG clip masks, CSV color grids) so patterns tile inside real instrument geometry
5. Compute true CNC offset paths (male inlay + pocket) — not just visual previews
6. Serve as a **design specification / proof-of-concept** for the unified art engine described in `ART_ENGINE_EXECUTIVE_SUMMARY.md`

---

## 2. Primary Users & Jobs-to-Be-Done

| User | Job-to-be-done | How this file serves it |
|------|----------------|------------------------|
| **Luthier (CNC)** | Design a rosette band / headstock inlay pattern and get a file my CNC can cut | SVG export with mm coords → Fusion 360 → toolpath → G-code |
| **Luthier (hand-cut)** | Get a scaled template I can print and glue to the workpiece | SVG export at real mm scale → print at 100% |
| **Developer (TPS team)** | Understand the geometry math for each pattern so I can port it to the Python backend | Pure-function generators with clear math, separated from UI |
| **Product owner** | Evaluate what a production inlay tool should look like before committing to backend implementation | Three running prototypes that demonstrate the full UX flow |

**Missing user:** The file does not address a luthier who wants to go from pattern → G-code in one tool. Every workflow shown requires leaving the app (Inkscape, Fusion 360, JSCut) to get to CNC output.

---

## 3. Key Requirements (Must / Should / Could)

### Must Have

| # | Requirement | Status |
|---|-------------|--------|
| M1 | All geometry in mm | ✅ V1/V2/V3 all use mm viewBox and mm dimensions on export |
| M2 | At least: herringbone, diamond, spiral, sunburst patterns | ✅ V1/V2 have all four + greek key + feather (V1) |
| M3 | SVG export with real dimensions | ✅ Export adds `width="Xmm" height="Ymm"` attributes |
| M4 | Material selection (at least shell, wood, metal) | ✅ 10-12 materials covering all three |
| M5 | Band/radius sizing for linear and radial patterns | ✅ `isLinear` flag on each shape drives correct dimension controls |

### Should Have

| # | Requirement | Status |
|---|-------------|--------|
| S1 | DXF import for real instrument boundaries | ✅ V2 adds DXF parser (LWPOLYLINE, POLYLINE, CIRCLE, ARC) |
| S2 | CNC offset paths (male + pocket) | ✅ V3 computes true normal-vector offsets for spirals. ⚠️ V1/V2 only show static hardcoded offset text ("±0.10 mm") without computing actual paths |
| S3 | Tile repeat that fills arbitrary band dimensions | ✅ V1 has `applyTile()`, V2 generators compute tiling internally |
| S4 | OpenSCAD as secondary DXF path | ✅ Both V1 and V2 generate OpenSCAD code (with caveats — see weaknesses) |
| S5 | Preset system for common configurations | ✅ V3 has 5 named presets. ⚠️ V1/V2 have only a single DEF default object |

### Could Have

| # | Requirement | Status |
|---|-------------|--------|
| C1 | Direct DXF export (bypass Inkscape) | ❌ Not implemented in any version |
| C2 | G-code generation | ❌ Not implemented — all versions punt to external CAM |
| C3 | Undo/redo | ❌ Not implemented |
| C4 | Save/load designs | ❌ No persistence. No preset save. No project file |
| C5 | Integration with existing backend (`inlay_calc.py`, art_studio) | ❌ Standalone React, zero connection to the Vue/FastAPI stack |

---

## 4. How Well the Design Serves Its Purpose

### Strengths

**S1. The math is clean and portable.** All six pattern generators in V1 are pure functions: `(params) → element descriptors[]`. No DOM, no state, no side effects. This is the ideal shape for porting to Python backend functions. The V3 spiral offset math (normal-vector computation from tangents) is geometrically correct and directly maps to CNC toolpath offsets.

**S2. mm discipline is consistent.** Every version maintains mm coordinates from generator through SVG viewBox through export dimensions. The "Scale Calibration" / "Band Dimensions" controls are the first thing in the parameter panel — correct priority for manufacturing software.

**S3. V2's ingestion layer is well-designed.** The DXF parser handles the four entity types that matter for lutherie (LWPOLYLINE, POLYLINE+VERTEX, CIRCLE, ARC). The SVG parser extracts paths from templates. The CSV parser with both material-name and alias modes is practical. The `activeClip` system that lets you switch between band rectangle, DXF boundary, and SVG mask without reloading files is a genuine UX win.

**S4. The three-version evolution shows design thinking.** V1 proves the pattern math works. V2 adds real-world import workflows. V3 proves CNC-grade offset computation. This is a healthy prototype progression, not aimless iteration.

**S5. The element descriptor intermediate representation is a good abstraction.** V1's `{type, fill, pts/d/cx/cy/r}` objects are a lightweight IR that decouples generation from rendering. This pattern maps directly to the `GeometryCollection` concept in the executive summary.

**S6. CNC workflow documentation is embedded in the UI.** Both V1/V2 show a step-by-step workflow (design → export → DXF conversion → Fusion 360 → toolpath → machine → fit → finish) right in the right panel. V3's "CNC Toolpaths" panel explains male/pocket/fit-gap semantics with color-coded offset values. This is excellent for an audience of luthiers, not software engineers.

### Weaknesses

**W1. Three separate components with massive duplication.** Materials catalog, UI primitives (Sl, MatPick, Toggle), SVG builder, OpenSCAD generator, export function, styling constants — all duplicated across V1/V2/V3 with minor variations. V2 adds 2 materials but copies the other 10 verbatim. V3 rewrites the slider with a slightly different `color` prop. This is the clearest signal that the file needs consolidation before any production use.

**W2. V3's CNC-grade offset computation only works for spirals.** The normal-vector offset path approach is correct, but herringbone, diamond, greek key, and sunburst in V1/V2 do not compute any offsets. The "CNC OFFSETS" panel in V1/V2 shows hardcoded strings (`"+0.10 mm"`, `"−0.10 mm"`) that are display-only. A luthier might believe these are computed per-pattern, but they are static text. This mismatch between implied and actual capability is the most dangerous aspect of the current design.

**W3. OpenSCAD output is incomplete and sometimes wrong.**
- V1/V2: `genOSCAD()` handles 5/6 shapes. Feather falls back to "use SVG export." Spiral says "use SVG export → Inkscape → DXF." The diamond OpenSCAD uses `rotate(45) square()` which is a rough approximation of the wave/lean diamond the SVG generator produces — the two outputs won't match.
- V3: No OpenSCAD at all (spiral-only tool exports SVG with offset layers).

**W4. React, not Vue.** The project frontend is Vue 3 + Pinia + TypeScript. These prototypes are React + inline styles + JavaScript. They cannot be directly integrated. The generators (pure functions) can be ported; the UI components cannot.

**W5. No DXF export.** Every downstream CNC workflow shown (Fusion 360, JSCut, RDWorks, Carbide) requires DXF input. The tool exports SVG and tells the user to convert via Inkscape or OpenSCAD. This is the biggest gap between what the tool produces and what the user's CNC actually needs.

**W6. The `dangerouslySetInnerHTML` SVG rendering is an XSS vector.** V2 loads user-provided DXF/SVG files, parses them, and injects the result into a `dangerouslySetInnerHTML` block. A malicious SVG with embedded `<script>` or event handlers would execute in the context of the app. The SVG parser (`parseSVGFile`) does not sanitize against this.

**W7. No error handling in file parsers.** `parseDXF()`, `parseSVGFile()`, and `parseCSV()` assume well-formed input. A corrupt DXF with unpaired code/value lines, an SVG without a `<svg>` root, or a CSV with mixed delimiters would produce silent wrong results or crash. The `useEffect` wraps everything in `try/catch(e){ /* skip on bad params */ }` which swallows all errors.

**W8. Inline styles with no design system.** Every component uses raw `style={{...}}` objects with hardcoded hex colors. The dark theme colors (`#070503`, `#0a0704`, `#150c04`, etc.) are repeated hundreds of times. No CSS variables, no theme object, no extractable tokens. This makes it impossible to theme, adapt for accessibility, or extract into the existing frontend design system.

---

## 5. Failure Modes & Risks

| # | Failure Mode | Severity | Likelihood | Mitigation |
|---|-------------|----------|------------|------------|
| F1 | **SVG → DXF conversion lossy** — Inkscape's SVG-to-DXF export introduces curve approximation errors, especially on arcs and spirals. A 0.05mm fit-gap tolerance budget can be consumed by export conversion alone. | High | High | Add native DXF R12 export using `ezdxf` in the Python backend. The executive summary already specifies this. |
| F2 | **Offset paths only exist for spirals** — luthier uses V2, sees "Male inlay: +0.10 mm" for herringbone, believes it's computed, cuts the wrong geometry | High | Medium | Either compute offsets for all patterns or remove the fake offset display from V1/V2. |
| F3 | **XSS via imported SVG** — malicious SVG loaded through DropZone executes arbitrary JS | High | Low (requires attacker-controlled file) | Sanitize SVG before injection. Use `DOMPurify` or render to `<img>` with data URL. |
| F4 | **DXF parser drops entities** — ARC angle calculation assumes counterclockwise. CW arcs (common in AutoCAD exports) produce inverted geometry. SPLINE and ELLIPSE entities are silently ignored. | Medium | Medium | Add SPLINE (common in fretboard inlays) and handle arc direction flags (code 73). |
| F5 | **Tile count overflow** — `Math.ceil(W/tw) * Math.ceil(H/th)` with small tile sizes (tw=3, th=3) and large bands (W=400, H=100) = 134 × 34 = 4,556 rect elements. SVG renders become sluggish. | Medium | Medium | Cap tile count or switch to `<pattern>` element for preview, full geometry only on export. |
| F6 | **No validation of band/pattern compatibility** — setting bandH=5 with toothH=80 produces a herringbone that's 16× taller than its band, clipped to a sliver. No warning shown. | Low | High | Add validation: warn when pattern unit exceeds band dimensions. |

---

## 6. Alternatives & Tradeoffs

### Option A: Consolidate all three into a single React prototype (Quick)

**What:** Merge V1/V2/V3 into one component. V2's ingestion + V1's 6 patterns + V3's offset math. Extract shared code (materials, UI primitives, SVG builder).

**Pro:** Fast path to a working tool; keeps everything in the browser; good for user testing.  
**Con:** Still React (not Vue); still no DXF export; still no backend integration; still no persistence.

**Use when:** You want a quick demo for user feedback before committing to backend investment.

### Option B: Port generators to Python, build Vue frontend (Medium)

**What:** Extract the six pure-function generators and V3's offset computation into `app/art_studio/generators/` as Python functions. Wire them through the existing art registry. Build a Vue frontend component against the API. Add DXF R12 export via `ezdxf`.

**Pro:** Integrates with existing architecture; Python generators match the executive summary plan; DXF export is trivial from Python; materials/presets stored in the database; works with the existing Vue SPA.  
**Con:** More engineering work; need to validate that Python SVG matches the JSX output exactly.

**Use when:** You're committed to building this into the product. This is the path described in the executive summary.

### Option C: Keep the React prototypes as standalone tools, port only the math (Pragmatic)

**What:** Host V2 as a static page (e.g., `/tools/inlay-designer/`) alongside the Vue app. Port only the generator math to Python for backend use (API-driven SVG/DXF generation, preset storage). The static prototype serves as the client; the Python backend serves as the manufacturing pipeline.

**Pro:** Minimal frontend rewrite; generators work in both languages; the prototype becomes a living spec that users can access immediately.  
**Con:** Two frameworks in production; no shared state/auth with the main app; risk of drift between JS and Python generators.

**Use when:** You want users to have access to a working tool immediately while the Vue integration happens in parallel.

---

## 7. Recommendations

### Quick Wins (1–2 days)

1. **Remove the fake CNC offset display from V1/V2.** Replace the hardcoded `"+0.10 mm"` / `"−0.10 mm"` strings with a note: "Offset paths available for spiral patterns. Other shapes: apply offset in your CAM tool." This prevents the most dangerous user misunderstanding (F2).

2. **Sanitize imported SVG in V2.** Before setting `dangerouslySetInnerHTML`, strip `<script>`, `on*` event attributes, and `<foreignObject>` from the parsed SVG. Or render to an `<img src="data:image/svg+xml;...">` which browsers sandbox automatically (F3).

3. **Merge the materials catalogs.** All three versions should use the same MATS object. V2's 12-entry catalog (with dyed red/blue) is the most complete. Define it once, import it into each version.

### Medium-Term (1–2 weeks)

4. **Port the six generators + offset computation to Python.** Each generator is a pure function that takes numeric params and returns a list of geometry primitives. Translation to Python is mechanical. Place them in `app/art_studio/generators/inlay_patterns.py` following the `ArtSpec` protocol from the executive summary. Add `ezdxf`-based DXF R12 export.

5. **Build a Vue component for the pattern designer.** Use the existing Pinia store pattern (composition API). The left-panel parameter controls → Pinia store → `watchEffect` → call backend API → receive SVG preview. Export button calls a different endpoint that returns DXF or high-res SVG.

6. **Consolidate V3's offset math into a general `offset_path()` utility.** The normal-vector approach works for any polyline, not just spirals. Build it as a shared CAM utility (`app/cam/geometry/offset.py`) that all generators can use.

### Long-Term (Architecture)

7. **Implement the unified art registry from the executive summary.** The six pattern generators become registered `ArtSpec` implementations. Material assignments come from the material catalog. DXF/SVG export goes through the unified exporter. Presets and designs get persisted through the snapshot system. Import (DXF/SVG/CSV) becomes an ingestion pipeline in the backend, not a frontend-only feature.

8. **Close the CNC loop.** The biggest gap is that the tool stops at SVG export. The existing `inlay_calc.py` already computes pocket depths, tool sizes, and speeds. Wire the pattern geometry to the inlay calculator to produce complete G-code (or at minimum, a Fusion 360-ready DXF with separate male/pocket layers and annotated toolpath parameters).

---

## 8. Open Questions & Data Needed

| # | Question | Who Answers | Why It Matters |
|---|----------|-------------|----------------|
| Q1 | Which patterns do real customers actually use? Is herringbone 80% of usage or 5%? | User research / analytics | Determines which generator gets offset computation first and which ones are "could have" |
| Q2 | What DXF entities do luthiers' CAD tools actually export? Is SPLINE common? | Sample DXF files from users | The V2 parser handles 4 entity types. If real files use SPLINEs (likely for fretboard outlines), the parser silently drops them |
| Q3 | Is the 0.05mm fit-gap clearance correct across all wood species? | Shop testing | Ebony swells differently than maple. A single hardcoded clearance may be wrong for 50% of material combinations |
| Q4 | Should OpenSCAD output be maintained or dropped? | Product decision | Two of six shapes fall back to "use SVG export." If <10% of users use OpenSCAD, the maintenance cost isn't justified |
| Q5 | Does the tile repeat engine produce correct geometry at tile boundaries? | Visual inspection of exported SVG at high zoom | The current `applyTile()` uses simple translation. Tile edge alignment for patterns with wave/lean parameters may produce visible seams |
| Q6 | Are these three components the authoritative spec, or are there other versions elsewhere? | Author | The file sits at the project root as `.txt`. If there are other copies in branches, design docs, or external tools, the "source of truth" needs to be established before porting |
| Q7 | What's the target machine profile? GRBL_3018 (small), Mach4_Router_4x8 (large), or both? | Product decision | Determines max band dimensions, minimum feature sizes (kerf width vs. pattern detail), and which CNC offset defaults make sense |

---

## Summary

This file is a **well-structured design prototype** that successfully proves six pattern generators, a multi-format ingestion pipeline, and CNC-grade offset path computation. The pure-function generator architecture maps directly to the unified art engine plan.

**The three critical issues before any production use are:**

1. The fake CNC offset display in V1/V2 that implies computed offsets when none exist
2. The XSS vulnerability in V2's SVG file import path
3. The absence of DXF export, which forces every user through a lossy manual conversion step

**The single biggest opportunity is:** porting the generator math to Python and closing the loop to DXF/G-code output through the existing backend — transforming this from "design tool that stops at SVG" to "design tool that produces machine-ready output."
