# Sprint Custodian Audit Report

**Date:** 2026-05-24  
**Audit Scope:** Constitutional Stabilization Sprint (Dev Orders 7P–8E)  
**Documents Analyzed:** 5 (100% coverage)  
**Confidence Level:** 95%+  
**Auditor Role:** Sprint Custodian / Systems Architect

---

## Executive Summary

### Sprint Purpose

This sprint represents a **governance inflection point** — the transition from ad-hoc architecture remediation to **governed platform evolution**. The luthiers-toolbox repository has established a formal governance layer with model-enforced invariants, CI-blocking authority gates, and explicit human-review boundaries.

### Key Findings

| Finding | Severity | Impact |
|---------|----------|--------|
| tap_tone_pi 27 unpushed commits | **CRITICAL** | Collaboration/reconstruction risk |
| IBG BLOCKED_PROVENANCE (5 paths) | **HIGH** | Export legitimacy gap until ratified |
| Three parallel review queue systems | **HIGH** | Operator workflow fragmentation |
| Confidence vocabulary collision (4+ representations) | **HIGH** | Authority inheritance confusion |
| 8E in-memory registries | **MEDIUM** | Restart loses queue state |
| Missing handoffs (5C, 5D, 5I-5L, 5U, 5W) | **MEDIUM** | Documentation gaps |
| Cross-repo convergence score 6.0/10 | **MEDIUM** | Integration boundaries unclear |

### Architectural Posture

The sprint successfully establishes:
- **CI-enforced governance gate** blocking authority-chain violations
- **DXF lifecycle guards** on all router endpoints (50+ → 0 unguarded)
- **Runtime capability federation** with 72 passing tests
- **Review queue routing (8E)** that routes human attention without authorizing execution
- **Model-enforced invariants** preventing accidental authorization at construction time

### Governance Alignment

**Local governance maturity:** 8.5/10 — Strong within luthiers-toolbox  
**Cross-repo governance maturity:** 6.0/10 — Vocabulary fragmentation, no shared schema kernel

### Reconstruction Readiness

**Per-repo:** 8.5/10 — Full rebuild possible from handoffs + codebase  
**Cross-repo:** 6.0/10 — Integration boundaries require inference

---

## 1. Technical Findings Report

### 1.1 Sprint Scope Analysis

| Track | Dev Orders | Systems Affected | Tests Added |
|-------|-----------|------------------|-------------|
| Governance Enforcement | PRs #17–#19 | `scripts/governance/`, CI pipeline | Deterministic inventory |
| Runtime Boundary | Phases 1A–2G | DXF routers, CAM services | 33 lifecycle guard |
| Capability Federation | MRP-5M–5Y | `runtime_capabilities/` | 72 integration |
| Review UX/Queue | 8C, 8D, 8E | `review_*` modules | 138 (68+70) |

**Total new tests this sprint:** 243+

### 1.2 Schema Changes

| Schema | Status | Impact |
|--------|--------|--------|
| `DxfLifecycleContext` | Created | DXF export governance |
| `FederatedCapability` | Created | Capability federation |
| `ReviewQueueItem` | Created | 8E queue routing |
| `ReviewDecisionRecord` | Created | 8E decision audit trail |
| `ReviewQueueCISummary` | Created | 8E CI classification |
| `ManufacturingReviewPanel` | Created | 8C review panels |
| `ReviewAttentionPriority` | Created | 8C priority scoring |
| `ReviewUXBaseline` | Created | 8D baseline comparison |

### 1.3 Invariant Enforcement

8E introduces **model-enforced invariants** via Pydantic validators:

```python
# ReviewQueueItem invariants (cannot be True)
human_review_required: bool = True      # Always True
decision_authorized: bool = False       # Always False
implementation_authorized: bool = False # Always False
execution_authorized: bool = False      # Always False
machine_output_allowed: bool = False    # Always False
```

**Enforcement mechanism:** `@model_validator(mode="after")` raises `ValueError` on violation.

### 1.4 File Inventory Delta

| Category | Created | Modified |
|----------|---------|----------|
| CAM models | 10 | 0 |
| CAM routers | 3 | 1 |
| Governance scripts | 4 | 0 |
| Runtime capabilities | 8 | 0 |
| Tests | 6 | 0 |
| Documentation | 5+ | 3 |

### 1.5 Complexity Metrics

| Module | Before | After | Reduction |
|--------|--------|-------|-----------|
| `parse_dxf` | CC 50 | CC 19 | 62% |
| `run_manufacturing_checks` | CC 50 | CC 12 | 76% |
| Unguarded DXF exports | 50+ | 0 | 100% |

---

## 2. Governance Compliance Assessment

### 2.1 Authority Hierarchy Compliance

| Tier | Document | Compliance |
|------|----------|------------|
| Tier 1 | `ARCHITECTURE_INVARIANTS.md` | **COMPLIANT** |
| Tier 2 | `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | **COMPLIANT** |
| Tier 3 | Runtime capability policies | **COMPLIANT** |

### 2.2 Cross-Repo Authority Crosswalk

**Aligned concepts (3 repos agree):**
- Human authority final for decisions
- Non-execution defaults
- Fail-closed validation
- Provenance tracking

**Divergent concepts:**

| Concept | tap_tone_pi | luthiers-toolbox | CAM-Assist |
|---------|-------------|------------------|------------|
| Authority class | `AuthorityClass` enum | `AuthorityState` + 8E flags | JSON block booleans |
| Confidence | `TypedConfidenceV1` | `ConfidenceDeclaration` + `rank_score` | — |
| Review queue | — | `ReviewQueueItem` (8E) | `index_staged_packages` (A11) |
| Decision record | — | `ReviewDecisionRecord` (8E) | `review_decision_record.schema.json` |

### 2.3 Constitutional Stabilization (DO 77–82) Compliance

| Dev Order | tap_tone Outcome | luthiers Impact | Status |
|-----------|------------------|-----------------|--------|
| 77 | Governance consolidation | Audit doc imported | **COMPLIANT** |
| 78 | ADR-0010 + AGE contract | Acoustic UI panels | **PENDING integration** |
| 79–80 | Presentation boundary | Shared report surfaces | **PENDING review** |
| 81 | Epistemic taxonomy | Map to `ConfidenceType` | **DOCS-ONLY** |
| 82 | Conditional stabilization | Escalation triggers | **ACTIVE** |

### 2.4 IBG Provenance Status

| Path | Lines | Status | Blocking |
|------|-------|--------|----------|
| `body_contour_solver.py` | 777, 808 | `BLOCKED_PROVENANCE` | R1 ratification |
| `arc_reconstructor.py` | 1116, 1279, 1303 | `BLOCKED_PROVENANCE` | R1 ratification |

**Ratification phases:**
- **R0** (Documentation): In progress
- **R1** (Governance ratification): Target next governance sprint
- **R2** (Export wrapper): Blocked on R1
- **R3** (Commercial posture): Gated

---

## 3. Architectural Risk Assessment

### 3.1 Critical Risks

| Risk | Evidence | Failure Mode | Mitigation |
|------|----------|--------------|------------|
| tap_tone 27 unpushed commits | Git forensics | Collaborator reconstruction failure | **P0: Push immediately** |
| IBG authority laundering | `BLOCKED_PROVENANCE` still open | Ungoverned geometry export | Complete R1 ratification |
| Review queue fragmentation | 3 parallel implementations | Operator runs wrong CLI/API | Publish unified spec |

### 3.2 High Risks

| Risk | Evidence | Failure Mode | Mitigation |
|------|----------|--------------|------------|
| Confidence vocabulary | 4+ representations | Silent authority inheritance | Mandate `TypedConfidence` |
| CAM→luthiers integration undefined | No wire-up on disk | False integration assumptions | Document as TBD |
| `rank_score` → `confidence_value` | IBG pipeline code | Operators treat rank as approval | Audit usage; add guards |

### 3.3 Medium Risks

| Risk | Evidence | Failure Mode | Mitigation |
|------|----------|--------------|------------|
| 8E in-memory registries | Design doc | Lost reviews on restart | Persistence layer (future) |
| Missing handoffs | 5C, 5D, 5I-5L, 5U, 5W | Documentation gaps | OBSERVATION entries |
| DxfWriter caller-context | Not rolled out | Central point affects 12+ paths | Contract enforcement |
| tap_tone language guard non-strict | 13 findings | Guidance claims truth | Enable strict CI |

### 3.4 Architectural Bottlenecks

| Bottleneck | Impact | Mitigation Path |
|------------|--------|-----------------|
| `dxf_writer.py` central point | All DXF exports flow through | Caller-context contract (Phase 2G) |
| Static capability registration | No runtime capability addition | Future: dynamic loading |
| No shared schema registry | Integration requires inference | `platform-contracts/` (Phase 2) |

---

## 4. Divergence Detection

### 4.1 Architectural Drift

| Domain | Drift Type | Severity | Evidence |
|--------|------------|----------|----------|
| Review semantics | CAM `approve_for_downstream_cam` vs 8E `mark_reviewed` | **HIGH** | Schema comparison |
| Confidence representation | 4+ incompatible patterns | **HIGH** | Crosswalk table |
| Provenance records | Epistemic vs DxfLifecycle vs strategy provenance | **MEDIUM** | No unified model |
| Package IDs | Incompatible formats | **MEDIUM** | `rqi-{uuid12}` vs `operation:spec_id` |

### 4.2 Schema Divergence

| Field | tap_tone_pi | luthiers-toolbox | CAM-Assist |
|-------|-------------|------------------|------------|
| Confidence | `TypedConfidenceV1` (domain + value + source) | `ConfidenceDeclaration` + bare `rank_score` | — |
| Authority | `AuthorityClass` enum | `AuthorityState` + boolean invariants | JSON block |
| Decision | — | `DecisionType` (5 types) | `approve_for_downstream_cam` |
| ID format | workflow_id | `rqi-{uuid12}` | `operation_type:source_spec_id` |

### 4.3 Duplicated Governance Logic

| System | Instances | Risk |
|--------|-----------|------|
| CI governance runners | 3 separate ecosystems | Duplicated policy logic |
| Review queue | CAM A11, luthiers 8E, IBG review packages | Incompatible workflows |
| Authority validation | JSON Schema + Pydantic + contract tests | No shared validator |

### 4.4 Conflicting Abstractions

| Conflict | Description | Resolution Path |
|----------|-------------|-----------------|
| Measurement vs geometry authority | tap_tone: capture ≠ truth; luthiers: COMPAT_ONLY; CAM: never executes | Crosswalk mapping |
| Review routing vs review package | 8E routes; IBG emits; unclear if CAM feeds luthiers | Integration spec |
| Advisory vs ranked candidate | tap_tone forbids guidance in exports; luthiers rank→confidence | Vocabulary guard |

### 4.5 Incompatible Workflows

| Workflow | System A | System B | Gap |
|----------|----------|----------|-----|
| Human review | 8E: decision updates status | CAM: record in manifest | No shared decision ID |
| Package staging | CAM: filesystem packages | luthiers: in-memory registry | Persistence mismatch |
| CI enforcement | luthiers: blocking gate | tap_tone: optional strict | Strictness mismatch |

---

## 5. Sprint Convergence Roadmap

### Phase 0 — Stabilize Locally (Immediate)

| Action | Owner | Priority | Status |
|--------|-------|----------|--------|
| Push tap_tone 27 commits | tap_tone_pi | **P0** | PENDING |
| Keep regression guard green | luthiers-toolbox | **P0** | ACTIVE |
| Rename constitutional import folder (avoid em-dash) | luthiers-toolbox | **P0** | PENDING |
| Restore research 1A/1B from remote branch | luthiers-toolbox | **P1** | PENDING |

### Phase 1 — Vocabulary Convergence (Week 1–2, docs-only)

| Action | Deliverable | Owner |
|--------|-------------|-------|
| Ratify `CROSS_REPO_AUTHORITY_CROSSWALK.md` | Signed crosswalk | All repos |
| Map epistemic status ↔ lifecycle class ↔ authority block | Mapping table | luthiers |
| Document CAM→luthiers integration as TBD | Integration spec (stub) | luthiers |
| Add `epistemic_status` optional field to review artifacts | Additive schema change | luthiers |

### Phase 2 — Contract Boundaries (Month 1)

| Action | Deliverable | Owner |
|--------|-------------|-------|
| Define `integration-v1` JSON Schema | Schema file | platform-contracts |
| CAM strategy package handoff spec | Import markers | CAM-Assist |
| tap_tone `viewer_pack_v1` import markers | Predicted/External flags | tap_tone_pi |
| Deprecate bare `confidence: float` | Migration guide | tap_tone_pi |

### Phase 3 — CI Harmonization (Month 1–2)

| Action | Deliverable | Owner |
|--------|-------------|-------|
| Shared authority invariant tests (parameterized) | pytest module | platform-contracts |
| CI manifest drift detection | CI job | luthiers-toolbox |
| Enable tap_tone language guard `--strict` | CI config | tap_tone_pi |
| Cross-repo contract tests | Integration test suite | All repos |

### Phase 4 — Runtime Integration (Month 2+, gated on R1)

| Action | Deliverable | Owner |
|--------|-------------|-------|
| IBG provenance ratification (R1) | Signed governance record | luthiers-toolbox |
| Review Router API (CAM package metadata) | REST endpoint | luthiers-toolbox |
| IBG review package alignment with 8C | Field mapping | luthiers-toolbox |
| DxfWriter caller-context rollout | Enforced contracts | luthiers-toolbox |

### Convergence Milestones

| Milestone | Definition of Done | Target |
|-----------|-------------------|--------|
| M1 | Crosswalk ratified by all repo owners | Week 1 |
| M2 | All repos CI green on authority invariant tests | Week 3 |
| M3 | CAM→luthiers integration spec (even if not implemented) | Week 4 |
| M4 | IBG provenance unblocked in lifecycle matrix | Month 2 |
| M5 | tap_tone 27 commits pushed | Immediate |

---

## 6. Recommended Immediate Actions

### Priority 0 (Today)

| Action | Owner | Risk Addressed |
|--------|-------|----------------|
| Push tap_tone 27 commits to origin | tap_tone_pi | Reconstruction/collaboration |
| Rename em-dash folder in luthiers imports | luthiers-toolbox | Path encoding issues |
| Verify regression guard green in CI | luthiers-toolbox | Bypass vectors |

### Priority 1 (This Week)

| Action | Owner | Risk Addressed |
|--------|-------|----------------|
| Schedule IBG R1 ratification session | luthiers governance | Export legitimacy gap |
| Restore `docs/research/` 1A/1B from remote | luthiers-toolbox | Research reconstruction |
| Document missing handoffs as OBSERVATION | luthiers-toolbox | Documentation gaps |
| Enable tap_tone language guard `--strict` after 13-fix | tap_tone_pi | Guidance authority |

### Priority 2 (This Sprint)

| Action | Owner | Risk Addressed |
|--------|-------|----------------|
| Add CI manifest drift detection | luthiers-toolbox | Capability drift |
| Document CAM→luthiers integration as TBD | All repos | False assumptions |
| Add governance inventory entry for research layer | luthiers-toolbox | Fragmentation |
| Audit `rank_score` → `confidence_value` usage | luthiers-toolbox | Authority inheritance |

---

## 7. Long-Term Stabilization Recommendations

### 7.1 Architectural Recommendations

1. **`platform-contracts` repository** — Schemas + invariant tests only; consumers: all three repos
2. **Unified review routing spec** — Implemented once in luthiers; CLI adapters in CAM-Assist
3. **Provenance service** — Read-only lineage API for DXF + strategy packages + measurement imports
4. **Governance dashboard** — Aggregate check_all, tap_tone CI scripts, CAM pytest summary

### 7.2 Domain Separation

| Domain | Owner | Scope |
|--------|-------|-------|
| Acoustic measurement | tap_tone_pi | Capture integrity, not truth claims |
| Strategy intent | CAM-Assist | Package + stage, no G-code |
| Geometry/runtime/CAM | luthiers-toolbox | Execution prep, governed exports |
| Cognition R&D | vectorizer-sandbox | External, `R_AND_D_EXCLUDED` |

### 7.3 Research Layer Governance

- Research waves continue as **institutional memory**
- Findings promote to governance via **explicit Dev Orders only**
- Research docs are **non-authoritative** — README authority banner required
- Cross-links required when duplicating concepts

### 7.4 Testing Requirements

| Requirement | Enforcement |
|-------------|-------------|
| Authority tests non-optional for merge | CI blocking |
| Deterministic manifest outputs | Hash validation |
| Cross-repo contract tests | Integration CI (future) |
| 8E invariant tests | Model validators |

### 7.5 Schema Evolution Policy

| Principle | Implementation |
|-----------|----------------|
| Additive-first | Optional fields before required |
| Deprecations with timeline | Migration docs required |
| No silent authority promotion | CI guards |
| Breaking changes require ADR/Dev Order | Governance gate |

---

## 8. Knowledge Preservation Notes

### 8.1 Assumptions Made

1. **8E is routing-only** — Does not authorize implementation, execution, or machine output
2. **Lifecycle guards are validation-only** — No mutation, no side effects (trust before provenance)
3. **IBG BLOCKED_PROVENANCE is intentional** — Fail-closed posture, not a bug
4. **vectorizer-sandbox is external** — `R_AND_D_EXCLUDED` lifecycle class enforced
5. **CAM→luthiers integration is undefined** — No wire-up found on disk

### 8.2 Inferred Architecture

```
[Photo/Blueprint Vectorizer] ──► DXF ──► [IBG Workflow 1A]
        │ (vectorizer-sandbox R&D)            │
        │                                      ▼
        │                           BodyEvidenceCandidate
        │                                      │
[CAM Runtime Spine] ◄── capability ◄── review queue 8E
        │
        ▼
   DXF exports (guarded) ──► fabrication

[CAM-Assist] ── strategy packages ──?──► (integration TBD)

[tap_tone_pi] ── measurement ──?──► (Predicted import only)
```

### 8.3 Non-Obvious Decisions

| Decision | Rationale |
|----------|-----------|
| 8E model-enforced invariants | Prevents accidental authorization at construction |
| 8E decision-to-status mapping fixed | Ensures audit trail consistency |
| 8E shallow panel lookup | Avoids circular registry dependencies |
| 8E computed-on-demand filtering | Avoids stale secondary indexes |
| No fake guards | False coverage worse than no guard |
| Validation-only first | Establish trust before provenance mutation |

### 8.4 Tribal Knowledge

1. **R12 vs R2000:** R12 for hobbyist (max compat); R2000 for CAM workflows (professional)
2. **Guard placement:** `assert_dxf_lifecycle_context()` immediately before `saveas()`, not at function entry
3. **Capability resolution backward compat:** If `request.capability_id` is None, resolution skipped
4. **Constitutional mode (DO 82):** Operational dev primary; escalate only on triggers

---

## 9. Unresolved Questions

| Question | Status | Resolution Path |
|----------|--------|-----------------|
| CAM-Assist approved packages feed luthiers 8E? | **PENDING** | Wire-up not found; explicit spec needed |
| `review_decision_record.schema.json` in CAM-Assist main? | **PENDING** | On branch `cam-a12-*`; merge pending |
| vectorizer-sandbox release tags | **PENDING** | `pending tag` in research docs |
| tap_tone 27 unpushed commits content | **PENDING** | Push to verify |
| Production deployment topology | **INFERRED** | Dev/CI focus |
| Research 1A/1B/1C spine complete on disk | **PARTIAL** | 1A/1B restored; 1C status unclear |
| IBG R1 ratification timeline | **UNSCHEDULED** | Next governance sprint target |

---

## 10. Reconstruction Readiness Scorecard

| Metric | Score | Notes |
|--------|-------|-------|
| Per-repo reconstruction readiness | 8.5/10 | Strong local handoffs |
| Cross-repo convergence readiness | 6.0/10 | Vocabulary fragmentation |
| Governance maturity (global) | 6.5/10 | High local, medium global |
| Architecture stability (global) | 7.0/10 | Three stable spines, undefined integration |
| Documentation coverage | 8.0/10 | Missing handoffs noted |
| Test coverage | 8.5/10 | 243+ new tests this sprint |
| CI enforcement | 8.0/10 | luthiers blocking; tap_tone optional strict |

**Overall Sprint Health:** **7.5/10**

---

## Appendix A: Document Coverage

| Document | Lines | Coverage | Key Findings |
|----------|-------|----------|--------------|
| `CROSS_REPO_AUTHORITY_CROSSWALK.md` | 260 | 100% | Semantic mapping, PENDING items |
| `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | 115 | 100% | 5 blocked paths, R0-R3 phases |
| `MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` | 527 | 100% | 8 divergence conflicts, 4-phase strategy |
| `SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md` | 877 | 100% | 66 commits, 8C/8D/8E coverage |
| `SPRINT_BOARD.md` | 228 | 100% | Historical context (March 2026) |

**Total lines analyzed:** 2,007  
**Coverage achieved:** 100%

---

## Appendix B: Git Forensics Snapshot

| Repository | Branch | HEAD | Upstream | Ahead | Behind |
|------------|--------|------|----------|-------|--------|
| luthiers-toolbox | main | `52259793` | origin/main | 2 | 0 |
| tap_tone_pi | main | `c910fcc` | origin/main | **27** | 0 |
| CAM-Assist-Blueprint | main | `07e6c04` | origin/main | 0 | 0 |
| vectorizer-sandbox | master | `6390c26` | origin/master | 0 | 0 |

**Critical:** tap_tone_pi 27 commits ahead of origin — highest reconstruction risk.

---

## Appendix C: Escalation Triggers (from DO 82)

Re-open constitutional review if:

- Authority semantics ambiguity at IBG export boundary
- Epistemic status conflicts between IBG candidates and CAM exports
- Operator sovereignty bypass via automated rank → export
- Provenance chain gaps discovered in production paths
- Boundary violations detected
- Authority laundering detected

---

*Audit completed: 2026-05-24*  
*Document coverage: 100% (5/5 documents, 2,007 lines)*  
*Confidence level: 95%+*  
*Next audit trigger: First cross-repo integration Dev Order, IBG R1 ratification, or tap_tone push*
