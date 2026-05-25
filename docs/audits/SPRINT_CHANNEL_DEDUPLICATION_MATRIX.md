# Sprint Channel Deduplication Matrix

**Date:** 2026-05-24  
**Purpose:** Prevent duplicate work across sprint channels  
**Scope:** luthiers-toolbox repository

---

## Active Branches

| Branch | PR | Status | Owner Channel |
|--------|-----|--------|---------------|
| `feat/confidence-envelope-interoperability` | #38 | Ready for review | Governance Normalization |
| `p0-repository-state-triage` | — | Pending decisions | Triage |
| `main` | — | Stable | — |

---

## COMPLETED WORK — Do Not Duplicate

### 1. Cross-Repo Governance Contracts (PR #38)

**Owner:** Governance Normalization 1A  
**Branch:** `feat/confidence-envelope-interoperability`  
**Status:** ✓ COMPLETE — Ready for merge

| Deliverable | File | Tests |
|-------------|------|-------|
| ConfidenceEnvelopeV1 | `governance/confidence_envelope.py` | 23 ✓ |
| ProvenanceAttachmentDraft | `governance/provenance_attachment.py` | 26 ✓ |
| AuthorityMetadata | `governance/authority_metadata.py` | 23 ✓ |
| Envelope spec doc | `CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md` | — |
| Metadata spec doc | `AUTHORITY_METADATA_NORMALIZATION.md` | — |
| IBG provenance spec | `IBG_PROVENANCE_ATTACHMENT_SPEC.md` | — |

**DO NOT:**
- Re-implement confidence envelope
- Re-implement provenance attachment draft
- Re-implement authority metadata
- Create duplicate spec docs

---

### 2. Constitutional Stabilization Import (Merged)

**Owner:** Governance Convergence (DO 77-83)  
**Status:** ✓ COMPLETE — Merged to main

| Deliverable | Location |
|-------------|----------|
| 9 constitutional files | `docs/handoffs/imports/constitutional_stabilization_do_77_82/` |
| Cross-repo authority crosswalk | `CROSS_REPO_AUTHORITY_CROSSWALK.md` |
| Multi-repo governance audit | `MULTI_REPOSITORY_GOVERNANCE_AUDIT_2026-05-24.md` |
| Epistemic status schema spec | `EPISTEMIC_STATUS_SCHEMA_SPEC.md` |
| Confidence migration test | `test_ibg_candidate_confidence_migration.py` |

**DO NOT:**
- Re-import constitutional docs from tap_tone
- Re-create authority crosswalk
- Re-audit multi-repo governance

---

### 3. CAM-Assist-Blueprint Integration (Merged)

**Owner:** CAM-Assist Sprint (A0-A12)  
**Status:** ✓ COMPLETE — 12 PRs merged

| Deliverable | Count |
|-------------|-------|
| Dev orders | 13 (A0-A12) |
| CLI scripts | 11 |
| JSON schemas | 3 |
| Tests | 236 passing |

**DO NOT:**
- Re-implement strategy packaging
- Re-create review packet generation
- Re-implement manifest validation

---

### 4. IBG Blocked Provenance Timeline (Merged)

**Owner:** Governance Convergence  
**Status:** ✓ COMPLETE — Documentation only

| Deliverable | Location |
|-------------|----------|
| Ratification timeline | `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |
| 5 blocked paths documented | In timeline doc |
| Phase R0-R3 defined | In timeline doc |

**DO NOT:**
- Re-document blocked paths
- Re-define ratification phases
- Attempt to unblock without R1 session

---

## PENDING WORK — Available for Assignment

### Priority 1: Requires Governance Decision

| Item | Blocker | Owner |
|------|---------|-------|
| IBG DXF export unblock (5 paths) | R1 ratification session | Governance |
| R1 provenance ratification | Governance session scheduling | Governance |

**No channel should attempt these without governance session.**

---

### Priority 2: Awaiting PR #38 Merge

| Item | Depends On | Suggested Owner |
|------|------------|-----------------|
| Package normalization to `contracts/` | PR #38 merge | Platform |
| Wire provenance to DXF export | PR #38 + R1 | IBG |
| Cross-repo CI normalization | PR #38 merge | Platform |

---

### Priority 3: Triage Branch Decisions

| Decision | ID | Impact |
|----------|-----|--------|
| Branch strategy | D1 | All implementation |
| Audit sources persistence | D2 | Audit PR |
| PR grouping | D4 | All PRs |

**Owner:** Triage channel on `p0-repository-state-triage`

---

### Priority 4: Documentation Only

| Item | Status | Suggested Owner |
|------|--------|-----------------|
| rank_score vs confidence_value disambiguation | Pending | Governance |
| Shared schema registry spec | Pending | Platform |
| Queue unification spec (8E ↔ CAM) | Pending | CAM/IBG |

---

## BLOCKED ITEMS — Do Not Attempt

| Item | Blocker | Unblock Condition |
|------|---------|-------------------|
| IBG DXF saves (5 paths) | BLOCKED_PROVENANCE | R1 ratification |
| tap_tone_pi push (27 commits) | Manual verification needed | Owner action at source |
| IBG memory population | Authority state | Human review + approval |
| DXF lifecycle promotion | Provenance wiring | R1 + implementation |
| Runtime federation | Out of scope | Future sprint |
| Confidence schema replacement | Design decision | Envelope is compatibility layer |

---

## Cross-Channel Coordination

### Shared Invariants (All Channels Must Respect)

```
execution_authorized = False        (always)
review_required = True              (always)
runtime_authoritative = False       (always, for envelopes)
IBG_DEFAULT_STATUS = BLOCKED        (until R1)
```

### Shared Enums (Do Not Redefine)

| Enum | Location | Owner |
|------|----------|-------|
| `ConfidenceType` | `confidence_declaration.py` | Existing |
| `AuthorityState` | `authority_state.py` | Existing |
| `EpistemicStatus` | `confidence_envelope.py` | Normalization 1A |
| `SemanticDomain` | `confidence_envelope.py` | Normalization 1A |
| `SourceSystem` | `confidence_envelope.py` | Normalization 1A |
| `ReviewState` | `authority_metadata.py` | Normalization 1A |
| `LifecycleState` | `authority_metadata.py` | Normalization 1A |
| `ProvenanceAttachmentStatus` | `provenance_attachment.py` | Normalization 1A |

---

## Test Coverage Summary

| Test Suite | Tests | Status | Owner |
|------------|-------|--------|-------|
| Confidence envelope | 23 | ✓ Passing | Normalization 1A |
| Provenance attachment | 26 | ✓ Passing | Normalization 1A |
| Authority metadata | 23 | ✓ Passing | Normalization 1A |
| Constitutional runtime | 37 | ✓ Passing | Governance Convergence |
| CAM-Assist | 236 | ✓ Passing | CAM Sprint |
| **Total new governance tests** | **72** | **✓ Passing** | — |

---

## File Ownership Matrix

### governance/ package

| File | Status | Owner | DO NOT Modify Without |
|------|--------|-------|----------------------|
| `confidence_envelope.py` | NEW | Normalization 1A | PR #38 review |
| `provenance_attachment.py` | NEW | Normalization 1A | PR #38 review |
| `authority_metadata.py` | NEW | Normalization 1A | PR #38 review |
| `confidence_declaration.py` | EXISTING | Foundation | Constitutional review |
| `authority_state.py` | EXISTING | Foundation | Constitutional review |
| `provenance_record.py` | EXISTING | Foundation | Constitutional review |
| `review_enforcement.py` | EXISTING | Foundation | Constitutional review |

### docs/governance/

| File | Status | Owner |
|------|--------|-------|
| `CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md` | NEW | Normalization 1A |
| `AUTHORITY_METADATA_NORMALIZATION.md` | NEW | Normalization 1A |
| `IBG_PROVENANCE_ATTACHMENT_SPEC.md` | NEW | Normalization 1A |
| `CROSS_REPO_AUTHORITY_CROSSWALK.md` | UPDATED | Governance Convergence |
| `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | EXISTING | Governance Convergence |

---

## Quick Reference: What Can I Work On?

| If you are... | You CAN work on | You CANNOT work on |
|---------------|-----------------|-------------------|
| Governance | R1 session scheduling, disambiguation docs | Unblocking IBG without session |
| Platform | CI normalization (post-merge), package restructure | Envelope reimplementation |
| IBG | Provenance wiring prep (post-R1) | DXF export unblocking |
| CAM | Queue unification spec | Strategy packaging (done) |
| Triage | D1-D4 decisions, branch cleanup | Implementation before decisions |
| Any | Documentation improvements | Replacing existing confidence models |

---

## Audit Document Cross-Reference

| Document | Scope | Current |
|----------|-------|---------|
| `RECONSTRUCTION_SPRINT_AUDIT_2026-05-24.md` | Multi-channel overview | Partially stale |
| `CROSS_REPO_GOVERNANCE_NORMALIZATION_1A_AUDIT.md` | Normalization sprint | Current |
| `RECONSTRUCTION_SPRINT_STATUS_2026-05-24.md` | Triage status | Pending decisions |
| **This document** | Deduplication matrix | **Current** |

---

*Matrix generated: 2026-05-24*  
*Update when: PR #38 merges, R1 scheduled, D1-D4 decided*
