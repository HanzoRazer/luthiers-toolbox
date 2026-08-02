# Treatment cohorts — Adirondack (and general rule)

> Draft intake rule for PR #244. Not materials-authority ratification.

## Why this matters

MB Sound publishes **separate suites** for the same botanical species under different treatments.  
**Torrefied Adirondack** and **plain (untreated) Adirondack** must never be pooled as one cohort for matching, defaults, or statistics.

Same `species_id` (`spruce_adirondack`) is allowed. Discrimination is mandatory via:

| Axis | Torrefied suite | Plain suite |
|------|-----------------|-------------|
| `treatment` | `torrefied` | `plain` |
| `species_cohort` | `adirondack_torrefied` | `adirondack` |
| Cohort file | `species/adirondack_torrefied/cohort.json` | `species/adirondack/cohort.json` |
| Specimen ID prefix | `mb-adt-` | `mb-ad-` (reserved) |
| Vendor card label (typical) | `TORREFIED ADIRONDACK` | `ADIRONDACK` (no torrefied) |

## Status

| Cohort | Status |
|--------|--------|
| `mb_sound_adirondack_torrefied` | Lab-procedure rebuild from complete workbook (21/22; gap `000002` unavailable) |
| `mb_sound_adirondack` | Empty stub — **source currently unavailable** (do not invent rows) |

## Rules

1. Never put plain Adirondack rows under `mb-adt-*` or `adirondack_torrefied`.  
2. Never average or match across `torrefied` and `plain` without an explicit cross-treatment analysis flag.  
3. Catalog IDs (`000001`…) may restart per video/batch — they are **not** globally unique across treatments; uniqueness is `(dataset, species_cohort, catalog_id)` or `specimen_id`.  
4. Same rule applies later to other species if MB Sound ships treated vs untreated suites.

## Other suites

| Suite | Cohort | Prefix | Status |
|-------|--------|--------|--------|
| Red Cedar (plain) | `red_cedar` | `mb-rc-` | Lab workbook rebuild complete (22/22) |
| Red Cedar (30-year naturally dried) | `red_cedar_30yr_naturally_dried` | `mb-rc30-` | partial — catalog `000024`–`000040` (17); earlier IDs + video URL **currently unavailable** |
| Alpine Spruce (plain) | `alpine_spruce` | `mb-as-` | intake complete (22/22); species_id `spruce_european`; video URL pending |
| European Spruce | `european_spruce` | — | empty stub — **source currently unavailable** |

## Blocked / unavailable sources (2026-08-02)

Operator report: the following are **not available now**. Leave stubs/gaps; do not fabricate specimens or URLs.

1. 30yr red-cedar source video URL  
2. 30yr red-cedar catalog frames before `000024` (and any after `000040`)  
3. Plain Adirondack suite frames  
4. European spruce suite frames  
5. Adirondack torrefied gap `000002` (still unavailable)

### Red Cedar treatment discrimination

Same `species_id` (`cedar_western_red`). Do not pool:

| Axis | Plain suite | 30-year naturally dried |
|------|-------------|-------------------------|
| `treatment` | `plain` | `naturally_dried_30yr` |
| `species_cohort` | `red_cedar` | `red_cedar_30yr_naturally_dried` |
| Specimen prefix | `mb-rc-` | `mb-rc30-` |
| Analysis names (observed) | `CED-C-##` / `CED-W-##` | `CA-*` / `CA3-*` / `CA23-*` / `CA2-*` / `CA1-*` |
| Vendor label (typical) | `RED CEDAR` | `30-YEAR NATURALLY DRIED RED CEDAR` |

