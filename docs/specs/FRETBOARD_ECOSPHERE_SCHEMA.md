# Fretboard Ecosphere Schema Reference

Canonical Pydantic schema for fretboard geometry, served by the
`/api/v1/fretboard/*` API. This document is the field-by-field reference.
For worked examples, see `data/ecosphere_samples/`.

**Schema version:** 1.0.0  
**Last updated:** 2026-04-30  
**Source:** `services/api/app/instrument_geometry/neck/fretboard_ecosphere.py`

---

## Overview

The `FretboardEcosphere` is the single source of truth for fretboard
geometry. Every projection (DXF, SVG, JSON, Scala) reads from the same
canonical document. The math kernels (`alternative_temperaments`,
`fret_math`, `scala_loader`) populate the document; the projections consume it.

**Request flow:**
```
FretboardInput (JSON)
    → POST /api/v1/fretboard/compute
    → FretboardEcosphere.compute(params)
    → FretboardEcosphere (JSON response)
```

**Projection flow:**
```
FretboardEcosphere
    → write_ecosphere_dxf()  → DXF bytes (9 layers)
    → to_scala_intervals()   → Scala .scl file
    → JSON serialization     → API response
```

---

## FretboardInput (Request Shape)

Top-level request shape. Posted to `/api/v1/fretboard/compute`.

### Scale Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `scale_type` | ScaleType | `"standard"` | `"standard"` or `"multiscale"` |
| `scale_length_mm` | float | 648.0 | Scale length in mm. For multiscale, this is the treble side. |
| `bass_scale_length_mm` | float? | null | Bass scale length (required when `scale_type="multiscale"`) |

### String Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `string_count` | int | 6 | Number of strings (1-18) |

### Fret Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fret_count` | int | 22 | Number of frets (1-36) |
| `perpendicular_fret` | int | 0 | Fret that is perpendicular to centerline (multiscale only; 0 = nut) |
| `temperament` | TemperamentType | `"equal_12"` | Tuning temperament (see Temperament Types below) |

### Width Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nut_width_mm` | float | 42.0 | Fretboard width at nut (gt 0, le 100) |
| `heel_width_mm` | float? | null | Width at last fret (null = auto-compute from taper) |
| `edge_offset_mm` | float | 3.0 | String setback from fretboard edge (0-10mm) |

### Radius Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `radius` | RadiusSpec | `{nut_radius_mm: 241.3}` | Compound radius specification (see Reference) |

### Other Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `extension_mm` | float | 0.0 | Length past last fret (0-50mm) |
| `slot_width_mm` | float | 0.58 | Fret slot width for DXF projection. Default matches Jescar 47104 tang. |
| `intonation_offsets_mm` | Dict[int, float] | `{}` | Per-string saddle compensation `{string_index: offset_mm}` |

### Temperament Types

| Value | Description |
|-------|-------------|
| `equal_12` | Standard 12-tone equal temperament |
| `equal_19` | 19-tone equal temperament |
| `equal_24` | 24-tone equal temperament (quarter-tones) |
| `equal_31` | 31-tone equal temperament |
| `pythagorean` | Pythagorean tuning (pure fifths) |
| `just_major` | Just intonation (major scale) |
| `meantone_quarter` | Quarter-comma meantone |

---

## FretboardEcosphere (Response Shape)

Top-level response shape. Returned from `/api/v1/fretboard/compute`.

| Field | Type | Description |
|-------|------|-------------|
| `input_params` | FretboardInput | Echo of the request for traceability |
| `fret_lines` | List[FretLine] | One per fret including nut at index 0 (see Reference) |
| `string_paths` | List[StringPath] | One per string from nut to bridge (see Reference) |
| `outline_points` | List[Tuple[float, float]] | 4 (x, y) points forming fretboard outline |
| `total_length_mm` | float | Nut to end of extension |
| `max_width_mm` | float | Width at widest point (heel) |
| `max_fret_angle_deg` | float | Maximum fret angle in degrees (0 for standard, >0 for multiscale) |
| `version` | str | Schema version (currently "1.0.0") |

---

## Worked Examples

### Single-Scale 25.5" 12-TET (Fender Strat)

**Request:**
```json
{
  "scale_length_mm": 647.7,
  "fret_count": 22,
  "temperament": "equal_12",
  "string_count": 6,
  "slot_width_mm": 0.58
}
```

**Response (abbreviated):**
```json
{
  "input_params": {
    "scale_type": "standard",
    "scale_length_mm": 647.7,
    "fret_count": 22,
    "temperament": "equal_12",
    "string_count": 6,
    "slot_width_mm": 0.58,
    ...
  },
  "fret_lines": [
    {
      "fret_number": 0,
      "points": [
        {"fret_number": 0, "string_index": 0, "x_mm": 0.0, "y_mm": -21.0},
        ...
      ],
      "angle_rad": 0.0,
      "is_perpendicular": true
    },
    ...
  ],
  "string_paths": [...],
  "outline_points": [[0.0, -21.0], [588.84, -28.0], [588.84, 28.0], [0.0, 21.0]],
  "total_length_mm": 588.84,
  "max_width_mm": 56.0,
  "max_fret_angle_deg": 0.0,
  "version": "1.0.0"
}
```

**Full response:** `data/ecosphere_samples/single_scale_fender_strat.json`

---

### Fan-Fret Smart Guitar Pro (686/648mm, perpendicular at fret 12)

**Request:**
```json
{
  "scale_type": "multiscale",
  "bass_scale_length_mm": 686.0,
  "scale_length_mm": 648.0,
  "fret_count": 24,
  "temperament": "equal_12",
  "string_count": 6,
  "slot_width_mm": 0.58,
  "perpendicular_fret": 12
}
```

**Response (abbreviated):**
```json
{
  "input_params": {
    "scale_type": "multiscale",
    "scale_length_mm": 648.0,
    "bass_scale_length_mm": 686.0,
    "perpendicular_fret": 12,
    ...
  },
  "fret_lines": [
    {
      "fret_number": 12,
      "points": [...],
      "angle_rad": 0.0,
      "is_perpendicular": true
    },
    {
      "fret_number": 1,
      "points": [...],
      "angle_rad": 0.0142,
      "is_perpendicular": false
    },
    ...
  ],
  "max_fret_angle_deg": 2.85,
  ...
}
```

**Full response:** `data/ecosphere_samples/fan_fret_smart_guitar_pro.json`

---

### Pythagorean Temperament (12-fret octave)

**Request:**
```json
{
  "scale_length_mm": 647.7,
  "fret_count": 12,
  "temperament": "pythagorean",
  "string_count": 6,
  "slot_width_mm": 0.58
}
```

**Response (abbreviated):**
```json
{
  "input_params": {
    "temperament": "pythagorean",
    "fret_count": 12,
    ...
  },
  "fret_lines": [
    {"fret_number": 1, "points": [{"x_mm": 36.32, ...}], ...},
    {"fret_number": 2, "points": [{"x_mm": 77.12, ...}], ...},
    ...
  ],
  ...
}
```

Pythagorean fret positions differ from 12-TET due to pure-fifth tuning.
Fret 12 is at exactly half the scale length (323.85mm) in both systems,
but intermediate frets differ by up to ~3.9mm at this scale length.

**Full response:** `data/ecosphere_samples/custom_temperament_pythagorean.json`

---

## Nested Type Reference

### FretLine

A complete fret line spanning all strings.

| Field | Type | Description |
|-------|------|-------------|
| `fret_number` | int | 0 for nut, 1-N for frets |
| `points` | List[FretPoint] | One point per string crossing |
| `angle_rad` | float | Angle from perpendicular in radians (0 for standard fretting) |
| `is_perpendicular` | bool | True when this fret is perpendicular to centerline |

**Computed properties:** `bass_point`, `treble_point`, `center_x_mm`

### FretPoint

A single computed point on a fret line.

| Field | Type | Description |
|-------|------|-------------|
| `fret_number` | int | Fret number (0 = nut) |
| `string_index` | int | String index (0 = bass side) |
| `x_mm` | float | Distance from nut along centerline |
| `y_mm` | float | Position across fretboard (negative = bass, positive = treble) |

### StringPath

Path of a single string from nut to bridge.

| Field | Type | Description |
|-------|------|-------------|
| `string_index` | int | String index (0 = bass) |
| `scale_length_mm` | float | Scale length for this string |
| `nut_position` | Tuple[float, float] | (x, y) at nut |
| `bridge_position` | Tuple[float, float] | (x, y) at bridge |
| `fret_intersections` | List[Tuple[float, float]] | (x, y) points where string crosses each fret |
| `intonation_offset_mm` | float | Saddle compensation offset (default 0.0) |

**Computed property:** `compensated_length_mm` = scale_length + intonation_offset

### RadiusSpec

Fretboard radius specification supporting single or compound radius.

| Field | Type | Description |
|-------|------|-------------|
| `nut_radius_mm` | float? | Radius at nut (null = flat fretboard) |
| `heel_radius_mm` | float? | Radius at heel (null = same as nut) |

**Computed properties:** `is_compound`, `is_flat`, `radius_at_position(ratio)`

---

## DXF Projection Layers

When exported via `/api/v1/fretboard/dxf`, the ecosphere projects to 9 layers:

| Layer | Content | Entity Type |
|-------|---------|-------------|
| STRINGS | Lines from nut to bridge | LINE |
| FRETS | Lines from bass to treble | LINE |
| FRETBOARD_OUTLINE | 4-point closed contour | LWPOLYLINE (R2000) / LINE (R12) |
| FRET_SLOTS | Closed rectangles per slot | LWPOLYLINE (R2000) / LINE (R12) |
| NUT | Nut line + string slot markers | LINE + CIRCLE |
| BRIDGE | Theoretical saddle line | LINE |
| BRIDGE_COMPENSATED | Per-string saddle points | CIRCLE |
| HARMONICS_OVERLAY | Reserved for future use | (empty) |
| ANNOTATIONS | Fret numbers + scale label | TEXT |

**R12 vs R2000:** Free tier returns R12 (LINE entities). Pro tier returns R2000
(LWPOLYLINE for closed contours, critical for CAM toolpath generation).

---

## Versioning

The `version` field in `FretboardEcosphere` tracks schema changes:

- **1.0.0** (2026-04-30): Initial release. Nine-layer DXF projection.

Breaking changes will increment the major version. New optional fields
that don't affect existing consumers increment the minor version.

---

## Related Documentation

- **API endpoints:** `/api/v1/fretboard/*` (see OpenAPI at `/openapi.json`)
- **DXF writer:** `app/cam/dxf_writer.py`
- **Math kernels:** `app/calculators/alternative_temperaments.py`
- **Scala loader:** `app/calculators/scala_loader.py`
- **Sample outputs:** `data/ecosphere_samples/`
