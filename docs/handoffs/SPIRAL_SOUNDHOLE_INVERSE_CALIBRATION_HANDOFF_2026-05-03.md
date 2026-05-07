# Spiral Soundhole Inverse Calibration System

## Extended Annotated Developer Handoff

**Date:** 2026-05-03  
**Status:** EXPERIMENTAL — Geometry engine complete, acoustic calibration pending  
**Author:** Claude Code  
**Scope:** Cross-repository integration (luthiers-toolbox + tap_tone_pi)

---

# Executive Summary

The spiral soundhole is a **distributed acoustic filter** that replaces the traditional round soundhole with logarithmic spiral slots. The geometry engine is production-ready, but the acoustic model requires field calibration before it can reliably predict Helmholtz frequency (f_H) and quality factor (Q).

This document defines the integration path between:
- **luthiers-toolbox** — contains the forward/inverse acoustic solver
- **tap_tone_pi** — provides calibrated field measurements

The core insight: tap_tone_pi can measure what the spiral model predicts. By running measurements on built instruments and inverting the model, we can calibrate the acoustic constants that currently rely on literature estimates.

**Critical constraint:** You cannot increase effective acoustic length without increasing loss in a spiral. The design optimization target is `L_eff / R_loss`, not maximizing perimeter or area.

---

# Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Current Implementation Status](#2-current-implementation-status)
3. [The Calibration Problem](#3-the-calibration-problem)
4. [Tap-Tone-Pi Measurement Capabilities](#4-tap-tone-pi-measurement-capabilities)
5. [Inverse Solver Architecture](#5-inverse-solver-architecture)
6. [Integration Design](#6-integration-design)
7. [Open Questions Requiring Resolution](#7-open-questions-requiring-resolution)
8. [Implementation Plan](#8-implementation-plan)
9. [Risk Analysis](#9-risk-analysis)
10. [File Reference](#10-file-reference)
11. [Appendix: Mathematical Foundation](#appendix-mathematical-foundation)

---

# 1. System Architecture

## 1.1 Physical Model

The instrument is modeled as a **coupled vibroacoustic system**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUPLED SYSTEM                               │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │  Top Plate   │◄────►│  Air Cavity  │◄────►│  Port System │  │
│  │  (m_t, k_t)  │      │  (V, C_a)    │      │  (M_a, R)    │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                                           │           │
│         ▼                                           ▼           │
│  String excitation                          Radiation to room   │
└─────────────────────────────────────────────────────────────────┘
```

**Reduced-order representation:**
```
m_t ẍ_t + c_t ẋ_t + k_t x_t + k_c(x_t - x_a) = F_string
m_a ẍ_a + c_a ẋ_a + k_a x_a + k_c(x_a - x_t) = 0
```

Where:
- `x_t`: top plate displacement
- `x_a`: air mode displacement  
- `k_a`: air stiffness (from cavity compliance)
- `c_a`: air + port damping (the quantity we must calibrate)

## 1.2 The Spiral as Acoustic Element

The spiral soundhole is **not** a simple hole. It is a distributed acoustic filter with:

| Property | Round Hole | Spiral Slot |
|----------|------------|-------------|
| End correction | Well-characterized (0.85r) | Empirical (α × w, α ∈ [0.6, 1.2]) |
| Path contribution | None | Distributed inertance (β × L_path) |
| Loss mechanism | Radiation only | Viscous + radiation + curvature |
| P:A ratio | Fixed by diameter | Tunable via slot width |

**Key insight from Williams 2019:** P:A > 0.10 mm⁻¹ required for acoustic efficiency gain over round hole. For constant-width spiral: P:A = 2/slot_width.

## 1.3 Repository Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                      tap_tone_pi                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ MEASUREMENT ONLY — No interpretation, no optimization     │  │
│  │                                                           │  │
│  │ Outputs:                                                  │  │
│  │   - f_H (Hz) from modal identification                    │  │
│  │   - Q from peak bandwidth                                 │  │
│  │   - Wood properties (E_L, E_C, ρ, damping)               │  │
│  │   - viewer_pack_v1.json (schema-validated)               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ JSON export                      │
│                              ▼                                  │
├─────────────────────────────────────────────────────────────────┤
│                     luthiers-toolbox                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ INTERPRETATION + OPTIMIZATION                             │  │
│  │                                                           │  │
│  │ Inputs:                                                   │  │
│  │   - Spiral geometry (known)                               │  │
│  │   - Body volume (known)                                   │  │
│  │   - Measured f_H, Q (from tap_tone_pi)                   │  │
│  │                                                           │  │
│  │ Outputs:                                                  │  │
│  │   - Calibrated model constants                            │  │
│  │   - Forward predictions for new designs                   │  │
│  │   - Optimal spiral parameters for target f_H/Q           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

This boundary is **architectural law** — tap_tone_pi must remain measurement-only per ADR-0001 and ADR-0009.

---

# 2. Current Implementation Status

## 2.1 Geometry Engine (COMPLETE)

**Source:** `services/api/app/instrument_geometry/soundhole/spiral_geometry.py`

| Component | Status | Lines |
|-----------|--------|-------|
| `SpiralSpec` dataclass | DONE | 32-42 |
| `SpiralGeometry` dataclass | DONE | 45-56 |
| `DualSpiralSpec` dataclass | DONE | 59-65 |
| `compute_spiral_geometry()` | DONE | 204-227 |
| `compute_dual_geometry()` | DONE | 230-245 |
| `generate_dxf()` | DONE | 250-289 |
| Closed-form P:A calculation | DONE | 179-201 |

**Validation:** 8/8 endpoint tests passing.

## 2.2 Acoustic Model (COMPLETE, UNCALIBRATED)

**Source:** `spiral_acoustic_model.py` (repo root)

| Component | Status | Notes |
|-----------|--------|-------|
| `SpiralPortSpec` | DONE | Includes calibration knobs |
| `spiral_path_length_m()` | DONE | Closed-form |
| `effective_length_spiral_m()` | DONE | Uses uncalibrated constants |
| `estimate_loss_resistance_spiral()` | DONE | Uses uncalibrated constants |
| `compute_multiport_system()` | DONE | Combines parallel ports |

**Constants requiring calibration:**
```python
slot_end_correction_alpha: float = 0.85   # Literature estimate, needs field data
distributed_path_factor: float = 0.08     # Empirical guess, needs field data
acoustic_loss_factor: float = 1.0         # Placeholder, needs field data
```

## 2.3 Forward/Inverse Solver (COMPLETE)

**Source:** `spiral_q_fh_solver.py` (repo root)

| Component | Status | Notes |
|-----------|--------|-------|
| `predict_system()` | DONE | Forward prediction of f_H, Q |
| `solve_spiral_parameters()` | DONE | Inverse: fit geometry to target |
| `sweep_parameter()` | DONE | Sensitivity analysis |
| `_objective()` | DONE | Cost function for optimization |

**Current inverse capability:** Solves for spiral geometry given target f_H/Q.

**Missing capability:** Solve for calibration constants given measured f_H/Q.

## 2.4 API Endpoints (COMPLETE)

**Source:** `services/api/app/routers/instrument_geometry/soundhole_router.py`

| Endpoint | Status |
|----------|--------|
| `POST /soundhole` | DONE |
| `GET /soundhole/types` | DONE |
| `GET /soundhole/spiral/default` | DONE |
| `POST /soundhole/spiral/geometry` | DONE |
| `POST /soundhole/spiral/dxf` | DONE |
| `POST /soundhole/spiral/validate` | DONE |

## 2.5 Test Status

| Test File | Status | Notes |
|-----------|--------|-------|
| `test_soundhole_spiral_endpoint.py` | 8/8 PASS | API integration |
| `test_soundhole_spiral.py` | FAIL | Old API signatures (bout_radius_mm vs start_radius_mm) |
| `test_spiral_q_fh_solver.py` | EXISTS | Not yet run |

---

# 3. The Calibration Problem

## 3.1 Problem Statement

The acoustic model predicts f_H and Q from spiral geometry:

```
f_H = (c / 2π) × √(A_total / (V × L_eff_eq))

Q = ω_H × M_eq / R_eq
```

Where:
- `L_eff_eq` depends on `slot_end_correction_alpha` and `distributed_path_factor`
- `R_eq` depends on `loss_scale` and loss model coefficients

**The problem:** We have literature estimates for these constants, but no field validation. The model may be 10-30% off from reality.

## 3.2 Why This Matters

| If calibration is wrong... | Consequence |
|----------------------------|-------------|
| α too high | Predicted f_H too low, builds come out bright |
| α too low | Predicted f_H too high, builds come out dark |
| β too high | Over-estimates tornavoz effect, expects more bass |
| β too low | Under-estimates inertance, Q predictions unreliable |
| loss_scale wrong | Q predictions off, can't tune damping |

For a production luthier tool, ±5 Hz accuracy on f_H is the target. Current uncalibrated model may be ±15 Hz.

## 3.3 The Inverse Calibration Approach

Instead of solving for spiral geometry (current capability), we solve for calibration constants:

```
CURRENT: Given (f_H_target, Q_target, body_spec) → Solve for spiral_geometry
NEEDED:  Given (f_H_measured, Q_measured, spiral_geometry, body_spec) → Solve for (α, β, loss_scale)
```

This requires:
1. Building instruments with known spiral geometry
2. Measuring f_H and Q on completed bodies
3. Running the inverse solver to fit calibration constants
4. Validating on hold-out instruments

## 3.4 Calibration Dataset Requirements

| Requirement | Minimum | Ideal |
|-------------|---------|-------|
| Number of instruments | 3 | 6+ |
| Geometry variation | 2 slot widths | Full preset range |
| Body style variation | 1 | 2-3 |
| Measurement quality | Phase 1 (single-mic) | Phase 2 (ODS) |
| Repeated measurements | 1 per instrument | 3 per instrument |

With 3 instruments and 3 unknowns (α, β, loss_scale), the system is exactly determined. More instruments provide overdetermined system for robust fitting.

---

# 4. Tap-Tone-Pi Measurement Capabilities

## 4.1 Relevant Measurement Workflows

### 4.1.1 Phase 1 — Single-Mic Tap Tone

**Purpose:** Quick f_H identification from assembled body.

**Process:**
1. Excite body (tap or speaker chirp)
2. Record with calibrated microphone
3. FFT → peak detection → modal frequencies

**Output:** Peak frequencies with prominence, sufficient for f_H identification.

**Limitation:** Q estimation less reliable without transfer function.

### 4.1.2 Phase 2 — ODS Grid Scanning

**Purpose:** Full modal analysis with Q extraction.

**Process:**
1. Define grid points on soundboard
2. Roving microphone captures at each point
3. Compute transfer functions and coherence
4. Modal identification with stabilization diagram

**Output:** 
- Modal frequencies with confidence
- Q factors from bandwidth
- Mode shapes (ODS)
- Coherence quality metric

**Source:** `tap_tone_pi/tap_tone_pi/damping/modes.py`

```python
@dataclass
class ModeIdentificationResult:
    frequency_hz: float
    damping_ratio: float        # ζ = 1/(2Q)
    quality_factor: float       # Q = f_n / bandwidth
    confidence: ModeConfidence
    bandwidth_hz: float
    spectral_prominence: float
```

### 4.1.3 Bending Stiffness

**Purpose:** Measure wood properties for loss model inputs.

**Output schema:** `contracts/schemas/moe_result.schema.json`

```json
{
  "E_GPa": 11.5,
  "EI_Nmm2": 245000,
  "uncertainty": {
    "E_GPa_pm": 0.3
  },
  "environment": {
    "temp_C": 22.5,
    "rh_pct": 45
  }
}
```

### 4.1.4 Wood Properties Analysis

**Source:** `tap_tone_pi/analyzer/analysis/wood_properties.py`

```python
@dataclass
class WoodProperties:
    density_kg_m3: float
    stiffness_along_gpa: float      # E_L
    stiffness_cross_gpa: float      # E_C (if measured)
    radiation_coefficient: float    # sqrt(E/ρ) / 1000
    damping_factor: float           # From peak bandwidth
    fundamental_hz: float
    confidence: float
```

## 4.2 Coupled Oscillator Model in Tap-Tone-Pi

**Source:** `tap_tone_pi/tap_tone_pi/design/coupled_2osc.py`

This module provides the theoretical framework that the spiral calibration must align with:

```python
def coupled_2osc_eigenfrequencies(
    # Top plate
    E_L_top, E_C_top, rho_top, h_top, a_top, b_top,
    A_eff_top, eta_top, gamma_top,
    # Cavity
    volume, hole_area, L_eff,  # <-- This is what spiral model must provide
    # Air
    rho_air, c_air,
) -> Tuple[eigenfrequencies, eigenvectors, info]:
```

**Key insight:** The `L_eff` parameter in this model is what the spiral acoustic model must correctly predict. If spiral model's `effective_length_spiral_m()` is wrong, the coupled mode predictions will be wrong.

## 4.3 Viewer Pack Contract

**Source:** `tap_tone_pi/contracts/viewer_pack_v1.schema.json`

The viewer pack is the **sanctioned export format** for measurement data. It includes:

```json
{
  "schema_version": "v1",
  "measurement_only": true,
  "interpretation": "deferred",
  "contents": {
    "audio": true,
    "spectra": true,
    "coherence": true,
    "ods": true,
    "wolf": true,
    "bending": true
  },
  "bending": {
    "E_L_GPa": 11.5,
    "E_C_GPa": 0.75,
    "density_g_cm3": 0.42,
    "c_m_s": 5200
  }
}
```

**Integration point:** luthiers-toolbox must read this format, not raw tap_tone_pi internals.

---

# 5. Inverse Solver Architecture

## 5.1 Current Solver Structure

**Source:** `spiral_q_fh_solver.py:421-502`

```python
def solve_spiral_parameters(
    body: BodySpec,
    base_specs: Sequence[SpiralSpec],
    target: TargetSpec,                    # Contains target_f_hz, target_q
    optimize_mask: Sequence[bool],         # Which spirals to optimize
    bounds: SolverBounds,
    global_search: bool = True,
    maxiter: int = 120,
) -> Tuple[List[SpiralSpec], SystemResult, Dict]:
```

**Optimization vector per spiral:**
```
[start_radius_mm, growth_rate_k, turns, slot_width_mm]
```

**Objective function:**
```python
def _objective(x, body, base_specs, optimize_mask, target):
    specs = _vector_to_specs(x, base_specs, optimize_mask)
    result = predict_system(body, specs)
    
    f_err = (result.f_H - target.target_f_hz) / target.target_f_hz
    q_err = (result.q - target.target_q) / target.target_q
    
    cost = weight_f * f_err² + weight_q * q_err²
    return cost
```

## 5.2 Required Extension: Calibration Solver

**New function needed:**

```python
def solve_calibration_constants(
    body: BodySpec,
    spiral_specs: Sequence[SpiralSpec],    # KNOWN geometry (not optimized)
    measured_f_hz: float,                   # From tap_tone_pi
    measured_q: float,                      # From tap_tone_pi
    initial_alpha: float = 0.85,
    initial_beta: float = 0.08,
    initial_loss_scale: float = 1.0,
) -> Tuple[CalibrationResult, Dict]:
    """
    Solve for acoustic calibration constants given measured data.
    
    Optimization vector: [alpha, beta, loss_scale]
    
    Bounds:
        alpha: [0.4, 1.4]       # Slot end correction
        beta:  [0.02, 0.20]     # Distributed path factor
        loss_scale: [0.5, 2.0]  # Loss multiplier
    
    Objective:
        Minimize (f_H_pred - f_H_meas)² + (Q_pred - Q_meas)²
    """
```

**CalibrationResult dataclass:**

```python
@dataclass
class CalibrationResult:
    slot_end_correction_alpha: float
    distributed_path_factor: float
    loss_scale: float
    
    # Fit quality
    f_H_residual_hz: float
    q_residual: float
    r_squared: float
    
    # Uncertainty (from Hessian or bootstrap)
    alpha_std: float
    beta_std: float
    loss_scale_std: float
    
    # Metadata
    n_instruments: int
    body_styles: List[str]
    measurement_source: str  # e.g., "viewer_pack_v1"
```

## 5.3 Multi-Instrument Calibration

For robust calibration across multiple instruments:

```python
def solve_calibration_multi_instrument(
    calibration_dataset: List[CalibrationDataPoint],
) -> CalibrationResult:
    """
    Fit single set of (alpha, beta, loss_scale) across multiple instruments.
    
    Each CalibrationDataPoint contains:
        - body: BodySpec
        - spirals: List[SpiralSpec]
        - measured_f_hz: float
        - measured_q: float
        - weight: float (optional, for heteroscedastic fitting)
    
    Objective:
        Sum over all instruments of weighted squared errors
    """
```

## 5.4 Solver Algorithm Selection

| Algorithm | Pros | Cons | Use When |
|-----------|------|------|----------|
| Nelder-Mead | Fast, no gradients | Local minimum risk | Good initial guess |
| differential_evolution | Global search | Slower | Unknown landscape |
| L-BFGS-B | Fast with bounds | Needs smooth objective | Calibration (smooth) |
| Basin-hopping | Escapes local minima | Slowest | High-stakes calibration |

**Recommendation:** Start with L-BFGS-B (smooth, bounded), fall back to differential_evolution if convergence issues.

---

# 6. Integration Design

## 6.1 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CALIBRATION WORKFLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: BUILD INSTRUMENT
─────────────────────────
    ┌──────────────────────┐
    │ Luthier builds body  │
    │ with spiral soundhole│
    │ (known geometry)     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Record spiral params │
    │ in build manifest    │
    │ (JSON)               │
    └──────────┬───────────┘
               │
               ▼

STEP 2: MEASURE
───────────────
    ┌──────────────────────┐
    │ tap_tone_pi          │
    │ Phase 1 or Phase 2   │
    │ measurement          │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Modal identification │
    │ → f_H, Q, confidence │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Export viewer_pack_v1│
    │ (measurement-only)   │
    └──────────┬───────────┘
               │
               ▼

STEP 3: CALIBRATE
─────────────────
    ┌──────────────────────┐
    │ luthiers-toolbox     │
    │ calibration_bridge.py│
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Read viewer_pack_v1  │
    │ Extract f_H, Q       │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Read build manifest  │
    │ Extract spiral geom  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ solve_calibration_   │
    │ constants()          │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Store calibration    │
    │ result (JSON)        │
    └──────────────────────┘

STEP 4: APPLY
─────────────
    ┌──────────────────────┐
    │ Future predictions   │
    │ use calibrated       │
    │ constants            │
    └──────────────────────┘
```

## 6.2 New Files Required

### 6.2.1 In luthiers-toolbox

| File | Purpose |
|------|---------|
| `services/api/app/calculators/spiral_calibration_bridge.py` | Read tap_tone_pi exports |
| `services/api/app/calculators/spiral_calibration_solver.py` | Inverse solver for constants |
| `contracts/spiral_calibration_dataset.schema.json` | Schema for calibration inputs |
| `contracts/spiral_calibration_result.schema.json` | Schema for calibration outputs |

### 6.2.2 In tap_tone_pi (if needed)

| File | Purpose |
|------|---------|
| `scripts/export/spiral_calibration_export.py` | Export f_H/Q in calibration-friendly format |

**Note:** This may not be needed if viewer_pack_v1 already contains sufficient data.

## 6.3 Schema Definitions

### 6.3.1 Calibration Dataset Entry

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "spiral_calibration_datapoint.schema.json",
  "type": "object",
  "required": ["instrument_id", "body_spec", "spiral_specs", "measurements"],
  "properties": {
    "instrument_id": {
      "type": "string",
      "description": "Unique identifier for this instrument"
    },
    "body_spec": {
      "type": "object",
      "properties": {
        "volume_liters": { "type": "number" },
        "style": { "type": "string" }
      }
    },
    "spiral_specs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "start_radius_mm": { "type": "number" },
          "growth_rate_k": { "type": "number" },
          "turns": { "type": "number" },
          "slot_width_mm": { "type": "number" },
          "top_thickness_mm": { "type": "number" }
        }
      }
    },
    "measurements": {
      "type": "object",
      "properties": {
        "f_H_hz": { "type": "number" },
        "f_H_uncertainty_hz": { "type": "number" },
        "q": { "type": "number" },
        "q_uncertainty": { "type": "number" },
        "measurement_method": { "enum": ["phase1", "phase2"] },
        "viewer_pack_sha256": { "type": "string" }
      }
    },
    "environment": {
      "type": "object",
      "properties": {
        "temp_C": { "type": "number" },
        "rh_pct": { "type": "number" }
      }
    }
  }
}
```

### 6.3.2 Calibration Result

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "spiral_calibration_result.schema.json",
  "type": "object",
  "required": ["calibration_id", "created_utc", "constants", "fit_quality"],
  "properties": {
    "calibration_id": { "type": "string" },
    "created_utc": { "type": "string", "format": "date-time" },
    "constants": {
      "type": "object",
      "properties": {
        "slot_end_correction_alpha": { "type": "number" },
        "distributed_path_factor": { "type": "number" },
        "loss_scale": { "type": "number" }
      }
    },
    "uncertainty": {
      "type": "object",
      "properties": {
        "alpha_std": { "type": "number" },
        "beta_std": { "type": "number" },
        "loss_scale_std": { "type": "number" }
      }
    },
    "fit_quality": {
      "type": "object",
      "properties": {
        "r_squared": { "type": "number" },
        "rmse_f_hz": { "type": "number" },
        "rmse_q": { "type": "number" },
        "n_instruments": { "type": "integer" }
      }
    },
    "dataset_sha256": { "type": "string" },
    "body_styles_included": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

## 6.4 API Endpoint Extensions

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/spiral/calibration/upload` | POST | Upload calibration dataset |
| `/api/spiral/calibration/solve` | POST | Run calibration solver |
| `/api/spiral/calibration/current` | GET | Get active calibration constants |
| `/api/spiral/calibration/predict` | POST | Forward prediction with calibrated model |

---

# 7. Open Questions Requiring Resolution

## 7.1 Instrument Availability

**Question:** Do you have spiral soundhole instruments built and ready for tap-tone measurement?

**Why it matters:** The inverse solver needs measured f_H and Q from real bodies. Without physical instruments, calibration cannot proceed.

**Ideal answer:** 
- 3+ instruments with different spiral geometries
- Carlos Jumbo body style (or known body with measured volume)
- Documented spiral parameters for each

**Fallback if no instruments exist:**
- Build one calibration prototype
- Use literature values with explicit uncertainty
- Plan calibration as future sprint

## 7.2 Measurement Protocol Selection

**Question:** What tap-tone measurement protocol should we use?

**Options:**

| Protocol | Effort | f_H Accuracy | Q Accuracy |
|----------|--------|--------------|------------|
| Phase 1 (single-mic) | 15 min | ±3 Hz | ±20% |
| Phase 2 (ODS grid) | 2 hours | ±1 Hz | ±5% |
| Both | 2.5 hours | Best | Best |

**Recommendation:** Phase 1 for f_H identification, Phase 2 if Q calibration is critical.

## 7.3 Repository Location for Calibration Code

**Question:** Should the calibration solver live in tap_tone_pi or luthiers-toolbox?

**Analysis:**

| Option | Pros | Cons |
|--------|------|------|
| tap_tone_pi | Close to measurement data | Violates measurement boundary |
| luthiers-toolbox | Respects architecture | Must import viewer_pack format |
| New shared package | Clean separation | Maintenance overhead |

**Recommendation:** luthiers-toolbox. The calibration is interpretation/optimization, which belongs outside the measurement-only boundary.

## 7.4 Target Body for First Calibration

**Question:** What body should we calibrate first?

**Options:**

| Body Style | Volume (L) | Spiral Config | Priority |
|------------|------------|---------------|----------|
| Carlos Jumbo | ~21 | Dual spiral | HIGH (reference design) |
| Dreadnought | ~22 | Single spiral | MEDIUM (common body) |
| OM/000 | ~17.5 | Compact spiral | MEDIUM (smaller body) |

**Recommendation:** Carlos Jumbo first (it's the reference design for the dual-spiral system).

## 7.5 Global vs. Per-Body Calibration

**Question:** Do you want a single global calibration or per-body-style calibration curves?

**Analysis:**

| Approach | Pros | Cons |
|----------|------|------|
| Global | One set of constants, simpler | May not fit all body styles |
| Per-body-style | Better fit | Needs 3+ instruments per style |
| Hierarchical | Best of both | Complex implementation |

**Recommendation:** Start with global calibration. If residuals are body-style-dependent, add per-style offsets later.

## 7.6 Uncertainty Quantification

**Question:** How should we propagate measurement uncertainty to calibration uncertainty?

**Options:**

1. **Bootstrap resampling** — resample dataset, refit, compute std
2. **Hessian inversion** — compute covariance from curvature at optimum
3. **Bayesian inference** — full posterior distribution via MCMC

**Recommendation:** Hessian inversion for initial implementation (fast, adequate). Bootstrap for validation. Bayesian if high-stakes decisions depend on calibration.

---

# 8. Implementation Plan

## 8.1 Phase 1: Foundation (Week 1)

### 8.1.1 Create Calibration Bridge Module

**File:** `services/api/app/calculators/spiral_calibration_bridge.py`

```python
"""
Bridge module for importing tap_tone_pi viewer_pack_v1 data
into the spiral calibration workflow.
"""

from pathlib import Path
from typing import Optional
import json

from pydantic import BaseModel, Field


class ViewerPackImport(BaseModel):
    """Extracted calibration-relevant data from viewer_pack_v1."""
    
    source_path: str
    schema_version: str
    
    # Modal data (extracted from analysis)
    f_H_hz: Optional[float] = None
    f_H_confidence: Optional[float] = None
    q_factor: Optional[float] = None
    q_confidence: Optional[float] = None
    
    # Wood properties (if bending data present)
    E_L_GPa: Optional[float] = None
    E_C_GPa: Optional[float] = None
    density_g_cm3: Optional[float] = None
    
    # Environment
    temp_C: Optional[float] = None
    rh_pct: Optional[float] = None


def import_viewer_pack(path: Path) -> ViewerPackImport:
    """
    Import a tap_tone_pi viewer_pack_v1 and extract calibration data.
    
    Args:
        path: Path to viewer_pack manifest.json
        
    Returns:
        ViewerPackImport with extracted data
        
    Raises:
        ValueError: If schema_version != 'v1' or measurement_only != True
    """
    with open(path) as f:
        manifest = json.load(f)
    
    # Validate measurement boundary
    if manifest.get("measurement_only") != True:
        raise ValueError("Only measurement-only viewer packs are accepted")
    
    if manifest.get("schema_version") != "v1":
        raise ValueError(f"Unsupported schema version: {manifest.get('schema_version')}")
    
    # Extract modal data
    # NOTE: This requires reading analysis files within the pack
    # Implementation depends on how modal ID results are stored
    
    result = ViewerPackImport(
        source_path=str(path),
        schema_version=manifest["schema_version"],
    )
    
    # Extract bending data if present
    if "bending" in manifest:
        b = manifest["bending"]
        result.E_L_GPa = b.get("E_L_GPa")
        result.E_C_GPa = b.get("E_C_GPa")
        result.density_g_cm3 = b.get("density_g_cm3")
    
    return result
```

### 8.1.2 Create Calibration Solver Module

**File:** `services/api/app/calculators/spiral_calibration_solver.py`

```python
"""
Inverse solver for spiral acoustic model calibration constants.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np
from scipy.optimize import minimize, differential_evolution

# Import existing solver components
from spiral_q_fh_solver import (
    BodySpec, SpiralSpec, predict_system,
    effective_length_m, loss_resistance,
)


@dataclass
class CalibrationDataPoint:
    """One instrument's data for calibration."""
    instrument_id: str
    body: BodySpec
    spirals: List[SpiralSpec]
    measured_f_hz: float
    measured_q: float
    weight: float = 1.0


@dataclass
class CalibrationResult:
    """Result of calibration fitting."""
    alpha: float
    beta: float
    loss_scale: float
    
    alpha_std: float
    beta_std: float
    loss_scale_std: float
    
    r_squared: float
    rmse_f_hz: float
    rmse_q: float
    n_instruments: int


def _apply_calibration(
    spirals: List[SpiralSpec],
    alpha: float,
    beta: float,
    loss_scale: float,
) -> List[SpiralSpec]:
    """Apply calibration constants to spiral specs."""
    return [
        SpiralSpec(
            start_radius_mm=s.start_radius_mm,
            growth_rate_k=s.growth_rate_k,
            turns=s.turns,
            slot_width_mm=s.slot_width_mm,
            top_thickness_mm=s.top_thickness_mm,
            label=s.label,
            slot_end_correction_alpha=alpha,
            distributed_path_factor=beta,
            loss_scale=loss_scale,
        )
        for s in spirals
    ]


def _calibration_objective(
    x: np.ndarray,
    dataset: List[CalibrationDataPoint],
) -> float:
    """
    Objective function for calibration fitting.
    
    Args:
        x: [alpha, beta, loss_scale]
        dataset: List of calibration data points
        
    Returns:
        Weighted sum of squared errors
    """
    alpha, beta, loss_scale = x
    
    total_cost = 0.0
    
    for dp in dataset:
        # Apply calibration to this instrument's spirals
        calibrated = _apply_calibration(dp.spirals, alpha, beta, loss_scale)
        
        # Predict f_H and Q
        try:
            result = predict_system(dp.body, calibrated)
        except Exception:
            return 1e12  # Infeasible
        
        # Relative errors
        f_err = (result.helmholtz_frequency_hz - dp.measured_f_hz) / dp.measured_f_hz
        q_err = (result.q - dp.measured_q) / dp.measured_q
        
        # Weighted squared error
        total_cost += dp.weight * (f_err**2 + 0.5 * q_err**2)
    
    return total_cost


def solve_calibration(
    dataset: List[CalibrationDataPoint],
    initial_alpha: float = 0.85,
    initial_beta: float = 0.08,
    initial_loss_scale: float = 1.0,
    global_search: bool = True,
) -> CalibrationResult:
    """
    Solve for calibration constants from measured data.
    
    Args:
        dataset: List of calibration data points
        initial_*: Starting values for constants
        global_search: If True, use differential_evolution first
        
    Returns:
        CalibrationResult with fitted constants and fit quality
    """
    bounds = [
        (0.4, 1.4),    # alpha
        (0.02, 0.20),  # beta
        (0.5, 2.0),    # loss_scale
    ]
    
    if global_search:
        de_result = differential_evolution(
            _calibration_objective,
            bounds=bounds,
            args=(dataset,),
            seed=42,
            maxiter=100,
            polish=False,
        )
        x0 = de_result.x
    else:
        x0 = np.array([initial_alpha, initial_beta, initial_loss_scale])
    
    # Local refinement
    local_result = minimize(
        _calibration_objective,
        x0=x0,
        args=(dataset,),
        method="L-BFGS-B",
        bounds=bounds,
    )
    
    alpha, beta, loss_scale = local_result.x
    
    # Compute fit quality metrics
    predictions = []
    for dp in dataset:
        calibrated = _apply_calibration(dp.spirals, alpha, beta, loss_scale)
        result = predict_system(dp.body, calibrated)
        predictions.append((result.helmholtz_frequency_hz, result.q))
    
    measured_f = np.array([dp.measured_f_hz for dp in dataset])
    measured_q = np.array([dp.measured_q for dp in dataset])
    pred_f = np.array([p[0] for p in predictions])
    pred_q = np.array([p[1] for p in predictions])
    
    rmse_f = np.sqrt(np.mean((pred_f - measured_f)**2))
    rmse_q = np.sqrt(np.mean((pred_q - measured_q)**2))
    
    ss_res_f = np.sum((pred_f - measured_f)**2)
    ss_tot_f = np.sum((measured_f - np.mean(measured_f))**2)
    r_squared = 1 - ss_res_f / ss_tot_f if ss_tot_f > 0 else 0
    
    # Uncertainty from Hessian (simplified)
    # Full implementation would compute Hessian at optimum
    alpha_std = 0.05  # Placeholder
    beta_std = 0.01   # Placeholder
    loss_scale_std = 0.1  # Placeholder
    
    return CalibrationResult(
        alpha=alpha,
        beta=beta,
        loss_scale=loss_scale,
        alpha_std=alpha_std,
        beta_std=beta_std,
        loss_scale_std=loss_scale_std,
        r_squared=r_squared,
        rmse_f_hz=rmse_f,
        rmse_q=rmse_q,
        n_instruments=len(dataset),
    )
```

### 8.1.3 Create Schema Files

Create `contracts/spiral_calibration_dataset.schema.json` and `contracts/spiral_calibration_result.schema.json` as defined in Section 6.3.

## 8.2 Phase 2: Measurement Campaign (Week 2-3)

### 8.2.1 Build Manifest Template

Create a template for recording spiral geometry during builds:

**File:** `templates/spiral_build_manifest.json`

```json
{
  "instrument_id": "carlos_jumbo_001",
  "build_date": "2026-05-XX",
  "body_style": "carlos_jumbo",
  "body_volume_liters": 21.0,
  "spirals": [
    {
      "label": "upper_bass",
      "center_x_mm": -88.0,
      "center_y_mm": -62.0,
      "start_radius_mm": 10.0,
      "growth_rate_k": 0.18,
      "turns": 1.1,
      "slot_width_mm": 14.0,
      "rotation_deg": 270.0,
      "top_thickness_mm": 2.6
    },
    {
      "label": "lower_treble",
      "center_x_mm": 78.0,
      "center_y_mm": 112.0,
      "start_radius_mm": 10.0,
      "growth_rate_k": 0.18,
      "turns": 1.1,
      "slot_width_mm": 14.0,
      "rotation_deg": 90.0,
      "top_thickness_mm": 2.6
    }
  ],
  "notes": ""
}
```

### 8.2.2 Measurement Protocol

1. Complete body assembly (strung or unstrung)
2. Record environmental conditions (temp, RH)
3. Run tap_tone_pi Phase 1 or Phase 2
4. Export viewer_pack_v1
5. Link viewer_pack to build manifest

## 8.3 Phase 3: Calibration and Validation (Week 4)

### 8.3.1 Initial Calibration

```python
# Load dataset
dataset = []
for manifest_path in Path("calibration_data/").glob("*.json"):
    dp = load_calibration_datapoint(manifest_path)
    dataset.append(dp)

# Run calibration
result = solve_calibration(dataset)

print(f"Alpha: {result.alpha:.3f} ± {result.alpha_std:.3f}")
print(f"Beta:  {result.beta:.3f} ± {result.beta_std:.3f}")
print(f"Loss:  {result.loss_scale:.3f} ± {result.loss_scale_std:.3f}")
print(f"R²:    {result.r_squared:.3f}")
print(f"RMSE f_H: {result.rmse_f_hz:.1f} Hz")
```

### 8.3.2 Validation on Hold-Out

If 6+ instruments available:
- Use 4 for training
- Hold out 2 for validation
- Report prediction error on hold-out

### 8.3.3 Update Default Constants

Once calibrated:

```python
# Update defaults in spiral_acoustic_model.py
CALIBRATED_ALPHA = 0.XX  # From calibration
CALIBRATED_BETA = 0.XX   # From calibration
CALIBRATED_LOSS_SCALE = X.XX  # From calibration
CALIBRATION_DATE = "2026-05-XX"
CALIBRATION_DATASET = "sha256:..."
```

## 8.4 Phase 4: API Integration (Week 5)

### 8.4.1 Add Calibration Endpoints

```python
@router.post("/calibration/upload")
async def upload_calibration_dataset(dataset: CalibrationDataset):
    """Upload calibration dataset."""
    ...

@router.post("/calibration/solve")
async def run_calibration(request: CalibrationRequest):
    """Run calibration solver on uploaded dataset."""
    ...

@router.get("/calibration/current")
async def get_current_calibration():
    """Get currently active calibration constants."""
    ...
```

### 8.4.2 Update Forward Prediction to Use Calibration

Modify `spiral_q_fh_solver.py:predict_system()` to read calibrated constants from config rather than hardcoded defaults.

---

# 9. Risk Analysis

## 9.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Insufficient instruments for calibration | HIGH | HIGH | Start with 1 instrument, accept wider uncertainty |
| Non-identifiable parameters | MEDIUM | HIGH | Fix one parameter, solve for others |
| Model structure wrong (not just constants) | MEDIUM | HIGH | Residual analysis, consider model extensions |
| Q measurement unreliable | MEDIUM | MEDIUM | Rely more on f_H, downweight Q in objective |
| Environment variation | LOW | MEDIUM | Record temp/RH, consider as covariate |

## 9.2 Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Instrument build delays | HIGH | HIGH | Start with existing instruments if available |
| Measurement equipment issues | LOW | HIGH | Validate tap_tone_pi setup first |
| Solver convergence issues | LOW | MEDIUM | Multiple initializations, global search |

## 9.3 Integration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| viewer_pack format changes | LOW | MEDIUM | Pin schema version, validate on import |
| Boundary violation temptation | MEDIUM | LOW | Code review, CI guard |
| Cross-repo dependency brittleness | MEDIUM | MEDIUM | Loose coupling via JSON, no direct imports |

---

# 10. File Reference

## 10.1 luthiers-toolbox Files

| File | Purpose | Status |
|------|---------|--------|
| `spiral_q_fh_solver.py` | Forward/inverse solver | EXISTS |
| `spiral_acoustic_model.py` | Acoustic model | EXISTS |
| `services/api/app/instrument_geometry/soundhole/spiral_geometry.py` | Geometry engine | EXISTS |
| `services/api/app/calculators/soundhole_facade.py` | API facade | EXISTS |
| `services/api/app/routers/instrument_geometry/soundhole_router.py` | REST endpoints | EXISTS |
| `services/api/app/calculators/spiral_calibration_bridge.py` | Import tap_tone_pi data | TO CREATE |
| `services/api/app/calculators/spiral_calibration_solver.py` | Calibration solver | TO CREATE |
| `contracts/spiral_calibration_dataset.schema.json` | Dataset schema | TO CREATE |
| `contracts/spiral_calibration_result.schema.json` | Result schema | TO CREATE |

## 10.2 tap_tone_pi Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `tap_tone_pi/damping/modes.py` | Modal identification | f_H, Q extraction |
| `tap_tone_pi/design/coupled_2osc.py` | Coupled model | Theoretical alignment |
| `analyzer/analysis/wood_properties.py` | Wood properties | Loss model inputs |
| `contracts/viewer_pack_v1.schema.json` | Export format | Integration point |
| `contracts/schemas/moe_result.schema.json` | Bending data | Stiffness inputs |

---

# Appendix: Mathematical Foundation

## A.1 Helmholtz Resonator

```
f_H = (c / 2π) × √(A / (V × L_eff))
```

Where:
- c = speed of sound (~343 m/s)
- A = total port area (m²)
- V = cavity volume (m³)
- L_eff = effective acoustic length (m)

## A.2 Effective Length for Spiral

```
L_eff = t + α × w + β × L_path
```

Where:
- t = top thickness (m)
- w = slot width (m)
- α = slot end correction factor (calibrate)
- L_path = spiral path length (m)
- β = distributed path factor (calibrate)

## A.3 Path Length (Closed Form)

For logarithmic spiral r(θ) = r₀ × e^(k×θ):

```
L_path = √(1 + k²) × (r₁ - r₀) / k
```

Where r₁ = r₀ × e^(k × θ_max) and θ_max = 2π × turns.

## A.4 Quality Factor

```
Q = ω_H × M_eq / R_eq
```

Where:
- ω_H = 2π × f_H
- M_eq = equivalent acoustic mass
- R_eq = equivalent loss resistance

## A.5 Loss Model

```
R_loss = loss_scale × (R_viscous + R_rad + R_curv)
```

Where:
- R_viscous ∝ μ × P / A² (boundary layer)
- R_rad ∝ ρ₀ × c × √A (radiation)
- R_curv ∝ ρ₀ × ω × L_path / √r_inner (curvature)

## A.6 Parallel Port Combination

For N parallel ports:

```
A_total = Σᵢ Aᵢ

L_eff_eq = A_total / Σᵢ (Aᵢ / L_eff,i)
```

---

# Conclusion

The spiral soundhole system is geometrically complete but acoustically uncalibrated. This document provides the architecture for a field calibration system that respects the measurement boundary between tap_tone_pi and luthiers-toolbox.

**Next action:** Resolve the open questions in Section 7, then proceed with Phase 1 implementation.

---

*Handoff prepared by Claude Code*  
*For The Production Shop — luthiers-toolbox*  
*2026-05-03*
