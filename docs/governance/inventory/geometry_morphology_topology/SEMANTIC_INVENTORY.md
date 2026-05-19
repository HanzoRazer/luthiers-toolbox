# Semantic Inventory — Geometry/Morphology/Topology

**Sprint:** Geometry/Morphology/Topology  
**Terminal:** 3  
**Date:** 2026-05-18  
**Status:** Non-authoritative inventory artifact

---

## Authority Statement

This inventory documents observed semantic usage. It does not:
- Ratify terms as canonical
- Assign ownership
- Normalize vocabulary
- Resolve collisions

Discovery does not imply endorsement.

---

## Focus Areas

Terminal 3 inventories:
- `geometry`
- `morphology`
- `topology`
- `primitive`
- `body_grid`
- `outline`
- `bbox`
- `continuity`
- `classification`
- `visualization`
- `serialization`

---

## Inventory Entries

### 1. GeometryType

| Field | Value |
|-------|-------|
| term | `GeometryType` |
| location | `app/instrument_geometry/body/ibg/body_grid/primitives.py:25` |
| values | `arc`, `line`, `spline`, `mixed`, `unknown` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 2. CurvatureClass

| Field | Value |
|-------|-------|
| term | `CurvatureClass` |
| location | `app/instrument_geometry/body/ibg/body_grid/primitives.py:34` |
| values | `convex_outward`, `concave_inward`, `straight`, `inflection`, `unknown` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 3. SlopeClass

| Field | Value |
|-------|-------|
| term | `SlopeClass` |
| location | `app/instrument_geometry/body/ibg/body_grid/primitives.py:43` |
| values | `ascending`, `descending`, `horizontal`, `vertical`, `diagonal_pos`, `diagonal_neg` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 4. PrimitiveType

| Field | Value |
|-------|-------|
| term | `PrimitiveType` |
| location | `app/instrument_geometry/body/ibg/body_grid/primitives.py:53` |
| values | 14 types including `arc_segment`, `line_segment`, `convex_bout`, `concave_waist`, `horn_projection`, `cutaway_intrusion`, etc. |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |
| authority_risk | High — creates binding classification vocabulary |

---

### 5. BodyMorphologyClass

| Field | Value |
|-------|-------|
| term | `BodyMorphologyClass` |
| location | `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:24` |
| values | `rounded_acoustic`, `rounded_single_cut`, `double_cut`, `offset_waist`, `angular_wedge`, `slab_body`, `carved_top`, `semi_symmetric`, `asymmetric`, `unknown` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No — but implements 7M `morphology` concept |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |
| authority_risk | High — de facto morphology authority |

---

### 6. ZoneId

| Field | Value |
|-------|-------|
| term | `ZoneId` |
| location | `app/instrument_geometry/body/ibg/body_grid/zones.py:24` |
| values | 15 zones including `centerline`, `upper_bout`, `waist`, `lower_bout`, `horn_left`, `horn_right`, `cutaway_left`, `cutaway_right`, `neck_pocket`, `bridge_region`, `butt_end`, `shoulder` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |
| authority_risk | High — creates spatial region semantics |

---

### 7. HornBehavior

| Field | Value |
|-------|-------|
| term | `HornBehavior` |
| location | `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:38` |
| values | `symmetric_horns`, `single_cut_treble`, `single_cut_bass`, `no_horns`, `pointed_horns`, `rounded_horns`, `angular_horns` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 8. WaistBehavior

| Field | Value |
|-------|-------|
| term | `WaistBehavior` |
| location | `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:49` |
| values | `deep_waist`, `moderate_waist`, `shallow_waist`, `suppressed_waist`, `offset_waist`, `angular_waist` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 9. BoutBehavior

| Field | Value |
|-------|-------|
| term | `BoutBehavior` |
| location | `app/instrument_geometry/body/ibg/body_grid/variant_grammar.py:59` |
| values | `rounded_bouts`, `angular_bouts`, `asymmetric_bouts`, `extended_lower`, `suppressed_upper` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 10. ContinuityLevel

| Field | Value |
|-------|-------|
| term | `ContinuityLevel` |
| location | `app/cam/topology_builder/contracts.py:16` |
| values | `G0`, `G1`, `G2` |
| declared_owner | None |
| operational_owner | CAM Topology Builder |
| 7M_registered | No |
| consumed_via_7N | No |
| semantic_context | Geometric surface junction quality |

---

### 11. ShellType

| Field | Value |
|-------|-------|
| term | `ShellType` |
| location | `app/cam/topology_builder/contracts.py:25` |
| values | `flat_extrusion`, `lofted`, `swept`, `composite` |
| declared_owner | None |
| operational_owner | CAM Topology Builder |
| 7M_registered | No |
| consumed_via_7N | No |

---

### 12. TopologyTier

| Field | Value |
|-------|-------|
| term | `TopologyTier` |
| location | `app/cam/topology_builder/contracts.py:34` |
| values | `PROTOTYPE`, `PRODUCTION` |
| declared_owner | None |
| operational_owner | CAM Topology Builder |
| 7M_registered | No |
| consumed_via_7N | No |
| collision_risk | Medium — "tier" overloaded with governance tiers |

---

### 13. CoordinateSpace

| Field | Value |
|-------|-------|
| term | `CoordinateSpace` |
| location | `app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py:23` |
| values | `raw_pixel`, `raw_mm`, `bounding_box`, `centerline_relative` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 14. EvidenceSource

| Field | Value |
|-------|-------|
| term | `EvidenceSource` |
| location | `app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py:32` |
| values | `vectorizer_dxf`, `constraint_extractor`, `photo_extraction`, `user_input`, `spec_default` |
| declared_owner | None |
| operational_owner | IBG Body Grid |
| 7M_registered | No |
| consumed_via_7N | No |
| sandbox_status | Pre-governance |

---

### 15. morphology (7M Registered)

| Field | Value |
|-------|-------|
| term | `morphology` |
| location | `app/cam/canonical_ontology_registry.py:392` |
| canonical_definition | "Semantic structure describing instrument body shape, regions, and topology under MRP governance." |
| declared_owner | MRP |
| governance_tier | 2 |
| canonical_contracts | `MorphologyContract`, `TopologyContract` |
| prohibited_reinterpretations | `runtime_computed_morphology`, `automatic_shape_inference` |
| lifecycle_semantics | `draft`, `validated`, `canonical` |
| aliases | `body_morphology`, `instrument_morphology` |
| implementation_gap | IBG implements without 7N consumption |

---

### 16. topology (7M Registered)

| Field | Value |
|-------|-------|
| term | `topology` |
| location | `app/cam/canonical_ontology_registry.py:472` |
| canonical_definition | "Semantic structure describing spatial relationships, regions, and connectivity under MRP governance." |
| declared_owner | MRP |
| governance_tier | 2 |
| canonical_contracts | `TopologyContract`, `RegionContract` |
| prohibited_reinterpretations | `runtime_topology_inference`, `automatic_region_detection` |
| lifecycle_semantics | `draft`, `validated`, `canonical` |
| aliases | `body_topology`, `spatial_topology` |
| semantic_collision | CAM uses for 3D shell construction (G0/G1/G2), not MRP spatial relationships |

---

## Summary

| Metric | Count |
|--------|-------|
| Terms inventoried | 16 |
| Declared owners identified | 2 (MRP for morphology, topology) |
| Operational owners identified | 3 (IBG, CAM Topology Builder, 7M) |
| Authority mismatches | 2 (IBG implements 7M terms without registration) |
| Enforcement gaps | 14 (unregistered IBG/CAM terms) |

---

## Notes

### IBG Sandbox Status

The IBG Body Grid system exists in sandbox/pre-governance state:
- Files are untracked in git
- No 7N consumer registration
- Creates de facto authority through operational usage
- 75 terms defined without 7M registration

### Topology Semantic Split

The term `topology` has divergent meanings:
1. **7M/MRP**: Semantic spatial structure (regions, connectivity)
2. **CAM**: Geometric surface continuity (G0/G1/G2 junctions)

This split requires C2 reconciliation.

### Cross-Reference

Full inventory details in: `C1_GEOMETRY_TOPOLOGY_SEMANTIC_INVENTORY.md`
