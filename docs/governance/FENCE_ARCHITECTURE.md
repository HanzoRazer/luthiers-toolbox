# 🔒 Fence Architecture - Governance Boundaries

> **Purpose**: Prevent architectural drift through automated boundary enforcement
> **Status**: Active enforcement across 8 profiles
> **Registry**: `FENCE_REGISTRY.json` (repo root)
> **Last Updated**: 2026-01-08

---

## Philosophy

> **"Good fences make good neighbors."**

Boundaries prevent:
- **Domain bleed** - RMOS orchestrating toolpaths directly
- **Hidden coupling** - CAM depending on RMOS workflow state
- **Authority violation** - AI sandbox creating artifacts
- **Legacy drift** - Frontend bypassing SDK layer

Each fence has:
1. **Clear rationale** - Why the boundary exists
2. **Enforcement script** - Automated CI check
3. **Escape hatch** - Artifact contracts or HTTP APIs
4. **Documentation** - How to work within boundaries

---

## Fence Profiles

### 1. External Boundary (Cross-Repo)

**Separates**: The Production Shop ↔ Tap Tone Analyzer

```json
{
  "profile": "external_boundary",
    "forbidden": ["tap_tone.*", "modes.*"],
      "reason": "ToolBox interprets measurements, doesn't perform them"
      }
      ```

      **Integration Pattern**: Artifact ingestion (JSON/CSV/WAV)

      **Enforcement**:
      ```bash
      cd services/api
      python -m app.ci.check_boundary_imports --profile toolbox
      ```

      **Documentation**: [docs/BOUNDARY_RULES.md](../BOUNDARY_RULES.md)

      ---

      ### 2. RMOS ↔ CAM Boundary (Internal Domain)

      **Separates**: Orchestration ↔ Execution

      ```
      ┌────────────────────────────────────────┐
      │ RMOS (Orchestration Layer)            │
      │ - Workflow state machine               │
      │ - Feasibility gates                    │
      │ - Artifact persistence                 │
      │ - Intent envelope construction         │
      └──────────┬─────────────────────────────┘
                 │
                            │ CamIntentV1 + HTTP
                                       │
                                       ┌──────────▼─────────────────────────────┐
                                       │ CAM (Execution Layer)                  │
                                       │ - Toolpath generation                  │
                                       │ - Post-processing                      │
                                       │ - Risk calculation                     │
                                       │ - G-code emission                      │
                                       └────────────────────────────────────────┘
                                       ```

                                       **RMOS Rules**:
                                       - ✅ Can import: `app.rmos.*`, `app.util.*`, `app.schemas.*`
                                       - ❌ Cannot import: `app.cam.toolpath.*`, `app.cam.post.*`
                                       - 💡 Use instead: CAM Intent envelope → HTTP call → result processing

                                       **CAM Rules**:
                                       - ✅ Can import: `app.cam.*`, `app.rmos.cam.CamIntentV1`
                                       - ❌ Cannot import: `app.rmos.workflow.*`, `app.rmos.runs.*`, `app.rmos.feasibility.*`
                                       - 💡 Use instead: Accept intent → compute → return data structure

                                       **Example Violation**:
                                       ```python
                                       # ❌ BAD: RMOS directly importing toolpath generator
                                       from app.cam.toolpath.roughing import generate_roughing_toolpath

                                       def plan_roughing(design):
                                           toolpath = generate_roughing_toolpath(design)  # Crosses boundary!
                                               return persist_toolpath(toolpath)
                                               ```

                                               **Correct Pattern**:
                                               ```python
                                               # ✅ GOOD: RMOS uses CAM Intent + HTTP
                                               from app.rmos.cam import CamIntentV1

                                               def plan_roughing(design):
                                                   intent = CamIntentV1(mode="roughing", design=design)
                                                       response = requests.post("/api/cam/roughing/gcode", json=intent.dict())
                                                           return persist_result(response.json())
                                                           ```

                                                           **Enforcement**:
                                                           ```bash
                                                           python -m app.ci.check_domain_boundaries --profile rmos_cam
                                                           ```

                                                           ---

                                                           ### 3. Operation Lane Boundary

                                                           **Separates**: Governed execution ↔ Stateless utilities

                                                           **Lane Definitions**:

                                                           | Lane | Artifacts | Feasibility | Audit | Example |
                                                           |------|-----------|-------------|-------|---------|
                                                           | **OPERATION** | Required | Required | Required | `/api/saw/batch/*` |
                                                           | **UTILITY** | None | Optional | None | `/api/cam/toolpath/roughing/gcode` |

                                                           **OPERATION Lane Requirements**:
                                                           ```python
                                                           # Required patterns:
                                                           - validate_and_persist()
                                                           - FeasibilityResult with risk_level
                                                           - Stage sequence (SPEC → PLAN → DECISION → EXECUTE)
                                                           - Artifact persistence per stage
                                                           - Learning feedback loop (optional but recommended)

                                                           # Forbidden patterns:
                                                           - direct file writes (use artifact abstraction)
                                                           - skip feasibility gate
                                                           - create artifacts without validation
                                                           ```

                                                           **Reference Implementation**: [docs/CNC_SAW_LAB_DEVELOPER_GUIDE.md](../CNC_SAW_LAB_DEVELOPER_GUIDE.md)

                                                           **Enforcement**:
                                                           ```bash
                                                           python -m app.ci.check_operation_lane_compliance
                                                           ```

                                                           ---

                                                           ### 4. AI Sandbox Boundary

                                                           **Separates**: Advisory intelligence ↔ Execution authority

                                                           **Philosophy**: AI can suggest, but humans decide.

                                                           ```
                                                           ┌─────────────────────────────────────────┐
                                                           │ AI Sandbox (_experimental/)            │
                                                           │ - Generate advisories                   │
                                                           │ - Return suggestions                    │
                                                           │ - Propose parameter adjustments         │
                                                           └──────────┬──────────────────────────────┘
                                                                      │
                                                                                 │ Advisory artifacts only
                                                                                            │
                                                                                            ┌──────────▼──────────────────────────────┐
                                                                                            │ Human Decision Gate                     │
                                                                                            │ - Review AI proposals                   │
                                                                                            │ - Approve/reject                        │
                                                                                            │ - Execute via authorized APIs           │
                                                                                            └─────────────────────────────────────────┘
                                                                                            ```

                                                                                            **Forbidden Imports**:
                                                                                            - `app.rmos.workflow.*` - Can't control state machine
                                                                                            - `app.rmos.runs.store.*` - Can't create artifacts
                                                                                            - `app.rmos.toolpaths.*` - Can't generate executable code

                                                                                            **Forbidden Calls**:
                                                                                            - `approve_workflow()`
                                                                                            - `generate_toolpaths()`
                                                                                            - `create_run_artifact()`
                                                                                            - `persist_run_artifact()`

                                                                                            **Allowed Pattern**:
                                                                                            ```python
                                                                                            # ✅ GOOD: AI returns advisory data
                                                                                            def suggest_feed_adjustment(metrics):
                                                                                                return {
                                                                                                        "advisory_type": "PARAMETER_SUGGESTION",
                                                                                                                "suggestion": {"feed_rate_mult": 0.85},
                                                                                                                        "confidence": 0.72,
                                                                                                                                "reasoning": "Detected burn marks..."
                                                                                                                                    }
                                                                                                                                    ```

                                                                                                                                    **Enforcement**:
                                                                                                                                    ```bash
                                                                                                                                    python ci/ai_sandbox/check_ai_import_boundaries.py
                                                                                                                                    python ci/ai_sandbox/check_ai_forbidden_calls.py
                                                                                                                                    python ci/ai_sandbox/check_ai_write_paths.py
                                                                                                                                    ```

                                                                                                                                    ---

                                                                                                                                    ### 5. Saw Lab Encapsulation

                                                                                                                                    **Pattern**: Self-contained reference implementation

                                                                                                                                    **Purpose**: Demonstrate OPERATION lane governance without depending on RMOS internals.

                                                                                                                                    **Allowed Dependencies**:
                                                                                                                                    - ✅ `app.saw_lab.*` (internal)
                                                                                                                                    - ✅ `app.rmos.runs_v2.*` (artifact storage only)
                                                                                                                                    - ✅ `app.rmos.cam.CamIntentV1` (intent envelope)
                                                                                                                                    - ✅ `app.util.*`, `app.schemas.*` (shared utilities)

                                                                                                                                    **Forbidden Dependencies**:
                                                                                                                                    - ❌ `app.cam.toolpath.*` - Use CAM Intent + HTTP
                                                                                                                                    - ❌ `app.rmos.workflow.*` - Saw Lab has its own stages

                                                                                                                                    **Stage Sequence**:
                                                                                                                                    ```
                                                                                                                                    SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK
                                                                                                                                      ↓      ↓        ↓          ↓        ↓         ↓
                                                                                                                                       Input  Plan   Approval  Toolpaths  G-code  Job Log
                                                                                                                                       Artifact Artifact Artifact Artifact  Export Learning
                                                                                                                                       ```

                                                                                                                                       **Enforcement**:
                                                                                                                                       ```bash
                                                                                                                                       python -m app.ci.check_saw_lab_encapsulation
                                                                                                                                       ```

                                                                                                                                       ---

                                                                                                                                       ### 6. Frontend SDK Boundary

                                                                                                                                       **Pattern**: Type-safe API consumption

                                                                                                                                       **Violation Example**:
                                                                                                                                       ```typescript
                                                                                                                                       // ❌ BAD: Raw fetch in component
                                                                                                                                       const response = await fetch("/api/cam/roughing/gcode", {
                                                                                                                                         method: "POST",
                                                                                                                                           headers: { "Content-Type": "application/json" },
                                                                                                                                             body: JSON.stringify(payload),
                                                                                                                                             });
                                                                                                                                             const gcode = await response.text();
                                                                                                                                             ```

                                                                                                                                             **Correct Pattern**:
                                                                                                                                             ```typescript
                                                                                                                                             // ✅ GOOD: Typed SDK helper
                                                                                                                                             import { cam } from "@/sdk/endpoints";

                                                                                                                                             const { gcode, summary, requestId } = await cam.roughingGcode(payload);
                                                                                                                                             // Header parsing, error handling, request-id automatic
                                                                                                                                             ```

                                                                                                                                             **Benefits**:
                                                                                                                                             1. Type safety (compiler catches mismatches)
                                                                                                                                             2. Header parsing in one place (X-CAM-Summary, X-Request-Id)
                                                                                                                                             3. Error handling consistency (ApiError with context)
                                                                                                                                             4. Testing: mock 1 function vs fetch() everywhere
                                                                                                                                             5. Migration: update SDK helper, not N components

                                                                                                                                             **Enforcement**:
                                                                                                                                             ```bash
                                                                                                                                             python scripts/ci/check_frontend_sdk_usage.py
                                                                                                                                             ```

                                                                                                                                             **Documentation**: [packages/client/src/sdk/endpoints/README.md](../../packages/client/src/sdk/endpoints/README.md)

                                                                                                                                             ---

                                                                                                                                             ### 7. Artifact Authority

                                                                                                                                             **Pattern**: Centralized validation for run artifacts

                                                                                                                                             **Authority Restriction**: Only `store.py` can create `RunArtifact` instances.

                                                                                                                                             **Rationale**:
                                                                                                                                             - Prevents bypassing validation
                                                                                                                                             - Ensures completeness guards execute
                                                                                                                                             - Maintains audit trail integrity
                                                                                                                                             - Single source of truth for artifact schema

                                                                                                                                             **Allowed**:
                                                                                                                                             ```python
                                                                                                                                             # ✅ GOOD: Use store interface
                                                                                                                                             from app.rmos.runs_v2.store import validate_and_persist

                                                                                                                                             artifact = validate_and_persist(
                                                                                                                                                 session_id="abc123",
                                                                                                                                                     tool_id="roughing",
                                                                                                                                                         payload={"...": "..."},
                                                                                                                                                             feasibility=feasibility_result,
                                                                                                                                                             )
                                                                                                                                                             ```

                                                                                                                                                             **Forbidden**:
                                                                                                                                                             ```python
                                                                                                                                                             # ❌ BAD: Direct construction
                                                                                                                                                             from app.rmos.runs_v2.schemas import RunArtifact

                                                                                                                                                             artifact = RunArtifact(  # Bypasses validation!
                                                                                                                                                                 run_id="xyz",
                                                                                                                                                                     ...
                                                                                                                                                                     )
                                                                                                                                                                     ```

                                                                                                                                                                     **Exception**: `TYPE_CHECKING` context for type hints only.

                                                                                                                                                                     **Enforcement**:
                                                                                                                                                                     ```bash
                                                                                                                                                                     python ci/rmos/check_no_direct_runartifact.py
                                                                                                                                                                     python ci/ai_sandbox/check_rmos_completeness_guard.py
                                                                                                                                                                     ```

                                                                                                                                                                     **Documentation**: [docs/governance/SECURITY_TRUST_BOUNDARY_CONTRACT_v1.md](SECURITY_TRUST_BOUNDARY_CONTRACT_v1.md)

                                                                                                                                                                     ---

                                                                                                                                                                     ### 8. Legacy Deprecation

                                                                                                                                                                     **Pattern**: Budget-based migration enforcement

                                                                                                                                                                     **Current State** (2026-01-08):
                                                                                                                                                                     - Budget: 10 legacy usages allowed
                                                                                                                                                                     - Current: 8 usages in 4 files
                                                                                                                                                                     - Status: ✅ Within budget

                                                                                                                                                                     **Legacy Patterns**:
                                                                                                                                                                     ```
                                                                                                                                                                     /api/cam/vcarve/*        → /api/cam/toolpath/vcarve/*
                                                                                                                                                                     /api/cam/roughing/*      → /api/cam/toolpath/roughing/*
                                                                                                                                                                     /api/rosette-patterns    → /api/art/rosette/pattern/patterns
                                                                                                                                                                     /api/art-studio/workflow/* → /api/rmos/workflow/*
                                                                                                                                                                     ```

                                                                                                                                                                     **Migration Workflow**:
                                                                                                                                                                     1. CI reports current usage count
                                                                                                                                                                     2. Fix legacy usages in frontend
                                                                                                                                                                     3. Reduce budget as migration progresses
                                                                                                                                                                     4. Goal: Budget = 0 (all code using canonical endpoints)

                                                                                                                                                                     **Enforcement**:
                                                                                                                                                                     ```bash
                                                                                                                                                                     cd services/api
                                                                                                                                                                     python -m app.ci.legacy_usage_gate \
                                                                                                                                                                       --roots ../../packages/client/src \
                                                                                                                                                                         --budget 10
                                                                                                                                                                         ```

                                                                                                                                                                         **Documentation**: [Legacy deprecation governance documentation

                                                                                                                                                                         ---

                                                                                                                                                                         ## Enforcement Stack

                                                                                                                                                                         ### CI Integration

                                                                                                                                                                         All fences run in CI via `.github/workflows/`:

                                                                                                                                                                         | Workflow | Fences | Blocking |
                                                                                                                                                                         |----------|--------|----------|
                                                                                                                                                                         | `architecture_scan.yml` | External boundary | ✅ Yes |
                                                                                                                                                                         | `ai_sandbox_enforcement.yml` | AI sandbox (3 checks) | ✅ Yes |
                                                                                                                                                                         | `artifact_linkage_gate.yml` | Artifact authority | ✅ Yes |
                                                                                                                                                                         | `legacy_endpoint_usage_gate.yml` | Legacy deprecation | ⚠️ Warning |
                                                                                                                                                                         | `domain_boundaries.yml` | RMOS↔CAM, Operation lane | ✅ Yes |

                                                                                                                                                                         ### Pre-Commit Hooks

                                                                                                                                                                         Optional local validation:
                                                                                                                                                                         ```bash
                                                                                                                                                                         .git/hooks/pre-commit → scripts/git-hooks/check-boundaries.sh
                                                                                                                                                                         ```

                                                                                                                                                                         Install:
                                                                                                                                                                         ```bash
                                                                                                                                                                         ln -s ../../scripts/git-hooks/check-boundaries.sh .git/hooks/pre-commit
                                                                                                                                                                         ```

                                                                                                                                                                         ### Local Development

                                                                                                                                                                         Run all checks before commit:
                                                                                                                                                                         ```bash
                                                                                                                                                                         make check-boundaries
                                                                                                                                                                         ```

                                                                                                                                                                         Or individual checks:
                                                                                                                                                                         ```bash
                                                                                                                                                                         cd services/api
                                                                                                                                                                         python -m app.ci.check_boundary_imports --profile toolbox
                                                                                                                                                                         python -m app.ci.check_domain_boundaries --profile rmos_cam
                                                                                                                                                                         python -m app.ci.check_operation_lane_compliance
                                                                                                                                                                         python ci/ai_sandbox/check_ai_import_boundaries.py
                                                                                                                                                                         ```

                                                                                                                                                                         ---

                                                                                                                                                                         ## Integration Patterns

                                                                                                                                                                         ### Pattern 1: Artifact Contract

                                                                                                                                                                         **Use When**: Domain A needs to consume Domain B's output without code dependency.

                                                                                                                                                                         **Example**: ToolBox consuming Analyzer measurements

                                                                                                                                                                         ```
                                                                                                                                                                         Analyzer (Producer)          ToolBox (Consumer)
                                                                                                                                                                         ─────────────────            ─────────────────
                                                                                                                                                                         1. Perform measurement       1. List artifacts
                                                                                                                                                                         2. Write JSON artifact       2. Load JSON
                                                                                                                                                                         3. Calculate SHA256          3. Validate schema
                                                                                                                                                                         4. Log to manifest.jsonl     4. Interpret + advise
                                                                                                                                                                         ```

                                                                                                                                                                         **Contract**:
                                                                                                                                                                         - JSON schema (versioned)
                                                                                                                                                                         - SHA256 integrity
                                                                                                                                                                         - Manifest for discovery
                                                                                                                                                                         - No code imports

                                                                                                                                                                         ---

                                                                                                                                                                         ### Pattern 2: HTTP API Contract

                                                                                                                                                                         **Use When**: Domain A needs to invoke Domain B's behavior.

                                                                                                                                                                         **Example**: RMOS requesting CAM toolpath generation

                                                                                                                                                                         ```
                                                                                                                                                                         RMOS (Client)                CAM (Server)
                                                                                                                                                                         ─────────────                ────────────
                                                                                                                                                                         1. Construct CamIntentV1     1. Receive intent
                                                                                                                                                                         2. POST /api/cam/roughing    2. Validate schema
                                                                                                                                                                         3. Wait for response         3. Generate toolpaths
                                                                                                                                                                         4. Parse result              4. Return JSON
                                                                                                                                                                         5. Persist artifact          5. No state change
                                                                                                                                                                         ```

                                                                                                                                                                         **Contract**:
                                                                                                                                                                         - OpenAPI spec
                                                                                                                                                                         - Versioned intent schema
                                                                                                                                                                         - Idempotent operations
                                                                                                                                                                         - No shared state

                                                                                                                                                                         ---

                                                                                                                                                                         ### Pattern 3: SDK Adapter

                                                                                                                                                                         **Use When**: Frontend needs type-safe API access.

                                                                                                                                                                         **Example**: Component calling CAM endpoint

                                                                                                                                                                         ```
                                                                                                                                                                         Component                    SDK Helper                API
                                                                                                                                                                         ─────────                    ──────────                ───
                                                                                                                                                                         1. Call cam.roughingGcode()  1. Construct payload      1. Receive POST
                                                                                                                                                                         2. Await result              2. POST /api/cam/...      2. Validate
                                                                                                                                                                         3. Use typed response        3. Parse headers          3. Execute
                                                                                                                                                                                                      4. Handle errors          4. Return JSON
                                                                                                                                                                                                                                   5. Extract request-id     5. Set headers
                                                                                                                                                                                                                                   ```

                                                                                                                                                                                                                                   **Contract**:
                                                                                                                                                                                                                                   - TypeScript interfaces
                                                                                                                                                                                                                                   - Header parsing in SDK
                                                                                                                                                                                                                                   - ApiError with context
                                                                                                                                                                                                                                   - Request-ID propagation

                                                                                                                                                                                                                                   ---

                                                                                                                                                                                                                                   ## Exemption Process

                                                                                                                                                                                                                                   **Policy**: No code exemptions. Integration requires explicit contracts.

                                                                                                                                                                                                                                   **Alternatives**:
                                                                                                                                                                                                                                   1. Create artifact schema (JSON/CSV)
                                                                                                                                                                                                                                   2. Create HTTP API contract (OpenAPI)
                                                                                                                                                                                                                                   3. Create SDK adapter layer
                                                                                                                                                                                                                                   4. Refactor to eliminate coupling

                                                                                                                                                                                                                                   **Escalation**: Architecture team review for new integration patterns.

                                                                                                                                                                                                                                   **Example Request** (use this template):
                                                                                                                                                                                                                                   ```markdown
                                                                                                                                                                                                                                   ## Boundary Exemption Request

                                                                                                                                                                                                                                   **Requestor**: [Name]
                                                                                                                                                                                                                                   **Date**: [YYYY-MM-DD]
                                                                                                                                                                                                                                   **Fence**: [Profile name from FENCE_REGISTRY.json]

                                                                                                                                                                                                                                   **Proposed Violation**:
                                                                                                                                                                                                                                   ```python
                                                                                                                                                                                                                                   from app.forbidden_module import ForbiddenClass
                                                                                                                                                                                                                                   ```

                                                                                                                                                                                                                                   **Rationale**: [Why existing patterns don't work]

                                                                                                                                                                                                                                   **Alternatives Considered**:
                                                                                                                                                                                                                                   1. Artifact contract - [Why not suitable]
                                                                                                                                                                                                                                   2. HTTP API - [Why not suitable]
                                                                                                                                                                                                                                   3. SDK adapter - [Why not suitable]

                                                                                                                                                                                                                                   **Impact Analysis**:
                                                                                                                                                                                                                                   - Coupling risk: [Assessment]
                                                                                                                                                                                                                                   - Testing impact: [Assessment]
                                                                                                                                                                                                                                   - Maintenance cost: [Assessment]

                                                                                                                                                                                                                                   **Proposed Integration Contract**: [New pattern specification]
                                                                                                                                                                                                                                   ```

                                                                                                                                                                                                                                   ---

                                                                                                                                                                                                                                   ## Metrics & Monitoring

                                                                                                                                                                                                                                   ### Tracked Metrics

                                                                                                                                                                                                                                   | Metric | Source | Dashboard |
                                                                                                                                                                                                                                   |--------|--------|-----------|
                                                                                                                                                                                                                                   | Boundary violations/month | CI logs | `reports/boundary_health.json` |
                                                                                                                                                                                                                                   | Legacy endpoint usage | Frontend scanner | `reports/legacy_usage.json` |
                                                                                                                                                                                                                                   | Artifact authority violations | RMOS completeness guard | `reports/artifact_audit.json` |
                                                                                                                                                                                                                                   | AI sandbox escape attempts | AI boundary checks | `reports/ai_violations.json` |

                                                                                                                                                                                                                                   ### Health Indicators

                                                                                                                                                                                                                                   ```json
                                                                                                                                                                                                                                   {
                                                                                                                                                                                                                                     "fence_health": {
                                                                                                                                                                                                                                         "external_boundary": { "violations": 0, "status": "GREEN" },
                                                                                                                                                                                                                                             "rmos_cam_boundary": { "violations": 0, "status": "GREEN" },
                                                                                                                                                                                                                                                 "ai_sandbox_boundary": { "violations": 2, "status": "YELLOW" },
                                                                                                                                                                                                                                                     "legacy_deprecation": { "usage_count": 8, "budget": 10, "status": "GREEN" }
                                                                                                                                                                                                                                                       },
                                                                                                                                                                                                                                                         "trend": "improving",
                                                                                                                                                                                                                                                           "last_violation": "2025-12-15T10:23:00Z"
                                                                                                                                                                                                                                                           }
                                                                                                                                                                                                                                                           ```

                                                                                                                                                                                                                                                           ---

                                                                                                                                                                                                                                                           ## References

                                                                                                                                                                                                                                                           | Document | Purpose |
                                                                                                                                                                                                                                                           |----------|---------|
                                                                                                                                                                                                                                                           | `FENCE_REGISTRY.json` (repo root) | Machine-readable boundary definitions |
                                                                                                                                                                                                                                                           | [BOUNDARY_RULES.md](../BOUNDARY_RULES.md) | External boundary (ToolBox↔Analyzer) |
                                                                                                                                                                                                                                                           | [OPERATION_EXECUTION_GOVERNANCE_v1.md](../OPERATION_EXECUTION_GOVERNANCE_v1.md) | Operation lane governance |
                                                                                                                                                                                                                                                           | [CNC_SAW_LAB_DEVELOPER_GUIDE.md](../CNC_SAW_LAB_DEVELOPER_GUIDE.md) | Saw Lab reference implementation |
                                                                                                                                                                                                                                                           | the endpoint routes documentation | API surface + lane classifications |
                                                                                                                                                                                                                                                           | [AI_CODE_BUNDLE_LOCK_POINTS_v1.md](AI_CODE_BUNDLE_LOCK_POINTS_v1.md) | Authoritative router prefixes |
                                                                                                                                                                                                                                                           | [packages/client/src/sdk/endpoints/README.md](../../packages/client/src/sdk/endpoints/README.md) | Frontend SDK patterns |

                                                                                                                                                                                                                                                           ---

                                                                                                                                                                                                                                                           ## Quick Reference Card

                                                                                                                                                                                                                                                           ### For AI Agents

                                                                                                                                                                                                                                                           ```markdown
                                                                                                                                                                                                                                                           **Before importing across domains:**

                                                                                                                                                                                                                                                           1. Check FENCE_REGISTRY.json for allowed imports
                                                                                                                                                                                                                                                           2. If forbidden, use artifact contract or HTTP API
                                                                                                                                                                                                                                                           3. Document integration pattern in code comments
                                                                                                                                                                                                                                                           4. Run CI checks locally before commit

                                                                                                                                                                                                                                                           **Red Flags** (immediate rejection):
                                                                                                                                                                                                                                                           - ❌ RMOS importing app.cam.toolpath.*
                                                                                                                                                                                                                                                           - ❌ CAM importing app.rmos.workflow.*
                                                                                                                                                                                                                                                           - ❌ AI sandbox importing app.rmos.runs.store.*
                                                                                                                                                                                                                                                           - ❌ Frontend using raw fetch() to API
                                                                                                                                                                                                                                                           - ❌ Direct RunArtifact() construction
                                                                                                                                                                                                                                                           ```

                                                                                                                                                                                                                                                           ### For Developers

                                                                                                                                                                                                                                                           ```bash
                                                                                                                                                                                                                                                           # Check all boundaries
                                                                                                                                                                                                                                                           make check-boundaries

                                                                                                                                                                                                                                                           # Check specific fence
                                                                                                                                                                                                                                                           python -m app.ci.check_boundary_imports --profile toolbox
                                                                                                                                                                                                                                                           python -m app.ci.check_domain_boundaries --profile rmos_cam

                                                                                                                                                                                                                                                           # Check legacy usage
                                                                                                                                                                                                                                                           cd services/api
                                                                                                                                                                                                                                                           python -m app.ci.legacy_usage_gate --roots ../../packages/client/src --budget 10
                                                                                                                                                                                                                                                           ```

                                                                                                                                                                                                                                                           ---

                                                                                                                                                                                                                                                           **Last Updated**: 2026-01-08  
                                                                                                                                                                                                                                                           **Maintainer**: Architecture Team  
                                                                                                                                                                                                                                                           **Review Cycle**: Quarterly

                                                                                                                                                                                                                                                           