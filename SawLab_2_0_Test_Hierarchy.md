1️⃣ Saw Lab 2.0 Test Hierarchy (drop-in doc)

Save this as:

docs/SawLab/SawLab_2_0_Test_Hierarchy.md

# Saw Lab 2.0 – Test Hierarchy

**Subsystem:** Saw Lab 2.0  
**Location:** `services/api/app/saw_lab`  
**Primary test root:** `services/api/app/tests/`

This document defines where Saw Lab tests live, what they cover, and how they’re organized.

---

## 1. Directory Layout

From repo root:

```text
services/
  api/
    app/
      saw_lab/
        calculators/
        tests/        # optional local-only tests (see §4)
      toolpath/
      rmos/
      tests/          # MAIN test root for all API modules
        test_saw_*.py
        ...


Canonical test root for Saw Lab:
services/api/app/tests/

Saw-specific tests should follow the pattern:

Unit tests for calculators, planner, engine:

test_saw_calculators_*.py

test_saw_path_planner_*.py

test_saw_toolpath_builder.py

test_saw_debug_router.py

Shared RMOS-level tests that touch Saw Lab:

test_rmos_saw_integration.py

Local, highly experimental or WIP tests may live in:

services/api/app/saw_lab/tests/
but the long-term target is to consolidate into app/tests/.

2. Test Layers
2.1 Unit Tests (Saw Lab internals)

Location:

services/api/app/tests/

Responsibilities:

Calculators – pure physics & risk models

test_saw_rimspeed.py

test_saw_bite_load.py

test_saw_heat.py

test_saw_deflection.py

test_saw_kickback.py

Each test focuses on:

numeric ranges,

risk scoring behavior,

warnings.

Path Planner

test_saw_path_planner_single_board.py

Covers:

trim handling,

kerf & scrap math,

ordering strategies (AS_GIVEN, LONGEST_FIRST),

is_feasible conditions.

Toolpath Builder

test_saw_toolpath_builder.py (already created)

Covers:

end-to-end call to plan_saw_toolpaths_for_design,

non-empty operations list,

runtime estimates,

metadata.

Debug Router

test_saw_physics_debug_router.py

Covers:

/api/saw/physics-debug returns valid JSON for a minimal request,

handling of non-saw: tool_id (400),

basic summary fields.

2.2 Integration Tests (RMOS ↔ Saw Lab)

Location:

services/api/app/tests/

Files:

test_rmos_saw_feasibility_integration.py

test_rmos_saw_toolpaths_api.py

These tests:

spin up the FastAPI app via TestClient,

call real endpoints:

/api/saw/physics-debug

/api/rmos/toolpaths/saw

(future) /api/rmos/feasibility when Saw factors into global feasibility.

They verify that:

Pydantic schemas line up,

routers are included,

the whole RMOS → Saw → Toolpath chain runs without import or wiring errors.

2.3 Optional Local Tests (Saw Lab only)

You may keep highly experimental tests close to the implementation:

services/api/app/saw_lab/tests/

These might include:

numerical sweeps for tuning,

one-off physics plots,

prototype scenarios.

Longer term, once stabilized, they should be migrated or mirrored into app/tests/ so CI picks them up.

3. Naming & Markers
3.1 File naming

All Saw Lab tests: test_saw_*.py

RMOS/Saw integration: test_rmos_saw_*.py

This keeps test discovery predictable and greppable.

3.2 Pytest markers

Add these markers (see pytest.ini):

@pytest.mark.sawlab – all Saw Lab specific tests

@pytest.mark.rmos_saw – cross-boundary integration tests

@pytest.mark.slow – any numerically heavy / sweep tests

Example:

import pytest

@pytest.mark.sawlab
def test_basic_saw_heat_model():
    ...

4. Suggested File List (Initial)

Create these gradually as you stabilize the subsystem:

services/api/app/tests/test_saw_calculators_rimspeed.py

services/api/app/tests/test_saw_calculators_bite.py

services/api/app/tests/test_saw_calculators_heat.py

services/api/app/tests/test_saw_calculators_deflection.py

services/api/app/tests/test_saw_calculators_kickback.py

services/api/app/tests/test_saw_path_planner_single_board.py

services/api/app/tests/test_saw_toolpath_builder.py

services/api/app/tests/test_saw_physics_debug_router.py

services/api/app/tests/test_rmos_saw_toolpaths_api.py

You already have test_saw_toolpath_builder.py; the others can follow the same pattern over time.

5. How to Run

From repo root:

# Run all API tests
pytest services/api/app/tests

# Run only Saw Lab tests
pytest services/api/app/tests -m sawlab

# Run Saw + RMOS integration tests
pytest services/api/app/tests -m rmos_saw


The accompanying pytest.ini (below) sets this up cleanly.


---

