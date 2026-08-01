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
| Módulo de Young / E / Rigidez longitudinal | `modulus_of_elasticity_gpa` | **not** `E_parallel_*` |
| Módulo transversal / E⊥ / Rigidez transversal | `E_C_gpa` | **not** `E_perpendicular_*` |
| Relación de anisotropía | `panel.R_anis` | or compute MOE/`E_C_gpa` |
| Frecuencia / f / Modo | `panel.modes[].frequency_hz` | keep vendor mode label |
| Respuesta en frecuencia | `panel.modes` / notes | curve ≠ single number |
| Índice de radiación / SRC / RR | `panel.src_vendor` | vendor formula; do not overload computed `radiation_ratio` without `indices_source` |
| Factor Q | `panel.q` | |
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
| Alpine / European spruce / abeto europeo | `spruce_european` (or alpine alias if present) |
| Red cedar / cedro rojo | `cedar_western_red` |
| Indian rosewood / palosanto de la India | `rosewood_east_indian` |
| American walnut / nogal americano | `walnut_black` |
| Malaysian blackwood | null + note until SoT id exists |
