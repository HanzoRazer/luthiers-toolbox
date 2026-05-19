# CAM Preview Route Conventions

**Date:** 2026-05-09  
**Status:** ACTIVE STANDARD  
**Scope:** Route naming and exposure conventions for governed preview

---

## Purpose

This document defines the canonical route patterns for governed CAM preview endpoints.

---

## Canonical Route Pattern

```
POST /api/cam/{domain}/preview
```

### Examples

| Operation | Route |
|-----------|-------|
| Nut slot | `POST /api/cam/nut-slot/preview` |
| Fret slot | `POST /api/cam/fret-slot/preview` |
| Drilling | `POST /api/cam/drilling/preview` |
| Profiling | `POST /api/cam/profiling/preview` |
| Binding | `POST /api/cam/binding/preview` |
| V-carve | `POST /api/cam/vcarve/preview` |
| Rosette | `POST /api/cam/rosette/preview` |

---

## Route Naming Rules

### Domain Naming

| Rule | Example | Counter-Example |
|------|---------|-----------------|
| Lowercase | `/nut-slot/` | `/NutSlot/` |
| Kebab-case | `/fret-slot/` | `/fret_slot/` |
| Singular operation | `/drilling/` | `/drill-holes/` |
| No version prefix | `/api/cam/` | `/api/v1/cam/` |

### Path Structure

```
/api/cam/{domain}/{action}
```

| Segment | Description |
|---------|-------------|
| `/api/` | API prefix |
| `/cam/` | CAM subsystem |
| `/{domain}/` | Operation domain |
| `/{action}` | Action (preview, gcode, export, etc.) |

---

## Action Suffixes

| Action | Purpose | Status |
|--------|---------|--------|
| `/preview` | Governed preview (JSON response) | GOVERNED PREVIEW |
| `/gcode` | G-code generation | GOVERNED EXPORT required |
| `/dxf` | DXF geometry export | Class B export |
| `/svg` | SVG visualization | Class A (viz only) |

### Current Standard

For GOVERNED PREVIEW status, only `/preview` action is allowed.

G-code and other machine-adjacent exports require GOVERNED EXPORT status.

---

## Route Expectations

### Preview Endpoints Must

1. **Return JSON**: Content-Type: application/json
2. **Include gate**: Response must have `gate` field
3. **Include coordinate_system**: Full coordinate metadata
4. **Include statistics**: Core statistics fields
5. **Be idempotent**: Same input produces same output
6. **Not produce machine output**: No G-code, no streaming

### Preview Endpoints Must Not

1. **Return G-code strings**: Even in response body
2. **Set Content-Disposition**: No file downloads
3. **Connect to machines**: No serial, no streaming
4. **Persist RMOS artifacts**: Preview is stateless

---

## Existing Routes Audit

### Compliant

| Route | Module | Notes |
|-------|--------|-------|
| `POST /api/cam/nut-slot/preview` | nut_slot_router.py | CANONICAL reference |

### Partially Compliant

| Route | Module | Issue |
|-------|--------|-------|
| `POST /api/cam/fret_slots/preview` | fret_slots_router.py | Underscore in path |
| `POST /api/cam/profiling/preview` | profile_router.py | Needs contract review |
| `POST /api/cam/binding/preview` | binding_router.py | Needs contract review |
| `POST /api/cam/vcarve/production/preview` | production_router.py | Extra `/production/` segment |

### Non-Standard

| Route | Issue |
|-------|-------|
| `POST /api/cam/rosette/preview` | In art_studio, not cam router |
| Various `/api/art/*/preview` | Art studio routes, not CAM |

---

## Route Registration

Governed preview routes must be registered in:

1. **Router file**: `app/cam/routers/{domain}/{domain}_router.py`
2. **Aggregator**: `app/cam/routers/aggregator.py`
3. **Manifest**: `app/router_registry/manifests/cam_manifest.py`

---

## Request Schema Convention

Request schemas should:

1. Use Pydantic BaseModel
2. Include Field() with descriptions
3. Include validation constraints (gt, ge, le, etc.)
4. Use `_mm` suffix for millimeter fields
5. Use `_deg` suffix for degree fields

Example:
```python
class FretSlotPreviewRequest(BaseModel):
    scale_length_mm: float = Field(..., gt=0, description="Scale length in mm")
    fret_count: int = Field(..., ge=1, le=36, description="Number of frets")
    slot_depth_mm: float = Field(default=3.0, gt=0, description="Slot depth in mm")
```

---

## Response Content-Type

| Action | Content-Type |
|--------|--------------|
| `/preview` | `application/json` |
| `/svg` | `image/svg+xml` |
| `/gcode` | `text/plain` (GOVERNED EXPORT only) |
| `/dxf` | `application/dxf` (GOVERNED EXPORT only) |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape |
| `CAM_PROMOTION_FRAMEWORK.md` | Promotion stages |
| `cam_manifest.py` | Router registration |

---

*Standard established: 2026-05-09*
