

1️⃣ Fan-Fret Perpendicular Fret + Fret Math

From services/api/app:

instrument_geometry/models.py

Any of:

instrument_geometry/fretboard*.py

instrument_geometry/fan_fret*.py

calculators/fret_slots_cam.py

Tests:

The test file(s) that mention:

fan-fret

“perpendicular fret”

angle_rad / is_perpendicular

2️⃣ Multi-Post Fret-Slot Export

From services/api/app:

Current fret-slot CAM:

calculators/fret_slots_cam.py

Current CAM routers touching fret slots / CAM preview:

Any of:

routers/cam_preview_router.py

routers/cam_fret_slots_export_router.py

any routers/cam_* that exposes fret-slot endpoints

Any postprocessor code (if present):

cam/postprocessors/ (tree + files), or any file with things like *_postprocessor, *_gcode, post_id

Tests:

The test file that checks:

/api/cam/fret_slots/export_multi or similar

3️⃣ Rosette Pattern API + Saw-Ops Slice / Pipeline

Rosette / patterns (from services/api/app):

Any of:

rosette/

art_studio/

patterns/

Any rosette-related files:

*rosette*.py

Saw Lab / Saw Ops:

saw_lab/ (all files or at least a tree listing + key modules)

Any saw-related routers:

routers/saw_*.py

routers/rosette_*.py

routers/rmos_* that mention saw/slice/rosette

Legacy rosette (if still in repo):

server/pipelines/rosette/ (file list + key files like rosette_calc.py, rosette_to_dxf.py)

Tests:

Test files that call:

/api/rosette-patterns

/rmos/saw-ops/slice/preview

/rmos/saw-ops/.../handoff

4️⃣ Analytics N9 (pattern/material analytics, anomalies, risk%)

From services/api/app:

Analytics routers:

routers/analytics*.py

Analytics logic:

analytics/ (all .py files)

Data they analyze:

Pattern models:

any rosette/pattern model files (e.g. models/rosette_pattern*.py or similar)

Material / strip models:

materials/*.py

models/material*.py

Tests:

Test files that mention:

categories, min_rings, radius, families.usage

width, suppliers

anomalies, risk_percent

5️⃣ MM0 Strip-Families Endpoint (405 error)

From services/api/app:

Routers for materials/strips:

routers/materials_router.py

routers/strip_router.py (if it exists)

Any strip/board calculators:

calculators/strip_*.py

or anything under materials/ dealing with “strip families”

Tests:

The test file that hits the MM0 / strip-families endpoint and gets 405

6️⃣ WebSocket OpenAPI / Docs (N10)

From services/api/app:

WebSocket router(s):

Any file in routers/ that:

uses WebSocket / websocket from FastAPI, or

has “ws”, “realtime”, “live” in the name

main.py:

The part where routers are included and WebSockets are defined

Tests:

The test file that checks:

WebSocket docs / OpenAPI presence

7️⃣ RMOS AI Core / Directional Workflow (port 8010)

Project / infra files:

docker-compose.yml (or any compose file that might define a service on port 8010)

Any separate RMOS AI service directory (if exists), e.g.:

rmos_ai/

services/rmos_ai/

Client code inside the main app:

Any file that contains:

":8010" or "http://localhost:8010"

Tests:

The test files that fail with connection refused on port 8010 (RMOS AI core, directional workflow).

If you want to start small, the easiest first batch is:

fret_slots_cam.py

instrument_geometry/models.py

(any fan-fret/fretboard module if it exists)

the two test files for:

perpendicular-fret

multi-post export

Then we can knock out those two features first and move down the list.