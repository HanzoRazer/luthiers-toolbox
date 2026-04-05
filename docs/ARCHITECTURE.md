# Architecture — The Production Shop

## Domain Map

| Domain | Entry Router | Description |
|--------|-------------|-------------|
| CAM | routers/cam/cam_workspace_router.py | Neck pipeline wizard, G-code generation, machine context, preflight gates |
| RMOS | rmos/api/rmos_feasibility_router.py | Risk management — feasibility rules, GREEN/YELLOW/RED gate, run lifecycle |
| Art Studio | art_studio/api/ | Rosette, inlay, binding, purfling design and G-code |
| Saw Lab | saw_lab/ | Saw blade advisory, batch operations, toolpath validation |
| Calculators | routers/cam/ + calculators/ | Fret slots, bridge, chipload, plate thickness, feeds/speeds |
| Acoustics | routers/acoustics/plate_router.py | Plate thickness physics, coupled oscillator model, tonewood presets |
| Instruments | routers/instruments/ + instrument_geometry/ | Body outlines, neck profiles, headstock templates, graduation maps |
| Materials | materials/registry/ | Tonewood registry (71 species), machining properties, E_L/E_C for plate physics |
| Business | business/ | Estimator, BOM, pricing, cashflow, cost attribution |
| Safety | core/safety.py + cam/preflight_gate.py | @safety_critical decorator, preflight gate, BCamMachineSpec limits |
| Blueprint | routers/blueprint/ + routers/blueprint_cam/ | DXF import, phase pipeline, CAM reconstruction |
| Vision | vision/ | AI image analysis, generation, segmentation |

*Paths above are relative to `services/api/app/`.*

## Key Architectural Decisions

**Single-instance deployment**  
One FastAPI process, SQLite + file storage.  
See [docs/DEPLOYMENT_VALIDATION.md](DEPLOYMENT_VALIDATION.md).

**Safety layer**  
Every G-code-emitting path passes through RMOS feasibility or the preflight gate.  
See [docs/SAFETY.md](SAFETY.md).

**Router registry**  
All routers are registered in `router_registry/manifests/` and loaded via `load_all_routers()`. 95 routers across 6 domain manifests. See `router_registry/manifest.py`.

**Module architecture (frontend)**  
5 modules: Design, Art Studio, CAM, Shop Floor, Smart Guitar. Each module has a shell view and context-aware calculator slots.  
See `packages/client/src/views/`.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3 + TypeScript + Pinia |
| Backend | FastAPI + Pydantic v2 |
| Storage | SQLite + file system |
| CAM math | Python (numpy, scipy) |
| G-code | GRBL dialect (BCAMCNC 2030A) |
| CNC | BCAMCNC 2030A — 48"×24"×4" envelope |
