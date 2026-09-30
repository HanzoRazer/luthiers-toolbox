# DEV ORDER — D28-SIDE-INVERSE-CONVERGENCE-001

**Status:** EXPERIMENT ONLY — no production behavior changes  
**Repo:** HanzoRazer/luthiers-toolbox  
**Branch:** `experiment/d28-side-profile-inverse-convergence`  
**Purpose:** Test whether the Sevy/Doolin spherical-back side-height equations can be inverted numerically against the measured 1937 Martin D-28 #65260 side profile and converge to a physically coherent geometry.

## Why this experiment exists

The repository contains two facts that appear contradictory only if their coordinate meanings are conflated:

- `BODY_LENGTH = 20.0 in`
- side-profile stations run from `0.0` to `30.4375 in`

The source code itself labels the side-profile axis as **distance from neck -> side depth**. The working hypothesis for this experiment is that `30.4375 in` is the developed half-perimeter / side-strip station from neck block to tail, not centerline body length.

Do not rewrite or "correct" either datum before testing that hypothesis.

## Canonical repository inputs

Read, do not modify:

- `services/api/app/instrument_geometry/specs/martin_d28_1937.py`
- `services/api/app/instrument_geometry/specs/martin_d28_1937.json`
- `services/api/app/instrument_geometry/body/ibg/body_contour_solver.py`
- `AGENTS.md`
- `CLAUDE.md`

Measured/source-derived D-28 #65260 values currently recorded:

```text
body_length = 20.0 in
upper_bout = 11.5 in
lower_bout = 15.625 in
waist = 11.0 in

raw side profile, station from neck -> tail:
0.0000   3.750
3.0000   3.740
6.0000   3.895
9.0000   4.085
10.5000  4.220
12.0000  4.240
15.0000  4.350
18.0000  4.455
21.0000  4.565
24.0000  4.640
27.0000  4.670
30.4375  4.720
```

Treat `side_profile_raw` as the primary observed data. It explicitly excludes top/back thickness and kerfing.

## Source equations already implemented in repo

### High-point location

```text
E = B - S

P = (L/2) - (E/2) * sqrt((4 R^2)/(L^2 + E^2) - 1)
```

Repository function:

`solve_high_point(L, B, S, R)`

### Side height

```text
H = (B + (R - sqrt(R^2 - P^2)))
    - (R - sqrt(R^2 - D^2))
    - (M + N)
```

Repository function:

`solve_side_height(B, R, P, D, M, N)`

For the RAW side-profile fit, start with `M=N=0` unless evidence in the source file requires a different interpretation.

## Central geometry issue

Doolin's method does **not** use side-strip station directly as `D`.

For each perimeter point, `D` is the in-plane Euclidean distance from the spherical-back high point to that point on the guitar outline.

Therefore the experiment must first map each measured side-strip station `s_i` to a perimeter point `(x_i, y_i)`.

Do not set `D_i = s_i`.

## Experiment objective

Determine whether an inverse solver can recover a stable, physically coherent solution from the recorded side-profile data.

### Model A — fixed historical body length

Fix:

`L = 20.0 in`

Fit at minimum:

- back radius `R`
- high-point location is then derived by the Sevy formula

Use the best available D-28 outline authority already in the repository to map the 0..30.4375 in side-strip stations to perimeter coordinates.

Report:
- fitted `R`
- derived `P`
- predicted height at every measured station
- residual at every station
- RMSE / max absolute residual
- whether the solution is stable across starting guesses

### Model B — inverse body-length check

Allow `L` and `R` to vary.

The outline must scale coherently with candidate `L`; do not independently distort bout widths unless the experiment explicitly declares another model.

Objective:

```text
minimize sum_i (H_predicted_i(L,R) - H_measured_i)^2
```

Report whether the optimizer converges near the repository's 20.0 in body length without being forced there.

This is a validation experiment, not permission to replace `BODY_LENGTH`.

### Model C — falsification of the conflation

Explicitly test the bad interpretation:

`30.4375 in == centerline body length`

Show quantitatively whether that interpretation can or cannot fit the measured side heights with a physically plausible spherical radius and outline.

The purpose is to distinguish:
- body length
- developed side-strip / half-perimeter length

rather than relying on naming alone.

## Solver requirements

Use at least two numerical approaches if practical:
- bounded least squares
- coarse grid + local refinement, or another independent method

Use multiple initial guesses.

Suggested broad bounds only:
- `L: 18..22 in` for Model B
- `R: 8..50 ft`

Do not silently narrow the bounds to force a historical-looking result.

## Sensitivity / identifiability

Run a small perturbation study:
- perturb each measured side height by approximately +/-0.01 in, or use an equivalent deterministic sensitivity sweep
- report how much fitted `L`, `R`, and `P` move

If `L` and `R` are strongly correlated or not separately identifiable from these data, say so explicitly.

A non-identifiable result is a valid outcome.

## Acceptance / convergence criteria

A result may be called **converged** only if:

1. multiple initial guesses reach the same basin;
2. at least two numerical approaches agree materially;
3. residuals show no obvious systematic trend that invalidates the spherical-back assumption;
4. fitted parameters remain inside declared bounds without landing on a bound merely because of constraint pressure;
5. the result is reasonably stable under the stated measurement perturbation.

Do **not** define success as "returns 20 inches."

## STOP conditions

Stop and report, rather than inventing geometry, if:

- no authoritative D-28 outline capable of mapping side-strip station to perimeter coordinates can be found;
- the side-profile station direction/origin cannot be reconciled with the outline;
- the available data do not identify `L` and `R` separately;
- convergence requires treating side-strip station as `D`;
- a physically plausible fit requires changing source measurements.

## Allowed writes

Only experimental artifacts:

- `scripts/experiments/d28_side_inverse_convergence.py`
- `docs/experiments/D28_SIDE_INVERSE_CONVERGENCE_RESULTS.md`
- focused tests under an experiments/test location if needed
- this Dev Order

No changes to:
- `martin_d28_1937.py`
- `martin_d28_1937.json`
- `body_contour_solver.py`
- production APIs
- manufacturing geometry
- governance docs

## Required result format

The results document must include:

1. exact repository SHA tested;
2. exact outline source used;
3. exact mapping from side station to perimeter coordinate;
4. equations and unit conventions;
5. Model A result;
6. Model B result;
7. Model C falsification result;
8. residual table for all 12 measurements;
9. convergence diagnostics;
10. sensitivity / identifiability finding;
11. final disposition, one of:
   - `CONVERGES_AND_SUPPORTS_20IN`
   - `CONVERGES_BUT_NOT_20IN`
   - `UNDERDETERMINED`
   - `SPHERICAL_MODEL_MISMATCH`
   - `INSUFFICIENT_GEOMETRY_AUTHORITY`

## Important interpretation rule

This experiment is evidence gathering only.

Even if the fit converges near 20.0 in, do not alter the historical D-28 spec. A separate owner-reviewed change would be required for any production or authority update.
