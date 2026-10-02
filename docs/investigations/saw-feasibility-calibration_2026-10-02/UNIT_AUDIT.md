# Unit and semantic audit

Traced from the request keys through `compute_saw_feasibility`, `SawScorerDesignSpec`, `_convert_to_saw_context` / `_convert_to_saw_design`, and into each calculator. No conversion was changed.

Independent checks below recompute only the defining kinematic and power identities from CASE-B inputs and compare them with observed metadata. They are not a second copy of the heat or beam solvers.

## Numeric and identifier facts the canonical path consumes

| Fact | Request unit | Context field | Calculator use | CASE-B check |
|---|---|---|---|---|
| `blade_diameter_mm` | mm | `blade_diameter_mm` | Rim speed divides by 1000 to metres. Deflection and dynamics divide by 2000 to metres of radius. | `pi * 254 * 3450 / 60000 = 45.883` m/s, metadata 45.88. Consistent. |
| `blade_kerf_mm` | mm | `blade_kerf_mm` | Cut width (mm) when dado width is 0. Heat contact length is also this kerf, divided by rim speed in mm/s. | Distinct from `blade_thickness_mm` 2.5. Both echoed. |
| `blade_thickness_mm` | mm | `blade_thickness_mm` | Divided by 1000 to metres for `I` and flexural rigidity. | Echoed 2.5. Not substituted for kerf. |
| `tooth_count` | count | `tooth_count` | Bite and heat/kickback feed-per-tooth denominator. Not in MRR. | Echoed 24. Integral values pass; non-integers are ERROR upstream. |
| `rpm` | 1/min | `max_rpm` | Operating speed in every calculator that needs RPM. The field name is `max_rpm`; the canonical converter assigns the submitted operating RPM, not a separate machine maximum. | `current_rpm` 3450. Not coerced to the model default 5000. |
| `arbor_size_mm` | mm | `arbor_size_mm` | Radius in metres = value/2000. | Unsupported length 114.3 mm = (254 − 25.4) / 2. Consistent. |
| `stock_thickness_mm` | mm | `stock_thickness_mm` | Cut depth (mm) when dado depth is 0. Kickback subtracts it from radius. Deflection uses it as beam width in metres, capped at diameter/4. | See stock cancellation below. |
| `feed_rate_mm_min` | mm/min | `feed_rate_mm_per_min` | Divided by 60 to mm/s for MRR. Bite uses mm/min directly so the minute cancels against RPM. | Bite `3000 / (3450 * 24) = 0.0362319` mm/tooth, metadata 0.03623. |
| `machine_power_kw` | kW | `machine_power_kw` | `* 1000 * 0.85` → watts available at the blade. Heat and deflection do not read it. | 3 * 1000 * 0.85 = 2550 W, metadata 2550.0. |
| `blade_youngs_modulus_gpa` | GPa | `blade_youngs_modulus_gpa` | `* 1e9` → Pa. | Echoed 200. |
| `cut_length_mm` | mm | design `cut_length_mm` | Cut time only: length/feed gives minutes, times 60 gives seconds. | 11.0 s at repeat 1, including the 5 s overhead in source. |
| `miter_angle_deg`, `bevel_angle_deg` | degree | design | Kickback steps at 15° and 30°. | Echoed 0. |
| `dado_width_mm`, `dado_depth_mm` | mm | design | Replace kerf and stock as cut width and depth when width > 0. | Both 0, so kerf and stock are used. |
| `repeat_count` | count | design | Multiplies cut time only. | Scores unchanged from repeat 1 to repeat 8; time 11.0 s → 88.0 s. |
| `material_id` | string | `material_id` | Substring map in rim speed and bite only. | `hardwood` → 40–70 m/s and 0.03–0.10 mm/tooth. |
| `use_dust_collection` | boolean | `use_dust_collection` | Heat multiplier 1.15 when false. | Echoed true. |
| `tool_id` | string | not a calculator input | Canonical path does not parse it. | Present on the fixture; not a blade specification. |

`spindle_power_watts`, when sent instead of `machine_power_kw`, is divided by 1000 once in `compute_saw_feasibility` and then follows the kW path. CASE-B-SANE uses 3000 W and matches CASE-B.

## Specific cutting energy

| Source | Stated unit | Value | Reaches the canonical calculators? |
|---|---|---|---|
| `MaterialProperties.specific_cutting_energy_j_per_mm3` default and heat/deflection/cutting-force fallback | J/mm³ | 30. Description in the model: softwood ~15, hardwood ~40, MDF ~25. Bounds `ge=5`, `le=200`. | Yes. `material is None`, so the fallback 30 is used. Metadata `specific_cutting_energy_j_per_mm3` is 30.0 on every sensitivity row. |
| `wood_species.json` `thermal.specific_cutting_energy_j_per_mm3` | Stored label is the mojibake `J/mmÂ³` | 0.22 to 1.08 across 473 species. `_meta.sources.estimation_methods` says these are estimates from specific gravity, not a published Kc table. | No. Constructing `MaterialProperties` with the minimum raises `greater_than_equal`. The canonical call never builds `MaterialProperties`. |

Dimensional identity that holds inside the cutting-force calculator, using its own unit comment: `Pc = kc [J/mm³] * MRR [mm³/s] = W`. CASE-B: `30 * 3750 = 112500` W, metadata 112500.0. `112500 / 2550 = 44.1176`, metadata power ratio 44.118.

What this audit does not establish: that 30 J/mm³ is the physical specific energy of the fixture's `hardwood` token. The species file, under the same unit label, is roughly 30 to 100 times smaller and cannot be loaded. The model description's hardwood figure (~40 J/mm³) agrees with the fallback much more than with the species file. A factor-of-1000 "J/cm³ mislabeled as J/mm³" repair is not demonstrated. The identity is unresolved. See adjudication class `FORMULA_REVIEW_REQUIRED` for the quantity and `MAPPING_DEFECT` for the unused material argument.

Hardcoded thermal companions used only by heat, same omission: density 700 kg/m³, specific heat 1700 J/(kg·K), conductivity 0.15 W/(m·K). Those units match the heat docstring (`alpha = k / (rho * cp)` in m²/s). They are not read from `material_id`.

## Observations that are not hidden coercion

Boundary submits of RPM 1000 and 10000, feed 100 and 20000, diameter 100 and 600, tooth count 10 and 120, and repeat count 1 and 100 are echoed by the calculator that consumes them (repeat count is echoed as cut time only). None is replaced by 5000 or 3000. All of those rows are still RED. Recorded in `evidence.json` `boundaries`.

## Semantic concerns recorded, not repaired

1. **Stock thickness cancels in heat.** Heat flux divides workpiece power by contact area, and both scale with depth, so `temp_rise_c` stays 6602.9 for stock 1, 25, 80, and 150 mm in the one-variable sweep. Thinning the stock does not change the heat score.

2. **Stock thickness cancels in deflection while it is below diameter/4.** Beam width tracks stock, and radial force tracks MRR, which also tracks stock. Deflection stays 74.9842 mm at stock 1 mm and 25 mm (diameter/4 is 63.5 mm). At 80 mm and 150 mm the width is capped and deflection rises to 94.4683 mm and 177.128 mm. A thinner board is not a stiffer result in this model.

3. **Kerf is used as a rim-wise contact length.** Heat's contact time is `blade_kerf_mm / rim_speed_mm_per_s`. Kerf is a width. The time for a tooth to cross the kerf is not the time a tooth spends in the cut. Temperature still changes with kerf (3812 °C at 1 mm, 6603 °C at 3 mm, 12055 °C at 10 mm) because contact time feeds the penetration depth after the flux has cancelled kerf.

4. **Kickback exposure is radius minus stock.** CASE-B reports 102 mm "above stock". That is the blade radius (127 mm) minus 25 mm, not a blade projection set by a table height. It adds 25 risk points and leaves the score at 65, so it does not cause the RED. Classed as a model-scope gap.

5. **`max_rpm` holds the operating RPM.** The name reads as a machine limit. The canonical converter stores the request `rpm` there, and rim speed reports it as `current_rpm`. For CASE-B those are the same number, 3450. There is no separate "maximum versus commanded" input on this path.

6. **Machine power cannot clear the overload inside the legal envelope of this fixture.** At 20 kW, the model maximum, available power is 17000 W and the ratio is still 6.618. Cutting-force score stays 10. Heat and deflection do not read power at all, so their RED scores are unchanged across 0.5, 3, 15, and 20 kW.

7. **Feed, kerf, and RPM move the energy outputs in the direction the formulas state, while the scores stay saturated.** Raising feed from 100 to 20000 mm/min raises cutting power from 3750 W to 750000 W and deflection from 2.4995 mm to 499.8946 mm. Heat temperature rises with feed except where the rubbing branch and contact time interact with RPM (RPM 2000 → 8672 °C, 3450 → 6603 °C, 6000 → 5007 °C, 10000 → 5818 °C). Heat score stays 15 because every one of those temperatures is above 200 °C. That saturation is why a physically monotone output can leave the public score unchanged.

None of these items was patched.
