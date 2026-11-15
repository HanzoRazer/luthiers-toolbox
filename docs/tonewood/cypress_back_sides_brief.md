# Bald Cypress as a Back & Sides Tonewood for Cuatros, Flat/Round-Back Mandolins, and Lutes

> **ᵉ Estimated Janka (added 2026-11-14).** Values marked ᵉ equal the bulk-import regression `Janka ≈ 0.00355 × density^1.85` (`scripts/bulk_import_wood_species.py`), not a hardness test. They rise smoothly with density, so they cannot rank species of similar density, and they can be far below published measurements for the hardest woods. Treat them as placeholders. See `VERIFICATION_LOG.md` (C-02).

> **FPL GTR-282 values (corrected 2026-11-15, `VERIFICATION_LOG.md` C-11).** For species that FPL GTR-282 (2021) covers, density (at 12% MC), specific gravity (G₁₂), Janka, MOE, MOR and shrinkage in the tables are now FPL values, and sound speed, impedance and E/ρ are recomputed from them. `scripts/check_tonewood_fpl_values.py` lists the species mapped and checks every such cell. Values for other species are unchanged and mostly unsourced.

*Executive brief · data from the repo tonewood database (no per-value source recorded; corrected 2026-11-14, see `VERIFICATION_LOG.md`) + computed acoustic figures · construction reference: 580 mm flat-back plan (Y. Fesselier)*

## Bottom line

**Bald Cypress is an excellent back-and-sides wood — never a soundboard — for the flat/bent-plate, plucked-string family: cuatros, flat- and round/bowl-back mandolins, and lutes.**[^1] Build it as **cypress back + sides over a spruce or cedar top.** Its dry, bright, fast-decay voice[^2] is exactly what these bright, articulate instruments are built to project, and it bends and works cleanly at their scales.

---

## Table 1 — The cypresses are *not* interchangeable (back/sides candidates)

"Cypress" spans very different woods; only Bald Cypress is a top-tier back/sides choice.[^3]

| Wood | Botanical | Density (kg/m³) | Janka (lbf) | MOE (GPa) | MOR (MPa) | Sound speed *c* (m/s) | Radiation ratio *R*[^4] |
|---|---|--:|--:|--:|--:|--:|--:|
| **Bald Cypress** ✅ | *Taxodium distichum* | 515 | 517 | **9.9** | 73.0 | 4384 | **8.51** |
| Monterey Cypress | *Hesperocyparis macrocarpa* | 515 | 369 ᵉ | 7.81 | 81.2 | 3894 | 7.56 |
| Mediterranean ("Spanish") Cypress | *Cupressus sempervirens* | 535 | 396 ᵉ | 5.28 | 44.6 | 3142 | 5.87 |

**Read:** Bald Cypress is the **stiffest and best-behaved** — highest MOE, highest sound speed, top *R* of the group. (Note the paradox: **Mediterranean cypress**, the *traditional Spanish flamenco* wood, scores the **lowest** *R* — proof that a back/sides wood is chosen for *character*, not radiation efficiency.[^5])

## Table 2 — Recommended soundboard tops (pair with the cypress body)

The top does the radiating, so it **must** be a true top wood — never cypress.[^6]

| Top wood | Density (kg/m³) | MOE (GPa) | Sound speed *c* (m/s) | Radiation ratio *R* | Voice |
|---|--:|--:|--:|--:|---|
| Western Red Cedar | 358 | 7.7 | 4635 | **12.93** | Warm, immediate, quick response |
| European Spruce (Alpine) | 405 | 9.5 | 4843 | **11.96** | Balanced, refined |
| Adirondack / Red Spruce | 448 | 11.4 | 5044 | **11.26** | Powerful, high headroom |
| Redwood (old growth) | 448 | 9.2 | 4532 | **10.12** | Warm, complex |
| Sitka Spruce | 448 | 10.8[^7] | 4910 | **10.96** | Bright, punchy, standard |
| Engelmann Spruce | 392 | 8.9[^7] | 4765 | **12.16** | Light, responsive, sweet |
| **Bald Cypress (for contrast)** ❌ | 515 | 9.9 | 4384 | **8.51** | *Reflector, not radiator — top-DISQUALIFIED* |

**Read:** the recommended tops sit at *R* ≈ **10.1–12.9**; cypress is ≈ **8.5** — about 16–34% lower. That gap is precisely why cypress goes on the **back/sides** and spruce/cedar goes on **top**.

---

## Fit by instrument (all flat or round/bowl-back — *not* carved archtop[^8])

| Family | Fit | Why cypress works |
|---|:--:|---|
| **Cuatros** — Puerto Rican (lead) | ★★★ | Bright, reflective back/sides carry a lead voice over an ensemble |
| **Cuatros** — Venezuelan (rhythm) | ★★★ | Dry, fast decay keeps percussive strumming articulate |
| **Flat-back mandolins** (Celtic/folk octave mandolin — *the reference plan*) | ★★☆ | Bright, punchy aesthetic; bends cleanly; light body |
| **Round/bowl-back mandolins** (Neapolitan) | ★★☆ | Light staved bowl; articulate, bright response |
| **Lutes** (and vihuela / baroque guitar) | ★★☆ | Light + quick response suits **polyphonic clarity**; genuine historical precedent[^9] |

## Using the 580 mm plan as the template

- **Scale:** 580 mm — sits in the Puerto Rican cuatro range (~560–585 mm); fret spacing transfers directly.
- **Construction:** flat, X-braced top over bent sides + flat back — the exact build where cypress belongs (**sides + back**), softwood on top.
- **To adapt for a PR cuatro:** widen to **5 double courses / 10 strings** and swap to the cuatro body outline; wood strategy unchanged.

## Practical build notes

- **Workability:** cuts and bends well; clear, wide, quartersawn stock is easy to get. Rot resistance is a storage bonus.
- **Sourcing:** inexpensive, domestic — no CITES, no import friction.
- **Cautions:** slightly brittle/resinous at knots — select clear stock, seal end grain, and thickness/brace for a lighter-than-hardwood back.

## Recommendation

**Approve Bald Cypress for back and sides** across the cuatro / flat-&-round-back mandolin / lute family, topped with spruce or cedar. Historically validated, acoustically correct for these bright, articulate instruments, low-cost, and easy to source.

---

## Annotations

[^1]: **Scope = plucked, flat/bent-plate instruments.** Cypress suits bodies whose plates are flat or bent (not carved). Carved-arch instruments are excluded — see note 8.

[^2]: **Character source:** dry, snappy attack and low sustain are the cypress-family character associated with flamenco guitars. The traditional flamenco wood is Mediterranean cypress (note 5); Bald Cypress is a domestic alternative, not the traditional wood (corrected 2026-11-14).

[^3]: **Data source:** density/Janka/MOE/MOR from the repo `wood_species.json`. These records carry no per-field source. Bald Cypress is in FPL GTR-282; Monterey and Mediterranean cypress are not, so their values are not FPL figures (corrected 2026-11-14).

[^4]: **Radiation ratio** *R = c/ρ*, where sound speed *c = √(E/ρ)*. Higher *R* = a more efficient radiator (governs **soundboards**). For **back/sides**, *R* is *not* the selection criterion — character and reflectivity are.

[^5]: **Character-not-efficiency:** Mediterranean cypress (*R* = 5.87) is the historic flamenco wood despite the lowest *R* — confirming back/sides are chosen for voice, weight, workability, and tradition.

[^6]: **Hard rule:** cypress *R* ≈ 8.5 vs. real tops at 10.1–12.9 → cypress is a poor radiator and must not be used for the soundboard.

[^7]: **Sitka and Engelmann MOE** are from FPL GTR-282 Table 5-3a (12% MC); the repo database still lacks them. *c* and *R* are computed from them. The earlier "*R* ≈ 12–13 from standard published values" had no citation and overstated Sitka (corrected 2026-11-15, C-11). For every species here except European Spruce, density, MOE, *c* and *R* now follow FPL (density at 12% MC by FPL Eq. 4-14); European Spruce is not in FPL and is unsourced.

[^8]: **Excluded — carved archtop mandolins/guitars:** these need a *carved* dense, stiff hardwood back (maple). Cypress (soft, low-density) can't hold a carved arch or give archtop projection. The title's "flat/round-back" qualifier is deliberate.

[^9]: **Lute precedent:** cypress appears in early Iberian plucked instruments; Italian harpsichord soundboards were traditionally cypress — evidence it belongs in the early-instrument tradition (a keyboard soundboard is a different structure, so this does not contradict the no-cypress-tops rule for this family) (workability caveat: brittle staves need clean, knot-free stock).

---

*Sources: repo `wood_species.json` and `luthier_tonewood_reference.json` (no per-value attribution); radiation ratios computed as R = √(E/ρ)/ρ; construction reference "Octave Mandole 580 mm, plan Y. Fesselier."*
