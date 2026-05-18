# IBG Constitutional Runtime Foundation

**Date:** 2026-05-18  
**Status:** IMPLEMENTED — Pending Ratification  
**Sprint:** DEV ORDER 1D — IBG Constitutional Intake Foundation  
**Authority:** Tier 1 Structural Invariant (pending ratification)

---

## Purpose

This document defines the constitutional runtime foundation for IBG semantic intake.

The core distinction:

```
IBG semantic discovery is permitted.
IBG ontology authority is NOT permitted.
```

This foundation ensures semantic intelligence cannot outrun semantic accountability.

---

## Problem Statement

Before this sprint, semantic objects in the IBG pipeline were plain containers:
- `BodyEvidence` — no authority tracking
- `BodyIsolationResult` — no provenance
- Confidence values — ambiguous semantics
- Review requirements — machine-clearable

This allowed failure modes:
- Silent authority inflation
- Provenance stripping
- Confidence misinterpretation
- Review bypass
- Unauthorized IBG memory population

---

## Solution: Constitutional Semantic Intake Objects

### New Runtime Foundation

Located in `services/api/app/governance/`:

| Module | Purpose |
|--------|---------|
| `authority_state.py` | Authority state enum and transition enforcement |
| `provenance_record.py` | Provenance lineage tracking |
| `confidence_declaration.py` | Typed confidence with explicit semantics |
| `review_enforcement.py` | Protected review requirements |

### Constitutional Wrapper

Located in `services/api/app/instrument_geometry/body/ibg/`:

| Module | Purpose |
|--------|---------|
| `body_evidence_candidate.py` | Constitutional wrapper around BodyEvidence |
| `ibg_intake_gate.py` | Intake validation gate |

---

## Authority States

```
canonical_geometry        → Original source artifact
derived_topology         → Geometry reconstructed from source
semantic_interpretation  → Meaning inferred from topology
advisory_candidate       → Ranked suggestion, not ratified
human_reviewed           → Examined by human, decision recorded
approved_for_generation  → Cleared for downstream CAD output
sandbox_experimental     → Untrusted experimental output
rejected                 → Explicitly rejected
archived_superseded      → No longer authoritative
```

### Transition Rules

Valid transitions follow a strict graph. Key rules:

1. **No silent authority elevation** — Cannot jump from advisory to canonical
2. **Human review required** — Must pass through `human_reviewed` before `approved_for_generation`
3. **No review bypass** — `sandbox_experimental` cannot skip to `approved_for_generation`

### Forbidden Transitions

```
advisory_candidate → canonical_geometry       FORBIDDEN
advisory_candidate → approved_for_generation  FORBIDDEN
sandbox_experimental → approved_for_generation FORBIDDEN
derived_topology → canonical_geometry         FORBIDDEN
```

---

## Provenance Tracking

Every semantic object carries:

```python
@dataclass
class ProvenanceRecord:
    object_id: str
    object_type: str
    source_artifact: str              # Original source
    derived_from: Optional[str]       # Parent object
    derivation_chain: List[str]       # Full ancestry
    transformation_history: List[TransformationRecord]
    topology_integrity_score: float   # 0.0-1.0
```

### Transformation Stages

```
SOURCE_INTAKE → TOPOLOGY_RECONSTRUCTION → GAP_CLOSURE
→ BODY_ISOLATION → MORPHOLOGY_ANALYSIS → CANDIDATE_RANKING
→ HUMAN_REVIEW → GENERATION_APPROVAL → CAD_GENERATION
```

---

## Confidence Semantics

Confidence is typed and declared:

```python
@dataclass
class ConfidenceDeclaration:
    value: float                # 0.0-1.0
    confidence_type: ConfidenceType  # epistemic|statistical|heuristic|human_assessed
    origin: str                 # What produced this
    interpretation: str         # What it means
    does_not_imply: List[str]   # Explicit non-implications
```

### Constitutional Safeguards

```python
def implies_correctness(self) -> bool:
    return False  # ALWAYS

def implies_canonicity(self) -> bool:
    return False  # ALWAYS

def implies_review_bypass(self) -> bool:
    return False  # ALWAYS

def implies_ibg_eligibility(self) -> bool:
    return False  # ALWAYS
```

Confidence value 0.99 does NOT mean:
- "this is correct"
- "this is canonical"
- "this can skip review"
- "this is eligible for IBG memory"

---

## Review Enforcement

Review requirements are protected:

```python
@dataclass
class ReviewEnforcement:
    _review_required: bool           # Protected
    _review_required_set_by: str     # Who set it
    review_history: List[ReviewRecord]
```

### Key Protection

Machine code can SET `review_required = True`.
Machine code CANNOT SET `review_required = False`.

Only human actors (IDs starting with `human:`) can:
- Clear `review_required`
- Issue `APPROVE` or `REJECT` decisions

### Bypass Detection

```python
# This raises ReviewBypassAttemptError:
enforcement.set_review_required(False, "system:bot", "bypass attempt")

# Bypass attempts are counted:
enforcement.bypass_attempt_count  # Accumulates
```

---

## IBG Intake Gate

The intake gate validates candidates before IBG memory population:

```python
gate = IBGIntakeGate()
result = gate.validate(candidate)

if not result.is_valid:
    for reason in result.rejections:
        print(f"Rejected: {reason.value}")
```

### Rejection Reasons

| Reason | Description |
|--------|-------------|
| `AUTHORITY_INSUFFICIENT` | Authority state < human_reviewed |
| `PROVENANCE_MISSING` | No provenance record |
| `PROVENANCE_INCOMPLETE` | Incomplete lineage |
| `REVIEW_REQUIRED` | Review not completed |
| `REVIEW_NOT_APPROVED` | Review completed but not approved |
| `CONFIDENCE_UNDECLARED` | Unknown confidence type |
| `REVIEW_BYPASS_DETECTED` | Bypass attempts exceed threshold |
| `TOPOLOGY_INTEGRITY_DEGRADED` | Integrity below minimum |
| `CANDIDATE_REJECTED` | In REJECTED authority state |

### Gate Configurations

```python
# Default: standard requirements
gate = create_default_intake_gate()

# Strict: higher topology threshold
gate = create_strict_intake_gate()

# Permissive: for development (NOT production)
gate = create_permissive_intake_gate()
```

---

## BodyEvidenceCandidate

Constitutional wrapper around `BodyEvidence`:

```python
@dataclass
class BodyEvidenceCandidate:
    candidate_id: str
    evidence: BodyEvidence
    authority: AuthorityStateContainer
    provenance: ProvenanceRecord
    confidence: ConfidenceDeclaration
    review: ReviewEnforcement
```

### Default State

```
authority_state = sandbox_experimental
review_required = True
approved_for_ibg_memory = False
```

### Usage

```python
# Create from evidence
candidate = create_candidate_from_evidence(
    evidence=body_evidence,
    source_artifact="/path/to/blueprint.dxf",
    extraction_method="body_isolation_stage",
)

# Record human review
candidate.record_review(
    "human:reviewer_123",
    ReviewDecision.APPROVE,
    "Verified body extraction",
)

# Check eligibility
if candidate.approved_for_ibg_memory:
    # Safe to proceed
    pass

# Or use gate
gate = create_default_intake_gate()
result = gate.validate_or_raise(candidate)  # Raises if invalid
```

---

## Canonical Ontology Registration

The following terms are registered in `canonical_ontology_registry.py`:

| Term | Domain | Tier |
|------|--------|------|
| `authority_state` | IBG Governance | 1 |
| `semantic_provenance` | IBG Governance | 1 |
| `confidence_declaration` | IBG Governance | 1 |
| `review_enforcement` | IBG Governance | 1 |

### Prohibited Reinterpretations

- `authority_state` ≠ confidence_level, quality_score
- `confidence_declaration` ≠ truth_score, approval_likelihood
- `review_enforcement` ≠ optional_review, machine_clearable_review

---

## Testing

Tests located in `services/api/tests/`:

| File | Coverage |
|------|----------|
| `test_governance_constitutional_runtime.py` | Authority, provenance, confidence, review |
| `test_ibg_intake_gate.py` | Gate rejection/acceptance, configuration |

Run tests:

```bash
pytest services/api/tests/test_governance_constitutional_runtime.py -v
pytest services/api/tests/test_ibg_intake_gate.py -v
```

---

## Current Boundaries

### Permitted

- Semantic discovery
- Advisory ranking
- Candidate evaluation
- Confidence scoring
- Diagnostic visibility

### NOT Permitted (Until Human Review)

- IBG memory population
- Canonical morphology registration
- Downstream CAD authority propagation
- Automatic semantic persistence

---

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| ProvenanceRecord exists and propagates | ✓ |
| AuthorityState exists and is enforced | ✓ |
| ConfidenceDeclaration separates confidence from legitimacy | ✓ |
| BodyEvidenceCandidate carries constitutional metadata | ✓ |
| IBGIntakeGate blocks unauthorized intake | ✓ |
| Review bypass vulnerability is closed | ✓ |
| Authority transitions are logged | ✓ |
| Sandbox systems cannot silently canonize | ✓ |
| Diagnostic outputs expose derivation lineage | ✓ |
| IBG memory population remains blocked without ratified authority | ✓ |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `SEMANTIC_PROVENANCE_MODEL.md` | Constitutional foundation spec |
| `BODY_ISOLATION_ADAPTER_REDESIGN_NOTES.md` | Adapter audit |
| `C2-B_TOPOLOGY_NAMESPACE_ARBITRATION_FINDINGS.md` | Namespace analysis |
| `IBG_ROLE_DEFINITION.md` | IBG governance boundaries |

---

*IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md — DEV ORDER 1D — 2026-05-18*
