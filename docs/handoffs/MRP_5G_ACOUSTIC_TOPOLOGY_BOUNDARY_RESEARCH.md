# MRP Dev Order 5G — Acoustic Topology Boundary Research Handoff

**Date:** 2026-05-14  
**Dev Order:** MRP-5G  
**Status:** COMPLETE

---

## Summary

MRP-5G established the architectural and governance boundaries for future acoustic topology runtime generation:

1. **Topology Authority Chain** — Explicit authority hierarchy from BOE to CAD kernel
2. **Topology Builder Model** — Recommended separate builder layer (pending MRP-5H validation)
3. **Runtime Rules** — Two-tier (PROTOTYPE/PRODUCTION) requirements
4. **Failure Classification** — Blocking vs warning severity with safe rejection protocol
5. **Readiness Matrix** — Instrument classification by topology runtime readiness
6. **Adaptive Boundary** — AI/LLM isolation from deterministic topology
7. **Kernel Evaluation** — Criteria for future CAD kernel selection

**Sprint Type:** Governance research (no runtime code)

---

## Deliverables

### 1. Topology Authority Chain

**Location:** `docs/architecture/TOPOLOGY_AUTHORITY_CHAIN.md`

**Authority Hierarchy:**
```
BOE (Geometry) → IMMUTABLE
    ↓
IBG (Morphology) → ADVISORY
    ↓
cad_semantics → EXTENDS
    ↓
Topology Builder → CONSTRUCTS (proposed)
    ↓
Translator → SERIALIZES
    ↓
CAD Kernel → IMPLEMENTS (behind adapter)
```

**Key Rule:**
> Topology builders may construct surfaces from approved geometry. They may not reinterpret or mutate approved geometry intent.

### 2. Topology Builder Model

**Location:** `docs/architecture/ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md`

**Recommendation:** RECOMMENDED_PENDING_MRP_5H_VALIDATION

**Rationale:**
- Topology construction too semantically heavy for translators
- Separation enables kernel-agnostic validation
- Multiple translators can share topology construction
- Clear semantic → topology → serialization boundaries

**Proposed Interface:**
```python
TopologyRequest → TopologyBuilder → TopologyResult → Translator
```

### 3. Runtime Rules (Two Tiers)

**Location:** `docs/governance/ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md`

**PROTOTYPE Tier:**
- G0 continuity acceptable
- Gap tolerance 0.1mm
- Warnings on quality issues
- Clear "prototype" marking

**PRODUCTION Tier:**
- G1 continuity required
- Kernel-verified closure
- Strict geometry preservation
- Manufacturing-ready output

**Junction Continuity:**
| Junction | PROTOTYPE | PRODUCTION |
|----------|-----------|------------|
| Rim ↔ Top | G0 acceptable | G1 required |
| Rim ↔ Back | G0 acceptable | G1 required |
| Neck transition | G0 | G0 |

### 4. Failure Classification

**Location:** `docs/governance/TOPOLOGY_FAILURE_CLASSIFICATION.md`

**Severity Levels:**
| Level | PROTOTYPE | PRODUCTION |
|-------|-----------|------------|
| BLOCKING | Reject | Reject |
| MAJOR | Warning | Blocking |
| WARNING | Log | Warning |

**Key Failures:**
| Failure | Severity |
|---------|----------|
| Open shell | BLOCKING |
| Self-intersection | BLOCKING |
| Non-manifold | MAJOR |
| Continuity break | MAJOR |
| Gap > tolerance | MAJOR |

**Safe Rejection:** No silent degradation allowed.

### 5. Readiness Matrix

**Location:** `docs/governance/ACOUSTIC_TOPOLOGY_READINESS_MATRIX.md`

**Classifications:**
| Readiness | Description |
|-----------|-------------|
| PROTOTYPE_POSSIBLE | Flat extrusion sufficient |
| MODERATE | Basic loft may be needed |
| RESEARCH_REQUIRED | Semantic gaps exist |
| COMPLEX | Advanced surface generation |
| FUTURE | Beyond current scope |
| OUT_OF_SCOPE | Not planned |

**Instrument Summary:**
| Instrument | Readiness |
|------------|-----------|
| Electric solid | PROTOTYPE_POSSIBLE |
| Flat-top acoustic (uniform) | PROTOTYPE_POSSIBLE |
| Flat-top acoustic (tapered) | RESEARCH_REQUIRED |
| Semi-hollow | MODERATE |
| Archtop | COMPLEX |
| Ukulele | PROTOTYPE_POSSIBLE |

### 6. Adaptive Boundary Rules

**Location:** `docs/governance/ADAPTIVE_TOPOLOGY_BOUNDARY_RULES.md`

**Core Principle:**
```
DETERMINISTIC MORPHOLOGY SPINE = AUTHORITATIVE
ADAPTIVE INTELLIGENCE LAYER = ADVISORY ONLY
```

**AI May NOT:**
- Construct topology
- Mutate geometry
- Override validation
- Bypass deterministic pipeline

**AI MAY (Advisory):**
- Recommend construction approach
- Classify input quality
- Suggest parameters
- Explain failures

### 7. CAD Kernel Boundary Analysis

**Location:** `docs/research/CAD_KERNEL_BOUNDARY_ANALYSIS.md`

**Principle:**
> CAD kernels are implementation dependencies, not semantic authorities.

**Evaluation Criteria:**
1. Dependency weight
2. Windows deployability
3. Deterministic output
4. STEP support
5. Topology validation
6. Licensing
7. Adapter isolation
8. Failure transparency

**Candidates:** OpenCASCADE, CadQuery, build123d, Custom

**Selection:** Deferred to MRP-5H evaluation

---

## Files Created

### Architecture

| File | Purpose |
|------|---------|
| `docs/architecture/TOPOLOGY_AUTHORITY_CHAIN.md` | Authority hierarchy |
| `docs/architecture/ACOUSTIC_TOPOLOGY_BUILDER_MODEL.md` | Builder layer proposal |

### Governance

| File | Purpose |
|------|---------|
| `docs/governance/ACOUSTIC_TOPOLOGY_RUNTIME_RULES.md` | Runtime constraints |
| `docs/governance/TOPOLOGY_FAILURE_CLASSIFICATION.md` | Error classification |
| `docs/governance/ACOUSTIC_TOPOLOGY_READINESS_MATRIX.md` | Instrument readiness |
| `docs/governance/ADAPTIVE_TOPOLOGY_BOUNDARY_RULES.md` | AI boundary rules |

### Research

| File | Purpose |
|------|---------|
| `docs/research/CAD_KERNEL_BOUNDARY_ANALYSIS.md` | Kernel evaluation |

### Handoff

| File | Purpose |
|------|---------|
| `docs/handoffs/MRP_5G_ACOUSTIC_TOPOLOGY_BOUNDARY_RESEARCH.md` | This document |

---

## What Was NOT Built (By Design)

Explicitly excluded per dev order:

- **Acoustic STEP generation** — No runtime code
- **Lofting implementation** — No surface generation
- **Shell construction** — No topology building
- **CAD kernel integration** — No kernel calls
- **Mesh generation** — Out of scope
- **CAM execution** — Out of scope

---

## Core Questions Resolved

### 1. Where does acoustic topology generation live?

**Answer:** Proposed Topology Builder layer between cad_semantics and translators.

**Status:** RECOMMENDED_PENDING_MRP_5H_VALIDATION

### 2. Who owns continuity validation?

**Answer:** Topology Builder owns construction; validation rules defined by governance.

### 3. What semantic inputs are sufficient for shell generation?

**Answer:** Documented in readiness matrix per instrument type.

### 4. How are shell/runtime failures classified?

**Answer:** BLOCKING/MAJOR/WARNING with tier-specific behavior.

### 5. Can topology builders mutate approved geometry?

**Answer:** NO. Geometry preservation is CRITICAL requirement.

### 6. Future relationship between components?

**Answer:** Documented in authority chain with clear boundaries.

---

## Future Implementation Roadmap

| Sprint | Focus | Enables |
|--------|-------|---------|
| MRP-5G | Topology governance | (This sprint) |
| MRP-5H | Topology builder prototype | Validate builder pattern |
| MRP-5I | Shell validation prototype | Validate closure/manifold |
| MRP-5J | Acoustic STEP runtime prototype | First acoustic CAD output |
| MRP-5K | CAD kernel adapter abstraction | Kernel isolation |
| MRP-5L | Continuity verification corpus | Regression for continuity |

### Dependency Risks

| Risk | Mitigation |
|------|------------|
| Kernel selection delays | Adapter pattern allows swap |
| Loft complexity | PROTOTYPE tier allows iteration |
| Windows deployment | Evaluation criterion |
| Continuity enforcement | Two-tier requirements |

### Governance Checkpoints

- [ ] MRP-5H: Builder pattern validated
- [ ] MRP-5I: Shell validation verified
- [ ] MRP-5J: PROTOTYPE tier achievable
- [ ] MRP-5K: Kernel adapter working
- [ ] MRP-5L: PRODUCTION tier criteria defined

---

## Definition of Done

✅ Topology authority chain documented  
✅ Topology builder boundary documented  
✅ Continuity governance documented (two-tier)  
✅ Failure classification documented  
✅ Readiness matrix completed  
✅ CAD kernel boundary analysis completed  
✅ Adaptive isolation rules documented  
✅ Roadmap exists  
✅ Handoff exists

---

## Related Documents

- `MRP_5F_ACOUSTIC_SEMANTIC_EXTENSION_HANDOFF.md` — Semantic foundation
- `MRP_5E_ACOUSTIC_BODY_SEMANTIC_RESEARCH.md` — Research foundation
- `ACOUSTIC_BODY_SEMANTIC_MODEL.md` — Semantic vocabulary
- `ACOUSTIC_TOPOLOGY_CONTINUITY_MODEL.md` — Continuity theory
- `CAD_TRANSLATOR_GOVERNANCE_RULES.md` — Translator boundaries
