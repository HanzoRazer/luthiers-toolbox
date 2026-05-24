# IBG BLOCKED_PROVENANCE — Ratification Timeline

**Date:** 2026-05-24  
**Status:** **BLOCKED** — export saves intentionally gated pending governance ratification  
**Authority:** Operational guidance (non-CI-blocking until ratified)  
**Cross-reference:** [`EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`](EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md), [`CANONICAL_PROVENANCE_MODEL.md`](CANONICAL_PROVENANCE_MODEL.md), [`IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md`](IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md), [`CROSS_REPO_AUTHORITY_CROSSWALK.md`](CROSS_REPO_AUTHORITY_CROSSWALK.md)

---

## Executive summary

Five IBG DXF save points in two files remain **`BLOCKED_PROVENANCE`**. They use `DxfWriter` (compat-governed) but **must not** receive Phase 2 lifecycle promotion until the IBG provenance attachment model is **ratified** and wired.

This is intentional fail-closed posture — not a bug.

---

## Blocked paths (verified on disk)

| File | Lines | Lifecycle class | Risk if unblocked prematurely |
|------|-------|-----------------|-------------------------------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 | `BLOCKED_PROVENANCE` | Ungoverned geometry export; authority laundering |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116, 1279, 1303 | `BLOCKED_PROVENANCE` | Same |

**Matrix reference:** Section 3 — IBG Blocked Provenance Candidates (`EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`).

---

## Blocking dependencies

| Prerequisite | Document / module | Status |
|--------------|-------------------|--------|
| Canonical provenance type taxonomy | `CANONICAL_PROVENANCE_MODEL.md` | **DRAFT FOR GOVERNANCE RATIFICATION** |
| IBG constitutional intake | `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` | **IMPLEMENTED — Pending Ratification** |
| `BodyEvidenceCandidate` provenance chain | `body_evidence_candidate.py` | Implemented; export boundary not wired |
| Epistemic posture for IBG outputs | tap_tone ADR-0012 (imported DO 81) | Constitutional in tap_tone; **mapping doc-only in luthiers** |
| Export lifecycle orchestrator adoption | Phase 2 plan | **Blocked** on rows above |

**Cross-repo epistemic default for IBG exports until ratified:**

```text
PREDICTED / HEURISTIC — not OBSERVED/DERIVED production authority
```

---

## Ratification phases (proposed)

### Phase R0 — Documentation convergence (complete / in progress)

- [x] Lifecycle matrix marks 5 calls `BLOCKED_PROVENANCE`
- [x] DXF guard plan documents disposition `blocked_provenance`
- [x] Cross-repo authority crosswalk maps epistemic posture
- [ ] Governance inventory entry for IBG provenance block (**P1**)

### Phase R1 — Governance ratification (target: next governance sprint)

1. Ratify `CANONICAL_PROVENANCE_MODEL.md` (or superseding Dev Order)
2. Ratify `IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md` authority tier
3. Publish IBG-specific provenance attachment spec:
   - Required fields at DXF save boundary
   - Mapping: `ProvenanceRecord` → `DxfLifecycleContext`
   - Epistemic status field (optional, aligned to ADR-0012)

**Exit criteria:** Signed governance record; matrix blocking condition updated from "awaiting ratification" to "implementation approved".

### Phase R2 — Minimal export wrapper (implementation)

1. Wire IBG saves through minimal provenance wrapper (per `RUNTIME_BOUNDARY_INVENTORY.md` Phase 2)
2. Unit tests: save rejected without provenance; save allowed with ratified context
3. Reclassify matrix rows from `BLOCKED_PROVENANCE` → `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`

**Exit criteria:** 5 paths green in lifecycle validator; no `BLOCKED` risk level.

### Phase R3 — Commercial posture (optional, gated)

- Align IBG review package visibility with Wave 1C artifact quality docs
- Cross-repo review routing spec (luthiers 8E ↔ IBG packages)

---

## What must NOT happen before R1

| Action | Why forbidden |
|--------|---------------|
| Add lifecycle guards that imply production legitimacy | False confidence in export governance story |
| Promote IBG DXF to `LIFECYCLE_GOVERNED` without provenance | Violates fail-closed matrix |
| Treat `rank_score` as approval for export | Authority laundering (ADR-0012 HEURISTIC) |
| Merge vectorizer-sandbox outputs into spine defaults | `R_AND_D_EXCLUDED` separation |

---

## Escalation triggers (from tap_tone DO 82)

Re-open constitutional review if:

- Authority semantics ambiguity at IBG export boundary
- Epistemic status conflicts between IBG candidates and CAM exports
- Operator sovereignty bypass via automated rank → export
- Provenance chain gaps discovered in production paths

---

## Owner & next action

| Item | Recommendation |
|------|----------------|
| **Owner** | luthiers-toolbox platform / governance (unassigned) |
| **Immediate** | Schedule R1 ratification session for provenance model + IBG foundation |
| **Track** | Update `MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` when R1 completes |

---

*Timeline version: 2026-05-24*  
*Next update: R1 ratification or first IBG export wrapper PR*
