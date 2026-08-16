# Tonewood Comparison: African Blackwood vs Malaysian Blackwood

> **Source:** `wood_species.json` v4.0.0
> **Generated:** 2026-06-22

This comparison addresses a common point of confusion: African Blackwood and Malaysian Blackwood share a trade name but are **botanically unrelated species** with dramatically different physical properties and tonal characteristics.

---

## At a Glance

| Species | Family | Density (kg/m³) | Janka (lbf) | Tone Character | Sustainability |
|---------|--------|:---:|:---:|----------------|----------------|
| **African Blackwood** | Dalbergia (rosewood) | 1,270 | 1,960 | Glassy, steely, focused, low damping | Endangered — CITES Appendix II |
| **Malaysian Blackwood** | Acacia | 640 | 1,160 | Warm, balanced, opens up with age | Sustainable — plantation-grown |

**Key insight:** These woods are not variants of the same species. They occupy opposite ends of the density spectrum and behave acoustically like different instrument classes.

---

## Physical Properties

| Property | African Blackwood | Malaysian Blackwood | Ratio |
|----------|:---:|:---:|:---:|
| **Scientific Name** | *Dalbergia melanoxylon* | *Acacia melanoxylon* | — |
| **Family** | Fabaceae (Dalbergia) | Fabaceae (Acacia) | — |
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

## Derived Acoustic Properties

These values are computed from the physical properties above using standard acoustic relationships.

| Property | African Blackwood | Malaysian Blackwood | Notes |
|----------|:---:|:---:|-------|
| **Specific Modulus (E/ρ)** | 14.1 | 18.5 | Malaysian higher — lighter weight per unit stiffness |
| **Est. Speed of Sound (m/s)** | ~3,760 | ~4,300 | `c = √(E/ρ)` — Malaysian propagates faster |
| **Est. Acoustic Impedance (10⁶ kg/m²s)** | ~4.78 | ~2.75 | `Z = ρc` — African reflects more energy |
| **Damping** | Very low | Moderate | Inferred from material class |

**Interpretation:** Despite African Blackwood's higher stiffness, its extreme density means the speed of sound is actually lower. However, its acoustic impedance is nearly double — it reflects energy rather than absorbing it.

---

## What Creates the "Glassy" vs "Warm" Tone Difference?

### The Builder's Observation

> "African Blackwood... has that fundamental and very direct powerful tone to it but it can become almost too steely"
>
> "Malaysian Blackwood... does have that fundamental and very direct powerful tone to it... but it has more warmth behind it"
>
> — Rory McGuinness, luthier

### The Physics Behind It

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

## Acoustic Mechanism Comparison

| Mechanism | African Blackwood | Malaysian Blackwood |
|-----------|-------------------|---------------------|
| **Internal Damping** | Very low — energy stays in vibration | Moderate — some energy becomes heat |
| **Acoustic Impedance** | Very high — reflects energy at boundaries | Moderate — transmits more, absorbs some |
| **High-Frequency Retention** | Strong — overtones persist | Attenuated — overtones decay faster |
| **Fundamental Emphasis** | Less prominent vs overtones | More prominent vs overtones |
| **Sustain Character** | Long, with harmonic complexity | Long, with fundamental dominance |

### Think of the Back/Sides as a Filter

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

## Thermal Properties

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

## CNC Machining

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

## Lutherie Profile

| Property | African Blackwood | Malaysian Blackwood |
|----------|:---|:---|
| **Guitar Relevance** | Emerging | Established |
| **Typical Uses** | Fretboard, bridge, nuts, wind instruments | Body, back/sides |
| **Tone Character** | *(not yet characterized in DB)* | Warm, balanced, opens up with age — koa alternative |
| **Sustainability** | CITES Appendix II — increasingly restricted | Sustainable — plantation-grown in Tasmania/Australia |
| **Builder Notes** | Traditional clarinet/oboe wood; extreme density limits guitar use | Increasingly popular as koa prices rise |

---

## Why This Matters for Modal Research

If we were instrumenting this comparison in a lab, we would not measure:
```
glassy
warm
```

We would measure:

### Resonance Peaks
```
f1, f2, f3, ...
```

### Q Factor (Quality Factor)
Higher Q correlates with:
```
ring
glassiness
clarity
```

African Blackwood's low damping predicts high Q.

### Decay Time
```
T60 measurements
energy above 1 kHz after excitation
energy above 2 kHz after excitation
```

African Blackwood should show longer decay in upper harmonics.

### Impedance Mismatch at Boundaries
```
reflection coefficient at glue joints
energy transfer efficiency to soundboard
```

African Blackwood's high impedance means more reflection at joints.

---

## Working Hypothesis

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

## Analysis

### Not Actually Similar Woods

Despite sharing the "blackwood" trade name:

| Attribute | African Blackwood | Malaysian Blackwood |
|-----------|-------------------|---------------------|
| Genus | *Dalbergia* | *Acacia* |
| True rosewood family | **Yes** | No |
| Density class | Extreme (sinks in water) | Moderate (floats) |
| Traditional use | Wind instruments | Guitar back/sides |
| Acoustic behavior | High-impedance reflector | Moderate-impedance transmitter |

They are as different as ebony and mahogany — the shared name is misleading.

### Application Implications

**African Blackwood** excels where:
- Extreme hardness is needed (fretboards, nuts, bridges)
- Low damping is desirable (wind instruments)
- High impedance reflection enhances projection

**Malaysian Blackwood** excels where:
- Warmth and balance are desired (back/sides)
- Workability matters (body carving)
- Sustainability is a factor (plantation wood)
- Cost is a factor (fraction of African Blackwood price)

### The Neck Effect

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

## Data Gaps to Address

| Species | Missing Data |
|---------|-------------|
| **African Blackwood** | Grain description, workability notes, contraction values, tone character, typical lutherie uses, sustainability status |
| **Malaysian Blackwood** | Speed of sound, acoustic impedance (measured, not derived) |
| **Both** | Q-factor measurements, damping coefficients, measured transfer functions |

The database has strong physical/mechanical data but lacks direct acoustic measurements. Filling these gaps — particularly Q-factor and damping — would allow the derived tonal predictions above to be validated experimentally.

---

## References

- Wood species data: `docs/audit-sources/tap_tone_pi/tap_tone_pi/materials/wood_species.json` v4.0.0
- Physical property source: The Wood Database (Eric Meier)
- Builder observation: Rory McGuinness (cited in research notes)
- Acoustic relationships: `c = √(E/ρ)`, `Z = ρc`, standard plate dynamics
