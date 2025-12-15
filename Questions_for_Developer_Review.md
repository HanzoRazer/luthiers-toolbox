Questions for Developer Review
1. MLPath Scope & Evolution
The MLPath class is currently a lightweight wrapper around point lists. Should it evolve to include:

Arc segments (G2/G3) as first-class primitives rather than polyline approximations?
Z-depth metadata for 3D toolpaths?
Tool compensation state (inside/outside/on-path)?
2. DXF Version Strategy
We support R12/R14/R18 export. Questions:

Is R12 the mandated default for all CAM exports, or should this be user-configurable per post-processor?
Should we add R2018+ read support via ezdxf's newer API, or is conversion outside the app acceptable?
3. Saw Bridge Integration Path
The saw_bridge.py is a simplified physics stub. When the 76 Saw Lab files are committed:

Should saw_bridge.py delegate to the full Saw Lab calculators (saw_lab/calculators/*.py)?
Or should it remain a lightweight facade with the option to swap backends?
4. Tool Library CRUD
Currently tool_library.json is read-only. Do we need:

Admin API endpoints for adding/editing tools and materials?
User-local overrides (e.g., ~/.luthiers-toolbox/custom_tools.json)?
Database migration (SQLite/Postgres) for multi-user scenarios?
5. Rosette Router Registration
Wave 3 created rosette_geometry.py but I notice there's an existing rosette_router.py in art_studio/. Should the new geometry module:

Replace the existing router's geometry logic?
Coexist as a separate low-level engine?
Be merged into the existing router?
6. SVG Ingest Limitations
The svg_ingest_service.py handles basic shapes. Is there a roadmap for:

Transform matrix support (transform="rotate(45)")?
Text-to-path conversion (for V-carve lettering)?
Nested <g> group handling?
7. Test Strategy
We added 25 new tests. Questions:

Should Wave tests be isolated in their own directory (tests/wave_1_6/) or remain in the flat tests folder?
What's the coverage target for new modules? (Currently at ~36% overall)
8. Breaking Change Policy
These waves touch core geometry classes. What's the policy for:

Deprecating old code paths (e.g., any pre-MLPath geometry functions)?
API versioning if router signatures change?
