# Body Isolation Adapter Redesign Notes

**Date:** 2026-05-18  
**Status:** PHASE 1-2A COMPLETE — DXF path constitutionally gated  
**Sprints:** DEV ORDER 1D, 1D-HARDEN, 2A  
**Commits:** `4f3039f3`, `a0135f93`, `7a8f918b`

---

## Summary

The constitutional runtime foundation is implemented. The DXF artifact path now produces `BodyEvidenceCandidate` with full provenance, authority state, confidence declaration, and review enforcement. The IBG Intake Gate blocks all candidates until human approval.

---

## Implementation Status

### Completed (Phase 1 + 2A)

| Component | Location | Status |
|-----------|----------|--------|
| `AuthorityState` enum | `app/governance/authority_state.py` | ✓ COMPLETE |
| `AuthorityStateContainer` | `app/governance/authority_state.py` | ✓ COMPLETE |
| `ProvenanceRecord` | `app/governance/provenance_record.py` | ✓ COMPLETE |
| `ConfidenceDeclaration` | `app/governance/confidence_declaration.py` | ✓ COMPLETE |
| `ReviewEnforcement` | `app/governance/review_enforcement.py` | ✓ COMPLETE |
| `BodyEvidenceCandidate` | `app/instrument_geometry/body/ibg/body_evidence_candidate.py` | ✓ COMPLETE |
| `IBGIntakeGate` | `app/instrument_geometry/body/ibg/ibg_intake_gate.py` | ✓ COMPLETE |
| `artifact_body_evidence_adapter.py` | `app/.../morphology_harvest/artifact_body_evidence_adapter.py` | ✓ COMPLETE |

### Remaining (Future Work)

| Component | Location | Status |
|-----------|----------|--------|
| `BodyIsolationResult` provenance | `services/photo-vectorizer/body_isolation_result.py` | NOT STARTED |
| `GeometryCoachV2` integration | `services/photo-vectorizer/geometry_coach_v2.py` | NOT STARTED |
| Human review UI | `blueprint_reader.html` or new | NOT STARTED |
| IBG memory population | — | BLOCKED (by design) |

---

## Architecture Decision

**Chosen: Option B — Wrapper Class**

Instead of patching `BodyIsolationResult` directly, the implementation created:

```
BodyEvidence (plain data container)
    ↓ wrapped by
BodyEvidenceCandidate (constitutional wrapper)
    ↓ validated by
IBGIntakeGate (entry gate)
```

**Rationale:**
- Separation of concerns (data vs. governance)
- No breaking changes to existing callers
- Clear constitutional boundary
- Reusable pattern for other semantic objects

---

## Data Flow (DXF Path — Implemented)

```
[DXF Artifact from Vectorizer]
    │
    ▼
[artifact_body_evidence_adapter.from_vectorizer_response_constitutional()]
    │ creates: BodyEvidence
    │ wraps in: BodyEvidenceCandidate
    │ attaches: ProvenanceRecord, AuthorityState, ConfidenceDeclaration
    │ sets: review_required = True, authority = advisory_candidate
    ▼
[IBGIntakeGate.validate()]
    │ checks: authority, provenance, review, confidence, topology
    │ result: BLOCKED (no human approval yet)
    ▼
[Human Review via API]
    │ candidate.record_review("human:reviewer", APPROVE, notes)
    │ authority transitions: advisory_candidate → human_reviewed
    ▼
[IBGIntakeGate.validate()]
    │ result: PASSED
    │ candidate.approved_for_ibg_memory = True
    ▼
[IBG Memory Population]
    │ (NOT YET IMPLEMENTED — gate exists, path blocked)
```

---

## Data Flow (Photo Path — Not Yet Implemented)

```
[Photo Input]
    │
    ▼
[BodyIsolationStage.run()]
    │ produces: BodyIsolationResult (pixel space)
    │ NO PROVENANCE YET
    ▼
[GeometryCoachV2.decide()]
    │ NO CONSTITUTIONAL WRAPPER YET
    ▼
[Future: Convert to BodyEvidence → BodyEvidenceCandidate]
    │ attach provenance
    │ pass through IBGIntakeGate
```

---

## Governance Modules

Located in `services/api/app/governance/`:

| Module | Purpose |
|--------|---------|
| `authority_state.py` | 9-state enum, FORBIDDEN_TRANSITIONS, AuthorityStateContainer |
| `provenance_record.py` | ProvenanceRecord, TransformationStage, derivation chains |
| `confidence_declaration.py` | Typed confidence that never implies correctness/canonicity |
| `review_enforcement.py` | Protected review_required, bypass attempt tracking |
| `__init__.py` | Public exports |

### AuthorityState Values

```python
SANDBOX_EXPERIMENTAL      # Untrusted experimental
ADVISORY_CANDIDATE        # Ranked suggestion, not ratified
HUMAN_REVIEWED           # Examined by human
APPROVED_FOR_GENERATION  # Cleared for CAD output
CANONICAL_GEOMETRY       # Original source artifact
DERIVED_TOPOLOGY         # Reconstructed from source
SEMANTIC_INTERPRETATION  # Meaning inferred
REJECTED                 # Explicitly rejected
ARCHIVED_SUPERSEDED      # No longer authoritative
```

### Forbidden Transitions

```python
FORBIDDEN_TRANSITIONS = {
    (ADVISORY_CANDIDATE, CANONICAL_GEOMETRY),
    (ADVISORY_CANDIDATE, APPROVED_FOR_GENERATION),
    (SANDBOX_EXPERIMENTAL, APPROVED_FOR_GENERATION),
    (SANDBOX_EXPERIMENTAL, CANONICAL_GEOMETRY),
    (DERIVED_TOPOLOGY, CANONICAL_GEOMETRY),
    (SEMANTIC_INTERPRETATION, CANONICAL_GEOMETRY),
    (REJECTED, APPROVED_FOR_GENERATION),
    (REJECTED, CANONICAL_GEOMETRY),
}
```

---

## IBG Intake Gate

Located in `app/instrument_geometry/body/ibg/ibg_intake_gate.py`

### Rejection Reasons

| Reason | Description |
|--------|-------------|
| `AUTHORITY_INSUFFICIENT` | Authority < human_reviewed |
| `PROVENANCE_MISSING` | No provenance record |
| `PROVENANCE_INCOMPLETE` | Incomplete lineage |
| `REVIEW_REQUIRED` | Review not completed |
| `REVIEW_NOT_APPROVED` | Completed but not approved |
| `CONFIDENCE_UNDECLARED` | Unknown confidence type |
| `REVIEW_BYPASS_DETECTED` | Bypass attempts > threshold |
| `TOPOLOGY_INTEGRITY_DEGRADED` | Integrity below minimum |
| `CANDIDATE_REJECTED` | In REJECTED state |

### Gate Configurations

```python
create_default_intake_gate()    # Standard: 0.5 topology, 0 bypass tolerance
create_strict_intake_gate()     # Production: 0.7 topology, stricter authority
create_permissive_intake_gate() # Dev only: 0.3 topology, 2 bypass tolerance
```

---

## Constitutional Adapter Output

`artifact_body_evidence_adapter.from_vectorizer_response_constitutional()` returns:

```python
@dataclass
class ConstitutionalAdapterResult:
    success: bool
    candidate: Optional[BodyEvidenceCandidate]
    gate_result: Optional[IntakeValidationResult]
    topology_integrity: float
    metadata: Optional[ArtifactMetadata]
    errors: Optional[List[str]]

    def to_review_json(self) -> Dict[str, Any]:
        """Review-ready JSON for API-only workflow."""
```

### Review JSON Structure

```json
{
  "candidate_id": "bec_abc123def456",
  "source_dxf": "/blueprints/guitar.dxf",
  "provenance": { "source_artifact": "...", "transformation_history": [...] },
  "authority_state": "advisory_candidate",
  "confidence_declaration": { "value": 0.75, "confidence_type": "heuristic", ... },
  "topology_integrity": 0.85,
  "gate_decision": { "is_valid": false, "rejections": ["authority_insufficient", "review_required"] },
  "review_required": true,
  "review_notes_placeholder": "",
  "metadata": { "source_file": "...", "entity_count": 42, "closed_contours": 3 }
}
```

---

## Tests

| Test File | Coverage |
|-----------|----------|
| `test_governance_constitutional_runtime.py` | Authority, provenance, confidence, review |
| `test_ibg_intake_gate.py` | Gate rejection/acceptance |
| `test_ibg_constitutional_integration.py` | Full flow smoke tests, failure modes |
| `test_artifact_constitutional_adapter.py` | Constitutional adapter output |

---

## Acceptance Criteria (Phase 1 + 2A)

| Criterion | Status |
|-----------|--------|
| ProvenanceRecord exists and propagates | ✓ |
| AuthorityState exists and is enforced | ✓ |
| ConfidenceDeclaration separates confidence from legitimacy | ✓ |
| BodyEvidenceCandidate carries constitutional metadata | ✓ |
| IBGIntakeGate blocks unauthorized intake | ✓ |
| Review bypass vulnerability is closed | ✓ |
| DXF adapter produces BodyEvidenceCandidate | ✓ |
| Gate blocks by default | ✓ |
| Review-ready JSON exists | ✓ |
| Tests prove weak provenance cannot enter IBG | ✓ |

---

## Original Audit (Historical Reference)

The original audit identified these gaps in `BodyIsolationResult`:

| Gap | Resolution |
|-----|------------|
| No authority state | Addressed via `BodyEvidenceCandidate` wrapper (DXF path) |
| No provenance lineage | `ProvenanceRecord` attached to candidate |
| Bare confidence float | `ConfidenceDeclaration` with typed semantics |
| Review bypass possible | `ReviewEnforcement` with protected flag |
| No intake gate | `IBGIntakeGate` with 8 rejection reasons |

The photo-vectorizer `BodyIsolationResult` still has these gaps. Future work will either:
- Add provenance fields directly to `BodyIsolationResult`
- Convert `BodyIsolationResult` → `BodyEvidence` → `BodyEvidenceCandidate`

---

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Where does human review happen? | API-only for now (future: UI) |
| Governance module location? | Shared `app/governance/`, not IBG-specific |
| Patch or wrap? | Wrap (`BodyEvidenceCandidate`) |
| Which path first? | DXF path (simpler, canonical artifacts) |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | Full foundation specification |
| `IBG_CONSTITUTIONAL_RUNTIME_1A_COVERAGE_NOTE.md` | 1A/1D relationship |
| `SEMANTIC_PROVENANCE_MODEL.md` | Constitutional foundation theory |
| `IBG_ROLE_DEFINITION.md` | IBG governance boundaries |

---

*BODY_ISOLATION_ADAPTER_REDESIGN_NOTES.md — Updated 2026-05-18 after DEV ORDER 2A*
