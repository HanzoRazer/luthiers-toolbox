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
- [Appendix A — Guitar body as speaker enclosure](#appendix-a--guitar-body-as-speaker-enclosure)

**Part II — Design Problems**
39. [Modal Area Coefficient A_n](#39-modal-area-coefficient-a_n)
40. [Brace Pattern as Stiffness Field D(x,y)](#40-brace-pattern-as-stiffness-field-dxy)
41. [Radiation Power P_rad](#41-radiation-power-p_rad)
42. [Brace Pattern Optimization](#42-brace-pattern-optimization)

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

## Appendix A — Guitar body as speaker enclosure

**Priority:** High — stated core product promise: outline editor behaves as a **speaker cabinet designer**, acoustic stack as **port calculator**.

**Prerequisite:** Body outline editor stable and trusted (2D outline in / out).

### Problem

The **body outline editor** and the **acoustic stack** (Helmholtz, soundhole sizing, `soundhole_calc`) are **not coupled** in product UX today. Volume for Helmholtz still flows from **dimensional presets** (§8 / `volume_from_dimensions` / `acoustic_body_volume.py`), not from the **user’s drawn outline**.

### Target coupling layer

1. **Outline → V:** From closed outline (and depth model), compute **enclosed air volume** \(V\) available to the Helmholtz mode (or a defined effective \(V\)).
2. **V → port:** Fix target air resonance \(f_H\) (or band); run **inverse Helmholtz** (§11, `solve_for_diameter_mm` and variants) to get **soundhole diameter / area** (or multi-port split).
3. **Canvas:** Draw **suggested soundhole** (and tolerances) on the same canvas as the outline — **cabinet + port** in one view.

### Missing mathematics (planning IDs)

| ID | Topic | Notes |
|----|--------|--------|
| **§37** | **Body outline → air volume** | §8 gives volume from **bout/length/depth numbers**, not from a **closed polygon** or Bézier outline. Need: area integral in outline plane × **depth law** (see §38), or calibrated 2.5D surrogate. |
| **§38** | **Depth profile from body style** | Map **body style** (dreadnought, OM, classical, archtop, …) to a **depth model** \(z(x,y)\) or section stack: endblock/neck depths, taper, arch height — so outline + style → \(V\). |

These are **not** yet full numbered sections in this file; they are **reserved** for the derivations that close the geometry–acoustics loop.

### Relation to existing implementation

- §8, `calculators/acoustic_body_volume.py`, `volume_from_dimensions()` — **proxy** for \(V\) until §37 exists.
- §11, `solve_for_diameter_mm()` — **inverse port** once \(V\) and \(f_H\) are fixed.
- `instrument_geometry/body/parametric.py` — outline **generation** from dimensions; inverse direction (outline → metrics) is separate work.

---

# Part II — Design Problems

The preceding sections (§1–§38) treat acoustic and geometric quantities as **forward problems**: given a geometry, predict a frequency or resonance. The plate modal formula says "this thickness produces that frequency." The Helmholtz formula says "this soundhole produces that air resonance."

The following sections treat the same physics as **design problems**: given a target acoustic behavior, find the geometry that produces it. This requires defining what "acoustic behavior" means precisely — not just frequency, but **how much air a vibrating mode actually displaces**. The modal area coefficient A_n is that definition.

This shift — from analysis to synthesis — is where lutherie becomes engineering design rather than measurement and description.

---

## 39. Modal Area Coefficient A_n

**Source:** Plate dynamics and acoustic radiation theory. The modal area coefficient is standard in loudspeaker design (where it appears as Sd, the effective diaphragm area) but rarely formalized in lutherie. Fletcher & Rossing, *Physics of Musical Instruments*, Ch. 3 and 9. Skudrzyk, *Foundations of Acoustics*, Ch. 12.

**Implementation:** Planned for `tap_tone_pi/analysis/modal_area.py` (not yet built). Requires Chladni pattern measurement hardware — see SPRINTS.md Research Track.

### Formula

The modal area coefficient for mode n is the integral of the mode shape over the plate surface:

```
A_n = ∫∫_S φ_n(x,y) dS
```

**Variables:**

| Symbol | Meaning | Units |
|--------|---------|-------|
| A_n | Modal area coefficient for mode n | m² |
| φ_n(x,y) | Normalized mode shape (eigenvector) of mode n | dimensionless |
| S | Plate surface area | m² |

The mode shape φ_n is normalized such that max|φ_n| = 1. The sign of φ_n indicates displacement direction (toward listener = positive, away = negative).

### Physical interpretation

A_n answers the question: **"How much of this mode actually pushes air?"**

Consider three mode shapes on a guitar top:

1. **Piston mode (1,1):** The entire plate moves in phase. φ_n(x,y) > 0 everywhere. The integral A_n is large — nearly equal to the plate area S.

2. **Dipole mode (2,1):** Half the plate moves up while half moves down. The positive and negative regions cancel in the integral. A_n ≈ 0.

3. **Distributed mode (3,2):** Multiple regions move in different phases. Partial cancellation. A_n is moderate.

### Classification by A_n

| Mode character | A_n magnitude | Radiation behavior |
|---------------|---------------|-------------------|
| Piston-like | A_n ≈ S | Strong monopole radiation |
| Dipole | A_n ≈ 0 | Radiation cancels (acoustic short-circuit) |
| Distributed | 0 < A_n < S | Partial radiation, frequency-dependent |

### Speaker analogy

A_n is the soundboard equivalent of **Sd** (speaker diaphragm effective area).

A 12" woofer moves more air than a 4" midrange driver at the same excursion — not because it moves farther, but because it has larger Sd. Similarly, a piston-like plate mode (large A_n) radiates more strongly than a dipole mode (small A_n) at the same velocity amplitude — the dipole's regions cancel.

**This is why mode shape matters more than frequency.** Two guitars with identical tap tone frequencies can sound radically different if one has piston-like low modes (large A_n, strong bass radiation) and the other has dipole modes at the same frequencies (small A_n, weak bass radiation).

### Measurement method

Direct measurement of φ_n(x,y) requires visualizing the mode shape. The classical method:

1. **Chladni patterns:** Sprinkle sand or salt on the plate, excite at resonant frequency f_n, observe nodal lines where sand accumulates
2. Nodal lines are where φ_n(x,y) = 0
3. Regions between nodal lines have opposite phase
4. Approximate A_n by summing signed region areas

Modern alternatives: laser vibrometry (expensive), holographic interferometry (specialized).

### Conditions and limitations

- **Assumes linear vibration:** A_n is computed from the eigenmode, which assumes small-amplitude linear response. At high excitation levels, mode shapes distort.
- **Frequency-independent:** A_n characterizes the mode shape geometry, not the radiation efficiency at any particular frequency. The radiation efficiency σ_n (see §41) captures the frequency dependence.
- **Single mode:** A_n applies to one mode at a time. Real plate motion is a superposition of modes; total radiation requires summing modal contributions (see §41).

### Known edge cases

- **Coupled modes:** When two modes have similar frequencies, they can couple and distort each other's shapes. The individual A_n values become ambiguous near the coupling region.
- **Nonuniform damping:** High local damping (at a brace joint, for example) can distort mode shapes from their undamped forms.

---

## 40. Brace Pattern as Stiffness Field D(x,y)

**Source:** Plate mechanics. The concept of treating discrete braces as a continuous stiffness field appears in Gore & Gilet, *Contemporary Acoustic Guitar Design*, Vol. 1, Ch. 5–6. Formalization as D(x,y) is standard in composite plate theory (Whitney, *Structural Analysis of Laminated Anisotropic Plates*).

**Implementation:** Planned for `calculators/plate_design/stiffness_field.py` (not yet built).

### Formula

The total flexural rigidity at any point (x,y) on the plate is the sum of plate and brace contributions:

```
D_total(x,y) = D_plate(x,y) + Σ_k D_brace,k(x,y)
```

**Variables:**

| Symbol | Meaning | Units |
|--------|---------|-------|
| D_total(x,y) | Total flexural rigidity at (x,y) | N·m |
| D_plate(x,y) | Plate flexural rigidity (may vary with thickness) | N·m |
| D_brace,k(x,y) | Contribution of brace k to rigidity at (x,y) | N·m |

### Plate flexural rigidity

For an isotropic plate:
```
D_plate = E × h³ / (12 × (1 - ν²))
```

For an orthotropic plate (wood):
```
D_L = E_L × h³ / 12      (along grain)
D_C = E_C × h³ / 12      (across grain)
```

Where:
- E, E_L, E_C = Young's modulus (isotropic, longitudinal, cross-grain)
- h = plate thickness
- ν = Poisson's ratio

### Brace contribution

Each brace k adds stiffness along its centerline:
```
D_brace,k(x,y) = E_brace × I_k × δ_w(x,y; brace_k)
```

Where:
- E_brace = Young's modulus of brace material
- I_k = moment of inertia of brace cross-section = b×h³/12 for rectangular
- δ_w(x,y; brace_k) = spreading function — 1 along brace centerline, decaying over width w

The spreading function accounts for the fact that a brace stiffens not just the line it occupies but a finite width around it.

### Physical interpretation: Two design dials

**Dial 1: Thickness → Frequency**

Changing plate thickness changes D_plate everywhere uniformly (as h³). This shifts all modal frequencies proportionally (f ∝ √D ∝ h). Thickness is a "frequency dial" — turn it up, all modes go up together.

**Dial 2: Bracing → Mode Shape**

Adding or moving braces changes D(x,y) locally. This changes which mode shapes are preferred. A brace across a potential antinode suppresses that mode relative to others. A brace along a potential nodal line has little effect on that mode.

Bracing is a "mode shape dial" — it doesn't just shift frequencies, it reshapes which modes exist and how they distribute energy.

### Speaker analogy

In loudspeaker design, cone profiles and surrounds serve the same function: controlling mode shape at the expense of frequency. A shallow cone radiates more pistonic motion at the cost of lower efficiency. A steep cone is efficient but breaks up into complex modes earlier.

The guitar maker's bracing pattern is analogous to the loudspeaker designer's cone geometry — both are mode-shape engineering tools, not just frequency tuners.

### Conditions and limitations

- **Quasi-static assumption:** The D(x,y) representation assumes brace attachment is rigid. In reality, glue joints have finite stiffness; very high-frequency modes can "see through" braces.
- **Neglects mass distribution:** The stiffness field D(x,y) affects frequencies through the eigenvalue equation, but mass distribution also matters. A brace adds both stiffness and mass; the net effect on frequency depends on both.
- **Continuous approximation:** Treating discrete braces as a continuous field is valid when plate wavelengths are larger than brace spacing. For very high modes, discrete brace positions matter individually.

### Design implication

**Thickness tuning is frequency-first thinking.**
**Brace pattern tuning is radiation-first thinking.**

The latter is more powerful but requires mode shape knowledge (§39). Without knowing A_n for each mode, brace changes are trial-and-error. With A_n data from Chladni measurements, brace design becomes targeted: suppress dipole modes, enhance piston modes.

---

## 41. Radiation Power P_rad

**Source:** Acoustic radiation from vibrating surfaces. Fletcher & Rossing, *Physics of Musical Instruments*, Ch. 3.5. Standard acoustics result; application to guitar plates is less common outside academic literature.

**Implementation:** Planned for `calculators/plate_design/radiation_power.py` (not yet built).

### Formula

Total acoustic power radiated by a vibrating plate:

```
P_rad = ½ × ρ₀ × c₀ × Σ_n σ_n × |v_n|² × A_n²
```

**Variables:**

| Symbol | Meaning | Units | Typical value |
|--------|---------|-------|---------------|
| P_rad | Total radiated acoustic power | W | 10⁻⁵ – 10⁻³ |
| ρ₀ | Air density | kg/m³ | 1.21 |
| c₀ | Speed of sound in air | m/s | 343 |
| σ_n | Radiation efficiency of mode n | dimensionless | 0.01 – 1.0 |
| v_n | Modal velocity amplitude | m/s | 10⁻³ – 10⁻¹ |
| A_n | Modal area coefficient (§39) | m² | 0 – 0.1 |

ρ₀ × c₀ ≈ 415 Pa·s/m is the characteristic acoustic impedance of air.

### Radiation efficiency σ_n

The radiation efficiency depends on the ratio of acoustic wavelength to plate size:

```
ka = 2πf × (characteristic_plate_dimension) / c₀
```

- **ka << 1** (low frequency): σ_n ≈ (ka)⁴ for monopole, (ka)⁶ for dipole — very inefficient
- **ka ≈ 1** (coincidence): σ_n rises toward 1
- **ka >> 1** (high frequency): σ_n → 1

For a guitar top (~0.4m characteristic dimension):
- At 100 Hz: ka ≈ 0.7, σ_n ≈ 0.1–0.3
- At 500 Hz: ka ≈ 3.7, σ_n ≈ 0.8–1.0

### Physical interpretation

**Power scales with A_n squared.** Doubling the modal area coefficient quadruples the radiated power from that mode.

This is why piston modes (large A_n) dominate low-frequency radiation and dipole modes (A_n ≈ 0) contribute little even if they have large velocity amplitude. The cancellation is quadratic, not linear.

### Speaker analogy

In loudspeaker engineering, the equivalent formula appears as:

```
P_rad = ½ × ρ₀ × c₀ × σ × |v|² × Sd²
```

Where Sd is the diaphragm area. The guitar top's multiple modes each act as their own "driver" with effective area A_n. The total sound is the sum of these modal drivers.

### Conditions and limitations

- **Far-field assumption:** The formula gives power radiated to infinity. Near-field (close to the plate) intensity patterns are more complex.
- **Neglects acoustic coupling:** Modes can couple acoustically through the air cavity. The Helmholtz resonance (§4) is one such coupling — it modifies the effective σ_n near f_H.
- **Linear superposition:** The sum over modes assumes modes don't interact nonlinearly. Valid for typical playing levels; breaks down at very high excitation.
- **Neglects back radiation:** Guitar backs also radiate, potentially out of phase with the top. Total guitar radiation requires summing top and back contributions with proper phase.

### Design insight

To maximize bass radiation:
1. **Maximize A_n for low modes** — design bracing so low modes are piston-like
2. **Avoid dipole cancellation** — asymmetric bracing can convert symmetric dipole modes to net-radiating asymmetric modes
3. **Accept frequency-efficiency tradeoff** — σ_n is low at low frequencies regardless of mode shape; thick low-frequency modes are inherently quieter than thin high-frequency modes

---

## 42. Brace Pattern Optimization

**Source:** Structural optimization theory applied to instrument acoustics. Academic treatments: Elejabarrieta et al., "Coupled modes of a guitar as a function of brace shape" (Applied Acoustics, 2000); Torres & Boullosa, "Optimization of a guitar top plate" (JASA, 1996).

**Implementation:** Planned for `calculators/plate_design/brace_optimizer.py` (not yet built). Requires §39–41 infrastructure.

### Optimization problem statement

```
maximize:   Σ_n w_n × A_n² × σ_n(f_n)
subject to: f_1 ∈ [f_target - Δ, f_target + Δ]     (fundamental frequency window)
            max_deflection ≤ d_max                  (structural constraint)
            max_stress ≤ σ_allow                    (strength constraint)
            total_mass ≤ m_budget                   (mass budget)
```

**Variables:**

| Symbol | Meaning | Units |
|--------|---------|-------|
| w_n | Weighting factor for mode n | dimensionless |
| A_n | Modal area coefficient (§39) | m² |
| σ_n(f_n) | Radiation efficiency at mode n frequency | dimensionless |
| f_1 | Fundamental plate frequency | Hz |
| d_max | Maximum allowable static deflection under string load | mm |
| σ_allow | Allowable stress in wood | MPa |
| m_budget | Total allowed brace + plate mass | kg |

### Weighting factors w_n

The builder's tonal preference enters through weighting:

| Preference | w_n distribution |
|------------|-----------------|
| Bass emphasis | High w_1, w_2; low w_n for n > 3 |
| Balanced | w_n ∝ 1/n (declining with mode number) |
| Treble/clarity | Lower w_1, w_2; higher w_n for n = 3–6 |

### Practical optimization approach

Full numerical optimization over brace positions is computationally expensive and requires accurate FEA. The practical closed-loop method:

1. **Start with traditional brace pattern** (X-brace, ladder, fan — per instrument family)
2. **Measure (f_n, A_n) pairs** using tap tones + Chladni patterns
3. **Identify problem modes:** modes with low A_n that should radiate, or modes at wrong frequencies
4. **Modify brace pattern** to address specific problems:
   - Move brace away from an antinode to increase that mode's A_n
   - Add brace across antinode to suppress a mode
   - Scallop brace to reduce local stiffness
   - Taper brace ends to smooth stiffness transitions
5. **Re-measure** and iterate

### Speaker analogy

Loudspeaker designers use the same iterative approach:
1. Start with known cone/surround design
2. Measure frequency response and breakup modes
3. Modify cone profile, add damping, adjust surround stiffness
4. Re-measure

The guitar maker's brace carving is analogous to the loudspeaker designer's cone profiling — both are mode-shape engineering through iterative measurement and modification.

### Conditions and limitations

- **Local optima:** Brace pattern optimization is highly nonlinear. There are many local optima; global optimization is impractical for continuous brace shape variables.
- **Manufacturing constraints:** Theoretical optima may require brace shapes that are impractical to carve or glue. Real optimization must include manufacturing feasibility.
- **Uncertainty:** Wood properties vary piece-to-piece. An optimized pattern for one plate may not be optimal for another. Robust optimization (optimizing for average performance across property variation) is more realistic than point optimization.
- **Coupled objectives:** The structural constraints (deflection, stress) compete with acoustic objectives. A stiffer, heavier bracing pattern is safer but acoustically dead. The art is in the tradeoff.

### Physical interpretation

**This closes the loop from measurement to design.**

Without A_n data, brace changes are guided only by tradition and trial-and-error. With A_n data from Chladni measurements, the luthier knows exactly which modes radiate poorly and can target those modes specifically.

This is the difference between:
- "I thinned the X-brace and it sounds better" (anecdote)
- "Mode 2 was dipole-like (A_2 = 0.003 m²); scalloping the X-brace converted it to monopole-like (A_2 = 0.018 m²), increasing its contribution to P_rad by 36×" (engineering)

Both statements may describe the same modification. The second one is reproducible.



---

## 43. Shell Stiffness from Dome Radius

A domed back plate behaves differently than a flat plate. The curvature introduces **membrane stiffness** that adds to the flexural stiffness D(x,y) from §40.

### Formula

**Frequency increase from doming:**

```
f_domed = f_flat × √(1 + C × (L/R)²)
```

**Sagitta (dome height at center):**

```
s = L² / (8R)
```

### Variables

| Symbol | Description | Units |
|--------|-------------|-------|
| R | Dome radius | m |
| L | Effective span (lower bout width) | m |
| s | Sagitta (dome height) | m |
| C | Calibration constant | dimensionless |
| f_flat | Modal frequency of equivalent flat plate | Hz |
| f_domed | Modal frequency of domed plate | Hz |

### Calibration constant C

Start with **C = 10** as a default. This value produces:
- 15ft back radius over 559mm span → ~7% frequency increase
- 25ft radius over same span → ~2.5% increase

The constant C encapsulates:
- Material-dependent membrane-to-flexural stiffness ratio
- Mode shape effects (different modes respond differently to curvature)
- Boundary condition influences

Refine C empirically by comparing predicted vs. measured frequencies on actual domed plates.

### Physical interpretation

**Tighter dome (smaller R) → higher membrane stiffness N → higher modal frequencies.**

The dome acts like a pre-tensioned drumhead. Even without changing plate thickness or bracing, curving the plate stiffens it. This is why:
- Classical guitar backs (flat or nearly flat) are more flexible
- Steel-string backs (15-25ft radius typical) are stiffer
- Archtop backs (tight radius, carved) are very stiff

### Connection to §40: Additive stiffness mechanisms

The total back plate stiffness combines:
1. **Flexural stiffness D(x,y)** — from plate thickness and bracing (§40)
2. **Membrane stiffness N(x,y)** — from dome curvature (this section)

Both contribute to the eigenvalue problem that determines modal frequencies. They are **additive** — a lightly braced but tightly domed back can have similar stiffness to a heavily braced flat back.

This gives the luthier two independent "dials":
- Bracing pattern controls D(x,y)
- Dome radius controls N(x,y)

### Design table: Typical back radii

| Radius (ft) | Radius (m) | Character |
|-------------|------------|-----------|
| Flat | ∞ | Maximum flexibility, classical style |
| 40 | 12.2 | Very subtle dome |
| 28 | 8.5 | Light dome (flamenco, some classical) |
| 20 | 6.1 | Moderate (smaller steel-string) |
| 15 | 4.6 | Standard steel-string |
| 12 | 3.7 | Pronounced dome (jumbo, slope-shoulder) |
| 10 | 3.0 | Aggressive (archtop territory) |

### Implementation

```javascript
// tools/backRadiusCalculator.js

import { domeCalc, sweepRadii, buildBackRadiusSummary } from './backRadiusCalculator.js';

// Single calculation
const result = domeCalc(15, 410);  // 15ft radius, 410mm span
// → { sagitta_mm: 3.44, percentIncrease: 7.2, ... }

// Sweep radii for design comparison
const sweep = sweepRadii(410, [10, 15, 20, 25, 30]);

// Full summary with recommendation
const summary = buildBackRadiusSummary(410);
```

### Conditions and limitations

- **Small dome approximation:** Formula assumes s << R (sagitta much smaller than radius). Valid for typical guitar backs where s < 10mm.
- **Isotropic assumption:** Real wood is orthotropic. The membrane stiffness effect varies with grain direction.
- **Mode-dependent:** Different modes respond differently to curvature. The calibration C is an average; individual modes may deviate.
- **Does not replace tap tuning:** This formula predicts the *direction* and *magnitude* of frequency change, not absolute frequencies. Use it to understand why a domed back is stiffer, not to replace measurement.

---

## 44. Longitudinal Body Radius Pairs and Wood Quality Mapping

The top and back of a steel-string acoustic guitar are radiused to **different** values, forming a **two-radius system** `(R_top, R_back)`. The ratio and absolute values of this pair are not arbitrary tradition — they are an acoustic decision that maps directly to wood quality, body size, and intended playing context.

§43 supplied the per-plate shell-stiffness correction. §44 applies that correction independently to top and back, and proposes a **design hypothesis** linking the radius pair to acoustic intent.

> **Design hypothesis: Ross Echols (PE #78195),** derived from Hazen-Williams flow optimization in irrigation system design. 32ft radius identified as the hydraulic balance point for energy distribution in spray field systems. Applied to acoustic plate energy distribution as an **untested cross-domain hypothesis**. Validation requires physical measurement (see §44 validation method below).

### The two-radius system

```
R_top  = top plate longitudinal radius   (typically larger)
R_back = back plate longitudinal radius  (typically smaller)
```

The ratio `R_top / R_back` defines the acoustic balance between top stiffness and back stiffness. A larger ratio means a comparatively stiffer back relative to the top — pushing the back toward "rigid reflector" behavior. A smaller ratio means top and back are closer in compliance — allowing the back to participate as a passive radiator.

### Industry reference points

| Builder | R_top (ft) | R_back (ft) | Ratio | Notes |
|---------|-----------:|------------:|------:|-------|
| Martin standard | 35 | 15 | 2.33 | Historical default — premium wood era |
| Martin alternate | 30 | 10 | 3.00 | Tighter top, stiffer back |
| Taylor (some models) | 40 | 10 | 4.00 | Flat top + stiff back, premium Sitka |
| Gibson J-45 | 35 | 15 | 2.33 | Same as Martin standard |
| **Ross experiment A** | **32** | **8** | **4.00** | Laminate / cheap wood target |
| **Ross experiment B** | **32** | **12** | **2.67** | Mid-grade solid target |
| **Ross experiment C** | **32** | **16** | **2.00** | Premium solid target |

### Per-plate shell correction (extends §43)

The shell-stiffness correction from §43 applies independently to each plate:

```
f_top_domed  = f_top_flat  × √(1 + C × (L_top / R_top)²)
f_back_domed = f_back_flat × √(1 + C × (L_back / R_back)²)
```

where `L_top` and `L_back` are the effective spans of each plate (often the lower bout width).

> **Calibration constant note:** A single global `C` is used here as in §43. `C_top` and `C_back` may differ due to material differences (spruce top vs hardwood back) and grain orientation (top is end-grain to bout direction; back is typically book-matched flat-grain). **The split is deferred pending physical calibration data.**

### The 32ft hydraulic balance hypothesis

In agricultural irrigation system design, the Hazen-Williams equation governs flow velocity vs. head loss in pipe networks feeding spray circles. Across many installations using ½ HP supply pumps, **a 32ft spray circle radius emerges as the hydraulic balance point** — large enough to avoid valve control problems (which plague <14ft circles) and small enough to avoid drift problems from oversized droplets (>35ft circles).

The cross-domain hypothesis: **the same balance point may apply to acoustic energy distribution across a guitar top plate.** Too flat a top is too compliant — energy disperses without efficient radiation. Too tight a top is too stiff — the plate cannot move as a coherent piston for low-frequency modes. The 32ft top radius is the working hypothesis for the acoustic balance point.

This is an **untested hypothesis**. It is included here as a documented design intent, not as established physics. The validation method below describes how to test it.

### Wood quality to radius pair mapping

| R_top / R_back | Wood tier | Back behavior | Mechanism |
|----------------|-----------|---------------|-----------|
| 32ft / 8ft | Laminate / cheaper solid | **Rigid reflector** | Top does all the work; tight back removes wood-quality variance from back contribution. A_n_back ≈ 0 by design. |
| 32ft / 12ft | Mid-grade solid | **Transition zone** | Back partially active. Good all-around balance for mid-tier hardwoods. |
| 32ft / 16ft | Premium solid | **Passive radiator** | Back participates as a coupled radiator. Requires premium wood to realize the benefit. |
| 35ft / 15ft (Martin) | Premium solid | Moderately active | Industry historical default for high-grade Adirondack/Sitka tops. |
| 40ft / 10ft (Taylor) | Premium solid | Inert reflector | Maximum top compliance + rigid back. Top-dominant projection. |

### Body size to radius pair mapping

The optimal radius pair correlates with body size and neck-joint position:

| Body class | Examples | Suggested R_top / R_back | Rationale |
|-----------|----------|-------------------------:|-----------|
| **Large** | Dreadnought, Jumbo | 35–40ft / 12–15ft | Large back area can participate as passive radiator if wood permits |
| **Mid** | OM, OOO, 000, 14-fret | 32ft / 12ft | Transition zone — back partially active |
| **Mid (13-fret)** | OOO, 000 with 13-fret | 32ft / 8ft | Bridge sits more centrally → top needs more support, back as reflector |
| **Small** | Parlor, 0, 00 | 30–32ft / 8ft | Top-dominant by necessity; near-field player listens to top |

### Why 13-fret bodies favor tighter back radius

A 13-fret neck-joint shifts the bridge toward the body center compared to a 14-fret joint of the same scale length. This reduces the available top area **behind** the bridge — the region most responsible for low-frequency top motion. The structural consequence:

- Less top area behind the bridge → top needs more longitudinal support
- A 32ft top (slightly tighter than Martin's 35ft) provides that support
- A tight back (8ft) removes the back as a variable, focusing all radiation through the top
- Player sits in near-field → direct top radiation dominates what they hear; back radiation reflects off the room and contributes less to the player's perception

This is why parlor and OOO 13-fret guitars built with 32ft/8ft are not making a compromise — they are matched to the acoustic situation.

### Validation method (Chladni mode-shape comparison)

The wood-quality and 32ft hypotheses can be tested with a controlled three-body experiment:

1. **Build three identical bodies** — same top wood, same back wood, same bracing pattern, same dimensions, same scale length. **Vary only `R_back`:**
   - Body A: `R_top = 32ft`, `R_back = 8ft`
   - Body B: `R_top = 32ft`, `R_back = 12ft`
   - Body C: `R_top = 32ft`, `R_back = 16ft`
2. **Tap-test each body** at the bridge and at the back center. Record A0 (Helmholtz), T1 (top main), B1 (back main) frequencies.
3. **Chladni-pattern each back plate** at the B1 frequency to extract the mode shape `φ_back(x,y)`.
4. **Calculate `A_n_back`** for each body using the §39 modal area coefficient formula.
5. **Predict `f_back` for each body** using §43 with the global `C` constant.
6. **Fit `C`** to minimize prediction error across the three bodies.

Predicted outcomes if the hypothesis holds:
- `A_n_back(Body A)` ≈ 0 → back is acoustically inert, all radiation from top
- `A_n_back(Body C)` >> 0 → back is acoustically active
- `f_back(Body A)` is the highest of the three
- `C` converges to a value in the range 5–20 (matching §43's first-pass default of 10)

### Speaker analogy

| Speaker concept | Guitar radius pair equivalent |
|-----------------|------------------------------|
| Sealed enclosure (rigid back) | Tight back radius (8ft) — back is a rigid wall |
| Vented / passive radiator enclosure | Loose back radius (15ft+) — back contributes radiation |
| Cone profile | Top brace pattern + top radius |
| Surround compliance | Top radius (`R_top`) |
| Wood quality matching | Driver-to-enclosure matching |

A 32ft/8ft guitar is an acoustic-suspension speaker. A 35ft/15ft Martin is a vented enclosure. Both are correct designs — for different drivers (woods).

### Conditions and limitations

- **Hypothesis status:** The 32ft hydraulic balance point is an **untested** cross-domain inference. No published acoustic measurement currently validates it.
- **Two-cylinder approximation:** Real radiused tops and backs are sections of cylinders along one axis (longitudinal) and approximately flat along the other (cross-grain). The §43 spherical-shell formula is an approximation when applied to a cylindrical section.
- **Wood-tier mapping is qualitative:** "Cheap," "mid-grade," and "premium" are not yet quantified. Future work should bind these tiers to measured `E_L`, density, and damping values from `wood_species.json`.
- **Calibration C is shared between top and back:** Deferred — see calibration constant note above.
- **Validation requires three identical bodies:** Wood variation between bodies will introduce noise. Use the same flitch for all three tops and the same flitch for all three backs.

### Implementation

```javascript
// tools/backRadiusCalculator.js — §44 functions

import { radiusPairCalc, INDUSTRY_RADIUS_PAIRS, suggestWoodTier } from './backRadiusCalculator.js';

// Per-plate shell corrections for a radius pair
const result = radiusPairCalc(32, 8, 410);
// → { top: {...}, back: {...}, ratio: 4.0, woodTier: 'laminate_or_cheap_solid', backBehavior: 'rigid_reflector', ... }

// Inspect the five industry reference points
console.log(INDUSTRY_RADIUS_PAIRS);

// Get wood tier suggestion from a custom radius pair
const tier = suggestWoodTier(32, 12);
// → 'mid_grade_solid'
```

### Connection to other sections

- **§39 Modal Area Coefficient `A_n`:** §44 predicts that 32ft/8ft drives `A_n_back → 0`. The validation method measures this directly.
- **§40 Brace pattern as `D(x,y)`:** Bracing and radius are **independent stiffness dials**. A lightly braced tightly domed back can match a heavily braced flat back (see §43 "Connection to §40").
- **§42 Brace pattern optimization:** Once `C` is calibrated from §44 validation data, brace optimization can include radius as a free parameter.
- **§43 Shell stiffness from dome radius:** §44 is the per-plate, paired-radius application of §43.
- **§14 Archtop arch geometric stiffness:** §43 already supersedes §14 for the back. §44 extends the framework to the top as well, since steel-string tops are also longitudinally radiused (just less aggressively than archtop carved tops).

---

*Document maintained by Ross Echols, PE #78195*
*For The Production Shop — luthiers-toolbox-main*
*Last updated: April 2026*
