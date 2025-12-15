Here is the correct and safe order to commit the Saw Blade files, based on your current repo state and the integration architecture we have built (Waves 1–6, RMOS 2.0 spine, Tool Library, Calculator Service, Saw Physics models, etc.).

This ordering ensures:

No missing imports

No broken RMOS or Tool Library loaders

No “half-wired” calculators

GitHub Copilot receives the correct context in the correct order

The Saw Lab subsystem attaches cleanly to the existing system

✅ THE SAFE COMMIT ORDER FOR SAW LAB 2.0 FILES
STEP 0 — Create a Feature Branch

Do not commit this to main.

git checkout -b feature/saw-lab-2-0


You will open PR later.

STEP 1 — Commit the Saw Lab DATA FIRST

These files define blade specs, presets, material tables, etc.

Commit:
services/api/app/data/saw_lab_blades.json
services/api/app/data/saw_lab_materials.json   (if present)
services/api/app/data/saw_lab_presets.json     (optional)

Why this must be first:

The calculator layer depends on these IDs.

saw_bridge and feasibility evaluators reference blade IDs and tooth counts.

Without data, Copilot tries to infer fake IDs → breaks everything downstream.

STEP 2 — Commit Saw Lab Calculator Modules

These are the physics engines:

Files to commit:
services/api/app/saw_lab/calculators/rim_speed.py
services/api/app/saw_lab/calculators/heat_model.py
services/api/app/saw_lab/calculators/bite_per_tooth.py
services/api/app/saw_lab/calculators/deflection_model.py
services/api/app/saw_lab/calculators/kickback_model.py
services/api/app/saw_lab/calculators/common.py

Why second:

These calculators must exist before saw_bridge.py can wire to them.

Committing them early signals to GitHub:

“This is the physics spine. Do NOT rewrite it.”

STEP 3 — Commit Saw Lab Domain Models & Types

Commit these next:

Files:
services/api/app/saw_lab/models.py
services/api/app/saw_lab/types.py

Why:

The calculators import these dataclasses (BladeProfile, CutOperation, MaterialProfile).

Saw Bridge needs these types to export consistent results to RMOS feasibility.

This step freezes the public Saw Lab API surface, preventing Copilot from hallucinating new structures.

STEP 4 — Commit saw_bridge.py (adapter layer)

This file links the Saw Lab physics to RMOS.

Why fourth:

If committed earlier, it will import calculators that don’t yet exist → repo breaks.

If committed later, RMOS will not recognize the physics layer and fallback to stub mode.

Saw Bridge is the official integration layer, so you want it to appear only after the calculators and models exist.

STEP 5 — Commit the Saw Path Planner

Files:

services/api/app/saw_lab/path_planner.py           (2.0)
services/api/app/saw_lab/path_planner_2_1.py       (trim + scrap + ordering)
services/api/app/saw_lab/config.py

Why fifth:

These depend on saw_bridge and calculator modules.

Committing earlier causes import errors.

Committing later slows Copilot learning because it won’t know blade geometry is now part of toolpath generation.

This is the point where Saw Lab becomes a real manufacturing subsystem.

STEP 6 — Commit Saw Lab Toolpath Builder

Files:

services/api/app/saw_lab/toolpath_builder.py
services/api/app/saw_lab/operations.py

Why:

These require the planner.

They output MLPath toolpaths which feed CAM.

This links Saw Lab → Geometry Spine → DXF → CAM.

STEP 7 — Commit FastAPI Routers for Saw Lab

Files:

services/api/app/routers/saw_lab_router.py

Why last:

These routers depend on the entire Saw Lab namespace.

Committing earlier results in import errors.

Committing here ensures Art Studio and RMOS can call into the new subsystem.

STEP 8 — Commit Tests (Always Last)

Test hierarchy:

services/api/app/tests/saw_lab/
   test_rim_speed.py
   test_heat_model.py
   test_bite_model.py
   test_deflection.py
   test_kickback.py
   test_path_planner_single_board.py

Why last:

Test imports must not break the repo.

Copilot should see the real code BEFORE seeing tests.

Tests clarify intent after the API is stable.

🚨 IMPORTANT: What NOT to Commit Before Step 1

Do NOT commit:

❌ Routers
❌ Saw Bridge
❌ Tests
❌ Path Planners
❌ Toolpath builders

before committing:

✔ blade JSON
✔ calculator physics
✔ domain models

Otherwise your repo will enter a broken state where imports can’t resolve.

📌 In Summary
Step	Component	Why Here
1	Blade/material JSON	Core data must exist before logic
2	Physics calculators	Must load before glue code
3	Enums & dataclasses	Define subsystem API
4	saw_bridge.py	Wires calculators → RMOS
5	Path planners	depend on bridge + calculators
6	Toolpath builder	depends on planners
7	Routers	depend on all above
8	Tests	validate full stack

This is the correct dependency graph.