# C2-A — Geometry Authority Decomposition

**Status:** DRAFT  
**Owner:** Terminal 3  
**Date:** 2026-05-18  
**Depends On:** None (first packet)

---

## 1. Boundary Dispute

Geometry semantics are fragmented across multiple systems with overlapping authority claims:

| System | Claimed Authority | Constitutional Status |
|--------|-------------------|----------------------|
| IBG Body Grid | Primitive types, morphology classes, zones | Sandbox (unratified) |
| BOE | Approved geometry | Authoritative |
| CAM TopologyBuilder | Surface continuity (G0/G1/G2) | Operational |
| MRP | Spatial topology, regions | Declared (Tier 2) |
| Export Object | Manufacturing intent | Authoritative |

**Core dispute:**

No decomposition exists distinguishing:
- **Primitive geometry** — Points, lines, arcs, splines (mathematical)
- **Morphology semantics** — Body shape classification (semantic)
- **Spatial topology** — Regions, connectivity (spatial)
- **Surface topology** — Continuity constraints (manufacturing)
- **Manufacturing geometry** — CAM-ready representation (operational)

IBG has discovered 75+ vocabulary terms that create de facto geometry semantics without constitutional authority. These terms are operationally active but not governmentally ratified.

---

## 2. C1 Evidence

| Source | Finding |
|--------|---------|
| COLL-G001 | Topology semantic divergence — MRP "topology" (spatial relationships) vs CAM "topology" (G0/G1/G2 continuity) are fundamentally different concepts |
| COLL-G002 | Morphology authority gap — IBG implements `BodyMorphologyClass`, `MorphologyDescriptor`, `MorphologyPrimitive` without 7N registration |
| COLL-G003 | Zone vs Region vocabulary — IBG `ZoneId` (15 zones) overlaps with 7M `RegionContract` |
| COLL-G005 | Primitive vocabulary ungoverned — 14 `PrimitiveType` values form classification foundation without 7M registration |
| IBG_SANDBOX | 75+ unregistered terms creating semantic pressure |

### 2.1 IBG Vocabulary Pressure

From `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md`:

| Pressure Type | Severity | Evidence |
|---------------|----------|----------|
| Primitive grammar pressure | HIGH | 14 primitive types form classification foundation |
| Morphology vocabulary pressure | HIGH | 10 morphology classes create binding semantics |
| Geometry partition pressure | HIGH | 15 zones define spatial ontology |

### 2.2 Operational Dependencies

| Consumer | Dependency Type | Risk |
|----------|-----------------|------|
| MorphologyAnalyzer | Direct | Consumes IBG primitives |
| BodyEvidence | Direct | Uses IBG coordinate system |
| Constraint extractor | Interface | Can produce IBG-compatible output |
| Export Object | Extension | IBGMorphologyExtension propagates sandbox data |

---

## 3. Proposed Decomposition

### 3.1 Layer Decomposition

| Layer | Authority Owner | Scope | Registration |
|-------|-----------------|-------|--------------|
| **Primitive Geometry** | 7M (to register) | Points, lines, arcs, splines, basic curves | 7M Tier 1 |
| **Morphology Semantics** | MRP (authoritative) or IBG (advisory) | Body shape classification, variant grammar | Pending arbitration |
| **Spatial Topology** | MRP | Regions, connectivity, spatial relationships | 7M Tier 2 |
| **Surface Topology** | CAM | G0/G1/G2 continuity, manufacturing constraints | CAM-scoped |
| **Manufacturing Geometry** | Export Object | CAM-ready representation, translator input | Export pipeline |

### 3.2 Term Decomposition

| Current Term | Proposed Namespace | Owner |
|--------------|-------------------|-------|
| `topology` (MRP sense) | `spatial_topology` or `morphology_topology` | MRP |
| `topology` (CAM sense) | `surface_topology` or `continuity_topology` | CAM |
| `PrimitiveType` | `geometry_primitive` or remain IBG-scoped | Pending |
| `ZoneId` | `body_zone` or align with `RegionContract` | Pending |
| `BodyMorphologyClass` | `morphology_class` under MRP or remain IBG-scoped | Pending |

### 3.3 Authority Assignment Options

**Option A: IBG Remains Sandbox**

IBG vocabulary remains advisory. All geometry authority flows through BOE and Export Object. IBG is consumed but never authoritative.

- Pro: No constitutional change required
- Con: Operational dependencies continue without governance

**Option B: IBG Graduates to Advisory Authority**

IBG registers as 7N consumer with explicit advisory status. Morphology vocabulary is ratified as "advisory classification" distinct from "authoritative geometry."

- Pro: Semantic discoveries become governable
- Con: Requires 7N registration process

**Option C: IBG Decomposes into Layers**

IBG's 75+ terms decompose into separate governance domains:
- Primitive types → 7M primitive geometry
- Morphology classes → MRP morphology
- Zones → MRP spatial topology
- Coordinate semantics → Export Object

- Pro: Clean authority boundaries
- Con: Significant governance overhead

**Recommended:** Option A for C2-A, with Option C as future target after C2-B/C2-C.

---

## 4. Affected Systems

| System | Role | Impact |
|--------|------|--------|
| IBG Body Grid | Producer | Must declare sandbox status; consumers warned |
| BOE | Producer | Unchanged (authoritative) |
| MorphologyAnalyzer | Consumer | Must treat IBG as advisory |
| BodyEvidence | Consumer | Must treat IBG coordinates as derived |
| Export Object | Consumer | IBGMorphologyExtension marked advisory |
| CAM TopologyBuilder | Producer | Namespace changes for "topology" term |
| MRP | Authority | Receives spatial topology ownership |

---

## 5. Migration Path

### 5.1 Documentation-Only Changes

| File | Change |
|------|--------|
| `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md` | Add C2-A reference, confirm sandbox status |
| `body_grid/` modules | Add docstring noting sandbox/advisory status |
| `CANONICAL_ONTOLOGY_VOCABULARY.md` | Add geometry layer decomposition reference |
| `body_export_bridge.py` | Add docstring noting IBGMorphologyExtension is advisory |

### 5.2 Interface Changes (C3)

| Change | Scope | Risk |
|--------|-------|------|
| Add `advisory_only: bool = True` to IBGMorphologyExtension | Export pipeline | Low |
| Rename `topology` usages to namespace-qualified form | CAM, MRP | Medium |
| Register primitive geometry terms in 7M | Governance | Low |

### 5.3 Breaking Changes (C3+)

| Change | Scope | Risk |
|--------|-------|------|
| Decompose IBG vocabulary into separate modules | IBG | High |
| Require 7N registration for IBG consumers | Consumers | High |

---

## 6. Non-Migration Alternative

| Scenario | Consequence | Acceptable? |
|----------|-------------|-------------|
| Document boundaries only, no code changes | IBG continues creating de facto authority; consumers unclear on status | Conditional — acceptable short-term |
| Mark IBGMorphologyExtension advisory in docs only | Risk of downstream systems treating as authoritative | Conditional — acceptable if monitored |
| Leave topology term collision | Continued confusion between MRP and CAM meanings | No — namespace decomposition required |

---

## 7. Terminal Review

| Terminal | Scope | Status |
|----------|-------|--------|
| Terminal 1 | Framework compliance | ☐ Pending |
| Terminal 2 | Runtime compatibility (CAM topology) | ☐ Pending |
| Terminal 3 | Geometry/Morphology (owner) | ☐ Pending |
| Terminal 4 | Provenance preservation | ☐ Pending |
| Terminal 5 | Export boundary (IBGMorphologyExtension) | ☐ Pending |

---

## 8. Ratification Status

- [ ] All required terminals approved
- [ ] Human review scheduled
- [ ] Human review complete
- [ ] **RATIFIED**

---

## 9. Related Documents

- `inventory/C1_GEOMETRY_TOPOLOGY_SEMANTIC_INVENTORY.md` — C1 evidence
- `inventory/geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md` — Collision details
- `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md` — IBG constitutional status
- `MORPHOLOGY_RECONSTRUCTION_PLATFORM.md` — MRP governance
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — 7M registry

---

## 10. Open Questions

1. Should primitive geometry types be registered in 7M Tier 1, or remain implementation details?

2. Should IBG morphology vocabulary graduate to MRP authority, or remain permanently advisory?

3. Is namespace prefixing (`spatial_topology` vs `surface_topology`) sufficient, or is deeper separation required?

4. Should IBGMorphologyExtension gain an explicit `advisory_only` field, or is documentation sufficient?

5. What is the timeline for topology namespace decomposition in code (C3)?

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-05-18 | Initial draft from C1 freeze | Claude Code |
