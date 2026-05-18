# C2 Topology Propagation Review

```
C2-B — CONSTITUTIONAL ARBITRATION PHASE
TOPOLOGY PROPAGATION ANALYSIS
SEMANTIC LEAKAGE PREVENTION
```

**Phase:** C2-B  
**Owner:** Terminal 2 (Runtime/CAM) + Terminal 5 (Export) Review  
**Date:** 2026-05-18  
**Status:** Analysis Complete — Awaiting Terminal Review

---

## 1. Purpose

This document analyzes topology semantic propagation paths to identify:
- Cross-domain leakage risks
- Authority escalation mechanisms
- Containment requirements
- Namespace boundary enforcement points

---

## 2. Topology Propagation Paths

### 2.1 MRP Topology Propagation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MRP GOVERNANCE LAYER                             │
│  ┌────────────┐                                                     │
│  │ 7M Registry│  morphology_topology registered                     │
│  │  topology  │                                                     │
│  └─────┬──────┘                                                     │
│        │                                                            │
│        │ GOVERNANCE BOUNDARY                                        │
└────────┼────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CONSUMER LAYER                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │ Morphology │  │ Spatial    │  │ Region     │                    │
│  │ Consumers  │  │ Reasoning  │  │ Consumers  │                    │
│  └────────────┘  └────────────┘  └────────────┘                    │
│                                                                     │
│  Status: Healthy — governance boundary respected                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Risk Assessment:** LOW — Clear governance boundary.

---

### 2.2 CAM Topology Propagation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAM TOPOLOGY BUILDER                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │ Continuity │  │  Shell     │  │ Topology   │                    │
│  │   Level    │  │  Type      │  │   Tier     │                    │
│  │ (G0/G1/G2) │  │            │  │            │                    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                    │
│        │               │               │                            │
│        └───────────────┼───────────────┘                            │
│                        │                                            │
│                        ▼                                            │
│               ┌─────────────────┐                                   │
│               │ Shell           │  surface_topology /               │
│               │ Construction    │  manufacturing_topology           │
│               └────────┬────────┘                                   │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RUNTIME EXECUTION                                │
│  ┌────────────┐                                                     │
│  │ CAM        │  Consumes topology for execution                    │
│  │ Runtime    │  observationalOnly enforced                         │
│  └────────────┘                                                     │
│                                                                     │
│  Status: Healthy — hard invariants protect boundary                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Risk Assessment:** LOW — Hard invariants enforce non-authority.

---

### 2.3 IBG Topology Propagation (RISK SURFACE)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IBG SANDBOX                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Zone      │  │ Morphology  │  │  Primitive  │                 │
│  │ Vocabulary  │  │ Vocabulary  │  │ Vocabulary  │                 │
│  │ (15 zones)  │  │ (10 classes)│  │ (14 types)  │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         └────────────────┼────────────────┘                         │
│                          │                                          │
│                          ▼                                          │
│                 ┌─────────────────┐                                 │
│                 │   Morphology    │                                 │
│                 │   Descriptor    │                                 │
│                 └────────┬────────┘                                 │
│                          │                                          │
│  SANDBOX BOUNDARY ═══════╪══════════════════════════════════════   │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ IBGMorphology│  │   Corpus     │  │ Visualization│
│  Extension   │  │   Builder    │  │              │
│              │  │              │  │              │
│ ⚠️ EXPORT    │  │ ⚠️ TRAINING  │  │ ⚠️ DISPLAY   │
│   LEAKAGE    │  │   HARDENING  │  │   AUTHORITY  │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Risk Assessment:** HIGH — Three propagation leakage paths identified.

---

## 3. IBG Export Leakage Analysis

### 3.1 Propagation Path

```
IBG MorphologyDescriptor
        │
        ▼
Body Export Bridge (body_export_bridge.py:163-172)
        │
        ▼
IBGMorphologyExtension
        │
        ├── radii_by_zone (ZoneId → radius)
        ├── side_heights_mm
        ├── dimensions
        └── confidence
        │
        ▼
Export Object
        │
        ▼
Translator Registry
        │
        ▼
DXF/JSON/CAD Output
```

### 3.2 Leaked Vocabulary

| Field | IBG Source | Constitutional Status |
|-------|------------|----------------------|
| `radii_by_zone` | ZoneId enum | Sandbox vocabulary |
| `side_heights_mm` | IBG computation | Derived geometry |
| `dimensions` | IBG computation | Derived geometry |
| `confidence` | IBG classification | Sandbox metric |

### 3.3 Risk Analysis

| Risk | Severity | Mechanism |
|------|----------|-----------|
| Sandbox vocabulary in production output | HIGH | ZoneId keys appear in export |
| Downstream authority inference | MEDIUM | Consumers may treat as canonical |
| Format authority creation | MEDIUM | Serialized IBG may become truth |

### 3.4 Containment Requirement

```
IBGMorphologyExtension must be marked advisory_only conceptually.
Downstream translators must NOT treat IBG data as authoritative.
Export consumers must understand sandbox provenance.
```

---

## 4. IBG Corpus Hardening Analysis

### 4.1 Propagation Path

```
IBG Classification
        │
        ▼
Corpus Builder
        │
        ├── Body outline + zone annotations
        ├── Primitive classifications
        └── Morphology class labels
        │
        ▼
Training Data
        │
        ▼
ML Model Training
        │
        ▼
Model Inference (future)
```

### 4.2 Hardening Mechanism

```
Repeated training on IBG vocabulary
creates implicit authority through model weights.
```

Even without constitutional registration:
- IBG zones become classification targets
- IBG primitives become feature labels
- IBG morphology classes become prediction outputs

### 4.3 Risk Analysis

| Risk | Severity | Mechanism |
|------|----------|-----------|
| Training authority | HIGH | Model learns IBG vocabulary |
| Semantic hardening | MEDIUM | Vocabulary becomes embedded |
| Inference authority | MEDIUM | Predictions use IBG terms |

### 4.4 Containment Requirement

```
Training data must carry sandbox provenance.
Model outputs must be labeled as derived/advisory.
IBG vocabulary in training does not create constitutional authority.
```

---

## 5. IBG Display Authority Analysis

### 5.1 Propagation Path

```
IBG Zone/Morphology/Primitive
        │
        ▼
UI Visualization
        │
        ├── Zone labels in UI
        ├── Morphology class display
        └── Primitive annotations
        │
        ▼
User Perception
```

### 5.2 Display Authority Risk

```
Users seeing IBG vocabulary in UI may assume canonical status.
Display repetition creates implicit authority.
```

### 5.3 Risk Analysis

| Risk | Severity | Mechanism |
|------|----------|-----------|
| Perceived authority | LOW | UI labels look official |
| User expectation | LOW | Users expect consistency |
| Documentation drift | LOW | IBG terms enter user docs |

### 5.4 Containment Requirement

```
UI should indicate sandbox/advisory status where practical.
User documentation should clarify IBG is experimental.
Display does not create constitutional authority.
```

---

## 6. Topology Semantic Boundary Analysis

### 6.1 MRP-CAM Topology Boundary

```
MRP: morphology_topology          CAM: surface_topology
         │                                  │
         │    ⚠️ SEMANTIC BOUNDARY          │
         │    Same word, different meaning  │
         └──────────────┬───────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ COLLISION RISK  │
              │ COLL-G001       │
              └─────────────────┘
```

### 6.2 Boundary Enforcement Points

| Point | Location | Enforcement |
|-------|----------|-------------|
| 7M Registration | canonical_ontology_registry.py | Governance term |
| Topology Builder | topology_builder/contracts.py | Operational term |
| Consumer APIs | Various | Should use namespaced terms |

### 6.3 Recommended Namespace Enforcement

```
When referring to MRP spatial topology: use morphology_topology
When referring to CAM surface continuity: use surface_topology
When referring to CAM shell construction: use manufacturing_topology
```

---

## 7. Continuity Propagation Analysis

### 7.1 Propagation Path

```
ContinuityLevel (G0/G1/G2)
        │
        ▼
Topology Builder
        │
        ▼
Shell Construction
        │
        ▼
CAM Runtime
        │
        ▼
Manufacturing Output
```

### 7.2 Independence Verification

Continuity semantics:
- Stays within CAM domain
- Does not leak to governance
- Does not contaminate MRP topology
- Remains manufacturing-scoped

**Risk Assessment:** LOW — Healthy containment.

### 7.3 Namespace Proposal

```
manufacturing_continuity
```

This explicitly separates continuity from topology namespace.

---

## 8. Zone/Region Propagation Analysis

### 8.1 IBG Zone Propagation

```
ZoneId (15 zones)
        │
        ├── IBGMorphologyExtension (export)
        ├── Corpus Builder (training)
        ├── UI Visualization (display)
        └── Zone Queries (internal)
```

### 8.2 MRP Region Propagation

```
RegionContract
        │
        └── Governance Consumers
```

### 8.3 Collision Risk

```
IBG zones and MRP regions describe spatial partitions.
Without namespace separation, consumers may conflate.
```

### 8.4 Namespace Enforcement

| Usage | Required Namespace |
|-------|-------------------|
| IBG body partitions | `morphology_zone` |
| MRP spatial contracts | `spatial_region` |
| CAM processing areas | `operational_region` |

---

## 9. Propagation Risk Summary

### 9.1 High Risk Paths

| Path | Risk | Containment |
|------|------|-------------|
| IBG → Export | Sandbox vocabulary leakage | advisory_only flag |
| IBG → Corpus | Training authority hardening | Provenance tagging |
| MRP-CAM topology | Semantic boundary collision | Namespace separation |

### 9.2 Medium Risk Paths

| Path | Risk | Containment |
|------|------|-------------|
| IBG → Display | Perceived authority | UI disclaimers |
| Zone/Region | Conflation | Namespace enforcement |
| Derived → Cached | Authority escalation | Provenance requirements |

### 9.3 Low Risk Paths (Healthy)

| Path | Status | Evidence |
|------|--------|----------|
| CAM Runtime | Contained | Hard invariants |
| Continuity | Contained | Manufacturing-scoped |
| MRP Topology | Contained | Governance boundary |

---

## 10. Terminal Review Requirements

### Terminal 2 — Runtime/CAM

- [ ] Validate surface_topology propagation paths
- [ ] Confirm manufacturing_continuity independence
- [ ] Review CAM runtime containment
- [ ] Flag any runtime topology leakage

### Terminal 5 — Export/Serialization

- [ ] Validate IBGMorphologyExtension containment
- [ ] Review export vocabulary propagation
- [ ] Confirm translator non-authority discipline
- [ ] Flag any format authority risks

---

## 11. Containment Recommendations Summary

### For IBG Export Leakage

```
1. Add advisory_only: true conceptually to IBGMorphologyExtension
2. Document that downstream systems must NOT treat as authoritative
3. Consider explicit provenance tagging in export output
```

### For IBG Corpus Hardening

```
1. Tag training data with sandbox provenance
2. Label model outputs as derived/advisory
3. Document that training does not create constitutional authority
```

### For Topology Semantic Boundary

```
1. Use namespaced terms in APIs: morphology_topology, surface_topology
2. Document semantic boundary clearly
3. Prevent implicit conversion between MRP and CAM topology
```

### For Zone/Region Conflation

```
1. Use morphology_zone for IBG partitions
2. Use spatial_region for MRP contracts
3. Use operational_region for CAM processing
```

---

## 12. Related Documents

### Primary Document

- `C2_TOPOLOGY_NAMESPACE_ARBITRATION.md` — Main decomposition

### Supporting Documents

- `C2_TOPOLOGY_COLLISION_APPENDIX.md` — Collision deepening
- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Geometry propagation (C2-A)

### C1 Evidence

- `export_serialization/SEMANTIC_COLLISION_LOG.md` — COLL-E002
- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md` — COLL-G001

---

*C2-B Topology Propagation Review — Analysis Complete*
