# The Reverse Engineering of the Martin D-28 #65260

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
