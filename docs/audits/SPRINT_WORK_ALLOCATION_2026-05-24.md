# Sprint Work Allocation — 2026-05-24

**Purpose:** Consolidate completed work across channels to prevent duplication  
**Sources:** 3 audit documents evaluated

---

## Completed Work (DO NOT DUPLICATE)

### Constitutional Import & Semantic Cleanup

| Item | Channel | Status |
|------|---------|--------|
| Constitutional import (9 files DO 77–82) | Governance Convergence | ✓ Complete |
| Em-dash path cleanup | Governance Convergence | ✓ Complete |
| Cross-repo governance audit (16+ docs) | Governance Convergence | ✓ Complete |
| Confidence vocabulary migration (`candidate_rank`) | Governance Convergence | ✓ Complete |
| Epistemic status schema spec | Governance Convergence | ✓ Complete |
| Constitutional runtime tests (37/37) | Governance Convergence | ✓ Pass |

### Cross-Repo Convergence Contracts (PR #38)

| Item | Channel | Status |
|------|---------|--------|
| `ConfidenceEnvelopeV1` | Normalization 1A | ✓ Complete |
| `ProvenanceAttachmentDraft` | Normalization 1A | ✓ Complete |
| `AuthorityMetadata` | Normalization 1A | ✓ Complete |
| Governance tests (72) | Normalization 1A | ✓ Pass |
| Compatibility docs (3) | Normalization 1A | ✓ Complete |

### CAM-Assist-Blueprint

| Item | Channel | Status |
|------|---------|--------|
| 13 dev orders (A0–A12) | CAM-Assist | ✓ Complete |
| 11 CLI scripts | CAM-Assist | ✓ Complete |
| 3 JSON schemas | CAM-Assist | ✓ Complete |
| Authority model enforcement | CAM-Assist | ✓ Complete |
| Tests (236) | CAM-Assist | ✓ Pass |

### Repository Triage

| Item | Channel | Status |
|------|---------|--------|
| Deep audit | P0 Triage | ✓ Complete |
| P0 triage report | P0 Triage | ✓ Complete |
| Authority crosswalk (updated) | P0 Triage | ✓ Complete |
| File classification (70+ → 10 PR groups) | P0 Triage | ✓ Complete |

---

## Shared Blockers (ALL CHANNELS BLOCKED)

| Blocker | Affects | Resolution |
|---------|---------|------------|
| IBG BLOCKED_PROVENANCE (5 paths) | IBG exports, lifecycle promotion | R1 ratification session |
| tap_tone_pi push (27 commits) | Cross-repo verification | Manual push at source |
| Pending decisions D1/D2/D4 | Implementation commits, PRs | Await decisions |

---

## DO NOT START (Blocked or Complete)

| Item | Reason |
|------|--------|
| IBG export unblocking | Blocked on R1 |
| DXF lifecycle promotion | Blocked on IBG |
| Confidence schema replacement | Complete (envelope is compatibility layer) |
| Constitutional import | Complete |
| Authority crosswalk | Complete |
| Epistemic status spec | Complete |

---

## Available Work (NOT YET CLAIMED)

| Item | Priority | Notes |
|------|----------|-------|
| Merge PR #38 | P1 | Normalization 1A ready for review |
| Package normalization to `contracts/` | P2 | Noted in 1A audit |
| Cross-repo CI normalization | P3 | Out of scope for current sprints |
| R1 ratification session scheduling | P1 | Governance owner action |

---

## Overlapping Work Detected

| Item | Channels | Resolution |
|------|----------|------------|
| Authority crosswalk | Governance Convergence + P0 Triage | Both updated same doc — verify no conflicts |
| IBG provenance timeline | Governance Convergence + P0 Triage | Both updated same doc — verify no conflicts |
| Confidence semantics | Governance Convergence + Normalization 1A | Complementary: `candidate_rank` (migration) + `ConfidenceEnvelopeV1` (wrapper) |

---

## Channel Summary

| Channel | Sprint | Status | Key Deliverable |
|---------|--------|--------|-----------------|
| Governance Convergence | DO 77–83 | Complete | Constitutional import + semantic migration |
| Normalization 1A | PR #38 | Ready for review | ConfidenceEnvelopeV1 + contracts |
| CAM-Assist-Blueprint | CAM-A0–A12 | Complete | Strategy packaging pipeline |
| P0 Triage | p0-repository-state-triage | Awaiting decisions | File classification + triage report |

---

## Next Actions by Priority

| Priority | Action | Owner | Blocked By |
|----------|--------|-------|------------|
| P0 | Resolve D1/D2/D4 decisions | User | — |
| P1 | Review/merge PR #38 | Reviewer | — |
| P1 | Schedule R1 ratification | Governance | — |
| P1 | Push tap_tone_pi 27 commits | tap_tone owner | Manual verification |
| P2 | Package normalization | Platform | PR #38 merge |
| P3 | Cross-repo CI | Platform | Multiple |

---

*Generated: 2026-05-24*  
*Sources: RECONSTRUCTION_SPRINT_AUDIT, CROSS_REPO_GOVERNANCE_NORMALIZATION_1A_AUDIT, RECONSTRUCTION_SPRINT_STATUS*
