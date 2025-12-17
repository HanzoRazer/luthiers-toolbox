DEV_CHECKLIST_ART_STUDIO_ROSETTE.md (or similar) in the repo.
# Art Studio · Rosette Integration Checklist

Scope: Make Rosette + Compare Mode a **first-class lane** in Luthier’s ToolBox, backed by real API, SQLite jobs, and Vue labs.

---

## 0. Branch & Baseline

- [ ] Pull latest `main`
- [ ] Create feature branch: `feature/art-studio-rosette-integration`
- [ ] From `services/api`, run:
  - [ ] `pytest tests/ -q` (capture current pass/fail count for reference)

---

## 1. Backend – Rosette Store + Router

**Files (drop-in / confirm present):**

- [ ] `services/api/app/art_studio_rosette_store.py`
- [ ] `services/api/app/routers/art_studio_rosette_router.py`

**Store wiring:**

- [ ] `art_studio_rosette_store.py`:
  - [ ] `init_db()` creates `rosette_jobs` + `rosette_presets`
  - [ ] `list_presets()`, `save_job()`, `list_jobs()`, `get_job()` behave as expected
  - [ ] Default DB path: `ART_STUDIO_DB_PATH` env or `art_studio.db`
- [ ] Ensure `art_studio.db` is **ignored** in `.gitignore`

**Router wiring:**

- [ ] In `app/main.py` (or equivalent):

  ```python
  from .routers.art_studio_rosette_router import router as art_studio_rosette_router

  app.include_router(
      art_studio_rosette_router,
      prefix="/api",
      tags=["ArtStudioRosette"],
  )



 @router.on_event("startup") calls init_db()


Endpoints:


 POST /api/art/rosette/preview


 POST /api/art/rosette/save


 GET  /api/art/rosette/jobs


 GET  /api/art/rosette/presets


 POST /api/art/rosette/compare



2. Backend – Sanity Tests (Manual)
From services/api:


 Start API server (uvicorn/dev script)


 POST /api/art/rosette/preview


 Returns 200


 Response includes job_id, paths, and bbox




 POST /api/art/rosette/save


 Returns 200


 Job can be seen in /api/art/rosette/jobs




 GET /api/art/rosette/jobs


 Returns at least one entry after save




 POST /api/art/rosette/compare


 With two valid job IDs → 200 and diff_summary


 With invalid IDs → 404





3. Frontend – Rosette Designer View
Files:


 packages/client/src/views/ArtStudioRosette.vue


Behavior:


 Page loads at /art-studio/rosette


 Form fields:


 Job name


 Preset selector (Safe / Aggressive, etc.)


 Pattern type


 Segments


 Inner/Outer radius


 Units




 Buttons:


 “Preview Rosette” → calls POST /api/art/rosette/preview


 “Save Job” → calls POST /api/art/rosette/save




 Preview:


 SVG shows polygon paths from paths


 Uses bbox for viewBox




 Recent jobs:


 Uses GET /api/art/rosette/jobs


 Clicking job reloads that preview + form values




Router:


 In Vue router (src/router/index.ts or similar):
import ArtStudioRosette from "@/views/ArtStudioRosette.vue";

{
  path: "/art-studio/rosette",
  name: "ArtStudioRosette",
  component: ArtStudioRosette,
}




4. Frontend – Rosette Compare Mode View
Files:


 packages/client/src/views/ArtStudioRosetteCompare.vue


Behavior:


 Page loads at /art-studio/rosette/compare


 Job A selector (job_id_a) and Job B selector (job_id_b)


 Populated from GET /api/art/rosette/jobs




 “Compare A ↔ B” button:


 Calls POST /api/art/rosette/compare


 Stores compareResult in state




 Diff Summary:


 Shows pattern types & segments for A/B


 Shows radii & deltas


 Shows units match/diff


 Displays union bbox




 Dual canvases:


 Left: job A geometry


 Right: job B geometry


 Both use union bbox for shared viewBox




Router:


 In Vue router:
import ArtStudioRosetteCompare from "@/views/ArtStudioRosetteCompare.vue";

{
  path: "/art-studio/rosette/compare",
  name: "ArtStudioRosetteCompare",
  component: ArtStudioRosetteCompare,
}




5. Tests – Art Studio Rosette
Files:


 services/api/tests/test_art_studio_rosette_router.py (preview + save + jobs)


 services/api/tests/test_art_studio_rosette_compare.py (A/B diff)


Run:
From services/api:


 pytest tests/test_art_studio_rosette_router.py -v


 pytest tests/test_art_studio_rosette_compare.py -v


Expectations:


 Both tests pass


 DB tables get created via init_db() without errors



6. CAM Core Stabilization (Short List)
These are existing tests that should be prioritized next (to reduce noise):


 Helical router:


 Router registered in main.py


 Helical tests no longer 404




 Adaptive router:


 Invalid inputs return 400 (not raw ValueError)




 Geometry router (post validation):


 Unknown post_id returns 400/404




 Bridge router:


 DXF export tests pass


 /bridge/health returns { "status": "ok", ... }




Run key subsets:


 pytest tests/test_helical_router.py -v


 pytest tests/test_adaptive_router.py -v


 pytest tests/test_geometry_router.py -v


 pytest tests/test_bridge_router.py -v



7. CI – Minimal Health Check
GitHub Actions (or equivalent):


 Workflow installs backend dependencies


 From services/api:


 pytest tests/test_art_studio_rosette_*.py


 Optionally add a small CAM subset (adaptive/bridge/helical)




Success criteria:


 CI fails if Art Studio tests break


 CI is quick enough to run on every push/PR



8. Docs – Developer Onramp
Update docs (e.g. DEV_QUICKSTART.md / ART_STUDIO_DEVELOPER_HANDOFF.md):


 Add “Art Studio Rosette” section:


 API endpoints


 Vue routes


 SQLite DB path and env var




 Note how to:


 Run Art Studio tests


 Open Art Studio Rosette/Compare in the browser





9. Final Wrap Check


 Rosette preview + save work end-to-end


 Rosette compare works end-to-end


 Art Studio Rosette fully lives inside the main ToolBox repo


 Minimal tests are green locally


 CI runs Art Studio tests on push/PR


Once all boxes are checked, Rosette is a stable lane and ready for:


Overlay coloring (added/removed geometry)


Risk snapshot logging


Integration with Blueprint → DXF → Adaptive pipeline



If you want, I can also generate a shorter “sticky note” version (like a 10-line TODO you can pin in VS Code) based on this.
