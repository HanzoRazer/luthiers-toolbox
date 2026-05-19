# Production Shop Tool Inventory

**Audit Date**: 2026-05-05  
**Purpose**: Catalog all standalone HTML tools, determine migration targets, identify unique logic for extraction

---

## Classification Buckets

| Bucket | Definition |
|--------|------------|
| **PROMOTE** | Production-quality, misarchived — restore to active tools |
| **PORT** | Unique logic worth extracting — port to Python/Vue |
| **PRESERVE** | Reference documentation — keep as-is |
| **SUPERSEDED** | Duplicate or older version — hash-compare before removal |
| **EXTERNAL** | Third-party tool — do not maintain |

---

## High-Priority Interactive Tools

### 1. soundhole_designer.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/soundhole_designer.html` |
| **Size** | 79.5 KB |
| **Classification** | **PROMOTE** — misarchived production code |
| **Title** | Soundhole Acoustic Calculator |
| **Scripts** | None external (all inline JS) |
| **Canvas/SVG** | Canvas-based visualization |
| **DXF/Export** | None |
| **localStorage** | None |
| **Vue Equivalent** | Partial — `soundhole_router.py` exists but lacks inverse solver and 2-cavity eigenvalue |

**Unique Formulas**:
- `Leff(a, p, t, k, g)` — effective port length with end correction
- `helmholtz(vol, ports, k, g)` — Helmholtz resonance calculator
- `twoCav()` — two-cavity eigenvalue solver for Selmer/Maccaferri
- Body volume calibration factor 1.83× (validated Martin OM, D-28, J-45)
- Plate-air coupling PMF = 0.92
- `BRAC_PRESCRIPTIONS[]` — bracing recommendation array

**Action**: Restore to `tools/` folder, port inverse solver to `soundhole_calc.py`

---

### 2. rosette-designer-v5.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/rosette_designer_history/rosette-designer-v5.html` |
| **Size** | 102.7 KB |
| **Classification** | **PORT** — latest rosette UI, valuable UX patterns |
| **Title** | Production Shop — Rosette Designer v5 |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas + SVG hybrid |
| **DXF/Export** | Yes (SVG export) |
| **localStorage** | None |
| **Vue Equivalent** | Yes — `rosette_designer_routes.py` + multiple engines |

**Unique Features**:
- Tile palette with drag-drop
- Recipe cards for saved designs
- Tab bar (Tiles / Library)
- Production Shop branding (JetBrains Mono + Playfair Display)

**Action**: Extract tile palette UX pattern for Vue Art Studio component

---

### 3. inlay_designer.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/inlay_designer.html` |
| **Size** | 185.3 KB |
| **Classification** | **PORT** — CNC layer system unique |
| **Title** | Celtic & Floral Inlay Designer |
| **Scripts** | None external |
| **Canvas/SVG** | SVG gallery + Canvas preview |
| **DXF/Export** | Yes (export functions present) |
| **localStorage** | None |
| **Vue Equivalent** | Partial — `inlay_router.py`, `inlay_geometry_*.py` exist |

**Unique Features**:
- Material assignment system (color swatches per layer)
- CNC Layers panel:
  - Centerline layer
  - Male/inlay piece offset
  - Pocket/wood cut offset
- Lock aspect ratio controls
- SVG motif gallery

**Action**: Port CNC layer offset system to `inlay_export.py`

---

### 4. amsterdam_spiro_engine.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/amsterdam_spiro_engine.html` |
| **Size** | 194.8 KB |
| **Classification** | **PORT** — spirograph geometry engine |
| **Title** | Amsterdam / Spiro Marquetry Engine |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas-based rendering |
| **DXF/Export** | Yes (export functions present) |
| **localStorage** | None |
| **Vue Equivalent** | None — unique spirograph patterns |

**Tabs**: Gallery (9), Spiro Flower, Oak Medallion, Floral Spray, Open Flower Oval

**Reference Patterns**: alma_tadema, lily_spray, etc.

**Action**: Extract spirograph geometry functions, integrate into Art Studio pattern library

---

### 5. marquetry_engine.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/marquetry_engine.html` |
| **Size** | 187.9 KB |
| **Classification** | **PORT** — full marquetry pattern system |
| **Title** | (Same as amsterdam_spiro or variant) |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas |
| **DXF/Export** | Yes |
| **localStorage** | None |
| **Vue Equivalent** | None |

**Note**: Duplicate exists at `rosette_designer_history/prototypes/premium/marquetry_engine.html`

**Action**: Hash-compare both files before consolidation

---

### 6. geo_band_generator.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/geo_band_generator.html` |
| **Size** | 72.3 KB |
| **Classification** | **PORT** — rope geometry algorithms |
| **Title** | Geometric Band & Rope Inlay Generator |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas |
| **DXF/Export** | Yes |
| **localStorage** | None |
| **Vue Equivalent** | Partial — `inlay_geometry_rope.py` exists |

**Tabs**: Pattern Gallery, Twisted Rope, Band Composer

**Unique Features**:
- Strand layer indicators for rope crossover
- Band composition system

**Action**: Verify rope crossover logic matches `inlay_geometry_rope.py`

---

### 7. vine_girih_generator.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/photo_vectorizer_patches/vine_girih_generator.html` |
| **Size** | 122.3 KB |
| **Classification** | **PORT** — Girih tessellation is unique |
| **Title** | Vine Scroll & Girih-5 Generator |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas |
| **DXF/Export** | Yes |
| **localStorage** | None |
| **Vue Equivalent** | None — no Girih implementation |

**Tabs**: Vine Motifs, Parametric Vine, Girih-5 Tessellation, Binding Flow

**Unique Features**:
- Girih-5 Islamic tessellation (5 tile types: decagon, pentagon, bowtie, rhombus, hexagon)
- Parametric vine scroll with bezier curves

**Action**: Port Girih-5 tessellation to `pattern_geometry.py`

---

### 8. headstock-designer.html

| Field | Value |
|-------|-------|
| **Path** | `archive/experimental/2026-03/Interactive_Headstock_Generator/headstock-designer.html` |
| **Size** | ~70 KB |
| **Classification** | **PORT** — Konva.js editor pattern |
| **Title** | Production Shop — Headstock Designer |
| **Scripts** | Konva.js v9 (CDN) |
| **Canvas/SVG** | Konva canvas |
| **DXF/Export** | SVG export + DXF import |
| **localStorage** | None |
| **Vue Equivalent** | Partial — `headstock_inlay_router.py` exists |

**Preset Headstocks**: Les Paul, Strat, PRS, Telecaster, SG

**Inlay Shapes**: Dot, Diamond, Block, Crown, Oval, Star, Hex, Text, Import

**Features**:
- Undo/redo history
- Snap to centerline
- Boundary lock
- Layer management
- Manufacturing info panel

**Action**: Valuable Konva.js patterns — extract for Vue headstock component

---

### 9. ps-parametric.html

| Field | Value |
|-------|-------|
| **Path** | `archive/experimental/2026-03/Interactive_Headstock_Generator/ps-parametric.html` |
| **Size** | ~70 KB |
| **Classification** | **PORT** — novelty scoring unique |
| **Title** | Production Shop — Parametric Headstock Designer |
| **Scripts** | Konva.js v9 (CDN) |
| **Canvas/SVG** | Konva canvas |
| **DXF/Export** | SVG export |
| **localStorage** | None |
| **Vue Equivalent** | None |

**Unique Features**:
- **Novelty meter** — scores design originality
- **Corpus distance** — proximity to known headstock shapes
- **Manufacture gates** — pass/fail indicators
- Tip style selector (4 options)
- Tuner pattern selector
- Paid tier badge

**Action**: Port novelty scoring + corpus distance algorithms

---

### 10. rope_rosette_engine.html

| Field | Value |
|-------|-------|
| **Path** | `docs/archive/rosette_designer_history/prototypes/premium/rope_rosette_engine.html` |
| **Size** | ~4.8 MB (large — contains embedded SVG patterns) |
| **Classification** | **PORT** — polar warp renderer unique |
| **Title** | Rope & Inlay Rosette Engine |
| **Scripts** | None external |
| **Canvas/SVG** | Canvas + embedded SVG vector patterns |
| **DXF/Export** | Vector export |
| **localStorage** | None |
| **Vue Equivalent** | Partial — `rope_twist_rosette.py` exists |

**Tabs**: Gallery (12), Rosette Builder, Band/Binding

**Features**:
- 6 vector patterns (recolorable)
- 6 photo patterns
- Polar Warp Renderer
- Ring layer management
- Color swatch assignment

**Action**: Extract polar warp renderer algorithm

---

## Reference Documentation (PRESERVE)

These are styled technical documents, not interactive tools.

| File | Size | Topic |
|------|------|-------|
| `bridge_geometry_path_pack.html` | 41.1 KB | Bridge geometry reference |
| `fret_wire_path_pack.html` | 40.0 KB | Fret wire selection guide |
| `neck_block_path_pack.html` | 30.8 KB | Neck/tail block sizing |
| `nut_compensation_path_pack.html` | 26.5 KB | Nut compensation physics |

**Note**: Beautiful Production Shop documentation styling — preserve for brand consistency reference.

---

## External Tools (EXTERNAL)

| File | Size | Source |
|------|------|--------|
| `Kerf Spacing Calculator Bending Wood - Inch.html` | 144.4 KB | blocklayer.com |

**Contains**: Google Ads scripts, external CSS, not Production Shop branding.

**Action**: Remove from repository — not our code, not maintainable.

---

## Duplicates to Hash-Compare

| File A | File B |
|--------|--------|
| `photo_vectorizer_patches/marquetry_engine.html` | `rosette_designer_history/prototypes/premium/marquetry_engine.html` |

**Action**: Run SHA256 comparison before any deletion.

---

## Junk Files (DELETE CANDIDATES)

Located in `docs/archive/photo_vectorizer_patches/`:

| Pattern | Count | Description |
|---------|-------|-------------|
| `saved_resource*.html` | 9 | Empty/minimal Chrome save artifacts |
| `s.html`, `s(1).html`, `s(2).html` | 3 | 0.2 KB each — empty |
| `ads.html`, `ads(1).html`, `ads(2).html` | 3 | Saved ad pages |
| `zrt_lookup_fy2021*.html` | 3 | Tax lookup pages — unrelated |
| `aframe.html` | 1 | A-Frame VR test — unrelated |
| `index.html` | 1 | Empty index |

**Action**: Delete after verifying no unique content.

---

## Backend Coverage Summary

**Extensive backend implementations exist for**:
- Rosette: 30+ files (`rosette_*.py`, `rope_twist_rosette.py`, etc.)
- Inlay: 15+ files (`inlay_*.py`, `celtic_parametric_knots.py`, etc.)
- Soundhole: 10+ files (`soundhole_*.py`, `spiral_geometry.py`)
- Headstock: 5+ files (`headstock_*.py`, `neck_headstock_*.py`)

**Missing from backend**:
- Two-cavity eigenvalue solver (in soundhole_designer.html)
- Inverse Helmholtz solver (in soundhole_designer.html)
- Girih-5 tessellation (in vine_girih_generator.html)
- Novelty scoring + corpus distance (in ps-parametric.html)
- Polar warp renderer (in rope_rosette_engine.html)
- Full spirograph geometry (in amsterdam_spiro_engine.html)

---

## Extraction Priority

### Phase 1: Critical Physics (Week 1)
1. `soundhole_designer.html` → Port `twoCav()` eigenvalue solver to `coupled_2osc.py`
2. `soundhole_designer.html` → Port inverse solver to `soundhole_calc.py`
3. `soundhole_designer.html` → Restore to active tools folder

### Phase 2: Pattern Geometry (Week 2)
4. `vine_girih_generator.html` → Port Girih-5 to `pattern_geometry.py`
5. `amsterdam_spiro_engine.html` → Port spirograph engine
6. `geo_band_generator.html` → Verify rope crossover vs `inlay_geometry_rope.py`

### Phase 3: Manufacturing Features (Week 3)
7. `inlay_designer.html` → Port CNC layer offsets to `inlay_export.py`
8. `ps-parametric.html` → Port novelty scorer to headstock validation
9. `rope_rosette_engine.html` → Port polar warp renderer

### Phase 4: UX Patterns (Week 4)
10. `rosette-designer-v5.html` → Extract tile palette for Vue
11. `headstock-designer.html` → Extract Konva.js patterns for Vue

---

## Notes

- **DO NOT DELETE** any file until SHA256 hash comparison is complete
- **DO NOT DELETE** any file with unique formulas not yet ported
- Path packs are valuable brand reference — preserve styling
- External tools (blocklayer.com) should be removed — not ours to maintain
