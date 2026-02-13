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
| 422 | Validation error |
| 500 | Internal server error |

---

## Related

- [API Overview](overview.md) - General information
- [Authentication](authentication.md) - Security
