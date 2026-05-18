# C2 Geometry Propagation Analysis

```
C2-A — CONSTITUTIONAL ARBITRATION PHASE
GEOMETRY AUTHORITY DECOMPOSITION
PROPAGATION PATH MAPPING
```

**Phase:** C2-A  
**Owner:** Terminal 2 (Runtime/CAM) + Terminal 5 (Export/Serialization) Review  
**Date:** 2026-05-18  
**Status:** Analysis Complete — Awaiting Arbitration

---

## 1. Authority Statement

This document maps geometry propagation paths across runtime and export systems.

This document does NOT:
- Change runtime behavior
- Modify export systems
- Mandate propagation changes
- Create enforcement rules

This document DOES:
- Map authority movement
- Identify escalation risks
- Document propagation boundaries
- Surface containment requirements

---

## 2. Propagation Path Inventory

### 2.1 Runtime Geometry Flow

```
┌─────────────────┐
│ Geometry Source │  (AUTHORITY ORIGIN UNRESOLVED)
│   (Unresolved)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Operation     │  Transforms geometry for execution
│   Resolution    │  Role: constrained_transformer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Topology     │  Constructs 3D shell topology
│    Builder      │  Role: operational_consumer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CAM Runtime   │  Executes operations
│                 │  Role: operational_consumer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RuntimeResult   │  observationalOnly: true
│     Base        │  Role: observational_consumer
└─────────────────┘
```

**Authority Checkpoints:**
- Operation Resolution: Transforms, does not redefine
- Topology Builder: Constructs, does not own
- CAM Runtime: Executes, does not create authority
- RuntimeResultBase: Observational scaffold (hard invariant)

**Risk Assessment:** LOW — Hard invariants enforce non-authority.

---

### 2.2 Export Propagation Flow

```
┌─────────────────┐
│ Geometry Source │  (AUTHORITY ORIGIN UNRESOLVED)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Body Export    │  Bridges geometry to export
│    Bridge       │  Role: constrained_transformer
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────────────┐
│ Export │ │ IBGMorphology      │  ⚠️ RISK: Sandbox propagation
│ Object │ │ Extension          │  Role: UNCLEAR
└───┬────┘ └─────────┬──────────┘
    │                │
    └───────┬────────┘
            ▼
┌─────────────────┐
│   Translator    │  Routes to target format
│    Registry     │  Role: observational_consumer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DXF/JSON/CAD    │  Emits format
│  Translator     │  Role: serializer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output File    │  serialized_geometry
└─────────────────┘
```

**Authority Checkpoints:**
- Body Export Bridge: Transforms, passes IBG data through
- Export Object: Contains core geometry
- IBGMorphologyExtension: **RISK SURFACE** — sandbox data propagates
- Translator: Encodes, does not define
- Output: serialized_geometry layer

**Risk Assessment:** MEDIUM — IBG sandbox propagation path exists.

---

### 2.3 IBG Propagation Paths

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IBG SANDBOX                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Body      │  │  Variant    │  │   Zones     │                 │
│  │   Grid      │  │  Grammar    │  │  (15 zones) │                 │
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
└──────────────────────────┼──────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ IBGMorphology│  │   Corpus     │  │ Visualization│
│  Extension   │  │   Builder    │  │  (UI Zones)  │
│              │  │              │  │              │
│ ⚠️ Export    │  │ ⚠️ Training  │  │ ⚠️ Present.  │
│   propagation│  │   weight     │  │   authority  │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Propagation Risks:**

| Path | Risk | Mechanism |
|------|------|-----------|
| IBG → Export | HIGH | IBGMorphologyExtension carries sandbox data |
| IBG → Corpus | MEDIUM | Training data accumulates authority weight |
| IBG → Visualization | LOW | Presentation could become de facto truth |

---

### 2.4 Adapter Propagation Flow

```
┌─────────────────┐
│ CAD Semantic    │  Defines semantic configuration
│  Definition     │  Role: constrained_transformer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Component       │  Routes to adapters
│  Router         │
└────────┬────────┘
         │
    ┌────┴─────────────┬────────────────┐
    │                  │                │
    ▼                  ▼                ▼
┌────────┐     ┌────────────┐    ┌────────────┐
│ Body   │     │ Soundhole  │    │  Bridge    │
│ Adapter│     │  Adapter   │    │  Adapter   │
└───┬────┘     └─────┬──────┘    └─────┬──────┘
    │                │                 │
    └────────────────┼─────────────────┘
                     ▼
            ┌─────────────────┐
            │ Translator      │
            │ Output          │
            └─────────────────┘
```

**Authority Risk:** Adapters may silently transform geometry meaning.

---

### 2.5 Topology Conversion Flow

```
┌─────────────────┐
│ 7M/MRP Topology │  Semantic spatial relationships
│ (morphology_    │  Regions, connectivity
│  topology)      │
└────────┬────────┘
         │
         │ ⚠️ SEMANTIC BOUNDARY
         │ Different meaning across boundary
         │
         ▼
┌─────────────────┐
│ CAM Topology    │  Geometric surface continuity
│ (surface_       │  G0/G1/G2 junctions
│  topology)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Shell          │  3D construction
│  Construction   │
└─────────────────┘
```

**Risk Assessment:** HIGH — Same term, different semantics.
**Collision Reference:** COLL-G001

---

### 2.6 Derived Geometry Escalation Paths

```
                    ┌─────────────────┐
                    │ Authoritative   │
                    │   Geometry      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Derived      │
                    │   Computation   │
                    └────────┬────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Cached     │    │   Repeated   │    │   Training   │
│   Values     │    │   Usage      │    │   Data       │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ ⚠️ ESCALATION RISK     │
              │ Derived treated as     │
              │ authoritative          │
              └────────────────────────┘
```

**Escalation Mechanisms:**

| Mechanism | Risk | Mitigation |
|-----------|------|------------|
| Caching | MEDIUM | Cache derived, not authority |
| Repeated usage | MEDIUM | Usage frequency ≠ authority |
| Training data | HIGH | Training weight ≠ truth |
| Absence of provenance | HIGH | Provenance mandatory |

---

## 3. Explicit System Analysis

### 3.1 IBGMorphologyExtension

**Location:** `app/export/body_export_bridge.py:163-172`

**Data Propagated:**
- `radii_by_zone` — Maps ZoneId to radius values
- `side_heights_mm` — IBG-derived height measurements
- `dimensions` — IBG-computed dimensional data
- `confidence` — IBG classification confidence

**Propagation Path:**
```
IBG Body Grid → MorphologyDescriptor → IBGMorphologyExtension → Export Object → Translator → Output File
```

**Risk Analysis:**
| Risk | Severity | Description |
|------|----------|-------------|
| Sandbox escape | HIGH | IBG vocabulary reaches production output |
| Authority inference | MEDIUM | Consumers may treat as authoritative |
| Format authority | MEDIUM | Serialized IBG data may become ground truth |

**Containment Requirement:**
- Add explicit `advisory_only: bool = True` field
- Document consumption constraints
- Consider separate `IBGAdvisoryData` type

---

### 3.2 Topology Builders

**Location:** `app/cam/topology_builder/`

**Contracts:**
- `ContinuityLevel`: G0, G1, G2
- `ShellType`: flat_extrusion, lofted, swept, composite
- `TopologyTier`: PROTOTYPE, PRODUCTION

**Authority Analysis:**
| Aspect | Status |
|--------|--------|
| Consumes geometry | YES |
| Defines geometry | NO |
| Creates topology | YES (surface_topology) |
| Claims authority | NO |

**Risk Assessment:** LOW — Clear operational consumer role.

---

### 3.3 Export Translators

**Location:** `app/cam/translators/`

**Authority Constraints:**
- `machine_output_supported=False` — Enforced by model validator
- `serializer_invocation_allowed=False` — Execution quarantine

**Propagation Role:** Pure serializer — encodes, does not define.

**Risk Assessment:** LOW — Strong quarantine enforcement.

---

### 3.4 DXF Preparation

**Location:** `app/cam/dxf_translator_boundary.py`

**Authority Analysis:**
| Aspect | Status |
|--------|--------|
| Receives geometry | From Export Object |
| Transforms geometry | For format encoding only |
| Defines geometry | NO |
| Creates authority | NO |

**Risk Assessment:** LOW — Format boundary respected.

---

### 3.5 Geometry Adapters

**Location:** Various `*_adapter.py` files

**Authority Risk:**
Adapters may silently transform geometry representation without explicit authority transfer.

**Containment Requirement:**
- Adapters must not redefine geometry meaning
- Transformations must be representational only
- Authority passthrough, not creation

---

### 3.6 Serializer Validators

**Location:** `app/export/` model validators

**Enforcement Points:**
| Validator | Purpose | Status |
|-----------|---------|--------|
| `machine_output_supported` | Block machine output | ENFORCED |
| `serializer_invocation_allowed` | Block execution | ENFORCED |
| Gate validation | Block red-gated exports | ENFORCED |

**Risk Assessment:** LOW — Strong constitutional restraint.

---

## 4. Risk Summary

### High Risk Paths

| Path | Risk | Priority |
|------|------|----------|
| IBG → Export | Sandbox vocabulary escape | CRITICAL |
| IBG → Corpus | Training authority accumulation | HIGH |
| Derived → Cached | Escalation to authority | HIGH |

### Medium Risk Paths

| Path | Risk | Priority |
|------|------|----------|
| Topology conversion | Semantic meaning change | MEDIUM |
| Adapter transformation | Silent authority mutation | MEDIUM |
| Format serialization | Format becoming truth | MEDIUM |

### Low Risk Paths (Healthy)

| Path | Status | Evidence |
|------|--------|----------|
| CAM Runtime | Contained | Hard invariants |
| Export Translators | Contained | Quarantine enforced |
| DXF Preparation | Contained | Format boundary |

---

## 5. Validator Enforcement Points

### Current Enforcement

| Point | Location | Type |
|-------|----------|------|
| RuntimeResultBase.observationalOnly | `runtime_results.py:49` | Structural |
| machine_output_supported | Model validators | Structural |
| serializer_invocation_allowed | Quarantine | Structural |
| Gate validation | Export bridge | Behavioral |

### Required Enforcement (C2 Recommendation)

| Point | Purpose | Status |
|-------|---------|--------|
| IBG advisory flag | Mark sandbox data as advisory | PROPOSED |
| Derived provenance | Require provenance on derived | PROPOSED |
| Authority boundary logging | Track authority flow | PROPOSED |

---

## 6. Containment Recommendations

### For IBG Propagation

```
1. Add `advisory_only: bool = True` to IBGMorphologyExtension
2. Document that downstream systems must NOT treat as authoritative
3. Consider separate `IBGAdvisoryData` type with explicit constraints
4. Log warning when IBG data enters production paths
```

### For Derived Geometry

```
1. Require provenance on all derived values
2. Require confidence/assumptions on all derived values
3. Cache derived values, not authority claims
4. Document derivation chains
```

### For Topology Conversion

```
1. Explicit namespace: morphology_topology vs surface_topology
2. Document semantic boundary
3. No implicit conversion between semantic types
```

---

## 7. Related Documents

### C1 Evidence

- `export_serialization/SEMANTIC_COLLISION_LOG.md` — COLL-E002
- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md` — COLL-G001
- `C1_STRATEGIC_FINDINGS.md` — Geometry authority risk

### Framework Documents

- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_GEOMETRY_OWNERSHIP_TOPOLOGY.md` — Domain mapping
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Term decomposition

---

*C2-A Geometry Propagation Analysis — Analysis Complete*
