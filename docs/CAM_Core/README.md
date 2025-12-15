# CAM-Core Scaffold

This directory tracks CAM-Core architecture notes, schemas, and telemetry once the subsystem is live.

## Current Status
- Backend namespace `services/api/app/cam_core/` created with tools, feeds & speeds, saw lab, and pipeline placeholders.
- Router `cam_core_router` remains dormant until CP-S40+ patches register subrouters.
- Tool registry/importers exist as placeholders; persistence wiring is deferred to CP-S30.
- Feeds & speeds, Saw Lab operations, and pipeline ops are defined but intentionally return placeholder responses.

## Next Steps
1. Flesh out tool importer implementations (Fusion, Carbide, Vectric) with schema validation.
2. Add feeds & speeds calculators tied to material presets and machine profiles.
3. Implement Saw Lab planners plus queue-driven spotlight diff workflows (CP-S21).
4. Document telemetry contracts and learning lanes as they materialize.
