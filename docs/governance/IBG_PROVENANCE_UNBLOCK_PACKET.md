# IBG Provenance Unblock Packet

**Created**: 2026-05-24  
**Status**: Action required — governance ratification  
**Blocking**: 5 DXF save points in `BLOCKED_PROVENANCE` lifecycle class

---

## 1. Blocked Save Points

| File | Line | Function | Current Status |
|------|------|----------|----------------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777 | `_export_contour_dxf` | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/body_contour_solver.py` | 808 | `_export_debug_dxf` | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116 | `_save_arc_geometry` | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1279 | `_export_reconstruction` | BLOCKED_PROVENANCE |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1303 | `_save_final_output` | BLOCKED_PROVENANCE |

**Risk if unblocked prematurely**: Ungoverned geometry export; authority laundering through unmarked provenance chain.

---

## 2. Required Provenance Fields

Each blocked save point must attach a `ProvenanceRecord` with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_type` | enum | Yes | `VECTORIZER_OUTPUT`, `SEMANTIC_INFERENCE`, `HUMAN_EDITED` |
| `source_id` | string | Yes | Reference to input artifact (blueprint UUID, vectorizer run ID) |
| `epistemic_status` | enum | Yes | One of: `PREDICTED`, `HEURISTIC`, `OPERATOR_ANNOTATED` |
| `transformation_chain` | list | Yes | Ordered list of processing steps |
| `human_review_status` | enum | Yes | `PENDING`, `REVIEWED`, `APPROVED` |
| `created_at` | ISO8601 | Yes | Timestamp |
| `created_by` | string | Yes | System/operator identifier |

---

## 3. Authority State Requirements

**Before unblock** (current):
```
AuthorityState.SANDBOX_EXPERIMENTAL  or
AuthorityState.ADVISORY_CANDIDATE
```

**After ratification** (target):
```
AuthorityState.DERIVED_TOPOLOGY  (with provenance attached)
```

**Never without human review**:
```
AuthorityState.CANONICAL_GEOMETRY
AuthorityState.APPROVED_FOR_GENERATION
```

---

## 4. Epistemic Status Mapping (ADR-0012)

| IBG Output Type | Epistemic Status | May Enter Production Export? |
|-----------------|------------------|------------------------------|
| Raw vectorizer geometry | PREDICTED | No — requires review |
| Morphology-inferred contour | HEURISTIC | No — advisory only |
| Human-reviewed geometry | OPERATOR_ANNOTATED | Yes — after approval |
| Ratified canonical body | OBSERVED (equivalent) | Yes — production |

---

## 5. Human Decision Required

**Governance session must decide**:

1. Is the provenance attachment spec (`ProvenanceRecord` → `DxfLifecycleContext`) complete?
2. Are the epistemic status mappings correct for IBG outputs?
3. Should `BLOCKED_PROVENANCE` paths graduate to `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`?
4. What is the review threshold — per-export or per-session approval?

**Format**: Synchronous governance session (not async PR review)

---

## 6. Exit Criteria

| Criterion | Verification |
|-----------|--------------|
| Provenance spec ratified | Signed governance record |
| ProvenanceRecord schema published | `schemas/provenance_record.schema.json` exists |
| IBG saves wired through provenance wrapper | Unit tests: save rejected without provenance |
| Matrix updated | 5 rows change from `BLOCKED_PROVENANCE` to `COMPAT_ONLY` or `LIFECYCLE_GOVERNED` |
| Lifecycle validator green | No `BLOCKED` risk level in CI |

---

## 7. Forbidden Until Ratification

| Action | Why |
|--------|-----|
| Add guards that imply production legitimacy | False confidence |
| Promote to `LIFECYCLE_GOVERNED` without provenance | Violates fail-closed |
| Treat `rank_score` as export approval | Authority laundering |
| Merge vectorizer outputs into spine defaults | `R_AND_D_EXCLUDED` boundary |

---

## 8. Owner and Timeline

| Item | Value |
|------|-------|
| Owner | luthiers-toolbox governance owner |
| Target | Next governance sprint (post 2026-05-24) |
| Dependencies | `CANONICAL_PROVENANCE_MODEL.md` ratification |
| Tracking | Update `MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` on completion |

---

## 9. Quick Reference

```
Files blocked:     5
Required fields:   7
Governance type:   Synchronous session
Exit criteria:     5 checkpoints
Risk if skipped:   Authority laundering, ungoverned export
```

---

*Packet version: 2026-05-24*  
*Source: IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md*
