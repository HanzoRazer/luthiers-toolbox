# LTB CAM Output Contract

**Version:** 1.0.0  
**Status:** Draft — pending LTB engineer confirmation  
**Scope:** Defines the interface between luthiers-toolbox CAM endpoints and CAM-Assist-Blueprint import

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

### LTB Must Provide

All other required fields come from LTB output. The importer validates their presence and fails loudly if any are missing.

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
  
  "toolpath": {
    "format": "ltb_toolpath_v1",
    "data": { }
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
    "hardness_janka": "<integer, optional>",
    "grain_direction": "<string, optional>"
  },
  
  "units": {
    "linear": "mm",
    "angular": "deg"
  },
  
  "coordinate_frame": {
    "origin": "<string, required>",
    "x_axis": "<string, required>",
    "y_axis": "<string, required>",
    "z_axis": "<string, optional>"
  },
  
  "provenance": {
    "source_spec_id": "<string, required>",
    "ltb_version": "<string, required>",
    "created_at": "<ISO-8601, required>",
    "created_by": "<string, optional>"
  }
}
```

---

## 4. Field Specifications

### 4.1 operation

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation_type` | string | **Yes** | Lutherie feature being machined. Feature-based, not method-based. Must draw from `CAM_ASSIST_OPERATION_TAXONOMY.md`. Examples: `fret_slots`, `pickup_route`, `inlay_pocket`, `binding_channel`. |
| `target_feature` | string | **Yes** | Instrument feature being operated on. Examples: `fretboard`, `body`, `headstock`, `neck`. |
| `cut_intent` | string | **Yes** | Geometric intent. One of: `slot`, `pocket`, `profile`, `drill`, `contour`, `channel`. |
| `method` | string | **Yes** | Machining method used. Examples: `vcarve`, `conventional`, `climb`, `drill`. V-Carve is recorded here, not in operation_type. |

**Validation:** The importer MUST reject LTB output missing `operation_type`. This is the feature-based identifier that CAM-Assist uses for taxonomy alignment.

### 4.2 geometry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dxf_file` | string | **Yes** | Filename of DXF geometry file. Must be included alongside the JSON output. |
| `primary_layer` | string | **Yes** | DXF layer containing primary operation geometry. |
| `reference_layers` | array | No | Additional reference layers in DXF. |

**Requirement:** LTB output MUST include a DXF file. The importer copies this file into the assembled package.

### 4.3 toolpath

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format` | string | **Yes** | Toolpath format identifier. Use `ltb_toolpath_v1`. |
| `data` | object | **Yes** | Toolpath data in the specified format. Structure TBD per format version. |

**Note:** The toolpath is included for provenance and review. CAM-Assist does not execute toolpaths — it packages them for human review.

### 4.4 tool

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_type` | string | **Yes** | Tool classification. Examples: `vbit`, `endmill`, `slot_cutter`, `drill`. |
| `diameter_mm` | number | **Yes** | Tool diameter in millimeters. |
| `angle_deg` | number | No | Bit angle for V-bits. Required for V-Carve operations. |
| `description` | string | No | Human-readable tool description. |

### 4.5 parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `depth_mm` | number | **Yes** | Maximum cut depth in millimeters. |
| `feed_mm_min` | number | **Yes** | Feed rate in mm/min. |
| `spindle_rpm` | integer | No | Spindle speed. |
| `depth_per_pass_mm` | number | No | Depth per pass for multi-pass operations. |

### 4.6 material

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `material_class` | string | **Yes** | One of: `softwood`, `hardwood`, `exotic`, `figured`, `laminate`, `composite`, `unknown`. |
| `species` | string | No | Specific wood species. |
| `hardness_janka` | integer | No | Janka hardness rating. |
| `grain_direction` | string | No | Grain orientation relative to operation. |

### 4.7 units

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `linear` | string | **Yes** | Linear unit. Must be `mm` (LTB normalizes to metric). |
| `angular` | string | **Yes** | Angular unit. Must be `deg`. |

**Note:** CAM-Assist converts to inches or mm based on strategy requirements. LTB always emits metric.

### 4.8 coordinate_frame

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `origin` | string | **Yes** | Reference point for coordinate origin. |
| `x_axis` | string | **Yes** | Direction of positive X axis. |
| `y_axis` | string | **Yes** | Direction of positive Y axis. |
| `z_axis` | string | No | Direction of positive Z axis. |

### 4.9 provenance

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_spec_id` | string | **Yes** | Reference to source instrument specification. |
| `ltb_version` | string | **Yes** | Version of luthiers-toolbox that generated output. |
| `created_at` | string | **Yes** | ISO-8601 timestamp. |
| `created_by` | string | No | Identifier of creator. |

---

## 5. Importer Behavior

### 5.1 Validation (Fail Loud)

The importer validates LTB output against this contract. On any missing required field:

```
ImportError: LTB output missing required field 'operation.operation_type'
```

No silent defaults. No partial imports. Missing required field = structured error naming the field.

### 5.2 Transformation

The importer transforms LTB output to `strategy.schema.json` format:

| LTB Field | Strategy Field |
|-----------|----------------|
| `operation.operation_type` | `operation_intent.operation_type` |
| `operation.target_feature` | `operation_intent.target_feature` |
| `operation.cut_intent` | `operation_intent.cut_intent` |
| `geometry.*` | `geometry.*` |
| `tool.*` | `operation.tool.*` |
| `parameters.*` | `operation.parameters.*` |
| `material.*` | `material_context.*` |
| `coordinate_frame.*` | `coordinate_frame.*` |
| `provenance.*` | `provenance.*` |

### 5.3 Injection (CAM-Assist Properties)

The importer unconditionally injects:

```json
{
  "strategy_version": "1.2",
  "operation_intent": {
    "non_execution_declaration": true
  },
  "safety_boundary": {
    "non_execution_declaration": true,
    "human_review_required": true,
    "execution_authority_claim": false
  },
  "approval_state": "pending"
}
```

These values are never read from LTB output.

### 5.4 Unit Conversion

LTB emits metric (`mm`). The importer converts to the target unit system:

- If strategy target is `inches`: convert all dimensions
- If strategy target is `mm`: pass through

The `units` field in the output strategy reflects the converted system.

---

## 6. File Deliverables

LTB CAM output is a directory containing:

```
<job_id>/
├── cam_output.json      # This contract's JSON structure
└── geometry.dxf         # Referenced DXF file
```

The importer consumes this directory and produces a strategy JSON file.

---

## 7. Coordination Checklist

Before the importer can consume real LTB output:

- [ ] LTB V-Carve endpoint emits `operation.operation_type` (feature-based, from taxonomy)
- [ ] LTB V-Carve endpoint emits `operation.method` = `"vcarve"`
- [ ] LTB V-Carve endpoint includes DXF geometry file
- [ ] LTB output structure matches this contract
- [ ] Field names and nesting confirmed

This checklist is the seam agreement. Both repos build to this contract.

---

## 8. Non-Goals

This contract does NOT specify:

- Toolpath execution format (CAM-Assist doesn't execute)
- Runtime integration (file-based only)
- Bidirectional data flow (one-way, LTB → CAM-Assist)
- LTB internal implementation (only the output shape)

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-25 | Initial draft |

---

*Contract document — defines the seam, does not authorize execution*
