# Tonewood Reference Library

Comparative analyses of wood species for lutherie applications.

> **Verification status (2026-11-14).** These documents are research notes, not a verified dataset. A review found estimated values presented as measured, misquoted CIRAD figures, wrong botanical identities and stale CITES statuses. Corrections made so far, the checks behind them and the open issues are in [VERIFICATION_LOG.md](VERIFICATION_LOG.md). Read it before citing any number from this folder.

---

## Catalogs

| Document | Species | Focus |
|----------|:-------:|-------|
| [tonewood_catalog_cirad_high_density.md](tonewood_catalog_cirad_high_density.md) | 157 | CIRAD database — all taxa with mean D12 ≥0.95 g/cm³ (regenerated from the CSV) |
| [tonewood_cites_alternatives_rosewood_ebony_range.md](tonewood_cites_alternatives_rosewood_ebony_range.md) | ~120 | CITES-free substitutes (800–1,200 kg/m³) |
| [tonewood_mahogany_alternatives_comprehensive.md](tonewood_mahogany_alternatives_comprehensive.md) | ~53 | **Deep-dive mahogany alternatives (450–700 kg/m³)** — CIRAD + web research |
| [tonewood_american_hardwoods_comprehensive.md](tonewood_american_hardwoods_comprehensive.md) | ~70 | **Domestic species guide** — all density tiers, zero imports |
| [tonewood_viability_emerging_species.md](tonewood_viability_emerging_species.md) | — | Emerging/exploratory species assessment |

---

## Species Comparisons

### Density Classes

| Document | Focus |
|----------|-------|
| [tonewood_comparison_extreme_density_glassy_character.md](tonewood_comparison_extreme_density_glassy_character.md) | **Canonical** — 65 species ≥950 kg/m³: tiers, regional summary, acoustics, recommendations, CIRAD cross-reference |
| [tonewood_comparison_extreme_density_annotated.md](tonewood_comparison_extreme_density_annotated.md) | *Secondary* — kept for thermal and CNC-machining tables only; its rankings are superseded |
| [tonewood_comparison_blackwoods_african_vs_malaysian.md](tonewood_comparison_blackwoods_african_vs_malaysian.md) | African (1,270) vs "Malaysian" (640) — glassy vs warm; Malaysian identity unverified |

### Families

| Document | Focus |
|----------|-------|
| [tonewood_comparison_acacia_family_blackwoods_koa.md](tonewood_comparison_acacia_family_blackwoods_koa.md) | Acacia + Albizia (Koa, Blackwoods, Monkeypod, Mugavu) |
| [tonewood_comparison_mahogany_koa_family.md](tonewood_comparison_mahogany_koa_family.md) | Mahogany and Koa family |
| [tonewood_comparison_rosewoods_ebonies_mesquite.md](tonewood_comparison_rosewoods_ebonies_mesquite.md) | Rosewoods + Ebonies + Honey Mesquite |

### Applications

| Document | Focus |
|----------|-------|
| [tonewood_comparison_acoustic_top_woods.md](tonewood_comparison_acoustic_top_woods.md) | Soundboard species (spruce, cedar, etc.) |
| [tonewood_comparison_cherry_mahogany_walnut_mesquite.md](tonewood_comparison_cherry_mahogany_walnut_mesquite.md) | Body woods — warm-mid cluster |

### Regional

| Document | Focus |
|----------|-------|
| [tonewood_comparison_african_hardwoods_angolan_species.md](tonewood_comparison_african_hardwoods_angolan_species.md) | Angolan species survey |
| [tonewood_comparison_african_hardwoods_mugavu.md](tonewood_comparison_african_hardwoods_mugavu.md) | Mugavu as mahogany alternative |

---

## Briefs

| Document | Focus |
|----------|-------|
| [cypress_back_sides_brief.md](cypress_back_sides_brief.md) | Bald Cypress as a back/sides wood for cuatros, mandolins and lutes |

---

## Data Sources

- `wood_species.json` v4.0.0 (473 species; 422 of its Janka values are the density regression, not measurements — see VERIFICATION_LOG.md C-02)
- `luthier_tonewood_reference.json` v1.0.0
- CIRAD Wood Density Database (Vieilledent et al. 2018)
- The Wood Database (Eric Meier)

## Tools

- `scripts/gen_cirad_high_density_catalog.py` — regenerates the CIRAD high-density catalog from the CSV
- `scripts/check_tonewood_cirad_citations.py` — checks every CIRAD D12/N citation in this folder against the CSV (`--fix` rewrites mismatches)
