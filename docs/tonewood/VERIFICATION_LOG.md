# Tonewood Library — Verification Log

> **Started:** 2026-11-14 (TONEWOOD-VERIFY-001)
> **Scope:** the 16 documents in `docs/tonewood/`, checked against the repo's own data files and, for CITES, the official Species+ database.
> **Status:** tranche 1 (C-01 to C-10) and tranche 2 (C-11, its review fixes C-12, and the source-label ruling C-13, 2026-11-15) done; C-14 (sourced shrinkage for 10 species in `wood_species.json`, CIRAD Tropix added as a source) and C-15 (Tropix shrinkage for 10 species that had none, 2026-11-17) and C-16 (shrinkage for 377 more species, FPL or Wood Database, 2026-11-19) applied; C-17 (shrinkage source ranking removed, owner decision 2026-11-20) recorded. The corrections below are applied. Of the rows under **Open issues**, O-01, O-02, O-03, the Granadillo remainder of O-06, O-08, O-11, and O-12 are still unresolved. O-04, O-05, O-07, O-09, and O-10 are resolved and stay in that table. O-05's remaining blackwoods/acacia duplication was reconciled on 2026-11-16 (TONEWOOD-BLACKWOODS-RECONCILIATION-003): documentation structure only. The measurements were not revalidated.

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
python scripts/check_tonewood_fpl_values.py --summary   # expect: "119 aliases resolve; 640 cells checked, 0 mismatches", exit 0

# C-11: regenerate the FPL reference CSV (needs the two FPL PDFs and pdfplumber; see docs/reference/fpl-gtr282/README.md).
# Refuses PDFs whose SHA-256 differs from the documented one; exits 1 on any parse problem or control character.
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

### C-09 — Canonical extreme-density document (resolves the extreme-density part of O-05)

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

**New check.** `scripts/check_tonewood_fpl_values.py` maps 119 document species names to FPL rows (unambiguous identities only; every one must resolve, C-12) and checks every density, SG, Janka, MOE, MOR, shrinkage, sound-speed, impedance, E/ρ and radiation-ratio cell for them. The check is strict: such a cell must equal the FPL value at display precision, so it can be attributed to FPL. After the C-12 fixes, 640 cells are checked with 0 mismatches; 9 cells that hold a range are listed rather than compared. About 1,300 property cells belong to species FPL does not cover and are not checked.

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

### C-12 — Review fixes to tranche 2 (2026-11-15)

A review of PR #486 found that the C-11 checker's "0 mismatches" did not cover everything it claimed to:

- **Extractor wrote a control character into two species names.** The cleanup `re.sub(r"([a-z])spp\.", …)` had the byte `\x01` where the back-reference `\1` belonged. It dropped the last letter of the genus and inserted the byte: `Mora (Mor\x01 spp.)`, `Cuangare (Dialyanther\x01 spp.)` — 24 CSV rows. Fixed and regenerated; the extractor now rejects any output cell containing a control character. No value changed, only those two names.
- **The checker silently skipped every Mora cell.** The `mora` alias named `Mora (Mora spp.)`, which was not in the corrupted CSV, and a missing row read as "no FPL data" rather than as an error. With the CSV fixed, 18 Mora cells in 3 documents mismatched: density 1,015 → 985 kg/m³, MOE 19.24 → 20.4 GPa, MOR 138.6 → 152.4 MPa, SG 1.01 → 0.88, Janka 1,295 ᵉ (an estimate) → 2,293 lbf / 10,200 N, and the derived values. The rosewood-range document attributed 1,015 to CIRAD, but its own CIRAD rows (1.05 for 1 *M. excelsa*, mean 1.02 for 10 *M. paraensis*) do not give 1,015 either. Mora rows were re-sorted where tables are ordered by density or MOE. Now every alias must name a row that exists in the CSV (with radial and tangential shrinkage where a shrinkage table is named), or the checker exits 1 before checking anything.
- **Range cells were dropped silently.** A cell like `400–450 kg/m³` was neither checked nor counted. They are now counted and listed with whether the FPL value falls inside. 12 were found for mapped species; 3 excluded the FPL value (Andiroba 650–700 twice, FPL 645; Khaya 550–690, FPL 497) and were replaced. The other 9 contain the FPL value and are left as ranges.
- **`--fix` exited 0 without re-checking.** It now checks again after rewriting and exits 1 if any mismatch remains.
- **The extractor did not check its input.** It printed the PDFs' SHA-256 but read whatever files it was given. It now refuses PDFs whose hash differs from the documented one.
- **Also corrected:** the rosewood-range document called Greenheart (22.4 GPa) "highest in database" in a table where Wamara, Bulletwood and Snakewood are stiffer.

Re-run result: 119 aliases resolve; 640 cells checked, 0 mismatches; 9 range cells not compared (all contain the FPL value); 1,299 property cells skipped (species not mapped to FPL).

### C-13 — FPL source labels made table-specific (owner ruling, 2026-11-15; resolves O-10)

The data policy's single label `FPL_GTR282_table_5-3` named Table 5-3 (strength) but was prescribed for shrinkage, which GTR-282 gives in Tables 4-3 and 4-4. Per the owner's ruling it is replaced by `FPL_GTR282_table_4-3`, `_4-4`, `_5-3a`, `_5-4a` and `_5-5a` in `CLAUDE.md` and `docs/process/wood_species_update_template.md`. The old label is listed as deprecated, not redefined. No record in `wood_species.json` or any code uses it (`git grep`), so nothing needed re-attribution. The CLAUDE.md example is now traceable: sugar maple, Table 4-3 p. 4-8 (4.8 / 9.9) and Table 5-3a G₁₂ 0.63 → 706 kg/m³ (it said 705 and "p.5-7").

**Follow-up correction (2026-11-15).** C-13 as merged (#486) left the template's example shrinkage at 5.0 / 3.1 under the new `FPL_GTR282_table_4-3` label, though Table 4-3 has no such row: a false provenance claim. The template example is now a complete sugar maple record from FPL, matching the CLAUDE.md example: shrinkage 9.9 / 4.8 (Table 4-3, p. 4-8); density 706 kg/m³, G₁₂ 0.63, MOE 12.6 GPa, MOR 109.0 MPa, Janka 6,400 N / 1,439 lbf (Table 5-3a). It had mixed 745 kg/m³, 13.07 GPa, 126.7 MPa and 1,725 lbf attributed to the Wood Database, from an unnamed species, and its Janka and SG had no source field. Neither example shows volumetric shrinkage, so nothing derived needed recomputing. `scripts/ci/test_policy_fpl_examples.py` (run in Core CI) now compares every FPL-attributed value in both examples with the extracted table, fails on a label that is deprecated, invalid, of the wrong table kind, or attached to nothing checkable, and has a negative control for the old 5.0 / 3.1 values.

### Reconciliation — O-05 blackwoods duplication (TONEWOOD-BLACKWOODS-RECONCILIATION-003, 2026-11-16)

Owner ruling 2026-11-15, carried out here. Both documents stay. `tonewood_comparison_acacia_family_blackwoods_koa.md` is the shared Acacia-family reference. `tonewood_comparison_blackwoods_african_vs_malaysian.md` is the focused African-versus-Malaysian comparison. Each links to the other.

Two sentences in the Acacia document contradicted the C-07 caution in that same document: the nomenclature key insight said Tasmanian, Malaysian, and Australian Blackwood are all *Acacia melanoxylon*, and The "Malaysian Blackwood" Question said Malaysian Blackwood is simply *Acacia melanoxylon* grown in Malaysia. Those sentences were withdrawn. They were not replaced with a new identification. The short African-versus-Malaysian ranking table in that section was removed; the same figures already stood in the focused comparison, and the family document's own boundary figures were left as printed. No density, Janka, MOE, MOR, shrinkage, or derived figure was rewritten in either document. No measurement was independently revalidated.

On owner review (2026-11-16) the trade-name identity wording was corrected in both documents: "botanically unrelated species" became different genera in the same family, Fabaceae, whose trade names do not establish species equivalence; Australian Blackwood's "Same species, regional variant" was removed and both unresolved trade names are "provisionally mapped" to *A. melanoxylon*; and every comparison-table cell naming the Malaysian column's species, genus or family now carries the reference-record caveat in the cell. No figure changed.

This resolves the duplication left open under O-05 after C-09. It does not scientifically validate the figures, the Malaysian trade name, or any purchasing, regulatory, engineering, or manufacturing use. Record: `docs/investigations/tonewood-verification-003/BLACKWOODS_RECONCILIATION.md`. Check: `scripts/ci/test_tonewood_blackwoods_reconciliation.py`. FPL re-check: 640 cells, 0 mismatches; skipped unmapped cells 1,299 → 1,295 because that removed table had four unmapped cells. CIRAD citations: 0 mismatches.

### C-14 — Shrinkage in `wood_species.json` for 10 species; CIRAD Tropix added as a source (owner approval, 2026-11-15)

**New source.** CIRAD–ITTO **Tropix** publishes one PDF sheet per species (313 sheets in the 2026 index) with average values, including **total tangential and radial shrinkage** — the breakdown the CIRAD density database lacks. Its terms (tropix-online.com/legal) put content under CC BY but prohibit "any reuse or extraction, in whole or in part, of the site's databases", and the sheets say "All rights reserved". Owner ruling: use it **one sheet at a time, cited per value**, never bulk-extracted. It is now priority 2 for tangential/radial shrinkage in CLAUDE.md (after FPL, before the Wood Database), with source label `CIRAD_Tropix` plus the sheet URL and "last update" date per field.

**Scope.** The 10 species that already held a shrinkage value and have a Tropix sheet under the same name. Nine sheets cover one species; Wenge's covers a two-species trade group (see Findings). Policy puts FPL first, and FPL Tables 4-3/4-4 cover 8 of them, so those 8 now carry FPL values (same rows as the C-11 checker's aliases); Tropix supplies only the 2 FPL lacks. Each sheet was read from its own PDF; every St/Sr pair agrees with the sheet's printed St/Sr ratio.

| Species (id) | Before: T / R (source) | FPL row | FPL T / R | Tropix T / R (sheet date) | Now |
|---|---|---|---|---|---|
| `bubinga` | 8.2 / 6.0 (Wood Database) | 4-4 Bubinga (*Guibourtia* spp.) | 8.4 / 5.8 | 7.9 / 5.5 (2024-03-11) | FPL |
| `jatoba` | 8.86 / 5.01 (**none**) | 4-4 Courbaril (*Hymenaea courbaril*) | 8.5 / 4.5 | 7.5 / 3.9 (2025-10-22) | FPL |
| `ipe` | 9.61 / 5.61 (**none**) | 4-4 Ipe (*Tabebuia* spp.) | 8.0 / 6.6 | 6.4 / 5.1 (2025-07-22) | FPL |
| `khaya` | 5.8 / 3.5 (Wood Database) | 4-4 Mahogany, African (*Khaya* spp.) | 4.5 / 2.5 | 5.5 / 3.7 (2025-05-16) | FPL |
| `ovangkol` | 8.3 / 4.3 (Wood Database) | 4-4 Ovangkol (*Guibourtia ehie*; FPL prints *Guibourta*, sic) | 8.2 / 4.5 | 8.0 / 3.9 (2024-04-24) | FPL |
| `purpleheart` | 9.61 / 5.61 (**none**) | 4-4 Purpleheart (*Peltogyne* spp.) | 6.1 / 3.2 | 6.7 / 4.4 (2024-01-17) | FPL |
| `cedar_western_red` | 5.0 / 2.4 (Wood Database) | 4-3 Cedar, Western redcedar | 5.0 / 2.4 | 5.5 / 2.2 (2024-01-15) | FPL (re-attributed; values unchanged) |
| `douglas_fir` | 7.3 / 4.5, vol. 11.6 (Wood Database) | 4-3 Douglas-fir, Coast | 7.6 / 4.8, vol. 12.4 | 6.9 / 4.7 (2023-10-30) | FPL, incl. volumetric |
| `african_padauk` | 5.0 / 3.1 (Wood Database, one combined `_shrinkage_source` key) | — | — | 5.0 / 3.2 (2024-07-30) | Tropix; volumetric 7.9 kept, attributed per field to the Wood Database (re-read 2026-11-15) |
| `wenge` | 9.03 / 5.23 (**none**) | — | — | 9.1 / 5.9 (2024-10-30) | Tropix |

Findings:

- **Ipe and purpleheart held identical placeholder values**: 9.61 / 5.61 shrinkage and 16.7 GPa MOE. Their real shrinkage differs (8.0 / 6.6 vs 6.1 / 3.2). The shared MOE is still in the JSON (O-03); FPL Table 5-5a gives purpleheart 15.7 GPa at 12% MC.
- **Khaya disagrees across sources**: FPL 4.5 / 2.5, Tropix 5.5 / 3.7, Wood Database 5.8 / 3.5. FPL is used because policy puts it first; it is the low outlier, so movement calculations for Khaya are now the least conservative of the three. Known limitation, disclosed for owner acceptance.
- **Wenge's sheet covers two species** (*Millettia laurentii* and *M. stuhlmannii*, panga panga). The JSON record names *M. laurentii* alone; the Tropix values are for the trade group, applied to a single-species record. Known limitation, accepted for this change.
- **Douglas-fir**: FPL has three rows (Coast, Interior north, Interior west). The JSON has one generic `douglas_fir` record that does not say which variety it represents; the **Coast** row is used for it, as in the C-11 checker. Known limitation: Interior material may shrink differently. The old 7.3 / 4.5 matched none of the three rows.
- Only shrinkage fields, their provenance fields, and the derived `tr_ratio` changed (scripted check: every other field of all 473 records is identical to `origin/main`). `tr_ratio` is tangential ÷ radial, has no source field, and no code reads it; it was recomputed for the three changed records that carry it, because the new values had made it stale: `khaya` 1.66 → 1.80, `douglas_fir` 1.6 → 1.58, `african_padauk` 1.6 → 1.56. `wood_movement_calc.get_shrinkage_data` reads the new values; no test pins any of these species.

After this change: 440 species have no tangential shrinkage, 8 are FPL, 2 Tropix, 14 Wood Database, and **9 remain unsourced** (`spruce_european`, `cedar_spanish`, `cherry_black`, `cypress_bald`, `oak_red`, `oak_white`, `spruce_white`, `tasmanian_blackwood`, `zebrawood`) — see O-12.

### C-15 — Tropix shrinkage for 10 species that had none (batch 2, 2026-11-17)

**Scope.** Ten species with **no** shrinkage value, a Tropix sheet that names the record's species in its botanical list, and no row in FPL Tables 4-3/4-4 (so Tropix is the highest-priority source that covers them). Same method as C-14: one sheet at a time, read from its own PDF, cited per value (`CIRAD_Tropix` + sheet URL + "last update" date, per field). Each St/Sr pair agrees with the sheet's printed St/Sr ratio within its rounding. Only tangential and radial values are added; Tropix gives no total volumetric shrinkage, so none is added.

| Species (id) | Record's species | Tropix sheet (botanical names listed) | Sheet date | T / R |
|---|---|---|---|---|
| `cumaru` | *Dipteryx odorata* | CUMARU / TONKA (*Dipteryx* group: *alata*, *micrantha*, *odorata*, *polyphylla*, *D.* p.p.) | 2025-08-11 | 7.7 / 5.5 |
| `makore` | *Tieghmella heckelii* (sic) | MAKORE (*Tieghemella heckelii*) | 2023-05-22 | 7.5 / 5.8 |
| `bloodwood` | *Brosimum rubescens* | MUIRAPIRANGA / BLOODWOOD (*B. rubescens*) | 2025-05-16 | 5.9 / 4.1 |
| `yellowheart` | *Euxylophora paraensis* | YELLOWHEART (*E. paraensis*) | 2025-05-16 | 6.5 / 5.7 |
| `tatajuba` | *Bagassa guianensis* | TATAJUBA (*B. guianensis*) | 2025-05-16 | 5.2 / 3.7 |
| `mango` | *Mangifera indica* | MANGO / MACHANG (*Mangifera* group: *foetida*, *indica*, *laurina*, *M.* p.p.) | 2026-03-30 | 6.1 / 4.2 |
| `cerejeira` | *Amburana cearensis* | CEREJEIRA (*A. cearensis*) | 2024-06-04 | 4.5 / 2.4 |
| `garapa` | *Apuleia leiocarpa* | GARAPA (*A. leiocarpa*) | 2024-05-15 | 7.5 / 4.2 |
| `timborana` | *Pseudopiptadenia suaveolens* | TIMBORANA (*P. suaveolens*, *P. psilostachya* and synonyms) | 2024-08-12 | 6.9 / 4.6 |
| `sucupira` | *Bowdichia nitida* | SUCUPIRA (trade group: *Bowdichia nitida*, *Diplotropis martiusii*, *D. purpurea*) | 2024-08-01 | 7.0 / 4.9 |

Findings:

- **Snakewood excluded — botanical mismatch.** The record names *Brosimum guianense*; Tropix's SNAKEWOOD sheet is *Zygia racemosa* (syn. *Marmaroxylon racemosum*), a different genus and family. Not applied. Sucupira took its place.
- **Trade-group sheets** (same limitation as Wenge in C-14): `cumaru` (five *Dipteryx* names), `mango` (three *Mangifera* species), `sucupira` (two genera) and `timborana` (two *Pseudopiptadenia* species) get group averages applied to single-species records.
- **Sucupira and FPL.** FPL 4-4 has a "Sucupira" row, but for *Diplotropis purpurea* (7.0 / 4.6), not the record's *Bowdichia nitida*, so FPL does not cover this species and Tropix is used. The Tropix group includes *D. purpurea*; its tangential value matches FPL's and its radial value is 0.3 higher.
- **Makore spelling.** The JSON's `scientific_name` is *Tieghmella heckelii*; the accepted spelling is *Tieghemella* (as on the Tropix sheet). Reported, not changed here.
- **Behaviour change.** These 10 species had no shrinkage, so `wood_movement_calc` rejected them with `ValueError`; it now returns results for them (supported species 47 → 57). Scripted check: the only change in all 473 records is that these 10 gained the 8 shrinkage and provenance fields; nothing else changed.

After this change: 430 species have no tangential shrinkage, 8 are FPL, 12 Tropix, 14 Wood Database, and 9 remain unsourced (O-12).

### C-16 — Shrinkage for 377 species that had none: FPL for 126, Wood Database for 251 (batch 3, 2026-11-19)

**Owner ruling (2026-11-19).** The Wood Database is an approved source with the same credibility as the others. None of these sources measured the boards a builder will use. Owner GO: fill the empty shrinkage values from it, each cited to its own species page, with the source recorded per field.

**Locating values.** An undated, unlicensed third-party bulk copy of wood-database.com (584 species; not committed to this repo) was used as an index of which page to cite and what it says.
- **Fidelity.** A seeded random sample of 30 rows was compared with the live pages: all 30 matched numerically on tangential and radial shrinkage.
- **Known faults of the copy:**
  - It drops the site's "~" (approximate) marker.
  - It leaves out values the site has. Cocobolo is blank in the copy but has a full line on its page, and 20 of the 30 sampled rows lack a volumetric value their page shows.
- **Consequences:**
  - Only tangential and radial values were imported; no volumetric.
  - Every row whose values were whole numbers (18) was re-read from its live page. 13 are marked approximate there, and keyaki's values are for a subspecies; these carry `_shrinkage_<dir>_approximate: true` (and a `_shrinkage_caveat` for keyaki).
  - **Limit of that re-read (found in PR #499 review, 2026-11-21):** the "~" marker is not confined to whole numbers. `black_palm` (*Borassus flabellifer*) is "Radial: ~5.5%, Tangential: ~5.5%" on its live page (T/R 1.0 there, as is usual for a palm), and now carries the approximate flag too (14 records). The other 232 non-whole-number Wood Database rows were not re-read for "~", so a missing flag does not mean the value is exact (O-12). The numbers themselves are unaffected: the 30-row sample matched numerically.
  - Blanks in the copy were treated as unknown, not as absent.

**Matching records to pages.**
- 369 records matched through their own `_source_url`, which already cites that page; 12 more matched an unambiguous identical scientific name.
- Four were **excluded** because the page describes a different species from the record:
  - `narra`: record *Pterocarpus dalbergioides*, page *P. indicus*
  - `partridgewood`: record *Caesalpinia granadillo*, page *Andira inermis*
  - `tiete_rosewood`: record *Goniorrhachis marginata*, page *Guibourtia hymenaeifolia*
  - `red_palm`: record *Cyrtostachys renda*, page *Cocos nucifera*
- `english_elm` (record *Ulmus minor*, page *U. procera*) is included; *U. procera* is commonly treated within *U. minor*.

**FPL first where FPL has the species.** 126 of the matched species have an FPL Table 4-3/4-4 row with both values. CLAUDE.md puts FPL first and the rows are already in `docs/reference/fpl-gtr282/`, so those 126 take FPL values (`_shrinkage_<dir>_source` + `_table_row`). 101 matched by name; a second pass found 25 filed under FPL group names (e.g. "Oak, white, Overcup", "Hickory, true, Shellbark", "Magnolia, Cucumbertree", "Cedar, Yellow" = Alaskan yellow cedar).
- Iroko, teak and merbau are among them, as are the domestic ashes, maples, pines, firs, birches, elms and others.
- Row choices follow name and synonym: *Chlorophora* = *Milicia*, *Ocotea rodiaei* = *Chlorocardium rodiei*, *Phoebe porosa* = *Ocotea porosa*, Azobe = ekki, Benge = mutenye, *Cybistax* = *Roseodendron* (primavera), Sucupira (*D. purpurea*) = tatabu.
- `bulletwood` uses FPL's "Bulletwood" row, not its "Balata" row.
- Kept on the Wood Database: `gray_birch` (FPL gives radial only), `coast_redwood` (FPL has separate old- and young-growth rows; the record does not say which).

**FPL vs Wood Database on the 126 shared species: the cross-check the owner asked about.**
- Agreement:
  - Both values are identical in 98 of 126.
  - Tangential is within 0.5 points in 119 of 126 and radial in 122 of 126.
  - Tangential differs by more than 15% in only 4 species.
- **Caveat:** identical values mostly mean the Wood Database reproduces FPL, so this is not 98 independent confirmations.

The seven species differing by more than 0.5 points:

| Species | FPL T / R | Wood Database T / R |
|---|---|---|
| `jarrah` | 11.0 / 7.7 | 9.4 / 6.3 |
| `balsa` | 7.6 / 3.0 | 6.0 / 2.3 |
| `iroko` | 3.8 / 2.8 | 4.8 / 3.3 |
| `peroba_rosa` | 6.4 / 3.8 | 7.4 / 4.2 |
| `okoume` | 6.1 / 4.1 | 7.1 / 4.6 |
| `kempas` | 7.4 / 6.0 | 6.7 / 5.1 |
| `greenheart` | 9.6 / 8.8 | 8.9 / 8.2 |

Findings:

- **Tropix priority not applied to 20 species.** These Wood Database-filled species also have a Tropix sheet, which CLAUDE.md ranks above the Wood Database: abura, araracanga, balau, beli, bosse, etimoe, freijo, guanacaste, idigbo, izombe, kosipo, lati, macacauba, mansonia, moabi, ohia, preciosa, pyinma, utile and wamara. They were filled under the owner's GO without reading those sheets. This was a deviation from the written priority at the time; the owner removed the priority on 2026-11-20 (C-17), so the values stand.
- **Duplicate records of one species** (`alder`/`red_alder`, `maple_soft`/`red_maple`, `pine_eastern_white`/`eastern_white_pine`) receive the same values. The duplication itself is reported, not fixed here.
- **Behaviour change.** `wood_movement_calc` now returns results for these 377 species instead of raising `ValueError` (supported species 57 → 434). Scripted check against the parent commit: the only change in all 473 records is that these 377 gained shrinkage and provenance fields; nothing else changed.
- **Test range widened.** `test_shrinkage_coefficients_realistic` required 3–12% tangential. Published FPL values exceed that (Pacific madrone 12.4, shellbark hickory 12.6, overcup oak 12.7, karri 12.4), as do Wood Database values for muninga (2.8) and mountain ash (13.0). The bound is now 1.5–15%, which still catches unit and decimal-place errors.

After this change: 53 species have no tangential shrinkage, 134 are FPL (95 Table 4-3, 39 Table 4-4), 12 Tropix, 265 Wood Database, and 9 remain unsourced.

### C-17 — Shrinkage sources: ranking removed (owner decision, 2026-11-20)

**Owner decision.** Following the 2026-11-19 ruling that the Wood Database is as credible as FPL and Tropix, the source ranking for tangential/radial shrinkage is dropped. CLAUDE.md and `docs/process/wood_species_update_template.md` now list FPL Tables 4-3/4-4, CIRAD Tropix and the Wood Database as approved sources of equal standing.
- Any approved source may supply a value. A sourced value is not replaced only because another approved source also covers the species.
- Where approved sources differ by more than 0.5 percentage points on the same value, every source's value is recorded in this log. Recorded so far: khaya (C-14: FPL 4.5 / 2.5, Tropix 5.5 / 3.7, Wood Database 5.8 / 3.5) and the seven FPL vs Wood Database pairs in C-16.
- `unknown_legacy` is not an approved source; those values stay flagged (O-12).
- Unchanged: the per-value citation requirement, the Tropix one-sheet-at-a-time rule, and the density source order.
- Data: no value changed. The 20 species in C-16 that have a Tropix sheet keep their Wood Database values. Their Tropix sheets were not read, so whether they disagree is unknown.
- Also fixed in CLAUDE.md: the `wood_database_meier` line said to put the URL in `_source_url`; shrinkage values record it in `_shrinkage_<dir>_url` (as C-14 to C-16 do), and `_source_url` stays the record-level page.

## Open issues

| ID | Issue | What fixing it needs |
|---|---|---|
| **O-01** | 32 ᵉ Janka values replaced by FPL measurements (C-11); 138 ᵉ markers remain (species FPL lacks), and 422 regression values remain in `wood_species.json` | Wood Database or ITTO measurements for the species FPL lacks |
| **O-02** | Per-value attribution: values for FPL-covered species are now attributable to FPL through the C-11 checker, but no document has source columns, and most values for other species are unsourced | Source columns, starting with the most-used species |
| **O-03** | MOE values in `wood_species.json` still carry no `_source` field; the documents now use FPL MOE for FPL species, so they disagree with the JSON (e.g. Honduran mahogany 10.3 vs 11.97) | Attribute or re-source each MOE in the JSON |
| **O-04** | ~~Shrinkage in the top-woods document; † estimates in the Angolan document~~ — resolved by C-11 | — |
| **O-05** | ~~Overlapping extreme-density documents~~ — resolved by C-09. ~~Blackwoods/acacia duplication~~ — resolved as duplication only by TONEWOOD-BLACKWOODS-RECONCILIATION-003 (2026-11-16). The Acacia-family document is the shared reference; the blackwoods document is the focused comparison. This does not scientifically validate the figures or the Malaysian trade name, and it grants no purchasing, regulatory, engineering, or manufacturing authority. Record: `docs/investigations/tonewood-verification-003/BLACKWOODS_RECONCILIATION.md` | — |
| **O-06** | Resolved by C-11 except **Granadillo** (*Platymiscium yucatanum*) MOE ~14.5 (and its 925 kg/m³ / 2,790 lbf): no source found in FPL or the Wood Database | A published value for *P. yucatanum* |
| **O-07** | ~~Sitka and Engelmann estimated radiation ratios~~ — resolved by C-11 | — |
| **O-08** | No measured damping data for any species; tone descriptions are unsourced forum and builder quotes | Literature damping values (e.g. CIRAD vibration studies) or the `luthier-acoustics-data` measurements |
| **O-09** | ~~Bagtikan CITES status~~ — resolved by C-11 (not CITES- or EU-listed) | — |
| **O-10** | ~~CLAUDE.md source label `FPL_GTR282_table_5-3` names the strength table~~ — resolved by C-13 (table-specific labels; old label deprecated) | — |
| **O-11** | Specific gravity basis is unstated in every document. FPL species now show G₁₂; other species' SG has an unknown basis, sometimes in the same row | State the basis per value, or drop SG where density is given |
| **O-12** | Shrinkage in `wood_species.json` (C-14 to C-17):<br>• 9 values still unsourced; at least 6 of those species are in FPL Tables 4-3/4-4 (black cherry, red and white oak, white spruce, bald cypress, Spanish cedar).<br>• 53 species have no shrinkage value, including the 4 excluded for species mismatch in C-16 and `snakewood` (C-15).<br>• ~~20 species take Wood Database values although a Tropix sheet exists (C-16)~~ — resolved by C-17 (no source ranking; values stand).<br>• `_shrinkage_<dir>_approximate` is complete only for the 18 whole-number Wood Database rows and `black_palm`; the other 232 Wood Database rows were not checked for the site's "~" marker (C-16). | FPL for the 6 unsourced FPL species; resolve the record identities of the 5 mismatched species |

## Findings outside `docs/tonewood/` (reported, not changed here)

- `wood_species.json`:
  - Disagrees with FPL GTR-282 for the species in C-11, e.g. Honduran mahogany MOE 11.97 (FPL 10.3), Guanacaste Janka 276 (Wood Database 470), Ovangkol Janka 1,890 (Wood Database 1,330).
  - 422 of 473 Janka values are the density regression (see C-02). Its `_meta` says estimates are "flagged with _note fields", but these Janka values are not flagged.
  - **31 species** contain mojibake: double-encoded UTF-8 such as "â€”" for an em dash. Examples: `cedar_western_red`, `cocobolo`, `koa`, `rosewood_brazilian`, `walnut_black`.
  - Kiaat, Doussie, Sipo (as an ID), Banga Wanga, Mugavu, Kibaba, Longhi and Mukulungu are absent, although the documents discuss them.
- `luthier_tonewood_reference.json` has drifted from `wood_species.json` (e.g. Khaya is `mahogany_african` vs `khaya`; its Khaya Janka is still 830).
- `SOURCES.md` and `WOOD_SPECIES_REFERENCE.md` describe 472 species and predate the per-field `_source` schema.
- Measured spruce/cedar specimen data (MB Sound, 114 specimens) lives in the `luthier-acoustics-data` repo (`mb-sound/v1.0.0`). It was moved out of this repo on 2026-08-25 (commit `2403c71b`).
