# LTB CAM Output Contract

**Version:** 1.0.0  
**Status:** Active  
**Scope:** Interface between luthiers-toolbox CAM endpoints and CAM-Assist-Blueprint import

---

## 1. Purpose

This contract specifies the JSON structure that luthiers-toolbox CAM endpoints must emit for CAM-Assist-Blueprint to import and assemble into strategy packages.

The contract is a **file format agreement**, not a runtime integration. LTB produces a JSON file; CAM-Assist consumes it. No shared database, no HTTP, no runtime dependency.

---

## 2. Authority Boundary

### CAM-Assist Injects (Never Reads From LTB)

The following fields are **constitutional properties of CAM-Assist** and are injected unconditionally by the importer:

| Field | Value | Rationale |
|-------|-------|-----------|
| `operation_intent.non_execution_declaration` | `true` | CAM-Assist never authorizes execution |
| `safety_boundary.non_execution_declaration` | `true` | Redundant assertion at safety layer |
| `safety_boundary.human_review_required` | `true` | Human review is mandatory |
| `safety_boundary.execution_authority_claim` | `false` | No execution authority claimed |
| `approval_state` | `"pending"` | All imported packages start pending |

**Rule:** The importer MUST NOT read these fields from LTB output. If LTB output contains them, they are ignored. The non-execution invariant cannot be transitively defeated by another repository.

---

## 3. Required LTB Output Structure

```json
{
  "ltb_cam_output_version": "1.0.0",
  
  "operation": {
    "operation_type": "<string, required>",
    "target_feature": "<string, required>",
    "cut_intent": "<string, required>",
    "method": "<string, required>"
  },
  
  "geometry": {
    "dxf_file": "<string, required>",
    "primary_layer": "<string, required>",
    "reference_layers": ["<string>"]
  },
  
  "tool": {
    "tool_type": "<string, required>",
    "diameter_mm": "<number, required>",
    "angle_deg": "<number, optional>",
    "description": "<string, optional>"
  },
  
  "parameters": {
    "depth_mm": "<number, required>",
    "feed_mm_min": "<number, required>",
    "spindle_rpm": "<integer, optional>",
    "depth_per_pass_mm": "<number, optional>"
  },
  
  "material": {
    "material_class": "<string, required>",
    "species": "<string, optional>",
    "hardness_janka": "<integer, optional>"
  },
  
  "units": {
    "linear": "mm",
    "angular": "deg"
  },
  
  "coordinate_frame": {
    "origin": "<string, required>",
    "x_axis": "<string, required>",
    "y_axis": "<string, required>"
  },
  
  "provenance": {
    "source_spec_id": "<string, required>",
    "ltb_version": "<string, required>",
    "created_at": "<ISO-8601, required>"
  }
}
```

---

## 4. Field Specifications

### 4.1 operation

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation_type` | string | **Yes** | Lutherie feature being machined. Feature-based, not method-based. Examples: `v_carve`, `fret_slots`, `pickup_route`, `inlay_pocket`. |
| `target_feature` | string | **Yes** | Instrument feature being operated on. Examples: `fretboard`, `body`, `headstock`. |
| `cut_intent` | string | **Yes** | Geometric intent. Must be one of: `slot`, `pocket`, `profile`, `drill`, `contour`, `channel`. |
| `method` | string | **Yes** | Machining method. Examples: `vcarve`, `conventional`, `climb`. |

**Validation:** The importer MUST reject LTB output missing `operation_type`.

### 4.2 geometry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dxf_file` | string | **Yes** | Filename of DXF geometry file. |
| `primary_layer` | string | **Yes** | DXF layer containing primary geometry. |
| `reference_layers` | array | No | Additional reference layers. |

### 4.3 tool

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_type` | string | **Yes** | Tool classification: `vbit`, `endmill`, `slot_cutter`, `drill`. |
| `diameter_mm` | number | **Yes** | Tool diameter in millimeters. |
| `angle_deg` | number | No | Bit angle for V-bits. |

### 4.4 parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `depth_mm` | number | **Yes** | Maximum cut depth in millimeters. |
| `feed_mm_min` | number | **Yes** | Feed rate in mm/min. |

### 4.5 material

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `material_class` | string | **Yes** | One of: `softwood`, `hardwood`, `exotic`, `figured`, `laminate`, `composite`, `unknown`. |

### 4.6 provenance

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_spec_id` | string | **Yes** | Reference to source instrument specification. |
| `ltb_version` | string | **Yes** | Version of luthiers-toolbox. |
| `created_at` | string | **Yes** | ISO-8601 timestamp. |

---

## 5. Importer Behavior

### 5.1 Validation

The importer validates LTB output against this contract. Missing required field = structured error naming the field.

### 5.2 Injection

The importer unconditionally injects CAM-Assist constitutional properties. These are never read from LTB output.

### 5.3 Unit Conversion

LTB emits metric. The importer converts to inches by default.

---

## 6. Synthetic Fixtures

Synthetic fixtures for testing MUST include:

```json
{
  "synthetic_fixture": true,
  "real_export": false
}
```

This prevents synthetic data from being mistaken for real provenance.

---

*Contract document — defines the seam, does not authorize execution*
