# C1 Inventory: Geometry/Topology/IBG Workstream

**Phase:** C1 — Collection  
**Date:** 2026-05-18  
**Status:** Inventory (no decisions made)  
**Scope:** Geometry origination, mutation, consumption, and silent authority patterns

---

## Purpose

This document inventories geometry and topology lifecycle terms across the system. Following C1 principles, it records semantic evidence without making reconciliation decisions.

**Core rule applied:** Inventory where geometry meaning originates, where it mutates, where it is consumed, and where it silently becomes authority. Do not stabilize or reconcile.

---

## 1. Authoritative Geometry Layer (CadSemantics)

**Source:** `services/api/app/export/cad_semantics.py`  
**Role:** Defining semantic source for CAD construction hints  
**Authority:** May EXTEND approved geometry context; may NOT override, reinterpret, or invent approved geometry

### 1.1 BodyCategory Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `flat_body` | `cad_semantics.py:34` | Export | body_type | Supported: solid electric guitars |
| `acoustic_flat_top` | `cad_semantics.py:35` | Export | body_type | Semantic only: steel-string, classical |
| `acoustic_arched_top` | `cad_semantics.py:36` | Export | body_type | Future: arched soundboard |
| `hollow_electric` | `cad_semantics.py:37` | Export | body_type | Future: semi-hollow |
| `archtop` | `cad_semantics.py:38` | Export | body_type | Future: jazz archtop |
| `resonator` | `cad_semantics.py:39` | Export | body_type | Future/unsupported: resonator guitars |
| `unknown` | `cad_semantics.py:40` | Export | body_type | Fallback |

### 1.2 RuntimeSupport Vocabulary (cad_semantics)

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `supported` | `cad_semantics.py:75` | Export | runtime | Full runtime generation |
| `semantic_only` | `cad_semantics.py:76` | Export | runtime | Schema valid, no runtime topology |
| `unsupported` | `cad_semantics.py:77` | Export | runtime | Not supported |

**Collision candidate:** CAM Runtime uses `unsupported` differently (see C1_RUNTIME_CAM_INVENTORY.md COL-001)

### 1.3 PlateType Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `flat` | `cad_semantics.py:67` | Export | surface | Planar surface |
| `radiused` | `cad_semantics.py:68` | Export | surface | Spherical cap (single radius) |
| `arched` | `cad_semantics.py:69` | Export | surface | Carved arch (RESEARCH_ONLY) |

### 1.4 SideProfileType Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `uniform` | `cad_semantics.py:46` | Export | profile | Constant depth |
| `tapered` | `cad_semantics.py:47` | Export | profile | Depth varies tail-to-neck |

### 1.5 ContinuityTarget Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `G0` | `cad_semantics.py:53` | Export | continuity | Positional continuity |
| `G1` | `cad_semantics.py:54` | Export | continuity | Tangent continuity |

### 1.6 ClosureType Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `closed_rim` | `cad_semantics.py:60` | Export | closure | Standard closed rim |
| `cutaway` | `cad_semantics.py:61` | Export | closure | Has cutaway |

---

## 2. Topology Runtime Support (Defined Contract)

**Source:** `services/api/app/cam/topology_builder/runtime_support.py`  
**Role:** Critical gate determining whether topology can be generated at runtime  
**Authority:** Defined topology semantic contract

### 2.1 TopologyRuntimeSupport Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `SUPPORTED_PROTOTYPE` | `runtime_support.py:27` | Topology | runtime | Can generate prototype topology now |
| `PARTIAL_PROTOTYPE` | `runtime_support.py:28` | Topology | runtime | Some features supported, others skipped with warnings |
| `UNSUPPORTED_RUNTIME` | `runtime_support.py:29` | Topology | runtime | Cannot generate, clean rejection required |
| `RESEARCH_REQUIRED` | `runtime_support.py:30` | Topology | runtime | Future capability needed |

**Collision candidate:** CAM Runtime `unsupported` (see C1_RUNTIME_CAM_INVENTORY.md)

### 2.2 Body Category → Runtime Support Mapping

| Body Category | Support Classification | Source |
|---------------|------------------------|--------|
| `flat_body` | `SUPPORTED_PROTOTYPE` | `runtime_support.py:37` |
| `acoustic_flat_top` | `SUPPORTED_PROTOTYPE` | `runtime_support.py:39` |
| `hollow_electric` | `PARTIAL_PROTOTYPE` | `runtime_support.py:41` |
| `archtop` | `RESEARCH_REQUIRED` | `runtime_support.py:43` |
| `acoustic_arched_top` | `RESEARCH_REQUIRED` | `runtime_support.py:44` |
| `resonator` | `RESEARCH_REQUIRED` | `runtime_support.py:46` |
| `unknown` | `UNSUPPORTED_RUNTIME` | `runtime_support.py:48` |

### 2.3 Feature Support Classification

| Feature | Support Classification | Notes |
|---------|------------------------|-------|
| `thickness_uniform` | `SUPPORTED_PROTOTYPE` | Level 1 |
| `thickness_component` | `SUPPORTED_PROTOTYPE` | Level 2 |
| `thickness_zonal` | `PARTIAL_PROTOTYPE` | Level 3 |
| `thickness_continuous` | `RESEARCH_REQUIRED` | Level 4 |
| `profile_flat` | `SUPPORTED_PROTOTYPE` | |
| `profile_uniform_arch` | `PARTIAL_PROTOTYPE` | |
| `profile_graduated_arch` | `RESEARCH_REQUIRED` | |
| `continuity_g0` | `SUPPORTED_PROTOTYPE` | |
| `continuity_g1` | `PARTIAL_PROTOTYPE` | |
| `continuity_g2` | `RESEARCH_REQUIRED` | |
| `taper_none` | `SUPPORTED_PROTOTYPE` | |
| `taper_linear` | `PARTIAL_PROTOTYPE` | |
| `taper_graduated` | `RESEARCH_REQUIRED` | |

---

## 3. Topology Builder Contracts

**Source:** `services/api/app/cam/topology_builder/contracts.py`  
**Role:** Interface contracts between cad_semantics and topology builder

### 3.1 ContinuityLevel Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `G0` | `contracts.py:19` | Topology | continuity | Positional continuity (touching) |
| `G1` | `contracts.py:20` | Topology | continuity | Tangent continuity (smooth) |
| `G2` | `contracts.py:21` | Topology | continuity | Curvature continuity (very smooth) |

**Cross-reference:** CadSemantics ContinuityTarget uses same vocabulary (aligned)

### 3.2 ShellType Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `flat_extrusion` | `contracts.py:27` | Topology | shell | Simple extrusion from profile |
| `lofted` | `contracts.py:28` | Topology | shell | Loft between profiles |
| `swept` | `contracts.py:29` | Topology | shell | Sweep along path |
| `composite` | `contracts.py:30` | Topology | shell | Multiple shells joined |

### 3.3 TopologyTier Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| `PROTOTYPE` | `contracts.py:36` | Topology | tier | G0 acceptable, warnings allowed |
| `PRODUCTION` | `contracts.py:37` | Topology | tier | G1 required, strict validation |

---

## 4. Instrument Geometry Enums

**Source:** `services/api/app/instrument_geometry/`  
**Role:** Source geometry definitions for instrument construction

### 4.1 CoordinateRegion Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `coordinate_system.py:35` | Geometry | coordinate | Regional coordinate classification |

### 4.2 DXFKind Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `dxf_registry.py:26` | Geometry | export | DXF type classification |

### 4.3 BodySymmetry Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `body/centerline.py:25` | Geometry | symmetry | Body symmetry classification |

### 4.4 InstrumentModelId Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `models.py:23` | Geometry | identity | Model identification |

### 4.5 InstrumentModelStatus Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `models.py:72` | Geometry | status | Model readiness status |

### 4.6 InstrumentCategory Vocabulary

| Term | Source File | Domain | Axis | Notes |
|------|-------------|--------|------|-------|
| (Enum values) | `models.py:101` | Geometry | category | Instrument type classification |

### 4.7 Neck System Vocabularies

| Vocabulary | Source File | Domain |
|------------|-------------|--------|
| `SetupWorkflowStep` | `neck/setup_workflow.py:20` | Setup |
| `DiagnosticGate` | `neck/setup_workflow.py:29` | Setup |
| `PlayerSymptom` | `neck/setup_workflow.py:85` | Setup |
| `ScaleType` | `neck/fretboard_ecosphere.py:41` | Fretboard |
| `TemperamentType` | `neck/fretboard_ecosphere.py:47` | Fretboard |

### 4.8 Pickup System Vocabularies

| Vocabulary | Source File | Domain |
|------------|-------------|--------|
| `BridgeType` | `pickup/cavity_placement.py:39` | Pickup |

---

## 5. IBG SANDBOX PRESSURE SURFACE

**Sandbox Status:** sandbox/pre-governance  
**Constitutional Status:** unratified  
**Semantic Pressure:** HIGH

IBG (Instrument Body Generator) is a sandbox system under development. Its vocabulary exerts high semantic pressure on the governance system because it defines morphology concepts that will likely become constitutional once ratified.

### 5.1 IBG Body Grid Schema

**Source:** `services/api/app/instrument_geometry/body/ibg/body_grid/body_grid_schema.py`

#### CoordinateSpace Vocabulary

| Term | Source File | Domain | Axis | Sandbox Status |
|------|-------------|--------|------|----------------|
| `raw_pixel` | `body_grid_schema.py:25` | IBG | coordinate | sandbox/pre-governance |
| `raw_mm` | `body_grid_schema.py:26` | IBG | coordinate | sandbox/pre-governance |
| `bounding_box` | `body_grid_schema.py:27` | IBG | coordinate | sandbox/pre-governance |
| `centerline_relative` | `body_grid_schema.py:28` | IBG | coordinate | sandbox/pre-governance |

#### EvidenceSource Vocabulary

| Term | Source File | Domain | Axis | Sandbox Status |
|------|-------------|--------|------|----------------|
| `vectorizer_dxf` | `body_grid_schema.py:33` | IBG | evidence | sandbox/pre-governance |
| `constraint_extractor` | `body_grid_schema.py:34` | IBG | evidence | sandbox/pre-governance |
| `photo_extraction` | `body_grid_schema.py:35` | IBG | evidence | sandbox/pre-governance |
| `user_input` | `body_grid_schema.py:36` | IBG | evidence | sandbox/pre-governance |
| `spec_default` | `body_grid_schema.py:37` | IBG | evidence | sandbox/pre-governance |

### 5.2 IBG Zone Vocabulary

**Source:** `services/api/app/instrument_geometry/body/ibg/body_grid/zones.py`

#### ZoneId Vocabulary

| Term | Source File | Y Range | Semantic Role | Sandbox Status |
|------|-------------|---------|---------------|----------------|
| `centerline` | `zones.py:26` | 0.0-1.0 | Body axis of reference | sandbox/pre-governance |
| `upper_bout` | `zones.py:27` | 0.50-0.75 | Secondary resonant mass | sandbox/pre-governance |
| `waist` | `zones.py:28` | 0.35-0.55 | Narrowest body region | sandbox/pre-governance |
| `lower_bout` | `zones.py:29` | 0.08-0.40 | Primary resonant mass | sandbox/pre-governance |
| `horn_left` | `zones.py:30` | 0.60-0.85 | Upper body projection (bass) | sandbox/pre-governance |
| `horn_right` | `zones.py:31` | 0.60-0.85 | Upper body projection (treble) | sandbox/pre-governance |
| `cutaway_left` | `zones.py:32` | 0.55-0.80 | Access cutaway (bass, rare) | sandbox/pre-governance |
| `cutaway_right` | `zones.py:33` | 0.55-0.80 | Access cutaway (treble) | sandbox/pre-governance |
| `neck_pocket` | `zones.py:34` | 0.80-1.0 | Neck attachment region | sandbox/pre-governance |
| `bridge_region` | `zones.py:35` | 0.15-0.35 | Bridge placement region | sandbox/pre-governance |
| `left_flank` | `zones.py:36` | 0.0-1.0 | Complete left side contour | sandbox/pre-governance |
| `right_flank` | `zones.py:37` | 0.0-1.0 | Complete right side contour | sandbox/pre-governance |
| `outer_boundary` | `zones.py:38` | - | Fallback zone | sandbox/pre-governance |
| `butt_end` | `zones.py:39` | 0.0-0.08 | Tail/end block region | sandbox/pre-governance |
| `shoulder` | `zones.py:40` | 0.75-0.90 | Transition bout to neck | sandbox/pre-governance |

### 5.3 IBG Primitives Vocabulary

**Source:** `services/api/app/instrument_geometry/body/ibg/body_grid/primitives.py`

#### GeometryType Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `arc` | `primitives.py:27` | IBG | sandbox/pre-governance |
| `line` | `primitives.py:28` | IBG | sandbox/pre-governance |
| `spline` | `primitives.py:29` | IBG | sandbox/pre-governance |
| `mixed` | `primitives.py:30` | IBG | sandbox/pre-governance |
| `unknown` | `primitives.py:31` | IBG | sandbox/pre-governance |

#### CurvatureClass Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `convex_outward` | `primitives.py:36` | IBG | sandbox/pre-governance |
| `concave_inward` | `primitives.py:37` | IBG | sandbox/pre-governance |
| `straight` | `primitives.py:38` | IBG | sandbox/pre-governance |
| `inflection` | `primitives.py:39` | IBG | sandbox/pre-governance |
| `unknown` | `primitives.py:40` | IBG | sandbox/pre-governance |

#### SlopeClass Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `ascending` | `primitives.py:45` | IBG | sandbox/pre-governance |
| `descending` | `primitives.py:46` | IBG | sandbox/pre-governance |
| `horizontal` | `primitives.py:47` | IBG | sandbox/pre-governance |
| `vertical` | `primitives.py:48` | IBG | sandbox/pre-governance |
| `diagonal_pos` | `primitives.py:49` | IBG | sandbox/pre-governance |
| `diagonal_neg` | `primitives.py:50` | IBG | sandbox/pre-governance |

#### PrimitiveType Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `arc_segment` | `primitives.py:55` | IBG | sandbox/pre-governance |
| `line_segment` | `primitives.py:56` | IBG | sandbox/pre-governance |
| `diagonal_segment` | `primitives.py:57` | IBG | sandbox/pre-governance |
| `convex_bout` | `primitives.py:58` | IBG | sandbox/pre-governance |
| `concave_waist` | `primitives.py:59` | IBG | sandbox/pre-governance |
| `horn_projection` | `primitives.py:60` | IBG | sandbox/pre-governance |
| `cutaway_intrusion` | `primitives.py:61` | IBG | sandbox/pre-governance |
| `flat_slab_edge` | `primitives.py:62` | IBG | sandbox/pre-governance |
| `offset_mass_region` | `primitives.py:63` | IBG | sandbox/pre-governance |
| `centerline_anchor` | `primitives.py:64` | IBG | sandbox/pre-governance |
| `bridge_axis_anchor` | `primitives.py:65` | IBG | sandbox/pre-governance |
| `butt_termination` | `primitives.py:66` | IBG | sandbox/pre-governance |
| `neck_junction` | `primitives.py:67` | IBG | sandbox/pre-governance |
| `shoulder_transition` | `primitives.py:68` | IBG | sandbox/pre-governance |

### 5.4 IBG Variant Grammar Vocabulary

**Source:** `services/api/app/instrument_geometry/body/ibg/body_grid/variant_grammar.py`

#### BodyMorphologyClass Vocabulary

| Term | Source File | Description | Sandbox Status |
|------|-------------|-------------|----------------|
| `rounded_acoustic` | `variant_grammar.py:26` | Dreadnought, jumbo, classical | sandbox/pre-governance |
| `rounded_single_cut` | `variant_grammar.py:27` | LP-style single cutaway | sandbox/pre-governance |
| `double_cut` | `variant_grammar.py:28` | SG-style, Stratocaster | sandbox/pre-governance |
| `offset_waist` | `variant_grammar.py:29` | Jazzmaster, Jaguar, Mustang | sandbox/pre-governance |
| `angular_wedge` | `variant_grammar.py:30` | Explorer, Flying V | sandbox/pre-governance |
| `slab_body` | `variant_grammar.py:31` | Telecaster, basic solid | sandbox/pre-governance |
| `carved_top` | `variant_grammar.py:32` | Archtop acoustic/electric | sandbox/pre-governance |
| `semi_symmetric` | `variant_grammar.py:33` | Minor asymmetry | sandbox/pre-governance |
| `asymmetric` | `variant_grammar.py:34` | Intentionally asymmetric | sandbox/pre-governance |
| `unknown` | `variant_grammar.py:35` | Fallback | sandbox/pre-governance |

#### HornBehavior Vocabulary

| Term | Source File | Sandbox Status |
|------|-------------|----------------|
| `symmetric_horns` | `variant_grammar.py:40` | sandbox/pre-governance |
| `single_cut_treble` | `variant_grammar.py:41` | sandbox/pre-governance |
| `single_cut_bass` | `variant_grammar.py:42` | sandbox/pre-governance |
| `no_horns` | `variant_grammar.py:43` | sandbox/pre-governance |
| `pointed_horns` | `variant_grammar.py:44` | sandbox/pre-governance |
| `rounded_horns` | `variant_grammar.py:45` | sandbox/pre-governance |
| `angular_horns` | `variant_grammar.py:46` | sandbox/pre-governance |

#### WaistBehavior Vocabulary

| Term | Source File | Sandbox Status |
|------|-------------|----------------|
| `deep_waist` | `variant_grammar.py:51` | sandbox/pre-governance |
| `moderate_waist` | `variant_grammar.py:52` | sandbox/pre-governance |
| `shallow_waist` | `variant_grammar.py:53` | sandbox/pre-governance |
| `suppressed_waist` | `variant_grammar.py:54` | sandbox/pre-governance |
| `offset_waist` | `variant_grammar.py:55` | sandbox/pre-governance |
| `angular_waist` | `variant_grammar.py:56` | sandbox/pre-governance |

#### BoutBehavior Vocabulary

| Term | Source File | Sandbox Status |
|------|-------------|----------------|
| `rounded_bouts` | `variant_grammar.py:61` | sandbox/pre-governance |
| `angular_bouts` | `variant_grammar.py:62` | sandbox/pre-governance |
| `asymmetric_bouts` | `variant_grammar.py:63` | sandbox/pre-governance |
| `extended_lower` | `variant_grammar.py:64` | sandbox/pre-governance |
| `suppressed_upper` | `variant_grammar.py:65` | sandbox/pre-governance |

### 5.5 IBG Arc Reconstructor

**Source:** `services/api/app/instrument_geometry/body/ibg/arc_reconstructor.py`

#### GapZone Vocabulary

| Term | Source File | Sandbox Status |
|------|-------------|----------------|
| (Enum values) | `arc_reconstructor.py:65` | sandbox/pre-governance |

---

## 6. Morphology Corpus (Harvest Layer)

**Sandbox Status:** sandbox/staging  
**Constitutional Status:** non-authoritative observational corpus  
**Semantic Pressure:** MEDIUM-HIGH

**Source:** `services/api/app/instrument_geometry/body/ibg/morphology_harvest/schema.py`

**Storage Authority Warning:** HarvestRecord is a preservation/coordination artifact. The `morphology_harvest/outputs/` directory is NOT canonical storage.

### 6.1 ReviewStatus Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `pending_review` | `schema.py:63` | Harvest | sandbox/staging |
| `approved` | `schema.py:64` | Harvest | sandbox/staging |
| `approved_with_edits` | `schema.py:65` | Harvest | sandbox/staging |
| `rejected` | `schema.py:66` | Harvest | sandbox/staging |
| `deferred` | `schema.py:67` | Harvest | sandbox/staging |

### 6.2 HarvestSource Vocabulary

| Term | Source File | Domain | Sandbox Status |
|------|-------------|--------|----------------|
| `vector_text` | `schema.py:72` | Harvest | sandbox/staging |
| `vector_no_text` | `schema.py:73` | Harvest | sandbox/staging |
| `raster_clean` | `schema.py:74` | Harvest | sandbox/staging |
| `raster_noisy` | `schema.py:75` | Harvest | sandbox/staging |
| `photo` | `schema.py:76` | Harvest | sandbox/staging |
| `mixed` | `schema.py:77` | Harvest | sandbox/staging |
| `unknown` | `schema.py:78` | Harvest | sandbox/staging |

### 6.3 Term Normalizations (Hardcoded Mappings)

| Source Term | Normalized Term | Notes |
|-------------|-----------------|-------|
| `lower_bout_mm` | `lower_bout_width_mm` | INSTRUMENT_SPECS drift |
| `upper_bout_mm` | `upper_bout_width_mm` | INSTRUMENT_SPECS drift |
| `waist_mm` | `waist_width_mm` | INSTRUMENT_SPECS drift |
| `body_width_mm` | `lower_bout_width_mm` | GuitarDimensions alias |
| `body_width_inches` | `lower_bout_width_inches` | GuitarDimensions alias |
| `lower_bout` | `lower_bout_width_mm` | Common variation |
| `upper_bout` | `upper_bout_width_mm` | Common variation |
| `waist` | `waist_width_mm` | Common variation |
| `body_length` | `body_length_mm` | Common variation |
| `scale_length` | `scale_length_mm` | Common variation |

**Semantic Pressure Note:** These normalizations encode decisions that should be governed, not hardcoded.

---

## 7. Semantic Collision Summary (Geometry/Topology)

### 7.1 Cross-Domain Term Collisions

| Term | Domain A | Meaning A | Domain B | Meaning B | Reconciliation |
|------|----------|-----------|----------|-----------|----------------|
| `unsupported` | CadSemantics | RuntimeSupport enum | TopologyBuilder | UNSUPPORTED_RUNTIME | Same concept, different casing |
| `unknown` | BodyCategory | Fallback | BodyMorphologyClass | Fallback | Same meaning |
| `G0`, `G1` | CadSemantics ContinuityTarget | Continuity level | Topology contracts | Continuity level | Aligned |

### 7.2 Duplicate Definition Patterns

| Pattern | Locations | Notes |
|---------|-----------|-------|
| `unknown` fallback | BodyCategory, GeometryType, CurvatureClass, BodyMorphologyClass, HarvestSource | Standard fallback pattern, acceptable |
| Continuity vocabulary | CadSemantics, Topology contracts | Aligned, same meaning |

### 7.3 Silent Authority Patterns

| Pattern | Location | Risk |
|---------|----------|------|
| IBG terms becoming de-facto standard | All IBG vocabularies | HIGH — pre-governance terms may calcify |
| Harvest term normalizations | `schema.py:83-97` | MEDIUM — hardcoded decisions |
| Zone Y-ranges | `zones.py` | MEDIUM — arbitrary values becoming authoritative |

---

## 8. Authority Flow Analysis

### 8.1 Where Geometry Meaning Originates

| System | Creates | Consumed By |
|--------|---------|-------------|
| CadSemantics | BodyCategory, RuntimeSupport | TopologyBuilder, Translators |
| TopologyBuilder | TopologyRuntimeSupport, ShellType | CAM Runtime |
| IBG Body Grid | ZoneId, PrimitiveType | Morphology Harvest |
| IBG Variant Grammar | BodyMorphologyClass, behaviors | Body classification |

### 8.2 Where Geometry Meaning Mutates

| Mutation Point | Before | After | Authority Gap |
|----------------|--------|-------|---------------|
| Harvest term normalization | Source term | Normalized term | Hardcoded mapping, no governance |
| BodyEvidence creation | HarvestRecord | Landmarks | Confidence loss |
| Zone classification | Raw point | ZoneAssignment | Fuzzy boundary decisions |

### 8.3 Where Geometry Silently Becomes Authority

| Location | Pattern | Risk |
|----------|---------|------|
| IBG Zone Y-ranges | Hardcoded constants become standard | HIGH |
| Variant Grammar rules | VARIANT_RULES dict | HIGH |
| Feature support classification | FEATURE_SUPPORT dict | MEDIUM |
| Body category support mapping | BODY_CATEGORY_SUPPORT dict | MEDIUM |

---

## 9. IBG Semantic Pressure Assessment

### 9.1 High-Pressure Terms (Require C2 Attention)

| Term Category | Count | Pressure Level | Reason |
|---------------|-------|----------------|--------|
| ZoneId vocabulary | 15 | HIGH | Defines morphology regions |
| PrimitiveType vocabulary | 14 | HIGH | Defines contour semantics |
| BodyMorphologyClass | 10 | HIGH | Defines body classification |
| Behavior vocabularies | 18 | HIGH | Define body characteristics |

### 9.2 IBG Constitutional Gaps

| Gap | Description | C2 Priority |
|-----|-------------|-------------|
| Zone boundary governance | Y-range values are arbitrary | HIGH |
| Primitive classification rules | Inference logic unverified | MEDIUM |
| Variant rule library | VARIANT_RULES as canonical? | HIGH |
| Coordinate normalization | Centerline detection unverified | MEDIUM |

---

## 10. Cross-Reference Status

### 10.1 vs lifecycle_registry.json

| Geometry Term | In Registry? | Status |
|---------------|--------------|--------|
| `supported` | No | CadSemantics local |
| `unsupported` | No | CadSemantics local |
| `SUPPORTED_PROTOTYPE` | No | TopologyBuilder local |
| `UNSUPPORTED_RUNTIME` | No | TopologyBuilder local |

### 10.2 vs semantic_registry.json

| Geometry Concept | In Registry? | Status |
|------------------|--------------|--------|
| Body category | No | **Candidate for registration** |
| Topology tier | No | **Candidate for registration** |
| Zone classification | No | **Candidate for registration** |

### 10.3 vs authority_chain_registry.json

| Authority Chain | Declared? | Status |
|-----------------|-----------|--------|
| CadSemantics → TopologyBuilder | No | **Authority gap** |
| IBG → Harvest | No | **Authority gap** |
| Vectorizer → IBG | No | **Authority gap** |

---

## 11. Related Documents

- `docs/governance/coordination/C1_RUNTIME_CAM_INVENTORY.md`
- `docs/governance/coordination/SEMANTIC_COLLISION_LOG.md`
- `docs/governance/ontology/lifecycle_registry.json`
- `docs/handoffs/CAM_RUNTIME_DISPATCHER_DEVELOPER_HANDOFF.md`
- `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md`

---

## C1 Status

**Collected:** Yes  
**Vocabularies Inventoried:** 24 enums, 100+ terms  
**IBG Sandbox Terms:** 72 terms across 12 vocabularies  
**Sandbox Pressure:** HIGH for IBG, MEDIUM-HIGH for Harvest  
**Decisions Made:** None  
**Next Phase:** C2 reconciliation (not this document)
