# CIRAD High-Density Species Catalog (mean D12 ≥ 0.95 g/cm³)

> **Source:** CIRAD Wood Density Database (Vieilledent et al. 2018), `docs/reference/cirad-density/Cirad-wood-density-database.csv`
> **Regenerated:** 2026-11-14 by `scripts/gen_cirad_high_density_catalog.py` (replaces the 2026-06-22 hand-built version)
> **Related:** `tonewood_comparison_extreme_density_annotated.md`, `VERIFICATION_LOG.md`

**157 taxa across 34 families** have a **mean** D12 ≥ 0.95 g/cm³ over all their CIRAD specimens (1010 taxa in the file).

> **Correction (2026-11-14).** The previous version listed 217 taxa. It selected each taxon by its *heaviest single specimen* and printed that maximum as D12 beside averaged Db and R%. Selecting by maximum gives 217 taxa; selecting by mean gives 157. Every value below is now a mean over all specimens, with the min–max range shown. See `VERIFICATION_LOG.md` (C-01).

> **Caution.** 65 of the 157 taxa rest on a single specimen. Genus-only rows (`sp`) pool unidentified specimens and are not species values. CIRAD gives density and shrinkage only — no stiffness (MOE), so nothing here ranks acoustic quality.

---

## Legend

- **D12** = mean density at 12% moisture content (g/cm³) over N specimens
- **Range** = lowest–highest specimen D12
- **Db** = mean basic density (oven-dry mass / green volume), as measured by CIRAD — not converted from D12
- **R** = mean volumetric shrinkage coefficient (% per % moisture change)
- **N** = number of CIRAD specimens

---

## Summary by Family

| Family | Taxa | Highest mean D12 | Taxa (top 3 by mean D12) |
|--------|:----:|:----------------:|--------------------------|
| **Leguminosae** | 44 | 1.29 | *Dalbergia melanoxylon*, *Platymiscium trinitatis*, *Bocoa prouacensis* |
| **Sapotaceae** | 24 | 1.20 | *Chrysophyllum prieurii*, *Manilkara dissecta*, *Manilkara huberi* |
| **Chrysobalanaceae** | 11 | 1.13 | *Licania ovalifolia*, *Licania canescens*, *Licania ternatensis* |
| **Lecythidaceae** | 9 | 1.14 | *Eschweilera simiorum*, *Lecythis pisonis*, *Eschweilera congestiflora* |
| **Myrtaceae** | 9 | 1.10 | *Xanthomyrtus hienghenensis*, *Eucalyptus paniculata*, *Eucalyptus tetrodonta* |
| **Lauraceae** | 7 | 1.31 | *Mezilaurus sp*, *Aniba canellila*, *Licaria sp* |
| **Cunoniaceae** | 5 | 1.06 | *Pancheria brunhesii*, *Pancheria sebertii*, *Pancheria ternata* |
| **Bignoniaceae** | 4 | 1.14 | *Phyllarthron articulatum*, *Handroanthus serratifolius*, *Phyllarthron madagascariense* |
| **Apocynaceae** | 4 | 0.99 | *Aspidosperma obscurinervium*, *Craspidospermum verticillatum*, *Aspidosperma sandwithianum* |
| **Rhizophoraceae** | 3 | 1.12 | *Rhizophora mangle*, *Rhizophora racemosa*, *Rhizophora sp* |
| **Clusiaceae** | 3 | 0.96 | *Calophyllum ferrugineum*, *Pentadesma butyracea*, *Tovomita carinata* |
| **Casuarinaceae** | 2 | 1.21 | *Gymnostoma nodiflorum*, *Casuarina equisetifolia* |
| **Sarcolaenaceae** | 2 | 1.12 | *Leptolaena multiflora*, *Rhodolaena bakeriana* |
| **Ochnaceae** | 2 | 1.06 | *Lophira alata*, *Ochna calodendron* |
| **Calophyllaceae** | 2 | 1.06 | *Mammea sp*, *Mammea bongo* |
| **Irvingiaceae** | 2 | 1.06 | *Klainedoxa gabonensis*, *Desbordesia insignis* |
| **Proteaceae** | 2 | 1.04 | *Stenocarpus trinervis*, *Dilobeia thouarsii* |
| **Olacaceae** | 2 | 1.01 | *Coula edulis*, *Strombosia grandifolia* |
| **Fagaceae** | 2 | 1.01 | *Quercus canariensis*, *Quercus ilex* |
| **Rubiaceae** | 2 | 1.00 | *Canthium sp*, *Breonia decaryana* |
| **Asteropeiaceae** | 2 | 0.98 | *Asteropeia sp*, *Asteropeia rhopaloides* |
| **Humiriaceae** | 2 | 0.97 | *Vantanea sp*, *Sacoglottis guianensis* |
| **Convolvulaceae** | 1 | 1.27 | *Humbertia madagascariensis* |
| **Peraceae** | 1 | 1.13 | *Chaetocarpus schomburgkianus* |
| **Sapindaceae** | 1 | 1.12 | *Arytera collina* |
| **Melastomataceae** | 1 | 1.10 | *Mouriri sp* |
| **Nothofagaceae** | 1 | 1.10 | *Nothofagus aequilateralis* |
| **Moraceae** | 1 | 1.10 | *Brosimum rubescens* |
| **Phyllanthaceae** | 1 | 1.09 | *Amanoa caribaea* |
| **Oleaceae** | 1 | 1.01 | *Olea sp* |
| **Arecaceae** | 1 | 0.96 | *Borassus aethiopum* |
| **Burseraceae** | 1 | 0.96 | *Tetragastris panamensis* |
| **Salicaceae** | 1 | 0.95 | *Ludia sp* |
| **Combretaceae** | 1 | 0.95 | *Buchenavia oxycarpa* |
| **Total** | **157** | | |

---

## Regional Distribution

A taxon sampled on more than one continent is counted in each, so rows can sum to more than the total.

| Region | Taxa | Mean D12 range |
|--------|:----:|:--------------:|
| South America | 68 | 0.95–1.31 |
| Africa | 61 | 0.95–1.29 |
| Pacific | 16 | 0.95–1.21 |
| Caribbean | 7 | 0.99–1.10 |
| Asia | 4 | 0.95–1.09 |
| Australia | 3 | 1.04–1.20 |
| Indian Ocean (incl. Madagascar) | 2 | 1.01–1.05 |
| Europe | 1 | 0.96–0.96 |

---

# Complete Catalog by Family

## Leguminosae — 44 taxa

The legume family: rosewoods (*Dalbergia*), Swartzia/Bocoa, cumaru (*Dipteryx*), jatoba (*Hymenaea*).

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.29 | 1.25–1.33 | 1.10 | 0.36 | 2 | *Dalbergia melanoxylon* | Africa |
| 1.24 | 1.24–1.24 | 1.03 | 0.68 | 1 | *Platymiscium trinitatis* | South America |
| 1.22 | 1.15–1.31 | 0.99 | 0.70 | 11 | *Bocoa prouacensis* | South America |
| 1.20 | 1.16–1.23 | 0.99 | — | 3 | *Erythrophleum chlorostachys* | Australia |
| 1.20 | 1.20–1.20 | 1.01 | 0.68 | 1 | *Swartzia ingaefolia* | South America |
| 1.20 | 1.10–1.29 | 0.99 | 0.68 | 10 | *Swartzia panacoco* | South America |
| 1.17 | 1.14–1.21 | 0.97 | — | 2 | *Acacia shirleyi* | Australia |
| 1.11 | 1.10–1.13 | 0.90 | 0.52 | 2 | *Xanthocercis madagascariensis* | Africa |
| 1.10 | 1.02–1.14 | 0.90 | 0.65 | 3 | *Dipteryx punctata* | South America |
| 1.09 | 1.06–1.13 | 0.92 | 0.60 | 4 | *Hymenaea parvifolia* | South America |
| 1.09 | 1.09–1.09 | 0.91 | 0.60 | 1 | *Dialium cochinchinense* | Asia |
| 1.08 | 1.08–1.08 | 0.93 | 0.64 | 1 | *Dialium bipindense* | Africa |
| 1.08 | 1.02–1.12 | 0.89 | 0.54 | 6 | *Librevillea klainei* | Africa |
| 1.07 | 0.99–1.18 | 0.90 | 0.61 | 9 | *Dipteryx odorata* | South America |
| 1.07 | 1.03–1.11 | 0.90 | 0.59 | 2 | *Dinizia excelsa* | South America |
| 1.07 | 0.92–1.15 | 0.88 | 0.67 | 3 | *Guibourtia demeusei* | Africa |
| 1.06 | 1.03–1.10 | 0.91 | 0.57 | 2 | *Platymiscium sp* | South America |
| 1.06 | 0.96–1.13 | 0.86 | 0.51 | 5 | *Oddoniodendron normandii* | Africa |
| 1.06 | 0.98–1.16 | 0.91 | 0.48 | 4 | *Dalbergia sp* | Africa |
| 1.05 | 1.01–1.09 | 0.89 | 0.60 | 4 | *Hymenaea intermedia* | South America |
| 1.05 | 1.05–1.05 | 0.89 | 0.68 | 1 | *Monopteryx inpae* | South America |
| 1.05 | 1.05–1.05 | 0.82 | 0.47 | 1 | *Mora excelsa* | Caribbean |
| 1.05 | 1.05–1.05 | 0.84 | 0.37 | 1 | *Prosopis africana* | Africa |
| 1.05 | 1.05–1.05 | 0.87 | 0.61 | 1 | *Swartzia leptopetala* | South America |
| 1.05 | 1.05–1.05 | 0.84 | 0.60 | 1 | *Swartzia oblanceolata* | South America |
| 1.05 | 1.05–1.05 | 0.86 | 0.66 | 1 | *Taralea oppositifolia* | South America |
| 1.05 | 0.98–1.09 | 0.88 | 0.63 | 5 | *Dipteryx polyphylla* | South America |
| 1.04 | 1.04–1.04 | 0.88 | 0.54 | 1 | *Dalbergia spruceana* | South America |
| 1.04 | 1.04–1.04 | 0.87 | 0.59 | 1 | *Martiodendron sp* | South America |
| 1.03 | 1.00–1.06 | 0.85 | 0.61 | 2 | *Dialium pachyphyllum* | Africa |
| 1.02 | 0.90–1.15 | 0.88 | 0.46 | 2 | *Hymenaea sp* | South America |
| 1.02 | 0.98–1.09 | 0.84 | 0.59 | 10 | *Mora paraensis* | South America |
| 1.02 | 1.01–1.03 | 0.88 | 0.57 | 2 | *Bobgunnia fistuloides* | Africa |
| 1.00 | 0.81–1.10 | 0.81 | 0.60 | 11 | *Zygia racemosa* | South America |
| 1.00 | 1.00–1.00 | 0.82 | 0.65 | 1 | *Dialium indum* | Asia |
| 1.00 | 0.97–1.04 | 0.84 | 0.59 | 3 | *Recordoxylon speciosum* | South America |
| 0.99 | 0.99–0.99 | 0.80 | 0.39 | 1 | *Hymenostegia pellegrinii* | Africa |
| 0.97 | 0.97–0.97 | 0.80 | 0.58 | 1 | *Cynometra hankei* | Africa |
| 0.96 | 0.92–0.99 | 0.79 | 0.52 | 2 | *Cynometra ananta* | Africa |
| 0.96 | 0.86–1.06 | 0.80 | 0.58 | 4 | *Erythrophleum suaveolens* | Africa |
| 0.96 | 0.93–0.98 | 0.82 | 0.56 | 2 | *Sweetia fruticosa* | South America |
| 0.95 | 0.95–0.95 | 0.82 | 0.44 | 1 | *Erythrophleum fordii* | Asia |
| 0.95 | 0.95–0.95 | 0.79 | 0.58 | 1 | *Myroxylon balsamum* | South America |
| 0.95 | 0.88–1.02 | 0.80 | 0.56 | 3 | *Peltogyne sp* | South America |

---

## Sapotaceae — 24 taxa

The bulletwood family. Dense, fine-grained woods traditionally used for tool handles and heavy construction.

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.20 | 0.99–1.33 | 0.97 | 0.56 | 4 | *Chrysophyllum prieurii* | South America |
| 1.14 | 1.14–1.14 | 0.97 | 0.62 | 1 | *Manilkara dissecta* | Pacific |
| 1.11 | 0.93–1.16 | 0.90 | 0.63 | 11 | *Manilkara huberi* | South America |
| 1.10 | 1.10–1.10 | 0.89 | 0.58 | 1 | *Planchonella microphylla* | Pacific |
| 1.10 | 1.10–1.10 | 0.91 | 0.78 | 1 | *Planchonella wakere* | Pacific |
| 1.10 | 1.10–1.10 | 0.87 | 0.70 | 1 | *Pouteria pallida* | Caribbean |
| 1.10 | 1.08–1.12 | 0.92 | 0.62 | 4 | *Letestua durissima* | Africa |
| 1.09 | 1.09–1.09 | 0.89 | 0.64 | 1 | *Mimusops sp* | Africa |
| 1.09 | 1.09–1.09 | 0.90 | 0.64 | 1 | *Pouteria guianensis* | South America |
| 1.09 | 1.00–1.19 | 0.88 | 0.61 | 20 | *Manilkara bidentata* | Caribbean, South America |
| 1.05 | 1.05–1.05 | 0.88 | 0.47 | 1 | *Faucherea laciniata* | Africa |
| 1.05 | 1.02–1.08 | 0.85 | 0.58 | 2 | *Manilkara obovata* | Africa |
| 1.04 | 1.04–1.04 | 0.85 | 0.43 | 1 | *Faucherea ambrensis* | Africa |
| 1.04 | 1.04–1.04 | 0.86 | 0.53 | 1 | *Faucherea sp* | Africa |
| 1.04 | 1.04–1.04 | 0.86 | 0.57 | 1 | *Faucherea thouvenotii* | Africa |
| 1.03 | 0.97–1.09 | 0.85 | 0.61 | 4 | *Faucherea parvifolia* | Africa |
| 0.99 | 0.98–1.01 | 0.80 | 0.65 | 2 | *Chrysophyllum lucentifolium* | South America |
| 0.99 | 0.97–1.04 | 0.78 | 0.62 | 6 | *Pouteria sp* | Caribbean, South America |
| 0.98 | 0.98–0.98 | 0.79 | 0.53 | 1 | *Neolemonniera clitandrifolia* | Africa |
| 0.98 | 0.90–1.05 | 0.81 | 0.65 | 8 | *Lecomtedoxa klaineana* | Africa |
| 0.96 | 0.88–1.10 | 0.76 | 0.58 | 10 | *Pradosia cochlearia* | South America |
| 0.96 | 0.93–0.98 | 0.79 | 0.61 | 2 | *Manilkara mabokeensis* | Africa |
| 0.95 | 0.89–1.01 | 0.79 | 0.53 | 5 | *Vitellaria paradoxa* | Africa |
| 0.95 | 0.95–0.95 | 0.77 | 0.55 | 1 | *Pycnandra fastuosa* | Pacific |

---

## Chrysobalanaceae — 11 taxa

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.13 | 1.13–1.13 | 0.88 | 0.62 | 1 | *Licania ovalifolia* | South America |
| 1.12 | 1.12–1.12 | 0.85 | 0.67 | 1 | *Licania canescens* | South America |
| 1.09 | 1.08–1.10 | 0.87 | 0.67 | 3 | *Licania ternatensis* | Caribbean |
| 1.08 | 1.03–1.13 | 0.85 | 0.58 | 4 | *Licania membranacea* | South America |
| 1.06 | 1.06–1.06 | 0.82 | 0.61 | 1 | *Licania alba* | South America |
| 1.06 | 1.06–1.06 | 0.87 | 0.47 | 1 | *Licania macrophylla* | South America |
| 1.05 | 1.05–1.05 | 0.83 | 0.64 | 1 | *Licania micrantha* | South America |
| 1.03 | 1.03–1.03 | 0.84 | 0.61 | 1 | *Licania majuscula* | South America |
| 1.02 | 0.98–1.06 | 0.83 | 0.32 | 2 | *Maranthes glabra* | Africa |
| 1.01 | 1.01–1.01 | 0.81 | 0.68 | 1 | *Maranthes robusta* | Africa |
| 1.00 | 0.92–1.09 | 0.80 | 0.64 | 4 | *Licania sp* | South America |

---

## Lecythidaceae — 9 taxa

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.14 | 1.14–1.14 | 0.94 | 0.51 | 1 | *Eschweilera simiorum* | South America |
| 1.10 | 1.10–1.10 | 0.93 | 0.69 | 1 | *Lecythis pisonis* | South America |
| 1.06 | 1.06–1.06 | 0.88 | 0.56 | 1 | *Eschweilera congestiflora* | South America |
| 1.02 | 1.01–1.04 | 0.83 | 0.60 | 2 | *Corythophora rimosa* | South America |
| 1.02 | 0.96–1.08 | 0.81 | 0.60 | 4 | *Foetidia clusioides* | Africa |
| 1.00 | 0.97–1.04 | 0.82 | 0.54 | 4 | *Lecythis zabucajo* | South America |
| 1.00 | 0.91–1.04 | 0.82 | 0.55 | 6 | *Eschweilera coriacea* | South America |
| 0.99 | 0.88–1.06 | 0.78 | 0.56 | 6 | *Eschweilera sp* | South America |
| 0.97 | 0.88–1.10 | 0.79 | 0.54 | 3 | *Lecythis idatimon* | South America |

---

## Myrtaceae — 9 taxa

The eucalyptus family. Australian hardwoods and plantation timber (CIRAD's samples include planted eucalypts outside Australia).

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.10 | 1.10–1.10 | 0.87 | 0.39 | 1 | *Xanthomyrtus hienghenensis* | Pacific |
| 1.08 | 1.05–1.13 | 0.85 | 0.62 | 3 | *Eucalyptus paniculata* | Africa |
| 1.04 | 1.03–1.05 | 0.86 | — | 3 | *Eucalyptus tetrodonta* | Australia |
| 1.01 | 1.01–1.01 | 0.84 | 0.56 | 1 | *Pimenta racemosa* | Caribbean |
| 0.99 | 0.84–1.07 | 0.82 | 0.62 | 5 | *Corymbia citriodora* | Africa |
| 0.99 | 0.97–1.00 | 0.81 | 0.55 | 3 | *Arillastrum gummiferum* | Pacific |
| 0.99 | 0.91–1.04 | 0.80 | 0.61 | 6 | *Eucalyptus microcorys* | Africa |
| 0.97 | 0.97–0.97 | 0.79 | 0.52 | 1 | *Eucalyptus delegatensis* | Africa |
| 0.97 | 0.91–1.02 | 0.78 | 0.54 | 2 | *Syzygium wagapense* | Pacific |

---

## Lauraceae — 7 taxa

Aromatic woods including cinnamon relatives.

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.31 | 1.31–1.32 | 1.10 | 0.74 | 2 | *Mezilaurus sp* | South America |
| 1.12 | 1.01–1.22 | 0.95 | 0.64 | 3 | *Aniba canellila* | South America |
| 1.06 | 1.06–1.06 | 0.89 | 0.57 | 1 | *Licaria sp* | South America |
| 1.05 | 0.62–1.23 | 0.89 | 0.57 | 15 | *Licaria canella* | South America |
| 1.02 | 1.02–1.02 | 0.83 | 0.64 | 1 | *Misanteca aritu* | South America |
| 0.97 | 0.97–0.97 | 0.77 | 0.60 | 1 | *Aniba melinonii* | South America |
| 0.97 | 0.97–0.97 | 0.80 | 0.36 | 1 | *Chlorocardium rodiei* | South America |

---

## Cunoniaceae — 5 taxa

| D12 | Range | Db | R | N | Taxon | Region |
|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| 1.06 | 1.06–1.06 | 0.88 | 0.50 | 1 | *Pancheria brunhesii* | Pacific |
| 1.05 | 1.05–1.05 | 0.81 | 0.58 | 1 | *Pancheria sebertii* | Pacific |
| 1.02 | 1.02–1.02 | 0.83 | 0.51 | 1 | *Pancheria ternata* | Pacific |
| 0.96 | 0.92–1.00 | 0.79 | 0.43 | 2 | *Cunonia austrocaledonica* | Pacific |
| 0.96 | 0.93–0.98 | 0.77 | 0.46 | 2 | *Weinmannia rutenbergii* | Africa |

---

## Families with fewer than 5 taxa (27 families, 48 taxa)

| Family | D12 | Range | Db | R | N | Taxon | Region |
|--------|:---:|:-----:|:--:|:-:|:-:|-------|--------|
| Bignoniaceae | 1.14 | 1.14–1.14 | 0.94 | 0.52 | 1 | *Phyllarthron articulatum* | Africa |
| Bignoniaceae | 1.11 | 1.02–1.18 | 0.93 | 0.61 | 7 | *Handroanthus serratifolius* | South America |
| Bignoniaceae | 1.07 | 1.07–1.07 | 0.90 | 0.69 | 1 | *Phyllarthron madagascariense* | Africa |
| Bignoniaceae | 1.02 | 0.90–1.19 | 0.88 | 0.63 | 12 | *Tabebuia sp* | South America |
| Apocynaceae | 0.99 | 0.94–1.03 | 0.79 | 0.67 | 4 | *Aspidosperma obscurinervium* | South America |
| Apocynaceae | 0.97 | 0.97–0.97 | 0.80 | 0.58 | 1 | *Craspidospermum verticillatum* | Africa |
| Apocynaceae | 0.96 | 0.96–0.96 | 0.77 | 0.61 | 1 | *Aspidosperma sandwithianum* | South America |
| Apocynaceae | 0.95 | 0.95–0.95 | 0.79 | 0.60 | 1 | *Stephanostegia sp* | Africa |
| Rhizophoraceae | 1.12 | 1.11–1.13 | 0.90 | 0.66 | 2 | *Rhizophora mangle* | South America |
| Rhizophoraceae | 1.06 | 1.06–1.06 | 0.88 | 0.80 | 1 | *Rhizophora racemosa* | Africa |
| Rhizophoraceae | 1.02 | 1.02–1.02 | 0.85 | 0.69 | 1 | *Rhizophora sp* | Africa |
| Clusiaceae | 0.96 | 0.96–0.96 | 0.78 | 0.59 | 1 | *Calophyllum ferrugineum* | Asia |
| Clusiaceae | 0.96 | 0.84–1.07 | 0.80 | 0.69 | 2 | *Pentadesma butyracea* | Africa |
| Clusiaceae | 0.95 | 0.95–0.95 | 0.73 | 0.55 | 1 | *Tovomita carinata* | South America |
| Casuarinaceae | 1.21 | 1.21–1.21 | 0.97 | 0.69 | 1 | *Gymnostoma nodiflorum* | Pacific |
| Casuarinaceae | 1.05 | 1.03–1.09 | 0.84 | 0.64 | 6 | *Casuarina equisetifolia* | Indian Ocean (incl. Madagascar), Pacific, South America |
| Sarcolaenaceae | 1.12 | 1.11–1.14 | 0.92 | 0.58 | 2 | *Leptolaena multiflora* | Africa |
| Sarcolaenaceae | 0.98 | 0.96–1.01 | 0.79 | 0.52 | 4 | *Rhodolaena bakeriana* | Africa |
| Ochnaceae | 1.06 | 1.01–1.14 | 0.86 | 0.58 | 16 | *Lophira alata* | Africa |
| Ochnaceae | 0.96 | 0.96–0.96 | 0.78 | 0.53 | 1 | *Ochna calodendron* | Africa |
| Calophyllaceae | 1.06 | 1.06–1.06 | 0.81 | 0.54 | 1 | *Mammea sp* | Africa |
| Calophyllaceae | 0.98 | 0.93–1.02 | 0.78 | 0.46 | 2 | *Mammea bongo* | Africa |
| Irvingiaceae | 1.06 | 0.99–1.11 | 0.87 | 0.65 | 6 | *Klainedoxa gabonensis* | Africa |
| Irvingiaceae | 1.05 | 0.97–1.11 | 0.85 | 0.59 | 5 | *Desbordesia insignis* | Africa |
| Proteaceae | 1.04 | 1.03–1.06 | 0.86 | 0.45 | 3 | *Stenocarpus trinervis* | Pacific |
| Proteaceae | 1.02 | 0.98–1.07 | 0.81 | 0.52 | 5 | *Dilobeia thouarsii* | Africa |
| Olacaceae | 1.01 | 0.91–1.08 | 0.85 | 0.55 | 6 | *Coula edulis* | Africa |
| Olacaceae | 1.00 | 0.98–1.01 | 0.84 | 0.50 | 3 | *Strombosia grandifolia* | Africa |
| Fagaceae | 1.01 | 0.97–1.06 | 0.83 | 0.56 | 3 | *Quercus canariensis* | Africa |
| Fagaceae | 0.96 | 0.92–1.02 | 0.79 | 0.57 | 6 | *Quercus ilex* | Africa, Europe |
| Rubiaceae | 1.00 | 0.98–1.01 | 0.79 | 0.55 | 3 | *Canthium sp* | Africa |
| Rubiaceae | 0.96 | 0.83–1.09 | 0.77 | 0.55 | 2 | *Breonia decaryana* | Africa |
| Asteropeiaceae | 0.98 | 0.98–0.98 | 0.81 | 0.59 | 1 | *Asteropeia sp* | Africa |
| Asteropeiaceae | 0.96 | 0.90–1.02 | 0.79 | 0.58 | 2 | *Asteropeia rhopaloides* | Africa |
| Humiriaceae | 0.97 | 0.96–0.99 | 0.80 | 0.62 | 2 | *Vantanea sp* | South America |
| Humiriaceae | 0.96 | 0.93–1.02 | 0.77 | 0.60 | 3 | *Sacoglottis guianensis* | South America |
| Convolvulaceae | 1.27 | 1.27–1.28 | 1.07 | 0.61 | 2 | *Humbertia madagascariensis* | Africa |
| Peraceae | 1.13 | 1.13–1.13 | 0.92 | 0.61 | 1 | *Chaetocarpus schomburgkianus* | South America |
| Sapindaceae | 1.12 | 1.11–1.13 | 0.92 | 0.69 | 2 | *Arytera collina* | Pacific |
| Melastomataceae | 1.10 | 1.10–1.10 | 0.85 | 0.66 | 1 | *Mouriri sp* | South America |
| Nothofagaceae | 1.10 | 1.10–1.10 | 0.94 | 0.62 | 2 | *Nothofagus aequilateralis* | Pacific |
| Moraceae | 1.10 | 0.97–1.29 | 0.94 | 0.54 | 7 | *Brosimum rubescens* | South America |
| Phyllanthaceae | 1.09 | 1.07–1.13 | 0.90 | 0.64 | 5 | *Amanoa caribaea* | Caribbean |
| Oleaceae | 1.01 | 1.01–1.01 | 0.83 | 0.54 | 1 | *Olea sp* | Indian Ocean (incl. Madagascar) |
| Arecaceae | 0.96 | 0.88–1.04 | 0.81 | 0.51 | 2 | *Borassus aethiopum* | Africa |
| Burseraceae | 0.96 | 0.92–0.99 | 0.79 | 0.58 | 4 | *Tetragastris panamensis* | South America |
| Salicaceae | 0.95 | 0.95–0.96 | 0.76 | 0.54 | 2 | *Ludia sp* | Africa |
| Combretaceae | 0.95 | 0.92–0.98 | 0.80 | 0.46 | 3 | *Buchenavia oxycarpa* | South America |

---

## Best-sampled taxa

Named species (not `sp`) with N ≥ 5, by mean D12. A large N means the mean is less likely to be one unusual tree; it says nothing about tone.

| Taxon | Family | D12 | Range | N | Countries |
|-------|--------|:---:|:-----:|:-:|-----------|
| *Bocoa prouacensis* | Leguminosae | 1.22 | 1.15–1.31 | 11 | French Guiana |
| *Swartzia panacoco* | Leguminosae | 1.20 | 1.10–1.29 | 10 | Brazil, French Guiana |
| *Handroanthus serratifolius* | Bignoniaceae | 1.11 | 1.02–1.18 | 7 | Brazil, French Guiana |
| *Manilkara huberi* | Sapotaceae | 1.11 | 0.93–1.16 | 11 | Brazil |
| *Brosimum rubescens* | Moraceae | 1.10 | 0.97–1.29 | 7 | Brazil, French Guiana |
| *Amanoa caribaea* | Phyllanthaceae | 1.09 | 1.07–1.13 | 5 | Guadeloupe |
| *Manilkara bidentata* | Sapotaceae | 1.09 | 1.00–1.19 | 20 | Brazil, French Guiana, Guadeloupe |
| *Librevillea klainei* | Leguminosae | 1.08 | 1.02–1.12 | 6 | Congo, Gabon |
| *Dipteryx odorata* | Leguminosae | 1.07 | 0.99–1.18 | 9 | Brazil, French Guiana |
| *Lophira alata* | Ochnaceae | 1.06 | 1.01–1.14 | 16 | Cameroon, Central African Republic, Cote d'Ivoire, Gabon |
| *Oddoniodendron normandii* | Leguminosae | 1.06 | 0.96–1.13 | 5 | Gabon |
| *Klainedoxa gabonensis* | Irvingiaceae | 1.06 | 0.99–1.11 | 6 | Cameroon, Cote d'Ivoire, Gabon |
| *Casuarina equisetifolia* | Casuarinaceae | 1.05 | 1.03–1.09 | 6 | French Guiana, French Polynesia, Reunion |
| *Dipteryx polyphylla* | Leguminosae | 1.05 | 0.98–1.09 | 5 | Brazil |
| *Desbordesia insignis* | Irvingiaceae | 1.05 | 0.97–1.11 | 5 | Cameroon, Gabon |
| *Licaria canella* | Lauraceae | 1.05 | 0.62–1.23 | 15 | Brazil, French Guiana |
| *Mora paraensis* | Leguminosae | 1.02 | 0.98–1.09 | 10 | Brazil |
| *Dilobeia thouarsii* | Proteaceae | 1.02 | 0.98–1.07 | 5 | Madagascar |
| *Coula edulis* | Olacaceae | 1.01 | 0.91–1.08 | 6 | Cameroon, Congo, Cote d'Ivoire, Gabon |
| *Zygia racemosa* | Leguminosae | 1.00 | 0.81–1.10 | 11 | Brazil, French Guiana |

---

## References

- Vieilledent G. et al. 2018. Bayesian modeling of wood density. *American Journal of Botany* doi:10.1002/ajb2.1175
- Data: `docs/reference/cirad-density/Cirad-wood-density-database.csv`
- Regenerate: `python scripts/gen_cirad_high_density_catalog.py . docs/tonewood/tonewood_catalog_cirad_high_density.md`
