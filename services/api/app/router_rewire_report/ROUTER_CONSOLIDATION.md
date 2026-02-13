# Router Consolidation Report

Generated: 2026-02-12 21:46:25.907996

## Current State

- **Router Files:** 188
- **Total Routes:** 378
- **Files > 500 lines:** 0
- **Duplicate Paths:** 42

## Route Classification

- **Core:** 0 routes
- **Power:** 4 routes
- **Internal:** 39 routes
- **Cull:** 335 routes

## Consolidation Plan


### Phase 1: Quick Wins (Delete Unused)
- Delete `/generate` from neck_router.py
- Delete `/export_dxf` from neck_router.py
- Delete `/presets` from neck_router.py
- Delete `/features` from health_router.py
- Delete `/features/catalog` from health_router.py
- Delete `/toolpaths` from smart_cam_router.py
- Delete `/preview` from smart_cam_router.py
- Delete `` from presets_router.py
- Delete `/{preset_id}` from presets_router.py
- Delete `` from presets_router.py

### Phase 2: Consolidation
- Merge `/generate` from 2 locations
- Merge `/presets` from 4 locations
- Merge `/toolpaths` from 3 locations
- Merge `/preview` from 5 locations
- Merge `` from 6 locations
- Merge `/{preset_id}` from 3 locations
- Merge `/` from 5 locations
- Merge `/templates` from 3 locations
- Merge `/info` from 5 locations
- Merge `/history` from 2 locations

### Phase 3: Decomposition

### Phase 4: Standardization
- Consolidate cam routers into routers/cam/
- Consolidate art routers into routers/art/
- Consolidate probe routers into routers/probe/
- Consolidate geometry routers into routers/geometry/
- Consolidate dxf routers into routers/dxf/