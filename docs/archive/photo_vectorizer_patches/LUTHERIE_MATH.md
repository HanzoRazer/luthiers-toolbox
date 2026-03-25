# Lutherie Mathematics Reference
## The Production Shop — `luthiers-toolbox-main`

**Intended audience:** Practicing engineers, experienced builders, and acousticians.
All formulas are sourced, calibrated against measured instruments, and annotated
with the conditions under which they hold and where they break down.
Challenges and corrections are welcomed — this document is a living record.

**Version:** March 2026
**Status:** Active — additions expected as `body_geometry_calc.py` is built

---

## Table of Contents

1. [Fret Position Geometry](#1-fret-position-geometry)
2. [Neck Join Position and Bridge Coupling](#2-neck-join-position-and-bridge-coupling)
3. [Saddle Slant Angle (Bridge Intonation Compensation)](#3-saddle-slant-angle)
4. [Helmholtz Air Resonance — Single Port](#4-helmholtz-air-resonance--single-port)
5. [Effective Neck Length and Perimeter Correction](#5-effective-neck-length-and-perimeter-correction)
6. [Multi-Port Helmholtz](#6-multi-port-helmholtz)
7. [Plate-Air Coupling Correction](#7-plate-air-coupling-correction)
8. [Body Volume from Dimensions](#8-body-volume-from-dimensions)
9. [Soundhole Structural Ring Width](#9-soundhole-structural-ring-width)
10. [Soundhole Placement Validation](#10-soundhole-placement-validation)
11. [Inverse Helmholtz Solver](#11-inverse-helmholtz-solver)
12. [Orthotropic Plate Modal Frequency](#12-orthotropic-plate-modal-frequency)
13. [Plate Thickness Inverse Solver](#13-plate-thickness-inverse-solver)
14. [Archtop Arch Geometric Stiffness](#14-archtop-arch-geometric-stiffness)
15. [Archtop Volume Correction for Arch Height](#15-archtop-volume-correction-for-arch-height)
16. [C-Bout Radius (Sagitta Formula)](#16-c-bout-radius-sagitta-formula)
17. [Nut Slot Depth](#17-nut-slot-depth)
18. [Setup Cascade (Action at 12th Fret)](#18-setup-cascade)
19. [String Tension](#19-string-tension)
20. [Acoustic Impedance](#20-acoustic-impedance)
21. [Kerfing Geometry](#21-kerfing-geometry)
22. [Fretboard Extension Mass Loading](#22-fretboard-extension-mass-loading)
23. [Side Port Perimeter Factor](#23-side-port-perimeter-factor)
24. [Two-Cavity Helmholtz (Selmer/Maccaferri)](#24-two-cavity-helmholtz)
25. [Neck Angle Calculation](#25-neck-angle-calculation)
26. [Error Log](#26-error-log)

---

## 1. Fret Position Geometry

**Source:** Equal temperament, well established since Marin Mersenne (1636).
**Implementation:** `instrument_geometry/neck/fret_math.py → compute_fret_positions_mm()`

### Formula

The distance from the nut to fret *n* on a scale of length *L*:

```
d_n = L × (1 - 1 / 2^(n/12))
```

Equivalently, the distance from fret *n* to the saddle (bridge end):

```
r_n = L / 2^(n/12)
```

### Key distances (645.16 mm / 25.4" scale)

| Fret | From nut (mm) | From bridge (mm) | % of scale |
|------|-------------|-----------------|-----------|
| 12 | 322.6 | 322.6 | 50.0% |
| 13 | 340.7 | 304.5 | 52.8% |
| 14 | 357.8 | 287.4 | 55.5% |
| 22 | 464.1 | 181.0 | 72.0% |
| 24 | 483.9 | 161.3 | 75.0% |

### Conditions and limits

The formula is exact for equal temperament. It does not model compensation —
real saddle positions are offset by `comp_mm` per string (see §3).
`compute_fret_positions_mm()` accepts any `fret_count` integer — there is no
upper limit imposed. 24-fret necks are geometrically valid; the physical
constraints are soundhole clearance and fretboard mass loading (§22).

---

## 2. Neck Join Position and Bridge Coupling

**Source:** Derived in this project. Not in Gore & Gilet or standard lutherie references
in this explicit form. The coupling efficiency argument was challenged and confirmed
correct after a sign-convention error was identified and corrected (see §26).

### Problem statement

Moving the neck join from the 12th to 13th fret (on a 14-fret body join) shifts
the neck block 12.2 mm toward the tail, moving the bridge the same distance
toward the neck block. The acoustic question is: how does this change the
efficiency with which the bridge drives the plate's fundamental (1,1) mode?

### Bridge position in effective plate coordinates

The top plate is not free-free. The neck block and upper transverse brace
heavily constrain the upper ~28% of the body. The acoustically active plate
begins approximately at the X-brace/upper transverse brace intersection.
The effective plate length is approximately:

```
L_eff_plate ≈ 0.72 × body_length
```

The effective start of the plate from the neck block:
```
x_plate_start ≈ 0.28 × body_length
```

Bridge position in effective plate coordinates (for body join at fret `j`):

```
x_bridge_from_neck = scale_length - fret_position(j)
bridge_in_plate = (x_bridge_from_neck - x_plate_start) / L_eff_plate
```

For Martin OM (body_length = 495 mm, scale = 645.16 mm):

| Join fret | Bridge from neck | Bridge in plate | Coupling |
|-----------|-----------------|-----------------|---------|
| 12 | 322.5 mm | (322.5 - 138.6) / 356.4 = **51.6%** | sin(π × 0.516) = 0.998 |
| 13 | 310.3 mm | (310.3 - 138.6) / 356.4 = **48.2%** | sin(π × 0.482) = 0.999 |
| 14 | 287.4 mm | (287.4 - 138.6) / 356.4 = **41.8%** | sin(π × 0.418) = 0.962 |

### Coupling efficiency

The (1,1) plate mode has maximum displacement at the plate center (50%).
Mode shape for simply-supported plate:

```
coupling_efficiency(x) = sin(π × x_bridge_in_plate)
```

The difference between 12-fret and 13-fret join is **negligible** (0.998 vs 0.999).
The difference between 12-fret and 14-fret join is small but real (0.998 vs 0.962).

### Why 13-fret matters on an all-mahogany OOO

The coupling efficiency argument alone does not explain the 13-fret preference.
The relevant mechanism is the **cross-grain mode coupling ratio**.

Mahogany top: E_C/E_L ≈ 0.12–0.14 (more isotropic than spruce at 0.06–0.08).
The (2,1) cross-grain mode frequency is proportionally closer to the (1,1)
fundamental on mahogany than on spruce. Moving the bridge 12.2 mm toward
the plate center slightly increases the (2,1) coupling relative to (1,1),
which suits mahogany's naturally stronger cross-grain character.

On spruce this tradeoff costs more than it gains.
On mahogany it costs little and gains midrange definition.

**This is a qualitative argument supported by the physics.
It has not been directly measured on matched-pair instruments.
Any builder who disputes it with measured data is correct to do so.**

---

## 3. Saddle Slant Angle

**Source:** Derived from `instrument_geometry/bridge/geometry.py → compute_saddle_positions_mm()`.
Gibson J-45 measured slant: ~4°. Taylor: varies by model.
**Implementation:** Add `compute_saddle_slant_angle()` to `bridge/geometry.py` (GEOMETRY-004, not yet built).

### Formula

The saddle is slanted because wound and plain strings require different
compensation lengths. The saddle slant angle is:

```
slant_angle_deg = arctan(Δcomp / string_spread)
```

Where:
- `Δcomp` = compensation_low_E - compensation_high_e (typically 2–4 mm)
- `string_spread` = distance between outer string contact points at saddle

`compute_saddle_positions_mm()` already returns per-string compensated saddle
positions. The slant angle is the arctangent of the slope of a best-fit line
through those positions projected onto the body width axis.

### Why it matters

A non-slanted saddle with average compensation will have the low E slightly
sharp and the high e slightly flat at the 12th fret. The slant distributes
this error evenly. The slot for a slanted saddle must be routed at the slant
angle — a square slot with a slanted saddle produces uneven string break angle.

---

## 4. Helmholtz Air Resonance — Single Port

**Source:** Classic Helmholtz resonator theory. Guitar application: Gore & Gilet,
*Contemporary Acoustic Guitar Design and Build*, Vol. 1. Calibrated in this
project against Martin OM, D-28, Gibson J-45 (see §7).

**Implementation:** `calculators/soundhole_calc.py → compute_helmholtz_multiport()`
Also originally in `calculators/acoustic_body_volume.py → calculate_helmholtz_frequency()`

### Formula

```
f_H = (c / 2π) × √(A / (V × L_eff))
```

**Variables:**

| Symbol | Meaning | Units | Typical value |
|--------|---------|-------|--------------|
| c | Speed of sound in air at 20°C | m/s | 343.0 |
| A | Port opening area | m² | 0.006–0.009 |
| V | Internal cavity volume | m³ | 0.010–0.025 |
| L_eff | Effective acoustic neck length | m | 0.008–0.015 |

### Conditions

- Assumes rigid cavity walls — valid for guitar; cavity compliance from top plate
  is captured in the coupling correction (§7).
- Assumes port area << cavity cross-section — valid for standard soundholes.
- Assumes isothermal air compression at low frequencies — valid below ~300 Hz.
- Does NOT model the coupled plate-air system. The coupling correction (§7)
  adjusts the prediction post-hoc.

### Existing implementation discrepancy

`acoustic_body_volume.py` line 220 uses:
```python
L_eff = 1.7 * top_thickness + 0.85 * soundhole_diameter
```
This is dimensionally mixed (mm + mm × mm) and gives incorrect L_eff in SI units.
The formula in `soundhole_calc.py` is correct:
```python
L_eff = top_thickness_m + k0 * r_eq
```
Both files should be reconciled. **Do not use the acoustic_body_volume.py formula
for new code.**

---

## 5. Effective Neck Length and Perimeter Correction

**Source:** End correction theory from acoustics (Rayleigh, 1877; Levine & Schwinger, 1948).
Perimeter correction: empirical, calibrated in this project. Gore's modified formula.

**Implementation:** `calculators/soundhole_calc.py → compute_port_neck_length()`

### Formula

```
r_eq = √(A / π)                          (equivalent circular radius)
k   = k₀ × (1 + γ × P / √A)             (perimeter-corrected end-correction coefficient)
L_eff = t + k × r_eq
```

**Constants:**

| Symbol | Value | Meaning |
|--------|-------|---------|
| k₀ | 1.7 | Flanged opening end correction (classical result) |
| γ | 0.02 | Perimeter sensitivity constant |
| t | plate thickness at port | m |
| P | port perimeter | m |
| A | port area | m² |

### Why the perimeter correction matters

For a circular hole: P/√A = 2π√(πr²)/(√(πr²)) = 2√π ≈ 3.54.
For a high-aspect-ratio shape (f-hole, slot): P/√A >> 3.54.

A Benedetto 17" f-hole (23 × 110 mm): P/√A ≈ 9.8.
This drives k from 1.7 to ~5.5 and L_eff from ~10 mm to ~52 mm.

**Consequence:** F-holes resonate lower than their area alone predicts.
A 17" archtop with two 23×110mm f-holes has a combined area of ~40 cm²
but resonates at ~90 Hz — not 120 Hz. The 120 Hz figure in some lutherie
literature refers to the top plate mode, not the air resonance.

### Calibration of γ

γ = 0.02 was fit to produce ±3–5 Hz accuracy across the following instruments:
- Martin OM (96mm hole, 17.5L): predicted 107.7 Hz, measured ~108 Hz
- Martin D-28 (100mm hole, 22.0L): predicted 98.1 Hz, measured ~98 Hz
- Gibson J-45 (98mm hole, 21.0L): predicted 99.4 Hz, measured ~100 Hz

**Before calibration, expect ±10–15 Hz accuracy.**
γ should be refit if working with non-standard hole geometries or body shapes
significantly different from the calibration set.

### F-hole L_eff correction table

| F-hole size (each) | Area (cm²) each | L_eff (mm) | f_H (24L body) |
|-------------------|----------------|-----------|--------------|
| 23×110mm × 2 | 19.9 | 52 | ~89 Hz |
| 30×110mm × 2 | 25.9 | 58 | ~97 Hz |
| 40×110mm × 2 | 34.6 | 66 | ~105 Hz |

---

## 6. Multi-Port Helmholtz

**Source:** Acoustic parallel impedance. Gore & Gilet application to guitar side ports.
**Implementation:** `calculators/soundhole_calc.py → compute_helmholtz_multiport()`

### Formula

Multiple openings (main hole + side ports) add as parallel acoustic masses:

```
A_total     = Σᵢ Aᵢ
L_eff_weighted = Σᵢ (Aᵢ × L_eff_i) / A_total
f_H = (c / 2π) × √(A_total / (V × L_eff_weighted))
```

Each port contributes its own L_eff (using the thickness of the plate it penetrates —
top thickness for top ports, side/rim thickness for side ports).

### Side port L_eff

Side ports use rim thickness (~2.3 mm) rather than top thickness (~2.5 mm).
For a 30mm diameter side port in a 2.3 mm rim:
```
L_eff_side = 0.0023 + 1.7 × 0.015 = 0.0023 + 0.0255 = 0.0278 m = 27.8 mm
```
Compare to main soundhole (96mm, 2.5mm top):
```
L_eff_top = 0.0025 + 1.7 × 0.048 = 0.0025 + 0.0816 = 0.0841 m = 84.1 mm
```
The side port has shorter L_eff per unit area than the main hole.
Adding a 30mm side port to an OM-size body raises f_H by approximately 3–6 Hz.

### Side port position and radiation

Side port position has no effect on f_H through the Helmholtz formula
(only area and L_eff matter). Position affects:
- Radiation pattern (which direction air exits)
- Coupling to cavity modes (lower bout ports couple more strongly to
  the fundamental; upper bout ports couple weakly)

| Position | f_H shift | Primary effect |
|----------|-----------|---------------|
| Upper treble | +3–6 Hz | Player monitor — sound toward right ear |
| Upper bass | +3–6 Hz | Balanced monitoring |
| Lower treble | +8–15 Hz | f_H tuning — strong lower bout coupling |
| Lower bass | +8–15 Hz | Maximum f_H shift (Stoll technique) |
| Waist | +1–4 Hz | Minimal — narrow rim limits port size |
| Symmetric pair | +6–12 Hz | Doubled area; stereo monitoring |

---

## 7. Plate-Air Coupling Correction

**Source:** Experimental calibration in this project. Theoretical basis:
coupled oscillator theory (Caldersmith 1978; Fletcher & Rossing, *Physics of
Musical Instruments*, Ch. 9–10).

**Implementation:** `calculators/soundhole_calc.py`, constant `PLATE_MASS_FACTOR = 0.92`

### What it corrects

The Helmholtz formula (§4) predicts the **uncoupled** air resonance — the frequency
the cavity would have if the top plate were rigid. In a real guitar the top plate
flexes, which reduces the effective cavity compliance and shifts the air resonance
downward by approximately 5–10%.

```
f_H_assembled = f_H_helmholtz × PMF
```

Where PMF = Plate Mass Factor. Calibrated value: **PMF = 0.92**.

### Calibration

| Instrument | Helmholtz predicted | After ×0.92 | Measured | Error |
|-----------|-------------------|------------|---------|-------|
| Martin OM | 117.1 Hz | 107.7 Hz | ~108 Hz | −0.3 Hz |
| Martin D-28 | 106.7 Hz | 98.1 Hz | ~98 Hz | +0.1 Hz |
| Gibson J-45 | 108.0 Hz | 99.4 Hz | ~100 Hz | −0.6 Hz |

### Conditions

PMF = 0.92 is calibrated for:
- Steel-string flat-top acoustics with X-brace construction
- Standard spruce or cedar tops, 2.0–3.0 mm thickness
- Bodies in the 14–25L range

PMF for archtops is effectively 1.0 (the rigid carved arch suppresses
plate compliance near the soundhole, making the Helmholtz cavity much stiffer).
Classical guitars with thinner tops (2.0 mm) may have PMF closer to 0.90.

---

## 8. Body Volume from Dimensions

**Source:** Elliptical cross-section integration. Mirrors
`calculators/acoustic_body_volume.py → calculate_body_volume()`.
Calibration factor derived in this project.

**Implementation:** `calculators/soundhole_calc.py → volume_from_dimensions()`

### Formula

Body divided into three sections: lower bout (40% of length), waist (25%), upper bout (35%).

```
lower_area = π × (lower_bout/2) × (depth_endblock/2) × shape_factor
waist_area  = π × (waist/2)     × (avg_depth/2)       × shape_factor
upper_area  = π × (upper_bout/2) × (depth_neck/2)     × shape_factor

avg_depth = (depth_endblock + depth_neck) / 2

V_lower = (lower_area + waist_area) / 2 × (body_length × 0.40)
V_waist = waist_area                    × (body_length × 0.25)
V_upper = (waist_area + upper_area) / 2 × (body_length × 0.35)

V_geometric = V_lower + V_waist + V_upper
V_calibrated = V_geometric × 1.83
```

### Shape factor

shape_factor = 0.85 for standard flat-top acoustics.
shape_factor = 0.75 for archtops (carved top reduces effective void area).

### Calibration factor 1.83

The elliptical model systematically underestimates real guitar volumes because:
1. Guitar cross-sections are not true ellipses — the back is flatter
2. Depth tapers along the body length (not captured in section model)
3. The three-section model is a crude trapezoidal integration

| Instrument | Computed | Measured | Factor |
|-----------|---------|---------|--------|
| Martin OM | 9.72 L | 17.5 L | 1.80× |
| Martin D-28 | 11.80 L | 22.0 L | 1.86× |
| Gibson J-45 | 11.31 L | 21.0 L | 1.86× |
| **Mean** | — | — | **1.83×** |

### When to use this formula

Use for estimating volumes when measured values are unavailable.
**Always prefer directly measured volumes when available.**
Accuracy: ±1.5L for standard guitar bodies.

---

## 9. Soundhole Structural Ring Width

**Source:** Thin-shell structural analysis. Empirical floor from luthiery practice.
**Implementation:** `calculators/soundhole_calc.py → check_ring_width()`

### Formula

```
ring_width_min = max(soundhole_radius × 0.15, 6.0 mm)
```

### Status thresholds

| Status | Condition |
|--------|-----------|
| GREEN | ring_width ≥ ring_width_min × 1.5 |
| YELLOW | ring_width_min ≤ ring_width < ring_width_min × 1.5 |
| RED | ring_width < ring_width_min |

### Physical basis

The 15% of radius rule: from thin-shell structural analysis, the annular
ring of spruce surrounding the hole acts as a ring beam. The minimum ring
width for this ring beam to resist the point load from the X-brace
pressing against it under string tension is approximately r × 0.15.

The 6.0 mm absolute minimum: empirical. Below 6 mm, seasonal humidity
movement (wood expansion and contraction across the grain) exceeds the
wood's inter-fiber shear strength at the soundhole edge. In high-humidity
variation climates (e.g., Houston, TX: 30–80% RH seasonal swing), a top
can move 3–6 mm across a 400 mm span. Ring widths below 6 mm crack.

**Source citation for 15% rule:** Gore & Gilet, Vol. 1, Ch. 8.
If any reader can provide a primary structural mechanics reference
for this value, it would strengthen this documentation.

---

## 10. Soundhole Placement Validation

**Source:** Traditional rule derived from plate modal analysis.
**Implementation:** `calculators/soundhole_calc.py → validate_placement()`

### Safe zone

```
x_min = body_length × 0.20   (clear of neck block)
x_max = body_length × 0.70   (clear of tail block / lower bout structure)
```

### Traditional 1/3 position

```
x_traditional = body_length × 0.333
```

The 1/3 position is often described as historical convention.
It is also physically motivated: it places the soundhole near the antinode
of the top plate's (1,1) mode along the longitudinal axis, maximizing
the radiation coupling of air breathing through the soundhole to the
plate's primary motion. Gore & Gilet's FEA results confirm this placement
is near-optimal for coupling the Helmholtz mode to the primary plate mode.

---

## 11. Inverse Helmholtz Solver

**Source:** Analytical inversion of the Helmholtz formula.
**Implementation:** `calculators/soundhole_calc.py → solve_for_diameter_mm()`

### Method

Since f_H ∝ √A and A = πr², the relationship is:

```
A_needed = (2πf_target/c)² × V × L_eff
```

But L_eff itself depends on r (through k × r_eq), making this implicit.
A bisection search over diameter [40, 150 mm] is used, converging in
< 60 iterations to ±0.01 Hz accuracy.

```
predict(d):
    r = (d/2) / 1000
    A = π × r²
    L_eff = compute_port_neck_length(A, 2πr, top_thickness, k0, γ)
    return helmholtz_multiport(V, [{area:A, perim:2πr, thick:top_thickness}]) × PMF

bisection: lo=40, hi=150
repeat until hi-lo < 0.01:
    mid = (lo+hi)/2
    if predict(mid) < target: lo=mid else: hi=mid
```

### Multi-port variant

`solve_for_diameter_with_side_port_mm()` adds the side port as a fixed
port to the multi-port calculation, then solves for the main hole diameter
needed to achieve the target with the side port present.

---

## 12. Orthotropic Plate Modal Frequency

**Source:** Classical orthotropic plate theory. Formula from Hearmon (1946),
used by Caldersmith, Gore, and in tap-tone practice universally.

**Implementation:** `calculators/plate_design/thickness_calculator.py → plate_modal_frequency()`

### Formula

```
f_mn = (η × π/2) × √[(E_L × m²/a⁴ + E_C × n²/b⁴) / ρ] × h
```

**Variables:**

| Symbol | Meaning | Units |
|--------|---------|-------|
| f_mn | Modal frequency for mode (m,n) | Hz |
| η | Geometry/boundary condition factor | dimensionless |
| E_L | Longitudinal Young's modulus (along grain) | Pa |
| E_C | Cross-grain Young's modulus | Pa |
| ρ | Wood density | kg/m³ |
| h | Plate thickness | m |
| a | Plate length (along grain) | m |
| b | Plate width (across grain) | m |
| m, n | Mode indices | integers |

### Key relationships

- **f ∝ h**: frequency is linear in thickness — doubling thickness doubles frequency.
  This makes the inverse problem (find h for target f) analytically tractable.
- **f ∝ √(E_L/ρ)**: speed-of-sound ratio governs tone. High E_L/ρ woods (Sitka spruce)
  favor strong fundamental modes; lower E_L/ρ (cedar) shifts response.
- **f ∝ 1/a²**: frequency scales as inverse square of plate length — longer plates
  resonate lower. This is why body size strongly affects bass response.

### Boundary condition factor η

η = 1.0 for simply-supported (all four edges free to rotate but not translate).
Real guitar plates are somewhere between simply-supported (η=1.0) and
clamped (η=1.57) due to the rim glue joint and kerfing.
Typical calibrated value for assembled box: η ≈ 1.2–1.35.

### Free plate vs assembled box

Free plate measurement (tap tones): η closer to 1.0.
Assembled box (plate glued into rim): effective η increases to ~1.2–1.35.
The transfer function (γ in `thickness_calculator.py`) maps free-plate
frequency to in-box frequency. For steel-string guitars: γ ≈ 0.85–0.95.

---

## 13. Plate Thickness Inverse Solver

**Source:** Derived from §12 by inverting f ∝ h.
**Implementation:** `calculators/plate_design/inverse_solver.py → solve_for_thickness()`

### Analytical solution (SIMPLE model)

Since f ∝ h for fixed material and geometry:

```
h_target = h_ref × (f_target / f_ref)

where f_ref = plate_modal_frequency(E_L, E_C, ρ, h_ref=3mm, a, b)
```

This is a single-evaluation closed form. Converged in 1 iteration.

### Numerical solution (RAYLEIGH_RITZ model)

For multi-mode targeting, `scipy.optimize.minimize_scalar` minimizes
weighted RMS frequency error over the thickness range [h_min, h_max].

### Mahogany example

Mahogany back plate, 559×241 mm, targeting 86 Hz fundamental:
```
E_L = 9.5e9 Pa, E_C = 1.2e9 Pa, ρ = 545 kg/m³
solve_for_thickness(86 Hz) → 2.33 mm
```
This result was cross-checked against published tap-tone data for
mahogany backs of similar dimensions.

---

## 14. Archtop Arch Geometric Stiffness

**Source:** Thin-shell mechanics. The arch converts bending loads to membrane
(in-plane) forces, dramatically increasing effective stiffness.
This is the governing acoustic variable for archtop guitars.

### Formula

Torsional stiffness of a curved shell under rocking bridge load scales as:

```
k_torsional ≈ E_wood × h × (arch_height / lower_bout_width)²
```

The squared arch-rise ratio is the key term. It means:
- Arch height change has quadratic effect on stiffness
- A 4mm increase in arch height (18→22mm on a 17" body) changes
  arch_rise_ratio from 0.042 to 0.051, changing the stiffness ratio from
  0.042² = 0.00176 to 0.051² = 0.00260 — a **48% increase**.

This is approximately equivalent to changing a flat-top plate thickness
by 0.6–0.8 mm. It is why D'Aquisto, Benedetto, and D'Angelico all
converge on 18–24 mm apex arch heights for 16–17" bodies.

### Arch rise ratio benchmarks (17" body, 432 mm lower bout)

| Arch height | Rise ratio | Stiffness index |
|------------|------------|----------------|
| 16 mm | 0.037 | 0.00137 |
| 18 mm | 0.042 | 0.00176 |
| 20 mm | 0.046 | 0.00212 |
| 22 mm | 0.051 | 0.00260 |
| 24 mm | 0.056 | 0.00314 |

### Conditions

This formula gives stiffness in the torsional mode (bridge rocking).
The flat-top plate formula (§12) gives stiffness in the breathing mode.
These are orthogonal modes. On a flat-top, breathing dominates.
On an archtop, torsional dominates. **They are not directly comparable.**

---

## 15. Archtop Volume Correction for Arch Height

**Source:** Geometric calculation. Arch volume reduces internal cavity volume.

### Formula

The arch displaces internal volume approximately as:

```
ΔV_arch ≈ 0.67 × plate_projected_area × arch_height_average × shape_factor
```

For a 17" archtop, top plate projected area ≈ 0.19 m², average arch height
across top ≈ 16 mm (apex 22 mm, edge 0 mm, average ~60% of apex):

```
ΔV_top ≈ 0.67 × 0.19 × 0.016 = 0.00204 m³ = 2.04 L
ΔV_back ≈ 0.67 × 0.19 × 0.018 = 0.00229 m³ = 2.29 L (back arch higher)
```

Total volume reduction vs flat box: ~4.3 L.

### Consequence for f_H design

Raising arch height by 2 mm reduces cavity volume by approximately:
```
ΔV ≈ 0.67 × 0.19 × 0.002 = 0.000255 m³ ≈ 0.25 L
```
This shifts f_H upward by ~1–2 Hz for a 24L body.

**On an archtop, arch height change affects both stiffness AND f_H simultaneously.
This coupling does not exist on flat-tops. You cannot tune stiffness independently
of f_H on an archtop through arch geometry alone.**

---

## 16. C-Bout Radius (Sagitta Formula)

**Source:** Classical geometry. Applied to guitar body outline in this project.
**Implementation:** Planned for `calculators/body_geometry_calc.py` (not yet built).

### Formula

The C-bout is modeled as a circular arc. Given:
- `w1` = width of wider bout (upper or lower, depending on which C-bout)
- `w2` = waist width
- `chord` = body length of the transition zone (typically 15% of body length)

```
sagitta = (w1 - w2) / 2
r_cbout = (chord² + sagitta²) / (2 × sagitta)
```

### Example: Martin OM upper C-bout

```
upper_bout = 299.7 mm, waist = 241.3 mm, chord = 495 × 0.15 = 74.3 mm
sagitta = (299.7 - 241.3) / 2 = 29.2 mm
r = (74.3² + 29.2²) / (2 × 29.2) = (5520 + 852) / 58.4 = 109 mm
```

### Side bending constraint

Minimum bend radius for wood sides at ~2.5 mm thickness (species-specific):
- Mahogany: ~173 mm
- Hard Maple: ~184 mm
- Rosewood: ~165 mm
- Mesquite (Honey): ~170 mm

The Martin OM upper C-bout radius (109 mm) is well within all species limits.
The constraint bites only for very narrow waists or very wide upper bouts.
A 17" archtop with a 280 mm waist has significantly gentler C-bouts than
an OM, which is why archtop sides are generally easier to bend.

---

## 17. Nut Slot Depth

**Source:** Setup mechanics. CONSTRUCTION-001 in BACKLOG.md.

### Formula

```
slot_depth = string_diameter/2 + action_clearance - fret_crown_height
```

Standard values:
- `action_clearance`: 0.5–0.8 mm (clearance above fret when played open)
- `fret_crown_height`: from `FRET_WIRE_PROFILES` (1.0–1.5 mm for common profiles)

For a standard medium fret (1.2 mm crown) and 0.6 mm clearance:
```
slot_depth = string_dia/2 + 0.6 - 1.2
```

For a wound low E (0.41 mm radius):
```
slot_depth = 0.41 + 0.6 - 1.2 = -0.19 mm → slot bottom is ABOVE fret bottom
```
This is correct: the string rides on the fret slot's side walls, not the floor.
A slot cut too deep produces open-string buzz.

---

## 18. Setup Cascade

**Source:** Standard luthiery. CONSTRUCTION-002 in BACKLOG.md.

### Order of operations

Action adjustments are coupled. The correct sequence:

```
1. Nut slot depth → sets open-string action
2. Neck relief (truss rod) → sets mid-neck bow (usually 0.2–0.4 mm at 7th fret)
3. Saddle height → sets action at 12th fret
4. Saddle compensation → sets intonation at 12th fret
```

Adjusting in any other order requires re-checking all previous steps.

### 12th fret action formula

```
action_12th = (saddle_height - top_surface) / 2
             + neck_relief_at_7th_fret / 2
             + fret_crown_height
```

This is an approximation that assumes linear neck geometry. The actual relationship
depends on neck bow, fret levelness, and saddle position.

---

## 19. String Tension

**Source:** Physics of vibrating strings. Standard reference: Mersenne's law.
CONSTRUCTION-004 in BACKLOG.md.

### Formula

```
T = (2 × f × L)² × μ
```

Where:
- `T` = string tension (N)
- `f` = fundamental frequency (Hz)
- `L` = vibrating string length = scale length (m)
- `μ` = linear mass density (kg/m)

For a steel string: `μ = π × (d/2)² × ρ_steel`
where `ρ_steel ≈ 7850 kg/m³`.

### Total tension on a 6-string guitar

A standard light string set (.012–.053) on 645mm scale at concert pitch:

| String | Gauge (in) | μ (kg/m) | T (N) |
|--------|-----------|---------|-------|
| High e | .012 | 0.00038 | 73 N |
| B | .016 | 0.00067 | 85 N |
| G | .024w | 0.0015 | 63 N |
| D | .032w | 0.0027 | 71 N |
| A | .042w | 0.0046 | 80 N |
| Low E | .053w | 0.0073 | 90 N |
| **Total** | | | **~462 N (~47 kg)** |

String tension feeds directly into neck block sizing (GEOMETRY-005) and
top deflection modeling (CONSTRUCTION-009).

---

## 20. Acoustic Impedance

**Source:** Wave mechanics. Z = ρc is a universal result from acoustics.

### Formula

```
Z = ρ × c_wood
```

Where:
- `ρ` = wood density (kg/m³)
- `c_wood` = speed of sound in the wood (m/s)

Note: c_wood ≈ √(E_L / ρ) for longitudinal propagation along the grain.

### Acoustic transmission at back plate

When a sound wave in the cavity (dominated by air: Z_air ≈ 0.00041 MRayl)
hits the back plate (Z_back ≈ 3–4 MRayl), the energy transmission is:

```
T = 1 - ((Z2 - Z1) / (Z2 + Z1))²
```

At these Z values T ≈ 0.003 regardless of whether the back is maple, rosewood,
or mesquite. All three materials reflect ~99.7% of incident energy.
The back plate impedance dominates only at very close values (e.g., back
made of the same material as the top spruce) — which never occurs in practice.

### Material comparison for guitar backs

| Material | ρ | Z (MRayl) | Character |
|---------|---|----------|----------|
| Honduran Mahogany | 545 | 2.55 | Warm, participates in radiation |
| Black Walnut | 610 | 2.63 | Warm, moderate |
| Koa | 625 | 2.55 | Sweet, participates |
| Hard Maple | 705 | 3.08 | Bright, nearly inert |
| E. Indian Rosewood | 830 | 3.09 | Rich, nearly inert |
| Brazilian Rosewood | 835 | 3.23 | Dense, inert |
| Honey Mesquite | 950 | 3.32 | Dense, inert — exceeds rosewood |
| Texas Ebony | 965 | 4.00 | Highly inert |

---

## 21. Kerfing Geometry

**Source:** Structural mechanics of thin-walled bending. GEOMETRY-003 in BACKLOG.md.
**Implementation:** `calculators/kerfing_calc.py` (not yet built).

### Kerf slot geometry

```
kerf_depth = stock_thickness × 0.70    (70% depth rule)
web_thickness = stock_thickness × 0.30  (remaining uncut web acts as hinge)
```

### Minimum bend radius

```
min_bend_radius = web_thickness × (kerf_spacing / kerf_depth) × 10
```

Empirical factor 10 accounts for wood grain variability. Tighter keyways (smaller
kerf_spacing) give better minimum radius for the same material.

### Glue surface area

```
glue_area = stock_height × body_perimeter - (kerf_depth × kerf_count)
```

---

## 22. Fretboard Extension Mass Loading

**Source:** Plate mechanics mass addition. Derived in this project.
The 7-gram figure is specific to standard ebony/rosewood fretboard dimensions.

### Formula

```
extra_mass = (fret_position(total_frets) - fret_position(body_join_fret))
             × board_width_mm × board_thickness_mm × species_density_g_mm³
             - (same for 20-fret baseline)
```

### 22 vs 24 fret comparison (645mm scale, 14-fret join)

```
extension_22 = fret_pos(22) - fret_pos(14) = 464.1 - 357.8 = 106.3 mm
extension_24 = fret_pos(24) - fret_pos(14) = 483.9 - 357.8 = 126.1 mm
extra_extension = 126.1 - 106.3 = 19.8 mm

extra_mass = 19.8 × 50 × 6 × 0.0012 (ebony) = 7.1 grams
```

### Acoustic consequence

7 grams added to the upper plate zone suppresses higher-order plate modes
(cross-grain bending modes, second longitudinal mode) while having minimal
effect on the (1,1) fundamental. The direction of the effect is the same as
adding a heavier finish coat: slight rounding of the attack, reduced upper
harmonic definition. On mahogany-top instruments this is mildly favorable.
On spruce tops it works against the spruce's natural strength.

### Soundhole conflict (24-fret geometry)

For a 14-fret join, 96mm soundhole at 165mm from neck block:
```
soundhole_front_edge = fret_pos(14) + 165 - 48 = 357.8 + 117 = 474.8 mm from nut
fret_24 = 483.9 mm from nut
conflict = 483.9 - 474.8 = 9.1 mm (overlap)
```

The 23rd fret has 0.5 mm clearance — essentially impossible without relocation.
The 24th fret requires the soundhole to move ~19 mm deeper into the body,
which conflicts with the X-brace intersection. Resolution options:
offset soundhole, reduced soundhole diameter, or X-brace repositioned forward.

---

## 23. Side Port Perimeter Factor

**Source:** Empirical, based on port type geometry.
**Implementation:** `calculators/soundhole_calc.py → SidePortSpec`, `PORT_TYPES`

### Perimeter factor by port type

```
perim_effective = perim_circular × perimeter_factor
```

| Port type | P_factor | P/√A ratio | L_eff effect |
|-----------|----------|-----------|-------------|
| Round | 1.0 | 3.54 | Baseline |
| Oval | 1.15 | ~4.1 | +5% L_eff |
| Slot (3:1 aspect) | 2.2 | ~7.8 | Significantly longer L_eff |
| Chambered | 1.0 + tube_length/1000 | — | Tube adds directly to L_eff |

### Slot port

A slot port (common on ukuleles) has a much larger perimeter for the same area
as a round port. This increases L_eff substantially, which **reduces** f_H
for the same port area compared to a round port.
A luthier using a slot side port as a f_H tuning tool is working
against the expected direction unless this is accounted for.

---

## 24. Two-Cavity Helmholtz

**Source:** Coupled resonator theory. Maccaferri application described in
Gore & Gilet and Bellow's analysis of Selmer guitars.
**Implementation:** `calculators/soundhole_calc.py → compute_two_cavity_helmholtz()`

### Two uncoupled resonators (approximation)

```
f_H1 = Helmholtz(V_main, ports_main_to_outside)   → main body to outside air
f_H2 = Helmholtz(V_int, aperture_to_main_cavity)   → resonator to body
```

### Coupling correction

When f_H1 and f_H2 are close, the modes repel each other:

```
Δ = |f_H1 - f_H2| × 0.10   (10% repulsion factor — empirical)
f_H1_coupled = f_H1 ∓ Δ/2
f_H2_coupled = f_H2 ± Δ/2
```

### Accuracy warning

The two-uncoupled-resonators approximation produces ±10 Hz accuracy.
The exact solution requires the full 2×2 coupled oscillator eigenvalue problem:

```
det([K_1 - ω²  -κ    ] = 0
    [-κ     K_2 - ω²])
```

Where κ = coupling coefficient proportional to aperture area.
This has not been implemented. For a Maccaferri reproduction where the
exact resonator peaks matter, use the exact eigenvalue solution.

---

## 25. Neck Angle Calculation

**Source:** Geometric derivation. GEOMETRY-001 in BACKLOG.md.
**Implementation:** `calculators/neck_angle_calc.py` (not yet built).

### Formula

```
neck_angle_deg = arctan(
    (bridge_height_above_body - fretboard_height_at_body_join)
    / distance_nut_to_bridge
)
```

Where:
- `bridge_height_above_body` = saddle_projection + bridge_base_height + top_thickness
- `fretboard_height_at_body_join` = fret_crown_height + fretboard_thickness
- `distance_nut_to_bridge` ≈ scale_length + saddle_compensation_avg

### Target neck angle by instrument type

| Type | Typical neck angle | Notes |
|------|------------------|-------|
| Flat-top acoustic | 1–2° | Saddle 8–14mm projection |
| Archtop jazz | 3–5° | Saddle 8–14mm, arch requires more |
| Classical | 0° | Typically straight, achieved by neck block geometry |
| Electric (set neck) | 0–4° | Varies by bridge height |

### Archtop special case

On archtops, neck angle is constrained by:
1. Arch height at upper bout → affects neck block seating
2. Required saddle height range (8–14mm for good break angle and tone)
3. Scale length and bridge foot placement

A 2mm increase in upper bout arch height requires approximately:
```
Δneck_angle ≈ arctan(Δarch_height / nut_to_bridge_mm)
             = arctan(2 / 645) = 0.18°
```

---

## 26. Error Log

All significant errors made during the derivation of formulas in this document
are recorded here with correction. This is the record demanded by peer review.

---

### Error 1 — Neck join comparison: 12 vs 14 fret stated instead of 12 vs 13 fret

**Session:** March 2026 lutherie discussion session.

**What was stated (incorrectly):**
The neck join comparison was framed as 12-fret vs 14-fret, computing a 24mm
bridge position shift as the relevant quantity.

**Correction supplied by:** Ross Echols (session participant).

**What is correct:**
The traditional flat-top acoustic alternative configuration under discussion
is **12-fret vs 13-fret body join**. The 14-fret join is standard, not the
alternative. The relevant comparison is:

```
12-fret join: bridge 322.5mm from neck block
13-fret join: bridge 310.3mm from neck block  (+12.2mm shift toward neck)
```

12.2mm, not 24mm. The coupling efficiency difference between 12-fret and
13-fret join is negligible by the mode shape calculation (0.998 vs 0.999).
The acoustic argument for 13-fret on all-mahogany instruments rests on the
cross-grain mode coupling ratio argument, not on a significant coupling
efficiency difference.

**14-fret flat-top guitars exist** (Martin has built them; custom builders
use them) and the formula in §2 correctly handles any join fret value.
The 13-fret configuration is the traditional alternative for OOO-style
instruments and is the comparison the all-mahogany argument refers to.

---

### Error 2 — F-hole archtop air resonance stated as 120 Hz

**Source document:** Uploaded reference document (`Acoustic_Guitar_Sound_Hole_Design.docx`).

**What was stated (in the source):**
Archtop f-holes produce air resonance at ~120 Hz.

**What the physics shows:**
The f-hole perimeter correction (see §5) drives L_eff to 50–52mm for a
standard 23×110mm f-hole. At this L_eff and typical archtop volumes (24L),
the predicted air resonance is **~89 Hz**, not 120 Hz.

The 120 Hz figure refers to the **top plate mode**, not the Helmholtz air
resonance. The two are distinct quantities and should not be conflated.

This was noted explicitly in the soundhole designer README and corrected
in all presets. The Benedetto 17" preset uses 90 Hz as the f_H target.

---

### Error 3 — Body volume calibration not applied initially

**What occurred:**
The `volume_from_dimensions()` function was initially written without
the 1.83× calibration factor, producing volumes of ~9.7L for a Martin OM.
The function was then calibrated against measured volumes (17.5L, 22.0L, 21.0L)
and the factor 1.83 was determined and applied.

**Lesson:** The elliptical cross-section model significantly underestimates
real guitar volumes. Any use of this formula without the calibration factor
will produce Helmholtz predictions that are too high by ~35%.

---

*Document maintained by Ross Echols, PE #78195*
*For The Production Shop — luthiers-toolbox-main*
*Last updated: March 2026*
