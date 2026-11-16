# Tonewood Comparison: African Blackwood vs Malaysian Blackwood

> **Source:** `wood_species.json` v4.0.0
> **Generated:** 2026-06-22

> **ᵉ Estimated Janka (added 2026-11-14).** Values marked ᵉ equal the bulk-import regression `Janka ≈ 0.00355 × density^1.85` (`scripts/bulk_import_wood_species.py`), not a hardness test. They rise smoothly with density, so they cannot rank species of similar density, and they can be far below published measurements for the hardest woods. Treat them as placeholders. See `VERIFICATION_LOG.md` (C-02).

> **Identity caution (added 2026-11-14, `VERIFICATION_LOG.md` C-07).** No source in this repo establishes that "Malaysian Blackwood" is *Acacia melanoxylon*. Every "Malaysian" value here is the Tasmanian Blackwood record from `wood_species.json` (e.g. MOE 11.82 GPa), so it describes *A. melanoxylon* in general, not Malaysian-grown stock. Plantation acacia in Malaysia is widely reported to be mainly *A. mangium* and its hybrids; confirm the species with the supplier before relying on these numbers.

> **Role: focused comparison (TONEWOOD-BLACKWOODS-RECONCILIATION-003).** The shared Acacia-family reference is [tonewood_comparison_acacia_family_blackwoods_koa.md](tonewood_comparison_acacia_family_blackwoods_koa.md). This file keeps the African-versus-Malaysian comparison only. It is a research note, not a purchasing, regulatory, engineering, or manufacturing authority. No measurement in this document was independently revalidated by this reconciliation.

## Purpose and limits

This document compares African Blackwood with the trade name Malaysian Blackwood. It is not the Acacia-family survey. Genera, the Koa and Mangium relatives, and the Albizia cousins stay in the shared reference linked above and again under Shared reference.

This comparison addresses a common point of confusion: African Blackwood and Malaysian Blackwood share a trade name but are **different genera within the same botanical family, Fabaceae; the trade names do not establish species equivalence.** The two columns below differ sharply in physical properties and tonal characteristics.

Read that sentence with the identity caution above. African Blackwood in these tables is *Dalbergia melanoxylon*. The Malaysian column is the Tasmanian Blackwood record (*Acacia melanoxylon*) from `wood_species.json`. That record is not an established identification of wood sold as Malaysian Blackwood. Where the column is that record, the two columns are different genera, *Dalbergia* and *Acacia*. This page does not decide what a supplier's Malaysian Blackwood is.

The figures below are the figures already in this document before the reconciliation. None were recalculated. Estimated Janka values remain marked ᵉ. Derived acoustic figures remain estimates from `c = √(E/ρ)` and `Z = ρc`, as the tables already say.

## Species and trade-name identity

| Trade name in this comparison | Record the values come from | What this library establishes |
|---|---|---|
| African Blackwood | *Dalbergia melanoxylon* | The African column is this species. It is a *Dalbergia*, not an *Acacia*. |
| Malaysian Blackwood | Tasmanian Blackwood record, *Acacia melanoxylon*, in `wood_species.json` | Not established as the trade name's species. The identity caution quotes the limit: no source here identifies Malaysian Blackwood as *A. melanoxylon*; the values (for example MOE 11.82 GPa) are the Tasmanian record and describe *A. melanoxylon* in general, not Malaysian-grown stock. Plantation acacia in Malaysia is widely reported to be mainly *A. mangium* and its hybrids. |

The scientific-name cell in Physical Properties still reads *Acacia melanoxylon* for the Malaysian column. That cell names the record, not a confirmed trade-name identity. The same limit applies to the genus cell and the "True rosewood family" cell under Not Actually Similar Woods: both follow the record's genus, not a confirmed identification of the trade name.

## African versus Malaysian properties

The Malaysian column in every table below is the Tasmanian record named above. Ratios and derived figures are the ones already printed. They were not recomputed.

### At a Glance

| Species | Family | Density (kg/m³) | Janka (lbf) | Tone Character | Sustainability |
|---------|--------|:---:|:---:|----------------|----------------|
| **African Blackwood** | Dalbergia (rosewood) | 1,270 | 1,960 ᵉ | Glassy, steely, focused, low damping | IUCN Near Threatened (2020); CITES App II, instruments exempt (#15) |
| **Malaysian Blackwood** | Acacia (reference record; trade-name identity not established) | 640 | 1,160 | Warm, balanced, opens up with age | Sustainable — plantation-grown |

**Key insight:** These woods are in different genera, not variants of one wood. They occupy opposite ends of the density spectrum and behave acoustically like different instrument classes. That statement is about the two columns as defined in Species and trade-name identity: *Dalbergia melanoxylon* beside the Tasmanian *A. melanoxylon* record. It is not a determination of wood sold under the Malaysian trade name.

---

### Physical Properties

| Property | African Blackwood | Malaysian Blackwood | Ratio |
|----------|:---:|:---:|:---:|
| **Scientific Name** | *Dalbergia melanoxylon* | *A. melanoxylon* reference record — not confirmed as the traded wood's species | — |
| **Family** | Fabaceae (Dalbergia) | Fabaceae (Acacia) — of the reference record | — |
| **Specific Gravity** | 1.27 | 0.58 | **2.2×** |
| **Density (kg/m³)** | 1,270 | 640 | **2.0×** |
| **Janka Hardness (lbf)** | 1,960 | 1,160 | 1.7× |
| **Janka Hardness (N)** | 8,719 | 5,160 | 1.7× |
| **MOE (GPa)** | 17.95 | 11.82 | 1.5× |
| **MOR (MPa)** | 213.6 | 96.5 | **2.2×** |
| **Grain** | — | Straight to wavy, often highly figured | — |
| **Workability** | — | Good | — |
| **Contraction Radial (%)** | — | 4.38 | — |
| **Contraction Tangential (%)** | — | 8.38 | — |

African Blackwood is **twice as dense** and **twice as strong** as Malaysian Blackwood. This is not a subtle difference — it is the difference between a clarinet bore and a guitar back.

---

### Derived Acoustic Properties

These values are computed from the physical properties above using standard acoustic relationships.

| Property | African Blackwood | Malaysian Blackwood | Notes |
|----------|:---:|:---:|-------|
| **Specific Modulus (E/ρ)** | 14.1 | 18.5 | Malaysian higher — lighter weight per unit stiffness |
| **Est. Speed of Sound (m/s)** | ~3,760 | ~4,300 | `c = √(E/ρ)` — Malaysian propagates faster |
| **Est. Acoustic Impedance (10⁶ kg/m²s)** | ~4.78 | ~2.75 | `Z = ρc` — African reflects more energy |
| **Damping** | Very low | Moderate | Inferred from material class |

**Interpretation:** Despite African Blackwood's higher stiffness, its extreme density means the speed of sound is actually lower. However, its acoustic impedance is nearly double — it reflects energy rather than absorbing it.

---

### Acoustic Mechanism Comparison

| Mechanism | African Blackwood | Malaysian Blackwood |
|-----------|-------------------|---------------------|
| **Internal Damping** | Very low — energy stays in vibration | Moderate — some energy becomes heat |
| **Acoustic Impedance** | Very high — reflects energy at boundaries | Moderate — transmits more, absorbs some |
| **High-Frequency Retention** | Strong — overtones persist | Attenuated — overtones decay faster |
| **Fundamental Emphasis** | Less prominent vs overtones | More prominent vs overtones |
| **Sustain Character** | Long, with harmonic complexity | Long, with fundamental dominance |

#### Think of the Back/Sides as a Filter

African Blackwood:
```
passes more high-frequency content
reflects energy back into the soundboard
minimal absorption
```

Malaysian Blackwood:
```
attenuates some high-frequency content
absorbs more energy internally
emphasizes fundamental modes
```

This is why African Blackwood sounds:
```
glassy
focused
steely
piano-like
```

While Malaysian Blackwood sounds:
```
warm
round
full
mahogany-adjacent
```

---

### Thermal Properties

| Property | African Blackwood | Malaysian Blackwood |
|----------|:---:|:---:|
| **Thermal Conductivity (W/m·K)** | 0.48 | 0.17 |
| **Specific Heat (J/kg·K)** | 1,238 | 1,650 |
| **SCE (J/mm³)** | 0.98 | 0.45 |
| **Heat Partition — Chip** | 0.56 | 0.70 |
| **Heat Partition — Tool** | 0.28 | 0.20 |
| **Heat Partition — Work** | 0.16 | 0.10 |

African Blackwood generates **more than twice the cutting energy** and routes more heat into the tool and workpiece. This makes it significantly harder to machine.

---

### CNC Machining

| Property | African Blackwood | Malaysian Blackwood |
|----------|:---:|:---:|
| **Hardness Scale** | 0.56 | 0.50 |
| **Burn Tendency** | 0.38 | 0.30 |
| **Tearout Tendency** | 0.37 | 0.30 |
| **Chipload Multiplier** | 0.85 | 1.00 |
| **Roughing Feed Max (mm/min)** | 3,200 | 4,000 |
| **Finishing Feed Max (mm/min)** | 1,820 | 2,500 |
| **Plunge Feed Max (mm/min)** | 992 | 1,000 |
| **Min RPM** | 14,480 | 12,000 |
| **Max RPM** | 24,000 | 24,000 |
| **Optimal SFM** | 696 | 800 |
| **Max DOC (mm)** | 9 | 12 |
| **Optimal DOC Ratio** | 0.39 | 0.50 |
| **Max WOC Ratio** | 0.42 | 0.50 |

| Risk | African Blackwood | Malaysian Blackwood |
|------|:---:|:---:|
| **Burn Risk** | Medium | Low |
| **Tearout Risk** | Medium | Low |
| **Dust Hazard** | **HIGH** | Low |

**Machining notes:**
- African Blackwood: Requires reduced chipload (0.85×), conservative DOC. Carbide mandatory. Dust is hazardous.
- Malaysian Blackwood: Machines beautifully. Standard parameters. Premium koa alternative at lower machining cost.

---

## Instrument-use implications

The tone descriptions, lutherie uses, and the neck note below are the comparison's existing reading of those properties. They are not new trial results.

### What Creates the "Glassy" vs "Warm" Tone Difference?

#### The Builder's Observation

> "African Blackwood... has that fundamental and very direct powerful tone to it but it can become almost too steely"
>
> "Malaysian Blackwood... does have that fundamental and very direct powerful tone to it... but it has more warmth behind it"
>
> — Rory McGuinness, luthier

#### The Physics Behind It

When builders describe tone as **glassy, steely, bell-like**, they are hearing:

```
strong overtone retention
high-frequency reflection
low internal damping
```

When builders describe tone as **warm, rich, rounded**, they are hearing:

```
stronger fundamental emphasis
high-frequency attenuation
moderate internal damping
```

---

### Lutherie Profile

| Property | African Blackwood | Malaysian Blackwood |
|----------|:---|:---|
| **Guitar Relevance** | Emerging | Established |
| **Typical Uses** | Fretboard, bridge, nuts, wind instruments | Body, back/sides |
| **Tone Character** | *(not yet characterized in DB)* | Warm, balanced, opens up with age — koa alternative |
| **Sustainability** | CITES Appendix II via *Dalbergia* spp. — finished instruments, parts and accessories exempt (#15); raw wood needs permits (see [CITES_STATUS.md](CITES_STATUS.md)) | Sustainable — plantation-grown in Tasmania/Australia |
| **Builder Notes** | Traditional clarinet/oboe wood; extreme density limits guitar use | Increasingly popular as koa prices rise |

---

### Analysis

#### Not Actually Similar Woods

Despite sharing the "blackwood" trade name:

| Attribute | African Blackwood | Malaysian Blackwood |
|-----------|-------------------|---------------------|
| Genus | *Dalbergia* | *Acacia* (reference record; trade-name identity not established) |
| True rosewood family | **Yes** | No |
| Density class | Extreme (sinks in water) | Moderate (floats) |
| Traditional use | Wind instruments | Guitar back/sides |
| Acoustic behavior | High-impedance reflector | Moderate-impedance transmitter |

They are as different as ebony and mahogany — the shared name is misleading.

#### Application Implications

**African Blackwood** excels where:
- Extreme hardness is needed (fretboards, nuts, bridges)
- Low damping is desirable (wind instruments)
- High impedance reflection enhances projection

**Malaysian Blackwood** excels where:
- Warmth and balance are desired (back/sides)
- Workability matters (body carving)
- Sustainability is a factor (plantation wood)
- Cost is a factor (fraction of African Blackwood price)

#### The Neck Effect

The same physics applies to neck wood selection. Changing:
```
mass
stiffness
damping
```
changes:
```
where vibrational energy goes
```
throughout the instrument.

A denser, stiffer neck (like African Blackwood) focuses energy and adds projection. A lighter, more damped neck (like Malaysian Blackwood or mahogany) allows more energy into the body, trading projection for warmth.

---

### Why This Matters for Modal Research

If we were instrumenting this comparison in a lab, we would not measure:
```
glassy
warm
```

We would measure:

#### Resonance Peaks
```
f1, f2, f3, ...
```

#### Q Factor (Quality Factor)
Higher Q correlates with:
```
ring
glassiness
clarity
```

African Blackwood's low damping predicts high Q.

#### Decay Time
```
T60 measurements
energy above 1 kHz after excitation
energy above 2 kHz after excitation
```

African Blackwood should show longer decay in upper harmonics.

#### Impedance Mismatch at Boundaries
```
reflection coefficient at glue joints
energy transfer efficiency to soundboard
```

African Blackwood's high impedance means more reflection at joints.

---

### Working Hypothesis

Based on material properties and builder observations:

| Property | African Blackwood | Malaysian Blackwood |
|----------|-------------------|---------------------|
| **Q Factor** | Higher | Lower |
| **Internal Damping** | Very low | Moderate |
| **Overtone Retention** | Strong | Attenuated |
| **Fundamental Emphasis** | Less relative to overtones | More relative to overtones |
| **Perceived Tone** | Glassy, steely, focused | Warm, rich, rounded |

What Rory described is not mystical — it is a direct manifestation of:
```
density
stiffness
damping
acoustic impedance
```

These are all quantities that could be measured in Tap-Tone-Pi workflows.

---

## Availability, sourcing, and regulatory distinctions

These are the sourcing and status words already printed in the tables. This reconciliation did not re-query Species+ and did not survey suppliers.

- **African Blackwood.** At a Glance: IUCN Near Threatened (2020); CITES Appendix II, instruments exempt (#15). Lutherie Profile: CITES Appendix II via *Dalbergia* spp. — finished instruments, parts and accessories exempt (#15); raw wood needs permits, with the existing link to [CITES_STATUS.md](CITES_STATUS.md).
- **Malaysian column.** At a Glance: "Sustainable — plantation-grown". Lutherie Profile: "Sustainable — plantation-grown in Tasmania/Australia". Those words belong to the Tasmanian *A. melanoxylon* record the column copies. They are not a finding about Malaysian-grown stock. Confirm the species with the supplier before relying on the column (identity caution).
- **Price.** Application Implications says Malaysian Blackwood can be a "fraction of African Blackwood price". No price figure is given. That phrase is not a quote, a market survey, or purchasing authority.
- **Dust.** The CNC table rates African Blackwood dust hazard HIGH and the Malaysian column Low. That is the existing machining note, not a regulatory classification made here.

## Known evidence gaps

The gap table is the document's existing list. One cell is stale relative to text already in this file: African Blackwood's "sustainability status" is listed as missing, while the Lutherie Profile table already states the CITES Appendix II annotation #15 position recorded under `VERIFICATION_LOG.md` C-06. This reconciliation does not treat that sentence as a new listing check. The other gaps, including missing Q-factor and damping measurements, still stand. Filling them would be a separate verification.

### Data Gaps to Address

| Species | Missing Data |
|---------|-------------|
| **African Blackwood** | Grain description, workability notes, contraction values, tone character, typical lutherie uses, sustainability status |
| **Malaysian Blackwood** | Speed of sound, acoustic impedance (measured, not derived) |
| **Both** | Q-factor measurements, damping coefficients, measured transfer functions |

The database has strong physical/mechanical data but lacks direct acoustic measurements. Filling these gaps — particularly Q-factor and damping — would allow the derived tonal predictions above to be validated experimentally.

---

## Shared reference

Botanical scope for the Acacia and Albizia tonewoods — genera, Tasmanian and Australian blackwood, the unverified Malaysian trade name, Koa, Mangium, Monkeypod, Mugavu, and the shared sourcing caution — is [tonewood_comparison_acacia_family_blackwoods_koa.md](tonewood_comparison_acacia_family_blackwoods_koa.md). This comparison does not restate that survey and does not rank those species against each other.

## Sources for this comparison

Citations below are the document's existing sources, kept as written. The historical `wood_species.json` path was not checked against another file and was not replaced. Shared family citations that this comparison does not use stay in the shared reference.

### References

- Wood species data: `docs/audit-sources/tap_tone_pi/tap_tone_pi/materials/wood_species.json` v4.0.0
- Physical property source: The Wood Database (Eric Meier)
- Builder observation: Rory McGuinness (cited in research notes)
- Acoustic relationships: `c = √(E/ρ)`, `Z = ρc`, standard plate dynamics

- Shared Acacia-family reference: [tonewood_comparison_acacia_family_blackwoods_koa.md](tonewood_comparison_acacia_family_blackwoods_koa.md)
- Identity limit: `docs/tonewood/VERIFICATION_LOG.md`, C-07
- Reconciliation record (duplication only, not a revalidation): `docs/investigations/tonewood-verification-003/BLACKWOODS_RECONCILIATION.md`
