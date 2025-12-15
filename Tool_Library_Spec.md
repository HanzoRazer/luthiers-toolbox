docs/Tool_Library_Spec.md
markdown
Copy code
# Tool Library Specification  
**Document:** Tool_Library_Spec.md  
**Scope:** Luthier’s ToolBox – Tools, Materials, Machines, RMOS, CAM, Saw Lab, Art Studio  
**Version:** 1.0  
**Status:** Active Specification  

---

# 1. Purpose

The Tool Library is the **canonical source of truth** for all cutter geometry, metadata, and physics-relevant parameters used across the entire Luthier’s ToolBox ecosystem.

It replaces all earlier, fragmented definitions including:

- `tool_db.py` + SQLite DB  
- machine-embedded tool tables  
- markdown feeds/speeds notes  
- ad-hoc tool definitions in CAM modules  
- separate Saw Lab blade files  

All subsystems—RMOS 2.0, Saw Lab 2.0, CAM Core, Art Studio—must now reference **one unified registry**.

---

# 2. File Structure

The Tool Library consists of:

services/api/app/data/tool_library.json
services/api/app/data/material_library.json

services/api/app/data/tool_library.py # loader + ToolProfile
services/api/app/data/material_library.py # loader + MaterialProfile

yaml
Copy code

---

# 3. JSON File Format (Canonical Representation)

## 3.1 The Root Structure (tool_library.json)

```jsonc
{
  "$schema": "https://example.com/tool_profile.schema.json",
  "version": "1.0",

  "tools": {
    "<tool_id>": { ... }
  }
}
4. ToolProfile Schema
Every entry in tools must conform to the structure below.

jsonc
Copy code
{
  "tool_id": "vbit60_6mm",
  "type": "vbit",                        // enum: endmill, router_bit, vbit, saw_blade, drill, etc.
  "name": "60° V-Bit 6mm",
  "geometry": {
    "diameter_mm": 6.0,
    "flutes": 2,
    "included_angle_deg": 60,            // for v-bits
    "helix_deg": null                    // optional
  },

  "recommended": {
    "chipload_mm": { "min": 0.01, "max": 0.03 },
    "rpm": { "min": 12000, "max": 18000 },
    "feed_mm_min": { "min": 400, "max": 1200 }
  },

  "limits": {
    "max_rpm": 24000,
    "max_stepdown_mm": 2.0,
    "max_stepover_mm": 3.0
  },

  "domain": {
    "materials": ["maple_hard", "ebony", "spruce"], // optional
    "operations": ["vcarve", "engrave"]
  },

  "notes": "Placeholder example"
}
5. Schema Field Reference
5.1 Required Fields
Field	Type	Description
tool_id	string	Unique, snake-case identifier.
type	enum	endmill, router_bit, vbit, saw_blade, drill, other.
name	string	Human-friendly name.
geometry.diameter_mm	float	Cutter diameter.
geometry.flutes	int	Number of cutting edges.

5.2 Optional (but recommended) Fields
Field	Type	Description
geometry.helix_deg	float / null	Endmill helix angle.
geometry.included_angle_deg	float / null	V-bit angle.
recommended.chipload_mm	object	Min/max chip thickness.
recommended.rpm	object	Suggested spindle range.
recommended.feed_mm_min	object	Suggested feed range.
limits.max_rpm	float	Hardware or tool limit.
limits.max_stepdown_mm	float	Safe axial DOC.
limits.max_stepover_mm	float	Safe radial DOC.
domain.operations	list	CAM operations (vcarve, pocket, etc.)

6. Special Case Schema: Saw Blades
Saw blades are stored in the same JSON using a type: "saw_blade".

Example:
jsonc
Copy code
{
  "tool_id": "blade_10in_80t_crosscut",
  "type": "saw_blade",
  "name": "10in 80T Crosscut Blade",
  "geometry": {
    "diameter_mm": 254.0,
    "tooth_count": 80,
    "kerf_mm": 2.4
  },
  "recommended": {
    "rim_speed_mps": { "min": 50, "max": 60 },
    "feed_mm_min": { "min": 300, "max": 900 }
  },
  "limits": {
    "max_rpm": 4800
  },
  "domain": {
    "operations": ["crosscut", "trim", "stock_prep"]
  },
  "notes": "Values used by Saw Lab physics: rimspeed, bite-per-tooth, kickback, heat."
}
Saw Lab calculators consume:
diameter_mm

tooth_count

kerf_mm

max_rpm

rim_speed_mps.min/max

7. material_library.json Schema
Identical structure pattern:

jsonc
Copy code
{
  "$schema": "https://example.com/material_profile.schema.json",
  "version": "1.0",

  "materials": {
    "maple_hard": {
      "material_id": "maple_hard",
      "name": "Hard Maple",

      "chipload_mm": { "min": 0.01, "max": 0.03 },
      "max_rpm": 24000,
      "heat_sensitivity": "medium",     // enum: low, medium, high

      "density_kg_m3": 705,             // optional
      "hardness_janka": 1450,           // optional

      "notes": "Example values"
    }
  }
}
8. Python API (tool_library.py)
python
Copy code
from dataclasses import dataclass
from typing import Dict, Optional
import json
from pathlib import Path

@dataclass
class ToolProfile:
    tool_id: str
    type: str
    name: str
    geometry: dict
    recommended: dict
    limits: dict
    domain: dict
    notes: Optional[str] = None

class ToolLibrary:
    def __init__(self, path: Path):
        self.raw = json.loads(path.read_text())
        self.tools: Dict[str, ToolProfile] = {
            tid: ToolProfile(tool_id=tid, **data)
            for tid, data in self.raw.get("tools", {}).items()
        }

    def get(self, tool_id: str) -> ToolProfile:
        return self.tools[tool_id]

# convenience accessor
def get_tool_profile(tool_id: str) -> ToolProfile:
    path = Path(__file__).parent / "tool_library.json"
    return ToolLibrary(path).get(tool_id)
9. Python API (material_library.py)
python
Copy code
@dataclass
class MaterialProfile:
    material_id: str
    name: str
    chipload_mm: dict
    max_rpm: Optional[float]
    heat_sensitivity: str
    density_kg_m3: Optional[float] = None
    hardness_janka: Optional[int] = None
    notes: Optional[str] = None
10. Naming Conventions
Tool IDs
php-template
Copy code
<type>_<diameter_mm>mm_<suffix>
endmill_3mm
vbit60_6mm
surfacing_25mm
blade_10in_80t_crosscut
Material IDs
php-template
Copy code
<species>_<variant>
maple_hard
ebony
spruce_sitka
mahogany_honduran
Machine IDs
nginx
Copy code
grbl_router_1
mach4_router_pro
massocnc_5axis
11. Validation Rules
Before accepting a tool entry:

geometry.diameter_mm > 0

flutes >= 1 (except saw blades)

tooth_count >= 10 for saw blades

recommended ranges must be:

min ≤ max

values > 0

tool_id must be unique

materials referenced must exist in material_library.json

12. Examples
12.1 Router Bit (Standard Endmill)
jsonc
Copy code
{
  "tool_id": "endmill_6mm",
  "type": "endmill",
  "name": "6mm 2-Flute Endmill",
  "geometry": {
    "diameter_mm": 6.0,
    "flutes": 2,
    "helix_deg": 30
  },
  "recommended": {
    "chipload_mm": { "min": 0.03, "max": 0.06 },
    "rpm": { "min": 12000, "max": 18000 },
    "feed_mm_min": { "min": 700, "max": 2400 }
  },
  "limits": {
    "max_rpm": 24000,
    "max_stepdown_mm": 3.0
  },
  "domain": {
    "operations": ["pocket", "profile"]
  }
}
12.2 Saw Blade (Crosscut)
jsonc
Copy code
{
  "tool_id": "blade_254mm_80t",
  "type": "saw_blade",
  "name": "254mm 80-Tooth Crosscut",
  "geometry": {
    "diameter_mm": 254,
    "tooth_count": 80,
    "kerf_mm": 2.4
  },
  "recommended": {
    "rim_speed_mps": { "min": 50, "max": 65 }
  },
  "limits": {
    "max_rpm": 4800
  },
  "domain": {
    "operations": ["saw_cut", "trim"]
  }
}
13. Integration Points
RMOS
Uses tool_id and material_id for:

chipload

heat

deflection

feed/speed feasibility

Saw Lab
Blade profiles → rim speed, kickback, bite-per-tooth, heat, kerf

CAM Core
Machine tool tables reference Tool Library by ID

Post-processing uses merged (tool + machine-slot) context

Art Studio
UI tool selectors

Preview operations

RMOS feasibility calls

14. Definition of Done
The Tool Library is considered stable when:

All tools used anywhere in ToolBox have entries in tool_library.json.

All materials have entries in material_library.json.

No calculator, router, CAM kernel, or Saw Lab module contains hard-coded tool geometry.

All tool and material metadata flows through the loaders.

RMOS 2.0 feasibility works solely through canonical data.

CAM post processors resolve all tool metadata via the registry.

15. Next Steps
Populate starter entries for common router bits, endmills, and saw blades.

Run migration scripts for data extraction from old scripts/databases.

Begin RMOS + Saw Lab integration.

Update CAM Core to reference tool_id instead of hard-coded values.

Add automated validation tests.

End of Tool_Library_Spec.md

yaml
Copy code
