# MB Sound field glossary (Spanish UI → TonewoodEntry / panel schema)

Overlapping acoustic quantities map to **`TonewoodEntry` names** (`materials/schemas.py`).  
Panel-only concepts map under `panel.*`. See [`NAMESPACE.md`](./NAMESPACE.md).

| Spanish / UI (common) | Schema path | Notes |
|----------------------|-------------|-------|
| Densidad | `density_kg_m3` | Confirm kg/m³ vs g/cm³ (×1000) |
| Peso / Masa | `panel.mass_g` | grams vs kg |
| Espesor / Grosor | `panel.thickness_mm` | mm |
| Largo / Longitud | `panel.length_mm` | along grain if labeled |
| Ancho / Anchura | `panel.width_mm` | across grain if labeled |
| Módulo de Young / E / Rigidez longitudinal / **Stiffness (Gpa)** | `modulus_of_elasticity_gpa` | MB card says “Stiffness”; analysis UI says “Young modulus” — **same field**, not `stiffness_gpa` |
| Módulo transversal / E⊥ / Rigidez transversal | `E_C_gpa` | **not** shown on first Adirondack frames |
| Relación de anisotropía | `panel.R_anis` | or compute MOE/`E_C_gpa` |
| Resonance Frequency / Frecuencia | `panel.modes[].frequency_hz` | single value → label `resonance_vendor` until (m,n) known |
| Respuesta en frecuencia / Spectrum | provenance + plots | unnumbered plots → [`LINKAGE.md`](./LINKAGE.md) |
| Radiation coefficient / Índice de radiación | `panel.src_vendor` | vendor formula (Nicoletti); do **not** silently overwrite computed `radiation_ratio` |
| Sustain (Q Factor) / Q factor | `panel.q` | |
| Sample name (analysis UI) | `panel.vendor_ids.analysis_sample_name` | e.g. `ADT-C-01` |
| Card number under species title | `panel.vendor_ids.catalog_id` | e.g. `000001` |
| Sample nodal lines (mm) | `panel.nodal_lines_mm` | analysis UI only |
| Año de corte | `panel.cutting_year` | |
| Humedad / MC | `panel.moisture_content_pct` | |
| Tapa / Soundboard / Top | `panel.role: soundboard` | TonewoodRole |
| Aros y fondo / Back & sides | `panel.role: back_sides` | |
| Abeto / Spruce | `species_id` | Adirondack / Alpine / European… |
| Cedro rojo | often `cedar_western_red` | confirm |
| Palosanto / Rosewood | `rosewood_*` | do not guess CITES from label alone |
| Nogal / Walnut | `walnut_*` | |

## Unit traps

1. **g/cm³ → kg/m³:** ×1000  
2. **MPa → GPa:** ÷1000  
3. Free-plate modes usually tens–hundreds of **Hz** (not kHz)  
4. If density from mass/(L×W×h) disagrees with stated density by >~5%, keep both and set `confidence: medium`

## Species_id hints (confirm before merge)

| Vendor label (EN/ES) | Likely `species_id` |
|----------------------|---------------------|
| Adirondack spruce / abeto rojo americano | `spruce_adirondack` |
| Torrefied Adirondack / Adirondack torrefacto | same `species_id`; `treatment: torrefied`; cohort `adirondack_torrefied`; IDs `mb-adt-*` |
| Plain / untreated Adirondack | same `species_id`; `treatment: plain`; cohort `adirondack`; IDs `mb-ad-*` |
| Alpine / European spruce / abeto europeo | `spruce_european` (or alpine alias if present) |
| Red cedar / cedro rojo | `cedar_western_red` |
| Indian rosewood / palosanto de la India | `rosewood_east_indian` |
| American walnut / nogal americano | `walnut_black` |
| Malaysian blackwood | null + note until SoT id exists |
