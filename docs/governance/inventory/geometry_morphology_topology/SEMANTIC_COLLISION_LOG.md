# Semantic Collision Log — Geometry/Morphology/Topology

**Sprint:** Geometry/Morphology/Topology  
**Terminal:** 3  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This log records observed semantic collisions. It does not:
- Resolve collisions
- Rename terms
- Assign winners
- Enforce corrections

**Critical:** Collisions recorded here MUST NOT be fixed during C1.

---

## Collision Entries

### COLL-G001: Topology Semantic Divergence

| Field | Value |
|-------|-------|
| collision_id | COLL-G001 |
| collision_type | overload |
| risk_level | High |
| do_not_fix_in_c1 | true |

**Terms:**
- `topology` (7M/MRP definition)
- `topology` (CAM TopologyBuilder usage)

**Locations:**
- `app/cam/canonical_ontology_registry.py:472` — 7M: "spatial relationships, regions, connectivity under MRP governance"
- `app/cam/topology_builder/contracts.py:33` — CAM: 3D shell construction with G0/G1/G2 continuity

**Collision Description:**
Same term means fundamentally different things:
1. **7M/MRP**: Semantic spatial structure for governance (regions, connectivity, spatial relationships)
2. **CAM**: Geometric surface continuity for manufacturing (G0 touching, G1 tangent, G2 curvature)

**C2 Candidate:**
Distinguish `morphology_topology` (MRP) vs `surface_topology` or `manufacturing_topology` (CAM).

---

### COLL-G002: Morphology Authority Gap

| Field | Value |
|-------|-------|
| collision_id | COLL-G002 |
| collision_type | authority_overlap |
| risk_level | High |
| do_not_fix_in_c1 | true |

**Terms:**
- `morphology` (7M registered)
- `BodyMorphologyClass` (IBG implementation)
- `MorphologyDescriptor` (IBG implementation)
- `MorphologyPrimitive` (IBG implementation)

**Locations:**
- `app/cam/canonical_ontology_registry.py:392` — 7M registered term
- `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24` — `BodyMorphologyClass`
- `app/instrument_geometry/body/ibg/body_grid/morphology_descriptor.py:53` — `MorphologyDescriptor`
- `app/instrument_geometry/body/ibg/body_grid/primitives.py:72` — `MorphologyPrimitive`

**Collision Description:**
IBG creates complete morphology vocabulary that:
1. Implements 7M `morphology` semantics
2. Is NOT registered as 7N consumer
3. Creates binding classification authority without governance

**C2 Candidate:**
Register IBG as 7N consumer with consumed_terms: `["morphology", "topology"]`

---

### COLL-G003: Zone vs Region Vocabulary

| Field | Value |
|-------|-------|
| collision_id | COLL-G003 |
| collision_type | geometry_ambiguity |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `ZoneId` (IBG 15 zones)
- `RegionContract` (7M topology contract)

**Locations:**
- `app/instrument_geometry/body/ibg/body_grid/zones.py:24` — `ZoneId` (15 zones)
- `app/cam/canonical_ontology_registry.py:480` — `RegionContract` (7M topology contract)

**Collision Description:**
IBG zones and 7M regions describe the same concept (spatial areas of body):
- IBG: `LOWER_BOUT`, `WAIST`, `UPPER_BOUT`, `HORN_LEFT`, etc. (15 specific zones)
- 7M: Generic `RegionContract` without specific region names

**C2 Candidate:**
Either:
1. Register zone vocabulary as 7M regions
2. Or document IBG zones as implementation detail of 7M regions

---

### COLL-G004: Tier Semantic Collision

| Field | Value |
|-------|-------|
| collision_id | COLL-G004 |
| collision_type | overload |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `tier` (multiple usages)

**Locations:**
- `app/cam/topology_builder/contracts.py:34` — `TopologyTier`: `PROTOTYPE`, `PRODUCTION`
- `app/cam/canonical_ontology_registry.py` — Governance tiers: 1, 2, etc.
- `docs/governance/` — Execution tiers: `precommit`, `ci`, `nightly`, `manual`

**Collision Description:**
"Tier" means different things in different contexts:
1. **Topology**: Runtime strictness level (PROTOTYPE vs PRODUCTION)
2. **Governance**: Authority level (Tier 1 structural, Tier 2 domain)
3. **Execution**: Check timing (precommit, ci, nightly)

**C2 Candidate:**
Prefix tier usages: `runtime_tier`, `governance_tier`, `execution_tier`

---

### COLL-G005: Primitive Vocabulary Ungoverned

| Field | Value |
|-------|-------|
| collision_id | COLL-G005 |
| collision_type | runtime_inference |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `PrimitiveType` (14 types)
- `MorphologyPrimitive`
- `primitive` (concept)

**Locations:**
- `app/instrument_geometry/body/ibg/body_grid/primitives.py:53` — `PrimitiveType` (14 types)
- `app/instrument_geometry/body/ibg/body_grid/primitives.py:72` — `MorphologyPrimitive`

**Collision Description:**
IBG defines 14 primitive types that form the foundation of morphology reasoning:
- `ARC_SEGMENT`, `LINE_SEGMENT`, `CONVEX_BOUT`, `CONCAVE_WAIST`, `HORN_PROJECTION`, etc.
- These primitives are used to classify body shapes
- They create semantic authority without governance
- No 7M registration exists for `primitive` as a term

**C2 Candidate:**
Register `morphology_primitive` in 7M with lifecycle semantics.

---

## Summary

| Collision Type | Count |
|----------------|-------|
| Synonym | 0 |
| Overload | 2 |
| Authority overlap | 1 |
| Lifecycle conflict | 0 |
| Provenance split | 0 |
| Geometry ambiguity | 1 |
| Runtime inference | 1 |
| Staging leakage | 0 |

| Risk Level | Count |
|------------|-------|
| Low | 0 |
| Medium | 3 |
| High | 2 |
| Critical | 0 |

---

## Notes

### IBG as Primary Collision Source

4 of 5 collisions involve IBG Body Grid vocabulary:
- COLL-G002: morphology authority gap
- COLL-G003: zone vs region
- COLL-G004: tier collision (partial)
- COLL-G005: primitive vocabulary

This is expected since IBG operates in sandbox/pre-governance state.

### CAM Topology Builder

1 collision involves CAM Topology Builder:
- COLL-G001: topology semantic divergence

The CAM usage of "topology" for G0/G1/G2 continuity is semantically distinct from MRP's spatial topology.

### Cross-Reference

Full collision analysis in: `C1_GEOMETRY_TOPOLOGY_SEMANTIC_INVENTORY.md`
