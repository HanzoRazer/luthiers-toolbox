# Production Shop — Lutherie Design Session Notes
## Organized by Topic

**Sessions captured:** March 18–19, 2026
**Platform:** The Production Shop — `luthiers-toolbox-main`
**Participants:** Ross Echols (PE #78195, luthier/developer)
**Purpose:** Design knowledge capture, backlog documentation, acoustic physics discussion

---

## Table of Contents

1. [Platform State and CAM Workspace Build](#1-platform-state-and-cam-workspace-build)
2. [Construction Knowledge Gaps — Full Audit](#2-construction-knowledge-gaps)
3. [Plate Thickness Design — Port from tap-tone-pi](#3-plate-thickness-design)
4. [Archtop Graduation Data — D'Aquisto Digitization](#4-archtop-graduation-data)
5. [Soundhole Physics and Designer](#5-soundhole-physics-and-designer)
6. [Side Ports — Comprehensive Analysis](#6-side-ports)
7. [Geometry Backlog — Ten Items](#7-geometry-backlog)
8. [Body Geometry Sweep Architecture](#8-body-geometry-sweep-architecture)
9. [Neck Join Position](#9-neck-join-position)
10. [Archtop — Neck Angle, Arch Height, Rim Depth](#10-archtop-neck-angle-arch-height-rim-depth)
11. [Fret Count — 24-Fret Acoustic Guitar](#11-fret-count)
12. [Mesquite as a Tonewood](#12-mesquite-as-a-tonewood)
13. [What This Knowledge Base Is Becoming](#13-what-this-knowledge-base-is-becoming)

---

## 1. Platform State and CAM Workspace Build

### What was built

The Production Shop is a Vue 3 + TypeScript ERP/CAM platform (`luthiers-toolbox-main`)
for instrument makers, with a FastAPI backend, ~530 Vue components, and domains
spanning CAM, RMOS risk management, art studio, saw lab, and toolbox modules.
Ross owns a BCAMCNC 2030A CNC router.

**CAM Workspace Phase 1 (completed this session):**

Backend (`services/api/app/`):

- `cam/machines.py` — Canonical `BCamMachineSpec` replacing two scattered definitions
  that used different unit systems. The old definitions disagreed on safe_z by 52%
  (0.6" / 15.24mm vs 10mm). Fixed to: max_z=101.6mm, safe_z=10mm, rapid=5080mm/min.
- `cam/neck/orchestrator.py` — Three safety fixes identified and corrected:
  (a) Tool changes between operations were missing — added `_tool_change_block()`
  (b) G43 tool length compensation was absent — added to `PostConfig`
  (c) `_program_footer()` hardcoded Z50 — now uses `machine.safe_z_mm`
- `calculators/fret_slots_cam.py` — Sagitta formula bug fixed. Old approximation
  was 0.42mm short at the 12th fret, producing undersized slot depth.
- `calculators/cam_cutting_evaluator.py` — Reformatted from single minified line
  (0 newlines) to 267 lines. Zero logic changes. Now readable and testable.
- `cam_workspace_router.py` — Full CAM workspace API (628 lines):
  - `POST /api/cam-workspace/neck/evaluate` — debounced gate check
  - `POST /api/cam-workspace/neck/generate/{op}` — G-code per operation
  - `POST /api/cam-workspace/neck/generate-full` — full program, returns .nc file
  - Gate tuning: diameter-relative chipload floor, heat capped at YELLOW,
    deflection YELLOW for multi-pass carving, kickback suppressed for dia<2mm saws

Frontend (`packages/client/src/`):

- `GateStatusBadge.vue` — RED/YELLOW/GREEN status with Z-ceiling display
- `GcodePreviewPanel.vue` — syntax-highlighted G-code preview with download
- `NeckOpPanel.vue` — single component drives all 4 operations via prop
- `CamWorkspaceView.vue` — 6-step wizard, three-panel layout
- `AppShell.vue` — added CAM tab with blue badge

**38/38 backend tests passing.**

### What remains in outputs (not yet committed to repo)

All files that need manual copy into `luthiers-toolbox-main`:

- `for-repo/BACKLOG.md` — 1,134-line implementation backlog (repo root)
- `for-repo/services/api/app/cam_workspace_router.py`
- `for-repo/services/api/app/cam/machines.py`
- `for-repo/services/api/app/cam/neck/orchestrator.py`
- `for-repo/services/api/app/calculators/cam_cutting_evaluator.py`
- `for-repo/services/api/app/calculators/plate_design/` (8 files)
- `for-repo/services/api/app/instrument_geometry/models/daquisto_excel/graduation_measurements.json`
- `for-repo/services/api/app/instrument_geometry/models/archtop_graduation_template.json`

---

## 2. Construction Knowledge Gaps

### Full gap audit conducted

The codebase was audited against the full domain of instrument construction.
The finding: strong coverage of geometry (fret math, compound radius, string spacing,
brace cross-section, headstock break angle) but significant gaps in construction
sequences, setup mechanics, and material behavior.

### CONSTRUCTION items written to BACKLOG.md

Ten items with full formulas and file paths:

| Item | Description | Key formula/connection |
|------|-------------|----------------------|
| CONSTRUCTION-001 | Nut slot depth | `slot_depth = dia/2 + clearance - fret_crown_height` |
| CONSTRUCTION-002 | Setup cascade | nut → relief → saddle → 12th fret action |
| CONSTRUCTION-003 | Fret leveling geometry | best-fit plane, cut depths, replacement flags |
| CONSTRUCTION-004 | String tension | `T = (2fL)² × μ` |
| CONSTRUCTION-005 | Glue joint geometry | dovetail, bolt-on, set-neck joint areas |
| CONSTRUCTION-006 | Humidity/wood movement | EMC from RH, dimensional change, crack risk |
| CONSTRUCTION-007 | Finish schedule | nitro/poly/oil/French polish coat sequences |
| CONSTRUCTION-008 | Electronics physical layout | pot spacing, jack placement, shielding |
| CONSTRUCTION-009 | Acoustic voicing history | longitudinal brace thinning model |
| CONSTRUCTION-010 | Build sequence composition | shared BuildSpec state object |

### Bridge saddle slant angle discussion

The question of why Gibson J-45 bridges are slanted ~4° was discussed.
The answer: the saddle slant compensates for the different intonation
compensation needed by wound vs plain strings. The low E needs the most
compensation (saddle furthest back), the high e needs the least.
The slant angle is `arctan(Δcomp / string_spread)`. Taylor guitars vary
their slant by model based on targeted playing style and string gauges.

---

## 3. Plate Thickness Design

### Port from tap-tone-pi

The `tap_tone_pi/design/` package contains a complete, tested, production-ready
plate thickness design system that was never ported to the toolbox. Eight modules
were identified and ported to `calculators/plate_design/`:

- `thickness_calculator.py` — orthotropic plate modal frequency, coupled eigenfrequencies
- `calibration.py` — 8 body styles × 14 tonewood material presets
- `inverse_solver.py` — solve for thickness given target frequency (single and multi-mode)
- `rayleigh_ritz.py` — variational mode solver for higher accuracy
- `alpha_beta.py` — physical γ derivation
- `gamma_calibration.py` — fit γ from measured free-plate data
- `coupled_2osc.py` — 2-oscillator rigid-back model
- `__init__.py`

### Mahogany example (validated)

Mahogany back plate, 559×241mm, targeting 86 Hz:
Inverse solver result: **2.33 mm**. Cross-checked against published data — valid.

### Connection to body geometry

`BodyCalibration` in `calibration.py` stores `top_a_m` and `top_b_m` as
hardcoded constants per body style. These should be derived from actual
body dimensions rather than hardcoded, so the plate mode calculation
updates correctly for non-catalog body designs. This is the connection
that `body_geometry_calc.py` (not yet built) needs to make.

---

## 4. Archtop Graduation Data

### D'Aquisto photograph digitized

A sketch of D'Aquisto archtop graduation measurements was photographed
and transcribed. The data captures top and back thickness at five stations
with arch heights:

**Top:** 3.0mm edge → 4.5mm apex. Arch height ~15.9mm (5/8") at bridge.
**Back:** 2.5mm min → 4.5mm apex. Arch height ~19.1mm (3/4") below waist.

Written to: `instrument_geometry/models/daquisto_excel/graduation_measurements.json`

### Key insight: proportions are universal

The observation was made (and confirmed against Benedetto and D'Angelico data)
that archtop graduation proportions are consistent across makers. What differs
is where individual makers set the absolute apex thickness and arch height
based on their wood selection and tonal targets.

**Consequence for the toolbox:** Rather than storing each maker's graduation
as a unique dataset, store a **normalized template** — each value expressed
as a fraction of the total range between edge and apex. The template is the
transferable knowledge. The absolute values are derived from the wood's
physical properties via the plate thickness calculator.

Normalized template written to: `instrument_geometry/models/archtop_graduation_template.json`

Key values:
- `arch_height_fraction_of_lower_bout_width`: 0.062 (top), 0.075 (back)
- These fractions hold across D'Aquisto, Benedetto, and D'Angelico instruments

---

## 5. Soundhole Physics and Designer

### Option B build — what was built

A complete standalone soundhole calculator was built over multiple sessions.
Final state: three files in `outputs/soundhole/`.

**`soundhole_calc.py`** (1,262 lines):
Complete Python module with:
- Helmholtz multi-port calculation (Gore-style perimeter correction)
- Plate-air coupling correction (PMF = 0.92, calibrated against 3 instruments)
- Structural ring width check
- Placement validation
- Inverse solver (bisection, < 60 iterations, ±0.01 Hz)
- Sensitivity curve (20 points, ±25mm diameter range)
- Body volume from dimensions (calibrated, 1.83× factor)
- Two-cavity Selmer/Maccaferri model
- Side port extensions (6 positions, 4 types, radiation descriptions)
- 7 calibrated presets (all within ±2 Hz of measured targets)

**`soundhole_designer.html`** — Interactive UI:
- 4 tabs: Design, Inverse Solver, Body Dimensions, Two-Cavity
- Body canvas with drag-to-reposition and scroll-to-resize
- Inline sensitivity sparkline
- Radiation panel for side ports
- JSON export

**`README.md`** — Physics reference with all formulas annotated.

### Critical physics finding: F-holes resonate at 85–100 Hz, not 120 Hz

The 120 Hz figure appearing in some lutherie literature is the top plate
mode, not the air resonance. F-holes have dramatically higher perimeter-to-area
ratio than round holes, which drives L_eff to 50–52mm (vs ~10mm for round holes).
This pushes f_H to ~89 Hz for a standard Benedetto 17" body.
All presets corrected to reflect measured/physics-derived values.

### Preset calibration results

| Preset | Predicted | Target | Error |
|--------|-----------|--------|-------|
| Martin OM | 107.7 Hz | 108 Hz | −0.3 Hz |
| Martin D-28 | 98.1 Hz | 98 Hz | +0.1 Hz |
| Gibson J-45 | 99.4 Hz | 100 Hz | −0.6 Hz |
| Classical | 97.4 Hz | 96 Hz | +1.4 Hz |
| Selmer Oval | 99.5 Hz | 100 Hz | −0.5 Hz |
| OM + Side Port | 113.6 Hz | 112 Hz | +1.6 Hz |
| Benedetto 17" F | 89.4 Hz | 90 Hz | −0.6 Hz |

---

## 6. Side Ports

### Why side ports were given their own treatment

Side ports are more varied and nuanced than the initial implementation suggested.
The initial model knew the Helmholtz math but had no concept of where on the rim
the port sits, what it does to radiation pattern, or the different port types
builders actually use.

### Side port types

| Type | Construction | Acoustic character |
|------|-------------|-------------------|
| Round | Forstner bit or hole saw | Baseline. Simple. |
| Oval | Router jig | P/A slightly higher → L_eff +5% |
| Slot | Router or oscillating tool | High P/A → significantly longer L_eff → smaller f_H shift per cm² |
| Chambered | Internal channel before exit | Channel length adds directly to L_eff — deliberate tuning possible |

### Side port position radiation descriptions

| Position | Primary radiation | f_H shift | Builder use |
|----------|------------------|-----------|------------|
| Upper treble | Toward player's right ear, upward | +3–6 Hz | Most common — performer monitor |
| Upper bass | Toward player's left arm, ceiling | +3–6 Hz | Balanced monitoring |
| Lower treble | Toward floor, treble side | +8–15 Hz | f_H tuning, not monitor |
| Lower bass | Toward floor, bass side | +8–15 Hz | Maximum f_H shift (Stoll technique) |
| Waist | At 90° to centerline | +1–4 Hz | Rare — narrow rim limits size |
| Symmetric pair | Both upper bouts | +6–12 Hz | Stereo-like player monitoring |

### What the current module gets right vs wrong

**Right:** Multi-port Helmholtz treats side ports correctly. L_eff uses side
thickness (2.3mm) rather than top thickness (2.5mm).

**Wrong (before this session):**
- No position parameter — no concept of where on the rim the port sits
- No radiation pattern model
- No structural clearance checks for neck/tail block proximity
- No tube/chambered port option for deliberate L_eff tuning

All four gaps addressed in `SidePortSpec` class and `analyze_side_port()` function.

---

## 7. Geometry Backlog

### Ten items written to BACKLOG.md (GEOMETRY-001 through GEOMETRY-010)

These are items the codebase was missing with full implementation specifications:

| Item | Description | Key connection |
|------|-------------|---------------|
| GEOMETRY-001 | Neck angle calculation | `neck_angle = arctan(bridge_height_delta / nut_to_bridge)` |
| GEOMETRY-002 | Soundhole placement rules | 1/3 body length + structural ring check |
| GEOMETRY-003 | Kerfing geometry | 70% kerf depth rule, min bend radius |
| GEOMETRY-004 | Bridge design geometry | Saddle slant = `arctan(Δcomp / spread)` |
| GEOMETRY-005 | Neck block and tail block sizing | String tension × safety factor |
| GEOMETRY-006 | Fret wire selection | `FRET_WIRE_PROFILES` table, tang → slot width |
| GEOMETRY-007 | Nut compensation: zero-fret vs traditional | Zero-fret shifts all positions by ½ crown width |
| GEOMETRY-008 | Tuning machine post height and string tree | Break angle ≥ 7° threshold |
| GEOMETRY-009 | Back brace pattern and geometry | Martin D-28 `BACK_BRACES` data already in repo |
| GEOMETRY-010 | Side thickness and bending parameters | Species: temp, moisture, min bend radius |

---

## 8. Body Geometry Sweep Architecture

### The design problem being addressed

The soundhole inverse solver (§5) and plate thickness inverse solver (§3)
work independently. The body geometry sweep connects them: given a set of
body dimension variables, find all configurations that simultaneously achieve
target f_H, target plate mode frequency, within buildable C-bout radii.

### Proposed `body_geometry_calc.py` architecture

```
Variables: lower_bout, upper_bout, waist, body_length, depth, join_fret
Fixed: scale_length, target_fH, target_plate_mode, material
Outputs: plate_thickness, hole_diameter, cbout_radius, coupling_efficiency
Constraints: cbout_radius ≥ species_min_bend, 2.0 ≤ thickness ≤ 4.5mm
Sweep: hold 4 variables, sweep 2, contour-plot acoustic score
```

### What changes when upper bout width varies (holding waist and lower bout constant)

1. **Volume changes** — upper section volume shifts (~1.5–2L per 20mm)
2. **C-bout curvature changes** — wider upper bout + fixed waist = tighter C-bout radius
3. **Plate dimensions change** — effective plate width for modal calculation shifts

The sagitta formula (§16 in math doc) computes C-bout radius from these dimensions.
This provides the buildability constraint that bounds the sweep.

### The key dataclasses needed

```python
@dataclass
class NeckJoinEffect:
    join_fret: int
    scale_mm: float
    body_length_mm: float
    bridge_from_neck_block_mm: float
    bridge_as_pct_body: float
    coupling_efficiency: float  # sin(π × bridge_in_effective_plate_pct)

@dataclass
class ArchtopGeometry:
    lower_bout_mm: float
    arch_height_mm: float
    arch_rise_ratio: float
    geometric_stiffness_factor: float
    volume_reduction_vs_flat_L: float
    neck_angle_required_deg: float
```

---

## 9. Neck Join Position

### The question

Traditional flat-top acoustics are built with 12 frets to the body.
Some builders, particularly for small bodies like OOO, advocate 13 frets
to the body, especially with all-mahogany construction. How does the
physics support or refute this?

### The physics

Moving from 12-fret to 13-fret body join shifts the bridge 12.2mm
toward the neck block (on a 645mm scale). This changes where the bridge
contacts the effective plate in modal coordinate terms.

The coupling efficiency calculation (mode shape amplitude at bridge position)
shows the difference between 12-fret and 13-fret join is **negligible**
by the mode shape argument alone (coupling efficiency 0.998 vs 0.999).

The real mechanism for the mahogany preference is different:
mahogany's more isotropic stiffness (E_C/E_L ≈ 0.12–0.14 vs spruce 0.06–0.08)
means its cross-grain modes are proportionally stronger. A 12.2mm shift
slightly increases cross-grain mode coupling relative to the fundamental —
which suits mahogany's natural character but costs more on spruce.

### Error correction

An error was made in the initial session stating this was a 12-fret vs 14-fret
comparison. Ross corrected this to 12-fret vs 13-fret. The 14-fret flat-top
exists (Martin has built them) but it is not the traditional alternative for
OOO instruments. The corrected analysis uses 12.2mm shift, not 24mm.
See §26 in the math document.

### Summary

The 13-fret all-mahogany OOO preference is:
- Physically motivated (cross-grain mode coupling)
- Not explicable by coupling efficiency alone
- A deliberate half-step optimization
- Moot without a cutaway on a steel-string guitar beyond the 20th fret

---

## 10. Archtop — Neck Angle, Arch Height, Rim Depth

### Neck join position on archtop: irrelevant acoustically

On a flat-top, the neck join position determines where the bridge lands on
the plate, affecting mode coupling. On an archtop, the bridge is floating and
adjustable — it is placed at the correct intonation point after stringing.
There is no acoustic cost to 14-fret join on archtops. Every major archtop
maker converged on 14-fret by the late 1930s.

**The neck angle replaces the neck join fret as the critical design variable.**

### Arch height is the primary stiffness variable

On a flat-top, plate thickness governs stiffness (linear in h).
On an archtop, arch height governs stiffness (quadratic in rise ratio).

A 4mm increase in arch height on a 17" Benedetto (18→22mm) increases
arch rise ratio from 0.042 to 0.051, changing the stiffness index by **48%**.
This is approximately equivalent to changing a flat-top plate thickness
by 0.6–0.8mm. This is why archtop makers discuss arch height with the
same gravity flat-top makers give tap tones.

### Volume and stiffness are coupled on archtops

This is the key difference between archtop and flat-top acoustic optimization:

On a flat-top: plate thickness changes stiffness WITHOUT changing volume.
Free variable.

On an archtop: raising arch height SIMULTANEOUSLY increases stiffness AND
reduces cavity volume (raising f_H through two mechanisms at once).
There is no free variable equivalent to plate thickness on a flat-top.

**Practical consequence:** Archtop designs cluster in a narrow arch height
range (18–24mm for 16–17" bodies) because the physics doesn't leave much room.
Variation between makers lies in the graduation profile (how arch height
falls from apex to rim), not in absolute apex height.

### Rim depth asymmetry

**Upper bout rim depth** — constrained. Changing it requires a compensating
neck angle change (~0.9° per 10mm depth change on a 17" archtop).
This is not a free design variable.

**Lower bout rim depth** — relatively free. Adding 10mm of lower bout depth
adds approximately 1.1L of cavity volume (shifting f_H by ~5–7 Hz) with no
effect on neck angle. This is the volume tuning control for archtops.

The sweep architecture should treat these differently:
- Upper bout depth: derived from neck angle target
- Lower bout depth: free acoustic variable for volume tuning

---

## 11. Fret Count

### The 22-fret acoustic is at the physical limit

For a standard 645mm scale with 14-fret body join and 96mm soundhole
at 165mm from the neck block:

- 22nd fret: 10.7mm clearance to soundhole front edge — tight but workable
- 23rd fret: 0.5mm clearance — essentially impossible without soundhole relocation
- 24th fret: 9.1mm conflict — requires design resolution

### Four solutions for 24-fret acoustic

**Solution 1 — Move soundhole 19mm deeper into body**
Clears the 24th fret. But conflicts with the X-brace intersection
(which sits at ~193mm, only 9mm from the required 184mm soundhole center).
X-brace must move 34mm toward the neck to restore clearance.
Acoustic consequence: reduced bass headroom, slightly brighter midrange.
Verdict: workable on larger bodies; costly on small bodies.

**Solution 2 — Reduce soundhole diameter to ~58mm**
Traditional position, no conflict. But 63% area reduction drives f_H to ~76 Hz.
Requires aggressive side porting to compensate.
Verdict: not viable without complete redesign around it from the start.

**Solution 3 — Offset or side soundhole**
Taylor NS24 (nylon string) used upper-treble corner soundhole.
Emerald X20 uses side soundholes entirely.
Acoustically cleanest — no bracing changes needed.
Visually breaks with traditional acoustic aesthetics.
Verdict: optimal if the builder accepts the non-traditional look.

**Solution 4 — Cutaway + 24 frets**
The natural pairing. A cutaway already removes upper bout material and
alters the body geometry. Adding 24 frets doesn't compound the acoustic
costs — they are already paid. A 24-fret cutaway acoustic is a coherent
design.

### Fretboard extension mass loading

Going from 22 to 24 frets adds 19.8mm of fretboard over the body top.
Extra mass: ~7 grams (ebony, 50mm wide, 6mm thick).
Effect: suppresses higher plate modes slightly. Favorable on mahogany tops,
mildly unfavorable on spruce tops.

### Historical context

Traditional acoustics: 19–22 frets. 22 is the current norm.
Electric guitars: 24 frets increasingly standard.
A 24-fret acoustic is not impossible — it requires solving the soundhole
conflict and accepting the acoustic trades. The knowledge base now includes
the numbers to make that decision explicitly.

---

## 12. Mesquite as a Tonewood

### Why this matters for a Texas-based luthier

Honey Mesquite (*Prosopis glandulosa*) is abundant in Texas and the Southwest.
It is classified as an invasive species — harvest is ecologically beneficial.
It is cheap and locally available. It has been compared to rosewood and ebony
in feel and appearance. The question: how does it perform acoustically?

### Database entry (from `luthier_tonewood_reference.json`)

```
density_kg_m3: 950
janka_hardness_lbf: 2345
modulus_of_elasticity_gpa: 11.58
modulus_of_rupture_mpa: 117.0
speed_of_sound_m_s: 3491
acoustic_impedance: 3.32
grain: interlocked, often wildly figured
tone_character: bright, dense, crystalline highs with strong sustain —
                similar to rosewood but more percussive
sustainability: abundant in Texas/Southwest US, invasive species —
                harvest is ecologically beneficial
```

### Comparison against ebony family (from database)

| Species | Density | Janka | MOE | SoS | Z |
|---------|---------|-------|-----|-----|---|
| African Ebony | 1030 | 3080 | ~17 GPa | 3400 | 3.50 |
| Macassar Ebony | 1120 | 3220 | — | 3500 | 3.92 |
| Katalox (Mexican Ebony) | 1050 | 3650 | — | 3550 | 3.73 |
| Texas Ebony | 965 | 1179 | 16.54 | 4140 | 4.00 |
| Honey Mesquite | **950** | **2345** | **11.58** | **3491** | **3.32** |
| E. Indian Rosewood | 830 | 2440 | 11.50 | 3728 | 3.09 |

Key finding: Mesquite Z = 3.32 MRayl exceeds both rosewood (3.09) and maple (3.08).
For back plate acoustic behavior, it is more reflective than the rosewood reference.

### Flat-top back and sides assessment

**Acoustic impedance:** 3.32 MRayl — more reflective than Indian or Brazilian rosewood.
For a flat-top back this means strong fundamental emphasis and good sustain.
The database describes the tone as "bright, dense, crystalline highs — similar to
rosewood but more percussive." For a back, this produces strong projection with
faster attack transients than a rosewood back.

**Side bending:** Estimated minimum bend radius ~170mm at 2.5mm thickness.
More forgiving than maple (184mm), despite the higher Janka hardness.
The MOR of 117 MPa gives it good toughness under bending stress.
The archtop's gentle waist radius (45–60mm) is well within mesquite's capability.
The constraint is blank availability — mesquite grows in branched forms,
limiting long clear sections needed for side sets.

**Workability warning:** High burn risk, high tearout risk from interlocked grain.
Carbide tooling required throughout. Dust is an irritant. Figured stock
requires card scrapers, not sandpaper (loads quickly due to silica content).
The BCAM handles this; hand-tool finishing is the challenge.

### Fretboard assessment

Janka 2345 lbf — comparable to African Ebony (3080 lbf), substantially higher
than Indian Rosewood (2440 lbf). Adequate wear resistance under steel strings.
MOE 11.58 GPa — lower than ebony (~17 GPa). Adds less neck stiffness than ebony.
Compensation: use 0.5mm thicker fretboard blank than ebony spec.
Fret seating behavior similar to rosewood (tang pressing, kerf sizing).

### Texas Ebony as the complement

Texas Ebony (*Ebenopsis ebano*) — also locally available, also in the database:
MOE 16.54 GPa, SoS 4140 m/s, Z = 4.00 MRayl.
Higher Z than anything except bubinga in the comparison table.
Higher MOE than African Ebony.
As a fretboard and bridge material for a mesquite-bodied guitar, it would be
stiffer and more acoustically transparent than any conventional choice.

### The instrument concept

A flat-top acoustic with:
- Mesquite back and sides (Z > rosewood, percussive character)
- Sitka or Adirondack spruce top
- Texas Ebony fretboard and bridge

This combination has never been built at scale. The acoustic credentials exceed
a standard Indian Rosewood/Ebony build on every measurable dimension,
using materials available within driving distance of Liberty, Texas,
from trees that should be harvested for ecological reasons.

---

## 13. What This Knowledge Base Is Becoming

### Traditional knowledge vs computational lutherie

The traditional knowledge base — Gore & Gilet, Benedetto, Somogyi, the Guild
of American Luthiers archives — is deep but descriptive. It records what the
masters did and offers qualitative explanations for why.

What is being built here is predictive. It can answer questions the
traditional literature never asked because those builders never had the tools
to ask them precisely.

### Specific examples of new ground covered in these sessions

**1. The 13-fret all-mahogany OOO argument** has been discussed in builder forums
for decades. Nobody has published the cross-grain mode coupling ratio calculation
that explains why mahogany's more isotropic stiffness makes that tradeoff
favorable while spruce does not. The number is `sin(π × bridge_in_effective_plate_pct)`.
The Production Shop can now sweep this against any body/wood combination.

**2. The archtop rim depth asymmetry** — that upper bout depth is constrained
by neck angle while lower bout depth is a relatively free acoustic variable —
is something every experienced archtop builder knows in their hands.
The explicit chain of dependencies (arch height → neck block seating → neck angle
→ saddle height range) has never been written as a calculation. It is now.

**3. The 24-fret acoustic conflict** reveals something builders who attempted
it likely couldn't have stated precisely: the 23rd fret has 0.5mm clearance
(essentially impossible), the 24th fret creates a 9.1mm physical conflict,
and the extra fretboard mass is ~7 grams. Those numbers are not in any book.

**4. Mesquite as a back/sides material** has acoustic impedance that exceeds
rosewood. The numbers are in the database. Nobody has built a
spruce/mesquite/Texas-ebony flat-top acoustic and published acoustic measurements.
The Production Shop is positioned to design it before building it.

### The folk knowledge problem

The best instruments ever built came from builders who understood the physics
deeply — they expressed that understanding through accumulated intuition rather
than equations. The equations and the intuition describe the same reality.

The Production Shop's role: where the folk knowledge has always been personal
and guarded, framing it computationally makes it reproducible, testable, and
extensible. A builder who has never met D'Aquisto or Benedetto can engage
with the geometry of a Benedetto arch graduation and understand why those
proportions work, not just copy them.

### The sweep that does not yet exist

A query like:
> "Show me all (body size, join fret, fret count, wood combination) configurations
> that achieve f_H between 100–112 Hz, plate fundamental between 175–185 Hz,
> no soundhole conflict, and C-bout radius within mahogany's bending limits."

This query does not exist anywhere in the world right now.
`body_geometry_calc.py` will make it possible.

---

*Notes compiled from session transcripts and conversation history*
*The Production Shop — luthiers-toolbox-main*
*Ross Echols, PE #78195 — March 2026*
