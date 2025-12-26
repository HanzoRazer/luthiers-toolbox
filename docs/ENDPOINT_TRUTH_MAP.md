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
| PUT | `/api/rmos/workflow/sessions/{session_id}/design` |
| POST | `/api/rmos/workflow/sessions/{session_id}/feasibility` |
| POST | `/api/rmos/workflow/sessions/{session_id}/approve` |
| POST | `/api/rmos/workflow/sessions/{session_id}/reject` |
| POST | `/api/rmos/workflow/sessions/{session_id}/request-revision` |
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

| Method | Endpoint |
|--------|----------|
| POST | `/api/art-studio/workflow/from-pattern` |
| POST | `/api/art-studio/workflow/from-generator` |
| POST | `/api/art-studio/workflow/from-snapshot` |
| GET | `/api/art-studio/workflow/sessions` |
| GET | `/api/art-studio/workflow/sessions/{session_id}` |
| PUT | `/api/art-studio/workflow/sessions/{session_id}/design` |
| POST | `/api/art-studio/workflow/sessions/{session_id}/feasibility` |
| POST | `/api/art-studio/workflow/sessions/{session_id}/approve` |
| POST | `/api/art-studio/workflow/sessions/{session_id}/reject` |
| POST | `/api/art-studio/workflow/sessions/{session_id}/request-revision` |
| POST | `/api/art-studio/workflow/sessions/{session_id}/save-snapshot` |
| GET | `/api/art-studio/workflow/generators` |

### Other

| Method | Endpoint |
|--------|----------|
| GET | `/api/presets_aggregate` |

---

## Duplicate Surface Warnings

> Endpoints that exist in multiple places. UI must target the correct one.

### Workflow Sessions

**DUPLICATE:** Same functionality at two prefixes.

| Surface A (RMOS) | Surface B (Art Studio) |
|------------------|------------------------|
| `GET /api/rmos/workflow/sessions` | `GET /api/art-studio/workflow/sessions` |
| `GET /api/rmos/workflow/sessions/{id}` | `GET /api/art-studio/workflow/sessions/{id}` |
| `PUT /api/rmos/workflow/sessions/{id}/design` | `PUT /api/art-studio/workflow/sessions/{id}/design` |
| `POST /api/rmos/workflow/sessions/{id}/feasibility` | `POST /api/art-studio/workflow/sessions/{id}/feasibility` |
| `POST /api/rmos/workflow/sessions/{id}/approve` | `POST /api/art-studio/workflow/sessions/{id}/approve` |
| `POST /api/rmos/workflow/sessions/{id}/reject` | `POST /api/art-studio/workflow/sessions/{id}/reject` |
| `POST /api/rmos/workflow/sessions/{id}/request-revision` | `POST /api/art-studio/workflow/sessions/{id}/request-revision` |
| `POST /api/rmos/workflow/sessions/{id}/save-snapshot` | `POST /api/art-studio/workflow/sessions/{id}/save-snapshot` |
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
| `POST /api/rmos/workflow/sessions/{id}/feasibility` | Session-scoped |
| `POST /api/art-studio/workflow/sessions/{id}/feasibility` | Legacy lane |

**Risk:** Different implementations, different response shapes.

**Recommendation:** Audit which UI components use which endpoint.

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
| RMOS Workflow | `/api/rmos/workflow` | 10 |
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
| Legacy Workflow | `/api/art-studio/workflow` | 12 |
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
