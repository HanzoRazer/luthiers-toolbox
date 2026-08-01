# Treatment cohorts — Adirondack (and general rule)

> Draft intake rule for PR #244. Not materials-authority ratification.

## Why this matters

MB Sound publishes **separate suites** for the same botanical species under different treatments.  
**Torrefied Adirondack** and **plain (untreated) Adirondack** must never be pooled as one cohort for matching, defaults, or statistics.

Same `species_id` (`spruce_adirondack`) is allowed. Discrimination is mandatory via:

| Axis | Torrefied suite | Plain suite |
|------|-----------------|-------------|
| `treatment` | `torrefied` | `plain` |
| `species_cohort` | `adirondack_torrefied` | `adirondack_plain` |
| Cohort file | `species/adirondack_torrefied/cohort.json` | `species/adirondack_plain/cohort.json` |
| Specimen ID prefix | `mb-adt-` | `mb-adp-` (reserved) |
| Vendor card label (typical) | `TORREFIED ADIRONDACK` | `ADIRONDACK` (no torrefied) |

## Status

| Cohort | Status |
|--------|--------|
| `mb_sound_adirondack_torrefied` | Intake complete-with-gap (21/22; gap `000002`) |
| `mb_sound_adirondack_plain` | Empty stub — awaiting frames |

## Rules

1. Never put plain Adirondack rows under `mb-adt-*` or `adirondack_torrefied`.  
2. Never average or match across `torrefied` and `plain` without an explicit cross-treatment analysis flag.  
3. Catalog IDs (`000001`…) may restart per video/batch — they are **not** globally unique across treatments; uniqueness is `(dataset, species_cohort, catalog_id)` or `specimen_id`.  
4. Same rule applies later to other species if MB Sound ships treated vs untreated suites.
