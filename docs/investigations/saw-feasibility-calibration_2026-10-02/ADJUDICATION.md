# Adjudication

RED on the complete repository fixture is what the frozen calculators return. It is not evidence that a catalogued shop saw, blade, and job were scored, because no such combination exists in the repository. It is also not the pre-repair constant score: the fixture's RPM, feed, diameter, kerf, teeth, stock, and power are the values in the calculator metadata.

## Findings

| ID | Class | Finding |
|---|---|---|
| F1 | `EXPECTED_SAFETY_RESULT` | Given the frozen formulas, CASE-B is RED 56.2. Heat 15, deflection 20, and cutting force 10 each sit under the < 30 gate. The weighted sum 56.2 would be YELLOW without that gate. The gate is existing aggregation, preserved on purpose. |
| F2 | `MAPPING_DEFECT` | `SawLabService.check_feasibility` calls `FeasibilityCalculatorBundle.evaluate(design, ctx)` with no `MaterialProperties`. `material_id=hardwood` selects rim-speed and bite-load bands only. Heat, deflection, and cutting force always take `kc=30`, density 700, specific heat 1700, and conductivity 0.15. |
| F3 | `FORMULA_REVIEW_REQUIRED` | Those three RED scores are the `kc * MRR` path at 30 J/mm³: 112500 W, power ratio 44.118, 6602.9 °C, 74.9842 mm deflection. The model text says hardwood is about 40 J/mm³. The species file's estimates are 0.22–1.08 under a corrupted `J/mm³` label and are rejected by `ge=5`. This increment does not choose which number is physical and does not change the formula. |
| F4 | `INSUFFICIENT_EVIDENCE` | A 1000× "J/cm³ written as J/mm³" repair is not shown. The kinematic identities (rim speed, bite, kW→W, J/mm³ × mm³/s → W) close on CASE-B. The species estimates are documented as specific-gravity regressions, not as a published Kc table that would prove the scale. |
| F5 | `MODEL_SCOPE_GAP` | Kickback exposure is blade radius minus stock (102 mm on CASE-B), not a table-saw blade projection. Score 65. It does not force RED. Heat and deflection also cancel ordinary stock thickness, and machine power inside 0.5–20 kW cannot move heat, deflection, or the cutting-force score off RED for this fixture. |
| F6 | `EXPECTED_SAFETY_RESULT` | CASE-D, the existing unsafe fixture, stays blocking RED 34.3 on the real evaluator, with additional rim-speed and blade-dynamics failures. |
| F7 | `INSUFFICIENT_EVIDENCE` | CASE-A cannot be assembled. Sample blades, machine presets, the species file, and bandsaw records do not jointly supply a saw job. No repository-authoritative realistic case was scored. |
| F8 | `EXPECTED_SAFETY_RESULT` | Every `hypothetical_sweep` row in `SENSITIVITY.csv`, including exact model bounds, is RED. `approved_operating_point` is false. Sweeps are not permission to run those settings. |

No finding is classed `UNIT_DEFECT` or `THRESHOLD_REVIEW_REQUIRED`. The mm, mm/min, RPM, and kW conversions that were checked match the calculator metadata. Thresholds were not retuned, and the evidence does not isolate a single threshold (as opposed to the shared `kc` magnitude) as the thing an owner should change.

## Answers

1. **First force to RED.** Heat, score 15, first in `FeasibilityCalculatorBundle` order. Deflection and cutting force would also force RED on their own.
2. **Strongest score contribution.** Bite load adds the most points (15.0). Cutting force creates the largest deficit (16.2 points) and has the lowest score (10) and the highest weight (0.18). The risk decision is the < 30 gate, not the largest term in the sum.
3. **Dimensions at the calculator boundary.** Rim speed, bite, arbor unsupported length, available watts, and `kc * MRR` in watts match the submitted units. Kerf and blade thickness stay distinct. The unresolved item is the meaning of `kc`, not a dropped millimetre conversion on those identities.
4. **Supported physical combination.** No. CASE-B is a constructed authority fixture. CASE-A is not in the repository.
5. **Sensitivity direction.** Feed, kerf, and diameter move power and deflection as the energy and beam formulas state. RPM moves rim speed and bite as the kinematic formulas state. Tooth count moves bite and the heat rubbing branch, not MRR. Repeat count moves only cut time. Scores for heat, deflection, and cutting force stay saturated in the bottom band across these one-variable sweeps, so the public score often does not move when the raw output does. Machine power reduces the ratio and never brings it through 1.0 inside the model maximum for this fixture.
6. **Compare route.** It calls the same `SawLabService.check_feasibility` and therefore the same bundle with no material. Omitted fields become `SawContext` defaults (254 mm, 3 mm kerf, 2.5 mm plate, 24 teeth, 5000 RPM, 25.4 mm arbor, 25 mm stock, 3000 mm/min, 3 kW, 200 GPa, dust on). It is not a richer physics model. It answers the same safety question with default fill where the canonical path now fails closed. This investigation did not call `compare_saw_candidates` and did not persist a run.
7. **GREEN or YELLOW without a physics change.** Not on a repository-authoritative job: none could be assembled. Not on the repository fixture or on any one-variable in-range sweep of that fixture: all RED. This is not a claim about the entire untested multi-variable space. Friendly combinations were not hunted.
8. **Containment.** **NO.** Neither the batch Saw route nor the compare route should be contained onto this verdict. The public result is the aggregate. Kinematic calculators respond coherently and still do not decide the risk. Compare would publish the same energy model, plus silent defaults the canonical path has stopped using.

## Containment readiness

`NO`

## Recommended next increment

SAW-ENERGY-IDENTITY-008

One decision increment. It may only resolve the identity of specific cutting energy and the omitted `MaterialProperties` argument:

- which repository statement is authoritative for `kc` (the calculator fallback and its hardwood ~40 J/mm³ description, the species-file estimates, or neither);
- whether the canonical call's failure to pass `MaterialProperties` is an accepted model limit or a defect;
- no formula, threshold, route, persistence, or inventory change unless that order explicitly authorizes one of those outcomes.

Route containment stays unauthorized until that decision exists. This package does not start it.
