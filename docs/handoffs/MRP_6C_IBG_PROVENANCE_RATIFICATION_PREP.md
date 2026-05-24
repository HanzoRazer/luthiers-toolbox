# MRP-6C: IBG Provenance Ratification Prep

**Sprint:** MRP-6C  
**Status:** COMPLETE  
**Date:** 2026-05-24  
**Handoff Author:** Claude (MRP governance sprint)

---

## Summary

Prepared R1 governance ratification materials for the 5 IBG BLOCKED_PROVENANCE DXF save points. This sprint creates documentation infrastructure for the R1 governance session — it does NOT unblock exports.

---

## Deliverables

| Artifact | Purpose | Location |
|----------|---------|----------|
| Ratification Packet | R1 session material | `docs/governance/IBG_PROVENANCE_RATIFICATION_PACKET.md` |
| Field Matrix | Required fields at save boundary | `docs/governance/IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` |
| Lifecycle Addendum | Transition rules | `docs/governance/IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md` |
| Governance Entry | Inventory pointer | `docs/governance/IBG_PROVENANCE_GOVERNANCE_ENTRY.md` |
| Timeline Update | R0 → COMPLETE | `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |
| Validation Tests | Doc consistency | `tests/test_ibg_provenance_ratification_docs.py` |

---

## Architectural Decisions

### IBGProvenanceAttachment as Companion Object

The attachment is a **separate companion object** to `DxfLifecycleContext`, not an extension of it:

```
DxfLifecycleContext (7 fields)    IBGProvenanceAttachment (14+ fields)
├── source_module                 ├── provenance_record_id
├── export_type                   ├── candidate_id
├── dxf_version                   ├── epistemic_status
├── lifecycle_status              ├── authority_state
├── runtime_callable              ├── topology_integrity_score
├── authority_context ─────────── │── authority_state (mapped)
└── provenance_status ─────────── └── (attachment present → IBG_ATTACHED)
```

**Rationale:** DxfLifecycleContext is lightweight by design. IBG-specific fields belong in a domain-specific attachment that callers can inspect without polluting the core lifecycle type.

### Fail-Closed Posture Preserved

All 5 IBG paths remain `BLOCKED_PROVENANCE`:
- `body_contour_solver.py:777`
- `body_contour_solver.py:808`
- `arc_reconstructor.py:1116`
- `arc_reconstructor.py:1279`
- `arc_reconstructor.py:1303`

No code changes were made to these files. This sprint is documentation-only.

### Forbidden Actions (Until R1)

| Action | Why |
|--------|-----|
| Add lifecycle guards implying legitimacy | False confidence |
| Promote to LIFECYCLE_GOVERNED | Requires orchestrator |
| Treat rank_score as approval | Authority laundering |
| Remove BLOCKED_PROVENANCE | Violates fail-closed |

---

## R1 Session Agenda (For Governance Owner)

1. Ratify `CANONICAL_PROVENANCE_MODEL.md`
2. Ratify `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` authority tier
3. Approve `IBGProvenanceAttachment` schema
4. Finalize required fields (14 required, 3 optional)
5. Sign transition rules from lifecycle addendum

**Exit criteria:** Signed governance record; matrix blocking condition updated.

---

## R2 Implementation Preview

After R1 ratification, R2 will:

1. Wire IBG saves through minimal provenance wrapper
2. Add validation: save rejected without attachment
3. Add validation: save rejected without reviewed authority state
4. Reclassify matrix rows: `BLOCKED_PROVENANCE` → `COMPAT_ONLY`

R2 is blocked on R1. Do not begin R2 until R1 completes.

---

## Test Coverage

```bash
pytest tests/test_ibg_provenance_ratification_docs.py -v
```

Tests validate:
- All 5 required docs exist
- R0 marked complete in timeline
- All 5 blocked paths listed
- All 14 required fields documented
- No premature LIFECYCLE_GOVERNED claims
- Cross-references intact

---

## Related Documents

| Document | Role |
|----------|------|
| `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Source matrix (Section 3) |
| `CANONICAL_PROVENANCE_MODEL.md` | Provenance taxonomy |
| `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | IBG authority model |
| `CROSS_REPO_AUTHORITY_CROSSWALK.md` | tap_tone vocabulary mapping |
| `DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Phase 2 guard implementation |

---

## Memory Impact

Saved to persistent memory:
- `feedback_ibg_provenance_posture.md` — BLOCKED_PROVENANCE is intentional
- `feedback_governance_convergence_principles.md` — additive vocabulary only

---

## Next Actions

| Action | Owner | Blocked On |
|--------|-------|------------|
| Schedule R1 governance session | Platform/governance owner | — |
| Conduct R1 ratification | Governance stakeholders | Session scheduled |
| Begin R2 implementation | Developer | R1 complete |

---

*MRP-6C complete. R0 documentation convergence achieved. Awaiting R1 ratification session.*
