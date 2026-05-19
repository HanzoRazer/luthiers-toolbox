# C2 Geometry Namespace Collisions

```
C2-A — CONSTITUTIONAL ARBITRATION PHASE
GEOMETRY AUTHORITY DECOMPOSITION
NAMESPACE COLLISION DECOMPOSITION
```

**Phase:** C2-A  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** Decomposition Complete — Awaiting Arbitration

---

## 1. Authority Statement

This document decomposes overloaded geometry semantics for arbitration.

This document does NOT:
- Choose winners
- Normalize globally
- Federate vocabulary
- Mandate renaming
- Resolve collisions

This document DOES:
- Classify collision types
- Map collision domains
- Decompose semantic layers
- Identify authority candidates
- Prepare arbitration surfaces

---

## 2. Collision Inventory

### C1 Source Collisions

| Collision ID | Term | Risk Level | Source |
|--------------|------|------------|--------|
| COLL-G001 | topology | High | geometry_morphology_topology |
| COLL-G002 | morphology | High | geometry_morphology_topology |
| COLL-G003 | zone/region | Medium | geometry_morphology_topology |
| COLL-G004 | tier | Medium | geometry_morphology_topology |
| COLL-G005 | primitive | Medium | geometry_morphology_topology |
| COLL-E001 | serialization | Medium | export_serialization |
| COLL-E002 | IBG propagation | High | export_serialization |
| COL-ACOU-001 | confidence | Medium | acoustics_observational |

### C2 Terminal 3 Review Additions

| Collision ID | Term | Risk Level | Source |
|--------------|------|------------|--------|
| COLL-T3-001 | partition | Medium | Terminal 3 topology review |
| COLL-T3-002 | boundary | Medium | Terminal 3 topology review |

---

## 3. Collision Decompositions

### COLLISION: geometry

**Status:** Overloaded across layers

| Usage | Domain | Meaning | Layer |
|-------|--------|---------|-------|
| geometry (canonical) | MRP | Dimensional truth | authoritative_geometry |
| geometry (runtime) | CAM | Execution representation | operational_geometry |
| geometry (derived) | Acoustics | Computed values | derived_geometry |
| geometry (presentation) | UI | Display values | presentation_geometry |
| geometry (serialized) | Export | Format encoding | serialized_geometry |
| geometry (IBG) | IBG | Pre-governance shapes | sandbox_geometry |

**Decomposition Proposal:**

| Namespace | Purpose | Authority |
|-----------|---------|-----------|
| `authoritative_geometry` | Canonical definition | Owner |
| `operational_geometry` | Runtime consumption | Consumer |
| `derived_geometry` | Computed interpretation | Non-authoritative |
| `presentation_geometry` | Display transform | Non-authoritative |
| `serialized_geometry` | Export encoding | Non-authoritative |
| `sandbox_geometry` | Pre-governance | Contained |

**C2 Candidate:** Layer-prefixed geometry references where semantic distinction required.

---

### COLLISION: topology

**Source:** COLL-G001

**Status:** Semantic divergence — HIGH RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| topology (MRP) | 7M Registry | Spatial relationships, regions, connectivity | `canonical_ontology_registry.py:472` |
| topology (CAM) | Topology Builder | 3D shell construction, G0/G1/G2 continuity | `topology_builder/contracts.py:33` |

**Decomposition Proposal:**

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `morphology_topology` | Spatial region relationships under MRP governance | MRP |
| `surface_topology` | Geometric surface continuity (G0/G1/G2) | CAM |
| `manufacturing_topology` | Shell construction for CAM | CAM |

**C2 Candidate:** Separate terms for MRP spatial semantics vs CAM geometric continuity.

---

### COLLISION: zone vs region

**Source:** COLL-G003

**Status:** Vocabulary overlap — MEDIUM RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| ZoneId | IBG | 15 named body zones | `zones.py:24` |
| RegionContract | 7M | Generic spatial region contract | `canonical_ontology_registry.py:480` |

**IBG Zones (15):**
```
centerline, upper_bout, waist, lower_bout, horn_left, horn_right,
cutaway_left, cutaway_right, neck_pocket, bridge_region, butt_end,
shoulder_left, shoulder_right, apex_upper, apex_lower
```

**Decomposition Proposal:**

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `morphology_zone` | IBG body partition | IBG (sandbox) |
| `spatial_region` | MRP region contract | MRP (governance) |
| `operational_region` | CAM processing areas | CAM (runtime) |

**C2 Candidate:** Either register IBG zones as 7M regions OR document as implementation detail.

---

### COLLISION: outline

**Status:** Usage divergence — MEDIUM RISK

| Usage | Domain | Meaning |
|-------|--------|---------|
| outline (visual) | Presentation | Display contour for rendering |
| outline (manufacturing) | CAM | Toolpath boundary for cutting |
| outline (extraction) | Vectorizer | Detected contour from image |
| outline (canonical) | Spec | Defined body shape |

**Decomposition Proposal:**

| Namespace | Purpose | Layer |
|-----------|---------|-------|
| `canonical_outline` | Authoritative body boundary | authoritative_geometry |
| `manufacturing_outline` | Toolpath boundary | operational_geometry |
| `display_outline` | Rendering contour | presentation_geometry |
| `extracted_outline` | Vectorizer output | derived_geometry |

**C2 Candidate:** Layer-prefixed outline references where semantic distinction required.

---

### COLLISION: dimensions

**Status:** Usage divergence — MEDIUM RISK

| Usage | Domain | Meaning |
|-------|--------|---------|
| dimensions (physical) | Spec | Canonical measurements |
| dimensions (bbox) | IBG | Bounding box values |
| dimensions (template) | User | User-defined constraints |
| dimensions (computed) | Derived | Calculated values |

**Decomposition Proposal:**

| Namespace | Purpose | Authority |
|-----------|---------|-----------|
| `canonical_dimensions` | Authoritative measurements | Owner |
| `bbox_dimensions` | Bounding box | Derived |
| `template_dimensions` | User constraints | User authority |
| `computed_dimensions` | Calculated values | Non-authoritative |

**C2 Candidate:** Source-prefixed dimension references.

---

### COLLISION: tier

**Source:** COLL-G004

**Status:** Overloaded — MEDIUM RISK

| Usage | Domain | Meaning | Values |
|-------|--------|---------|--------|
| tier (runtime) | CAM | Topology strictness | `PROTOTYPE`, `PRODUCTION` |
| tier (governance) | 7M | Authority level | 1, 2, 3 |
| tier (execution) | CI | Check timing | `precommit`, `ci`, `nightly`, `manual` |

**Decomposition Proposal:**

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `runtime_tier` | Topology strictness level | CAM |
| `governance_tier` | Authority hierarchy level | MRP |
| `execution_tier` | Check timing category | CI |

**C2 Candidate:** Domain-prefixed tier usages.

---

### COLLISION: primitive

**Source:** COLL-G005

**Status:** Ungoverned vocabulary — MEDIUM RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| PrimitiveType | IBG | 14 morphology primitive types | `primitives.py:53` |
| primitive (concept) | General | Basic geometric element | Various |

**IBG Primitives (14):**
```
arc_segment, line_segment, convex_bout, concave_waist, horn_projection,
cutaway_intrusion, transition_curve, blend_fillet, shoulder_curve,
neck_joint_curve, end_block, apex_point, inflection_point, tangent_point
```

**Decomposition Proposal:**

| Namespace | Purpose | Status |
|-----------|---------|--------|
| `morphology_primitive` | IBG classification primitives | Sandbox |
| `geometry_primitive` | Basic geometric elements | General |

**C2 Candidate:** Register `morphology_primitive` in 7M with lifecycle semantics if IBG graduates.

---

### COLLISION: partition

**Source:** Terminal 3 Review (C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md)

**Status:** Overloaded — MEDIUM RISK

| Usage | Domain | Meaning |
|-------|--------|---------|
| partition (spatial) | MRP/IBG | Subdivision of body into regions |
| partition (manufacturing) | CAM | Decomposition of shell for toolpath |

**Decomposition Proposal:**

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `spatial_partition` | Body region subdivision | MRP/IBG |
| `manufacturing_partition` | Shell decomposition for toolpath | CAM |

**C2 Candidate:** Domain-prefixed partition usages where semantic distinction required.

---

### COLLISION: boundary

**Source:** Terminal 3 Review (C2_TOPOLOGY_NAMESPACE_SEPARATION_REVIEW.md)

**Status:** Overloaded — MEDIUM RISK

| Usage | Domain | Meaning |
|-------|--------|---------|
| boundary (region) | MRP | Interface between spatial regions |
| boundary (toolpath) | CAM | Edge of machining area |
| boundary (zone) | IBG | Y-range constraints on zones |

**Decomposition Proposal:**

| Namespace | Purpose | Domain |
|-----------|---------|--------|
| `region_boundary` | Spatial region interface | MRP |
| `toolpath_boundary` | Machining area edge | CAM |
| `zone_boundary` | IBG zone Y-range constraint | IBG (sandbox) |

**C2 Candidate:** Domain-prefixed boundary usages where semantic distinction required.

---

### COLLISION: morphology

**Source:** COLL-G002

**Status:** Authority gap — HIGH RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| morphology (7M) | MRP | Registered governance term | `canonical_ontology_registry.py:392` |
| BodyMorphologyClass | IBG | 10-value classification enum | `variant_grammar.py:24` |
| MorphologyDescriptor | IBG | Full classification object | `morphology_descriptor.py:53` |
| MorphologyPrimitive | IBG | Classification primitive | `primitives.py:72` |

**Decomposition Proposal:**

| Namespace | Purpose | Status |
|-----------|---------|--------|
| `morphology` (7M) | Canonical governance term | Authoritative |
| `ibg_morphology_class` | IBG classification | Sandbox consumer |
| `ibg_morphology_descriptor` | IBG classification object | Sandbox consumer |

**C2 Candidate:** Register IBG as 7N consumer with `consumed_terms: ["morphology", "topology"]`

---

## 4. Authority Candidate Matrix

| Term | Current Authority | Candidates | Arbitration Required |
|------|-------------------|------------|---------------------|
| geometry | UNRESOLVED | Spec, Template, MRP | YES |
| topology | SPLIT | MRP (spatial), CAM (surface) | YES — Terminal 3 VALIDATED |
| morphology | 7M REGISTERED | MRP, IBG consumer | MEDIUM |
| zone | UNRESOLVED | IBG (impl), MRP (contract) | YES |
| outline | UNRESOLVED | Multiple layers | YES |
| dimensions | UNRESOLVED | Multiple sources | YES |
| partition | UNRESOLVED | MRP (spatial), CAM (manufacturing) | YES — Terminal 3 addition |
| boundary | UNRESOLVED | MRP (region), CAM (toolpath), IBG (zone) | YES — Terminal 3 addition |
| tier | OVERLOADED | Domain-specific | NO (prefix) |
| primitive | SANDBOX | IBG | DEFERRED |

---

## 5. Decomposition Rules

### DO

- Classify collision semantic layers
- Map collision to C2 geometry layers
- Identify all authority candidates
- Document propagation paths
- Preserve domain vocabulary

### DO NOT

- Choose winners
- Normalize globally
- Rename terms without arbitration
- Federate without ratification
- Collapse semantic layers

---

## 6. Namespace Strategy

### Layer Prefixing

When semantic distinction required:
```
authoritative_* — canonical truth
operational_* — runtime consumption
derived_* — computed values
presentation_* — display values
serialized_* — export encoding
sandbox_* — pre-governance
```

### Domain Prefixing

When domain distinction required:
```
morphology_* — MRP spatial semantics
surface_* — CAM geometric continuity
manufacturing_* — CAM production
ibg_* — IBG sandbox vocabulary
runtime_* — CAM execution
governance_* — MRP governance
```

---

## 7. Arbitration Surface Summary

| Surface | Priority | Status |
|---------|----------|--------|
| geometry authority origin | CRITICAL | Unresolved |
| topology semantic split | HIGH | Decomposed — Terminal 3 VALIDATED |
| morphology authority gap | HIGH | Decomposed |
| zone/region vocabulary | MEDIUM | Decomposed |
| outline layer distinction | MEDIUM | Decomposed |
| partition overload | MEDIUM | Decomposed (Terminal 3 addition) |
| boundary overload | MEDIUM | Decomposed (Terminal 3 addition) |
| tier overload | LOW | Prefix solution |
| primitive vocabulary | LOW | Sandbox deferred |

---

## 8. Related Documents

### C1 Collision Logs

- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md`
- `export_serialization/SEMANTIC_COLLISION_LOG.md`
- `acoustics_observational/SEMANTIC_COLLISION_LOG.md`

### Framework Documents

- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_GEOMETRY_OWNERSHIP_TOPOLOGY.md` — Domain mapping
- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Flow analysis

---

*C2-A Geometry Namespace Collisions — Decomposition Complete*
