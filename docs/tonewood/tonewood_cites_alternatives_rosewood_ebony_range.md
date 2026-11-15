# CITES-Free Alternatives: Rosewood–Ebony Range (800–1,200 kg/m³)

> **Sources:** CIRAD Wood Density Database (368 taxa with mean D12 0.80–1.20; 1,311 specimens in band), Web research 2025-2026, `wood_species.json`
> **Generated:** 2026-06-22
> **Purpose:** Comprehensive substitution guide beyond "the usual suspects"

> **ᵉ Estimated Janka (added 2026-11-14).** Values marked ᵉ equal the bulk-import regression `Janka ≈ 0.00355 × density^1.85` (`scripts/bulk_import_wood_species.py`), not a hardness test. They rise smoothly with density, so they cannot rank species of similar density, and they can be far below published measurements for the hardest woods. Treat them as placeholders. See `VERIFICATION_LOG.md` (C-02).

> **FPL GTR-282 values (corrected 2026-11-15, `VERIFICATION_LOG.md` C-11).** For species that FPL GTR-282 (2021) covers, density (at 12% MC), specific gravity (G₁₂), Janka, MOE, MOR and shrinkage in the tables are now FPL values, and sound speed, impedance and E/ρ are recomputed from them. `scripts/check_tonewood_fpl_values.py` lists the species mapped and checks every such cell. Values for other species are unchanged and mostly unsourced.

This document draws on the **368 CIRAD taxa** whose mean density falls in the rosewood-to-ebony band (1,311 specimens). Goes far beyond Pau Ferro and Katalox.

---

## Part I: CITES-Restricted Species (What We're Replacing)

### Dalbergia Genus (True Rosewoods) — Appendix II, except *D. nigra* (Appendix I)

Statuses corrected 2026-11-14 against Species+ — see [CITES_STATUS.md](CITES_STATUS.md).

| Species | Trade Name | Density | Status |
|---------|-----------|:-------:|--------|
| *Dalbergia nigra* | Brazilian Rosewood | 944 | **Appendix I** — effectively banned |
| *Dalbergia latifolia* | East Indian Rosewood | 885 | Appendix II — regulated |
| *Dalbergia retusa* | Cocobolo | 1,095 | Appendix II — restricted |
| *Dalbergia melanoxylon* | African Blackwood | 1,270 | Appendix II — restricted |
| *Dalbergia cochinchinensis* | Siamese Rosewood | 1,035 | Appendix II — not I; annotation routes it to #4, likely no instrument exemption |
| *Dalbergia baronii* | Madagascar Rosewood | 935 | Appendix II |
| *Dalbergia cearensis* | Kingwood/Violetwood | 1,200 | Appendix II |
| *Dalbergia decipularis* | Brazilian Tulipwood | 970 | Appendix II |
| *Dalbergia spruceana* | Jacaranda do Pará | 1,040 | Appendix II |

**Note:** Since 2019-11-26 (annotation #15), finished musical instruments, finished instrument parts and finished accessories of Appendix II *Dalbergia* are exempt. Raw wood, blanks and sawn sets still need permits. *D. nigra* (Appendix I) has no exemption.

### Other Restricted Species (CITES or IUCN — the two are different)

| Species | Trade Name | Density | Status |
|---------|-----------|:-------:|--------|
| *Diospyros crassiflora* | African Ebony | 1,030 | IUCN only, not checked (not CITES; CITES lists only Madagascar *Diospyros*) |
| *Diospyros celebica* | Macassar Ebony | 1,120 | IUCN Vulnerable, not checked; not CITES |
| *Guibourtia demeusei* | Bubinga | 890 | Appendix II (2017); instruments exempt under #15 |
| *Millettia laurentii* | Wenge | 870 | IUCN Endangered (1998); not CITES |
| *Pterocarpus erinaceus* | Kosso / African rosewood (not African padauk, *P. soyauxii*) | 745 | Appendix II (#17); African padauk is also App II since 2023 |

---

## Part II: CIRAD Deep Dive — The Leguminosae Family

**99 CIRAD taxa with a mean D12 of 0.80–1.20 (482 specimens in band)** — the rosewood family extends far beyond Dalbergia.

> **Corrected 2026-11-14 (`VERIFICATION_LOG.md` C-04).** All D12 and N values in Parts II–III were recomputed from `docs/reference/cirad-density/Cirad-wood-density-database.csv` as the mean over all specimens. The earlier values matched none of the 58 rows: D12 was mostly each taxon's heaviest specimen, and the N column matched neither CIRAD file. Rows now outside their tier are flagged rather than moved.

### Tier 1: Highest Density (D12 > 1.10)

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.22 | 11 | *Bocoa prouacensis* | Boco | French Guiana | Slightly lighter than African Blackwood (CIRAD mean 1.29) (range 1.15–1.31) |
| 1.20 | 1 | *Swartzia ingaefolia* | — | Brazil | Swartzia genus unexplored (single specimen) |
| 1.07 | 9 | *Dipteryx odorata* | **Cumaru/Tonka** | French Guiana | Known; very hard (range 0.99–1.18) — *below this tier on mean D12* |
| 1.07 | 3 | *Guibourtia demeusei* | Bubinga | Gabon | CITES II, instruments exempt #15 (range 0.92–1.15) — *below this tier on mean D12* |
| 1.02 | 2 | *Hymenaea sp* | Jatoba relatives | Brazil | Multiple species (range 0.90–1.15) — *below this tier on mean D12* |
| 1.10 | 3 | *Dipteryx punctata* | Cumaru variant | French Guiana | Less known than D. odorata (range 1.02–1.14) — *below this tier on mean D12* |
| 1.09 | 4 | *Hymenaea parvifolia* | — | Brazil | Unexplored Jatoba relative (range 1.06–1.13) — *below this tier on mean D12* |
| 1.06 | 5 | *Oddoniodendron normandii* | — | Gabon | **Completely unexplored** (range 0.96–1.13) — *below this tier on mean D12* |
| 1.11 | 2 | *Xanthocercis madagascariensis* | — | Madagascar | Unexplored (range 1.10–1.13) |
| 1.07 | 2 | *Dinizia excelsa* | Angelim Vermelho | Brazil | Known timber (range 1.03–1.11) — *below this tier on mean D12* |
| 1.08 | 6 | *Librevillea klainei* | — | Gabon | Unexplored (range 1.02–1.12) — *below this tier on mean D12* |
| 1.20 | 10 | *Swartzia panacoco* | **Wamara** | French Guiana | High MOE potential (range 1.10–1.29) |

### Tier 2: Core Rosewood Range (D12 0.95–1.10)

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.00 | 11 | *Zygia racemosa* | Angelim Rajado | French Guiana | Figured; underexplored (range 0.81–1.10) |
| 1.06 | 4 | *Dalbergia sp* | Madagascar Rosewood | Madagascar | CITES (range 0.98–1.16) |
| 1.09 | 1 | *Dialium cochinchinense* | Keranji | Vietnam | Asian option (single specimen) |
| 0.86 | 18 | *Hymenaea courbaril* | **Jatoba** | Brazil | Well-known (range 0.78–1.09) — *below this tier on mean D12* |
| 1.02 | 10 | *Mora paraensis* | Mora | Brazil | Underexplored (range 0.98–1.09) |
| 1.08 | 1 | *Dialium bipindense* | — | Gabon | African Dialium (single specimen) |
| 0.91 | 10 | *Cylicodiscus gabunensis* | Okan | Gabon | Dense; durable (range 0.77–1.06) — *below this tier on mean D12* |
| 1.05 | 1 | *Mora excelsa* | **Mora** | Trinidad | (single specimen) |
| 1.05 | 1 | *Prosopis africana* | African Mesquite | Guinea | The densest Prosopis (single specimen) |
| 1.04 | 1 | *Dalbergia spruceana* | Jacaranda do Pará | Brazil | CITES Dalbergia (single specimen) |
| 0.89 | 5 | *Andira coriacea* | Angelim da Mata | French Guiana | Andira genus (range 0.74–1.03) — *below this tier on mean D12* |
| 0.95 | 3 | *Peltogyne sp* | **Purpleheart** | French Guiana | Well-known (range 0.88–1.02) |

### Tier 3: Lower Rosewood Range (D12 0.85–0.95)

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 0.95 | 1 | *Myroxylon balsamum* | **Santos Mahogany** | Peru | Balsam of Peru (single specimen) |
| — | 0 | *Diplotropis martiusii* | Sucupira Preta | Brazil | Dark; dense; **not in CIRAD density file** |
| 0.54 | 8 | *Parkia pendula* | Faveira | Brazil | Large tree (range 0.49–0.62) — *below this tier on mean D12* |
| — | 0 | *Peltogyne pubescens* | Purpleheart variant | French Guiana | Multiple species; **not in CIRAD density file** |
| 0.78 | 1 | *Hymenolobium petraeum* | Angelim Pedra | Brazil | "Stone Angelim" (single specimen) — *below this tier on mean D12* |
| — | 0 | *Bowdichia nitida* | Sucupira | French Guiana | Classic timber; **not in CIRAD density file** |

---

## Part III: Non-Legume Families

### Sapotaceae (Bulletwood Family) — 35 taxa in band

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.09 | 20 | *Manilkara bidentata* | **Bulletwood/Balata** | French Guiana | very dense (range 1.00–1.19) |
| 1.20 | 4 | *Chrysophyllum prieurii* | — | French Guiana | Unexplored (range 0.99–1.33) |
| 1.11 | 11 | *Manilkara huberi* | Maçaranduba | Brazil | Dense; red (range 0.93–1.16) |
| 1.14 | 1 | *Manilkara dissecta* | — | New Caledonia | Pacific option (single specimen) |
| 1.10 | 4 | *Letestua durissima* | — | Congo | "Durissima" = very hard (range 1.08–1.12) |
| 1.10 | 1 | *Planchonella microphylla* | — | New Caledonia | Pacific (single specimen) |
| 0.96 | 10 | *Pradosia cochlearia* | — | French Guiana | Underexplored (range 0.88–1.10) |
| 1.03 | 4 | *Faucherea parvifolia* | — | Madagascar | Multiple Faucherea species (range 0.97–1.09) |

### Lauraceae (Laurel Family) — 12 taxa in band

Aromatic woods with potential unique tonal properties:

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.05 | 15 | *Licaria canella* | Canela | Brazil | Cinnamon-scented (range 0.62–1.23) |
| 1.12 | 3 | *Aniba canellila* | Casca Preciosa | Brazil | Aromatic (range 1.01–1.22) |
| 1.06 | 1 | *Licaria sp* | — | French Guiana | Multiple species (single specimen) |
| 1.02 | 1 | *Misanteca aritu* | — | Brazil | Unexplored (single specimen) |
| 0.71 | 20 | *Ocotea porosa* | **Imbuia** | Brazil | Classic Brazilian wood (range 0.61–0.88) |

### Bignoniaceae (Ipe/Lapacho Family) — 5 Taxa

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.11 | 7 | *Handroanthus serratifolius* | **Ipe/Lapacho** | French Guiana | Extreme hardness (range 1.02–1.18) |
| 1.14 | 1 | *Phyllarthron articulatum* | — | Madagascar | Unexplored (single specimen) |
| 1.02 | 12 | *Tabebuia sp* | Lapacho variants | Brazil | Multiple species (range 0.90–1.19) |
| 0.93 | 3 | *Handroanthus heptaphyllus* | Pink Ipe | Paraguay | Lighter variant (range 0.88–0.98) |

### Moraceae (Mulberry/Fig Family) — 4 taxa in band

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.10 | 7 | *Brosimum rubescens* | **Bloodwood** | Brazil | Vivid red; known (range 0.97–1.29) |
| 0.84 | 4 | *Morus mesozygia* | African Mulberry | Ivory Coast | Underexplored (range 0.77–0.92) |
| 0.80 | 6 | *Bagassa guianensis* | Tatajuba | French Guiana | Yellow; figured (range 0.70–0.88) |
| 0.88 | 1 | *Maclura tinctoria* | Fustic (not Osage orange, *M. pomifera*) | Paraguay | Dye wood (single specimen) |

### Myrtaceae (Eucalyptus Family) — 30 taxa in band

Australian and plantation options:

| D12 | N | Taxa | Trade Name | Origin | Notes |
|:---:|:-:|------|-----------|--------|-------|
| 1.08 | 3 | *Eucalyptus paniculata* | Grey Ironbark | Burundi (planted) | Very dense eucalypt (range 1.05–1.13) |
| 1.10 | 1 | *Xanthomyrtus hienghenensis* | — | New Caledonia | Pacific endemic (single specimen) |
| 0.99 | 5 | *Corymbia citriodora* | Lemon-Scented Gum | Madagascar | Aromatic (range 0.84–1.07) |
| 0.99 | 6 | *Eucalyptus microcorys* | Tallowwood | Madagascar | Dense (range 0.91–1.04) |
| 1.01 | 1 | *Pimenta racemosa* | Bay Rum Tree | Guadeloupe | Aromatic (single specimen) |
| 0.99 | 3 | *Arillastrum gummiferum* | — | New Caledonia | Endemic (range 0.97–1.00) |
| 0.90 | 8 | *Corymbia maculata* | Spotted Gum | Madagascar | Known timber (range 0.79–0.98) |

---

## Part IV: Web Research — Emerging & Validated Alternatives

### Established CITES-Free Substitutes

| Species | Density | Janka | Character | Status |
|---------|:-------:|:-----:|-----------|--------|
| **Pau Ferro** | 880 | 2,030 | "As close to rosewood as possible without being Dalbergia" | **Primary substitute** |
| **Katalox** | 1,050 | 3,650 | Bright, bell-like — hardest non-ebony | Ebony substitute |
| **Jatoba** | 861 | 2,360 | Warm, solid; between maple and rosewood | Budget rosewood |
| **Chechen** | 880 | 994 ᵉ | "Caribbean Rosewood" — regal color | Figured alternative |
| **Bocote** | 850 | 2,200 | Bold figure; balanced tone | Decorative |
| **Ziricote** | 815 | 1,900 | "Brazilian looks with Macassar overtones" | Premium figured |
| **Granadillo** | 925 | 2,790 | Bright, responsive; exceptional voice separation | Limited supply |

### Synthetic/Engineered Options

| Material | Description | Use |
|----------|-------------|-----|
| **Richlite** | Recycled paper + resin; greyish layers when carved | Fretboards |
| **Rocklite** | Wood pulp + resin; designed to match ebony properties | Fretboards, bridges |
| **Ebanol** | Dyed beech composite | Budget fretboards |

**Key difference:** Rocklite is specifically designed for instruments; Richlite is a general composite.

### African Alternatives (Non-Dalbergia)

| Species | Density | Notes |
|---------|:-------:|-------|
| **Panga Panga** | 870 | Wenge cousin; dark enough for ebony substitute |
| **Mopane** | 1,075 | Replacing African Blackwood for woodwinds |
| **Zebrawood** | 750 | Dramatic figure; popular fretboard |
| **Camelthorn** | 1,200+ | Namibian; extremely dense |
| **Okan** | 1,060 | *Cylicodiscus gabunensis*; underexplored |

### South American Alternatives

| Species | Density | Notes |
|---------|:-------:|-------|
| **Macacauba** | 950 | "Unique sound" — bright colors; backs/sides |
| **Goncalo Alves (Tigerwood)** | 1001 | Between rosewood and Koa tonally |
| **Curupay** | 1,025 | "Patagonian Rosewood" — NOT true rosewood |
| **Mora** | 1,015 | CIRAD: 1 *M. excelsa* + 10 *M. paraensis* specimens ("39" was the S column, corrected 2026-11-15, C-10); consistent |
| **Angelim Vermelho** | 1,070 | *Dinizia excelsa*; known timber |
| **Sucupira** | 920 | Dark; traditional |
| **Wamara** | 1,080 | *Swartzia panacoco*; highest MOE potential |
| **Imbuia** | 660 | *Ocotea porosa*; classic Brazilian walnut |

### Australian Alternatives

| Species | Density | Notes |
|---------|:-------:|-------|
| **Australian Blackwood** | 640 | "Punchy bottom, mid/high of mahogany" — Koa comparison |
| **Jarrah** | 845 | "As nice as ebony, better than rosewood" for durability |
| **Merbau** | 830 | Warm, rich |
| **Spotted Gum** | 940 | Dense eucalypt |
| **Grey Ironbark** | 1,130 | Extremely dense |
| **Gidgee** | 1,150 | Dense Acacia |
| **Australian Buloke** | 1,085 | Hardest Australian wood |

### Asian Alternatives

| Species | Density | Notes |
|---------|:-------:|-------|
| **Keranji** | 1,090 | *Dialium cochinchinense*; Vietnamese |
| **Rengas** | 900 | Malaysian; allergenic (use caution) |
| **Pyinkado** | 1,000 | Burmese ironwood |

---

## Part V: Regional Deep Dives

### Madagascar — The Forgotten Source

CIRAD documents numerous Madagascar endemics:

| D12 | Taxa | Notes |
|:---:|------|-------|
| 1.13 | *Xanthocercis madagascariensis* | Leguminosae; unexplored |
| 1.03 | *Faucherea parvifolia* | Sapotaceae |
| 1.09 | *Mimusops sp* | Sapotaceae |
| 0.84 | *Ravensara sp* | Lauraceae; aromatic |
| 0.83 | *Cryptocarya louvelii* | Lauraceae |

**Caution:** Madagascar faces severe deforestation; any sourcing requires sustainability verification.

### New Caledonia — Pacific Endemics

| D12 | Taxa | Family | Notes |
|:---:|------|--------|-------|
| 1.14 | *Manilkara dissecta* | Sapotaceae | Dense |
| 1.10 | *Xanthomyrtus hienghenensis* | Myrtaceae | 1 specimen |
| 1.10 | *Planchonella microphylla* | Sapotaceae | |
| 1.00 | *Arillastrum gummiferum* | Myrtaceae | Endemic |
| 0.93 | *Storckiella pancheri* | Leguminosae | |

### French Guiana — The Research Hotspot

Most-sampled region in CIRAD for this density range:

| D12 | Taxa | Trade Name |
|:---:|------|-----------|
| 1.22 | *Bocoa prouacensis* | Boco |
| 1.09 | *Manilkara bidentata* | Bulletwood |
| 1.11 | *Handroanthus serratifolius* | Ipe |
| 1.05 | *Licaria canella* | Canela |
| 1.10 | *Dipteryx punctata* | Cumaru |
| 1.20 | *Swartzia panacoco* | Wamara |

---

## Part VI: Substitution Matrices

### For Brazilian Rosewood (Back/Sides)

| Priority | Species | Density | Why |
|:--------:|---------|:-------:|-----|
| 1 | **Ziricote** | 815 | "Brazilian looks with depth of tone" |
| 2 | **Pau Ferro** | 880 | Industry standard |
| 3 | **Cocobolo** | 1,095 | *(if CITES II acceptable)* |
| 4 | **Granadillo** | 925 | Exceptional voice separation |
| 5 | **Macacauba** | 950 | Unique bright sound |
| 6 | **Australian Blackwood** | 640 | Different character but proven |
| 7 | **Imbuia** | 660 | Classic Brazilian alternative |

### For East Indian Rosewood (Fretboard)

| Priority | Species | Density | Why |
|:--------:|---------|:-------:|-----|
| 1 | **Pau Ferro** | 880 | Drop-in replacement |
| 2 | **Jatoba** | 861 | Budget; similar hardness |
| 3 | **Chechen** | 880 | "Caribbean Rosewood" |
| 4 | **Panga Panga** | 870 | Wenge cousin; dark |
| 5 | **Goncalo Alves** | 1001 | Figured |
| 6 | **Keranji** | 1,090 | Asian Dialium; underexplored |

### For African Ebony (Fretboard)

| Priority | Species | Density | Why |
|:--------:|---------|:-------:|-----|
| 1 | **Katalox** | 1,050 | Hardest; bright |
| 2 | **Rocklite** | — | Engineered; consistent |
| 3 | **Ipe** | 1,119 | Extreme hardness — ⚠ **CITES Appendix II since 2024-11-25 (#17)**, not CITES-free |
| 4 | **Mopane** | 1,075 | Woodwind industry adoption |
| 5 | **Bulletwood** | 1,059 | Very dense; *Manilkara* |
| 6 | **Jarrah** | 845 | "As nice as ebony" per builders |
| 7 | **Camelthorn** | 1,200+ | Namibian extreme |

### For African Blackwood (Extreme Applications)

| Priority | Species | Density | Why |
|:--------:|---------|:-------:|-----|
| 1 | **Bocoa prouacensis** | 1,220 | Close to African Blackwood (CIRAD mean 1.22 vs 1.29); 11 specimens |
| 2 | **Camelthorn** | 1,200+ | Namibian; extreme density |
| 3 | **Grey Ironbark** | 1,130 | Australian eucalypt |
| 4 | **Gidgee** | 1,150 | Australian Acacia |
| 5 | **Mopane** | 1,075 | Industry-adopted for woodwinds |
| 6 | **Australian Buloke** | 1,085 | Hardest Australian |

### For Cocobolo (Accent/Decorative)

| Priority | Species | Density | Why |
|:--------:|---------|:-------:|-----|
| 1 | **Bocote** | 850 | Bold figure; balanced |
| 2 | **Kingwood** | 1,200 | Violet color *(CITES II)* |
| 3 | **Macacauba** | 950 | Bright colors |
| 4 | **Bloodwood** | 1,050 | Vivid red |
| 5 | **Goncalo Alves** | 1001 | Tiger stripe figure |

---

## Part VII: Stiffness Champions (Highest MOE)

For bridges and nuts where energy transfer matters:

| Species | MOE (GPa) | Density | Notes |
|---------|:---------:|:-------:|-------|
| **Greenheart** | 22.4 | 1,010 | Highest in database |
| **Wamara** | 24.38 | 1,080 | *Swartzia panacoco* |
| **Snakewood** | 23.20 | 1,210 | Exotic figure |
| **Bulletwood** | 23.8 | 1,059 | Very stiff |
| **Cumaru** | 22.33 | 1,085 | Known; hard — ⚠ CITES Appendix II since 2024-11-25 (#17) |
| **Bloodwood** | 20.78 | 1,050 | Vivid red |
| **Marblewood** | 19.43 | 1,005 | Figured |
| **Mora** | 19.24 | 1,015 | CIRAD: 1 *M. excelsa* + 10 *M. paraensis* specimens ("39" was the S column, corrected 2026-11-15, C-10) |

---

## Part VIII: US Domestic Options

| Species | Density | MOE | Notes |
|---------|:-------:|:---:|-------|
| **Live Oak** | 986 | 13.7 | SE United States; curved grain |
| **Osage Orange** | 855 | 11.64 | Brilliant yellow; abundant |
| **Black Locust** | 773 | 14.14 | Rot-resistant |
| **Persimmon** | 835 | 13.86 | Traditional; fine-grained |
| **Honey Mesquite** | 950 | 11.58 | **Invasive** — ecological benefit |
| **Texas Ebony** | 965 | 16.54 | Not true ebony; legume |
| **Dogwood** | 815 | 13.26 | Hard; fine-grained |

**The Texas Trio:** Honey Mesquite (950), Texas Ebony (965), and Live Oak (986, FPL GTR-282) span 950–986 kg/m³ with no restrictions.

---

## Part IX: Completely Unexplored Species (Research Priorities)

These CIRAD-documented species have **zero guitar industry presence**:

### Highest Priority

| D12 | Taxa | Family | Specimens | Why Investigate |
|:---:|------|--------|:---------:|-----------------|
| 1.22 | *Bocoa prouacensis* | Leguminosae | 11 | Close to African Blackwood (1.22 vs 1.29) |
| 1.09 | *Manilkara bidentata* | Sapotaceae | 20 | Bulletwood; highest specimen count |
| 1.05 | *Licaria canella* | Lauraceae | 15 | Aromatic; potential unique tone |
| 1.06 | *Oddoniodendron normandii* | Leguminosae | 5 | Completely unknown |
| 1.20 | *Swartzia panacoco* | Leguminosae | 10 | Wamara; high MOE |
| 1.10 | *Xanthomyrtus hienghenensis* | Myrtaceae | 1 | New Caledonia endemic |

### Medium Priority

| D12 | Taxa | Family | Notes |
|:---:|------|--------|-------|
| 1.14 | *Phyllarthron articulatum* | Bignoniaceae | Madagascar |
| 1.10 | *Letestua durissima* | Sapotaceae | Name means "very hard" |
| 1.09 | *Dialium cochinchinense* | Leguminosae | Keranji; Asian |
| 0.91 | *Cylicodiscus gabunensis* | Leguminosae | Okan; dense African |
| 1.01 | *Pimenta racemosa* | Myrtaceae | Bay Rum; aromatic |

### Aromatic Species (Potential Unique Tone)

| D12 | Taxa | Family | Scent |
|:---:|------|--------|-------|
| 1.05 | *Licaria canella* | Lauraceae | Cinnamon |
| 1.12 | *Aniba canellila* | Lauraceae | Aromatic bark |
| 0.99 | *Corymbia citriodora* | Myrtaceae | Lemon |
| 1.01 | *Pimenta racemosa* | Myrtaceae | Bay rum/allspice |
| 0.84 | *Ravensara sp* | Lauraceae | Medicinal |

---

## Part X: Data Gaps

### Missing Acoustic Data

Most CIRAD species lack:
- Speed of sound
- Damping coefficients  
- Q-factor
- Tap-tone characterization

### Missing from wood_species.json

These CIRAD species have no entry in the guitar tonewood database:
- *Bocoa prouacensis*
- *Oddoniodendron normandii*
- *Licaria canella*
- *Xanthomyrtus hienghenensis*
- *Manilkara dissecta*
- *Planchonella* spp.
- Most Madagascar endemics

---

## Summary

**1,255 CIRAD entries** exist in the rosewood-ebony range. The guitar industry uses perhaps 25.

**Key findings:**

1. **Bocoa prouacensis** (mean D12 1.22, 11 specimens) comes **close to African Blackwood** (1.29) and is unexplored for guitars (corrected 2026-11-14, `VERIFICATION_LOG.md` C-05)
2. The **Swartzia genus** contains multiple high-density species with potential (Wamara, S. ingaefolia)
3. **Sapotaceae family** (Bulletwood relatives) has 39 taxa in range — almost none used for instruments
4. **Lauraceae** (aromatic laurels) may offer unique tonal properties from aromatic compounds
5. **New Caledonia** and **Madagascar** have numerous dense endemics never evaluated
6. **Mopane** is already replacing African Blackwood in the woodwind industry — guitars should follow
7. **Rocklite** is now engineered specifically to match ebony properties
8. **US domestic options** exist: Honey Mesquite, Texas Ebony, Live Oak, Osage Orange

The alternatives exist. They just haven't been characterized.

---

## Sources

### Web Research
- [Acoustic Guitar: Beyond Rosewood - 12 Alt-Wood Guitars](https://acousticguitar.com/beyond-rosewood-12-mid-priced-alt-wood-guitars/)
- [Guitar World: Rosewood CITES Restrictions](https://www.guitarworld.com/news/rosewood-set-to-return-as-cites-lifts-guitar-restrictions)
- [TalkBass: Rocklite vs Richlite](https://www.talkbass.com/threads/rocklite-the-latest-synthetic-ebony-for-fingerboards.1311057/)
- [Rocklite UK](https://www.rocklite.co.uk/)
- [Guitar Kit World: Engineered Ebony Fretboards](https://guitarkitworld.com/blogs/resources/engineered-ebony-fretboards)
- [Mangore/Bellucci: Tonewood Properties](https://www.mangore.com/wood)
- [The Wood Database](https://www.wood-database.com/)
- [Tonewood Data Source](https://tonewooddatasource.weebly.com/)
- [NK Forster: Australian Tonewoods](https://nkforsterguitars.com/uncategorized/australian-tonewoods/)
- [Mixdown: Guide to Australian Tonewood](https://mixdownmag.com.au/features/mixdowns-guide-to-australian-tonewood/)
- [Maderas Barber: Macacauba](https://maderasbarber.com/tonewood/en/768-macacauba)
- [UMGF: Macacauba/Hormigo/Granadillo](https://www.acousticguitarforum.com/forums/showthread.php?t=645886)
- [Savage Woods: Chechen](https://savagewoods.com/chechen-wood/)
- [Duffield Timber: African Hardwoods Guide](https://duffieldtimber.com/the-workbench/timber-trends/exotic-african-hardwoods-guide-types-species-uses-benefits)

### Database Sources
- CIRAD Wood Density Database (Vieilledent et al. 2018)
- `wood_species.json` v4.0.0
