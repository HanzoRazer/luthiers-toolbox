# Wood Species Update Template

Standard process for updating or adding wood species entries in `wood_species.json`.

## Prerequisites

- Wood Database (wood-database.com) access for primary species data
- FPL Wood Handbook GTR-282 PDF for North American species verification
- CITES Species Index JSON (`Index_of_CITES_Species_*.json`) for regulatory status
- CIRAD wood density database for tropical species density verification

## Update Checklist

### 1. Core Identity Fields

```json
{
  "id": "species_id",
  "name": "Common Display Name",
  "scientific_name": "Genus species",
  "common_names": ["Name 1", "Name 2", "Regional Name"],
  "category": "hardwood|softwood",
  "guitar_relevance": "established|emerging|experimental"
}
```

**Verification**: Scientific name from Wood Database or ITIS (itis.gov).

### 2. CITES Status

Check CITES Species Index JSON for listing status.

```json
"cites_status": "not_listed",
```

Valid values:
- `"not_listed"` — No CITES regulation
- `"appendix_I"` — Most restricted; commercial trade prohibited
- `"appendix_II"` — Regulated; requires export/re-export permits
- `"appendix_III"` — Country-specific listing
- `"appendix_I_II"` — Split-listed populations

For listed species, add details object:

```json
"cites_status": "appendix_II",
"cites_details": {
  "listing_date": "2023-02-23",
  "annotation": "#17",
  "genus_listing": true,
  "scope": "All populations",
  "source": "CITES_checklist_2026-04-30",
  "source_url": "https://checklist.cites.org/"
}
```

**Annotation field**: Critical for understanding what's regulated. Annotation #17 covers logs, sawn wood, veneer, and laminated wood — finished instruments may be exempt.

### 3. Naming Caveats

For species with genus-level confusion or trade name ambiguity:

```json
"naming_caveats": "Common name 'X' may refer to Y species. Verify when sourcing.",
"cites_genus_caveat": "Genus contains CITES-listed species. Visual ID unreliable."
```

### 4. Physical Properties

All numerical fields require `_source` attribution.

Example: sugar maple, every value from FPL GTR-282 (shrinkage Table 4-3, p. 4-8; the rest Table 5-3a, 12% MC;
density = 1000 × G₁₂ × 1.12, FPL Eq. 4-14; lbf = N / 4.448). `scripts/ci/test_policy_fpl_examples.py` checks each
FPL-attributed value here and in CLAUDE.md against `docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv`.

```json
"physical": {
  "density_kg_m3": 706,
  "_density_source": "FPL_GTR282_table_5-3a",
  
  "contraction_tangential_pct": 9.9,
  "contraction_radial_pct": 4.8,
  "_shrinkage_tangential_source": "FPL_GTR282_table_4-3",
  "_shrinkage_radial_source": "FPL_GTR282_table_4-3",
  
  "modulus_of_elasticity_gpa": 12.6,
  "modulus_of_rupture_mpa": 109.0,
  "_mechanical_source": "FPL_GTR282_table_5-3a",
  
  "janka_hardness_lbf": 1439,
  "janka_hardness_n": 6400,
  "_hardness_source": "FPL_GTR282_table_5-3a",
  
  "specific_gravity": 0.63,
  "_specific_gravity_source": "FPL_GTR282_table_5-3a",
  "_specific_gravity_caveat": "G12: ovendry weight, volume at 12% MC (FPL footnote b); per-flitch measurement recommended"
}
```

**Sources** (as in CLAUDE.md, per property):

*Tangential/radial shrinkage* — approved sources have equal standing (owner rulings 2026-11-19/20); any
one may supply a value, and a sourced value is not replaced only because another approved source covers
the species. Where they differ by more than 0.5 points, record every source's value in
`docs/tonewood/VERIFICATION_LOG.md`.
- FPL GTR-282 Tables 4-3 (domestic) / 4-4 (imported). Cite the exact table and row
- CIRAD Tropix species sheets — one sheet at a time, cited per value (sheet URL + "last update" date);
  never bulk-extracted (see CLAUDE.md)
- Wood Database (Eric Meier) — cited per value with the species page URL
- `unknown_legacy` — not an approved source: untraceable, flagged for follow-up

*Density*
1. FPL GTR-282 — specific gravity from Tables 5-3a (US), 5-4a (Canadian), 5-5a (other imported), converted to
   density at 12% MC (FPL Eq. 4-14)
2. CIRAD wood density database (2018) — tropical species; density and volumetric shrinkage only
3. Wood Database — when neither FPL nor CIRAD has the species

*Mechanical (MOE, MOR, Janka side hardness)*: FPL Tables 5-3a / 5-4a / 5-5a first, then the Wood Database.
Gore & Gilet — lutherie-specific validation, not a primary value source.

**Valid _source values**:
- `"FPL_GTR282_table_4-3"`, `"FPL_GTR282_table_4-4"` — FPL GTR-282 shrinkage tables
- `"FPL_GTR282_table_5-3a"`, `"FPL_GTR282_table_5-4a"`, `"FPL_GTR282_table_5-5a"` — FPL GTR-282 mechanical tables (metric)
- `"FPL_GTR282_table_5-3"` — **deprecated 2026-11-15, do not use**: it names the strength table but was used for
  shrinkage. Not redefined; re-attribute any value carrying it to the table it came from (see CLAUDE.md)
- `"wood_database_meier"` — wood-database.com
- `"CIRAD_2018"` — CIRAD wood density database
- `"CIRAD_Tropix"` — CIRAD–ITTO Tropix species sheet (shrinkage); with `_shrinkage_<dir>_url` and `_shrinkage_<dir>_sheet_date`
- `"unknown_legacy"` — Unverified, flagged for follow-up

**Optional per-field qualifiers** (shrinkage):
- `_shrinkage_<dir>_approximate: true` — the source prints the value as approximate (e.g. "~4%" on wood-database.com)
- `_shrinkage_caveat` — free-text limitation, e.g. values given for a subspecies

### 5. Caveats Object

Typed caveats with semantic keys:

```json
"caveats": {
  "naming": "Trade name ambiguity description",
  "regulatory": "CITES/permit requirements for this species",
  "sustainability": "IUCN status or sourcing concerns",
  "data_confidence": "Source conflicts or measurement range notes",
  "working_properties": "Dust hazards, tool wear, special handling",
  "tonal_uncertainty": "Limited lutherie documentation disclaimer",
  "supply": "Heritage stock, limited availability notes"
}
```

### 6. Lutherie Section

```json
"lutherie": {
  "typical_uses": ["body", "back_sides", "top", "fretboard", "neck", "accent"],
  "tone_character": "Description based on builds or extrapolated from physics",
  "_tone_confidence": "high|medium|low",
  "_tone_source": "production_builds|extrapolated_from_physical_properties",
  "stability_notes": "Dimensional stability assessment",
  "sustainability": "not_restricted|cites_regulated|endangered"
}
```

### 7. Source URL

```json
"_source_url": "https://www.wood-database.com/species-name/"
```

## Worked Example: African Padauk

See `wood_species.json` entry for `african_padauk` — complete implementation of this template with:
- CITES genus caveat (Pterocarpus contains listed species)
- Naming caveat (Mukula confusion)
- Physical properties with CIRAD specific gravity range caveat
- Low tone confidence (extrapolated, not validated in builds)
- Complete source attribution

## Commit Convention

Each species update is a separate commit:

```
data(wood_species): audit douglas_fir — add FPL source attribution

- Verify physical properties against FPL GTR-282 Table 5-3
- Add _shrinkage_*_source fields
- Add cites_status: not_listed
- Add caveats.supply for heritage stock notation
```

## Testing

After updates, verify:
1. `pytest tests/test_wood_movement_calc.py` — shrinkage calculations still work
2. `pytest tests/test_side_bending_calc.py` — bending parameters still work
3. JSON validity: `python -c "import json; json.load(open('path/to/wood_species.json'))"`
