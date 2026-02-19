# Wood Species Reference

**Version:** 4.0.0  
**Total species:** 472  
**Last updated:** February 2026  
**Source data:** [`wood_species.json`](wood_species.json)  
**Methodology & citations:** [`SOURCES.md`](SOURCES.md)

---

## Data Sources

| Source | Description | License |
|--------|-------------|---------|
| [USDA FPL Wood Handbook: Wood as an Engineering Material](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/fplgtr282.pdf) | thermal_conductivity (Table 3-11, ±20%), SG, Janka, MOR, MOE, shrinkage for ~30 domestic species | U.S. Government work — public domain |
| [The Wood Database](https://www.wood-database.com) | density, MOR, MOE for 465 species; per-species URLs in _source_url fields | Referenced under fair use |
| [CIRAD Wood Collection Index](https://github.com/openwoodlab/cirad-wood-collection) | Specific gravity cross-validation from 34,395 specimens across 1,831 genera | CC-BY open data |

> **Estimation note:** Thermal k, SCE, specific heat, and Janka (bulk species) estimated from SG/density regressions per FPL guidance. Machining params derived from hardness scale. All estimates flagged with _note fields. Full methodology in SOURCES.md.

---

## Guitar Relevance Tiers

| Tier | Count | Description |
|------|-------|-------------|
| **Primary** | 19 | Traditional tonewoods — the classic guitar species |
| **Established** | 30 | Well-known guitar woods with proven track records |
| **Emerging** | 57 | Species gaining popularity as sustainable or affordable alternatives |
| **Exploratory** | 366 | Valid machinable woods — available for experimentation |

---

## Units

| Abbreviation | Unit | Description |
|-------------|------|-------------|
| SG | — | Specific gravity (oven-dry weight / green volume) |
| Density | kg/m³ | Air-dry density |
| Janka | lbf | Side hardness, pound-force |
| MOR | MPa | Modulus of rupture — static bending strength at 12% MC |
| MOE | GPa | Modulus of elasticity — static bending stiffness at 12% MC |
| k | W/(m·K) | Thermal conductivity at 12% MC, across grain |
| SCE | J/mm³ | Specific cutting energy |
| Feeds | mm/min | CNC feed rates |
| RPM | rev/min | Spindle speed |

---

## Primary Tonewoods

*The core species that have defined the sound and feel of electric and acoustic guitars for decades.*

| # | Species | Scientific Name | Type | SG | Density | Janka | MOR | MOE | k |
|--:|---------|-----------------|------|----|---------|-------|-----|-----|---|
| 1 | **Red Alder** | *Alnus rubra* | H | 0.41 | 420 | 590 | — | — | 0.12 |
| 2 | **Swamp Ash** | *Fraxinus spp.* | H | 0.48 | 500 | 1010 | — | — | 0.14 |
| 3 | **American Basswood** | *Tilia americana* | H | 0.38 | 415 | 410 | 60.0 | 10.07 | 0.11 |
| 4 | **Western Red Cedar** | *Thuja plicata* | S | 0.33 | 370 | 350 | 53.1 | 7.78 | 0.1 |
| 5 | **Cocobolo** | *Dalbergia retusa* | H | 1.1 | 1095 | 2960 | — | — | 0.42 |
| 6 | **African Ebony** | *Diospyros crassiflora* | H | 1.03 | 1030 | 3080 | — | — | 0.21 |
| 7 | **Macassar Ebony** | *Diospyros celebica* | H | 1.09 | 1120 | 3220 | — | — | 0.22 |
| 8 | **Hawaiian Koa** | *Acacia koa* | H | 0.6 | 625 | 1170 | 87.0 | 10.37 | 0.15 |
| 9 | **African Mahogany (Khaya)** | *Khaya spp.* | H | 0.5 | 530 | 830 | — | — | 0.12 |
| 10 | **Honduran Mahogany** | *Swietenia macrophylla* | H | 0.52 | 545 | 800 | 98.4 | 11.97 | 0.12 |
| 11 | **Hard Maple (Sugar Maple)** | *Acer saccharum* | H | 0.66 | 705 | 1450 | 118.5 | 13.49 | 0.18 |
| 12 | **Soft Maple (Red Maple)** | *Acer rubrum* | H | 0.56 | 610 | 950 | — | — | 0.15 |
| 13 | **Brazilian Rosewood** | *Dalbergia nigra* | H | 0.82 | 835 | 2790 | — | — | 0.18 |
| 14 | **East Indian Rosewood** | *Dalbergia latifolia* | H | 0.8 | 830 | 2440 | — | — | 0.17 |
| 15 | **Adirondack Spruce (Red Spruce)** | *Picea rubens* | S | 0.43 | 435 | 560 | 74.0 | 11.2 | 0.19 |
| 16 | **Engelmann Spruce** | *Picea engelmannii* | S | 0.37 | 385 | 390 | — | — | 0.11 |
| 17 | **European Spruce (Alpine/German)** | *Picea abies* | S | 0.4 | 405 | 490 | 65.0 | 9.5 | 0.18 |
| 18 | **Sitka Spruce** | *Picea sitchensis* | S | 0.42 | 425 | 510 | — | — | 0.12 |
| 19 | **Black Walnut** | *Juglans nigra* | H | 0.56 | 610 | 1010 | 90.7 | 11.34 | 0.14 |

### Detailed Profiles

<a id="alder"></a>
#### Red Alder

**ID:** `alder` · **Category:** hardwood · **Scientific name:** *Alnus rubra*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.41 |
| Density | 420 kg/m³ |
| Janka Hardness | 590 lbf / 2624 N |
| Grain | straight |
| Workability | excellent |
| Resinous | No |
| Thermal Conductivity | 0.12 W/(m·K) |
| Specific Heat | 1700 J/(kg·K) |
| Specific Cutting Energy | 0.35 J/mm³ |
| Hardness Scale | 0.25 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.4 |
| Roughing Feed Max | 5000 mm/min |
| Finishing Feed Max | 3000 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: low |
| Guitar Uses | body |
| Tone Character | balanced, slightly bright, clear |
| Sustainability | sustainable, abundant |

<a id="ash_swamp"></a>
#### Swamp Ash

**ID:** `ash_swamp` · **Category:** hardwood · **Scientific name:** *Fraxinus spp.*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.48 |
| Density | 500 kg/m³ |
| Janka Hardness | 1010 lbf / 4493 N |
| Grain | prominent, open pore |
| Workability | good |
| Resinous | No |
| Thermal Conductivity | 0.14 W/(m·K) |
| Specific Heat | 1700 J/(kg·K) |
| Specific Cutting Energy | 0.42 J/mm³ |
| Hardness Scale | 0.5 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.6 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: medium |
| Guitar Uses | body |
| Tone Character | bright, twangy, scooped mids |
| Sustainability | declining (emerald ash borer) |

<a id="basswood"></a>
#### American Basswood

**ID:** `basswood` · **Category:** hardwood · **Scientific name:** *Tilia americana*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.38 |
| Density | 415 kg/m³ |
| Janka Hardness | 410 lbf / 1824 N |
| Modulus of Rupture | 60.0 MPa |
| Modulus of Elasticity | 10.07 GPa |
| Grain | straight, fine |
| Workability | excellent - very soft |
| Resinous | No |
| Thermal Conductivity | 0.11 W/(m·K) |
| Specific Heat | 1750 J/(kg·K) |
| Specific Cutting Energy | 0.3 J/mm³ |
| Hardness Scale | 0.15 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 6000 mm/min |
| Finishing Feed Max | 3500 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: low |
| Guitar Uses | body |
| Tone Character | warm, even, pickup-forward |
| Sustainability | sustainable |

<a id="cedar_western_red"></a>
#### Western Red Cedar

**ID:** `cedar_western_red` · **Category:** softwood · **Scientific name:** *Thuja plicata* · **Also known as:** Western Red Cedar

| Property | Value |
|----------|-------|
| Specific Gravity | 0.33 |
| Density | 370 kg/m³ |
| Janka Hardness | 350 lbf / 1557 N |
| Modulus of Rupture | 53.1 MPa |
| Modulus of Elasticity | 7.78 GPa |
| Grain | straight |
| Workability | excellent - very soft |
| Resinous | Yes |
| Shrinkage (radial) | 4.43% |
| Shrinkage (tangential) | 7.69% |
| Thermal Conductivity | 0.1 W/(m·K) |
| Specific Heat | 1850 J/(kg·K) |
| Specific Cutting Energy | 0.22 J/mm³ |
| Hardness Scale | 0.1 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 5500 mm/min |
| Finishing Feed Max | 3200 mm/min |
| RPM Range | 10000–22000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | soundboard |
| Tone Character | warm, dark, immediate response |
| Sustainability | sustainable |

<a id="cocobolo"></a>
#### Cocobolo

**ID:** `cocobolo` · **Category:** hardwood · **Scientific name:** *Dalbergia retusa*

| Property | Value |
|----------|-------|
| Specific Gravity | 1.1 |
| Density | 1095 kg/m³ |
| Janka Hardness | 2960 lbf / 13167 N |
| Grain | irregular, fine texture, striking figure |
| Workability | difficult — very oily, sensitizing dust |
| Resinous | Yes |
| Thermal Conductivity | 0.42 W/(m·K) |
| Specific Heat | 1340 J/(kg·K) |
| Specific Cutting Energy | 0.87 J/mm³ |
| Hardness Scale | 0.85 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 1750 mm/min |
| Finishing Feed Max | 950 mm/min |
| RPM Range | 16800–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: high |
| Guitar Uses | body_top, back_sides, fretboard, bridge |
| Tone Character | warm, rich, complex — among finest rosewoods |
| Sustainability | CITES Appendix II — restricted |

<a id="ebony_african"></a>
#### African Ebony

**ID:** `ebony_african` · **Category:** hardwood · **Scientific name:** *Diospyros crassiflora*

| Property | Value |
|----------|-------|
| Specific Gravity | 1.03 |
| Density | 1030 kg/m³ |
| Janka Hardness | 3080 lbf / 13701 N |
| Grain | straight |
| Workability | difficult - very hard |
| Resinous | No |
| Thermal Conductivity | 0.21 W/(m·K) |
| Specific Heat | 1300 J/(kg·K) |
| Specific Cutting Energy | 0.75 J/mm³ |
| Hardness Scale | 0.95 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 1500 mm/min |
| Finishing Feed Max | 800 mm/min |
| RPM Range | 18000–24000 |
| CNC Risks | Burn: high, Tearout: high, Dust: high |
| Guitar Uses | fretboard, bridge, nuts |
| Tone Character | bright, articulate, percussive |
| Sustainability | endangered, use alternatives |

<a id="ebony_macassar"></a>
#### Macassar Ebony

**ID:** `ebony_macassar` · **Category:** hardwood · **Scientific name:** *Diospyros celebica* · **Also known as:** Macassar Ebony

| Property | Value |
|----------|-------|
| Specific Gravity | 1.09 |
| Density | 1120 kg/m³ |
| Janka Hardness | 3220 lbf / 14323 N |
| Grain | striped |
| Workability | difficult |
| Resinous | No |
| Thermal Conductivity | 0.22 W/(m·K) |
| Specific Heat | 1250 J/(kg·K) |
| Specific Cutting Energy | 0.8 J/mm³ |
| Hardness Scale | 1.0 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 1200 mm/min |
| Finishing Feed Max | 700 mm/min |
| RPM Range | 18000–24000 |
| CNC Risks | Burn: high, Tearout: high, Dust: high |
| Guitar Uses | fretboard, bridge, decorative |
| Tone Character | bright, defined |
| Sustainability | vulnerable |

<a id="koa"></a>
#### Hawaiian Koa

**ID:** `koa` · **Category:** hardwood · **Scientific name:** *Acacia koa*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.6 |
| Density | 625 kg/m³ |
| Janka Hardness | 1170 lbf / 5204 N |
| Modulus of Rupture | 87.0 MPa |
| Modulus of Elasticity | 10.37 GPa |
| Grain | interlocked, often highly figured |
| Workability | moderate |
| Resinous | No |
| Thermal Conductivity | 0.15 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.5 J/mm³ |
| Hardness Scale | 0.55 |
| Burn Tendency | 0.35 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: low |
| Guitar Uses | body, back_sides, soundboard |
| Tone Character | warm, balanced, opens up with age like rosewood |
| Sustainability | limited supply, plantation-grown increasing |

<a id="mahogany_african"></a>
#### African Mahogany (Khaya)

**ID:** `mahogany_african` · **Category:** hardwood · **Scientific name:** *Khaya spp.* · **Also known as:** African Mahogany

| Property | Value |
|----------|-------|
| Specific Gravity | 0.5 |
| Density | 530 kg/m³ |
| Janka Hardness | 830 lbf / 3692 N |
| Grain | interlocked |
| Workability | good |
| Resinous | No |
| Thermal Conductivity | 0.12 W/(m·K) |
| Specific Heat | 1600 J/(kg·K) |
| Specific Cutting Energy | 0.45 J/mm³ |
| Hardness Scale | 0.42 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | body, neck |
| Tone Character | similar to honduran, slightly brighter |
| Sustainability | sustainable alternative |

<a id="mahogany_honduran"></a>
#### Honduran Mahogany

**ID:** `mahogany_honduran` · **Category:** hardwood · **Scientific name:** *Swietenia macrophylla* · **Also known as:** Honduran Mahogany

| Property | Value |
|----------|-------|
| Specific Gravity | 0.52 |
| Density | 545 kg/m³ |
| Janka Hardness | 800 lbf / 3558 N |
| Modulus of Rupture | 98.4 MPa |
| Modulus of Elasticity | 11.97 GPa |
| Grain | interlocked |
| Workability | excellent |
| Resinous | No |
| Shrinkage (radial) | 4.41% |
| Shrinkage (tangential) | 8.41% |
| Thermal Conductivity | 0.12 W/(m·K) |
| Specific Heat | 1600 J/(kg·K) |
| Specific Cutting Energy | 0.45 J/mm³ |
| Hardness Scale | 0.4 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | body, neck, back_sides |
| Tone Character | warm, balanced, good sustain |
| Sustainability | CITES Appendix II |

<a id="maple_hard"></a>
#### Hard Maple (Sugar Maple)

**ID:** `maple_hard` · **Category:** hardwood · **Scientific name:** *Acer saccharum* · **Also known as:** Hard Maple

| Property | Value |
|----------|-------|
| Specific Gravity | 0.66 |
| Density | 705 kg/m³ |
| Janka Hardness | 1450 lbf / 6450 N |
| Modulus of Rupture | 118.5 MPa |
| Modulus of Elasticity | 13.49 GPa |
| Grain | straight to figured |
| Workability | moderate - hard on tools |
| Resinous | No |
| Shrinkage (radial) | 4.82% |
| Shrinkage (tangential) | 8.73% |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.55 J/mm³ |
| Hardness Scale | 0.7 |
| Burn Tendency | 0.6 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 3000 mm/min |
| Finishing Feed Max | 2000 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: high, Tearout: low, Dust: low |
| Guitar Uses | neck, top, fretboard |
| Tone Character | bright, articulate, snappy |
| Sustainability | sustainable |

<a id="maple_soft"></a>
#### Soft Maple (Red Maple)

**ID:** `maple_soft` · **Category:** hardwood · **Scientific name:** *Acer rubrum*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.56 |
| Density | 610 kg/m³ |
| Janka Hardness | 950 lbf / 4226 N |
| Grain | straight to figured |
| Workability | good |
| Resinous | No |
| Thermal Conductivity | 0.15 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.48 J/mm³ |
| Hardness Scale | 0.5 |
| Burn Tendency | 0.4 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: low |
| Guitar Uses | body, back_sides |
| Tone Character | warm maple tone, less bright than hard |
| Sustainability | sustainable |

<a id="rosewood_brazilian"></a>
#### Brazilian Rosewood

**ID:** `rosewood_brazilian` · **Category:** hardwood · **Scientific name:** *Dalbergia nigra* · **Also known as:** Brazilian Rosewood

| Property | Value |
|----------|-------|
| Specific Gravity | 0.82 |
| Density | 835 kg/m³ |
| Janka Hardness | 2790 lbf / 12411 N |
| Grain | interlocked |
| Workability | moderate |
| Resinous | Yes |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1400 J/(kg·K) |
| Specific Cutting Energy | 0.65 J/mm³ |
| Hardness Scale | 0.85 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 1800 mm/min |
| Finishing Feed Max | 1000 mm/min |
| RPM Range | 16000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: high |
| Guitar Uses | fretboard, back_sides |
| Tone Character | rich, complex, legendary |
| Sustainability | CITES Appendix I - highly restricted |

<a id="rosewood_east_indian"></a>
#### East Indian Rosewood

**ID:** `rosewood_east_indian` · **Category:** hardwood · **Scientific name:** *Dalbergia latifolia* · **Also known as:** East Indian Rosewood

| Property | Value |
|----------|-------|
| Specific Gravity | 0.8 |
| Density | 830 kg/m³ |
| Janka Hardness | 2440 lbf / 10854 N |
| Grain | interlocked |
| Workability | moderate - oily, dulls tools |
| Resinous | Yes |
| Thermal Conductivity | 0.17 W/(m·K) |
| Specific Heat | 1400 J/(kg·K) |
| Specific Cutting Energy | 0.6 J/mm³ |
| Hardness Scale | 0.8 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 2000 mm/min |
| Finishing Feed Max | 1200 mm/min |
| RPM Range | 16000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: high |
| Guitar Uses | fretboard, back_sides, bridge |
| Tone Character | warm, complex overtones, sustain |
| Sustainability | CITES regulated |

<a id="spruce_adirondack"></a>
#### Adirondack Spruce (Red Spruce)

**ID:** `spruce_adirondack` · **Category:** softwood · **Scientific name:** *Picea rubens* · **Also known as:** Red Spruce

| Property | Value |
|----------|-------|
| Specific Gravity | 0.43 |
| Density | 435 kg/m³ |
| Janka Hardness | 560 lbf / 2491 N |
| Modulus of Rupture | 74.0 MPa |
| Modulus of Elasticity | 11.2 GPa |
| Grain | straight, tight |
| Workability | good |
| Resinous | Yes |
| Shrinkage (radial) | 3.0% |
| Shrinkage (tangential) | 6.9% |
| Thermal Conductivity | 0.19 W/(m·K) |
| Specific Heat | 1742 J/(kg·K) |
| Specific Cutting Energy | 0.43 J/mm³ |
| Hardness Scale | 0.16 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 5200 mm/min |
| Finishing Feed Max | 3020 mm/min |
| RPM Range | 11280–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: low |
| Guitar Uses | soundboard |
| Tone Character | powerful, headroom, loud — the pre-war dreadnought tonewood |
| Sustainability | limited supply — slow-growing |

<a id="spruce_engelmann"></a>
#### Engelmann Spruce

**ID:** `spruce_engelmann` · **Category:** softwood · **Scientific name:** *Picea engelmannii* · **Also known as:** Engelmann Spruce

| Property | Value |
|----------|-------|
| Specific Gravity | 0.37 |
| Density | 385 kg/m³ |
| Janka Hardness | 390 lbf / 1735 N |
| Grain | straight, fine |
| Workability | good - very soft |
| Resinous | Yes |
| Thermal Conductivity | 0.11 W/(m·K) |
| Specific Heat | 1800 J/(kg·K) |
| Specific Cutting Energy | 0.25 J/mm³ |
| Hardness Scale | 0.15 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.65 |
| Roughing Feed Max | 5000 mm/min |
| Finishing Feed Max | 3000 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: low |
| Guitar Uses | soundboard |
| Tone Character | warm, responsive, lower overtones than Sitka |
| Sustainability | sustainable |

<a id="spruce_european"></a>
#### European Spruce (Alpine/German)

**ID:** `spruce_european` · **Category:** softwood · **Scientific name:** *Picea abies*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.4 |
| Density | 405 kg/m³ |
| Janka Hardness | 490 lbf / 2180 N |
| Modulus of Rupture | 65.0 MPa |
| Modulus of Elasticity | 9.5 GPa |
| Grain | straight, very tight, stiff |
| Workability | good — soft but stiff |
| Resinous | Yes |
| Shrinkage (radial) | 2.8% |
| Shrinkage (tangential) | 6.8% |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1760 J/(kg·K) |
| Specific Cutting Energy | 0.41 J/mm³ |
| Hardness Scale | 0.14 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.6 |
| Roughing Feed Max | 5300 mm/min |
| Finishing Feed Max | 3080 mm/min |
| RPM Range | 11120–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: low |
| Guitar Uses | soundboard |
| Tone Character | warm, complex, refined — the classical luthier's choice |
| Sustainability | sustainable — European plantations |

<a id="spruce_sitka"></a>
#### Sitka Spruce

**ID:** `spruce_sitka` · **Category:** softwood · **Scientific name:** *Picea sitchensis* · **Also known as:** Sitka Spruce

| Property | Value |
|----------|-------|
| Specific Gravity | 0.42 |
| Density | 425 kg/m³ |
| Janka Hardness | 510 lbf / 2269 N |
| Grain | straight, tight |
| Workability | good - soft |
| Resinous | Yes |
| Thermal Conductivity | 0.12 W/(m·K) |
| Specific Heat | 1800 J/(kg·K) |
| Specific Cutting Energy | 0.28 J/mm³ |
| Hardness Scale | 0.2 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.6 |
| Roughing Feed Max | 4500 mm/min |
| Finishing Feed Max | 2800 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: low |
| Guitar Uses | soundboard |
| Tone Character | versatile, strong fundamental |
| Sustainability | sustainable |

<a id="walnut_black"></a>
#### Black Walnut

**ID:** `walnut_black` · **Category:** hardwood · **Scientific name:** *Juglans nigra* · **Also known as:** Black Walnut

| Property | Value |
|----------|-------|
| Specific Gravity | 0.56 |
| Density | 610 kg/m³ |
| Janka Hardness | 1010 lbf / 4493 N |
| Modulus of Rupture | 90.7 MPa |
| Modulus of Elasticity | 11.34 GPa |
| Grain | straight to figured |
| Workability | excellent |
| Resinous | No |
| Shrinkage (radial) | 4.3% |
| Shrinkage (tangential) | 8.29% |
| Thermal Conductivity | 0.14 W/(m·K) |
| Specific Heat | 1700 J/(kg·K) |
| Specific Cutting Energy | 0.45 J/mm³ |
| Hardness Scale | 0.5 |
| Burn Tendency | 0.25 |
| Tearout Tendency | 0.25 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: medium |
| Guitar Uses | body, back_sides |
| Tone Character | warm, rich mids, mahogany-like |
| Sustainability | sustainable |

---

## Established Guitar Woods

*Proven guitar woods in regular use by luthiers, with well-understood tonal and machining characteristics.*

| # | Species | Scientific Name | Type | SG | Density | Janka | MOR | MOE | k |
|--:|---------|-----------------|------|----|---------|-------|-----|-----|---|
| 1 | **White Ash** | *Fraxinus americana* | H | 0.63 | 670 | 1320 | — | — | 0.17 |
| 2 | **American Beech** | *Fagus grandifolia* | H | 0.68 | 720 | 1300 | — | — | 0.18 |
| 3 | **Yellow Birch** | *Betula alleghaniensis* | H | 0.66 | 690 | 1260 | — | — | 0.18 |
| 4 | **Bocote** | *Cordia elaeagnoides* | H | 0.75 | 775 | 2200 | 114.4 | 12.19 | 0.3 |
| 5 | **Bubinga** | *Guibourtia demeusei* | H | 0.86 | 890 | 2410 | 168.3 | 18.41 | 0.34 |
| 6 | **Spanish Cedar** | *Cedrela odorata* | H | 0.43 | 450 | 600 | 78.0 | 9.7 | 0.19 |
| 7 | **Black Cherry** | *Prunus serotina* | H | 0.53 | 560 | 950 | 78.0 | 10.24 | 0.15 |
| 8 | **Bald Cypress** | *Taxodium distichum* | S | 0.46 | 510 | 510 | 73.1 | 9.93 | 0.14 |
| 9 | **Douglas-Fir** | *Pseudotsuga menziesii* | S | 0.51 | 530 | 660 | 75.3 | 10.0 | 0.14 |
| 10 | **Granadillo** | *Platymiscium yucatanum* | H | 0.9 | 925 | 2790 | — | — | 0.35 |
| 11 | **Ipe (Brazilian Walnut)** | *Handroanthus spp.* | H | 1.08 | 1100 | 3510 | 168.6 | 16.7 | 0.25 |
| 12 | **Iroko** | *Milicia excelsa* | H | 0.63 | 660 | 1260 | 97.1 | 10.9 | 0.26 |
| 13 | **Jatoba (Brazilian Cherry)** | *Hymenaea courbaril* | H | 0.83 | 910 | 2690 | 126.9 | 14.07 | 0.22 |
| 14 | **Katalox (Mexican Ebony)** | *Swartzia cubensis* | H | 1.05 | 1050 | 3650 | — | — | 0.41 |
| 15 | **Merbau (Kwila)** | *Intsia bijuga* | H | 0.8 | 830 | 2460 | 145.2 | 15.93 | 0.32 |
| 16 | **Northern Red Oak** | *Quercus rubra* | H | 0.65 | 700 | 1290 | 123.1 | 13.82 | 0.18 |
| 17 | **White Oak** | *Quercus alba* | H | 0.72 | 770 | 1360 | 144.7 | 15.26 | 0.19 |
| 18 | **Ovangkol (Shedua)** | *Guibourtia ehie* | H | 0.78 | 810 | 1890 | 140.3 | 18.6 | 0.31 |
| 19 | **Pau Ferro (Bolivian Rosewood)** | *Machaerium scleroxylon* | H | 0.85 | 880 | 2030 | 131.0 | 14.0 | 0.34 |
| 20 | **Eastern White Pine** | *Pinus strobus* | S | 0.37 | 385 | 380 | — | — | 0.11 |
| 21 | **Yellow Poplar (Tulipwood)** | *Liriodendron tulipifera* | H | 0.46 | 450 | 540 | — | — | 0.13 |
| 22 | **Purpleheart** | *Peltogyne paniculata* | H | 0.86 | 880 | 2520 | 168.6 | 16.7 | 0.23 |
| 23 | **Redwood (Old Growth)** | *Sequoia sempervirens* | S | 0.41 | 420 | 420 | 60.3 | 8.55 | 0.12 |
| 24 | **Sapele** | *Entandrophragma cylindricum* | H | 0.62 | 640 | 1510 | 99.4 | 12.04 | 0.17 |
| 25 | **White Spruce** | *Picea glauca* | S | 0.4 | 410 | 480 | 65.5 | 9.7 | 0.18 |
| 26 | **Tasmanian Blackwood** | *Acacia melanoxylon* | H | 0.58 | 640 | 1160 | 96.5 | 11.82 | 0.17 |
| 27 | **Teak** | *Tectona grandis* | H | 0.63 | 655 | 1155 | 97.1 | 12.28 | 0.26 |
| 28 | **Wenge** | *Millettia laurentii* | H | 0.81 | 870 | 1930 | 136.9 | 14.75 | 0.22 |
| 29 | **Zebrawood** | *Microberlinia brazzavillensis* | H | 0.75 | 785 | 1575 | 124.1 | 13.88 | 0.21 |
| 30 | **Ziricote** | *Cordia dodecandra* | H | 0.79 | 815 | 1900 | — | — | 0.32 |

### Detailed Profiles

<a id="ash_white"></a>
#### White Ash

**ID:** `ash_white` · **Category:** hardwood · **Scientific name:** *Fraxinus americana* · **Also known as:** White Ash

| Property | Value |
|----------|-------|
| Specific Gravity | 0.63 |
| Density | 670 kg/m³ |
| Janka Hardness | 1320 lbf / 5872 N |
| Grain | prominent, open pore |
| Workability | good |
| Resinous | No |
| Thermal Conductivity | 0.17 W/(m·K) |
| Specific Heat | 1700 J/(kg·K) |
| Specific Cutting Energy | 0.5 J/mm³ |
| Hardness Scale | 0.6 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: medium |
| Guitar Uses | body |
| Tone Character | bright, aggressive, strong mids |
| Sustainability | declining (emerald ash borer) |

<a id="beech_american"></a>
#### American Beech

**ID:** `beech_american` · **Category:** hardwood · **Scientific name:** *Fagus grandifolia* · **Also known as:** American Beech

| Property | Value |
|----------|-------|
| Specific Gravity | 0.68 |
| Density | 720 kg/m³ |
| Janka Hardness | 1300 lbf / 5783 N |
| Grain | straight, fine |
| Workability | moderate |
| Resinous | No |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.52 J/mm³ |
| Hardness Scale | 0.62 |
| Burn Tendency | 0.5 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 3200 mm/min |
| Finishing Feed Max | 2000 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: low |
| Guitar Uses | back_sides |
| Tone Character | bright, even, good projection |
| Sustainability | sustainable |

<a id="birch_yellow"></a>
#### Yellow Birch

**ID:** `birch_yellow` · **Category:** hardwood · **Scientific name:** *Betula alleghaniensis* · **Also known as:** Yellow Birch

| Property | Value |
|----------|-------|
| Specific Gravity | 0.66 |
| Density | 690 kg/m³ |
| Janka Hardness | 1260 lbf / 5604 N |
| Grain | straight to wavy |
| Workability | moderate |
| Resinous | No |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.5 J/mm³ |
| Hardness Scale | 0.62 |
| Burn Tendency | 0.4 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: low |
| Guitar Uses | body, back_sides |
| Tone Character | bright, articulate, maple-like |
| Sustainability | sustainable |

<a id="bocote"></a>
#### Bocote

**ID:** `bocote` · **Category:** hardwood · **Scientific name:** *Cordia elaeagnoides*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.75 |
| Density | 775 kg/m³ |
| Janka Hardness | 2200 lbf / 9786 N |
| Modulus of Rupture | 114.4 MPa |
| Modulus of Elasticity | 12.19 GPa |
| Grain | straight to wild, dramatic figure |
| Workability | moderate — oily |
| Resinous | Yes |
| Thermal Conductivity | 0.3 W/(m·K) |
| Specific Heat | 1550 J/(kg·K) |
| Specific Cutting Energy | 0.64 J/mm³ |
| Hardness Scale | 0.63 |
| Burn Tendency | 0.25 |
| Tearout Tendency | 0.35 |
| Roughing Feed Max | 2850 mm/min |
| Finishing Feed Max | 1610 mm/min |
| RPM Range | 15040–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | fretboard, body_top, accent |
| Tone Character | bright, snappy, great visual impact |
| Sustainability | not threatened |

<a id="bubinga"></a>
#### Bubinga

**ID:** `bubinga` · **Category:** hardwood · **Scientific name:** *Guibourtia demeusei*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.86 |
| Density | 890 kg/m³ |
| Janka Hardness | 2410 lbf / 10720 N |
| Modulus of Rupture | 168.3 MPa |
| Modulus of Elasticity | 18.41 GPa |
| Grain | interlocked, often pommelé figure |
| Workability | moderate — hard but clean-cutting |
| Resinous | No |
| Thermal Conductivity | 0.34 W/(m·K) |
| Specific Heat | 1484 J/(kg·K) |
| Specific Cutting Energy | 0.71 J/mm³ |
| Hardness Scale | 0.69 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.4 |
| Roughing Feed Max | 2550 mm/min |
| Finishing Feed Max | 1430 mm/min |
| RPM Range | 15520–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: high |
| Guitar Uses | body_top, body, back_sides, neck_laminate |
| Tone Character | warm, rich bass, articulate mids — prized for bass guitars |
| Sustainability | CITES Appendix II since 2017 |

<a id="cedar_spanish"></a>
#### Spanish Cedar

**ID:** `cedar_spanish` · **Category:** hardwood · **Scientific name:** *Cedrela odorata* · **Also known as:** Spanish Cedar

| Property | Value |
|----------|-------|
| Specific Gravity | 0.43 |
| Density | 450 kg/m³ |
| Janka Hardness | 600 lbf / 2669 N |
| Modulus of Rupture | 78.0 MPa |
| Modulus of Elasticity | 9.7 GPa |
| Grain | straight, medium to coarse |
| Workability | excellent — very easy to work |
| Resinous | Yes |
| Shrinkage (radial) | 4.2% |
| Shrinkage (tangential) | 6.3% |
| Thermal Conductivity | 0.19 W/(m·K) |
| Specific Heat | 1742 J/(kg·K) |
| Specific Cutting Energy | 0.43 J/mm³ |
| Hardness Scale | 0.17 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.35 |
| Roughing Feed Max | 5150 mm/min |
| Finishing Feed Max | 2990 mm/min |
| RPM Range | 11360–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: low |
| Guitar Uses | neck |
| Tone Character | warm — traditional classical guitar neck wood |
| Sustainability | CITES Appendix III — plantation-grown available |

<a id="cherry_black"></a>
#### Black Cherry

**ID:** `cherry_black` · **Category:** hardwood · **Scientific name:** *Prunus serotina* · **Also known as:** Black Cherry

| Property | Value |
|----------|-------|
| Specific Gravity | 0.53 |
| Density | 560 kg/m³ |
| Janka Hardness | 950 lbf / 4226 N |
| Modulus of Rupture | 78.0 MPa |
| Modulus of Elasticity | 10.24 GPa |
| Grain | straight, fine |
| Workability | excellent |
| Resinous | No |
| Shrinkage (radial) | 4.19% |
| Shrinkage (tangential) | 8.09% |
| Thermal Conductivity | 0.15 W/(m·K) |
| Specific Heat | 1700 J/(kg·K) |
| Specific Cutting Energy | 0.45 J/mm³ |
| Hardness Scale | 0.45 |
| Burn Tendency | 0.5 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: low |
| Guitar Uses | body, back_sides |
| Tone Character | warm, sweet mids, similar to mahogany |
| Sustainability | sustainable |

<a id="cypress_bald"></a>
#### Bald Cypress

**ID:** `cypress_bald` · **Category:** softwood · **Scientific name:** *Taxodium distichum* · **Also known as:** Bald Cypress

| Property | Value |
|----------|-------|
| Specific Gravity | 0.46 |
| Density | 510 kg/m³ |
| Janka Hardness | 510 lbf / 2269 N |
| Modulus of Rupture | 73.1 MPa |
| Modulus of Elasticity | 9.93 GPa |
| Grain | straight |
| Workability | excellent |
| Resinous | Yes |
| Shrinkage (radial) | 3.8% |
| Shrinkage (tangential) | 6.2% |
| Thermal Conductivity | 0.14 W/(m·K) |
| Specific Heat | 1800 J/(kg·K) |
| Specific Cutting Energy | 0.3 J/mm³ |
| Hardness Scale | 0.2 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 5000 mm/min |
| Finishing Feed Max | 3000 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: low |
| Guitar Uses | back_sides |
| Tone Character | dry, percussive, bright — quintessential flamenco tonewood |
| Sustainability | sustainable |

<a id="douglas_fir"></a>
#### Douglas-Fir

**ID:** `douglas_fir` · **Category:** softwood · **Scientific name:** *Pseudotsuga menziesii*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.51 |
| Density | 530 kg/m³ |
| Janka Hardness | 660 lbf / 2936 N |
| Modulus of Rupture | 75.3 MPa |
| Modulus of Elasticity | 10.0 GPa |
| Grain | straight, pronounced growth rings |
| Workability | good |
| Resinous | Yes |
| Shrinkage (radial) | 4.18% |
| Shrinkage (tangential) | 8.05% |
| Thermal Conductivity | 0.14 W/(m·K) |
| Specific Heat | 1750 J/(kg·K) |
| Specific Cutting Energy | 0.32 J/mm³ |
| Hardness Scale | 0.3 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.4 |
| Roughing Feed Max | 4500 mm/min |
| Finishing Feed Max | 2800 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: low |
| Guitar Uses | soundboard, bracing |
| Tone Character | strong, clear, good for steel-string |
| Sustainability | sustainable, abundant |

<a id="granadillo"></a>
#### Granadillo

**ID:** `granadillo` · **Category:** hardwood · **Scientific name:** *Platymiscium yucatanum*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.9 |
| Density | 925 kg/m³ |
| Janka Hardness | 2790 lbf / 12411 N |
| Grain | straight, fine |
| Workability | moderate — dense but clean-cutting |
| Resinous | No |
| Thermal Conductivity | 0.35 W/(m·K) |
| Specific Heat | 1460 J/(kg·K) |
| Specific Cutting Energy | 0.74 J/mm³ |
| Hardness Scale | 0.8 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 2000 mm/min |
| Finishing Feed Max | 1100 mm/min |
| RPM Range | 16400–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: high |
| Guitar Uses | fretboard, back_sides, bridge |
| Tone Character | warm, complex, true rosewood character |
| Sustainability | limited supply |

<a id="ipe"></a>
#### Ipe (Brazilian Walnut)

**ID:** `ipe` · **Category:** hardwood · **Scientific name:** *Handroanthus spp.*

| Property | Value |
|----------|-------|
| Specific Gravity | 1.08 |
| Density | 1100 kg/m³ |
| Janka Hardness | 3510 lbf / 15613 N |
| Modulus of Rupture | 168.6 MPa |
| Modulus of Elasticity | 16.7 GPa |
| Grain | fine, interlocked |
| Workability | very difficult — extremely hard, contains lapachol |
| Resinous | Yes |
| Shrinkage (radial) | 5.61% |
| Shrinkage (tangential) | 9.61% |
| Thermal Conductivity | 0.25 W/(m·K) |
| Specific Heat | 1250 J/(kg·K) |
| Specific Cutting Energy | 0.8 J/mm³ |
| Hardness Scale | 0.98 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 1200 mm/min |
| Finishing Feed Max | 700 mm/min |
| RPM Range | 18000–24000 |
| CNC Risks | Burn: high, Tearout: low, Dust: high |
| Guitar Uses | bridge, accent |
| Tone Character | bright, bell-like, extreme sustain |
| Sustainability | threatened in some regions |

<a id="iroko"></a>
#### Iroko

**ID:** `iroko` · **Category:** hardwood · **Scientific name:** *Milicia excelsa*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.63 |
| Density | 660 kg/m³ |
| Janka Hardness | 1260 lbf / 5605 N |
| Modulus of Rupture | 97.1 MPa |
| Modulus of Elasticity | 10.9 GPa |
| Grain | interlocked |
| Workability | good — some interlocked grain tearout |
| Resinous | No |
| Thermal Conductivity | 0.26 W/(m·K) |
| Specific Heat | 1622 J/(kg·K) |
| Specific Cutting Energy | 0.56 J/mm³ |
| Hardness Scale | 0.36 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.45 |
| Roughing Feed Max | 4200 mm/min |
| Finishing Feed Max | 2420 mm/min |
| RPM Range | 12880–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: medium |
| Guitar Uses | body |
| Tone Character | warm, midrange focus, mahogany-like character |
| Sustainability | not threatened — teak substitute |

<a id="jatoba"></a>
#### Jatoba (Brazilian Cherry)

**ID:** `jatoba` · **Category:** hardwood · **Scientific name:** *Hymenaea courbaril*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.83 |
| Density | 910 kg/m³ |
| Janka Hardness | 2690 lbf / 11966 N |
| Modulus of Rupture | 126.9 MPa |
| Modulus of Elasticity | 14.07 GPa |
| Grain | interlocked |
| Workability | difficult — very hard, dulls tools |
| Resinous | No |
| Shrinkage (radial) | 5.01% |
| Shrinkage (tangential) | 8.86% |
| Thermal Conductivity | 0.22 W/(m·K) |
| Specific Heat | 1400 J/(kg·K) |
| Specific Cutting Energy | 0.65 J/mm³ |
| Hardness Scale | 0.83 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 1800 mm/min |
| Finishing Feed Max | 1000 mm/min |
| RPM Range | 16000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: medium |
| Guitar Uses | fretboard |
| Tone Character | bright, percussive, similar to rosewood but less complex |
| Sustainability | not threatened — common budget rosewood alternative |

<a id="katalox"></a>
#### Katalox (Mexican Ebony)

**ID:** `katalox` · **Category:** hardwood · **Scientific name:** *Swartzia cubensis*

| Property | Value |
|----------|-------|
| Specific Gravity | 1.05 |
| Density | 1050 kg/m³ |
| Janka Hardness | 3650 lbf / 16236 N |
| Grain | straight, very fine |
| Workability | very difficult — extremely hard |
| Resinous | No |
| Thermal Conductivity | 0.41 W/(m·K) |
| Specific Heat | 1370 J/(kg·K) |
| Specific Cutting Energy | 0.83 J/mm³ |
| Hardness Scale | 1.0 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.15 |
| Roughing Feed Max | 1200 mm/min |
| Finishing Feed Max | 700 mm/min |
| RPM Range | 18000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: high |
| Guitar Uses | fretboard, bridge |
| Tone Character | bright, bell-like — ebony alternative |
| Sustainability | not threatened — ebony substitute |

<a id="merbau"></a>
#### Merbau (Kwila)

**ID:** `merbau` · **Category:** hardwood · **Scientific name:** *Intsia bijuga*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.8 |
| Density | 830 kg/m³ |
| Janka Hardness | 2460 lbf / 10943 N |
| Modulus of Rupture | 145.2 MPa |
| Modulus of Elasticity | 15.93 GPa |
| Grain | interlocked, coarse |
| Workability | moderate — yellow deposits in pores |
| Resinous | No |
| Thermal Conductivity | 0.32 W/(m·K) |
| Specific Heat | 1520 J/(kg·K) |
| Specific Cutting Energy | 0.67 J/mm³ |
| Hardness Scale | 0.7 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.35 |
| Roughing Feed Max | 2500 mm/min |
| Finishing Feed Max | 1400 mm/min |
| RPM Range | 15600–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | fretboard, body |
| Tone Character | warm, rosewood-like with stronger mids |
| Sustainability | vulnerable in some regions |

<a id="oak_red"></a>
#### Northern Red Oak

**ID:** `oak_red` · **Category:** hardwood · **Scientific name:** *Quercus rubra* · **Also known as:** Red Oak

| Property | Value |
|----------|-------|
| Specific Gravity | 0.65 |
| Density | 700 kg/m³ |
| Janka Hardness | 1290 lbf / 5736 N |
| Modulus of Rupture | 123.1 MPa |
| Modulus of Elasticity | 13.82 GPa |
| Grain | prominent, ring-porous |
| Workability | moderate |
| Resinous | No |
| Shrinkage (radial) | 4.92% |
| Shrinkage (tangential) | 8.8% |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.52 J/mm³ |
| Hardness Scale | 0.62 |
| Burn Tendency | 0.35 |
| Tearout Tendency | 0.6 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: medium, Tearout: high, Dust: medium |
| Guitar Uses | body |
| Tone Character | bright, raw, open-grain character |
| Sustainability | sustainable |

<a id="oak_white"></a>
#### White Oak

**ID:** `oak_white` · **Category:** hardwood · **Scientific name:** *Quercus alba* · **Also known as:** White Oak

| Property | Value |
|----------|-------|
| Specific Gravity | 0.72 |
| Density | 770 kg/m³ |
| Janka Hardness | 1360 lbf / 6049 N |
| Modulus of Rupture | 144.7 MPa |
| Modulus of Elasticity | 15.26 GPa |
| Grain | prominent, ring-porous |
| Workability | moderate |
| Resinous | No |
| Shrinkage (radial) | 5.39% |
| Shrinkage (tangential) | 9.16% |
| Thermal Conductivity | 0.19 W/(m·K) |
| Specific Heat | 1600 J/(kg·K) |
| Specific Cutting Energy | 0.55 J/mm³ |
| Hardness Scale | 0.65 |
| Burn Tendency | 0.4 |
| Tearout Tendency | 0.6 |
| Roughing Feed Max | 3200 mm/min |
| Finishing Feed Max | 2000 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: medium, Tearout: high, Dust: medium |
| Guitar Uses | body |
| Tone Character | bright, aggressive, pronounced highs |
| Sustainability | sustainable |

<a id="ovangkol"></a>
#### Ovangkol (Shedua)

**ID:** `ovangkol` · **Category:** hardwood · **Scientific name:** *Guibourtia ehie*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.78 |
| Density | 810 kg/m³ |
| Janka Hardness | 1890 lbf / 8407 N |
| Modulus of Rupture | 140.3 MPa |
| Modulus of Elasticity | 18.6 GPa |
| Grain | interlocked, figure common |
| Workability | moderate — interlocked grain tearout |
| Resinous | No |
| Thermal Conductivity | 0.31 W/(m·K) |
| Specific Heat | 1532 J/(kg·K) |
| Specific Cutting Energy | 0.66 J/mm³ |
| Hardness Scale | 0.54 |
| Burn Tendency | 0.25 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 3300 mm/min |
| Finishing Feed Max | 1880 mm/min |
| RPM Range | 14320–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: medium |
| Guitar Uses | back_sides, body |
| Tone Character | warm, complex — rosewood family character |
| Sustainability | not threatened |

<a id="pau_ferro"></a>
#### Pau Ferro (Bolivian Rosewood)

**ID:** `pau_ferro` · **Category:** hardwood · **Scientific name:** *Machaerium scleroxylon*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.85 |
| Density | 880 kg/m³ |
| Janka Hardness | 2030 lbf / 9030 N |
| Modulus of Rupture | 131.0 MPa |
| Modulus of Elasticity | 14.0 GPa |
| Grain | straight to irregular, fine texture |
| Workability | moderate — oily |
| Resinous | Yes |
| Thermal Conductivity | 0.34 W/(m·K) |
| Specific Heat | 1490 J/(kg·K) |
| Specific Cutting Energy | 0.7 J/mm³ |
| Hardness Scale | 0.58 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 3100 mm/min |
| Finishing Feed Max | 1760 mm/min |
| RPM Range | 14640–24000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: high |
| Guitar Uses | fretboard, back_sides |
| Tone Character | bright, rosewood-like, slightly more mid-forward |
| Sustainability | not CITES listed — popular rosewood substitute |

<a id="pine_eastern_white"></a>
#### Eastern White Pine

**ID:** `pine_eastern_white` · **Category:** softwood · **Scientific name:** *Pinus strobus*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.37 |
| Density | 385 kg/m³ |
| Janka Hardness | 380 lbf / 1690 N |
| Grain | straight |
| Workability | excellent |
| Resinous | Yes |
| Thermal Conductivity | 0.11 W/(m·K) |
| Specific Heat | 1800 J/(kg·K) |
| Specific Cutting Energy | 0.25 J/mm³ |
| Hardness Scale | 0.12 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 5500 mm/min |
| Finishing Feed Max | 3200 mm/min |
| RPM Range | 10000–22000 |
| CNC Risks | Burn: low, Tearout: medium, Dust: low |
| Guitar Uses | body |
| Tone Character | warm, resonant when aged — cigar box guitar tradition |
| Sustainability | sustainable, abundant |

<a id="poplar_yellow"></a>
#### Yellow Poplar (Tulipwood)

**ID:** `poplar_yellow` · **Category:** hardwood · **Scientific name:** *Liriodendron tulipifera* · **Also known as:** Yellow Poplar

| Property | Value |
|----------|-------|
| Specific Gravity | 0.46 |
| Density | 450 kg/m³ |
| Janka Hardness | 540 lbf / 2402 N |
| Grain | straight |
| Workability | excellent |
| Resinous | No |
| Thermal Conductivity | 0.13 W/(m·K) |
| Specific Heat | 1750 J/(kg·K) |
| Specific Cutting Energy | 0.33 J/mm³ |
| Hardness Scale | 0.22 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 5000 mm/min |
| Finishing Feed Max | 3000 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: low |
| Guitar Uses | body |
| Tone Character | neutral, similar to alder but less defined |
| Sustainability | sustainable, abundant |

<a id="purpleheart"></a>
#### Purpleheart

**ID:** `purpleheart` · **Category:** hardwood · **Scientific name:** *Peltogyne paniculata*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.86 |
| Density | 880 kg/m³ |
| Janka Hardness | 2520 lbf / 11210 N |
| Modulus of Rupture | 168.6 MPa |
| Modulus of Elasticity | 16.7 GPa |
| Grain | straight to interlocked |
| Workability | moderate — turns purple when cut, gummy when heated |
| Resinous | No |
| Shrinkage (radial) | 5.61% |
| Shrinkage (tangential) | 9.61% |
| Thermal Conductivity | 0.23 W/(m·K) |
| Specific Heat | 1350 J/(kg·K) |
| Specific Cutting Energy | 0.7 J/mm³ |
| Hardness Scale | 0.82 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 2000 mm/min |
| Finishing Feed Max | 1200 mm/min |
| RPM Range | 16000–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: medium |
| Guitar Uses | neck_laminate, accent, fretboard |
| Tone Character | bright, strong sustain, mid-forward |
| Sustainability | not threatened |

<a id="redwood"></a>
#### Redwood (Old Growth)

**ID:** `redwood` · **Category:** softwood · **Scientific name:** *Sequoia sempervirens*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.41 |
| Density | 420 kg/m³ |
| Janka Hardness | 420 lbf / 1868 N |
| Modulus of Rupture | 60.3 MPa |
| Modulus of Elasticity | 8.55 GPa |
| Grain | straight, fine |
| Workability | excellent |
| Resinous | No |
| Shrinkage (radial) | 4.28% |
| Shrinkage (tangential) | 7.81% |
| Thermal Conductivity | 0.12 W/(m·K) |
| Specific Heat | 1800 J/(kg·K) |
| Specific Cutting Energy | 0.28 J/mm³ |
| Hardness Scale | 0.18 |
| Burn Tendency | 0.1 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 5000 mm/min |
| Finishing Feed Max | 3000 mm/min |
| RPM Range | 10000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: low |
| Guitar Uses | soundboard, body |
| Tone Character | warm, dark, cedar-like response |
| Sustainability | old growth restricted — salvage/reclaimed only |

<a id="sapele"></a>
#### Sapele

**ID:** `sapele` · **Category:** hardwood · **Scientific name:** *Entandrophragma cylindricum*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.62 |
| Density | 640 kg/m³ |
| Janka Hardness | 1510 lbf / 6715 N |
| Modulus of Rupture | 99.4 MPa |
| Modulus of Elasticity | 12.04 GPa |
| Grain | interlocked, ribbon figure |
| Workability | good — some tearout on interlocked grain |
| Resinous | No |
| Shrinkage (radial) | 4.43% |
| Shrinkage (tangential) | 8.42% |
| Thermal Conductivity | 0.17 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.48 J/mm³ |
| Hardness Scale | 0.55 |
| Burn Tendency | 0.35 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 3500 mm/min |
| Finishing Feed Max | 2200 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: medium |
| Guitar Uses | body, neck, back_sides |
| Tone Character | like mahogany but brighter, good midrange definition |
| Sustainability | sustainable — most common mahogany alternative |

<a id="spruce_white"></a>
#### White Spruce

**ID:** `spruce_white` · **Category:** softwood · **Scientific name:** *Picea glauca* · **Also known as:** White Spruce

| Property | Value |
|----------|-------|
| Specific Gravity | 0.4 |
| Density | 410 kg/m³ |
| Janka Hardness | 480 lbf / 2135 N |
| Modulus of Rupture | 65.5 MPa |
| Modulus of Elasticity | 9.7 GPa |
| Grain | straight, tight |
| Workability | good |
| Resinous | Yes |
| Shrinkage (radial) | 3.0% |
| Shrinkage (tangential) | 7.0% |
| Thermal Conductivity | 0.18 W/(m·K) |
| Specific Heat | 1760 J/(kg·K) |
| Specific Cutting Energy | 0.41 J/mm³ |
| Hardness Scale | 0.14 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.55 |
| Roughing Feed Max | 5300 mm/min |
| Finishing Feed Max | 3080 mm/min |
| RPM Range | 11120–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: low |
| Guitar Uses | bracing, soundboard |
| Tone Character | bright, even — common bracing wood |
| Sustainability | sustainable, abundant |

<a id="tasmanian_blackwood"></a>
#### Tasmanian Blackwood

**ID:** `tasmanian_blackwood` · **Category:** hardwood · **Scientific name:** *Acacia melanoxylon*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.58 |
| Density | 640 kg/m³ |
| Janka Hardness | 1160 lbf / 5160 N |
| Modulus of Rupture | 96.5 MPa |
| Modulus of Elasticity | 11.82 GPa |
| Grain | straight to wavy, often highly figured |
| Workability | good |
| Resinous | No |
| Shrinkage (radial) | 4.38% |
| Shrinkage (tangential) | 8.38% |
| Thermal Conductivity | 0.17 W/(m·K) |
| Specific Heat | 1650 J/(kg·K) |
| Specific Cutting Energy | 0.45 J/mm³ |
| Hardness Scale | 0.5 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.3 |
| Roughing Feed Max | 4000 mm/min |
| Finishing Feed Max | 2500 mm/min |
| RPM Range | 12000–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: low |
| Guitar Uses | body, back_sides |
| Tone Character | warm, balanced, opens up with age — koa alternative |
| Sustainability | sustainable, plantation-grown in Tasmania and Australia |

<a id="teak"></a>
#### Teak

**ID:** `teak` · **Category:** hardwood · **Scientific name:** *Tectona grandis*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.63 |
| Density | 655 kg/m³ |
| Janka Hardness | 1155 lbf / 5138 N |
| Modulus of Rupture | 97.1 MPa |
| Modulus of Elasticity | 12.28 GPa |
| Grain | straight, oily |
| Workability | good — oily, dulls tools over time |
| Resinous | Yes |
| Thermal Conductivity | 0.26 W/(m·K) |
| Specific Heat | 1622 J/(kg·K) |
| Specific Cutting Energy | 0.56 J/mm³ |
| Hardness Scale | 0.33 |
| Burn Tendency | 0.15 |
| Tearout Tendency | 0.2 |
| Roughing Feed Max | 4350 mm/min |
| Finishing Feed Max | 2510 mm/min |
| RPM Range | 12640–24000 |
| CNC Risks | Burn: low, Tearout: low, Dust: medium |
| Guitar Uses | body, fretboard |
| Tone Character | warm, dry, tight low end |
| Sustainability | plantation-grown widely available |

<a id="wenge"></a>
#### Wenge

**ID:** `wenge` · **Category:** hardwood · **Scientific name:** *Millettia laurentii*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.81 |
| Density | 870 kg/m³ |
| Janka Hardness | 1930 lbf / 8587 N |
| Modulus of Rupture | 136.9 MPa |
| Modulus of Elasticity | 14.75 GPa |
| Grain | straight, very coarse open pore |
| Workability | difficult — splintery, dulls tools |
| Resinous | No |
| Shrinkage (radial) | 5.23% |
| Shrinkage (tangential) | 9.03% |
| Thermal Conductivity | 0.22 W/(m·K) |
| Specific Heat | 1400 J/(kg·K) |
| Specific Cutting Energy | 0.6 J/mm³ |
| Hardness Scale | 0.75 |
| Burn Tendency | 0.2 |
| Tearout Tendency | 0.7 |
| Roughing Feed Max | 2500 mm/min |
| Finishing Feed Max | 1500 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: low, Tearout: high, Dust: high |
| Guitar Uses | neck, fretboard |
| Tone Character | dark, emphasized bass, warm with controlled highs |
| Sustainability | endangered — IUCN listed |

<a id="zebrawood"></a>
#### Zebrawood

**ID:** `zebrawood` · **Category:** hardwood · **Scientific name:** *Microberlinia brazzavillensis*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.75 |
| Density | 785 kg/m³ |
| Janka Hardness | 1575 lbf / 7006 N |
| Modulus of Rupture | 124.1 MPa |
| Modulus of Elasticity | 13.88 GPa |
| Grain | interlocked, distinctive striped figure |
| Workability | moderate — tearout on interlocked grain |
| Resinous | No |
| Shrinkage (radial) | 4.94% |
| Shrinkage (tangential) | 8.82% |
| Thermal Conductivity | 0.21 W/(m·K) |
| Specific Heat | 1500 J/(kg·K) |
| Specific Cutting Energy | 0.55 J/mm³ |
| Hardness Scale | 0.65 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.5 |
| Roughing Feed Max | 3000 mm/min |
| Finishing Feed Max | 1800 mm/min |
| RPM Range | 14000–24000 |
| CNC Risks | Burn: medium, Tearout: medium, Dust: medium |
| Guitar Uses | body_top, body, back_sides |
| Tone Character | bright, articulate, distinctive appearance |
| Sustainability | vulnerable — limited supply |

<a id="ziricote"></a>
#### Ziricote

**ID:** `ziricote` · **Category:** hardwood · **Scientific name:** *Cordia dodecandra*

| Property | Value |
|----------|-------|
| Specific Gravity | 0.79 |
| Density | 815 kg/m³ |
| Janka Hardness | 1900 lbf / 8452 N |
| Grain | irregular, spider-web figure |
| Workability | good — machines cleanly despite density |
| Resinous | No |
| Thermal Conductivity | 0.32 W/(m·K) |
| Specific Heat | 1526 J/(kg·K) |
| Specific Cutting Energy | 0.66 J/mm³ |
| Hardness Scale | 0.54 |
| Burn Tendency | 0.3 |
| Tearout Tendency | 0.25 |
| Roughing Feed Max | 3300 mm/min |
| Finishing Feed Max | 1880 mm/min |
| RPM Range | 14320–24000 |
| CNC Risks | Burn: medium, Tearout: low, Dust: medium |
| Guitar Uses | body_top, back_sides, fretboard |
| Tone Character | warm, complex, rosewood-like with unique character |
| Sustainability | limited supply — slow-growing |

---

## Emerging Alternatives

*Species gaining traction as luthiers seek sustainable, cost-effective, and tonally interesting alternatives to traditional tonewoods.*

| # | Species | Scientific Name | Type | SG | Density | Janka | MOR | MOE | k |
|--:|---------|-----------------|------|----|---------|-------|-----|-----|---|
| 1 | **African Blackwood** | *Dalbergia melanoxylon* | H | 1.27 | 1270 | 1960 | 213.6 | 17.95 | 0.48 |
| 2 | **African Padauk** | *Pterocarpus soyauxii* | H | 0.74 | 745 | 731 | 126.7 | 13.07 | 0.3 |
| 3 | **American Chestnut** | *Castanea dentata* | H | 0.48 | 480 | 324 | 59.3 | 8.48 | 0.21 |
| 4 | **Australian Blackwood** | — | H | 0.64 | 640 | 552 | 103.6 | 14.82 | 0.26 |
| 5 | **Australian Cypress** | *Callitris spp.* | S | 0.65 | 650 | 568 | 79.6 | 9.32 | 0.27 |
| 6 | **Black Locust** | *Robinia pseudoacacia* | H | 0.77 | 770 | 777 | 133.8 | 14.14 | 0.31 |
| 7 | **Black Palm** | *Borassus flabellifer* | H | 0.97 | 970 | 1191 | 137.6 | 15.6 | 0.38 |
| 8 | **Bloodwood** | *Brosimum rubescens* | H | 1.05 | 1050 | 1379 | 174.4 | 20.78 | 0.41 |
| 9 | **Camphor** | *Cinnamomum camphora* | H | 0.52 | 520 | 376 | 80.5 | 11.56 | 0.22 |
| 10 | **Canarywood** | *Centrolobium spp.* | H | 0.83 | 830 | 892 | 131.6 | 14.93 | 0.33 |
| 11 | **Chechen** | *Metopium brownei* | H | 0.88 | 880 | 994 | 93.0 | 15.53 | 0.35 |
| 12 | **Cumaru** | *Dipteryx odorata* | H | 1.08 | 1085 | 1465 | 175.1 | 22.33 | 0.42 |
| 13 | **Curupay** | *Anadenanthera colubrina* | H | 1.02 | 1025 | 1318 | 193.2 | 18.04 | 0.4 |
| 14 | **English Walnut** | *Juglans regia* | H | 0.64 | 640 | 552 | 111.5 | 10.81 | 0.26 |
| 15 | **European Ash** | *Fraxinus excelsior* | H | 0.68 | 680 | 617 | 103.6 | 12.31 | 0.28 |
| 16 | **European Beech** | *Fagus sylvatica* | H | 0.71 | 710 | 668 | 110.1 | 14.31 | 0.29 |
| 17 | **European Yew** | *Taxus baccata* | S | 0.68 | 675 | 609 | 96.8 | 10.15 | 0.28 |
| 18 | **Goncalo Alves** | *Astronium graveolens* | H | 0.91 | 905 | 1047 | 117.0 | 16.56 | 0.36 |
| 19 | **Greenheart** | *Chlorocardium rodiei* | H | 1.01 | 1010 | 1283 | 185.5 | 24.64 | 0.39 |
| 20 | **Huon Pine** | *Lagarostrobos franklinii* | S | 0.56 | 560 | 431 | 76.3 | 9.23 | 0.24 |
| 21 | **Imbuia** | *Ocotea porosa* | H | 0.66 | 660 | 584 | 84.8 | 9.61 | 0.27 |
| 22 | **Jarrah** | *Eucalyptus marginata* | H | 0.83 | 835 | 902 | 108.0 | 14.7 | 0.33 |
| 23 | **Leadwood** | *Combretum imberbe* | H | 1.22 | 1220 | 1820 | 144.5 | 17.2 | 0.47 |
| 24 | **Lignum Vitae** | *Guaiacum officinale* | H | 1.26 | 1260 | 1932 | 123.9 | 17.11 | 0.48 |
| 25 | **Lyptus** | *Eucalyptus grandis × urophylla* | H | 0.85 | 850 | 933 | 118.0 | 14.13 | 0.34 |
| 26 | **Madagascar Rosewood** | *Dalbergia baronii* | H | 0.94 | 935 | 1112 | 165.7 | 12.01 | 0.37 |
| 27 | **Makore** | *Tieghmella heckelii* | H | 0.69 | 685 | 626 | 112.6 | 10.71 | 0.28 |
| 28 | **Mango** | *Mangifera indica* | H | 0.68 | 675 | 609 | 88.5 | 11.53 | 0.28 |
| 29 | **Marblewood** | *Marmaroxylon racemosum* | H | 1.0 | 1005 | 1271 | 157.1 | 19.43 | 0.39 |
| 30 | **Monterey Cypress** | *Hesperocyparis macrocarpa* | S | 0.52 | 515 | 369 | 81.2 | 7.81 | 0.22 |
| 31 | **Mopane** | *Colophospermum mopane* | H | 1.07 | 1075 | 1440 | 114.0 | 13.22 | 0.41 |
| 32 | **Mora** | *Mora excelsa* | H | 1.01 | 1015 | 1295 | 155.5 | 19.24 | 0.39 |
| 33 | **Mulberry** | *Morus spp.* | H | 0.69 | 690 | 634 | 80.6 | 9.32 | 0.28 |
| 34 | **Muninga** | *Pterocarpus angolensis* | H | 0.6 | 605 | 497 | 98.2 | 8.73 | 0.25 |
| 35 | **Narra** | *Pterocarpus dalbergioides* | H | 0.66 | 655 | 576 | 96.3 | 11.89 | 0.27 |
| 36 | **New Zealand Kauri** | *Agathis australis* | S | 0.54 | 540 | 403 | 86.6 | 11.87 | 0.23 |
| 37 | **Olive** | *Olea europaea* | H | 0.98 | 980 | 1213 | 143.0 | 12.39 | 0.38 |
| 38 | **Osage Orange** | *Maclura pomifera* | H | 0.85 | 855 | 943 | 128.6 | 11.64 | 0.34 |
| 39 | **Pacific Yew** | *Taxus brevifolia* | S | 0.7 | 705 | 660 | 104.8 | 9.31 | 0.28 |
| 40 | **Panga Panga** | *Millettia stuhlmannii* | H | 0.87 | 870 | 974 | 131.2 | 15.73 | 0.34 |
| 41 | **Partridgewood** | *Caesalpinia granadillo* | H | 0.83 | 835 | 902 | 127.5 | 18.17 | 0.33 |
| 42 | **Pau Santo** | — | H | 1.11 | 1115 | 1541 | 187.8 | 17.85 | 0.43 |
| 43 | **Peroba Rosa** | *Aspidosperma polyneuron* | H | 0.78 | 775 | 786 | 89.5 | 10.95 | 0.31 |
| 44 | **Pink Ivory** | *Berchemia zeyheri* | H | 1.03 | 1035 | 1342 | 138.1 | 15.12 | 0.4 |
| 45 | **Queensland Maple** | — | H | 0.56 | 560 | 431 | 81.0 | 10.83 | 0.24 |
| 46 | **Redheart** | *Erythroxylum spp.* | H | 0.64 | 640 | 552 | 98.7 | 10.32 | 0.26 |
| 47 | **Rubberwood** | *Hevea brasiliensis* | H | 0.59 | 595 | 482 | 71.9 | 9.07 | 0.25 |
| 48 | **Santos Mahogany** | *Myroxylon balsamum* | H | 0.92 | 915 | 1069 | 148.7 | 16.41 | 0.36 |
| 49 | **Sassafras** | *Sassafras albidum* | H | 0.49 | 495 | 343 | 62.1 | 7.72 | 0.21 |
| 50 | **Siamese Rosewood** | *Dalbergia cochinchinensis* | H | 1.03 | 1035 | 1342 | 171.0 | 16.38 | 0.4 |
| 51 | **Snakewood** | *Brosimum guianense* | H | 1.21 | 1210 | 1792 | 195.0 | 23.2 | 0.46 |
| 52 | **Sucupira** | *Bowdichia nitida* | H | 0.92 | 920 | 1080 | 162.5 | 18.0 | 0.36 |
| 53 | **Tatajuba** | *Bagassa guianensis* | H | 0.8 | 800 | 834 | 123.7 | 18.98 | 0.32 |
| 54 | **Texas Ebony** | *Ebenopsis ebano* | H | 0.96 | 965 | 1179 | 152.3 | 16.54 | 0.38 |
| 55 | **Tiete Rosewood** | *Goniorrhachis marginata* | H | 0.94 | 945 | 1134 | 109.2 | 14.0 | 0.37 |
| 56 | **Yellowheart** | *Euxylophora paraensis* | H | 0.82 | 825 | 882 | 115.9 | 16.64 | 0.33 |
| 57 | **Yucatan Rosewood** | — | H | 0.68 | 680 | 617 | 70.1 | 7.76 | 0.28 |

### Species Notes

**African Blackwood** (*Dalbergia melanoxylon*) — `african_blackwood`
> SG 1.27 · 1270 kg/m³ · Janka 1960 lbf · MOR 213.6 MPa · MOE 17.95 GPa · Hardness scale 0.56 · Warnings: burn:medium, dust:high

**African Padauk** (*Pterocarpus soyauxii*) — `african_padauk`
> SG 0.74 · 745 kg/m³ · Janka 731 lbf · MOR 126.7 MPa · MOE 13.07 GPa · Hardness scale 0.21 · Warnings: dust:medium

**American Chestnut** (*Castanea dentata*) — `american_chestnut`
> SG 0.48 · 480 kg/m³ · Janka 324 lbf · MOR 59.3 MPa · MOE 8.48 GPa · Hardness scale 0.09

**Australian Blackwood** — `australian_blackwood`
> SG 0.64 · 640 kg/m³ · Janka 552 lbf · MOR 103.6 MPa · MOE 14.82 GPa · Hardness scale 0.16 · Warnings: dust:medium

**Australian Cypress** (*Callitris spp.*) — `australian_cypress`
> SG 0.65 · 650 kg/m³ · Janka 568 lbf · MOR 79.6 MPa · MOE 9.32 GPa · Hardness scale 0.16 · Warnings: dust:medium

**Black Locust** (*Robinia pseudoacacia*) — `black_locust`
> SG 0.77 · 770 kg/m³ · Janka 777 lbf · MOR 133.8 MPa · MOE 14.14 GPa · Hardness scale 0.22 · Warnings: dust:medium

**Black Palm** (*Borassus flabellifer*) — `black_palm`
> SG 0.97 · 970 kg/m³ · Janka 1191 lbf · MOR 137.6 MPa · MOE 15.6 GPa · Hardness scale 0.34 · Warnings: dust:high

**Bloodwood** (*Brosimum rubescens*) — `bloodwood`
> SG 1.05 · 1050 kg/m³ · Janka 1379 lbf · MOR 174.4 MPa · MOE 20.78 GPa · Hardness scale 0.39 · Warnings: burn:medium, dust:high

**Camphor** (*Cinnamomum camphora*) — `camphor`
> SG 0.52 · 520 kg/m³ · Janka 376 lbf · MOR 80.5 MPa · MOE 11.56 GPa · Hardness scale 0.11

**Canarywood** (*Centrolobium spp.*) — `canarywood`
> SG 0.83 · 830 kg/m³ · Janka 892 lbf · MOR 131.6 MPa · MOE 14.93 GPa · Hardness scale 0.25 · Warnings: dust:high

**Chechen** (*Metopium brownei*) — `chechen`
> SG 0.88 · 880 kg/m³ · Janka 994 lbf · MOR 93.0 MPa · MOE 15.53 GPa · Hardness scale 0.28 · Warnings: dust:high

**Cumaru** (*Dipteryx odorata*) — `cumaru`
> SG 1.08 · 1085 kg/m³ · Janka 1465 lbf · MOR 175.1 MPa · MOE 22.33 GPa · Hardness scale 0.42 · Warnings: burn:medium, dust:high

**Curupay** (*Anadenanthera colubrina*) — `curupay`
> SG 1.02 · 1025 kg/m³ · Janka 1318 lbf · MOR 193.2 MPa · MOE 18.04 GPa · Hardness scale 0.38 · Warnings: dust:high

**English Walnut** (*Juglans regia*) — `english_walnut`
> SG 0.64 · 640 kg/m³ · Janka 552 lbf · MOR 111.5 MPa · MOE 10.81 GPa · Hardness scale 0.16 · Warnings: dust:medium

**European Ash** (*Fraxinus excelsior*) — `european_ash`
> SG 0.68 · 680 kg/m³ · Janka 617 lbf · MOR 103.6 MPa · MOE 12.31 GPa · Hardness scale 0.18 · Warnings: dust:medium

**European Beech** (*Fagus sylvatica*) — `european_beech`
> SG 0.71 · 710 kg/m³ · Janka 668 lbf · MOR 110.1 MPa · MOE 14.31 GPa · Hardness scale 0.19 · Warnings: dust:medium

**European Yew** (*Taxus baccata*) — `european_yew`
> SG 0.68 · 675 kg/m³ · Janka 609 lbf · MOR 96.8 MPa · MOE 10.15 GPa · Hardness scale 0.17 · Warnings: dust:medium

**Goncalo Alves** (*Astronium graveolens*) — `goncalo_alves`
> SG 0.91 · 905 kg/m³ · Janka 1047 lbf · MOR 117.0 MPa · MOE 16.56 GPa · Hardness scale 0.3 · Warnings: dust:high

**Greenheart** (*Chlorocardium rodiei*) — `greenheart`
> SG 1.01 · 1010 kg/m³ · Janka 1283 lbf · MOR 185.5 MPa · MOE 24.64 GPa · Hardness scale 0.37 · Warnings: dust:high

**Huon Pine** (*Lagarostrobos franklinii*) — `huon_pine`
> SG 0.56 · 560 kg/m³ · Janka 431 lbf · MOR 76.3 MPa · MOE 9.23 GPa · Hardness scale 0.12

**Imbuia** (*Ocotea porosa*) — `imbuia`
> SG 0.66 · 660 kg/m³ · Janka 584 lbf · MOR 84.8 MPa · MOE 9.61 GPa · Hardness scale 0.17 · Warnings: dust:medium

**Jarrah** (*Eucalyptus marginata*) — `jarrah`
> SG 0.83 · 835 kg/m³ · Janka 902 lbf · MOR 108.0 MPa · MOE 14.7 GPa · Hardness scale 0.26 · Warnings: dust:high

**Leadwood** (*Combretum imberbe*) — `leadwood`
> SG 1.22 · 1220 kg/m³ · Janka 1820 lbf · MOR 144.5 MPa · MOE 17.2 GPa · Hardness scale 0.52 · Warnings: burn:medium, dust:high

**Lignum Vitae** (*Guaiacum officinale*) — `lignum_vitae`
> SG 1.26 · 1260 kg/m³ · Janka 1932 lbf · MOR 123.9 MPa · MOE 17.11 GPa · Hardness scale 0.55 · Warnings: burn:medium, dust:high

**Lyptus** (*Eucalyptus grandis × urophylla*) — `lyptus`
> SG 0.85 · 850 kg/m³ · Janka 933 lbf · MOR 118.0 MPa · MOE 14.13 GPa · Hardness scale 0.27 · Warnings: dust:high

**Madagascar Rosewood** (*Dalbergia baronii*) — `madagascar_rosewood`
> SG 0.94 · 935 kg/m³ · Janka 1112 lbf · MOR 165.7 MPa · MOE 12.01 GPa · Hardness scale 0.32 · Warnings: dust:high

**Makore** (*Tieghmella heckelii*) — `makore`
> SG 0.69 · 685 kg/m³ · Janka 626 lbf · MOR 112.6 MPa · MOE 10.71 GPa · Hardness scale 0.18 · Warnings: dust:medium

**Mango** (*Mangifera indica*) — `mango`
> SG 0.68 · 675 kg/m³ · Janka 609 lbf · MOR 88.5 MPa · MOE 11.53 GPa · Hardness scale 0.17 · Warnings: dust:medium

**Marblewood** (*Marmaroxylon racemosum*) — `marblewood`
> SG 1.0 · 1005 kg/m³ · Janka 1271 lbf · MOR 157.1 MPa · MOE 19.43 GPa · Hardness scale 0.36 · Warnings: dust:high

**Monterey Cypress** (*Hesperocyparis macrocarpa*) — `monterey_cypress`
> SG 0.52 · 515 kg/m³ · Janka 369 lbf · MOR 81.2 MPa · MOE 7.81 GPa · Hardness scale 0.11

**Mopane** (*Colophospermum mopane*) — `mopane`
> SG 1.07 · 1075 kg/m³ · Janka 1440 lbf · MOR 114.0 MPa · MOE 13.22 GPa · Hardness scale 0.41 · Warnings: burn:medium, dust:high

**Mora** (*Mora excelsa*) — `mora`
> SG 1.01 · 1015 kg/m³ · Janka 1295 lbf · MOR 155.5 MPa · MOE 19.24 GPa · Hardness scale 0.37 · Warnings: dust:high

**Mulberry** (*Morus spp.*) — `mulberry`
> SG 0.69 · 690 kg/m³ · Janka 634 lbf · MOR 80.6 MPa · MOE 9.32 GPa · Hardness scale 0.18 · Warnings: dust:medium

**Muninga** (*Pterocarpus angolensis*) — `muninga`
> SG 0.6 · 605 kg/m³ · Janka 497 lbf · MOR 98.2 MPa · MOE 8.73 GPa · Hardness scale 0.14

**Narra** (*Pterocarpus dalbergioides*) — `narra`
> SG 0.66 · 655 kg/m³ · Janka 576 lbf · MOR 96.3 MPa · MOE 11.89 GPa · Hardness scale 0.16 · Warnings: dust:medium

**New Zealand Kauri** (*Agathis australis*) — `new_zealand_kauri`
> SG 0.54 · 540 kg/m³ · Janka 403 lbf · MOR 86.6 MPa · MOE 11.87 GPa · Hardness scale 0.12

**Olive** (*Olea europaea*) — `olive`
> SG 0.98 · 980 kg/m³ · Janka 1213 lbf · MOR 143.0 MPa · MOE 12.39 GPa · Hardness scale 0.35 · Warnings: dust:high

**Osage Orange** (*Maclura pomifera*) — `osage_orange`
> SG 0.85 · 855 kg/m³ · Janka 943 lbf · MOR 128.6 MPa · MOE 11.64 GPa · Hardness scale 0.27 · Warnings: dust:high

**Pacific Yew** (*Taxus brevifolia*) — `pacific_yew`
> SG 0.7 · 705 kg/m³ · Janka 660 lbf · MOR 104.8 MPa · MOE 9.31 GPa · Hardness scale 0.19 · Warnings: dust:medium

**Panga Panga** (*Millettia stuhlmannii*) — `panga_panga`
> SG 0.87 · 870 kg/m³ · Janka 974 lbf · MOR 131.2 MPa · MOE 15.73 GPa · Hardness scale 0.28 · Warnings: dust:high

**Partridgewood** (*Caesalpinia granadillo*) — `partridgewood`
> SG 0.83 · 835 kg/m³ · Janka 902 lbf · MOR 127.5 MPa · MOE 18.17 GPa · Hardness scale 0.26 · Warnings: dust:high

**Pau Santo** — `pau_santo`
> SG 1.11 · 1115 kg/m³ · Janka 1541 lbf · MOR 187.8 MPa · MOE 17.85 GPa · Hardness scale 0.44 · Warnings: burn:medium, dust:high

**Peroba Rosa** (*Aspidosperma polyneuron*) — `peroba_rosa`
> SG 0.78 · 775 kg/m³ · Janka 786 lbf · MOR 89.5 MPa · MOE 10.95 GPa · Hardness scale 0.22 · Warnings: dust:medium

**Pink Ivory** (*Berchemia zeyheri*) — `pink_ivory`
> SG 1.03 · 1035 kg/m³ · Janka 1342 lbf · MOR 138.1 MPa · MOE 15.12 GPa · Hardness scale 0.38 · Warnings: dust:high

**Queensland Maple** — `queensland_maple`
> SG 0.56 · 560 kg/m³ · Janka 431 lbf · MOR 81.0 MPa · MOE 10.83 GPa · Hardness scale 0.12

**Redheart** (*Erythroxylum spp.*) — `redheart`
> SG 0.64 · 640 kg/m³ · Janka 552 lbf · MOR 98.7 MPa · MOE 10.32 GPa · Hardness scale 0.16 · Warnings: dust:medium

**Rubberwood** (*Hevea brasiliensis*) — `rubberwood`
> SG 0.59 · 595 kg/m³ · Janka 482 lbf · MOR 71.9 MPa · MOE 9.07 GPa · Hardness scale 0.14

**Santos Mahogany** (*Myroxylon balsamum*) — `santos_mahogany`
> SG 0.92 · 915 kg/m³ · Janka 1069 lbf · MOR 148.7 MPa · MOE 16.41 GPa · Hardness scale 0.31 · Warnings: dust:high

**Sassafras** (*Sassafras albidum*) — `sassafras`
> SG 0.49 · 495 kg/m³ · Janka 343 lbf · MOR 62.1 MPa · MOE 7.72 GPa · Hardness scale 0.1

**Siamese Rosewood** (*Dalbergia cochinchinensis*) — `siamese_rosewood`
> SG 1.03 · 1035 kg/m³ · Janka 1342 lbf · MOR 171.0 MPa · MOE 16.38 GPa · Hardness scale 0.38 · Warnings: dust:high

**Snakewood** (*Brosimum guianense*) — `snakewood`
> SG 1.21 · 1210 kg/m³ · Janka 1792 lbf · MOR 195.0 MPa · MOE 23.2 GPa · Hardness scale 0.51 · Warnings: burn:medium, dust:high

**Sucupira** (*Bowdichia nitida*) — `sucupira`
> SG 0.92 · 920 kg/m³ · Janka 1080 lbf · MOR 162.5 MPa · MOE 18.0 GPa · Hardness scale 0.31 · Warnings: dust:high

**Tatajuba** (*Bagassa guianensis*) — `tatajuba`
> SG 0.8 · 800 kg/m³ · Janka 834 lbf · MOR 123.7 MPa · MOE 18.98 GPa · Hardness scale 0.24 · Warnings: dust:medium

**Texas Ebony** (*Ebenopsis ebano*) — `texas_ebony`
> SG 0.96 · 965 kg/m³ · Janka 1179 lbf · MOR 152.3 MPa · MOE 16.54 GPa · Hardness scale 0.34 · Warnings: dust:high

**Tiete Rosewood** (*Goniorrhachis marginata*) — `tiete_rosewood`
> SG 0.94 · 945 kg/m³ · Janka 1134 lbf · MOR 109.2 MPa · MOE 14.0 GPa · Hardness scale 0.32 · Warnings: dust:high

**Yellowheart** (*Euxylophora paraensis*) — `yellowheart`
> SG 0.82 · 825 kg/m³ · Janka 882 lbf · MOR 115.9 MPa · MOE 16.64 GPa · Hardness scale 0.25 · Warnings: dust:high

**Yucatan Rosewood** — `yucatan_rosewood`
> SG 0.68 · 680 kg/m³ · Janka 617 lbf · MOR 70.1 MPa · MOE 7.76 GPa · Hardness scale 0.18 · Warnings: dust:medium

---

## Exploratory Species

*Valid CNC-machinable species not yet widely used in guitar building. Included to support experimentation with underutilized and sustainable wood sources.*

| # | Species | Scientific Name | Type | SG | Density | Janka | MOR | MOE | k |
|--:|---------|-----------------|------|----|---------|-------|-----|-----|---|
| 1 | **Abura** | — | H | 0.56 | 560 | 431 | 81.1 | 9.56 | 0.24 |
| 2 | **Afata** | — | H | 0.63 | 630 | 536 | 126.9 | 13.38 | 0.26 |
| 3 | **African Crabwood** | — | H | 0.69 | 695 | 643 | 102.0 | 14.77 | 0.28 |
| 4 | **African Juniper** | — | S | 0.54 | 535 | 396 | 80.4 | 10.09 | 0.23 |
| 5 | **African Mesquite** | — | H | 0.94 | 945 | 1134 | 130.5 | 13.92 | 0.37 |
| 6 | **African Walnut** | *Lovoa trichilioides* | H | 0.54 | 540 | 403 | 84.5 | 9.24 | 0.23 |
| 7 | **Afrormosia** | — | H | 0.72 | 725 | 695 | 100.9 | 11.83 | 0.29 |
| 8 | **Afzelia Doussie** | — | H | 0.81 | 805 | 843 | 122.3 | 14.44 | 0.32 |
| 9 | **Afzelia Xylay** | — | H | 0.82 | 825 | 882 | 118.7 | 13.37 | 0.33 |
| 10 | **Ailanthus** | — | H | 0.6 | 600 | 490 | 76.2 | 11.19 | 0.25 |
| 11 | **Alaska Paper Birch** | — | H | 0.61 | 610 | 505 | 93.8 | 13.1 | 0.25 |
| 12 | **Alaskan Yellow Cedar** | *Cupressus nootkatensis* | S | 0.49 | 495 | 343 | 76.6 | 9.79 | 0.21 |
| 13 | **Alder Leaf Birch** | — | H | 0.53 | 530 | 389 | 61.9 | 8.52 | 0.23 |
| 14 | **Algarrobo Blanco** | — | H | 0.79 | 785 | 805 | 63.1 | 6.08 | 0.32 |
| 15 | **Aliso Del Cerro** | — | H | 0.44 | 440 | 276 | 57.4 | 7.83 | 0.19 |
| 16 | **Alligator Juniper** | — | S | 0.58 | 585 | 467 | 46.2 | 4.48 | 0.24 |
| 17 | **Amazon Rosewood** | — | H | 1.08 | 1085 | 1465 | 116.9 | 12.9 | 0.42 |
| 18 | **Amendoim** | — | H | 0.8 | 800 | 834 | 108.8 | 12.21 | 0.32 |
| 19 | **American Elm** | *Ulmus americana* | H | 0.56 | 560 | 431 | 81.4 | 9.24 | 0.24 |
| 20 | **American Hornbeam** | — | H | 0.79 | 785 | 805 | 112.4 | 11.68 | 0.32 |
| 21 | **Andaman Padauk** | — | H | 0.77 | 770 | 777 | 101.9 | 12.1 | 0.31 |
| 22 | **Andean Alder** | — | H | 0.39 | 385 | 215 | 51.2 | 7.81 | 0.18 |
| 23 | **Andiroba** | — | H | 0.66 | 660 | 584 | 107.4 | 13.55 | 0.27 |
| 24 | **Angelim Vermelho** | — | H | 1.07 | 1070 | 1428 | 156.0 | 19.39 | 0.41 |
| 25 | **Anigre** | — | H | 0.55 | 550 | 417 | 83.0 | 10.95 | 0.23 |
| 26 | **Apple** | *Malus domestica* | H | 0.83 | 830 | 892 | 88.3 | 8.76 | 0.33 |
| 27 | **Araracanga** | — | H | 0.94 | 935 | 1112 | 152.1 | 20.97 | 0.37 |
| 28 | **Argentine Lignum Vitae** | — | H | 1.2 | 1200 | 1765 | 139.0 | 18.05 | 0.46 |
| 29 | **Argentine Osage Orange** | — | H | 0.91 | 910 | 1058 | 134.9 | 14.9 | 0.36 |
| 30 | **Atlantic White Cedar** | *Chamaecyparis thyoides* | S | 0.38 | 380 | 210 | 46.9 | 6.41 | 0.17 |
| 31 | **Atlas Cedar** | — | S | 0.53 | 530 | 389 | 87.2 | 9.78 | 0.23 |
| 32 | **Australian Buloke** | *Allocasuarina luehmannii* | H | 1.08 | 1085 | 1465 | 130.0 | 18.5 | 0.42 |
| 33 | **Australian Red Cedar** | — | S | 0.48 | 485 | 330 | 71.5 | 9.22 | 0.21 |
| 34 | **Austrian Pine** | — | S | 0.47 | 475 | 318 | 64.4 | 10.81 | 0.2 |
| 35 | **Avodire** | — | H | 0.57 | 575 | 452 | 106.2 | 11.13 | 0.24 |
| 36 | **Balau** | — | H | 0.85 | 850 | 933 | 122.3 | 16.95 | 0.34 |
| 37 | **Balsa** | *Ochroma pyramidale* | H | 0.15 | 150 | 38 | 19.6 | 3.71 | 0.09 |
| 38 | **Balsam Fir** | — | S | 0.4 | 400 | 231 | 60.7 | 9.57 | 0.18 |
| 39 | **Balsam Poplar** | — | H | 0.37 | 370 | 200 | 46.9 | 7.59 | 0.17 |
| 40 | **Bamboo** | *Bambusoideae spp.* | H | 0.5 | 500 | 349 | 76.0 | 18.0 | 0.21 |
| 41 | **Batai** | — | H | 0.38 | 375 | 205 | 55.2 | 7.91 | 0.17 |
| 42 | **Beefwood** | — | H | 0.96 | 965 | 1179 | 94.0 | 14.0 | 0.38 |
| 43 | **Bekak** | — | H | 0.77 | 765 | 767 | 145.0 | 15.77 | 0.31 |
| 44 | **Beli** | — | H | 0.77 | 770 | 777 | 134.8 | 16.09 | 0.31 |
| 45 | **Bigleaf Maple** | *Acer macrophyllum* | H | 0.55 | 545 | 410 | 73.8 | 10.0 | 0.23 |
| 46 | **Bigtooth Aspen** | — | H | 0.43 | 435 | 270 | 62.8 | 9.86 | 0.19 |
| 47 | **Bitternut Hickory** | — | H | 0.73 | 735 | 713 | 117.9 | 12.35 | 0.3 |
| 48 | **Black Ash** | *Fraxinus nigra* | H | 0.55 | 545 | 410 | 86.9 | 11.0 | 0.23 |
| 49 | **Black Cottonwood** | *Populus trichocarpa* | H | 0.39 | 385 | 215 | 58.6 | 8.76 | 0.18 |
| 50 | **Black Ironwood** | — | H | 1.35 | 1355 | 2210 | 125.5 | 20.46 | 0.51 |
| 51 | **Black Maple** | — | H | 0.64 | 640 | 552 | 91.7 | 11.17 | 0.26 |
| 52 | **Black Mesquite** | *Prosopis nigra* | H | 0.82 | 825 | 882 | 77.3 | 7.7 | 0.33 |
| 53 | **Black Oak** | *Quercus velutina* | H | 0.71 | 715 | 677 | 99.5 | 11.97 | 0.29 |
| 54 | **Black Poplar** | — | H | 0.39 | 385 | 215 | 63.7 | 7.21 | 0.18 |
| 55 | **Black Siris** | — | H | 0.76 | 760 | 758 | 96.4 | 11.77 | 0.31 |
| 56 | **Black Spruce** | *Picea mariana* | S | 0.45 | 450 | 288 | 69.7 | 10.5 | 0.2 |
| 57 | **Black Tupelo** | — | H | 0.55 | 545 | 410 | 65.5 | 8.19 | 0.23 |
| 58 | **Black Wattle** | — | H | 0.73 | 730 | 704 | 121.8 | 14.6 | 0.3 |
| 59 | **Black Willow** | — | H | 0.41 | 415 | 248 | 53.8 | 6.97 | 0.18 |
| 60 | **Blackheart Sassafras** | — | H | 0.62 | 620 | 520 | 100.5 | 12.6 | 0.26 |
| 61 | **Blue Ash** | — | H | 0.64 | 640 | 552 | 95.2 | 9.66 | 0.26 |
| 62 | **Blue Gum** | *Eucalyptus globulus* | H | 0.82 | 820 | 873 | 134.7 | 18.76 | 0.33 |
| 63 | **Bomanga** | — | H | 0.57 | 570 | 445 | 86.6 | 12.19 | 0.24 |
| 64 | **Bosse** | — | H | 0.6 | 600 | 490 | 103.2 | 10.91 | 0.25 |
| 65 | **Box Elder** | — | H | 0.48 | 485 | 330 | 55.2 | 7.24 | 0.21 |
| 66 | **Boxwood** | *Buxus sempervirens* | H | 0.96 | 965 | 1179 | 136.5 | 12.27 | 0.38 |
| 67 | **Brazilian Pau Rosa** | — | H | 0.73 | 730 | 704 | 130.0 | 17.0 | 0.3 |
| 68 | **Brazilwood** | *Paubrasilia echinata* | H | 1.05 | 1050 | 1379 | 176.1 | 20.2 | 0.41 |
| 69 | **Breadnut** | — | H | 0.75 | 750 | 740 | 112.6 | 14.37 | 0.3 |
| 70 | **Broad Leaved Apple** | — | H | 0.75 | 750 | 740 | 78.0 | 12.5 | 0.3 |
| 71 | **Brown Ebony** | — | H | 1.16 | 1160 | 1658 | 158.0 | 18.7 | 0.45 |
| 72 | **Brownheart** | — | H | 0.93 | 925 | 1090 | 150.5 | 17.83 | 0.37 |
| 73 | **Buckthorn** | — | H | 0.6 | 605 | 497 | 60.0 | 6.62 | 0.25 |
| 74 | **Bulletwood** | — | H | 1.08 | 1080 | 1452 | 192.2 | 23.06 | 0.42 |
| 75 | **Bur Oak** | — | H | 0.72 | 725 | 695 | 75.3 | 7.17 | 0.29 |
| 76 | **Burma Padauk** | — | H | 0.86 | 865 | 963 | 138.8 | 14.14 | 0.34 |
| 77 | **Burmese Blackwood** | — | H | 1.06 | 1060 | 1403 | 78.9 | 11.03 | 0.41 |
| 78 | **Butternut** | *Juglans cinerea* | H | 0.43 | 435 | 270 | 55.9 | 8.14 | 0.19 |
| 79 | **California Black Oak** | — | H | 0.62 | 620 | 520 | 59.4 | 6.76 | 0.26 |
| 80 | **California Red Fir** | *Abies magnifica* | S | 0.43 | 435 | 270 | 71.5 | 10.23 | 0.19 |
| 81 | **Candlenut** | — | H | 0.39 | 390 | 221 | 50.9 | 7.33 | 0.18 |
| 82 | **Cape Holly** | — | H | 0.64 | 640 | 552 | 75.4 | 9.06 | 0.26 |
| 83 | **Caribbean Pine** | — | S | 0.62 | 625 | 528 | 92.0 | 12.03 | 0.26 |
| 84 | **Catalpa** | *Catalpa speciosa* | H | 0.46 | 460 | 299 | 64.8 | 8.35 | 0.2 |
| 85 | **Cedar Elm** | — | S | 0.66 | 655 | 576 | 93.1 | 10.21 | 0.27 |
| 86 | **Cedar Of Lebanon** | — | S | 0.52 | 520 | 376 | 82.0 | 10.1 | 0.22 |
| 87 | **Cerejeira** | *Amburana cearensis* | H | 0.56 | 560 | 431 | 72.9 | 10.88 | 0.24 |
| 88 | **Ceylon Ebony** | — | H | 0.92 | 915 | 1069 | 128.6 | 14.07 | 0.36 |
| 89 | **Chanfuta** | — | H | 0.83 | 835 | 902 | 109.0 | 11.75 | 0.33 |
| 90 | **Cheesewood** | — | H | 0.38 | 380 | 210 | 54.0 | 7.52 | 0.17 |
| 91 | **Cherrybark Oak** | — | H | 0.79 | 785 | 805 | 124.8 | 15.7 | 0.32 |
| 92 | **Chestnut Oak** | — | H | 0.75 | 750 | 740 | 91.7 | 11.0 | 0.3 |
| 93 | **Chichipate** | — | H | 1.0 | 1005 | 1271 | 151.1 | 20.39 | 0.39 |
| 94 | **Coast Redwood** | — | S | 0.41 | 415 | 248 | 61.7 | 8.41 | 0.18 |
| 95 | **Coffeetree** | — | H | 0.68 | 675 | 609 | 72.4 | 9.79 | 0.28 |
| 96 | **Coolibah** | — | H | 1.13 | 1130 | 1579 | 144.5 | 17.24 | 0.44 |
| 97 | **Crack Willow** | — | H | 0.43 | 430 | 264 | 64.9 | 7.95 | 0.19 |
| 98 | **Cuban Mahogany** | — | H | 0.6 | 600 | 490 | 74.4 | 9.31 | 0.25 |
| 99 | **Cucumbertree** | — | H | 0.53 | 530 | 389 | 84.8 | 12.55 | 0.23 |
| 100 | **Cyprus Cedar** | — | S | 0.52 | 520 | 376 | 82.0 | 10.1 | 0.22 |
| 101 | **Dahoma** | — | H | 0.69 | 695 | 643 | 111.6 | 12.9 | 0.28 |
| 102 | **Dark Red Meranti** | — | H | 0.68 | 675 | 609 | 87.7 | 12.02 | 0.28 |
| 103 | **Dawn Redwood** | — | S | 0.34 | 335 | 167 | 61.4 | 6.12 | 0.16 |
| 104 | **Deglupta** | — | H | 0.5 | 500 | 349 | 79.6 | 10.79 | 0.21 |
| 105 | **Dogwood** | *Cornus florida* | H | 0.81 | 815 | 863 | 115.3 | 13.26 | 0.32 |
| 106 | **Doi** | — | H | 0.61 | 610 | 505 | 79.7 | 11.39 | 0.25 |
| 107 | **Downy Birch** | — | H | 0.62 | 625 | 528 | 122.5 | 12.03 | 0.26 |
| 108 | **Dry Zone Mahogany** | — | H | 0.77 | 770 | 777 | 92.8 | 11.13 | 0.31 |
| 109 | **Dutch Elm** | — | H | 0.57 | 575 | 452 | 68.7 | 7.52 | 0.24 |
| 110 | **East African Olive** | — | H | 0.97 | 975 | 1202 | 155.4 | 17.77 | 0.38 |
| 111 | **East Indian Kauri** | — | S | 0.52 | 520 | 376 | 67.0 | 9.3 | 0.22 |
| 112 | **East Indian Satinwood** | — | H | 0.97 | 970 | 1191 | 130.8 | 14.01 | 0.38 |
| 113 | **Eastern Cottonwood** | — | H | 0.45 | 450 | 288 | 58.6 | 9.45 | 0.2 |
| 114 | **Eastern Hemlock** | *Tsuga canadensis* | S | 0.45 | 450 | 288 | 61.4 | 8.28 | 0.2 |
| 115 | **Eastern Red Cedar** | *Juniperus virginiana* | S | 0.53 | 530 | 389 | 60.7 | 6.07 | 0.23 |
| 116 | **Eastern White Pine** | — | S | 0.4 | 400 | 231 | 59.3 | 8.55 | 0.18 |
| 117 | **Ebiara** | — | H | 0.72 | 725 | 695 | 109.6 | 11.14 | 0.29 |
| 118 | **Ekki** | — | H | 1.06 | 1065 | 1415 | 195.8 | 18.99 | 0.41 |
| 119 | **Elgon Olive** | — | H | 0.77 | 770 | 777 | 111.3 | 10.81 | 0.31 |
| 120 | **Endra Endra** | — | H | 1.24 | 1240 | 1875 | 180.4 | 20.69 | 0.47 |
| 121 | **English Elm** | *Ulmus minor* | H | 0.56 | 565 | 438 | 65.0 | 7.12 | 0.24 |
| 122 | **English Oak** | *Quercus robur* | H | 0.68 | 675 | 609 | 97.1 | 10.6 | 0.28 |
| 123 | **Espave** | — | H | 0.5 | 500 | 349 | 62.5 | 8.71 | 0.21 |
| 124 | **Etimoe** | — | H | 0.76 | 755 | 749 | 142.4 | 13.75 | 0.31 |
| 125 | **European Alder** | — | H | 0.54 | 535 | 396 | 91.4 | 11.01 | 0.23 |
| 126 | **European Aspen** | — | H | 0.45 | 450 | 288 | 62.0 | 9.75 | 0.2 |
| 127 | **European Hornbeam** | — | H | 0.73 | 735 | 713 | 110.4 | 12.1 | 0.3 |
| 128 | **European Larch** | *Larix decidua* | S | 0.57 | 575 | 452 | 90.0 | 11.8 | 0.24 |
| 129 | **European Lime** | — | H | 0.54 | 535 | 396 | 85.4 | 11.71 | 0.23 |
| 130 | **European Silver Fir** | — | S | 0.41 | 415 | 248 | 66.1 | 8.28 | 0.18 |
| 131 | **Field Maple** | — | H | 0.69 | 690 | 634 | 123.0 | 11.8 | 0.28 |
| 132 | **Fijian Kauri** | — | S | 0.55 | 550 | 417 | 60.0 | 9.8 | 0.23 |
| 133 | **Freijo** | — | H | 0.58 | 580 | 460 | 88.0 | 13.13 | 0.24 |
| 134 | **Garapa** | *Apuleia leiocarpa* | H | 0.82 | 820 | 873 | 127.8 | 15.57 | 0.33 |
| 135 | **Giant Chinkapin** | — | H | 0.52 | 515 | 369 | 73.8 | 8.55 | 0.22 |
| 136 | **Giant Sequoia** | — | H | 0.38 | 375 | 205 | 52.4 | 6.79 | 0.17 |
| 137 | **Gidgee** | — | H | 1.15 | 1150 | 1631 | 130.0 | 18.5 | 0.44 |
| 138 | **Gowen Cypress** | — | S | 0.48 | 480 | 324 | 56.9 | 4.5 | 0.21 |
| 139 | **Grand Fir** | — | S | 0.45 | 450 | 288 | 60.3 | 10.55 | 0.2 |
| 140 | **Gray Birch** | — | H | 0.56 | 560 | 431 | 67.6 | 7.93 | 0.24 |
| 141 | **Gray Box** | — | H | 1.12 | 1120 | 1553 | 151.8 | 18.01 | 0.43 |
| 142 | **Green Ash** | — | H | 0.64 | 640 | 552 | 97.2 | 11.4 | 0.26 |
| 143 | **Guanacaste** | — | H | 0.44 | 440 | 276 | 59.6 | 8.46 | 0.19 |
| 144 | **Guatemalan Mora** | — | H | 0.91 | 910 | 1058 | 134.9 | 14.9 | 0.36 |
| 145 | **Hackberry** | *Celtis occidentalis* | H | 0.59 | 595 | 482 | 75.9 | 8.21 | 0.25 |
| 146 | **Hard Milkwood** | — | H | 0.74 | 740 | 722 | 84.8 | 13.52 | 0.3 |
| 147 | **Hazelnut** | — | H | 0.7 | 700 | 651 | 98.5 | 8.27 | 0.28 |
| 148 | **Holly** | *Ilex opaca* | H | 0.64 | 640 | 552 | 71.0 | 7.66 | 0.26 |
| 149 | **Holm Oak** | — | H | 0.96 | 960 | 1168 | 146.4 | 13.41 | 0.38 |
| 150 | **Honey Locust** | *Gleditsia triacanthos* | H | 0.76 | 755 | 749 | 101.4 | 11.24 | 0.31 |
| 151 | **Hoop Pine** | — | S | 0.5 | 500 | 349 | 85.0 | 11.77 | 0.21 |
| 152 | **Hophornbeam** | — | H | 0.79 | 785 | 805 | 97.2 | 11.72 | 0.32 |
| 153 | **Horse Chestnut** | — | H | 0.5 | 500 | 349 | 67.5 | 7.15 | 0.21 |
| 154 | **Hububalli** | — | H | 0.69 | 685 | 626 | 100.8 | 12.63 | 0.28 |
| 155 | **Idigbo** | — | H | 0.52 | 520 | 376 | 84.5 | 10.03 | 0.22 |
| 156 | **Incense Cedar** | *Calocedrus decurrens* | S | 0.39 | 385 | 215 | 55.2 | 7.17 | 0.18 |
| 157 | **Indian Laurel** | — | H | 0.85 | 855 | 943 | 101.4 | 12.46 | 0.34 |
| 158 | **Indian Pulai** | — | H | 0.41 | 410 | 242 | 55.4 | 8.41 | 0.18 |
| 159 | **Indian Silver Greywood** | — | H | 0.68 | 680 | 617 | 88.6 | 13.22 | 0.28 |
| 160 | **Itin** | — | H | 1.27 | 1275 | 1974 | 153.8 | 17.38 | 0.48 |
| 161 | **Izombe** | — | H | 0.73 | 730 | 704 | 120.2 | 11.75 | 0.3 |
| 162 | **Jack Pine** | *Pinus banksiana* | S | 0.5 | 500 | 349 | 68.3 | 9.31 | 0.21 |
| 163 | **Japanese Larch** | — | S | 0.5 | 500 | 349 | 80.1 | 8.76 | 0.21 |
| 164 | **Jeffrey Pine** | — | S | 0.45 | 450 | 288 | 64.1 | 8.55 | 0.2 |
| 165 | **Jelutong** | *Dyera costulata* | H | 0.45 | 450 | 288 | 55.4 | 8.44 | 0.2 |
| 166 | **Jucaro** | — | H | 0.99 | 990 | 1236 | 146.6 | 16.42 | 0.39 |
| 167 | **Karri** | *Eucalyptus diversicolor* | H | 0.89 | 885 | 1005 | 127.8 | 20.44 | 0.35 |
| 168 | **Kempas** | *Koompassia malaccensis* | H | 0.88 | 880 | 994 | 118.5 | 20.09 | 0.35 |
| 169 | **Keruing** | — | H | 0.74 | 745 | 731 | 115.2 | 15.81 | 0.3 |
| 170 | **Keyaki** | — | H | 0.62 | 620 | 520 | 96.7 | 10.73 | 0.26 |
| 171 | **Khasi Pine** | — | S | 0.61 | 610 | 505 | 87.0 | 12.25 | 0.25 |
| 172 | **Kosipo** | — | H | 0.68 | 680 | 617 | 92.7 | 11.31 | 0.28 |
| 173 | **Koto** | — | H | 0.59 | 595 | 482 | 105.4 | 12.08 | 0.25 |
| 174 | **Lancewood** | — | H | 0.98 | 980 | 1213 | 163.5 | 20.0 | 0.38 |
| 175 | **Lati** | — | H | 0.79 | 785 | 805 | 127.3 | 14.81 | 0.32 |
| 176 | **Laurel Blanco** | — | H | 0.56 | 565 | 438 | 86.7 | 12.93 | 0.24 |
| 177 | **Laurel Oak** | — | H | 0.74 | 740 | 722 | 98.8 | 12.37 | 0.3 |
| 178 | **Lebbeck** | — | H | 0.64 | 635 | 544 | 94.7 | 12.66 | 0.26 |
| 179 | **Lebombo Ironwood** | — | H | 0.89 | 885 | 1005 | 128.0 | 11.0 | 0.35 |
| 180 | **Lemon Scented Gum** | — | H | 0.95 | 950 | 1146 | 134.4 | 16.66 | 0.37 |
| 181 | **Lemonwood** | — | H | 0.81 | 810 | 853 | 152.4 | 15.75 | 0.32 |
| 182 | **Leyland Cypress** | — | S | 0.5 | 500 | 349 | 82.7 | 6.82 | 0.21 |
| 183 | **Light Red Meranti** | — | H | 0.48 | 480 | 324 | 77.3 | 11.39 | 0.21 |
| 184 | **Limba** | *Terminalia superba* | H | 0.56 | 555 | 424 | 86.2 | 10.49 | 0.24 |
| 185 | **Limber Pine** | — | S | 0.45 | 450 | 288 | 62.8 | 8.07 | 0.2 |
| 186 | **Live Oak** | *Quercus virginiana* | H | 1.0 | 1000 | 1260 | 125.6 | 13.52 | 0.39 |
| 187 | **Loblolly Pine** | *Pinus taeda* | S | 0.57 | 570 | 445 | 88.3 | 12.3 | 0.24 |
| 188 | **Lodgepole Pine** | *Pinus contorta* | S | 0.47 | 465 | 306 | 64.8 | 9.24 | 0.2 |
| 189 | **London Plane** | *Platanus × acerifolia* | H | 0.56 | 560 | 431 | 74.7 | 8.9 | 0.24 |
| 190 | **Longleaf Pine** | *Pinus palustris* | S | 0.65 | 650 | 568 | 100.0 | 13.7 | 0.27 |
| 191 | **Louro Preto** | — | H | 0.88 | 880 | 994 | 117.9 | 10.9 | 0.35 |
| 192 | **Macacauba** | — | H | 0.95 | 950 | 1146 | 148.6 | 19.56 | 0.37 |
| 193 | **Machiche** | — | H | 0.89 | 890 | 1015 | 173.8 | 18.93 | 0.35 |
| 194 | **Madrone** | *Arbutus menziesii* | H | 0.8 | 795 | 824 | 71.7 | 8.48 | 0.32 |
| 195 | **Mangium** | — | H | 0.58 | 585 | 467 | 98.2 | 11.07 | 0.24 |
| 196 | **Mansonia** | — | H | 0.66 | 660 | 584 | 119.8 | 11.43 | 0.27 |
| 197 | **Maritime Pine** | — | S | 0.5 | 500 | 349 | 73.0 | 8.54 | 0.21 |
| 198 | **Mediterranean Cypress** | — | S | 0.54 | 535 | 396 | 44.6 | 5.28 | 0.23 |
| 199 | **Messmate** | — | H | 0.75 | 750 | 740 | 112.3 | 14.29 | 0.3 |
| 200 | **Mexican Cypress** | — | S | 0.47 | 470 | 312 | 76.4 | 8.72 | 0.2 |
| 201 | **Moabi** | — | H | 0.86 | 860 | 953 | 160.3 | 16.66 | 0.34 |
| 202 | **Mockernut Hickory** | — | H | 0.81 | 815 | 863 | 132.4 | 15.31 | 0.32 |
| 203 | **Monkey Puzzle** | — | H | 0.54 | 535 | 396 | 96.3 | 11.57 | 0.23 |
| 204 | **Monkeypod** | — | H | 0.6 | 600 | 490 | 65.7 | 7.92 | 0.25 |
| 205 | **Monkeythorn** | — | H | 0.8 | 800 | 834 | 112.0 | 13.14 | 0.32 |
| 206 | **Mountain Ash** | *Eucalyptus regnans* | H | 0.68 | 680 | 617 | 96.7 | 14.02 | 0.28 |
| 207 | **Movingui** | — | H | 0.72 | 720 | 686 | 129.2 | 12.23 | 0.29 |
| 208 | **Musk Sandalwood** | — | H | 0.94 | 940 | 1123 | 124.4 | 11.13 | 0.37 |
| 209 | **Mutenye** | — | H | 0.8 | 800 | 834 | 152.3 | 18.6 | 0.32 |
| 210 | **Nandubay** | — | H | 1.01 | 1015 | 1295 | 44.3 | 9.79 | 0.39 |
| 211 | **Nargusta** | — | H | 0.79 | 785 | 805 | 122.5 | 15.21 | 0.32 |
| 212 | **Nepalese Alder** | — | H | 0.5 | 500 | 349 | 51.0 | 8.28 | 0.21 |
| 213 | **New Guinea Walnut** | — | H | 0.62 | 625 | 528 | 87.0 | 11.53 | 0.26 |
| 214 | **Noble Fir** | — | S | 0.41 | 415 | 248 | 74.4 | 11.17 | 0.18 |
| 215 | **Norfolk Island Pine** | — | S | 0.49 | 495 | 343 | 80.9 | 11.89 | 0.21 |
| 216 | **Northern Silky Oak** | — | H | 0.56 | 560 | 431 | 65.7 | 8.92 | 0.24 |
| 217 | **Northern White Cedar** | — | S | 0.35 | 350 | 181 | 44.8 | 5.52 | 0.16 |
| 218 | **Norway Maple** | — | H | 0.65 | 645 | 560 | 115.0 | 10.6 | 0.27 |
| 219 | **Nutmeg Hickory** | — | H | 0.68 | 675 | 609 | 114.5 | 11.72 | 0.28 |
| 220 | **Nyatoh** | — | H | 0.62 | 620 | 520 | 96.0 | 13.37 | 0.26 |
| 221 | **Obeche** | *Triplochiton scleroxylon* | H | 0.38 | 380 | 210 | 59.8 | 6.44 | 0.17 |
| 222 | **Ocote Pine** | — | S | 0.7 | 700 | 651 | 101.5 | 15.23 | 0.28 |
| 223 | **Ohia** | — | H | 0.92 | 915 | 1069 | 125.9 | 15.65 | 0.36 |
| 224 | **Okoume** | — | H | 0.43 | 430 | 264 | 75.0 | 8.47 | 0.19 |
| 225 | **Opepe** | — | H | 0.77 | 770 | 777 | 116.3 | 13.25 | 0.31 |
| 226 | **Oregon Ash** | — | H | 0.61 | 610 | 505 | 87.6 | 9.38 | 0.25 |
| 227 | **Oregon Myrtle** | — | H | 0.64 | 635 | 544 | 66.9 | 8.45 | 0.26 |
| 228 | **Oregon White Oak** | — | H | 0.81 | 815 | 863 | 70.3 | 7.51 | 0.32 |
| 229 | **Overcup Oak** | — | H | 0.76 | 760 | 758 | 86.9 | 9.8 | 0.31 |
| 230 | **Pacific Maple** | — | H | 0.6 | 605 | 497 | 91.1 | 12.08 | 0.25 |
| 231 | **Pacific Silver Fir** | — | S | 0.43 | 435 | 270 | 70.6 | 11.59 | 0.19 |
| 232 | **Paldao** | — | H | 0.67 | 670 | 600 | 93.7 | 12.1 | 0.27 |
| 233 | **Paper Birch** | — | H | 0.61 | 610 | 505 | 84.8 | 10.97 | 0.25 |
| 234 | **Parana Pine** | — | S | 0.55 | 545 | 410 | 92.3 | 11.37 | 0.23 |
| 235 | **Patula Pine** | — | S | 0.57 | 575 | 452 | 79.3 | 10.09 | 0.24 |
| 236 | **Pau Rosa** | — | H | 1.03 | 1030 | 1330 | 166.2 | 17.1 | 0.4 |
| 237 | **Paulownia** | *Paulownia tomentosa* | H | 0.28 | 280 | 120 | 37.8 | 4.38 | 0.14 |
| 238 | **Pear** | *Pyrus communis* | H | 0.69 | 690 | 634 | 83.3 | 7.8 | 0.28 |
| 239 | **Pear Hawthorn** | — | H | 0.78 | 775 | 786 | 119.0 | 9.43 | 0.31 |
| 240 | **Pecan** | *Carya illinoinensis* | H | 0.73 | 735 | 713 | 94.5 | 11.93 | 0.3 |
| 241 | **Pericopsis** | — | H | 0.77 | 770 | 777 | 121.7 | 14.94 | 0.31 |
| 242 | **Persimmon** | *Diospyros virginiana* | H | 0.83 | 835 | 902 | 122.1 | 13.86 | 0.33 |
| 243 | **Peruvian Walnut** | *Juglans neotropica* | H | 0.6 | 600 | 490 | 77.0 | 7.81 | 0.25 |
| 244 | **Pheasantwood** | — | H | 0.8 | 800 | 834 | 85.8 | 10.9 | 0.32 |
| 245 | **Pignut Hickory** | — | H | 0.83 | 835 | 902 | 138.6 | 15.59 | 0.33 |
| 246 | **Pin Oak** | — | H | 0.7 | 705 | 660 | 95.6 | 11.81 | 0.28 |
| 247 | **Pink Ash** | — | H | 0.52 | 515 | 369 | 55.0 | 9.1 | 0.22 |
| 248 | **Pink Lapacho** | — | H | 0.96 | 960 | 1168 | 160.1 | 19.13 | 0.38 |
| 249 | **Pinyon Pine** | — | S | 0.59 | 595 | 482 | 53.8 | 7.86 | 0.25 |
| 250 | **Pitch Pine** | — | S | 0.55 | 545 | 410 | 74.5 | 9.86 | 0.23 |
| 251 | **Plum** | *Prunus domestica* | H | 0.8 | 795 | 824 | 88.4 | 10.19 | 0.32 |
| 252 | **Pond Pine** | — | S | 0.61 | 610 | 505 | 80.0 | 12.07 | 0.25 |
| 253 | **Ponderosa Pine** | *Pinus ponderosa* | S | 0.45 | 450 | 288 | 64.8 | 8.9 | 0.2 |
| 254 | **Port Orford Cedar** | *Chamaecyparis lawsoniana* | S | 0.47 | 465 | 306 | 84.8 | 11.35 | 0.2 |
| 255 | **Post Oak** | — | H | 0.75 | 750 | 740 | 90.1 | 10.31 | 0.3 |
| 256 | **Preciosa** | — | H | 1.1 | 1100 | 1502 | 183.9 | 17.56 | 0.42 |
| 257 | **Primavera** | — | H | 0.47 | 465 | 306 | 70.5 | 7.81 | 0.2 |
| 258 | **Prosopis Juliflora** | — | H | 0.8 | 800 | 834 | 115.5 | 12.13 | 0.32 |
| 259 | **Pumpkin Ash** | — | H | 0.57 | 575 | 452 | 76.6 | 8.76 | 0.24 |
| 260 | **Pyinma** | — | H | 0.7 | 705 | 660 | 97.4 | 10.8 | 0.28 |
| 261 | **Quaking Aspen** | — | H | 0.41 | 415 | 248 | 57.9 | 8.14 | 0.18 |
| 262 | **Quebracho** | — | H | 1.21 | 1205 | 1779 | 144.9 | 14.58 | 0.46 |
| 263 | **Queensland Kauri** | — | S | 0.47 | 470 | 312 | 64.0 | 7.8 | 0.2 |
| 264 | **Quina** | — | H | 0.93 | 930 | 1101 | 157.0 | 16.76 | 0.37 |
| 265 | **Radiata Pine** | *Pinus radiata* | S | 0.52 | 515 | 369 | 79.2 | 10.06 | 0.22 |
| 266 | **Ramin** | — | H | 0.66 | 655 | 576 | 123.1 | 15.55 | 0.27 |
| 267 | **Raspberry Jam** | — | H | 1.04 | 1040 | 1354 | 130.0 | 18.5 | 0.4 |
| 268 | **Red Alder** | — | H | 0.45 | 450 | 288 | 67.6 | 9.52 | 0.2 |
| 269 | **Red Ash** | — | H | 0.72 | 725 | 695 | 134.0 | 19.0 | 0.29 |
| 270 | **Red Bloodwood** | — | H | 0.86 | 865 | 963 | 99.1 | 12.83 | 0.34 |
| 271 | **Red Elm** | *Ulmus rubra* | H | 0.6 | 600 | 490 | 89.7 | 10.28 | 0.25 |
| 272 | **Red Maple** | — | H | 0.61 | 610 | 505 | 92.4 | 11.31 | 0.25 |
| 273 | **Red Palm** | *Cyrtostachys renda* | H | 0.82 | 820 | 873 | 89.4 | 11.41 | 0.33 |
| 274 | **Red Pine** | *Pinus resinosa* | S | 0.55 | 545 | 410 | 75.9 | 11.24 | 0.23 |
| 275 | **Rengas** | — | H | 0.77 | 765 | 767 | 90.3 | 13.2 | 0.31 |
| 276 | **Rhodesian Teak** | — | H | 0.89 | 890 | 1015 | 84.3 | 8.48 | 0.35 |
| 277 | **River Red Gum** | — | H | 0.87 | 870 | 974 | 123.8 | 11.8 | 0.34 |
| 278 | **Rock Elm** | — | H | 0.76 | 755 | 749 | 102.1 | 10.62 | 0.31 |
| 279 | **Rock Sheoak** | — | H | 0.89 | 890 | 1015 | 94.0 | 14.0 | 0.35 |
| 280 | **Rose Gum** | — | H | 0.64 | 640 | 552 | 107.8 | 14.15 | 0.26 |
| 281 | **Rose Sheoak** | — | H | 0.94 | 940 | 1123 | 145.0 | 20.0 | 0.37 |
| 282 | **Rough Barked Apple** | — | H | 0.86 | 865 | 963 | 110.0 | 11.0 | 0.34 |
| 283 | **Rowan** | — | H | 0.77 | 770 | 777 | 119.3 | 10.28 | 0.31 |
| 284 | **Sand Pine** | — | S | 0.55 | 545 | 410 | 80.0 | 9.72 | 0.23 |
| 285 | **Sande** | — | H | 0.56 | 555 | 424 | 94.9 | 14.65 | 0.24 |
| 286 | **Sapodilla** | — | H | 1.04 | 1040 | 1354 | 184.2 | 20.41 | 0.4 |
| 287 | **Scarlet Oak** | — | H | 0.73 | 735 | 713 | 110.9 | 12.18 | 0.3 |
| 288 | **Scots Pine** | *Pinus sylvestris* | S | 0.55 | 550 | 417 | 83.3 | 10.08 | 0.23 |
| 289 | **Serviceberry** | — | H | 0.83 | 835 | 902 | 116.6 | 12.97 | 0.33 |
| 290 | **Sessile Oak** | — | H | 0.71 | 710 | 668 | 97.1 | 10.47 | 0.29 |
| 291 | **Shagbark Hickory** | — | H | 0.8 | 800 | 834 | 139.3 | 14.9 | 0.32 |
| 292 | **Shellbark Hickory** | — | H | 0.77 | 770 | 777 | 124.8 | 13.03 | 0.31 |
| 293 | **Shittim** | — | H | 0.66 | 660 | 584 | 98.1 | 10.69 | 0.27 |
| 294 | **Shortleaf Pine** | — | S | 0.57 | 570 | 445 | 90.3 | 12.1 | 0.24 |
| 295 | **Shumard Oak** | — | H | 0.73 | 730 | 704 | 123.0 | 14.86 | 0.3 |
| 296 | **Siam Balsa** | — | H | 0.4 | 400 | 231 | 50.6 | 7.17 | 0.18 |
| 297 | **Silver Birch** | *Betula pendula* | H | 0.64 | 640 | 552 | 114.3 | 13.96 | 0.26 |
| 298 | **Silver Maple** | *Acer saccharinum* | H | 0.53 | 530 | 389 | 61.4 | 7.86 | 0.23 |
| 299 | **Sissoo** | — | H | 0.77 | 770 | 777 | 97.5 | 10.4 | 0.31 |
| 300 | **Slash Pine** | — | S | 0.66 | 655 | 576 | 112.4 | 13.7 | 0.27 |
| 301 | **Smooth Barked Apple** | — | H | 0.99 | 990 | 1236 | 132.0 | 16.0 | 0.39 |
| 302 | **Sneezewood** | — | H | 1.0 | 1000 | 1260 | 145.5 | 17.7 | 0.39 |
| 303 | **Soto** | — | H | 1.28 | 1280 | 1989 | 148.7 | 15.69 | 0.49 |
| 304 | **Sourwood** | — | H | 0.61 | 610 | 505 | 80.0 | 10.62 | 0.25 |
| 305 | **Southern Magnolia** | — | H | 0.56 | 560 | 431 | 77.2 | 9.66 | 0.24 |
| 306 | **Southern Red Oak** | — | H | 0.68 | 675 | 609 | 83.0 | 10.2 | 0.28 |
| 307 | **Southern Redcedar** | — | S | 0.51 | 505 | 356 | 64.8 | 8.07 | 0.22 |
| 308 | **Southern Silky Oak** | — | H | 0.59 | 590 | 475 | 74.4 | 7.93 | 0.25 |
| 309 | **Spotted Gum** | — | H | 0.94 | 940 | 1123 | 141.8 | 19.77 | 0.37 |
| 310 | **Spruce Pine** | — | S | 0.53 | 525 | 382 | 71.0 | 9.69 | 0.23 |
| 311 | **Subalpine Fir** | — | S | 0.53 | 530 | 389 | 58.0 | 9.13 | 0.23 |
| 312 | **Sugar Pine** | *Pinus lambertiana* | S | 0.4 | 400 | 231 | 56.6 | 8.21 | 0.18 |
| 313 | **Sugi** | *Cryptomeria japonica* | H | 0.36 | 360 | 190 | 36.4 | 7.65 | 0.17 |
| 314 | **Sumac** | — | H | 0.53 | 530 | 389 | 70.4 | 8.21 | 0.23 |
| 315 | **Sumatran Pine** | — | S | 0.71 | 710 | 668 | 96.4 | 14.9 | 0.29 |
| 316 | **Swamp Chestnut Oak** | — | H | 0.78 | 780 | 795 | 94.9 | 12.09 | 0.31 |
| 317 | **Swamp Mahogany** | — | H | 0.79 | 785 | 805 | 120.6 | 14.12 | 0.32 |
| 318 | **Swamp White Oak** | — | H | 0.77 | 765 | 767 | 120.0 | 13.99 | 0.31 |
| 319 | **Sweet Birch** | *Betula lenta* | H | 0.73 | 735 | 713 | 116.6 | 14.97 | 0.3 |
| 320 | **Sweet Cherry** | *Prunus avium* | H | 0.6 | 600 | 490 | 103.3 | 10.55 | 0.25 |
| 321 | **Sweet Chestnut** | *Castanea sativa* | H | 0.59 | 590 | 475 | 71.4 | 8.61 | 0.25 |
| 322 | **Sweetbay** | — | H | 0.55 | 545 | 410 | 75.2 | 11.31 | 0.23 |
| 323 | **Sweetgum** | *Liquidambar styraciflua* | H | 0.55 | 545 | 410 | 86.2 | 11.31 | 0.23 |
| 324 | **Sycamore** | *Platanus occidentalis* | H | 0.55 | 545 | 410 | 69.0 | 9.79 | 0.23 |
| 325 | **Sycamore Maple** | — | H | 0.61 | 615 | 512 | 98.1 | 9.92 | 0.25 |
| 326 | **Table Mountain Pine** | — | S | 0.57 | 575 | 452 | 80.0 | 10.69 | 0.24 |
| 327 | **Tamarack** | *Larix laricina* | H | 0.59 | 595 | 482 | 80.0 | 11.31 | 0.25 |
| 328 | **Tamarind** | *Tamarindus indica* | H | 0.85 | 850 | 933 | 111.0 | 13.22 | 0.34 |
| 329 | **Tambootie** | — | H | 0.95 | 955 | 1157 | 102.7 | 9.08 | 0.37 |
| 330 | **Tamo Ash** | — | H | 0.56 | 560 | 431 | 74.6 | 8.24 | 0.24 |
| 331 | **Tanoak** | — | H | 0.68 | 675 | 609 | 114.8 | 14.29 | 0.28 |
| 332 | **Tasmanian Myrtle** | — | H | 0.62 | 625 | 528 | 98.2 | 12.62 | 0.26 |
| 333 | **Tatabu** | — | H | 0.93 | 925 | 1090 | 152.2 | 19.82 | 0.37 |
| 334 | **Thuya** | — | H | 0.68 | 680 | 617 | 93.8 | 12.41 | 0.28 |
| 335 | **Timborana** | *Pseudopiptadenia suaveolens* | H | 0.8 | 800 | 834 | 120.0 | 16.41 | 0.32 |
| 336 | **Tineo** | — | H | 0.71 | 710 | 668 | 90.0 | 10.81 | 0.29 |
| 337 | **Tornillo** | — | H | 0.56 | 555 | 424 | 68.1 | 10.86 | 0.24 |
| 338 | **Turkey Oak** | — | H | 0.72 | 720 | 686 | 114.3 | 10.81 | 0.29 |
| 339 | **Turpentine** | — | H | 0.94 | 940 | 1123 | 149.0 | 15.5 | 0.37 |
| 340 | **Utile** | *Entandrophragma utile* | H | 0.64 | 635 | 544 | 103.8 | 11.65 | 0.26 |
| 341 | **Virginia Pine** | — | S | 0.52 | 515 | 369 | 89.7 | 10.48 | 0.22 |
| 342 | **Waddywood** | — | H | 1.43 | 1430 | 2441 | 150.0 | 21.5 | 0.54 |
| 343 | **Wamara** | — | H | 1.08 | 1080 | 1452 | 196.5 | 24.38 | 0.42 |
| 344 | **Water Hickory** | — | H | 0.69 | 690 | 634 | 122.8 | 13.93 | 0.28 |
| 345 | **Water Oak** | — | H | 0.72 | 725 | 695 | 114.6 | 14.02 | 0.29 |
| 346 | **Water Tupelo** | — | H | 0.55 | 550 | 417 | 66.5 | 8.62 | 0.23 |
| 347 | **West African Albizia** | — | H | 0.6 | 605 | 497 | 82.7 | 10.91 | 0.25 |
| 348 | **Western Hemlock** | *Tsuga heterophylla* | S | 0.47 | 465 | 306 | 77.9 | 11.24 | 0.2 |
| 349 | **Western Juniper** | — | S | 0.44 | 440 | 276 | 61.5 | 4.43 | 0.19 |
| 350 | **Western Larch** | *Larix occidentalis* | S | 0.57 | 575 | 452 | 89.7 | 12.9 | 0.24 |
| 351 | **Western Sheoak** | — | H | 0.73 | 730 | 704 | 98.0 | 9.36 | 0.3 |
| 352 | **Western White Pine** | *Pinus monticola* | S | 0.43 | 435 | 270 | 66.9 | 10.07 | 0.19 |
| 353 | **White Fir** | *Abies concolor* | S | 0.41 | 415 | 248 | 66.9 | 10.24 | 0.18 |
| 354 | **White Meranti** | — | H | 0.59 | 590 | 475 | 80.2 | 10.24 | 0.25 |
| 355 | **White Poplar** | *Populus alba* | H | 0.44 | 440 | 276 | 65.0 | 8.9 | 0.19 |
| 356 | **White Willow** | — | H | 0.4 | 400 | 231 | 56.2 | 7.76 | 0.18 |
| 357 | **Willow Leaf Red Quebracho** | — | H | 1.21 | 1210 | 1792 | 126.5 | 15.12 | 0.46 |
| 358 | **Willow Oak** | — | H | 0.77 | 770 | 777 | 102.4 | 12.44 | 0.31 |
| 359 | **Winged Elm** | — | H | 0.68 | 675 | 609 | 102.1 | 11.38 | 0.28 |
| 360 | **Wych Elm** | — | H | 0.6 | 605 | 497 | 98.2 | 11.14 | 0.25 |
| 361 | **Yellow Box** | — | H | 1.07 | 1075 | 1440 | 122.0 | 14.0 | 0.41 |
| 362 | **Yellow Buckeye** | — | H | 0.4 | 400 | 231 | 51.7 | 8.07 | 0.18 |
| 363 | **Yellow Gum** | — | H | 1.01 | 1010 | 1283 | 111.0 | 12.0 | 0.39 |
| 364 | **Yellow Lapacho** | — | H | 1.1 | 1100 | 1502 | 162.6 | 15.53 | 0.42 |
| 365 | **Yellow Meranti** | — | H | 0.56 | 565 | 438 | 80.8 | 10.68 | 0.24 |
| 366 | **Yellow Silverballi** | — | H | 0.61 | 610 | 505 | 67.0 | 9.1 | 0.25 |

---

## Appendix: Alphabetical Index

| Species | ID | Tier | SG | Density | Janka | MOR | MOE |
|---------|-----|------|-----|---------|-------|-----|-----|
| Abura | `abura` | ⚪ exploratory | 0.56 | 560 | 431 | 81.1 | 9.56 |
| Adirondack Spruce (Red Spruce) | `spruce_adirondack` | 🟢 primary | 0.43 | 435 | 560 | 74.0 | 11.2 |
| Afata | `afata` | ⚪ exploratory | 0.63 | 630 | 536 | 126.9 | 13.38 |
| African Blackwood | `african_blackwood` | 🟡 emerging | 1.27 | 1270 | 1960 | 213.6 | 17.95 |
| African Crabwood | `african_crabwood` | ⚪ exploratory | 0.69 | 695 | 643 | 102.0 | 14.77 |
| African Ebony | `ebony_african` | 🟢 primary | 1.03 | 1030 | 3080 | — | — |
| African Juniper | `african_juniper` | ⚪ exploratory | 0.54 | 535 | 396 | 80.4 | 10.09 |
| African Mahogany (Khaya) | `mahogany_african` | 🟢 primary | 0.5 | 530 | 830 | — | — |
| African Mesquite | `african_mesquite` | ⚪ exploratory | 0.94 | 945 | 1134 | 130.5 | 13.92 |
| African Padauk | `african_padauk` | 🟡 emerging | 0.74 | 745 | 731 | 126.7 | 13.07 |
| African Walnut | `african_walnut` | ⚪ exploratory | 0.54 | 540 | 403 | 84.5 | 9.24 |
| Afrormosia | `afrormosia` | ⚪ exploratory | 0.72 | 725 | 695 | 100.9 | 11.83 |
| Afzelia Doussie | `afzelia_doussie` | ⚪ exploratory | 0.81 | 805 | 843 | 122.3 | 14.44 |
| Afzelia Xylay | `afzelia_xylay` | ⚪ exploratory | 0.82 | 825 | 882 | 118.7 | 13.37 |
| Ailanthus | `ailanthus` | ⚪ exploratory | 0.6 | 600 | 490 | 76.2 | 11.19 |
| Alaska Paper Birch | `alaska_paper_birch` | ⚪ exploratory | 0.61 | 610 | 505 | 93.8 | 13.1 |
| Alaskan Yellow Cedar | `alaskan_yellow_cedar` | ⚪ exploratory | 0.49 | 495 | 343 | 76.6 | 9.79 |
| Alder Leaf Birch | `alder_leaf_birch` | ⚪ exploratory | 0.53 | 530 | 389 | 61.9 | 8.52 |
| Algarrobo Blanco | `algarrobo_blanco` | ⚪ exploratory | 0.79 | 785 | 805 | 63.1 | 6.08 |
| Aliso Del Cerro | `aliso_del_cerro` | ⚪ exploratory | 0.44 | 440 | 276 | 57.4 | 7.83 |
| Alligator Juniper | `alligator_juniper` | ⚪ exploratory | 0.58 | 585 | 467 | 46.2 | 4.48 |
| Amazon Rosewood | `amazon_rosewood` | ⚪ exploratory | 1.08 | 1085 | 1465 | 116.9 | 12.9 |
| Amendoim | `amendoim` | ⚪ exploratory | 0.8 | 800 | 834 | 108.8 | 12.21 |
| American Basswood | `basswood` | 🟢 primary | 0.38 | 415 | 410 | 60.0 | 10.07 |
| American Beech | `beech_american` | 🔵 established | 0.68 | 720 | 1300 | — | — |
| American Chestnut | `american_chestnut` | 🟡 emerging | 0.48 | 480 | 324 | 59.3 | 8.48 |
| American Elm | `american_elm` | ⚪ exploratory | 0.56 | 560 | 431 | 81.4 | 9.24 |
| American Hornbeam | `american_hornbeam` | ⚪ exploratory | 0.79 | 785 | 805 | 112.4 | 11.68 |
| Andaman Padauk | `andaman_padauk` | ⚪ exploratory | 0.77 | 770 | 777 | 101.9 | 12.1 |
| Andean Alder | `andean_alder` | ⚪ exploratory | 0.39 | 385 | 215 | 51.2 | 7.81 |
| Andiroba | `andiroba` | ⚪ exploratory | 0.66 | 660 | 584 | 107.4 | 13.55 |
| Angelim Vermelho | `angelim_vermelho` | ⚪ exploratory | 1.07 | 1070 | 1428 | 156.0 | 19.39 |
| Anigre | `anigre` | ⚪ exploratory | 0.55 | 550 | 417 | 83.0 | 10.95 |
| Apple | `apple` | ⚪ exploratory | 0.83 | 830 | 892 | 88.3 | 8.76 |
| Araracanga | `araracanga` | ⚪ exploratory | 0.94 | 935 | 1112 | 152.1 | 20.97 |
| Argentine Lignum Vitae | `argentine_lignum_vitae` | ⚪ exploratory | 1.2 | 1200 | 1765 | 139.0 | 18.05 |
| Argentine Osage Orange | `argentine_osage_orange` | ⚪ exploratory | 0.91 | 910 | 1058 | 134.9 | 14.9 |
| Atlantic White Cedar | `atlantic_white_cedar` | ⚪ exploratory | 0.38 | 380 | 210 | 46.9 | 6.41 |
| Atlas Cedar | `atlas_cedar` | ⚪ exploratory | 0.53 | 530 | 389 | 87.2 | 9.78 |
| Australian Blackwood | `australian_blackwood` | 🟡 emerging | 0.64 | 640 | 552 | 103.6 | 14.82 |
| Australian Buloke | `australian_buloke` | ⚪ exploratory | 1.08 | 1085 | 1465 | 130.0 | 18.5 |
| Australian Cypress | `australian_cypress` | 🟡 emerging | 0.65 | 650 | 568 | 79.6 | 9.32 |
| Australian Red Cedar | `australian_red_cedar` | ⚪ exploratory | 0.48 | 485 | 330 | 71.5 | 9.22 |
| Austrian Pine | `austrian_pine` | ⚪ exploratory | 0.47 | 475 | 318 | 64.4 | 10.81 |
| Avodire | `avodire` | ⚪ exploratory | 0.57 | 575 | 452 | 106.2 | 11.13 |
| Balau | `balau` | ⚪ exploratory | 0.85 | 850 | 933 | 122.3 | 16.95 |
| Bald Cypress | `cypress_bald` | 🔵 established | 0.46 | 510 | 510 | 73.1 | 9.93 |
| Balsa | `balsa` | ⚪ exploratory | 0.15 | 150 | 38 | 19.6 | 3.71 |
| Balsam Fir | `balsam_fir` | ⚪ exploratory | 0.4 | 400 | 231 | 60.7 | 9.57 |
| Balsam Poplar | `balsam_poplar` | ⚪ exploratory | 0.37 | 370 | 200 | 46.9 | 7.59 |
| Bamboo | `bamboo` | ⚪ exploratory | 0.5 | 500 | 349 | 76.0 | 18.0 |
| Batai | `batai` | ⚪ exploratory | 0.38 | 375 | 205 | 55.2 | 7.91 |
| Beefwood | `beefwood` | ⚪ exploratory | 0.96 | 965 | 1179 | 94.0 | 14.0 |
| Bekak | `bekak` | ⚪ exploratory | 0.77 | 765 | 767 | 145.0 | 15.77 |
| Beli | `beli` | ⚪ exploratory | 0.77 | 770 | 777 | 134.8 | 16.09 |
| Bigleaf Maple | `bigleaf_maple` | ⚪ exploratory | 0.55 | 545 | 410 | 73.8 | 10.0 |
| Bigtooth Aspen | `bigtooth_aspen` | ⚪ exploratory | 0.43 | 435 | 270 | 62.8 | 9.86 |
| Bitternut Hickory | `bitternut_hickory` | ⚪ exploratory | 0.73 | 735 | 713 | 117.9 | 12.35 |
| Black Ash | `black_ash` | ⚪ exploratory | 0.55 | 545 | 410 | 86.9 | 11.0 |
| Black Cherry | `cherry_black` | 🔵 established | 0.53 | 560 | 950 | 78.0 | 10.24 |
| Black Cottonwood | `black_cottonwood` | ⚪ exploratory | 0.39 | 385 | 215 | 58.6 | 8.76 |
| Black Ironwood | `black_ironwood` | ⚪ exploratory | 1.35 | 1355 | 2210 | 125.5 | 20.46 |
| Black Locust | `black_locust` | 🟡 emerging | 0.77 | 770 | 777 | 133.8 | 14.14 |
| Black Maple | `black_maple` | ⚪ exploratory | 0.64 | 640 | 552 | 91.7 | 11.17 |
| Black Mesquite | `black_mesquite` | ⚪ exploratory | 0.82 | 825 | 882 | 77.3 | 7.7 |
| Black Oak | `black_oak` | ⚪ exploratory | 0.71 | 715 | 677 | 99.5 | 11.97 |
| Black Palm | `black_palm` | 🟡 emerging | 0.97 | 970 | 1191 | 137.6 | 15.6 |
| Black Poplar | `black_poplar` | ⚪ exploratory | 0.39 | 385 | 215 | 63.7 | 7.21 |
| Black Siris | `black_siris` | ⚪ exploratory | 0.76 | 760 | 758 | 96.4 | 11.77 |
| Black Spruce | `black_spruce` | ⚪ exploratory | 0.45 | 450 | 288 | 69.7 | 10.5 |
| Black Tupelo | `black_tupelo` | ⚪ exploratory | 0.55 | 545 | 410 | 65.5 | 8.19 |
| Black Walnut | `walnut_black` | 🟢 primary | 0.56 | 610 | 1010 | 90.7 | 11.34 |
| Black Wattle | `black_wattle` | ⚪ exploratory | 0.73 | 730 | 704 | 121.8 | 14.6 |
| Black Willow | `black_willow` | ⚪ exploratory | 0.41 | 415 | 248 | 53.8 | 6.97 |
| Blackheart Sassafras | `blackheart_sassafras` | ⚪ exploratory | 0.62 | 620 | 520 | 100.5 | 12.6 |
| Bloodwood | `bloodwood` | 🟡 emerging | 1.05 | 1050 | 1379 | 174.4 | 20.78 |
| Blue Ash | `blue_ash` | ⚪ exploratory | 0.64 | 640 | 552 | 95.2 | 9.66 |
| Blue Gum | `blue_gum` | ⚪ exploratory | 0.82 | 820 | 873 | 134.7 | 18.76 |
| Bocote | `bocote` | 🔵 established | 0.75 | 775 | 2200 | 114.4 | 12.19 |
| Bomanga | `bomanga` | ⚪ exploratory | 0.57 | 570 | 445 | 86.6 | 12.19 |
| Bosse | `bosse` | ⚪ exploratory | 0.6 | 600 | 490 | 103.2 | 10.91 |
| Box Elder | `box_elder` | ⚪ exploratory | 0.48 | 485 | 330 | 55.2 | 7.24 |
| Boxwood | `boxwood` | ⚪ exploratory | 0.96 | 965 | 1179 | 136.5 | 12.27 |
| Brazilian Pau Rosa | `brazilian_pau_rosa` | ⚪ exploratory | 0.73 | 730 | 704 | 130.0 | 17.0 |
| Brazilian Rosewood | `rosewood_brazilian` | 🟢 primary | 0.82 | 835 | 2790 | — | — |
| Brazilwood | `brazilwood` | ⚪ exploratory | 1.05 | 1050 | 1379 | 176.1 | 20.2 |
| Breadnut | `breadnut` | ⚪ exploratory | 0.75 | 750 | 740 | 112.6 | 14.37 |
| Broad Leaved Apple | `broad_leaved_apple` | ⚪ exploratory | 0.75 | 750 | 740 | 78.0 | 12.5 |
| Brown Ebony | `brown_ebony` | ⚪ exploratory | 1.16 | 1160 | 1658 | 158.0 | 18.7 |
| Brownheart | `brownheart` | ⚪ exploratory | 0.93 | 925 | 1090 | 150.5 | 17.83 |
| Bubinga | `bubinga` | 🔵 established | 0.86 | 890 | 2410 | 168.3 | 18.41 |
| Buckthorn | `buckthorn` | ⚪ exploratory | 0.6 | 605 | 497 | 60.0 | 6.62 |
| Bulletwood | `bulletwood` | ⚪ exploratory | 1.08 | 1080 | 1452 | 192.2 | 23.06 |
| Bur Oak | `bur_oak` | ⚪ exploratory | 0.72 | 725 | 695 | 75.3 | 7.17 |
| Burma Padauk | `burma_padauk` | ⚪ exploratory | 0.86 | 865 | 963 | 138.8 | 14.14 |
| Burmese Blackwood | `burmese_blackwood` | ⚪ exploratory | 1.06 | 1060 | 1403 | 78.9 | 11.03 |
| Butternut | `butternut` | ⚪ exploratory | 0.43 | 435 | 270 | 55.9 | 8.14 |
| California Black Oak | `california_black_oak` | ⚪ exploratory | 0.62 | 620 | 520 | 59.4 | 6.76 |
| California Red Fir | `california_red_fir` | ⚪ exploratory | 0.43 | 435 | 270 | 71.5 | 10.23 |
| Camphor | `camphor` | 🟡 emerging | 0.52 | 520 | 376 | 80.5 | 11.56 |
| Canarywood | `canarywood` | 🟡 emerging | 0.83 | 830 | 892 | 131.6 | 14.93 |
| Candlenut | `candlenut` | ⚪ exploratory | 0.39 | 390 | 221 | 50.9 | 7.33 |
| Cape Holly | `cape_holly` | ⚪ exploratory | 0.64 | 640 | 552 | 75.4 | 9.06 |
| Caribbean Pine | `caribbean_pine` | ⚪ exploratory | 0.62 | 625 | 528 | 92.0 | 12.03 |
| Catalpa | `catalpa` | ⚪ exploratory | 0.46 | 460 | 299 | 64.8 | 8.35 |
| Cedar Elm | `cedar_elm` | ⚪ exploratory | 0.66 | 655 | 576 | 93.1 | 10.21 |
| Cedar Of Lebanon | `cedar_of_lebanon` | ⚪ exploratory | 0.52 | 520 | 376 | 82.0 | 10.1 |
| Cerejeira | `cerejeira` | ⚪ exploratory | 0.56 | 560 | 431 | 72.9 | 10.88 |
| Ceylon Ebony | `ceylon_ebony` | ⚪ exploratory | 0.92 | 915 | 1069 | 128.6 | 14.07 |
| Chanfuta | `chanfuta` | ⚪ exploratory | 0.83 | 835 | 902 | 109.0 | 11.75 |
| Chechen | `chechen` | 🟡 emerging | 0.88 | 880 | 994 | 93.0 | 15.53 |
| Cheesewood | `cheesewood` | ⚪ exploratory | 0.38 | 380 | 210 | 54.0 | 7.52 |
| Cherrybark Oak | `cherrybark_oak` | ⚪ exploratory | 0.79 | 785 | 805 | 124.8 | 15.7 |
| Chestnut Oak | `chestnut_oak` | ⚪ exploratory | 0.75 | 750 | 740 | 91.7 | 11.0 |
| Chichipate | `chichipate` | ⚪ exploratory | 1.0 | 1005 | 1271 | 151.1 | 20.39 |
| Coast Redwood | `coast_redwood` | ⚪ exploratory | 0.41 | 415 | 248 | 61.7 | 8.41 |
| Cocobolo | `cocobolo` | 🟢 primary | 1.1 | 1095 | 2960 | — | — |
| Coffeetree | `coffeetree` | ⚪ exploratory | 0.68 | 675 | 609 | 72.4 | 9.79 |
| Coolibah | `coolibah` | ⚪ exploratory | 1.13 | 1130 | 1579 | 144.5 | 17.24 |
| Crack Willow | `crack_willow` | ⚪ exploratory | 0.43 | 430 | 264 | 64.9 | 7.95 |
| Cuban Mahogany | `cuban_mahogany` | ⚪ exploratory | 0.6 | 600 | 490 | 74.4 | 9.31 |
| Cucumbertree | `cucumbertree` | ⚪ exploratory | 0.53 | 530 | 389 | 84.8 | 12.55 |
| Cumaru | `cumaru` | 🟡 emerging | 1.08 | 1085 | 1465 | 175.1 | 22.33 |
| Curupay | `curupay` | 🟡 emerging | 1.02 | 1025 | 1318 | 193.2 | 18.04 |
| Cyprus Cedar | `cyprus_cedar` | ⚪ exploratory | 0.52 | 520 | 376 | 82.0 | 10.1 |
| Dahoma | `dahoma` | ⚪ exploratory | 0.69 | 695 | 643 | 111.6 | 12.9 |
| Dark Red Meranti | `dark_red_meranti` | ⚪ exploratory | 0.68 | 675 | 609 | 87.7 | 12.02 |
| Dawn Redwood | `dawn_redwood` | ⚪ exploratory | 0.34 | 335 | 167 | 61.4 | 6.12 |
| Deglupta | `deglupta` | ⚪ exploratory | 0.5 | 500 | 349 | 79.6 | 10.79 |
| Dogwood | `dogwood` | ⚪ exploratory | 0.81 | 815 | 863 | 115.3 | 13.26 |
| Doi | `doi` | ⚪ exploratory | 0.61 | 610 | 505 | 79.7 | 11.39 |
| Douglas-Fir | `douglas_fir` | 🔵 established | 0.51 | 530 | 660 | 75.3 | 10.0 |
| Downy Birch | `downy_birch` | ⚪ exploratory | 0.62 | 625 | 528 | 122.5 | 12.03 |
| Dry Zone Mahogany | `dry_zone_mahogany` | ⚪ exploratory | 0.77 | 770 | 777 | 92.8 | 11.13 |
| Dutch Elm | `dutch_elm` | ⚪ exploratory | 0.57 | 575 | 452 | 68.7 | 7.52 |
| East African Olive | `east_african_olive` | ⚪ exploratory | 0.97 | 975 | 1202 | 155.4 | 17.77 |
| East Indian Kauri | `east_indian_kauri` | ⚪ exploratory | 0.52 | 520 | 376 | 67.0 | 9.3 |
| East Indian Rosewood | `rosewood_east_indian` | 🟢 primary | 0.8 | 830 | 2440 | — | — |
| East Indian Satinwood | `east_indian_satinwood` | ⚪ exploratory | 0.97 | 970 | 1191 | 130.8 | 14.01 |
| Eastern Cottonwood | `eastern_cottonwood` | ⚪ exploratory | 0.45 | 450 | 288 | 58.6 | 9.45 |
| Eastern Hemlock | `eastern_hemlock` | ⚪ exploratory | 0.45 | 450 | 288 | 61.4 | 8.28 |
| Eastern Red Cedar | `eastern_red_cedar` | ⚪ exploratory | 0.53 | 530 | 389 | 60.7 | 6.07 |
| Eastern White Pine | `pine_eastern_white` | 🔵 established | 0.37 | 385 | 380 | — | — |
| Eastern White Pine | `eastern_white_pine` | ⚪ exploratory | 0.4 | 400 | 231 | 59.3 | 8.55 |
| Ebiara | `ebiara` | ⚪ exploratory | 0.72 | 725 | 695 | 109.6 | 11.14 |
| Ekki | `ekki` | ⚪ exploratory | 1.06 | 1065 | 1415 | 195.8 | 18.99 |
| Elgon Olive | `elgon_olive` | ⚪ exploratory | 0.77 | 770 | 777 | 111.3 | 10.81 |
| Endra Endra | `endra_endra` | ⚪ exploratory | 1.24 | 1240 | 1875 | 180.4 | 20.69 |
| Engelmann Spruce | `spruce_engelmann` | 🟢 primary | 0.37 | 385 | 390 | — | — |
| English Elm | `english_elm` | ⚪ exploratory | 0.56 | 565 | 438 | 65.0 | 7.12 |
| English Oak | `english_oak` | ⚪ exploratory | 0.68 | 675 | 609 | 97.1 | 10.6 |
| English Walnut | `english_walnut` | 🟡 emerging | 0.64 | 640 | 552 | 111.5 | 10.81 |
| Espave | `espave` | ⚪ exploratory | 0.5 | 500 | 349 | 62.5 | 8.71 |
| Etimoe | `etimoe` | ⚪ exploratory | 0.76 | 755 | 749 | 142.4 | 13.75 |
| European Alder | `european_alder` | ⚪ exploratory | 0.54 | 535 | 396 | 91.4 | 11.01 |
| European Ash | `european_ash` | 🟡 emerging | 0.68 | 680 | 617 | 103.6 | 12.31 |
| European Aspen | `european_aspen` | ⚪ exploratory | 0.45 | 450 | 288 | 62.0 | 9.75 |
| European Beech | `european_beech` | 🟡 emerging | 0.71 | 710 | 668 | 110.1 | 14.31 |
| European Hornbeam | `european_hornbeam` | ⚪ exploratory | 0.73 | 735 | 713 | 110.4 | 12.1 |
| European Larch | `european_larch` | ⚪ exploratory | 0.57 | 575 | 452 | 90.0 | 11.8 |
| European Lime | `european_lime` | ⚪ exploratory | 0.54 | 535 | 396 | 85.4 | 11.71 |
| European Silver Fir | `european_silver_fir` | ⚪ exploratory | 0.41 | 415 | 248 | 66.1 | 8.28 |
| European Spruce (Alpine/German) | `spruce_european` | 🟢 primary | 0.4 | 405 | 490 | 65.0 | 9.5 |
| European Yew | `european_yew` | 🟡 emerging | 0.68 | 675 | 609 | 96.8 | 10.15 |
| Field Maple | `field_maple` | ⚪ exploratory | 0.69 | 690 | 634 | 123.0 | 11.8 |
| Fijian Kauri | `fijian_kauri` | ⚪ exploratory | 0.55 | 550 | 417 | 60.0 | 9.8 |
| Freijo | `freijo` | ⚪ exploratory | 0.58 | 580 | 460 | 88.0 | 13.13 |
| Garapa | `garapa` | ⚪ exploratory | 0.82 | 820 | 873 | 127.8 | 15.57 |
| Giant Chinkapin | `giant_chinkapin` | ⚪ exploratory | 0.52 | 515 | 369 | 73.8 | 8.55 |
| Giant Sequoia | `giant_sequoia` | ⚪ exploratory | 0.38 | 375 | 205 | 52.4 | 6.79 |
| Gidgee | `gidgee` | ⚪ exploratory | 1.15 | 1150 | 1631 | 130.0 | 18.5 |
| Goncalo Alves | `goncalo_alves` | 🟡 emerging | 0.91 | 905 | 1047 | 117.0 | 16.56 |
| Gowen Cypress | `gowen_cypress` | ⚪ exploratory | 0.48 | 480 | 324 | 56.9 | 4.5 |
| Granadillo | `granadillo` | 🔵 established | 0.9 | 925 | 2790 | — | — |
| Grand Fir | `grand_fir` | ⚪ exploratory | 0.45 | 450 | 288 | 60.3 | 10.55 |
| Gray Birch | `gray_birch` | ⚪ exploratory | 0.56 | 560 | 431 | 67.6 | 7.93 |
| Gray Box | `gray_box` | ⚪ exploratory | 1.12 | 1120 | 1553 | 151.8 | 18.01 |
| Green Ash | `green_ash` | ⚪ exploratory | 0.64 | 640 | 552 | 97.2 | 11.4 |
| Greenheart | `greenheart` | 🟡 emerging | 1.01 | 1010 | 1283 | 185.5 | 24.64 |
| Guanacaste | `guanacaste` | ⚪ exploratory | 0.44 | 440 | 276 | 59.6 | 8.46 |
| Guatemalan Mora | `guatemalan_mora` | ⚪ exploratory | 0.91 | 910 | 1058 | 134.9 | 14.9 |
| Hackberry | `hackberry` | ⚪ exploratory | 0.59 | 595 | 482 | 75.9 | 8.21 |
| Hard Maple (Sugar Maple) | `maple_hard` | 🟢 primary | 0.66 | 705 | 1450 | 118.5 | 13.49 |
| Hard Milkwood | `hard_milkwood` | ⚪ exploratory | 0.74 | 740 | 722 | 84.8 | 13.52 |
| Hawaiian Koa | `koa` | 🟢 primary | 0.6 | 625 | 1170 | 87.0 | 10.37 |
| Hazelnut | `hazelnut` | ⚪ exploratory | 0.7 | 700 | 651 | 98.5 | 8.27 |
| Holly | `holly` | ⚪ exploratory | 0.64 | 640 | 552 | 71.0 | 7.66 |
| Holm Oak | `holm_oak` | ⚪ exploratory | 0.96 | 960 | 1168 | 146.4 | 13.41 |
| Honduran Mahogany | `mahogany_honduran` | 🟢 primary | 0.52 | 545 | 800 | 98.4 | 11.97 |
| Honey Locust | `honey_locust` | ⚪ exploratory | 0.76 | 755 | 749 | 101.4 | 11.24 |
| Hoop Pine | `hoop_pine` | ⚪ exploratory | 0.5 | 500 | 349 | 85.0 | 11.77 |
| Hophornbeam | `hophornbeam` | ⚪ exploratory | 0.79 | 785 | 805 | 97.2 | 11.72 |
| Horse Chestnut | `horse_chestnut` | ⚪ exploratory | 0.5 | 500 | 349 | 67.5 | 7.15 |
| Hububalli | `hububalli` | ⚪ exploratory | 0.69 | 685 | 626 | 100.8 | 12.63 |
| Huon Pine | `huon_pine` | 🟡 emerging | 0.56 | 560 | 431 | 76.3 | 9.23 |
| Idigbo | `idigbo` | ⚪ exploratory | 0.52 | 520 | 376 | 84.5 | 10.03 |
| Imbuia | `imbuia` | 🟡 emerging | 0.66 | 660 | 584 | 84.8 | 9.61 |
| Incense Cedar | `incense_cedar` | ⚪ exploratory | 0.39 | 385 | 215 | 55.2 | 7.17 |
| Indian Laurel | `indian_laurel` | ⚪ exploratory | 0.85 | 855 | 943 | 101.4 | 12.46 |
| Indian Pulai | `indian_pulai` | ⚪ exploratory | 0.41 | 410 | 242 | 55.4 | 8.41 |
| Indian Silver Greywood | `indian_silver_greywood` | ⚪ exploratory | 0.68 | 680 | 617 | 88.6 | 13.22 |
| Ipe (Brazilian Walnut) | `ipe` | 🔵 established | 1.08 | 1100 | 3510 | 168.6 | 16.7 |
| Iroko | `iroko` | 🔵 established | 0.63 | 660 | 1260 | 97.1 | 10.9 |
| Itin | `itin` | ⚪ exploratory | 1.27 | 1275 | 1974 | 153.8 | 17.38 |
| Izombe | `izombe` | ⚪ exploratory | 0.73 | 730 | 704 | 120.2 | 11.75 |
| Jack Pine | `jack_pine` | ⚪ exploratory | 0.5 | 500 | 349 | 68.3 | 9.31 |
| Japanese Larch | `japanese_larch` | ⚪ exploratory | 0.5 | 500 | 349 | 80.1 | 8.76 |
| Jarrah | `jarrah` | 🟡 emerging | 0.83 | 835 | 902 | 108.0 | 14.7 |
| Jatoba (Brazilian Cherry) | `jatoba` | 🔵 established | 0.83 | 910 | 2690 | 126.9 | 14.07 |
| Jeffrey Pine | `jeffrey_pine` | ⚪ exploratory | 0.45 | 450 | 288 | 64.1 | 8.55 |
| Jelutong | `jelutong` | ⚪ exploratory | 0.45 | 450 | 288 | 55.4 | 8.44 |
| Jucaro | `jucaro` | ⚪ exploratory | 0.99 | 990 | 1236 | 146.6 | 16.42 |
| Karri | `karri` | ⚪ exploratory | 0.89 | 885 | 1005 | 127.8 | 20.44 |
| Katalox (Mexican Ebony) | `katalox` | 🔵 established | 1.05 | 1050 | 3650 | — | — |
| Kempas | `kempas` | ⚪ exploratory | 0.88 | 880 | 994 | 118.5 | 20.09 |
| Keruing | `keruing` | ⚪ exploratory | 0.74 | 745 | 731 | 115.2 | 15.81 |
| Keyaki | `keyaki` | ⚪ exploratory | 0.62 | 620 | 520 | 96.7 | 10.73 |
| Khasi Pine | `khasi_pine` | ⚪ exploratory | 0.61 | 610 | 505 | 87.0 | 12.25 |
| Kosipo | `kosipo` | ⚪ exploratory | 0.68 | 680 | 617 | 92.7 | 11.31 |
| Koto | `koto` | ⚪ exploratory | 0.59 | 595 | 482 | 105.4 | 12.08 |
| Lancewood | `lancewood` | ⚪ exploratory | 0.98 | 980 | 1213 | 163.5 | 20.0 |
| Lati | `lati` | ⚪ exploratory | 0.79 | 785 | 805 | 127.3 | 14.81 |
| Laurel Blanco | `laurel_blanco` | ⚪ exploratory | 0.56 | 565 | 438 | 86.7 | 12.93 |
| Laurel Oak | `laurel_oak` | ⚪ exploratory | 0.74 | 740 | 722 | 98.8 | 12.37 |
| Leadwood | `leadwood` | 🟡 emerging | 1.22 | 1220 | 1820 | 144.5 | 17.2 |
| Lebbeck | `lebbeck` | ⚪ exploratory | 0.64 | 635 | 544 | 94.7 | 12.66 |
| Lebombo Ironwood | `lebombo_ironwood` | ⚪ exploratory | 0.89 | 885 | 1005 | 128.0 | 11.0 |
| Lemon Scented Gum | `lemon_scented_gum` | ⚪ exploratory | 0.95 | 950 | 1146 | 134.4 | 16.66 |
| Lemonwood | `lemonwood` | ⚪ exploratory | 0.81 | 810 | 853 | 152.4 | 15.75 |
| Leyland Cypress | `leyland_cypress` | ⚪ exploratory | 0.5 | 500 | 349 | 82.7 | 6.82 |
| Light Red Meranti | `light_red_meranti` | ⚪ exploratory | 0.48 | 480 | 324 | 77.3 | 11.39 |
| Lignum Vitae | `lignum_vitae` | 🟡 emerging | 1.26 | 1260 | 1932 | 123.9 | 17.11 |
| Limba | `limba` | ⚪ exploratory | 0.56 | 555 | 424 | 86.2 | 10.49 |
| Limber Pine | `limber_pine` | ⚪ exploratory | 0.45 | 450 | 288 | 62.8 | 8.07 |
| Live Oak | `live_oak` | ⚪ exploratory | 1.0 | 1000 | 1260 | 125.6 | 13.52 |
| Loblolly Pine | `loblolly_pine` | ⚪ exploratory | 0.57 | 570 | 445 | 88.3 | 12.3 |
| Lodgepole Pine | `lodgepole_pine` | ⚪ exploratory | 0.47 | 465 | 306 | 64.8 | 9.24 |
| London Plane | `london_plane` | ⚪ exploratory | 0.56 | 560 | 431 | 74.7 | 8.9 |
| Longleaf Pine | `longleaf_pine` | ⚪ exploratory | 0.65 | 650 | 568 | 100.0 | 13.7 |
| Louro Preto | `louro_preto` | ⚪ exploratory | 0.88 | 880 | 994 | 117.9 | 10.9 |
| Lyptus | `lyptus` | 🟡 emerging | 0.85 | 850 | 933 | 118.0 | 14.13 |
| Macacauba | `macacauba` | ⚪ exploratory | 0.95 | 950 | 1146 | 148.6 | 19.56 |
| Macassar Ebony | `ebony_macassar` | 🟢 primary | 1.09 | 1120 | 3220 | — | — |
| Machiche | `machiche` | ⚪ exploratory | 0.89 | 890 | 1015 | 173.8 | 18.93 |
| Madagascar Rosewood | `madagascar_rosewood` | 🟡 emerging | 0.94 | 935 | 1112 | 165.7 | 12.01 |
| Madrone | `madrone` | ⚪ exploratory | 0.8 | 795 | 824 | 71.7 | 8.48 |
| Makore | `makore` | 🟡 emerging | 0.69 | 685 | 626 | 112.6 | 10.71 |
| Mangium | `mangium` | ⚪ exploratory | 0.58 | 585 | 467 | 98.2 | 11.07 |
| Mango | `mango` | 🟡 emerging | 0.68 | 675 | 609 | 88.5 | 11.53 |
| Mansonia | `mansonia` | ⚪ exploratory | 0.66 | 660 | 584 | 119.8 | 11.43 |
| Marblewood | `marblewood` | 🟡 emerging | 1.0 | 1005 | 1271 | 157.1 | 19.43 |
| Maritime Pine | `maritime_pine` | ⚪ exploratory | 0.5 | 500 | 349 | 73.0 | 8.54 |
| Mediterranean Cypress | `mediterranean_cypress` | ⚪ exploratory | 0.54 | 535 | 396 | 44.6 | 5.28 |
| Merbau (Kwila) | `merbau` | 🔵 established | 0.8 | 830 | 2460 | 145.2 | 15.93 |
| Messmate | `messmate` | ⚪ exploratory | 0.75 | 750 | 740 | 112.3 | 14.29 |
| Mexican Cypress | `mexican_cypress` | ⚪ exploratory | 0.47 | 470 | 312 | 76.4 | 8.72 |
| Moabi | `moabi` | ⚪ exploratory | 0.86 | 860 | 953 | 160.3 | 16.66 |
| Mockernut Hickory | `mockernut_hickory` | ⚪ exploratory | 0.81 | 815 | 863 | 132.4 | 15.31 |
| Monkey Puzzle | `monkey_puzzle` | ⚪ exploratory | 0.54 | 535 | 396 | 96.3 | 11.57 |
| Monkeypod | `monkeypod` | ⚪ exploratory | 0.6 | 600 | 490 | 65.7 | 7.92 |
| Monkeythorn | `monkeythorn` | ⚪ exploratory | 0.8 | 800 | 834 | 112.0 | 13.14 |
| Monterey Cypress | `monterey_cypress` | 🟡 emerging | 0.52 | 515 | 369 | 81.2 | 7.81 |
| Mopane | `mopane` | 🟡 emerging | 1.07 | 1075 | 1440 | 114.0 | 13.22 |
| Mora | `mora` | 🟡 emerging | 1.01 | 1015 | 1295 | 155.5 | 19.24 |
| Mountain Ash | `mountain_ash` | ⚪ exploratory | 0.68 | 680 | 617 | 96.7 | 14.02 |
| Movingui | `movingui` | ⚪ exploratory | 0.72 | 720 | 686 | 129.2 | 12.23 |
| Mulberry | `mulberry` | 🟡 emerging | 0.69 | 690 | 634 | 80.6 | 9.32 |
| Muninga | `muninga` | 🟡 emerging | 0.6 | 605 | 497 | 98.2 | 8.73 |
| Musk Sandalwood | `musk_sandalwood` | ⚪ exploratory | 0.94 | 940 | 1123 | 124.4 | 11.13 |
| Mutenye | `mutenye` | ⚪ exploratory | 0.8 | 800 | 834 | 152.3 | 18.6 |
| Nandubay | `nandubay` | ⚪ exploratory | 1.01 | 1015 | 1295 | 44.3 | 9.79 |
| Nargusta | `nargusta` | ⚪ exploratory | 0.79 | 785 | 805 | 122.5 | 15.21 |
| Narra | `narra` | 🟡 emerging | 0.66 | 655 | 576 | 96.3 | 11.89 |
| Nepalese Alder | `nepalese_alder` | ⚪ exploratory | 0.5 | 500 | 349 | 51.0 | 8.28 |
| New Guinea Walnut | `new_guinea_walnut` | ⚪ exploratory | 0.62 | 625 | 528 | 87.0 | 11.53 |
| New Zealand Kauri | `new_zealand_kauri` | 🟡 emerging | 0.54 | 540 | 403 | 86.6 | 11.87 |
| Noble Fir | `noble_fir` | ⚪ exploratory | 0.41 | 415 | 248 | 74.4 | 11.17 |
| Norfolk Island Pine | `norfolk_island_pine` | ⚪ exploratory | 0.49 | 495 | 343 | 80.9 | 11.89 |
| Northern Red Oak | `oak_red` | 🔵 established | 0.65 | 700 | 1290 | 123.1 | 13.82 |
| Northern Silky Oak | `northern_silky_oak` | ⚪ exploratory | 0.56 | 560 | 431 | 65.7 | 8.92 |
| Northern White Cedar | `northern_white_cedar` | ⚪ exploratory | 0.35 | 350 | 181 | 44.8 | 5.52 |
| Norway Maple | `norway_maple` | ⚪ exploratory | 0.65 | 645 | 560 | 115.0 | 10.6 |
| Nutmeg Hickory | `nutmeg_hickory` | ⚪ exploratory | 0.68 | 675 | 609 | 114.5 | 11.72 |
| Nyatoh | `nyatoh` | ⚪ exploratory | 0.62 | 620 | 520 | 96.0 | 13.37 |
| Obeche | `obeche` | ⚪ exploratory | 0.38 | 380 | 210 | 59.8 | 6.44 |
| Ocote Pine | `ocote_pine` | ⚪ exploratory | 0.7 | 700 | 651 | 101.5 | 15.23 |
| Ohia | `ohia` | ⚪ exploratory | 0.92 | 915 | 1069 | 125.9 | 15.65 |
| Okoume | `okoume` | ⚪ exploratory | 0.43 | 430 | 264 | 75.0 | 8.47 |
| Olive | `olive` | 🟡 emerging | 0.98 | 980 | 1213 | 143.0 | 12.39 |
| Opepe | `opepe` | ⚪ exploratory | 0.77 | 770 | 777 | 116.3 | 13.25 |
| Oregon Ash | `oregon_ash` | ⚪ exploratory | 0.61 | 610 | 505 | 87.6 | 9.38 |
| Oregon Myrtle | `oregon_myrtle` | ⚪ exploratory | 0.64 | 635 | 544 | 66.9 | 8.45 |
| Oregon White Oak | `oregon_white_oak` | ⚪ exploratory | 0.81 | 815 | 863 | 70.3 | 7.51 |
| Osage Orange | `osage_orange` | 🟡 emerging | 0.85 | 855 | 943 | 128.6 | 11.64 |
| Ovangkol (Shedua) | `ovangkol` | 🔵 established | 0.78 | 810 | 1890 | 140.3 | 18.6 |
| Overcup Oak | `overcup_oak` | ⚪ exploratory | 0.76 | 760 | 758 | 86.9 | 9.8 |
| Pacific Maple | `pacific_maple` | ⚪ exploratory | 0.6 | 605 | 497 | 91.1 | 12.08 |
| Pacific Silver Fir | `pacific_silver_fir` | ⚪ exploratory | 0.43 | 435 | 270 | 70.6 | 11.59 |
| Pacific Yew | `pacific_yew` | 🟡 emerging | 0.7 | 705 | 660 | 104.8 | 9.31 |
| Paldao | `paldao` | ⚪ exploratory | 0.67 | 670 | 600 | 93.7 | 12.1 |
| Panga Panga | `panga_panga` | 🟡 emerging | 0.87 | 870 | 974 | 131.2 | 15.73 |
| Paper Birch | `paper_birch` | ⚪ exploratory | 0.61 | 610 | 505 | 84.8 | 10.97 |
| Parana Pine | `parana_pine` | ⚪ exploratory | 0.55 | 545 | 410 | 92.3 | 11.37 |
| Partridgewood | `partridgewood` | 🟡 emerging | 0.83 | 835 | 902 | 127.5 | 18.17 |
| Patula Pine | `patula_pine` | ⚪ exploratory | 0.57 | 575 | 452 | 79.3 | 10.09 |
| Pau Ferro (Bolivian Rosewood) | `pau_ferro` | 🔵 established | 0.85 | 880 | 2030 | 131.0 | 14.0 |
| Pau Rosa | `pau_rosa` | ⚪ exploratory | 1.03 | 1030 | 1330 | 166.2 | 17.1 |
| Pau Santo | `pau_santo` | 🟡 emerging | 1.11 | 1115 | 1541 | 187.8 | 17.85 |
| Paulownia | `paulownia` | ⚪ exploratory | 0.28 | 280 | 120 | 37.8 | 4.38 |
| Pear | `pear` | ⚪ exploratory | 0.69 | 690 | 634 | 83.3 | 7.8 |
| Pear Hawthorn | `pear_hawthorn` | ⚪ exploratory | 0.78 | 775 | 786 | 119.0 | 9.43 |
| Pecan | `pecan` | ⚪ exploratory | 0.73 | 735 | 713 | 94.5 | 11.93 |
| Pericopsis | `pericopsis` | ⚪ exploratory | 0.77 | 770 | 777 | 121.7 | 14.94 |
| Peroba Rosa | `peroba_rosa` | 🟡 emerging | 0.78 | 775 | 786 | 89.5 | 10.95 |
| Persimmon | `persimmon` | ⚪ exploratory | 0.83 | 835 | 902 | 122.1 | 13.86 |
| Peruvian Walnut | `peruvian_walnut` | ⚪ exploratory | 0.6 | 600 | 490 | 77.0 | 7.81 |
| Pheasantwood | `pheasantwood` | ⚪ exploratory | 0.8 | 800 | 834 | 85.8 | 10.9 |
| Pignut Hickory | `pignut_hickory` | ⚪ exploratory | 0.83 | 835 | 902 | 138.6 | 15.59 |
| Pin Oak | `pin_oak` | ⚪ exploratory | 0.7 | 705 | 660 | 95.6 | 11.81 |
| Pink Ash | `pink_ash` | ⚪ exploratory | 0.52 | 515 | 369 | 55.0 | 9.1 |
| Pink Ivory | `pink_ivory` | 🟡 emerging | 1.03 | 1035 | 1342 | 138.1 | 15.12 |
| Pink Lapacho | `pink_lapacho` | ⚪ exploratory | 0.96 | 960 | 1168 | 160.1 | 19.13 |
| Pinyon Pine | `pinyon_pine` | ⚪ exploratory | 0.59 | 595 | 482 | 53.8 | 7.86 |
| Pitch Pine | `pitch_pine` | ⚪ exploratory | 0.55 | 545 | 410 | 74.5 | 9.86 |
| Plum | `plum` | ⚪ exploratory | 0.8 | 795 | 824 | 88.4 | 10.19 |
| Pond Pine | `pond_pine` | ⚪ exploratory | 0.61 | 610 | 505 | 80.0 | 12.07 |
| Ponderosa Pine | `ponderosa_pine` | ⚪ exploratory | 0.45 | 450 | 288 | 64.8 | 8.9 |
| Port Orford Cedar | `port_orford_cedar` | ⚪ exploratory | 0.47 | 465 | 306 | 84.8 | 11.35 |
| Post Oak | `post_oak` | ⚪ exploratory | 0.75 | 750 | 740 | 90.1 | 10.31 |
| Preciosa | `preciosa` | ⚪ exploratory | 1.1 | 1100 | 1502 | 183.9 | 17.56 |
| Primavera | `primavera` | ⚪ exploratory | 0.47 | 465 | 306 | 70.5 | 7.81 |
| Prosopis Juliflora | `prosopis_juliflora` | ⚪ exploratory | 0.8 | 800 | 834 | 115.5 | 12.13 |
| Pumpkin Ash | `pumpkin_ash` | ⚪ exploratory | 0.57 | 575 | 452 | 76.6 | 8.76 |
| Purpleheart | `purpleheart` | 🔵 established | 0.86 | 880 | 2520 | 168.6 | 16.7 |
| Pyinma | `pyinma` | ⚪ exploratory | 0.7 | 705 | 660 | 97.4 | 10.8 |
| Quaking Aspen | `quaking_aspen` | ⚪ exploratory | 0.41 | 415 | 248 | 57.9 | 8.14 |
| Quebracho | `quebracho` | ⚪ exploratory | 1.21 | 1205 | 1779 | 144.9 | 14.58 |
| Queensland Kauri | `queensland_kauri` | ⚪ exploratory | 0.47 | 470 | 312 | 64.0 | 7.8 |
| Queensland Maple | `queensland_maple` | 🟡 emerging | 0.56 | 560 | 431 | 81.0 | 10.83 |
| Quina | `quina` | ⚪ exploratory | 0.93 | 930 | 1101 | 157.0 | 16.76 |
| Radiata Pine | `radiata_pine` | ⚪ exploratory | 0.52 | 515 | 369 | 79.2 | 10.06 |
| Ramin | `ramin` | ⚪ exploratory | 0.66 | 655 | 576 | 123.1 | 15.55 |
| Raspberry Jam | `raspberry_jam` | ⚪ exploratory | 1.04 | 1040 | 1354 | 130.0 | 18.5 |
| Red Alder | `alder` | 🟢 primary | 0.41 | 420 | 590 | — | — |
| Red Alder | `red_alder` | ⚪ exploratory | 0.45 | 450 | 288 | 67.6 | 9.52 |
| Red Ash | `red_ash` | ⚪ exploratory | 0.72 | 725 | 695 | 134.0 | 19.0 |
| Red Bloodwood | `red_bloodwood` | ⚪ exploratory | 0.86 | 865 | 963 | 99.1 | 12.83 |
| Red Elm | `red_elm` | ⚪ exploratory | 0.6 | 600 | 490 | 89.7 | 10.28 |
| Red Maple | `red_maple` | ⚪ exploratory | 0.61 | 610 | 505 | 92.4 | 11.31 |
| Red Palm | `red_palm` | ⚪ exploratory | 0.82 | 820 | 873 | 89.4 | 11.41 |
| Red Pine | `red_pine` | ⚪ exploratory | 0.55 | 545 | 410 | 75.9 | 11.24 |
| Redheart | `redheart` | 🟡 emerging | 0.64 | 640 | 552 | 98.7 | 10.32 |
| Redwood (Old Growth) | `redwood` | 🔵 established | 0.41 | 420 | 420 | 60.3 | 8.55 |
| Rengas | `rengas` | ⚪ exploratory | 0.77 | 765 | 767 | 90.3 | 13.2 |
| Rhodesian Teak | `rhodesian_teak` | ⚪ exploratory | 0.89 | 890 | 1015 | 84.3 | 8.48 |
| River Red Gum | `river_red_gum` | ⚪ exploratory | 0.87 | 870 | 974 | 123.8 | 11.8 |
| Rock Elm | `rock_elm` | ⚪ exploratory | 0.76 | 755 | 749 | 102.1 | 10.62 |
| Rock Sheoak | `rock_sheoak` | ⚪ exploratory | 0.89 | 890 | 1015 | 94.0 | 14.0 |
| Rose Gum | `rose_gum` | ⚪ exploratory | 0.64 | 640 | 552 | 107.8 | 14.15 |
| Rose Sheoak | `rose_sheoak` | ⚪ exploratory | 0.94 | 940 | 1123 | 145.0 | 20.0 |
| Rough Barked Apple | `rough_barked_apple` | ⚪ exploratory | 0.86 | 865 | 963 | 110.0 | 11.0 |
| Rowan | `rowan` | ⚪ exploratory | 0.77 | 770 | 777 | 119.3 | 10.28 |
| Rubberwood | `rubberwood` | 🟡 emerging | 0.59 | 595 | 482 | 71.9 | 9.07 |
| Sand Pine | `sand_pine` | ⚪ exploratory | 0.55 | 545 | 410 | 80.0 | 9.72 |
| Sande | `sande` | ⚪ exploratory | 0.56 | 555 | 424 | 94.9 | 14.65 |
| Santos Mahogany | `santos_mahogany` | 🟡 emerging | 0.92 | 915 | 1069 | 148.7 | 16.41 |
| Sapele | `sapele` | 🔵 established | 0.62 | 640 | 1510 | 99.4 | 12.04 |
| Sapodilla | `sapodilla` | ⚪ exploratory | 1.04 | 1040 | 1354 | 184.2 | 20.41 |
| Sassafras | `sassafras` | 🟡 emerging | 0.49 | 495 | 343 | 62.1 | 7.72 |
| Scarlet Oak | `scarlet_oak` | ⚪ exploratory | 0.73 | 735 | 713 | 110.9 | 12.18 |
| Scots Pine | `scots_pine` | ⚪ exploratory | 0.55 | 550 | 417 | 83.3 | 10.08 |
| Serviceberry | `serviceberry` | ⚪ exploratory | 0.83 | 835 | 902 | 116.6 | 12.97 |
| Sessile Oak | `sessile_oak` | ⚪ exploratory | 0.71 | 710 | 668 | 97.1 | 10.47 |
| Shagbark Hickory | `shagbark_hickory` | ⚪ exploratory | 0.8 | 800 | 834 | 139.3 | 14.9 |
| Shellbark Hickory | `shellbark_hickory` | ⚪ exploratory | 0.77 | 770 | 777 | 124.8 | 13.03 |
| Shittim | `shittim` | ⚪ exploratory | 0.66 | 660 | 584 | 98.1 | 10.69 |
| Shortleaf Pine | `shortleaf_pine` | ⚪ exploratory | 0.57 | 570 | 445 | 90.3 | 12.1 |
| Shumard Oak | `shumard_oak` | ⚪ exploratory | 0.73 | 730 | 704 | 123.0 | 14.86 |
| Siam Balsa | `siam_balsa` | ⚪ exploratory | 0.4 | 400 | 231 | 50.6 | 7.17 |
| Siamese Rosewood | `siamese_rosewood` | 🟡 emerging | 1.03 | 1035 | 1342 | 171.0 | 16.38 |
| Silver Birch | `silver_birch` | ⚪ exploratory | 0.64 | 640 | 552 | 114.3 | 13.96 |
| Silver Maple | `silver_maple` | ⚪ exploratory | 0.53 | 530 | 389 | 61.4 | 7.86 |
| Sissoo | `sissoo` | ⚪ exploratory | 0.77 | 770 | 777 | 97.5 | 10.4 |
| Sitka Spruce | `spruce_sitka` | 🟢 primary | 0.42 | 425 | 510 | — | — |
| Slash Pine | `slash_pine` | ⚪ exploratory | 0.66 | 655 | 576 | 112.4 | 13.7 |
| Smooth Barked Apple | `smooth_barked_apple` | ⚪ exploratory | 0.99 | 990 | 1236 | 132.0 | 16.0 |
| Snakewood | `snakewood` | 🟡 emerging | 1.21 | 1210 | 1792 | 195.0 | 23.2 |
| Sneezewood | `sneezewood` | ⚪ exploratory | 1.0 | 1000 | 1260 | 145.5 | 17.7 |
| Soft Maple (Red Maple) | `maple_soft` | 🟢 primary | 0.56 | 610 | 950 | — | — |
| Soto | `soto` | ⚪ exploratory | 1.28 | 1280 | 1989 | 148.7 | 15.69 |
| Sourwood | `sourwood` | ⚪ exploratory | 0.61 | 610 | 505 | 80.0 | 10.62 |
| Southern Magnolia | `southern_magnolia` | ⚪ exploratory | 0.56 | 560 | 431 | 77.2 | 9.66 |
| Southern Red Oak | `southern_red_oak` | ⚪ exploratory | 0.68 | 675 | 609 | 83.0 | 10.2 |
| Southern Redcedar | `southern_redcedar` | ⚪ exploratory | 0.51 | 505 | 356 | 64.8 | 8.07 |
| Southern Silky Oak | `southern_silky_oak` | ⚪ exploratory | 0.59 | 590 | 475 | 74.4 | 7.93 |
| Spanish Cedar | `cedar_spanish` | 🔵 established | 0.43 | 450 | 600 | 78.0 | 9.7 |
| Spotted Gum | `spotted_gum` | ⚪ exploratory | 0.94 | 940 | 1123 | 141.8 | 19.77 |
| Spruce Pine | `spruce_pine` | ⚪ exploratory | 0.53 | 525 | 382 | 71.0 | 9.69 |
| Subalpine Fir | `subalpine_fir` | ⚪ exploratory | 0.53 | 530 | 389 | 58.0 | 9.13 |
| Sucupira | `sucupira` | 🟡 emerging | 0.92 | 920 | 1080 | 162.5 | 18.0 |
| Sugar Pine | `sugar_pine` | ⚪ exploratory | 0.4 | 400 | 231 | 56.6 | 8.21 |
| Sugi | `sugi` | ⚪ exploratory | 0.36 | 360 | 190 | 36.4 | 7.65 |
| Sumac | `sumac` | ⚪ exploratory | 0.53 | 530 | 389 | 70.4 | 8.21 |
| Sumatran Pine | `sumatran_pine` | ⚪ exploratory | 0.71 | 710 | 668 | 96.4 | 14.9 |
| Swamp Ash | `ash_swamp` | 🟢 primary | 0.48 | 500 | 1010 | — | — |
| Swamp Chestnut Oak | `swamp_chestnut_oak` | ⚪ exploratory | 0.78 | 780 | 795 | 94.9 | 12.09 |
| Swamp Mahogany | `swamp_mahogany` | ⚪ exploratory | 0.79 | 785 | 805 | 120.6 | 14.12 |
| Swamp White Oak | `swamp_white_oak` | ⚪ exploratory | 0.77 | 765 | 767 | 120.0 | 13.99 |
| Sweet Birch | `sweet_birch` | ⚪ exploratory | 0.73 | 735 | 713 | 116.6 | 14.97 |
| Sweet Cherry | `sweet_cherry` | ⚪ exploratory | 0.6 | 600 | 490 | 103.3 | 10.55 |
| Sweet Chestnut | `sweet_chestnut` | ⚪ exploratory | 0.59 | 590 | 475 | 71.4 | 8.61 |
| Sweetbay | `sweetbay` | ⚪ exploratory | 0.55 | 545 | 410 | 75.2 | 11.31 |
| Sweetgum | `sweetgum` | ⚪ exploratory | 0.55 | 545 | 410 | 86.2 | 11.31 |
| Sycamore | `sycamore` | ⚪ exploratory | 0.55 | 545 | 410 | 69.0 | 9.79 |
| Sycamore Maple | `sycamore_maple` | ⚪ exploratory | 0.61 | 615 | 512 | 98.1 | 9.92 |
| Table Mountain Pine | `table_mountain_pine` | ⚪ exploratory | 0.57 | 575 | 452 | 80.0 | 10.69 |
| Tamarack | `tamarack` | ⚪ exploratory | 0.59 | 595 | 482 | 80.0 | 11.31 |
| Tamarind | `tamarind` | ⚪ exploratory | 0.85 | 850 | 933 | 111.0 | 13.22 |
| Tambootie | `tambootie` | ⚪ exploratory | 0.95 | 955 | 1157 | 102.7 | 9.08 |
| Tamo Ash | `tamo_ash` | ⚪ exploratory | 0.56 | 560 | 431 | 74.6 | 8.24 |
| Tanoak | `tanoak` | ⚪ exploratory | 0.68 | 675 | 609 | 114.8 | 14.29 |
| Tasmanian Blackwood | `tasmanian_blackwood` | 🔵 established | 0.58 | 640 | 1160 | 96.5 | 11.82 |
| Tasmanian Myrtle | `tasmanian_myrtle` | ⚪ exploratory | 0.62 | 625 | 528 | 98.2 | 12.62 |
| Tatabu | `tatabu` | ⚪ exploratory | 0.93 | 925 | 1090 | 152.2 | 19.82 |
| Tatajuba | `tatajuba` | 🟡 emerging | 0.8 | 800 | 834 | 123.7 | 18.98 |
| Teak | `teak` | 🔵 established | 0.63 | 655 | 1155 | 97.1 | 12.28 |
| Texas Ebony | `texas_ebony` | 🟡 emerging | 0.96 | 965 | 1179 | 152.3 | 16.54 |
| Thuya | `thuya` | ⚪ exploratory | 0.68 | 680 | 617 | 93.8 | 12.41 |
| Tiete Rosewood | `tiete_rosewood` | 🟡 emerging | 0.94 | 945 | 1134 | 109.2 | 14.0 |
| Timborana | `timborana` | ⚪ exploratory | 0.8 | 800 | 834 | 120.0 | 16.41 |
| Tineo | `tineo` | ⚪ exploratory | 0.71 | 710 | 668 | 90.0 | 10.81 |
| Tornillo | `tornillo` | ⚪ exploratory | 0.56 | 555 | 424 | 68.1 | 10.86 |
| Turkey Oak | `turkey_oak` | ⚪ exploratory | 0.72 | 720 | 686 | 114.3 | 10.81 |
| Turpentine | `turpentine` | ⚪ exploratory | 0.94 | 940 | 1123 | 149.0 | 15.5 |
| Utile | `utile` | ⚪ exploratory | 0.64 | 635 | 544 | 103.8 | 11.65 |
| Virginia Pine | `virginia_pine` | ⚪ exploratory | 0.52 | 515 | 369 | 89.7 | 10.48 |
| Waddywood | `waddywood` | ⚪ exploratory | 1.43 | 1430 | 2441 | 150.0 | 21.5 |
| Wamara | `wamara` | ⚪ exploratory | 1.08 | 1080 | 1452 | 196.5 | 24.38 |
| Water Hickory | `water_hickory` | ⚪ exploratory | 0.69 | 690 | 634 | 122.8 | 13.93 |
| Water Oak | `water_oak` | ⚪ exploratory | 0.72 | 725 | 695 | 114.6 | 14.02 |
| Water Tupelo | `water_tupelo` | ⚪ exploratory | 0.55 | 550 | 417 | 66.5 | 8.62 |
| Wenge | `wenge` | 🔵 established | 0.81 | 870 | 1930 | 136.9 | 14.75 |
| West African Albizia | `west_african_albizia` | ⚪ exploratory | 0.6 | 605 | 497 | 82.7 | 10.91 |
| Western Hemlock | `western_hemlock` | ⚪ exploratory | 0.47 | 465 | 306 | 77.9 | 11.24 |
| Western Juniper | `western_juniper` | ⚪ exploratory | 0.44 | 440 | 276 | 61.5 | 4.43 |
| Western Larch | `western_larch` | ⚪ exploratory | 0.57 | 575 | 452 | 89.7 | 12.9 |
| Western Red Cedar | `cedar_western_red` | 🟢 primary | 0.33 | 370 | 350 | 53.1 | 7.78 |
| Western Sheoak | `western_sheoak` | ⚪ exploratory | 0.73 | 730 | 704 | 98.0 | 9.36 |
| Western White Pine | `western_white_pine` | ⚪ exploratory | 0.43 | 435 | 270 | 66.9 | 10.07 |
| White Ash | `ash_white` | 🔵 established | 0.63 | 670 | 1320 | — | — |
| White Fir | `white_fir` | ⚪ exploratory | 0.41 | 415 | 248 | 66.9 | 10.24 |
| White Meranti | `white_meranti` | ⚪ exploratory | 0.59 | 590 | 475 | 80.2 | 10.24 |
| White Oak | `oak_white` | 🔵 established | 0.72 | 770 | 1360 | 144.7 | 15.26 |
| White Poplar | `white_poplar` | ⚪ exploratory | 0.44 | 440 | 276 | 65.0 | 8.9 |
| White Spruce | `spruce_white` | 🔵 established | 0.4 | 410 | 480 | 65.5 | 9.7 |
| White Willow | `white_willow` | ⚪ exploratory | 0.4 | 400 | 231 | 56.2 | 7.76 |
| Willow Leaf Red Quebracho | `willow_leaf_red_quebracho` | ⚪ exploratory | 1.21 | 1210 | 1792 | 126.5 | 15.12 |
| Willow Oak | `willow_oak` | ⚪ exploratory | 0.77 | 770 | 777 | 102.4 | 12.44 |
| Winged Elm | `winged_elm` | ⚪ exploratory | 0.68 | 675 | 609 | 102.1 | 11.38 |
| Wych Elm | `wych_elm` | ⚪ exploratory | 0.6 | 605 | 497 | 98.2 | 11.14 |
| Yellow Birch | `birch_yellow` | 🔵 established | 0.66 | 690 | 1260 | — | — |
| Yellow Box | `yellow_box` | ⚪ exploratory | 1.07 | 1075 | 1440 | 122.0 | 14.0 |
| Yellow Buckeye | `yellow_buckeye` | ⚪ exploratory | 0.4 | 400 | 231 | 51.7 | 8.07 |
| Yellow Gum | `yellow_gum` | ⚪ exploratory | 1.01 | 1010 | 1283 | 111.0 | 12.0 |
| Yellow Lapacho | `yellow_lapacho` | ⚪ exploratory | 1.1 | 1100 | 1502 | 162.6 | 15.53 |
| Yellow Meranti | `yellow_meranti` | ⚪ exploratory | 0.56 | 565 | 438 | 80.8 | 10.68 |
| Yellow Poplar (Tulipwood) | `poplar_yellow` | 🔵 established | 0.46 | 450 | 540 | — | — |
| Yellow Silverballi | `yellow_silverballi` | ⚪ exploratory | 0.61 | 610 | 505 | 67.0 | 9.1 |
| Yellowheart | `yellowheart` | 🟡 emerging | 0.82 | 825 | 882 | 115.9 | 16.64 |
| Yucatan Rosewood | `yucatan_rosewood` | 🟡 emerging | 0.68 | 680 | 617 | 70.1 | 7.76 |
| Zebrawood | `zebrawood` | 🔵 established | 0.75 | 785 | 1575 | 124.1 | 13.88 |
| Ziricote | `ziricote` | 🔵 established | 0.79 | 815 | 1900 | — | — |

---

*Generated from `wood_species.json` v4.0.0. See [SOURCES.md](SOURCES.md) for full data provenance and estimation methodology.*