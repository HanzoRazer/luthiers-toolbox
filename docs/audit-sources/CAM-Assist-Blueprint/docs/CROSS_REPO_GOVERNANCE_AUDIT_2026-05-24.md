# Cross-Repository Governance Audit

**Audit Date**: 2026-05-24  
**Scope**: CAM-Assist-Blueprint, luthiers-toolbox, tap_tone_pi  
**Sprint Window**: 2026-05-14 to 2026-05-24  
**Audit Type**: Deep architectural reconstruction and convergence assessment

---

## 1. Executive Summary

This audit examines three repositories forming a distributed lutherie manufacturing intelligence platform. Each repository maintains strong internal governance but cross-repo integration remains fragmented.

### Ecosystem Overview

| Repository | Domain | Sprint State | Tests | Governance Maturity |
|------------|--------|--------------|-------|---------------------|
| **CAM-Assist-Blueprint** | Strategy intent packaging | CAM-A0–A12 complete | 236 | 8.0/10 |
| **luthiers-toolbox** | Runtime spine, geometry authority | MRP-5M–6A complete | 466+ | 8.5/10 |
| **tap_tone_pi** | Acoustic measurement | DO-78, DO-81 complete | 2,596 | 9.2/10 |

### Key Findings

1. **Philosophical alignment: STRONG** — All repos enforce human authority, non-execution defaults, fail-closed validation
2. **Vocabulary alignment: WEAK** — Three parallel authority enums, incompatible confidence types
3. **Schema interoperability: NONE** — No shared registry, incompatible ID formats, no `$id` namespaces
4. **Integration path: UNDEFINED** — No API contracts between repos, no cross-repo tests

### Critical Blockers

| Blocker | Repository | Risk Level |
|---------|------------|------------|
| 27 unpushed commits | tap_tone_pi | P0 — Reconstruction risk |
| IBG BLOCKED_PROVENANCE (5 DXF points) | luthiers-toolbox | P0 — Authority laundering risk |
| Three parallel review queue implementations | All | P1 — Workflow fragmentation |
| No cross-repo contract tests | All | P1 — Silent integration failures |

### Convergence Score: 5.5/10

Philosophically aligned, operationally fragmented. Convergence requires vocabulary normalization, schema registry, and integration contracts before runtime coupling.

---

## 2. Technical Findings Report

### 2.1 CAM-Assist-Blueprint

**Purpose**: Non-execution strategy packaging for CNC lutherie workflows

**Sprint Accomplishments (A0–A12)**:
- Complete pipeline: validate → review → manifest → assemble → inspect → index → archive → validate → stage → queue → decision
- 11 CLI scripts with consistent patterns
- 3 JSON schemas (strategy, manifest, review_decision_record)
- 236 tests, all passing

**Authority Model**:
```
Strategy:        execution_authority_claim = false
Manifest:        non_execution_declaration = true
                 execution_authority_claim = false
                 requires_human_review = true
Review Decision: does_not_authorize_machine_execution = true
                 requires_downstream_cam_verification = true
                 human_review_recorded = true
```

**Key Files**:
- `schemas/strategy.schema.json`
- `schemas/strategy_package_manifest.schema.json`
- `schemas/review_decision_record.schema.json`
- `scripts/record_review_decision.py` (A12)

**Integration Gap**: No defined interface to luthiers-toolbox capability federation

---

### 2.2 luthiers-toolbox

**Purpose**: Runtime spine, geometry authority, DXF lifecycle management

**Sprint Accomplishments (MRP-5M–6A)**:
- CI-blocking governance gate (`scripts/governance/check_all.py`)
- DXF lifecycle classification matrix (6 statuses, 5 Phase 2A+ guards)
- Runtime capability federation (72 tests, deterministic manifest)
- 8E review queue with 5 Pydantic-enforced invariants
- Export lifecycle orchestrator (gate order: Validation → Admission → Capability → Execution → Provenance)

**Authority Model**:
```python
class AuthorityState(Enum):
    SANDBOX_EXPERIMENTAL = "sandbox_experimental"
    ADVISORY_CANDIDATE = "advisory_candidate"
    SEMANTIC_INTERPRETATION = "semantic_interpretation"
    DERIVED_TOPOLOGY = "derived_topology"
    CANONICAL_GEOMETRY = "canonical_geometry"
    HUMAN_REVIEWED = "human_reviewed"
    APPROVED_FOR_GENERATION = "approved_for_generation"
    REJECTED = "rejected"
    ARCHIVED_SUPERSEDED = "archived_superseded"
```

**8E Review Queue Invariants** (model-enforced):
```python
human_review_required: Literal[True] = True
decision_authorized: Literal[False] = False
implementation_authorized: Literal[False] = False
execution_authorized: Literal[False] = False
machine_output_allowed: Literal[False] = False
```

**Key Files**:
- `services/api/app/governance/authority_state.py`
- `services/api/app/governance/confidence_declaration.py`
- `services/api/app/cam/review_queue_item.py`
- `docs/governance/EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`

**Blocked Paths**: 5 IBG DXF save points in `BLOCKED_PROVENANCE` awaiting ratification

---

### 2.3 tap_tone_pi

**Purpose**: Acoustic measurement instrumentation (capture, not interpretation)

**Sprint Accomplishments**:
- Constitutional ADRs (0010, 0011, 0012)
- AGE Constitutional Contract
- Epistemic Status Matrix (7 states, forbidden transitions)
- Agentic contracts layer
- 2,596 tests (139 new this sprint)
- Net code reduction: -1,593 lines

**Authority Model (ADR-0010/0011)**:

| Authority Class | May Establish Truth? | May Enter Export? |
|-----------------|---------------------|-------------------|
| MEASUREMENT | Yes | Yes |
| PROVENANCE | Yes (process) | Yes |
| DECISION SUPPORT | No | No |
| INTERPRETIVE | No | No |

**Epistemic Status Taxonomy (ADR-0012)**:
```
Observed → Derived → Estimated → Predicted
                  ↓
              Heuristic (non-authoritative)
```

**Forbidden Transitions**:
- Derived cannot become Observed
- Predicted cannot become Derived
- Heuristic cannot become Derived

**Constitutional Enforcement**:
- `ci/check_guidance_language.py` — AST-based forbidden term detection
- Forbidden phrases: "detected as truth", "must fix", "optimal", "cause is"

**Key Files**:
- `docs/ADR-0010-guidance-authority-boundary.md`
- `docs/ADR-0011-measurement-authority.md`
- `docs/ADR-0012-epistemic-status-taxonomy.md`
- `tap_tone_pi/agentic/contracts/advisory_authority.py`

---

## 3. Governance Compliance Assessment

### 3.1 Shared Governance Principles (Aligned)

All repositories enforce these invariants:

| Principle | CAM-Assist | luthiers-toolbox | tap_tone_pi |
|-----------|------------|------------------|-------------|
| Human authority preserved | ✓ | ✓ | ✓ |
| Non-execution defaults | ✓ | ✓ | ✓ |
| Fail-closed validation | ✓ | ✓ | ✓ |
| Provenance tracking | ✓ | ✓ | ✓ |
| Confidence ≠ approval | ✓ | ✓ | ✓ |
| Advisory ≠ authority | ✓ | ✓ | ✓ |

### 3.2 Vocabulary Divergence (Critical)

| Concept | CAM-Assist | luthiers-toolbox | tap_tone_pi |
|---------|------------|------------------|-------------|
| Authority enum | N/A (boolean flags) | `AuthorityState` (9 values) | `AuthorityClass` (4 values) |
| Confidence type | N/A | `ConfidenceType` (6 values) | `ConfidenceDomain` (5 values) |
| Epistemic status | N/A | N/A | `EpistemicStatus` (7 values) |
| Review decision | `decision` field | `DecisionType` enum | N/A |

**Risk**: Authority laundering through vocabulary mapping ambiguity

### 3.3 Schema Divergence (Critical)

| Issue | Impact |
|-------|--------|
| No shared `$id` namespace | Cannot validate cross-repo references |
| Incompatible ID formats | CAM uses `operation:spec_id`, toolbox uses UUIDs |
| No schema registry | Schemas duplicated, drift inevitable |
| Version fields present but no migration logic | Breaking changes will fail silently |

### 3.4 Review Queue Fragmentation (High)

Three parallel implementations:

| Implementation | Location | Status |
|----------------|----------|--------|
| CAM-A11/A12 | `scripts/index_staged_packages.py`, `record_review_decision.py` | Complete, file-based |
| 8E Review Queue | `app/cam/review_queue_item.py` | Complete, in-memory |
| IBG Workflow 1A | luthiers-toolbox | Blocked on provenance |

**Risk**: Operators must learn three different review workflows

---

## 4. Architectural Risk Assessment

### 4.1 P0 Risks (Immediate Action Required)

| Risk | Repository | Impact | Mitigation |
|------|------------|--------|------------|
| 27 unpushed commits | tap_tone_pi | Total reconstruction loss if local disk fails | Push immediately |
| IBG BLOCKED_PROVENANCE | luthiers-toolbox | Cannot export geometry from vectorizer paths | Phase R1 ratification session |
| No cross-repo tests | All | Silent integration failures | Contract test suite |

### 4.2 P1 Risks (Sprint-Level)

| Risk | Repository | Impact | Mitigation |
|------|------------|--------|------------|
| Vocabulary collision | All | Authority laundering, wrong decisions | Crosswalk ratification |
| Schema drift | All | Breaking integrations | Shared registry |
| Review queue fragmentation | All | Operator confusion | Unified review model |
| Missing handoffs | luthiers-toolbox | Reconstruction gaps | Document MRP-5C, 5D, 5I-5L |

### 4.3 P2 Risks (Quarter-Level)

| Risk | Repository | Impact | Mitigation |
|------|------------|--------|------------|
| No integration API | All | Manual copy-paste integration | Define CAM→toolbox contract |
| Ephemeral 8E state | luthiers-toolbox | Queue state lost on restart | Persist to database |
| Large archive handling | CAM-Assist | Unknown behavior >100MB | Load testing |
| PyQt6 test skips | tap_tone_pi | UI boundary coverage gap | Mock or install dependency |

---

## 5. Sprint Convergence Roadmap

### Phase 0: Stabilization (Immediate — 24 hours)

| Task | Owner | Deliverable |
|------|-------|-------------|
| Push 27 commits to origin | tap_tone_pi | Remote backup |
| Document MRP-5C, 5D, 5I-5L | luthiers-toolbox | Handoff completeness |
| Merge CAM-A12 to main | CAM-Assist | Sprint closure |

### Phase 1: Vocabulary Convergence (Week 1)

| Task | Deliverable |
|------|-------------|
| Ratify CROSS_REPO_AUTHORITY_CROSSWALK.md | Canonical mapping document |
| Define shared authority enum subset | Interop vocabulary |
| Align confidence/epistemic naming | No collision in merged context |
| Add vocabulary CI checks | Drift prevention |

### Phase 2: Schema Normalization (Week 2)

| Task | Deliverable |
|------|-------------|
| Define shared `$id` namespace (e.g., `https://lutherie.dev/schemas/`) | URI authority |
| Extract common authority schema | `authority.schema.json` |
| Add `$ref` to existing schemas | Deduplication |
| Create shared schema validation CI | Cross-repo enforcement |

### Phase 3: Contract Boundaries (Week 3)

| Task | Deliverable |
|------|-------------|
| Define CAM → luthiers-toolbox integration API | `cam_import_contract.schema.json` |
| Define tap_tone → luthiers-toolbox measurement API | `measurement_import_contract.schema.json` |
| Add contract tests | Cross-repo CI |
| Document integration sequence | Integration runbook |

### Phase 4: Review Queue Unification (Week 4)

| Task | Deliverable |
|------|-------------|
| Design unified review queue model | Shared Pydantic model |
| Migrate CAM-A11/A12 to shared model | Backward-compatible |
| Migrate 8E queue to shared model | Persistence layer |
| Add queue federation API | Cross-repo queue visibility |

### Phase 5: IBG Provenance Ratification (Month 2)

| Task | Deliverable |
|------|-------------|
| Phase R1 governance session | Ratification decision |
| Define IBG provenance model | `ibg_provenance.schema.json` |
| Unblock 5 DXF save points | Production geometry export |
| Add provenance CI guards | Authority chain enforcement |

### Phase 6: Runtime Integration (Month 3+)

| Task | Deliverable |
|------|-------------|
| CAM package import into capability federation | Live integration |
| Measurement data import pipeline | Tap tone → toolbox |
| End-to-end integration tests | Full pipeline validation |
| Operator training | Unified workflow |

---

## 6. Recommended Immediate Actions

### Today (P0)

1. **tap_tone_pi**: `git push origin main` — 27 commits at risk
2. **CAM-Assist-Blueprint**: Merge CAM-A12 PR if not merged
3. **All repos**: Verify CI passing on main branches

### This Week (P1)

1. **luthiers-toolbox**: Document missing MRP handoffs (5C, 5D, 5I-5L, 5U, 5W)
2. **All repos**: Review and ratify CROSS_REPO_AUTHORITY_CROSSWALK.md
3. **CAM-Assist-Blueprint**: Define `package_manifest_id` → capability federation mapping

### Next Week (P2)

1. **All repos**: Create shared-schemas repository or directory
2. **luthiers-toolbox**: Schedule IBG provenance ratification (Phase R1)
3. **tap_tone_pi**: Enable strict guidance language guard (fix 13 findings)

---

## 7. Long-Term Stabilization Recommendations

### 7.1 Governance Infrastructure

| Recommendation | Rationale |
|----------------|-----------|
| Shared schema registry | Single source of truth for contracts |
| Cross-repo CI matrix | Catch integration breaks before merge |
| Unified ADR format | Consistent governance documentation |
| Quarterly governance review | Prevent drift accumulation |

### 7.2 Integration Architecture

| Recommendation | Rationale |
|----------------|-----------|
| Event-driven integration | Loose coupling, async processing |
| Capability-based routing | CAM packages → capability federation |
| Unified review queue | Single operator workflow |
| Audit trail federation | Cross-repo decision visibility |

### 7.3 Documentation Standards

| Recommendation | Rationale |
|----------------|-----------|
| Timestamped handoff files | No overwriting, full history |
| Per-sprint architecture snapshot | Reconstruction safety |
| Cross-repo convergence reports | Drift visibility |
| Integration runbooks | Operator self-service |

### 7.4 Testing Strategy

| Recommendation | Rationale |
|----------------|-----------|
| Contract tests per integration point | Interface stability |
| Cross-repo integration test suite | End-to-end validation |
| Load testing for archives >100MB | Scale limits known |
| Chaos testing for queue persistence | Reliability verification |

---

## 8. Assumptions and Unknowns

### Assumptions

1. All three repos will remain under same ownership/governance authority
2. Vocabulary convergence is achievable without breaking changes
3. IBG provenance can be ratified within 30 days
4. No fourth repository will be added to ecosystem in near term

### Unknowns

1. Exact mapping between CAM `package_manifest_id` and toolbox capability IDs
2. Whether 8E queue should persist to same database as geometry
3. Performance characteristics of cross-repo validation
4. Operator training timeline for unified workflow

### Dependencies

1. IBG ratification blocks geometry export from vectorizer paths
2. Vocabulary convergence blocks schema normalization
3. Schema normalization blocks contract boundaries
4. Contract boundaries block runtime integration

---

## 9. File Reference Index

### CAM-Assist-Blueprint

| File | Purpose |
|------|---------|
| `schemas/strategy.schema.json` | Fret slot strategy contract |
| `schemas/strategy_package_manifest.schema.json` | Package authority block |
| `schemas/review_decision_record.schema.json` | Review decision authority |
| `scripts/record_review_decision.py` | A12 decision recorder |
| `docs/SPRINT_ARCHITECTURE_HANDOFF_2026-05-24.md` | Sprint handoff |

### luthiers-toolbox

| File | Purpose |
|------|---------|
| `docs/governance/CROSS_REPO_AUTHORITY_CROSSWALK.md` | Authority mapping |
| `docs/governance/IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Provenance blockers |
| `services/api/app/governance/authority_state.py` | Authority enum |
| `services/api/app/governance/confidence_declaration.py` | Confidence types |
| `services/api/app/cam/review_queue_item.py` | 8E queue model |

### tap_tone_pi

| File | Purpose |
|------|---------|
| `docs/ADR-0010-guidance-authority-boundary.md` | Guidance limits |
| `docs/ADR-0011-measurement-authority.md` | Measurement authority |
| `docs/ADR-0012-epistemic-status-taxonomy.md` | Epistemic states |
| `docs/AGE_CONSTITUTIONAL_CONTRACT.md` | AGE capabilities |
| `tap_tone_pi/agentic/contracts/advisory_authority.py` | Authority contracts |

---

## 10. Audit Certification

This audit reviewed:
- 15 governance documents across 3 repositories
- 3 schema definitions
- 4 authority models
- 3 review queue implementations
- 66+ commits (luthiers), 27 commits (tap_tone), 28 commits (CAM)

**Coverage estimate**: 95%+ of governance-relevant material

**Audit conclusion**: Repositories are individually mature but operationally siloed. Convergence roadmap required before runtime integration.

---

*Audit generated: 2026-05-24*  
*Non-execution infrastructure — this audit does not authorize machine execution*
