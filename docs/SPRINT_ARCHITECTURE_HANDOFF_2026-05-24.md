# Sprint Architecture Handoff

**Sprint Window**: 2026-05-15 to 2026-05-24  
**Total Commits**: 66  
**Files Changed**: ~497  
**PRs Merged**: #17–#37  
**Version**: Sprint Checkpoint 2026-05-23

---

## 1. Executive Summary

This sprint consolidated the repository's runtime governance foundation across three major parallel tracks:

1. **Governance Enforcement** (PRs #17–#19): Unified policy runner, document inventory, and CI-blocking governance gate
2. **Runtime Boundary Program** (Phases 1A–2G): DXF lifecycle inventory, non-mutating guards, and caller-context contracts
3. **Runtime Capability Federation** (MRP-5M through MRP-5Y): Complete governed runtime spine with 72 passing tests

**Key Outcomes**:
- Governance gate is CI-enforced; authority-chain violations now block CI
- DXF compatibility layer fully inventoried with lifecycle guards on all router endpoints
- Runtime capability federation layer implemented with deterministic manifest generation
- Complexity reduction achieved (parse_dxf CC 50→19, run_manufacturing_checks CC 50→12)
- 11-test regression guard protects capability bypass vectors

**Unresolved Blockers**: None blocking. Deferred items documented as FOLLOW_UP.

**Architectural Direction**: The sprint establishes governance-first development. All DXF exports route through `dxf_compat.create_document()`. The runtime spine provides capability resolution gates before adapter execution. Future work builds on this foundation rather than bypassing it.

**Why This Matters**: Without this sprint, the repository had 50+ unguarded DXF save points, no capability federation, and no CI-enforced governance. A single malformed export or capability bypass could propagate silently. This sprint closes those vectors.

---

## 2. Sprint Timeline & Milestones

### 2026-05-20 (Day 1)

| Commit | Milestone |
|--------|-----------|
| `a9bb2fe2` | **Complexity Reduction PR #24**: parse_dxf CC 50→19, run_manufacturing_checks CC 50→12 |
| `ef954747` | Vectorizer technical debt audit documented |
| `f1e11d99` | Phase 0.5 semantic sandbox import gate (#26) |
| `f53bb479` | Tier A vectorizer modules relocated to vectorizer-sandbox (#27) |
| `13937525` | Safe remediation PR-1/2/3 and local dev layout (#28) |
| `261436ae` | Migrated sandbox folders removed + migration handoffs |

### 2026-05-21 (Day 2)

| Commit | Milestone |
|--------|-----------|
| `a73494d5` | Runtime Boundary Phase 1C/1D complete |
| `dc548428` | DXF save/write lifecycle guard plan (Phase 1E) |
| `2228a96e` | **DXF lifecycle guard implemented** (Phase 2A) — 33 unit tests |
| `bc075e79` | Guard status tracking in lifecycle matrix (Phase 2B) |
| `16587231` | Neck router guards added (Phase 2C) |
| `18779212` | Remaining router guards added (Phase 2D) |
| `774a6ff4` | Experimental drift session synthesis (Dev Order 72) |

### 2026-05-22 (Day 3)

| Commit | Milestone |
|--------|-----------|
| `b4c91a84` | Runtime service guards added (Phase 2F) |
| `4e7dd127` | Federation CI enforcement and drift baselines (Dev Order 7Y) |
| `6c74e3a1` | Governance baseline freeze and release readiness (Dev Order 7Z) |
| `671c4161` | Post-freeze expansion gate governance (8A) |
| `9ad75faf` | **PR #34 merged**: Runtime service DXF guards |

### 2026-05-23 (Day 4)

| Commit | Milestone |
|--------|-----------|
| `5b2a4dc4` | **Governed runtime spine** (MRP-5M through MRP-5V) |
| `fac9830a` | Runtime spine release verification (MRP-5X) |
| `0f386975` | Capability regression guard — 11 tests |
| `07cc00fa` | DxfWriter lifecycle context contract (Phase 2G) |
| `c2f0891c` | Complete governed runtime spine (MRP-5M through MRP-5Y) |
| `81764bb0` | **PR #35 merged**: Regression guard |
| `79ed2ec7` | **PR #36 merged**: DxfWriter assessment |
| `a5d3c1f7` | **PR #37 merged**: MRP-5X release verification consolidation |

### 2026-05-24 (Day 5)

| Commit | Milestone |
|--------|-----------|
| `2017aba9` | Governed review UX and queue routing (8C, 8D, 8E) |

**Dev Order 8C — Review UX Contracts**:
- ManufacturingReviewPanel with human_review_required=True, auto_approval_allowed=False invariants
- ProvenanceExplanationArtifact for artifact explanations
- ReviewAttentionPriority with score-based classification (critical≥0.85, high≥0.65, medium≥0.35)
- Registry for all 8C artifacts with clear_for_tests() helpers

**Dev Order 8D — Review UX CI Enforcement**:
- ReviewUXBaseline model with threshold fields
- ReviewUXCIEnforcementSummary with classification logic
- Baseline comparison infrastructure
- 68 unit tests

**Dev Order 8E — Review Queue Routing**:
- ReviewQueueItem with 5 model-enforced invariants
- ReviewDecisionRecord with decision-to-status mapping
- Review queue registry with computed-on-demand filtering
- ReviewQueueCISummary for CI classification
- 70+ unit tests

### Branch Activity

| Branch | Status | Purpose |
|--------|--------|---------|
| `main` | Active | Production trunk |
| `mrp-5x-runtime-capability-regression-guard` | Merged | Regression guard PR #35 |
| `runtime-boundary-phase-2g-dxf-writer-assessment` | Merged | DxfWriter contract PR #36 |
| `mrp-5x-release-verification-consolidation` | Merged | MRP-5X consolidation PR #37 |

---

## 3. Commit-Level Analysis

### Theme 1: Governance Enforcement (PRs #17–#19)

| Commit | Purpose | Significance |
|--------|---------|--------------|
| `d8bc9ade` | Unified governance runner + ontology validation (#17) | Establishes single policy execution path |
| `d3bda4fa` | Governance document inventory (#18) | Machine-parseable governance document index |
| `2c76aad8` | Promote governance gate to blocking mode (#19) | CI now fails on authority-chain violations |

**Files Modified**:
- `scripts/governance/check_all.py` — Unified policy runner
- `scripts/governance/build_governance_inventory.py` — Document inventory builder
- `tests/governance/test_build_governance_inventory.py` — Deterministic output tests

### Theme 2: Complexity Reduction (PR #24)

| Commit | Purpose | Impact |
|--------|---------|--------|
| `fb06decb` | Extract pure helpers from parse_dxf and run_manufacturing_checks | CC 50→19, CC 50→12 |
| `32d91800` | Add @safety_critical decorators to CAM G-code functions | Safety annotations |

**Files Modified**:
- `services/api/app/cam/inlay_import.py` — 6 extracted functions
- `services/api/app/cam/rosette_manufacturing.py` — 7 extracted functions

### Theme 3: DXF Lifecycle Guards (Phases 2A–2G)

| Commit | Purpose | Files Guarded |
|--------|---------|---------------|
| `2228a96e` | Implement DxfLifecycleGuard | `app/util/dxf_lifecycle_guard.py` |
| `16587231` | Neck router guards (Phase 2C) | 3 neck routers |
| `18779212` | Router guard batch (Phase 2D) | 3 additional routers |
| `b4c91a84` | Runtime service guards (Phase 2F) | `dxf_consolidator`, `layer_consolidator`, `unified_dxf_cleaner` |
| `07cc00fa` | DxfWriter caller-context contract | Documentation only |

**Architectural Pattern**: `assert_dxf_lifecycle_context()` called immediately before `doc.saveas()`. Validation-only; no mutation.

### Theme 4: Runtime Capability Federation (MRP-5V)

| Commit | Purpose | Tests |
|--------|---------|-------|
| `5b2a4dc4` | Implement runtime_capabilities package | 42 integration tests |
| `0f386975` | Capability regression guard | 11 invariant tests |
| `fac9830a` | Release verification | 19 verification tests |

**Package Created**: `app/cam/runtime_capabilities/`
- `contracts.py` — FederatedCapability, namespaced IDs
- `registry.py` — CapabilityRegistry with duplicate rejection
- `policies.py` — ExecutionPolicyFederation (5 policies)
- `resolution.py` — CapabilityResolver
- `manifest.py` — Deterministic manifest generation

---

## 4. Repository & File-Level Mapping

### Core Runtime Modules

| Path | Purpose | Dependencies |
|------|---------|--------------|
| `app/cam/runtime_capabilities/` | Capability federation layer | None (new root) |
| `app/cam/runtime_service/` | Certified runtime service | runtime_capabilities, runtime_admission |
| `app/cam/runtime_admission/` | Admission control gate | topology_validation |
| `app/cam/runtime_provenance/` | Lineage recording | runtime_service |
| `app/cam/runtime_manifest/` | Manifest generation | runtime_capabilities |
| `app/cam/topology_validation/` | Topology certification | None (new root) |

### Governance Scripts

| Path | Purpose | Owner |
|------|---------|-------|
| `scripts/governance/check_all.py` | Unified policy runner | CI pipeline |
| `scripts/governance/build_governance_inventory.py` | Document inventory | CI pipeline |
| `scripts/governance/validate_export_lifecycle_matrix.py` | Matrix validator | CI pipeline |
| `scripts/governance/audit_authority_chains.py` | Authority chain audit | Manual |

### DXF Lifecycle Components

| Path | Purpose | Guard Status |
|------|---------|--------------|
| `app/util/dxf_lifecycle_guard.py` | Lifecycle guard implementation | N/A (is guard) |
| `app/util/dxf_compat.py` | DXF compatibility layer | Upstream |
| `cam/dxf_writer.py` | Central DXF writer | REQUIRES_CALLER_CONTEXT |
| `cam/dxf_consolidator.py` | DXF consolidation | GUARD_ADDED |
| `cam/layer_consolidator.py` | Layer consolidation | GUARD_ADDED |
| `cam/unified_dxf_cleaner.py` | DXF cleanup | GUARD_ADDED |

### 8C/8D/8E Review UX & Queue Modules

| Path | Purpose | Tests |
|------|---------|-------|
| `app/cam/manufacturing_review_panel.py` | ManufacturingReviewPanel model | 8C |
| `app/cam/provenance_explanation.py` | ProvenanceExplanationArtifact model | 8C |
| `app/cam/review_attention_priority.py` | ReviewAttentionPriority model | 8C |
| `app/cam/review_ux_registry.py` | Registry for 8C artifacts | 8C |
| `app/cam/review_ux_baseline.py` | ReviewUXBaseline model | 8D |
| `app/cam/review_ux_ci_enforcement.py` | CI enforcement logic | 8D |
| `app/cam/review_queue_item.py` | ReviewQueueItem model | 8E |
| `app/cam/review_decision_record.py` | ReviewDecisionRecord model | 8E |
| `app/cam/review_queue_registry.py` | Queue/decision registry | 8E |
| `app/cam/review_queue_ci.py` | ReviewQueueCISummary | 8E |

### 8C/8D/8E Router Modules

| Path | Prefix | Endpoints |
|------|--------|-----------|
| `app/routers/cam/review_ux_router.py` | `/api/cam/review-ux` | panels, explanations, priorities |
| `app/routers/cam/review_ux_ci_router.py` | `/api/cam/review-ux/ci` | CI summary, baseline comparison |
| `app/routers/cam/review_queue_router.py` | `/api/cam/review-queue` | items, decisions, filters, CI |

### Test Files

| Path | Tests | Purpose |
|------|-------|---------|
| `tests/cam/test_runtime_spine_full_verification.py` | 19 | End-to-end spine verification |
| `tests/cam/test_runtime_capability_integration.py` | 42 | Capability federation |
| `tests/cam/test_runtime_capability_regression_guard.py` | 11 | Bypass regression guard |
| `tests/test_dxf_lifecycle_guard.py` | 33 | Lifecycle guard unit tests |
| `tests/cam/test_review_ux_ci_enforcement.py` | 68 | 8D CI enforcement tests |
| `tests/cam/test_review_queue_routing.py` | 70+ | 8E queue routing tests |

---

## 5. Schema & Data Model Documentation

### DxfLifecycleContext

```python
@dataclass
class DxfLifecycleContext:
    source_module: str           # e.g., "routers.neck.export"
    export_type: str             # e.g., "dxf-create-save"
    dxf_version: str             # e.g., "R2010", "R12"
    lifecycle_status: str        # e.g., "COMPAT_ONLY"
    runtime_callable: str        # e.g., "router_endpoint"
    authority_context: str       # e.g., "pipeline_stage"
    provenance_status: str       # e.g., "PENDING"
```

### FederatedCapability

```python
@dataclass
class FederatedCapability:
    capability_id: str           # e.g., "operation:nut_slot"
    namespace: CapabilityNamespace
    local_id: str
    version: str
    source_name: str
    display_name: str
    description: str
    governance_classification: GovernanceClassification
    enabled: bool
    deterministic: bool
    replay_safe: bool
    compatibility_tags: Set[str]
    required_tags: Set[str]
    domain_metadata: Dict
```

### CapabilityResolutionResult

```python
@dataclass
class CapabilityResolutionResult:
    status: ResolutionStatus      # RESOLVED, NOT_FOUND, DISABLED, etc.
    requested_capability_id: str
    resolved_capability: Optional[FederatedCapability]
    policy_decision: PolicyDecision
    rejection_reasons: List[str]
    compatibility_summary: CompatibilitySummary
    policies_evaluated: List[str]
```

### 8E ReviewQueueItem

```python
class ReviewQueueItem(BaseModel):
    queue_item_id: str                          # rqi-{uuid12}
    panel_id: Optional[str]                     # Link to 8C panel
    priority_id: Optional[str]                  # Link to 8C priority
    provenance_explanation_id: Optional[str]    # Link to 8C explanation

    source_layer: ReviewSourceLayer             # 8 options
    review_priority: ReviewPriority             # low/medium/high/critical
    review_status: ReviewStatus                 # 6 states

    assigned_role: Optional[str]                # Human reviewer role
    review_reason: str                          # Why review needed
    blocking_issues: List[str]
    warnings: List[str]

    # 8E INVARIANTS (model-enforced, cannot be True)
    human_review_required: bool = True          # Always True
    decision_authorized: bool = False           # Always False
    implementation_authorized: bool = False     # Always False
    execution_authorized: bool = False          # Always False
    machine_output_allowed: bool = False        # Always False

    deterministic_queue_hash: str
```

**ReviewSourceLayer options:** manufacturing_cognition, geometry_authority, strategy_export, fixture_topology, manufacturing_replay, federation, review_ux, post_freeze

**ReviewStatus states:** queued → in_review → needs_more_evidence → reviewed | deferred | rejected

### 8E ReviewDecisionRecord

```python
class ReviewDecisionRecord(BaseModel):
    decision_id: str                            # rdr-{uuid12}
    queue_item_id: str                          # Parent queue item

    decision_type: DecisionType                 # 5 types
    decision_rationale: str
    reviewer_ref: Optional[str]
    resulting_review_status: ReviewStatus

    # 8E INVARIANTS
    human_review_recorded: bool = True          # Always True
    implementation_authorized: bool = False     # Always False
    execution_authorized: bool = False          # Always False
    machine_output_allowed: bool = False        # Always False

    deterministic_decision_hash: str
```

**Decision-to-Status Mapping:**
| DecisionType | Resulting Status |
|-------------|------------------|
| acknowledge | in_review |
| request_more_evidence | needs_more_evidence |
| defer | deferred |
| reject | rejected |
| mark_reviewed | reviewed |

### 8E Invariant Enforcement Pattern

All governance models use Pydantic `@model_validator(mode="after")`:

```python
@model_validator(mode="after")
def enforce_8e_invariants(self) -> "ReviewQueueItem":
    if self.implementation_authorized:
        raise ValueError("8E invariant violation: implementation_authorized must be False")
    if self.execution_authorized:
        raise ValueError("8E invariant violation: execution_authorized must be False")
    if self.machine_output_allowed:
        raise ValueError("8E invariant violation: machine_output_allowed must be False")
    return self
```

### Schema Evolution

| Schema | Before Sprint | After Sprint |
|--------|---------------|--------------|
| DxfLifecycleContext | Did not exist | Created |
| FederatedCapability | Did not exist | Created |
| CertifiedRuntimeRequest | No capability_id | Added capability_id, is_replay_mode |
| ServiceExecutionStatus | No CAPABILITY_REJECTED | Added CAPABILITY_REJECTED |
| ReviewQueueItem | Did not exist | Created (8E) |
| ReviewDecisionRecord | Did not exist | Created (8E) |
| ReviewQueueCISummary | Did not exist | Created (8E) |
| ManufacturingReviewPanel | Did not exist | Created (8C) |
| ReviewAttentionPriority | Did not exist | Created (8C) |
| ReviewUXBaseline | Did not exist | Created (8D) |

---

## 6. Build & Development Environment

### Package Manager

```bash
# Python dependencies
pip install -r services/api/requirements.txt

# Frontend dependencies
cd packages/client && npm install
```

### Test Commands

```bash
# Full test suite
cd services/api && pytest

# Governance checks
python scripts/governance/check_all.py --tier ci

# Runtime spine verification
pytest tests/cam/test_runtime_spine_full_verification.py -v

# Capability regression guard
pytest tests/cam/test_runtime_capability_regression_guard.py -q

# DXF lifecycle guard tests
pytest tests/test_dxf_lifecycle_guard.py -v
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PYTEST_COV_FAIL_UNDER` | Coverage threshold | 20 |
| `GOVERNANCE_TIER` | Check tier (precommit/ci/nightly) | ci |

### CI Configuration

Governance is CI-enforced via `scripts/governance/check_all.py`:

```bash
# Pre-commit tier (<2s each)
python scripts/governance/check_all.py --tier precommit

# CI tier (<30s each, default)
python scripts/governance/check_all.py --tier ci

# Nightly tier (full init required)
python scripts/governance/check_all.py --tier nightly
```

---

## 7. Scripts, Utilities, and Automation

### Governance Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `check_all.py` | Unified policy runner | --tier flag | Exit code + report |
| `build_governance_inventory.py` | Build document inventory | docs/governance/*.md | JSON inventory |
| `validate_export_lifecycle_matrix.py` | Validate lifecycle matrix | EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md | Exit code |
| `audit_authority_chains.py` | Audit authority chains | Source files | Authority report |

### Runtime Provenance Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `audit_runtime_capabilities.py` | Audit capability registry | None | Capability report |
| `verify_runtime_spine_release.py` | Verify release readiness | None | 19-check report |
| `generate_runtime_manifest.py` | Generate capability manifest | None | JSON manifest |
| `execute_replay_bundle.py` | Execute replay bundle | Bundle path | Replay result |
| `compare_replay_artifact.py` | Compare artifacts | Two artifact paths | Diff report |

### Operational Risks

| Script | Risk | Mitigation |
|--------|------|------------|
| `execute_replay_bundle.py` | Executes runtime operations | Requires certified topology |
| `generate_runtime_manifest.py` | Produces deterministic manifest | Content hash validation |

---

## 8. Architectural Changes During the Sprint

### 8E Governance Stack Position

```
7Z (Governance Baseline Freeze)
    ↓
8A (Post-Freeze Expansion Gate)
    ↓
8C (Review UX Contracts) ← Creates reviewable artifacts
    ↓
8D (CI Enforcement) ← Validates against baselines
    ↓
8E (Review Queue Routing) ← Routes human attention
```

**8E Core Principle:**
```
Review routing may organize human decisions.
Review routing may not make human decisions.
```

8E routes human attention. It does NOT: authorize implementation, authorize execution, invoke serializers, mutate geometry, generate machine output, auto-approve anything.

### Systems Added

| System | Purpose | Entry Point |
|--------|---------|-------------|
| DxfLifecycleGuard | Validation-only DXF lifecycle enforcement | `app/util/dxf_lifecycle_guard.py` |
| CapabilityRegistry | Federated capability registration | `app/cam/runtime_capabilities/registry.py` |
| CapabilityResolver | Capability resolution with policy checks | `app/cam/runtime_capabilities/resolution.py` |
| ExecutionPolicyFederation | Policy evaluation layer | `app/cam/runtime_capabilities/policies.py` |
| ReviewQueueRegistry | Queue item/decision storage | `app/cam/review_queue_registry.py` |
| ReviewUXRegistry | Panel/explanation/priority storage | `app/cam/review_ux_registry.py` |

### Systems Removed

| System | Reason | Migration |
|--------|--------|-----------|
| `vectorizer_phase2.py` | Relocated to vectorizer-sandbox | External repo |
| `cognitive_extraction_engine.py` | Tier A relocation | vectorizer-sandbox |
| `extract_body_grid_v*.py` | Superseded versions | vectorizer-sandbox |

### Refactors

| Module | Change | Complexity Reduction |
|--------|--------|---------------------|
| `inlay_import.py` | Extract 6 pure helpers | CC 50 → 19 |
| `rosette_manufacturing.py` | Extract 7 pure helpers | CC 50 → 12 |

### Subsystem Boundaries

```
Before:
  DXF Export → [50+ unguarded save points] → File

After:
  DXF Export → dxf_compat.create_document()
            → DxfLifecycleGuard.assert()
            → doc.saveas()
            → File
```

### Technical Debt Introduced

| Item | Severity | Notes |
|------|----------|-------|
| DxfWriter REQUIRES_CALLER_CONTEXT | Low | Callers must supply context; no fake guards |
| MRP-5U handoff missing | Low | MRP-5V implemented missing functionality |
| Service/replay namespaces empty | Low | Structure exists; not populated |

### Technical Debt Reduced

| Item | Before | After |
|------|--------|-------|
| parse_dxf complexity | CC 50 | CC 19 |
| run_manufacturing_checks complexity | CC 50 | CC 12 |
| Unguarded DXF exports | 50+ | 0 router endpoints |
| Capability bypass vectors | Open | 11 tests guarding |

---

## 9. Testing & Validation

### Test Results Summary

| Suite | Tests | Status |
|-------|-------|--------|
| Runtime spine verification | 19 | PASS |
| Capability integration | 42 | PASS |
| Capability regression guard | 11 | PASS |
| DXF lifecycle guard | 33 | PASS |
| Review UX CI enforcement (8D) | 68 | PASS |
| Review queue routing (8E) | 70+ | PASS |
| Full API test suite | 223+ | PASS |

### Validation Methods

| Method | Purpose | Frequency |
|--------|---------|-----------|
| Capability manifest hash | Determinism verification | Every build |
| Policy evaluation determinism | Policy consistency | Every build |
| Source registry immutability | Federation safety | Every build |
| Guard status tracking | Lifecycle coverage | CI |

### Unresolved Test Gaps

| Gap | Severity | Mitigation |
|-----|----------|------------|
| Deep geometry compatibility | Low | Tag-based compat only |
| Full behavioral execution | Medium | Contracts tested, not behavior |
| Dynamic capability loading | Low | Static registration only |

---

## 10. Risks, Fragility, and Technical Debt

### Critical Risks (None Active)

All CRITICAL findings from technical debt audit resolved or classified as archive/test noise.

### High Priority Debt

| Item | Location | Impact |
|------|----------|--------|
| DxfWriter caller-context rollout | `cam/dxf_writer.py` | Central point affects 12+ paths |
| Missing handoffs (5C, 5D, 5I-5L, 5U, 5W) | docs/handoffs/ | Documentation gaps |

### Medium Priority Debt

| Item | Location | Impact |
|------|----------|--------|
| CI enforcement of manifest changes | CI pipeline | Manifest drift undetected |
| Service/replay namespace population | runtime_capabilities | Empty namespaces |
| Dynamic capability loading | runtime_capabilities | Static registration only |

### Low Priority Debt

| Item | Location | Impact |
|------|----------|--------|
| Deep geometry compatibility | runtime_capabilities | Tag-based only |
| Production version (1.0.0) | runtime_capabilities | Currently 0.1.0 |
| Photo-vectorizer cleanup | services/photo-vectorizer | Under evaluation |
| 8E in-memory registries | review_queue_registry.py | Restarts lose queue state |
| 8E shallow panel lookup | build_review_queue_from_panel | No deep provenance query |
| 8E no user integration | assigned_role field | String only, not user accounts |
| 8E stale detection placeholder | detect_stale_review_items | Requires created_at timestamps |

### Architectural Bottlenecks

| Bottleneck | Impact | Mitigation Path |
|------------|--------|-----------------|
| `dxf_writer.py` central point | All DXF exports flow through | Caller-context contract |
| Static capability registration | No runtime capability addition | Future: dynamic loading |

---

## 11. Knowledge Preservation Notes

### Assumptions Made

1. **Lifecycle guards are validation-only**: No mutation, no logging, no side effects. This was intentional to establish trust before adding provenance attachment.

2. **Capability IDs are namespaced**: Format is `{namespace}:{local_id}`. This prevents collision across domains.

3. **Source registries are immutable**: Federation wraps but never mutates domain-local registries.

4. **DxfWriter cannot be internally guarded**: It doesn't know caller identity. Callers must supply context.

### Inferred Architecture

The runtime spine follows a strict gate order:
```
Validation → Admission → Capability → Execution → Provenance
```

Each gate can reject; later gates cannot override earlier rejections.

### Tribal Knowledge

1. **R12 vs R2000**: Use R12 for maximum compatibility (hobbyist tier), R2000 for CAM workflows (professional tier).

2. **Guard placement**: `assert_dxf_lifecycle_context()` goes immediately before `saveas()`, not at function entry.

3. **Capability resolution backward compatibility**: If `request.capability_id` is None, resolution is skipped.

### Non-Obvious Decisions

| Decision | Rationale |
|----------|-----------|
| No fake guards | A guard with "unknown" context is worse than no guard — creates false coverage |
| Validation-only first | Establish trust before provenance mutation |
| 11 regression tests | Focused invariants, not comprehensive coverage |
| Missing handoffs as OBSERVATION | Don't assume intentional skip; document gaps |
| 8E model-enforced invariants | Prevents accidental authorization at construction time |
| 8E decision-to-status mapping fixed | Ensures audit trail consistency |
| 8E shallow panel lookup | Avoids circular dependencies between registries |
| 8E computed-on-demand filtering | Avoids stale secondary indexes, simpler code |
| 8E no direct PATCH endpoint | Status changes only via decisions (audit trail) |

---

## 12. Reconstruction Readiness Assessment

### Reconstruction Score: 8.5/10

**Strengths**:
- Complete governance document inventory
- DXF lifecycle fully inventoried with machine-parseable matrix
- Runtime spine documented with 72 tests
- Complexity reduction committed with clear before/after metrics

**Gaps**:
- Missing handoffs (5C, 5D, 5I-5L, 5U, 5W) — not blocking
- DxfWriter caller-context not yet rolled out — documented
- No CI enforcement of manifest changes — follow-up item

### Recommended Reconstruction Sequence

1. **Start with governance**: `scripts/governance/check_all.py --list` shows all checks
2. **Review lifecycle matrix**: `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`
3. **Run verification**: `scripts/runtime_provenance/verify_runtime_spine_release.py`
4. **Trace capability flow**: `app/cam/runtime_capabilities/__init__.py` exports

### Stabilization Priorities

| Priority | Action |
|----------|--------|
| 1 | Keep regression guard green (11 tests) |
| 2 | Keep lifecycle matrix validator passing |
| 3 | Keep governance gate CI-enforced |
| 4 | Document any new DXF save points in matrix |

### Modularization Opportunities

| Opportunity | Complexity | Value |
|-------------|------------|-------|
| Extract DxfWriter caller-context interface | Medium | High — enables internal guards |
| Add CI manifest drift detection | Low | Medium — catches capability changes |
| Populate service/replay namespaces | Low | Low — structure exists |

---

## 13. Recommended Next Sprint Actions

### Immediate (Next 1-2 Days)

| Action | Owner | Priority |
|--------|-------|----------|
| Monitor regression guard in CI | Runtime team | P0 |
| Document any new DXF exports | DXF team | P0 |
| Run nightly governance tier | CI | P1 |

### Cleanup (This Week)

| Action | Priority | Effort |
|--------|----------|--------|
| Add CI manifest drift detection | Medium | Low |
| Document missing handoffs as OBSERVATION | Low | Low |
| Review photo-vectorizer status | Low | Low |

### Refactor Opportunities

| Opportunity | Priority | Effort |
|-------------|----------|--------|
| DxfWriter caller-context interface | Medium | Medium |
| Service namespace population | Low | Low |
| Dynamic capability loading | Low | High |

### Architecture Hardening

| Action | Priority | Rationale |
|--------|----------|-----------|
| Keep lifecycle guards validation-only | P0 | Trust before mutation |
| Expand regression guard to new capabilities | P1 | Prevent bypass vectors |
| Add deep geometry compatibility | Low | Tag-based is sufficient for now |

---

## Appendix A: Commit Reference

| Hash | Date | Type | Summary |
|------|------|------|---------|
| `2017aba9` | 2026-05-24 | feat | Governed review UX and queue routing (8C, 8D, 8E) |
| `a5d3c1f7` | 2026-05-23 | merge | PR #37: MRP-5X release verification consolidation |
| `8ddd8897` | 2026-05-23 | docs | Consolidate MRP-5X release verification |
| `c2f0891c` | 2026-05-23 | feat | Complete governed runtime spine (MRP-5M through MRP-5Y) |
| `0f386975` | 2026-05-23 | test | Capability regression guard (MRP-5X) |
| `5b2a4dc4` | 2026-05-23 | feat | Implement governed runtime spine (MRP-5M through MRP-5V) |
| `b4c91a84` | 2026-05-22 | chore | DXF lifecycle guards to runtime services |
| `6c74e3a1` | 2026-05-22 | feat | Governance baseline freeze (Dev Order 7Z) |
| `4e7dd127` | 2026-05-22 | feat | Federation CI enforcement (Dev Order 7Y) |
| `18779212` | 2026-05-21 | feat | DXF lifecycle guards to remaining routers (Phase 2D) |
| `16587231` | 2026-05-21 | feat | DXF lifecycle guards to neck routers (Phase 2C) |
| `2228a96e` | 2026-05-21 | feat | Implement DXF lifecycle guard (Phase 2A) |
| `a73494d5` | 2026-05-21 | feat | Runtime Boundary Phase 1C/1D complete |
| `a9bb2fe2` | 2026-05-20 | fix | Safety decorators and complexity reduction (#24) |
| `2c76aad8` | 2026-05-19 | feat | Promote governance gate to blocking mode (#19) |
| `d3bda4fa` | 2026-05-19 | feat | Governance document inventory (#18) |
| `d8bc9ade` | 2026-05-19 | feat | Unified governance runner (#17) |

---

## Appendix B: File Inventory

### Created This Sprint

| Path | Purpose |
|------|---------|
| `app/util/dxf_lifecycle_guard.py` | Lifecycle guard implementation |
| `app/cam/runtime_capabilities/` | Capability federation package (8 files) |
| `scripts/runtime_provenance/` | Runtime utilities (9 files) |
| `tests/cam/test_runtime_capability_regression_guard.py` | Regression guard tests |
| `tests/cam/test_runtime_spine_full_verification.py` | Spine verification tests |
| `docs/governance/RUNTIME_CAPABILITY_REGRESSION_GUARD.md` | Guard documentation |
| `docs/governance/DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Lifecycle guard plan |
| `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Lifecycle matrix |
| `app/cam/manufacturing_review_panel.py` | 8C ManufacturingReviewPanel model |
| `app/cam/provenance_explanation.py` | 8C ProvenanceExplanationArtifact model |
| `app/cam/review_attention_priority.py` | 8C ReviewAttentionPriority model |
| `app/cam/review_ux_registry.py` | 8C registry for panels/explanations/priorities |
| `app/cam/review_ux_baseline.py` | 8D ReviewUXBaseline model |
| `app/cam/review_ux_ci_enforcement.py` | 8D CI enforcement logic |
| `app/cam/review_queue_item.py` | 8E ReviewQueueItem model |
| `app/cam/review_decision_record.py` | 8E ReviewDecisionRecord model |
| `app/cam/review_queue_registry.py` | 8E queue/decision registry |
| `app/cam/review_queue_ci.py` | 8E ReviewQueueCISummary model |
| `app/routers/cam/review_ux_router.py` | 8C REST endpoints |
| `app/routers/cam/review_ux_ci_router.py` | 8D REST endpoints |
| `app/routers/cam/review_queue_router.py` | 8E REST endpoints |
| `tests/cam/test_review_ux_ci_enforcement.py` | 8D 68 tests |
| `tests/cam/test_review_queue_routing.py` | 8E 70+ tests |
| `docs/handoffs/CAM_8E_REVIEW_QUEUE_ROUTING_HANDOFF.md` | 8E handoff document |

### Modified This Sprint

| Path | Change |
|------|--------|
| `routers/neck/neck_profile_export.py` | Added lifecycle guard |
| `routers/neck/headstock_transition_export.py` | Added lifecycle guard |
| `routers/neck/export.py` | Added lifecycle guard |
| `routers/headstock/dxf_export.py` | Added lifecycle guard |
| `routers/export/curve_export_router.py` | Added lifecycle guard |
| `routers/dxf_preflight_router.py` | Added lifecycle guard |
| `cam/dxf_consolidator.py` | Added lifecycle guard |
| `cam/layer_consolidator.py` | Added lifecycle guard |
| `cam/unified_dxf_cleaner.py` | Added lifecycle guard |
| `cam/inlay_import.py` | Complexity reduction |
| `cam/rosette_manufacturing.py` | Complexity reduction |
| `app/router_registry/manifests/cam_manifest.py` | Added 8C, 8D, 8E router registrations |

---

## Appendix C: 8E API Reference

### Queue Item Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cam/review-queue/items` | Create queue item |
| GET | `/api/cam/review-queue/items` | List all items (priority sorted) |
| GET | `/api/cam/review-queue/items/{id}` | Get item by ID |
| POST | `/api/cam/review-queue/items/from-panel/{panel_id}` | Create from 8C panel |

### Decision Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cam/review-queue/decisions` | Record decision (updates item status) |
| GET | `/api/cam/review-queue/items/{id}/decisions` | Get decision history |

### Filter Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cam/review-queue/by-status/{status}` | Filter by status |
| GET | `/api/cam/review-queue/by-priority/{priority}` | Filter by priority |

### CI Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cam/review-queue/ci` | Get CI summary (PASS/WARN/FAIL) |

### CI Classification Logic

**FAIL conditions:**
- Any authorization violation (decision_authorized, implementation_authorized, execution_authorized, machine_output_allowed = True)

**WARN conditions:**
- critical_open_count > 0
- high_open_count > 0  
- missing_assignment_count > 0
- needs_more_evidence_count > 0
- blocking_issue_count > 0

**PASS:**
- No failures, no warnings

---

*Generated: 2026-05-24*  
*Sprint Architecture Handoff v1.1*  
*Updated with 8C/8D/8E comprehensive coverage*
