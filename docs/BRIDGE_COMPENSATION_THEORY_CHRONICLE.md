# Bridge Compensation Theory Chronicle

> **Purpose**: Document the physics, mathematics, and architectural discussions from the Interactive Bridge Compensation Lab sandbox development
> **Last Updated**: 2026-03-18

---

## Table of Contents

1. [Physics of Bridge Compensation](#physics-of-bridge-compensation)
2. [Core Mathematical Formulas](#core-mathematical-formulas)
3. [The Cents-to-Length Conversion](#the-cents-to-length-conversion)
4. [Straight Saddle Fitting](#straight-saddle-fitting)
5. [Break Angle Considerations](#break-angle-considerations)
6. [Neck Angle as the Keystone](#neck-angle-as-the-keystone)
7. [Semi-Empirical Design Model](#semi-empirical-design-model)
8. [Repo Audit Findings](#repo-audit-findings)
9. [Architecture Decisions](#architecture-decisions)

---

## Physics of Bridge Compensation

### Why Bridges Are Slanted

Acoustic guitar bridges are typically slanted 2-4 degrees relative to the frets. This slant exists because:

1. **Bass strings need more compensation than treble strings**
2. **Compensation = extra length added beyond the nominal scale length**
3. **The extra length corrects for pitch sharpening caused by fretting**

### The Fretting Problem

When you press a string against a fret:

1. The string stretches slightly (increases tension)
2. Higher tension = higher pitch
3. Without compensation, fretted notes would all be sharp

### String-Dependent Factors

Different strings need different amounts of compensation because:

| Factor | Effect on Compensation |
|--------|----------------------|
| **Gauge** | Heavier strings need more compensation |
| **Tension** | Lower tension strings need more |
| **Wound vs Plain** | Wound strings typically need ~0.5mm more |
| **Action height** | Higher action = more stretch = more compensation |

---

## Core Mathematical Formulas

### Per-String Compensation (Theoretical)

The theoretical compensation for string `i` can be approximated as:

```
c_i ≈ (L_n × EA) / (4 × L_0 × T_0) × h_n² × (1/x + 1/(L_0 - x))
```

Where:
- `L_n` = fret-to-saddle length at fret n
- `EA` = string stiffness (Young's modulus × cross-sectional area)
- `L_0` = open string length (scale length)
- `T_0` = open string tension
- `h_n` = string height at fret n
- `x` = position along the fret

This formula captures the physics but requires material properties that are rarely available.

### Saddle Slant Angle

For a straight saddle approximation:

```
θ = arctan(Δc / string_spread)
```

Where:
- `Δc = bass_compensation - treble_compensation`
- `string_spread` = distance from treble to bass string (typically 54mm for 6-string)

**Typical values**: θ ≈ 2-4 degrees

---

## The Cents-to-Length Conversion

### The Setup Problem

At the bench, you measure intonation error in **cents** (via tuner). You need to convert this to **millimeters** of saddle movement.

### The Formula

```
ΔL = L × (2^(e/1200) - 1)
```

Where:
- `ΔL` = length change needed (mm)
- `L` = scale length (mm)
- `e` = cents error (positive = sharp, negative = flat)

### Sign Convention

| Measurement | Meaning | Action |
|-------------|---------|--------|
| +5 cents | Note is sharp | Move saddle BACK (+ΔL) |
| -3 cents | Note is flat | Move saddle FORWARD (-ΔL) |

### Example Calculation

For a 628.65mm scale length with +4 cents error:

```
ΔL = 628.65 × (2^(4/1200) - 1)
ΔL = 628.65 × (1.00231 - 1)
ΔL = 628.65 × 0.00231
ΔL ≈ 1.45 mm
```

The saddle position should be moved back by ~1.45mm for that string.

### Derivation

The formula comes from the relationship between frequency and length:

1. Frequency ratio for cents: `f'/f = 2^(cents/1200)`
2. Frequency is inversely proportional to length: `f ∝ 1/L`
3. Therefore: `L'/L = f/f' = 1 / 2^(cents/1200) = 2^(-cents/1200)`
4. The saddle adjustment: `ΔL = L' - L = L × (2^(cents/1200) - 1)` for moving the saddle back when sharp

---

## Straight Saddle Fitting

### The Practical Constraint

Most acoustic guitars use a **straight saddle** for manufacturing simplicity. This means we must find the best-fit line through ideal per-string compensation points.

### Weighted Least-Squares Fit

Given:
- `x_i` = lateral position of string i (mm from treble edge)
- `c_i` = target compensation for string i (mm)
- `w_i` = weight for string i (default = 1.0)

Find line `c = a + b × x` that minimizes weighted squared error:

```
minimize: Σ w_i × (c_i - (a + b × x_i))²
```

### Solution

```python
w_sum = Σ w_i
x_bar = (Σ w_i × x_i) / w_sum
c_bar = (Σ w_i × c_i) / w_sum

numerator = Σ w_i × (x_i - x_bar) × (c_i - c_bar)
denominator = Σ w_i × (x_i - x_bar)²

slope_b = numerator / denominator
intercept_a = c_bar - slope_b × x_bar
```

### Residuals

The **residual** for string i is the difference between ideal compensation and fitted line:

```
residual_i = c_i - (a + b × x_i)
```

Residuals indicate how much error remains if you use a straight saddle. Large residuals (> 0.2mm) suggest considering:
- Individual crown points on the saddle
- A curved saddle top
- Checking for measurement errors

### Fit Quality Classification

| RMS Residual | Quality | Meaning |
|--------------|---------|---------|
| < 0.05 mm | Excellent | Straight saddle is nearly optimal |
| 0.05-0.10 mm | Good | Minimal compromise |
| 0.10-0.20 mm | Fair | Some crowning may help |
| 0.20-0.35 mm | Poor | Consider individual compensation |
| > 0.35 mm | Very Poor | Check inputs; straight saddle inadequate |

---

## Break Angle Considerations

### What is Break Angle?

The **break angle** is the angle at which the string passes over the saddle crown, measured from horizontal.

### Carruth's Threshold

Luthier Alan Carruth identified **~6 degrees** as the adequacy threshold:

> "Below 6 degrees, you start losing coupling efficiency and getting unpredictable behavior."

### Effect on Intonation

Inadequate break angle can cause:
- Inconsistent witness point formation
- Variable effective string length
- Erratic intonation readings

### Typical Values

| Guitar Type | Typical Break Angle |
|-------------|-------------------|
| Flat-top acoustic | 8-15 degrees |
| Classical | 6-10 degrees |
| Archtop | 12-20 degrees |

### Integration with Compensation Calculator

The sandbox considered adding break angle validation:

```python
if break_angle_deg < 6.0:
    warnings.append(
        f"Break angle {break_angle_deg:.1f}° is below Carruth threshold (6°). "
        "Intonation may be unstable."
    )
```

This remains a **future enhancement** pending integration with break angle computation.

---

## Neck Angle as the Keystone

### The Discovery

During sandbox development, an important architectural insight emerged:

> **Neck angle is the keystone constraint that governs all downstream geometry.**

### The Geometry Chain

```
Neck Angle
    ↓
Bridge Height (follows from action target + neck angle)
    ↓
Break Angle (follows from bridge height + saddle height)
    ↓
Compensation Stability (depends on adequate break angle)
```

### Why This Matters

If you set neck angle incorrectly, you end up with:
- Wrong bridge height to achieve target action
- Wrong break angle as a consequence
- Compensation calculations that don't match physical reality

### Repo Status

The sandbox audit found:
- Neck angle math exists in `luthier_calculator.py`
- However, it's **buried and orphaned**, not productized
- Missing: canonical module, endpoint, integration into design chain

### Recommendation

> The repo should promote neck angle to a first-class canonical calculator before compensation can be fully integrated.

---

## Semi-Empirical Design Model

### Purpose

For the **Design Mode** of the calculator, we need to estimate compensation from string specifications before the guitar is built.

### The Model

```python
def estimate_compensation_mm(
    scale_length_mm: float,
    action_mm: float,          # at 12th fret
    gauge_in: float,           # string diameter in inches
    tension_lb: float,         # string tension in pounds
    is_wound: bool,            # wound vs plain
) -> float:
    base = 0.45
    gauge_term = 0.55 * (gauge_in * 25.4)  # convert to mm
    action_term = 0.18 * (action_mm ** 1.7)
    scale_term = 0.25 * (scale_length_mm / 647.7)
    tension_term = 7.5 / max(tension_lb, 1.0)
    wound_term = 0.55 if is_wound else 0.0

    return base + gauge_term + action_term + scale_term + tension_term + wound_term
```

### Coefficient Origins

| Term | Rationale |
|------|-----------|
| **base** | Minimum compensation for any string |
| **gauge_term** | Heavier strings need proportionally more |
| **action_term** | Non-linear relationship with action height |
| **scale_term** | Longer scales need slightly more (normalized to 25.5") |
| **tension_term** | Lower tension = more stretch = more compensation |
| **wound_term** | Wound strings consistently need ~0.5mm more |

### Calibration Status

> **Important**: These coefficients are sandbox defaults, not calibrated against real instruments.

The model should be treated as:
- A reasonable starting estimate
- Requiring validation against built instruments
- Potentially needing per-luthier calibration profiles

---

## Repo Audit Findings

### What the Sandbox Found

During exploration, the following observations were made about the luthiers-toolbox repository:

#### Bridge Break Angle
- **Expected**: Broken or missing
- **Found**: Further along than assumed; v2 model exists
- **Status**: May need consolidation but not absent

#### Neck Angle
- **Expected**: Missing entirely
- **Found**: Exists in `luthier_calculator.py`
- **Status**: Implemented but not productized (orphaned)

#### Compensation Fields
- **Expected**: Absent
- **Found**: Project model already has `compensation_treble_mm`, `compensation_bass_mm`
- **Status**: Integration points exist

#### Bridge Lab / Project State
- **Expected**: Minimal host environment
- **Found**: More complete than assumed
- **Status**: Good integration foundation exists

### Implications

1. The sandbox's diagnosis of "missing functionality" was partially overstated
2. The real gap is **integration and productization**, not fundamental absence
3. The compensation calculator fills a genuine void (no canonical saddle compensation module)
4. Neck angle needs **promotion**, not creation from scratch

---

## Architecture Decisions

### ADR-001: Composable-First Design

**Decision**: Implement core logic in a Vue composable (`useBridgeCompensation`) with UI as a thin layer.

**Rationale**:
- Separation of concerns
- Testability (logic can be tested without UI)
- Reusability across different host contexts
- Alignment with existing repo patterns

### ADR-002: Dual-Mode Support

**Decision**: Single component supports both Setup Mode and Design Mode.

**Rationale**:
- Unified product experience
- Shared math infrastructure
- Smooth workflow: Design → Build → Setup → Refine

### ADR-003: Loose Host Coupling

**Decision**: Panel does not assume specific project store; host provides prefill/save callbacks.

**Rationale**:
- Drop into Calculator Hub, Bridge Lab, or DESIGN context
- No rewrite of calculator for each host
- Clear interface boundary

### ADR-004: CSV as Bench Interface

**Decision**: Primary bench workflow uses CSV import/export.

**Rationale**:
- Matches existing shop practices (spreadsheet-based tracking)
- Round-trip capability
- Archival of measurements
- Compatibility with other tools

### ADR-005: Warnings Over Blocking

**Decision**: Show warnings for anomalous values rather than blocking input.

**Rationale**:
- Trust the operator
- Unusual situations may be legitimate
- Educational feedback over gatekeeping
- Warnings help catch errors without preventing work

---

## Open Questions

### Q1: Should compensation include break angle adjustment?

**Discussion**: Some theories suggest compensation should be adjusted based on break angle adequacy. Below Carruth's 6° threshold, effective string length becomes less predictable.

**Current Position**: Track break angle as a separate concern. Add warning if below threshold. Do not automatically adjust compensation values.

### Q2: How should the predictive model be calibrated?

**Discussion**: The semi-empirical coefficients need validation against real instruments.

**Options**:
1. Collect data from community (crowdsource)
2. Partner with specific luthiers for controlled measurements
3. Allow per-user calibration profiles
4. Keep as "beta" with disclosure

### Q3: Should residuals drive individual crown recommendations?

**Discussion**: Large residuals indicate a straight saddle is suboptimal. Should the tool recommend specific crown heights?

**Current Position**: Show residuals clearly. Let luthier decide whether/how to crown. Don't automate crown recommendations yet.

### Q4: Integration priority: Break angle or neck angle first?

**Discussion**: Both are upstream of compensation. Which should be productized first?

**Recommendation**: Neck angle first, because:
- It's the true keystone (affects bridge height, which affects break angle)
- Existing implementation just needs promotion
- Break angle computation depends on bridge height, which depends on neck angle

---

## Glossary

| Term | Definition |
|------|------------|
| **Compensation** | Extra length added beyond nominal scale length to correct fretting-induced pitch sharpening |
| **Scale Length** | Nominal vibrating string length from nut to saddle |
| **Setback** | Distance the saddle sits behind the nominal scale length position |
| **Break Angle** | Angle at which string passes over saddle crown, measured from horizontal |
| **Witness Point** | Point where string contacts saddle crown; defines effective vibrating length |
| **Crown** | Shaped top of saddle that creates per-string setback variation |
| **Residual** | Difference between ideal per-string compensation and fitted line value |
| **Cents** | Logarithmic pitch unit; 100 cents = 1 semitone, 1200 cents = 1 octave |

---

## References

1. **Carruth, Alan** - Work on break angle adequacy thresholds
2. **Gore, Trevor** - Contemporary Acoustic Guitar Design and Build (compensation and intonation chapters)
3. **Mottola, R.M.** - Lutherie Information resources on compensation
4. **Fletcher & Rossing** - The Physics of Musical Instruments (string physics fundamentals)

---

*Chronicle will be periodically appended as sandbox development continues.*
