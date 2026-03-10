# Tonewood Comparison: Rosewoods · Ebonies · Honey Mesquite

> **Source:** `wood_species.json` v4.0.0 + `luthier_tonewood_reference.json` v1.0.0
> **Generated:** 2026-03-10

This comparison groups two traditional fretboard/bridge rosewoods, three ebonies (two classic, one emerging regional), and honey mesquite as a domestic alternative bridging both families.

---

## At a Glance

| Species | Relevance | Density (kg/m³) | Janka (lbf) | Tone Character | Sustainability |
|---------|:---------:|:---:|:---:|----------------|----------------|
| **Brazilian Rosewood** | Primary | 835 | 2,790 | Rich, complex, legendary | CITES Appendix I — highly restricted |
| **East Indian Rosewood** | Primary | 830 | 2,440 | Warm, complex overtones, sustain | CITES regulated |
| **African Ebony** | Primary | 1,030 | 3,080 | Bright, articulate, percussive | Endangered — use alternatives |
| **Macassar Ebony** | Primary | 1,120 | 3,220 | Bright, defined | Vulnerable |
| **Texas Ebony** | Emerging | 965 | 1,179 | *(not yet characterized)* | *(not yet characterized)* |
| **Honey Mesquite** | Emerging | 950 | 2,345 | Bright, crystalline highs, strong sustain — rosewood-like but more percussive | Abundant — invasive, harvest is ecologically beneficial |

---

## Physical Properties

| Property | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Scientific Name** | *Dalbergia nigra* | *Dalbergia latifolia* | *Diospyros crassiflora* | *Diospyros celebica* | *Ebenopsis ebano* | *Prosopis glandulosa* |
| **Specific Gravity** | 0.82 | 0.80 | 1.03 | 1.09 | 0.96 | 0.86 |
| **Density (kg/m³)** | 835 | 830 | 1,030 | 1,120 | 965 | 950 |
| **Janka Hardness (lbf)** | 2,790 | 2,440 | 3,080 | 3,220 | 1,179 | 2,345 |
| **Janka Hardness (N)** | 12,411 | 10,854 | 13,701 | 14,323 | 5,244 | 10,431 |
| **Grain** | Interlocked | Interlocked | Straight | Striped | — | Interlocked, wildly figured |
| **Workability** | Moderate | Moderate — oily, dulls tools | Difficult — very hard | Difficult | — | Difficult — very hard, dulls cutters |
| **Resinous** | Yes | Yes | No | No | No | No |
| **Contraction Radial (%)** | — | — | — | — | — | — |
| **Contraction Tangential (%)** | — | — | — | — | — | — |
| **MOE (GPa)** | — | — | — | — | 16.54 | 11.58 |
| **MOR (MPa)** | — | — | — | — | 152.3 | 117.0 |

> **Note:** MOE/MOR data for the four primary species is absent from the main `wood_species.json` physical records. Texas Ebony and Honey Mesquite have structural data populated.

---

## Acoustic Properties

| Property | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Speed of Sound (m/s)** | *null* | *null* | *null* | *null* | 4,140 | 3,491 |
| **Acoustic Impedance (10⁶ kg/m²s)** | *null* | *null* | *null* | *null* | 4.00 | 3.32 |
| **Tone Character** | Rich, complex, legendary | Warm, complex overtones, sustain | Bright, articulate, percussive | Bright, defined | — | Bright, crystalline highs, strong sustain |

> **Data gap:** The four most historically important species in this set (both rosewoods and both traditional ebonies) have `null` speed-of-sound and acoustic impedance values in the tonewood reference. This is a significant gap — these are the benchmark species against which alternatives are compared.

---

## Thermal Properties

| Property | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Thermal Conductivity (W/m·K)** | 0.18 | 0.17 | 0.21 | 0.22 | 0.38 | 0.37 |
| **Specific Heat (J/kg·K)** | 1,400 | 1,400 | 1,300 | 1,250 | 1,424 | 1,450 |
| **SCE (J/mm³)** | 0.65 | 0.60 | 0.75 | 0.80 | 0.77 | 0.78 |
| **Heat Partition — Chip** | 0.63 | 0.65 | 0.60 | 0.58 | 0.61 | 0.60 |
| **Heat Partition — Tool** | 0.24 | 0.22 | 0.25 | 0.27 | 0.25 | 0.25 |
| **Heat Partition — Work** | 0.13 | 0.13 | 0.15 | 0.15 | 0.15 | 0.15 |

All six species generate substantially more cutting energy than standard body woods (0.45 J/mm³ for cherry/mahogany/walnut). Macassar Ebony is the worst at 0.80 J/mm³. The heat partition shifts away from chips and toward tool/workpiece in the densest species — meaning more tool wear and more thermal stress in the blank.

---

## CNC Machining

| Property | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hardness Scale** | 0.85 | 0.80 | 0.95 | 1.00 | 0.34 | 0.70 |
| **Burn Tendency** | 0.20 | 0.20 | 0.10 | 0.10 | 0.27 | 0.45 |
| **Tearout Tendency** | 0.30 | 0.30 | 0.20 | 0.20 | 0.30 | 0.55 |
| **Chipload Multiplier** | 0.65 | 0.70 | 0.60 | 0.55 | 1.03 | 0.80 |
| **Roughing Feed Max (mm/min)** | 1,800 | 2,000 | 1,500 | 1,200 | 4,300 | 2,800 |
| **Finishing Feed Max (mm/min)** | 1,000 | 1,200 | 800 | 700 | 2,480 | 1,800 |
| **Plunge Feed Max (mm/min)** | 350 | 400 | 300 | 250 | 1,388 | 700 |
| **Min RPM** | 16,000 | 16,000 | 18,000 | 18,000 | 12,720 | 16,000 |
| **Max RPM** | 24,000 | 24,000 | 24,000 | 24,000 | 24,000 | 24,000 |
| **Optimal SFM** | 450 | 500 | 400 | 380 | 894 | 650 |
| **Max DOC (mm)** | 3 | 4 | 3 | 2 | 13 | 8 |
| **Optimal DOC Ratio** | 0.20 | 0.25 | 0.20 | 0.15 | 0.51 | 0.40 |
| **Max WOC Ratio** | 0.25 | 0.30 | 0.25 | 0.20 | 0.53 | 0.40 |
| **Finishing WOC Ratio** | 0.05 | 0.05 | 0.05 | 0.04 | 0.15 | 0.10 |

### Machining Aggressiveness Ranking (most to least restrictive)

1. **Macassar Ebony** — hardest wood in registry (scale 1.00). Max DOC 2mm, chipload ×0.55, finishing feed 700 mm/min. Carbide only. Extreme tool wear.
2. **African Ebony** — scale 0.95. Max DOC 3mm, chipload ×0.60, finishing feed 800 mm/min. Carbide mandatory.
3. **Brazilian Rosewood** — scale 0.85. Max DOC 3mm, chipload ×0.65. Oily, resinous — gums tools.
4. **East Indian Rosewood** — scale 0.80. Slightly more forgiving DOC (4mm) and feeds than Brazilian.
5. **Honey Mesquite** — scale 0.70. More aggressive cuts possible (8mm DOC) but highest tearout (0.55) and burn tendency (0.45) in the group.
6. **Texas Ebony** — scale 0.34. Surprisingly machine-friendly despite 965 kg/m³ density. Standard chipload (1.03×), deep cuts allowed (13mm DOC).

### Machining Warnings

| Risk | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Burn Risk** | Medium | Medium | High | High | Low | High |
| **Tearout Risk** | Medium | Medium | High | High | Medium | High |
| **Dust Hazard** | High | High | High | High | High | High |

**Every species in this comparison has HIGH dust hazard.** Full dust extraction is mandatory for all six.

| Species | Machining Notes |
|---------|-----------------|
| **Brazilian Rosewood** | Extremely rare and expensive. Test on scrap first. Dust is sensitizing. |
| **East Indian Rosewood** | Oily wood dulls tools fast. Dust is sensitizing — use extraction. |
| **African Ebony** | Extremely hard. Use sharp carbide, light cuts. Dust is hazardous. |
| **Macassar Ebony** | Hardest wood in registry. Extreme tool wear. Carbide only. |
| **Texas Ebony** | *(No detailed notes in database)* |
| **Honey Mesquite** | Extremely hard — dulls HSS quickly, use carbide. Interlocked grain tears easily on figured stock. Dust is irritating. Small blanks common due to tree form. |

---

## Lutherie Profile

| Property | Brazilian Rosewood | East Indian Rosewood | African Ebony | Macassar Ebony | Texas Ebony | Honey Mesquite |
|----------|:---|:---|:---|:---|:---|:---|
| **Guitar Relevance** | Primary | Primary | Primary | Primary | Emerging | Emerging |
| **Typical Uses** | Fretboard, back/sides | Fretboard, back/sides, bridge | Fretboard, bridge, nuts | Fretboard, bridge, decorative | *(none listed)* | Body, body top, fretboard, bridge, accent |
| **Sustainability** | CITES Appendix I — highly restricted | CITES regulated | Endangered — use alternatives | Vulnerable | — | Abundant — invasive, harvest ecologically beneficial |

---

## Analysis

### The Rosewood Pair

Brazilian and East Indian rosewood are virtually identical in density (835 vs 830 kg/m³) and share interlocked, resinous grain. Brazilian is the harder of the two (Janka 2,790 vs 2,440) and carries the more legendary tonal reputation — "rich, complex, legendary" vs East Indian's "warm, complex overtones, sustain." Both are CITES-listed; Brazilian at Appendix I is effectively unobtainable for new instruments. East Indian remains the industry-standard rosewood for fretboards and back/sides but faces increasing regulation.

CNC behavior is similar — both require reduced chipload (0.65–0.70×), conservative DOC (3–4mm), high minimum RPM (16,000), and produce sensitizing dust. East Indian is marginally more forgiving across the board. Both are oily/resinous, which lubricates the cut but gums tooling.

### The Ebony Trio

African and Macassar ebony are the traditional fretboard/bridge ebonies — the densest and hardest woods in the entire 472-species database. Macassar at 1,120 kg/m³ and Janka 3,220 is the absolute ceiling: hardness scale 1.00, max DOC just 2mm, chipload multiplier 0.55. African is slightly more forgiving (scale 0.95, 3mm DOC) but both demand sharp carbide, minimal feed rates, and accept that tool wear is a cost of business.

**Texas Ebony is the surprise.** Despite 965 kg/m³ density (heavier than Brazilian Rosewood), its Janka hardness is only 1,179 — less than half of the traditional ebonies. This translates to a dramatically different CNC profile: hardness scale 0.34, standard chipload (1.03×), and a generous 13mm max DOC. It also has the highest MOE (16.54 GPa) and MOR (152.3 MPa) of any species in this comparison — structurally it's the stiffest and strongest. The acoustic data (speed of sound 4,140 m/s, impedance 4.00) positions it as a high-impedance wood with strong energy transfer. The lutherie fields are unpopulated — Texas Ebony is a data gap waiting to be characterized, but the physical properties are promising for fretboards and bridges.

### Honey Mesquite: The Crossover

Mesquite sits between the rosewoods and ebonies by density (950 kg/m³) but closer to rosewood in tonal character — "bright, crystalline highs with strong sustain, similar to rosewood but more percussive." Its acoustic impedance (3.32) exceeds both rosewoods and its speed of sound (3,491 m/s) is the lowest of the group, concentrating energy into a denser, more percussive attack.

It's the most versatile species here by use case — the database lists body, body top, fretboard, bridge, and accent applications, whereas the rosewoods and ebonies are primarily fretboard/bridge/back-sides woods. The wildly figured grain gives it an aesthetic edge for visible applications.

The CNC tradeoff vs the ebonies: mesquite is easier to cut (chipload 0.80× vs 0.55–0.65×, DOC 8mm vs 2–4mm) but burns and tears more. The ebonies' straight/striped grain resists tearout; mesquite's interlocked figure fights back.

### Sustainability Context

This is the critical axis. The four primary species face compounding supply pressure:

| Species | CITES Status | Practical Availability |
|---------|-------------|----------------------|
| Brazilian Rosewood | Appendix I | Effectively unavailable for new instruments |
| East Indian Rosewood | Appendix II | Available but regulated, paperwork burden increasing |
| African Ebony | Endangered | Industry shifting away; Taylor Guitars' Ebony Project promoting streaked alternatives |
| Macassar Ebony | Vulnerable | Available but declining |

Texas Ebony and Honey Mesquite are both North American species with no CITES restrictions. Mesquite is explicitly *invasive* in the American Southwest — every board harvested is an ecological net positive. Texas Ebony (*Ebenopsis ebano*) is a legume, not a true *Diospyros* ebony, but earns the name from its dense, dark heartwood.

### Data Gaps to Address

| Species | Missing Data |
|---------|-------------|
| **Brazilian Rosewood** | Speed of sound, acoustic impedance, MOE, MOR, contraction values |
| **East Indian Rosewood** | Speed of sound, acoustic impedance, MOE, MOR, contraction values |
| **African Ebony** | Speed of sound, acoustic impedance, MOE, MOR, contraction values |
| **Macassar Ebony** | Speed of sound, acoustic impedance, MOE, MOR, contraction values |
| **Texas Ebony** | Grain description, workability, tone character, typical uses, sustainability, machining notes |
| **Honey Mesquite** | Contraction values |

The four primary species lack acoustic measurements — the very properties most relevant to their status as tonewoods. The two emerging species have better structural/acoustic data but lack lutherie characterization. Filling these gaps would significantly improve the database's value for tonewood selection.
