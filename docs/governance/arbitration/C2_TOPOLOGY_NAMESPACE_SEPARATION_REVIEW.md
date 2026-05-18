# C2 Topology Namespace Separation Review

```
C2-A — TERMINAL 3 REVIEW ADDENDUM
TOPOLOGY SEMANTIC DIFFERENTIATION VALIDATION
FLATTENING RISK ANALYSIS
```

**Phase:** C2-A  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** REVIEW COMPLETE — TENSIONS IDENTIFIED

---

## 1. Authority Statement

This document validates topology namespace decomposition quality and identifies remaining flattening risks.

This document:
- Validates decomposition integrity
- Identifies unresolved topology ambiguities
- Classifies remaining flattening risks
- Maps future arbitration needs

This document does NOT:
- Normalize topology globally
- Choose between MRP and CAM semantics
- Federate topology vocabulary
- Mandate implementation changes

---

## 2. Core Constitutional Principle

```
SHARED TERMINOLOGY DOES NOT IMPLY SHARED ONTOLOGY
```

This principle governs all topology decomposition validation.

### The Flattening Danger

The greatest risk is:

```
Multiple semantically distinct topology systems
being collapsed into one universal topology concept
```

Topology flattening would:
- Destroy MRP spatial semantics
- Corrupt CAM manufacturing intent
- Create ungovernable semantic debt
- Block future federation

---

## 3. Topology Semantic Domains

### 3.1 MRP Topology (morphology_topology)

**Source:** 7M Registry (`canonical_ontology_registry.py:472`)

**Definition:**
```
Semantic structure describing spatial relationships, regions,
and connectivity under MRP governance
```

**Semantic Content:**
| Concept | Meaning | Example |
|---------|---------|---------|
| Region | Named spatial area | upper_bout, waist, lower_bout |
| Connectivity | How regions relate | waist connects upper/lower bout |
| Boundary | Region interface | bout-to-waist transition |
| Partition | Spatial subdivision | body divided into zones |

**Authority Status:** 7M registered, MRP governance

---

### 3.2 CAM Topology (surface_topology)

**Source:** TopologyBuilder (`topology_builder/contracts.py:33`)

**Definition:**
```
3D shell construction with geometric continuity constraints
(G0 positional, G1 tangent, G2 curvature)
```

**Semantic Content:**
| Concept | Meaning | Example |
|---------|---------|---------|
| Continuity | Junction smoothness | G0, G1, G2 |
| Shell | 3D surface assembly | lofted body shell |
| Junction | Surface connection | edge blend |
| Tier | Strictness level | PROTOTYPE, PRODUCTION |

**Authority Status:** CAM operational, manufacturing-scoped

---

### 3.3 Semantic Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                    MRP TOPOLOGY DOMAIN                       │
│                                                              │
│   "Where is the waist?"                                      │
│   "How do the bouts connect?"                                │
│   "What regions does this body have?"                        │
│                                                              │
│   Answer: SPATIAL RELATIONSHIPS                              │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ SEMANTIC BOUNDARY
                         │ Different questions, different answers
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAM TOPOLOGY DOMAIN                       │
│                                                              │
│   "Is this junction smooth enough to machine?"               │
│   "What continuity does this shell require?"                 │
│   "Can we achieve G2 at this transition?"                    │
│                                                              │
│   Answer: MANUFACTURING CONTINUITY                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Decomposition Quality Assessment

### 4.1 Namespace Decomposition (from C2_GEOMETRY_NAMESPACE_COLLISIONS.md)

| Proposed Namespace | Purpose | Domain | Quality |
|-------------------|---------|--------|---------|
| `morphology_topology` | Spatial region relationships | MRP | ADEQUATE |
| `surface_topology` | Geometric surface continuity | CAM | ADEQUATE |
| `manufacturing_topology` | Shell construction | CAM | REDUNDANT |

**Assessment:**
- `morphology_topology` and `surface_topology` preserve semantic distinction
- `manufacturing_topology` may be redundant with `surface_topology`
- No flattening in current decomposition

### 4.2 Zone/Region Decomposition

| Proposed Namespace | Purpose | Domain | Quality |
|-------------------|---------|--------|---------|
| `morphology_zone` | IBG body partition | IBG (sandbox) | ADEQUATE |
| `spatial_region` | MRP region contract | MRP (governance) | ADEQUATE |
| `operational_region` | CAM processing areas | CAM (runtime) | ADEQUATE |

**Assessment:**
- Three-way split preserves semantic distinctions
- IBG zones remain sandbox-scoped
- MRP regions maintain governance authority
- CAM regions serve operational purpose

---

## 5. Remaining Flattening Risks

### 5.1 RISK: Topology Term Reuse Without Namespace

**Severity:** HIGH

**Description:**
Code may use "topology" without namespace prefix, implicitly assuming one semantic domain.

**Evidence:**
- `topology_builder/contracts.py` uses `TopologyTier`, `TopologyValidation`
- MRP uses `topology` in 7M definition
- No current enforcement of namespace prefixing

**Mitigation:**
- Document namespace requirement
- Add code comments at semantic boundaries
- C3: Consider lint rule for unprefixed "topology" usage

---

### 5.2 RISK: IBG Zone Vocabulary Treating as MRP Region

**Severity:** MEDIUM

**Description:**
IBG's 15 zones (sandbox) may be consumed as if they were MRP's spatial regions (governance).

**IBG Zones (sandbox):**
```
centerline, upper_bout, waist, lower_bout, horn_left, horn_right,
cutaway_left, cutaway_right, neck_pocket, bridge_region, butt_end,
shoulder_left, shoulder_right, apex_upper, apex_lower
```

**MRP Region Contract (governance):**
Generic `RegionContract` without specific region names.

**Risk:**
- IBG zone names could become de facto MRP region names
- Sandbox vocabulary would escape to governance

**Mitigation:**
- IBG zones must remain `morphology_zone` namespace
- MRP region names require separate governance ratification
- No automatic mapping between IBG zones and MRP regions

---

### 5.3 RISK: Continuity Levels Confused With Spatial Topology

**Severity:** LOW

**Description:**
CAM's `ContinuityLevel` (G0, G1, G2) might be confused with MRP's spatial connectivity.

**CAM Continuity:**
```python
class ContinuityLevel(str, Enum):
    G0 = "G0"  # Position
    G1 = "G1"  # Tangent
    G2 = "G2"  # Curvature
```

**MRP Connectivity:**
```
How spatial regions relate (e.g., waist connects to bouts)
```

**Risk:**
- Low, because terminology is sufficiently different
- G0/G1/G2 are clearly manufacturing terms

**Mitigation:**
- Document distinction if confusion arises
- No immediate action required

---

### 5.4 RISK: Topology Decomposition Incomplete for Partitioning Semantics

**Severity:** MEDIUM

**Description:**
"Partition" semantics appear in both domains with different meanings:
- MRP: Spatial subdivision of body into regions
- CAM: Shell decomposition for manufacturing

**Evidence:**
- IBG zones partition body spatially
- CAM may partition shell for toolpath generation

**Mitigation:**
- Add `spatial_partition` vs `manufacturing_partition` distinction
- Document in namespace collisions addendum

---

### 5.5 RISK: Boundary Semantics Overloaded

**Severity:** MEDIUM

**Description:**
"Boundary" means different things:
- MRP: Interface between spatial regions (e.g., waist-to-bout boundary)
- CAM: Edge of toolpath or machining area
- IBG: Y-range constraints on zones

**Evidence:**
- IBG zones have Y-range boundaries (0.0 = butt, 1.0 = neck)
- CAM has toolpath boundaries
- MRP has region interface boundaries

**Mitigation:**
- Add `region_boundary` vs `toolpath_boundary` vs `zone_boundary` distinction
- Document in namespace collisions addendum

---

## 6. Unresolved Topology Tensions

### 6.1 TENSION: Should IBG Zones Map to MRP Regions?

**Question:**
When IBG graduates from sandbox, should IBG zone vocabulary become MRP region vocabulary?

**Position A — Yes, IBG zones inform MRP regions:**
- IBG has discovered useful spatial vocabulary
- Zone names are meaningful for instrument morphology
- MRP should adopt validated IBG discoveries

**Position B — No, IBG zones remain implementation detail:**
- MRP regions require separate governance process
- IBG zones are classification aids, not governance terms
- Mapping would conflate sandbox with governance

**Terminal 3 Assessment:**
Position B is constitutionally correct. IBG zones are `sandbox_geometry` and cannot become `authoritative_geometry` without explicit governance graduation. The namespace separation must be maintained even if IBG is later federated.

---

### 6.2 TENSION: Is TopologyTier a Governance or Runtime Concept?

**Question:**
`TopologyTier` (PROTOTYPE, PRODUCTION) — is this governance tier or runtime tier?

**Evidence:**
- Located in CAM topology builder (runtime)
- But uses "tier" which collides with governance tier (1, 2, 3)

**Assessment:**
This is COLL-G004 (tier overload). Current decomposition proposes `runtime_tier` for CAM usage. This is adequate — no topology-specific tension.

---

### 6.3 TENSION: Does Shell Construction Create Topology?

**Question:**
When CAM TopologyBuilder constructs a shell, is it creating topology or consuming geometry?

**Assessment:**
TopologyBuilder creates `surface_topology` (manufacturing continuity), not `morphology_topology` (spatial relationships). These are different semantic outputs. The terminology collision is the risk, not the function.

---

## 7. Namespace Stability Assessment

### 7.1 Stable Decompositions

| Decomposition | Status | Evidence |
|---------------|--------|----------|
| morphology_topology vs surface_topology | STABLE | Clear semantic distinction |
| zone vs region | STABLE | Sandbox vs governance boundary |
| primitive geometry vs morphology primitive | STABLE | Different abstraction levels |

### 7.2 Unstable Decompositions

| Decomposition | Status | Issue |
|---------------|--------|-------|
| partition semantics | UNSTABLE | Spatial vs manufacturing not distinguished |
| boundary semantics | UNSTABLE | Multiple meanings not namespace-separated |
| manufacturing_topology vs surface_topology | UNCLEAR | May be redundant |

---

## 8. Recommended Namespace Addendum

Based on this review, Terminal 3 recommends adding to `C2_GEOMETRY_NAMESPACE_COLLISIONS.md`:

### 8.1 Additional Collision: partition

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

---

### 8.2 Additional Collision: boundary

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

---

## 9. IBG Containment Validation

### 9.1 Current Containment Status

| IBG Component | Containment | Risk |
|---------------|-------------|------|
| Body Grid | Sandbox | LOW — file untracked |
| Variant Grammar | Sandbox | MEDIUM — creates classifications |
| Zones (15) | Sandbox | MEDIUM — may escape to regions |
| Primitives (14) | Sandbox | MEDIUM — may escape to geometry |
| MorphologyDescriptor | Sandbox | HIGH — de facto authority |

### 9.2 Containment Validation

**Proposal from Packet 001:** Add `advisory_only: bool = True` to IBGMorphologyExtension

**Terminal 3 Assessment:** ADEQUATE but INSUFFICIENT

**Recommendation:** In addition to advisory flag:
1. Document that IBG zone names are `morphology_zone`, NOT `spatial_region`
2. Document that IBG primitives are `morphology_primitive`, NOT `geometry_primitive`
3. Require explicit governance graduation for any IBG term to become MRP term
4. Block automatic namespace promotion

---

## 10. Packet 001 Review Notes

### 10.1 Terminal 3 Validation of Namespace Decomposition

**Status:** VALIDATED with additions

**Findings:**
- Topology semantic split (morphology_topology vs surface_topology) is ADEQUATE
- Zone/region decomposition is ADEQUATE
- Two additional collisions identified (partition, boundary)
- Manufacturing_topology may be redundant with surface_topology

### 10.2 Terminal 3 Validation of IBG Containment

**Status:** VALIDATED with recommendations

**Findings:**
- Advisory-only flag is necessary but not sufficient
- Namespace containment must also be documented
- IBG graduation must not automatically promote namespace

### 10.3 Terminal 3 Confirmation of Topology Semantic Split

**Status:** CONFIRMED

**Assessment:**
The morphology_topology vs surface_topology split correctly preserves semantic distinction. These are fundamentally different concepts:
- MRP topology answers: "What spatial structure does this instrument have?"
- CAM topology answers: "What manufacturing continuity does this shell require?"

These questions have different answers and must not collapse.

### 10.4 Terminal 3 Flagged Authority Candidate Gaps

**Gap 1:** No authority candidate for "spatial partition" vs "manufacturing partition"

**Gap 2:** No authority candidate for "boundary" disambiguation

**Gap 3:** Unclear if `manufacturing_topology` is a separate domain or subset of `surface_topology`

---

## 11. Escalation Candidates

### 11.1 Tier 2 Escalations (Arbitration Packet Scope)

| Issue | Recommendation |
|-------|----------------|
| partition collision | Add to C2_GEOMETRY_NAMESPACE_COLLISIONS.md |
| boundary collision | Add to C2_GEOMETRY_NAMESPACE_COLLISIONS.md |

### 11.2 Tier 3 Escalations (Human Arbitration Required)

| Issue | Recommendation |
|-------|----------------|
| Should manufacturing_topology merge with surface_topology? | Defer until CAM domain review |
| Should IBG zones inform MRP regions upon graduation? | Block until governance criteria defined |

---

## 12. Terminal 3 Dissent Record

### 12.1 Disagreement: manufacturing_topology redundancy

**Position:** Terminal 3 believes `manufacturing_topology` may be redundant with `surface_topology`.

**Reasoning:** Both describe CAM manufacturing continuity. Shell construction is a form of surface topology construction.

**Deferred:** This is not a blocking issue. Document disagreement, proceed with current decomposition.

### 12.2 Deferred Question: IBG Zone Graduation Path

**Question:** If IBG graduates, what happens to zone vocabulary?

**Terminal 3 Position:** Zone vocabulary should NOT automatically become MRP region vocabulary. Graduation should require separate namespace arbitration.

**Status:** DEFERRED — governance graduation criteria not yet defined.

---

## 13. Summary

### Decomposition Quality

| Aspect | Quality | Notes |
|--------|---------|-------|
| Topology semantic split | HIGH | morphology_topology vs surface_topology preserves distinction |
| Zone/region decomposition | HIGH | Sandbox vs governance boundary maintained |
| IBG containment | MEDIUM | Advisory flag needed + namespace documentation |
| Partition semantics | LOW | Collision not yet documented |
| Boundary semantics | LOW | Collision not yet documented |

### Flattening Risk Assessment

| Risk | Severity | Status |
|------|----------|--------|
| Topology term reuse without namespace | HIGH | Document + monitor |
| IBG zones → MRP regions | MEDIUM | Block without governance |
| Continuity ≠ connectivity confusion | LOW | No action required |
| Partition overload | MEDIUM | Add to collisions doc |
| Boundary overload | MEDIUM | Add to collisions doc |

### Terminal 3 Verdict

```
TOPOLOGY NAMESPACE SEPARATION: VALIDATED

Remaining work:
1. Add partition/boundary collisions to namespace document
2. Document IBG namespace containment beyond advisory flag
3. Clarify manufacturing_topology relationship to surface_topology
```

---

## 14. Related Documents

### C2 Arbitration

- `C2_ARBITRATION_FRAMEWORK.md` — Constitutional arbitration structure
- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Term decomposition (to update)
- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Flow analysis
- `packets/C2_GEOMETRY_ARBITRATION_PACKET_001.md` — Active packet (to update)

### C1 Foundation

- `C1_GEOMETRY_TOPOLOGY_SEMANTIC_INVENTORY.md` — Original inventory
- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md` — COLL-G001 evidence

### IBG Classification

- `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md` — IBG constitutional containment

---

*C2-A Terminal 3 Review — Topology Namespace Separation Validated*
