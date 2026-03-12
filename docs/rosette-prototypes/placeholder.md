# Rosette JSX Prototype Addendum — Batch 2

> **8 new React/JSX prototypes** found at repo root (not yet filed into `docs/rosette-prototypes/jsx/`).  
> These represent a second generation of interactive canvas-based rosette visualizers, distinct from the 11 v1–v4 wave/grid prototypes already archived.

---

## Classification Summary

| File | Lines | Status | Category | Key Innovation |
|------|------:|--------|----------|----------------|
| `shape-compositor.jsx` | 732 | **Superseded** by v2 | Compositor v1 | 13-shape parametric library, single-ring mode |
| `shape-compositor (1).jsx` | 759 | **Superseded** by v3 | Compositor v2 | +hyperbolic_wave shape (non-repeating drift) |
| `shape-compositor (2).jsx` | 880 | **Latest** | Compositor v3 | +braid_trenza (N-strand helical braid with 3D over/under) |
| `rosette-designer.jsx` | 544 | **Superseded** by Studio | Multi-ring v1 | Color-index pattern generators, pixel scanline render |
| `rosette-studio.jsx` | 636 | **Latest** | Multi-ring v2 | Wood material system, grain bitmap cache, named presets |
| `rosette-wheel.jsx` | 511 | **Unique** | Cell Painter | Symmetry painting on fixed 7-ring layout (full/half/quarter/none) |
| `hyperbolic-rosette.jsx` | 643 | **Unique** | Dedicated Composer | Hyperbolic wave multi-ring with spin animation |
| `diamond-chevron-rosette.jsx` | 657 | **Unique** | Dedicated Composer | Diamond + stepped chevron multi-ring with grain direction |

---

## Progressive Chain 1: Shape Compositor

Single-ring shape-tile exploration tool. Each version adds shapes to the SHAPES library while keeping the same annular rendering engine.

### v1 — `shape-compositor.jsx` (732 lines)
- **13 shapes** in 3 groups:
  - Polygon: parallelogram (chamfer, lean), diamond (corner round), star (3–12 pt), hexagon (squish)
  - Curve: ellipse, leaning oval, crescent (cutout), lens/vesica, teardrop, ogee, fish scale
  - Organic: asymmetric rope (drift), petal/paisley
- Material alternation: single / AB / ABA / ABC / ABCD / wave-sin
- Grain direction: tangential, radial, diagonal
- Tile gap control, grid overlay, outline toggle
- Each shape has per-tile parametric sliders with defaults and hints

### v2 — `shape-compositor (1).jsx` (759 lines) — SUPERSEDED
- **+1 shape**: `hyperbolic_wave` (non-repeating bezier wave, drift via `Math.log(idx)`, chaos modulation)
- **+5 presets**: Hyp·Calm, Hyp·Storm, Hyp·Drift, Hyp·Chaos, Hyp·Slow
- All v1 shapes preserved, same renderer

### v3 — `shape-compositor (2).jsx` (880 lines) — LATEST
- **+1 shape**: `braid_trenza` (N-strand helical braid)
  - Painter's-order z-sort for correct over/under
  - Per-strand material assignment
  - 3D curvature highlights (top-edge linear gradient)
  - Under-edge drop shadows on top strands
  - Rounded parallelogram strand ends
  - Dedicated `drawBraid()` method (separate from standard tile pipeline)
- **+4 presets**: Braid 3-str, Braid 4-str, Braid Pearl, Braid Koa
- All v1 + v2 shapes preserved (15 total)

---

## Progressive Chain 2: Multi-Ring Designer → Studio

Full ring-stack composers with per-ring pattern configuration.

### v1 — `rosette-designer.jsx` (544 lines) — SUPERSEDED
- **Pattern types**: solid, brick, wave, rope, scroll, custom grid
- Rendering: pixel scanline into `ImageData` (no grain textures)
- Color system: 4-color palette mapped by index (hex → rgb)
- Ring stack: add/remove/reorder, per-ring type+params editor
- Wave pattern: full archY asymmetric formula (same as Python backend), ROPE_GRID/ROPE_MIRROR tiles
- Scroll pattern: C-curve pairs (top opens down, bottom opens up)
- Custom grid: pixel-painting tool with configurable dimensions

### v2 — `rosette-studio.jsx` (636 lines) — LATEST
- **Replaces color indices with wood material IDs** (WOODS palette: 14 species)
- **Grain bitmap cache**: per-wood-species offscreen canvas with:
  - Deterministic PRNG seeded per cell
  - Tight vs open grain, figured/wavy lines, pore dots
  - Iridescent shimmer (MOP, abalone) via radial HSL gradients
- **Pattern types expanded**: solid, checkerboard, brick, stripe, wave, rope, custom
- **Per-ring material slots**: 1–4 wood species per pattern type
- **Presets**: Torres (classic), Pearl (MOP/abalone), Celtic (koa/walnut)
- Grain overlay blended at 55% opacity over pixel-scanline base

---

## Unique Items

### `rosette-wheel.jsx` (511 lines) — Cell Painter

A fundamentally different paradigm from the pattern generators above.

- **Fixed 7-ring layout**: Inner Binding → Inner Frieze → Inner Border → Main Band → Outer Border → Outer Frieze → Outer Binding
- **Ring widths in mm**: [0.6, 3.0, 0.5, 8.0, 0.5, 2.5, 0.6] — matches real Torres proportions
- **Cell-based painting**: each cell = 1 segment × 1 ring, clickable
- **Symmetry modes**: full (all segments mirror), half, quarter, none
- **Polar hit-testing**: mouse position → (ring, segment) via atan2 + distance
- **Wood grain per cell**: dedicated `makeGrainPattern()` with figured wavy lines, iridescent shimmer, pore dots
- **Default scheme**: Torres pattern — ebony bindings, maple friezes, rosewood main band
- **14 wood species** with tight/figure/iridescent properties + per-species accent color
- **Scale**: 4.8 mm/px, soundhole radius 40.8mm

### `hyperbolic-rosette.jsx` (643 lines) — Hyperbolic Wave Composer

A dedicated multi-ring composer built around the hyperbolic wave tile as the hero element.

- **Ring types**: solid, stripe, checker, hyp (hyperbolic wave)
- **`hypDraw()` function**: bezier-curve wave tile with:
  - `thick`: strand thickness ratio
  - `wave`: vertical amplitude
  - `skew`: peak position (asymmetric arch)
  - `drift`: `Math.log(idx+2)` — non-repeating hyperbolic drift
  - `chaos`: `Math.sin(idx*0.17)` modulation
- **Grain engine**: cached per (woodId, seed, width, height) with iridescent support
- **4 presets**:
  - Classic Dark: ebony/maple/rosewood, N=28, drift=1.4
  - Pearl Storm: MOP/abalone, N=36, drift=1.8, chaos=0.68
  - Koa Drift: warm Hawaiian, N=20, drift=0.5, low chaos
  - Cedar Fire: soundboard woods, N=32, drift=2.0, chaos=0.88
- **Spin animation**: slow rotation via requestAnimationFrame
- **Material distribution**: AB, ABC, ABCD, Wave A↔B
- **Edge shading**: linear gradient for subtle 3D tile lift
- **Annular clipping**: tiles clipped to ring bounds (prevents overflow)

### `diamond-chevron-rosette.jsx` (657 lines) — Diamond & Chevron Composer

A dedicated multi-ring composer for two new hero tile types not found in any other prototype.

- **Ring types**: solid, stripe, checker, diamond, chevron
- **`drawDiamond()` function**: (ported from Shape Compositor)
  - Square-space diamond with `wave`, `lean`, `bevel` params
  - Amplitude-based vertical oscillation per tile index
  - 8-point beveled variant with wavy chamfered edges
- **`drawChevron()` function**: NEW shape type
  - N-step interlocking zigzag
  - `steps`: number of zigzag teeth (1–6)
  - `lean`: directional lean
  - `round`: corner rounding via arcTo
  - `depth`: zigzag depth
- **`grainFill()` function**: directional grain (tangential, radial, diagonal)
- **5 presets**:
  - Dial-In: rosewood/ebony diamonds, radial grain — the "dialed" reference settings
  - Chevron 3-Step: maple/rosewood zigzags
  - Combined: diamond outer + chevron inner — dual hero bands
  - Pearl Diamond: MOP/abalone, diagonal grain for shimmer
  - Chevron Lean Koa: warm koa arrowheads with rounded corners
- **Per-ring grain direction** control (tangential → radial → diagonal)
- **Facet lighting**: top-left bright, bottom-right shadow gradient per tile

---

## Shared Architecture Across All 8 Files

### WOODS Material Library
All files carry a variant of the same wood palette (12–14 species):
- **Tone woods**: ebony, maple, quilted maple, rosewood, spruce, cedar, mahogany, koa, ovangkol, walnut
- **Inlay materials**: mother-of-pearl, abalone, bone
- **Void**: "air" / "none" (dark, represents open channel/gap)
- Properties vary by generation: base+grain (earliest) → +tight/figure (mid) → +accent/hi/iridescent (latest)

### Grain Rendering
All files use the same deterministic PRNG pattern: `s=(s*9301+49297)%233280; return s/233280`
- Tight-grain species: many thin straight lines
- Figured species: wavy sinusoidal lines
- Iridescent materials: radial HSL gradients cycling through hue
- Open-grain species: pore dots

### Annular Rendering
Two approaches used:
1. **Pixel scanline** (rosette-designer, rosette-studio): iterate all canvas pixels, compute polar coords (atan2 + distance), map to ring row/col, look up material → ImageData
2. **Tile-stamp** (compositors, hyperbolic, diamond-chevron, rosette-wheel): for each tile slot, translate+rotate to tile center, clip to annular sector, draw shape path, fill with wood + grain overlay

### UI Pattern
All export a single default React component. Dark "Production Shop" theme:
- Background: `#080604` → `#060402`
- Gold accent: `#e8c87a`
- Amber text: `#c9a96e`
- Muted info: `#4a3010`
- Consistent header: "THE PRODUCTION SHOP · INLAY MODULE"

---

## Recommended Filing

When moving to `docs/rosette-prototypes/jsx/`:

| Current Name | Recommended Archive Name | Reason |
|---|---|---|
| `shape-compositor.jsx` | `shape-compositor-v1.jsx` | Progressive v1 |
| `shape-compositor (1).jsx` | `shape-compositor-v2-hyperbolic.jsx` | Progressive v2 |
| `shape-compositor (2).jsx` | `shape-compositor-v3-braid.jsx` | Progressive v3 — LATEST |
| `rosette-designer.jsx` | `rosette-designer-v1-color-index.jsx` | Superseded by studio |
| `rosette-studio.jsx` | `rosette-studio-v1-wood-material.jsx` | Latest multi-ring |
| `rosette-wheel.jsx` | `rosette-wheel-v1-symmetry-painter.jsx` | Unique concept |
| `hyperbolic-rosette.jsx` | `hyperbolic-rosette-v1-dedicated.jsx` | Unique dedicated composer |
| `diamond-chevron-rosette.jsx` | `diamond-chevron-rosette-v1.jsx` | Unique dedicated composer |

---

## Relationship to Backend

| JSX Concept | Python Backend Equivalent | Gap |
|---|---|---|
| Shape Compositor tile shapes | `modern_pattern_generator.py` pattern types | Backend has 7 types; JSX has 15 tile shapes — many not yet ported |
| Hyperbolic wave (bezier drift) | Not yet in backend | New pattern type needed |
| Braid/trenza (over/under) | Not yet in backend | New pattern type needed |
| Diamond wave | Not yet in backend | New pattern type needed |
| Stepped chevron | Not yet in backend | New pattern type needed |
| Wood material palette | `traditional_builder.py` preset formulas | Backend uses luthier-school presets; JSX uses raw species |
| Grain rendering | N/A (visual only — grain is physical) | No backend equivalent needed |
| archY formula | `_build_wave_grid()` in modern_pattern_generator | Already aligned |

---

*Generated: March 12, 2026 — Batch 2 JSX prototype examination*
