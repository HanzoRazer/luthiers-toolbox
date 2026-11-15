# Tonewood Comparison: Acoustic Guitar Top Woods

> **Source:** `wood_species.json` v4.0.0 + `luthier_tonewood_reference.json` v1.0.0. **Corrected 2026-11-15 (C-11):** specific gravity, density, Janka, shrinkage, MOE, MOR, E/ρ, sound speed and impedance now come from FPL GTR-282 (2021) — see [FPL values](#fpl-values) below. Machining and tone rows are unchanged and unsourced.
> **Generated:** 2026-04-09

> **ᵉ Estimated Janka (added 2026-11-14).** Values marked ᵉ equal the bulk-import regression `Janka ≈ 0.00355 × density^1.85` (`scripts/bulk_import_wood_species.py`), not a hardness test. They rise smoothly with density, so they cannot rank species of similar density, and they can be far below published measurements for the hardest woods. Treat them as placeholders. See `VERIFICATION_LOG.md` (C-02).

This comparison covers the primary and alternative soundboard woods for acoustic guitars: three spruces (Sitka, Adirondack, Engelmann), two cedars (Western Red, Alaskan Yellow), redwood, and three unconventional top choices (mahogany, maple, Douglas-fir).

---

## At a Glance

| Species | Relevance | Density at 12% MC (kg/m³) | Janka (lbf) | Tone Character | Sustainability |
|---------|:---------:|:---:|:---:|----------------|----------------|
| **Sitka Spruce** | Primary | 448 | 517 | Versatile, strong fundamental | Sustainable |
| **Adirondack Spruce** | Primary | 448 | 495 | Powerful, headroom, loud — the pre-war dreadnought tonewood | Limited supply — slow-growing |
| **Engelmann Spruce** | Primary | 392 | 393 | Warm, responsive, lower overtones than Sitka | Sustainable |
| **Western Red Cedar** | Primary | 358 | 360 | Warm, dark, immediate response | Sustainable |
| **Alaskan Yellow Cedar** | Exploratory | 493 | 585 | *(not yet characterized)* | *(not yet characterized)* |
| **Redwood (Old Growth)** | Established | 448 | 472 | Warm, dark, cedar-like response | Old growth restricted — salvage only |
| **Honduran Mahogany** | Primary | 529 | 809 | Warm, balanced, good sustain | CITES Appendix II |
| **Hard Maple** | Primary | 706 | 1,439 | Bright, articulate, snappy | Sustainable |
| **Douglas-Fir** | Established | 538 | 719 | Strong, clear, good for steel-string | Sustainable, abundant |

---

## Physical Properties

| Property | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Scientific Name** | *Picea sitchensis* | *Picea rubens* | *Picea engelmannii* | *Thuja plicata* | *Cupressus nootkatensis* | *Sequoia sempervirens* | *Swietenia macrophylla* | *Acer saccharum* | *Pseudotsuga menziesii* |
| **Specific Gravity (G₁₂)** | 0.40 | 0.40 | 0.35 | 0.32 | 0.44 | 0.40 | 0.47 | 0.63 | 0.48 |
| **Density at 12% MC (kg/m³)** | 448 | 448 | 392 | 358 | 493 | 448 | 529 | 706 | 538 |
| **Janka Hardness (lbf)** | 517 | 495 | 393 | 360 | 585 | 472 | 809 | 1,439 | 719 |
| **Janka Hardness (N)** | 2,300 | 2,200 | 1,750 | 1,600 | 2,600 | 2,100 | 3,600 | 6,400 | 3,200 |
| **Grain** | Straight, tight | Straight, tight | Straight, fine | Straight | — | Straight, fine | Interlocked | Straight to figured | Straight, pronounced rings |
| **Workability** | Good — soft | Good | Good — very soft | Excellent — very soft | — | Excellent | Excellent | Moderate — hard on tools | Good |
| **Resinous** | Yes | Yes | Yes | Yes | Yes | No | No | No | Yes |
| **Shrinkage Radial, green→ovendry (%)** | 4.3 | 3.8 | 3.8 | 2.4 | 2.8 | 2.6 | 3.0 | 4.8 | 4.8 |
| **Shrinkage Tangential, green→ovendry (%)** | 7.5 | 7.8 | 7.1 | 5.0 | 6.0 | 4.4 | 4.1 | 9.9 | 7.6 |
| **Shrinkage Volumetric, green→ovendry (%)** | 11.5 | 11.8 | 11.0 | 6.8 | 9.2 | 6.8 | 7.8 | 14.7 | 12.4 |

---

## Acoustic & Structural Properties

| Property | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Modulus of Elasticity, 12% MC (GPa)** | 10.8 | 11.4 | 8.9 | 7.7 | 9.8 | 9.2 | 10.3 | 12.6 | 13.4 |
| **Modulus of Rupture, 12% MC (MPa)** | 70.0 | 74.0 | 64.0 | 51.7 | 77.0 | 69.0 | 79.3 | 109.0 | 85.0 |
| **E/ρ Ratio (stiffness-to-weight)** | 24.1 | 25.4 | 22.7 | 21.5 | 19.9 | 20.5 | 19.5 | 17.9 | 24.9 |
| **Speed of Sound (m/s)** † | 4,910 | 5,044 | 4,765 | 4,635 | 4,459 | 4,532 | 4,414 | 4,226 | 4,993 |
| **Acoustic Impedance (10⁶ kg/m²s)** † | 2.20 | 2.26 | 1.87 | 1.66 | 2.20 | 2.03 | 2.33 | 2.98 | 2.68 |
| **Tone Character** | Versatile, strong fundamental | Powerful, headroom, loud | Warm, responsive, lower overtones | Warm, dark, immediate response | — | Warm, dark, cedar-like | Warm, balanced, sustain | Bright, articulate, snappy | Strong, clear |

> † Computed, not measured: c = √(E/ρ), Z = ρ × c, from the FPL MOE and density at 12% MC. No value is estimated from a similar species any more (the earlier Sitka and Engelmann figures were, and Engelmann's 5,090 m/s was overstated). FPL's MOE is from a center-loaded beam and is not shear-corrected; FPL notes it "can be increased by 10%", which would raise c by about 5%. The ranking is unaffected.

---

## Thermal Properties

| Property | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Thermal Conductivity (W/m·K)** | 0.12 | 0.19 | 0.11 | 0.10 | 0.21 | 0.12 | 0.12 | 0.18 | 0.14 |
| **Specific Heat Capacity (J/kg·K)** | 1,800 | 1,742 | 1,800 | 1,850 | 1,706 | 1,800 | 1,600 | 1,650 | 1,750 |
| **Specific Cutting Energy (J/mm³)** | 0.28 | 0.43 | 0.25 | 0.22 | 0.47 | 0.28 | 0.45 | 0.55 | 0.32 |
| **Heat Partition — Chip** | 0.73 | 0.69 | 0.74 | 0.75 | 0.68 | 0.73 | 0.70 | 0.70 | 0.72 |
| **Heat Partition — Tool** | 0.17 | 0.19 | 0.16 | 0.15 | 0.20 | 0.17 | 0.20 | 0.20 | 0.18 |
| **Heat Partition — Work** | 0.10 | 0.12 | 0.10 | 0.10 | 0.12 | 0.10 | 0.10 | 0.10 | 0.10 |

---

## CNC Machining

| Property | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Hardness Scale** | 0.20 | 0.16 | 0.15 | 0.10 | 0.10 | 0.18 | 0.40 | 0.70 | 0.30 |
| **Burn Tendency** | 0.20 | 0.15 | 0.15 | 0.10 | 0.15 | 0.10 | 0.30 | 0.60 | 0.30 |
| **Tearout Tendency** | 0.60 | 0.50 | 0.65 | 0.50 | 0.23 | 0.30 | 0.50 | 0.30 | 0.40 |
| **Chipload Multiplier** | 1.15 | 1.17 | 1.20 | 1.30 | 1.22 | 1.25 | 1.00 | 0.85 | 1.10 |
| **Roughing Feed Max (mm/min)** | 4,500 | 5,200 | 5,000 | 5,500 | 5,500 | 5,000 | 4,000 | 3,000 | 4,500 |
| **Finishing Feed Max (mm/min)** | 2,800 | 3,020 | 3,000 | 3,200 | 3,200 | 3,000 | 2,500 | 2,000 | 2,800 |
| **Plunge Feed Max (mm/min)** | 1,200 | 1,712 | 1,400 | 1,800 | 1,820 | 1,500 | 1,000 | 600 | 1,200 |
| **Min RPM** | 12,000 | 11,280 | 10,000 | 10,000 | 10,800 | 10,000 | 12,000 | 14,000 | 12,000 |
| **Max RPM** | 24,000 | 24,000 | 24,000 | 22,000 | 24,000 | 24,000 | 24,000 | 24,000 | 24,000 |
| **Optimal SFM** | 900 | 1,056 | 950 | 1,100 | 1,110 | 1,000 | 800 | 700 | 900 |
| **Max DOC (mm)** | 10 | 15 | 12 | 15 | 16 | 14 | 12 | 8 | 12 |
| **Optimal DOC Ratio** | 0.50 | 0.61 | 0.55 | 0.65 | 0.64 | 0.60 | 0.50 | 0.35 | 0.50 |
| **Max WOC Ratio** | 0.50 | 0.62 | 0.55 | 0.65 | 0.65 | 0.60 | 0.50 | 0.40 | 0.50 |
| **Finishing WOC Ratio** | 0.10 | 0.17 | 0.12 | 0.18 | 0.18 | 0.15 | 0.10 | 0.08 | 0.12 |

### Machining Warnings

| Risk | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Burn Risk** | Low | Low | Low | Low | Low | Low | Low | High | Low |
| **Tearout Risk** | High | Medium | High | Medium | Low | Low | Medium | Low | Medium |
| **Dust Hazard** | Low | Low | Low | Medium | Low | Low | Medium | Low | Low |

| Species | Notes |
|---------|-------|
| **Sitka Spruce** | Softwood tears easily across grain. Sharp tools essential. |
| **Adirondack Spruce** | Stiffest North American spruce. Premium soundboard wood. |
| **Engelmann Spruce** | Softer than Sitka. Preferred for fingerstyle guitars. Very fragile — light cuts only. |
| **Western Red Cedar** | Aromatic dust can be irritating. Very soft — light clamping pressure. |
| **Alaskan Yellow Cedar** | *(No detailed notes in database)* |
| **Redwood** | Soft, stable, beautiful. Old growth salvage only. |
| **Honduran Mahogany** | Watch for tearout on interlocked grain areas. |
| **Hard Maple** | Very prone to burning. Keep sharp tools, adequate feed rate. |
| **Douglas-Fir** | Resinous — gums up tooling. Clean cutters frequently. |

---

## Lutherie Profile

| Property | Sitka Spruce | Adirondack Spruce | Engelmann Spruce | W. Red Cedar | Yellow Cedar | Redwood | Mahogany | Hard Maple | Douglas-Fir |
|----------|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **Guitar Relevance** | Primary | Primary | Primary | Primary | Exploratory | Established | Primary | Primary | Established |
| **Typical Uses** | Soundboard | Soundboard | Soundboard | Soundboard | — | Soundboard, body | Body, neck, back/sides | Neck, top, fretboard | Soundboard, bracing |
| **Sustainability** | Sustainable | Limited supply | Sustainable | Sustainable | — | Old growth restricted | CITES Appendix II | Sustainable | Sustainable, abundant |

---

## Analysis

### The Spruce Family: Industry Standards

The three spruces represent the core of acoustic guitar soundboard selection, each with distinct characteristics:

**Sitka Spruce** is the industry workhorse — the most widely used soundboard wood in modern production. Its density (448 kg/m³) and stiffness (MOE 10.8 GPa) place it between Engelmann and Adirondack, delivering a versatile tone with strong fundamental response. It handles both fingerstyle and flatpicking well, making it the safest default choice. Abundant and sustainable from Pacific Northwest forests.

**Adirondack Spruce** (Red Spruce) is the premium choice — the "pre-war dreadnought tonewood" that powered the golden age Martin guitars. At MOE 11.4 GPa it is the stiffest spruce in FPL's tables, at the same specific gravity as Sitka (0.40, 448 kg/m³) — so it is stiffer, not heavier, delivering more headroom and volume before compression. The tradeoff: limited supply from slow-growing Appalachian forests means higher cost and less consistency in selection.

**Engelmann Spruce** is the lightest and softest spruce in this comparison (392 kg/m³, Janka 393, MOE 8.9 GPa). This translates to a warmer, more responsive sound with lower overtones — the fingerstyle player's spruce. Its fragility demands light cuts during machining (tearout tendency 0.65, the highest in this group). Sustainable supply from Rocky Mountain forests.

### The Cedar Family: Warmth and Immediacy

**Western Red Cedar** is the primary alternative to spruce, offering a fundamentally different tonal character. At 358 kg/m³ and MOE 7.7 GPa, it's the lightest and least stiff top wood in this comparison. The result: warm, dark tone with immediate response — the soundboard speaks quickly without the "breaking in" period that spruce often requires. Classical and fingerstyle builders favor cedar for its responsiveness at lighter touch. Very soft (Janka 360) — use light clamping pressure and sharp tools.

**Alaskan Yellow Cedar** (*Cupressus nootkatensis*) is an exploratory species that deserves more attention. Despite the name, it's not a true cedar but a cypress. At 493 kg/m³, it's significantly denser than Western Red Cedar — closer to Douglas-fir territory. Its MOE (9.8 GPa) is above Western Red Cedar and Engelmann but below Sitka and Adirondack, and it is harder than any spruce here (Janka 585; the earlier 343 was a density-regression estimate). The database lacks tone characterization, but the physical properties suggest a voice between cedar's warmth and spruce's clarity. Low tearout tendency (0.23) makes it machine-friendly. Supply is limited; climate change is affecting northern stands.

### Redwood: The Cedar Cousin

**Redwood** (Old Growth) is tonally similar to Western Red Cedar — "warm, dark, cedar-like response" — but with slightly different physical properties. At 448 kg/m³ (the same as Sitka) and MOE 9.2 GPa, it is as dense as Sitka but less stiff — between cedar and the spruces in stiffness. The non-resinous nature (unlike the spruces and cedars) simplifies finishing. The critical constraint is availability: new-growth redwood lacks the tight grain structure of old-growth; salvage and reclaimed sources are the only responsible options for instrument-grade stock.

### The Outliers: Mahogany, Maple, and Douglas-Fir

These three species are not traditional soundboard woods but see use in specific applications:

**Honduran Mahogany** as a soundboard is unconventional but has a devoted following. At 529 kg/m³, it's about 18% denser than Sitka spruce — the resulting top is warmer, with less treble sparkle and more mid-focused tone. Mahogany-top guitars (like the Martin 00-15M) have a distinctly "woody" voice. Its MOE (10.3 GPa) is slightly below Sitka's, so it is not stiffer than spruce, only heavier (the earlier 11.97 GPa was unsourced). CITES Appendix II listing affects availability.

**Hard Maple** as a top wood appears primarily on archtop jazz guitars and some solid-body electrics. At 706 kg/m³ and Janka 1,439, it's by far the heaviest and hardest species in this comparison. Its MOE (12.6 GPa) is high, but so is its density: it has the lowest E/ρ (17.9) and the highest acoustic impedance (2.98) here, which go with a bright, articulate, snappy tone with strong attack. CNC machining requires caution: burn tendency 0.60 is the highest in this group — keep feeds up and tools sharp.

**Douglas-Fir** is an established but underrated top wood, favored by some builders for steel-string flattops. At 538 kg/m³ and MOE 13.4 GPa, it is the stiffest species in this comparison and about as dense as mahogany. Its E/ρ (24.9) is second only to Adirondack — the earlier "lowest ratio" came from an unsourced MOE of 10.0 GPa. The pronounced growth rings create visual distinction. Tone is described as "strong, clear, good for steel-string" — more headroom than cedar, warmer than maple. Abundant and sustainable supply from Pacific Northwest forests.

### Stiffness-to-Weight: The Key Soundboard Metric

For soundboard selection, the stiffness-to-weight ratio (E/ρ) is more relevant than MOE alone — a top must be both stiff enough to resist string tension and light enough to vibrate freely.

| Species | E/ρ Ratio | Interpretation |
|---------|:---------:|----------------|
| **Adirondack Spruce** | 25.4 | Highest — maximum headroom per gram |
| **Douglas-Fir** | 24.9 | Second — stiffest wood here, at a softwood density |
| **Sitka Spruce** | 24.1 | High — the reference soundboard |
| **Engelmann Spruce** | 22.7 | Below the other spruces — lower MOE |
| **Western Red Cedar** | 21.5 | Good ratio despite low absolute MOE |
| **Redwood** | 20.5 | Cedar-like efficiency |
| **Alaskan Yellow Cedar** | 19.9 | Lower — denser cedar |
| **Honduran Mahogany** | 19.5 | Low — heavier than spruce for less stiffness |
| **Hard Maple** | 17.9 | Lowest — dense |

E/ρ is MOE (GPa) divided by density at 12% MC (g/cm³), both from FPL GTR-282. The spruces and Douglas-fir lead; the cedars and redwood sit in the middle. Mahogany (19.5) is second-lowest, so E/ρ does **not** explain why mahogany tops work — they are a voicing choice (a darker, mid-focused top), not an efficiency one. (Corrected 2026-11-15: the earlier table had no Sitka or Engelmann values, ranked Douglas-fir last and mahogany second, all from unsourced MOE values.)

### Player-Centric Selection Guide

| Player Style | Recommended Top | Why |
|--------------|-----------------|-----|
| **Flatpicking, bluegrass** | Adirondack Spruce | Maximum headroom, loud projection |
| **Strumming, all-around** | Sitka Spruce | Versatile, handles everything |
| **Fingerstyle, light touch** | Engelmann Spruce or Cedar | Immediate response, warm tone |
| **Classical, nylon-string** | Western Red Cedar | Dark warmth, traditional voice |
| **Blues, slide** | Mahogany | Mid-focused, woody character |
| **Jazz archtop** | Hard Maple | Bright, articulate, punchy |
| **Budget/experimental** | Douglas-Fir | Underrated, abundant, clear |

---

## Data Gaps to Address

| Species | Missing Data |
|---------|-------------|
| **Alaskan Yellow Cedar** | Grain description, workability, tone character, typical uses, sustainability |
| **All species** | Speed of sound, acoustic impedance (computed, not measured) |

The Sitka and Engelmann MOE, MOR and shrinkage gaps are filled from FPL GTR-282 (2026-11-15). Those values are still missing from `wood_species.json`, which this document no longer reads them from.

---

<a id="fpl-values"></a>
## FPL values: sources and derivations

Added 2026-11-15 (C-11). Every value comes from `docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv` (FPL GTR-282, 2021). Mechanical values are at 12% moisture content.

| Species | FPL mechanical row | FPL shrinkage row |
|---|---|---|
| Sitka Spruce | 5-3a Spruce, Sitka | 4-3 Spruce, Sitka |
| Adirondack Spruce | 5-3a Spruce, Red | 4-3 Spruce, Red |
| Engelmann Spruce | 5-3a Spruce, Engelmann | 4-3 Spruce, Engelmann |
| Western Red Cedar | 5-3a Cedar, Western redcedar | 4-3 Cedar, Western redcedar |
| Alaskan Yellow Cedar | 5-3a Cedar, Yellow | 4-3 Cedar, Yellow |
| Redwood | 5-3a Redwood, Old-growth | 4-3 Redwood, Old growth |
| Honduran Mahogany | 5-5a Mahogany, true (*Swietenia macrophylla*) | 4-4 Mahogany, true |
| Hard Maple | 5-3a Maple, Sugar | 4-3 Maple, Sugar |
| Douglas-Fir | 5-3a Douglas-fir, Coast | 4-3 Douglas-fir, Coast |

- **Janka** is FPL's side hardness at 12% MC, converted at 1 lbf = 4.448 N.
- **Density at 12% MC** is FPL Eq. 4-14, ρ₁₂ = 1000 × G₁₂ × 1.12, with G₁₂ from Table 5-3a. Table 5-5a gives mahogany only basic specific gravity (G_b = 0.45), so its G₁₂ = 0.472 comes from FPL Eqs. 4-9 and 4-11 (S₁₂ = 7.8 × (1 − 12/30), MC_fs = 30%).
- **Shrinkage** is green to ovendry. The earlier "Contraction" rows (e.g. Western Red Cedar 4.43/7.69, against FPL's 2.4/5.0) had no source and were replaced.
- **MOE** in FPL comes from small clear specimens, which are stiffer than typical guitar stock with runout. Use these values to compare species, not to predict one board.

---

## Key Takeaways

1. **Sitka Spruce is the safe default** — versatile, available, sustainable, well-documented.

2. **Adirondack is the premium upgrade** — more headroom and volume, but limited supply and higher cost.

3. **Engelmann and Cedar are the fingerstyle choices** — lighter, warmer, more responsive at low volumes.

4. **Alaskan Yellow Cedar is worth investigating** — denser than Western Red, lower tearout, unexplored tonal territory.

5. **Mahogany tops are a voicing choice** — E/ρ is second-lowest here (19.5), so expect a warmer, mid-focused voice, not more efficiency.

6. **Douglas-Fir is underrated** — stiffest wood here with the second-highest E/ρ (24.9); abundant, sustainable, clear tone; consider for production instruments.

7. **Hard Maple is for archtops** — too heavy and bright for flattops, but perfect for carved-top jazz guitars.
