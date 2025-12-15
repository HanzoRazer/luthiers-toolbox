docs/Tool_Library_Audit_Checklist.md

You don’t need to edit anything except the exact paths if they differ.

# Tool Library Audit Checklist  
_Luthier’s ToolBox – Router Bits, Saw Blades & Calculators_

## 0. Purpose

This checklist exists to make **all tool data** (router bits, saw blades, drills, etc.) flow through a **single, centralized Tool Library**, instead of being scattered across Python/TS code as hard-coded numbers.

**Goal:**  
- One canonical JSON tool library  
- Everything else references tools by **`tool_id`**  
- RMOS, Saw Lab, CAM, and Art Studio all read from the same source of truth

---

## 1. Confirm the Canonical Tool Library Location

### 1.1 Locate the Tool Library JSON

In VS Code or your editor, search for:

- `tool_library.json`
- `Tool_Library_Spec`
- `"router_bit"` or `"saw_blade"` in JSON

✅ **Action:**  
- Identify the **one** JSON file that will become the canonical library, e.g.:

- `services/api/app/tooling/tool_library.json`  
  or  
- `assets/tool_library.json`

👉 Write the final chosen path here:

- Canonical tool JSON: `_______________________________`

### 1.2 Confirm the Loader

Search for:

- `ToolLibrary`
- `load_tool_library`
- `get_tool_by_id`
- `tool_library_loader`

✅ **Action:**  
- Identify the Python module that will be the **single loader API**, e.g.:

- `services/api/app/tooling/library.py`

Write it here:

- Canonical loader module: `_______________________________`

The loader should expose something like:

- `get_tool(tool_id: str) -> Tool`
- `list_tools(kind: Optional[str]) -> List[Tool]`

If it doesn’t yet, add a TODO there (not scattered elsewhere).

---

## 2. Inventory What You Already Have

### 2.1 Router Bits

Search:

- `router_bit`
- `"vbit"` or `"v_bit"`
- `"downcut"` / `"upcut"`
- `diameter_mm` near “router”

✅ **Action:**  
- For each **real bit** you find (in JSON or code), ensure it has a **`tool_id`** and an entry in the canonical JSON.

Example JSON entry:

```json
{
  "id": "router_1_4_downcut",
  "kind": "router_bit",
  "diameter_mm": 6.35,
  "flutes": 2,
  "material": "carbide",
  "chipload_recommended_mm": 0.03,
  "notes": "General-purpose 1/4 in downcut."
}


Check off:

 All current router bits appear in tool_library.json

 Each has a stable id

2.2 Saw Blades (Saw Lab)

Search:

saw_blade

kerf_mm

rim_speed

tooth_count

"blade_"

✅ Action:
Collect any saw blade specs you’ve already entered (from Saw Lab JSONs or scripts) and ensure they’re all represented in the canonical library:

{
  "id": "saw_blade_8in_kerf_2mm_60t",
  "kind": "saw_blade",
  "diameter_mm": 203.2,
  "kerf_mm": 2.0,
  "tooth_count": 60,
  "geometry_family": "ATB",
  "max_rpm": 6000,
  "notes": "Fine crosscut / rosette slicing."
}


Check off:

 All Saw Lab blade definitions merged into tool_library.json

 No “private” blade specs hiding in separate Saw Lab files

3. Find & Mark Hard-Coded Tools in Backend (Python)
3.1 Search Patterns

From repo root, in VS Code or similar, search for:

diameter_mm =

diameter_in =

kerf_mm

chipload_mm

tooth_count

flute_count

rpm =

feed_mm_min =

specific numeric combos you know represent a particular tool (e.g. 6.35 + 2 flutes)

Directories to pay special attention to:

services/api/app/calculators/

services/api/app/rmos/

services/api/app/saw_lab/

server/pipelines/ (legacy calculators / physics)

3.2 Classification

✅ For each hit, classify:

 Legacy only (server/pipelines):
Document it, but migration can be Phase 2.

 Active API path (services/api):
These must be migrated to tool_id.

Make a short scratch list:

[ ] calculators/chipload.py – hard-coded 1/4" bit (6.35mm, 2 flutes)
[ ] saw_lab/rim_speed.py – hard-coded 8" blade (203.2mm, kerf 2.0mm)
[ ] cam/rosette_planner.py – hard-coded v-bit 60deg

4. Refactor Call Sites to Use tool_id

For each active hard-coded tool, fix it like this:

4.1 Before (example)
# calculators/chipload.py
chipload_mm = feed_mm_min / (rpm * flute_count)
# diameter_mm, flute_count, etc. passed as raw numbers from many places

4.2 After (conceptual)
from app.tooling.library import get_tool

tool = get_tool(tool_id="router_1_4_downcut")

chipload_mm = compute_chipload(
    rpm=ctx.tool_setup.rpm,
    feed_mm_min=ctx.tool_setup.feed_mm_min,
    flute_count=tool.flutes,
    diameter_mm=tool.diameter_mm,
    material_id=tool.material,
)


✅ Action per call site:

 Identify which physical tool it really is.

 Ensure that tool exists in tool_library.json with an id.

 Replace the raw numbers with get_tool("that_id") and pull fields from the Tool object.

5. Saw Lab ↔ Tool Library Integration

The goal: Saw Lab never invents its own saw blade schema again.

5.1 Calculators

Modules like:

saw_lab/rim_speed.py

saw_lab/heat.py

saw_lab/bite_per_tooth.py

saw_lab/kickback_risk.py

✅ Action:

 Ensure each of these takes a tool_id (or Tool object) as part of its input.

 Remove stray diameter_mm, kerf_mm, etc. literals and fetch them from the tool library.

5.2 Saw Path Planner

Wherever the Saw Path Planner (2.0 / 2.1) chooses a blade:

✅ Action:

 Use blade_id only (no baked-in diameters/kerfs).

 If a special blade is used for thin rosette slicing, add that blade to tool_library.json and reference its ID.

6. Frontend (Vue/TS) Audit

Search in packages/client/src/ for:

tool_id

diameterMm

flutes

anything like DEFAULT_TOOL, DEFAULT_BIT, etc.

✅ Action:

 Replace any duplicated tool constants in TS with calls to an API that returns the canonical tool library, or with an enum of tool_id values only.

 UI should deal in tool_id + pretty name, not reinvent diameter/flutes/material.

7. RMOS + Feasibility Layer

RMOS/scoring should never guess tool geometry.

Search for:

ctx.tool_setup.diameter_mm

ctx.tool_setup.flute_count

tool_material

carbide/HSS strings

✅ Action:

 Ensure RMOS gets tool_id in its RmosContext.

 If RMOS sets defaults, they should be default tool IDs, not raw geometry.

 All calculators behind RMOS read their tool inputs from get_tool(tool_id).

8. Documentation & “Done” Criteria

Add a short note to:

Tool_Library_Spec.md

Calculator_Spine_Overview.md (if present)

✅ Document:

Tool JSON path

Loader API module

Recommendation: “All future calculators must use tool_id and get_tool().”

✅ Checkboxes for “Audit Complete”

 Canonical tool library JSON identified and confirmed

 Tool loader module identified and confirmed

 All active router bits migrated to JSON + tool_id

 All active saw blades migrated to JSON + tool_id

 Saw Lab physics use tool IDs exclusively

 RMOS & calculators no longer hard-code tool geometry

 Frontend doesn’t duplicate tool geometry (only IDs / labels)

 Docs updated to reflect the Tool Library as the single source of truth

When all of the above are checked, the Tool Library migration is complete and new tools can be added centrally without hunting through scattered code.