# Tonewood Comparison: Cherry · Mahogany · Black Walnut · Honey Mesquite · American Sycamore

> **Source:** `wood_species.json` v4.0.0 (472 species) + `luthier_tonewood_reference.json` v1.0.0
> **Generated:** 2026-03-10

> **FPL GTR-282 values (corrected 2026-11-15, `VERIFICATION_LOG.md` C-11).** For species that FPL GTR-282 (2021) covers, density (at 12% MC), specific gravity (G₁₂), Janka, MOE, MOR and shrinkage in the tables are now FPL values, and sound speed, impedance and E/ρ are recomputed from them. `scripts/check_tonewood_fpl_values.py` lists the species mapped and checks every such cell. Values for other species are unchanged and mostly unsourced.

---

## Physical Properties

| Property | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Scientific Name** | *Prunus serotina* | *Swietenia macrophylla* | *Juglans nigra* | *Prosopis glandulosa* | *Platanus occidentalis* |
| **Specific Gravity** | 0.50 | 0.47 | 0.55 | 0.86 | 0.49 |
| **Density (kg/m³)** | 560 | 529 | 616 | 950 | 549 |
| **Janka Hardness (lbf)** | 944 | 809 | 1,012 | 2,345 | 764 |
| **Janka Hardness (N)** | 4,200 | 3,600 | 4,500 | 10,431 | 3,400 |
| **Grain** | Straight, fine | Interlocked | Straight to figured | Interlocked, wildly figured | Interlocked, lace-like ray fleck on quartersawn |
| **Workability** | Excellent | Excellent | Excellent | Difficult — very hard, dulls cutters | Good — tears on interlocked grain, clean on quartersawn |
| **Resinous** | No | No | No | No | No |
| **Contraction Radial (%)** | 3.7 | 3.0 | 5.5 | — | 5.0 |
| **Contraction Tangential (%)** | 7.1 | 4.1 | 7.8 | — | 8.4 |

---

## Acoustic & Structural Properties

| Property | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Speed of Sound (m/s)** | 4,289 | 4,414 | 4,339 | 3,491 | 4,226 † |
| **Acoustic Impedance (10⁶ kg/m²s)** | 2.40 | 2.33 | 2.67 | 3.32 | 2.32 † |
| **Modulus of Elasticity (GPa)** | 10.3 | 10.3 | 11.6 | 11.58 | 9.8 |
| **Modulus of Rupture (MPa)** | 85.0 | 79.3 | 101.0 | 117.0 | 69.0 |
| **Tone Character** | Warm, sweet mids — similar to mahogany | Warm, balanced, good sustain | Warm, rich mids, mahogany-like | Bright, crystalline highs, strong sustain — rosewood-like but more percussive | Warm, open, airy — light body with pronounced mids, low damping |

> † American Sycamore speed of sound and acoustic impedance computed from MOE and density: c = √(E/ρ) = √(9.8×10⁹ / 549) ≈ 4,226 m/s; Z = ρ × c = 549 × 4,226 ≈ 2.32 × 10⁶ kg/m²s.
>
> **Corrected 2026-11-15 (C-11):** density, Janka, shrinkage, MOE and MOR for cherry, mahogany, walnut and sycamore are now FPL GTR-282 values (Tables 4-3, 4-4, 5-3a, 5-5a; density at 12% MC by FPL Eq. 4-14); speed of sound and impedance are recomputed from them. Honey mesquite is not in FPL and is unchanged.

---

## Thermal Properties

| Property | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Thermal Conductivity (W/m·K)** | 0.15 | 0.12 | 0.14 | 0.37 | 0.23 |
| **Specific Heat Capacity (J/kg·K)** | 1,700 | 1,600 | 1,700 | 1,450 | 1,670 |
| **Specific Cutting Energy (J/mm³)** | 0.45 | 0.45 | 0.45 | 0.78 | 0.51 |
| **Heat Partition — Chip** | 0.70 | 0.70 | 0.70 | 0.60 | 0.67 |
| **Heat Partition — Tool** | 0.20 | 0.20 | 0.20 | 0.25 | 0.21 |
| **Heat Partition — Work** | 0.10 | 0.10 | 0.10 | 0.15 | 0.13 |

---

## CNC Machining

| Property | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|----------|:---:|:---:|:---:|:---:|:---:|
| **Hardness Scale** | 0.45 | 0.40 | 0.50 | 0.70 | 0.12 |
| **Burn Tendency** | 0.50 | 0.30 | 0.25 | 0.45 | 0.16 |
| **Tearout Tendency** | 0.20 | 0.50 | 0.25 | 0.55 | 0.24 |
| **Chipload Multiplier** | 1.0 | 1.0 | 1.0 | 0.80 | 1.20 |
| **Roughing Feed Max (mm/min)** | 4,000 | 4,000 | 4,000 | 2,800 | 5,400 |
| **Finishing Feed Max (mm/min)** | 2,500 | 2,500 | 2,500 | 1,800 | 3,140 |
| **Plunge Feed Max (mm/min)** | 1,000 | 1,000 | 1,000 | 700 | 1,784 |
| **Min RPM** | 12,000 | 12,000 | 12,000 | 16,000 | 10,960 |
| **Max RPM** | 24,000 | 24,000 | 24,000 | 24,000 | 24,000 |
| **Optimal SFM** | 800 | 800 | 800 | 650 | 1,092 |
| **Max DOC (mm)** | 12 | 12 | 12 | 8 | 16 |
| **Optimal DOC Ratio** | 0.50 | 0.50 | 0.50 | 0.40 | 0.63 |
| **Max WOC Ratio** | 0.50 | 0.50 | 0.50 | 0.40 | 0.64 |
| **Finishing WOC Ratio** | 0.10 | 0.10 | 0.10 | 0.10 | 0.18 |

### Machining Warnings

| Risk | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|------|:---:|:---:|:---:|:---:|:---:|
| **Burn Risk** | Medium | Low | Low | High | Low |
| **Tearout Risk** | Low | Medium | Low | High | Low |
| **Dust Hazard** | Low | Medium | Medium | High | Low |

| Species | Notes |
|---------|-------|
| **Black Cherry** | Burns easily with dull tools. Beautiful darkening patina. |
| **Honduran Mahogany** | Watch for tearout on interlocked grain areas. |
| **American Black Walnut** | Excellent machining properties. Similar to mahogany. |
| **Honey Mesquite** | Extremely hard — dulls HSS quickly, use carbide. Interlocked grain tears easily on figured stock. Dust is irritating. Small blanks common due to tree form. |
| **American Sycamore** | Soft and forgiving on tooling. Interlocked grain can tear on flatsawn faces — quartersawn stock machines cleanly and reveals distinctive lace-like ray fleck figure. Low dust hazard. |

---

## Lutherie Profile

| Property | Black Cherry | Honduran Mahogany | American Black Walnut | Honey Mesquite | American Sycamore |
|----------|:---|:---|:---|:---|:---|
| **Guitar Relevance** | Established | Primary | Primary | Emerging | Exploratory |
| **Typical Uses** | Body, back/sides | Body, neck, back/sides | Body, back/sides | Body, body top, fretboard, bridge, accent | Body, back/sides, soundboard (experimental) |
| **Sustainability** | Sustainable | CITES Appendix II | Sustainable | Abundant — invasive species, harvest is ecologically beneficial | Abundant — common eastern US bottomland tree, no harvest restrictions |

---

## Analysis

### The Warm-Mid Cluster: Cherry, Mahogany, Walnut

Cherry, mahogany, and walnut form a tonal cluster — all three sit in the "warm, mid-focused" zone with similar density (529–616 kg/m³), acoustic impedance (2.33–2.67), and MOE (10.3–11.6 GPa). They share excellent workability and standard CNC parameters.

- **Honduran Mahogany** is the benchmark tonewood of the group. It has the highest speed of sound (4,414 m/s) because it is the lightest, not the stiffest: walnut (11.6 GPa) and mesquite (11.58) have a higher MOE than mahogany (10.3), and its MOR (79.3 MPa) is the second-lowest here (corrected 2026-11-14 and 2026-11-15, see `VERIFICATION_LOG.md`). The classic Les Paul body wood. CITES-listed — availability is tightening and pricing reflects it.
- **American Black Walnut** is the closest mahogany substitute by the numbers. Denser (616 vs 529 kg/m³), harder (1,012 vs 809 lbf) and stiffer, with a slightly richer mid emphasis. Best overall machining profile of the five (lowest combined burn + tearout tendency). Domestically abundant and sustainable.
- **Black Cherry** leans sweeter than the other two. Its strength (MOR 85 MPa) sits between mahogany (79.3) and walnut (101), and it is harder than mahogany (944 vs 809 lbf). Burn-prone with dull tooling but tearout risk is minimal thanks to its fine, straight grain. The darkening patina is a finish consideration.

### The Outlier: Honey Mesquite

At 950 kg/m³ and Janka 2,345 lbf, mesquite is nearly twice as dense as the warm-mid cluster — closer to rosewood territory. It produces a distinctly brighter, more percussive voice with the highest acoustic impedance (3.32) and lowest speed of sound (3,491 m/s) of the group. The high density concentrates energy differently: more percussive attack, crystalline highs, and strong sustain.

CNC-wise, mesquite demands respect: carbide tooling only, reduced chipload (0.80× multiplier), shallower cuts (8mm vs 12mm max DOC), lower feeds across the board, and higher minimum RPM (16,000). Specific cutting energy is 73% higher than the other three (0.78 vs 0.45 J/mm³), meaning more heat generation — the heat partition shifts toward tool and workpiece.

The tradeoff: stunning wildly figured grain, a brilliant and unique tonal fingerprint, and it's an invasive species in the American Southwest — guilt-free harvesting with ecological benefit.

### The Lightweight Candidate: American Sycamore

American Sycamore (*Platanus occidentalis*) enters this comparison as an exploratory species — currently uncharacterized for lutherie in the tonewood reference but with physical properties that warrant investigation.

At 549 kg/m³ and Janka 764 lbf, sycamore is the softest wood in this comparison and close to mahogany in both density (549 vs 529) and hardness (764 vs 809). (The earlier "Janka 410 — roughly half the hardness" was wrong; FPL measures 764 lbf.) The computed speed of sound (4,226 m/s) and acoustic impedance (2.32) place it just below cherry in the warm-mid cluster, suggesting a similar tonal family: warm, open, and airy with pronounced mids.

The low MOE (9.8 GPa) and MOR (69.0 MPa) — the weakest structural numbers in this set — indicate a flexible, resonant body that would favor fundamental emphasis over overtone complexity. This profile is characteristic of soundboard-weight tonewoods rather than back/side stock, though the density is appropriate for either role in steel-string acoustic construction.

The quartersawn face is where sycamore becomes visually distinctive: prominent medullary rays produce a lace-like fleck pattern unique among North American hardwoods. This figure is often compared to European plane (*Platanus acerifolia*), which has a long history in European instrument making.

CNC-wise, sycamore is the easiest species in this comparison to machine: lowest hardness scale (0.12), lowest burn tendency (0.16), highest chipload multiplier (1.20), and the fastest permissible feed rates across the board (5,400 mm/min roughing). The only concern is tearout on flatsawn faces due to interlocked grain — quartersawn orientation eliminates this.

**Data gaps:** Tone character, acoustic properties, and sustainability status are unpopulated in the wood database. Speed of sound and acoustic impedance shown here are computed from MOE/density, not measured. Tap-tone testing of sycamore body blanks would provide measured acoustic data to validate or correct these estimates.

**Verdict:** A promising exploratory candidate for back/sides or experimental soundboard use in the cherry/mahogany weight class. The extremely easy machinability, distinctive quartersawn figure, and domestic abundance make it worth prototyping. Needs measured acoustic data before any tone character claims can be made with confidence.
