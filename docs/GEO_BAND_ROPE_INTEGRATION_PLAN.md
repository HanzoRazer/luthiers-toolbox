# Geo Band & Rope Generator → Inlay Engine Integration Plan

**Source:** `geo_band_generator.html` (~1,570 lines JS)
**Target:** `services/api/app/art_studio/services/generators/` (Python inlay engine)
**Reference SVGs:** `twisted_rope_cable_dropin_svgs/` (6 files)
**Date:** March 12, 2026

---

## Executive Summary

The Geometric Band & Rope Inlay Generator contains three feature families that map
onto **three new generators** plus **one compositor** for the unified inlay engine.
The math infrastructure we added last session (`inlay_geometry.py`) already covers
~60% of what's needed — the remainder is the **twisted rope algorithm** (phase-based
strand weaving with crossing detection) and the **band compositor** (multi-layer
stacking with gap/repeat/mirror).

### What We Get

| Source Tab | New Generator(s) | Key Capability |
|---|---|---|
| Pattern Gallery (6 motifs) | `hex_chain`, `diamond_border`, `chevron`, `parquet`, `nested_diamond` | Pre-built polygon motifs with 2-material assignment, tile repeat |
| Twisted Rope | `twisted_rope` | Parametric N-strand weaving with correct sin/cos phase math, crossing detection, 5 centerline shapes |
| Band Composer | `band_compose()` compositor function | Multi-layer stacking of any generators with gap/repeat/mirror |

### Critical Review Findings to Fix During Port

| # | Issue | Impact | Fix Strategy |
|---|---|---|---|
| W1 | CNC offsets use stroke-width, not geometric offset | Cyan "male cut" layer is decorative, not functional | Use existing `offset_polygon()` / `offset_polyline_strip()` |
| W2 | Rope pocket is `<rect>` even for curved centerlines | Wrong pocket shape for S-wave/C-scroll/spiral | Compute parallel offset of the strand envelope |
| W5 | Band composer has no export | Canvas-only, stub `exportComposeSVG()` | Build real compositor that returns `GeometryCollection` |

---

## Phase 1 — Gallery Motif Generators (5 new shapes)

**What:** Port the 6 SVG motifs from `MOTIFS` catalogue into the inlay engine as
polygon-based generators. These overlap with our existing `diamond` generator, so
we add 5 new ones (our diamond already covers that family).

**Math required:** Already have it — `tessellate_path_d()` can parse the SVG `<path>`
elements (rope border motif); polygon points are trivially parsed.

### New generators

| Generator | Source Motif | Geometry | Params |
|---|---|---|---|
| `hex_chain` | `hex_chain` (300×1000, 28 polygons) | Hexagons + linking bars, vertical repeating | `cell_h_mm`, `count`, `material` |
| `rope_border_motif` | `rope_border` (1200×260, 14 bezier paths) | Interleaving S-curve strands as closed shapes | `band_w_mm`, `repeats`, `material` |
| `parquet_panel` | `parquet` (800×1000, 17 polygons) | Nested diamonds with radiating wedges | `size_mm`, `material` |
| `chevron_panel` | `chevron` (450×1000, 24 polygons) | Nested chevrons with side triangles | `band_h_mm`, `count`, `material` |
| `nested_diamond` | `nested_diam` (1300×420, 26 polygons) | Concentric diamonds with corner markers | `band_w_mm`, `diamonds`, `material` |

### Implementation approach

Each generator follows the same pattern:
1. Pre-computed polygon vertex lists (extracted from SVG reference files, in viewBox coords)
2. Scale from viewBox to target mm using `scale_mm / max(vb_w, vb_h)`
3. Assign `material_index` based on original fill (black=0, white=1)
4. Return `GeometryCollection` with `linear=True` for the band motifs

### Data extraction

The 6 SVG files in `twisted_rope_cable_dropin_svgs/` contain the canonical geometry:
- Polygons: parse `points="x1,y1 x2,y2 ..."` attributes → `List[Pt]`
- Paths: parse `d="M ... C ... Z"` via `tessellate_path_d()`
- Fills: `fill="white"` → material_index=1, else material_index=0
- Skip `<rect>` elements tagged as backgrounds (first two rects in each file)

### Files to modify

- `inlay_patterns.py` — Add 5 generator functions + register in `INLAY_GENERATORS`
- `schemas/inlay_patterns.py` — Add 5 new values to `InlayShape` Literal
- `test_inlay_patterns.py` — Tests for each new generator

### Effort: Small — polygon data is static, generators are simple scale+translate.

---

## Phase 2 — Twisted Rope Generator (the big one)

**What:** Port the corrected rope algorithm from `geo_band_generator.html` into a
`twisted_rope` generator. This is the highest-value feature — no other tool in the
engine can generate parametric rope geometry.

### Algorithm (from JS source, corrected from Python stub)

```
For each sample point i along centerline (N=200 samples):
  T(i) = unit tangent
  N(i) = unit normal (CCW perpendicular)
  s(i) = cumulative arc length

For strand k (k = 0..numStrands-1):
  phase_k = k · 2π / numStrands
  lateral(i) = sin(phase_k + ω·s(i)) · ropeRadius · 0.42
  depth(i)   = cos(phase_k + ω·s(i))          ← over/under ordering
  position(i) = centerline(i) + N(i) · lateral(i)
  width(i)    = strandWidthFrac · (1 - |depth(i)| · taper · 0.4)
```

### What we already have

| Need | Have? | Where |
|---|---|---|
| Tangent / Normal computation along polyline | ✅ Partial | Used in `offset_polyline()` — need to extract T/N arrays |
| Catmull-Rom / spline for centerline shapes | ✅ | `catmull_rom()`, `sample_spline()` |
| Arc-length parameterization | ❌ | Need to compute cumulative arc lengths |
| Strand path generation (sin/cos phase) | ❌ | Core new math |
| Crossing detection (depth sign change) | ❌ | Core new math |
| Dual-rail strand outlines | ✅ | `offset_polyline_strip()` |
| True geometric CNC offset of strands | ✅ | `offset_polygon()` |

### New math to add to `inlay_geometry.py`

```python
def compute_tangent_normal_arclen(pts: Polyline) -> Tuple[
    List[Pt],     # tangents
    List[Pt],     # normals (CCW)
    List[float],  # cumulative arc lengths
]:
    """Compute per-vertex tangent, normal, and cumulative arc length."""

def generate_strand_path(
    centerline: Polyline,
    normals: List[Pt],
    arc_lens: List[float],
    strand_index: int,
    num_strands: int,
    rope_radius_mm: float,
    twist_per_mm: float,
    taper: float = 0.0,
) -> Tuple[Polyline, List[float], List[float]]:
    """Generate strand centerline, depths, and widths.
    Returns (points, depth_per_point, width_per_point)."""

def split_strand_at_crossings(
    pts: Polyline,
    depths: List[float],
    widths: List[float],
) -> List[Dict]:
    """Split strand into segments where depth changes sign.
    Returns list of {pts, on_top: bool, avg_width} segments."""
```

### Centerline shapes (5, matching JS)

| Shape | Algorithm | Params |
|---|---|---|
| `straight` | Linear from (-L/2, 0) to (L/2, 0) | `length_mm` |
| `cscroll` | Quarter-circle arc, R = L × 0.45 | `length_mm` |
| `swave` | Sinusoidal, A = min(H×0.18, amplitude), freq from L | `length_mm`, `amplitude` |
| `spiral` | Archimedean, 2.2 turns inward | `length_mm` |
| `custom` | User-supplied points (use `sample_spline()`) | `points` |

### Generator signature

```python
def twisted_rope(params: Dict[str, Any]) -> GeometryCollection:
    """Parametric twisted rope inlay band.

    Params
    ------
    num_strands  : int   — 2–5, default 3
    rope_width   : float — total rope width (mm), default 6
    twist_per_mm : float — angular frequency ω (rad/mm), default 0.25
    strand_width : float — fraction of rope width per strand, 0.2–0.9, default 0.55
    taper        : float — depth-based width taper, 0–0.5, default 0
    shape        : str   — centerline shape (straight/cscroll/swave/spiral/custom)
    length_mm    : float — band length, default 120
    kerf_mm      : float — CNC kerf for offset layers, default 0.10
    strand_mats  : list  — material_index per strand, default [0,1,2]
    amplitude    : float — S-wave amplitude (mm), default 10
    custom_pts   : list  — custom centerline points [[x,y], ...]
    """
```

### Output structure

Each strand becomes **two elements** in the `GeometryCollection`:
1. **Strand outline** — closed polygon from `offset_polyline_strip(strand_path, strand_width/2)`
   - `material_index` from `strand_mats[k]`
   - `kind="polygon"`
2. **Strand crossing metadata** — stored in element `metadata` dict:
   - `on_top: bool` — whether this segment is the "over" strand
   - `strand_index: int`
   - `depth_avg: float`

The overall collection also includes:
3. **Centerline** — `kind="polyline"`, `material_index=-1` (construction line)
4. **CNC pocket envelope** — `kind="polygon"`, computed as:
   - For straight: `offset_polyline_strip(centerline, rope_width/2 + kerf)`
   - For curved: same approach — follows the curve, not a rectangle (fixing W2/W5)

### Presets (4, matching JS)

```python
ROPE_PRESETS = {
    "purfling":  {"num_strands": 3, "rope_width": 4,  "twist_per_mm": 0.40,
                  "strand_width": 0.5,  "taper": 0.1, "shape": "straight",
                  "length_mm": 100, "strand_mats": [0, 1, 2]},
    "binding":   {"num_strands": 3, "rope_width": 7,  "twist_per_mm": 0.22,
                  "strand_width": 0.58, "taper": 0.0, "shape": "swave",
                  "length_mm": 180, "strand_mats": [2, 1, 0]},
    "headstock": {"num_strands": 2, "rope_width": 5,  "twist_per_mm": 0.30,
                  "strand_width": 0.6,  "taper": 0.2, "shape": "cscroll",
                  "length_mm": 90,  "strand_mats": [0, 1]},
    "fret":      {"num_strands": 4, "rope_width": 3,  "twist_per_mm": 0.55,
                  "strand_width": 0.45, "taper": 0.3, "shape": "straight",
                  "length_mm": 45,  "strand_mats": [0, 1, 2, 3]},
}
```

### Critical fix: True geometric CNC offsets

The JS original uses `stroke-width` expansion for CNC layers (review findings W1, W2).
The Python port will use real geometric offsets:

```python
# For each strand outline polygon:
male_cut = offset_polygon(strand_outline, +kerf_mm)   # outward
pocket_cut = offset_polygon(strand_outline, -kerf_mm)  # inward

# For the envelope (fixes W2 — curved pocket):
envelope = offset_polyline_strip(centerline, rope_width/2 + kerf_mm)
# This follows the curve for S-wave/C-scroll/spiral — no more <rect>
```

### Files to modify

- `inlay_geometry.py` — Add `compute_tangent_normal_arclen()`, `generate_strand_path()`, `split_strand_at_crossings()`
- `inlay_patterns.py` — Add `twisted_rope()` generator + `ROPE_PRESETS` + register
- `schemas/inlay_patterns.py` — Add `"twisted_rope"` to `InlayShape`
- `test_inlay_patterns.py` — Tests for rope math + generator

### Effort: Medium — core algorithm is clear, main work is strand outline generation and crossing segmentation.

---

## Phase 3 — Band Compositor

**What:** Port the Band Composer tab as a **compositor function** that takes multiple
generator outputs and stacks them into a composite band. This is not a generator
itself — it's an orchestrator.

### What the JS does

```javascript
// Layer stack: array of {motifKey, mat1, mat2, weight}
// Band settings: totalWidth, bandHeight, gapMM, repeats, mirror
// For each layer:
//   1. Scale motif to fit (bandWidth × layerHeight based on weight)
//   2. Clip to layer bounds
//   3. Draw gap between layers (ebony purfling line)
// For repeats > 1: tile horizontally, optionally mirror alternate tiles
```

### Python compositor design

```python
def compose_band(
    layers: List[Dict[str, Any]],
    band_width_mm: float = 150,
    band_height_mm: float = 25,
    gap_mm: float = 0.5,
    repeats: int = 4,
    mirror: bool = False,
    kerf_mm: float = 0.10,
) -> GeometryCollection:
    """Stack multiple inlay patterns into a composite band.

    Each layer dict:
      shape: str         — generator key from INLAY_GENERATORS
      params: dict       — generator params
      weight: float      — height proportion (default 1.0)

    Process:
      1. Generate each layer's pattern via generate_inlay_pattern()
      2. Scale each to fit (band_width / repeats) × (layer_height based on weight)
      3. Stack vertically with gap_mm ebony purfling lines between
      4. Tile horizontally for repeats, mirror alternates if flag set
      5. Add gap elements as thin rectangles (material_index for ebony)
      6. Return combined GeometryCollection
    """
```

### Compositor presets (4, matching JS)

```python
BAND_PRESETS = {
    "rosette": {
        "layers": [
            {"shape": "nested_diamond", "params": {"band_w_mm": 150}, "weight": 1},
            {"shape": "rope_border_motif", "params": {"band_w_mm": 150}, "weight": 0.5},
        ],
        "band_width_mm": 150, "band_height_mm": 25, "gap_mm": 0.5, "repeats": 4,
    },
    "body_binding": {
        "layers": [
            {"shape": "twisted_rope", "params": {"length_mm": 150}, "weight": 1},
            {"shape": "diamond", "params": {"tile_w": 8}, "weight": 0.8},
            {"shape": "twisted_rope", "params": {"length_mm": 150}, "weight": 1},
        ],
        "band_width_mm": 180, "band_height_mm": 20, "gap_mm": 0.3, "repeats": 1,
    },
    "fretboard": {
        "layers": [
            {"shape": "hex_chain", "params": {"cell_h_mm": 10}, "weight": 1},
            {"shape": "chevron_panel", "params": {"band_h_mm": 15}, "weight": 1},
        ],
        "band_width_mm": 150, "band_height_mm": 30, "gap_mm": 0.5, "repeats": 4,
    },
    "headstock": {
        "layers": [
            {"shape": "parquet_panel", "params": {"size_mm": 40}, "weight": 1},
            {"shape": "nested_diamond", "params": {"band_w_mm": 100}, "weight": 0.7},
        ],
        "band_width_mm": 120, "band_height_mm": 35, "gap_mm": 0.5, "repeats": 2,
    },
}
```

### API endpoint

Add a new endpoint or overload the existing generate endpoint:

```python
@router.post("/compose")
def compose_band_endpoint(req: ComposeBandRequest) -> InlayPatternResponse:
    """Generate a composite multi-layer band."""
```

### Files to modify

- `inlay_patterns.py` — Add `compose_band()` function + `BAND_PRESETS`
- `schemas/inlay_patterns.py` — Add `ComposeBandRequest` Pydantic model
- `api/inlay_pattern_routes.py` — Add `/compose` endpoint
- `test_inlay_patterns.py` — Tests for compositor

### Effort: Medium — the compositor logic is straightforward scaling/stacking, but the API schema needs care.

---

## Phase 4 — Material Catalogue

**What:** Port the 12-material catalogue from MATS constant.

### Current state

`inlay_geometry.py` already has a `MATERIALS` dict (used by `mat_color()`), but it
only has 4 entries. The JS source has 12 with proper names, hex colors, and grain colors.

### Expanded catalogue

```python
MATERIALS = {
    "mop":       {"name": "MOP White",    "color": "#ddeef8", "grain": "#c0d0dc"},
    "abalone":   {"name": "Abalone",      "color": "#58a87a", "grain": "#3a7858"},
    "black_mop": {"name": "Black MOP",    "color": "#28283a", "grain": "#181828"},
    "gold_mop":  {"name": "Gold MOP",     "color": "#d4a030", "grain": "#a87818"},
    "paua":      {"name": "Paua Abalone", "color": "#3858a0", "grain": "#283878"},
    "maple":     {"name": "Maple",        "color": "#eee0b0", "grain": "#d4c080"},
    "ebony":     {"name": "Ebony",        "color": "#181008", "grain": "#0c0804"},
    "rosewood":  {"name": "Rosewood",     "color": "#481c10", "grain": "#341008"},
    "koa":       {"name": "Koa",          "color": "#c07020", "grain": "#a05010"},
    "bloodwood": {"name": "Bloodwood",    "color": "#981e10", "grain": "#781208"},
    "holly":     {"name": "Holly",        "color": "#f0f0e0", "grain": "#dcdcc8"},
    "walnut":    {"name": "Walnut",       "color": "#6a3c18", "grain": "#4a2810"},
}
```

### Files to modify

- `inlay_geometry.py` — Expand `MATERIALS` dict to 12 entries, update `mat_color()`

### Effort: Trivial — data copy.

---

## Implementation Order

```
Phase 4: Materials (trivial, unblocks all material references)
  │
  ├── Phase 1: Gallery motifs (small, independent)
  │
  ├── Phase 2: Twisted rope (medium, core value)
  │     ├── 2a: Math layer (tangent/normal/arclen, strand gen, crossing split)
  │     ├── 2b: Centerline shapes (5)
  │     ├── 2c: Generator + presets
  │     └── 2d: True CNC offsets (fixes W1, W2, W5 from review)
  │
  └── Phase 3: Band compositor (medium, depends on all generators existing)
        ├── 3a: Compositor function
        ├── 3b: API endpoint + schema
        └── 3c: Presets
```

### Recommended sequence: 4 → 1 → 2a → 2b → 2c → 2d → 3a → 3b → 3c

---

## Summary of Changes Per File

| File | Phase | Changes |
|---|---|---|
| `inlay_geometry.py` | 4, 2a | Expand MATERIALS; add `compute_tangent_normal_arclen()`, `generate_strand_path()`, `split_strand_at_crossings()` |
| `inlay_patterns.py` | 1, 2c, 3a | Add 5 gallery generators, `twisted_rope()`, `compose_band()`; register all in `INLAY_GENERATORS` |
| `schemas/inlay_patterns.py` | 1, 2c, 3b | Add 6 new shapes to `InlayShape`; add `ComposeBandRequest` model |
| `api/inlay_pattern_routes.py` | 3b | Add `/compose` endpoint |
| `test_inlay_patterns.py` | 1, 2, 3 | Tests for all new generators + compositor + rope math |

### Net new generators: 6 (hex_chain, rope_border_motif, parquet_panel, chevron_panel, nested_diamond, twisted_rope)
### Net new functions: 1 compositor (`compose_band`)
### Net new math: 3 functions in geometry module
### Total `InlayShape` values after: 16 (current 10 + 6 new)

---

## Review Findings Cross-Reference

| Review Finding | Phase | How It's Fixed |
|---|---|---|
| W1: Stroke-width CNC offsets (gallery) | 1, 2d | All generators use `offset_polygon()` for true geometric offsets |
| W2: Rope pocket is `<rect>` for curved | 2d | Use `offset_polyline_strip(centerline, rope_width/2 + kerf)` |
| W3: No DXF export | — | Already solved — `inlay_export.py` has `geometry_to_dxf()` via ezdxf |
| W4: OpenSCAD export incomplete | — | Not porting — DXF covers this need |
| W5: Rope only works for straight in export | 2c | All 5 centerline shapes produce proper strand geometry |
| W6: Composer has no export | 3a | `compose_band()` returns `GeometryCollection` → SVG/DXF via existing pipeline |
| W7: No error handling in canvas drawing | 2c | Python generators validate params, raise `ValueError` for invalid inputs |
| W8: Gallery motif parser strips `<g>` wrong | 1 | Python uses pre-extracted polygon data, no regex parsing |
| F1: User cuts wrong geometry | 2d | True geometric offsets via `offset_polygon()` |
| F2: Wrong pocket for curved centerlines | 2d | `offset_polyline_strip()` follows the curve |
| F3: Strand order mismatch | 2c | Element metadata includes `strand_index` and `on_top` flag |
| S4: No DXF export | — | Already solved |

---

## Open Questions (from Review, with Recommendations)

| # | Question | Recommendation |
|---|---|---|
| Q1 | Real kerf values per material? | Default 0.10mm. Add `kerf_mm` param to all generators. Document that MOP/shell needs ~0.05mm, wood ~0.10mm, abalone ~0.08mm. |
| Q2 | OpenSCAD usage? | Don't port. DXF + SVG covers all CNC workflows. |
| Q4 | Most common centerline shape? | Implement all 5. Straight first (purfling), then S-wave (binding). |
| Q6 | Target machine profile? | Use existing `machine_profiles.json` IDs. Default min feature = 0.3mm. |
| Q7 | Non-rectangular boundaries? | Phase 3 compositor handles rectangular bands. Curved boundaries (rosette rings) deferred to v2 — would need `inlay_import.py` DXF ring extraction. |
