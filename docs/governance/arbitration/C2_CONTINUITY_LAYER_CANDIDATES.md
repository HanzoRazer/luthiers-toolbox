# C2 Continuity Layer Candidates

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
CONTINUITY LAYER CANDIDATE ENUMERATION
```

**Phase:** C2-C  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** Enumeration Complete — Awaiting Terminal Review

---

## 1. Authority Statement

This document enumerates continuity layer candidates for constitutional arbitration.

This document:
- Identifies candidate continuity layers
- Maps layer authority relationships
- Documents evidence for each candidate
- Prepares arbitration surface

This document does NOT:
- Assign canonical ownership
- Choose between candidates
- Mandate layer structure
- Create enforcement rules

---

## 2. Candidate Continuity Layers

### Layer 1: Geometric Continuity (geometric_continuity)

**Definition:**
Mathematical measure of surface junction smoothness (G0/G1/G2).

**Authority Candidate:** CAM topology_builder

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| `topology_builder/contracts.py:16-21` | ContinuityLevel enum | IMPLEMENTED |
| `topology_builder/contracts.py:93-112` | ContinuityMetadata | IMPLEMENTED |
| `topology_builder/validation.py:190-233` | validate_continuity() | IMPLEMENTED |

**Semantic Content:**
```python
class ContinuityLevel(str, Enum):
    G0 = "G0"  # Positional (touching)
    G1 = "G1"  # Tangent (smooth)
    G2 = "G2"  # Curvature (very smooth)
```

**Assessment:**
- Clear mathematical semantics
- Single implementation
- Well-contained scope
- **CANDIDATE STRENGTH: STRONG**

---

### Layer 2: Governance Continuity (governance_continuity)

**Definition:**
Immutable hash-linked review ancestry for deterministic replay.

**Authority Candidate:** Governance ledger (7L module)

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| `translator_governance_continuity_graph.py:74-241` | TranslatorGovernanceContinuityGraph | IMPLEMENTED |
| `translator_governance_continuity_graph.py:596-702` | build_governance_continuity_graph() | IMPLEMENTED |
| `translator_governance_continuity_graph.py:753-808` | replay_governance_trace() | IMPLEMENTED |

**Semantic Content:**
```
continuity_graph_id — Deterministic graph identifier
review_trace_chain — Ordered hash sequence
deterministic_continuity_hash — Canonical replay anchor
continuity_integrity_valid — Chain unbroken status
```

**7L Invariants:**
```
replayable = true (always)
immutable = true (always)
execution_authorized = false (always)
machine_output_allowed = false (always)
```

**Assessment:**
- Strong invariant enforcement
- Domain-specific vocabulary
- No geometric semantics
- **CANDIDATE STRENGTH: STRONG**

---

### Layer 3: Semantic Continuity (semantic_continuity)

**Definition:**
Advisory CAD construction hints for surface junctions.

**Authority Candidate:** cad_semantics module

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| `export/cad_semantics.py:50-55` | ContinuityTarget enum | IMPLEMENTED |
| `export/cad_semantics.py:165-181` | RimSemantics | IMPLEMENTED |
| `export/cad_semantics.py:394-480` | validate_acoustic_semantics() | IMPLEMENTED |

**Semantic Content:**
```python
class ContinuityTarget(str, Enum):
    G0 = "G0"  # Positional continuity
    G1 = "G1"  # Tangent continuity
```

**Assessment:**
- Advisory only (no enforcement)
- Consumption path unclear
- G2 intentionally omitted
- **CANDIDATE STRENGTH: WEAK (consumption gap)**

---

### Layer 4: Manufacturing Continuity (manufacturing_continuity)

**Definition:**
Tier-based validation strictness for manufacturing output.

**Authority Candidate:** CAM runtime (TopologyTier)

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| `topology_builder/contracts.py:33-37` | TopologyTier enum | IMPLEMENTED |
| `topology_builder/validation.py:96-142` | Tier-based validation | IMPLEMENTED |
| `topology_builder/validation.py:190-233` | Tier affects continuity rules | IMPLEMENTED |

**Semantic Content:**
```python
class TopologyTier(str, Enum):
    PROTOTYPE = "PROTOTYPE"  # G0 acceptable, warnings allowed
    PRODUCTION = "PRODUCTION"  # G1 required, strict validation
```

**Assessment:**
- Controls validation behavior
- Clear tier semantics
- Collision with governance tier (COLL-G004)
- **CANDIDATE STRENGTH: MEDIUM (tier collision)**

---

### Layer 5: Process Continuity (process_continuity)

**Definition:**
Unbroken chain of custody from design to production.

**Authority Candidate:** UNDEFINED

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| BOE invariants | Geometry must not mutate | IMPLICIT |
| Governance ledger | Review chain | PARTIAL |
| Translator boundary | G-code generation | IMPLICIT |

**Semantic Content:**
```
Chain of custody — Geometry unchanged from BOE approval
Approval chain — Governance sign-offs present
Execution chain — G-code derived from approved geometry
```

**Assessment:**
- No formal implementation
- Spread across multiple systems
- Implicit rather than explicit
- **CANDIDATE STRENGTH: WEAK (undefined)**

---

### Layer 6: Validation Continuity (validation_continuity)

**Definition:**
Continuity enforcement during topology construction.

**Authority Candidate:** CAM validation module

**Evidence:**
| Location | Content | Status |
|----------|---------|--------|
| `topology_builder/validation.py:190-233` | validate_continuity() | IMPLEMENTED |
| `topology_builder/exceptions.py` | ContinuityValidationError | IMPLEMENTED |

**Semantic Content:**
```python
def validate_continuity(shell, tier):
    """
    PROTOTYPE: G0 acceptable, G1 warning
    PRODUCTION: G1 required, G0 BLOCKING
    """
```

**Assessment:**
- Enforcement mechanism for geometric continuity
- Subordinate to Layer 1 (geometric)
- May not warrant separate layer status
- **CANDIDATE STRENGTH: SUBORDINATE**

---

## 3. Layer Authority Matrix

| Layer | Candidate Authority | Evidence Strength | Collision Risk |
|-------|---------------------|-------------------|----------------|
| geometric_continuity | CAM topology_builder | STRONG | LOW |
| governance_continuity | Governance ledger | STRONG | LOW |
| semantic_continuity | cad_semantics | WEAK | MEDIUM |
| manufacturing_continuity | CAM runtime | MEDIUM | HIGH (tier) |
| process_continuity | UNDEFINED | WEAK | HIGH |
| validation_continuity | CAM validation | SUBORDINATE | LOW |

---

## 4. Layer Relationship Diagram

```
                    ┌─────────────────────────────────┐
                    │     GEOMETRIC CONTINUITY         │
                    │   (G0/G1/G2 mathematical)        │
                    │   Authority: topology_builder    │
                    └───────────────┬─────────────────┘
                                    │
                                    │ enforces
                                    ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐
│   MANUFACTURING CONTINUITY   │───▶│   VALIDATION CONTINUITY     │
│   (TopologyTier strictness)  │    │   (Runtime enforcement)     │
│   Authority: CAM runtime     │    │   Authority: CAM validation │
└─────────────────────────────┘    └─────────────────────────────┘
                                    
                    ┌─────────────────────────────────┐
                    │     SEMANTIC CONTINUITY          │
                    │   (Advisory CAD hints)           │
                    │   Authority: cad_semantics       │
                    └───────────────┬─────────────────┘
                                    │
                                    │ advisory (no enforcement)
                                    ▼
                    ┌─────────────────────────────────┐
                    │         ??? CONSUMERS ???        │
                    │   (Path unclear)                 │
                    └─────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │     GOVERNANCE CONTINUITY        │
                    │   (Immutable review chains)      │
                    │   Authority: Governance ledger   │
                    └─────────────────────────────────┘
                    (Isolated — no connection to geometric)

                    ┌─────────────────────────────────┐
                    │     PROCESS CONTINUITY           │
                    │   (Chain of custody)             │
                    │   Authority: UNDEFINED           │
                    └─────────────────────────────────┘
                    (Implicit — spread across systems)
```

---

## 5. Gap Analysis

### 5.1 Clear Authority (No Gap)

| Layer | Authority | Status |
|-------|-----------|--------|
| geometric_continuity | CAM topology_builder | CLEAR |
| governance_continuity | Governance ledger | CLEAR |

### 5.2 Weak Authority (Gap)

| Layer | Issue | Recommendation |
|-------|-------|----------------|
| semantic_continuity | Consumption path unclear | Document advisory nature |
| manufacturing_continuity | Tier collision | Namespace prefix |

### 5.3 Missing Authority (Major Gap)

| Layer | Issue | Recommendation |
|-------|-------|----------------|
| process_continuity | No formal definition | Either define or explicitly defer |

### 5.4 Subordinate Layer

| Layer | Parent | Recommendation |
|-------|--------|----------------|
| validation_continuity | geometric_continuity | May not need separate layer |

---

## 6. Recommended Layer Structure

### 6.1 Primary Layers (Distinct Authority)

```
geometric_continuity     — CAM topology_builder (G0/G1/G2)
governance_continuity    — Governance ledger (hash chains)
```

### 6.2 Supporting Layers (Subordinate Authority)

```
manufacturing_continuity — Subordinate to geometric (tier-based)
validation_continuity    — Implementation of geometric enforcement
```

### 6.3 Advisory Layers (No Enforcement)

```
semantic_continuity      — CAD hints only (advisory)
```

### 6.4 Undefined Layers (Defer or Define)

```
process_continuity       — Requires formal definition or deferral
```

---

## 7. Arbitration Questions

### 7.1 Should semantic_continuity be formalized?

**Position A — Formalize:**
- Connect ContinuityTarget to topology_builder
- Create consumption path
- Enforce advisory→enforcement bridge

**Position B — Document as advisory:**
- Keep ContinuityTarget as advisory
- Document no enforcement path
- Rename to ContinuityHint

**Terminal 3 Assessment:** Position B — advisory status should be explicit.

### 7.2 Should process_continuity be defined?

**Position A — Define formally:**
- Create ProcessContinuity type
- Span BOE, governance, translator boundaries
- Explicit chain of custody tracking

**Position B — Defer:**
- Process continuity is implicit
- Adding formal layer creates governance overhead
- Existing invariants sufficient

**Terminal 3 Assessment:** Position B — defer unless explicit need arises.

### 7.3 Is validation_continuity a separate layer?

**Position A — Separate layer:**
- Validation rules distinct from geometric semantics
- Tier-based behavior warrants own layer
- Clear implementation boundary

**Position B — Subordinate to geometric:**
- Validation implements geometric continuity
- No separate semantic content
- Layer proliferation risk

**Terminal 3 Assessment:** Position B — validation is implementation, not layer.

---

## 8. Terminal Review Requirements

### Terminal 2 — Runtime/CAM

- [ ] Confirm geometric continuity layer scope
- [ ] Validate manufacturing continuity boundaries
- [ ] Review validation as subordinate vs layer
- [ ] Flag missing runtime continuity needs

### Terminal 4 — Provenance/Observational

- [ ] Confirm governance continuity isolation
- [ ] Validate 7L invariant coverage
- [ ] Review process continuity need
- [ ] Flag provenance continuity gaps

### Terminal 5 — Export/Serialization

- [ ] Clarify semantic continuity consumers
- [ ] Validate advisory-only status
- [ ] Review CAD translator requirements
- [ ] Flag format continuity needs

---

## 9. Related Documents

### C2 Framework

- `C2_CONTINUITY_SEMANTIC_DECOMPOSITION.md` — Semantic domain analysis
- `C2_CONTINUITY_NAMESPACE_COLLISIONS.md` — Collision decomposition
- `C2_CONTINUITY_PROPAGATION_ANALYSIS.md` — Propagation paths
- `C2_GEOMETRY_AUTHORITY_FRAMEWORK.md` — Geometry layer reference

### Code References

- `topology_builder/contracts.py` — ContinuityLevel, TopologyTier
- `topology_builder/validation.py` — validate_continuity()
- `translator_governance_continuity_graph.py` — Governance continuity
- `export/cad_semantics.py` — ContinuityTarget

---

*C2-C Continuity Layer Candidates — Enumeration Complete*
