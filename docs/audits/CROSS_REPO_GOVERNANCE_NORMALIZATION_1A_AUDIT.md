# Cross-Repo Governance Normalization 1A — Sprint Audit

**Date:** 2026-05-24  
**Sprint:** Cross-Repo Governance Normalization 1A  
**Repo:** luthiers-toolbox  
**Branch:** `feat/confidence-envelope-interoperability`  
**PR:** #38  
**Status:** **COMPLETE — Ready for Review**

---

## Executive Summary

This sprint implemented additive convergence contracts for cross-repo interoperability. All work is **compatibility layer only** — no replacement of existing models, no IBG unblocking, no runtime federation.

| Metric | Value |
|--------|-------|
| Files created | 7 |
| Tests added | 72 |
| Tests passing | 72 |
| IBG save points unblocked | 0 |
| Runtime federation introduced | No |
| Existing models replaced | No |

---

## Completed Deliverables

### 1. ConfidenceEnvelopeV1 (Complete)

**File:** `services/api/app/governance/confidence_envelope.py`

Cross-repo semantic compatibility layer that wraps confidence values WITHOUT replacing existing models.

| Feature | Status |
|---------|--------|
| Core dataclass | ✓ Implemented |
| Constitutional invariants | ✓ Enforced |
| Factory methods | ✓ 4 methods |
| Serialization | ✓ Round-trip tested |
| Tests | ✓ 23 passing |

**Preserved Models (NOT replaced):**
- `TypedConfidenceV1` (tap_tone_pi)
- `ConfidenceDeclaration` (luthiers-toolbox)
- `rank_score` (IBG workflow)
- `confidence_value` (various)

**Constitutional Invariants:**
```python
runtime_authoritative: Literal[False] = False   # CANNOT be overridden
review_required: Literal[True] = True           # CANNOT be overridden
execution_authorized: Literal[False] = False   # CANNOT be overridden
```

**Factory Methods:**
| Method | Source System |
|--------|---------------|
| `from_confidence_declaration()` | luthiers-toolbox |
| `from_typed_confidence_dict()` | tap_tone_pi |
| `from_rank_score()` | IBG workflow |
| `from_vectorizer_output()` | vectorizer-sandbox |

---

### 2. ProvenanceAttachmentDraft (Complete)

**File:** `services/api/app/governance/provenance_attachment.py`

Draft structures for IBG provenance ratification substrate. **NOT wired to DXF export.**

| Feature | Status |
|---------|--------|
| Core dataclass | ✓ Implemented |
| Status enum | ✓ 4 states |
| IBG factory | ✓ Defaults to BLOCKED |
| Submission logic | ✓ Blocked cannot submit |
| Tests | ✓ 26 passing |

**Provenance Attachment Status:**
| Status | Exportable | IBG Default |
|--------|------------|-------------|
| `DRAFT` | No | — |
| `PENDING_RATIFICATION` | No | — |
| `RATIFIED` | Yes* | — |
| `BLOCKED` | No | **Yes** |

*Ratification requires explicit governance session — this code path cannot ratify.

**IBG Default Behavior:**
```python
IBG_DEFAULT_STATUS = ProvenanceAttachmentStatus.BLOCKED
# IBG drafts require R1 ratification session
# Cannot be submitted for ratification while blocked
```

---

### 3. AuthorityMetadata (Complete)

**File:** `services/api/app/governance/authority_metadata.py`

Additive metadata structure for cross-repo normalization. All fields optional or default-safe.

| Feature | Status |
|---------|--------|
| Core dataclass | ✓ Implemented |
| ReviewState enum | ✓ 7 states |
| LifecycleState enum | ✓ 5 states |
| SourceRepo enum | ✓ 6 values |
| Factory functions | ✓ 3 functions |
| Tests | ✓ 23 passing |

**Default Authority Exclusions:**
```python
authority_exclusions = [
    "execution authorization",
    "production deployment",
    "governance bypass",
    "review bypass",
    "lifecycle promotion",
    "cross-repo authority propagation",
]
```

**Factory Functions:**
| Function | Use Case |
|----------|----------|
| `create_luthiers_authority_metadata()` | General luthiers artifacts |
| `create_vectorizer_authority_metadata()` | R&D excluded outputs |
| `create_ibg_authority_metadata()` | IBG with blocked provenance |

---

### 4. Documentation (Complete)

| Document | Purpose |
|----------|---------|
| `docs/governance/CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md` | Envelope compatibility spec |
| `docs/governance/AUTHORITY_METADATA_NORMALIZATION.md` | Metadata contract spec |
| `docs/governance/IBG_PROVENANCE_ATTACHMENT_SPEC.md` | R1 ratification substrate |

All docs explicitly state: **"compatibility layer, not replacement"**

---

### 5. Tests (Complete)

**Location:** `tests/governance/`

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_confidence_envelope.py` | 23 | ✓ All passing |
| `test_provenance_attachment_draft.py` | 26 | ✓ All passing |
| `test_authority_metadata.py` | 23 | ✓ All passing |
| **Total** | **72** | **✓ All passing** |

**Key Test Categories:**
- Constitutional invariant enforcement
- Source system wrapping
- Serialization round-trip
- Factory function correctness
- IBG blocked status enforcement
- Authority exclusion verification

---

### 6. Module Exports (Complete)

**File:** `services/api/app/governance/__init__.py`

All new types are exported:

```python
# Confidence Envelope
ConfidenceEnvelopeV1, SemanticDomain, EpistemicStatus, SourceSystem

# Provenance Attachment
ProvenanceAttachmentDraft, ProvenanceAttachmentStatus, IBG_DEFAULT_STATUS

# Authority Metadata
AuthorityMetadata, ReviewState, LifecycleState, SourceRepo
```

---

## Explicitly NOT Done (Per Sprint Scope)

| Item | Status | Reason |
|------|--------|--------|
| IBG DXF saves unblocked | NOT DONE | Requires R1 ratification |
| R1 provenance ratified | NOT DONE | Requires governance session |
| IBG exports lifecycle-governed | NOT DONE | Requires provenance wiring |
| Runtime federation | NOT DONE | Out of scope |
| Confidence schema replacement | NOT DONE | Compatibility layer only |
| Automatic governance routing | NOT DONE | Out of scope |
| vectorizer-sandbox modifications | NOT DONE | Separate repo |
| Production semantic consensus | NOT DONE | Out of scope |
| Package restructure to `contracts/` | NOT DONE | Noted as pending |

---

## IBG Blocked Provenance Verification

All 5 IBG save points remain `BLOCKED_PROVENANCE`:

| File | Line | Status |
|------|------|--------|
| `body_contour_solver.py` | 777 | BLOCKED_PROVENANCE |
| `body_contour_solver.py` | 808 | BLOCKED_PROVENANCE |
| `arc_reconstructor.py` | 1116 | BLOCKED_PROVENANCE |
| `arc_reconstructor.py` | 1279 | BLOCKED_PROVENANCE |
| `arc_reconstructor.py` | 1303 | BLOCKED_PROVENANCE |

**Verification:** `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` unchanged.

---

## Cross-Repo Compatibility Status

| Repo | Compatibility Artifact | Status |
|------|------------------------|--------|
| tap_tone_pi | `TypedConfidenceV1` wrapping | ✓ Factory method exists |
| luthiers-toolbox | `ConfidenceDeclaration` wrapping | ✓ Factory method exists |
| vectorizer-sandbox | R&D excluded posture | ✓ Factory method exists |
| CAM-Assist-Blueprint | Authority block alignment | ✓ Metadata supports |

**Epistemic Status Alignment (ADR-0012):**
| Status | Implemented |
|--------|-------------|
| OBSERVED | ✓ |
| DERIVED | ✓ |
| ESTIMATED | ✓ |
| PREDICTED | ✓ |
| HEURISTIC | ✓ |
| OPERATOR_ANNOTATED | ✓ |
| EXTERNALLY_SOURCED | ✓ |

---

## Package Structure Note

```
services/api/app/governance/
├── __init__.py                  # Updated exports
├── confidence_envelope.py       # NEW: ConfidenceEnvelopeV1
├── provenance_attachment.py     # NEW: ProvenanceAttachmentDraft
├── authority_metadata.py        # NEW: AuthorityMetadata
├── authority_state.py           # Existing
├── confidence_declaration.py    # Existing (NOT replaced)
├── provenance_record.py         # Existing (NOT replaced)
└── review_enforcement.py        # Existing
```

Contract-like governance models currently live flat under `app/governance` pending package normalization to `app/governance/contracts/`.

---

## Governance Checks

| Check | Result |
|-------|--------|
| `pytest tests/governance -v` | ✓ 72 passed |
| `scripts/governance/check_all.py --tier precommit` | ✓ Passed |

---

## Next Steps (For Other Sprints)

| Priority | Action | Owner |
|----------|--------|-------|
| P1 | Merge PR #38 | Reviewer |
| P1 | Schedule R1 ratification session | Governance |
| P2 | Package normalization to `contracts/` | Platform |
| P2 | Wire provenance to DXF export (post-R1) | IBG |
| P3 | Cross-repo CI normalization | Platform |

---

## Commit History

| Commit | Description |
|--------|-------------|
| `f7d851b3` | Add ConfidenceEnvelopeV1 + IBG spec + tests (23) |
| `93da8fab` | Complete convergence contracts + docs + tests (49) |

---

## Files Changed Summary

**New Files (7):**
```
services/api/app/governance/confidence_envelope.py
services/api/app/governance/provenance_attachment.py
services/api/app/governance/authority_metadata.py
docs/governance/CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md
docs/governance/AUTHORITY_METADATA_NORMALIZATION.md
docs/governance/IBG_PROVENANCE_ATTACHMENT_SPEC.md
tests/governance/test_confidence_envelope.py
tests/governance/test_provenance_attachment_draft.py
tests/governance/test_authority_metadata.py
```

**Modified Files (1):**
```
services/api/app/governance/__init__.py
```

---

## Acceptance Criteria Verification

| Criterion | Met |
|-----------|-----|
| ConfidenceEnvelopeV1 exists | ✓ |
| Provenance attachment draft model exists | ✓ |
| Authority metadata model exists | ✓ |
| Governance docs explain compatibility boundaries | ✓ |
| Tests prove confidence does not imply authority | ✓ |
| IBG provenance remains blocked | ✓ |
| No runtime federation introduced | ✓ |
| Governance checks pass | ✓ |

---

*Audit generated: 2026-05-24*  
*Sprint: Cross-Repo Governance Normalization 1A*  
*Auditor: Claude Code*
