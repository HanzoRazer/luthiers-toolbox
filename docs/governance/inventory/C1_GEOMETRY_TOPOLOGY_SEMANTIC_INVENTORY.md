# C1 Terminal 3: Geometry/Morphology/Topology Semantic Inventory

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Scope**: Geometry semantic layers, morphology classification terms, topology continuity semantics, primitive vocabulary, visualization/runtime geometry boundaries

---

## 1. IBG Body Grid Vocabulary (Sandbox / Pre-Governance)

### Status Note

The IBG Body Grid system (`app/instrument_geometry/body/ibg/body_grid/`) is **untracked** and represents sandbox vocabulary that creates **de facto semantic authority** without 7M registration or 7N consumption governance.

This vocabulary is actively used but exists outside the governance chain established by 7M/7N/7O.

---

### 1.1 Geometry Type Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/primitives.py:25-31`

| Term | Value | Meaning | Registered in 7M? |
|------|-------|---------|-------------------|
| `ARC` | "arc" | Curved contour segment | No |
| `LINE` | "line" | Straight contour segment | No |
| `SPLINE` | "spline" | Freeform curve | No |
| `MIXED` | "mixed" | Combined geometry types | No |
| `UNKNOWN` | "unknown" | Unclassified geometry | No |

**Authority Gap**: GeometryType creates foundational geometry vocabulary without governance registration.

---

### 1.2 Curvature Class Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/primitives.py:34-40`

| Term | Value | Meaning | Registered in 7M? |
|------|-------|---------|-------------------|
| `CONVEX_OUTWARD` | "convex_outward" | Bulging away from body center | No |
| `CONCAVE_INWARD` | "concave_inward" | Curving toward body center | No |
| `STRAIGHT` | "straight" | No curvature | No |
| `INFLECTION` | "inflection" | Direction change | No |
| `UNKNOWN` | "unknown" | Unclassified curvature | No |

**Authority Gap**: Defines how curvature is classified for morphology reasoning.

---

### 1.3 Primitive Type Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/primitives.py:53-68`

| Term | Value | Semantic Role |
|------|-------|---------------|
| `ARC_SEGMENT` | "arc_segment" | Generic arc primitive |
| `LINE_SEGMENT` | "line_segment" | Generic line primitive |
| `DIAGONAL_SEGMENT` | "diagonal_segment" | Angled line |
| `CONVEX_BOUT` | "convex_bout" | Bout region with outward curve |
| `CONCAVE_WAIST` | "concave_waist" | Waist region with inward curve |
| `HORN_PROJECTION` | "horn_projection" | Upper bout horn |
| `CUTAWAY_INTRUSION` | "cutaway_intrusion" | Cutaway access region |
| `FLAT_SLAB_EDGE` | "flat_slab_edge" | Telecaster-style flat edge |
| `OFFSET_MASS_REGION` | "offset_mass_region" | Asymmetric mass distribution |
| `CENTERLINE_ANCHOR` | "centerline_anchor" | Reference point on centerline |
| `BRIDGE_AXIS_ANCHOR` | "bridge_axis_anchor" | Bridge alignment reference |
| `BUTT_TERMINATION` | "butt_termination" | Tail end of body |
| `NECK_JUNCTION` | "neck_junction" | Neck attachment point |
| `SHOULDER_TRANSITION` | "shoulder_transition" | Upper bout to neck transition |

**Registration Status**: None registered in 7M
**Collision Risk**: High — creates parallel morphology vocabulary outside 7M `morphology` term

---

### 1.4 Body Morphology Class Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24-35`

| Term | Value | Meaning |
|------|-------|---------|
| `ROUNDED_ACOUSTIC` | "rounded_acoustic" | Dreadnought, jumbo, classical |
| `ROUNDED_SINGLE_CUT` | "rounded_single_cut" | LP-style single cutaway |
| `DOUBLE_CUT` | "double_cut" | SG-style, Stratocaster |
| `OFFSET_WAIST` | "offset_waist" | Jazzmaster, Jaguar, Mustang |
| `ANGULAR_WEDGE` | "angular_wedge" | Explorer, Flying V |
| `SLAB_BODY` | "slab_body" | Telecaster, basic solid body |
| `CARVED_TOP` | "carved_top" | Archtop acoustic/electric |
| `SEMI_SYMMETRIC` | "semi_symmetric" | Mostly symmetric with minor asymmetry |
| `ASYMMETRIC` | "asymmetric" | Intentionally asymmetric |
| `UNKNOWN` | "unknown" | Unclassified |

**Collision with 7M**: 7M defines `morphology` as:
> "Semantic structure describing instrument body shape, regions, and topology under MRP governance."

IBG BodyMorphologyClass **implements** this semantic concept but is **not governed** by 7M.

---

### 1.5 Zone Definition Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/zones.py:24-40`

| Zone ID | Y Range | Semantic Role |
|---------|---------|---------------|
| `CENTERLINE` | 0.0-1.0 | Body axis of reference |
| `UPPER_BOUT` | 0.50-0.75 | Secondary resonant mass |
| `WAIST` | 0.35-0.55 | Narrowest body region |
| `LOWER_BOUT` | 0.08-0.40 | Widest body region, primary mass |
| `HORN_LEFT` | 0.60-0.85 | Left horn projection |
| `HORN_RIGHT` | 0.60-0.85 | Right horn projection |
| `CUTAWAY_LEFT` | 0.55-0.80 | Left cutaway (rare) |
| `CUTAWAY_RIGHT` | 0.55-0.80 | Right cutaway (common) |
| `NECK_POCKET` | 0.80-1.0 | Neck attachment region |
| `BRIDGE_REGION` | 0.15-0.35 | Bridge placement |
| `LEFT_FLANK` | 0.0-1.0 | Complete left contour |
| `RIGHT_FLANK` | 0.0-1.0 | Complete right contour |
| `OUTER_BOUNDARY` | — | Fallback zone |
| `BUTT_END` | 0.0-0.08 | Tail/end block region |
| `SHOULDER` | 0.75-0.90 | Upper bout to neck transition |

**Authority Gap**: Zone definitions create spatial region semantics without governance.

---

### 1.6 Behavior Classification Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:38-66`

#### Horn Behavior (7 types)
| Term | Meaning |
|------|---------|
| `SYMMETRIC_HORNS` | Equal horns both sides |
| `SINGLE_CUT_TREBLE` | Cutaway on treble side only |
| `SINGLE_CUT_BASS` | Cutaway on bass side (rare) |
| `NO_HORNS` | Rounded upper bout, no horns |
| `POINTED_HORNS` | Sharp pointed horns |
| `ROUNDED_HORNS` | Soft rounded horns |
| `ANGULAR_HORNS` | Angular/wedge horns |

#### Waist Behavior (6 types)
| Term | Meaning |
|------|---------|
| `DEEP_WAIST` | Classical-style deep waist |
| `MODERATE_WAIST` | Standard acoustic waist |
| `SHALLOW_WAIST` | Dreadnought-style |
| `SUPPRESSED_WAIST` | Explorer, V-style (minimal) |
| `OFFSET_WAIST` | Asymmetric waist position |
| `ANGULAR_WAIST` | Sharp angles at waist |

#### Bout Behavior (5 types)
| Term | Meaning |
|------|---------|
| `ROUNDED_BOUTS` | Smooth curved bouts |
| `ANGULAR_BOUTS` | Sharp angled bouts |
| `ASYMMETRIC_BOUTS` | Different left/right |
| `EXTENDED_LOWER` | Extra-wide lower bout |
| `SUPPRESSED_UPPER` | Small upper bout (SG-style) |

**Collision Risk**: Medium — these are sub-classifications of 7M `morphology` concepts.

---

### 1.7 Evidence and Coordinate Vocabulary

**Source**: `app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py:23-38`

#### CoordinateSpace
| Term | Meaning |
|------|---------|
| `RAW_PIXEL` | Pixel coordinates |
| `RAW_MM` | Millimeter coordinates |
| `BOUNDING_BOX` | Normalized to bounding box |
| `CENTERLINE_RELATIVE` | Normalized to centerline |

#### EvidenceSource
| Term | Meaning |
|------|---------|
| `VECTORIZER_DXF` | From blueprint vectorizer |
| `CONSTRAINT_EXTRACTOR` | From constraint extraction |
| `PHOTO_EXTRACTION` | From photo analysis |
| `USER_INPUT` | Manual entry |
| `SPEC_DEFAULT` | From instrument specification |

**Registration Status**: None registered in 7M.

---

## 2. CAM Topology Builder Vocabulary

### 2.1 Topology Continuity Vocabulary

**Source**: `app/cam/topology_builder/contracts.py:16-22`

| Term | Value | Meaning | Registered in 7M? |
|------|-------|---------|-------------------|
| `G0` | "G0" | Positional continuity (touching) | No |
| `G1` | "G1" | Tangent continuity (smooth) | No |
| `G2` | "G2" | Curvature continuity (very smooth) | No |

**Semantic Context**: Geometric surface junction quality, not governance topology.

---

### 2.2 Shell Type Vocabulary

**Source**: `app/cam/topology_builder/contracts.py:25-31`

| Term | Value | Meaning |
|------|-------|---------|
| `FLAT_EXTRUSION` | "flat_extrusion" | Simple extrusion from profile |
| `LOFTED` | "lofted" | Loft between profiles |
| `SWEPT` | "swept" | Sweep along path |
| `COMPOSITE` | "composite" | Multiple shells joined |

**Registration Status**: Not registered in 7M.

---

### 2.3 Topology Tier Vocabulary

**Source**: `app/cam/topology_builder/contracts.py:34-38`

| Term | Value | Meaning |
|------|-------|---------|
| `PROTOTYPE` | "PROTOTYPE" | G0 acceptable, warnings allowed |
| `PRODUCTION` | "PRODUCTION" | G1 required, strict validation |

**Collision with 7M**: Uses "tier" but with different semantics than governance tiers.

---

## 3. 7M Registered Geometry/Topology Terms

### 3.1 `morphology` — Registered

**Source**: `app/cam/canonical_ontology_registry.py:392-407`

```python
{
    "term": "morphology",
    "canonical_definition": (
        "Semantic structure describing instrument body shape, regions, "
        "and topology under MRP governance."
    ),
    "owning_domain": "MRP",
    "owning_governance_tier": 2,
    "canonical_contracts": ["MorphologyContract", "TopologyContract"],
    "prohibited_reinterpretations": [
        "runtime_computed_morphology",
        "automatic_shape_inference",
    ],
    "lifecycle_semantics": ["draft", "validated", "canonical"],
    "aliases": ["body_morphology", "instrument_morphology"],
}
```

**IBG Collision**: IBG Body Grid directly implements "body_morphology" vocabulary without consuming this 7M registration.

---

### 3.2 `topology` — Registered

**Source**: `app/cam/canonical_ontology_registry.py:472-488`

```python
{
    "term": "topology",
    "canonical_definition": (
        "Semantic structure describing spatial relationships, regions, "
        "and connectivity under MRP governance."
    ),
    "owning_domain": "MRP",
    "owning_governance_tier": 2,
    "canonical_contracts": ["TopologyContract", "RegionContract"],
    "prohibited_reinterpretations": [
        "runtime_topology_inference",
        "automatic_region_detection",
    ],
    "lifecycle_semantics": ["draft", "validated", "canonical"],
    "aliases": ["body_topology", "spatial_topology"],
}
```

**CAM Topology Builder Collision**: Uses "topology" for 3D shell construction (G0/G1/G2 continuity), not MRP spatial relationships.

---

### 3.3 `geometry_authority` — Referenced but Not Found

**Evidence**: `app/cam/runtime/dispatcher.py:208` calls `runtime.resolve_geometry(intent)` without checking `geometry_authority`.

The 7M registry appears to define geometry-related terms, but the specific `geometry_authority` term was not found in the scanned portion.

---

## 4. Semantic Collisions

### COLL-G001: Topology Semantic Divergence

**Term**: `topology`

**Locations**:
- `app/cam/canonical_ontology_registry.py:472` — 7M definition: "spatial relationships, regions, connectivity under MRP governance"
- `app/cam/topology_builder/contracts.py:33` — CAM usage: 3D shell construction with G0/G1/G2 continuity

**Collision Type**: Semantic overloading

**Severity**: High — Same term means fundamentally different things:
1. **7M/MRP**: Semantic spatial structure for governance
2. **CAM**: Geometric surface continuity for manufacturing

**C2 Candidate**: Distinguish `morphology_topology` (MRP) vs `surface_topology` or `manufacturing_topology` (CAM).

---

### COLL-G002: Morphology Authority Gap

**Term**: `morphology`

**Locations**:
- `app/cam/canonical_ontology_registry.py:392` — 7M registered term
- `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24` — `BodyMorphologyClass`
- `app/instrument_geometry/body/ibg/body_grid/morphology_descriptor.py:53` — `MorphologyDescriptor`

**Collision Type**: De facto authority without registration

**Severity**: High — IBG creates complete morphology vocabulary that:
1. Implements 7M `morphology` semantics
2. Is NOT registered as 7N consumer
3. Creates binding classification authority

**C2 Candidate**: Register IBG as 7N consumer with consumed_terms: `["morphology", "topology"]`

---

### COLL-G003: Zone vs Region Vocabulary

**Term**: Zone definitions

**Locations**:
- `app/instrument_geometry/body/ibg/body_grid/zones.py:24` — `ZoneId` (15 zones)
- `app/cam/canonical_ontology_registry.py:480` — `RegionContract` (7M topology contract)

**Collision Type**: Parallel spatial vocabulary

**Severity**: Medium — IBG zones and 7M regions describe the same concept (spatial areas of body):
- IBG: `LOWER_BOUT`, `WAIST`, `UPPER_BOUT`, etc.
- 7M: Generic `RegionContract` without specific region names

**C2 Candidate**: Either:
1. Register zone vocabulary as 7M regions
2. Or document IBG zones as implementation detail of 7M regions

---

### COLL-G004: Tier Semantic Collision

**Term**: `tier`

**Locations**:
- `app/cam/topology_builder/contracts.py:34` — `TopologyTier`: `PROTOTYPE`, `PRODUCTION`
- `app/cam/canonical_ontology_registry.py` — Governance tiers: 1, 2, etc.
- `docs/governance/` — Execution tiers: `precommit`, `ci`, `nightly`, `manual`

**Collision Type**: Semantic overloading

**Severity**: Medium — "Tier" means:
1. **Topology**: Runtime strictness level (PROTOTYPE vs PRODUCTION)
2. **Governance**: Authority level (Tier 1 structural, Tier 2 domain)
3. **Execution**: Check timing (precommit, ci, nightly)

**C2 Candidate**: Prefix tier usages: `runtime_tier`, `governance_tier`, `execution_tier`

---

### COLL-G005: Primitive Vocabulary Ungoverned

**Term**: `primitive`

**Locations**:
- `app/instrument_geometry/body/ibg/body_grid/primitives.py:53` — `PrimitiveType` (14 types)
- `app/instrument_geometry/body/ibg/body_grid/primitives.py:72` — `MorphologyPrimitive`

**Collision Type**: Unregistered domain vocabulary

**Severity**: Medium — IBG defines 14 primitive types that form the foundation of morphology reasoning:
- These primitives are used to classify body shapes
- They create semantic authority without governance
- No 7M registration exists for `primitive` as a term

**C2 Candidate**: Register `morphology_primitive` in 7M with lifecycle semantics.

---

## 5. Authority Gaps

### High Priority

| Gap | Risk | Location |
|-----|------|----------|
| IBG morphology outside 7N | De facto authority without consumption registration | `body_grid/` |
| CAM topology != MRP topology | Semantic confusion, wrong authority assumptions | `topology_builder/` |
| Zone vocabulary ungoverned | Spatial region semantics without registration | `zones.py` |

### Medium Priority

| Gap | Risk | Location |
|-----|------|----------|
| Primitive vocabulary unregistered | Classification authority without governance | `primitives.py` |
| Behavior classifications unregistered | Variant grammar creates ungoverned semantics | `variant_grammar.py` |
| Continuity vocabulary unregistered | G0/G1/G2 semantics without governance | `topology_builder/contracts.py` |

### Low Priority

| Gap | Risk | Location |
|-----|------|----------|
| EvidenceSource vocabulary | Source tracking without registration | `body_grid_schema.py` |
| CoordinateSpace vocabulary | Coordinate system semantics | `body_grid_schema.py` |

---

## 6. Cross-Reference with 7M Registry

### 6.1 Terms Used but Not Registered

| Term | Domain | Usage Location | Risk |
|------|--------|----------------|------|
| `GeometryType` | IBG | primitives.py | Medium |
| `CurvatureClass` | IBG | primitives.py | Medium |
| `PrimitiveType` | IBG | primitives.py | Medium |
| `BodyMorphologyClass` | IBG | variant_grammar.py | High |
| `ZoneId` | IBG | zones.py | High |
| `ContinuityLevel` | CAM | contracts.py | Medium |
| `ShellType` | CAM | contracts.py | Low |
| `TopologyTier` | CAM | contracts.py | Medium |

### 6.2 Terms Registered and Used

| 7M Term | Implementation | Consistent? |
|---------|----------------|-------------|
| `morphology` | IBG BodyMorphologyClass, MorphologyDescriptor | No — not consumed via 7N |
| `topology` | CAM TopologyBuilder | No — different semantics |

### 6.3 Terms Registered but Not Observed

| 7M Term | Expected Usage | Observed? |
|---------|----------------|-----------|
| `MorphologyContract` | IBG should implement | No |
| `TopologyContract` | IBG/CAM should implement | No |
| `RegionContract` | Zone system should implement | No |

---

## 7. IBG Sandbox Classification

### Sandbox Status

The IBG Body Grid system should be flagged as **sandbox / pre-governance vocabulary**:

1. **Untracked files**: `services/api/app/instrument_geometry/body/ibg/body_grid/` is untracked in git
2. **No 7N registration**: Not registered as runtime semantic consumer
3. **Creates authority**: Defines binding morphology classification vocabulary
4. **Active usage**: Used by MorphologyAnalyzer to classify bodies

### Recommended Governance Path

When IBG exits sandbox:

1. Register IBG as 7N consumer with consumed_terms: `["morphology", "topology"]`
2. Register zone vocabulary in 7M under `morphology` domain
3. Register primitive types in 7M with lifecycle semantics
4. Validate that IBG's morphology semantics match 7M canonical definition

---

## 8. Summary Statistics

### Vocabulary Counts

| Category | Count |
|----------|-------|
| IBG geometry types | 5 |
| IBG curvature classes | 5 |
| IBG primitive types | 14 |
| IBG morphology classes | 10 |
| IBG zone definitions | 15 |
| IBG behavior classifications | 18 |
| CAM topology types | 8 |
| **Total unregistered terms** | **75** |

### Collision Summary

| Severity | Count |
|----------|-------|
| High | 2 |
| Medium | 3 |
| Low | 0 |
| **Total** | **5** |

---

## 9. Recommended C2 Actions (Not Implemented in C1)

1. **Register IBG as 7N consumer** with consumed_terms: `["morphology", "topology"]`
2. **Distinguish topology semantics**: `morphology_topology` (MRP) vs `surface_topology` (CAM)
3. **Register zone vocabulary** in 7M under morphology domain
4. **Register primitive types** in 7M with lifecycle semantics
5. **Prefix tier usages** to distinguish runtime_tier vs governance_tier
6. **Document IBG sandbox status** explicitly in IBG module

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This inventory is evidence for C2 reconciliation.
