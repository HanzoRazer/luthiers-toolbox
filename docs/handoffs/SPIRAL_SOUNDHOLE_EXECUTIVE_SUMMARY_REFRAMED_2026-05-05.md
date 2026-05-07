# Spiral Soundhole — Reframed Executive Summary & Inverse Calibration Plan

**Date:** 2026-05-05  
**Status:** Geometry production-ready; acoustic comparison and inverse calibration experimental  
**Reframing:** Spiral soundholes are being evaluated as **candidate replacement apertures** for conventional guitar soundholes, not primarily as tornavoz replacements.

---

## 1. Executive Reframe

The spiral soundhole feature should be reframed from:

> “A spiral behaves like a distributed, lossy tornavoz.”

to:

> **A spiral soundhole is a candidate replacement aperture for round, oval, D-hole, and Tacoma-style offset/duck-head soundholes. A tornavoz is only an optional compensation layer if the spiral aperture does not meet acoustic targets by itself.**

This matters because the mathematical reference object changes.

The primary comparison is now:

\[
\text{round / oval / D-hole / Tacoma aperture} \quad \Longleftrightarrow \quad \text{spiral aperture}
\]

not:

\[
\text{tornavoz} \quad \Longleftrightarrow \quad \text{spiral}
\]

The tornavoz remains relevant, but as a fallback correction if the spiral aperture lacks sufficient effective acoustic length, lower-mid coupling, or impedance control.

---

## 2. Current Software Status

The existing geometry implementation remains valid and useful.

### Production-Ready

| Component | Status |
|---|---|
| Geometry engine | Complete |
| Spiral presets | Complete |
| API endpoints | Complete |
| DXF export | Complete |
| Endpoint tests | Passing |
| Acoustic model | Experimental / uncalibrated |

The current system already defines logarithmic spiral geometry:

\[
r(\theta)=r_0e^{k\theta}
\]

and the constant-width slot relationship:

\[
P:A = \frac{2}{w}
\]

where \(w\) is slot width.

That geometry is still the foundation. The major change is how the acoustic model is interpreted.

---

## 3. Corrected Acoustic Question

The next-phase question is:

\[
\boxed{
\text{Can a spiral aperture replace a conventional aperture while preserving or improving measurable acoustic behavior?}
}
\]

The conventional aperture families to compare against are:

1. Round soundhole  
2. Oval / Selmer-style aperture  
3. D-hole / Maccaferri-style aperture  
4. Tacoma-style offset / duck-head soundhole  
5. Spiral aperture  
6. Spiral aperture plus optional trim port  
7. Spiral aperture plus optional tornavoz correction

The spiral is not assumed to be better. It is evaluated by measurement and calibration.

---

## 4. Mathematical Reframe

### 4.1 Previous Model Emphasis

The previous model emphasized:

\[
L_{\text{eff}},\quad R_{\text{loss}},\quad Q
\]

as though the spiral were primarily trying to reproduce tornavoz behavior.

That model is still useful, but it is now a **secondary correction model**.

### 4.2 New Primary Model

The primary model compares aperture families using:

\[
A,\quad P,\quad L_{\text{eff}},\quad f_H,\quad Q_H,\quad R_{\text{loss}},\quad \text{structural penalty}
\]

with the base Helmholtz relation:

\[
f_H=\frac{c}{2\pi}\sqrt{\frac{A}{V L_{\text{eff}}}}
\]

The core inverse problem becomes:

\[
\boxed{
\text{Given measured } f_H,Q,\text{ and known body/aperture geometry, estimate the aperture model constants.}
}
\]

---

## 5. Tornavoz Repositioned as Optional Compensation

The tornavoz should be modeled as an optional impedance attachment:

\[
L_{\text{eff, corrected}} =
L_{\text{eff, aperture}} + L_{\text{tornavoz}}
\]

or in impedance form:

\[
Z_{\text{total}} = Z_{\text{aperture}} + Z_{\text{tornavoz}}
\]

It should not be embedded into the spiral geometry class as if it were intrinsic to the aperture.

### Correct Role

| Item | Role |
|---|---|
| Spiral aperture | Primary candidate replacement soundhole |
| Third spiral / trim port | Optional treble / upper-mid balancing aperture |
| Tornavoz | Optional compensation if aperture-only result underperforms |

---

## 6. Inverse Math Concept

The repos already contain the inverse-solver concept: predict or solve for unknown design variables using measured frequency and damping data.

The corrected inverse workflow is:

### 6.1 Forward Model

Given:

\[
\text{body volume},\quad \text{aperture geometry},\quad \text{estimated constants}
\]

predict:

\[
f_H,\quad Q,\quad L_{\text{eff}},\quad R_{\text{loss}}
\]

### 6.2 Inverse Calibration Model

Given:

\[
f_{H,\text{measured}},\quad Q_{\text{measured}},\quad \text{known aperture geometry},\quad \text{known body volume}
\]

solve for:

\[
\alpha,\quad \beta,\quad \lambda_{\text{loss}}
\]

where:

- \(\alpha\): aperture end-correction coefficient  
- \(\beta\): distributed path contribution coefficient  
- \(\lambda_{\text{loss}}\): damping/loss scale  

### 6.3 Design Solver

After calibration, solve the design problem:

\[
\text{Find aperture dimensions that match target } f_H,Q,\text{ and structural limits.}
\]

This is not a measurement task. It belongs in the design/modeling repo, not in the desktop analyzer.

---

## 7. tap_tone_pi Boundary

The desktop analyzer remains measurement-only.

It should not solve geometry.

It should record:

\[
f_H,\quad Q,\quad \text{decay},\quad \text{spectra},\quad \text{coherence},\quad \text{metadata}
\]

The design/modeling side consumes those measurements.

### Correct Repository Boundary

| Repo / Tool | Responsibility |
|---|---|
| tap_tone_pi | Measurement, data collection, evidence export |
| luthiers-toolbox | Geometry, modeling, inverse solver, design interpretation |
| bridge scripts | Convert measurement output into calibration datasets |

The analyzer may store metadata such as aperture type and test state, but it should not compute or optimize aperture geometry.

---

## 8. Reframing the Four Python Scripts

Four scripts/modules should be reframed as a pipeline rather than as separate experiments.

---

### 8.1 `spiral_geometry.py`

**Current role:** Spiral geometry engine.

**Reframed role:** One aperture-geometry implementation inside a broader aperture comparison system.

It should remain responsible for:

- centerline generation  
- wall offsets  
- area  
- perimeter  
- DXF output  
- Carlos Jumbo presets  

It should not compute acoustic truth.

Recommended future abstraction:

```python
class ApertureGeometry:
    def area(self) -> float: ...
    def perimeter(self) -> float: ...
    def characteristic_length(self) -> float: ...
```

Then spiral becomes:

```python
class SpiralApertureGeometry(ApertureGeometry):
    ...
```

---

### 8.2 `spiral_acoustic_model.py`

**Current role:** Forward acoustic model for spiral ports.

**Reframed role:** Aperture acoustic model, generalized beyond spirals.

It should become or feed into:

```python
aperture_acoustic_model.py
```

with aperture classes:

```python
RoundApertureSpec
OvalApertureSpec
DHoleApertureSpec
DuckHeadApertureSpec
SpiralApertureSpec
```

Each aperture computes:

\[
A,\quad P,\quad L_{\text{eff}},\quad R_{\text{loss}},\quad f_H,\quad Q
\]

The spiral model remains one candidate among several.

---

### 8.3 `spiral_q_fh_solver.py`

**Current role:** Numerical solver to fit spiral parameters to target \(f_H\) and \(Q\).

**Reframed role:** Aperture replacement solver.

It should answer:

\[
\boxed{
\text{Can candidate aperture geometry match the reference aperture's measured or target } f_H,Q?
}
\]

Recommended new name:

```text
aperture_q_fh_solver.py
```

Recommended solver modes:

1. **Reference matching**
   - Match spiral aperture to round / oval / D-hole / Tacoma aperture.

2. **Measured calibration**
   - Use tap_tone_pi measured \(f_H,Q\) to calibrate model constants.

3. **Compensation solve**
   - If spiral-only underperforms, estimate optional tornavoz correction length.

---

### 8.4 Interactive Math Solver

**Current role:** Interactive exploration of target \(f_H,Q\) and spiral parameters.

**Reframed role:** Interactive aperture comparison and inverse calibration tool.

It should allow the user to select:

```text
reference aperture: round | oval | D-hole | Tacoma duck-head
candidate aperture: spiral | spiral + trim port | spiral + tornavoz
body volume
measured f_H
measured Q
```

Then it should output:

- predicted vs measured \(f_H\)
- predicted vs measured \(Q\)
- required \(L_{\text{eff}}\)
- estimated aperture dimensions
- optional tornavoz correction if needed
- confidence / calibration status

The interface should avoid claims like “best tone.” It should report model fit and measurement comparison.

---

## 9. New Comparison Objective

The solver objective should be reframed as:

\[
J =
w_f(f_H-f_{H,\text{ref}})^2
+
w_Q(Q-Q_{\text{ref}})^2
+
w_A(A-A_{\text{ref}})^2
+
w_P(P-P_{\text{ref}})^2
+
w_S S_{\text{structural}}
\]

where:

- \(f_{H,\text{ref}}\): reference aperture air resonance  
- \(Q_{\text{ref}}\): reference aperture Q  
- \(A_{\text{ref}}\): reference aperture area  
- \(P_{\text{ref}}\): reference aperture perimeter  
- \(S_{\text{structural}}\): structural penalty, such as bridge-zone intrusion or weak web thickness  

This turns the spiral aperture into a candidate design, not a predetermined solution.

---

## 10. Measurement Campaign Reframe

The experimental campaign should test aperture replacement in stages:

1. Closed body / no aperture  
2. Conventional reference aperture  
   - round, oval, D-hole, or Tacoma-style  
3. Spiral aperture with equivalent area target  
4. Spiral aperture with optimized perimeter/area  
5. Spiral + small trim port  
6. Spiral + tornavoz only if needed  

This lets the data show whether the spiral can replace the conventional aperture before adding compensation.

---

## 11. Recommended Executive Summary Replacement Text

The executive summary should say:

> The spiral soundhole is a production-ready geometry feature and an experimental acoustic aperture family. The next phase is to evaluate whether logarithmic spiral apertures can replace conventional round, oval, D-hole, or Tacoma-style offset soundholes. The acoustic model should compare aperture families using area, perimeter, effective length, Helmholtz frequency, quality factor, and structural penalty. A tornavoz is treated only as an optional compensation layer if spiral-only aperture performance does not meet target measurements.

---

## 12. Developer Task Reframe

### Replace “Spiral Tornavoz Substitute” language with:

```text
Spiral Aperture Replacement Validation
```

### Add or revise modules toward:

```text
aperture_geometry/
aperture_acoustic_model.py
aperture_q_fh_solver.py
aperture_inverse_calibration.py
tap_tone_pi_calibration_bridge.py
```

### Preserve tap_tone_pi boundary:

```text
measurement only, no geometry optimization
```

### Add calibration workflow:

```text
measurement → viewer_pack export → inverse calibration → updated aperture model constants
```

---

## 13. Final Corrected Statement

\[
\boxed{
\text{The spiral soundhole is being tested as a replacement aperture family.}
}
\]

\[
\boxed{
\text{The tornavoz is an optional correction, not the design target.}
}
\]

\[
\boxed{
\text{The inverse solver should estimate either aperture dimensions or model constants from measured } f_H,Q,\text{ and instrument metadata.}
}
\]

---

## 14. Immediate Next Development Step

Create an aperture-level model that generalizes the existing spiral-only scripts:

```text
aperture_acoustic_model.py
aperture_q_fh_solver.py
aperture_inverse_calibration.py
```

Then preserve the existing spiral scripts as implementation references or compatibility wrappers.

---

*Prepared for developer handoff reframing — Spiral Aperture Replacement Validation Phase.*
