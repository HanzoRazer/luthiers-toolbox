# Body Isolation Adapter Redesign Notes

**Date:** 2026-05-18  
**Status:** EXPERIMENTAL_CANDIDATE — Not approved for production  
**Sprint:** DEV ORDER 1B — Adapter Constitutional Audit  
**Depends On:** SEMANTIC_PROVENANCE_MODEL.md (Tier 1 pending ratification)

---

## Purpose

This document audits the existing body isolation implementation against the Semantic Provenance Model and identifies gaps that must be closed before any adapter can populate IBG memory or become a production authority layer.

---

## Current Implementation Inventory

### Existing Components (photo-vectorizer ecosystem)

| File | Purpose | Authority State |
|------|---------|-----------------|
| `body_isolation_result.py` | Result dataclass with diagnostics | `advisory_candidate` |
| `body_isolation_stage.py` | Stage 4.5 wrapper with retry profiles | `advisory_candidate` |
| `geometry_coach_v2.py` | Coach with ownership-aware retry logic | `advisory_candidate` |
| `geometry_authority.py` | Expected body profile lookup | `derived_topology` reference |

### Current Data Flow

```
[Photo/PDF Input]
    │ authority: canonical_source
    ▼
[Background Removal / FG Mask]
    │ authority: derived_topology
    ▼
[BodyIsolationStage.run()]
    │ authority: semantic_interpretation
    │ produces: BodyIsolationResult
    ▼
[GeometryCoachV2.decide()]
    │ authority: advisory_candidate
    │ decides: accept | retry | manual_review
    ▼
[ContourStage] ← BODY REGION USED HERE
    │ authority: advisory_candidate
    │ uses body_bbox_px as ownership filter
    ▼
[Export]
```

---

## Audit Against Semantic Provenance Model

### 1. Authority State Compliance

| Requirement | Current Status | Gap |
|-------------|----------------|-----|
| Objects must declare authority state | **MISSING** | No `authority_state` field in BodyIsolationResult |
| State transitions must be logged | **MISSING** | No `authority_state_history` |
| Forbidden transitions must fail | **MISSING** | No enforcement mechanism |

### 2. Provenance Chain Compliance

| Requirement | Current Status | Gap |
|-------------|----------------|-----|
| `source_artifact` tracked | **MISSING** | No lineage to original DXF/image |
| `derivation_chain` preserved | **MISSING** | No chain of transformations |
| `transformation_method` documented | **PARTIAL** | `source` field captures mask origin only |

### 3. Confidence Semantics Compliance

| Requirement | Current Status | Gap |
|-------------|----------------|-----|
| `confidence_type` declared | **MISSING** | `confidence` is a bare float |
| `confidence_origin` tracked | **MISSING** | Unclear what produced the score |
| `does_not_imply` explicit | **MISSING** | No safeguard against misinterpretation |

### 4. Human Review Compliance

| Requirement | Current Status | Gap |
|-------------|----------------|-----|
| `human_review_required` flag | **PRESENT** | `review_required` field exists |
| `human_review_completed` flag | **MISSING** | No tracking of review state |
| `human_review_decision` recorded | **MISSING** | No decision field |
| Review bypass prevention | **MISSING** | Nothing prevents machine from setting `review_required = False` |

### 5. IBG Intake Gate Compliance

| Requirement | Current Status | Gap |
|-------------|----------------|-----|
| Input authority >= `human_reviewed` | **NOT ENFORCED** | No gate |
| Provenance chain intact | **NOT CHECKED** | No validation |
| Human review decision = `approve` | **NOT CHECKED** | No gate |

---

## Critical Gaps Summary

### BLOCKING — Must fix before any IBG integration

1. **No provenance lineage** — BodyIsolationResult has no link to source DXF/image
2. **No authority state machine** — Objects can be used at any trust level
3. **No confidence semantics** — `confidence: 0.87` is ambiguous (heuristic? statistical? human?)
4. **No review bypass prevention** — Machine can set `review_required = False`

### SERIOUS — Should fix before production use

5. **No transformation stage identity** — Which pipeline stage produced this?
6. **No topology integrity score** — How much geometry was lost/degraded?
7. **No forbidden transition enforcement** — Advisory can become canonical silently

### MODERATE — Can be addressed incrementally

8. **Sparse diagnostics** — `diagnostics` dict is unstructured
9. **No decay tracking** — Cached results don't track staleness
10. **No supersession chain** — When results are replaced, old isn't archived

---

## Redesign Requirements

### R1. Add ProvenanceRecord to BodyIsolationResult

```python
@dataclass
class BodyIsolationResult:
    # ... existing fields ...
    
    # NEW: Provenance metadata
    provenance: Optional[ProvenanceRecord] = None
```

The adapter MUST NOT populate this result into downstream systems if `provenance is None`.

### R2. Add Confidence Declaration

```python
@dataclass
class BodyIsolationResult:
    # ... existing fields ...
    
    # REPLACE bare confidence float with typed declaration
    confidence_declaration: Optional[ConfidenceDeclaration] = None
```

Current `confidence: float` becomes `confidence_declaration.value`.

### R3. Add Authority State Machine

Create `authority_state.py`:

```python
class AuthorityStateMachine:
    """Enforces valid state transitions."""
    
    VALID_TRANSITIONS = {
        AuthorityState.CANONICAL_SOURCE: {AuthorityState.DERIVED_TOPOLOGY},
        AuthorityState.DERIVED_TOPOLOGY: {AuthorityState.SEMANTIC_INTERPRETATION},
        AuthorityState.SEMANTIC_INTERPRETATION: {AuthorityState.ADVISORY_CANDIDATE},
        AuthorityState.ADVISORY_CANDIDATE: {AuthorityState.HUMAN_REVIEWED},
        AuthorityState.HUMAN_REVIEWED: {AuthorityState.APPROVED_FOR_GENERATION},
        # ANY → sandbox/archived allowed
    }
    
    FORBIDDEN_TRANSITIONS = {
        (AuthorityState.ADVISORY_CANDIDATE, AuthorityState.CANONICAL_SOURCE),
        (AuthorityState.DERIVED_TOPOLOGY, AuthorityState.CANONICAL_SOURCE),
        (AuthorityState.SANDBOX_EXPERIMENTAL, AuthorityState.APPROVED_FOR_GENERATION),
    }
    
    def transition(self, obj, to_state, reason, actor):
        if (obj.authority_state, to_state) in self.FORBIDDEN_TRANSITIONS:
            raise ForbiddenTransitionError(...)
        # ... record transition in history ...
```

### R4. Add IBG Intake Gate

```python
def validate_for_ibg_intake(result: BodyIsolationResult) -> None:
    """Gate that MUST pass before IBG memory population."""
    
    if result.provenance is None:
        raise ProvenanceMissingError("Cannot populate IBG without provenance")
    
    if result.provenance.authority_state < AuthorityState.HUMAN_REVIEWED:
        raise AuthorityInsufficientError(
            f"IBG intake requires human_reviewed, got {result.provenance.authority_state}"
        )
    
    if not result.provenance.human_review_completed:
        raise ReviewIncompleteError("IBG intake requires completed human review")
    
    if result.provenance.human_review_decision != "approve":
        raise ReviewRejectedError(
            f"IBG intake requires approval, got {result.provenance.human_review_decision}"
        )
```

### R5. Immutable Review Flag

The `review_required` field must be immutable once set to `True` by machine:

```python
@dataclass
class BodyIsolationResult:
    _review_required: bool = field(default=False, repr=False)
    _review_required_locked: bool = field(default=False, repr=False)
    
    @property
    def review_required(self) -> bool:
        return self._review_required
    
    def set_review_required(self, value: bool, actor: str) -> None:
        if self._review_required and not value:
            if not actor.startswith("human:"):
                raise ReviewBypassAttemptError(
                    "Machine cannot clear review_required flag"
                )
        self._review_required = value
        if value:
            self._review_required_locked = True
```

---

## Decision Matrix

| Option | Description | Recommendation |
|--------|-------------|----------------|
| **A. Refactor** | Add provenance to existing BodyIsolationResult | RECOMMENDED for short-term |
| **B. Replace** | New BodyIsolationCandidate class with provenance built-in | Consider for v2 |
| **C. Archive** | Freeze current, build parallel system | NOT RECOMMENDED (duplication) |

**Recommended path:**

1. Add `ProvenanceRecord` as optional field (backwards compatible)
2. Add `ConfidenceDeclaration` alongside existing `confidence` (deprecate bare float)
3. Create `AuthorityStateMachine` as external validator
4. Create `IBGIntakeGate` as external validator
5. Wire gates into any path that touches IBG memory

---

## Implementation Sequence

```
Phase 1 — Provenance Foundation (current sprint)
├── A. Define ProvenanceRecord dataclass (in governance/)
├── B. Define AuthorityState enum
├── C. Define ConfidenceDeclaration dataclass
└── D. Define AuthorityStateMachine

Phase 2 — Result Integration (next sprint)
├── E. Add provenance field to BodyIsolationResult
├── F. Add confidence_declaration field
├── G. Deprecate bare confidence float
└── H. Add serialization support (to_payload/from_payload)

Phase 3 — Gate Enforcement (following sprint)
├── I. Implement IBGIntakeGate
├── J. Wire gate to IBG population path
├── K. Add governance check to CI
└── L. Add runtime assertions

Phase 4 — Coach Integration (final sprint)
├── M. Update GeometryCoachV2 to emit provenance
├── N. Update BodyIsolationStage to attach source lineage
├── O. Add human review workflow hooks
└── P. End-to-end test with real DXF
```

---

## Open Questions

1. **Where does human review happen?** — CLI? Web UI? Both?
2. **Who reviews?** — Any user? Only project owner?
3. **What is reviewed?** — Just body bbox? Full contour set? DXF overlay?
4. **How is review persisted?** — Database? Sidecar JSON? Git commit?

These must be answered before Phase 3 can complete.

---

## Classification

This document and all referenced adapter code is classified as:

```
authority_state: sandbox_experimental
human_review_required: true
approved_for_generation: false
approved_for_ibg_memory: false
```

No code in this ecosystem may populate IBG memory until:
1. SEMANTIC_PROVENANCE_MODEL.md is ratified (Tier 1)
2. Phases 1-3 above are complete
3. Chief Engineer approves production deployment

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| `SEMANTIC_PROVENANCE_MODEL.md` | Constitutional foundation (depends on) |
| `AUTHORITY_STATE_ARCHITECTURE.md` | State machine details (to be written) |
| `IBG_ROLE_DEFINITION.md` | IBG governance context |
| `THREE_LOOP_ARCHITECTURE_REFRAMED.md` | Coach integration context |

---

*BODY_ISOLATION_ADAPTER_REDESIGN_NOTES.md — DEV ORDER 1B — 2026-05-18*
