# API Endpoints

Complete reference for all API endpoints.

---

## Health & Status

### GET /health

Check API health status.

**Response:**

```json
{
  "status": "ok",
  "version": "0.33.0"
}
```

---

## Calculators

### POST /api/calculators/string-tension

Calculate string tension using Mersenne's Law.

**Request:**

```json
{
  "scale_length_mm": 648,
  "strings": [
    {
      "gauge": 0.010,
      "pitch": "E4",
      "material": "plain_steel"
    }
  ]
}
```

**Response:**

```json
{
  "strings": [
    {
      "gauge": 0.010,
      "pitch": "E4",
      "frequency_hz": 329.63,
      "tension_lbs": 16.2,
      "tension_n": 72.1
    }
  ],
  "total_tension_lbs": 16.2,
  "total_tension_n": 72.1
}
```

---

### POST /api/calculators/fret-positions

Calculate fret positions for given scale length.

**Request:**

```json
{
  "scale_length_mm": 648,
  "fret_count": 22,
  "intonation_model": "equal_temperament_12"
}
```

**Response:**

```json
{
  "positions": [36.39, 70.63, 102.86, ...],
  "unit": "mm",
  "scale_length": 648,
  "fret_count": 22
}
```

---

### POST /api/calculators/convert

Convert between units.

**Request:**

```json
{
  "value": 25.4,
  "from_unit": "mm",
  "to_unit": "inches",
  "category": "length"
}
```

**Response:**

```json
{
  "result": 1.0,
  "from": "25.4 mm",
  "to": "1.0 inches"
}
```

---

### POST /api/calculators/board-feet

Calculate board feet.

**Request:**

```json
{
  "thickness_inches": 1.0,
  "width_inches": 8.0,
  "length_inches": 96.0,
  "quantity": 2
}
```

**Response:**

```json
{
  "board_feet": 10.67,
  "total_cubic_inches": 1536
}
```

---

## DXF Processing

### POST /api/dxf/upload

Upload a DXF file for processing.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| file | File | DXF file |

**Response:**

```json
{
  "id": "abc123",
  "filename": "body.dxf",
  "entity_count": 156,
  "layers": ["OUTLINE", "POCKETS", "HOLES"],
  "bounds": {
    "x_min": 0,
    "x_max": 400,
    "y_min": 0,
    "y_max": 200
  },
  "issues": []
}
```

---

### GET /api/dxf/validate/{id}

Get validation results for uploaded DXF.

**Response:**

```json
{
  "valid": true,
  "issues": [],
  "warnings": [
    {
      "type": "open_contour",
      "layer": "OUTLINE",
      "count": 2
    }
  ]
}
```

---

## CAM Operations

### POST /api/cam/pocket

Generate pocket toolpath.

**Request:**

```json
{
  "geometry_id": "abc123",
  "layer": "POCKETS",
  "tool": {
    "diameter": 6.0,
    "flutes": 2
  },
  "params": {
    "stepover_pct": 45,
    "stepdown": 2.0,
    "depth": 10.0,
    "feed_rate": 2000,
    "plunge_rate": 500,
    "rpm": 18000
  }
}
```

**Response:**

```json
{
  "id": "job123",
  "status": "completed",
  "stats": {
    "total_distance_mm": 5420,
    "estimated_time_sec": 342
  }
}
```

---

### POST /api/cam/contour

Generate contour toolpath.

**Request:**

```json
{
  "geometry_id": "abc123",
  "layer": "OUTLINE",
  "tool": {
    "diameter": 6.0,
    "flutes": 2
  },
  "params": {
    "offset": "outside",
    "depth": 20.0,
    "stepdown": 3.0,
    "tabs": {
      "enabled": true,
      "count": 4,
      "width": 8.0,
      "height": 2.0
    }
  }
}
```

---

### GET /api/cam/preview/{id}

Get toolpath preview data.

**Response:**

```json
{
  "id": "job123",
  "paths": [...],
  "bounds": {...},
  "stats": {
    "total_distance_mm": 5420,
    "cutting_distance_mm": 4200,
    "rapid_distance_mm": 1220,
    "estimated_time_sec": 342
  }
}
```

---

### GET /api/cam/export/{id}

Download G-code.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| post | string | Post processor (grbl, mach, etc.) |
| units | string | Output units (mm, inch) |

**Response:** `text/plain` G-code file

---

### POST /api/cam/retract/gcode

### POST /api/cam/retract/gcode/download

### POST /api/cam/retract/gcode_governed

### POST /api/cam/retract/gcode/download_governed

Retract G-code generation.

> **BREAKING CHANGE — all four routes now fail closed.**
>
> These routes previously emitted G-code. They no longer do. Every one of them
> returns **`409 SAFETY_BLOCKED`** and emits no machine output, and will keep
> doing so until a substantive retract feasibility evaluator exists.
>
> This is a deliberate change of the *public* contract on unchanged URLs, made
> under the owner ruling of 2026-08-23 (RMOS-CONVERGE-001B): the governing unit
> is the production capability, not the URL suffix, and an ungoverned
> convenience endpoint is not an accepted alternate production path.

**What changed for callers:**

| | Before | Now |
|---|---|---|
| `POST /gcode` | `200` `text/plain` G-code, `X-ToolBox-Lane: draft`, no run or hash | `409 SAFETY_BLOCKED`, no G-code |
| `POST /gcode/download` | `200` `.nc` attachment, `X-ToolBox-Lane: draft`, no run or hash | `409 SAFETY_BLOCKED`, no attachment |
| `POST /gcode_governed` | `200` G-code wrapped in a run carrying a self-minted `GREEN` decision | `409 SAFETY_BLOCKED`, no G-code |
| `POST /gcode/download_governed` | `200` `.nc` wrapped in the same self-minted run | `409 SAFETY_BLOCKED`, no attachment |

The `_governed` suffix no longer denotes a second lane. Each suffixed route is a
retained alias of its plain counterpart and returns an identical response.

**If you consume these routes, you must:**

- check the status before treating a response body as G-code. A `409` body is
  JSON; saving it as a `.nc` file writes an error message to a machine program;
- stop branching on `X-ToolBox-Lane: draft` for the plain routes. The old draft
  lane is gone and is not coming back when an evaluator lands;
- expect no `X-GCode-SHA256` and no `Content-Disposition` on a blocked response.

**Consumer impact, plainly:** clients that keyed on `draft` or assumed all
`200` / POST export bodies were G-code must change. The in-tree Vue retract
card now surfaces the safety block instead of saving the 409 JSON as `.nc`.

**Parameter binding (do not confuse the two families):**

| Route | How parameters bind |
|---|---|
| `POST /gcode`, `POST /gcode_governed` | Query string: `strategy`, `current_z`, `safe_z`, `ramp_feed`, `helix_radius`, `helix_pitch`. A JSON body is **ignored**. |
| `POST /gcode/download`, `POST /gcode/download_governed` | JSON body (`RetractStrategyIn`). |

The in-tree Vue exporter talks to `POST /gcode`. It previously POSTed a JSON
body and silently received defaults; it now sends the same fields as query
params. That is a bug fix, not a change in what FastAPI accepts.

**Blocked response:**

```json
{
  "detail": {
    "error": "SAFETY_BLOCKED",
    "message": "Retract G-code generation blocked by server-side safety policy.",
    "run_id": "run_2f1c…",
    "decision": { "risk_level": "UNKNOWN", "...": "..." },
    "authoritative_feasibility": { "...": "..." }
  }
}
```

Blocked attempts remain auditable: a `BLOCKED` run artifact is persisted with the
feasibility hash, and with no `gcode_sha256` and no attachments. Look it up with
`GET /api/rmos/runs_v2/runs/{run_id}` using the `run_id` from the response.

**Note on retract strategies.** The two route families accept different strategy
vocabularies — `/gcode` takes `direct | ramped | helical`, `/gcode/download`
takes `minimal | safe | incremental` (default `safe`). Reconciling them is a
pending ruling; until then, do not assume a value valid on one is valid on the
other.

---

## RMOS (Safety)

### GET /api/rmos/runs_v2/runs

List manufacturing runs.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | int | Results per page (default: 20) |
| offset | int | Pagination offset |
| risk_level | string | Filter by GREEN/YELLOW/RED |

**Response:**

```json
{
  "items": [
    {
      "run_id": "run123",
      "created_at": "2025-01-15T14:30:00Z",
      "decision": "GREEN",
      "export_allowed": true
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

---

### GET /api/rmos/runs_v2/runs/{id}

Get run details.

**Response:**

```json
{
  "run_id": "run123",
  "created_at": "2025-01-15T14:30:00Z",
  "decision": "YELLOW",
  "rules_triggered": [
    {
      "id": "F010",
      "level": "YELLOW",
      "message": "High stepover percentage"
    }
  ],
  "export_allowed": true,
  "override": null
}
```

---

### POST /api/rmos/feasibility/check

Check operation feasibility.

**Request:**

```json
{
  "geometry": {
    "width_mm": 100,
    "length_mm": 200,
    "depth_mm": 10
  },
  "tool": {
    "diameter": 6.0,
    "flute_length_mm": 20
  },
  "material": {
    "id": "hardwood",
    "hardness": "hard"
  },
  "params": {
    "stepdown": 3.0,
    "stepover_pct": 50
  }
}
```

**Response:**

```json
{
  "decision": "GREEN",
  "rules_triggered": [],
  "export_allowed": true
}
```

---

### POST /api/rmos/runs_v2/runs/{id}/override

Apply operator override.

**Request:**

```json
{
  "reason": "Tested with scrap material, parameters acceptable",
  "risk_acknowledged": true
}
```

**Response:**

```json
{
  "status": "ok",
  "override_applied": true,
  "export_allowed": true
}
```

---

## Machine Profiles

### GET /api/machines/profiles

List machine profiles.

**Response:**

```json
{
  "profiles": [
    {
      "id": "shapeoko4",
      "name": "Shapeoko 4 XXL",
      "work_area": {"x": 838, "y": 838, "z": 95}
    }
  ]
}
```

---

### POST /api/machines/profiles

Create machine profile.

**Request:**

```json
{
  "name": "My CNC",
  "work_area": {"x": 600, "y": 400, "z": 80},
  "limits": {
    "max_feed_xy": 8000,
    "max_feed_z": 3000,
    "max_rpm": 24000
  },
  "controller": "grbl"
}
```

---

## Art Studio

### POST /api/art-studio/rosette

Generate rosette pattern.

**Request:**

```json
{
  "pattern_type": "concentric_rings",
  "inner_diameter": 100,
  "outer_diameter": 130,
  "params": {
    "ring_count": 5,
    "ring_widths": [2, 1, 5, 1, 2]
  }
}
```

**Response:**

```json
{
  "id": "rosette123",
  "geometry": {...},
  "dxf": "..."
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing the problem",
  "status_code": 400
}
```

### Common Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 409 | Blocked by server-side safety policy (`SAFETY_BLOCKED`) — the operation was refused before any machine output was generated. The body carries the authoritative decision and a `run_id`; it is **not** machine output. |
| 422 | Validation error |
| 500 | Internal server error |

---

## Related

- [API Overview](overview.md) - General information
- [Authentication](authentication.md) - Security
