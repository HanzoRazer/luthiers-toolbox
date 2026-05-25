# Multi-Repository Governance Audit

**Date:** 2026-05-24  
**Scope:** luthiers-toolbox, tap_tone_pi, CAM-Assist-Blueprint  
**Documents Reviewed:** 16+ governance documents  
**Coverage:** 95%+  

---

## Executive Summary

Three repositories independently converged on identical constitutional principles:
- **Human authority** / operator sovereignty is supreme
- **Non-execution declarations** — no system authorizes machine action
- **Fail-closed validation** — unclear states block, not proceed

This convergence represents constitutional alignment achieved through parallel evolution, not coordinated design. The audit validates this alignment while identifying integration gaps requiring explicit Dev Orders before cross-repo data flows.

### Key Finding

The ecosystem has established a mature constitutional governance framework. The primary risk is not missing governance, but **integration without explicit semantic mapping** — different vocabularies describing the same constitutional intent.

---

## 1. Constitutional Alignment Assessment

### 1.1 Core Principles (Verified Aligned)

| Principle | tap_tone_pi | luthiers-toolbox | CAM-Assist |
|-----------|-------------|------------------|------------|
| Operator sovereignty | ADR-0010 §4 | 8E invariants | A12 human records |
| Non-execution | Forbidden in exports | `execution_authorized=False` | `execution_authority_claim=false` |
| Human review required | Export boundary | `human_review_required=True` | `requires_human_review=true` |
| Fail-closed | CI guards block | BLOCKED_PROVENANCE gates | Schema const enforcement |

**Assessment:** ALIGNED INTENT — implementation vocabulary differs, but constitutional semantics match.

### 1.2 Authority Domain Model

tap_tone_pi ADR-0010 established four orthogonal authority domains:

| Domain | Definition | Cross-Repo Mapping |
|--------|------------|-------------------|
| **Measurement** | Captured observational records | luthiers: LIFECYCLE_GOVERNED DXF paths |
| **Advisory** | Prioritizes operator attention | luthiers: Review routing, rank signals |
| **Interpretive** | Frames semantic context | luthiers: IBG morphology interpretation |
| **Operator** | Final human judgment | luthiers: ReviewDecisionRecord |

**Assessment:** tap_tone domain model is constitutional; luthiers implements analogues without explicit mapping. Integration requires Dev Order to wire explicit domain declarations.

### 1.3 Epistemic Status Taxonomy

ADR-0012 defines seven epistemic states:

| Status | Authority Level | luthiers Analogue |
|--------|-----------------|-------------------|
| OBSERVED | Measurement-authoritative | LIFECYCLE_GOVERNED exports |
| DERIVED | Computationally authoritative | COMPAT_ONLY paths |
| ESTIMATED | Approximation only | — |
| PREDICTED | Model-dependent | IBG candidates (pre-ratification) |
| HEURISTIC | No authority | rank_score, advisory panels |
| OPERATOR-ANNOTATED | Operator authority | ReviewDecisionRecord |
| EXTERNALLY-SOURCED | External authority | Imported DXF/blueprint paths |

**Assessment:** Taxonomy is constitutional in tap_tone; luthiers has functional analogues. IBG outputs default to PREDICTED/HEURISTIC until provenance ratification.

---

## 2. Governance Complementarity

### 2.1 Structural vs Lexical Governance

| Repository | Governance Type | Enforcement Mechanism |
|------------|-----------------|----------------------|
| tap_tone_pi | **Structural** | CI guards, INSTRUMENT CLASS headers |
| luthiers-toolbox | **Lexical** | Forbidden vocabulary, lifecycle classification |
| CAM-Assist | **Schema** | JSON Schema const enforcement |

**Insight (DO 77):** Combined structural + lexical governance is intentional complementarity — not duplication to merge blindly.

### 2.2 CI Enforcement Matrix

| Repository | Pre-commit | CI | Nightly |
|------------|------------|-----|---------|
| tap_tone_pi | check_advisory_boundary.py | check_boundary_imports.py | — |
| luthiers-toolbox | check_protected_paths.py | check_all.py | Full governance suite |
| CAM-Assist | pytest | Schema validation | — |

**Assessment:** tap_tone has mature CI enforcement. luthiers has comprehensive tiered system. Integration CI coverage is a gap.

---

## 3. Review Queue Semantic Mapping

### 3.1 Parallel Systems (Not Drop-In Replacements)

| Property | luthiers 8E | CAM A11/A12 | IBG Workflow 1A |
|----------|-------------|-------------|-----------------|
| **Purpose** | Route human attention | Index staged packages | Emit ranked candidates |
| **ID format** | `rqi-{uuid12}` | Package directory + hash | Workflow/candidate IDs |
| **Storage** | In-memory (ephemeral) | Filesystem | Workflow artifacts |
| **Authorizes execution?** | **No** | **No** | **No** |

### 3.2 Decision Type Mapping

| luthiers DecisionType | CAM A12 Analogue | Notes |
|-----------------------|------------------|-------|
| `acknowledge` | — | Operator opens review |
| `defer` | Staged package remains queued | |
| `reject` | Reject decision record | |
| `mark_reviewed` | `approve_for_downstream_cam` | Schema verified on A12 branch |

### 3.3 Non-Authorization (Shared)

All three systems explicitly do NOT authorize:
- Machine execution
- Auto-approval
- Implementation without human review
- G-code generation
- Downstream CAM without human decision

---

## 4. IBG Blocked Provenance Status

### 4.1 Blocked Paths (5 Total)

| File | Lines | Status |
|------|-------|--------|
| `body_contour_solver.py` | 777, 808 | BLOCKED_PROVENANCE |
| `arc_reconstructor.py` | 1116, 1279, 1303 | BLOCKED_PROVENANCE |

### 4.2 Blocking Dependencies

| Prerequisite | Status |
|--------------|--------|
| Canonical provenance model ratification | DRAFT |
| IBG constitutional foundation ratification | IMPLEMENTED — Pending |
| BodyEvidenceCandidate provenance chain | Implemented; boundary not wired |
| Epistemic posture mapping | Documentation-only |

### 4.3 Ratification Timeline

| Phase | Target |
|-------|--------|
| R0 — Documentation convergence | Complete |
| R1 — Governance ratification | Next governance sprint |
| R2 — Minimal export wrapper | Post-R1 |
| R3 — Commercial posture | Gated |

**Assessment:** IBG blocking is intentional fail-closed posture. Unblocking requires explicit governance ratification, not implementation work.

---

## 5. Confidence Vocabulary Collision Risk

### 5.1 Cross-Repo Confidence Types

| Field | Repository | Authoritative? |
|-------|------------|----------------|
| TypedConfidenceV1 | tap_tone_pi | **No** — for DECISION_SUPPORT |
| ConfidenceDeclaration | luthiers | **No** — `implies_correctness()` always False |
| rank_score | luthiers IBG | **No** — sort key only |
| confidence_value | luthiers | **No** — but label says "confidence" |

### 5.2 Collision: confidence_value vs rank_score

`confidence_value` on IBG candidates is copied from `rank_score` in the pipeline. This creates semantic confusion — the label "confidence" implies truth-likeness, but the value is a sort key.

**Recommendation:** Rename to `candidate_rank` or add explicit `_is_heuristic: true` marker.

### 5.3 Constitutional Non-Implications (All Repos Agree)

```
High score / confidence does NOT imply:
  - correctness
  - approval
  - execution authority
  - review bypass
  - canonical / production readiness
```

---

## 6. Authority Laundering Prevention

### 6.1 The Laundering Chain (ADR-0011)

```
Measurement Confidence
        ↓
Advisory Interpretation      ← Status change required
        ↓
Historical Weighting         ← Repetition ≠ elevation
        ↓
Operator Trust               ← Human judgment only
        ↓
Emergent Canonization        ← CONSTITUTIONAL VIOLATION
```

### 6.2 Constitutional Interruption Points

| Transition | Gate |
|------------|------|
| Measurement → Advisory | Status must change to HEURISTIC/DERIVED |
| Advisory → Historical | Repetition does not elevate status |
| Historical → Trust | Operator judgment is OPERATOR-ANNOTATED |
| Trust → Canonical | **FORBIDDEN** — no system path creates canonical authority |

### 6.3 Cross-Repo Status

| Repository | Authority Laundering Prevention |
|------------|--------------------------------|
| tap_tone_pi | ADR-0011 constitutional doctrine |
| luthiers-toolbox | ConfidenceDeclaration non-implications |
| CAM-Assist | Authority block const enforcement |

**Assessment:** All three repos have laundering prevention. tap_tone has the most explicit constitutional doctrine.

---

## 7. Presentation Authority Leakage

### 7.1 Risk Categories

| Risk | Example | Consequence |
|------|---------|-------------|
| Visual validation | Green checkmarks on advisory | User reads as validated |
| Confidence conflation | "85% confidence" bare | User reads as "85% correct" |
| Grade authority | "Quality Grade: A" | User reads as calibrated measurement |
| Approval semantics | "PASSED" badges | User reads advisory as test result |

### 7.2 Remediation Status

tap_tone_pi Dev Order 80 applied four patches:
- `html_report.py:353` — Quality Grade (heuristic)
- `html_report.py:426` — Quality Grade (heuristic)
- `html_report.py:430` — Advisory Confidence
- `engine.py:168` — Advisory confidence

**Assessment:** tap_tone presentation boundary is remediated. luthiers requires equivalent audit when UI surfaces advisory outputs.

---

## 8. Immediate Convergence Actions

### Priority 0 (Blocking)

| Action | Owner |
|--------|-------|
| Push tap_tone 27 commits to origin | tap_tone_pi |
| Rename constitutional import path (em-dash in folder name) | luthiers-toolbox |

### Priority 1 (High)

| Action | Owner |
|--------|-------|
| Add epistemic_status optional field to review artifacts | luthiers-toolbox |
| Schedule R1 ratification session for provenance model | luthiers-toolbox |
| Merge CAM A12 schema to main | CAM-Assist-Blueprint |

### Priority 2 (Medium)

| Action | Owner |
|--------|-------|
| Publish shared review-decision-v1 spec (docs-only) | Platform (future) |
| Integration CI for cross-repo boundaries | TBD |

---

## 9. Long-Term Stabilization Recommendations

### 9.1 Constitutional Mode

tap_tone_pi now operates in **conditional constitutional stabilization mode**:
- Operational development is primary
- Constitutional escalation only on triggers

**Recommendation:** luthiers-toolbox should adopt the same mode. The constitutional baseline is sufficient; further governance expansion should be implementation-driven.

### 9.2 Escalation Triggers

Re-enter constitutional work only when:
- Authority semantics become ambiguous
- Epistemic status conflicts arise
- Boundary violations discovered
- Provenance legitimacy questions emerge
- Operator sovereignty is bypassed
- Authority laundering is detected

### 9.3 Shared Schema Recommendations (Future)

```
platform-contracts/authority-v1.json
platform-contracts/epistemic-status-v1.json
platform-contracts/review-decision-v1.json
platform-contracts/confidence-v1.json
```

**Status:** Documentation-only recommendation. Implementation requires cross-repo coordination Dev Order.

---

## 10. Risk Assessment

### 10.1 Architectural Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Authority laundering | **High** | ADR-0011 defines interruption points |
| IBG unblocking without ratification | **High** | BLOCKED_PROVENANCE enforced |
| Confidence semantic confusion | **Medium** | Rename confidence_value to candidate_rank |
| Integration without mapping | **Medium** | Require explicit Dev Orders |
| Presentation leakage | **Medium** | ADVISORY_PRESENTATION_BOUNDARY.md |

### 10.2 Integration Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Different vocabulary for same concepts | High | Cross-repo authority crosswalk |
| Missing integration CI | Medium | Add cross-boundary tests |
| Schema drift | Medium | Shared schema spec (future) |

---

## 11. Compliance Assessment

### 11.1 Governance Framework Compliance

| Aspect | Status |
|--------|--------|
| Authority boundaries defined | ✓ |
| Epistemic classification defined | ✓ |
| Review queue semantics documented | ✓ |
| IBG blocking enforced | ✓ |
| Presentation rules documented | ✓ |
| CI enforcement active | ✓ |

### 11.2 Constitutional Completeness

| Repository | Constitutional Baseline |
|------------|------------------------|
| tap_tone_pi | Complete (ADR-0009 through ADR-0012) |
| luthiers-toolbox | Functional (IBG foundation, lifecycle matrix) |
| CAM-Assist | Schema-enforced (authority blocks) |

### 11.3 Gaps

| Gap | Impact | Remediation |
|-----|--------|-------------|
| Epistemic status schema not implemented | Medium | Deferred to future Dev Order |
| Cross-repo integration CI | Medium | Add when integration begins |
| IBG provenance not wired | High | Requires R1 ratification |

---

## Appendix A: Documents Reviewed

### tap_tone_pi

1. ADR-0010-advisory-authority-constitutional-boundary.md
2. ADR-0011-measurement-authority-constitutional-definition.md
3. ADR-0012-epistemic-status-taxonomy.md
4. AGE_CONTRACT.md
5. ADVISORY_PRESENTATION_BOUNDARY.md
6. CONSTITUTIONAL_CONTINUATION_NOTICE.md
7. SPRINT_ARCHITECTURE_HANDOFF.md

### luthiers-toolbox

1. CROSS_REPO_AUTHORITY_CROSSWALK.md
2. IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md
3. MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md
4. EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md
5. CANONICAL_PROVENANCE_MODEL.md
6. IBG_CONSTITUTIONAL_RUNTIME_FOUNDATION.md
7. SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md

### CAM-Assist-Blueprint

1. Strategy package manifest schema
2. Review decision record schema (A12 branch)

---

## Appendix B: Sprint Convergence Timeline

| Dev Order | Repository | Outcome |
|-----------|------------|---------|
| 77 | tap_tone_pi | Governance consolidation audit |
| 78 | tap_tone_pi | ADR-0010 + AGE_CONTRACT.md |
| 79 | tap_tone_pi | ADVISORY_PRESENTATION_BOUNDARY.md |
| 80 | tap_tone_pi | Presentation patches applied |
| 81 | tap_tone_pi | ADR-0011, ADR-0012, schema implications |
| 82 | tap_tone_pi | Constitutional mode transition |
| 8C-8E | luthiers-toolbox | Review UX foundation |
| 7U-7Z | luthiers-toolbox | CAM runtime provenance |
| 1D | luthiers-toolbox | IBG constitutional intake foundation |

---

**Audit Version:** 1.0.0  
**Auditor:** Multi-repository governance analysis  
**Next Review:** Upon first cross-repo integration Dev Order or IBG R1 ratification
