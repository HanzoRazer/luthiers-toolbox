# API Lane Consolidation Plan

> Eliminate "two-lane" confusion (duplicate endpoints + duplicate storage) while keeping the repo stable.

---

## 1. Canonical Lanes (Source of Truth)

### Art Studio Lane (Design-First)

| Aspect | Value |
|--------|-------|
| **URLs** | `/api/art/*` |
| **Code** | `services/api/app/art_studio/api/*` |
| **Storage** | `services/api/app/art_studio/services/*store*` |
| **Frontend** | `packages/client/*` binds exclusively to `/api/art/*` |

**Rationale:** Clean, predictable, maps to Phase 31.x "Art Studio Core Completion" philosophy.

### RMOS Lane (Manufacturing Oracle + Observability)

| Aspect | Value |
|--------|-------|
| **URLs** | `/api/rmos/*` |
| **Code** | `services/api/app/rmos/*` + `rmos/runs_v2/*` |
| **UI** | Log Viewer binds to `/api/rmos/logs/*` |

**Rationale:** Deterministic core; logs/runs_v2 is unified telemetry and replay spine.

---

## 2. Freeze vs Migrate

### A. Freeze (Compatibility Mode)

These routes remain available but receive only security/critical fixes.

#### Legacy Art Lane: `/api/art-studio/*`

```
/api/art-studio/rosette/*      (preview/export/presets)
/api/art-studio/workflow/*     (sessions/approve/reject/save-snapshot)
```

**Status:** FROZEN. No new features.

#### Transitional Lane: `/rosette/*`

```
/rosette/snapshots/*
/rosette/feasibility/*
```

**Status:** FROZEN immediately. Do not build UI against it.

**Risk:** Inconsistent prefix, high "wrong endpoint" wiring risk.

---

### B. Migrate (Move to Canonical Lane)

#### Snapshots

| From | To |
|------|-----|
| `/rosette/snapshots/*` | `/api/art/snapshots/*` |
| Any legacy snapshot endpoints | `/api/art/snapshots/*` |

**Migration:** Ensure `/api/art/snapshots/*` supports all required fields (spec, feasibility, metadata, run_id link).

#### Preview Rendering

| From | To |
|------|-----|
| `/api/art-studio/rosette/preview` | `/api/art/rosette/preview/svg` |

**Migration:** Keep output contract stable (same viewBox rules, same scale assumptions).

#### Workflow Sessions

| From | To |
|------|-----|
| `/api/art-studio/workflow/*` | `/api/art/*` or `/api/rmos/workflow/*` |

**Decision required:** Pick one owner:
- Art Studio = design-only state
- RMOS = governed state machine

Do not keep both.

---

## 3. Consolidation Mechanics

### Step 1: Lane Policy Doc

Create this document. Done.

**Policy:**
- All new Art Studio endpoints must be under `/api/art/*`
- Legacy `/api/art-studio/*` is frozen
- `/rosette/*` is transitional and will be removed

### Step 2: Deprecation Headers

For frozen legacy endpoints, add:

```python
response.headers["Deprecation"] = "true"
response.headers["Sunset"] = "2025-06-01"
response.headers["Link"] = '</api/art/...>; rel="successor-version"'
```

Server log warning:
```python
logger.warning("DEPRECATED endpoint hit: %s successor=%s", request.path, successor_path)
```

### Step 3: Frontend Cutover

Single PR to update UI clients:
- Call `/api/art/*` only for Art Studio operations
- Never call `/api/art-studio/*` or `/rosette/*`

### Step 4: Block New Legacy Features

PR review rule:
- Any new endpoint touching `/api/art-studio/*` or `/rosette/*` must justify why it's not `/api/art/*`
- Otherwise reject

### Step 5: Remove Duplicate Mounts

Once usage drops to near zero:
1. Stop mounting `/rosette/*` routers
2. Stop mounting `/api/art-studio/*` routers (or keep behind feature flag)
3. Delete dead code after stabilization window

---

## 4. Timeline

### Phase A (Now)

- [x] Document lane policy (this doc)
- [ ] Freeze legacy lanes (no new features)
- [ ] Add deprecation headers
- [ ] Cutover frontend to `/api/art/*`

### Phase B (After 1-2 Release Cycles)

- [ ] Add metrics: count hits to deprecated endpoints
- [ ] Remove `/rosette/*` mounts (most confusing)

### Phase C (When Stable)

- [ ] Remove `/api/art-studio/*` mounts
- [ ] Or keep behind `ENABLE_LEGACY_ART_STUDIO=1` flag

---

## 5. Migration Matrix

| Area | Freeze | Migrate To | Owner |
|------|--------|------------|-------|
| Art Studio core APIs | No | `/api/art/*` | Art Studio |
| Legacy Art Studio routes | `/api/art-studio/*` | `/api/art/*` | Art Studio |
| No-prefix rosette routes | `/rosette/*` | `/api/art/*` | Art Studio |
| Feasibility | Legacy endpoints | `/api/art/rosette/feasibility/batch` | RMOS authority, Art Studio caller |
| Logs / runs | No | `/api/rmos/logs/*` + `/api/rmos/runs/*` | RMOS |
| Preview rendering | Legacy preview | `/api/art/rosette/preview/svg` | Art Studio |
| Snapshots | Legacy endpoints | `/api/art/snapshots/*` | Art Studio |

---

## 6. Guardrails

### CI Check (Future)

Fail PRs that introduce new router prefixes `/rosette` or `/api/art-studio` unless `legacy-exception` label is present.

### Unit Test

Assert:
- Canonical endpoints exist
- Legacy endpoints return `Deprecation: true` header

---

## 7. Success Criteria

- [ ] UI uses only `/api/art/*` + `/api/rmos/*`
- [ ] Logs show near-zero traffic to `/api/art-studio/*` and `/rosette/*`
- [ ] Router mounts in `main.py` are simplified (one Art Studio lane + RMOS lane)
- [ ] Developers stop asking "which endpoint is real?"

---

## Quick Reference

### Canonical Endpoints

```
/api/art/patterns/*
/api/art/snapshots/*
/api/art/generators/*
/api/art/rosette/preview/svg
/api/art/rosette/feasibility/batch
/api/art/rosette/jobs/*
/api/art/rosette/compare/*
/api/art/rosette/pattern/*

/api/rmos/ai/*
/api/rmos/profiles/*
/api/rmos/logs/*
/api/rmos/runs/*
/api/rmos/workflow/*
/api/rmos/strip-families/*
/api/rmos/patterns/*
/api/rmos/saw-ops/*
```

### Deprecated Endpoints (Do Not Use)

```
/api/art-studio/rosette/*       → use /api/art/rosette/*
/api/art-studio/workflow/*      → use /api/rmos/workflow/*
/rosette/snapshots/*            → use /api/art/snapshots/*
/rosette/feasibility/*          → use /api/art/rosette/feasibility/*
/feasibility                    → use /api/art/rosette/feasibility/batch
/toolpaths                      → internal only
```
