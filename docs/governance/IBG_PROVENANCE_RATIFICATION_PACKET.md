# IBG Provenance Ratification Packet

**Sprint:** MRP-6C  
**Status:** R1 RATIFICATION PREP  
**Date:** 2026-05-24  
**Authority:** Governance ratification material — NOT operational policy until R1 completes

---

## Executive Summary

This packet prepares the R1 governance ratification session for IBG provenance attachment. It defines exactly what provenance must exist at the IBG DXF save boundary before any of the five blocked save points can transition from `BLOCKED_PROVENANCE` to `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`.

**Core principle:**
```
IBG may generate semantic pressure.
IBG may not resolve semantic legitimacy.
```

Therefore:
```
IBG export promotion requires governance-ratified provenance,
not implementation convenience.
```

---

## Current Blocked Save Points

Five IBG DXF save points remain intentionally blocked:

| File | Lines | Status |
|------|-------|--------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116, 1279, 1303 | BLOCKED_PROVENANCE |

**Matrix reference:** `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` Section 3

These paths use `DxfWriter` (compat-governed) but must not receive lifecycle promotion until provenance attachment is ratified and wired.

---

## Ratification Dependencies

| Prerequisite | Document | Status |
|--------------|----------|--------|
| Canonical provenance taxonomy | `CANONICAL_PROVENANCE_MODEL.md` | DRAFT FOR GOVERNANCE RATIFICATION |
| IBG constitutional foundation | `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | IMPLEMENTED — Pending Ratification |
| Cross-repo authority alignment | `CROSS_REPO_AUTHORITY_CROSSWALK.md` | Created 2026-05-24 |
| Export lifecycle classification | `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Active |
| Ratification timeline | `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Active |

---

## Required Provenance Attachment Fields

### Schema Layers

Two provenance schemas exist as complementary layers:

| Layer | Document | Role |
|-------|----------|------|
| Canonical taxonomy | `CANONICAL_PROVENANCE_MODEL.md` | Abstract provenance contract |
| IBG runtime shape | `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | Concrete IBG provenance candidate |

Neither schema is superseded. MRP-6C reconciles them without merging.

### Canonical → IBG → DXF Lifecycle Mapping

| Canonical Field | IBG Runtime Field | DXF Lifecycle Implication |
|-----------------|-------------------|---------------------------|
| `provenance_type` | `object_type` | Determines `authority_context` |
| `provenance_agent` | `derived_from`, `derivation_chain` | Populates `source_module` lineage |
| `provenance_timestamp` | (implicit in transformation_history) | Audit trail |
| `provenance_payload.derivation_inputs` | `source_artifact` | Sets `provenance_status` |
| `provenance_payload.derivation_algorithm` | `transformation_history[].stage` | Documents reconstruction method |
| — | `topology_integrity_score` | Gate threshold for promotion |

### Required IBG Provenance Fields at DXF Boundary

The following fields MUST be present before any IBG DXF save:

| Field | Required | Source | Purpose |
|-------|----------|--------|---------|
| `provenance_record_id` | Yes | Auto-generated | Unique lineage anchor |
| `source_artifact_id` | Yes | Upstream DXF/blueprint | Origin traceability |
| `ibg_run_id` | Yes | Workflow execution | Session traceability |
| `candidate_id` | Yes | BodyEvidenceCandidate | Semantic object reference |
| `epistemic_status` | Yes | Pipeline stage | Authority posture |
| `authority_state` | Yes | AuthorityStateContainer | Governance state |
| `confidence_type` | Yes | ConfidenceDeclaration | Confidence semantics |
| `topology_integrity_score` | Yes | ProvenanceRecord | Quality threshold |
| `reconstruction_method` | Yes | transformation_history | Algorithm lineage |
| `operator_review_status` | Yes | ReviewEnforcement | Human review state |
| `export_intent` | Yes | Caller | Purpose declaration |
| `lifecycle_target` | Yes | Caller | COMPAT_ONLY or LIFECYCLE_GOVERNED |
| `schema_version` | Yes | Fixed | Contract version |

**Detailed field matrix:** See `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md`

---

## ProvenanceRecord → DxfLifecycleContext Mapping

`DxfLifecycleContext` is the existing lifecycle gate context. It should NOT be extended in R2.

Instead, R2 should implement a **separate companion object**:

```
DxfLifecycleContext (existing)
+
IBGProvenanceAttachment (new, required for IBG paths)
```

### Mapping to Existing DxfLifecycleContext Fields

| DxfLifecycleContext Field | IBG Provenance Source | Value Pattern |
|---------------------------|----------------------|---------------|
| `source_module` | `ibg_run_id` + caller | `"ibg.body_contour_solver"` |
| `export_type` | Fixed | `"dxf-create-save"` |
| `dxf_version` | Caller/config | `"R2000"` or `"R12"` |
| `lifecycle_status` | Gate decision | `"COMPAT_ONLY"` (post-R2) |
| `runtime_callable` | Caller | `"runtime_service"` |
| `authority_context` | `authority_state` | `"ibg_semantic_interpretation"` |
| `provenance_status` | Attachment presence | `"IBG_ATTACHED"` or `"PENDING"` |

### Future R2 Implementation Shape

```python
@dataclass
class IBGProvenanceAttachment:
    """Required companion for IBG DXF saves after R2."""
    provenance_record_id: str
    source_artifact_id: str
    ibg_run_id: str
    candidate_id: str
    epistemic_status: EpistemicStatus
    authority_state: AuthorityState
    confidence_type: ConfidenceType
    topology_integrity_score: float
    reconstruction_method: str
    operator_review_status: str
    export_intent: str
    lifecycle_target: str
    schema_version: str = "ibg_provenance.v1"
```

This is pseudocode only. R2 implements; MRP-6C documents.

---

## Epistemic Status Mapping

### Cross-Repo Authority Reference

The canonical epistemic taxonomy comes from tap_tone ADR-0012 via:
```
docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md
```

**Crosswalk = authority reference**

### IBG-Specific Application Table

For engineer usability, IBG outputs map to epistemic status as follows:

| IBG Pipeline Stage | Epistemic Status | Authority Level | May Populate IBG Memory? |
|--------------------|------------------|-----------------|--------------------------|
| Source artifact intake | EXTERNALLY_SOURCED | External authority | No (input only) |
| Topology reconstruction | DERIVED | Computationally authoritative | No |
| Gap closure | DERIVED | Computationally authoritative | No |
| Body isolation | PREDICTED | Model-dependent | No |
| Morphology analysis | PREDICTED | Model-dependent | No |
| Candidate ranking | HEURISTIC | No authority | No |
| Human review (approve) | OPERATOR_ANNOTATED | Operator only | **Yes** (after gate) |
| Human review (reject) | OPERATOR_ANNOTATED | Operator only | No |

**IBG table = applied implementation guidance**

### Key Invariants

```
rank_score is HEURISTIC — not approval
confidence_value is HEURISTIC — not correctness
PREDICTED does not imply DERIVED
DERIVED does not imply OBSERVED
No epistemic status implies execution authority
```

---

## Authority Laundering Failure Modes

Authority laundering occurs when an operation silently elevates authority without proper governance transition.

### Failure Mode 1: Rank-to-Approval Laundering

```
FAILURE: rank_score 0.95 → treated as approval
CORRECT: rank_score 0.95 → sorting priority only
```

**Detection:** `rank_score` appears in authorization logic
**Prevention:** Model-enforced `implies_correctness() → False`

### Failure Mode 2: Confidence-to-Authority Laundering

```
FAILURE: confidence_value 0.99 → skips review
CORRECT: confidence_value 0.99 → still requires human review
```

**Detection:** `confidence_value` in review bypass conditions
**Prevention:** ReviewEnforcement protected setter

### Failure Mode 3: Derivation-to-Observation Laundering

```
FAILURE: DERIVED topology → labeled OBSERVED
CORRECT: DERIVED topology → remains DERIVED
```

**Detection:** epistemic_status upgraded without transformation record
**Prevention:** Provenance chain audit

### Failure Mode 4: Silent Lifecycle Promotion

```
FAILURE: BLOCKED_PROVENANCE → LIFECYCLE_GOVERNED (no ratification)
CORRECT: BLOCKED_PROVENANCE → R1 → R2 → COMPAT_ONLY
```

**Detection:** Matrix row changes without governance record
**Prevention:** CI matrix validation

### Failure Mode 5: IBG Memory Bypass

```
FAILURE: BodyEvidence → IBG memory (no gate)
CORRECT: BodyEvidenceCandidate → IBGIntakeGate → IBG memory
```

**Detection:** IBG memory write without gate.validate()
**Prevention:** Gate integration enforcement

---

## Ratification Checklist

### R0 — Documentation Convergence (MRP-6C)

- [x] Lifecycle matrix marks 5 calls BLOCKED_PROVENANCE
- [x] DXF guard plan documents disposition blocked_provenance
- [x] Cross-repo authority crosswalk maps epistemic posture
- [x] Research layer governance entry created
- [ ] IBG provenance ratification packet created (this document)
- [ ] IBG provenance field matrix created
- [ ] IBG DXF lifecycle mapping addendum created
- [ ] Governance inventory entry for IBG provenance block
- [ ] Ratification timeline updated with MRP-6C status

### R1 — Governance Ratification (Future Sprint)

- [ ] CANONICAL_PROVENANCE_MODEL.md ratified
- [ ] IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md authority tier ratified
- [ ] IBGProvenanceAttachment schema approved
- [ ] Required fields finalized
- [ ] Transition rules signed
- [ ] Exit criteria verified

### R2 — Minimal Export Wrapper (Future Sprint)

- [ ] IBGProvenanceAttachment implemented
- [ ] Save boundary wiring complete
- [ ] Unit tests: save rejected without attachment
- [ ] Unit tests: save allowed with valid attachment
- [ ] Matrix rows reclassified COMPAT_ONLY
- [ ] No BLOCKED risk level remaining

---

## R1 Exit Criteria

R1 ratification is complete when:

1. Governance record exists documenting:
   - IBGProvenanceAttachment schema approval
   - Required fields list finalized
   - Authority state transition rules ratified
   - Epistemic status mapping ratified

2. Matrix blocking condition updated from:
   ```
   awaiting ratification
   ```
   to:
   ```
   implementation approved
   ```

3. No open questions in provenance model

4. Cross-repo alignment verified against crosswalk

---

## R2 Implementation Preconditions

R2 may NOT begin until:

1. R1 exit criteria met
2. IBGProvenanceAttachment schema exists in code
3. Save boundary integration points identified
4. Test patterns established
5. Rollback plan documented

R2 implements:
- Export wrapper
- Gate wiring
- Matrix reclassification

R2 does NOT implement:
- New ontology terms
- Schema changes beyond IBGProvenanceAttachment
- Cross-repo runtime integration

---

## Explicit Non-Implementation Statement

**MRP-6C does not:**
- Unblock IBG DXF exports
- Add lifecycle guards implying production legitimacy
- Promote BLOCKED_PROVENANCE rows
- Wire export wrappers
- Modify DXF save behavior
- Treat rank_score as approval
- Merge vectorizer-sandbox outputs into production defaults
- Create new ontology without ratification

All five IBG save points remain `BLOCKED_PROVENANCE` after MRP-6C.

---

## Related Documents

| Document | Role |
|----------|------|
| `CANONICAL_PROVENANCE_MODEL.md` | Provenance taxonomy |
| `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | IBG runtime foundation |
| `CROSS_REPO_AUTHORITY_CROSSWALK.md` | Cross-repo vocabulary alignment |
| `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Lifecycle classification |
| `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Chronology |
| `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` | Field requirements |
| `IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md` | Lifecycle transition rules |
| `IBG_PROVENANCE_GOVERNANCE_ENTRY.md` | Inventory pointer |

---

*IBG Provenance Ratification Packet — MRP-6C — 2026-05-24*
