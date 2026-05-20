# IBG Sandbox Semantic Classification

**Phase:** C1 — Collection (Complete)  
**Date:** 2026-05-18  
**Status:** Sandbox pressure surface analysis  
**Purpose:** Detailed classification of IBG semantic terms for C2 federation planning

---

## Executive Summary

IBG (Instrument Body Generator) represents the largest unfederated ontology incubation surface in the repository. With 72 terms across 12 vocabularies, IBG operates in a pre-governance sandbox state while exerting high semantic pressure on downstream systems.

This document classifies each IBG vocabulary by:
- **Sandbox status** — current governance state
- **Constitutional status** — ratification readiness
- **Semantic pressure** — impact on other systems
- **Federation priority** — C2 attention level

---

## 1. IBG Sandbox Overview

### 1.1 Overall Classification

| Metric | Value |
|--------|-------|
| Total vocabularies | 12 |
| Total terms | 72 |
| In lifecycle registry | 0 |
| In semantic registry | 0 |
| In authority chain | Partial (IBG → BOE declared, internals undeclared) |
| Constitutional status | Unratified |
| Semantic pressure | HIGH |

### 1.2 Pressure Surface Distribution

| Vocabulary Group | Terms | Pressure | Priority |
|------------------|-------|----------|----------|
| Body Grid Schema | 9 | MEDIUM | 3 |
| Zone Definitions | 15 | HIGH | 1 |
| Primitives | 20 | HIGH | 1 |
| Variant Grammar | 24 | HIGH | 1 |
| Morphology Harvest | 13 | MEDIUM-HIGH | 2 |

---

## 2. Body Grid Schema Vocabulary

**Source:** `body_grid_schema.py`  
**Sandbox Status:** sandbox/pre-governance  
**Constitutional Status:** Unratified  
**Semantic Pressure:** MEDIUM  
**Federation Priority:** 3

### 2.1 CoordinateSpace Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `raw_pixel` | Source coordinate space | LOW | Document |
| `raw_mm` | Calibrated coordinate space | MEDIUM | Consider registration |
| `bounding_box` | Normalized coordinate space | MEDIUM | Consider registration |
| `centerline_relative` | Canonical coordinate space | HIGH | Register in lifecycle |

**Recommendation:** `centerline_relative` should graduate to lifecycle registry as the canonical IBG coordinate system.

### 2.2 EvidenceSource Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `vectorizer_dxf` | Primary extraction source | HIGH | Register in semantic |
| `constraint_extractor` | Secondary extraction source | MEDIUM | Document |
| `photo_extraction` | Alternative source | LOW | Document |
| `user_input` | Manual override source | MEDIUM | Document |
| `spec_default` | Fallback source | LOW | Document |

**Recommendation:** `vectorizer_dxf` should be registered as the canonical IBG evidence source.

---

## 3. Zone Definitions Vocabulary

**Source:** `zones.py`  
**Sandbox Status:** sandbox/pre-governance  
**Constitutional Status:** Unratified  
**Semantic Pressure:** HIGH  
**Federation Priority:** 1 (CRITICAL)

### 3.1 ZoneId Enum

| Term | Y-Range | Semantic Role | Pressure | C2 Action |
|------|---------|---------------|----------|-----------|
| `centerline` | 0.0-1.0 | Reference axis | HIGH | Register as canonical |
| `upper_bout` | 0.50-0.75 | Secondary resonant mass | HIGH | Register |
| `waist` | 0.35-0.55 | Narrowest region | HIGH | Register |
| `lower_bout` | 0.08-0.40 | Primary resonant mass | HIGH | Register |
| `horn_left` | 0.60-0.85 | Bass horn projection | MEDIUM | Register |
| `horn_right` | 0.60-0.85 | Treble horn projection | MEDIUM | Register |
| `cutaway_left` | 0.55-0.80 | Bass cutaway (rare) | LOW | Document |
| `cutaway_right` | 0.55-0.80 | Treble cutaway | MEDIUM | Register |
| `neck_pocket` | 0.80-1.0 | Neck attachment | HIGH | Register |
| `bridge_region` | 0.15-0.35 | Bridge placement | HIGH | Register |
| `left_flank` | 0.0-1.0 | Full left contour | MEDIUM | Document |
| `right_flank` | 0.0-1.0 | Full right contour | MEDIUM | Document |
| `outer_boundary` | N/A | Fallback zone | LOW | Document |
| `butt_end` | 0.0-0.08 | Tail/end block | MEDIUM | Register |
| `shoulder` | 0.75-0.90 | Bout-to-neck transition | MEDIUM | Register |

### 3.2 Zone Y-Range Authority Issue

**Critical Finding:** Zone Y-ranges are hardcoded constants that are becoming implicit authority without governance review.

| Zone | Y-Range | Risk |
|------|---------|------|
| `lower_bout` | 0.08-0.40 | These values define body proportions |
| `waist` | 0.35-0.55 | Overlap with lower_bout intentional? |
| `upper_bout` | 0.50-0.75 | Overlap with waist intentional? |

**Recommendation:** Zone Y-ranges must be registered as governed constants with explicit overlap semantics.

---

## 4. Primitives Vocabulary

**Source:** `primitives.py`  
**Sandbox Status:** sandbox/pre-governance  
**Constitutional Status:** Unratified  
**Semantic Pressure:** HIGH  
**Federation Priority:** 1 (CRITICAL)

### 4.1 GeometryType Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `arc` | Curved segment | HIGH | Register |
| `line` | Straight segment | HIGH | Register |
| `spline` | Complex curve | MEDIUM | Register |
| `mixed` | Composite segment | LOW | Document |
| `unknown` | Fallback | LOW | Document |

### 4.2 CurvatureClass Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `convex_outward` | Bulging from center | HIGH | Register |
| `concave_inward` | Curving toward center | HIGH | Register |
| `straight` | No curvature | MEDIUM | Document |
| `inflection` | Direction change | MEDIUM | Document |
| `unknown` | Fallback | LOW | Document |

### 4.3 SlopeClass Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `ascending` | Moving neckward | MEDIUM | Document |
| `descending` | Moving buttward | MEDIUM | Document |
| `horizontal` | Constant Y | MEDIUM | Document |
| `vertical` | Constant X | MEDIUM | Document |
| `diagonal_pos` | Positive slope | LOW | Document |
| `diagonal_neg` | Negative slope | LOW | Document |

### 4.4 PrimitiveType Enum

| Term | Semantic Role | Pressure | C2 Action |
|------|---------------|----------|-----------|
| `arc_segment` | Basic arc | HIGH | Register |
| `line_segment` | Basic line | HIGH | Register |
| `diagonal_segment` | Angled line | MEDIUM | Document |
| `convex_bout` | Outward curve | HIGH | Register |
| `concave_waist` | Inward curve | HIGH | Register |
| `horn_projection` | Horn element | HIGH | Register |
| `cutaway_intrusion` | Cutaway element | HIGH | Register |
| `flat_slab_edge` | Flat edge | MEDIUM | Document |
| `offset_mass_region` | Asymmetric region | MEDIUM | Document |
| `centerline_anchor` | Center reference | HIGH | Register |
| `bridge_axis_anchor` | Bridge reference | HIGH | Register |
| `butt_termination` | Tail end | MEDIUM | Document |
| `neck_junction` | Neck transition | MEDIUM | Document |
| `shoulder_transition` | Shoulder curve | MEDIUM | Document |

---

## 5. Variant Grammar Vocabulary

**Source:** `variant_grammar.py`  
**Sandbox Status:** sandbox/pre-governance  
**Constitutional Status:** Unratified  
**Semantic Pressure:** HIGH  
**Federation Priority:** 1 (CRITICAL)

### 5.1 BodyMorphologyClass Enum

| Term | Description | Pressure | C2 Action |
|------|-------------|----------|-----------|
| `rounded_acoustic` | Dreadnought, jumbo, classical | HIGH | Register |
| `rounded_single_cut` | LP-style single cutaway | HIGH | Register |
| `double_cut` | SG, Stratocaster | HIGH | Register |
| `offset_waist` | Jazzmaster, Jaguar | HIGH | Register |
| `angular_wedge` | Explorer, Flying V | HIGH | Register |
| `slab_body` | Telecaster, basic solid | HIGH | Register |
| `carved_top` | Archtop | MEDIUM | Register |
| `semi_symmetric` | Minor asymmetry | MEDIUM | Document |
| `asymmetric` | Intentional asymmetry | MEDIUM | Document |
| `unknown` | Fallback | LOW | Document |

### 5.2 HornBehavior Enum

| Term | Pressure | C2 Action |
|------|----------|-----------|
| `symmetric_horns` | HIGH | Register |
| `single_cut_treble` | HIGH | Register |
| `single_cut_bass` | LOW | Document |
| `no_horns` | MEDIUM | Document |
| `pointed_horns` | MEDIUM | Document |
| `rounded_horns` | MEDIUM | Document |
| `angular_horns` | MEDIUM | Document |

### 5.3 WaistBehavior Enum

| Term | Pressure | C2 Action |
|------|----------|-----------|
| `deep_waist` | HIGH | Register |
| `moderate_waist` | MEDIUM | Document |
| `shallow_waist` | MEDIUM | Document |
| `suppressed_waist` | HIGH | Register |
| `offset_waist` | MEDIUM | Document |
| `angular_waist` | MEDIUM | Document |

### 5.4 BoutBehavior Enum

| Term | Pressure | C2 Action |
|------|----------|-----------|
| `rounded_bouts` | HIGH | Register |
| `angular_bouts` | HIGH | Register |
| `asymmetric_bouts` | MEDIUM | Document |
| `extended_lower` | MEDIUM | Document |
| `suppressed_upper` | MEDIUM | Document |

### 5.5 VARIANT_RULES Dictionary

**Critical Finding:** The `VARIANT_RULES` dictionary defines morphology classification rules that are becoming implicit authority.

| Rule ID | Risk Level |
|---------|------------|
| `rounded_single_cut` | HIGH — defines LP-style detection |
| `angular_wedge` | HIGH — defines Explorer-style detection |
| `offset_double_cut` | HIGH — defines Jazzmaster-style detection |
| `slab_body` | HIGH — defines Telecaster-style detection |
| `rounded_acoustic` | HIGH — defines acoustic body detection |
| `double_cut_horns` | HIGH — defines SG/Strat-style detection |

**Recommendation:** VARIANT_RULES must be registered as governed classification rules with explicit primitive requirements.

---

## 6. Morphology Harvest Vocabulary

**Source:** `morphology_harvest/schema.py`  
**Sandbox Status:** sandbox/staging  
**Constitutional Status:** Non-authoritative observational corpus  
**Semantic Pressure:** MEDIUM-HIGH  
**Federation Priority:** 2

### 6.1 ReviewStatus Enum

| Term | Pressure | C2 Action |
|------|----------|-----------|
| `pending_review` | MEDIUM | Document |
| `approved` | MEDIUM | Consider lifecycle |
| `approved_with_edits` | LOW | Document |
| `rejected` | LOW | Document |
| `deferred` | LOW | Document |

### 6.2 HarvestSource Enum

| Term | Pressure | C2 Action |
|------|----------|-----------|
| `vector_text` | MEDIUM | Document |
| `vector_no_text` | MEDIUM | Document |
| `raster_clean` | LOW | Document |
| `raster_noisy` | LOW | Document |
| `photo` | LOW | Document |
| `mixed` | LOW | Document |
| `unknown` | LOW | Document |

### 6.3 Term Normalization Mappings

**Critical Finding:** Hardcoded TERM_NORMALIZATIONS dictionary bypasses governance.

| Source Term | Normalized Term | Risk |
|-------------|-----------------|------|
| `lower_bout_mm` | `lower_bout_width_mm` | MEDIUM |
| `upper_bout_mm` | `upper_bout_width_mm` | MEDIUM |
| `waist_mm` | `waist_width_mm` | MEDIUM |
| `body_width_mm` | `lower_bout_width_mm` | HIGH — semantic assumption |
| `body_width_inches` | `lower_bout_width_inches` | HIGH — semantic assumption |

**Recommendation:** Term normalizations should be registered in alias registry with explicit mapping rationale.

---

## 7. Federation Priority Matrix

### 7.1 Priority 1: CRITICAL (C2 Immediate)

| Vocabulary | Reason |
|------------|--------|
| ZoneId | Defines morphology regions, Y-ranges hardening |
| PrimitiveType | Defines contour semantics, downstream dependencies |
| BodyMorphologyClass | Defines classification vocabulary |
| VARIANT_RULES | Defines classification behavior |

### 7.2 Priority 2: HIGH (C2 Phase 2)

| Vocabulary | Reason |
|------------|--------|
| HornBehavior | Defines horn classification |
| WaistBehavior | Defines waist classification |
| BoutBehavior | Defines bout classification |
| GeometryType | Fundamental geometry terms |
| CurvatureClass | Fundamental curvature terms |
| HarvestSource | Evidence classification |
| TERM_NORMALIZATIONS | Hardcoded semantic decisions |

### 7.3 Priority 3: MEDIUM (C2 Phase 3)

| Vocabulary | Reason |
|------------|--------|
| CoordinateSpace | Internal to Body Grid |
| EvidenceSource | Internal to Body Grid |
| SlopeClass | Internal to Primitives |
| ReviewStatus | Harvest-local |

---

## 8. C2 Federation Recommendations

### 8.1 Lifecycle Registry Additions

Terms to register in `lifecycle_registry.json`:

```json
{
  "centerline_relative": {
    "canonical_definition": "Centerline-relative normalized coordinate space for body geometry",
    "owner_domain": "IBG Body Grid",
    "classification": "CANONICAL"
  },
  "zone_boundary": {
    "canonical_definition": "Spatial partition boundary in normalized Y-space",
    "owner_domain": "IBG Zone System",
    "classification": "CANONICAL"
  }
}
```

### 8.2 Semantic Registry Additions

Terms to register in `semantic_registry.json`:

```json
{
  "body_zone": {
    "canonical_definition": "Named semantic region of an instrument body",
    "owner_domain": "IBG / Morphology Layer",
    "authority_tier": 2
  },
  "morphology_primitive": {
    "canonical_definition": "Classified contour segment with geometry and zone association",
    "owner_domain": "IBG / Morphology Layer",
    "authority_tier": 2
  },
  "variant_grammar": {
    "canonical_definition": "Behavior-based classification rules for body morphology",
    "owner_domain": "IBG / Morphology Layer",
    "authority_tier": 2
  }
}
```

### 8.3 Authority Chain Additions

Chain to add to `authority_chain_registry.json`:

```json
{
  "ibg_morphology_chain": {
    "description": "Authority flow for IBG morphology classification",
    "sequence": [
      "Blueprint/Photo",
      "Vectorizer",
      "Body Grid Evidence",
      "Zone Classification",
      "Primitive Detection",
      "Variant Grammar",
      "Morphology Class"
    ],
    "invariants": [
      "Zone boundaries are governed constants",
      "Variant rules are explicit, not implicit",
      "Classification is deterministic given primitives"
    ]
  }
}
```

---

## 9. Sandbox Graduation Criteria

### 9.1 Requirements for IBG Terms to Graduate

| Criterion | Requirement |
|-----------|-------------|
| Lifecycle registration | Term in lifecycle_registry.json |
| Semantic registration | Concept in semantic_registry.json |
| Authority chain | Term in declared authority chain |
| CI enforcement | Term validated by governance checks |
| Documentation | Term has prohibited_meanings field |

### 9.2 Graduation Sequence

1. **Zone system first** — ZoneId, zone boundaries, centerline_relative
2. **Primitive system second** — GeometryType, CurvatureClass, PrimitiveType
3. **Grammar system third** — BodyMorphologyClass, VARIANT_RULES
4. **Harvest system fourth** — TERM_NORMALIZATIONS, EvidenceSource

---

## 10. Related Documents

- `C1_GEOMETRY_TOPOLOGY_INVENTORY.md` — Full IBG term inventory
- `C1_STRATEGIC_FINDINGS.md` — Constitutional synthesis
- `docs/governance/ontology/lifecycle_registry.json` — Target registry
- `docs/governance/ontology/semantic_registry.json` — Target registry
- `docs/governance/ontology/authority_chain_registry.json` — Target registry

---

## Sandbox Classification Summary

| Status | Count | Description |
|--------|-------|-------------|
| **sandbox/pre-governance** | 59 | Not in any registry, operating as de-facto authority |
| **sandbox/staging** | 13 | Harvest terms, non-authoritative observational |
| **graduated** | 0 | None yet registered in governance infrastructure |

IBG represents unfederated ontology emergence. C2 must federate these terms without collapsing their semantic richness.
