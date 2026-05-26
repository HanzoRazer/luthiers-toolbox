# IBG Provenance R1 Ratification Record

**Decision ID:** IBG-R1-________  
**Date:** YYYY-MM-DD  
**Participants:**  
**Status:** DRAFT | SIGNED

---

## Ratified documents

| Document | Version / commit | Ratified |
|----------|------------------|----------|
| `CANONICAL_PROVENANCE_MODEL.md` | | [ ] |
| `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | | [ ] |
| `IBG_PROVENANCE_RATIFICATION_PACKET.md` | | [ ] |
| `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` | | [ ] |
| `IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md` | | [ ] |

---

## Approved save-boundary fields

Copy mandatory fields from `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` and freeze:

| Field | Required at save | Notes |
|-------|------------------|-------|
| `provenance_record_id` | | |
| `source_artifact_id` | | |
| `ibg_run_id` | | |
| `candidate_id` | | |
| `epistemic_status` | | |
| `authority_state` | | |
| `confidence_type` | | |
| `topology_integrity_score` | | |
| `reconstruction_method` | | |
| `operator_review_status` | | |
| `export_intent` | | |
| `lifecycle_target` | | |
| `schema_version` | | |

---

## Epistemic posture at export

- Default export posture: `predicted` / `heuristic`
- Production `OBSERVED` / `DERIVED` authority: forbidden without separate ADR
- `rank_score` is not export authorization

---

## Lifecycle transition approval

- [ ] `BLOCKED_PROVENANCE` → `COMPAT_ONLY` via provenance wrapper (DO 79/80)
- [ ] Direct `BLOCKED_PROVENANCE` → `LIFECYCLE_GOVERNED` forbidden
- [ ] Matrix updates require explicit governance PR

---

## Engineering authorization

- [ ] Phase D: `BodyEvidenceCandidate` → `ProvenanceAttachmentDraft` bridge
- [ ] Phase E: ratified export enablement mechanism
- [ ] No production bypass of `governed_ibg_writer_saveas`

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Governance owner | | |
| Platform engineering | | |

---

*Template — MRP-6C / DO 80. Signed copy: `IBG_R1_RATIFICATION_RECORD_YYYY-MM-DD.md`.*
