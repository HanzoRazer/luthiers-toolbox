# Cross-Channel Work Deduplication Matrix

**Date:** 2026-05-24  
**Purpose:** Prevent duplicate work across sprint channels  
**Sources:** 3 audit documents consolidated

---

## 1. Completed Work — Do Not Duplicate

### CAM-Assist-Blueprint

| Item | Channel | Evidence |
|------|---------|----------|
| Strategy validation CLI | CAM-A2 | `validate_strategy_package.py` |
| Review packet generator | CAM-A3 | `generate_review_packet.py` |
| Package assembly | CAM-A5 | `assemble_strategy_package.py` |
| Package inspection | CAM-A6 | `inspect_strategy_package.py` |
| Package indexing | CAM-A7 | `index_strategy_packages.py` |
| Archive creation | CAM-A8 | `archive_strategy_package.py` |
| Archive validation | CAM-A9 | `validate_package_archive.py` |
| Import staging | CAM-A10 | `stage_strategy_package.py` |
| Review queue generation | CAM-A11 | `index_staged_packages.py` |
| Review decision recording | CAM-A12 | `record_review_decision.py` |
| Strategy schema | CAM-A1 | `strategy.schema.json` |
| Manifest schema | CAM-A4 | `strategy_package_manifest.schema.json` |
| Decision schema | CAM-A12 | `review_decision_record.schema.json` |

**Status:** All 13 dev orders merged to main (`86a76d7`)

---

### luthiers-toolbox — Governance Convergence

| Item | Channel | Evidence |
|------|---------|----------|
| Constitutional import (9 files) | DO 77-82 | `docs/handoffs/imports/constitutional_stabilization_do_77_82/` |
| Path cleanup (em-dash → ASCII) | DO 77-82 | Folder renamed |
| Cross-repo governance audit | DO 77-82 | `MULTI_REPOSITORY_GOVERNANCE_AUDIT_2026-05-24.md` |
| Confidence vocabulary migration | DO 77-82 | `candidate_rank` parameter added |
| Epistemic status schema spec | DO 77-82 | `EPISTEMIC_STATUS_SCHEMA_SPEC.md` |
| Governance checks (9/13) | DO 77-82 | CI passing |
| Constitutional runtime tests (37/37) | DO 77-82 | pytest passing |

**Status:** Complete

---

### luthiers-toolbox — Normalization 1A

| Item | Channel | Evidence |
|------|---------|----------|
| ConfidenceEnvelopeV1 | 1A | `governance/confidence_envelope.py` |
| ProvenanceAttachmentDraft | 1A | `governance/provenance_attachment.py` |
| AuthorityMetadata | 1A | `governance/authority_metadata.py` |
| Factory methods (4 source systems) | 1A | Implemented |
| Convergence tests (72) | 1A | All passing |
| Envelope docs | 1A | `CROSS_REPO_CONFIDENCE_ENVELOPE_V1.md` |
| Metadata docs | 1A | `AUTHORITY_METADATA_NORMALIZATION.md` |
| Provenance spec | 1A | `IBG_PROVENANCE_ATTACHMENT_SPEC.md` |

**Status:** PR #38 ready for review

---

### luthiers-toolbox — P0 Triage

| Item | Channel | Evidence |
|------|---------|----------|
| Deep audit | P0 Triage | `SPRINT_CONVERGENCE_DEEP_AUDIT_2026-05-24.md` |
| P0 triage report | P0 Triage | `P0_REPOSITORY_STATE_TRIAGE_REPORT.md` |
| Authority crosswalk update | P0 Triage | `CROSS_REPO_AUTHORITY_CROSSWALK.md` |
| IBG timeline | P0 Triage | `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |
| File classification (70+ files → 10 PR groups) | P0 Triage | Documented |

**Status:** Complete — awaiting decisions D1, D2, D4

---

### tap_tone_pi

| Item | Channel | Evidence |
|------|---------|----------|
| ADR-0010 guidance authority | DO 78 | `docs/ADR-0010-guidance-authority-boundary.md` |
| ADR-0011 measurement authority | DO 81A | `docs/ADR-0011-measurement-authority.md` |
| ADR-0012 epistemic taxonomy | DO 81B | `docs/ADR-0012-epistemic-status-taxonomy.md` |
| AGE constitutional contract | DO 78 | `docs/AGE_CONSTITUTIONAL_CONTRACT.md` |
| Epistemic status matrix | DO 81C | `docs/EPISTEMIC_STATUS_MATRIX.md` |
| Constitutional tests | DO 81D | Tests passing |
| 27 commits pushed | Stabilization | `main` synced with `origin/main` |

**Status:** Complete

---

## 2. Blocked Work — Do Not Attempt

| Item | Blocker | Owner | Unblock Condition |
|------|---------|-------|-------------------|
| IBG DXF export (5 paths) | R1 ratification | Governance | Synchronous governance session |
| IBG lifecycle promotion | R1 ratification | Governance | Provenance model ratified |
| Implementation commits | D1 decision | P0 Triage | Branch strategy decided |
| Audit sources persistence | D2 decision | P0 Triage | Decision made |
| PR grouping | D4 decision | P0 Triage | Decision made |

**Rule:** These items cannot proceed until blockers resolve. Do not attempt workarounds.

---

## 3. Pending Work — Available for Assignment

| Item | Priority | Dependencies | Notes |
|------|----------|--------------|-------|
| Merge PR #38 | P1 | Review | Normalization 1A deliverables |
| Schedule R1 ratification session | P1 | Governance owner | IBG provenance |
| Package normalization to `contracts/` | P2 | PR #38 merged | Restructure governance models |
| Wire provenance to DXF export | P2 | R1 complete | Post-ratification |
| Cross-repo CI normalization | P3 | None | Platform work |
| `rank_score` vs `confidence_value` doc | P1 | None | Documentation only |
| Draft IBG provenance spec | P1 | None | R1 input |

---

## 4. Explicitly Deferred — Do Not Start

| Item | Reason | Defer Until |
|------|--------|-------------|
| Shared schema registry | Docs-first approach | Integration proves mapping |
| Shared authority enum | Crosswalk sufficient | Runtime integration needed |
| Queue unification | Intentionally separate layers | Adapter pattern later |
| Runtime federation | Out of scope | Post-R1 |
| G-code generation | Out of scope | Never (CAM-Assist) |
| Cross-repo CI integration | P3 priority | After P1/P2 complete |

---

## 5. Ownership Summary

| Channel | Repo | Status | Next Action |
|---------|------|--------|-------------|
| CAM-A0–A12 | CAM-Assist-Blueprint | **COMPLETE** | None |
| DO 77–82 | tap_tone_pi | **COMPLETE** | None |
| Governance Convergence | luthiers-toolbox | **COMPLETE** | None |
| Normalization 1A | luthiers-toolbox | **PR READY** | Merge PR #38 |
| P0 Triage | luthiers-toolbox | **BLOCKED** | Await D1/D2/D4 |
| IBG Provenance | luthiers-toolbox | **BLOCKED** | Schedule R1 |

---

## 6. Collision Risks

| Risk | Channels Affected | Mitigation |
|------|-------------------|------------|
| Authority crosswalk edits | All | Single source: `luthiers-toolbox/docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` |
| Confidence envelope modifications | Normalization 1A, IBG | Only 1A owns envelope; IBG consumes via factory |
| Epistemic status schema | tap_tone, luthiers | tap_tone ADR-0012 is canonical; luthiers imports |
| Review queue changes | CAM-Assist, luthiers 8E | Separate systems; crosswalk documents mapping |
| IBG save points | Normalization 1A, IBG | R1 ratification required; no unilateral changes |

---

## 7. Quick Reference

### Complete — No Action Needed

```
CAM-Assist-Blueprint: A0-A12 (13 dev orders, 236 tests)
tap_tone_pi: DO 77-82 (ADRs 0010-0012, constitutional contract)
luthiers-toolbox: Governance Convergence (9 imports, vocabulary migration)
luthiers-toolbox: Normalization 1A (3 models, 72 tests) — PR #38 pending
luthiers-toolbox: P0 Triage (audit, classification) — decisions pending
```

### Blocked — Cannot Proceed

```
IBG DXF export → R1 ratification
Implementation commits → D1 decision
```

### Available — Can Start

```
Merge PR #38
Schedule R1 session
rank_score documentation
IBG provenance spec draft
```

---

*Generated: 2026-05-24*  
*Purpose: Cross-channel deduplication*
