# BOE / IBG — Instrument Family Conflation

**Created:** 2026-05-28
**Revised:** 2026-05-28 — Type tier defined as **sound-production mechanism** (not lineage); added **electro-acoustic** and **regional/ethnic** Types.
**Status:** NAMED — structural re-architecture **deferred** (post-MVP). Per-model geometry-resolution check is IN scope under **CI-RED-015-D**.
**Systems:** Body Outline Editor (**BOE**), Image Body Generator (**IBG**)
**Related:** `SPRINTS.md` → CI-RED-015-D (MVP-path scoped); `docs/archive/2026/evaluations/GAP_ANALYSIS_MASTER.md`

---

## Summary

The instrument taxonomy in BOE/IBG defines a "family" by **instrument _type_** (acoustic / electric / archtop / latin_american / …). In doing so, **type supplanted Brand and Model** — the two levels where a luthier (and a consumer) actually reason about an instrument. Collapsing the taxonomy onto a single type axis causes a **breakdown in interpretation**: a model that lacks its own registered geometry silently falls back to a _type-family default_, even when the model's own artifact exists.

The intended shape, which fits consumer tradition, is a three-level hierarchy:

```
Type  →  Brand  →  Model
```

- Electric → **Gibson** → Les Paul
- Electric → **Fender** → Stratocaster
- Acoustic → **Gibson** → J-45
- Acoustic → **Martin** → D-28

`FAMILY_DEFAULTS` (and the family IDs in `instrument_families.json`) encode only the **Type** level. Brand and Model exist today only as flat spec-id strings (`gibson_les_paul.json`, `fender_stratocaster.json`, `gibson_j45.json`), with no first-class Brand tier between them. That flattening is the conflation.

### What "Type" means here

Type is the **fundamental sound-production mechanism** — *acoustic, electro-acoustic, electric, bass, ukulele, mandolin, regional/ethnic* — **not** body lineage (*dreadnought, jumbo, OM, parlor, archtop, slope-shouldered*). At the mechanism level an instrument is unambiguously one Type: a J-45 is acoustic, a Telecaster is electric, a hollow-body ES-335 is still electric (its body's job differs from a flat-top). The cross-classification that breaks a lineage-based Type tier cannot occur here, because the taxonomy stops making claims at the contested level.

**Operationally, Type is the level at which fabrication fundamentally diverges.** The taxonomy exists to serve the cut, so the test for a Type boundary is a process test: two instruments share a Type when the platform makes their bodies the *same way*, and differ in Type when the body-making process itself diverges. An acoustic body (hollow soundbox, bracing, soundhole) and an electric body (solid blank, pickup and control cavities) are not two points on one process — they are different fabrication processes. Mechanism tracks that divergence; lineage does not, because a dreadnought and a jumbo are fabricated the same way and differ only in dimensions. That is the principled reason Type sits at the mechanism level and lineage drops to Model metadata.

Two Types capture cases that the bare acoustic/electric split leaves ambiguous:

- **Electro-acoustic** — an acoustic body with onboard pickup/preamp. Its outline is acoustic, but the electronics cavity and output routing make its body-handling distinct enough to warrant its own Type rather than a silent acoustic fallback.
- **Regional/Ethnic** — instruments whose identity is defined by **tradition** rather than by the acoustic/electric split. The Puerto Rican and Venezuelan **Cuatros** are the first members. This is a deliberate tradition-based Type: where mechanism alone doesn't capture what the instrument *is*, tradition does. (It replaces the current `latin_american` family id, which conflated a single tradition with the whole regional axis.)

Lineage information stays valuable but moves to **descriptive metadata on the Model**, not a tier of the hierarchy:

```yaml
acoustic-gibson-J45:
  body_style: dreadnought (slope-shouldered)   # descriptive — does NOT drive lookup
  lineage: 1947-onwards Gibson flat-top series
  comparable_to: jumbo (dimensional), dreadnought (categorical)
  body_dimensions: [actual numbers]
```

Lookup is by **Model identity** (`acoustic-gibson-J45`), which always resolves to the Model's own data. Lineage descriptors support filtering and display ("show all dreadnought-style instruments") as a filter over Model metadata — never fallback computation.

### Navigation (the UI trade-off)

Under this taxonomy the platform navigates **Type → Brand → Model** (e.g., *Acoustic → Gibson → J-45*). That is one more selection layer than a lineage-based hierarchy, and a wider Brand tier, but every step is unambiguous: the user knows the broad mechanism, and each brand knows its own models. Popup menus (or equivalent) carry the navigation weight so the **data model stays clean** — the taxonomy never asks the system or the user to make a contested categorization call. Gibson buyers navigate in Gibson terms, Martin buyers in Martin terms, instead of being forced into a shared dreadnought/jumbo/OM grid that fits neither.

---

## The two systems and their artifacts

| System | Role | Owns |
|--------|------|------|
| **BOE** — Body Outline Editor | Author/edit body outlines | spec JSONs, `*_body_outline.dxf` artifacts |
| **IBG** — Image Body Generator | Generate body geometry from registered outlines, with type-family fallback | `body_outlines.json` (outline registry), `FAMILY_DEFAULTS`, `instrument_families.json` |

The DXFs and specs on disk are **BOE development artifacts**. `body_outlines.json` is the **IBG registry** that decides whether a model uses its own outline or a fallback.

---

## Where the conflation lives

1. **`FAMILY_DEFAULTS`** — keyed by Type (Acoustic / Electric / Archtop / Cuatro). A model with no registered outline inherits a Type default.
2. **`instrument_families.json`** — family IDs are Type/tradition-level (`acoustic_flat_top`, `solid_body_electric`, `archtop`, `semi_hollow`, `classical`, `ukulele`, `bass`, `gypsy_jazz`, `latin_american`). No Brand tier.
3. **`body_outlines.json`** — the IBG registry. A model **absent** here gets the Type-family fallback, regardless of whether a BOE outline artifact exists on disk.

**Target shape (post-rearchitecture):**
- `FAMILY_DEFAULTS` → **mechanism-tier** defaults (*acoustic / electro-acoustic / electric / bass / ukulele / mandolin / regional-ethnic*), which should **rarely fire**: every Model resolves to its own data, so the mechanism default exists only for genuinely-unknown instruments and should **warn loud**, never silently substitute.
- `instrument_families.json` → the **mechanism-tier** registry (not lineage groups like `acoustic_flat_top` / `archtop`).
- A new **Brand** tier sits between Type and Model.
- `body_outlines.json` → keyed by **Model identity**.

## Canonical symptom — Gibson J-45 (a gating model)

J-45 has **both** a spec (`gibson_j45.json`) and BOE outline artifacts (`J45_body_outline.dxf`, `J45_body_outline_dense.dxf`) on disk, but is **reported absent from `body_outlines.json`**. The interpretation breakdown that follows:

- IBG can't find J-45 in the outline registry →
- falls back to the **acoustic Type-family default** →
- a real J-45 outline exists in BOE but is **never served**.

That is "type supplants model" in one concrete case, landing on a model we intend to gate MVP on.

### Why Type cannot be the lineage tier

The J-45 is the cleanest proof. By **lineage** it is a *slope-shouldered dreadnought* (dreadnought by category and tradition); by **dimension** its body resembles a *jumbo* more than a Martin-style dreadnought. Under a lineage-tier Type, J-45 belongs to **two Types at once by two correct definitions**, and **no Type-based fallback can be correct for it**. Under a mechanism-tier Type, J-45 is simply **acoustic**, the dreadnought-vs-jumbo question becomes Model metadata, and the conflict dissolves — the taxonomy stops trying to encode information that doesn't cleanly encode. This is why the long-term target (below) puts Type at the mechanism level, not the lineage level.

> **Status of this symptom:** reported from the model inventory; **to be confirmed** by the CI-RED-015-D per-model geometry-resolution check (does each gating model resolve to its own outline, or a Type-family fallback?). It is the geometry-leg analogue of the route "wrong-winner" check.

---

## Model tiers (for the CI-RED-015-D cut-path check)

| Tier | Models | Treatment |
|------|--------|-----------|
| **1 — gating** | Gibson Les Paul, Fender Stratocaster, Gibson J-45 | Geometry resolution checked; J-45 first |
| **2 — look carefully** | Explorer, Flying V, SG, Jumbo Archtop, Martin D-28 1937, **Carlos Jumbo** (same-era commits, **have** body outlines) | Inspect, do not gate |
| **3 — look only** | Telecaster, Epiphone Spartan, ES-335, Melody Maker, L-00, OM-28, Klein, both Cuatros, Soprano Ukulele, F-Style Mandolin, Selmer-Maccaferri, Bass | No gate |

**Excluded from the taxonomy:**
- **Smart Guitar** — not accessible in the public version; out of the public taxonomy entirely and out of the CI-RED-015-D cut-path.

**Forthcoming (blueprints not yet processed):**
- **Cello, Violin, Banjo** — unprocessed blueprints. Each needs a Type placement when processed: bowed strings (cello, violin) and banjo do not fit acoustic/electric cleanly and are candidates either for their own mechanism-tier Types or for **Regional/Ethnic**-style tradition Types — decided at processing time, not now.
- **Mandolin** — additional blueprints pending; the *mandolin* Type already exists (F-Style outline registered).

---

## Scope decision

**Deferred (post-MVP, re-architecture — not housekeeping):**
- Restructuring `FAMILY_DEFAULTS` and `instrument_families.json` to the **mechanism-tier** Type definition (*acoustic / electro-acoustic / electric / bass / ukulele / mandolin / regional-ethnic*) and adding a **Brand** layer between Type and Model.
- Migrating lineage descriptors (dreadnought, jumbo, OM, parlor, archtop, slope-shouldered, …) to **Model metadata**.
- Reconciling every BOE outline artifact into the IBG `body_outlines.json` registry, **keyed by Model identity**.

This is in the same class as "manifest the 143 unmanifested routers" and the 49%-unmanifested platform-trust finding: real, named, and **out of the home-stretch cut**.

**In scope now (correctness, under CI-RED-015-D):**
- For each **gating** model (LP / Strat / J-45), verify geometry resolves to **that model's own outline**, not a Type-family fallback. J-45 is the live suspect.

---

## Guidance going forward

- **Do not** add new families keyed by Type alone; preserve the Brand and Model levels.
- **Do not** let a model silently inherit a Type-family outline when a BOE artifact for that model exists — register it, or fail loud. Silent fallback is the same false-green class as deleted routers and stranded stashes.
- **Lineage** (dreadnought, jumbo, slope-shouldered, etc.) is **descriptive metadata on Models, not a tier** of the taxonomy. Do not introduce new family categories at the lineage level.
- When the re-architecture is scheduled, the target shape is **Type → Brand → Model**, where **Type is the sound-production mechanism** (acoustic / electro-acoustic / electric / bass / ukulele / mandolin / regional-ethnic); `instrument_families.json` becomes that mechanism layer, a new Brand layer sits beneath it, and spec ids resolve as Models under a Brand.
