a concrete scaffolding plan that plugs the new Rosette Generator / RMOS Studio into your existing N8–N10 architecture without breaking anything, using an N11 “shell” layer on top of the current stack. 

RMOS_N8_N10_ARCHITECTURE

I’ll structure it as three bundles of scaffolding:

S1 – Backend Scaffolding (N11.0 Core hooks)

S2 – Frontend Scaffolding (N11.1 Rosette Designer shell)

S3 – Data & Ops Scaffolding (N11.2 analytics, safety, LiveMonitor)

Each bundle is “safe to merge” even if the geometry algorithms aren’t finished yet.

1. Design Goal & Constraints

From the N8–N10 doc, we know: 

RMOS_N8_N10_ARCHITECTURE

N8: SQLite stores + migration + export pipelines are already in place.

N9: Analytics, strip-family manager, artifacts, promotion lanes exist.

N10: LiveMonitor + safety policy engine + apprenticeship modes are live.

The Rosette generator adds:

Visual Rosette Designer UI and column/ring editing

Geometry engine: tile segmentation, slices, kerf, herringbone, twist

Manufacturing planner & CNC integration, but we only need scaffolding now.

So: we don’t implement the full RMOS Studio engine here. We just:

Create “real” modules and endpoints with stub implementations.

Wire them into N8–N10 stores, safety, LiveMonitor.

Give you a working skeleton route /rmos/rosette-designer that can be developed incrementally.

2. Bundle S1 – Backend Scaffolding (Core N11.0 Hooks)
2.1 Create rosette backend package

Add a new package but keep functions mostly as placeholders:

services/api/app/cam/rosette/
    __init__.py
    tile_segmentation.py
    kerf_compensation.py
    herringbone.py
    saw_batch_generator.py


Initial contents:

# tile_segmentation.py
from typing import Any, Dict

def compute_tile_segmentation_stub(ring: Dict[str, Any]) -> Dict[str, Any]:
    """
    SCAFFOLDING ONLY.
    Returns a minimal segmentation shape with dummy values.
    Replace later with real algorithm from RMOS_STUDIO_ALGORITHMS.md.
    """
    return {
        "segmentation_id": f"seg_stub_{ring.get('ring_id', 0)}",
        "ring_id": ring.get("ring_id", 0),
        "tile_count": 8,
        "tile_length_mm": 5.0,
        "tiles": []
    }


Similarly for kerf_compensation.py, herringbone.py, saw_batch_generator.py – just return simple, static structures with correct keys.

2.2 Add rosette API router with stub endpoints

Create services/api/app/api/routes/rmos_rosette_api.py:

from fastapi import APIRouter, HTTPException
from typing import Any, Dict
from ...cam.rosette.tile_segmentation import compute_tile_segmentation_stub

router = APIRouter(prefix="/api/rmos/rosette", tags=["rmos-rosette"])

@router.post("/segment-ring")
def segment_ring(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scaffolding endpoint: accepts ring config, returns dummy segmentation.
    """
    ring = payload.get("ring")
    if not ring:
        raise HTTPException(status_code=400, detail="Missing ring definition")
    return compute_tile_segmentation_stub(ring)

@router.post("/generate-slices")
def generate_slices_stub(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scaffolding endpoint: returns empty slice batch.
    """
    return {
        "batch_id": "stub-batch",
        "ring_id": payload.get("ring_id", 0),
        "slices": []
    }

@router.post("/patterns")
def create_rosette_pattern_stub(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scaffolding only – will later call PatternStore.
    """
    # For now just echo payload and attach a fake pattern_id
    return {**payload, "pattern_id": "rosette_stub_001"}


Register router in your main FastAPI app alongside existing RMOS routes. 

RMOS_N8_N10_ARCHITECTURE

2.3 Extend PatternStore for rosette pattern_type

Using the extended structure from the doc: 

RMOS_N8_N10_ARCHITECTURE

Add pattern_type TEXT column (default "generic").

Optionally add rosette_geometry TEXT for the richer JSON body.

Migration:

ALTER TABLE patterns ADD COLUMN pattern_type TEXT DEFAULT 'generic';
ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT;


In PatternStore.get():

def get(self, pattern_id: str) -> dict:
    row = self.db.get_pattern(pattern_id)
    pattern = self._row_to_dict(row)
    if pattern.get("pattern_type") == "rosette":
        return self._enrich_rosette_pattern(pattern)
    return pattern


For scaffolding, _enrich_rosette_pattern() can just return the raw JSON untouched.

2.4 Extend JobLogStore for rosette job types

Add new job_type values like "rosette_slice_batch" into your enums/constants, but keep behavior identical to other jobs for now. 

RMOS_N8_N10_ARCHITECTURE

Example joblog row stub:

{
  "job_id": "JOB-ROSETTE-STUB-001",
  "job_type": "rosette_slice_batch",
  "pattern_id": "rosette_stub_001",
  "status": "planned",
  "parameters": {},
  "results": {}
}


Logging can be wired later; for scaffolding, just ensure the type exists and doesn’t break analytics.

3. Bundle S2 – Frontend Scaffolding (Rosette Designer Shell)
3.1 Create Rosette Designer route & view

Add a new route (keeps all existing N8–N10 views intact): 

RMOS_N8_N10_ARCHITECTURE

// router/index.ts
{
  path: '/rmos/rosette-designer',
  name: 'RosetteDesigner',
  component: () => import('@/views/RosetteDesignerView.vue')
}


Add navigation entry in your RMOS menu.

3.2 Create minimal view & components

View shell: packages/client/src/views/RosetteDesignerView.vue

<template>
  <div class="rosette-designer-page">
    <h1>Rosette Designer (Scaffolding)</h1>
    <div class="layout">
      <ColumnStripEditor />
      <RingConfigPanel />
      <TilePreviewCanvas />
    </div>
  </div>
</template>

<script setup lang="ts">
import ColumnStripEditor from '@/components/rmos/ColumnStripEditor.vue'
import RingConfigPanel from '@/components/rmos/RingConfigPanel.vue'
import TilePreviewCanvas from '@/components/rmos/TilePreviewCanvas.vue'
</script>


Then create very thin scaffolding components under components/rmos/:

ColumnStripEditor.vue – show a simple list of mock strips, no editing logic yet.

RingConfigPanel.vue – simple form with radius, width, tile length, “Segment” button.

TilePreviewCanvas.vue – just shows “Preview coming soon” or renders the dummy segmentation.

3.3 Rosette Designer Pinia store (scaffolding only)

Create useRosetteDesignerStore.ts as a light wrapper around state + stub API calls, matching the doc’s pattern. 

RMOS_N8_N10_ARCHITECTURE

// useRosetteDesignerStore.ts
import { defineStore } from 'pinia'

export interface RosetteRing {
  ring_id: number
  radius_mm: number
  width_mm: number
  tile_length_mm: number
}

export const useRosetteDesignerStore = defineStore('rosetteDesigner', () => {
  const rings = ref<RosetteRing[]>([])

  async function segmentRing(ring: RosetteRing) {
    const res = await fetch('/api/rmos/rosette/segment-ring', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ring })
    })
    return await res.json() // uses stub backend for now
  }

  return { rings, segmentRing }
})


This gives you a vertical slice:

UI form → Pinia store → /api/rmos/rosette/segment-ring → stub result.

No geometry yet, but wiring is done.

4. Bundle S3 – Data, Analytics, LiveMonitor & Safety Scaffolding

This bundle ensures the rosette generator “hooks into” the existing N8–N10 systems, even if its core is still stubbed.

4.1 Data / migration scaffolding (N8 alignment)

Add pattern_type and rosette_geometry columns (already covered above).

Update any pattern queries that should ignore or include rosette patterns:

For “generic” analytics, filter pattern_type != 'rosette' initially.

For future rosette analytics, query pattern_type = 'rosette'. 

RMOS_N8_N10_ARCHITECTURE

This avoids breaking current dashboards until rosette features are stable.

4.2 Analytics scaffolding (N9 alignment)

Add placeholder endpoint for rosette analytics:

# rmos_analytics_api.py
@router.get("/patterns/rosette/tile-distribution")
def get_rosette_tile_distribution_stub():
    """
    Scaffolding: returns an empty distribution.
    """
    return {"patterns": [], "distribution": []}


Nothing calls it yet, but the endpoint exists and is testable.

4.3 LiveMonitor integration (N10 alignment)

You already have event types and LiveMonitor store; extend them with a rosette job event type. 

RMOS_N8_N10_ARCHITECTURE

Backend: when you (later) create a rosette job, send an event like:

event = {
  "event_type": "job_started",
  "job_id": "JOB-ROSETTE-STUB-001",
  "pattern_id": "rosette_stub_001",
  "status": "started",
  "timestamp": "...",
  "metadata": {
      "rosette": True,
      "rings": 0,
      "fragility_score": None,
  },
}


For scaffolding, you can trigger one manually (e.g., when calling generate-slices).

Frontend: LiveMonitor just receives it and shows it using existing UI.

4.4 Safety system scaffolding

Add a simple action type for rosette operations into the existing safety engine, but initially classify as “low” risk and always allow. 

RMOS_N8_N10_ARCHITECTURE

# safety evaluation stub
if payload["action"] == "rosette_design":
    return SafetyDecision(
        decision="allow",
        mode=current_mode,
        risk_level="low",
        requires_override=False,
        reason="Rosette design scaffold; no machine operation."
    )


Later, when rosette export → CNC is real, you can bump risk and require override tokens.

5. Suggested Implementation Order (Concrete Checklist)

If you want a straight “do this next” list:

Step 1 – DB & Store Scaffolding

 Add pattern_type + rosette_geometry columns to patterns.

 Extend PatternStore to recognize "rosette" pattern_type (no special logic yet).

 Add rosette job_type constants to JobLogStore.

Step 2 – Backend API shell

 Create services/api/app/cam/rosette/* with stub functions.

 Add rmos_rosette_api.py with segment-ring, generate-slices, patterns stub endpoints.

 Register rosette router under /api/rmos/rosette.

Step 3 – Frontend route & components

 Add /rmos/rosette-designer route in router.

 Create RosetteDesignerView.vue with three placeholder panels.

 Create minimal ColumnStripEditor.vue, RingConfigPanel.vue, TilePreviewCanvas.vue.

 Implement useRosetteDesignerStore with a call into /segment-ring.

Step 4 – Ops & Observability hooks

 Add rosette-specific event type to LiveMonitor (job events).

 Add a minimal safety evaluation path (action: "rosette_design" → allow).

 Add stub rosette analytics endpoint (/patterns/rosette/tile-distribution).

Step 5 – Smoke tests

 Backend tests: endpoints return 200 and expected dummy shapes.

 Frontend tests: visiting /rmos/rosette-designer mounts the view and can call segmentRing without crashing.

 Manual: confirm rosette calls do not affect existing N8–N10 views.

If you like, next I can take this plan and turn it into a concrete “Bundle N11-SCAFFOLDING” spec file (e.g., /docs/N11_ROSETTE_SCAFFOLDING_PLAN.md) that your devs can drop directly into the repo.

Sources
You said:
create this patch Bundle N11-SCAFFOLDING” spec file (e.g., /docs/N11_ROSETTE_SCAFFOLDING_PLAN.md) 
ChatGPT said:

Below is the complete, repo-ready /docs/N11_ROSETTE_SCAFFOLDING_PLAN.md — written as an official “patch bundle” specification in your established N-series style.
This is a formal engineering drop-in document for integration into the N8–N10 architecture.

N11_ROSETTE_SCAFFOLDING_PLAN.md
Patch Bundle N11 — Rosette Generator Integration Scaffolding

Version 1.0 — Architecture & Implementation Spec

1. Purpose of Patch N11

Patch N11-SCAFFOLDING introduces a complete, safe-to-merge scaffolding layer that integrates the RMOS Rosette Generator into the N8 → N10 architecture stack without requiring the full geometry engine to be implemented yet.

N11 does NOT include:

Real segmentation algorithms

Real kerf/herringbone logic

Real CNC geometry

N11 does provide:

A complete vertical slice from UI → Store → API → Backend → DB → JobLog → LiveMonitor

New pattern_type support

Rosette-safe analytics hooks

A safe expansion of the N10 safety/ops framework

A placeholder Rosette Designer page

All endpoints and data structures your real engine will need

N11 is the official integration framework for the future N12 Rosette Engine.

2. Architectural Context

N8–N10 currently provide:

N8 — SQLite stores, migrations, pattern registry, export layer

N9 — Analytics, strip-family management, promotion lanes

N10 — LiveMonitor, safety policy engine, apprenticeship modes

The Rosette Generator (RMOS Studio) introduces:

Column builder

Ring builder

Tile segmentation

Slice generator

Kerf, twist, herringbone

CNC export

Manufacturing planner

JobLog traces

Operator workflow

N11 scaffolding connects these new systems to N8–N10 in strictly stub form.

3. N11 Deliverables (High-Level)

N11 provides:

Backend Rosette Package (Stub Implementations)

Rosette API Router (/api/rmos/rosette)

PatternStore upgrades (rosette pattern_type)

JobLogStore upgrades (rosette job types)

Rosette Designer UI Shell & Components

Pinia Store: useRosetteDesignerStore

Analytics placeholder endpoints

LiveMonitor integration hooks

Safety Engine scaffolding

DB Migration Patch

All are functional but stubbed.
They allow real code to drop in without structural rework.

4. Backend Scaffolding (N11.0 Core)

Directory added:

services/api/app/cam/rosette/
    tile_segmentation.py
    kerf_compensation.py
    herringbone.py
    saw_batch_generator.py
    __init__.py


Each file contains a minimal stub return signature, e.g.:

def compute_tile_segmentation_stub(ring: dict) -> dict:
    return {
        "segmentation_id": f"seg_stub_{ring.get('ring_id', 0)}",
        "ring_id": ring.get("ring_id", 0),
        "tile_count": 8,
        "tile_length_mm": 5.0,
        "tiles": []
    }


Purpose: establish signatures and module names so N12 can replace logic with zero merge conflicts.

5. Rosette API Router (N11.0-B)

New router:

services/api/app/api/routes/rmos_rosette_api.py


Endpoints:

/segment-ring

Stub tile segmentation.

/generate-slices

Stub slice batch.

/patterns

Stub pattern creation for pattern_type = "rosette".

These are safe to call and structured identically to future real endpoints.

Registered under:

app.include_router(rmos_rosette_api.router)

6. PatternStore Scaffolding (N11.1)
Schema migration:
ALTER TABLE patterns ADD COLUMN pattern_type TEXT DEFAULT 'generic';
ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT;

Store updates:

Recognize pattern_type = "rosette".

Round-trip storage of rosette_geometry JSON.

No transformation logic until N12.

Implications:

Analytics should exclude rosette patterns unless explicitly filtered.

All UI components consuming patterns must ignore unknown pattern_type.

7. JobLog Store Extension (N11.1-B)

Add new job types:

"rosette_slice_batch"
"rosette_pattern_generation"
"rosette_preview"


Stubbed JobLog entries:

{
  "job_id": "JOB-ROSETTE-STUB-001",
  "job_type": "rosette_slice_batch",
  "pattern_id": "rosette_stub_001",
  "status": "planned",
  "parameters": {},
  "results": {}
}


JobLog filtering remains unchanged.
N12 will add real slice batch outputs.

8. Frontend Rosette Designer Shell (N11.2)

New route:

/rmos/rosette-designer


Vue view:

packages/client/src/views/RosetteDesignerView.vue


Includes:

ColumnStripEditor.vue (stub)

RingConfigPanel.vue (stub)

TilePreviewCanvas.vue (stub)

Each component is UI-only and communicates via the Pinia store.

The Designer View is mounted and navigable immediately.

9. Pinia Store Integration (N11.2-B)

Add:

packages/client/src/stores/useRosetteDesignerStore.ts


Minimal state:

rings: ref<RosetteRing[]>([])


Actions:

async function segmentRing(ring: RosetteRing)
async function generateSlices(ring_id: number)


Backend calls use the stub API routers.

This ensures the full vertical slice exists even without real algorithms.

10. Analytics Scaffolding (N11.3)

Add placeholder endpoint:

GET /api/analytics/patterns/rosette/tile-distribution


Returns:

{
  "patterns": [],
  "distribution": []
}


Analytics dashboards may safely ignore rosette patterns until N12.

11. LiveMonitor & Event Stream Hooks (N11.4)

Extend event types:

"job_started"
"job_planned"
"job_completed"
"job_failed"
"rosette"


When Rosette Designer runs a segmentation or slice generation, send a stub event:

event = {
  "event_type": "job_started",
  "job_id": "JOB-ROSETTE-STUB-001",
  "pattern_id": "rosette_stub_001",
  "metadata": {"rosette": True},
}


LiveMonitor must display these events using generic job tiles.

12. Safety Engine Scaffolding (N11.5)

Add a new action type:

"rosette_design"


Default safety rule (until N12):

if action == "rosette_design":
    return SafetyDecision(
        decision="allow",
        mode=current_mode,
        risk_level="low",
        requires_override=False,
        reason="Rosette scaffold has no manufacturing risk."
    )


When CNC export exists, risk level changes.

13. DB Migration Patch (N11.6)

Add migration:

migrations/patch_n11_rosette_scaffolding.sql


Contents:

ALTER TABLE patterns ADD COLUMN pattern_type TEXT DEFAULT 'generic';
ALTER TABLE patterns ADD COLUMN rosette_geometry TEXT;


This is a one-way migration and safe for production.

14. Testing Requirements (N11-QA)
Backend Tests

/segment-ring returns stub segmentation

/generate-slices returns empty slices array

/patterns accepts and returns pattern_type="rosette"

Frontend Tests

Visiting /rmos/rosette-designer mounts view

segmentRing() sends correct payload and receives stub response

Components do not throw on unset geometry

Integration Tests

JobLog accepts rosette job types

LiveMonitor receives a rosette event successfully

PatternStore handles pattern_type safely

15. Future Patch Linking

N11 → prepares → N12 (full engine)

N12 will deliver:

Real tile segmentation

Real slice calculation

Kerf & twist geometry

Herringbone alternation

Multi-ring assembly logic

CNC export layer

Full user previews

Slicing math from RMOS_STUDIO_ALGORITHMS.md

N11 ensures:

N12 will merge cleanly with no UI or backend architectural changes.

16. File Location

Place this document at:

/docs/N11_ROSETTE_SCAFFOLDING_PLAN.md
