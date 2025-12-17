
A) /docs/TOOLBOX_CAM_ARCHITECTURE_v1.md
# ToolBox CAM Architecture v1

> Goal: Define a neutral CAM architecture for the Luthier’s ToolBox ecosystem that:
> - Plays nicely with FreeCAD’s CAM model (ToolBits, Jobs, Ops).
> - Stays JSON-/API-driven (no GUI/FCStd dependency).
> - Integrates cleanly with existing ToolBox components (DXF/SVG, CompareLab, N-series CAM).

---

## 1. High-Level Overview

The ToolBox CAM system is structured around **three main abstraction layers**:

1. **Geometry Layer** – DXF/SVG/JSON shapes from ToolBox design tools.
2. **CAM Model Layer** – Machine-agnostic CAM job description (tools, stock, operations, sequencing).
3. **Execution Layer** – Machine-specific G-code and validation (posts, CompareLab, golden checks).

FreeCAD CAM provides a strong reference for layer 2 (Job/Tool/Operation concepts). ToolBox adopts the concepts, but keeps its own JSON + API formats.

---

## 2. Core Components

### 2.1 Geometry Layer

**Sources:**

- Rosette Designer, Fingerboard Generator, Body Templates.
- DXF/SVG importers.
- (Later) Fusion 360 / FreeCAD exports.

**Responsibilities:**

- Represent 2D curves and regions as **normalized geometry**:
  - `paths` (polyline / spline approximations)
  - `regions` (closed loops, pockets)
- Provide **tags** for semantic intent:
  - `"role": "body_outline"`, `"fingerboard_slot"`, `"rosette_channel"`, etc.
- Serve as the input to CAM Operations.

Geometry is **machine-agnostic** and **CAM-agnostic**.

---

### 2.2 CAM Model Layer

This is the heart of the architecture, modeled loosely on FreeCAD’s CAM “Job”:

- **CAMJob**
  - `id`, `name`, `description`
  - `machine` (router, mill, etc.)
  - `stock` (block size & origin)
  - `tool_controllers` (Tool + feed/speed/stepdown)
  - `operations` (Profile, Pocket, Drilling, Engrave, etc.)
  - `post_settings` (target controller, output path)

The CAMJob is:

- JSON-serializable.
- Editable from the ToolBox UI.
- Executable by the backend to create a neutral “path program”.
- Exportable via multiple post processors.

#### 2.2.1 Tooling

ToolBox adopts a FreeCAD-like structure:

- **ToolShape** – geometry template (e.g., flat endmill, ball, V, saw-blade disc).
- **ToolBit** – a single physical tool instance:
  - Diameter, flute length, stick-out, kerf, tooth count, etc.
- **ToolLibrary** – a collection of ToolBits with metadata:
  - `machine_id`, `material_tag`, `vendor`, etc.

Tooling is shared between Jobs and between machines.

#### 2.2.2 Tool Controllers

Each **ToolController** binds a ToolBit to a Job with context:

- `tool_bit_id`
- `spindle_speed`
- `feed_rate`
- `plunge_rate`
- `stepdown`
- `stepover`
- `coolant`, `ramp_entry`, etc.

This mirrors FreeCAD’s `ToolController` objects but stays JSON-first.

#### 2.2.3 CAM Operations

Operations reference:

- **Geometry** (`source_geometry_id`, `selection_tags`),
- **ToolController** (`tool_controller_id`),
- **Operation parameters** (depth, side, allowance, strategy).

Operations are independent of the post and machine. Examples:

- `Profile2D`
- `Pocket2D`
- `DrillPattern`
- `Engrave`
- `Adaptive2D`
- `VCarve`
- `DressupTabs`, `DressupRamp`, `DressupLeadInOut`

Dressups are modeled as **modifiers** that wrap or decorate a parent operation.

---

### 2.3 Execution Layer

The Execution Layer is responsible for:

1. **Neutral Path Program Generation**
   - From CAMJob → internal, ordered list of “commands”:
     - `Rapid`, `FeedMove`, `ArcMove`, `ToolChange`, `SpindleOn/Off`, etc.
   - This is the “internal G-code DSL”.

2. **Post Processing**
   - Map neutral commands to machine dialects:
     - GRBL
     - Mach3/4
     - FANUC-style
     - “Thin-Kerf Saw” safe mode (special G-code patterns for slitting blades).

3. **Verification & Validation**
   - Pass resulting G-code through:
     - **CompareLab** (SVG/G-code geometry diffs, layer-aware).
     - **Golden Compare System** (baseline + regression + CI drift alerts).
   - Optionally feed into external simulators later.

---

## 3. ToolBox–FreeCAD Compatibility Plan

FreeCAD informs the **concepts**, but ToolBox stays independent:

- **Compatible Concepts:**
  - ToolBit / ToolLibrary
  - Job / ToolController / Operation / Dressup
  - Post-processors
- **Not Imported:**
  - FCStd storage format
  - FreeCAD GUI / Workbench
  - Full 3D stock modeling

**Interoperability path:**

- Support importing **FreeCAD ToolBits & Libraries** (`.fctb`, `.fctl`) into the ToolBox Tool Preset system.
- Optional future: export a ToolBox CAMJob as a FreeCAD Path Job script for advanced users.

---

## 4. Component-Level Architecture

### 4.1 Backend (FastAPI / Python)

- `cam/models.py` – Pydantic models for:
  - `CAMJob`, `ToolBit`, `ToolLibrary`, `ToolController`, `Operation`
- `cam/toolbit_importer.py` – Load `.fctb` / `.fctl` into ToolBox ToolBit schema.
- `cam/path_engine.py` – Job → neutral path program.
- `cam/posts/` – Post processors:
  - `grbl_post.py`, `fanuc_post.py`, `thin_saw_post.py`, etc.
- `cam/api.py` – Endpoints:
  - `POST /cam/jobs`
  - `GET /cam/jobs/{id}`
  - `POST /cam/jobs/{id}/generate-path`
  - `POST /cam/jobs/{id}/export-gcode?post=grbl`
  - `POST /cam/jobs/{id}/compare` → wires into CompareLab `/compare/run`.

---

### 4.2 Frontend (Vue / ToolBox UI)

- `components/cam/CAMJobEditor.vue`
  - Tabs: Stock | Tools | Operations | Simulation | Export.
- `components/cam/ToolLibraryPanel.vue`
  - Browse ToolBits, import from FreeCAD libraries.
- `components/cam/OperationEditor.vue`
  - Different controls per operation type.
- `components/cam/SimulationPreview.vue`
  - 2D toolpath overlay, calls CompareLab for diff.

---

## 5. Roadmap Alignment

- **Near-term:**
  - Implement ToolBit/ToolLibrary schema + importer.
  - Implement core 2D operations (Profile2D, Pocket2D, Drill, Engrave).
  - Integrate with CompareLab and golden checks.

- **Mid-term:**
  - Add Dressups (Tabs, Ramp, Lead-in/out).
  - Multiple post processors (GRBL, FANUC).
  - Job presets for standard guitar operations.

- **Long-term:**
  - Semi-automated CAM templates:
    - “Neck CAM preset”
    - “Fingerboard CAM preset”
    - “Rosette CAM preset”
  - Optional FreeCAD interoperability for advanced workflows.
________________________________________
B) /docs/CAM_TOOLBIT_IMPORTER_DESIGN.md
# CAM ToolBit Importer Design (FreeCAD → ToolBox)

> Goal: Import FreeCAD ToolBits (`.fctb`) and ToolBit Libraries (`.fctl`) into the ToolBox
> Tool system, so existing CAM users can reuse their tool definitions and ToolBox can share
> a conventional tooling vocabulary.

---

## 1. FreeCAD ToolBit Files – Quick Overview

FreeCAD’s Path workbench uses:

- **ToolShape** – CAD geometry describing generic tool shape (FCStd).
- **ToolBit (.fctb)** – JSON definition of a single cutting tool:
  - Tool geometry parameters (diameter, length, shoulder, etc.).
  - Metadata (name, description, manufacturer, etc.).
  - Reference to a ToolShape.

- **ToolBit Library (.fctl)** – JSON collection of ToolBits:
  - Library name
  - Metadata (machine, material)
  - `tools: [ { ToolBitRef… } ]`

ToolBox will:

- Parse `.fctb` & `.fctl` JSON.
- Map fields into its **ToolBit** schema.
- Ignore GUI-specific or FreeCAD-specific fields we don’t need.

---

## 2. ToolBox ToolBit Schema (Target)

ToolBox internal `ToolBit` model (Pydantic):

```python
class ToolBit(BaseModel):
    id: str
    name: str
    type: Literal["endmill", "ballend", "vbit", "drill", "saw"]
    diameter: float
    flute_length: Optional[float] = None
    tool_length: Optional[float] = None
    corner_radius: Optional[float] = None
    included_angle: Optional[float] = None  # for V-bits
    kerf: Optional[float] = None            # for saw blades
    tooth_count: Optional[int] = None

    vendor: Optional[str] = None
    part_number: Optional[str] = None
    notes: Optional[str] = None

    tags: List[str] = []
ToolLibrary:
class ToolLibrary(BaseModel):
    id: str
    name: str
    machine_id: Optional[str] = None
    material_tag: Optional[str] = None
    tools: List[ToolBit] = []
________________________________________
3. Importer Responsibilities
The importer must:
1.	Detect file type (.fctb vs .fctl).
2.	Parse JSON safely.
3.	For each FreeCAD ToolBit:
o	Map geometry fields into ToolBox schema.
o	Normalize units (ToolBox expects mm).
o	Generate a stable id (e.g., slug from name or hash).
4.	For libraries:
o	Create a ToolLibrary with metadata from .fctl.
o	Attach imported ToolBits (inline or by reference).
5.	Handle slitting / saw blade tools as special case:
o	Recognize FreeCAD’s parameters that map to thin-kerf saws.
o	Set type="saw", kerf, tool_length, tooth_count.
________________________________________
4. Mapping FreeCAD → ToolBox Fields (Conceptual)
(Field names here are illustrative; real JSON keys depend on FreeCAD’s version.)
FreeCAD ToolBit JSON (simplified concept):
{
  "name": "6mm Endmill",
  "type": "EndMill",
  "parameters": {
    "diameter": 6.0,
    "length": 50.0,
    "fluteLength": 20.0,
    "cornerRadius": 0.0
  },
  "shape": "EndmillShape.fcstd",
  "attributes": {
    "vendor": "CarbideCo",
    "partNumber": "CC-EM-6-50",
    "notes": "General purpose"
  }
}
ToolBox mapping:
•	ToolBit.name ← name
•	ToolBit.type ← map FreeCAD type:
o	EndMill → "endmill"
o	BallEnd → "ballend"
o	Drill → "drill"
o	SlotCutter / Saw → "saw"
•	diameter ← parameters.diameter
•	tool_length ← parameters.length
•	flute_length ← parameters.fluteLength
•	corner_radius ← parameters.cornerRadius
•	vendor ← attributes.vendor
•	part_number ← attributes.partNumber
•	notes ← attributes.notes
•	tags ← list from:
o	FreeCAD attributes
o	library metadata (machine, material)
o	custom flags (“imported-from-freecad”)
Saw / Slitting Tool Special Case:
If type or parameters indicate a disk/slitting saw:
•	type = "saw"
•	kerf ← parameters.kerf or parameters.diameter / toothCount fallback
•	tooth_count ← parameters.toothCount if present
________________________________________
5. Importer Implementation Plan
5.1 Backend Module
cam/toolbit_importer.py:
from pathlib import Path
import json
from typing import List, Tuple

from .models import ToolBit, ToolLibrary


def import_fctb(path: Path) -> ToolBit:
    data = json.loads(path.read_text(encoding="utf-8"))
    # ... map FreeCAD JSON → ToolBit as described ...
    return ToolBit(
        id=generate_id(data),
        name=data["name"],
        type=map_type(data.get("type")),
        diameter=extract_diameter(data),
        flute_length=extract_flute_length(data),
        tool_length=extract_length(data),
        corner_radius=extract_corner_radius(data),
        included_angle=extract_included_angle(data),
        kerf=extract_kerf_if_saw(data),
        tooth_count=extract_tooth_count_if_saw(data),
        vendor=extract_vendor(data),
        part_number=extract_part_number(data),
        notes=extract_notes(data),
        tags=["imported-from-freecad"],
    )


def import_fctl(path: Path) -> ToolLibrary:
    data = json.loads(path.read_text(encoding="utf-8"))
    lib_name = data.get("name") or path.stem
    tools: List[ToolBit] = []

    for tool_def in data.get("tools", []):
        # some libraries reference external .fctb files, others inline
        if "file" in tool_def:
            tb_path = (path.parent / tool_def["file"]).resolve()
            tool = import_fctb(tb_path)
        else:
            tool = map_inline_toolbit(tool_def)

        tools.append(tool)

    return ToolLibrary(
        id=slugify(lib_name),
        name=lib_name,
        machine_id=data.get("machineId"),
        material_tag=data.get("material"),
        tools=tools,
    )
Helper functions handle mapping and unit normalization.
5.2 API Endpoint
cam/api.py:
•	POST /cam/tools/import/freecad
Request: upload a .fctb or .fctl file.
Response: list of imported ToolBits and/or ToolLibraries.
Example:
{
  "libraries": [
    {
      "id": "router_hardwood",
      "name": "Router – Hardwood",
      "tool_count": 12
    }
  ],
  "tools": [
    {
      "id": "6mm-endmill-carbideco",
      "name": "6mm Endmill – CarbideCo",
      "type": "endmill",
      "diameter": 6.0
    }
  ]
}
5.3 UI Integration
•	A small “Import from FreeCAD” button in ToolLibraryPanel.vue.
•	After import:
o	Libraries appear in ToolBox’s “Tool Preset Hub”.
o	Tools can be assigned to CAMJobs via ToolControllers.
________________________________________
6. Safety & Validation
Because ToolBox targets thin-kerf blades and specialized lutherie tools:
•	Importer should:
o	Flag suspicious or incomplete geometry (missing diameter, etc.).
o	Mark imported tools with a clear "imported-from-freecad" tag.
o	Allow the user to edit and re-save tools in ToolBox format.
This ensures imported tools become first-class ToolBox components, not opaque foreign objects.

---

## C) `/docs/CAM_JOB_SCHEMA_v1.md`

```md
# CAM Job Schema v1 (ToolBox)

> Goal: Define the JSON schema for ToolBox CAM Jobs that:
> - Follows the conceptual model of FreeCAD CAM Jobs.
> - Integrates with existing ToolBox geometry and CompareLab.
> - Is simple enough to evolve over time.

---

## 1. Top-Level CAM Job Structure

A **CAMJob** is the top-level unit of work for generating toolpaths.

```jsonc
{
  "id": "job_neck_001",
  "name": "Neck Blank – Maple – Router",
  "description": "Profile, pockets, and tuner drilling for maple neck.",

  "machine": {
    "id": "router_bcm2030",
    "label": "BCM 2030CA Router",
    "controller": "grbl",
    "work_envelope": { "x": 2000, "y": 3000, "z": 200 }
  },

  "stock": {
    "material": "maple",
    "units": "mm",
    "size": { "x": 900, "y": 200, "z": 50 },
    "origin": "lower_left_top",       // enum
    "work_offset": "G54"
  },

  "geometry_source": {
    "type": "toolbox-design",
    "id": "neck_template_v3"
  },

  "tool_controllers": [
    {
      "id": "tc_endmill_6mm_rough",
      "tool_bit_id": "tb_6mm_endmill",
      "spindle_speed": 18000,
      "feed_rate": 2400,
      "plunge_rate": 800,
      "stepdown": 3.0,
      "stepover": 2.4,
      "coolant": "none",
      "notes": "Maple roughing"
    }
  ],

  "operations": [
    /* see next section */
  ],

  "post": {
    "id": "post_grbl_router",
    "output_path": "output/neck_001.nc",
    "safe_z": 5.0,
    "clearance_z": 10.0,
    "home_sequence": "G28",
    "header_template": null,
    "footer_template": null
  }
}
________________________________________
2. Operation Schema
2.1 Base Operation
All operations share a common envelope:
{
  "id": "op_profile_neck_outline",
  "type": "Profile2D",
  "label": "Neck Outline Profile",
  "enabled": true,
  "priority": 10,

  "tool_controller_id": "tc_endmill_6mm_rough",
  "geometry_ref": {
    "source": "geometry_layer",
    "selection_tags": ["neck_outline"]
  },

  "parameters": {
    // type-specific
  },

  "dressups": [
    // optional list of dressup modifiers
  ]
}
________________________________________
2.2 Profile2D Parameters
"parameters": {
  "side": "outside",                // outside | inside | on
  "depth_mode": "absolute",         // absolute | relative
  "final_depth": -15.0,             // mm, negative = below top
  "allowance": 0.0,                 // finishing allowance
  "stepdown_override": null,        // use tool default if null
  "compensation": "left",           // left/right/none (controller comp)
  "entry_strategy": "ramp",         // plunge | ramp | helix
  "ramp_angle": 5.0,                // degrees, if "ramp"
  "tabs": {
    "enabled": true,
    "tab_length": 12.0,
    "tab_height": 3.0,
    "tab_spacing": 150.0
  }
}
Use cases:
•	Body outlines
•	Neck perimeter
•	Pickup and control cavities (as Profile + Pocket combos).
________________________________________
2.3 Pocket2D Parameters
"parameters": {
  "strategy": "offset",             // offset | zigzag | spiral
  "depth_mode": "absolute",
  "final_depth": -3.0,
  "stepdown_override": null,
  "allowance": 0.0,
  "island_tags": ["keepout_inlay"],
  "pocket_clearance": 0.5
}
Use cases:
•	Rosette channels
•	Inlay pockets
•	Control recesses
________________________________________
2.4 DrillPattern Parameters
"parameters": {
  "pattern_type": "points-from-tags",   // points-from-tags | grid | linear
  "point_tags": ["tuner_holes"],
  "peck_drilling": true,
  "peck_depth": 2.0,
  "dwell": 0.25,
  "retract_mode": "full"                // full | partial
}
Use cases:
•	Tuner holes
•	Strap button holes
•	Bridge mounting holes
________________________________________
2.5 Engrave / VCarve Parameters
"parameters": {
  "mode": "engrave",            // engrave | vcarve
  "depth": -1.2,
  "follow_centerline": true,
  "use_inline_width": false
}
Use cases:
•	Logos
•	Inlay outlines
•	Decorative lines on fingerboards or tops.
________________________________________
2.6 Dressups
Dressups are small modifiers applied on top of an operation.
Example Dressup: RampEntry
{
  "id": "dressup_ramp_entry_neck_outline",
  "type": "RampEntry",
  "parameters": {
    "angle": 3.0,
    "length": null
  }
}
Example Dressup: Tabs
{
  "id": "dressup_tabs_body",
  "type": "Tabs",
  "parameters": {
    "tab_length": 10.0,
    "tab_height": 2.5,
    "tab_spacing": 120.0
  }
}
In the engine, Dressups are applied in order:
1.	Generate base toolpath for operation.
2.	Apply each Dressup in sequence (ramp, tabs, etc.).
________________________________________
3. Neutral Path Program
Backend converts CAMJob + operations → a neutral path sequence:
[
  { "cmd": "SetUnit", "unit": "mm" },
  { "cmd": "SetFeed", "feed": 2400 },
  { "cmd": "SetSpindle", "rpm": 18000, "direction": "CW" },
  { "cmd": "Rapid", "x": 0, "y": 0, "z": 10 },
  { "cmd": "FeedMove", "x": 100, "y": 0, "z": -3 },
  { "cmd": "ArcMove", "x": 150, "y": 50, "z": -3, "i": 25, "j": 25, "cw": true },
  { "cmd": "ToolChange", "tool": "tb_3mm_ball" }
]
This is not exposed directly to users; it’s the internal representation used by post processors.
________________________________________
4. Post Export
Post config from the Job:
"post": {
  "id": "post_grbl_router",
  "output_path": "output/neck_001.nc",
  "safe_z": 5.0,
  "clearance_z": 10.0,
  "home_sequence": "G28",
  "header_template": null,
  "footer_template": null
}
Backend:
1.	Loads post plugin by id.
2.	Maps neutral path commands → G-code dialect.
3.	Writes to output_path.
4.	Optionally triggers:
o	CompareLab diff (geometry vs. golden).
o	Golden check (for regression).
________________________________________
5. API Endpoints (Summary)
Proposed endpoints (FastAPI):
•	POST /cam/jobs – Create/update a CAMJob.
•	GET /cam/jobs/{id} – Fetch a CAMJob.
•	POST /cam/jobs/{id}/generate-path – Generate neutral path program (for debug).
•	POST /cam/jobs/{id}/export-gcode?post=grbl – Export to machine G-code.
•	POST /cam/jobs/{id}/compare – Generate a compare SVG and diff via CompareLab.
•	POST /cam/tools/import/freecad – Use ToolBit importer to load .fctb / .fctl.
________________________________________
6. Versioning Strategy
•	This document describes v1 of the CAM Job schema.
•	Changes are tracked via:
o	schema_version field on future Jobs.
o	Migration utilities to update Jobs from v1 → v2 if needed.
For now, v1 is intentionally small, 2D, and guitar-focused:
•	It covers 80% of your near-term CNC work (necks, fingerboards, rosettes, bodies).
•	It leaves space for 2.5D/3D surface operations later.

