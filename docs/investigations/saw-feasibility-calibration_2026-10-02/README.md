# Saw feasibility calibration — why complete requests stay RED

**Order:** SAW-FEASIBILITY-CALIBRATION-007. **Base:** `ea320c844a5df62954d732602bf4371c4228d3ae` (current `origin/main` at investigation time, merge of PR #421). **Evidence commit:** `e25c83bcfe2f6396f885520b7359afd56310252f` on `cursor/saw-feasibility-calibration-007`. The branch head after the manifest's recorded CBSP21 run is the tip of that branch; it is not copied into `evidence.json`, because the generator must stay byte-stable.

This increment is evidence and adjudication. It does not change production formulas, thresholds, routes, persistence, or the manufacturing-output inventory. It does not authorize a merge or Saw-route containment.

## Question

After PR #420 and PR #422, complete Saw feasibility requests reach the seven canonical calculators and still return RED for ordinary in-range numbers. Is that RED:

1. a correct safety conclusion for the tested machine, blade, and job;
2. a remaining unit, semantic, or mapping defect;
3. an unsupported operating envelope; or
4. a formula or threshold that needs a separately authorized physics change?

## Proven starting state

Re-checked against `origin/main` `ea320c844a5df62954d732602bf4371c4228d3ae`:

| Fact | Evidence |
|---|---|
| PR #420 is merged | `e06b3075a4e1fa9610f551598ff6cdd025c32802` is an ancestor of this base |
| PR #422 is merged | `9f15a2202ae059a23e744a4fb737e48dc5e5944d` is an ancestor of this base |
| Missing facts | Blocking UNKNOWN, `score` is null (`compute_saw_feasibility`) |
| Invalid facts, including non-integral `rpm`, `tooth_count`, and `repeat_count` | Blocking ERROR, `score` is null |
| Complete requests | Reach `feasibility_scorer` and all seven calculators |
| Rosette-only fields and `tool_id` suffixes | Do not change a complete Saw result (authority suite) |
| Manufacturing inventory | 13 `LIVE_UNGOVERNED` rows; Saw routes are not contained |
| Open PRs overlapping this surface | None at investigation start |

The authority baseline `tests/rmos/test_saw_authority_context.py` was run unchanged before this package was written (45 passed). The inventory checker was run unchanged (239 candidates, 13 `LIVE_UNGOVERNED`).

## Frozen decisions

1. RED is a safety result until evidence proves a defect.
2. All seven calculators and the current aggregation stay as they are.
3. Every material fact cites a repository source.
4. Values are labeled `observed`, `repository_authoritative`, `repository_fixture`, `derived`, or `hypothetical_sweep`.
5. A sensitivity sweep is diagnostic. It is not an approved operating point.
6. A field that passes range validation is not, by itself, a valid job.
7. The Compare-route evaluator is semantic comparison only. It is not canonical authority.
8. No Saw route leaves `LIVE_UNGOVERNED` in this increment.
9. No merge without explicit owner authorization.

## What was traced

The public canonical path is `compute_saw_feasibility` → `SawScorerDesignSpec` / `_score_via_scorer` → strict `_convert_to_saw_context` / `_convert_to_saw_design` → `SawLabService.check_feasibility` → `FeasibilityCalculatorBundle.evaluate(design, ctx)`.

`evaluate` does not receive `MaterialProperties`. Heat, deflection, and cutting force therefore use the in-code defaults (`kc` 30 J/mm³, density 700 kg/m³, specific heat 1700 J/(kg·K), conductivity 0.15 W/(m·K)). `material_id` selects only the rim-speed and bite-load lookup bands.

## Cases

| Case | Status | Verdict |
|---|---|---|
| CASE-A repository nominal | **Not assembled.** No machine, blade, material, and job record together supply thickness, arbor, RPM, feed, stock, power, and cut geometry. | No verdict invented |
| CASE-B `COMPLETE_SAW_REQUEST` | Repository fixture, explicitly not a production-approved setup. Same physical numbers as `SANE_SAW` via `spindle_power_watts=3000`. | RED, score 56.2 |
| CASE-C one-variable in-range sweeps and exact model bounds | `hypothetical_sweep`. `approved_operating_point` is false on every row. | All RED |
| CASE-D unsafe control from `test_sac026_028_unsafe_fixture_blocks_red_real_evaluator` | Known invalid control | RED, score 34.3 |

## Plain-language conclusion

The RED on the only complete repository fixture is what the frozen calculators compute. It is not the pre-#420 constant 49.4, and the submitted RPM, feed, diameter, kerf, tooth count, stock, power, and repeat count are echoed rather than replaced by 5000 RPM or 3000 mm/min.

Three calculators score below 30: heat (15), deflection (20), and cutting force (10). Any one of those is enough to force RED before the 80/50 bands. The weighted sum is 56.2, which would be YELLOW if that gate did not exist. Heat is first in evaluation order. Cutting force has the lowest score and the largest weighted-score deficit.

Those three scores share one upstream value: specific cutting energy is fixed at 30 J/mm³ because the canonical call does not pass a material. At the fixture's removal rate (3750 mm³/s) that produces 112500 W of cutting power against 2550 W available on the 3 kW fixture (power ratio 44.118), a reported temperature rise of 6602.9 °C, and 74.9842 mm of blade deflection. Rim speed (45.88 m/s), bite (0.03623 mm/tooth), and blade dynamics (nearest critical 9043 RPM, margin 0.6185) score 100 and are dimensionally consistent with the submitted RPM and diameter.

The species file's specific-cutting-energy estimates (0.22 to 1.08, 473 species, estimated from specific gravity) share a unit label with that 30 J/mm³ default and are rejected by `MaterialProperties` (`ge=5`). This increment does not decide which statement is the physical quantity. That disagreement is the next decision, not a tuned score.

No repository-authoritative realistic job was available to score. No one-variable in-range sweep of the fixture produced GREEN or YELLOW. Canonical Saw authority is **not** ready for batch or compare containment.

## Recommended next increment

**SAW-ENERGY-IDENTITY-008** only. Resolve whether `kc = 30` J/mm³, the model description (softwood ~15, hardwood ~40, MDF ~25), and the species-file estimates are the same quantity, and whether omitting `MaterialProperties` on the canonical call is an accepted limit or a defect. Do not change formulas, thresholds, routes, or inventory in that increment unless the owner explicitly authorizes one of those outcomes there. Do not start route containment from this package.

## Limitations

- CASE-A does not exist in the repository. CASE-B is a test fixture, not a catalogued machine cutting a catalogued blade.
- Sweeps change one variable at a time from that fixture. They are not a search for a permitting operating point.
- Intermediate calculator metadata was already returned by the public feasibility payload. No production logging or response field was added.
- The Compare route was not executed. Its defaults were read from `SawContext()` so the comparison would not persist a run artifact.

## Files

- `INPUT_AUTHORITY.md` — source of every fact, and the substitutions that were rejected.
- `CALCULATOR_TRACE.md` — per-calculator inputs, outputs, and how they become the verdict.
- `UNIT_AUDIT.md` — units from the request through each calculator.
- `SENSITIVITY.csv` — one-variable sweeps. Not approved operating conditions.
- `evidence.json` — machine-readable trace regenerated by the script below.
- `ADJUDICATION.md` — finding classes and the single next increment.

## Reproduction

From the repository root, with the `services/api` virtualenv:

```bash
services/api/.venv/bin/python scripts/investigations/generate_saw_feasibility_calibration.py
cd services/api && .venv/bin/python -m pytest tests/rmos/test_saw_feasibility_calibration_evidence.py -q --no-cov
```

The generator calls `compute_saw_feasibility` only. It does not monkeypatch calculators and does not write production data. Two generations in one process must match before it writes `evidence.json` and `SENSITIVITY.csv`.
