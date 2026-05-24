# Sprint Deep Audit Report

**Date:** 2026-05-24  
**Scope:** MRP-5M through MRP-6A, Dev Orders 7Y–8E, Cross-Repo Governance Convergence  
**Auditor Role:** Senior Systems Architect / Governance Auditor  
**Coverage:** 95%+ of referenced documentation analyzed  
**Status:** COMPLETE

---

## Executive Summary

This audit covers a 10-day sprint window (2026-05-15 to 2026-05-24) representing the most significant governance and runtime architecture consolidation in the repository's history. The sprint executed **three major parallel tracks**:

### Track 1: Governed Runtime Spine (MRP-5M → MRP-6A)
- **6 core modules** implemented (7,280 lines)
- **111 tests** passing with 11-test regression guard
- **Complete gate chain**: Validation → Admission → Capability → Execution → Provenance → Replay
- **Constitutional invariants** enforced: "AI may advise but not authorize execution"

### Track 2: Review UX & Queue Routing (8C, 8D, 8E)
- **Review queue routing** with 5 model-enforced invariants
- **138+ tests** covering CI enforcement and queue semantics
- **Non-execution guarantee**: `execution_authorized=False` always, model-validated

### Track 3: Cross-Repository Governance Convergence
- **4 repositories** analyzed (luthiers-toolbox, tap_tone_pi, CAM-Assist-Blueprint, vectorizer-sandbox)
- **Constitutional stabilization** (DO 77–82) imported and mapped
- **Authority crosswalk** created for vocabulary normalization
- **Convergence score**: 6.0/10 (per-repo: 8.8/10)

**Critical Finding:** The sprint successfully established governance-first development discipline. All DXF exports now route through `dxf_compat`. The runtime spine provides capability resolution gates before adapter execution. However, **5 IBG DXF save points remain BLOCKED_PROVENANCE** pending governance ratification.

**Reconstruction Readiness:** 8.5/10 (single-repo), 6.0/10 (cross-repo)

---

## 1. Technical Findings Report

### 1.1 Sprint Intent Reconstruction

The sprint pursued **constitutional runtime governance** — ensuring that:
1. No capability executes without explicit resolution and admission
2. No DXF export bypasses lifecycle tracking
3. No review queue routes decisions, only attention
4. No cross-repo integration assumes shared vocabulary without mapping

**Architectural philosophy:** Gate-before-execute; fail-closed validation; human authority preserved.

### 1.2 Systems Affected

| System | Change Type | Lines | Tests |
|--------|-------------|-------|-------|
| `runtime_capabilities/` | New package | ~2,200 | 42 |
| `runtime_service/` | Enhanced | ~1,400 | 19 |
| `runtime_admission/` | New package | ~1,100 | — |
| `runtime_provenance/` | New package | ~1,200 | 39 |
| `runtime_manifest/` | New package | ~780 | — |
| `topology_validation/` | New package | ~600 | — |
| `dxf_lifecycle_guard.py` | New module | ~200 | 33 |
| `review_ux_*` (8C) | New modules | ~400 | 68 |
| `review_queue_*` (8E) | New modules | ~500 | 70+ |
| **Total** | — | **~8,380** | **~270** |

### 1.3 Major Changes Introduced

#### Runtime Capability Federation
```
FederatedCapability → CapabilityRegistry → CapabilityResolver → PolicyFederation
```
- Namespaced capability IDs (`operation:nut_slot`, `adapter:dxf_export`)
- 5 execution policies evaluated deterministically
- Duplicate capability rejection at registration time

#### DXF Lifecycle Guard Program
- **55+ export paths** inventoried
- **7 router endpoints** with GUARD_ADDED status
- **3 runtime services** guarded
- **5 IBG paths** BLOCKED_PROVENANCE (intentional)

#### Review Queue Invariants (8E)
```python
human_review_required = True          # Always
decision_authorized = False           # Always
implementation_authorized = False     # Always
execution_authorized = False          # Always
machine_output_allowed = False        # Always
```
Pydantic `@model_validator(mode="after")` enforces these at construction time.

### 1.4 Schema Changes

| Schema | State | Purpose |
|--------|-------|---------|
| `FederatedCapability` | New | Capability metadata with governance classification |
| `CapabilityResolutionResult` | New | Resolution status, policy decision, rejection reasons |
| `DxfLifecycleContext` | New | Export provenance tracking |
| `ReviewQueueItem` | New | Queue item with 5 invariants |
| `ReviewDecisionRecord` | New | Decision audit trail |
| `CertifiedRuntimeRequest` | Enhanced | Added `capability_id`, `is_replay_mode` |

### 1.5 Governance Implementations

| Mechanism | Status | CI Tier |
|-----------|--------|---------|
| `check_all.py` unified runner | Active | ci |
| Authority chain audit | Active | manual |
| Export lifecycle matrix validator | Active | ci |
| Capability regression guard | Active | ci |
| DXF lifecycle guard | Active | runtime |
| Review queue CI summary | Active | ci |

---

## 2. Governance Compliance Assessment

### 2.1 Compliance Matrix

| Governance Tier | Document | Sprint Status |
|-----------------|----------|---------------|
| **Tier 1 (Structural)** | `ARCHITECTURE_INVARIANTS.md` | COMPLIANT |
| **Tier 1 (Structural)** | `FEATURE_PARITY_MIGRATION_POLICY.md` | COMPLIANT |
| **Tier 2 (Domain)** | `MORPHOLOGY_RECONSTRUCTION_PLATFORM.md` | COMPLIANT |
| **Tier 2 (Domain)** | `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | COMPLIANT |
| **Tier 3 (Operational)** | `SPRINT_NAMESPACE_STANDARD.md` | COMPLIANT |
| **Tier 3 (Operational)** | Capability registry | COMPLIANT |

### 2.2 Constitutional Alignment (DO 77–82 Import)

The sprint imported and mapped tap_tone_pi constitutional documents:

| ADR | Concept | luthiers Mapping |
|-----|---------|------------------|
| ADR-0010 | Advisory authority boundary | 8E `execution_authorized=False` |
| ADR-0011 | Measurement authority | `DxfLifecycleContext.provenance_status` |
| ADR-0012 | Epistemic status taxonomy | `ConfidenceDeclaration.confidence_type` |

**Alignment score:** Strong conceptual alignment; vocabulary normalization PENDING.

### 2.3 Authority Chain Compliance

| Authority Type | tap_tone_pi | luthiers-toolbox | Status |
|----------------|-------------|------------------|--------|
| Human review required | Export tests | 8E invariants | ALIGNED |
| Machine execution forbidden | N/A (measurement) | 8E invariants | ALIGNED |
| Confidence ≠ authority | TypedConfidenceV1 | ConfidenceDeclaration | ALIGNED (vocabulary differs) |
| Provenance required | Epistemic status | DxfLifecycleContext | PARTIAL (5 IBG paths blocked) |

### 2.4 Governance Gaps Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| G-001 | IBG BLOCKED_PROVENANCE (5 paths) | HIGH | Ratification R1–R2 per timeline |
| G-002 | Confidence vocabulary collision | MEDIUM | Adopt TypedConfidence pattern |
| G-003 | No shared cross-repo schema registry | MEDIUM | Phase 2 convergence |
| G-004 | 8E in-memory queue (ephemeral) | LOW | Document in ops runbook |
| G-005 | tap_tone 27 unpushed commits | MEDIUM | Push to origin |

---

## 3. Architectural Risk Assessment

### 3.1 Risk Registry

| Risk ID | Risk | Likelihood | Impact | Severity | Mitigation |
|---------|------|------------|--------|----------|------------|
| R-001 | IBG DXF bypasses lifecycle governance | Low | High | **HIGH** | BLOCKED_PROVENANCE gate holds |
| R-002 | Capability bypass via unknown ID | Low | High | **MEDIUM** | 11-test regression guard |
| R-003 | Review queue treats rank as approval | Medium | High | **HIGH** | Model-enforced invariants |
| R-004 | Cross-repo integration assumes shared vocabulary | High | Medium | **MEDIUM** | Authority crosswalk created |
| R-005 | DxfWriter central point (12+ callers) | Low | Medium | **LOW** | REQUIRES_CALLER_CONTEXT documented |
| R-006 | Manifest drift undetected | Medium | Low | **LOW** | CI enforcement follow-up |

### 3.2 Technical Debt Hotspots

| Hotspot | Location | Debt Type | Action |
|---------|----------|-----------|--------|
| DxfWriter caller context | `cam/dxf_writer.py` | Architecture | Rollout caller-context interface |
| Missing handoffs | `docs/handoffs/` | Documentation | Create as OBSERVATION |
| Service/replay namespaces | `runtime_capabilities/` | Incomplete | Populate per Replay Lane |
| 8E shallow panel lookup | `review_queue_registry.py` | Design | Acceptable for Phase 1 |
| Dynamic capability loading | `runtime_capabilities/` | Feature gap | Future enhancement |

### 3.3 Failure Mode Analysis

| Failure Mode | Detection | Impact | Recovery |
|--------------|-----------|--------|----------|
| Capability not found | ResolutionStatus.NOT_FOUND | Request rejected | Register capability |
| Disabled capability | ResolutionStatus.DISABLED | Request rejected | Enable in registry |
| Replay-unsafe in replay mode | ResolutionStatus.REPLAY_UNSAFE | Request rejected | Use replay-safe alternative |
| Admission rejected | AdmissionDecision.REJECTED | Execution blocked | Fix topology/tier |
| Guard context missing | Assertion error | Export blocked | Caller must supply context |
| IBG provenance gap | BLOCKED_PROVENANCE | Export blocked | Complete R1–R2 ratification |

---

## 4. Sprint Convergence Roadmap

### Phase 0: Immediate Stabilization (Days 1–3)

| Task | Priority | Owner | Dependency |
|------|----------|-------|------------|
| Push tap_tone 27 commits to origin | P0 | tap_tone_pi | None |
| Keep regression guard green | P0 | luthiers-toolbox | None |
| Commit audit bundle to main | P1 | luthiers-toolbox | None |
| Ratify crosswalk with repo owners | P1 | Cross-repo | Crosswalk created |

### Phase 1: Vocabulary Convergence (Week 1–2)

| Task | Priority | Owner | Dependency |
|------|----------|-------|------------|
| Add `epistemic_status` to review artifacts | P1 | luthiers-toolbox | None (additive) |
| Cleanup tap_tone 13 language guard findings | P1 | tap_tone_pi | None |
| Document CAM→luthiers as TBD | P2 | All | None |
| Create governance inventory entry for research | P2 | luthiers-toolbox | None |

### Phase 2: Schema Normalization (Month 1)

| Task | Priority | Owner | Dependency |
|------|----------|-------|------------|
| Ratify IBG provenance model (R1) | P0 | luthiers-toolbox | Governance session |
| Wire IBG provenance wrapper (R2) | P1 | luthiers-toolbox | R1 complete |
| Add CI manifest drift detection | P2 | luthiers-toolbox | None |
| Publish `review-decision-v1` spec (docs) | P2 | Cross-repo | Vocabulary convergence |

### Phase 3: Architectural Alignment (Month 2)

| Task | Priority | Owner | Dependency |
|------|----------|-------|------------|
| Enable tap_tone `--strict` language guard | P1 | tap_tone_pi | 13 findings fixed |
| CAM manifest authority field alignment | P2 | CAM-Assist | Authority crosswalk |
| Shared authority invariant tests | P2 | Cross-repo | Vocabulary convergence |
| Review Router API (read-only CAM index) | P3 | luthiers-toolbox | IBG ratification |

### Phase 4: Long-Term Integration (Month 3+)

| Task | Priority | Owner | Dependency |
|------|----------|-------|------------|
| `platform-contracts` repo (schemas only) | P2 | Cross-repo | Vocabulary stable |
| Unified provenance service (read-only) | P3 | luthiers-toolbox | Schema normalization |
| Governance dashboard aggregation | P3 | Cross-repo | All CI scripts stable |
| Dynamic capability loading | P3 | luthiers-toolbox | Static proven |

### Convergence Milestones

| Milestone | Definition of Done | Target |
|-----------|-------------------|--------|
| M1 | Crosswalk doc ratified | Week 1 |
| M2 | IBG R1 ratification complete | Week 2 |
| M3 | All repos CI green on authority tests | Week 4 |
| M4 | CAM→luthiers integration spec | Month 2 |
| M5 | IBG BLOCKED_PROVENANCE resolved | Month 2 |

---

## 5. Recommended Immediate Actions

### Critical (P0)

| Action | Rationale | Owner |
|--------|-----------|-------|
| **Push tap_tone 27 commits** | Reconstruction/collaboration risk | tap_tone_pi |
| **Keep regression guard green** | Capability bypass protection | luthiers-toolbox |
| **Do not promote IBG to LIFECYCLE_GOVERNED** | BLOCKED_PROVENANCE exists for a reason | All |

### High Priority (P1)

| Action | Rationale | Owner |
|--------|-----------|-------|
| Schedule R1 ratification session | Unblocks IBG export governance | luthiers-toolbox |
| Add `epistemic_status` field (additive) | Cross-repo vocabulary alignment | luthiers-toolbox |
| Commit audit artifacts | Preserve institutional memory | luthiers-toolbox |
| Document any new DXF exports in matrix | Maintain lifecycle inventory | DXF team |

### Medium Priority (P2)

| Action | Rationale | Owner |
|--------|-----------|-------|
| CI manifest drift detection | Catch capability changes | CI team |
| Fix tap_tone 13 language findings | Enable strict mode | tap_tone_pi |
| Create missing handoffs as OBSERVATION | Documentation completeness | Docs |
| Add governance inventory entry for research | Link research → governance | luthiers-toolbox |

---

## 6. Long-Term Stabilization Recommendations

### Architectural Principles (Preserve)

1. **Gate-before-execute**: No capability executes without resolution + admission
2. **Fail-closed validation**: Unknown/disabled/unsafe capabilities rejected
3. **Human authority supreme**: Review queues route attention, not decisions
4. **Provenance required**: All governed exports carry lifecycle context
5. **Sandbox discovers / runtime ratifies**: No cognition bypasses constitutional gates

### Stability Priorities

| Priority | Action | Why |
|----------|--------|-----|
| 1 | Keep 11-test regression guard green | Core bypass protection |
| 2 | Keep lifecycle matrix validator passing | Export coverage tracking |
| 3 | Keep governance gate CI-enforced | Authority chain integrity |
| 4 | Maintain R&D/production separation | Cognition must not silently enter spine |
| 5 | Preserve constitutional imports | Cross-repo alignment baseline |

### Anti-Patterns to Block

| Anti-Pattern | Why Forbidden | Enforcement |
|--------------|---------------|-------------|
| Direct `ezdxf.new()` in production | Bypasses dxf_compat | CI grep gate |
| `rank_score` → approval | Authority laundering | 8E model validators |
| IBG DXF without provenance | Ungoverned geometry export | BLOCKED_PROVENANCE matrix |
| Sandbox import to spine | R&D must graduate explicitly | `check_semantic_sandbox_imports.py` |
| Capability bypass via unknown ID | Gate circumvention | Regression guard tests |
| Auto-fabrication from review queue | Human authority violation | 8E invariants |

### Research Layer Position

| Principle | Implementation |
|-----------|----------------|
| Research is **non-authoritative** | README authority banner |
| Research documents findings, not law | Governance → code; Research → memory |
| Waves 0–E preserve lineage | Do not erase; amend in place |
| Cognition graduation requires Dev Order | Explicit promotion only |

---

## 7. Appendices

### A. File References

| Category | Key Files |
|----------|-----------|
| Runtime Spine | `app/cam/runtime_capabilities/`, `runtime_service/`, `runtime_admission/` |
| DXF Lifecycle | `app/util/dxf_lifecycle_guard.py`, `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` |
| Review Queue | `app/cam/review_queue_*.py`, `review_ux_*.py` |
| Governance | `scripts/governance/check_all.py`, `docs/governance/` |
| Cross-Repo | `CROSS_REPO_AUTHORITY_CROSSWALK.md`, `MULTI_REPO_GOVERNANCE_CONVERGENCE_REPORT.md` |
| Constitutional | `docs/handoffs/imports/constitutional_stabilization_do_77_82/` |
| Research | `docs/research/RESEARCH_WAVE_INDEX.md` |

### B. Schema References

| Schema | Location | Version |
|--------|----------|---------|
| FederatedCapability | `runtime_capabilities/contracts.py` | 0.1.0 |
| CapabilityManifest | `runtime_capabilities/manifest.py` | 0.1.0 |
| DxfLifecycleContext | `util/dxf_lifecycle_guard.py` | 1.0 |
| ReviewQueueItem | `cam/review_queue_item.py` | 8E |
| ReviewDecisionRecord | `cam/review_decision_record.py` | 8E |
| BodyEvidenceCandidate | `ibg/body_evidence_candidate.py` | 1A |

### C. Commit References

| Commit | Description |
|--------|-------------|
| `81764bb0` | PR #35 merge: Runtime spine + regression guard |
| `52259793` | Sprint handoff timestamped pattern |
| `2017aba9` | 8C/8D/8E review UX and queue routing |
| `6c74e3a1` | Governance baseline freeze (7Z) |
| `4e7dd127` | Federation CI enforcement (7Y) |

### D. Subsystem Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GOVERNANCE LAYER (Tier 1-3)                     │
├─────────────────────────────────────────────────────────────────────┤
│  check_all.py ──► authority_chain_audit ──► lifecycle_validator    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                      RUNTIME SPINE (MRP-5)                          │
├─────────────────────────────────────────────────────────────────────┤
│  CertifiedTopology ──► RuntimeAdmission ──► CapabilityResolver      │
│         │                     │                     │               │
│         ▼                     ▼                     ▼               │
│  CertifiedRuntimeService ──► RuntimeProvenance ──► RuntimeReplay    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                      DXF LIFECYCLE LAYER                            │
├─────────────────────────────────────────────────────────────────────┤
│  dxf_compat ──► DxfLifecycleGuard ──► EXPORT_LIFECYCLE_MATRIX       │
│        │                                         │                  │
│        ▼                                         ▼                  │
│  COMPAT_ONLY (25+) ─── GUARD_ADDED (10) ─── BLOCKED_PROVENANCE (5)  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                      REVIEW UX LAYER (8C-8E)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ManufacturingReviewPanel ──► ReviewAttentionPriority               │
│         │                              │                            │
│         ▼                              ▼                            │
│  ReviewQueueItem ──► ReviewDecisionRecord ──► ReviewQueueCISummary  │
│  (5 invariants)       (decision audit)        (PASS/WARN/FAIL)      │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│                      IBG / RESEARCH BOUNDARY                        │
├─────────────────────────────────────────────────────────────────────┤
│  BodyEvidenceCandidate ──► IBGIntakeGate ──► BLOCKED_PROVENANCE     │
│         │                                                           │
│         ▼                                                           │
│  vectorizer-sandbox (R_AND_D_EXCLUDED) ──► import_gate_CI           │
└─────────────────────────────────────────────────────────────────────┘
```

### E. Assumptions and Unknowns

| Item | Status | Notes |
|------|--------|-------|
| CAM→luthiers runtime integration | **UNKNOWN** | No wire-up found on disk |
| tap_tone 27 commits content | **ASSUMED** | Constitutional stabilization sprint |
| Research 1C branch existence | **UNKNOWN** | 1A/1B restored; 1C may be separate |
| Production deployment topology | **INFERRED** | Dev/CI focus evident |
| IBG ratification timeline | **DOCUMENTED** | Per `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` |

---

*Audit completed: 2026-05-24*  
*Coverage: 95%+ of referenced documentation*  
*Next audit trigger: IBG R1 ratification or first cross-repo integration Dev Order*
