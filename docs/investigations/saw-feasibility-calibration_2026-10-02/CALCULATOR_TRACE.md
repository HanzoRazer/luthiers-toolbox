# Calculator trace

Canonical call, CASE-B, observed from `compute_saw_feasibility` with `COMPLETE_SAW_REQUEST`. Engine: `feasibility_scorer`. No calculator was monkeypatched.

Evaluation order and weights are `FeasibilityCalculatorBundle` in `services/api/app/saw_lab/calculators/__init__.py`. The bundle calls `calculator.calculate(design, ctx)` and does not pass `MaterialProperties`.

Risk rule, from `_classify_risk`: if any calculator score is below 30, the verdict is RED before the bands. Otherwise score ≥ 80 is GREEN, score ≥ 50 is YELLOW, and anything lower is RED. The final score is the weighted sum clamped to 0–100 and rounded to one decimal. Weights sum to 1.

Cut time is `(cut_length_mm / feed_rate_mm_per_min) * 60 + 5` seconds of positioning overhead, times `repeat_count`. CASE-B: `(300 / 3000) * 60 + 5 = 11.0` s. Repeat count does not enter the seven scores.

## CASE-B scoreboard

| Order | Calculator | Source | Score | Weight | Weighted points | Forces RED | Raw output used for the score |
|---|---|---|---|---|---|---|---|
| 1 | heat | `calculators/saw_heat.py` | 15.0 | 0.15 | 2.25 | yes | `temp_rise_c` 6602.9 |
| 2 | deflection | `calculators/saw_deflection.py` | 20.0 | 0.12 | 2.40 | yes | `deflection_mm` 74.9842 |
| 3 | rim_speed | `calculators/saw_rimspeed.py` | 100.0 | 0.13 | 13.00 | no | `rim_speed_m_s` 45.88, band 40–70 |
| 4 | bite_load | `calculators/saw_bite_load.py` | 100.0 | 0.15 | 15.00 | no | `bite_load_mm` 0.03623, band 0.03–0.10 |
| 5 | kickback | `calculators/saw_kickback.py` | 65.0 | 0.15 | 9.75 | no | exposure 102.0 mm, risk score 35 |
| 6 | cutting_force | `calculators/saw_cutting_force.py` | 10.0 | 0.18 | 1.80 | yes | `power_ratio` 44.118, `cutting_power_w` 112500 |
| 7 | blade_dynamics | `calculators/saw_blade_dynamics.py` | 100.0 | 0.12 | 12.00 | no | nearest critical 9043 RPM, margin 0.6185 |

Weighted sum 56.2 matches the reported score (`score_matches_weighted_sum` true).

## What forces RED

Heat is the first calculator in evaluation order with score < 30, so it is the first gate that forces RED. Deflection and cutting force also score below 30. Any one of the three is sufficient. Removing the correlation and keeping the rule:

- The weighted sum alone would be YELLOW (56.2 is between 50 and 80). The < 30 rule, not the sum, is why the public verdict is RED.
- Largest positive contribution to the sum: bite load, 15.0 points.
- Largest deficit against a perfect score: cutting force, `(100 - 10) * 0.18 = 16.2` points, then heat `(100 - 15) * 0.15 = 12.75`, then deflection `(100 - 20) * 0.12 = 9.6`.
- Lowest individual score: cutting force, 10.

Heat, deflection, and cutting force all consume the same unsupplied material default `kc = 30` J/mm³. Rim speed, bite, kickback, and blade dynamics do not.

Shared derived intermediates on CASE-B (observed metadata, not recomputed by the harness):

- Cut width = kerf 3 mm, cut depth = stock 25 mm, feed 3000/60 = 50 mm/s.
- `mrr_mm3_per_s` = 3750 (cutting force and deflection metadata).
- `specific_cutting_energy_j_per_mm3` = 30.0.
- `cutting_power_w` = 112500.
- `available_power_w` = 2550 (`3 kW * 1000 * 0.85`).
- `power_ratio` = 44.118.
- Tangential force 2451.89 N, radial force 980.76 N (radial ratio 0.4 in both force and deflection).

## Per calculator

### Heat

Equation in source, not reimplemented here: cutting power `kc * MRR`; 20% of that power is assigned to the workpiece; contact time is kerf divided by rim speed in mm/s; temperature rise uses `q * sqrt(alpha * tc) / k`. Score bands: ≤ 80 °C → 100, ≤ 140 → 75, ≤ 200 → 45, else 15. CASE-B is above 200 °C, score 15, warning "Critical heat: ~6603 C rise".

Hardcoded when `material` is omitted: `kc` 30, density 700, `cp` 1700, `k` 0.15, burn tendency 0.5. Metadata echoes those thermal defaults (`thermal_conductivity` 0.15, `burn_tendency` 0.5) and `dust_collection_active` true. `feed_per_tooth_mm` 0.0362 is above the 0.02 mm rubbing threshold, so the rubbing multiplier is off.

### Deflection

Cantilever model in source: `delta = Fr * L^3 / (3 * E * I)`, with `Fr` from the same `kc * MRR / rim_speed * 0.4`. Unsupported length observed 114.3 mm (radius 127 mm minus arbor radius 12.7 mm). `I` uses stock thickness as the beam width, capped at diameter/4. Young's modulus observed 200 GPa. Score bands: ≤ 0.05 mm → 100, ≤ 0.10 → 85, ≤ 0.25 → 55, else 20. Observed deflection 74.9842 mm, score 20.

### Rim speed

`v = pi * diameter_mm * rpm / (1000 * 60)` m/s. `material_id` `hardwood` selects 40–70 m/s. Observed 45.88 m/s, `current_rpm` 3450, recommended RPM 4135, score 100. No warning.

### Bite load

`feed_mm_per_min / (rpm * tooth_count)`. Hardwood band 0.03–0.10 mm/tooth. Observed 0.03623 mm, feed echoed 3000, tooth count 24, RPM 3450, score 100. No warning.

### Kickback

Additive risk inverted from 100. Crosscut contributes 10. Exposure is `diameter/2 - stock_thickness` = 102 mm, which is above the 40 mm "high exposure" step and contributes another 25. Feed per tooth 0.0362 mm is between the 0.02 and 0.2 mm steps, so feed adds nothing. Angles are 0. Risk score 35, score 65, warning "Moderate kickback risk (1 factors)". This does not force RED.

The exposure term is radius minus stock, not a measured blade height above a table. See the unit audit.

### Cutting force

`Pc = kc * MRR` with the comment that J/mm³ times mm³/s is watts. Available power is `machine_power_kw * 1000 * 0.85`. Score is 10 when the ratio exceeds 1. Observed ratio 44.118, score 10, warning "OVERLOAD: cutting needs 112500 W but machine provides 2550 W (4412%)". The secondary tangential-force penalty does not apply because the score is already below 50.

### Blade dynamics

Annular-plate estimate using steel density 7850 kg/m³, Poisson 0.3, and eigenvalues 2.00, 5.31, 8.54. Observed mode-1 critical speed 9043 RPM, operating RPM 3450, margin 0.6185, flexural rigidity 286.1722 N·m, score 100. No warning. Margin below 0.05 would score 15; CASE-D at 9000 RPM reaches that branch (margin 0.0048, score 15).

## CASE-D

Same path. Overrides 18000 mm/min, 100 mm stock, 0.5 kW, 9000 RPM. Observed RED 34.3. Forcers: heat 15 (`temp_rise_c` 24528.7), deflection 20 (271.5963 mm), rim speed 10 (119.69 m/s), cutting force 10 (2.7e6 W, ratio 6352.941, `kc` still 30), blade dynamics 15. Bite stays 100 (0.08333 mm/tooth). Kickback stays 65. The harness still returns a blocking RED from the real evaluator.

## Aggregation status

Resolved, not left open. The public score is the weighted sum. The public risk is the < 30 gate, which dominates the band that the sum would have selected.
