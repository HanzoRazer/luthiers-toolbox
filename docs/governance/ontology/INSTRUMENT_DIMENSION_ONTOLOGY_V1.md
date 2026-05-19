# Instrument Dimension Ontology V1

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION  
**Date:** 2026-05-15  
**Authority:** PROPOSED — NOT RATIFIED  
**Scope:** Foundational body dimension fields only  
**Track:** Instrument Knowledge Reconciliation (Sandbox)

---

## Purpose

This document establishes semantic definitions for foundational instrument dimension fields. It serves as ontology discovery and semantic arbitration preparation, NOT canonical ratification.

**This document:**
- Documents competing meanings currently in the repository
- Identifies current usage patterns by source
- Proposes preferred semantic direction
- Flags unresolved authority questions

**This document does NOT:**
- Ratify canonical meaning (requires governance approval)
- Migrate existing storage
- Modify consumers
- Delete duplicate systems

---

## Authority Statement

This ontology draft is:

```
semantic arbitration groundwork
```

NOT:

```
canonical repository truth
```

The distinction matters because the repository currently lacks semantic consensus on dimensional meaning. Presenting this as fully authoritative would create accidental ontology authority — the exact failure mode the governance methodology warns against.

**Required lifecycle:**

```
draft ontology (this document)
→ governance review
→ conflict arbitration
→ canonical ratification
→ executable schema
→ migration planning
```

---

## Measurement Convention Framework

Before defining individual fields, this section establishes the measurement convention categories that create semantic ambiguity.

### Convention A: Physical Instrument Measurement

Measurement of the actual physical instrument body.

| Property | Definition |
|----------|------------|
| Reference | Physical instrument |
| Technique | Direct measurement with calipers/ruler |
| Orientation | Instrument in playing position |
| Origin | Typically heel or butt end |
| Precision | Sub-millimeter |

### Convention B: Outline Bounding Box

Measurement derived from the geometric bounding box of a body outline.

| Property | Definition |
|----------|------------|
| Reference | 2D outline polygon |
| Technique | min/max of coordinate arrays |
| Orientation | Depends on outline orientation in source file |
| Origin | Bounding box corner |
| Precision | Depends on outline resolution |

### Convention C: Construction Template

Measurement for construction/manufacturing purposes.

| Property | Definition |
|----------|------------|
| Reference | Template or plan drawing |
| Technique | CAD measurement from template |
| Orientation | Template-specific |
| Origin | Template-specific |
| Precision | Template resolution |

**Critical insight:** These conventions produce different values for the same instrument. The repository currently conflates them without explicit distinction.

---

## Canonical Field Definitions

### Field 1: `body_length_mm`

#### Observed Meanings

| Meaning | Description |
|---------|-------------|
| A | Physical body length: heel-to-tail measurement along centerline |
| B | Outline bounding box height: vertical extent of body outline polygon |
| C | Template reference length: construction dimension from plan |

#### Current Repository Usage

| Source | Apparent Meaning | Example Value (Stratocaster) |
|--------|------------------|------------------------------|
| `instrument_specs.py` | Physical body length (A) | 406 mm |
| `body_templates.json` | Template length (C) | 396 mm |
| `outlines.py` _BODY_METADATA | Bounding box height (B) | 458.8 mm |

#### Semantic Conflict

The Stratocaster shows 62.8 mm variance (406 vs 458.8) between physical and bbox interpretations. This is not measurement error — it reflects fundamentally different measurement conventions.

#### Governance Recommendation

**Preferred future meaning:**

```
Physical instrument body length measured along the centerline
from the heel joint to the tail/butt end.
```

**Rationale:** This is the semantically meaningful lutherie measurement. Bounding box values should use a distinct field name.

#### Status

```
UNRESOLVED — requires canonical ratification
```

---

### Field 2: `lower_bout_width_mm`

#### Observed Meanings

| Meaning | Description |
|---------|-------------|
| A | Maximum horizontal width in the lower bout region |
| B | Horizontal chord at the widest point of lower bout |
| C | Bounding box width of entire body |

#### Current Repository Usage

| Source | Apparent Meaning | Example Value (Stratocaster) |
|--------|------------------|------------------------------|
| `instrument_specs.py` | Maximum lower bout width (A) | 408 mm |
| `body_templates.json` | Body width (uses `width_mm`) | 318 mm |
| `outlines.py` _BODY_METADATA | Bounding box width (C) | 322.3 mm |

#### Semantic Conflict

`body_templates.json` uses generic `width_mm` which conflates with lower bout width. The 90 mm variance (408 vs 318) suggests completely different measurement targets — likely the template measures something other than the widest point.

#### Governance Recommendation

**Preferred future meaning:**

```
Maximum horizontal width of the body in the lower bout region,
measured as a horizontal chord perpendicular to the centerline.
```

**Rationale:** Explicit about measurement technique (horizontal chord) and location (lower bout maximum).

#### Status

```
UNRESOLVED — requires canonical ratification
```

---

### Field 3: `upper_bout_width_mm`

#### Observed Meanings

| Meaning | Description |
|---------|-------------|
| A | Maximum horizontal width in the upper bout region |
| B | Width at a specific y-position (normalized or absolute) |

#### Current Repository Usage

| Source | Apparent Meaning | Example Value (Stratocaster) |
|--------|------------------|------------------------------|
| `instrument_specs.py` | Maximum upper bout width (A) | 311 mm |
| `body_templates.json` | Not explicitly present | — |
| `outlines.py` | Not explicitly present | — |

#### Semantic Conflict

Less severe than other fields — primarily appears in `instrument_specs.py`. However, lack of presence in other sources creates implicit conflict: consumers may derive upper bout from outline data using different methods.

#### Governance Recommendation

**Preferred future meaning:**

```
Maximum horizontal width of the body in the upper bout region,
measured as a horizontal chord perpendicular to the centerline.
```

#### Status

```
UNRESOLVED — requires canonical ratification
```

---

### Field 4: `waist_width_mm`

#### Observed Meanings

| Meaning | Description |
|---------|-------------|
| A | Minimum horizontal width at the waist |
| B | Width at a specific y-position defined by `waist_y_norm` |

#### Current Repository Usage

| Source | Apparent Meaning | Example Value (Stratocaster) |
|--------|------------------|------------------------------|
| `instrument_specs.py` | Minimum waist width (A) + y-position | 308 mm @ y_norm=0.47 |
| `body_templates.json` | Not explicitly present | — |
| `outlines.py` | Not explicitly present | — |

#### Semantic Conflict

The `instrument_specs.py` includes `waist_y_norm` which implies waist is at a specific position, but the width value (308) is nearly equal to lower bout (408 is lower_bout) suggesting measurement ambiguity for double-cutaway bodies where "waist" is less pronounced.

#### Governance Recommendation

**Preferred future meaning:**

```
Minimum horizontal width of the body at the waist region,
measured as a horizontal chord perpendicular to the centerline.
```

**Note:** For bodies without clear waist (e.g., Flying V), this field may be semantically inapplicable.

#### Status

```
UNRESOLVED — requires canonical ratification
```

---

### Field 5: `body_outline_bbox_width_mm`

#### Observed Meanings

This field does NOT currently exist explicitly. It is PROPOSED to disambiguate from physical measurements.

| Meaning | Description |
|---------|-------------|
| PROPOSED | Horizontal extent of the body outline bounding box |

#### Current Repository Usage

| Source | Field Used | Example Value (Stratocaster) |
|--------|------------|------------------------------|
| `outlines.py` _BODY_METADATA | `width_mm` | 322.3 mm |

#### Semantic Conflict

Currently `width_mm` in `outlines.py` is bbox-derived but not explicitly named as such. This creates conflation with physical `lower_bout_width_mm`.

#### Governance Recommendation

**Preferred future meaning:**

```
Horizontal extent (max_x - min_x) of the body outline polygon
bounding box, in millimeters.
```

**Rationale:** Explicit bbox prefix prevents conflation with physical measurements.

#### Status

```
PROPOSED NEW FIELD — requires canonical ratification
```

---

### Field 6: `body_outline_bbox_height_mm`

#### Observed Meanings

This field does NOT currently exist explicitly. It is PROPOSED to disambiguate from physical measurements.

| Meaning | Description |
|---------|-------------|
| PROPOSED | Vertical extent of the body outline bounding box |

#### Current Repository Usage

| Source | Field Used | Example Value (Stratocaster) |
|--------|------------|------------------------------|
| `outlines.py` _BODY_METADATA | `height_mm` | 458.8 mm |

#### Semantic Conflict

Currently `height_mm` in `outlines.py` is bbox-derived but named generically. The 458.8 mm value differs significantly from physical body_length (406 mm), demonstrating the conflation problem.

#### Governance Recommendation

**Preferred future meaning:**

```
Vertical extent (max_y - min_y) of the body outline polygon
bounding box, in millimeters.
```

#### Status

```
PROPOSED NEW FIELD — requires canonical ratification
```

---

### Field 7: `scale_length_mm`

#### Observed Meanings

| Meaning | Description |
|---------|-------------|
| A | Nut-to-bridge saddle distance (vibrating string length) |
| B | Fret scale mathematical basis (2x nut-to-12th-fret) |

#### Current Repository Usage

| Source | Apparent Meaning | Example Value (Stratocaster) |
|--------|------------------|------------------------------|
| `instrument_specs.py` | Not present in BODY_DIMENSIONS | — |
| `body_templates.json` | Physical scale length (A) | 647.7 mm |
| `instrument_model_registry.json` | Physical scale length (A) | 648.0 mm |

#### Semantic Conflict

Minor variance (647.7 vs 648.0) likely represents different sources (Fender spec vs rounded). More importantly, scale_length belongs to the neck/fretboard domain, not body domain — its presence in body templates creates domain boundary ambiguity.

#### Governance Recommendation

**Preferred future meaning:**

```
Vibrating string length from nut to bridge saddle contact point,
in millimeters. This is a neck/fretboard property, not a body property.
```

**Note:** Consider whether this field belongs in body ontology at all, or should be deferred to a neck/fretboard ontology layer.

#### Status

```
UNRESOLVED — domain ownership unclear
```

---

## Observed Semantic Conflicts

### Conflict 1: Stratocaster Dimensional Disagreement

| Source | body_length | lower_bout_width | width_generic |
|--------|-------------|------------------|---------------|
| `instrument_specs.py` | 406 mm | 408 mm | — |
| `body_templates.json` | 396 mm | — | 318 mm |
| `outlines.py` | — | — | 322.3 mm (bbox) |
| `outlines.py` | 458.8 mm (bbox height) | — | — |

**Likely cause:** Three different measurement conventions applied to the same instrument.

**Ontology implication:** `body_length_mm` lacks stable semantic definition. Values range from 396 to 458.8 mm depending on interpretation.

**Status:** UNRESOLVED

---

### Conflict 2: Les Paul Dimensional Disagreement

| Source | body_length | lower_bout_width | width_generic |
|--------|-------------|------------------|---------------|
| `instrument_specs.py` | 450 mm | 340 mm | — |
| `body_templates.json` | 444 mm | — | 330 mm |
| `outlines.py` | 269.2 mm (bbox height) | — | 383.5 mm (bbox width) |

**Likely cause:** The outline bbox height (269.2 mm) is dramatically smaller than physical length (450 mm), suggesting the outline may be oriented differently (landscape vs portrait) or represents only a portion of the body.

**Ontology implication:** Outline data cannot be directly compared to physical measurements without transformation metadata.

**Status:** UNRESOLVED — requires outline orientation investigation

---

### Conflict 3: Terminology Drift

| Source Term | Normalized Term | Source | Issue |
|-------------|-----------------|--------|-------|
| `length_mm` | `body_length_mm` | body_templates.json | Missing `body_` prefix |
| `width_mm` | ambiguous | body_templates.json | Could be bbox or lower_bout |
| `height_mm` | `body_outline_bbox_height_mm` | outlines.py | Missing `bbox` qualifier |
| `body_width_mm` | `lower_bout_width_mm` | GuitarDimensions | Semantic alias |

**Ontology implication:** Field names do not consistently indicate measurement convention.

**Status:** UNRESOLVED — requires terminology normalization

---

## Semantic Boundaries

### This Ontology Owns

- Body dimension field semantic definitions
- Measurement convention disambiguation
- Physical vs. bounding box distinction

### This Ontology Does NOT Own

- Outline coordinate data (owned by body_outlines.py)
- Morphology classification (owned by body_grid)
- Construction specifications (owned by spec files)
- CAM/machining dimensions (owned by CAM domain)
- Neck/fretboard dimensions (separate ontology layer)

---

## Allowed Derivations

### Permitted

| Derivation | Rule |
|------------|------|
| bbox → bbox | Bounding box values may derive other bbox values |
| physical → physical | Physical values may derive other physical values |
| bbox + transform → physical | With explicit transformation metadata and provenance |

### Forbidden

| Derivation | Reason |
|------------|--------|
| bbox → physical (implicit) | Conflates measurement conventions |
| physical → bbox (implicit) | Loses measurement provenance |
| Mixed convention averaging | Creates meaningless hybrid values |

---

## Normalization Mappings

These mappings document observed terminology variations that should normalize to canonical field names.

| Source Term | Canonical Term | Confidence | Notes |
|-------------|----------------|------------|-------|
| `body_length` | `body_length_mm` | HIGH | Add unit suffix |
| `length_mm` (in body context) | `body_length_mm` | MEDIUM | Context-dependent |
| `body_width` | `lower_bout_width_mm` | MEDIUM | Semantic alias, verify |
| `width_mm` (in body context) | AMBIGUOUS | LOW | Could be bbox or lower_bout |
| `height_mm` (in outline context) | `body_outline_bbox_height_mm` | HIGH | Bbox-derived |
| `lower_bout` | `lower_bout_width_mm` | HIGH | Add `_width_mm` suffix |
| `upper_bout` | `upper_bout_width_mm` | HIGH | Add `_width_mm` suffix |
| `waist` | `waist_width_mm` | HIGH | Add `_width_mm` suffix |

---

## Related Coordinate Conventions

The `body_grid` system currently uses:

```
y_norm: 0.0 at butt/tail, 1.0 at neck end
x_norm: signed distance from centerline (negative=bass, positive=treble)
```

**This ontology does NOT ratify a repository-wide canonical coordinate system.**

Coordinate ontology deserves separate governance because it affects:
- Geometry systems
- Morphology analysis
- CAM operations
- RMOS validation
- Vectorizer output
- Body grid
- Adaptive runtime systems

Coordinate system ratification is deferred to a future ontology layer.

---

## Known Ambiguities

### Ambiguity 1: Outline Orientation

Body outlines may be stored in different orientations (portrait vs. landscape). Without explicit orientation metadata, bbox dimensions cannot be reliably interpreted.

**Impact:** Les Paul bbox height (269.2 mm) suggests landscape orientation, but this is not documented.

**Recommendation:** Add `outline_orientation` metadata to outline storage.

---

### Ambiguity 2: Cutaway Bodies

For bodies with cutaways (Stratocaster, Les Paul), the "upper bout" concept becomes ambiguous — is it measured at the cutaway, or at the theoretical maximum if the cutaway weren't present?

**Impact:** Upper bout measurements may not be comparable across instruments with different cutaway styles.

**Recommendation:** Define separate fields for `upper_bout_at_cutaway_mm` vs `upper_bout_theoretical_mm` if distinction matters.

---

### Ambiguity 3: Waist Definition for Non-Traditional Bodies

Flying V, Explorer, and other angular bodies lack a traditional waist. Current `waist_width_mm` semantics are undefined for these body styles.

**Impact:** Waist values for angular bodies may be meaningless or measured inconsistently.

**Recommendation:** Define waist as "minimum width" which is meaningful for all body styles, or mark field as "not applicable" for certain body families.

---

## Deferred Ontology Areas

The following are explicitly OUT OF SCOPE for this V1 ontology:

| Area | Reason for Deferral |
|------|---------------------|
| Neck pocket dimensions | Separate construction domain |
| Hardware cavity dimensions | Separate construction domain |
| Bracing patterns | Separate acoustic domain |
| Morphology descriptors | Owned by body_grid |
| Feature routes | Separate CAM domain |
| Headstock dimensions | Separate ontology layer |
| Fretboard dimensions | Separate ontology layer |
| Coordinate systems | Requires broader governance |

These areas require their own ontology documents after the foundational dimension ontology is ratified.

---

## Promotion Implications

If this ontology is ratified, the following promotion workflow is implied:

### Evidence Sources (Tier 3 — Non-Canonical)

```
morphology_harvest/outputs/
vectorizer extractions
AI vision outputs
```

These produce dimensional evidence, NOT canonical values.

### Curated Stage (Tier 2 — Reviewed)

```
data_registry/curated/instruments/
```

Evidence promoted after human review, using ontology field names.

### Canonical Authority (Tier 1 — Governed)

```
data_registry/system/instruments/
```

Ratified values conforming to ontology definitions.

**Key principle:**

```
Promotion is semantic arbitration, not file movement.
```

Values must be verified against ontology definitions during promotion.

---

## Governance Questions Requiring Decision

| # | Question | Impact |
|---|----------|--------|
| 1 | Should bbox fields be separate from physical fields? | Schema design |
| 2 | Should `scale_length_mm` be in body ontology or deferred? | Domain boundaries |
| 3 | How should cutaway bodies handle upper bout? | Measurement convention |
| 4 | Should waist be "minimum width" for all bodies? | Semantic definition |
| 5 | Is outline orientation metadata required? | Data requirements |

---

## Document Lifecycle

| Phase | Status | Date |
|-------|--------|------|
| Initial draft | COMPLETE | 2026-05-15 |
| Governance review | PENDING | — |
| Conflict arbitration | PENDING | — |
| Canonical ratification | PENDING | — |
| Executable schema | BLOCKED | — |
| Migration planning | BLOCKED | — |

---

## Terminology Note

**Data Promotion Tiers vs. Governance Authority Tiers**

This document uses "Tier 1/2/3" to describe data promotion stages. This is distinct from `GOVERNANCE_AUTHORITY_HIERARCHY.md` which uses "Tier 1/2/3" for governance authority strata. These are separate semantic systems. See `GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md` for disambiguation.

---

## Related Documents

### Governance Stack Documents

- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md` — Tier 3→2 review governance
- `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` — Governance-state visibility
- `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md` — Ownership boundaries
- `docs/governance/ontology/GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md` — Stack consistency verification

### Audit Documents

- `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md` — Storage topology audit
- `docs/governance/MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md` — Staging authority
- `docs/governance/MORPHOLOGY_HARVEST_GOVERNANCE_AUDIT.md` — Collision audit

### Source Files

- `services/api/app/instrument_geometry/instrument_specs.py` — Current "canonical" source
- `services/api/app/data_registry/system/instruments/body_templates.json` — Template source
- `services/api/app/instrument_geometry/body/outlines.py` — Outline metadata source

---

*Instrument Dimension Ontology V1 — DRAFT FOR GOVERNANCE RECONCILIATION*
