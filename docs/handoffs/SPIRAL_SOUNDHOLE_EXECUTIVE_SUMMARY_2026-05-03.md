Below is a **full engineering specification** built from your merged handoff + our session work. This is written as a **design + modeling + implementation spec**, not just a summary, and is structured so it can plug directly into your repo as a Phase-2 document.

---

# 📄 ENGINEERING SPEC

## Spiral Soundhole Acoustic System

### Carlos Jumbo / Selmer / Tacoma Hybrid

---

# 1. Scope

This specification defines:

* The **acoustic model** of the spiral soundhole system
* The **equivalent tornavoz behavior**
* The **distributed damping mechanism**
* The **target performance metrics**
* The **computational extensions required in the codebase**

---

# 2. System Definition

## 2.1 Physical Model

The instrument is modeled as a **coupled vibroacoustic system**:

[
\boxed{
\text{Top plate} + \text{Air cavity} + \text{Port system} + \text{Back plate}
}
]

Reduced-order representation:

[
\begin{aligned}
m_t \ddot{x}_t + c_t \dot{x}*t + k_t x_t + k_c(x_t - x_a) &= F*{\text{string}} \
m_a \ddot{x}_a + c_a \dot{x}_a + k_a x_a + k_c(x_a - x_t) &= 0
\end{aligned}
]

Where:

* (x_t): top displacement
* (x_a): air mode displacement
* (k_a): air stiffness
* (c_a): air + port damping

---

# 3. Helmholtz Subsystem

## 3.1 Base Equation

[
\boxed{
f_H = \frac{c}{2\pi} \sqrt{\frac{A}{V L_{\text{eff}}}}
}
]

---

## 3.2 Effective Length Definition

[
\boxed{
L_{\text{eff}} = L_{\text{geom}} + \Delta L_{\text{end}}
}
]

For circular ports:

[
\Delta L \approx 0.85r
]

For slots / spirals:

[
\Delta L \approx \alpha \cdot w
]

Where:

* (w): slot width
* (\alpha \in [0.6, 1.2]) (empirical)

---

# 4. Spiral Geometry Model

## 4.1 Parametric Form

Logarithmic spiral:

[
r(\theta) = r_0 e^{k\theta}
]

---

## 4.2 Path Length

[
L_{\text{path}} = \int_{\theta_0}^{\theta_1} \sqrt{r^2 + \left(\frac{dr}{d\theta}\right)^2} d\theta
]

Closed form:

[
\boxed{
L_{\text{path}} = \frac{r(\theta)}{\sqrt{1+k^2}} \Big|_{\theta_0}^{\theta_1}
}
]

---

## 4.3 Area and Perimeter

[
A \approx w \cdot L_{\text{path}}
]

[
P \approx 2 L_{\text{path}}
]

[
\boxed{
\frac{P}{A} = \frac{2}{w}
}
]

(Already implemented in your geometry engine)

---

# 5. Tornavoz Equivalence

## 5.1 Acoustic Mass

[
\boxed{
M_a = \rho_0 \frac{L_{\text{eff}}}{A}
}
]

---

## 5.2 Impedance Models

### Ideal tornavoz

[
Z = j\omega M_a
]

---

### Spiral system

[
\boxed{
Z = j\omega M_a + R_{\text{loss}}
}
]

---

# 6. Loss Model (Critical Section)

## 6.1 Boundary Layer Loss

[
R_{\text{viscous}} \propto \frac{\mu P}{A^2}
]

---

## 6.2 Radiation Loss

[
R_{\text{rad}} \propto \rho_0 c_0 \cdot \sigma(f)
]

Where:

* (\sigma(f)): radiation efficiency

---

## 6.3 Curvature Loss

[
R_{\text{curv}} \propto \kappa^2 L_{\text{path}}
]

Where:

* (\kappa): local curvature

---

## 6.4 Total Loss

[
\boxed{
R_{\text{loss}} = R_{\text{viscous}} + R_{\text{rad}} + R_{\text{curv}}
}
]

---

# 7. Quality Factor

[
\boxed{
Q = \frac{\omega M_a}{R_{\text{loss}}}
}
]

---

## 7.1 Target Ranges

| Parameter         | Target            |
| ----------------- | ----------------- |
| (f_H)             | 90–105 Hz         |
| (Q_H)             | 6–10              |
| (Q_{\text{mid}})  | 8–14              |
| (Q_{\text{high}}) | > Selmer baseline |

---

# 8. Multi-Port System

## 8.1 Combined Area

[
A_{\text{total}} = \sum_i A_i
]

---

## 8.2 Combined Length (parallel ports)

[
\frac{1}{L_{\text{eff,total}}} = \sum_i \frac{A_i}{A_{\text{total}}} \cdot \frac{1}{L_{\text{eff},i}}
]

---

## 8.3 Third Spiral Constraint

[
\boxed{
A_3 = 0.10\text{–}0.25(A_1 + A_2)
}
]

---

# 9. Structural Coupling

## 9.1 Plate Stiffness

[
\boxed{
D(x,y) = \frac{E h(x,y)^3}{12(1-\nu^2)}
}
]

---

## 9.2 Thickness Field

| Region  | Thickness  |
| ------- | ---------- |
| Main    | 2.2–2.3 mm |
| Islands | 2.6–2.8 mm |

---

## 9.3 Stiffness Ratio

[
\left(\frac{2.8}{2.3}\right)^3 \approx 1.8
]

---

# 10. Acoustic Radiation

[
\boxed{
P_{\text{rad}} = \frac{1}{2} \rho_0 c_0 \sum_n \sigma_n |v_n|^2 A_n^2
}
]

---

# 11. System Interpretation

[
\boxed{
\text{Spiral = distributed acoustic filter}
}
]

NOT:

* single resonance device
* simple hole

---

# 12. Experimental Design

## 12.1 Test Sequence

1. Closed body
2. Temporary circular port
3. Dual spirals
4. Dual + third spiral
5. Tornavoz inserts

---

## 12.2 Tornavoz Length Sweep

[
L_t = 20, 30, 40, 50\ \text{mm}
]

---

## 12.3 Measurements

* (f_H)
* (Q_H)
* frequency response
* decay (T60)
* bridge mobility
* phase coherence

---

# 13. Acceptance Criteria

[
f_H = 90\text{–}105\ \text{Hz}
]

[
Q_H = 6\text{–}10
]

[
\Delta f_H(\text{third spiral}) \le 8\ \text{Hz}
]

[
Q_{\text{high}} \text{ preserved}
]

---

# 14. Software Architecture Extension

## 14.1 Required Modules

```python
compute_spiral_length(spec)
compute_effective_length(spec)
compute_port_impedance(spec)
estimate_q(spec)
estimate_loss(spec)
```

---

## 14.2 Example Interface

```python
class AcousticPortModel:
    def __init__(self, spiral_spec):
        ...

    def effective_length(self) -> float:
        ...

    def impedance(self, frequency: float) -> complex:
        ...

    def q_factor(self) -> float:
        ...
```

---

# 15. Critical Engineering Insight

[
\boxed{
\text{You cannot increase effective length without increasing loss in a spiral}
}
]

This is the governing constraint.

---

# 16. Design Risk

| Risk         | Cause                         |
| ------------ | ----------------------------- |
| Muddy tone   | excessive perimeter           |
| Weak treble  | high (R_{\text{loss}})        |
| Thin bass    | insufficient (L_{\text{eff}}) |
| Phase issues | multi-port mismatch           |

---

# 17. Final Design Principle

[
\boxed{
\text{Optimize } \frac{L_{\text{eff}}}{R_{\text{loss}}}
}
]

NOT:

* maximize perimeter
* maximize area

---

# 🔚 Final Statement

[
\boxed{
\text{The spiral soundhole is a distributed, lossy substitute for a tornavoz}
}
]

The success of the system depends on:

[
\boxed{
\text{balancing acoustic mass (L_eff) against damping (R_loss)}
}
]

---

If you want next step, I can:

* turn this into a **simulation-ready Python module**
* or build a **numerical solver to predict Q and f_H from your spiral parameters**
* or integrate this directly into your API as a new `/acoustic-model` endpoint
