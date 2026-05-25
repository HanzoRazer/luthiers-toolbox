# Sprint Completion Matrix — 2026-05-24

**Purpose:** Cross-channel coordination to prevent duplicate work  
**Source Documents:**
- `RECONSTRUCTION_SPRINT_AUDIT_2026-05-24.md`
- `CROSS_REPO_GOVERNANCE_NORMALIZATION_1A_AUDIT.md`
- `RECONSTRUCTION_SPRINT_STATUS_2026-05-24.md`
- `RECONSTRUCTION_SPRINT_STATE_AUDIT_2026-05-24.md`

---

## COMPLETE — Do Not Duplicate

### Governance Infrastructure

| Item | Deliverable | Channel |
|------|-------------|---------|
| Constitutional import (DO 77-82) | 9 files in `handoffs/imports/` | Governance Convergence |
| Cross-repo governance audit | 16+ docs audited | Governance Convergence |
| Confidence vocabulary migration | `candidate_rank` parameter | Governance Convergence |
| Epistemic status schema | `EPISTEMIC_STATUS_SCHEMA_SPEC.md` | Governance Convergence |
| Authority crosswalk | `CROSS_REPO_AUTHORITY_CROSSWALK.md` | luthiers-toolbox |
| IBG timeline | `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | luthiers-toolbox |
| File classification | 70+ files → 10 PR groups | P0 Triage |
| Constitutional path verification | Verified correct | P0 Triage |

### Cross-Repo Normalization (PR #38)

| Item | Deliverable | Tests |
|------|-------------|-------|
| ConfidenceEnvelopeV1 | `governance/confidence_envelope.py` | 23 |
| ProvenanceAttachmentDraft | `governance/provenance_attachment.py` | 26 |
| AuthorityMetadata | `governance/authority_metadata.py` | 23 |
| Envelope spec | `CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md` | — |
| Metadata spec | `AUTHORITY_METADATA_NORMALIZATION.md` | — |
| Module exports | `governance/__init__.py` updated | — |

### IBG Provenance Ratification Prep (MRP-6C)

| Item | Deliverable | Tests |
|------|-------------|-------|
| Ratification packet | `IBG_PROVENANCE_RATIFICATION_PACKET.md` | — |
| Field matrix | `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` | — |
| Lifecycle addendum | `IBG_DXF_LIFECYCLE_MAPPING_ADDENDUM.md` | — |
| Governance entry | `IBG_PROVENANCE_GOVERNANCE_ENTRY.md` | — |
| Doc validation tests | `test_ibg_provenance_ratification_docs.py` | 16 |

### Runtime Spine (MRP-5M through 6A)

| Item | Deliverable | PRs |
|------|-------------|-----|
| Runtime admission control | MRP-5M | #31-37 |
| Provenance replay | MRP-5N | merged |
| Deterministic replay | MRP-5O | merged |
| Spine integration | MRP-5P, 5QR | merged |
| Service consolidation | MRP-5S | merged |
| Contract freeze | MRP-5T | merged |
| Capability federation | MRP-5V | merged |
| Release verification | MRP-5X | merged |
| Post-merge verification | MRP-6A | merged |

### DXF Lifecycle Guards (Phase 2)

| Item | Deliverable | Commit |
|------|-------------|--------|
| Guard implementation | Phase 2A | 2228a96e |
| Status tracking | Phase 2B | bc075e79 |
| Neck router guards | Phase 2C | 16587231 |
| Remaining router guards | Phase 2D | 18779212 |
| Runtime service guards | Phase 2F | b4c91a84 |
| DxfWriter assessment | Phase 2G | 07cc00fa |

### CAM Track

| Item | Deliverable | Status |
|------|-------------|--------|
| CAM-A0 through A12 | 13 dev orders | Complete |
| 11 CLI scripts | strategy package tooling | Delivered |
| 3 JSON schemas | strategy, manifest, review | Delivered |
| Federation CI | CAM-7Y | Complete |
| Baseline freeze | CAM-7Z | Complete |
| Expansion gate | CAM-8A | Complete |
| Review UX | CAM-8C, 8D | Complete |
| Queue routing | CAM-8E | Complete |
| Operational readiness | CAM-8F | Complete |

---

## BLOCKED — Cannot Proceed

| Item | Blocker | Owner |
|------|---------|-------|
| IBG DXF export (5 paths) | R1 governance ratification | Governance |
| R2 IBG export wrapper | R1 completion | Developer |
| IBG → CAM integration | R2 implementation | Developer |
| tap_tone_pi push (27 commits) | Manual verification at source | Platform |
| Implementation commits | D1 branch strategy decision | Developer |

### IBG Blocked Paths (Verified)

```
body_contour_solver.py:777   BLOCKED_PROVENANCE
body_contour_solver.py:808   BLOCKED_PROVENANCE
arc_reconstructor.py:1116    BLOCKED_PROVENANCE
arc_reconstructor.py:1279    BLOCKED_PROVENANCE
arc_reconstructor.py:1303    BLOCKED_PROVENANCE
```

**Do NOT attempt to:**
- Add lifecycle guards implying legitimacy
- Promote to LIFECYCLE_GOVERNED
- Treat rank_score as export approval
- Remove BLOCKED_PROVENANCE classification

---

## PENDING DECISIONS — Awaiting Input

| ID | Decision | Impact |
|----|----------|--------|
| D1 | Branch strategy | Blocks all implementation commits |
| D2 | Audit sources persistence | Blocks audit PR |
| D4 | PR grouping | Blocks all PRs |

**Channels should not proceed with implementation until D1-D4 are resolved.**

---

## NOT DONE — Available for Work

### High Priority (P1)

| Item | Description | Depends On |
|------|-------------|------------|
| R1 governance session | Ratify IBG provenance model | Schedule only |
| Canonical provenance ratification | Ratify CANONICAL_PROVENANCE_MODEL.md | R1 session |
| IBG constitutional authority tier | Ratify authority semantics | R1 session |
| PR #38 review | Cross-repo normalization | Reviewer |

### Medium Priority (P2)

| Item | Description | Depends On |
|------|-------------|------------|
| Package normalization | Move to `contracts/` | PR #38 merge |
| rank_score vs confidence_value doc | Clarification document | — |
| Cross-repo CI normalization | Shared CI checks | Platform capacity |

### Low Priority (P3) / Out of Scope

| Item | Reason |
|------|--------|
| Shared schema registry | Deferred — additive convergence only |
| Shared authority enum | Deferred — each repo owns vocabulary |
| Queue unification (8E + CAM-A) | Deferred — intentionally separate |
| luthiers-toolbox API integration with CAM-A | Blocked on R2 |
| G-code generation | Explicitly out of scope |
| Runtime federation | Out of scope |
| Confidence schema replacement | Compatibility layer only |
| Automatic governance routing | Out of scope |
| vectorizer-sandbox modifications | Separate repo |
| Broad epistemic_status rollout | Blocked on R1 |
| DXF lifecycle promotion | Blocked on R2 |

---

## Cross-Channel Dependencies

```
                    ┌─────────────────┐
                    │  R1 Governance  │
                    │    Session      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────┐ ┌───────────────┐
    │ IBG Provenance  │ │ Vocab   │ │ Constitutional │
    │ Ratification    │ │ Rollout │ │ Authority      │
    └────────┬────────┘ └─────────┘ └───────────────┘
             │
             ▼
    ┌─────────────────┐
    │ R2 Export       │
    │ Wrapper         │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ IBG → CAM       │
    │ Integration     │
    └─────────────────┘
```

---

## Channel Assignment Recommendation

| Channel | Should Work On | Should NOT Work On |
|---------|----------------|-------------------|
| Governance | Schedule R1 session | Implementation |
| luthiers-toolbox | PR #38 merge, docs | IBG unblocking |
| CAM | 8F+ (if any) | IBG integration |
| tap_tone_pi | Local verification | luthiers push |
| vectorizer-sandbox | Research only | Production code |

---

## Verification Commands

```bash
# Governance tests
pytest tests/governance -v  # 72 tests

# IBG ratification doc tests
pytest tests/test_ibg_provenance_ratification_docs.py -v  # 16 tests

# Constitutional runtime tests
pytest tests/test_governance_constitutional_runtime.py -v  # 37 tests

# Full governance check
python scripts/governance/check_all.py --tier ci
```

---

*Sprint Completion Matrix — 2026-05-24*
