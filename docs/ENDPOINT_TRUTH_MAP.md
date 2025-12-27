# Endpoint Truth Map

> Complete API surface area for Luthier's Toolbox (if all optional imports succeed).

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

| Domain | Prefix | Count |
|--------|--------|-------|
| RMOS AI | `/api/rmos/ai` | 5 |
| RMOS Profiles | `/api/rmos/profiles` | 7 |
| RMOS Profile History | `/api/rmos/profiles/history` | 5 |
| RMOS Logs | `/api/rmos/logs` | 3 |
| RMOS Strip Families | `/api/rmos/strip-families` | 5 |
| RMOS Patterns | `/api/rmos/patterns` | 5 |
| RMOS Saw Ops | `/api/rmos/saw-ops` | 2 |
| RMOS Runs | `/api/rmos/runs` | 17 |
| RMOS Workflow | `/api/rmos/workflow` | 17 |
| Root-mounted | `/` | 2 |
| Art Patterns | `/api/art/patterns` | 5 |
| Art Generators | `/api/art/generators` | 1 |
| Art Preview | `/api/art/rosette/preview` | 1 |
| Art Snapshots | `/api/art/snapshots` | 7 |
| Art Rosette Snapshots | `/api/art/rosette/snapshots` | 7 |
| Art Rosette Feasibility | `/api/art/rosette/feasibility` | 1 |
| Art Rosette Jobs | `/api/art/rosette/jobs` | 5 |
| Art Rosette Compare | `/api/art/rosette/compare` | 3 |
| Art Rosette Pattern | `/api/art/rosette/pattern` | 6 |
| Legacy Rosette | `/api/art-studio/rosette` | 5 |
| Legacy Workflow | `/api/art-studio/workflow` | 8 |
| Other | `/api` | 1 |
| **Total** | | **~115** |

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
