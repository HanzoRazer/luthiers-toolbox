# Input authority

Every material fact used in this investigation is classified as one of:

- `repository_authoritative` — a catalogued machine, blade, material, or job record.
- `repository_fixture` — a value that already exists in a Saw route or service test, including fixtures the test itself marks as constructed.
- `derived` — computed by production code from the inputs above. Recorded, not re-derived in the harness.
- `hypothetical_sweep` — an in-range probe. Not an approved operating point.
- `observed` — a production-calculator output captured by the diagnostic harness.

CASE-A was not assembled. No field below is promoted to `repository_authoritative`.

## CASE-A — not assembled

Required together for a nominal job: blade diameter, kerf, blade thickness, tooth count, arbor, operating RPM, feed, stock thickness, machine power, Young's modulus, dust-collection flag, cut length, cut type, angles, dado sizes, and repeat count.

| Candidate source | What it actually contains | Why it was not used as CASE-A |
|---|---|---|
| `services/api/data/sample_saw_blades.json` | Four blades: diameter, kerf, tooth count, carbide label. Ids `saw:thin_140`, `saw:thin_125`, `saw:standard_150`, `saw:heavy_180`. | No thickness, arbor, RPM, feed, stock, power, or cut geometry. |
| `services/api/app/cam/machines.py` `MACHINE_PRESETS` / `BCamMachineSpec` | Router and spindle travel, RPM limits, feed limits. | No `power_kw` or saw-blade identity. RPM bands are router bands, often above the Saw context maximum of 10000. |
| `services/api/app/data_registry/system/materials/wood_species.json` | 473 species. `thermal.specific_cutting_energy_j_per_mm3` from 0.22 to 1.08. Provenance: estimated from specific-gravity regressions, not a published Kc table. Stored unit label is the literal mojibake `J/mmÂ³` (U+00C2 U+00B3). | Rejected by `MaterialProperties` (`greater_than_equal`, bound `ge=5`). The canonical path does not load this file. |
| `services/api/app/cam_core/saw_lab/bandsaw/data/bandsaw_blades.json` | Bandsaw width, thickness, TPI, kerf. | Different machine class. Kerf values are below the circular-saw kerf minimum of 1.0 mm. No diameter, RPM, or power. |
| `app/data/cam_core/saw_blades.json` and `services/api/app/saw_lab/data/saw_blades.json` | Named in older docs and scripts. | Not present in this tree. |
| `SawContext()` defaults | Diameter 254 mm, kerf 3 mm, thickness 2.5 mm, 24 teeth, max RPM 5000, arbor 25.4 mm, stock 25 mm, feed 3000 mm/min, power 3 kW, E 200 GPa, dust collection on. | Model defaults used when the Compare route omits a field. Not a machine record. |

Unavailable, and not invented: a single repository identity that binds one machine's power and RPM to one blade's thickness and arbor and one job's stock, feed, and cut geometry.

## CASE-B — repository fixture

Source: `COMPLETE_SAW_REQUEST` in `services/api/tests/rmos/test_saw_authority_context.py`.

The fixture comment states that the request is constructed for authority testing and is not a production-approved machine setup, and describes the numbers as "10 inch 24T bench-saw-ish". Classification for every field: `repository_fixture`. Confidence: the values are what the authority suite submits; they are not a catalogued physical combination.

| Field | Value | Unit at the API boundary | Transformation on the canonical path |
|---|---|---|---|
| `tool_id` | `saw:authority_test` | identifier | Not parsed. Suffixes do not change the score. |
| `material_id` | `hardwood` | string key | Copied to `SawContext.material_id`. Selects rim-speed and bite-load bands only. Not loaded as `MaterialProperties`. |
| `blade_diameter_mm` | 254.0 | mm | Copied. |
| `blade_kerf_mm` | 3.0 | mm | Copied. Used as cut width when `dado_width_mm` is 0. |
| `blade_thickness_mm` | 2.5 | mm | Copied. Plate thickness, not kerf. |
| `tooth_count` | 24 | count | Copied. Must be an integral number. |
| `rpm` | 3450 | revolutions per minute | Assigned to `SawContext.max_rpm`. Calculators use that field as the operating speed (`current_rpm`). |
| `arbor_size_mm` | 25.4 | mm | Copied. |
| `stock_thickness_mm` | 25.0 | mm | Copied. Used as cut depth when dado depth is 0. |
| `feed_rate_mm_min` | 3000.0 | mm/min | Copied to `feed_rate_mm_per_min`. |
| `machine_power_kw` | 3.0 | kW | Copied. Cutting force converts with `* 1000 * 0.85`. |
| `blade_youngs_modulus_gpa` | 200.0 | GPa | Copied. Deflection and dynamics convert with `* 1e9` to Pa. |
| `use_dust_collection` | true | boolean | Copied. Heat applies a 1.15 multiplier only when this is false. |
| `cut_length_mm` | 300.0 | mm | Design fact. Consumed by cut-time estimation, not by the seven scores. |
| `cut_type` | `crosscut` | enum string | Kickback base risk 10. |
| `miter_angle_deg` | 0.0 | degree | Kickback only. |
| `bevel_angle_deg` | 0.0 | degree | Kickback only. |
| `dado_width_mm` | 0.0 | mm | Zero selects kerf as cut width. |
| `dado_depth_mm` | 0.0 | mm | Zero selects stock thickness as cut depth. |
| `repeat_count` | 1 | count | Cut-time multiplier only. Must be an integral number. |

`SANE_SAW` in `services/api/tests/rmos/test_rmos_feasibility_authority.py` is the same physical fixture with `spindle_power_watts` 3000 instead of `machine_power_kw` 3. The canonical path divides watts by 1000 once. Re-scored in this investigation as CASE-B-SANE: RED 56.2, same score and risk as CASE-B.

## CASE-C — hypothetical sweeps

Source of the baseline: CASE-B. Source of each changed value: the inclusive bounds and interior points of `SawContext` / `SawDesign` in `services/api/app/saw_lab/models.py` (`rpm` 1000–10000, feed 100–20000 mm/min, diameter 100–600 mm, kerf 1–10 mm, teeth 10–120, stock 1–150 mm, power 0.5–20 kW, repeat 1–100).

Classification: `hypothetical_sweep`. `approved_operating_point` is false. Exact bound echoes are in `evidence.json` under `boundaries`. The full grid is `SENSITIVITY.csv`.

## CASE-D — known invalid control

Source: `test_sac026_028_unsafe_fixture_blocks_red_real_evaluator` in `services/api/tests/rmos/test_saw_authority_context.py`.

Overrides on top of CASE-B, as that test already does:

| Field | Value | Classification |
|---|---|---|
| `feed_rate_mm_min` | 18000 | repository fixture (unsafe control) |
| `stock_thickness_mm` | 100 | repository fixture (unsafe control) |
| `machine_power_kw` | 0.5 | repository fixture (unsafe control) |
| `rpm` | 9000 | repository fixture (unsafe control) |

Observed verdict: RED, score 34.3, engine `feasibility_scorer`.

## Rejected substitutions

- Filling CASE-A from `SawContext` defaults or from `sample_saw_blades.json` plus a guessed spindle power.
- Loading species specific-cutting-energy estimates into `MaterialProperties`.
- Treating a range-valid field set as a valid job.
- Calling the Compare-route default fill a richer physics model.
- Choosing inputs because they might score GREEN or YELLOW.
