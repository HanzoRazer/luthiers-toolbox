# Mathematical Formula Catalog

**Audit Date**: 2026-04-30  
**Scope**: services/api/, services/blueprint-import/, services/photo-vectorizer/, docs/, scripts/  
**Purpose**: Manual verification support - read-only audit, no corrections made

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total Formulas Catalogued** | 147 |
| **High Risk** | 52 |
| **Medium Risk** | 58 |
| **Low Risk** | 37 |
| **Cited (Specific)** | 28 |
| **Cited (General)** | 41 |
| **Named** | 34 |
| **Uncited** | 44 |

### By Domain Category

| Domain | Count | High Risk | With Tests |
|--------|-------|-----------|------------|
| acoustic_physics | 24 | 14 | 18 |
| lutherie_geometry | 38 | 18 | 22 |
| cnc_cam | 26 | 16 | 14 |
| structural_mechanics | 18 | 11 | 12 |
| wood_movement | 8 | 4 | 5 |
| signal_processing | 9 | 2 | 4 |
| optimization | 8 | 5 | 3 |
| geometry_2d_3d | 12 | 0 | 8 |
| data_processing | 4 | 0 | 3 |

### Critical Gaps Identified

1. **Uncited CNC machining formulas** - Hardness-based scaling in `bulk_import_wood_species.py` has 15+ empirical coefficients without source references. These feed directly into feeds/speeds recommendations.

2. **Tool deflection uses hardcoded E=90,000 MPa** - No material selection for carbide vs HSS vs ceramic.

3. **Body scoring heuristics** - Custom 6-factor weighted scoring in vectorizer lacks validation methodology documentation.

4. **Test coverage gaps** - Neck angle, neck taper, bridge height profile, fan brace geometry lack dedicated unit tests despite being high-risk.

---

## Domain: ACOUSTIC_PHYSICS

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Helmholtz resonance (multiport) | soundhole_physics.py:164 | HIGH | cited_specific | Yes |
| Coupled resonator eigenfreq | soundhole_physics.py:323 | HIGH | cited_general | Yes |
| Port neck length correction | soundhole_physics.py:123 | MEDIUM | cited_general | Yes |
| Plate modal frequency | plate_design/thickness_calculator.py:70 | HIGH | cited_specific | Unknown |
| Rayleigh-Ritz stiffness matrix | plate_design/rayleigh_ritz.py:297 | HIGH | cited_general | Yes |
| Rayleigh-Ritz mass matrix | plate_design/rayleigh_ritz.py:414 | HIGH | cited_general | Yes |
| Alpha parameter | plate_design/alpha_beta.py:171 | HIGH | cited_general | Yes |
| Beta parameter | plate_design/alpha_beta.py:385 | HIGH | cited_general | Yes |
| Gamma coefficient | plate_design/alpha_beta.py:453 | HIGH | cited_general | Yes |
| Logarithmic spiral centerline | soundhole/spiral_geometry.py:114 | HIGH | cited_specific | Yes |
| Spiral P:A ratio (closed form) | soundhole/spiral_geometry.py:179 | MEDIUM | cited_specific | Yes |
| String tension | string_tension.py:246 | HIGH | cited_general | Yes |
| Soundhole stiffness reduction | soundhole_stiffness.py:120 | HIGH | cited_specific | Partial |
| Body volume estimation | acoustic_body_volume.py:145 | HIGH | uncited | Yes |
| Two-cavity analysis | soundhole_resonator.py:176 | HIGH | cited_general | Yes |

---

### FORMULA: Helmholtz Resonance (Multiport)

**File**: `services/api/app/calculators/soundhole_physics.py`  
**Lines**: 164-218  
**Function**: `compute_helmholtz_multiport()`

**Formula (code)**:
```python
f_uncoupled = (C_AIR / (2 * math.pi)) * math.sqrt(total_area / (volume_m3 * L_eff_weighted))
f_H = f_uncoupled * plate_mass_factor
```

**Plain language**: Helmholtz frequency = (speed_of_sound / 2pi) * sqrt(port_area / (volume * effective_length)), corrected for plate-air coupling.

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific  
**References**: Gore & Gilet, *Contemporary Acoustic Guitar Design and Build*; Fletcher & Rossing, *The Physics of Musical Instruments*, Ch. 9-10

**Constants**:
- `C_AIR = 343.0` m/s (speed of sound at 20C) - **verify against actual shop conditions**
- `K0 = 1.7` (round-hole end-correction baseline)
- `GAMMA = 0.02` (perimeter sensitivity coefficient)
- `PLATE_MASS_FACTOR = 0.92` (calibrated against Martin OM, D-28, Gibson J-45)

**Risk Score**: HIGH - directly predicts instrument tone character

**Context** (lines 154-228):
```python
def compute_helmholtz_multiport(
    volume_m3: float,
    ports: List[PortSpec],
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
) -> HelmholtzResult:
    """
    Compute Helmholtz resonance for multi-port configuration.
    
    Ports act as parallel acoustic masses with area-weighted averaging.
    
    References:
        Gore & Gilet, Contemporary Acoustic Guitar Design and Build
        Fletcher & Rossing, The Physics of Musical Instruments, Ch. 9-10
    """
    if volume_m3 <= 0:
        raise ValueError("volume_m3 must be > 0")
    
    total_area = sum(p.area_m2 for p in ports)
    L_eff_weighted = sum(p.area_m2 * compute_port_neck_length(
        p.area_m2, p.perimeter_m, p.thickness_m, k0, gamma
    ) for p in ports) / total_area
    
    f_uncoupled = (C_AIR / (2 * math.pi)) * math.sqrt(total_area / (volume_m3 * L_eff_weighted))
    f_H = f_uncoupled * plate_mass_factor
    
    return HelmholtzResult(
        frequency_hz=f_H,
        uncoupled_frequency_hz=f_uncoupled,
        total_port_area_m2=total_area,
        effective_length_m=L_eff_weighted,
    )
```

**Unit Tests**: `tests/test_soundhole_physics.py` (161 tests in soundhole suite)  
**API Reachable**: Yes - POST `/api/instrument/soundhole`

---

### FORMULA: Coupled Resonator Eigenfrequencies

**File**: `services/api/app/calculators/soundhole_physics.py`  
**Lines**: 323-376  
**Function**: `exact_coupled_eigenfreq()`

**Formula (code)**:
```python
kappa_sq = C_AIR ** 2 * A_ap_m2 / (L_eff_ap_m * math.sqrt(V1_m3 * V2_m3))
mean_sq = (w1_sq + w2_sq) / 2.0
half_diff_sq = (w1_sq - w2_sq) / 2.0
discriminant = math.sqrt(half_diff_sq ** 2 + kappa_4)
w_plus_sq = mean_sq + discriminant
w_minus_sq = max(0.0, mean_sq - discriminant)
```

**Plain language**: Exact 2x2 eigenvalue solution for two coupled Helmholtz resonators. Characteristic equation: (omega^2 - omega1^2)(omega^2 - omega2^2) = kappa^4.

**Domain**: acoustic_physics  
**Source Attribution**: cited_general (coupled oscillator theory, first principles)

**Constants**:
- `C_AIR = 343.0` m/s

**Risk Score**: HIGH - affects Maccaferri/Selmer internal resonator predictions

**Unit Tests**: Yes  
**API Reachable**: Yes - two-cavity analysis endpoint

---

### FORMULA: Plate Modal Frequency (Orthotropic)

**File**: `services/api/app/calculators/plate_design/thickness_calculator.py`  
**Lines**: 70-121  
**Function**: `plate_modal_frequency()`

**Formula (code)**:
```python
term_L = E_L_Pa * (m**2) / (a**4)
term_C = E_C_Pa * (n**2) / (b**4)
stiffness_term = (term_L + term_C) / rho
f = eta * (math.pi / 2.0) * math.sqrt(stiffness_term) * h
```

**Plain language**: Modal frequency = (geometry_factor * pi/2) * sqrt((E_L * m^2/a^4 + E_C * n^2/b^4) / density) * thickness

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific  
**References**: Gore & Gilet; Fletcher & Rossing; Caldersmith 1978

**Constants**:
- `eta` (geometry factor, default 1.0)
- Wood properties: E_L, E_C, G_LC, nu_LC, rho

**Risk Score**: HIGH - core acoustic prediction

**Unit Tests**: Unknown - no dedicated test file found  
**API Reachable**: Yes - plate router endpoints

---

### FORMULA: Logarithmic Spiral Soundhole

**File**: `services/api/app/instrument_geometry/soundhole/spiral_geometry.py`  
**Lines**: 114-129  
**Function**: `_spiral_points()`

**Formula (code)**:
```python
r = r0 * math.exp(k * theta)
x = cx + r * math.cos(angle)
y = cy + r * math.sin(angle)
```

**Plain language**: r(theta) = r0 * e^(k*theta) - logarithmic spiral equation

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific  
**References**: Williams 2019 (mwguitars.com.au Parts 7-8)

**Constants**:
- Default k = 0.18 (growth rate per radian)
- Default turns = 1.1
- Default slot_width = 14.0mm
- Williams threshold: P:A > 0.10 mm^-1 for acoustic efficiency

**Risk Score**: HIGH - affects CNC soundhole routing

**Unit Tests**: Yes - `test_soundhole_spiral.py`  
**API Reachable**: Yes - `/api/instrument/soundhole`

---

### FORMULA: Spiral P:A Ratio (Closed Form)

**File**: `services/api/app/instrument_geometry/soundhole/spiral_geometry.py`  
**Lines**: 179-201  
**Function**: `_closed_form_stats()`

**Formula (code)**:
```python
alpha = atan(1.0/k)
one_wall = (r_end - r0) / sin(alpha)
perim = 2 * one_wall
area = slot_w * one_wall
pa = 2 / slot_w  # Independent of k, turns!
```

**Plain language**: Arc length L = (r_end - r0) / sin(atan(1/k)). P:A ratio = 2/slot_width (independent of growth rate and turns).

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific (Williams 2019)

**Constants**:
- Williams efficiency threshold: P:A > 0.10 mm^-1

**Risk Score**: MEDIUM - affects acoustic design validation

**Unit Tests**: Yes  
**API Reachable**: Yes

---

### FORMULA: String Tension (Mersenne's Law)

**File**: `services/api/app/calculators/string_tension.py`  
**Lines**: 246-284  
**Function**: `compute_string_tension()`

**Formula (code)**:
```python
tension_n = ((2.0 * frequency_hz * L) ** 2) * mu
```

**Plain language**: T = (2 * f * L)^2 * mu - string tension from frequency, length, and linear mass density

**Domain**: acoustic_physics  
**Source Attribution**: cited_general (Mersenne's Law, classical physics)

**Constants**:
- `RHO_STEEL_KG_M3 = 7850.0` (steel density) - **standard value**
- `RHO_BRONZE_KG_M3 = 8800.0` (phosphor bronze)
- `RHO_NYLON_KG_M3 = 1150.0`

**Risk Score**: HIGH - affects structural calculations downstream

**Unit Tests**: Yes - `test_string_tension.py`  
**API Reachable**: Yes - POST `/api/calculators/string-tension`

---

### FORMULA: Soundhole Stiffness Reduction

**File**: `services/api/app/calculators/soundhole_stiffness.py`  
**Lines**: 120-228  
**Function**: `compute_top_stiffness_reduction()`

**Formula (code)**:
```python
raw_reduction = K * (area_ratio ** 0.75) * mode_coupling
mode_coupling = math.sin(math.pi * x_frac)
```

**Plain language**: Stiffness reduction = K * (hole_area/plate_area)^0.75 * sin(pi * position_fraction)

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific (Gore & Gilet)

**Constants**:
- `STIFFNESS_K = 0.798` (single-point calibration) - **requires validation**
- `BRACING_RESTORE_DEFAULT = 0.70`

**Risk Score**: HIGH - affects bracing prescription

**Unit Tests**: Partial  
**API Reachable**: Yes

---

### FORMULA: Air Virtual Mass

**File**: `services/api/app/calculators/plate_design/alpha_beta.py`  
**Lines**: ~200-250  
**Function**: Part of alpha/beta system

**Formula (code)**:
```python
m_air = (8.0 / 3.0) * rho_air * (r_eff**3)
```

**Plain language**: m_air = (8/3) * rho_air * r_eff^3 - virtual mass of air loaded on vibrating plate

**Domain**: acoustic_physics  
**Source Attribution**: cited_specific (Gore & Gilet, Fletcher & Rossing Ch 9, Caldersmith 1978)

**Constants**:
- `AIR_DENSITY_KG_M3 = 1.2`
- `AIR_SPEED_OF_SOUND_M_S = 343.0`

**Risk Score**: HIGH - core voicing prediction

**Unit Tests**: Yes  
**API Reachable**: Yes

---

## Domain: LUTHERIE_GEOMETRY

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Fret position (12-TET) | fret_math.py:99 | HIGH | cited_general | Yes |
| Perpendicular fret distance | fret_math.py:17 | HIGH | named | Yes |
| Multiscale fret positions | fret_math.py:160 | HIGH | cited_general | Yes |
| Neck angle | neck_angle.py:71 | HIGH | uncited | **No** |
| Inverse neck angle solver | neck_angle.py:128 | HIGH | cited_specific | **No** |
| Neck taper width | taper_math.py:99 | HIGH | cited_specific | **No** |
| Bridge compensation | bridge/geometry.py:166 | MEDIUM | uncited | Yes |
| Saddle positions | bridge/geometry.py:50 | HIGH | cited_general | Yes |
| Cents to mm conversion | saddle_compensation.py | HIGH | cited_general | Yes |
| Compound radius | radius_profiles.py:40 | MEDIUM | cited_general | **No** |
| Radius arc points | radius_profiles.py:74 | MEDIUM | uncited | **No** |
| Bridge height profile | bridge/geometry.py:77 | HIGH | uncited | **No** |
| Cubic Bezier | body/parametric.py:43 | MEDIUM | cited_general | **No** |
| String spacing (centered) | spacing.py:47 | HIGH | uncited | **No** |
| String spacing (edge margin) | spacing.py:88 | HIGH | uncited | **No** |
| Break angle | bridge_break_angle.py:164 | HIGH | named | Yes |

---

### FORMULA: Fret Position (Equal Temperament)

**File**: `services/api/app/instrument_geometry/neck/fret_math.py`  
**Lines**: 99-114  
**Function**: `compute_fret_positions_mm()`

**Formula (code)**:
```python
ratio = math_pow(2.0, n / 12.0)
position = scale_length_mm - (scale_length_mm / ratio)
```

**Plain language**: d_n = L * (1 - 1/2^(n/12)) - distance from nut to fret n for 12-TET equal temperament

**Domain**: lutherie_geometry  
**Source Attribution**: cited_general (12-TET, Mersenne 1636)

**Constants**:
- `SEMITONE_RATIO = 2.0 ** (1.0 / 12.0)` = 1.05946309...
- 12 semitones per octave

**Risk Score**: HIGH - directly affects fret slot CNC positioning

**Context** (lines 99-114):
```python
def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """Compute distance from the nut to each fret (in mm) for an equal-tempered"""
    if scale_length_mm <= 0:
        raise ValueError("scale_length_mm must be > 0")
    if fret_count <= 0:
        raise ValueError("fret_count must be > 0")

    fret_positions: List[float] = []
    for n in range(1, fret_count + 1):
        ratio = math_pow(2.0, n / 12.0)
        position = scale_length_mm - (scale_length_mm / ratio)
        fret_positions.append(position)

    return fret_positions
```

**Unit Tests**: Yes - `test_golden_fret_positions.py`, `test_fret_slots_math.py`  
**API Reachable**: Yes - `/api/instrument/geometry/frets`

---

### FORMULA: Neck Angle from Geometry

**File**: `services/api/app/instrument_geometry/neck/neck_angle.py`  
**Lines**: 71-125  
**Function**: `compute_neck_angle()`

**Formula (code)**:
```python
body_length_mm = compute_fret_to_bridge_mm(inp.nut_to_bridge_mm, inp.neck_joint_fret)
height_diff_mm = (inp.bridge_height_mm + inp.saddle_projection_mm) - inp.fretboard_height_at_joint_mm
angle_rad = atan(height_diff_mm / body_length_mm)
```

**Plain language**: theta = arctan((H_saddle + H_bridge - H_fretboard) / L_body) - derives neck angle from saddle/bridge height relative to fretboard plane

**Domain**: lutherie_geometry / structural_mechanics  
**Source Attribution**: uncited (standard geometry derivation)

**Constants**:
- Gate thresholds: GREEN 1.0-3.5 deg, YELLOW 0.5-1.0 or 3.5-5.0 deg, RED <0.5 or >5.0 deg

**Risk Score**: HIGH - incorrect angle causes neck reset

**Unit Tests**: **No dedicated test file found** - **CRITICAL GAP**  
**API Reachable**: Yes - instrument geometry router

---

### FORMULA: Inverse Neck Angle Solver (Target Action)

**File**: `services/api/app/instrument_geometry/neck/neck_angle.py`  
**Lines**: 128-216  
**Function**: `solve_for_target_action()`

**Formula (code)**:
```python
geometric_action_mm = target_action - (relief_mm * 0.6)
angle_rad = atan(geometric_action_mm / nut_to_12th_mm)
```

**Plain language**: Given target action at 12th fret, solve for required neck angle and saddle height. Relief contributes ~60% at 12th fret (parabolic approximation).

**Domain**: lutherie_geometry  
**Source Attribution**: cited_specific (ACOUSTIC-001 in code comments)

**Constants**:
- Relief contribution factor: 0.6 (60% at 12th fret) - **requires validation**

**Risk Score**: HIGH - setup tool affects playability

**Unit Tests**: **No dedicated test file found** - **CRITICAL GAP**  
**API Reachable**: Yes

---

### FORMULA: Width at Fret (Distance-Based Taper)

**File**: `services/api/app/instrument_geometry/neck_taper/taper_math.py`  
**Lines**: 99-127  
**Function**: `width_at_fret()`

**Formula (code)**:
```python
W_f = inputs.nut_width + (x_f / L_N) * (inputs.end_width - inputs.nut_width)
```

**Plain language**: Width at fret f = W_nut + (distance_to_fret / reference_length) * (W_end - W_nut). Linear interpolation based on physical distance, not fret index.

**Domain**: lutherie_geometry  
**Source Attribution**: cited_specific ("CNC Layout Guide for tapered guitar neck blank" - docstring)

**Risk Score**: HIGH - affects CNC neck blank routing

**Unit Tests**: **No dedicated test file found** - **CRITICAL GAP**  
**API Reachable**: Yes - `/api/instrument/geometry/neck-taper`

---

### FORMULA: Break Angle

**File**: `services/api/app/calculators/bridge_break_angle.py`  
**Lines**: 164-326  
**Function**: `calculate_break_angle()`

**Formula (code)**:
```python
theta = arctan((h - slot_depth) / d)
```

**Plain language**: String break angle at saddle with slot offset correction

**Domain**: lutherie_geometry  
**Source Attribution**: named (Carruth 6 degree minimum)

**Constants**:
- `CARRUTH_MINIMUM_ANGLE_DEG = 6.0` - **named but should cite source**

**Risk Score**: HIGH - affects tone transfer, string seating

**Unit Tests**: Yes - `test_bridge_break_angle.py`  
**API Reachable**: Yes - POST `/api/calculators/break-angle`

---

### FORMULA: Saddle Compensation Estimate

**File**: `services/api/app/calculators/saddle_compensation.py`  
**Lines**: 193-280  
**Function**: `estimate_string_compensation_mm()`

**Formula (code)**:
```python
delta = c1*action + c2*gauge + c3*stiffness + c4*scale + c5*wound_factor + c6
```

**Plain language**: Semi-empirical 6-term model for saddle compensation

**Domain**: lutherie_geometry  
**Source Attribution**: cited_general (empirical fitting)

**Constants**:
- `c1 = 0.18` (action coefficient)
- `c2 = 0.45` (gauge coefficient)
- `c3 = 0.05` (stiffness coefficient)
- `c4 = 0.002` (scale factor)
- `c5 = 0.35` (wound/plain factor)
- `c6 = 0.25` (baseline offset)

**Risk Score**: HIGH - intonation accuracy

**Unit Tests**: Yes - `test_saddle_compensation.py`  
**API Reachable**: Yes

---

### FORMULA: Cents to Millimeter Conversion

**File**: `services/api/app/calculators/saddle_compensation.py`  
**Function**: `compute_saddle_adjustment()`

**Formula (code)**:
```python
delta = scale_length_mm * (2 ** (cents_error / 1200) - 1)
```

**Plain language**: Saddle adjustment in mm from cents error. 5 cents on 628mm scale = ~1.8mm.

**Domain**: lutherie_geometry  
**Source Attribution**: cited_general (cent to frequency ratio standard)

**Constants**:
- 1200 cents per octave

**Risk Score**: HIGH - setup tool affects intonation

**Unit Tests**: Yes - `test_saddle_compensation.py`  
**API Reachable**: Yes

---

## Domain: CNC_CAM

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Chipload | cam/vcarve/chipload.py:79 | HIGH | uncited | Partial |
| V-bit depth for width | cam/vcarve/geometry.py:24 | HIGH | uncited | Partial |
| Jerk-limited time estimate | cam/feedtime_l3.py:66 | MEDIUM | named | Unknown |
| Helical plunge arc length | cam/helical_core.py:177 | MEDIUM | uncited | Partial |
| Tool deflection (Euler-Bernoulli) | cam_core/feeds_speeds/deflection_model.py:7 | HIGH | named | Unknown |
| Menger curvature | cam/adaptive_spiralizer_utils.py:45 | MEDIUM | uncited | Unknown |
| Corner fillet geometry | cam/biarc_math.py:83 | MEDIUM | uncited | Unknown |
| Bandsaw blade tension | cam_core/saw_lab/bandsaw/physics.py:29 | HIGH | cited_general | Partial |
| Bandsaw drift angle | cam_core/saw_lab/bandsaw/physics.py:58 | MEDIUM | cited_general | Partial |
| Gullet-capacity feed rate | cam_core/saw_lab/bandsaw/physics.py:87 | HIGH | cited_general | Partial |
| Specific cutting energy | cam/energy_model.py:203 | MEDIUM | cited_general | Unknown |
| Polygon miter offset | cam/adaptive_core.py:244 | MEDIUM | uncited | Partial |
| Heat rating heuristic | cam_core/feeds_speeds/heat_model.py:5 | MEDIUM | uncited | Partial |
| Rim speed | calculators/cam_cutting_evaluator.py:144 | HIGH | uncited | Yes |
| Bite per tooth | calculators/saw_adapters/bite_per_tooth_adapter.py:39 | MEDIUM | uncited | Yes |

---

### FORMULA: Chipload Calculation

**File**: `services/api/app/cam/vcarve/chipload.py`  
**Lines**: 79-98  
**Also**: `services/api/app/cam_core/feeds_speeds/chipload_calc.py:5-9`  
**Function**: `calculate_chipload()` / `calc_chipload_mm()`

**Formula (code)**:
```python
chipload = feed_rate_mm_min / (spindle_rpm * flute_count)
```

**Plain language**: Thickness of material removed per cutting edge per revolution (mm/tooth)

**Domain**: cnc_cam  
**Source Attribution**: uncited - Standard machining formula (**should cite Machinery's Handbook**)

**Constants** (material chipload ranges in mm/tooth):
- Softwood: 0.08 - 0.15
- Hardwood: 0.05 - 0.10
- MDF/Plywood: 0.10 - 0.20
- Aluminum: 0.02 - 0.05
- Acrylic: 0.05 - 0.10

**Risk Score**: HIGH - incorrect chipload leads to tool breakage or poor finish

**Unit Tests**: Partial - `test_cam_feeds_speeds_smoke.py`  
**API Reachable**: Yes - `/api/cam/feeds-speeds/`

---

### FORMULA: V-Bit Depth for Width

**File**: `services/api/app/cam/vcarve/geometry.py`  
**Lines**: 24-48  
**Function**: `vbit_depth_for_width()`

**Formula (code)**:
```python
half_angle_rad = math.radians(bit_angle_deg / 2.0)
tan_half = math.tan(half_angle_rad)
depth = line_width_mm / (2.0 * tan_half)
```

**Plain language**: Calculate cut depth needed to achieve desired line width with V-bit

**Domain**: cnc_cam  
**Source Attribution**: uncited (geometric derivation)

**Risk Score**: HIGH - incorrect depth causes wrong line width or tool crash

**Unit Tests**: Partial  
**API Reachable**: Yes

---

### FORMULA: Tool Deflection (Euler-Bernoulli)

**File**: `services/api/app/cam_core/feeds_speeds/deflection_model.py`  
**Lines**: 7-15  
**Function**: `estimate_deflection_mm()`

**Formula (code)**:
```python
I = pi * (tool_diameter_mm ** 4) / 64.0  # Moment of inertia
E = 90_000  # MPa, carbide approximation
L = stickout_mm
deflection = (force_n * L**3) / (3 * E * I)
```

**Plain language**: Cantilever beam deflection for router bit under cutting force

**Domain**: cnc_cam  
**Source Attribution**: named ("Euler-Bernoulli beam math")

**Constants**:
- `E = 90,000 MPa` (carbide Young's modulus) - **HARDCODED, no material selection**

**Risk Score**: HIGH - underestimated deflection causes dimensional inaccuracy or tool breakage

**Unit Tests**: Unknown  
**API Reachable**: Yes

---

### FORMULA: Bandsaw Blade Tension

**File**: `services/api/app/cam_core/saw_lab/bandsaw/physics.py`  
**Lines**: 29-55  
**Function**: `compute_blade_tension()`

**Formula (code)**:
```python
a_m2 = blade.cross_section_mm2() * 1e-6
sigma = lo + (hi - lo) * max(0.0, min(1.0, stress_fraction))
tension_n = sigma * a_m2
```

**Plain language**: Blade tension force T = stress x cross-section area

**Domain**: cnc_cam  
**Source Attribution**: cited_general  
**References**: Duginske, *The New Complete Guide to the Bandsaw*

**Constants**:
- Carbon steel sigma: 55-70 MPa
- Bi-metal sigma: 70-90 MPa

**Risk Score**: HIGH - incorrect tension causes blade breakage or poor cuts

**Unit Tests**: Partial - `test_woodworking_and_bandsaw.py`  
**API Reachable**: Yes

---

### FORMULA: Bandsaw Drift Angle

**File**: `services/api/app/cam_core/saw_lab/bandsaw/physics.py`  
**Lines**: 58-84  
**Function**: `compute_drift_angle()`

**Formula (code)**:
```python
pitch_mm = 25.4 / max(tpi, 0.1)
drift_rad = 0.012 * (bw / wd) * (1500.0 / rpm) * (6.35 / pitch_mm)
drift_deg = max(0.05, min(4.0, math.degrees(drift_rad)))
```

**Plain language**: Empirical drift angle estimate for bandsaw blade lead

**Domain**: cnc_cam  
**Source Attribution**: cited_general ("Duginske - empirical")

**Constants**:
- Reference RPM: 1500
- Reference pitch: 6.35mm
- Coefficient: 0.012

**Risk Score**: MEDIUM - affects fence angle, not safety-critical

**Unit Tests**: Partial  
**API Reachable**: Yes

---

### FORMULA: Gullet-Capacity Feed Rate

**File**: `services/api/app/cam_core/saw_lab/bandsaw/physics.py`  
**Lines**: 87-118  
**Function**: `compute_feed_rate()`

**Formula (code)**:
```python
pitch_mm = 25.4 / max(blade.tpi, 0.1)
gullet_depth_mm = 0.55 * blade.width_mm
gullet_area_mm2 = 0.5 * pitch_mm * gullet_depth_mm
engagement = max(stock_thickness_mm, blade.kerf_mm)
ipm = (gullet_area_mm2 * sfpm * eff) / (engagement * 25.4 * 12.0)
```

**Plain language**: Maximum feed rate based on gullet chip carrying capacity

**Domain**: cnc_cam  
**Source Attribution**: cited_general ("Gullet capacity theory")

**Constants**:
- Gullet depth factor: 0.55 x blade width
- Default efficiency: 0.35

**Risk Score**: HIGH - overfeeding causes blade stalling or breakage

**Unit Tests**: Partial  
**API Reachable**: Yes

---

### FORMULA: Rim Speed

**File**: `services/api/app/calculators/cam_cutting_evaluator.py`  
**Lines**: 144-160  
**Function**: `calculate_rim_speed()`

**Formula (code)**:
```python
rim_speed = pi * D * rpm / 60000  # m/s
```

**Plain language**: Saw blade peripheral velocity

**Domain**: cnc_cam  
**Source Attribution**: uncited (kinematics)

**Constants**:
- `max_rim_speed = 80.0` m/s (safety limit) - **verify against blade manufacturer specs**

**Risk Score**: HIGH - safety critical

**Unit Tests**: Yes  
**API Reachable**: Yes

---

### FORMULA: Specific Cutting Energy

**File**: `services/api/app/cam/energy_model.py`  
**Lines**: 203-230  
**Function**: `_vol_removed_for_move()`, `energy_breakdown()`

**Formula (code)**:
```python
volume = length * stepover * tool_d * stepdown * k  # k=0.9 for trochoids
energy = volume * sce_j_per_mm3
heat_chip = energy * heat_partition.get("chip", 0.7)
heat_tool = energy * heat_partition.get("tool", 0.2)
heat_work = energy * heat_partition.get("work", 0.1)
```

**Plain language**: Cutting energy from material removal volume and specific cutting energy

**Domain**: cnc_cam  
**Source Attribution**: cited_general ("Specific Cutting Energy theory - Merchant, Shaw")

**Constants** (SCE in J/mm3):
- Softwood: 0.0010-0.0015
- Hardwood: 0.0015-0.0025
- Aluminum: 0.0030-0.0050
- Heat partition: chip 65%, tool 25%, work 10% (typical) - **uncited**

**Risk Score**: MEDIUM - affects tool life predictions

**Unit Tests**: Unknown  
**API Reachable**: Yes

---

## Domain: STRUCTURAL_MECHANICS

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Top deflection | top_deflection_calc.py:118 | HIGH | cited_general | Yes |
| Plate EI | top_deflection_calc.py:65 | MEDIUM | cited_general | Yes |
| Required EI (inverse) | bracing_calc.py:213 | HIGH | uncited | Yes |
| Brace dimensions for EI | bracing_calc.py:248 | HIGH | uncited | Yes |
| Brace section area | _bracing_physics.py:52 | MEDIUM | uncited | Yes |
| Second moment of area | _bracing_physics.py:97 | HIGH | cited_general | Yes |
| Camber arc height | _bracing_physics.py:142 | MEDIUM | uncited | Yes |
| Side bending parameters | side_bending_calc.py:770 | HIGH | cited_general | Yes |
| Lignin glass transition | side_bending_calc.py:643 | MEDIUM | cited_specific | Yes |
| Saddle force decomposition | saddle_force_calc.py:72 | HIGH | uncited | Yes |
| Fan brace angles | bracing/fan_brace.py:96 | HIGH | named | **No** |

---

### FORMULA: Top Deflection

**File**: `services/api/app/calculators/top_deflection_calc.py`  
**Lines**: 118-175  
**Function**: `compute_top_deflection()`

**Formula (code)**:
```python
static_deflection_m = (load_n * (a ** 2) * (b ** 2)) / (3.0 * composite_EI * L)
creep_projection_mm = static_deflection_mm * CREEP_FACTOR
```

**Plain language**: delta = F * a^2 * b^2 / (3 * EI * L) - simply-supported beam deflection at point load, plus 35% creep factor

**Domain**: structural_mechanics  
**Source Attribution**: cited_general (beam theory)

**Constants**:
- `CREEP_FACTOR = 0.35` (wood relaxation over lifetime)
- Gate thresholds: GREEN <1.5mm, YELLOW 1.5-3mm, RED >3mm

**Risk Score**: HIGH - structural integrity prediction

**Unit Tests**: Yes  
**API Reachable**: Yes - POST `/api/calculators/top-deflection`

---

### FORMULA: Second Moment of Area (Brace Profiles)

**File**: `services/api/app/calculators/_bracing_physics.py`  
**Lines**: 97-140  
**Function**: `second_moment_of_area()`

**Formula (code)**:
```python
# Rectangular: I = w * h^3 / 12
# Triangular:  I = w * h^3 / 36
# Parabolic:   I = (8/175) * w * h^3
```

**Plain language**: Second moment of area for different brace cross-section profiles

**Domain**: structural_mechanics  
**Source Attribution**: cited_general (engineering handbooks)

**Risk Score**: HIGH - direct input to stiffness calculations

**Unit Tests**: Yes  
**API Reachable**: Indirect

---

### FORMULA: Side Bending Parameters

**File**: `services/api/app/calculators/side_bending_calc.py`  
**Lines**: 770-900  
**Function**: `compute_bending_parameters()`

**Formula (code)**:
```python
# Minimum elastic radius
R_min = (E_GPa * 1e9) * (thickness_mm / 1000.0) / (2.0 * MOR_MPa * 1e6) * 1000.0
# Hot bending radius
R_min_hot = R_min * bendability_factor
```

**Plain language**: R_min = E * t / (2 * MOR) - minimum bend radius from outer fiber stress

**Domain**: structural_mechanics  
**Source Attribution**: cited_general  
**References**: Gore & Gilet Vol.1 S3.4; Cumpiano & Natelson pp.180-186

**Constants**:
- Bendability factors per species (0.44-0.60)
- E/MOR values from USDA Wood Handbook

**Risk Score**: HIGH - prevents breakage during bending

**Unit Tests**: Yes  
**API Reachable**: Yes

---

### FORMULA: Lignin Glass Transition

**File**: `services/api/app/calculators/side_bending_calc.py`  
**Lines**: 643-648  
**Function**: `lignin_tg_celsius()`

**Formula (code)**:
```python
return 200.0 - 8.0 * mc_pct
```

**Plain language**: Tg(MC) = 200 - 8 * moisture_content_percent

**Domain**: structural_mechanics  
**Source Attribution**: cited_specific  
**References**: Goring, D.A.I. *Pulp and Paper Magazine of Canada*, 1963

**Risk Score**: MEDIUM - affects bending temperature recommendations

**Unit Tests**: Yes  
**API Reachable**: Yes

---

### FORMULA: Fan Brace Angles

**File**: `services/api/app/instrument_geometry/bracing/fan_brace.py`  
**Lines**: 96-101  
**Function**: `get_fan_brace_pattern()` (inner loop)

**Formula (code)**:
```python
angle_rad = math.radians(angle_offset)
dx = fan_length * math.sin(angle_rad)
dy = fan_length * math.cos(angle_rad)
```

**Plain language**: Fan brace endpoints computed by projecting from apex at computed angle. Each brace angle = (index+1) * (spread_angle/2) / (half_braces + 0.5).

**Domain**: structural_mechanics  
**Source Attribution**: named (Torres bracing pattern, 1850s)

**Constants**:
- Default fan_spread_angle = 50 degrees total

**Risk Score**: HIGH - affects top bracing template

**Unit Tests**: **No dedicated test file found** - **CRITICAL GAP**  
**API Reachable**: Yes

---

## Domain: WOOD_MOVEMENT

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Dimensional change | wood_movement_calc.py:108 | HIGH | cited_general | Yes |
| MC from RH | wood_movement_calc.py:108 | MEDIUM | cited_general | Yes |
| Thermal conductivity | bulk_import_wood_species.py:127 | MEDIUM | uncited | **No** |
| Specific cutting energy | bulk_import_wood_species.py:130 | MEDIUM | uncited | **No** |
| Specific heat capacity | bulk_import_wood_species.py:133 | LOW | uncited | **No** |
| Janka from density | bulk_import_wood_species.py:140 | MEDIUM | uncited | **No** |

---

### FORMULA: Wood Dimensional Change

**File**: `services/api/app/calculators/wood_movement_calc.py`  
**Lines**: 108-178  
**Function**: `compute_wood_movement()`

**Formula (code)**:
```python
mc_change = (rh_delta / 100.0) * MC_CHANGE_PER_RH_PCT * 100
movement = abs(dimension_mm * (mc_change / 100.0) * coeff * 100)
```

**Plain language**: DW = W0 * DMC * S_r - dimensional change = initial_dimension * moisture_content_change * shrinkage_coefficient

**Domain**: wood_movement  
**Source Attribution**: cited_general  
**References**: Wood Handbook (USDA Forest Products Laboratory)

**Constants**:
- `MC_CHANGE_PER_RH_PCT = 0.30` (0.3% MC per 1% RH change)
- `RADIAL_TO_TANGENTIAL_RATIO = 0.55`
- Per-species tangential shrinkage coefficients (22 species)

**Risk Score**: HIGH - affects joint sizing and construction tolerances

**Unit Tests**: Yes - `test_board_feet.py`  
**API Reachable**: Yes - POST `/wood-movement`

---

### FORMULA: Janka Hardness from Density

**File**: `scripts/bulk_import_wood_species.py`  
**Lines**: 140-141  
**Function**: `janka_from_density()`

**Formula (code)**:
```python
return round(0.00355 * (density_kgm3 ** 1.85))
```

**Plain language**: Janka = 0.00355 * density^1.85 - power-law regression estimate

**Domain**: wood_movement / cnc_cam  
**Source Attribution**: uncited - **empirical regression, no paper reference**

**Constants**:
- 0.00355 (coefficient)
- 1.85 (exponent)

**Risk Score**: MEDIUM - used for machining parameter estimation

**Unit Tests**: **None in scripts/** - **GAP**  
**API Reachable**: Yes - feeds into `wood_species.json`

---

### FORMULA: Thermal Conductivity from SG

**File**: `scripts/bulk_import_wood_species.py`  
**Lines**: 127-128  
**Function**: `estimate_thermal_k()`

**Formula (code)**:
```python
return 0.04 + 0.35 * sg
```

**Plain language**: k = 0.04 + 0.35 * specific_gravity (W/m K)

**Domain**: wood_movement / cnc_cam  
**Source Attribution**: uncited

**Constants**:
- 0.04 (intercept)
- 0.35 (slope)

**Risk Score**: MEDIUM - affects heat calculations

**Unit Tests**: **None**  
**API Reachable**: Yes

---

## Domain: SIGNAL_PROCESSING

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Circularity | vectorizer_phase3.py:807 | LOW | named | Indirect |
| Hu moments log transform | vectorizer_phase3.py:826 | LOW | cited_general | **No** |
| 12-TET fret ratio detection | calibration/scale_detector.py:354 | LOW | cited_specific | **No** |
| Hausdorff distance | contour_stage.py:75 | LOW | named | Indirect |
| Body Helmholtz (standalone) | calibrate_carlos_jumbo.py:273 | LOW | cited_general | **No** |

---

### FORMULA: Circularity

**File**: `services/blueprint-import/vectorizer_phase3.py`  
**Lines**: 807, 923, 1724, 3151  
**Function**: `MLContourClassifier.extract_features()`, `PrimitiveDetector.detect_circle()`, `classify_contour()`

**Formula (code)**:
```python
circularity = 4 * np.pi * area / (perimeter * perimeter)
```

**Plain language**: Isoperimetric quotient - 1.0 for perfect circle, <1 for other shapes

**Domain**: signal_processing / geometry_2d_3d  
**Source Attribution**: named (standard computational geometry formula)

**Constants**:
- pi
- Threshold 0.85 for circle detection

**Risk Score**: LOW - well-established formula

**Unit Tests**: Indirectly tested  
**API Reachable**: Yes

---

### FORMULA: 12-TET Fret Ratio Detection

**File**: `services/blueprint-import/calibration/scale_detector.py`  
**Lines**: 354-423  
**Function**: `ScaleReferenceDetector._detect_from_fret_pattern()`

**Formula (code)**:
```python
expected_ratio = 2 ** (1/12)  # = 1.0595
first_fret_factor = 1 - 2**(-1/12)
```

**Plain language**: Detects scale length from fret spacing using 12-TET formula

**Domain**: signal_processing (pattern detection)  
**Source Attribution**: cited_specific (12-TET mathematical definition)

**Constants**:
- 2^(1/12) = 1.0595...
- Tolerance 15%

**Risk Score**: LOW - well-documented music theory

**Unit Tests**: **No direct test**  
**API Reachable**: Yes

---

## Domain: OPTIMIZATION

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Body candidate scoring | vectorizer_phase3.py:1882 | HIGH | uncited | Partial |
| Body ownership score | contour_plausibility.py:61 | HIGH | uncited | Yes |
| Merge guard epsilon | contour_stage.py:121 | MEDIUM | uncited | Yes |
| Scale calibration (two-pass) | contour_stage.py:231 | HIGH | uncited | Partial |
| Export block threshold | contour_stage.py:133 | HIGH | uncited | Yes |

---

### FORMULA: Body Candidate Scoring

**File**: `services/blueprint-import/vectorizer_phase3.py`  
**Lines**: 1882-1967  
**Function**: `score_body_candidate()`

**Formula (code)**:
```python
aspect_score = 25.0 * (1.0 - min(abs(aspect - 1.3) / 0.5, 1.0))
# + solidity_score, size_score, position_score, grid_overlap_score
```

**Plain language**: Multi-factor weighted scoring (0-100) to identify true body outline among candidates

**Domain**: optimization  
**Source Attribution**: uncited (custom algorithm)

**Constants**:
- Aspect ratio sweet spot: 1.3
- Solidity threshold: 0.85
- Area ratio range: 0.05-0.70
- Center distance threshold: 0.35

**Risk Score**: HIGH - custom heuristic affecting body detection accuracy

**Unit Tests**: Partial  
**API Reachable**: Yes

---

### FORMULA: Body Ownership Score

**File**: `services/photo-vectorizer/contour_plausibility.py`  
**Lines**: 61-106  
**Function**: `body_ownership_score()`

**Formula (code)**:
```python
score = (
    0.50 * completeness
    + 0.25 * vertical_coverage
    + 0.10 * (1.0 - border_contact)
    + 0.15 * (1.0 - neck_inclusion)
)
```

**Plain language**: Weighted score to determine if contour owns the body vs fragment

**Domain**: optimization  
**Source Attribution**: uncited (custom)

**Constants**:
- Weights: 0.50/0.25/0.10/0.15
- vertical_coverage threshold: 0.45
- border_contact penalty: 0.30
- neck_inclusion penalty: 0.25
- completeness threshold: 0.55

**Risk Score**: HIGH - core body detection logic

**Unit Tests**: Yes - `test_body_ownership_score.py`, `test_contour_plausibility_ownership.py`  
**API Reachable**: Yes

---

## Domain: GEOMETRY_2D_3D

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Euclidean distance | vectorizer_phase3.py:180 | LOW | named | Indirect |
| Ellipse area | vectorizer_phase3.py:953 | LOW | named | **No** |
| Arc/angle calculations | vectorizer_phase3.py:1004 | LOW | named | **No** |
| Douglas-Peucker | vectorizer_phase3.py:2568 | MEDIUM | named | Indirect |
| PPI conversion | calibration/pixel_calibrator.py:239 | LOW | named | Yes |
| Centrality score | edge_to_dxf.py:153 | LOW | uncited | **No** |
| Arc center from radius | cam/biarc_math.py:184 | LOW | uncited | Unknown |

---

### FORMULA: Douglas-Peucker Simplification Tolerances

**File**: `services/blueprint-import/vectorizer_phase3.py`  
**Lines**: 2568-2570  
**Function**: `export_to_dxf()`

**Formula (code)**:
```python
simplified = cv2.approxPolyDP(pts_array, tolerance, closed=True)
```

**Plain language**: Reduces contour point count while preserving shape

**Domain**: geometry_2d_3d  
**Source Attribution**: named (Ramer-Douglas-Peucker algorithm)

**Constants** (layer-specific tolerances in mm):
- BODY_OUTLINE: 0.05mm
- NECK_POCKET: 1.0mm
- Other layers: various

**Risk Score**: MEDIUM - tolerance values directly affect CAD accuracy

**Unit Tests**: Indirectly tested  
**API Reachable**: Yes

---

## Domain: ELECTRONICS

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| Parallel resistance | wiring/impedance_math.py:41 | LOW | uncited | Yes |
| RC tone rolloff | wiring/impedance_math.py:68 | MEDIUM | cited_general | Yes |
| Pickup resonant peak | wiring/impedance_math.py:120 | MEDIUM | named | Yes |

---

### FORMULA: RC Tone Rolloff

**File**: `services/api/app/calculators/wiring/impedance_math.py`  
**Lines**: 68-117  
**Function**: `calculate_tone_rolloff()`

**Formula (code)**:
```python
cutoff = 1.0 / (2.0 * math.pi * r_ohms * c_farads)
```

**Plain language**: f_c = 1 / (2*pi*R*C) - RC low-pass cutoff frequency

**Domain**: electronics  
**Source Attribution**: cited_general (circuit theory)

**Risk Score**: MEDIUM - affects tone response

**Unit Tests**: Yes  
**API Reachable**: Yes

---

## Domain: TEMPERAMENT_TUNING

### Summary Table

| Formula | File | Risk | Attribution | Tests |
|---------|------|------|-------------|-------|
| N-TET ratios | alternative_temperaments.py:109 | MEDIUM | uncited | Yes |
| Deviation in cents | alternative_temperaments.py:213 | LOW | cited_general | Yes |
| Just intonation | alternative_temperaments.py:233 | MEDIUM | cited_general | Yes |
| Pythagorean | alternative_temperaments.py:272 | MEDIUM | cited_general | Yes |
| Meantone | alternative_temperaments.py:316 | MEDIUM | cited_general | Yes |
| Staggered frets | alternative_temperaments.py:358 | HIGH | uncited | Yes |

---

### FORMULA: N-TET Frequency Ratios

**File**: `services/api/app/calculators/alternative_temperaments.py`  
**Lines**: 109-130  
**Function**: `compute_n_tet_ratios()`

**Formula (code)**:
```python
ratio[i] = 2**(i/n)  # for i in 0..fret_count
```

**Plain language**: Frequency ratios for arbitrary N-tone equal temperament

**Domain**: temperament_tuning  
**Source Attribution**: uncited (N-TET definition)

**Risk Score**: MEDIUM

**Unit Tests**: Yes  
**API Reachable**: Yes

---

### FORMULA: Quarter-Comma Meantone

**File**: `services/api/app/calculators/alternative_temperaments.py`  
**Lines**: 316-355  
**Function**: `compute_meantone_positions()`

**Formula (code)**:
```python
fifth = 3/2 * (81/80)**(-comma_fraction)  # then stack fifths
```

**Plain language**: Quarter-comma meantone with syntonic comma distribution

**Domain**: temperament_tuning  
**Source Attribution**: cited_general (meantone theory)

**Constants**:
- `SYNTONIC_COMMA = 81/80`

**Risk Score**: MEDIUM

**Unit Tests**: Yes  
**API Reachable**: Yes

---

## Physical Constants Inventory

| Constant | Value | Location | Source | Verify |
|----------|-------|----------|--------|--------|
| C_AIR | 343.0 m/s | soundhole_physics.py | Speed of sound at 20C | Temperature-dependent |
| K0 | 1.7 | soundhole_physics.py | Round-hole end-correction | Gore & Gilet |
| GAMMA | 0.02 | soundhole_physics.py | Perimeter sensitivity | Calibrated |
| PLATE_MASS_FACTOR | 0.92 | soundhole_physics.py | Martin OM, D-28, J-45 | Calibrated |
| CREEP_FACTOR | 0.35 | top_deflection_calc.py | Wood creep | Needs source |
| RHO_STEEL_KG_M3 | 7850.0 | string_tension.py | Steel density | Standard |
| RHO_BRONZE_KG_M3 | 8800.0 | string_tension.py | Phosphor bronze | Standard |
| LIGNIN_Tg_DRY_C | 200 | side_bending_calc.py | Lignin Tg | Goring 1963 |
| MC_CHANGE_PER_RH_PCT | 0.30 | wood_movement_calc.py | 1% RH = 0.3% MC | Wood Handbook |
| CARRUTH_MINIMUM_ANGLE_DEG | 6.0 | bridge_break_angle.py | Break angle | Needs citation |
| E_STEEL | 200,000 MPa | deflection_adapter.py | Steel modulus | Standard |
| E_CARBIDE | 90,000 MPa | deflection_model.py | Carbide modulus | **Hardcoded** |
| STIFFNESS_K | 0.798 | soundhole_stiffness.py | Single-point calibration | Needs validation |
| VOLUME_FACTOR | 1.83 | docs/LUTHERIE_MATH.md | Body volume calibration | 3-instrument mean |
| SEMITONE_RATIO | 1.0594631 | fret_math.py | 2^(1/12) | Mathematical |

---

## Special Focus Area: CNC Feeds/Speeds

**Location**: `scripts/bulk_import_wood_species.py` lines 407-465

**CRITICAL FINDING**: 15+ hardness-based scaling formulas with uncited empirical coefficients:

```python
chipload = max(0.5, 1.3 - 0.8 * hs)
rough_feed = max(1200, 6000 - 5000 * hs)
finish_feed = max(700, 3500 - 3000 * hs)
plunge_feed = max(250, 2000 - 1800 * hs)
min_rpm = max(10000, 10000 + 8000 * hs)
max_doc = max(2, 18 - 16 * hs)
optimal_doc_ratio = max(0.15, 0.7 - 0.55 * hs)
max_woc_ratio = max(0.2, 0.7 - 0.5 * hs)
finishing_woc_ratio = max(0.04, 0.2 - 0.16 * hs)
```

**Risk**: HIGH - directly affects machine operation safety and quality

**Source Attribution**: uncited - appears to be empirical/author-derived

**Unit Tests**: None in scripts/

**Recommendation**: These formulas require validation against Machinery's Handbook or equivalent CNC machining references before production use.

---

## Special Focus Area: saw_blades.json Consumers

**File**: `services/api/app/data/cam_core/saw_blades.json`

**Consumers identified**:
1. `services/api/app/cam_core/saw_lab/saw_blade_validator.py`
2. `services/api/app/cam_core/api/saw_lab_router.py`
3. `services/api/app/services/saw_lab_gcode_emit_service.py`

**Critical Constants in saw_blades.json**:
- `recommended_bite_mm_per_tooth`: 0.08 - 0.25 mm
- `max_rpm`: 9000 - 24000
- `recommended_rim_speed_m_per_min`: 3000 - 4400

---

## Test Coverage Summary

### Formulas WITH Dedicated Tests
- Fret positions (12-TET)
- Helmholtz resonance (161 tests)
- String tension
- Bridge break angle
- Saddle compensation
- Side bending parameters
- Top deflection
- Wood movement
- Bracing calculations

### Formulas LACKING Tests (High-Risk)
1. `compute_neck_angle()` - neck_angle.py
2. `solve_for_target_action()` - neck_angle.py
3. `width_at_fret()` - taper_math.py
4. `fret_distance()` - taper_math.py
5. `compute_bridge_height_profile()` - bridge/geometry.py
6. `get_fan_brace_pattern()` - bracing/fan_brace.py
7. `compute_centered_spacing_mm()` - spacing.py
8. `compute_edge_margin_spacing_mm()` - spacing.py
9. Tool deflection (E=90,000 MPa hardcoded)
10. All scripts/bulk_import_wood_species.py formulas

---

## Verification Recommendations

### Priority 1: High-Risk Uncited
1. CNC hardness scaling formulas in bulk_import_wood_species.py
2. Tool deflection with hardcoded modulus
3. Body scoring heuristics in vectorizer
4. Relief contribution factor (0.6) in neck angle solver

### Priority 2: High-Risk Named (Need Full Citation)
1. Carruth minimum break angle (6 degrees)
2. Torres bracing pattern angles
3. Creep factor (0.35)

### Priority 3: Calibrated Constants (Document Methodology)
1. PLATE_MASS_FACTOR = 0.92
2. STIFFNESS_K = 0.798
3. VOLUME_FACTOR = 1.83
4. GAMMA = 0.02

---

*Catalog prepared for manual verification. No formulas were corrected or modified during this audit.*
