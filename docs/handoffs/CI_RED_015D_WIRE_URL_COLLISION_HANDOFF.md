# CI-RED-015-D: Wire URL Collision Audit Handoff

**Created:** 2026-05-28  
**Sprint:** CI-RED-015-D  
**Audit Tool:** `services/api/scripts/audit_wire_urls.py`  
**Output:** `services/api/metrics/wire_url_audit.json`

---

## Executive Summary

The existing `audit_endpoints.py` measures **decorator paths only**, not actual wire URLs. This creates false positives: a decorator `@router.get("/status")` in different manifested routers appears as a "duplicate" even when the files mount at different prefixes (e.g., `/api/cam/assist/status` vs `/api/acoustics/status`).

This audit implements **wire URL resolution**:
```
wire_url = manifest_prefix + router_prefix + decorator_path
```

**Results:**
| Metric | Count |
|--------|-------|
| Total endpoints | 1181 |
| Manifested files | 141 |
| Unmanifested files | 143 |
| Unmanifested endpoints | 580 |
| Decorator "duplicates" | 124 |
| **False positives** | 85 |
| **Actual wire URL collisions** | 68 |

The debt gate has been measuring the wrong thing. 85 of 124 decorator duplicates are false positives — routers with the same decorator path but different wire URLs.

---

## Wire URL Collisions (68 Total)

These are **real routing bugs** — multiple files define the same HTTP method + wire URL.

### Critical Collisions (High Traffic Routes)

| Wire URL | Files | Severity |
|----------|-------|----------|
| `POST /gcode` | 11 | CRITICAL |
| `GET /info` | 7 | HIGH |
| `POST /preview` | 6 | HIGH |
| `GET /patterns` | 5 | MEDIUM |
| `GET /status` | 4 | MEDIUM |
| `GET /materials` | 4 | MEDIUM |
| `GET /` | 4 | HIGH |
| `POST /dxf` | 3 | HIGH |
| `GET /templates` | 3 | MEDIUM |
| `POST /calculate` | 3 | MEDIUM |

### Detailed Collision Report

#### `POST /gcode` — 11 files

| File | Manifest Status |
|------|-----------------|
| `routers/neck/headstock_transition_export.py` | Manifested |
| `routers/simulation_consolidated_router.py` | Manifested |
| `routers/adaptive/gcode_router.py` | UNMANIFESTED |
| `routers/neck/neck_profile_export.py` | UNMANIFESTED |
| `routers/retract/retract_gcode_router.py` | UNMANIFESTED |
| `cam/routers/drilling/drill_modal_router.py` | UNMANIFESTED |
| `cam/routers/profiling/profile_router.py` | UNMANIFESTED |
| `cam/routers/toolpath/biarc_router.py` | UNMANIFESTED |
| `cam/routers/toolpath/roughing_router.py` | UNMANIFESTED |
| `cam/routers/toolpath/vcarve_router.py` | UNMANIFESTED |
| `cam/routers/vcarve/production_router.py` | UNMANIFESTED |

**Root cause:** Generic `/gcode` path without domain prefix. Only 2 are manifested; FastAPI loads whichever appears first.

#### `GET /info` — 7 files

| File | Manifest Status |
|------|-----------------|
| `routers/registry_router.py` | Manifested |
| `cam/routers/binding/binding_router.py` | UNMANIFESTED |
| `cam/routers/drilling/drill_modal_router.py` | UNMANIFESTED |
| `cam/routers/profiling/profile_router.py` | UNMANIFESTED |
| `cam/routers/toolpath/biarc_router.py` | UNMANIFESTED |
| `cam/routers/toolpath/roughing_router.py` | UNMANIFESTED |
| `cam/routers/vcarve/production_router.py` | UNMANIFESTED |

**Root cause:** Every CAM router defines `/info` without a unique prefix.

#### `POST /preview` — 6 files

| File | Manifest Status |
|------|-----------------|
| `art_studio/api/rosette_designer_routes.py` | Manifested |
| `routers/cam/guitar/acoustic_cam_router.py` | UNMANIFESTED |
| `cam/routers/binding/binding_router.py` | UNMANIFESTED |
| `cam/routers/drilling/drilling_preview_router.py` | UNMANIFESTED |
| `cam/routers/profiling/profile_router.py` | UNMANIFESTED |
| `cam/routers/vcarve/production_router.py` | UNMANIFESTED |

**Root cause:** Multiple preview endpoints without domain isolation.

#### Domain-Specific Collisions

| Wire URL | Files | Notes |
|----------|-------|-------|
| `POST /soundhole/spiral/geometry` | 2 | woodworking_router + instrument_geometry/soundhole_router |
| `POST /soundhole/spiral/dxf` | 2 | Same as above |
| `GET /runs` | 2 | rmos/runs_v2/api_runs + acoustics_router |
| `GET /runs/{run_id}` | 2 | Same as above |
| `POST /import-zip` | 2 | rmos/runs_v2/acoustics_router + rmos/acoustics/router_import |
| `GET /attachments/{sha256}` | 2 | acoustics_router + api_global_attachments |

---

## False Positive Analysis (85 Cases)

These are decorator paths that appear duplicated but resolve to **different wire URLs**. The existing debt gate counts these as problems when they are not.

**Example:**
- `routers/soundhole_router.py` defines `@router.get("/types")`
  - Mounted at `/api/instrument/soundhole` → wire URL `/api/instrument/soundhole/types`
- `routers/binding_design_router.py` defines `@router.get("/types")`
  - Mounted at `/api/binding` → wire URL `/api/binding/types`

Same decorator path, different wire URLs. **Not a collision.**

The debt gate should measure **wire URL collisions**, not decorator duplicates.

---

## Unmanifested Routers (143 files, 580 endpoints)

Files with `@router` decorators that have no entry in `router_registry/manifests/`.

### Top Offenders by Endpoint Count

| File | Endpoints |
|------|-----------|
| `core/store_registry.py` | 12 |
| `routers/probe/setup_router.py` | 11 |
| `api/deps/rmos_stores.py` | 10 |
| `cam/routers/toolpath/roughing_router.py` | 9 |
| `cam/routers/vcarve/production_router.py` | 9 |
| `cam/routers/profiling/profile_router.py` | 8 |
| `routers/cam/guitar/acoustic_cam_router.py` | 8 |
| `cam/routers/drilling/drill_modal_router.py` | 7 |
| `business/bom_router.py` | 7 |
| `rmos/api_routes.py` | 7 |

### Impact

- **49% of files** with router decorators are unmanifested
- **49% of endpoints** (580/1181) come from unmanifested routers
- Unmanifested routers receive **no manifest prefix**, causing most collisions

---

## Collision Patterns

### Pattern 1: Generic Path Without Prefix

```python
# In cam/routers/drilling/drill_modal_router.py
router = APIRouter()  # No prefix

@router.post("/gcode")  # Collides with 10 other files
def generate_gcode(): ...
```

**Fix:** Add prefix to APIRouter or ensure manifest entry with prefix.

### Pattern 2: Duplicate Routers (Legacy + New)

```python
# Both files define same paths:
# routers/woodworking_router.py (manifested)
# routers/instrument_geometry/soundhole_router.py (unmanifested)

@router.post("/soundhole/spiral/geometry")
@router.post("/soundhole/spiral/dxf")
```

**Fix:** Remove one, add redirect, or consolidate.

### Pattern 3: Module Duplication

```python
# routers/simulation_consolidated_router.py (manifested)
# cam/routers/simulation/simulation_consolidated_router.py (unmanifested)
```

Same file appears in two locations. One should be deleted.

---

## Recommended Actions

### Immediate (CI-RED-015-D-b)

1. **Update debt gate** to measure wire URL collisions, not decorator duplicates
   - Use `scripts/audit_wire_urls.py` output instead of `audit_endpoints.py`
   - New gate threshold: 0 wire URL collisions (currently 68)

2. **Fix critical collision:** `POST /gcode`
   - Choose canonical location (likely `cam/routers/toolpath/`)
   - Add manifest prefix to other gcode generators
   - Pattern: `/api/{domain}/gcode` (e.g., `/api/cam/drill/gcode`)

### Short-term (CI-RED-015-D-c)

3. **Manifest the unmanifested**
   - Add manifest entries for legitimate routers
   - Delete dead/duplicate routers
   - Target: reduce 143 unmanifested files to <20

4. **Fix soundhole collision**
   - `woodworking_router.py` vs `instrument_geometry/soundhole_router.py`
   - Per memory `feedback_spiral_location.md`: spiral goes in `instrument_geometry/`
   - Mark `woodworking_router.py` soundhole endpoints deprecated

### Long-term

5. **Establish prefix discipline**
   - All new routers must have either:
     - `APIRouter(prefix="/domain/...")` in the file, OR
     - A manifest entry with a non-empty prefix
   - Add pre-commit check for new router files

---

## Tool Reference

### Running the Audit

```bash
cd services/api
python scripts/audit_wire_urls.py
```

### Output Files

- `metrics/wire_url_audit.json` — full audit data (collisions, false positives, unmanifested)
- Console output — summary + detailed collision report

### Key Functions

```python
# Wire URL computation
def compute_wire_url(manifest_prefix, router_prefix, decorator_path):
    parts = [manifest_prefix, router_prefix, decorator_path]
    wire_url = "/".join(p.strip("/") for p in parts if p.strip("/"))
    return "/" + wire_url if wire_url else "/"
```

---

## Debt Gate Recommendation

**Current gate:** Measures decorator-path duplicates (inflated by false positives)

**Proposed gate:** Measure `wire_url_collisions` from `wire_url_audit.json`

```python
# In debt gate
audit = json.load(open("metrics/wire_url_audit.json"))
collision_count = audit["summary"]["wire_url_collisions"]
assert collision_count == 0, f"Wire URL collisions: {collision_count}"
```

The 124 "decorator duplicates" included 85 false positives. The real problem is 68 wire URL collisions — a smaller but more actionable number.

---

## Appendix: Collision Index

All 68 wire URL collisions by category:

| Category | Count | Wire URLs |
|----------|-------|-----------|
| CAM/Toolpath | 23 | `/gcode`, `/info`, `/preview`, `/materials` |
| RMOS | 8 | `/runs`, `/runs/{run_id}`, `/import-zip`, `/attachments/{sha256}` |
| Business | 6 | `/calculate`, `/templates`, `/bom` |
| Instrument | 6 | `/bridge`, `/soundhole/spiral/*` |
| Core | 5 | `/`, `/patterns`, `/status` |
| Export | 4 | `/dxf`, `/validate` |
| Other | 16 | Various |
