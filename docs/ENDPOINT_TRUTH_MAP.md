# Endpoint Truth Map

> Complete API surface area for Luthier's Toolbox (if all optional imports succeed).

---

## Operation Execution Governance - Lane Classifications

> **Added 2025-12-29**: Lane annotations per `OPERATION_EXECUTION_GOVERNANCE_v1.md`.
>
> Machine-executing endpoints must declare: `LANE=OPERATION` (governed) or `LANE=UTILITY` (legacy).

### Lane Definitions

| Lane | Description | Requirements |
|------|-------------|--------------|
| **OPERATION** | Governed execution pipeline | Artifacts, feasibility gate, audit trail |
| **UTILITY** | Stateless/legacy | No governance guarantees, preview/dev use |

### Machine-Output Endpoints by Lane

#### OPERATION Lane (Governed)

> Reference implementation: CNC Saw Lab Batch

| Endpoint | Tool Type | Stage | Notes |
|----------|-----------|-------|-------|
| `POST /api/saw/batch/spec` | saw | SPEC | Reference impl |
| `POST /api/saw/batch/plan` | saw | PLAN | Reference impl |
| `POST /api/saw/batch/approve` | saw | DECISION | Reference impl |
| `POST /api/saw/batch/toolpaths` | saw | EXECUTE | Reference impl |
| `GET /api/saw/batch/op-toolpaths/{id}/gcode` | saw | EXPORT | Reference impl |
| `GET /api/saw/batch/executions/{id}/gcode` | saw | EXPORT | Reference impl |
| `POST /api/saw/batch/job-log` | saw | FEEDBACK | Reference impl |
| `POST /api/rmos/toolpaths` | rmos | EXECUTE | Promoted Wave 9 |
| `POST /api/cam/rosette/plan-toolpath` | rosette | PLAN | Promoted Wave 9 |
| `POST /api/cam/rosette/post-gcode` | rosette | EXECUTE | Promoted Wave 9 |
| `POST /api/art-studio/vcarve/gcode` | vcarve | EXECUTE | Promoted Wave 9 |

#### UTILITY Lane (Legacy/Preview)

> These endpoints produce G-code but bypass governance. Suitable for development, simulation, preview.

| Endpoint | Tool Type | Notes |
|----------|-----------|-------|
| `POST /api/cam/drilling/gcode` | drill | Legacy generator |
| `POST /api/cam/drilling/pattern/gcode` | drill | Legacy generator |
| `POST /api/cam/toolpath/roughing/gcode` | roughing | Legacy generator |
| `POST /api/cam/toolpath/biarc/gcode` | contour | Legacy generator |
| `POST /api/cam/toolpath/helical_entry` | plunge | Legacy generator |
| `POST /api/cam/roughing/gcode_intent` | roughing | Intent-native, no artifacts |
| `POST /feasibility` | — | Root-mounted, stateless |
| `POST /toolpaths` | — | Root-mounted, stateless |
| `POST /api/rmos/workflow/sessions/{id}/toolpaths/request` | rosette | Session-scoped, legacy |
| `POST /api/rmos/workflow/sessions/{id}/toolpaths/store` | rosette | Session-scoped, legacy |
| `POST /api/art-studio/rosette/export-dxf` | rosette | DXF export, no artifacts |
| `POST /api/art/rosette/preview/svg` | rosette | Preview only |

#### N/A (Non-Machine Endpoints)

All other endpoints (CRUD, validation, query, analytics) are **not in scope** for lane governance.

### Migration Priority

| Priority | Endpoint(s) | Target Lane | Effort |
|----------|-------------|-------------|--------|
| ✅ Done | `/api/saw/batch/*` | OPERATION | Reference impl |
| Done | `/api/cam/rosette/*` | OPERATION | Promoted Wave 9 |
| Done | `/api/art-studio/vcarve/gcode` | OPERATION | Promoted Wave 9 |
| 4 | `/api/cam/drilling/*` | OPERATION | 2-3 days |
| 5 | `/api/cam/toolpath/roughing/*` | OPERATION | 3-5 days |

---

## CNC Saw Lab Batch Endpoints

> **Added 2025-12-29**: Reference implementation for governed operation execution.
>
> **Lane:** OPERATION (full governance)
> **Feature Branch:** `feature/cnc-saw-labs`
> **Developer Guide:** `docs/CNC_SAW_LAB_DEVELOPER_GUIDE.md`

### Core Workflow (`/api/saw/batch`)

| Method | Endpoint | Stage | Description |
|--------|----------|-------|-------------|
| POST | `/api/saw/batch/spec` | SPEC | Create batch specification |
| POST | `/api/saw/batch/plan` | PLAN | Generate execution plan with feasibility |
| POST | `/api/saw/batch/approve` | DECISION | Approve plan, create decision artifact |
| POST | `/api/saw/batch/toolpaths` | EXECUTE | Generate toolpaths (server-side feasibility) |

### G-Code Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saw/batch/op-toolpaths/{artifact_id}/gcode` | Single op G-code (.ngc) |
| GET | `/api/saw/batch/executions/{artifact_id}/gcode` | Combined G-code for all OK ops |

### Operator Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/saw/batch/job-log` | Record job completion, metrics, signals |

### Learning System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saw/batch/learning-events/by-execution` | Get learning events for execution |
| POST | `/api/saw/batch/learning-events/approve` | Accept/reject learning event |
| GET | `/api/saw/batch/learning-overrides/resolve` | Resolve active overrides |
| POST | `/api/saw/batch/learning-overrides/apply` | Preview tuned context |
| GET | `/api/saw/batch/executions/with-learning` | List executions with learning applied |

### Metrics & Rollups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saw/batch/executions/metrics-rollup/by-execution` | Get execution rollup |
| POST | `/api/saw/batch/executions/metrics-rollup/by-execution` | Persist execution rollup |
| GET | `/api/saw/batch/decisions/metrics-rollup/by-decision` | Get decision rollup |
| GET | `/api/saw/batch/decisions/trends` | Trend analysis |
| GET | `/api/saw/batch/executions/metrics-rollup/history` | Rollup history |
| GET | `/api/saw/batch/decisions/metrics-rollup/latest-vs-prev` | Compare rollups |
| GET | `/api/saw/batch/rollups/diff` | Diff two rollups |

### CSV Exports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saw/batch/executions/job-logs.csv` | Export job logs as CSV |
| GET | `/api/saw/batch/decisions/execution-rollups.csv` | Export rollups as CSV |

### Status & Lookups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/saw/batch/learning-hook/status` | Learning hook enabled? |
| GET | `/api/saw/batch/rollups/hook/status` | Rollup hook enabled? |
| GET | `/api/saw/batch/learning-overrides/apply/status` | Apply overrides enabled? |
| GET | `/api/saw/batch/execution` | Get execution by decision |
| GET | `/api/saw/batch/executions/by-decision` | List executions for decision |
| GET | `/api/saw/batch/links` | Get artifact links by label/session |

### Artifact Kinds

| Kind | Description |
|------|-------------|
| `saw_batch_spec` | Input specification |
| `saw_batch_plan` | Plan with feasibility scores |
| `saw_batch_decision` | Approved execution order |
| `saw_batch_execution` | Parent execution artifact |
| `saw_batch_op_toolpaths` | Individual op toolpaths |
| `saw_batch_job_log` | Operator feedback |
| `saw_lab_learning_event` | Proposed adjustments |
| `saw_lab_learning_decision` | Accept/reject decision |
| `saw_batch_execution_metrics_rollup` | Aggregated execution metrics |
| `saw_batch_decision_metrics_rollup` | Aggregated decision metrics |

---

## RMOS Endpoints

### AI Routes (`/api/rmos/ai`)

| Method | Endpoint |
|--------|----------|
| POST | `/api/rmos/ai/constraint-search` |
| POST | `/api/rmos/ai/quick-check` |
| GET | `/api/rmos/ai/workflows` |
| GET | `/api/rmos/ai/health` |
| GET | `/api/rmos/ai/status/{status_code}` |

### Constraint Profiles (`/api/rmos/profiles`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/profiles` |
| POST | `/api/rmos/profiles` |
| GET | `/api/rmos/profiles/ids` |
| GET | `/api/rmos/profiles/{profile_id}` |
| PUT | `/api/rmos/profiles/{profile_id}` |
| DELETE | `/api/rmos/profiles/{profile_id}` |
| GET | `/api/rmos/profiles/{profile_id}/constraints` |

### Profile History (`/api/rmos/profiles/history`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/profiles/history` |
| GET | `/api/rmos/profiles/history/{profile_id}` |
| POST | `/api/rmos/profiles/history/{profile_id}/rollback` |
| GET | `/api/rmos/profiles/history/types` |
| GET | `/api/rmos/profiles/history/status` |

### Logs (`/api/rmos/logs`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/logs/recent` |
| GET | `/api/rmos/logs/recent/v2` |
| GET | `/api/rmos/logs/{run_id}` |

### Strip Families (`/api/rmos/strip-families`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/strip-families` |
| POST | `/api/rmos/strip-families` |
| GET | `/api/rmos/strip-families/{family_id}` |
| PUT | `/api/rmos/strip-families/{family_id}` |
| DELETE | `/api/rmos/strip-families/{family_id}` |

### Patterns (`/api/rmos/patterns`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/patterns` |
| POST | `/api/rmos/patterns` |
| GET | `/api/rmos/patterns/{pattern_id}` |
| PUT | `/api/rmos/patterns/{pattern_id}` |
| DELETE | `/api/rmos/patterns/{pattern_id}` |

### Saw Ops (`/api/rmos/saw-ops`)

| Method | Endpoint |
|--------|----------|
| POST | `/api/rmos/saw-ops/slice/preview` |
| POST | `/api/rmos/saw-ops/pipeline/handoff` |

### Runs (`/api/rmos/runs`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/runs/recent` |
| GET | `/api/rmos/runs/recent/v2` |
| GET | `/api/rmos/runs/{run_id}` |
| GET | `/api/rmos/runs/{run_id}/download` |
| GET | `/api/rmos/runs/diff/{a_id}/{b_id}` |
| PATCH | `/api/rmos/runs/{run_id}/meta` |
| GET | `/api/rmos/runs/{run_id}/meta` |
| GET | `/api/rmos/runs/{run_id}/artifacts` |
| GET | `/api/rmos/runs/{run_id}/artifacts/{artifact_id}` |
| GET | `/api/rmos/runs/{run_id}/artifacts/{artifact_id}/download` |
| POST | `/api/rmos/runs/{run_id}/artifacts/{artifact_id}/promote` |
| GET | `/api/rmos/runs/{run_id}/attachments` |
| POST | `/api/rmos/runs/{run_id}/attachments` |
| GET | `/api/rmos/runs/{run_id}/attachments/{attachment_id}` |
| GET | `/api/rmos/runs/{run_id}/attachments/{attachment_id}/download` |
| DELETE | `/api/rmos/runs/{run_id}/attachments/{attachment_id}` |
| POST | `/api/rmos/runs/{run_id}/attachments/verify` |

### Workflow Sessions (`/api/rmos/workflow`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/rmos/workflow/sessions` |
| POST | `/api/rmos/workflow/sessions` |
| GET | `/api/rmos/workflow/sessions/{session_id}` |
| GET | `/api/rmos/workflow/sessions/{session_id}/snapshot` |
| GET | `/api/rmos/workflow/sessions/{session_id}/events` |
| POST | `/api/rmos/workflow/sessions/{session_id}/design` |
| POST | `/api/rmos/workflow/sessions/{session_id}/context` |
| POST | `/api/rmos/workflow/sessions/{session_id}/feasibility/request` |
| POST | `/api/rmos/workflow/sessions/{session_id}/feasibility/store` |
| POST | `/api/rmos/workflow/approve` |
| POST | `/api/rmos/workflow/reject` |
| POST | `/api/rmos/workflow/sessions/{session_id}/toolpaths/request` |
| POST | `/api/rmos/workflow/sessions/{session_id}/toolpaths/store` |
| POST | `/api/rmos/workflow/sessions/{session_id}/revision` |
| POST | `/api/rmos/workflow/sessions/{session_id}/archive` |
| POST | `/api/rmos/workflow/sessions/{session_id}/save-snapshot` |
| GET | `/api/rmos/workflow/generators` |

### Root-Mounted RMOS Endpoints

> Mounted without `/api/rmos` prefix.

| Method | Endpoint |
|--------|----------|
| POST | `/feasibility` |
| POST | `/toolpaths` |

---

## Art Studio Endpoints

### Core Completion Lane (`/api/art`)

#### Patterns

| Method | Endpoint |
|--------|----------|
| GET | `/api/art/patterns` |
| POST | `/api/art/patterns` |
| GET | `/api/art/patterns/{pattern_id}` |
| PUT | `/api/art/patterns/{pattern_id}` |
| DELETE | `/api/art/patterns/{pattern_id}` |

#### Generators

| Method | Endpoint |
|--------|----------|
| POST | `/api/art/generators/{generator_key}/generate` |

#### Preview

| Method | Endpoint |
|--------|----------|
| POST | `/api/art/rosette/preview/svg` |

#### Snapshots

| Method | Endpoint |
|--------|----------|
| GET | `/api/art/snapshots/recent` |
| GET | `/api/art/snapshots/{snapshot_id}` |
| PUT | `/api/art/snapshots/{snapshot_id}` |
| DELETE | `/api/art/snapshots/{snapshot_id}` |
| GET | `/api/art/snapshots/{snapshot_id}/export` |
| GET | `/api/art/snapshots/{snapshot_id}/export/download` |
| POST | `/api/art/snapshots/import` |

#### Rosette Feasibility

| Method | Endpoint |
|--------|----------|
| POST | `/api/art/rosette/feasibility/batch` |

#### Rosette Snapshots

| Method | Endpoint |
|--------|----------|
| GET | `/api/art/rosette/snapshots/recent` |
| GET | `/api/art/rosette/snapshots/{snapshot_id}` |
| PUT | `/api/art/rosette/snapshots/{snapshot_id}` |
| DELETE | `/api/art/rosette/snapshots/{snapshot_id}` |
| GET | `/api/art/rosette/snapshots/{snapshot_id}/export` |
| GET | `/api/art/rosette/snapshots/{snapshot_id}/export/download` |
| POST | `/api/art/rosette/snapshots/import` |

#### Rosette Jobs

| Method | Endpoint |
|--------|----------|
| GET | `/api/art/rosette/jobs/recent` |
| POST | `/api/art/rosette/jobs/create` |
| GET | `/api/art/rosette/jobs/{job_id}` |
| POST | `/api/art/rosette/jobs/{job_id}/cancel` |
| GET | `/api/art/rosette/jobs/{job_id}/events` |

#### Rosette Compare

| Method | Endpoint |
|--------|----------|
| POST | `/api/art/rosette/compare/snapshot` |
| GET | `/api/art/rosette/compare/snapshots` |
| GET | `/api/art/rosette/compare/export_csv` |

#### Rosette Pattern Generation

| Method | Endpoint |
|--------|----------|
| GET | `/api/art/rosette/pattern/status` |
| GET | `/api/art/rosette/pattern/patterns` |
| GET | `/api/art/rosette/pattern/patterns/{pattern_id}` |
| POST | `/api/art/rosette/pattern/generate_traditional` |
| POST | `/api/art/rosette/pattern/generate_modern` |
| POST | `/api/art/rosette/pattern/export` |

### Legacy Rosette Lane (`/api/art-studio/rosette`)

| Method | Endpoint |
|--------|----------|
| GET | `/api/art-studio/rosette/presets` |
| GET | `/api/art-studio/rosette/presets/{preset_name}` |
| POST | `/api/art-studio/rosette/preset/{preset_name}/preview` |
| POST | `/api/art-studio/rosette/preview` |
| POST | `/api/art-studio/rosette/export-dxf` |

### Legacy Workflow Lane (`/api/art-studio/workflow`)

> **Note:** This lane is deprecated. Use `/api/rmos/workflow/*` instead.

| Method | Endpoint | Status |
|--------|----------|--------|
| POST | `/api/art-studio/workflow/from-pattern` | Legacy |
| POST | `/api/art-studio/workflow/from-generator` | Legacy |
| POST | `/api/art-studio/workflow/from-snapshot` | Legacy |
| GET | `/api/art-studio/workflow/sessions` | Legacy |
| GET | `/api/art-studio/workflow/sessions/{session_id}` | Legacy |
| PUT | `/api/art-studio/workflow/sessions/{session_id}/design` | Legacy |
| POST | `/api/art-studio/workflow/sessions/{session_id}/save-snapshot` | Legacy |
| GET | `/api/art-studio/workflow/generators` | Legacy |

### Other

| Method | Endpoint |
|--------|----------|
| GET | `/api/presets_aggregate` |

---

## Duplicate Surface Warnings

> Endpoints that exist in multiple places. UI must target the correct one.

### Workflow Sessions

**DUPLICATE:** Same functionality at two prefixes.

| Surface A (RMOS - Canonical) | Surface B (Art Studio - Legacy) |
|------------------------------|--------------------------------|
| `GET /api/rmos/workflow/sessions` | `GET /api/art-studio/workflow/sessions` |
| `GET /api/rmos/workflow/sessions/{session_id}` | `GET /api/art-studio/workflow/sessions/{session_id}` |
| `POST /api/rmos/workflow/sessions/{session_id}/design` | `PUT /api/art-studio/workflow/sessions/{session_id}/design` |
| `POST /api/rmos/workflow/sessions/{session_id}/feasibility/request` | (not implemented) |
| `POST /api/rmos/workflow/sessions/{session_id}/feasibility/store` | (not implemented) |
| `POST /api/rmos/workflow/approve` | (not implemented) |
| `POST /api/rmos/workflow/reject` | (not implemented) |
| `POST /api/rmos/workflow/sessions/{session_id}/revision` | (not implemented) |
| `POST /api/rmos/workflow/sessions/{session_id}/save-snapshot` | `POST /api/art-studio/workflow/sessions/{session_id}/save-snapshot` |
| `GET /api/rmos/workflow/generators` | `GET /api/art-studio/workflow/generators` |

**Risk:** UI component hits one, backend fix deployed to the other.

**Recommendation:** Consolidate to `/api/rmos/workflow/*` and deprecate `/api/art-studio/workflow/*`.

---

### Snapshots

**DUPLICATE:** Three separate snapshot APIs.

| Surface A | Surface B | Surface C |
|-----------|-----------|-----------|
| `/api/art/snapshots/*` | `/api/art/rosette/snapshots/*` | — |

Both have `recent`, `{id}`, `export`, `import` endpoints.

**Risk:** Snapshot created via one API invisible to the other.

**Recommendation:** Determine canonical surface and redirect/deprecate others.

---

### Patterns

**DUPLICATE:** Two pattern CRUD APIs.

| RMOS | Art Studio |
|------|------------|
| `/api/rmos/patterns` | `/api/art/patterns` |
| `/api/rmos/patterns/{id}` | `/api/art/patterns/{id}` |

**Risk:** Pattern created in one store not visible in the other.

**Recommendation:** Clarify if these are different pattern types or consolidate.

---

### Feasibility

**DUPLICATE:** Multiple feasibility endpoints.

| Endpoint | Notes |
|----------|-------|
| `POST /feasibility` | Root-mounted, no `/api` prefix |
| `POST /api/art/rosette/feasibility/batch` | Art Studio lane |
| `POST /api/rmos/workflow/sessions/{session_id}/feasibility/request` | Session-scoped (request) |
| `POST /api/rmos/workflow/sessions/{session_id}/feasibility/store` | Session-scoped (store) |

**Risk:** Different implementations, different response shapes.

**Recommendation:** Use RMOS workflow endpoints for new development.

---

## Summary

| Domain | Prefix | Count | Lane |
|--------|--------|-------|------|
| **CNC Saw Lab Batch** | `/api/saw/batch` | 27 | **OPERATION** |
| RMOS AI | `/api/rmos/ai` | 5 | N/A |
| RMOS Profiles | `/api/rmos/profiles` | 7 | N/A |
| RMOS Profile History | `/api/rmos/profiles/history` | 5 | N/A |
| RMOS Logs | `/api/rmos/logs` | 3 | N/A |
| RMOS Strip Families | `/api/rmos/strip-families` | 5 | N/A |
| RMOS Patterns | `/api/rmos/patterns` | 5 | N/A |
| RMOS Saw Ops | `/api/rmos/saw-ops` | 2 | UTILITY |
| RMOS Runs | `/api/rmos/runs` | 17 | N/A |
| RMOS Workflow | `/api/rmos/workflow` | 17 | UTILITY* |
| Root-mounted | `/` | 2 | UTILITY |
| Art Patterns | `/api/art/patterns` | 5 | N/A |
| Art Generators | `/api/art/generators` | 1 | N/A |
| Art Preview | `/api/art/rosette/preview` | 1 | UTILITY |
| Art Snapshots | `/api/art/snapshots` | 7 | N/A |
| Art Rosette Snapshots | `/api/art/rosette/snapshots` | 7 | N/A |
| Art Rosette Feasibility | `/api/art/rosette/feasibility` | 1 | UTILITY |
| Art Rosette Jobs | `/api/art/rosette/jobs` | 5 | N/A |
| Art Rosette Compare | `/api/art/rosette/compare` | 3 | N/A |
| Art Rosette Pattern | `/api/art/rosette/pattern` | 6 | N/A |
| Legacy Rosette | `/api/art-studio/rosette` | 5 | UTILITY |
| Legacy Workflow | `/api/art-studio/workflow` | 8 | UTILITY |
| CAM Consolidated | `/api/cam/*` | ~30 | UTILITY |
| Other | `/api` | 1 | N/A |
| **Total** | | **~175** | |

> *UTILITY = Only toolpath-producing endpoints; CRUD/query endpoints are N/A
> *RMOS Workflow toolpath endpoints are UTILITY; session CRUD is N/A

---

## Notes

1. **Conditional Mounting:** Routers with `try/except` in `main.py` may not be available if imports fail.

2. **Root-mounted endpoints:** `/feasibility` and `/toolpaths` lack `/api` prefix - likely internal/legacy.

3. **Auth Requirements:** RMOS runs endpoints require authentication. Manufacturing decisions require `admin` or `operator` role.

4. **Preferred Lanes:**
   - **RMOS:** Use `/api/rmos/*` for all RMOS functionality
   - **Art Studio:** Use `/api/art/*` (Core Completion lane), treat `/api/art-studio/*` as legacy

---

## Implementation Drift Analysis

> Generated 2025-12-26. Documents discrepancies between truth map and actual implementation.

### RMOS Workflow: Truth Map vs Implementation

The truth map specifies certain endpoint structures that differ from the actual implementation:

| Truth Map | Actual Implementation | Status |
|-----------|----------------------|--------|
| `POST .../sessions/{session_id}/approve` | `POST /api/rmos/workflow/approve` (body: `session_id`) | Design difference |
| `POST .../sessions/{session_id}/reject` | `POST /api/rmos/workflow/reject` (body: `session_id`) | Design difference |
| `POST .../sessions/{session_id}/feasibility` | Split: `.../feasibility/request` + `.../feasibility/store` | Design difference |
| `POST .../sessions/{session_id}/request-revision` | `POST .../sessions/{session_id}/revision` | Path difference |
| `PUT .../sessions/{session_id}/design` | `POST .../sessions/{session_id}/design` | Method difference |

### Root Cause

The implementation follows a different API design philosophy:
- **Approve/Reject**: Uses root-level endpoints with `session_id` in body for simpler RBAC
- **Feasibility**: Split into request/store for async workflow support
- **Design**: Uses POST for idempotent state transitions (not true PUT semantics)

---

## Mitigation Plan

### Phase 1: Align Truth Map with Implementation (Low Risk)

Update the truth map to reflect actual implementation. This is documentation-only.

**Tasks:**
1. Update RMOS Workflow section to match actual endpoints:
   - Change `POST .../approve` to root-level
   - Change `POST .../reject` to root-level
   - Split feasibility into request/store
   - Change `PUT` to `POST` for design endpoint
   - Change `request-revision` to `revision`

2. Add "Actual Implementation" column to duplicate warnings

### Phase 2: Deprecation Aliases (Medium Risk)

Add thin alias routes that redirect old paths to new implementation.

**Tasks:**
1. Create `workflow_compat_router.py` with aliases:
   ```python
   @router.post("/sessions/{session_id}/approve")
   def approve_compat(session_id: str):
       return approve_session(ApproveRequest(session_id=session_id))
   ```

2. Add deprecation headers to alias responses:
   ```
   Deprecation: true
   Sunset: 2025-06-01
   Link: </api/rmos/workflow/approve>; rel="successor-version"
   ```

3. Log usage of deprecated aliases for migration tracking

### Phase 3: Frontend Migration (Higher Risk)

Migrate frontend to use canonical endpoints.

**Tasks:**
1. Audit `packages/client/src` for workflow API usage
2. Update SDK wrapper functions in `packages/sdk/src`
3. Update any direct fetch calls to use new paths
4. Remove compat aliases after migration complete

### Phase 4: Legacy Lane Deprecation

Deprecate `/api/art-studio/workflow/*` entirely.

**Tasks:**
1. Add deprecation middleware to art-studio workflow router
2. Update frontend to use `/api/rmos/workflow/*` exclusively
3. Set sunset date and communicate to any API consumers
4. Remove art-studio workflow router after sunset

---

## CI Gate Recommendations

### Feature Hunt Improvements

1. **Normalize path parameters**: Treat `{id}`, `{session_id}`, `{run_id}` as equivalent for matching
2. **Method flexibility**: Allow POST/PUT interchangeability with warning
3. **Split endpoint detection**: Recognize `foo/request` + `foo/store` as implementing `foo`

### Proposed Exit Code Changes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Perfect match | Pass |
| 1 | Warnings only (aliases, method diff) | Pass with warning |
| 2 | Missing required endpoints | Fail |
| 3 | Extra undocumented endpoints | Pass with warning |
| 4 | Frontend calls missing endpoints | Fail |

---

## Quick Reference: Canonical RMOS Workflow Endpoints

| Operation | Canonical Endpoint | Method |
|-----------|-------------------|--------|
| Create session | `/api/rmos/workflow/sessions` | POST |
| Get session | `/api/rmos/workflow/sessions/{session_id}` | GET |
| List sessions | `/api/rmos/workflow/sessions` | GET |
| Set design | `/api/rmos/workflow/sessions/{session_id}/design` | POST |
| Set context | `/api/rmos/workflow/sessions/{session_id}/context` | POST |
| Request feasibility | `/api/rmos/workflow/sessions/{session_id}/feasibility/request` | POST |
| Store feasibility | `/api/rmos/workflow/sessions/{session_id}/feasibility/store` | POST |
| Approve | `/api/rmos/workflow/approve` | POST |
| Reject | `/api/rmos/workflow/reject` | POST |
| Request toolpaths | `/api/rmos/workflow/sessions/{session_id}/toolpaths/request` | POST |
| Store toolpaths | `/api/rmos/workflow/sessions/{session_id}/toolpaths/store` | POST |
| Require revision | `/api/rmos/workflow/sessions/{session_id}/revision` | POST |
| Archive | `/api/rmos/workflow/sessions/{session_id}/archive` | POST |
| Save snapshot | `/api/rmos/workflow/sessions/{session_id}/save-snapshot` | POST |
| Get snapshot | `/api/rmos/workflow/sessions/{session_id}/snapshot` | GET |
| Get events | `/api/rmos/workflow/sessions/{session_id}/events` | GET |
| List generators | `/api/rmos/workflow/generators` | GET |

---

## CAM Consolidated Endpoints (Wave 18)

> **Added 2025-12-27**: Consolidated CAM router provides organized endpoints under `/api/cam/<category>`.

### Drilling (`/api/cam/drilling`)

| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/cam/drilling/gcode` | Generate drilling G-code |
| GET | `/api/cam/drilling/info` | Get drilling operation info |
| POST | `/api/cam/drilling/pattern/gcode` | Generate pattern drilling G-code |
| GET | `/api/cam/drilling/pattern/info` | Get pattern info |

### Toolpath (`/api/cam/toolpath`)

| Method | Endpoint | Notes |
|--------|----------|-------|
| POST | `/api/cam/toolpath/roughing/gcode` | Generate roughing G-code |
| GET | `/api/cam/toolpath/roughing/info` | Get roughing operation info |
| POST | `/api/cam/toolpath/biarc/gcode` | Generate contour-following G-code |
| GET | `/api/cam/toolpath/biarc/info` | Get biarc operation info |
| POST | `/api/cam/toolpath/helical_entry` | Generate helical plunge G-code |
| GET | `/api/cam/toolpath/helical_health` | Health check |
| POST | `/api/cam/toolpath/vcarve/preview_infill` | Generate V-carve infill preview |

### Other Consolidated Categories

| Category | Prefix | Description |
|----------|--------|-------------|
| Fret Slots | `/api/cam/fret_slots` | Fret slot CAM preview and export |
| Relief | `/api/cam/relief` | Relief carving operations |
| Risk | `/api/cam/risk` | CAM risk reports and aggregation |
| Rosette | `/api/cam/rosette` | Rosette toolpath generation |
| Simulation | `/api/cam/simulation` | G-code parsing and simulation |
| Export | `/api/cam/export` | SVG, post-processor, DXF export |
| Monitoring | `/api/cam/monitoring` | CAM metrics and logs |
| Pipeline | `/api/cam/pipeline` | Pipeline execution and presets |
| Utility | `/api/cam/utility` | Settings, backup, optimization |

---

## CAM Intent Endpoints (H7.2)

> **Added 2025-12-27**: Intent-native CAM endpoints using `CamIntentV1` envelope.

### Roughing G-code Intent (`/api/cam/roughing`)

| Method | Endpoint | Query Params | Notes |
|--------|----------|--------------|-------|
| POST | `/api/cam/roughing/gcode_intent` | `strict=bool` | H7.2.2: Intent-native roughing |

**Request Body:** `CamIntentV1` envelope with roughing-specific `design` fields.

**Query Parameters:**
- `strict=false` (default): Returns 200 with issues in response body
- `strict=true`: Returns 422 if normalization issues exist (H7.2.3)

**Response (200):**
```json
{
  "gcode": "G21\nG90\n...",
  "status": "OK" | "OK_WITH_ISSUES",
  "issues": [
    {"code": "STEPDOWN_EXCEEDS_DEPTH", "message": "...", "path": "design.stepdown_mm"}
  ]
}
```

**Response (422 - strict mode only):**
```json
{
  "detail": {
    "error": "CAM_INTENT_NORMALIZATION_ISSUES",
    "issues": [...]
  }
}
```

**Metrics:**
- `cam_roughing_intent_requests_total` — Total requests
- `cam_roughing_intent_issues_total` — Requests with normalization issues
- `cam_roughing_intent_strict_rejects_total` — Strict mode rejections
- `cam_roughing_intent_latency_ms` — Request latency histogram

---

## Compare Consolidated Endpoints (Wave 19)

> **Added 2025-12-27**: Consolidated Compare router at `/api/compare`.

### Categories

| Category | Prefix | Description |
|----------|--------|-------------|
| Baselines | `/api/compare/baselines` | Baseline CRUD and geometry diff |
| Risk | `/api/compare/risk` | Risk aggregation, bucket detail, export |
| Lab | `/api/compare/lab` | Compare Lab UI endpoints |
| Automation | `/api/compare/automation` | SVG compare automation |

---

## Legacy Route Governance

> **Added 2025-12-27**: All legacy routes now tracked via governance middleware.

### Tagged Routes

Legacy routes have `"Legacy"` in their FastAPI tags array. The `EndpointGovernanceMiddleware` detects this and:
1. Records hits to `/api/governance/stats`
2. Logs warnings (once per process) for legacy endpoint access
3. Enables usage-based deprecation decisions

### Checking Usage

```bash
# Get governance stats
curl http://localhost:8000/api/governance/stats

# Response includes legacy route hit counts
{
  "legacy_hits": {
    "GET /api/cam/vcarve/preview": 142,
    "POST /api/compare/baseline": 0,
    ...
  }
}
```

### Deprecation Workflow

1. Deploy with legacy routes tagged
2. Monitor `/api/governance/stats` for 1-2 weeks
3. Routes with zero hits → safe to remove
4. Routes with hits → migrate frontend first, then remove

---

## Frontend Legacy Usage Audit

> **Added 2025-12-27**: CI gate scans frontend for legacy API endpoint usage.

### CI Gate

The `legacy_usage_gate.py` script scans frontend code and fails CI if legacy usage exceeds budget.

```bash
# Run manually
cd services/api
python -m app.ci.legacy_usage_gate \
  --roots "../../packages/client/src" "../../packages/sdk/src" \
  --budget 10

# Exit codes:
# 0 = No legacy endpoints used
# 1 = Legacy usage within budget (warning)
# 2 = Legacy usage exceeds budget (fail)
```

### Current Frontend Legacy Usage (2025-12-27)

**8 legacy usages in 4 files** (budget: 10)

| File | Line | Legacy Path | Canonical Replacement |
|------|------|-------------|----------------------|
| `DrillingLab.vue` | 637 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` |
| `DrillingLab.vue` | 674 | `/api/cam/drill/gcode/download` | `/api/cam/drilling/gcode/download` |
| `CAMEssentialsLab.vue` | 364 | `/api/cam/roughing/gcode` | `/api/cam/toolpath/roughing/gcode` |
| `CAMEssentialsLab.vue` | 388 | `/api/cam/drill/gcode` | `/api/cam/drilling/gcode` |
| `CAMEssentialsLab.vue` | 451 | `/api/cam/biarc/gcode` | `/api/cam/toolpath/biarc/gcode` |
| `useRosettePatternStore.ts` | 21 | `/api/rosette-patterns` | `/api/art/rosette/pattern/patterns` |
| `useRosettePatternStore.ts` | 35 | `/api/rosette-patterns` | `/api/art/rosette/pattern/patterns` |
| `BridgeLabView.vue` | 517 | `/api/cam/roughing_gcode` | `/api/cam/toolpath/roughing/gcode` |

### Legacy Path Patterns Detected

| Pattern | Canonical Replacement | Notes |
|---------|----------------------|-------|
| `/api/cam/vcarve/*` | `/api/cam/toolpath/vcarve/*` | Wave 18 |
| `/api/cam/helical/*` | `/api/cam/toolpath/helical/*` | Wave 18 |
| `/api/cam/biarc/*` | `/api/cam/toolpath/biarc/*` | Wave 18 |
| `/api/cam/roughing/*` | `/api/cam/toolpath/roughing/*` | Wave 18 (or use H7.2 intent) |
| `/api/cam/drill/*` | `/api/cam/drilling/*` | Wave 18 |
| `/api/cam/svg/*` | `/api/cam/export/*` | Wave 18 |
| `/api/rosette-patterns` | `/api/art/rosette/pattern/*` | Art Studio v2 |
| `/api/art-studio/workflow/*` | `/api/rmos/workflow/*` | RMOS canonical |
| `/api/art-studio/rosette/*` | `/api/art/rosette/*` | Art Studio v2 |

### Migration Priority

1. **High**: `useRosettePatternStore.ts` - Used by rosette pattern UI
2. **Medium**: `CAMEssentialsLab.vue` - CAM operations lab
3. **Medium**: `DrillingLab.vue` - Drilling operations
4. **Low**: `BridgeLabView.vue` - Bridge lab view
