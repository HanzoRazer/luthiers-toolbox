# Semantic Provenance Model

**Date:** 2026-05-18  
**Status:** DRAFT — Constitutional Foundation  
**Sprint:** DEV ORDER 1A — Semantic Provenance & Authority Propagation  
**Authority:** Tier 1 Structural Invariant (pending ratification)

---

## Purpose

This document defines the provenance propagation architecture for semantic transformations across the Luthiers Toolbox geometry pipeline.

The core principle:

```
Every semantic transformation must preserve:
- provenance (where did this come from?)
- derivation visibility (how was it produced?)
- authority state (what trust level does it have?)
- epistemic honesty (what do we actually know?)
```

---

## Problem Statement

The repository has evolved a semantic pipeline:

```
canonical geometry
→ reconstructed topology
→ semantic occupancy
→ advisory evidence
→ candidate rankings
→ human ratification
→ downstream CAD generation
```

Without explicit provenance propagation, the following failure modes occur:

| Failure Mode | Description |
|--------------|-------------|
| Silent authority inflation | Advisory rankings become canonical truth |
| Derivation collapse | Reconstructed topology treated as source geometry |
| Confidence misinterpretation | Statistical confidence becomes ontological certainty |
| Cache poisoning | Derived artifacts become de facto authority |
| Review bypass | Machine outputs skip human ratification |

---

## Authority State Taxonomy

Every semantic object must declare its authority state explicitly.

### Defined States

| State | Code | Meaning |
|-------|------|---------|
| `canonical_source` | `CS` | Original artifact from authoritative source |
| `derived_topology` | `DT` | Geometry reconstructed from source |
| `semantic_interpretation` | `SI` | Meaning inferred from topology |
| `advisory_candidate` | `AC` | Ranked suggestion, not ratified |
| `human_reviewed` | `HR` | Examined by human, decision recorded |
| `approved_for_generation` | `AG` | Cleared for downstream CAD output |
| `sandbox_experimental` | `SX` | Untrusted experimental output |
| `archived_superseded` | `AS` | No longer authoritative |

### State Transition Rules

```
canonical_source → derived_topology       (reconstruction)
derived_topology → semantic_interpretation (scoring/classification)
semantic_interpretation → advisory_candidate (ranking)
advisory_candidate → human_reviewed       (human inspection)
human_reviewed → approved_for_generation  (explicit approval)

ANY STATE → sandbox_experimental          (experimental fork)
ANY STATE → archived_superseded           (supersession)
```

### Forbidden Transitions

```
advisory_candidate → canonical_source     FORBIDDEN
derived_topology → canonical_source       FORBIDDEN
semantic_interpretation → canonical_source FORBIDDEN
sandbox_experimental → approved_for_generation FORBIDDEN (without human_reviewed)
```

---

## Provenance Object Structure

Every semantic object in the pipeline should carry provenance metadata.

### Minimal Provenance Record

```python
@dataclass
class ProvenanceRecord:
    """Provenance metadata for semantic pipeline objects."""
    
    # Identity
    object_id: str                    # Unique identifier
    object_type: str                  # e.g., "BodyEvidenceCandidate"
    
    # Authority
    authority_state: AuthorityState   # Current trust level
    authority_state_history: List[AuthorityStateTransition]
    
    # Lineage
    source_artifact: str              # Original source path/id
    derived_from: Optional[str]       # Parent object id
    derivation_chain: List[str]       # Full ancestry
    
    # Transformation
    transformation_stage: str         # e.g., "topology_reconstruction"
    transformation_method: str        # e.g., "reconstruct_contours"
    transformation_params: Dict       # Parameters used
    transformation_timestamp: str     # ISO timestamp
    
    # Confidence
    confidence_value: float           # 0.0-1.0
    confidence_type: ConfidenceType   # epistemic | statistical | heuristic
    confidence_origin: str            # What produced this score
    
    # Review
    human_review_required: bool
    human_review_completed: bool
    human_review_decision: Optional[str]
    human_reviewer_id: Optional[str]
    
    # Integrity
    topology_integrity_score: float   # 0.0-1.0
    topology_degradation_notes: List[str]
```

### Authority State Transition Record

```python
@dataclass
class AuthorityStateTransition:
    """Record of an authority state change."""
    from_state: AuthorityState
    to_state: AuthorityState
    timestamp: str
    reason: str
    actor: str  # "system" | "human:<id>" | "governance:<rule>"
```

---

## Confidence Semantics

Confidence values must not be conflated with ontological truth.

### Confidence Types

| Type | Code | Meaning |
|------|------|---------|
| `epistemic` | `EP` | Quality of knowledge/evidence |
| `statistical` | `ST` | Probability from model/scoring |
| `heuristic` | `HE` | Rule-based estimate |
| `human_assessed` | `HA` | Human judgment |

### Confidence Does NOT Imply

```
confidence = 0.95 does NOT mean:
- "this is correct"
- "this is canonical"
- "this is approved"
- "this can skip review"
```

### Confidence Declaration

```python
@dataclass
class ConfidenceDeclaration:
    value: float                  # 0.0-1.0
    confidence_type: ConfidenceType
    origin: str                   # What produced this
    interpretation: str           # What this value means
    does_not_imply: List[str]     # Explicit non-implications
```

---

## Transformation Stage Taxonomy

### Defined Stages

| Stage | Code | Input | Output |
|-------|------|-------|--------|
| `source_intake` | `SI` | External file | Canonical artifact |
| `topology_reconstruction` | `TR` | LINE entities | Chain/contour loops |
| `gap_closure` | `GC` | Open chains | Closed contours |
| `occupancy_analysis` | `OA` | Contours | Zone occupancy scores |
| `candidate_ranking` | `CR` | Scored contours | Ranked candidates |
| `semantic_classification` | `SC` | Candidates | Morphology descriptors |
| `human_review` | `HR` | Candidates | Reviewed decisions |
| `generation_approval` | `GA` | Reviewed items | Approved for CAD |
| `cad_generation` | `CG` | Approved items | DXF/G-code output |

### Stage Lineage Preservation

Each stage must:
1. Record input object provenance
2. Document transformation method
3. Preserve derivation chain
4. Declare output authority state
5. Not elevate authority state without explicit transition

---

## Semantic Pipeline Provenance Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROVENANCE FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Vectorizer DXF]                                               │
│       │ authority: canonical_source                             │
│       │ confidence_type: N/A (source)                           │
│       ▼                                                         │
│  [Topology Reconstruction]                                      │
│       │ authority: derived_topology                             │
│       │ confidence_type: heuristic                              │
│       │ preserves: source_artifact lineage                      │
│       ▼                                                         │
│  [STEM/Grid Occupancy Analysis]                                 │
│       │ authority: semantic_interpretation                      │
│       │ confidence_type: statistical                            │
│       │ preserves: derivation_chain                             │
│       ▼                                                         │
│  [Candidate Ranking]                                            │
│       │ authority: advisory_candidate                           │
│       │ confidence_type: statistical                            │
│       │ requires: human_review_required = true                  │
│       ▼                                                         │
│  [Human Review] ◄─────────────────────────────────────────┐     │
│       │ authority: human_reviewed                         │     │
│       │ confidence_type: human_assessed                   │     │
│       │ decision: approve | reject | defer                │     │
│       ▼                                                   │     │
│  [IBG Memory Population]                                  │     │
│       │ authority: approved_for_generation                │     │
│       │ GATE: requires authority >= human_reviewed        │     │
│       │                                                   │     │
│       ▼                                                   │     │
│  [Downstream CAD Generation]                              │     │
│       │ authority: preserved from input                   │     │
│       │ provenance: full chain attached                   │     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Constitutional Boundaries

### Inviolable Rules

1. **No silent authority elevation**
   - Authority state changes must be explicit
   - Transitions must be logged
   - Forbidden transitions must fail

2. **No provenance stripping**
   - Exports must preserve derivation chain
   - Flattening provenance is forbidden
   - Source lineage must survive all transformations

3. **No review bypass**
   - Advisory candidates cannot become canonical without human review
   - `human_review_required: true` cannot be set to false by machine

4. **No confidence misrepresentation**
   - Confidence type must be declared
   - Confidence does not imply correctness
   - Statistical confidence is not ontological certainty

5. **No cached authority**
   - Cached semantic outputs retain original authority state
   - Cache does not elevate trust level
   - Stale cache must not supersede fresh source

---

## Implementation Requirements

### For BodyIsolationAdapter

The adapter must:

1. Accept only `canonical_source` or `derived_topology` input
2. Output `advisory_candidate` authority state
3. Set `human_review_required: true` on all candidates
4. Preserve full derivation chain
5. Declare confidence type as `statistical` or `heuristic`
6. Never populate IBG memory directly

### For IBG Intake

IBG memory population requires:

1. Input authority state >= `human_reviewed`
2. Provenance chain intact
3. Topology integrity score above threshold
4. Human review decision = `approve`

### For Downstream CAD Generation

CAD export requires:

1. Input authority state >= `approved_for_generation`
2. Provenance metadata attached to output
3. Source lineage preserved in output metadata

---

## Enforcement

### Governance Checks

Add to `scripts/governance/check_all.py`:

```python
def check_provenance_integrity():
    """Verify provenance rules are not violated."""
    # Check for forbidden state transitions
    # Check for missing provenance fields
    # Check for authority inflation
```

### Runtime Assertions

```python
def assert_authority_sufficient(obj, required_state):
    """Fail if object authority is below required level."""
    if obj.provenance.authority_state < required_state:
        raise AuthorityInsufficientError(
            f"Required: {required_state}, "
            f"Actual: {obj.provenance.authority_state}"
        )
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AUTHORITY_STATE_ARCHITECTURE.md` | State machine details |
| `BODYEVIDENCE_PROVENANCE_SPEC.md` | BodyEvidence-specific rules |
| `CONFIDENCE_PROPAGATION_RULES.md` | Confidence semantics |
| `SEMANTIC_AUTHORITY_BOUNDARIES.md` | Boundary enforcement |

---

## Ratification Status

| Section | Status |
|---------|--------|
| Authority State Taxonomy | DRAFT |
| Provenance Object Structure | DRAFT |
| Confidence Semantics | DRAFT |
| Transformation Stages | DRAFT |
| Constitutional Boundaries | DRAFT |
| Implementation Requirements | DRAFT |

This document requires Chief Engineer ratification before becoming Tier 1 governance.

---

*SEMANTIC_PROVENANCE_MODEL.md — DEV ORDER 1A — 2026-05-18*
