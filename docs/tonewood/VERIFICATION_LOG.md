# Tonewood Library — Verification Log

> **Started:** 2026-11-14 (TONEWOOD-VERIFY-001)
> **Scope:** the 16 documents in `docs/tonewood/`, checked against the repo's own data files and, for CITES, the official Species+ database.
> **Status:** tranche 1 (C-01 to C-10) and tranche 2 (C-11, 2026-11-15) done. The corrections below are applied. Everything under **Open issues** is still wrong or unverified and is **not** fixed yet.

## Why this log exists

A review of the 16 documents found estimated values printed as measurements, CIRAD figures that did not match the CIRAD file, wrong botanical identities and stale CITES statuses. Each correction below names the check that found it, so it can be re-run instead of taken on trust.

## Re-running the checks

From the repo root:

```bash
# C-01: regenerate the CIRAD high-density catalog from the CSV (deterministic)
python scripts/gen_cirad_high_density_catalog.py . docs/tonewood/tonewood_catalog_cirad_high_density.md

# C-01, C-03, C-04, C-05: every CIRAD D12 / N citation in docs/tonewood vs the CSV
python scripts/check_tonewood_cirad_citations.py        # expect: "0 mismatches", exit 0

# C-11: density, SG, Janka, MOE, MOR, shrinkage and derived values vs FPL GTR-282 (strict)
python scripts/check_tonewood_fpl_values.py --summary   # expect: "0 mismatches", exit 0

# C-11: regenerate the FPL reference CSV (needs the two FPL PDFs and pdfplumber; see docs/reference/fpl-gtr282/README.md)
python scripts/extract_fpl_gtr282_tables.py <pdf dir> docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv
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

### C-09 — Canonical extreme-density document (resolves O-05)

Owner decision 2026-11-14: keep one document as canonical rather than merge. `tonewood_comparison_extreme_density_glassy_character.md` is **canonical**: it covers more species (65 from 950 kg/m³ vs 27 from 1,000) and has the regional summary and fuller CIRAD section. `tonewood_comparison_extreme_density_annotated.md` is **secondary**: kept for its thermal and CNC-machining tables, with its tiers, rankings and recommendations marked superseded. Both docs carry a status banner, and the README index lists them that way. Ipe recommendations in both now carry its CITES Appendix II status (since 2024-11-25).

---

### C-10 — Review fixes to this tranche (2026-11-15)

A review of PR #484 found four defects, three of them introduced or left behind by the corrections above:

- **Mugavu given Khaya's CITES listing.** The C-06 edit to `tonewood_comparison_african_hardwoods_mugavu.md` replaced a correct "Not CITES-listed" bullet for Mugavu (*Albizia coriaria*) with African *Khaya*'s Appendix II (#17) text. The same document (summary and properties tables) and the Angolan document's status table already said "not listed". Reverted.
- **"Acquire stock before CoP20"** survived in the Kibaba notes of `tonewood_comparison_african_hardwoods_angolan_species.md`, right under the corrected status line. Removed; the sources table now notes that CoP20 had no *Entandrophragma* proposal.
- **Mora "39 CIRAD specimens"** (two places in `tonewood_cites_alternatives_rosewood_ebony_range.md`). 39 is the S (fibre saturation) value of the single *Mora excelsa* row, not a count. CIRAD holds 1 *M. excelsa* and 10 *M. paraensis* specimens.
- **README overstated the checker.** It said the script checks "every" D12/N citation. It checks only table rows with an italic binomial and a single D12 value, plus "N specimens" written exactly that way, which is why the Mora count got through. The README now states the limit.

Re-check: `grep -rn "39 CIRAD\|before CoP20" docs/tonewood` finds only this log and `CITES_STATUS.md`; no other prose "N CIRAD specimens" claim remains; the checker still reports 0 mismatches.

### C-11 — FPL GTR-282 values for the species it covers (tranche 2, 2026-11-15)

**New reference.** `docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv` holds FPL GTR-282 (2021) Tables 4-3, 4-4 (shrinkage), 5-3a, 5-4a and 5-5a (mechanical, metric), extracted by `scripts/extract_fpl_gtr282_tables.py` with source-PDF SHA-256s. It was cross-checked against FPL's own inch-pound tables: 1,390 of 1,397 values agree; the 7 others are FPL's own inconsistencies (listed in its README).

**New check.** `scripts/check_tonewood_fpl_values.py` maps about 100 document species names to FPL rows (unambiguous identities only) and checks every density, SG, Janka, MOE, MOR, shrinkage, sound-speed, impedance, E/ρ and radiation-ratio cell for them. The check is strict: such a cell must equal the FPL value at display precision, so it can be attributed to FPL. 619 cells are checked; 0 mismatch. About 1,300 property cells belong to species FPL does not cover and are not checked.

**Corrections.** `--fix` rewrote 418 cells in 12 documents. The acoustic top-woods document was corrected by hand first and agrees with the checker. Prose that quoted the old numbers was rewritten by hand; a scan of non-table lines for every replaced number then found only unchanged values and thresholds. Conventions: density is at 12% MC by FPL Eq. 4-14 (ρ = 1000·G₁₂·1.12; for Table 5-5a species, G₁₂ from basic SG by Eqs. 4-9 and 4-11); Janka is FPL side hardness; MOE is not shear-corrected (FPL footnote c).

Findings, by the size of the change:

- **Janka estimates replaced by measurements (O-01, partly).** 32 ᵉ regression values are now FPL side hardness: the hickories (pignut 902 → 2,136 lbf), the red and white oaks (pin oak 617 → 1,506), ashes, birches, elms, tupelos, honey locust, lignum vitae (1,932 → 4,496), bulletwood (1,452 → 3,192), greenheart (1,283 → 2,360), Alaskan yellow cedar (343 → 585). American sycamore was 410 lbf without a ᵉ mark; FPL gives 764.
- **Rankings that changed.** Lignum vitae (4,496), not Katalox or Ipe, is the hardest wood in the extreme-density documents. East Indian rosewood is harder than Brazilian (3,170 vs 2,720 lbf). Greenheart is not the stiffest wood (Wamara, bulletwood and snakewood rank above it). On E/ρ, Douglas-fir moves from last to second among top woods and Honduran mahogany from second to second-lowest.
- **Honduran mahogany** (5 documents): MOE 11.97 → 10.3 GPa, MOR 98.4 → 79.3 MPa, density 545 → 529, shrinkage 4.41/8.41 → 3.0/4.1. It is no longer the stiffest wood in the mahogany/koa and cherry/walnut comparisons.
- **Unsourced "contraction" rows** (e.g. Western Red Cedar 4.43/7.69 against FPL 2.4/5.0) replaced by FPL shrinkage (O-04).
- **Sitka and Engelmann MOE** filled from FPL (10.8 and 8.9 GPa). Engelmann's 5,090 m/s, "estimated from similar species", is 4,765 (O-07). The cypress brief's uncited "published" radiation ratios for both are now computed.
- **SG-based shrinkage estimates removed** (O-04): 10 † cells in the Angolan summary table and 15 † rows in its species profiles (Banga Wanga, Mugavu, Longhi white and red, Mukulungu).
- **O-06 resolved except Granadillo.** Ovangkol Janka is 1,330 lbf (Wood Database; FPL has none); the documents had 1,890 and 1,360. Guanacaste 470 lbf (Wood Database) is right; the JSON's 276 is wrong. African padauk 731 → 1,710 lbf (Wood Database; 731 was the unflagged regression value). Granadillo (*Platymiscium yucatanum*) MOE ~14.5 has no source: neither FPL nor the Wood Database has that species.
- **O-09 resolved.** Bagtikan (*Parashorea malaanonan*) is not in Species+, so it is neither CITES- nor EU-listed. The same lookup found an EU Annex D listing, effective 2026-06-29 (Reg. (EU) 2026/1383), of seven *Shorea* s.l. genera (meranti, lauan, balau, and *Pentacme contorta*, which shares Bagtikan's "white lauan / white seraya" trade name). It is added to `CITES_STATUS.md`.
- **Stale CITES text found on the way.** The Mugavu document still called Khaya "sustainable … no restrictions" in three places, and listed Utile as "Unknown". Both corrected.

Not done: specific gravity and density for species FPL does not cover, and FPL values in `wood_species.json` (still reported, not changed here).

## Open issues

| ID | Issue | What fixing it needs |
|---|---|---|
| **O-01** | 32 ᵉ Janka values replaced by FPL measurements (C-11); 138 ᵉ markers remain (species FPL lacks), and 422 regression values remain in `wood_species.json` | Wood Database or ITTO measurements for the species FPL lacks |
| **O-02** | Per-value attribution: values for FPL-covered species are now attributable to FPL through the C-11 checker, but no document has source columns, and most values for other species are unsourced | Source columns, starting with the most-used species |
| **O-03** | MOE values in `wood_species.json` still carry no `_source` field; the documents now use FPL MOE for FPL species, so they disagree with the JSON (e.g. Honduran mahogany 10.3 vs 11.97) | Attribute or re-source each MOE in the JSON |
| **O-04** | ~~Shrinkage in the top-woods document; † estimates in the Angolan document~~ — resolved by C-11 | — |
| **O-05** | ~~Overlapping extreme-density documents~~ — resolved by C-09. Still open: `blackwoods_african_vs_malaysian` repeats a section of the acacia document | Owner decision on the blackwoods document |
| **O-06** | Resolved by C-11 except **Granadillo** (*Platymiscium yucatanum*) MOE ~14.5 (and its 925 kg/m³ / 2,790 lbf): no source found in FPL or the Wood Database | A published value for *P. yucatanum* |
| **O-07** | ~~Sitka and Engelmann estimated radiation ratios~~ — resolved by C-11 | — |
| **O-08** | No measured damping data for any species; tone descriptions are unsourced forum and builder quotes | Literature damping values (e.g. CIRAD vibration studies) or the `luthier-acoustics-data` measurements |
| **O-09** | ~~Bagtikan CITES status~~ — resolved by C-11 (not CITES- or EU-listed) | — |
| **O-10** | The CLAUDE.md source label `FPL_GTR282_table_5-3` names the strength table. In GTR-282 the shrinkage tables are 4-3 and 4-4 | Owner decision: correct the label in the policy |
| **O-11** | Specific gravity basis is unstated in every document. FPL species now show G₁₂; other species' SG has an unknown basis, sometimes in the same row | State the basis per value, or drop SG where density is given |

## Findings outside `docs/tonewood/` (reported, not changed here)

- `wood_species.json`:
  - Disagrees with FPL GTR-282 for the species in C-11, e.g. Honduran mahogany MOE 11.97 (FPL 10.3), Guanacaste Janka 276 (Wood Database 470), Ovangkol Janka 1,890 (Wood Database 1,330).
  - 422 of 473 Janka values are the density regression (see C-02). Its `_meta` says estimates are "flagged with _note fields", but these Janka values are not flagged.
  - **31 species** contain mojibake: double-encoded UTF-8 such as "â€”" for an em dash. Examples: `cedar_western_red`, `cocobolo`, `koa`, `rosewood_brazilian`, `walnut_black`.
  - Kiaat, Doussie, Sipo (as an ID), Banga Wanga, Mugavu, Kibaba, Longhi and Mukulungu are absent, although the documents discuss them.
- `luthier_tonewood_reference.json` has drifted from `wood_species.json` (e.g. Khaya is `mahogany_african` vs `khaya`; its Khaya Janka is still 830).
- `SOURCES.md` and `WOOD_SPECIES_REFERENCE.md` describe 472 species and predate the per-field `_source` schema.
- Measured spruce/cedar specimen data (MB Sound, 114 specimens) lives in the `luthier-acoustics-data` repo (`mb-sound/v1.0.0`). It was moved out of this repo on 2026-08-25 (commit `2403c71b`).
