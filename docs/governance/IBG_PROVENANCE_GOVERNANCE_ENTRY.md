# IBG Provenance Governance Entry

**Status:** ACTIVE_BLOCKER  
**Classification:** RATIFICATION_PENDING  
**Sprint:** MRP-6C  
**Date:** 2026-05-24

---

## Purpose

This document registers the IBG provenance block in the governance inventory. It serves as an index pointer to the full ratification materials.

---

## Blocker Summary

| Attribute | Value |
|-----------|-------|
| Blocker ID | IBG-PROV-001 |
| Blocked Paths | 5 DXF save points |
| Current Status | BLOCKED_PROVENANCE |
| Runtime Effect | Blocks export lifecycle promotion |
| Ratification Phase | R0 complete, R1 pending |

---

## Blocked Save Points

| File | Lines |
|------|-------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116, 1279, 1303 |

---

## Authority Declaration

```yaml
authority: governance/ratification_pending
ci_blocking: false (documentation only until R2)
runtime_effect: blocks export promotion
status: active_blocker
classification: provenance_governance
```

---

## Related Documents

| Document | Role |
|----------|------|
| [IBG_PROVENANCE_RATIFICATION_PACKET.md](IBG_PROVENANCE_RATIFICATION_PACKET.md) | R1 ratification material |
| [IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md](IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md) | Required fields |
| [IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md](IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md) | Transition rules |
| [IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md](IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md) | Chronology |
| [EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md](EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md) | Matrix source |
| [CROSS_REPO_AUTHORITY_CROSSWALK.md](CROSS_REPO_AUTHORITY_CROSSWALK.md) | Epistemic alignment |
| [CANONICAL_PROVENANCE_MODEL.md](CANONICAL_PROVENANCE_MODEL.md) | Provenance taxonomy |
| [IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md](IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md) | IBG runtime foundation |

---

## Ratification Phases

| Phase | Status | Description |
|-------|--------|-------------|
| R0 | **Complete** | Documentation convergence |
| R1 | **Pending** | Governance ratification |
| R2 | Blocked on R1 | Minimal export wrapper |
| R3 | Blocked on R2 | Commercial posture (optional) |

---

## What This Blocker Prevents

Until R1 completes:
- No IBG DXF export lifecycle promotion
- No lifecycle guards implying production legitimacy
- No rank_score treated as approval
- No silent authority elevation

---

## What Must Happen for Unblock

1. R1 governance session completes
2. IBGProvenanceAttachment schema ratified
3. Required fields finalized
4. Transition rules signed
5. R2 implementation completes
6. Matrix rows reclassified via governance PR

---

## Inventory Metadata

```json
{
  "blocker_id": "IBG-PROV-001",
  "status": "active_blocker",
  "classification": "provenance_governance",
  "blocked_paths": 5,
  "ratification_phase": "R1_pending",
  "sprint": "MRP-6C",
  "ci_blocking": false,
  "runtime_effect": "blocks_export_promotion"
}
```

---

*IBG Provenance Governance Entry — MRP-6C — 2026-05-24*
