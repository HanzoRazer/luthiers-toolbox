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

```json
"physical": {
  "density_kg_m3": 745,
  "_density_source": "wood_database_meier",
  
  "contraction_tangential_pct": 5.0,
  "contraction_radial_pct": 3.1,
  "_shrinkage_tangential_source": "FPL_GTR282_table_5-3",
  "_shrinkage_radial_source": "FPL_GTR282_table_5-3",
  
  "modulus_of_elasticity_gpa": 13.07,
  "modulus_of_rupture_mpa": 126.7,
  "_mechanical_source": "wood_database_meier",
  
  "janka_hardness_lbf": 1725,
  "janka_hardness_n": 7672,
  
  "specific_gravity": 0.74,
  "_specific_gravity_caveat": "CIRAD reports range X-Y; per-flitch measurement recommended"
}
```

**Source priority**:
1. FPL GTR-282 Table 5-3 — North American species (shrinkage, MOE, MOR, density)
2. Wood Database (Eric Meier) — Tropical species, comprehensive properties
3. CIRAD — Tropical species density, volumetric shrinkage
4. Gore & Gilet — Lutherie-specific validation

**Valid _source values**:
- `"FPL_GTR282_table_5-3"` — USDA Forest Products Lab
- `"wood_database_meier"` — wood-database.com
- `"CIRAD_2018"` — CIRAD wood density database
- `"unknown_legacy"` — Unverified, flagged for follow-up

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
