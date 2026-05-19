# C2 Continuity Namespace Collisions

```
C2-C — CONSTITUTIONAL ARBITRATION PHASE
CONTINUITY NAMESPACE COLLISION DECOMPOSITION
```

**Phase:** C2-C  
**Owner:** Terminal 3 (Geometry/Morphology/Topology Arbitration)  
**Date:** 2026-05-18  
**Status:** Decomposition Complete — Awaiting Terminal Review

---

## 1. Authority Statement

This document decomposes overloaded continuity semantics for arbitration.

This document does NOT:
- Choose winners
- Normalize globally
- Federate vocabulary
- Mandate renaming
- Resolve collisions

This document DOES:
- Classify collision types
- Map collision domains
- Decompose semantic layers
- Identify authority candidates
- Prepare arbitration surfaces

---

## 2. Collision Inventory

### C2-C New Collisions

| Collision ID | Term | Risk Level | Source |
|--------------|------|------------|--------|
| COLL-C001 | continuity | High | Cross-domain overload |
| COLL-C002 | ContinuityLevel vs ContinuityTarget | Medium | Type duplication |
| COLL-C003 | continuity_graph | Low | Governance-specific |
| COLL-C004 | continuity validation | Medium | Runtime vs semantic |

### Cross-Reference: Existing Collisions

| Collision ID | Term | Relevance |
|--------------|------|-----------|
| COLL-G004 | tier | TopologyTier overloads governance/execution tier |
| COLL-G001 | topology | Continuity validation uses topology concepts |

---

## 3. Collision Decompositions

### COLLISION: continuity (COLL-C001)

**Status:** Overloaded across 5 domains — HIGH RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| continuity (geometric) | CAM | G0/G1/G2 surface smoothness | `contracts.py:16-21` |
| continuity (governance) | Governance | Immutable review chain integrity | `translator_governance_continuity_graph.py` |
| continuity (semantic) | CAD hints | Advisory construction target | `cad_semantics.py:50-55` |
| continuity (manufacturing) | Runtime | Tier-based validation strictness | `validation.py:190-233` |
| continuity (process) | Workflow | Chain of custody integrity | Implicit |

**Decomposition Proposal:**

| Namespace | Purpose | Authority |
|-----------|---------|-----------|
| `geometric_continuity` | G0/G1/G2 surface junction smoothness | CAM topology_builder |
| `governance_continuity` | Immutable review chain integrity | Governance ledger |
| `semantic_continuity` | CAD construction hints (advisory) | CAD semantics |
| `manufacturing_continuity` | Tier-based validation strictness | CAM runtime |
| `process_continuity` | Workflow chain custody | UNDEFINED |

**C2 Candidate:** Domain-prefixed continuity references where semantic distinction required.

---

### COLLISION: ContinuityLevel vs ContinuityTarget (COLL-C002)

**Status:** Type duplication — MEDIUM RISK

| Type | Location | Values | Authority |
|------|----------|--------|-----------|
| ContinuityLevel | `topology_builder/contracts.py:16` | G0, G1, G2 | Enforcement |
| ContinuityTarget | `export/cad_semantics.py:50` | G0, G1 | Advisory |

**Semantic Difference:**

| Aspect | ContinuityLevel | ContinuityTarget |
|--------|-----------------|------------------|
| Purpose | Validation enforcement | Construction hints |
| Authority | Hard enforcement | Advisory only |
| Values | G0, G1, G2 | G0, G1 (no G2) |
| Consumption | validate_continuity() | CAD translators |
| Failure mode | BLOCKING (PRODUCTION) | No enforcement |

**Decomposition Proposal:**

| Option | Change | Risk |
|--------|--------|------|
| A (preserve) | Keep both, add documentation | Low change risk |
| B (rename) | Rename ContinuityTarget → ContinuityHint | Breaking change |
| C (unify) | Single type with authority marker | Complexity |

**Terminal 3 Recommendation:** Option A — preserve with documentation.

---

### COLLISION: continuity_graph (COLL-C003)

**Status:** Governance-specific — LOW RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| continuity_graph | Governance | Hash-linked review ancestry | `translator_governance_continuity_graph.py:74` |
| continuity_graph_id | Governance | Deterministic graph identifier | `translator_governance_continuity_graph.py:89` |
| continuity_integrity | Governance | Chain integrity status | `translator_governance_continuity_graph.py:128` |

**Assessment:**
This is governance-domain-specific vocabulary. No collision with geometric continuity — different namespace.

**Decomposition Proposal:**
No action required. Governance continuity vocabulary is self-contained with 7L invariants.

---

### COLLISION: continuity validation (COLL-C004)

**Status:** Runtime vs semantic — MEDIUM RISK

| Usage | Domain | Meaning | Evidence |
|-------|--------|---------|----------|
| validate_continuity() | CAM runtime | Check G0/G1/G2 achievement | `validation.py:190` |
| continuity_target | CAD hints | Target for construction | `cad_semantics.py:173` |

**Risk:**
Developer may assume ContinuityTarget feeds into validate_continuity().
This is false — they are separate systems with no direct connection.

**Propagation Path Gap:**
```
ContinuityTarget (cad_semantics.py)
    ↓
RimSemantics.continuity_target
    ↓
??? (no path to topology_builder validation)
```

**Decomposition Proposal:**

| Namespace | Purpose | Connection |
|-----------|---------|------------|
| `validation_continuity` | Runtime enforcement | topology_builder |
| `target_continuity` | Advisory hints | cad_semantics (no enforcement) |

---

## 4. Propagation Path Analysis

### 4.1 Geometric Continuity Propagation

```
ContinuityLevel                    [contracts.py:16]
       │
       ├──▶ TopologyRequest.continuity_targets   [contracts.py:228]
       │           │
       │           ▼
       │    ContinuityMetadata                   [contracts.py:93]
       │           │
       │           ▼
       │    ShellDescriptor.continuity[]         [contracts.py:133]
       │           │
       │           ▼
       ├──▶ validate_continuity()                [validation.py:190]
       │           │
       │           ▼
       └──▶ TopologyResult                       [contracts.py:259]
```

**Containment Status:** HEALTHY
- Confined to topology_builder domain
- Clear authority chain
- No escape to governance domain

### 4.2 Governance Continuity Propagation

```
TranslatorGovernanceReviewLedgerEntry
       │
       ▼
build_governance_continuity_graph()              [translator_governance_continuity_graph.py:596]
       │
       ▼
TranslatorGovernanceContinuityGraph              [translator_governance_continuity_graph.py:74]
       │
       ├──▶ 7L Invariant Enforcement
       │    ├── replayable = true
       │    ├── immutable = true
       │    ├── execution_authorized = false
       │    └── machine_output_allowed = false
       │
       ▼
replay_governance_trace()                        [translator_governance_continuity_graph.py:753]
       │
       ▼
GovernanceReplayResult                           [translator_governance_continuity_graph.py:244]
```

**Containment Status:** HEALTHY
- Strong 7L invariant enforcement
- Model validators prevent invariant bypass
- No geometric semantics
- Immutable by design

### 4.3 Semantic Continuity Propagation

```
ContinuityTarget                                 [cad_semantics.py:50]
       │
       ▼
RimSemantics.continuity_target                   [cad_semantics.py:173]
       │
       ▼
AcousticSemantics.rim                            [cad_semantics.py:229]
       │
       ▼
CadSemantics.acoustic                            [cad_semantics.py:309]
       │
       ▼
??? CONSUMPTION PATH UNCLEAR ???
```

**Containment Status:** UNCLEAR
- No evidence of consumption by topology_builder
- May be dead code or future intent
- Advisory nature not enforced

---

## 5. Authority Candidate Matrix

| Term | Current Authority | Evidence | Arbitration Required |
|------|-------------------|----------|---------------------|
| ContinuityLevel | CAM topology_builder | Single implementation | NO |
| ContinuityTarget | cad_semantics | Single implementation | NO |
| continuity_graph | Governance ledger | 7L invariants | NO |
| validate_continuity | CAM runtime | Single implementation | NO |
| process_continuity | UNDEFINED | No implementation | YES — if formalized |

---

## 6. Namespace Strategy

### Domain Prefixing

When semantic distinction required:
```
geometric_continuity_* — G0/G1/G2 surface junctions
governance_continuity_* — review chain integrity
semantic_continuity_* — CAD construction hints
manufacturing_continuity_* — tier validation strictness
process_continuity_* — workflow chain custody
```

### Type Prefixing

When type distinction required:
```
ContinuityLevel — enforcement type (G0/G1/G2)
ContinuityTarget — advisory type (G0/G1 hints)
ContinuityMetadata — tracking type (target vs achieved)
ContinuityGraph — governance type (hash chains)
```

---

## 7. Cross-Collision Dependencies

### COLL-C001 → COLL-G004 (tier)

TopologyTier (PROTOTYPE, PRODUCTION) controls continuity validation strictness.
This creates a dependency chain:

```
TopologyTier (COLL-G004)
      │
      ▼
validate_continuity() behavior
      │
      ├── PROTOTYPE: G0 acceptable
      └── PRODUCTION: G1 required (G0 BLOCKING)
```

If COLL-G004 (tier) is resolved by renaming TopologyTier to `manufacturing_tier` or `runtime_tier`, continuity validation must update references.

### COLL-C002 → No Dependencies

ContinuityLevel and ContinuityTarget are isolated.
No cross-references between them.
Resolution can be independent.

---

## 8. Arbitration Surface Summary

| Surface | Priority | Status |
|---------|----------|--------|
| "continuity" overload | HIGH | Decomposed — namespace strategy defined |
| ContinuityLevel vs ContinuityTarget | MEDIUM | Decomposed — preserve with documentation |
| continuity_graph | LOW | No action — governance-contained |
| validate_continuity confusion | MEDIUM | Decomposed — path gap documented |
| process_continuity undefined | LOW | Deferred — no formal definition |

---

## 9. Recommended Actions

### Immediate (C2-C)

1. **Add namespace documentation** at module boundaries
2. **Document ContinuityTarget advisory nature** in docstring
3. **Clarify propagation gap** between cad_semantics and topology_builder

### Deferred (C3)

1. **Consider ContinuityTarget → ContinuityHint rename** if confusion persists
2. **Define process_continuity formally** if workflow integrity needed
3. **Add lint rule** for unprefixed "continuity" in ambiguous contexts

---

## 10. Related Documents

### C2 Framework

- `C2_ARBITRATION_FRAMEWORK.md` — Constitutional arbitration structure
- `C2_GEOMETRY_NAMESPACE_COLLISIONS.md` — Geometry collision decomposition
- `C2_CONTINUITY_SEMANTIC_DECOMPOSITION.md` — Continuity semantic analysis

### Code References

- `topology_builder/contracts.py` — ContinuityLevel, ContinuityMetadata
- `topology_builder/validation.py` — validate_continuity()
- `translator_governance_continuity_graph.py` — Governance continuity
- `export/cad_semantics.py` — ContinuityTarget, RimSemantics

---

*C2-C Continuity Namespace Collisions — Decomposition Complete*
