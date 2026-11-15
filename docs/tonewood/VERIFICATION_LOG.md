# Tonewood Library — Verification Log

> **Started:** 2026-11-14 (TONEWOOD-VERIFY-001)
> **Scope:** the 16 documents in `docs/tonewood/`, checked against the repo's own data files and, for CITES, the official Species+ database.
> **Status:** tranche 1 done. The corrections below are applied. Everything under **Open issues** is still wrong or unverified and is **not** fixed yet.

## Why this log exists

A review of the 16 documents found estimated values printed as measurements, CIRAD figures that did not match the CIRAD file, wrong botanical identities and stale CITES statuses. Each correction below names the check that found it, so it can be re-run instead of taken on trust.

## Re-running the checks

From the repo root:

```bash
# C-01: regenerate the CIRAD high-density catalog from the CSV (deterministic)
python scripts/gen_cirad_high_density_catalog.py . docs/tonewood/tonewood_catalog_cirad_high_density.md

# C-01, C-03, C-04, C-05: every CIRAD D12 / N citation in docs/tonewood vs the CSV
python scripts/check_tonewood_cirad_citations.py        # expect: "0 mismatches", exit 0
```

C-02 (estimated Janka) is reproduced by computing `0.00355 × density^1.85` and comparing it with each Janka value. The formula is `janka_from_density` in `scripts/bulk_import_wood_species.py`.

---

## Corrections applied

### C-01 — CIRAD high-density catalog used each species' heaviest specimen

- **Found:** `tonewood_catalog_cirad_high_density.md` printed each taxon's *maximum* specimen D12 beside *averaged* Db and R%. Example: *Bocoa prouacensis* was shown at 1.31; its 11 CIRAD specimens range 1.15–1.31, mean 1.22.
- **Effect:** 217 taxa qualified at ≥0.95 g/cm³ by maximum, but only **157** by mean.
- **Fix:** regenerated the whole document with `scripts/gen_cirad_high_density_catalog.py`. All values are now means, with the range and N shown, and 65 single-specimen taxa are flagged.

### C-02 — Estimated Janka values presented as measured

- **Found:** the bulk species import fills Janka with a density regression, `Janka ≈ 0.00355 × density^1.85`. **422 of the 473** Janka values in `wood_species.json` equal that formula to within 3 lbf. The documents copied them into tables beside real test values.
- **Effect:** the hardest woods are badly understated. African Blackwood shows 1,960 in three documents but 3,670 in another, and "Buloke, hardest Australian" was contradicted by its own table.
- **Fix:** **148** table cells in 11 documents now carry the marker **ᵉ**, and each affected document has a header note explaining it. Values were *marked, not replaced*: replacing them needs a sourced measurement for each (see open issue O-01).
- **Limit:** detection needs density and Janka in the same table row. Formula values quoted in prose, or in tables without a density column, are not marked (examples: Padauk 731 in `tonewood_viability_emerging_species.md`, Guanacaste 470).

### C-03 — "1,740 species" and "172 American species"

- `tonewood_mahogany_alternatives_comprehensive.md`: "1,740 CIRAD species in 450–700 kg/m³" is the number of *specimens* in that band. By taxon mean it is **404 taxa** in **64 families**. Corrected.
- `tonewood_american_hardwoods_comprehensive.md`: "172 American species in the database" cannot be traced, because `wood_species.json` has no origin field. The guide itself names about 70 species. Corrected to "about 70".
- `tonewood_cites_alternatives_rosewood_ebony_range.md`: "1,255 entries / 300+ taxa" corrected to **368 taxa (1,311 specimens)** with mean D12 0.80–1.20, and the family subtotals recomputed.
- `README.md` index counts updated to match.

### C-04 — CITES-alternatives document: CIRAD rows matched none of 58

- **Found:** every one of the 58 D12/N rows in Parts II–III disagreed with the CSV.
  - D12 was mostly the taxon's maximum.
  - The N column matched neither CIRAD file. *Mora excelsa* was given N = 39 against 1 in the file; *Xanthomyrtus* "40 specimens" against 1.
  - *Parkia pendula* was listed at 0.93, but its heaviest specimen is 0.62.
  - Three taxa (*Diplotropis martiusii*, *Peltogyne pubescens*, *Bowdichia nitida*) are not in the density file at all.
- **Fix:** all rows recomputed as means with ranges. Rows that now fall outside their tier are flagged, not moved, and missing taxa are labelled. The "Bocoa is denser than African Blackwood" claim (1.22 vs 1.29) was corrected in four places.

### C-05 — Same CIRAD errors in other documents

`scripts/check_tonewood_cirad_citations.py --fix` corrected 65 further mismatches:

| Document | Corrections |
|---|---|
| `tonewood_comparison_extreme_density_glassy_character.md` | 17 |
| `tonewood_comparison_extreme_density_annotated.md` | 8 |
| `tonewood_mahogany_alternatives_comprehensive.md` | 12 (e.g. Utile N 39 → 9, *Khaya senegalensis* 0.69 → 0.76) |
| `tonewood_cites_alternatives_rosewood_ebony_range.md` | 28 in the summary tables |

Notes resting on the old maxima were rewritten: "ties African Blackwood", "Blackwood/Bloodwood confirmed", and the family summary copied from the old catalog. The checker now reports **0 mismatches**.

**Limit:** the checker reads single D12 values. Ranges such as "0.66–0.70" are not checked.

### C-06 — CITES status (new reference: `CITES_STATUS.md`)

Checked against Species+, the official CITES database (UNEP-WCMC), with IUCN categories from iucnredlist.org. Corrected:

- **Siamese rosewood** (*D. cochinchinensis*): Appendix **II**, not I (three places).
- **Sapele, Sipo, Kibaba** (*Entandrophragma*): **not CITES-listed**; EU Annex D only. Previously shown as "Appendix II" or "proposed at CoP20, buy before Nov 2025". The EU postponed the proposal to CoP21 (2028).
- **Kiaat, Chanfuta, Doussie** (African *Pterocarpus* / *Afzelia*): **Appendix II since 2023-02-23** (#17). Previously "not listed".
- **Khaya** and **African Padauk**: Appendix II (#17). Previously "not listed / no CITES burden" in the Mugavu and viability documents.
- **Ipe** and **Cumaru**: Appendix II since 2024-11-25. They were recommended as CITES-free; they are now flagged.
- **Dalbergia instrument exemption** stated precisely (annotation #15: finished instruments, parts and accessories; not *D. nigra*). IUCN categories relabelled as IUCN, not CITES.
- *Pterocarpus erinaceus* is Kosso / African rosewood, not "African Padauk" (*P. soyauxii*).

### C-07 — Botanical identity errors

| Corrected statement | What it should say |
|---|---|
| "Okoume, Ayous, Abachi — same species: *Aucoumea klaineana*" | Ayous/Abachi/Obeche is *Triplochiton scleroxylon*, a different tree. |
| Okoume "D12 0.49–0.50, 50+ specimens, lighter than basswood" | CIRAD has **13** specimens, mean 0.44, range 0.32–0.55; comparable to basswood (415). |
| "Sweet Chestnut" filed as American chestnut | *Castanea sativa* is European; reclaimed "wormy chestnut" is American (*C. dentata*). |
| *Maclura tinctoria* "Fustic/Osage" | Fustic. Osage orange is *M. pomifera*. |
| "Malaysian Blackwood = *Acacia melanoxylon*" | No source supports this, and every "Malaysian" value is the Tasmanian record. Flagged as unverified in two documents. |
| "Only American *Diospyros* / *Morus* / wild Meliaceae" | *D. texana*, *M. microphylla* and *Swietenia mahagoni* (south Florida) are also native. |
| "Bald Cypress is the quintessential/traditional flamenco wood" | The traditional flamenco wood is *Cupressus sempervirens*. Fixed in two documents. |

### C-08 — Internal contradictions and stale text

- **Contradictions corrected:**
  - Hickory "denser than Pau Ferro" (800–835 vs 880).
  - "White oak lighter than red oak" (770 vs 700 in the same table).
  - Mahogany "strongest MOR" (mesquite is 117 vs 98.4).
  - "Of the four" in a five-species comparison.
- **Mukulungu:**
  - "Class 5 durability — marine-rated" corrected; in EN 350, class 5 means *not durable*.
  - "Highest density in this comparison" corrected (Blackwood is 1,270, Panga Panga 880).
- **Angolan data-gaps table:** said MOE was missing for six species that have MOE in `wood_species.json`. Rewritten, with sound speed computed as c = √(E/ρ).
- **Cypress brief:**
  - The "FPL-grade" claim is withdrawn; Monterey and Mediterranean cypress are not in FPL.
  - The unexplained "3384–4413" figure is removed.
  - The radiation-ratio gap was overstated ("11–13", "a third lower"); corrected to 10.7–13 and 20–35%.
- Typos fixed ("silica inclite", "calcium carbite") and leftover AI-session text removed from the Mugavu document.

---

## Open issues (not fixed in this tranche)

| ID | Issue | What fixing it needs |
|---|---|---|
| **O-01** | 148 marked ᵉ Janka values (and 422 in `wood_species.json`) still have no measured replacement | A sourced measurement per species (Wood Database, FPL, ITTO) with attribution |
| **O-02** | No per-value source attribution in any of the 16 documents, which the CLAUDE.md wood data policy requires | Rebuild the tables with source columns; start with the most-used species |
| **O-03** | MOE values in `wood_species.json` carry no `_source` field (e.g. Iroko 10.9, Wenge 14.75), so computed sound speeds inherit the gap | Attribute or re-source each MOE |
| **O-04** | Shrinkage values in `tonewood_comparison_acoustic_top_woods.md` (e.g. W. Red Cedar 4.43/7.69) look inconsistent with FPL; the angolan document estimates shrinkage from SG (†), which the policy forbids | Check against FPL Table 5-3 / Wood Database; remove the † estimates |
| **O-05** | Two overlapping documents, `extreme_density_annotated` and `extreme_density_glassy_character`, give different thresholds, tiers and bridge rankings; `blackwoods_african_vs_malaysian` repeats a section of the acacia document | **Owner decision:** merge, or keep one as canonical |
| **O-06** | Value disagreements between documents and the JSON: Ovangkol (825/1,360 vs 810/1,890), Guanacaste Janka (470 vs 276), Granadillo MOE (~14.5 vs null), Padauk Janka (731 vs 1,725) | Resolve each against a source |
| **O-07** | Sitka and Engelmann radiation ratios are "estimated from similar species" in two documents | Use published MOE values with attribution |
| **O-08** | No measured damping data for any species; tone descriptions are unsourced forum and builder quotes | Literature damping values (e.g. CIRAD vibration studies) or the `luthier-acoustics-data` measurements |
| **O-09** | Bagtikan CITES status not checked | One Species+ lookup |

## Findings outside `docs/tonewood/` (reported, not changed here)

- `wood_species.json`:
  - 422 of 473 Janka values are the density regression (see C-02). Its `_meta` says estimates are "flagged with _note fields", but these Janka values are not flagged.
  - **31 species** contain mojibake: double-encoded UTF-8 such as "â€”" for an em dash. Examples: `cedar_western_red`, `cocobolo`, `koa`, `rosewood_brazilian`, `walnut_black`.
  - Kiaat, Doussie, Sipo (as an ID), Banga Wanga, Mugavu, Kibaba, Longhi and Mukulungu are absent, although the documents discuss them.
- `luthier_tonewood_reference.json` has drifted from `wood_species.json` (e.g. Khaya is `mahogany_african` vs `khaya`; its Khaya Janka is still 830).
- `SOURCES.md` and `WOOD_SPECIES_REFERENCE.md` describe 472 species and predate the per-field `_source` schema.
- Measured spruce/cedar specimen data (MB Sound, 114 specimens) lives in the `luthier-acoustics-data` repo (`mb-sound/v1.0.0`). It was moved out of this repo on 2026-08-25 (commit `2403c71b`).
