docs/Tool_Library_Migration_Plan.md

# Tool Library Migration Plan  
**Scope:** Luthier’s ToolBox – Tools, Materials, Machines, CAM, RMOS, Saw Lab, Art Studio  
**Owner:** Ross / ToolBox Core  
**Status:** Draft v1.0

---

## 1. Purpose & Goals

The current ToolBox ecosystem has **multiple, overlapping “tool libraries”** scattered across:

- `tool_db.py` + `tool_library.sqlite` (SQL-based tool/material DB)
- `machines.json` and machine tool tables (per-machine tools)
- legacy `assets/machine_profiles.json` (server-era)
- markdown notes and ad-hoc chipload / feeds & speeds docs
- Saw Lab prototype data files (e.g., `saw_lab_blades.json`)
- hard-coded tool info inside various CAM, neck, bridge, and rosette modules

This makes it difficult to:

- keep tools/materials **consistent**
- keep RMOS feasibility & physics **trustworthy**
- wire Art Studio & Saw Lab **safely** into CAM
- onboard collaborators without breaking things

**Goal of this plan:**  
Migrate from fragmented, ad-hoc tool definitions to a **single, canonical Tool & Material Registry** under `services/api/app/data/`, and refactor existing systems to *consume* that registry instead of reinventing it.

---

## 2. Target Architecture (End State)

### 2.1 Canonical Data Layer

All tools & materials live in a **single, versioned data layer**:

```text
services/api/app/data/
  tool_library.json        # ALL tools (router bits, endmills, saw blades, etc.)
  material_library.json    # ALL materials (woods, plastics, metals, etc.)
  machines.json            # ALL machine profiles + per-machine tool slots

  __init__.py
  tool_library.py          # Loader + ToolProfile API
  material_library.py      # Loader + MaterialProfile API
  machines_library.py      # Loader + MachineProfile API (optional, later)

2.2 Accessors & Profiles

Core Python accessors:

tool_library.py

load_tool_library()

get_tool_profile(tool_id)

iteration utilities

material_library.py

load_material_library()

get_material_profile(material_id)

machines_library.py (optional later)

load_machines()

get_machine(machine_id)

get_machine_tool(machine_id, t) → returns { tool_id, rpm, feed, plunge, … }

These hide the underlying JSON format and give all callers a common, typed API.

2.3 Consumers of the Registry

Once the registry is in place, the following systems become readers, not owners:

RMOS 2.0 calculators

Uses tool_id + material_id → chipload, heat, deflection, etc.

Saw Lab 2.0

Uses tool_id of type "saw_blade" → rim speed, bite per tooth, kickback, etc.

CAM Core

Uses tool_id & machine slots → post context (TOOL, DIA, RPM, FEED, etc.)

Art Studio

Provides tool selection drop-downs and passes tool_id to RMOS for feasibility.

Any future AI suggestion engines

Suggests tool_id + parameters, validated through the registry and calculators.

3. Current State – Inputs to Migrate

These are the known sources of “tool information” that need to be mined and consolidated, not preserved as separate authorities:

SQL-based tool DB

tool_db.py

tool_library.sqlite (if present on disk)

feeds_router.py (/tooling endpoints)

Per-machine tool tables

machines.json (and any variants referenced in CAM docs)

machines_tools_router.py

tool_table.py

Legacy server-era profiles

server/machine_router.py

server/materials_router.py

assets/machine_profiles.json

Docs & notes

Speeds & feeds markdown files

Bits/Routers/Chipload search results

CAM CAD developer handoff docs

Any physics notes baked into docs

Saw Lab prototypes

saw_lab_blades.json

any saw blade specs from PDFs / RFQ sheets / Saw Lab docs

4. Phased Migration Strategy

Migration will happen in four phases:

Phase 1 – Design & Stub the Canonical Schemas

Phase 2 – Data Extraction & Consolidation

Phase 3 – Refactor Consumers to Use the Registry

Phase 4 – Cleanup, Deprecation, and Documentation

Each phase can be delivered as its own feature branch / PR.

5. Phase 1 – Design & Stub the Canonical Schemas
5.1 Define ToolProfile schema

Create services/api/app/data/tool_library.json with schema-level comments in the first draft (even if empty):

{
  "$schema": "https://example.com/tool_profile.schema.json",
  "tools": {
    "endmill_3mm": {
      "tool_id": "endmill_3mm",
      "type": "endmill",                // "endmill" | "router_bit" | "vbit" | "saw_blade" | "drill" | ...
      "name": "3mm Endmill",
      "diameter_mm": 3.0,
      "flutes": 2,
      "helix_deg": 0.0,
      "recommended_chipload_mm": { "min": 0.02, "max": 0.04 },
      "max_rpm": 24000,
      "notes": "Placeholder – replace with real data"
    }
  }
}


Required fields (per tool):

tool_id (string, unique)

type (string enum)

name (string)

diameter_mm (float)

flutes (int)

Optional fields:

helix_deg (float)

recommended_chipload_mm.min/max (float)

max_rpm (float)

notes (string)

domain-specific fields (e.g., tooth_count, kerf_mm for saw blades)

5.2 Define MaterialProfile schema

Create services/api/app/data/material_library.json:

{
  "$schema": "https://example.com/material_profile.schema.json",
  "materials": {
    "maple_hard": {
      "material_id": "maple_hard",
      "name": "Hard Maple",
      "chipload_mm": { "min": 0.01, "max": 0.03 },
      "max_rpm": 24000,
      "heat_sensitivity": "medium",  // "low" | "medium" | "high"
      "notes": "Placeholder – replace with real data"
    }
  }
}

5.3 Define MachineProfile schema (lightweight)

Create (or plan for) services/api/app/data/machines.json:

{
  "machines": {
    "grbl_router_1": {
      "machine_id": "grbl_router_1",
      "name": "Garage GRBL Router",
      "post_kind": "grbl",
      "tools": [
        {
          "t": 1,
          "tool_id": "endmill_3mm",
          "spindle_rpm": 18000,
          "feed_mm_min": 800,
          "plunge_mm_min": 300
        }
      ]
    }
  }
}

5.4 Implement loader stubs

Create tool_library.py, material_library.py with:

dataclasses ToolProfile, MaterialProfile

load_*_library() functions

get_tool_profile(tool_id)

get_material_profile(material_id)

These can initially return just a few placeholder entries. The important part is to lock in the API for all future consumers.

Deliverable:
PR that adds tool_library.json, material_library.json, loader modules, and dataclasses – even with minimal or dummy data.

6. Phase 2 – Data Extraction & Consolidation

This is where we mine all existing sources and migrate them into the canonical JSON registries.

6.1 From SQLite: tool_db.py / tool_library.sqlite

If tool_library.sqlite exists:

Write scripts/export_tool_db_to_json.py that:

imports tool_db.py (SQLAlchemy models)

connects to the DB

reads all Tool and Material rows

maps them to the new schema (tool_id, type, chipload, etc.)

writes/merges into tool_library.json and material_library.json.

Use a deterministic tool_id naming convention:

"{type}_{diameter_mm}mm_{suffix}", e.g. endmill_3mm, vbit60_6mm.

If tool_library.sqlite does not exist:

Still use tool_db.py as a semantic reference for which fields matter:

name, type, diameter, flute_count, helix

material chipload, max_rpm, etc.

Manually seed tool_library.json with a small starter set.

6.2 From machines.json & machine tool tables

Identify all machines.json locations (current and legacy).

For each machine:

Extract listed tools.

For each tool entry:

map or create a tool_id matching tool_library.json.

move geometry fields into the global tool_library.json if not already present.

keep per-machine overrides (rpm, feed, plunge, t, etc.) in machines.json.

Update machines.json entries to reference only:

t

tool_id

per-machine parameters (rpm, feed, plunge)

Not geometry.

6.3 From markdown feeds/speeds & chipload notes

Systematically mine:

“Speeds & Feeds” markdowns

Bits & Routers search docs

Chipload docs

ToolBox CAM CAD handoff docs

For each entry that mentions:

a cutter diameter

a flute count

a material

suggested RPM / feed

chipload rules

…convert that into:

a ToolProfile entry in tool_library.json (if it’s a tool)

or a MaterialProfile entry in material_library.json (if it’s a material rule)

or a comment in the notes field

Where there are conflicting values (e.g., 0.02 vs 0.04 mm/tooth for the same tool), resolve by policy:

Conservatively favor safer / gentler values for default,

Keep alternative values documented in notes for operators.

6.4 From Saw Lab blade definitions

Identify saw_lab_blades.json or similar files.

Map blades into tool_library.json entries with:

type: "saw_blade"

diameter_mm

tooth_count

kerf_mm

recommended rim speed band (m_per_s)

Keep Saw Lab–specific fields either:

in the canonical schema (if it’s not too disruptive),

or in a saw sub-object (e.g. "saw": { "tooth_count": 80, ... }).

7. Phase 3 – Refactor Consumers to Use the Registry

Once the data is consolidated, point all major consumers at the new library layer.

7.1 RMOS calculators & feasibility

Update:

services/api/app/calculators/service.py

services/api/app/calculators/saw_bridge.py

any rmos/feasibility.py modules

to:

accept tool_id + material_id in their inputs

resolve them with get_tool_profile(tool_id) and get_material_profile(material_id)

compute chipload / heat / deflection based on registry-driven values

7.2 Saw Lab calculators

Update Saw Lab modules to:

take tool_id (for saw blades)

resolve blade properties from the tool library

derive rim speed, bite per tooth, kickback, deflection using those values

This removes any duplicated “saw_blades.json” definitions that drift.

7.3 CAM core & post processors

Update:

machines_tools_router.py

tool_table.py

any post-processor templates / injection helpers

so that:

tool_table.py looks up tool geometry via get_tool_profile(tool_id)

machines.json only overrides per-machine runtime settings (rpm, feed, plunge, t)

This ensures that geometry & physics come from one place; machine files only describe how this specific machine uses that tool.

7.4 Art Studio & front-end selectors

Update Art Studio / front-end code (when ready) to:

fetch available tools from a simple API:

e.g. GET /api/tooling/tools → list of tool_id, type, name, diameter

filter by type (router_bit, endmill, saw_blade, etc.)

pass only tool_id (and material_id) into RMOS / Saw Lab for feasibility and path planning.

8. Phase 4 – Cleanup, Deprecation & Docs

After the new registry is working and consumers are refactored:

8.1 Deprecate / archive old sources

Mark tool_db.py and SQLite DB usage as legacy:

Either delete or move to legacy/ with a README stating “replaced by tool_library.json”.

Move old markdown notes into:

docs/legacy/Tool_Feeds_Speeds_Notes/

Link them from a central “history” page.

8.2 Update documentation

Add section in ToolBox_CAM_CAD_Developer_Handoff.md describing:

the new Tool & Material Registry,

how to add tools,

how to add materials,

how to update machine-specific slots.

Create docs/Tool_Library_Spec.md summarizing:

the JSON schemas,

the loader APIs,

example entries.

8.3 Add regression tests

Create tests such as:

test_tool_library_loads_and_resolves_profiles.py

test_material_library_loads_and_resolves_profiles.py

test_machines_library_resolves_tool_slots.py

test_calculators_use_registry_data.py

These should assert:

at least one tool & one material load correctly,

key RMOS calculators do not hard-code diameters/flutes/chiploads,

Saw Lab calculators respect the shared tool data.

9. Branching & Rollout Strategy

Recommended Git flow:

feature/tool-library-schema

Adds JSON schemas + loader stubs.

feature/tool-library-migrate-data

Adds migration scripts & populates tool/material JSON from all sources.

feature/tool-library-rmos-sawlab-integration

Wires RMOS & Saw Lab to use the registry.

feature/tool-library-cam-integration

Refactors machines & post injection to use registry.

At each step:

Keep CI/pytest green,

Avoid large, all-or-nothing diffs,

Use explicit DEPRECATED tags for old modules before removal.

10. Success Criteria (Definition of Done)

The migration is considered complete when:

✅ tool_library.json and material_library.json exist and contain all core tools/materials in use.

✅ All major calculators and feasibility routines accept tool_id + material_id, and resolve via the registry.

✅ Saw Lab 2.0 uses the same tool registry for blade data.

✅ Machines use tool_id references, not duplicated geometry.

✅ No “hidden” tool definitions remain in random modules or markdowns.

✅ Docs are updated to show one clear way to add/edit tools and materials.

✅ New contributors can onboard by reading a single Tool Library document, not hunting across the repo.

Once these are met, the ToolBox has a stable, extensible backbone for all future cutting physics, AI guidance, and multi-machine deployment.