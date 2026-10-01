# The Reverse Engineering of the Martin D-28 #65260

> **STATUS.** The **Corrected Rerun 002 (Arnold side-height authority)** section
> immediately below is the current result. The original first run is
> **SUPERSEDED**: it used `4.4375 in` as the waist *side height* (that value is a
> separate drawing "DEEP" / assembled-depth annotation, comparison-only) and
> assumed a waist station of `10.5 in`. Rerun 002 uses the Arnold side height
> `4.220 in` applied at the **geometrically derived** waist station. The first
> run is retained verbatim further down as historical evidence. **Rerun 003
> (Arnold outline authority) has since been COMPLETED** using the verified traced
> CAD reconstruction of the Arnold #65260 drawing — see the Rerun 003 section
> directly below; its disposition is `SPHERICAL_MODEL_MISMATCH`. No production,
> spec, or authority file is modified by any run. **Run 004A** (original
> side-measurement authority cleanup) is recorded at the top; it removes the
> unsupported 10.5/30.4375 station assignments from the active solve and concludes
> `SINGLE_RADIUS_MODEL_MISMATCH_PERSISTS`. **Run 004B** (proportional dreadnought
> similitude from the GenOne Sheet 05 side-contour template) is recorded at the
> very top: the shape transfer is admissible by construction (no high point) but
> does not reproduce #65260's side profile tightly —
> `PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT`. **Run 004C** (constrained developed-side reconstruction) is recorded at the very top: Arnold's measurements define the side geometry (GenOne gives only landmark priors), 30.4375 in is the active developed coordinate, and the result is `CONSTRAINED_DEVELOPED_RECONSTRUCTION_SUPPORTED`. A follow-on **Rerun 003A
> station-datum audit** is recorded above the Rerun 003 section; it concludes
> `DATUM_DEFINITION_UNRESOLVED` and marks Rerun 003's `SPHERICAL_MODEL_MISMATCH`
> as **STRENGTHENED**.

<!-- RERUN004C_START -->
## Run 004C — Constrained Developed-Side Reconstruction

- Repository SHA tested: `c5799c46af9830d87aaae645221ea9f8ce0fcd59`
- Reverses the 004B hierarchy: **Arnold's measured side heights are the primary hard constraints**; the GenOne plan contributes **longitudinal landmark priors only** (no depth values). The developed side length **30.4375 in is the active coordinate authority** (not inferred from the plan perimeter); **station 27 in is in-domain**. No Sevy high point.
- Artifacts: `D28_65260_DEVELOPED_SIDE_AUTHORITY_004C.json`, `D28_65260_CONSTRAINED_SIDE_PROFILE_004C.csv`, `D28_65260_LANDMARK_RECONSTRUCTION_004C.csv`, `D28_65260_DEEP_INTERPRETATION_004C.csv`, `D28_65260_RERUN_004C_ANALYSIS.csv`, `D28_65260_RERUN_004C_SUMMARY.csv`. No PDF vendored.

### Why 004C follows 004B

- 004B showed a generic full-shape transfer does not fit #65260's side profile.
- 004C reverses the hierarchy: Arnold measurements define the geometry; GenOne contributes only proportional landmark priors; 30.4375 in is an active developed-side authority; 27 in is valid/in-domain; 26.73 in is a different (plan-view) quantity; 4 7/16 DEEP is assembled depth, not raw side height.

### Constrained reconstruction (PCHIP through all Arnold points)

- All 11 source points reproduced exactly (max error 0.00e+00 in). Shape-preserving PCHIP (handles the 3.750→3.740 dip; no global monotonicity forced); overshoot = 0.0000 in; curvature max = 0.0653; slope ∈ [-0.0100, 0.0691].

### Waist placement (Arnold-constrained + GenOne prior)

- GenOne proportional waist prior → s = **11.16 in** (GenOne waist center u=0.367).
- Arnold-constrained solve H(s)=4.220 → s = **11.55 in** (between stations 9 and 12).
- Profile at the GenOne prior predicts H=4.2015 in → waist residual **-0.0185 in**. The GenOne prior and the Arnold-interpolated waist agree within a fraction of an inch; the waist is placeable without contradiction.

### Landmark back-check (GenOne prior → #65260 developed station)

| landmark | GenOne station | u (neck=0) | prior s (in) | reconstructed s (in) |
|---|---:|---:|---:|---:|
| head | 31.37 | 0.000 | 0.00 | — |
| upper_bout | 23.52 | 0.261 | 7.94 | — |
| waist | 20.34 | 0.367 | 11.16 | 11.55 |
| lower_bout | 11.66 | 0.656 | 19.95 | — |
| tail | 1.31 | 1.000 | 30.44 | 30.44 |

### Developed length vs plan half-perimeter (different quantities)

- Developed side length **30.4375 in** (004C authority) vs plan-view half-perimeter **26.73 in** (diagnostic): difference 3.71 in (13.9%). These are treated as different geometric quantities; 26.73 does NOT constrain station placement in 004C.

### GenOne analogy & 4 7/16 DEEP

- GenOne 30 11/32 (30.34375) vs Arnold 30 7/16 (30.4375): diff 0.09375 in → `SOURCE_SUPPORTED_ANALOGY` (supports a ~30.4-in developed side).
- 4 7/16 DEEP (4.4375) − waist side height (4.22) = **0.2175 in (5.525 mm)** → `SOURCE_CORROBORATED_INTERPRETATION` (top+back plate contribution per GenOne construction convention; exact split unresolved; #65260 plate thicknesses not invented).

### Diagnostic fits (not governing)

- Single-radius sphere fitted to the reconstructed profile: R ≈ 40.7 ft, P ≈ -13.66 in, RMSE 0.0648 in (confirms the spherical model remains inadmissible; the constrained profile does not rely on it).
- poly3: RMSE 0.0246 in.
- poly4: RMSE 0.0187 in.

### Bracing / Datum A (independent, qualitative)

- The developed-side reconstruction changes no plan-view geometry; it remains compatible with soundhole Datum A, the X-brace (49°+49°=98°, lower 110°), page-2 brace dimensions, and BB1–BB4 longitudinal placement. Brace cross-section depths are not compared to side depth.

### Disposition

**`CONSTRAINED_DEVELOPED_RECONSTRUCTION_SUPPORTED`**

- All source points reproduced exactly (max err 0.00e+00 in); no overshoot (0.0000 in).
- Waist placeable at s=11.55 in (H=4.220 between stations 9 and 12); GenOne proportional prior s=11.16 in; profile at the prior predicts 4.2015 in (residual -0.0185 in).
- Developed coordinate 30.4375 in internally coherent; station 27 in-domain; no Sevy high point / single-radius condition required.

Parent dispositions `SPHERICAL_MODEL_MISMATCH` and `PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT` are untouched.

<!-- RERUN004C_END -->

---

<!-- RERUN004B_START -->
## Run 004B — Proportional Dreadnought Similitude

- Repository SHA tested: `37875e24049be25ba9b3a33f9f777900a654d39f`
- Replaces the falsified single-radius spherical model with a **pure normalized side-depth shape transfer** from the **GenOne Sheet 05 Dreadnought Side Contour Template** (a real drawn template, not BodyContourSolver/Sevy). No spherical high point governs the model, so a P<0 result is impossible by construction.
- Neither PDF is vendored; extracted geometry + SHA-256/provenance committed (`D28_65260_GENONE_SIDE_CONTOUR_004B.csv`, `D28_65260_RERUN_004B_PROVENANCE.json`, `D28_65260_RERUN_004B_ANALYSIS.csv`, `D28_65260_RERUN_004B_SUMMARY.csv`).

### Reference extraction (GenOne Sheet 05)

- Side-contour template extracted on a 1 in = 72.03 pt station grid (stations 1=tail .. 31.0=neck); 30.0 per-station depths.
- Total depth (incl. plates): neck = 3.642 in, tail = 4.629 in (drawing end dims 3 3/4 / 4 3/4 in).
- **Plate thickness** is NOT numerically dimensioned in the GenOne set (Sheet 02: "Top Thickness Varies"); not assumed. The endpoint rescale to Arnold's side-only heights subsumes a constant plate offset (normalized shape is invariant to it); any plate-thickness variation is unquantified and flagged. Repo 25-ft spherical contour used only as a comparison diagnostic.

### Known-answer round-trip fixture

- extract → normalize → denormalize: RMSE = 0.00000 in, max = 0.00000 in (identity, numerical precision).
- interpolation round-trip (4× resolution): max = 0.00714 in (≤ 0.010 in tolerance: PASS).

### Transfer onto #65260 (endpoints 3.750 neck / 4.720 bottom)

`H(u) = 3.750 + f_GenOne(u)·(4.720 − 3.750)`, u = developed fraction (0 neck .. 1 tail); Arnold station u = station / 30.4375.

| Arnold station (in) | u | measured H (in) | predicted H (in) | residual (in) |
|---:|---:|---:|---:|---:|
| 0 | 0.000 | 3.7500 | 3.7500 | +0.0000 |
| 3 | 0.099 | 3.7400 | 3.8616 | +0.1216 |
| 6 | 0.197 | 3.8950 | 3.9084 | +0.0134 |
| 9 | 0.296 | 4.0850 | 4.1530 | +0.0680 |
| 12 | 0.394 | 4.2400 | 4.3690 | +0.1290 |
| 15 | 0.493 | 4.3500 | 4.4937 | +0.1437 |
| 18 | 0.591 | 4.4550 | 4.5569 | +0.1019 |
| 21 | 0.690 | 4.5650 | 4.5614 | -0.0036 |
| 24 | 0.789 | 4.6400 | 4.6067 | -0.0333 |
| 27 | 0.887 | 4.6700 | 4.6729 | +0.0029 |
| waist @u=0.347 | 0.347 | 4.2200 | 4.2751 | +0.0551 |
| bottom @u=1.000 | 1.000 | 4.7200 | 4.7200 | +0.0000 |

- Interior numeric-station **RMSE = 0.0872 in**, max |resid| = 0.1437 in; waist residual +0.0551 in.

### Diagnostic (not governing): equivalent single-radius sphere

- A sphere fitted to the transferred heights would need R ≈ 22.5 ft, P ≈ -3.08 in — reported only to compare with the falsified model; the shape transfer itself uses no high point.

### H1 — datum reconciliation (promoted)

- GenOne **30 11/32 in = 30.34375** (developed side-template length: tail-block center → head/neck end).
- Arnold **30 7/16 in = 30.4375** (developed 'distance from neck end'; datum per 003A).
- Difference = **0.09375 in (3/32 in, 0.31%)**.
- Classification: **`SOURCE_SUPPORTED_ANALOGY`** — Both quantities are developed side lengths of a dreadnought measured between the head/neck and tail block ends. The 3/32 in (0.31%) difference is consistent with minor endpoint-convention or build differences, not a different measurement type. Note the separate, still-open tension: the ACOUSTIC-BODY-traced #65260 plan-view half-perimeter (26.73 in, Rerun 003) is ~3.6 in shorter than both developed side lengths, which remains UNRESOLVED.
- H1 was NOT used to tune the fit; it guided only the side-length-convention investigation.

### Bracing / Datum A compatibility (qualitative)

- The shape transfer changes only the side-height profile; it does not alter the #65260 plan outline, soundhole Datum A, or the X-brace/back-brace plan layout. The reconstructed side geometry remains compatible with the measured #65260 brace positions and Datum A relationships (no plan-view geometry changed). Brace cross-section depths are NOT compared to back-arch rise (unrelated quantities).

### Disposition

**`PROPORTIONAL_SIMILITUDE_DOES_NOT_SUPPORT_FIT`**

- Model is admissible by construction (pure shape transfer; no high point / no P<0).
- Interior numeric-station RMSE = 0.0872 in, max |resid| = 0.1437 in; waist residual = +0.0551 in.
- Transferred generic-dreadnought shape does not reproduce the Arnold side-height sequence within acceptable residuals.

Parent `SPHERICAL_MODEL_MISMATCH` is untouched. Classification ledger: GenOne template = `DRAWING_DERIVED`; transferred heights/residuals/round-trip = `CALCULATED`; H1 analogy = `SOURCE_SUPPORTED_ANALOGY`; #65260↔developed-span reconciliation (26.73 vs 30.4) = `UNRESOLVED`.

<!-- RERUN004B_END -->

---

<!-- RERUN004A_START -->
## Run 004A — Original Side-Measurement Authority Cleanup

- Repository SHA tested: `4638db2db9e5216e8121f28663afa280433fccb2`
- Corrects the experimental source model before the 004B similitude study. Reuses the Rerun 003 Arnold/JD traced outline and Sevy/Doolin equations unchanged; no historical value, outline, or production/spec/authority file is modified; neither PDF is vendored.
- Artifacts: `D28_65260_SIDE_HEIGHT_AUTHORITY_004A.json`, `D28_65260_SOURCE_AUTHORITY_CROSSWALK_004A.csv`, `D28_65260_SIDE_AUTHORITY_004A_CONVERGENCE.csv`, `D28_65260_SIDE_AUTHORITY_004A_SUMMARY.csv`.

### Source correction

1. The production repo representation conflates measured heights with inferred station coordinates: waist 4.220 in with station **10.5 in**, and bottom 4.720 in with station **30.4375 in**.
2. Arnold's original numeric-station series establishes only the stations **0,3,6,9,12,15,18,21,24,27** (heights unchanged).
3. The numeric heights themselves remain valid (`SOURCE_MEASURED`).
4. **10.5 and 30.4375 are preserved as `LEGACY_REPO_ASSIGNMENT` evidence but excluded from the active 004A solve** (no 30.4375 span, no normalization, no 10.5 waist station).
5. Waist (4.220) and bottom (4.720) are now **geometric validation points** — waist at the minimum-width point, bottom at the tail endpoint.

### Active mapping (literal plan-view developed arc; no clamping)

| Arnold station (in) | in-domain? | status |
|---:|:--:|---|
| 0 | True | OK |
| 3 | True | OK |
| 6 | True | OK |
| 9 | True | OK |
| 12 | True | OK |
| 15 | True | OK |
| 18 | True | OK |
| 21 | True | OK |
| 24 | True | OK |
| 27 | False | OUT_OF_DOMAIN |

- Plan-view half-perimeter = 26.728 in; **station 27 in is OUT_OF_DOMAIN** (27 > 26.73), reported not clamped. Stations 0–24 map normally.
- Geometric waist developed station = 9.277 in (y/L=0.326); geometric tail at y=19.99 in.

### Multi-anchor inverse (source-supported anchors 9 / 12 / 15 only)

| anchor (in→in) | L (in) | R (ft) | P (in) | numeric RMSE | max resid | waist resid | bottom resid | admissible | bound |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 9.0→4.085 | 21.20 | 43.00 | -12.98 | 0.0105 | 0.0152 | -0.0893 | -0.0078 | False | False |
| 12.0→4.24 | 21.16 | 40.00 | -11.39 | 0.0098 | 0.0171 | -0.0848 | -0.0084 | False | False |
| 15.0→4.35 | 21.19 | 39.00 | -10.80 | 0.0098 | 0.0171 | -0.0828 | -0.0086 | False | False |

### Global least-squares (numeric stations 0–24 in-domain)

- L = 21.20 in, R = 39.60 ft, P = -11.11 in, numeric RMSE = 0.0088 in, max resid = 0.0166 in; waist resid = -0.0838 in, bottom resid = -0.0085 in; admissible = False, bound = False.

### Comparison — Rerun 003 / 003A / Run 004A

| aspect | Rerun 003 | Rerun 003A | Run 004A |
|---|---|---|---|
| active station count | 11 (0..30.4375) | 11 (+normalized test) | 10 (0..27) |
| 10.5 active | no (geometric waist) | no | no |
| 30.4375 active | yes (B boundary/clamp) | yes (normalized endpoint) | **no** |
| waist treatment | geometric | geometric | geometric validation |
| bottom treatment | station 30.4375 (B) | station 30.4375 | **geometric tail (B)** |
| best L (anchor 12) | ~21.9 in | ~22.0 / ~12 (norm) | 21.16 in |
| best R (anchor 12) | ~35 ft | ~34 / ~9 (norm) | 40.00 ft |
| P (anchor 12) | <0 | <0 | -11.39 in |
| physical admissibility | inadmissible (P<0) | inadmissible (P<0) | inadmissible (P<0) |
| disposition | SPHERICAL_MODEL_MISMATCH | STRENGTHENED | see conclusion |

### Run 004A conclusion

**`SINGLE_RADIUS_MODEL_MISMATCH_PERSISTS`**

- Every anchor fit on the cleaned source still requires P<0 (anchors L~21.2-21.2 in, all inadmissible); global LS P<0 as well. Removing 10.5/30.4375 did not change this.
- Station 27 in is OUT_OF_DOMAIN (27 > plan half-perimeter 26.73 in); the developed-length shortfall persists independent of the legacy stations.

Note: the Rerun 003A normalized-30.4375 mapping is **not** used in the active 004A solve (the source does not establish 30.4375 as a terminal station); it is retained only as historical robustness evidence.

### Next-step gate

- Run 004A shows the single-radius spherical mismatch persists after source cleanup, so **RUN 004B — PROPORTIONAL DREADNOUGHT SIMILITUDE is AUTHORIZED** as the next experiment (not implemented here). 004B will normalize the generic dreadnought plan's body/side relationships, scale them onto the verified #65260 geometry, validate against the cleaned Arnold side-height dataset, and back-check against the measured #65260 bracing layout.

### Classification ledger

- `SOURCE_MEASURED`: Arnold numeric heights 0–27; waist 4.220; bottom 4.720.
- `LEGACY_REPO_ASSIGNMENT`: waist station 10.5; bottom station 30.4375 (excluded from solve).
- `CALCULATED`: geometric waist station, half-perimeter, inverse (L,R,P).
- `UNRESOLVED`: relation of 10.5/30.4375 to the original series; developed-span convention.

<!-- RERUN004A_END -->

---

<!-- RERUN003A_START -->
## Rerun 003A — Arnold Station Datum Audit

- Repository SHA tested: `bdd45d4cc2ec07fb07af9acdc9e7a14e09447e88`
- Coordinate/datum audit of Arnold's "distance from neck end" station system, using the Rerun 003 Arnold-derived outline unchanged. No historical value or outline was modified; neither PDF is vendored.
- Audit CSV: `D28_65260_STATION_DATUM_AUDIT_003A.csv`; summary `D28_65260_STATION_DATUM_AUDIT_003A_SUMMARY.csv`.

### Step 1 — Source-wording evidence (SOURCE FACT vs interpretation)

| source | wording | supports | does NOT support | confidence |
|---|---|---|---|---|
| John Arnold correspondence (email header) | "Distance from neck end, side width" | distance measured from the neck end; values are side widths | does NOT specify plan-view vs developed vs 3D vs longitudinal | high (verbatim) |
| Rerun 002 order (Ross) restatement | "developed distance from neck end (in)" | developed-side-strip interpretation | "developed" is an added interpretation, not Arnold's word | interpretation, not source |
| 1937 D-28.pdf (Arnold drawing) | plan view + side-profile strip; 'DEEP' depth annotations; no station-path definition | side depths exist as drawn dimensions | no annotation defines how 'distance from neck end' was measured | medium (hand-drawn scan) |
| ACOUSTIC BODY.pdf (JD tracing) | 20.0 / 11.7 / 15.7 / Ø4.0 dimensions; datum A = soundhole | plan-view geometry + calibration | carries no side-station coordinate definition | high (CAD) |

**SOURCE FACT:** Arnold's verbatim coordinate label is "Distance from neck end". The qualifier "developed" is a downstream interpretation (Rerun 002 order), not Arnold's word. No source names the measuring-path convention.

### Step 2 — Reference geometry (Rerun 003, unchanged)

- Body length 19.99 in; geometric waist y=6.52 in (y/L=0.326), developed waist station 9.28 in; plan-view half-perimeter **S_CAD = 26.728 in**; Arnold stated span **S_Arnold = 30.4375 in**.
- Discrepancy: **3.7092 in (13.9%)**.

### Steps 3/5 — Station mapping (CALCULATION): literal (A) vs normalized (C)

| Arnold s (in) | u | A: s_CAD / status | A: (x,y) | C: s_CAD | C: (x,y) | side H |
|---:|---:|---|---|---:|---|---:|
| 0.0000 | 0.000 | 0.00 / OK | (2.06,0.00) | 0.00 | (2.06,0.00) | 3.750 |
| 3.0000 | 0.099 | 3.00 / OK | (4.99,0.48) | 2.63 | (4.67,0.29) | 3.740 |
| 6.0000 | 0.197 | 6.00 / OK | (5.82,3.28) | 5.27 | (5.79,2.55) | 3.895 |
| 9.0000 | 0.296 | 9.00 / OK | (5.42,6.25) | 7.90 | (5.58,5.16) | 4.085 |
| 12.0000 | 0.394 | 12.00 / OK | (6.02,9.16) | 10.54 | (5.55,7.77) | 4.240 |
| 15.0000 | 0.493 | 15.00 / OK | (7.25,11.89) | 13.17 | (6.52,10.22) | 4.350 |
| 18.0000 | 0.591 | 18.00 / OK | (7.86,14.81) | 15.81 | (7.52,12.65) | 4.455 |
| 21.0000 | 0.690 | 21.00 / OK | (7.38,17.75) | 18.44 | (7.84,15.25) | 4.565 |
| 24.0000 | 0.789 | 24.00 / OK | (5.40,19.81) | 21.08 | (7.36,17.82) | 4.640 |
| 27.0000 | 0.887 | 27.00 / OUT_OF_DOMAIN | (2.68,19.99) | 23.71 | (5.68,19.75) | 4.670 |
| 30.4375 | 1.000 | 30.44 / OUT_OF_DOMAIN | (2.68,19.99) | 26.73 | (2.68,19.99) | 4.720 |

- Model A first OUT_OF_DOMAIN station: 27.0 in and 30.4375 in exceed S_CAD=26.73 in (reported OUT_OF_DOMAIN, not silently clamped).

### Step 4 — Model B (longitudinal): REJECTED INTERPRETATION

- A literal longitudinal reading is dimensionally impossible: the station span 30.4375 in exceeds the body length 19.99 in. No source-supported unit/datum transform closes this. Rejected (body not stretched to fit).

### Step 6 — Model D (3D developed rim): REJECTED as the span explanation

- Plan-view arc = 26.728 in; 3D rim = 26.753 in; increase 0.024 in (0.09%).
- This explains only **0.7%** of the 3.709 in gap. Side-height variation cannot lengthen the rim from 26.73 to 30.44 in. (A dome-following path D2 was not asserted — no source defines such a measurement path.)

### Steps 7 — Model E (proportional side-strip)

- Scale k = 30.4375 / 26.728 = **1.1388** (13.9% elongation). Mathematically identical to the normalized endpoint map (C). A 13.9% elongation is not produced by any physical side-following path (the 3D rim adds only 0.09%), and no source supports such a convention.

### Steps 8 — Station spacing

- Arnold's 0,3,6,...,27 increments are uniform 3-in steps with a final 3.4375-in interval to 30.4375. Uniform spacing is consistent with marks laid on a flexible rule/side strip but is NOT itself proof of any single convention (observation vs interpretation kept distinct).

### Step 9 — Spherical inverse under each admissible datum (anchors 9/12/15)

| model | anchor | L (in) | R (ft) | P (in) | RMSE (in) | max resid | waist resid | admissible | bound |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|
| A_literal | 9.0 | 22.05 | 34.00 | -6.90 | 0.0282 | 0.0657 | -0.0657 | False | False |
| A_literal | 12.0 | 21.87 | 35.00 | -7.67 | 0.0281 | 0.0696 | -0.0696 | False | False |
| A_literal | 15.0 | 21.95 | 33.00 | -6.50 | 0.0270 | 0.0639 | -0.0639 | False | False |
| C_normalized | 9.0 | 12.58 | 9.00 | -2.00 | 0.0308 | 0.0545 | -0.0446 | False | False |
| C_normalized | 12.0 | 12.23 | 9.00 | -2.41 | 0.0319 | 0.0556 | -0.0503 | False | False |
| C_normalized | 15.0 | 12.44 | 9.00 | -2.16 | 0.0312 | 0.0550 | -0.0469 | False | False |

### Step 10 / 15 — Audit conclusion and parent disposition

**Station-datum audit conclusion: `DATUM_DEFINITION_UNRESOLVED`.**

- Model B (longitudinal) dimensionally rejected: Arnold span 30.4375 in > 20 in body length.
- Model D (3D rim) rejected: rim path adds only 0.024 in (0.09%), explaining 0.7% of the 3.709 in gap.
- Models A (literal) and C/E (normalized/proportional) both yield inadmissible spherical fits (P<0) — literal at R~34 ft / L~22 in, normalized collapsing to L~12 in (near the lower bound) / R~9 ft. Inadmissibility is robust to the datum choice.
- Source wording ('Distance from neck end') does not name the measuring-path convention; 'developed' is a downstream qualifier, not Arnold's word.

**Parent inverse disposition (Rerun 003 `SPHERICAL_MODEL_MISMATCH`): `STRENGTHENED`.**

Reasoning: the source cannot name the datum convention (UNRESOLVED), but every defensible coordinate model was tested and none yields an admissible single-radius spherical fit — literal (L~22 in, R~34 ft) and normalized (L~12 in, R~9 ft) both require P<0, longitudinal is dimensionally impossible, and the 3D rim / proportional paths cannot physically produce the 13.9% span elongation. Because the inadmissibility is **robust to the datum choice**, the datum ambiguity does not rescue the spherical model; the mismatch is strengthened rather than merely provisional. No new parent disposition vocabulary is introduced.

### Classification ledger

- `SOURCE FACT`: Arnold wrote "Distance from neck end, side width"; waist has no numeric station.
- `CALCULATION`: S_CAD=26.73 in; 3D rim=26.75 in; k=1.139; inverse (L,R,P) per model.
- `HYPOTHESIS`: normalized/proportional station coordinate (tested, not asserted as Arnold's).
- `REJECTED INTERPRETATION`: longitudinal (dimensional); 3D rim as span explanation (0.09%).
- `UNRESOLVED`: the physical measuring-path convention behind the 30.4375-in span.

<!-- RERUN003A_END -->

---

<!-- RERUN003_START -->
## Corrected Rerun 003 — Arnold Outline Authority

- Repository SHA tested: `f69284cfef9f1931674f5230e8a53b69e4b15dcf`
- Outline authority: **Arnold-derived CAD tracing** `ACOUSTIC BODY.pdf` (verified traced reconstruction of the John Arnold #65260 drawing, confirmed by JD).
- Primary historical source (provenance): John Arnold 1937 D-28 #65260 drawing (`1937 D-28.pdf`). Neither PDF is committed (public repo; copyrighted); see the provenance manifest `D28_65260_RERUN_003_PROVENANCE.json`.
- Extracted geometry: `D28_65260_ARNOLD_OUTLINE.csv`; convergence `D28_65260_SIDE_INVERSE_RERUN_003_CONVERGENCE.csv`; summary `D28_65260_SIDE_INVERSE_RERUN_003_SUMMARY.csv`.

### Source classification

| item | classification |
|---|---|
| John Arnold #65260 drawing | `SOURCE_MEASURED` (primary historical) |
| ACOUSTIC BODY.pdf outline / soundhole / dims | `DRAWING_DERIVED` (verified tracing) |
| Arnold side-height series (0..30.4375) | `SOURCE_MEASURED` (correspondence) |
| waist 4.220 in | `SOURCE_MEASURED` (validation, not anchor) |
| 4.4375 in DEEP | `HYPOTHESIS` (comparison only) |
| body length L=20 (A1 fixed) | `DRAWING_DERIVED` calibration |
| geometric waist / bout maxima / s_waist | `CALCULATED` (from perimeter) |
| generic dreadnought similitude | `PROPORTIONAL_ESTIMATE` (not used here) |

### Outline extraction + calibration authority table

| quantity | Arnold-drawing-derived (extracted) | repo value | difference | used for Rerun 003 |
|---|---:|---:|---:|---|
| body length | 19.99 in | 20.0 in | -0.01 in | A1 fixed L; A2 floats |
| upper bout | 11.64 in | 11.5 in | +0.14 in | outline shape |
| lower bout | 15.72 in | 15.625 in | +0.09 in | outline shape |
| soundhole Ø (datum A) | 3.99 in | 4.0 in | -0.01 in | datum cross-check |
| geometric waist width | 10.82 in | 11.0 in | -0.18 in | CALCULATED output |

- Datum A (soundhole center): y_from_neck = 5.896 in, y_from_tail = 14.094 in (extracted directly from the Ø4.0 circle).
- Symmetry: symmetric_by_construction; **CAD symmetry discrepancy = 0 by construction** (NOT evidence the physical 1937 instrument was symmetric).

### Geometric waist (derived output)

- Geometric waist: width 10.818 in at y = 6.523 in (y/L = 0.326); developed station **s_waist = 9.277 in**.
- Developed neck→tail half-perimeter: 26.728 in (Arnold bottom-end station = 30.4375 in).
- Rerun 002 parametric waist station was 14.298 in; **shift = -5.021 in** with the real outline.

### Integration convergence (developed side length)

| resolution (pts) | half-perimeter (in) |
|---:|---:|
| 1993 | 26.7283 |
| 3986 | 26.7282 |
| 7972 | 26.7282 |

### A. Anchor-constrained solves (hard anchor 12.000 in → 4.240 in; also 9 & 15)

| anchor (in→in) | A1 fixed-L: R (ft) / P (in) / RMSE | A2 float-L: L (in) / R (ft) / P (in) / RMSE | admissible |
|---|---|---|:--:|
| 12.0→4.24 | no root | 21.87 / 35.00 / -7.67 / 0.0281 | False |
| 9.0→4.085 | no root | 22.05 / 34.00 / -6.90 / 0.0282 | False |
| 15.0→4.35 | no root | 21.95 / 33.00 / -6.50 / 0.0270 | False |

- Waist-height floor over the (L,R) box (A1, extracted outline): 4.1156 in (target validation 4.220 in).

### Validation at the primary-anchor solution (station 12 → 4.240)

| station (in) | measured H (in) | predicted H (in) | residual (in) | D (in) | role |
|---:|---:|---:|---:|---:|---|
| 0.0 | 3.7500 | 3.7439 | -0.0061 | 29.625 | S bc |
| 3.0 | 3.7400 | 3.7437 | +0.0037 | 29.628 | validation |
| 6.0 | 3.8950 | 3.9038 | +0.0088 | 27.270 | validation |
| 9.0 | 4.0850 | 4.0860 | +0.0010 | 24.308 | validation |
| 12.0 | 4.2400 | 4.2400 | -0.0000 | 21.488 | ANCHOR |
| 15.0 | 4.3500 | 4.3464 | -0.0036 | 19.298 | validation |
| 18.0 | 4.4550 | 4.4368 | -0.0182 | 17.221 | validation |
| 21.0 | 4.5650 | 4.5310 | -0.0340 | 14.750 | validation |
| 24.0 | 4.6400 | 4.6200 | -0.0200 | 11.952 | validation |
| 27.0 | 4.6700 | 4.6854 | +0.0154 | 9.373 | validation |
| 30.4375 | 4.7200 | 4.7098 | -0.0102 | 8.211 | B bc |
| waist@10.15 | 4.2200 | 4.1504 | -0.0696 | 23.171 | validation |

### B. Full least squares

| variant | L (in) | R (in/ft) | P (in) | RMSE (in) | admissible | flags |
|---|---:|---:|---:|---:|:--:|---|
| B_A2_floatL | 21.365 | 446.1/37.18 | -9.545 | 0.0126 | False | P<0 |
| B_A1_fixedL | 19.990 | 600.0/50.00 | -19.081 | 0.0301 | False | P<0 |

### C. Identifiability (anchor clustering + perturbation)

- A2 recovered L across anchors 9/12/15: 21.87..22.05 in (range 0.18); R 33.00..35.00 ft.
- Perturbation (outline scale ±0.5%, heights ±0.01 in) recovered R (fixed-L, primary anchor):
  - scale+0.5%: R = no root
  - scale-0.5%: R = no root
  - h+0.01: R = 47.3 ft, P=-17.51 in
  - h-0.01: R = no root

### D. Rerun 002 (parametric) vs Rerun 003 (Arnold outline)

| quantity | Rerun 002 (parametric) | Rerun 003 (Arnold outline) |
|---|---|---|
| outline authority | BodyContourSolver parametric | Arnold-derived CAD tracing |
| waist y/L | 0.44 (assumed) | 0.326 (derived) |
| derived waist station | 14.30 in | 9.28 in |
| half-perimeter | 31.28 in | 26.73 in |
| hard anchor | waist 4.4375 then 4.220 | station 12.000 → 4.240 |
| disposition | INSUFFICIENT_GEOMETRY_AUTHORITY | SPHERICAL_MODEL_MISMATCH |

### Inconsistency audit

| field | value / conflict | class | disposition |
|---|---|---|---|
| waist side height 4.220 vs 4.4375 DEEP | Δ = +0.2175 in | `SOURCE_CONFLICT` | 4.220 = validation; DEEP comparison-only |
| derived waist station vs Rerun 002 | 9.28 in vs 14.30 in (shift -5.02) | `DERIVATION_MISMATCH` | use Arnold-outline value; parametric was wrong |
| developed half-perimeter vs Arnold span | 26.73 in vs 30.4375 in | `UNIT_OR_DATUM_AMBIGUITY` | plan-view developed length < Arnold stated span; stations >26.7 in clamp to tail; possibly Arnold measured along the domed side |
| waist width | 10.82 in (CALCULATED) vs repo 11.0 in | `DERIVATION_MISMATCH` | outline is authority; repo value not used |
| upper/lower bout | 11.64 / 15.72 in (extracted) vs repo 11.5 / 15.625, label 11.7 / 15.7 | `DRAWING_DERIVED` | drawing/label used, deltas reported |
| admissible single-radius spherical fit | none (best fits require P<0) | `UNRESOLVED` | model-level defect; not a geometry-authority gap |
| CAD symmetry | 0 by construction | `DRAWING_DERIVED` | not evidence the real instrument is symmetric |
| martin_d28_1937.py | single-line module exports nothing | `REPO_CONFLICT` | flagged, not fixed |

### Disposition

**SPHERICAL_MODEL_MISMATCH**

- All anchor solutions are physically inadmissible (P<0/P>L) or radius-bound-pinned.

Interpretation: replacing the parametric outline with the Arnold-derived tracing **removed the Rerun 002 non-identifiability** — the 9/12/15 in hard anchors now converge tightly (L≈22 in, R≈34 ft, RMSE≈0.028 in). But that converged fit is **physically inadmissible** (spherical high point outside the body, P<0) and needs a near-flat ~34 ft back at L≈22 in, not 20 in. So the outline authority is now sufficient and the residual failure is the **single-radius spherical-back model itself**, not the geometry. The proportional generic-dreadnought similitude study (Rerun 004) is the appropriate next experiment.

<!-- RERUN003_END -->

---

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
