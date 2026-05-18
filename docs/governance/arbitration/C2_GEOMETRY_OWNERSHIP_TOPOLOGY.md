# C2 Geometry Ownership Topology

```
C2-A — CONSTITUTIONAL ARBITRATION PHASE
GEOMETRY AUTHORITY DECOMPOSITION
OWNERSHIP TOPOLOGY MAPPING
```

**Phase:** C2-A  
**Owner:** Terminal 1 (Governance Integration Lead)  
**Date:** 2026-05-18  
**Status:** Decomposition Complete — Awaiting Arbitration

---

## 1. Authority Statement

This document maps geometry authority relationships across domains.

This document does NOT:
- Assign canonical geometry ownership
- Federate geometry domains
- Resolve authority disputes
- Mandate implementation

This document DOES:
- Map current authority relationships
- Identify ownership candidates
- Document consumption patterns
- Surface arbitration requirements

---

## 2. Ownership Role Reference

| Role | Meaning | Rights |
|------|---------|--------|
| **authoritative_owner** | Defines geometry truth | Create/mutate meaning |
| **constrained_transformer** | Adapts geometry | Transform, not redefine |
| **serializer** | Emits representation | Encode only |
| **observational_consumer** | Reads geometry | Read only |
| **operational_consumer** | Runtime consumption | Consume for execution |
| **sandbox_incubator** | Experimental producer | Pre-governance creation |
| **derived_producer** | Computes interpretations | Derive, not define |

---

## 3. Domain Authority Map

### Runtime/CAM Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| CAM Topology Builder | operational_consumer | operational_geometry | Consumes geometry for shell construction |
| RuntimeResultBase | observational_consumer | operational_geometry | `observationalOnly: Literal[True]` enforced |
| Operation Resolution | constrained_transformer | operational_geometry | Transforms for execution |
| CAM Runtime | operational_consumer | operational_geometry | Executes, does not define |

**Authority Status:** Clear non-owner discipline observed.

**Key Evidence:**
- `runtime_results.py:49` — `observationalOnly: Literal[True]`
- `translator_execution_quarantine.py` — `serializer_invocation_allowed: false`

---

### Export/Serialization Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| DXF Translator | serializer | serialized_geometry | Emits format, no authority |
| Body Export Bridge | serializer | serialized_geometry | Passes IBG data through |
| CAD Semantics | constrained_transformer | serialized_geometry | Translates, does not define |
| Translator Registry | observational_consumer | serialized_geometry | Routes, no authority |

**Authority Status:** Strong non-authority enforcement via model validators.

**Key Evidence:**
- `cad_semantics.py` — `machine_output_supported=False` enforced
- `translator_execution_quarantine.py` — Execution prohibited

**Risk Surface:** `IBGMorphologyExtension` propagates sandbox data (COLL-E002).

---

### IBG Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| Body Grid | sandbox_incubator | sandbox_geometry | Pre-governance vocabulary |
| Variant Grammar | sandbox_incubator | morphology_geometry | Creates classification without governance |
| Zone System | sandbox_incubator | sandbox_geometry | 15 zones without 7M registration |
| Primitives | sandbox_incubator | sandbox_geometry | 14 types without governance |
| Morphology Descriptor | sandbox_incubator | morphology_geometry | De facto morphology authority |

**Authority Status:** SANDBOX — no constitutional authority.

**Key Evidence:**
- Files untracked in git
- No 7N consumer registration
- COLL-G002: Morphology authority gap
- COLL-G005: Primitive vocabulary ungoverned

**Risk Surface:** High pressure to treat sandbox vocabulary as authoritative.

---

### Acoustics Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| AcousticState | observational_consumer | derived_geometry | Consumer interface pattern |
| MeasurementArchive | observational_consumer | derived_geometry | Geometry summary, not ownership |
| DiagnosticSnapshot | observational_consumer | derived_geometry | Observational scaffold |

**Authority Status:** REFERENCE PATTERN — exemplary consumer discipline.

**Key Evidence:**
- `ApertureGeometryLike` — explicit consumer interface
- Code comment: "reference, not merged"
- Mandatory confidence on derived values

---

### Visualization Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| UI Components | observational_consumer | presentation_geometry | Display only |
| Preview Systems | observational_consumer | presentation_geometry | No authority claim |
| SVG Renderers | constrained_transformer | presentation_geometry | Transform for display |

**Authority Status:** Healthy presentation boundaries observed.

---

### Morphology Harvest Domain

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| Corpus Builder | derived_producer | morphology_geometry | Accumulates from IBG |
| Training Data | derived_producer | morphology_geometry | ML training source |
| Classification Cache | derived_producer | morphology_geometry | Cached classifications |

**Authority Status:** Derived producer — accumulates semantic weight through use.

**Risk Surface:** Training data becomes de facto authority over time.

---

### Vectorizer Domain (Placeholder)

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| Blueprint Extraction | UNRESOLVED | UNRESOLVED | Creates geometry from images |
| Scale Detection | derived_producer | derived_geometry | Computes scale factor |
| Contour Detection | derived_producer | derived_geometry | Extracts contours |

**Authority Status:** UNRESOLVED — extraction/authority boundary unclear.

**Questions:**
- Does vectorizer create authoritative geometry?
- Is extracted geometry derived or authoritative?
- Who owns geometry after extraction?

---

### MRP Domain (Placeholder)

| System | Current Role | Layer | Evidence |
|--------|--------------|-------|----------|
| 7M Registry | governance_authority | authoritative_geometry | Registers canonical terms |
| 7N Consumer Registry | governance_authority | authoritative_geometry | Registers consumption |
| Morphology Contract | authoritative_owner | morphology_geometry | Declared owner |
| Topology Contract | authoritative_owner | morphology_geometry | Declared owner |

**Authority Status:** Constitutional authority declared but not operational.

**Questions:**
- Does 7M registration create authority or document it?
- What is the relationship between registration and implementation?

---

## 4. Cross-Domain Boundaries

### Authority Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTHORITATIVE LAYER (UNRESOLVED)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ Instrument │  │  Template  │  │ Vectorizer │  │    MRP     │    │
│  │   Spec?    │  │ Definition?│  │ Extraction?│  │ Registry?  │    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘    │
│        │               │               │               │            │
│        └───────────────┴───────┬───────┴───────────────┘            │
│                                │ AUTHORITY ORIGIN UNCLEAR           │
└────────────────────────────────┼────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OPERATIONAL LAYER                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│  │ CAM Runtime│  │  Topology  │  │ Operation  │                    │
│  │            │  │  Builder   │  │ Resolution │                    │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                    │
│        │               │               │                            │
│        └───────────────┴───────┬───────┘                            │
│                                │ CONSUMES, DOES NOT DEFINE          │
└────────────────────────────────┼────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   DERIVED     │ │ PRESENTATION  │ │  SERIALIZED   │ │   SANDBOX     │
├───────────────┤ ├───────────────┤ ├───────────────┤ ├───────────────┤
│ Acoustics     │ │ UI Components │ │ DXF Export    │ │ IBG Body Grid │
│ Helmholtz Est │ │ Preview       │ │ JSON Export   │ │ Morphology    │
│ Zone Radii    │ │ SVG Render    │ │ CAD Translate │ │ Primitives    │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
 NON-AUTHORITATIVE  NON-AUTHORITATIVE  NON-AUTHORITATIVE  CONTAINED
```

---

## 5. Consumption Patterns

### Healthy Consumption (Observed)

| Consumer | Source | Pattern | Status |
|----------|--------|---------|--------|
| Acoustics | Geometry | Consumer interface | REFERENCE |
| CAM Runtime | Geometry | Hard invariants | STRONG |
| Export | Geometry | Quarantine enforced | STRONG |

### Risk Consumption (Observed)

| Consumer | Source | Pattern | Risk |
|----------|--------|---------|------|
| Export | IBG | IBGMorphologyExtension | Sandbox propagation |
| Corpus | IBG | Training accumulation | Implicit authority |
| Visualization | IBG | Zone rendering | Presentation authority |

---

## 6. Unresolved Authority Surfaces

### Primary Unresolved Questions

| Question | Domains Affected | Priority |
|----------|------------------|----------|
| Who owns body outline definition? | All | CRITICAL |
| Does extraction create authority? | Vectorizer, MRP | HIGH |
| Does user input create authority? | Template, Spec | HIGH |
| Can classification exist without geometry authority? | IBG, Morphology | HIGH |
| Does 7M registration create or document authority? | MRP, All | MEDIUM |

### Authority Candidates

| Candidate | Evidence | Gaps |
|-----------|----------|------|
| Instrument Spec JSON | Contains canonical dimensions | User input, not system truth |
| Template Definition | User-created geometry | User authority, not system |
| Vectorizer Extraction | Creates geometry from images | Input is external, not owned |
| MRP Registry | Constitutional registration | Registry vs implementation gap |

---

## 7. Federation Readiness

### Ready for Federation

| Domain | Readiness | Evidence |
|--------|-----------|----------|
| Acoustics | HIGH | Consumer-without-authority discipline |
| CAM Runtime | HIGH | Hard invariants, observational scaffolds |
| Export | HIGH | Strong quarantine enforcement |
| Presentation | MEDIUM | Healthy boundaries, not documented |

### Not Ready for Federation

| Domain | Readiness | Blocker |
|--------|-----------|---------|
| IBG | LOW | Sandbox containment required first |
| Geometry Authority | CRITICAL | Origin unresolved |
| Vectorizer | LOW | Authority boundary undefined |
| MRP | MEDIUM | Registry/implementation gap |

---

## 8. Arbitration Requirements

### Required Before Federation

1. **Resolve authoritative geometry origin**
   - Where does geometry truth begin?
   - What creates geometry authority?

2. **Contain IBG sandbox**
   - Explicit sandbox boundaries
   - Advisory-only propagation
   - Governance graduation gate

3. **Define vectorizer authority boundary**
   - Is extraction derivation or creation?
   - Who owns extracted geometry?

4. **Clarify MRP registry relationship**
   - Registration as documentation vs authority creation
   - 7M/7N operational relationship

---

## 9. Related Documents

### C1 Foundation

- `C1_STRATEGIC_FINDINGS.md` — Geometry authority risk surface
- `geometry_morphology_topology/SEMANTIC_COLLISION_LOG.md` — IBG collisions
- `export_serialization/SEMANTIC_COLLISION_LOG.md` — Export propagation

### Framework Documents

- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Layer definitions
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Term decomposition
- `C2_GEOMETRY_PROPAGATION_ANALYSIS.md` — Flow analysis

---

*C2-A Geometry Ownership Topology — Mapping Complete*
