# FPL GTR-282 species tables (Wood Handbook, 2021)

`fpl_gtr282_species_tables.csv` holds the per-species rows of five tables from:

> Forest Products Laboratory. 2021. *Wood Handbook — Wood as an Engineering Material.* General Technical Report FPL-GTR-282. Madison, WI: USDA Forest Service, Forest Products Laboratory.

It is a US federal government work and in the public domain.

| Table | Chapter | Content | Species |
|---|---|---|---|
| 4-3 | 4, Moisture Relations and Physical Properties (Glass & Zelinka) | Shrinkage of domestic woods, green to ovendry: radial, tangential, volumetric % | 115 |
| 4-4 | 4 | Shrinkage of some woods imported into the United States (+ origin AF/AM/AS) | 82 |
| 5-3a | 5, Mechanical Properties (Senalik & Farber) | Strength properties of woods grown in the United States, metric | 113 |
| 5-4a | 5 | Mechanical properties of Canadian woods imported into the United States, metric | 27 |
| 5-5a | 5 | Mechanical properties of other imported woods, metric (+ sample origin) | 75 |

## Source files

| File | URL | SHA-256 |
|---|---|---|
| Chapter 4 | https://research.fs.usda.gov/download/treesearch/62243.pdf | `8459aad8c6643e635f1d0c443f9e796e82ef8d650920d89838932bef8cd24880` |
| Chapter 5 | https://research.fs.usda.gov/download/treesearch/62244.pdf | `724c99666ad364c4bd13022b5b1db09bb391166eace37bd920fee1f8d2d23204` |

The PDFs are not committed. To regenerate (needs `pdfplumber`, which is not a repo dependency):

```bash
python scripts/extract_fpl_gtr282_tables.py <dir holding 62243.pdf and 62244.pdf> docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv
```

The script rebuilds rows from word coordinates. Plain-text extraction loses the indentation that makes "Sitka" a member of the "Spruce" group, and layout mode shifts values between rows (it gave balsa a specific gravity of 0.42; the table says 0.16). Every row must have exactly its table's cell count, or the script reports it and exits 1. It also exits 1, before extracting, if either PDF's SHA-256 differs from the table above, and after extracting if any output cell contains a control character (an earlier version wrote `\x01` into the Mora and Cuangare names; see `docs/tonewood/VERIFICATION_LOG.md` C-12).

## CSV format

Long format: `table, species, condition, property, value, origin`.

- `species` is FPL's name with group headers joined: `Spruce, Sitka`, `Oak, white, Live`, `Hickory, true, Mockernut`. Botanical names are as FPL prints them, including its spelling variants (5-5a has "Llomba" where 4-4 has "Ilomba").
- `condition` is `green`, `12pct` (12% moisture content), or `green_to_ovendry` for shrinkage.
- Units are in the property name: `moe_mpa`, `mor_kpa`, `side_hardness_n`, `shrink_tangential_pct`, ... Blank FPL cells ("—") are omitted.

## Read before using these numbers

- **Side hardness is the Janka test** (load perpendicular to grain), in newtons. 1 lbf = 4.448 N.
- **Specific gravity basis:** ovendry weight and volume green or at 12% MC (footnote b). This is not density at 12% MC, so do not compare it directly with CIRAD's D12.
- **MOE** comes from a center-loaded beam with a 14:1 span-to-depth ratio. FPL says it "can be increased by 10%" to correct for shear deflection (footnote c). The CSV has the printed value, without the 10%.
- **Source labels.** Cite the exact table: `FPL_GTR282_table_4-3`, `_4-4` (shrinkage), `_5-3a`, `_5-4a`, `_5-5a` (mechanical). The old label `FPL_GTR282_table_5-3` named the strength table but was used for shrinkage; it is deprecated (CLAUDE.md, 2026-11-15), not redefined.

## Validation

The metric tables were cross-checked against FPL's own inch-pound twins (5-3b, 5-4b, 5-5b), extracted with the same script. 1,397 MOE, MOR, side hardness and specific gravity values were checked; 1,390 agree within conversion and rounding. The 7 that disagree are inconsistencies in FPL itself, or rounding at small values, not extraction errors:

| Table | Species | Value | Metric | Inch-pound |
|---|---|---|---|---|
| 5-3a | Birch, yellow | green side hardness | 3,600 N | 780 lbf (3,470 N) |
| 5-3a | Western redcedar | green side hardness | 1,200 N | 260 lbf (1,157 N) |
| 5-3a | Subalpine fir | green side hardness | 1,200 N | 260 lbf (1,157 N) |
| 5-3a | Western white pine | green side hardness | 1,200 N | 260 lbf (1,157 N) |
| 5-3a | Western white pine | 12% specific gravity | 0.35 | 0.38 |
| 5-3a | Red spruce | green side hardness | 1,600 N | 340 lbf (1,512 N) |
| 5-3a | Red spruce | 12% side hardness | 2,200 N | 530 lbf (2,357 N) |
