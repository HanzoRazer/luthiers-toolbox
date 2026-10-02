# D28 SIDE INVERSE RERUN 002
## The Reverse Engineering of the Martin D-28 #65260

**Status:** EXPERIMENT ONLY - evidence gathering, no production/spec changes.

## Why this rerun is required

The first run conflated two different quantities:

- John Arnold's direct side measurement at the waist: **4.220 in SIDE HEIGHT**, excluding top and back thickness.
- Arnold drawing annotation at the waist: **4 7/16 in = 4.4375 in BODY DEPTH / DEEP**, a different assembled-body measurement.

The first run incorrectly used 4.4375 in as the hard side-height constraint. This rerun corrects that.

There is a second ambiguity that must also be removed:

John Arnold's email lists:

```text
Distance from neck end, side width
0        3.750
3        3.740
6        3.895
9        4.085
Waist    4.220
12       4.240
15       4.350
18       4.455
21       4.565
24       4.640
27       4.670
30 7/16  4.720
```

The email does **not** assign the waist a numeric developed-side station. Therefore **10.5 in is not source-measured authority** merely because it lies between 9 and 12. The waist constraint must be applied at the actual geometric waist location on the plan-view outline, then converted to developed neck-to-waist side arc length by the mapping model.

## Experimental authority rule

For this rerun, use the source-declared experimental values below. Do not silently substitute repository defaults or values from the first run.

At the end, audit all inconsistencies between:
- direct Arnold correspondence,
- Arnold drawing annotations,
- repo production/spec values,
- derived values,
- first-run assumptions.

Do not resolve discrepancies automatically.

## Source-declared experimental inputs

### Direct John Arnold correspondence - authoritative side-height observations

These are measurements from Arnold's 1937 D-28, the same guitar used for his drawing.

All values exclude top and back thickness.

```text
developed distance from neck end (in)    side height (in)
0.0000                                   3.750
3.0000                                   3.740
6.0000                                   3.895
9.0000                                   4.085
WAIST                                    4.220
12.0000                                  4.240
15.0000                                  4.350
18.0000                                  4.455
21.0000                                  4.565
24.0000                                  4.640
27.0000                                  4.670
30.4375 bottom end                       4.720
```

### Arnold drawing - separate assembled-depth evidence

```text
waist drawing annotation: 4 7/16 DEEP = 4.4375 in
```

Treat this as a separate assembled-body-depth observation. Do not use it as side height in the spherical-back inverse solve.

The difference:

```text
4.4375 - 4.2200 = 0.2175 in = 5.5245 mm
```

may be consistent with top+back contribution or another measurement datum, but this is a **hypothesis only** until the drawing datum is fully established.

## Correct fixed point

The hard inverse constraint is:

```text
H_waist_side = 4.220 in
```

at the **geometric waist point** of the D-28 outline.

Do NOT set:

```text
waist_station = 10.5 in
```

unless the actual mapped developed neck-to-waist side arc length independently evaluates to 10.5 in.

Instead:

1. Construct/use the authoritative D-28 plan-view half-outline.
2. Identify the geometric waist point from the outline.
3. Integrate developed side arc length from the neck end to that point.
4. Call that derived quantity `s_waist`.
5. Apply the 4.220 in hard side-height constraint at `s_waist`.

Report the derived `s_waist` and compare it to the legacy/inferred 10.5 in value.

## Revised nested inverse method

For each candidate spherical back radius R:

1. Use direct side-height endpoints:
   - S_neck = 3.750 in
   - B_tail = 4.720 in
   - M = N = 0 for the raw side-height series.
2. Map the geometric waist to its perimeter point and developed side station.
3. Solve body length L such that the Sevy/Doolin model predicts:
   - H_waist = 4.220 in exactly.
4. Derive high point P.
5. Map each numeric Arnold station (0,3,6,9,12,...,30.4375) to the corresponding perimeter point by developed side arc length.
6. Compute D_i as the Euclidean in-plane distance from the spherical high point to each mapped perimeter point.
7. Predict all non-waist side heights.
8. Minimize residuals only over points not used as hard constraints.

## Required analyses

### A. Corrected waist-constrained nested solve
- Hard constraint = 4.220 side height at actual geometric waist.
- Radius sweep R = 8..50 ft unless the equations impose a stricter physically valid range.
- Solve L(R).
- Report residuals, RMSE, max residual, P, and whether the optimum is interior or bound-limited.

### B. Full least-squares cross-check
Fit L and R independently against the direct Arnold side-height observations while preserving the actual geometric waist location.

Reject or flag solutions with:
- P < 0
- P > L
- radius on bound without an interior minimum
- invalid square-root geometry.

### C. Anchor/leave-one-out identifiability
Use alternate observed points as exact anchors and test whether recovered (L,R) pairs cluster.

### D. Compare first run vs corrected run
Explicitly compare:

```text
FIRST RUN (incorrect conflation):
H_waist = 4.4375 in
waist station assumed = 10.5 in

RERUN 002:
H_waist = 4.220 in
waist station = derived geometric waist arc-length station
```

Report changes in:
- recovered L
- recovered R
- P
- RMSE
- residual pattern
- identifiability
- physical admissibility.

### E. Drawing-depth reconciliation check
After the side-height solve only, compare:

```text
drawing waist depth = 4.4375 in
side waist height   = 4.2200 in
difference          = 0.2175 in
```

Do not force the inverse side-height model to explain this 0.2175 in.

If top/back thickness information in the drawing or repo can explain some/all of the difference, report that separately as a provenance-backed reconciliation. Otherwise classify it as unresolved datum/measurement-method difference.

## Terminology rule

Use these terms consistently:

- **side height**: Arnold correspondence values, excluding top/back.
- **assembled body depth / "DEEP"**: drawing annotation if that is what the drawing dimension spans.
- **developed side station**: distance measured along the side from neck end.
- **body length L**: centerline neck-block-to-tail-block plan-view length.
- **back radius R**: spherical-back model radius.
- **high point P**: Sevy/Doolin spherical-back high-point location.

Do not use "depth" and "height" interchangeably.

## Required inconsistency audit

At minimum report:

1. `4.220 side height` vs repo labeling/usage.
2. `4.4375 DEEP` drawing value vs side height.
3. repo `waist station = 10.5` assumption vs derived geometric waist developed station.
4. `30.4375` developed station span vs repo `total_length` naming.
5. any remaining mismatch between the 12-point direct Arnold profile and the spherical-back model.

## Allowed writes

Only experimental files on this branch:
- `scripts/experiments/d28_side_inverse_convergence.py`
- `scripts/experiments/test_d28_side_inverse_convergence.py`
- `docs/experiments/THE_REVERSE_ENGINEERING_OF_MARTIN_D28_65260.md`
- this rerun order

Do not modify production/spec/authority files.

## Final disposition

Use one of:
- `CONVERGES_AND_SUPPORTS_20IN`
- `CONVERGES_BUT_NOT_20IN`
- `UNDERDETERMINED`
- `SPHERICAL_MODEL_MISMATCH`
- `INSUFFICIENT_GEOMETRY_AUTHORITY`

A cleaner numerical fit is not itself evidence of correctness. The result must remain physically admissible and source-consistent.
