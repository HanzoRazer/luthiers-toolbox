# The Reverse Engineering of the Martin D-28 #65260

> **STATUS.** The **Corrected Rerun 002 (Arnold side-height authority)** section
> immediately below is the current result. The original first run is
> **SUPERSEDED**: it used `4.4375 in` as the waist *side height* (that value is a
> separate drawing "DEEP" / assembled-depth annotation, comparison-only) and
> assumed a waist station of `10.5 in`. Rerun 002 uses the Arnold side height
> `4.220 in` applied at the **geometrically derived** waist station. The first
> run is retained verbatim further down as historical evidence. No production,
> spec, or authority file is modified by either run.

<!-- RERUN002_START -->
## Corrected Rerun 002 — Arnold Side Height Authority

- Repository SHA tested: `c77fec5e834cbad6fc239767455a2ad201cc419b`
- Convergence log: `docs/experiments/results/D28_65260_SIDE_INVERSE_RERUN_002_CONVERGENCE.csv`
- Summary: `docs/experiments/results/D28_65260_SIDE_INVERSE_RERUN_002_SUMMARY.csv`

### Experimental authority rule (read first)

Only the declared inputs govern the solve. The hard waist constraint is the
John Arnold **side height 4.22 in**; the drawing annotation
**4.4375 in DEEP** is a separate assembled-depth measurement used for
comparison only and is never used as side height. The waist station is derived
from the outline geometry, not assumed. Repo values are read only for mapping,
provenance, comparison, validation, and inconsistency detection. No production,
spec, or authority file is modified.

### Active experimental inputs

```text
ACTIVE EXPERIMENTAL INPUTS (Rerun 002 — Arnold side-height authority)
  waist_side_height_in   = 4.22  (HARD constraint)
  waist_station          = GEOMETRICALLY DERIVED (not 10.5)
  drawing_DEEP_in        = 4.4375  (COMPARISON ONLY — not side height)
  S_shoulder_in @0.0     = 3.75
  B_butt_in @30.4375   = 4.72
  M_top_in / N_back_in   = 0.0 / 0.0
  R_bounds_ft            = (8.0, 50.0)
  L_bounds_in            = (12.0, 40.0)
  Arnold side heights (in; developed station -> side height):
         0.0 -> 3.7500
         3.0 -> 3.7400
         6.0 -> 3.8950
         9.0 -> 4.0850
        12.0 -> 4.2400
        15.0 -> 4.3500
        18.0 -> 4.4550
        21.0 -> 4.5650
        24.0 -> 4.6400
        27.0 -> 4.6700
     30.4375 -> 4.7200
    WAIST    -> 4.2200  (@derived station)
  mapping geometry (repo, mapping-only, NOT a solve input):
    lower_bout_width_in = 15.625
    upper_bout_width_in = 11.5
    waist_width_in = 11.0
    waist_y_norm = 0.44
    outline_authority = BodyContourSolver two-arc outline (parametric)
    station_mapping = absolute developed arc length from neck
```

### Geometric waist derivation

- Geometric waist point (@ nominal L = 20 in): (x = 5.500 in, y = 8.800 in from tail).
- Derived developed neck-to-waist station `s_waist` (@ L = 20 in): **14.298 in**.
- Legacy assumed waist station: 10.5 in.
- Difference (derived − legacy, @ L = 20): **+3.798 in**. The 10.5 in figure was never source-measured; it was inferred from lying between stations 9 and 12.
- Outline half-perimeter (neck→tail) @ L = 20 in: 31.281 in.
- Mapping: each Arnold station maps to the perimeter point at that **absolute**
  developed arc length from the neck; `D` is the Euclidean in-plane distance from
  the spherical high point to the mapped point (never the station).

### A. Corrected waist-constrained nested solve (H_waist = 4.220 in)

| R (in) | R (ft) | L (in) | P (in) | s_waist (in) | val RMSE (in) | max|resid| (in) | admissible | bound |
|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 96.0 | 8.00 | n/a | n/a | n/a | n/a | n/a | n/a | True |
| 132.0 | 11.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 168.0 | 14.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 204.0 | 17.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 240.0 | 20.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 276.0 | 23.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 312.0 | 26.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 348.0 | 29.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 384.0 | 32.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 420.0 | 35.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 456.0 | 38.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 492.0 | 41.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 528.0 | 44.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 564.0 | 47.00 | n/a | n/a | n/a | n/a | n/a | n/a | False |
| 600.0 | 50.00 | n/a | n/a | n/a | n/a | n/a | n/a | True |

- **No admissible root at any R.** The model's minimum achievable waist side height over the (L, R) search box is **4.2978 in** (at L = 12.0 in, R = 50.0 ft), which is above the **4.22 in** target. The 4.220 in constraint at the geometric waist (developed s ≈ 14.3 in) is therefore unsatisfiable — the bracketing grid scan (logged in the convergence CSV) shows the waist residual never changes sign.


### B. Full least-squares cross-check (L, R)

| L0 | R0 | L (in) | R (in/ft) | P (in) | RMSE (in) | admissible | bound | flags |
|---:|---:|---:|---:|---:|---:|:--:|:--:|---|
| 20 | 180 | 19.939 | 600.0/50.00 | -19.182 | 0.0548 | False | True | P<0 (high point beyond tail); bound |
| 18 | 300 | 19.939 | 600.0/50.00 | -19.182 | 0.0548 | False | True | P<0 (high point beyond tail); bound |
| 22 | 120 | 19.939 | 600.0/50.00 | -19.182 | 0.0548 | False | True | P<0 (high point beyond tail); bound |
| 16 | 500 | 19.939 | 600.0/50.00 | -19.182 | 0.0548 | False | True | P<0 (high point beyond tail); bound |
| 30 | 250 | 19.939 | 600.0/50.00 | -19.182 | 0.0548 | False | True | P<0 (high point beyond tail); bound |

### C. Anchor / leave-one-out identifiability

| anchor | L (in) | R (in/ft) | P (in) | RMSE others (in) | admissible |
|---|---:|---:|---:|---:|:--:|
| 3.0 | 12.658 | 96.0/8.00 | -0.990 | 0.0469 | False |
| 6.0 | 12.931 | 96.0/8.00 | -0.699 | 0.0483 | False |
| 9.0 | 20.283 | 552.0/46.00 | -16.222 | 0.0399 | False |
| 12.0 | 20.011 | 576.0/48.00 | -17.878 | 0.0404 | False |
| 15.0 | 22.836 | 600.0/50.00 | -14.040 | 0.0486 | False |
| 18.0 | 19.540 | 480.0/40.00 | -14.023 | 0.0425 | False |
| 21.0 | 19.728 | 600.0/50.00 | -19.598 | 0.0414 | False |
| 24.0 | 20.965 | 600.0/50.00 | -17.243 | 0.0400 | False |
| 27.0 | 23.024 | 504.0/42.00 | -9.697 | 0.0497 | False |
| WAIST | n/a | n/a | n/a | n/a | n/a |

- Recovered L spread: 12.66 .. 23.02 in (range 10.37 in).

### D. First run (superseded) vs Rerun 002

| quantity | first run (superseded) | Rerun 002 |
|---|---|---|
| waist side height | 4.4375 in (DEEP mis-used) | 4.22 in (Arnold side height) |
| waist station | 10.5 in (assumed) | 14.30 in (derived @L=20) |
| recovered L* | 20.29 in | no admissible solution |
| recovered R* | 8.0 ft (bound) | n/a |
| P* | 5.59 in | n/a |
| validation RMSE | 0.1897 in | n/a |
| disposition | UNDERDETERMINED | INSUFFICIENT_GEOMETRY_AUTHORITY |

The first run appeared to 'support 20 in' only because it imposed the wrong
(higher) 4.4375 in value at an assumed 10.5 in station. With the correct 4.220 in
side height at the geometrically derived waist, that apparent support disappears.

### E. Drawing-depth reconciliation (side height vs DEEP)

- Drawing waist DEEP = 4.4375 in; Arnold waist side height = 4.22 in; difference = **0.2175 in** (5.5245 mm).
- The inverse side-height solve is NOT forced to explain this offset. The spec
  side profile excludes top/back thickness (M=N=0), and the repo records no
  #65260 top/back plate thickness that provenance-links to 0.2175 in, so the
  offset is left as an **unresolved datum/measurement-method difference**
  (assembled 'DEEP' depth vs bare side height) — a hypothesis, not a conclusion.

### STOP condition encountered

- Hard waist constraint 4.22 in is unsatisfiable with physically admissible geometry: the model's minimum achievable waist side height over the search box is 4.2978 in > 4.22 in. The geometric waist (developed s=14.30 in from the outline authority) cannot be reconciled with the Arnold 4.220 in reading under the spherical-back model.
- Per the rerun order, this is reported rather than resolved by inventing
  geometry or by treating the developed station as `D`.

### Disposition

**INSUFFICIENT_GEOMETRY_AUTHORITY**

- Analysis A found no admissible root at any R: the model's minimum achievable waist side height (4.2978 in) exceeds the 4.220 in target, so the hard constraint at the geometric waist cannot be met.
- The geometric waist location comes from the parametric outline authority (BodyContourSolver, waist_y_norm=0.44); its developed station (~14.3 in) disagrees with where the 4.220 in reading sits in Arnold's monotonic series (~10.5 in), so the constraint and the outline cannot be reconciled.
- Every unconstrained least-squares solution is physically inadmissible (P<0) and/or radius-bound-pinned, so B offers no admissible cross-check either.

### Inconsistency audit

| field / value | experimental | conflicting repo/source | difference | source | effect | class | disposition |
|---|---|---|---|---|---|---|---|
| waist side height | 4.22 in (Arnold side height) | repo side_profile_raw['10.5']=4.22 in (same number, labelled waist) | 0.000 in (value agrees; label/station differ) | Arnold correspondence vs martin_d28_1937.json | hard constraint value confirmed; applied at derived station not 10.5 | `EXPERIMENTAL_OVERRIDE` | use 4.220 as side height; repo unchanged |
| 4.4375 in DEEP drawing value | comparison-only (assembled depth) | first run used it as side height; Δ vs side height = +0.2175 in | +0.2175 in | Arnold drawing annotation vs Arnold correspondence | excluded from the side-height solve (see reconciliation, section E) | `SOURCE_CONFLICT` | treat 0.2175 in as unresolved datum/method difference (hypothesis only) |
| waist developed station | derived s_waist=14.298 in (@L=20) | legacy assumed 10.5 in | +3.798 in | outline geometry vs first-run assumption | moves the hard-constraint location toward the tail vs the legacy guess | `DERIVATION_MISMATCH` | use geometrically derived station; 10.5 was never source-measured |
| 30.4375 in | developed side-strip span (Arnold bottom-end station) | repo total_length=30.4375 in; outline half-perimeter@L=20=31.28 in | +0.84 in vs half-perimeter | repo dimensions.total_length; derived outline | governs absolute arc-length mapping; 'body length' reading falsified previously | `UNIT_OR_DATUM_AMBIGUITY` | read 30.4375 in as developed side span, not centerline body length |
| Arnold 12-pt profile vs spherical-back model | 12 side-height points | single-radius spherical back | n/a | Arnold correspondence vs Sevy/Doolin model | residual pattern + non-identifiability indicate limited model fit | `UNRESOLVED` | report as-is; do not force the model to match |
| plan-view outline authority | not declared | BodyContourSolver parametric outline; waist_y_norm=0.44 family default | model dependence | body_contour_solver FAMILY_DEFAULTS | derived s_waist and D mapping depend on the parametric outline shape | `UNRESOLVED` | replace with a measured #65260 perimeter if one becomes available |
| martin_d28_1937.py module | n/a | single line; early # comment swallows all code (exports nothing) | code vs data-bearing .json | services/api/app/instrument_geometry/specs/martin_d28_1937.py | none (observations sourced from the rerun order / .json) | `REPO_CONFLICT` | flag for owner; not fixed here |

Classes: `EXPERIMENTAL_OVERRIDE`, `REPO_CONFLICT`, `SOURCE_CONFLICT`, `DERIVATION_MISMATCH`, `UNIT_OR_DATUM_AMBIGUITY`, `UNRESOLVED`.

<!-- RERUN002_END -->

---

# SUPERSEDED — First run (historical evidence)

> Superseded by Corrected Rerun 002 above. Retained verbatim. This first run used
> waist side height = `4.4375 in` and an assumed waist station = `10.5 in`; both
> are corrected in Rerun 002 (`4.220 in` side height at the derived geometric
> waist). Kept only as a record of the earlier (incorrect) conflation.

Isolated inverse-geometry experiment. Evidence gathering only — no production,
authority, or spec change is made or implied by this document.

## Experimental authority rule — read first

Only the values declared in the *Active experimental inputs* block below govern
this solve. They override conflicting values found elsewhere in the repository
for the purpose of this experiment. Repository defaults, production specs, family
defaults, historical estimates, and inferred values are **not** silently
substituted for a declared experimental value. Repository values are read only
for outline mapping/interpretation, provenance, comparison, validation, and
inconsistency detection. If a required governing value were missing, the run
stops and reports it rather than borrowing a repo source. Every discrepancy is
recorded in the Inconsistency Register (section 12); none is auto-resolved. No
production authority is changed by this experiment.

## Active experimental inputs

```text
ACTIVE EXPERIMENTAL INPUTS
  waist_depth_in            = 4.4375  (overrides repo legacy 4.22)
  waist_station_in          = 10.5
  B_butt_depth_in (station 30.4375) = 4.72
  S_shoulder_depth_in (station 0.0) = 3.75
  M_top_thickness_in        = 0.0
  N_back_thickness_in       = 0.0
  R_bounds_ft               = (8.0, 50.0)
  L_bounds_in               = (12.0, 40.0)
  observations (side profile, in; * = experimental override):
    station      0.0 -> 3.7500
    station      3.0 -> 3.7400
    station      6.0 -> 3.8950
    station      9.0 -> 4.0850
    station     10.5 -> 4.4375 *
    station     12.0 -> 4.2400
    station     15.0 -> 4.3500
    station     18.0 -> 4.4550
    station     21.0 -> 4.5650
    station     24.0 -> 4.6400
    station     27.0 -> 4.6700
    station  30.4375 -> 4.7200
  mapping geometry (repo, mapping-only, NOT a solve input):
    lower_bout_width_in = 15.625
    upper_bout_width_in = 11.5
    waist_width_in = 11.0
    waist_y_norm = 0.44
    station_span_in = 30.4375
    outline_authority = BodyContourSolver two-arc outline (parametric)
```

## 1. Provenance

- Repository SHA tested: `3e16383f0d2c0063ac821d2c6b2194dc3948d3d2`
- Branch: `experiment/d28-side-profile-inverse-convergence`
- Equations reused (unmodified): `solve_high_point`, `solve_side_height` in
  `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py`.
- Outline authority: `BodyContourSolver` two-arc plan-view outline, seeded with
  the D-28 spec widths and scaled to the candidate body length. This is a
  parametric reconstruction, not an independently measured perimeter polygon —
  see the identifiability finding.
- Observations: `martin_d28_1937.json` `side_profile_raw` and `dimensions`
  (read-only). Incidental defect noted, not fixed here: the sibling
  `martin_d28_1937.py` is a single physical line whose early `#` comment swallows
  every assignment, so that module exports nothing; the JSON is the usable copy.

## 2. Authoritative waist correction

- Waist side depth used as the hard constraint: **4.4375 in**.
- Repository legacy value at station 10.5 in: `4.22 in` — treated
  as suspect/superseded for this experiment and left unchanged in the spec.

## 3. Units, boundary conditions, mapping

- Units: inches throughout (the Sevy formulas are unit-agnostic).
- Boundary depths from the profile endpoints (raw ⇒ M = N = 0):
  - S (shoulder/neck, station 0.0) = 3.75 in
  - B (butt/tail, station 30.4375) = 4.72 in  ⇒  E = B − S = 0.970 in
- Equations:
  - `P = (L/2) − (E/2)·sqrt(4R²/(L²+E²) − 1)`
  - `H = (B + (R − sqrt(R²−P²))) − (R − sqrt(R²−D²)) − (M+N)`
- **Station-to-perimeter mapping:** each developed station `s` maps to the point
  at normalised arc-length fraction `s / 30.4375` along the neck→tail half of the
  L-scaled outline. `D` is the Euclidean distance from the high point (0, P) to
  that perimeter point. **`D` is never set equal to the station.**
- Validation stations (out-of-sample): [3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0]

## 4. Analysis A — waist-constrained nested solve (waist = 4.4375 in)

For each candidate R, L is solved so the model reproduces the waist depth exactly;
the remaining non-waist, non-endpoint points are pure validation.

| R (in) | R (ft) | solved L (in) | P (in) | val RMSE (in) | val max|resid| (in) |
|---:|---:|---:|---:|---:|---:|
| 96.0 | 8.00 | 20.294 | 5.589 | 0.1897 | 0.3039 |
| 130.2 | 10.85 | 22.529 | 5.686 | 0.1929 | 0.2952 |
| 164.3 | 13.69 | 24.565 | 5.816 | 0.1976 | 0.2952 |
| 198.5 | 16.54 | 26.450 | 5.966 | 0.2016 | 0.2972 |
| 232.7 | 19.39 | 28.216 | 6.128 | 0.2048 | 0.2981 |
| 266.8 | 22.24 | 29.884 | 6.299 | 0.2074 | 0.2985 |
| 301.0 | 25.08 | 31.471 | 6.475 | 0.2095 | 0.2987 |
| 335.2 | 27.93 | 32.987 | 6.654 | 0.2113 | 0.2987 |
| 369.4 | 30.78 | 34.443 | 6.835 | 0.2128 | 0.2985 |
| 403.5 | 33.63 | 35.844 | 7.017 | 0.2137 | 0.2959 |
| 437.7 | 36.47 | 37.198 | 7.199 | 0.2145 | 0.2936 |
| 471.9 | 39.32 | 38.508 | 7.382 | 0.2153 | 0.2917 |
| 506.0 | 42.17 | 39.779 | 7.564 | 0.2159 | 0.2901 |
| 540.2 | 45.02 | n/a | n/a | n/a | n/a |
| 574.4 | 47.86 | n/a | n/a | n/a | n/a |

- Coarse best: R* = 96.00 in (8.00 ft), L* = 20.294 in, P* = 5.589 in, validation RMSE = 0.1897 in.
- Local refinement (independent of the grid): R* = 96.52 in, L* = 20.329 in, RMSE = 0.1897 in.

### Residuals at the best Analysis-A solution

| station (in) | measured H (in) | predicted H (in) | residual (in) | D (in) |
|---:|---:|---:|---:|---:|
| 0.0 (S bc) | 3.7500 | 3.7500 | +0.0000 | 14.705 |
| 3.0 | 3.7400 | 3.8975 | +0.1575 | 13.719 |
| 6.0 | 3.8950 | 4.0989 | +0.2039 | 12.244 |
| 9.0 | 4.0850 | 4.3252 | +0.2402 | 10.333 |
| 10.5 (waist*) | 4.4375 | 4.4375 | -0.0000 | 9.236 |
| 12.0 | 4.2400 | 4.5439 | +0.3039 | 8.060 |
| 15.0 | 4.3500 | 4.6307 | +0.2807 | 6.953 |
| 18.0 | 4.4550 | 4.5448 | +0.0898 | 8.049 |
| 21.0 | 4.5650 | 4.5062 | -0.0588 | 8.496 |
| 24.0 | 4.6400 | 4.5279 | -0.1121 | 8.248 |
| 27.0 | 4.6700 | 4.6026 | -0.0674 | 7.330 |
| 30.4375 (B bc) | 4.7200 | 4.7200 | +0.0000 | 5.589 |

`(S bc)`/`(B bc)` fix the boundary depths; `(waist*)` is the hard constraint at the authoritative 4.4375 in.

## 5. Analysis B — independent full least squares in (L, R)

| L0 | R0 | fitted L (in) | fitted R (in / ft) | P (in) | RMSE (in) | success |
|---:|---:|---:|---:|---:|---:|:--:|
| 20 | 180 | 15.929 | 152.5 / 12.71 | -1.294 | 0.0811 | True |
| 18 | 300 | 15.929 | 152.5 / 12.71 | -1.294 | 0.0811 | True |
| 22 | 120 | 15.929 | 152.5 / 12.71 | -1.294 | 0.0811 | True |
| 16 | 500 | 15.929 | 152.5 / 12.71 | -1.294 | 0.0811 | True |
| 30 | 250 | 15.929 | 152.5 / 12.71 | -1.294 | 0.0811 | True |

## 6. Analysis C — leave-one-out anchor test

Each row uses a different profile point as the exact anchor (in place of the
waist) and re-solves; clustered `(L, R)` would indicate identifiability.

| anchor station (in) | recovered L (in) | recovered R (in / ft) | RMSE others (in) |
|---:|---:|---:|---:|
| 3.0 | 12.737 | 121.6 / 10.14 | 0.0977 |
| 6.0 | 14.479 | 138.7 / 11.56 | 0.0879 |
| 9.0 | 14.503 | 138.7 / 11.56 | 0.0878 |
| 12.0 | n/a | n/a | n/a |
| 15.0 | 13.456 | 121.6 / 10.14 | 0.0929 |
| 18.0 | 16.831 | 181.4 / 15.12 | 0.0863 |
| 21.0 | 18.070 | 258.3 / 21.53 | 0.0894 |
| 24.0 | 24.737 | 275.4 / 22.95 | 0.1246 |
| 27.0 | 16.061 | 121.6 / 10.14 | 0.0893 |
| 10.5 | 20.294 | 96.0 / 8.00 | 0.1897 |

- Recovered L spread: 12.74 .. 24.74 in (range 12.00 in).
- Recovered R spread: 8.00 .. 22.95 ft.

## 7. Half-perimeter test for 30.4375 in

- Developed neck→tail half-perimeter of the outline at L = 20 in: 31.281 in.
- Developed neck→tail half-perimeter at the recovered L* = 20.29 in: 31.499 in.
- Recorded side-profile span (station max): 30.4375 in.
- Interpretation: whether 30.4375 in reads as developed side-strip / half-perimeter
  length rather than centerline body length is judged by how close the outline's
  half-perimeter is to 30.4375 in versus how close the body length is to 20 in.
- Verdict: the developed neck→tail half-perimeter at the historical L = 20 in is
  31.28 in, within 0.84 in (2.8%) of 30.4375 in.
  This is consistent with 30.4375 in being a developed side-strip / half-perimeter
  length, not centerline body length.

## 8. Model C — falsification of `30.4375 in == body length`

- Fixing L = 30.4375 in and fitting R alone: R = 600.0 in (50.00 ft), P = -3.89 in, RMSE = 0.1039 in, on bound.
- Verdict: treating 30.4375 in as centerline body length is not physically admissible — the fit lands on the radius bound and/or drives the high point outside the body (P < 0).

## 9. Sensitivity / identifiability

- ±0.01 in perturbation of every measured height (Analysis A):
  - recovered L: 20.08 .. 20.50 in
  - recovered R: 96.0 .. 96.0 in (8.00 .. 8.00 ft)
  - recovered P: 5.43 .. 5.74 in

## 10. Waist-value comparison — authoritative 4.4375 vs legacy 4.220

| waist H (in) | R* (in / ft) | L* (in) | P* (in) | validation RMSE (in) |
|---:|---:|---:|---:|---:|
| 4.4375 (authoritative) | 96.0 / 8.00 | 20.294 | 5.589 | 0.1897 |
| 4.220 (legacy repo) | 155.8 / 12.98 | 16.320 | -1.071 | 0.0456 |

- ΔL* (authoritative − legacy) = +3.974 in; ΔR* = -59.8 in.

## 11. Disposition

**UNDERDETERMINED**

- Leave-one-out anchors do NOT cluster: (L, R) depends on which point is treated as exact -> not separately identifiable.
- Analysis A's minimum sits on the R bound (8.0 ft); validation RMSE is monotonic in R, so A has no interior optimum.
- The unconstrained least-squares solution places the spherical high point outside the body (P = -1.29 in < 0) — physically inadmissible, a further sign the data do not pin the geometry.
- Waist correction is decisive for the recovered length: 4.4375 in gives L* = 20.29 in (P* = +5.59 in), while the legacy 4.220 in gives L* = 16.32 in (P* = -1.07 in). The corrected value moves the recovered length toward the historical 20 in.
- Supporting the developed-length reading: the outline half-perimeter at L = 20 in (31.28 in) is close to 30.4375 in, whereas treating 30.4375 in as body length is physically inadmissible (Model C).

## 12. Inconsistency audit

Discrepancies between experimental, repository-production, derived, and
source/context values. None is resolved, normalised, or overwritten here.

| field / value | experimental | conflicting repo/source | difference | source / location | effect on solve | class | recommended disposition |
|---|---|---|---|---|---|---|---|
| waist side depth @ station 10.5 | 4.4375 in | 4.22 in | +0.2175 in | martin_d28_1937.json side_profile_raw['10.5'] (and .py) | moves recovered L* by +3.97 in and flips P* sign (legacy P*<0, authoritative P*>0) | `EXPERIMENTAL_OVERRIDE` | keep experimental value; verify against Arnold drawing; leave repo unchanged |
| martin_d28_1937.py module | n/a | exports nothing (single line; early # comment swallows all code) | code vs data-bearing .json | services/api/app/instrument_geometry/specs/martin_d28_1937.py | none on this solve (observations sourced from the .json) | `REPO_CONFLICT` | flag for owner; the .py spec is non-functional and should be repaired separately |
| body length L | not an input (recovered) | repo body_length 20.0 in | A: 20.29 in; B: 15.93 in | repo dimensions.body_length vs derived | recovered L disagrees across methods -> not separately identifiable | `DERIVATION_MISMATCH` | do not adjust repo; L underdetermined by these data |
| 30.4375 in (station span / total_length) | developed side-strip span (station max) | repo total_length 30.4375 in; outline half-perimeter @L=20 = 31.28 in | +0.84 in vs half-perimeter | repo dimensions.total_length; derived outline | governs station->perimeter mapping; 'body length' reading falsified by Model C | `UNIT_OR_DATUM_AMBIGUITY` | read 30.4375 in as developed side-strip / half-perimeter length |
| waist depth vs neighbouring raw stations | 4.4375 in @10.5 | raw 9.0->4.085, 12.0->4.24 (monotone-increasing profile) | waist exceeds station 12.0 by +0.1975 in | martin_d28_1937.json side_profile_raw | creates a local bulge the smooth spherical model cannot match (systematic flanking residuals up to ~0.30 in) | `SOURCE_CONFLICT` | verify Arnold waist reading; UNRESOLVED pending source |
| waist_y_norm (perimeter waist position) | not declared | 0.44 (BodyContourSolver dreadnought family default) | family default used for mapping | body_contour_solver FAMILY_DEFAULTS | sets where the waist sits along the perimeter -> affects D mapping | `UNRESOLVED` | replace with a measured #65260 waist position if an authoritative outline is obtained |

Classes: `EXPERIMENTAL_OVERRIDE`, `REPO_CONFLICT`, `SOURCE_CONFLICT`, `DERIVATION_MISMATCH`, `UNIT_OR_DATUM_AMBIGUITY`, `UNRESOLVED`.

## 13. Interpretation rule

This experiment is evidence only. Even a convergence near 20 in would not license
editing `martin_d28_1937.*`; any production or authority change requires a separate
owner-reviewed order.
