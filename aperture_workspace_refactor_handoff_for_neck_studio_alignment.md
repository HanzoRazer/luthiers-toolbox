# Aperture Workspace Refactor — Architectural Handoff

**Project:** Luthiers Toolbox  
**Related Sprint:** Neck Generation Studio Refactor  
**Status:** Track A partially complete (spiral math corrected)  
**Purpose:** Align the Aperture/Soundhole refactor with the stabilized Neck Studio architecture so both systems share the same frontend and generator framework.

---

# 1. Executive Summary

The soundhole/spiral subsystem is undergoing a major reframing.

The original architecture treated the spiral system primarily as:

> a standalone spiral soundhole generator.

The new architecture reframes the subsystem as:

\[
\boxed{
\text{Aperture System Workspace}
}
\]

where the spiral aperture is one member of a broader aperture family.

Implemented aperture families currently include:

- round
- oval
- f-hole
- spiral

Future aperture families (not yet implemented):

- D-hole
- Tacoma-style duck-head
- trapezoid
- side-port
- slot-port

The frontend consolidation work should align with the Neck Studio architecture rather than creating a parallel UI framework.

---

# 2. Current State of the Soundhole/Aperture Refactor

## Completed

### Spiral math correction (critical)

The logarithmic spiral path-length formula was corrected in:

```text
services/api/app/instrument_geometry/soundhole/spiral_geometry.py
services/api/app/calculators/soundhole_calc.py
services/api/app/calculators/soundhole_facade.py
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

Old (incorrect):

\[
L \approx \frac{r_1-r_0}{\sin(\arctan(1/k))}
\]

Corrected:

\[
\boxed{
L_{path} = \frac{\sqrt{1+k^2}}{k}(r_1-r_0)
}
\]

Regression tests:

```text
15 tests passing in test_soundhole_spiral.py
```

### Impact of correction

Carlos Jumbo default spiral metrics changed significantly:

| Metric | Old | Corrected |
|---|---:|---:|
| Arc length | ~25 mm | 139.4 mm |
| Area per spiral | ~350 mm² | 1951.8 mm² |
| Total dual area | ~700 mm² | 3903.5 mm² |
| vs 4" round | ~35% | 192.6% |

This means the current Carlos defaults should now be treated as:

\[
\boxed{
\text{experimental high-area apertures}
}
\]

rather than direct equivalents to conventional soundholes.

---

# 3. Reframing Objectives

The architecture is changing from:

```text
spiral generator
```

to:

```text
aperture-system identification and comparison workspace
```

The system now supports two workflows:

## Forward Design Workflow

\[
\text{geometry} \rightarrow f_H,Q,\text{ area/perimeter estimates}
\]

Purpose:

- geometry design
- DXF export
- area/perimeter analysis
- candidate aperture creation

## Inverse Calibration Workflow

\[
\text{measured } f_H,Q \rightarrow L_{eff},R_{loss},\alpha,\beta
\]

Purpose:

- infer acoustic behavior from measurements
- compare aperture families
- calibrate acoustic models
- connect to tap_tone_pi measurements

---

# 4. Relationship to tap_tone_pi

The analyzer repo (`tap_tone_pi`) remains:

\[
\boxed{
\text{measurement-only infrastructure}
}
\]

Responsibilities:

- FFT
- Q estimation
- transfer functions
- coherence
- viewer pack export
- metadata capture

The aperture workspace belongs in:

```text
luthiers-toolbox
```

Responsibilities:

- geometry
- acoustic modeling
- inverse solving
- comparison
- export
- design workflows

The analyzer should NOT contain geometry optimization logic.

---

# 5. Alignment Requirement with Neck Studio

The Neck Studio sprint has stabilized and should now define the canonical frontend architecture.

The Aperture Workspace should NOT create:

- a separate generator shell
- a separate parameter architecture
- a separate export workflow
- a separate route hierarchy
- a separate canvas abstraction

Instead, it should inherit or align with the Neck Studio framework.

---

# 6. Expected Shared Frontend Architecture

The following patterns from Neck Studio should become canonical across the Art Studio domain.

## Shared Workspace Shell

Recommended:

```text
ArtStudioWorkspace.vue
```

Shared features:

- tool registry
- parameter sidebar
- preview canvas
- export drawer
- presets
- save/load state
- measurement import

---

## Shared UI Components

Expected reusable components:

```text
GeneratorShell.vue
ParameterPanel.vue
CanvasPreview.vue
ExportDrawer.vue
PresetSelector.vue
MeasurementImportPanel.vue
```

The Aperture Workspace should use these patterns instead of creating custom standalone implementations.

---

## Shared Tool Registry

Recommended:

```ts
ToolRegistry
```

Each workspace tool should register:

```ts
{
  id,
  category,
  route,
  icon,
  status,
  implementation,
  presets,
  exportCapabilities
}
```

The aperture system should integrate into the same registry model.

---

# 7. Aperture Workspace Structure

## Proposed Workspace

```text
ApertureDesignerWorkspace.vue
```

Subpanels:

```text
RoundOvalFholePanel.vue
SpiralAperturePanel.vue
ApertureComparisonPanel.vue
InverseSolverPanel.vue
MeasurementCalibrationPanel.vue
```

The existing:

```text
SpiralSoundholeDesigner.vue
```

should be absorbed into this workspace as the spiral-specific panel.

It should NOT remain the top-level conceptual object.

---

# 8. Aperture Geometry Model

## New Shared Output Model

Recommended file:

```text
services/api/app/instrument_geometry/soundhole/aperture_geometry.py
```

Recommended dataclass:

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

---

## Important architectural rule

Do NOT replace:

```python
SpiralParams
RoundParams
OvalParams
FHoleParams
```

Instead:

\[
\boxed{
\text{specific params} \rightarrow \text{generic aperture geometry}
}
\]

Each aperture family produces a normalized geometry output.

---

# 9. Equivalent Diameter Guidance

Equivalent diameter remains useful for:

- backwards compatibility
- quick UI preview
- rough Helmholtz estimation
- circular clearance assumptions

But the new acoustic framework must preserve:

\[
A,\quad P,\quad P/\sqrt{A},\quad L_{eff},\quad R_{loss},\quad Q
\]

especially for:

- spiral
- oval
- f-hole

Do NOT reduce non-round apertures to equivalent diameter too early in the solver chain.

---

# 10. Tornavoz Reframing

The previous framing incorrectly drifted toward:

```text
a spiral as a tornavoz substitute
```

The corrected framing is:

```text
spiral = candidate replacement aperture
tornavoz = optional compensation layer
```

Tornavoz should NOT be an aperture type.

Recommended structure:

```python
@dataclass
class TornavozAttachment:
    length_mm: float
    flare_angle_deg: float = 0.0
    loss_factor: float = 1.0
```

Applied as a modifier:

\[
Z_{total}=Z_{aperture}+Z_{tornavoz}
\]

---

# 11. Existing Misarchived Assets

A parallel audit identified several archived HTML files containing production-quality logic.

Highest-priority promoted asset:

```text
soundhole_designer.html
```

Contains:

- inverse Helmholtz solver
- two-cavity Selmer/Maccaferri solver
- body volume calibration
- Leff calculations
- PMF logic

This logic is NOT fully represented in the active Vue/API layer.

Do NOT delete or supersede until extraction parity exists.

---

# 12. Required Extraction Work

## Critical acoustics

Extract into:

```text
services/api/app/calculators/aperture_inverse_solver.py
services/api/app/calculators/two_cavity_solver.py
```

Compare first against:

```text
soundhole_calc.py
```

before merging formulas.

---

# 13. API Guidance

## Preserve existing API contracts

Do NOT break:

```text
POST /api/instrument/soundhole
GET /api/instrument/soundhole/types
POST /api/instrument/soundhole/spiral/geometry
POST /api/instrument/soundhole/spiral/dxf
```

Instead:

- preserve existing fields
- add non-breaking `aperture_geometry`
- avoid changing request payloads during Track A

---

## Implemented types only

`GET /soundhole/types` should currently return only:

```text
round
oval
fhole
spiral
```

Do NOT expose:

```text
D-hole
duck-head
trapezoid
side-port
slot-port
```

until backend implementations exist.

---

# 14. Dependency Graph

## Current status

Completed:

```text
A1 Freeze destructive actions
A2 Spiral math correction
Regression tests
```

Pending:

```text
A3 ApertureGeometry
A4 API augmentation
A5 Documentation vocabulary refactor
A6 Workspace consolidation
```

---

## Recommended order

### Immediate next

```text
A3 ApertureGeometry
```

### Then

```text
A4 Non-breaking API augmentation
```

### Then

```text
A5 Vocabulary/documentation refactor
```

### Then

```text
Compare soundhole_calc.py vs soundhole_designer.html
```

### Then

```text
A6 Frontend consolidation
```

Only after the Neck Studio framework patterns are stable.

---

# 15. Frontend Consolidation Objective

The final frontend goal is:

\[
\boxed{
\text{fewer top-level tools, more shared infrastructure}
}
\]

Not:

```text
many independent generator pages
```

Target structure:

```text
ArtStudioWorkspace
├─ ApertureWorkspace
├─ RosetteWorkspace
├─ InlayWorkspace
├─ PatternWorkspace
├─ HeadstockWorkspace
└─ ShopCalculatorWorkspace
```

Each workspace should share:

- parameter panels
- export systems
- presets
- canvas behavior
- tool registry
- measurement import patterns

---

# 16. Final Guidance

The aperture sprint should now proceed as:

\[
\boxed{
\text{frontend alignment first, extraction second, cleanup last}
}
\]

The critical physics correction is already complete.

The remaining work is primarily:

- architectural alignment
- shared frontend infrastructure
- inverse solver extraction
- workspace consolidation
- documentation reframing

The goal is not merely a better spiral tool.

The goal is:

\[
\boxed{
\text{a unified aperture-system modeling and calibration workspace}
}
\]

---

# Appendix A: Verified Implementation Guidance (Q1–Q9)

The following Q&A was verified against the extracted `luthiers-toolbox-main` archive. It separates **confirmed repo facts** from **recommended architecture** and served as the authoritative guidance for this implementation.

---

## Q1 — Current spiral math location

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

Equivalent frontend formula:

```ts
const alpha = Math.atan(1.0 / p.k)
const oneWall = (rEnd - p.r0) / Math.sin(alpha)
```

**Correct formula** for r(θ) = r₀e^(kθ):

\[
\boxed{
L_{\text{path}}=
\frac{\sqrt{1+k^2}}{k}(r_1-r_0)
}
\]

with fallback:

\[
L_{\text{path}}=r_0\theta
\quad \text{when } k\rightarrow 0
\]

The archived `soundhole_designer.html` is a different issue: it contains inverse Helmholtz and two-cavity logic that should be extracted, but it is not the primary spiral geometry source. The inventory identifies it as a promoted/misarchived production calculator with `Leff`, `helmholtz`, and `twoCav()` logic.

---

## Q2 — Frontend existence

**Confirmed**: the Vue frontend exists in this repo.

Files found:

```text
packages/client/src/views/art-studio/SoundholeDesignerView.vue
packages/client/src/components/toolbox/acoustics/SpiralSoundholeDesigner.vue
```

So Track A is **refactor existing Vue**, not "build new Vue from scratch."

However, the active Vue implementation and archived HTML are not feature-equivalent. The inventory says `soundhole_designer.html` has inverse solver and two-cavity eigenvalue features missing from the current Vue/API surface.

---

## Q3 — ApertureGeometry placement

**Recommended**: create a new shared output model, do **not** replace spiral params.

Use:

```text
services/api/app/instrument_geometry/soundhole/aperture_geometry.py
```

or, if you want to keep calculators separate:

```text
services/api/app/calculators/aperture_geometry.py
```

Best structure:

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

Each aperture type should keep its own params:

```python
RoundParams
OvalParams
FHoleParams
SpiralParams
```

and produce a generic `ApertureGeometry`.

So:

\[
\boxed{
\text{specific params} \rightarrow \text{generic geometry output}
}
\]

Do not make `ApertureGeometry` replace `SpiralParams`. It should wrap or normalize outputs.

---

## Q4 — Equivalent diameter validity

Yes, your proposed rule is basically right.

**Use equivalent diameter for**:

```text
quick UI preview
legacy API compatibility
rough round-hole comparison
position / clearance checks that expect circular diameter
backwards-compatible Helmholtz estimates
```

**Use full aperture tuple for**:

```text
inverse solver
acoustic comparison
loss estimation
effective length
manufacturing risk
non-round aperture comparison
f-hole / spiral / oval behavior
```

The full tuple should be:

\[
A,\quad P,\quad P/\sqrt{A},\quad L_{\text{eff}},\quad R_{\text{loss}},\quad Q
\]

Equivalent diameter preserves area only:

\[
d_{\text{eq}}=2\sqrt{\frac{A}{\pi}}
\]

It does **not** preserve perimeter, edge loss, slot behavior, or structural penalty.

---

## Q5 — Carlos presets

The preset parameters are not necessarily wrong.

What is wrong is the **derived metrics** calculated from them:

```text
area
perimeter
total_length
area ratio vs 4-inch round
equivalent diameter
possibly acoustic f_H predictions
```

The Carlos defaults in the handoff are:

```text
start_radius_mm = 10.0
growth_rate_k = 0.18
turns = 1.1
slot_width_mm = 14.0
```

for both upper and lower spirals, with different centers and rotations.

After fixing the path-length formula, recompute all derived values. Then decide whether the presets are still acoustically reasonable.

So:

\[
\boxed{
\text{Do not change preset inputs first. Recompute outputs first.}
\]

---

## Q6 — Breaking changes

Do **not** make breaking API changes in Track A.

**Preserve**:

```text
POST /api/instrument/soundhole
GET /api/instrument/soundhole/types
GET /api/instrument/soundhole/spiral/default
POST /api/instrument/soundhole/spiral/geometry
POST /api/instrument/soundhole/spiral/dxf
POST /api/instrument/soundhole/spiral/validate
```

These endpoints are documented as complete in the inverse calibration handoff.

**Recommended API strategy**:

### Existing response

Keep existing fields.

### Add non-breaking fields

Add:

```json
"aperture_geometry": {
  "type": "spiral",
  "area_mm2": 0,
  "perimeter_mm": 0,
  "equivalent_diameter_mm": 0,
  "path_length_mm": 0,
  "pa_ratio_mm_inv": 0
}
```

### Do not add future types yet

`GET /soundhole/types` should only return implemented types:

```text
round
oval
fhole
spiral
```

Do not return D-hole, duck-head, trapezoid, side-port, or slot-port as active types until backend geometry and tests exist.

---

## Q7 — Tornavoz placement

Tornavoz should be a **modifier**, not an aperture type.

Correct model:

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

or:

\[
Z_{\text{total}} = Z_{\text{aperture}} + Z_{\text{tornavoz}}
\]

Do not put tornavoz parameters inside `SpiralParams`.

Do not add `TORNAVOZ` to `SoundholeType`.

Use:

```python
soundhole_type = "spiral"
modifier = TornavozAttachment(...)
```

This preserves the reframing:

\[
\boxed{
\text{aperture first, compensation second}
}
\]

---

## Q8 — Inverse solver source

There are at least two relevant sources:

### Existing production-ish math/reference

`LUTHERIE_MATH.md` already documents an inverse Helmholtz solver and two-cavity Helmholtz sections. It states implementation references for inverse Helmholtz and multi-port logic in `soundhole_calc.py`, and also notes two-cavity approximations.

### Misarchived richer implementation

`soundhole_designer.html` contains unique formulas including:

```text
Leff()
helmholtz()
twoCav()
body volume calibration factor 1.83x
PMF = 0.92
```

and is specifically flagged as missing from the active Vue/API surface.

So answer:

- `soundhole_calc.py` already has some inverse/multi-port acoustic math.
- `soundhole_designer.html` likely contains additional or more complete interactive solver logic.
- Do not blindly port it over. Diff formulas first.

**Recommended step**:

```text
Compare soundhole_calc.py vs soundhole_designer.html:
  Leff
  helmholtz
  inverse diameter/area
  multi-port
  two-cavity
  PMF
  volume calibration
```

Then port only the missing or better-tested pieces.

---

## Q9 — Dependency order inside Track A

Not strictly linear. Use this dependency graph:

```text
A1 Freeze destructive actions
   └─ must happen first

A2 Fix spiral math                          ← COMPLETE
   ├─ can run immediately after A1
   ├─ prerequisite for recalculating presets
   └─ prerequisite for trustworthy acoustic comparison

A3 Define aperture vocabulary / implemented vs future types
   ├─ can run in parallel with A2
   └─ prerequisite for docs and UI language

A4 Create common ApertureGeometry output
   ├─ depends on A3
   ├─ should follow A2 enough to avoid encoding wrong spiral metrics
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

1. Freeze deletion/moves.
2. Fix spiral path-length formula in all four places. ← COMPLETE
3. Add regression tests for the corrected formula. ← COMPLETE
4. Recompute Carlos derived metrics. ← COMPLETE
5. Define `ApertureGeometry`.
6. Add `aperture_geometry` to responses without breaking existing schema.
7. Update docs/language: aperture replacement, not tornavoz replacement.
8. Compare `soundhole_calc.py` vs `soundhole_designer.html`.
9. Only then begin Vue consolidation.

This order minimizes rework.

---

*End of Appendix A*
