# Kerf Bending Geometry: Complete Mathematical Derivation

**Document:** Production Shop — Kerfing Calculator Mathematical Basis  
**Author:** Ross L. Echols, Jr., P.E. #78195  
**Module:** `services/api/app/calculators/kerfing_calc.py`  
**Status:** Formal derivation supporting production code

---

## 1. Problem Statement and Scope

Kerf bending is the process of cutting a series of parallel saw slots across the face of a rigid wood strip so that it can be bent to a target curve without steaming or lamination. Two physically independent constraints govern any valid kerf design:

1. **Geometric constraint (Blocklayer):** The total material removed by the cuts must equal the arc length difference between the outer and inner faces of the bent strip.
2. **Structural constraint (Hayward):** The remaining uncut wood between cuts — the *web* — must not fall below an empirically established minimum thickness.

This document derives both constraints from first principles, unifies them into a single modified formula, establishes the feasibility condition, proves a geometric identity, and connects the material's modulus of elasticity (MOE) to a supplementary web stress check.

---

## 2. Notation

| Symbol | Definition | Units |
|--------|-----------|-------|
| $t$ | Strip thickness (radial dimension) | mm |
| $R_\text{out}$ | Outside bend radius (uncut face) | mm |
| $R_\text{in}$ | Inside bend radius (kerfed face) $= R_\text{out} - t$ | mm |
| $\theta$ | Sweep angle of the curve | radians |
| $w$ | Kerf width (actual blade cutting width) | mm |
| $m$ | Minimum web thickness (Hayward) $= 1.6$ mm | mm |
| $n$ | Number of kerf cuts | dimensionless |
| $s$ | Spacing between cuts, center to center | mm |
| $b$ | Web width (wood between adjacent cuts) $= s - w$ | mm |
| $E_C$ | Cross-grain Young's modulus | GPa |
| $\sigma$ | Bending stress at web root | MPa |
| $\text{MOR}_C$ | Cross-grain modulus of rupture | MPa |
| $\phi$ | Safety factor for wood (0.50) | dimensionless |

---

## 3. Geometric Derivation (Blocklayer Constraint)

### 3.1 Arc Length Difference

Consider a straight strip of thickness $t$ bent through sweep angle $\theta$ to a curve of outside radius $R_\text{out}$. The outer face follows a circular arc of length:

$$L_\text{out} = R_\text{out} \cdot \theta$$

The inner face follows a concentric arc at radius $R_\text{in} = R_\text{out} - t$:

$$L_\text{in} = R_\text{in} \cdot \theta = (R_\text{out} - t) \cdot \theta$$

The arc length difference — the excess material on the outer face relative to the inner — is:

$$\Delta L = L_\text{out} - L_\text{in} = R_\text{out} \cdot \theta - (R_\text{out} - t) \cdot \theta = t \cdot \theta$$

**Key result:**

$$\boxed{\Delta L = t \cdot \theta}$$

This is independent of radius. The arc difference depends only on the strip thickness and sweep angle, not on where the curve is located.

### 3.2 Material to Remove

When bent, each kerf slot closes completely. Each slot of width $w$ removes exactly $w$ mm of arc length along the outer face when fully closed. For $n$ cuts to account for the full arc difference:

$$n \cdot w = \Delta L = t \cdot \theta$$

Solving for the exact (non-integer) cut count:

$$n_\text{exact} = \frac{t \cdot \theta}{w}$$

Since cuts must be whole numbers and any underage leaves the kerf not fully closing:

$$\boxed{n_\text{min} = \left\lceil \frac{t \cdot \theta}{w} \right\rceil}$$

This is the **Blocklayer lower bound**: the minimum number of cuts required to geometrically accommodate the target curve.

### 3.3 Even Spacing

With $n$ cuts distributed evenly along the outer face, the center-to-center spacing is:

$$s = \frac{L_\text{out}}{n} = \frac{R_\text{out} \cdot \theta}{n}$$

The resulting web width between adjacent cuts:

$$b = s - w = \frac{R_\text{out} \cdot \theta}{n} - w$$

---

## 4. Structural Derivation (Hayward Constraint)

### 4.1 Empirical Minimum Web

Hayward, writing in *The Woodworker* (1939–1967, reprinted by Lost Art Press 2023), establishes through decades of workshop practice that the remaining wood between kerfs must be at least $\tfrac{1}{16}$ inch:

$$m = \frac{1}{16} \text{ in} = 1.5875 \text{ mm} \approx \mathbf{1.6 \text{ mm}}$$

Below this thickness, the web splits along the grain under the bending stress imposed by closing the adjacent kerfs. This is a structural failure mode — grain shear at the web root — and is empirically established rather than analytically derived.

### 4.2 Web Width Inequality

Applying the Hayward minimum to the web width expression from §3.3:

$$b \geq m$$

$$\frac{R_\text{out} \cdot \theta}{n} - w \geq m$$

$$\frac{R_\text{out} \cdot \theta}{n} \geq w + m$$

$$n \leq \frac{R_\text{out} \cdot \theta}{w + m}$$

Since $n$ must be a whole number:

$$\boxed{n_\text{max} = \left\lfloor \frac{R_\text{out} \cdot \theta}{w + m} \right\rfloor}$$

This is the **Hayward upper bound**: the maximum number of cuts permitted before the web falls below the structural minimum.

---

## 5. Combined Formula and Feasibility

### 5.1 Feasibility Condition

A valid design requires both constraints to be simultaneously satisfiable:

$$n_\text{min} \leq n_\text{max}$$

$$\left\lceil \frac{t \cdot \theta}{w} \right\rceil \leq \left\lfloor \frac{R_\text{out} \cdot \theta}{w + m} \right\rfloor$$

Dropping the ceiling and floor operators to obtain the continuous inequality:

$$\frac{t}{w} \leq \frac{R_\text{out}}{w + m}$$

Cross-multiplying (all quantities positive):

$$t(w + m) \leq R_\text{out} \cdot w$$

$$tw + tm \leq R_\text{out} \cdot w$$

$$tm \leq w(R_\text{out} - t) = w \cdot R_\text{in}$$

Solving for the minimum feasible kerf width:

$$\boxed{w_\text{min} = \frac{t \cdot m}{R_\text{in}}}$$

**Interpretation:** For a given strip thickness and inside radius, there exists a minimum blade kerf width below which no integer $n$ can simultaneously satisfy both the geometric closing condition and the Hayward web floor. A blade narrower than $w_\text{min}$ produces a design where cuts sufficient to close the arc would leave webs thinner than 1.6 mm.

### 5.2 Equivalence of Infeasibility Conditions

The conditions "$w < w_\text{min}$" and "$n_\text{min} > n_\text{max}$" are algebraically identical. Proof:

$$w < w_\text{min} = \frac{tm}{R_\text{in}} \implies tm > w \cdot R_\text{in}$$

$$n_\text{min} > n_\text{max} \implies \frac{t\theta}{w} > \frac{R_\text{out}\theta}{w+m} \implies \frac{t}{w} > \frac{R_\text{out}}{w+m} \implies t(w+m) > R_\text{out} \cdot w \implies tm > w(R_\text{out}-t) = w \cdot R_\text{in}$$

Both reduce to $tm > w \cdot R_\text{in}$. Checking $w \geq w_\text{min}$ is sufficient. $\square$

### 5.3 Optimal Cut Count

Given a feasible design ($w \geq w_\text{min}$), the optimal choice is:

$$n = n_\text{min}$$

This is minimal because:
- Fewer cuts → wider web $b = s - w$ → more uncut material per unit length → stronger joint
- More cuts ($n > n_\text{min}$) produces narrower webs and reduces net cross-section
- Any $n$ in the range $[n_\text{min}, n_\text{max}]$ is geometrically valid; $n_\text{min}$ maximizes structural integrity

### 5.4 Complete Modified Blocklayer–Hayward Formula

Given strip thickness $t$, outside radius $R_\text{out}$, sweep angle $\theta$ (radians), blade kerf $w$, and Hayward minimum web $m = 1.6$ mm:

**Step 1 — Feasibility check:**
$$w_\text{min} = \frac{t \cdot m}{R_\text{out} - t}$$
If $w < w_\text{min}$: no valid solution exists. Use a wider blade or increase $R_\text{out}$.

**Step 2 — Constraint bounds:**
$$n_\text{min} = \left\lceil \frac{t \cdot \theta}{w} \right\rceil \qquad n_\text{max} = \left\lfloor \frac{R_\text{out} \cdot \theta}{w + m} \right\rfloor$$

**Step 3 — Optimal cut count:**
$$n = n_\text{min}$$

**Step 4 — Spacing and web:**
$$s = \frac{R_\text{out} \cdot \theta}{n} \qquad b = s - w$$

Verify $b \geq m$ (guaranteed by construction when $n \leq n_\text{max}$).

---

## 6. The Geometric Identity

### 6.1 Statement

At the exact (non-integer) solution $n_\text{exact} = t\theta/w$, the product of cut count and web width equals the inner arc length:

$$n_\text{exact} \cdot b_\text{exact} = R_\text{in} \cdot \theta$$

### 6.2 Proof

At $n_\text{exact}$:

$$s_\text{exact} = \frac{R_\text{out} \cdot \theta}{n_\text{exact}} = \frac{R_\text{out} \cdot \theta \cdot w}{t \cdot \theta} = \frac{R_\text{out} \cdot w}{t}$$

$$b_\text{exact} = s_\text{exact} - w = \frac{R_\text{out} \cdot w}{t} - w = w\left(\frac{R_\text{out}}{t} - 1\right) = \frac{w(R_\text{out} - t)}{t} = \frac{w \cdot R_\text{in}}{t}$$

Therefore:

$$n_\text{exact} \cdot b_\text{exact} = \frac{t\theta}{w} \cdot \frac{w R_\text{in}}{t} = R_\text{in} \cdot \theta \qquad \square$$

### 6.3 Interpretation

The total length of all webs equals the inner arc length of the curve. This is not a coincidence — it expresses the conservation of arc: the outer arc is partitioned into $n$ kerfs (each of width $w$) and $n$ webs (each of width $b$), and:

$$n \cdot w + n \cdot b = n(w + b) = n \cdot s = R_\text{out} \cdot \theta = L_\text{out}$$

Subtracting the kerf contribution:

$$n \cdot b = L_\text{out} - n \cdot w = R_\text{out} \cdot \theta - t \cdot \theta = R_\text{in} \cdot \theta = L_\text{in}$$

**The webs collectively reconstruct the inner arc.** Kerf bending is geometrically equivalent to replacing the inner face with $n$ discrete arc segments of total length $L_\text{in}$.

At the ceiling integer $n = n_\text{min} \geq n_\text{exact}$, the web is slightly larger than the exact solution (conservative):

$$b = \frac{R_\text{out} \cdot \theta}{n_\text{min}} - w > b_\text{exact} \geq m$$

---

## 7. Material Stress Analysis (MOE Integration)

### 7.1 Motivation

The Blocklayer–Hayward formula is independent of wood species: it depends only on geometry and the empirical Hayward floor. However, the Young's modulus $E_C$ (cross-grain) governs how much bending stress is imposed on the web root when the kerf closes. Stiffer species produce higher stress at the same geometry.

### 7.2 Web Bending Model

Each web acts as a short beam clamped at its base (the uncut strip face) and loaded by the closing of the adjacent kerf slot. At the web root, the outer fiber is in tension and the inner fiber in compression.

For a rectangular beam bent to radius $R$, the bending stress at the outer fiber (distance $y = m/2$ from the neutral axis, where $m$ is the web depth) is:

$$\sigma = \frac{E_C \cdot y}{R} = \frac{E_C \cdot (m/2)}{R_\text{in}}$$

The denominator uses $R_\text{in}$ because the web bends on the inner side of the strip. This gives:

$$\boxed{\sigma = \frac{E_C \cdot m}{2 \cdot R_\text{in}}}$$

**Note on web dimension:** The quantity $m$ in this formula is the **web depth** — the remaining thickness at the bottom of the kerf slot (Hayward's 1.6 mm floor). This is not the web *width* $b = s - w$, which is the horizontal separation between cuts. The web width can be tens of millimeters; the web depth is the thin hinge at the kerf bottom.

### 7.3 Safe Stress Condition

The web must remain in the elastic range. The failure criterion:

$$\sigma \leq \text{MOR}_C \cdot \phi$$

where $\phi = 0.50$ is the safety factor for wood (accounting for natural variability, moisture content variation, and load duration effects per NDS). Substituting:

$$\frac{E_C \cdot m}{2 R_\text{in}} \leq \text{MOR}_C \cdot \phi$$

Solving for the minimum safe inner radius at a given web depth:

$$\boxed{R_\text{in,min} = \frac{E_C \cdot m}{2 \cdot \text{MOR}_C \cdot \phi}}$$

And the maximum safe web depth at a given radius:

$$\boxed{m_\text{safe} = \frac{2 \cdot R_\text{in} \cdot \text{MOR}_C \cdot \phi}{E_C}}$$

### 7.4 Calibration to Hayward's Empirical Data

The cross-grain modulus of rupture $\text{MOR}_C$ is distinct from the along-grain value tabulated in the Wood Database. Cross-grain bending involves fiber tension at the web root and is measured in a different test orientation.

For Sitka spruce — the most common kerfing stock and Hayward's implied reference species — back-calculating from Hayward's empirical minimum:

$$\text{MOR}_{C,\text{Sitka}} = \frac{E_C \cdot m}{2 \cdot R_\text{in} \cdot \phi} = \frac{0.85 \times 10^3 \text{ MPa} \times 1.6 \text{ mm}}{2 \times 106 \text{ mm} \times 0.50} = 12.83 \text{ MPa}$$

(using $R_\text{in} = 109 - 3 = 106$ mm for 3 mm binding at 109 mm outside radius, the OM upper C-bout reference case). This calibrates to $\text{MOR}_{C,\text{Sitka}} = 13.0$ MPa, consistent with USDA Forest Products Laboratory values for cross-grain flexural strength of Sitka spruce.

### 7.5 Species Stiffness Groups

Species are classified by cross-grain stiffness $E_C$ into three groups:

| Group | $E_C$ range | Examples | Implication |
|-------|------------|---------|-------------|
| Flexible | $E_C < 0.55$ GPa | Basswood, Yellow Poplar | Forgiving — any standard radius |
| Standard | $0.55 \leq E_C \leq 0.90$ GPa | All spruce, cedar, mahogany | Standard guitar kerfing |
| Stiff | $E_C > 0.90$ GPa | Maple, Indian Rosewood | Tight radii may require steam pre-treatment |

For stiff species, the material stress check at the Hayward floor provides a second, independent check on the design. The stiffness groups are informational — the Blocklayer–Hayward formula is identical for all species; only the supplementary stress check is species-dependent.

---

## 8. Kerfed Lining vs. Binding: Two Applications, One Formula

The same geometric formula underlies two distinct guitar construction applications, with different governing constraints.

### 8.1 Kerfed Lining (Internal Structure)

Kerfed lining is the flexible wood strip glued inside the sides to provide a glue surface for the top and back plates. The lining only needs to **flex** enough to conform to the body curve; the kerfs need not close completely.

For this application, the governing constraint is the **geometric flex limit**:

$$R_\text{geom} = \frac{b \cdot s}{w}$$

where $b$ is the web thickness ($= 0.30 \times$ stock height for the 70% kerf depth rule), $s$ is the kerf spacing, and $w$ is the kerf width. This is the radius at which the kerf slot just closes — the maximum achievable curvature. For standard guitar lining dimensions (10 mm stock, 4 mm spacing, 1.5 mm bandsaw kerf), $R_\text{geom} = 8$ mm, far below any guitar body radius.

**The Blocklayer arc-difference formula does not govern kerfed lining** because the kerfs do not need to close completely; the lining only needs to flex.

### 8.2 Binding and Panel Bending

For bending a **solid binding strip** or panel where the outside face must remain continuous and the kerfs must close completely when bent to the target radius, the Blocklayer geometric constraint is active and the full Modified Blocklayer–Hayward formula applies.

The distinction is:
- **Lining:** flex only → geometric flex limit governs → $R_\text{geom}$ formula
- **Binding/panel:** full closure → arc difference governs → Blocklayer–Hayward formula

---

## 9. Derivation Summary Table

| Quantity | Formula | Source |
|---------|---------|--------|
| Arc difference | $\Delta L = t \cdot \theta$ | Euclidean geometry |
| Minimum cuts (Blocklayer) | $n_\text{min} = \lceil t\theta / w \rceil$ | $\Delta L = n \cdot w$ |
| Maximum cuts (Hayward) | $n_\text{max} = \lfloor R_\text{out}\theta / (w+m) \rfloor$ | $b \geq m \Rightarrow n \leq R_\text{out}\theta/(w+m)$ |
| Minimum feasible kerf | $w_\text{min} = tm / R_\text{in}$ | $n_\text{min} \leq n_\text{max}$ |
| Optimal cut count | $n = n_\text{min}$ | Maximizes web width |
| Spacing | $s = R_\text{out}\theta / n$ | Even distribution |
| Web width | $b = s - w$ | Definition |
| Geometric identity | $n_\text{exact} \cdot b_\text{exact} = R_\text{in} \cdot \theta$ | Algebra (§6.2) |
| Web bending stress | $\sigma = E_C \cdot m / (2R_\text{in})$ | Euler-Bernoulli beam theory |
| Min safe radius (MOE) | $R_\text{in,min} = E_C \cdot m / (2 \cdot \text{MOR}_C \cdot \phi)$ | $\sigma \leq \text{MOR}_C \cdot \phi$ |
| Lining flex limit | $R_\text{geom} = b_\text{lining} \cdot s / w$ | Geometric slot-closing |

---

## 10. Worked Example: Maple Binding, OM Guitar

**Problem:** Specify kerf cuts to bend a 3 mm maple binding strip around the upper C-bout of an OM guitar. Outside radius $R_\text{out} = 109$ mm, sweep $= 90°$, bandsaw kerf $w = 1.5$ mm.

**Parameters:**

$$t = 3 \text{ mm}, \quad R_\text{out} = 109 \text{ mm}, \quad R_\text{in} = 106 \text{ mm}$$
$$\theta = 90° \times \frac{\pi}{180} = \frac{\pi}{2} \approx 1.5708 \text{ rad}, \quad w = 1.5 \text{ mm}, \quad m = 1.6 \text{ mm}$$

**Step 1 — Feasibility:**

$$w_\text{min} = \frac{3 \times 1.6}{106} = \frac{4.8}{106} = 0.0453 \text{ mm}$$

Since $w = 1.5 \text{ mm} \gg 0.0453 \text{ mm}$: feasible. $\checkmark$

**Step 2 — Constraint bounds:**

$$n_\text{min} = \left\lceil \frac{3 \times \pi/2}{1.5} \right\rceil = \left\lceil \frac{4.712}{1.5} \right\rceil = \lceil 3.14 \rceil = 4$$

$$n_\text{max} = \left\lfloor \frac{109 \times \pi/2}{1.5 + 1.6} \right\rfloor = \left\lfloor \frac{171.2}{3.1} \right\rfloor = \lfloor 55.2 \rfloor = 55$$

Constraint window: $n \in [4, 55]$. Wide window — ample headroom.

**Step 3 — Optimal cuts:**

$$n = n_\text{min} = 4$$

**Step 4 — Spacing and web:**

$$s = \frac{109 \times \pi/2}{4} = \frac{171.2}{4} = 42.80 \text{ mm}$$

$$b = 42.80 - 1.5 = 41.30 \text{ mm} \gg 1.6 \text{ mm} \checkmark$$

**Step 5 — Geometric identity check:**

$$n_\text{exact} \cdot b_\text{exact} = 3.14 \times \frac{1.5 \times 106}{3} = 3.14 \times 53.0 = 166.4 \text{ mm}$$

$$R_\text{in} \cdot \theta = 106 \times \frac{\pi}{2} = 166.5 \text{ mm} \checkmark$$

**Step 6 — Material stress check (maple):**

$$E_C = 1.10 \text{ GPa}, \quad \text{MOR}_C = 38.0 \text{ MPa}, \quad \phi = 0.50$$

$$\sigma = \frac{1100 \times 1.6}{2 \times 106} = \frac{1760}{212} = 8.30 \text{ MPa}$$

$$\text{Allowable} = 38.0 \times 0.50 = 19.0 \text{ MPa}$$

$$\sigma = 8.30 \leq 19.0 \text{ MPa} \checkmark \quad \text{(margin: } 10.7 \text{ MPa)}$$

**Result:** 4 cuts at 42.8 mm center spacing. Cuts placed at 10.7, 53.5, 96.3, 139.1 mm from the start of the bend (half-spacing from each end for symmetric distribution).

---

## 11. Boundary Cases and Limits

### 11.1 As $R \to \infty$ (Flat Panel)

$$w_\text{min} = \frac{tm}{R_\text{in}} \to 0$$

Any blade width is feasible for a flat panel. This is consistent — flat panels can be bent to any radius with enough cuts, regardless of blade width.

### 11.2 As $R_\text{in} \to t$ (Extreme Tight Radius)

$$w_\text{min} = \frac{tm}{t} = m = 1.6 \text{ mm}$$

At the minimum possible inside radius (zero inside radius, $R_\text{out} = t$), the minimum blade width equals the Hayward web thickness. The kerf must be at least as wide as the web it leaves — a physically sensible lower bound.

### 11.3 As $t \to 0$ (Infinitely Thin Strip)

$$n_\text{min} = \left\lceil \frac{t\theta}{w} \right\rceil \to 1 \quad (\text{or } 0)$$

An infinitely thin strip requires no material removal — it can wrap around any radius with zero cuts. Consistent with the limit of the formula.

### 11.4 Single Exact Solution ($w = w_\text{min}$)

When $w$ equals exactly $w_\text{min}$, the two constraints converge: $n_\text{min} = n_\text{max}$. There is exactly one valid integer (the continuous solution is an integer at this point). This is the minimum-kerf-width design point — the solution that simultaneously uses the narrowest blade and provides the fewest cuts.

---

## 12. Sources and Calibration Basis

| Quantity | Value | Source |
|---------|-------|--------|
| Hayward minimum web $m$ | 1.6 mm (1/16 in) | Hayward, *The Woodworker* (1939–1967), reprinted Lost Art Press 2023 |
| Blocklayer formula | $n = \lceil t\theta/w \rceil$ | Blocklayer.com `KerfEng_V18.js`; independently confirmed by KERF_BENDING.pdf |
| Safety factor $\phi$ | 0.50 | NDS (National Design Specification for Wood Construction); USDA Wood Handbook |
| $\text{MOR}_{C,\text{Sitka}}$ | 13.0 MPa | Calibrated to Hayward's empirical floor; consistent with USDA FPL data |
| $E_C$ values | Species-dependent | USDA Forest Products Laboratory *Wood Handbook* (2021); Wood Database (Eric Meier) |
| Geometric identity | $n \cdot b = R_\text{in}\theta$ | Derived in §6.2 (original to this document) |
| 70% kerf depth rule | $d = 0.70 \times h$ | Gore & Gilet, *Contemporary Acoustic Guitar Design and Build*; Capone & Lanzara (2019) |

---

*Document maintained as part of The Production Shop lutherie ERP platform.*  
*Mathematical notation uses standard engineering conventions; angles are in radians unless stated otherwise.*
