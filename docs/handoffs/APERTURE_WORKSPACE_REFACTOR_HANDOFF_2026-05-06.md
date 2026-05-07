# Aperture Workspace Refactor — Developer Handoff

**Date**: 2026-05-06  
**Status**: Track A in progress — spiral math COMPLETE, architecture design APPROVED  
**Priority**: HIGH — blocks frontend consolidation and acoustic feature parity  
**Depends on**: Neck Studio architecture (reference model)

---

## Executive Summary

This handoff documents the refactoring of the spiral soundhole tool into a unified **Aperture System Workspace**. The spiral becomes one aperture family among several, not the entire tool. This architectural shift aligns with the Neck Studio pattern and enables future aperture types without duplicating infrastructure.

**Critical fix applied**: Spiral arc length formula corrected in 4 files. Previous formula underestimated path length by factor of ~5.5×.

---

## 1. Spiral Math Fix — COMPLETE

### 1.1 The Bug

**Old formula** (incorrect):
```python
alpha = math.atan(1.0 / k)
one_wall = (r_end - r0) / math.sin(alpha)
```

This simplifies to `sqrt(1 + k²) × (r_end - r0)`, missing the `/k` divisor.

**Correct formula**:
```
L = sqrt(1 + k²) / k × (r_end - r0)
```

For k → 0 (near-circular):
```
L = r0 × θ_end
```

### 1.2 Files Fixed

| File | Location | Status |
|------|----------|--------|
| `spiral_geometry.py` | `services/api/app/instrument_geometry/soundhole/` | FIXED |
| `soundhole_calc.py` | `services/api/app/calculators/` | FIXED |
| `soundhole_facade.py` | `services/api/app/calculators/` | FIXED |
| `SpiralSoundholeDesigner.vue` | `packages/client/src/components/toolbox/acoustics/` | FIXED |

### 1.3 Corrected Carlos Jumbo Metrics

| Metric | Old (wrong) | Corrected | Impact |
|--------|-------------|-----------|--------|
| Arc length per spiral | ~25 mm | 139.4 mm | 5.5× increase |
| Area per spiral | ~350 mm² | 1951.8 mm² | 5.5× increase |
| Total dual-spiral area | ~700 mm² | 3903.5 mm² | 5.5× increase |
| vs 4" round hole | ~35% | 192.6% | Now exceeds round hole |
| P:A ratio | 0.143 mm⁻¹ | 0.143 mm⁻¹ | Unchanged (2/slot_width) |

### 1.4 New Helper Function

Added to `spiral_geometry.py`:

```python
def _spiral_arc_length(r0: float, r_end: float, k: float, theta_end: float) -> float:
    """
    Compute arc length of logarithmic spiral r(θ) = r0 * e^(kθ).
    
    Correct formula: L = sqrt(1 + k²) / k × (r_end - r0)
    
    For k → 0 (near-circular spiral), falls back to circular arc: L = r0 × θ
    """
    if abs(k) < 1e-6:
        return r0 * theta_end
    return math.sqrt(1.0 + k * k) / k * (r_end - r0)
```

### 1.5 Regression Tests

New test file: `services/api/tests/test_soundhole_spiral.py`

15 tests covering:
- Known-value arc length verification
- Factor verification (sqrt(1+k²)/k)
- Near-circular fallback (k→0)
- Carlos preset metrics
- P:A ratio invariance
- Edge cases (zero turns, small k, offset center)

All tests pass.

---

## 2. Aperture Reframing

### 2.1 Vocabulary Change

**Remove or demote**:
```
spiral = tornavoz substitute
```

**Use instead**:
```
spiral = candidate replacement aperture
tornavoz = optional compensation layer (modifier)
```

### 2.2 Concept Rename

| Old | New |
|-----|-----|
| Spiral Soundhole Designer | Aperture System Workspace |
| soundhole type | aperture family |
| spiral params | aperture-specific params |

### 2.3 Implemented Aperture Families

```
round    — traditional circular
oval     — Selmer/Maccaferri elliptical
f-hole   — archtop f-holes
spiral   — logarithmic spiral slot
```

### 2.4 Roadmap Aperture Families (NOT YET IMPLEMENTED)

```
D-hole       — Django/gypsy jazz
duck-head    — Tacoma papoose variant
trapezoid    — custom shapes
side-port    — secondary ports
slot-port    — linear slots
```

Do NOT expose these in UI or API until geometry + tests exist.

---

## 3. ApertureGeometry — Common Output Model

### 3.1 Location

Create: `services/api/app/calculators/aperture_geometry.py`

### 3.2 Schema

```python
from dataclasses import dataclass
from typing import Literal

ApertureType = Literal["round", "oval", "fhole", "spiral"]

@dataclass
class ApertureGeometry:
    """
    Common output model for all aperture types.
    
    Produced by type-specific calculators, consumed by:
    - Helmholtz solver
    - Inverse solver
    - Manufacturing risk assessment
    - Frontend comparison panels
    """
    aperture_type: ApertureType
    area_mm2: float
    perimeter_mm: float
    equivalent_diameter_mm: float
    characteristic_width_mm: float | None = None  # slot_width for spiral
    path_length_mm: float | None = None           # arc length for spiral
    pa_ratio_mm_inv: float | None = None          # P/A ratio
    
    # Extended metrics for acoustic modeling
    effective_length_mm: float | None = None      # L_eff for Helmholtz
    loss_estimate: float | None = None            # R_loss
    
    @property
    def is_slot_type(self) -> bool:
        """True for apertures where P:A matters (spiral, slot-port)."""
        return self.aperture_type in ("spiral", "slot_port")
```

### 3.3 Type-Specific Params (Unchanged)

Each aperture type keeps its own params dataclass:

```python
# Already exists
@dataclass
class SpiralParams:
    slot_width_mm: float = 14.0
    start_radius_mm: float = 10.0
    growth_rate_k: float = 0.18
    turns: float = 1.1
    rotation_deg: float = 0.0
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0

# Add similar for others
@dataclass
class OvalParams:
    major_axis_mm: float
    minor_axis_mm: float
    center_x_mm: float = 0.0
    center_y_mm: float = 0.0
    rotation_deg: float = 0.0

@dataclass
class FHoleParams:
    length_mm: float
    waist_width_mm: float
    # ... f-hole specific geometry
```

### 3.4 Relationship

```
SpiralParams  ─┐
OvalParams    ─┼─► compute_geometry() ─► ApertureGeometry
FHoleParams   ─┤
RoundParams   ─┘
```

Type-specific params are input; `ApertureGeometry` is normalized output.

---

## 4. Tornavoz as Modifier

### 4.1 Schema

```python
@dataclass
class TornavozAttachment:
    """
    Optional compensation layer applied to ANY aperture.
    Not an aperture type itself.
    """
    length_mm: float
    inner_diameter_mm: float
    flare_angle_deg: float = 0.0
    loss_factor: float = 1.0
    
    @property
    def effective_length_mm(self) -> float:
        """Acoustic effective length including end correction."""
        return self.length_mm + 0.85 * (self.inner_diameter_mm / 2)
```

### 4.2 Application

```python
def combine_aperture_with_tornavoz(
    aperture: ApertureGeometry,
    tornavoz: TornavozAttachment | None
) -> ApertureGeometry:
    """
    Modify aperture effective length when tornavoz is attached.
    """
    if tornavoz is None:
        return aperture
    
    combined = ApertureGeometry(
        aperture_type=aperture.aperture_type,
        area_mm2=aperture.area_mm2,
        perimeter_mm=aperture.perimeter_mm,
        equivalent_diameter_mm=aperture.equivalent_diameter_mm,
        characteristic_width_mm=aperture.characteristic_width_mm,
        path_length_mm=aperture.path_length_mm,
        pa_ratio_mm_inv=aperture.pa_ratio_mm_inv,
        effective_length_mm=(
            (aperture.effective_length_mm or 0) + tornavoz.effective_length_mm
        ),
        loss_estimate=aperture.loss_estimate,
    )
    return combined
```

---

## 5. API Compatibility Strategy

### 5.1 Existing Endpoints — DO NOT BREAK

| Endpoint | Status |
|----------|--------|
| `POST /api/instrument/soundhole` | Keep unchanged |
| `GET /api/instrument/soundhole/types` | Keep unchanged |
| `GET /api/instrument/soundhole/spiral/default` | Keep unchanged |
| `POST /api/instrument/soundhole/spiral/geometry` | Keep unchanged |
| `POST /api/instrument/soundhole/spiral/dxf` | Keep unchanged |
| `POST /api/instrument/soundhole/spiral/validate` | Keep unchanged |

### 5.2 Non-Breaking Additions

Add `aperture_geometry` field to responses:

```json
{
  "soundhole_type": "spiral",
  "diameter_mm": 49.8,
  "area_mm2": 1951.8,
  "perimeter_mm": 278.8,
  "pa_ratio_mm_inv": 0.1429,
  
  "aperture_geometry": {
    "aperture_type": "spiral",
    "area_mm2": 1951.8,
    "perimeter_mm": 278.8,
    "equivalent_diameter_mm": 49.8,
    "characteristic_width_mm": 14.0,
    "path_length_mm": 139.4,
    "pa_ratio_mm_inv": 0.1429
  }
}
```

Existing clients ignore new fields; new clients can use structured output.

### 5.3 Types Endpoint — Only Return Implemented

`GET /api/instrument/soundhole/types` should return:

```json
{
  "types": ["round", "oval", "fhole", "spiral"],
  "default": "round"
}
```

Do NOT return `D-hole`, `duck-head`, `trapezoid`, `side-port`, `slot-port` until implemented.

---

## 6. Inverse Solver Extraction

### 6.1 Source Comparison Required

| Feature | `soundhole_calc.py` | `soundhole_designer.html` |
|---------|---------------------|---------------------------|
| Basic Helmholtz | Yes | Yes |
| Inverse diameter | Partial | Yes |
| Two-cavity eigenvalue | No | Yes (`twoCav()`) |
| Body volume calibration | No | Yes (1.83×) |
| PMF coupling factor | No | Yes (0.92) |
| Bracing prescriptions | No | Yes (`BRAC_PRESCRIPTIONS[]`) |

### 6.2 Extraction Steps

1. Read `soundhole_designer.html` functions:
   - `Leff(a, p, t, k, g)` — effective length
   - `helmholtz(vol, ports, k, g)` — forward Helmholtz
   - `twoCav()` — two-cavity eigenvalue solver

2. Compare against `soundhole_calc.py` implementations

3. Port missing/better implementations to:
   - `soundhole_calc.py` — inverse solver additions
   - `coupled_2osc.py` — two-cavity eigenvalue

4. Add regression tests with known guitar measurements

### 6.3 Calibration Constants

From `soundhole_designer.html`:

```javascript
const BODY_VOL_FACTOR = 1.83;  // Validated against Martin OM, D-28, J-45
const PMF = 0.92;              // Plate-air coupling factor
```

These should be configurable, not hardcoded.

---

## 7. Frontend Architecture — Align with Neck Studio

### 7.1 Reference Pattern

Neck Studio uses:
```
NeckStudioView.vue
├── NeckWorkspace.vue (layout container)
├── NeckParameterPanel.vue
├── NeckPreviewCanvas.vue
├── NeckExportPanel.vue
└── shared/
    ├── SliderInput.vue
    ├── PresetDropdown.vue
    └── ExportButton.vue
```

### 7.2 Target Aperture Structure

```
ApertureStudioView.vue
├── ApertureWorkspace.vue (layout container)
├── panels/
│   ├── ApertureTypeSelector.vue      (round/oval/fhole/spiral dropdown)
│   ├── RoundOvalPanel.vue            (simple diameter/axes controls)
│   ├── SpiralAperturePanel.vue       (k, turns, slot_width, rotation)
│   ├── FHolePanel.vue                (f-hole specific controls)
│   ├── TornavozModifierPanel.vue     (optional attachment)
│   ├── ApertureComparisonPanel.vue   (side-by-side metrics)
│   └── InverseSolverPanel.vue        (target f_H → aperture params)
├── AperturePreviewCanvas.vue
├── ApertureExportPanel.vue
└── shared/ (reuse from Neck Studio)
```

### 7.3 Absorb Existing Component

`SpiralSoundholeDesigner.vue` → refactor into `SpiralAperturePanel.vue`

Do NOT delete. Preserve existing functionality as one panel within the workspace.

### 7.4 Shared Components

Reuse from Neck Studio where possible:
- `SliderInput.vue` — numeric sliders with units
- `PresetDropdown.vue` — preset selection
- `ExportButton.vue` — DXF/SVG export triggers
- `ValidationBadge.vue` — pass/warn/fail indicators

---

## 8. Misarchived Asset Recovery

### 8.1 Priority Recoveries

| File | Location | Action |
|------|----------|--------|
| `soundhole_designer.html` | `docs/archive/photo_vectorizer_patches/` | PROMOTE — restore to active tools |

Contains inverse solver and two-cavity logic not in Vue/API.

### 8.2 Port Candidates (from TOOL_INVENTORY.md)

| File | Unique Logic | Target |
|------|--------------|--------|
| `vine_girih_generator.html` | Girih-5 tessellation | `pattern_geometry.py` |
| `amsterdam_spiro_engine.html` | Spirograph geometry | Art Studio patterns |
| `ps-parametric.html` | Novelty scoring, corpus distance | Headstock validation |
| `rope_rosette_engine.html` | Polar warp renderer | Rosette engine |
| `inlay_designer.html` | CNC layer offset system | `inlay_export.py` |

### 8.3 External Tool — Remove

`Kerf Spacing Calculator Bending Wood - Inch.html` — blocklayer.com external tool, not Production Shop code.

---

## 9. Documentation Updates Required

### 9.1 Files Needing Vocabulary Update

| File | Change |
|------|--------|
| `SPIRAL_SOUNDHOLE_EXECUTIVE_SUMMARY.md` | Reframe as aperture system |
| `SPIRAL_SOUNDHOLE_DEVELOPER_HANDOFF.md` | Reframe vocabulary |
| `SPIRAL_SOUNDHOLE_INVERSE_CALIBRATION_HANDOFF.md` | Reframe vocabulary |
| API docstrings | Update aperture language |
| Frontend tooltips | Update user-facing text |

### 9.2 Key Vocabulary Changes

| Old | New |
|-----|-----|
| "spiral soundhole designer" | "aperture workspace" |
| "spiral = tornavoz substitute" | "spiral = aperture option; tornavoz = modifier" |
| "soundhole type" | "aperture family" |
| "equivalent diameter" | "equivalent diameter (for compatibility)" |

---

## 10. Execution Order — Dependency Graph

```
[1] Freeze deletion/moves ─────────────────────────────────────────┐
                                                                   │
[2] Fix spiral math ──────────────────────────────── COMPLETE ◄────┤
    └─► regression tests                             COMPLETE      │
                                                                   │
[3] Define ApertureGeometry ───────────────────────────────────────┤
    └─► aperture_geometry.py                                       │
    └─► TornavozAttachment                                         │
                                                                   │
[4] Add aperture_geometry to API responses ────────────────────────┤
    └─► non-breaking additions                                     │
    └─► preserve existing fields                                   │
                                                                   │
[5] Update docs/vocabulary ────────────────────────────────────────┤
    └─► handoffs                                                   │
    └─► API docstrings                                             │
    └─► frontend tooltips                                          │
                                                                   │
[6] Compare soundhole_calc.py vs soundhole_designer.html ──────────┤
    └─► diff Leff, helmholtz, twoCav                               │
    └─► port missing implementations                               │
                                                                   │
[7] Vue workspace consolidation ───────────────────────────────────┤
    └─► ApertureWorkspace.vue                                      │
    └─► absorb SpiralSoundholeDesigner.vue                         │
    └─► align with Neck Studio pattern                             │
                                                                   │
[8] Archive cleanup ───────────────────────────────────────────────┘
    └─► hash-compare duplicates
    └─► delete confirmed junk
    └─► preserve reference docs
```

---

## 11. Acceptance Criteria

### 11.1 Math Fix (DONE)

- [x] Arc length formula corrected in all 4 files
- [x] k→0 fallback implemented
- [x] Carlos preset metrics recalculated
- [x] Regression tests pass (15/15)

### 11.2 ApertureGeometry

- [ ] `aperture_geometry.py` created
- [ ] `ApertureGeometry` dataclass defined
- [ ] `TornavozAttachment` dataclass defined
- [ ] Type-specific params produce `ApertureGeometry` output

### 11.3 API Compatibility

- [ ] Existing endpoints unchanged
- [ ] `aperture_geometry` field added to responses
- [ ] Types endpoint returns only implemented types

### 11.4 Inverse Solver

- [ ] `soundhole_designer.html` formulas extracted
- [ ] `twoCav()` ported to `coupled_2osc.py`
- [ ] Inverse solver tests pass

### 11.5 Frontend

- [ ] `ApertureWorkspace.vue` created
- [ ] `SpiralAperturePanel.vue` extracted from existing component
- [ ] Shared components reused from Neck Studio
- [ ] Aperture type selector functional

### 11.6 Documentation

- [ ] Vocabulary updated in handoffs
- [ ] API docstrings updated
- [ ] Frontend tooltips updated

---

## 12. Files Modified This Session

| File | Change |
|------|--------|
| `spiral_geometry.py` | Corrected arc length formula, added `_spiral_arc_length()` |
| `soundhole_calc.py` | Corrected arc length formula |
| `soundhole_facade.py` | Corrected arc length formula |
| `SpiralSoundholeDesigner.vue` | Corrected arc length formula |
| `test_soundhole_spiral.py` | New regression test suite (15 tests) |
| `TOOL_INVENTORY.md` | New — comprehensive HTML tool audit |

---

## 13. Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/TOOL_INVENTORY.md` | HTML tool audit and migration plan |
| `docs/handoffs/SOUNDHOLE_DESIGNER_HTML_REFACTOR_HANDOFF_2026-05-05.md` | Spiral geometry integration plan |
| `docs/handoffs/SPIRAL_SOUNDHOLE_EXECUTIVE_SUMMARY_2026-05-03.md` | Acoustic system spec |
| `CLAUDE.md` | Project instructions, soundhole type system |

---

## 14. Contact

**Git branch**: `fix/wood-shrinkage-data-integrity` (or create new `feature/aperture-workspace`)  
**Primary files**: `spiral_geometry.py`, `soundhole_facade.py`, `SpiralSoundholeDesigner.vue`  
**Test command**: `cd services/api && pytest tests/test_soundhole_spiral.py -v`

---

*This handoff documents Track A (Refactoring + Reframing) of the aperture system consolidation. Track B (Documentation Reframe) and Track C (Recovery + Extraction) follow after Track A stabilizes.*

---

## Appendix A: Verified Implementation Guidance (Q1–Q9)

The following Q&A was verified against the extracted `luthiers-toolbox-main` archive. It separates **confirmed repo facts** from **recommended architecture** and served as the authoritative guidance for this implementation.

---

### Q1 — Current spiral math location

Primary locations using the current spiral path-length formula:

```text
services/api/app/instrument_geometry/soundhole/spiral_geometry.py
services/api/app/calculators/soundhole_facade.py
services/api/app/calculators/soundhole_calc.py
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

The developer handoff identifies `spiral_geometry.py` as the geometry engine, `soundhole_facade.py` as the facade layer, and `soundhole_calc.py` as the Helmholtz calculator.

**Current formula found in code** (incorrect):

```python
alpha = math.atan(1.0 / k)
one_wall = (r_end - r0) / math.sin(alpha)
```

**Correct formula** for r(θ) = r₀e^(kθ):

```
L_path = sqrt(1 + k²) / k × (r₁ - r₀)
```

with fallback:

```
L_path = r₀θ  when k → 0
```

The archived `soundhole_designer.html` contains inverse Helmholtz and two-cavity logic that should be extracted separately.

---

### Q2 — Frontend existence

**Confirmed**: Vue frontend exists in this repo.

```text
packages/client/src/views/art-studio/SoundholeDesignerView.vue
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

Track A is **refactor existing Vue**, not build from scratch.

The active Vue and archived HTML are not feature-equivalent. `soundhole_designer.html` has inverse solver and two-cavity eigenvalue features missing from current Vue/API.

---

### Q3 — ApertureGeometry placement

**Recommended**: Create new shared output model, do NOT replace spiral params.

Location:
```text
services/api/app/calculators/aperture_geometry.py
```

Structure:
```python
@dataclass
class ApertureGeometry:
    aperture_type: str
    area_mm2: float
    perimeter_mm: float
    equivalent_diameter_mm: float
    characteristic_width_mm: float | None = None
    path_length_mm: float | None = None
    pa_ratio_mm_inv: float | None = None
```

Each aperture type keeps its own params (`RoundParams`, `OvalParams`, `FHoleParams`, `SpiralParams`) and produces generic `ApertureGeometry`.

**Rule**: specific params → generic geometry output

---

### Q4 — Equivalent diameter validity

**Use equivalent diameter for**:
- Quick UI preview
- Legacy API compatibility
- Rough round-hole comparison
- Position/clearance checks expecting circular diameter
- Backwards-compatible Helmholtz estimates

**Use full aperture tuple for**:
- Inverse solver
- Acoustic comparison
- Loss estimation
- Effective length
- Manufacturing risk
- Non-round aperture comparison
- F-hole / spiral / oval behavior

Full tuple: A, P, P/√A, L_eff, R_loss, Q

Equivalent diameter preserves area only:
```
d_eq = 2√(A/π)
```

It does NOT preserve perimeter, edge loss, slot behavior, or structural penalty.

---

### Q5 — Carlos presets

Preset **parameters** are not necessarily wrong.

What is wrong: **derived metrics** calculated from them:
- area
- perimeter
- total_length
- area ratio vs 4-inch round
- equivalent diameter
- acoustic f_H predictions

Carlos defaults:
```
start_radius_mm = 10.0
growth_rate_k = 0.18
turns = 1.1
slot_width_mm = 14.0
```

**Rule**: Do not change preset inputs first. Recompute outputs first.

---

### Q6 — Breaking changes

Do NOT make breaking API changes in Track A.

**Preserve**:
```
POST /api/instrument/soundhole
GET /api/instrument/soundhole/types
GET /api/instrument/soundhole/spiral/default
POST /api/instrument/soundhole/spiral/geometry
POST /api/instrument/soundhole/spiral/dxf
POST /api/instrument/soundhole/spiral/validate
```

**API strategy**:
1. Keep existing response fields
2. Add non-breaking `aperture_geometry` field
3. `GET /soundhole/types` returns only implemented types: round, oval, fhole, spiral
4. Do NOT return D-hole, duck-head, trapezoid, side-port, slot-port until implemented

---

### Q7 — Tornavoz placement

Tornavoz is a **modifier**, not an aperture type.

```python
@dataclass
class TornavozAttachment:
    length_mm: float
    flare_angle_deg: float = 0.0
    loss_factor: float = 1.0
```

Applied to any aperture:
```python
effective_length_total = aperture.effective_length + tornavoz.effective_length
```

Do NOT put tornavoz parameters inside `SpiralParams`.
Do NOT add `TORNAVOZ` to `SoundholeType`.

**Rule**: aperture first, compensation second

---

### Q8 — Inverse solver source

**Two relevant sources**:

1. `soundhole_calc.py` — has some inverse/multi-port acoustic math
2. `soundhole_designer.html` — contains additional formulas:
   - `Leff()`
   - `helmholtz()`
   - `twoCav()`
   - body volume calibration factor 1.83×
   - PMF = 0.92

**Action**: Compare before porting. Diff formulas first:
- Leff
- helmholtz
- inverse diameter/area
- multi-port
- two-cavity
- PMF
- volume calibration

Port only missing or better-tested pieces.

---

### Q9 — Dependency order inside Track A

```
A1 Freeze destructive actions
   └─ must happen first

A2 Fix spiral math                          ← COMPLETE
   ├─ can run immediately after A1
   ├─ prerequisite for recalculating presets
   └─ prerequisite for trustworthy acoustic comparison

A3 Define aperture vocabulary
   ├─ can run in parallel with A2
   └─ prerequisite for docs and UI language

A4 Create common ApertureGeometry output
   ├─ depends on A3
   ├─ should follow A2 to avoid encoding wrong metrics
   └─ prerequisite for frontend consolidation

A5 Reframe inverse solver
   ├─ depends on A3
   ├─ can run in parallel with A4
   └─ should not depend on Vue work

A6 Frontend workspace consolidation
   ├─ depends on A3 and A4
   ├─ should happen after math fix lands
   └─ should absorb SpiralSoundholeDesigner.vue, not delete it
```

**Practical execution order**:
1. Freeze deletion/moves
2. Fix spiral path-length formula in all four places ← COMPLETE
3. Add regression tests for corrected formula ← COMPLETE
4. Recompute Carlos derived metrics ← COMPLETE
5. Define `ApertureGeometry`
6. Add `aperture_geometry` to responses (non-breaking)
7. Update docs/language
8. Compare `soundhole_calc.py` vs `soundhole_designer.html`
9. Begin Vue consolidation

This order minimizes rework.

---

*End of Appendix A*
