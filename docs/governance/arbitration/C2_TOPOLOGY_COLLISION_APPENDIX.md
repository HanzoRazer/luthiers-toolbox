# C2 Topology Collision Appendix

```
C2-B — CONSTITUTIONAL ARBITRATION PHASE
TOPOLOGY COLLISION DEEPENING
SEMANTIC NON-EQUIVALENCE PRESERVATION
```

**Phase:** C2-B  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** Appendix Complete — Supporting Document

---

## 1. Purpose

This appendix deepens collision analysis for topology namespace arbitration.

It provides:
- Detailed collision evidence
- Semantic divergence mapping
- Authority candidate analysis
- Non-equivalence preservation rationale

---

## 2. COLL-G001: Topology Semantic Divergence

### 2.1 Collision Evidence

| Field | Value |
|-------|-------|
| collision_id | COLL-G001 |
| collision_type | overload |
| risk_level | High |
| do_not_fix_in_c1 | true (frozen) |
| c2_status | Decomposition proposed |

### 2.2 Location Evidence

**MRP/7M Definition:**
```
Location: app/cam/canonical_ontology_registry.py:472
Term: topology
Definition: "Semantic structure describing spatial relationships, 
            regions, and connectivity under MRP governance."
Governance tier: 2
Canonical contracts: TopologyContract, RegionContract
```

**CAM Definition:**
```
Location: app/cam/topology_builder/contracts.py:33
Term: TopologyBuilder usage
Meaning: 3D shell construction with G0/G1/G2 continuity
Related: ContinuityLevel, ShellType, TopologyTier
```

### 2.3 Semantic Divergence Analysis

| Aspect | MRP Topology | CAM Topology |
|--------|--------------|--------------|
| Domain | Governance | Manufacturing |
| Purpose | Spatial structure classification | 3D shell construction |
| Primitives | Regions, connectivity | Surfaces, junctions |
| Continuity | Not applicable | G0/G1/G2 core concept |
| Authority | Constitutional | Operational |

### 2.4 Why These Are NOT Equivalent

```
MRP topology describes WHAT spatial structures exist.
CAM topology describes HOW surfaces connect geometrically.
```

Collapsing them would:
- Merge governance semantics into manufacturing
- Conflate spatial classification with geometric construction
- Create false authority over manufacturing decisions

### 2.5 Decomposition Proposal

| Namespace | Domain | Purpose |
|-----------|--------|---------|
| `morphology_topology` | MRP | Spatial structure relationships |
| `surface_topology` | CAM | Geometric surface continuity |
| `manufacturing_topology` | CAM | Shell construction semantics |

---

## 3. COLL-G002: Morphology Authority Gap

### 3.1 Collision Evidence

| Field | Value |
|-------|-------|
| collision_id | COLL-G002 |
| collision_type | authority_overlap |
| risk_level | High |
| do_not_fix_in_c1 | true (frozen) |
| c2_status | Gap documented, containment proposed |

### 3.2 Location Evidence

**7M Registration:**
```
Location: app/cam/canonical_ontology_registry.py:392
Term: morphology
Definition: "Semantic structure describing instrument body shape, 
            regions, and topology under MRP governance."
Governance tier: 2
Lifecycle semantics: draft, validated, canonical
```

**IBG Implementation:**
```
Location: app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24
Type: BodyMorphologyClass
Values: rounded_acoustic, rounded_single_cut, double_cut, 
        offset_waist, angular_wedge, slab_body, carved_top, 
        semi_symmetric, asymmetric, unknown

Location: app/instrument_geometry/body/ibg/body_grid/morphology_descriptor.py:53
Type: MorphologyDescriptor
Purpose: Complete morphology classification object

Location: app/instrument_geometry/body/ibg/body_grid/primitives.py:72
Type: MorphologyPrimitive
Purpose: Classification primitive type
```

### 3.3 Gap Analysis

| System | Authority Claim | Registration Status |
|--------|-----------------|---------------------|
| MRP 7M | Governance term owner | Registered |
| IBG | Implementation | NOT registered as 7N consumer |

```
Gap: IBG implements 7M morphology concept without 7N consumer registration.
```

### 3.4 Authority Classification

| IBG Component | Constitutional Status |
|---------------|----------------------|
| BodyMorphologyClass | Sandbox implementation of 7M morphology |
| MorphologyDescriptor | Sandbox classification object |
| MorphologyPrimitive | Sandbox primitive vocabulary |

### 3.5 Containment Proposal

```
IBG vocabulary receives ibg_morphology_* prefix.
IBG remains sandbox-contained.
No promotion to governance authority.
Future 7N registration possible but not required.
```

---

## 4. COLL-G003: Zone vs Region Vocabulary

### 4.1 Collision Evidence

| Field | Value |
|-------|-------|
| collision_id | COLL-G003 |
| collision_type | geometry_ambiguity |
| risk_level | Medium |
| do_not_fix_in_c1 | true (frozen) |
| c2_status | Namespace decomposition proposed |

### 4.2 Location Evidence

**IBG Zones:**
```
Location: app/instrument_geometry/body/ibg/body_grid/zones.py:24
Type: ZoneId
Count: 15 zones
Values: centerline, upper_bout, waist, lower_bout, horn_left, 
        horn_right, cutaway_left, cutaway_right, neck_pocket, 
        bridge_region, butt_end, shoulder_left, shoulder_right, 
        apex_upper, apex_lower
```

**7M Regions:**
```
Location: app/cam/canonical_ontology_registry.py:480
Type: RegionContract
Purpose: Generic spatial region contract under MRP governance
```

### 4.3 Semantic Comparison

| Aspect | IBG ZoneId | MRP RegionContract |
|--------|------------|-------------------|
| Specificity | Guitar body-specific | Generic/abstract |
| Count | 15 named zones | Undefined |
| Authority | Sandbox | Governance |
| Purpose | Morphology classification | Spatial abstraction |

### 4.4 Non-Equivalence Rationale

```
IBG zones are instrument-specific body partitions.
MRP regions are abstract spatial contracts.
These serve different constitutional purposes.
```

### 4.5 Namespace Decomposition

| Namespace | Purpose | Constitutional Status |
|-----------|---------|----------------------|
| `morphology_zone` | IBG body partition | Sandbox (advisory) |
| `spatial_region` | MRP region contract | Governance |
| `operational_region` | CAM processing area | Runtime |

---

## 5. COLL-G005: Primitive Vocabulary Ungoverned

### 5.1 Collision Evidence

| Field | Value |
|-------|-------|
| collision_id | COLL-G005 |
| collision_type | runtime_inference |
| risk_level | Medium |
| do_not_fix_in_c1 | true (frozen) |
| c2_status | Containment proposed |

### 5.2 Location Evidence

```
Location: app/instrument_geometry/body/ibg/body_grid/primitives.py:53
Type: PrimitiveType
Count: 14 types
Values: arc_segment, line_segment, convex_bout, concave_waist, 
        horn_projection, cutaway_intrusion, transition_curve, 
        blend_fillet, shoulder_curve, neck_joint_curve, end_block, 
        apex_point, inflection_point, tangent_point
```

### 5.3 Authority Risk

```
IBG primitives create binding classification vocabulary.
No 7M registration exists for primitive as a term.
Downstream systems may consume as authoritative.
```

### 5.4 Pressure Analysis

| Consumer | Risk | Mechanism |
|----------|------|-----------|
| Corpus Builder | HIGH | Training data uses primitives |
| Export Bridge | MEDIUM | IBGMorphologyExtension propagates |
| Visualization | LOW | UI renders primitive labels |

### 5.5 Containment Proposal

| Namespace | Purpose | Status |
|-----------|---------|--------|
| `morphology_primitive` | IBG classification primitive | Sandbox (advisory) |
| `geometry_primitive` | Basic geometric element | General |

---

## 6. COLL-T3-001: Partition Overload

### 6.1 Terminal 3 Review Addition

| Field | Value |
|-------|-------|
| collision_id | COLL-T3-001 |
| collision_type | overload |
| risk_level | Medium |
| source | Terminal 3 topology review |
| c2_status | Namespace decomposition proposed |

### 6.2 Usage Analysis

| Usage | Domain | Meaning |
|-------|--------|---------|
| partition (IBG) | Body Grid | Zone boundary demarcation |
| partition (CAM) | Topology Builder | Shell segmentation for manufacturing |
| partition (governance) | Domain governance | Semantic authority separation |

### 6.3 Namespace Decomposition

| Namespace | Purpose |
|-----------|---------|
| `zone_partition` | IBG zone demarcation |
| `shell_partition` | CAM shell segmentation |
| `authority_partition` | Governance domain separation |

---

## 7. COLL-T3-002: Boundary Overload

### 7.1 Terminal 3 Review Addition

| Field | Value |
|-------|-------|
| collision_id | COLL-T3-002 |
| collision_type | overload |
| risk_level | Medium |
| source | Terminal 3 topology review |
| c2_status | Namespace decomposition proposed |

### 7.2 Usage Analysis

| Usage | Domain | Meaning |
|-------|--------|---------|
| boundary (geometric) | CAM | Geometric edge/contour for manufacturing |
| boundary (semantic) | Governance | Authority boundary between domains |
| boundary (zone) | IBG | Zone demarcation line |

### 7.3 Namespace Decomposition

| Namespace | Purpose |
|-----------|---------|
| `geometric_boundary` | CAM edge/contour |
| `authority_boundary` | Governance domain boundary |
| `zone_boundary` | IBG zone demarcation |

---

## 8. Continuity Independence Analysis

### 8.1 Why Continuity Is Independent

```
Continuity semantics answers: "How smooth are geometric junctions?"
Topology semantics answers: "What structures exist and how are they connected?"
```

These are orthogonal questions.

### 8.2 Continuity Vocabulary

| Term | Meaning | Domain |
|------|---------|--------|
| G0 | Positional continuity | CAM |
| G1 | Tangent continuity | CAM |
| G2 | Curvature continuity | CAM |

### 8.3 Independence Evidence

```
Location: app/cam/topology_builder/contracts.py:16
Type: ContinuityLevel
Values: G0, G1, G2
Purpose: Manufacturing junction quality specification
```

Continuity is:
- Manufacturing-specific
- Junction-focused
- Quality metric

Topology is:
- Structure-focused
- Connection-focused
- Existence assertion

### 8.4 Namespace Proposal

| Namespace | Purpose |
|-----------|---------|
| `manufacturing_continuity` | Junction quality specification |

This separates continuity from topology as independent semantic layer.

---

## 9. Cross-Collision Dependency Map

```
COLL-G001 (topology)
    │
    ├── COLL-G002 (morphology) ─── IBG pressure
    │       │
    │       └── COLL-G005 (primitive) ─── IBG vocabulary
    │
    ├── COLL-G003 (zone/region) ─── IBG spatial
    │
    ├── COLL-T3-001 (partition) ─── cross-domain
    │
    └── COLL-T3-002 (boundary) ─── cross-domain
```

All collisions trace back to topology overloading.

---

## 10. IBG Pressure Summary

### 10.1 Total IBG Vocabulary Pressure

| Category | Terms | Constitutional Status |
|----------|-------|----------------------|
| Morphology classes | 10 | Sandbox |
| Zones | 15 | Sandbox |
| Primitives | 14 | Sandbox |
| Behaviors (horn, waist, bout) | 18 | Sandbox |
| Schema types | 4 | Sandbox |

**Total:** 61+ ungoverned terms exerting pressure on governance.

### 10.2 Containment Doctrine

```
All IBG vocabulary is advisory_only conceptually.
All IBG vocabulary is sandbox-contained operationally.
All IBG vocabulary is ungoverned constitutionally.
```

### 10.3 Future Federation Path

If IBG vocabulary graduates to governance:
1. Register IBG as 7N consumer
2. Map IBG vocabulary to 7M terms
3. Establish consumption contracts
4. Document authority boundaries

This is NOT C2-B scope. Deferred to C2-C.

---

## 11. Related Documents

### Primary Document

- `C2_TOPOLOGY_NAMESPACE_ARBITRATION.md` — Main decomposition

### C2-A Foundation

- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Geometry collisions

### C1 Evidence

- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md`
- `geometry_morphology_topology/SEMANTIC_INVENTORY.md`

---

*C2-B Topology Collision Appendix — Evidence Deepening Complete*
