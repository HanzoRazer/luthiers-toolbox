# MB Sound / materials field namespace — provisional alignment note

> **Status: PROVISIONAL — NOT a specification-authority ruling.**  
> Does **not** decide Inv-026-A (or any materials-vocabulary authority investigation).  
> Does **not** admit Inv-024 source extraction.  
> Draft-PR scaffolding only; merge must not be treated as ratifying field authority.

## Concern

Inventing parallel names for the same physical quantities (`E_parallel_gpa` vs `modulus_of_elasticity_gpa` vs `E_L_GPa`) creates **namespace collision**: importers and cross-repo consumers cannot tell whether two fields are the same quantity.

## What this note does

For this empty MB Sound **scaffold**, overlapping quantities temporarily reuse the **existing in-repo** `TonewoodEntry` property names so we do not mint a fourth vocabulary while waiting on authority.

| Layer | Current in-repo reference (not cross-repo ratified) |
|-------|-----------------------------------------------------|
| Pydantic | `services/api/app/materials/schemas.py` → `TonewoodEntry` |
| Species SoT | `wood_species.json` |
| Curated acoustic view | `luthier_tonewood_reference.json` |

If a cross-repo materials JSON / Inv-026-A ruling supersedes this, **rebind the corpus** — do not treat this file as locked authority.

## Provisional scaffold rules (revocable)

1. Prefer `density_kg_m3`, `modulus_of_elasticity_gpa`, `E_C_gpa` over invented synonyms.  
2. Discriminate rows with `record_kind: "measured_panel"` so they are not species averages.  
3. Join species via `species_id` only.  
4. Panel-only keys under `panel.*`.  
5. Plate calculator `E_L_GPa` / `E_C_GPa` remain **call-site adapters**, not a storage vocabulary.  
6. Forbidden in this scaffold: `E_parallel_gpa`, `E_perpendicular_gpa`, `youngs_modulus`, bare `moe`.

## Explicit non-claims

- Not cross-repo schema ratification  
- Not permission to extract/ingest MB Sound media (Inv-024 remains parked on source availability)  
- Not a change to `TonewoodEntry` / `wood_species.json` contracts beyond a pointer in `SOURCES.md`
