# Wood Species Data — Sources & Methodology

**File:** `wood_species.json` v4.0.0  
**Species count:** 472  
**Last updated:** February 2026

---

## Primary Sources

### 1. USDA Forest Products Laboratory — Wood Handbook

> **Full title:** *Wood Handbook: Wood as an Engineering Material*  
> **Publication:** General Technical Report FPL-GTR-282, Forest Products Laboratory, USDA Forest Service, Madison, WI.  
> **URL:** [https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fplgtr282.pdf](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fplgtr282.pdf)

**Data used:**

| Chapter / Table | Properties | Notes |
|-----------------|------------|-------|
| **Table 3-11** — Thermal conductivity of selected hardwoods and softwoods | `thermal_conductivity_w_per_mk` | Values at 12% moisture content, across-grain. ±20% tolerance per FPL guidance. |
| **Ch. 5** — Mechanical Properties of Wood | `modulus_of_rupture_mpa`, `modulus_of_elasticity_gpa`, `janka_hardness_lbf`, `specific_gravity` | Static bending values at 12% MC for ~30 domestic species. |
| **Ch. 5, Table 5-3** — Shrinkage values | `contraction_radial_pct`, `contraction_tangential_pct` | Green to oven-dry, select species only. |

**Coverage:** ~30 species with direct FPL values (all domestic U.S. hardwoods and softwoods). These carry no estimation flag.

---

### 2. The Wood Database

> **Author:** Eric Meier  
> **URL:** [https://www.wood-database.com](https://www.wood-database.com)  
> **License:** Content used under fair-use for material property reference (non-commercial research compilation).

**Data used:**

| Dataset | Properties | Notes |
|---------|------------|-------|
| Individual species pages (465 species) | `density_kg_m3`, `modulus_of_rupture_mpa`, `modulus_of_elasticity_gpa` | Bulk CSV export cross-referenced against published species pages. Each entry carries `_source_url` linking to the originating page. |
| Species descriptions | `grain`, `workability`, `scientific_name` | For species where FPL data was unavailable. |

**Coverage:** 465 species with MOR (MPa), MOE (GPa), and density (kg/m³). Source URLs are preserved per-species in the `_source_url` field.

---

### 3. CIRAD Wood Collection Index

> **Institution:** CIRAD (Centre de Coopération Internationale en Recherche Agronomique pour le Développement), Montpellier, France  
> **Dataset:** Tropix / CIRAD Wood Collection Index  
> **URL:** [https://github.com/openwoodlab/cirad-wood-collection](https://github.com/openwoodlab/cirad-wood-collection)  
> **Records:** 34,395 specimens across 1,831 genera

**Data used:**

| Field | Properties | Notes |
|-------|------------|-------|
| Specific gravity by genus | Cross-validation of `specific_gravity` | Genus-level SG averages computed from all specimens. Used to validate (not replace) density-derived SG values for tropical species. |
| Family classification | Taxonomic verification | Used to confirm species family assignments. |

**Coverage:** Cross-validation layer, not a primary data source. Discrepancies noted where CIRAD genus average spans multiple related species (e.g., *Acacia* spp.).

---

## Derived & Estimated Values

For species lacking direct laboratory measurements, the following estimation methods are used. **All estimated values are flagged** with a `_note` field in the JSON entry.

### Thermal Conductivity

**Method:** Linear regression from specific gravity, per FPL Wood Handbook guidance (Ch. 3, §3.2):

$$k = 0.04 + 0.35 \times SG$$

where $k$ is thermal conductivity in W/(m·K) at 12% MC, across grain. This relationship explains ~90% of variance for air-dry softwoods and hardwoods (FPL Fig. 3-3). Tolerance: ±20%.

### Specific Cutting Energy (SCE)

**Method:** Linear estimate from specific gravity:

$$SCE = 0.15 + 0.65 \times SG$$

Based on published cutting-force research for orthogonal wood cutting. Values in J/mm³.

### Specific Heat Capacity

**Method:** Linear estimate from specific gravity:

$$c_p = 2000 - 600 \times SG$$

Approximation from FPL Wood Handbook Ch. 3, Table 3-10. Values in J/(kg·K).

### Janka Hardness (when not directly available)

**Method:** Power-law regression from air-dry density:

$$J_{lbf} = 0.00355 \times \rho^{1.85}$$

where $\rho$ is density in kg/m³. Derived from regression of FPL + Wood Database Janka values against published densities. R² ≈ 0.85.

### Machining Parameters

All CNC-specific values (`chipload_multiplier`, `feed_clamp`, `speed_clamp`, `doc_limits`, `woc_limits`, `burn_tendency`, `tearout_tendency`) are **computed from the hardness scale** (itself derived from Janka). These are conservative starting points, not laboratory-verified feeds and speeds. The formulas are documented in `scripts/merge_wood_data.py` and `scripts/bulk_import_wood_species.py`.

---

## Data Tiers & Provenance

Each species includes a `guitar_relevance` field indicating its classification:

| Tier | Count | Description | Data Quality |
|------|-------|-------------|--------------|
| **primary** | 19 | Traditional tonewoods (spruce, mahogany, rosewood, ebony, maple, etc.) | Highest — FPL + empirical lutherie data + hand-curated machining parameters |
| **established** | 30 | Well-known guitar woods (sapele, walnut, bubinga, bocote, etc.) | High — FPL or Wood Database + curated lutherie notes |
| **emerging** | 57 | Gaining popularity as sustainable/affordable alternatives | Medium — Wood Database + estimated thermal/machining values |
| **exploratory** | 366 | Valid machinable woods, not yet common in guitars | Baseline — Wood Database density/MOR/MOE + all other values estimated |

### How to identify estimated vs. measured values

- **Thermal block:** If `_note` contains "estimated from density/SG", all thermal values are computed.
- **Machining block:** For emerging/exploratory species, all machining values are formula-derived.
- **Physical block:** `modulus_of_rupture_mpa` and `modulus_of_elasticity_gpa` are always from published sources (FPL or Wood Database).
- **Janka:** For the original 49 species, Janka is from published sources. For bulk-imported species, Janka is estimated from density.

---

## Version History

| Version | Date | Species | Changes |
|---------|------|---------|---------|
| 1.0.0 | Feb 2026 | 13 | Initial consolidation from 6 scattered files |
| 2.0.0 | Feb 2026 | 26 | Added FPL thermal conductivity data (Table 3-11) |
| 2.1.0 | Feb 2026 | 34 | Added structural mechanics (MOR, MOE, Janka, contraction) |
| 3.0.0 | Feb 2026 | 49 | Merged Wood Database CSV + CIRAD cross-validation |
| 4.0.0 | Feb 2026 | 472 | Bulk import of all Wood Database species; added `guitar_relevance` tiering |

---

## Licensing & Attribution

- **USDA FPL Wood Handbook** — U.S. Government work, public domain.
- **The Wood Database** (wood-database.com) — Content referenced under fair use. Individual species page URLs preserved in `_source_url` fields. Site operated by Eric Meier.
- **CIRAD Wood Collection Index** — Open data, published under CC-BY via GitHub. Original dataset: CIRAD, Montpellier, France.
- **Estimation formulas** — Derived from published FPL relationships and published cutting-force literature. No proprietary data.

---

## Contact & Corrections

If you identify an error in species data, please:

1. Check the `_source_url` for the original reference.
2. Compare against the USDA FPL Wood Handbook (latest edition).
3. File an issue with the species `id`, the incorrect field, and the corrected value with its source.
