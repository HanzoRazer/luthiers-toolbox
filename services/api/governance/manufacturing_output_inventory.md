# Manufacturing output inventory

Inventory coverage is not manufacturing qualification. `UNEXAMINED` does not mean safe. A listed authority key does not prove that enforcement occurs before generation.

Pinned base SHA: `cf3f1c131fbee4586d82780b865eb1d09af8a350`

- OpenAPI paths: 1078
- Live route operations: 1157
- Candidates: 239
- Confirmed emitters: 47
- Delegates: 3
- Non-emitting: 0
- Unexamined: 189
- Fail-closed: 35
- Permitted by authority: 0
- Live-ungoverned: 15
- Unknown containment: 189
- Not applicable: 0

## Authority layers

- `manufacturing_output`: 21
- `none`: 15
- `readiness`: 14
- `unknown`: 189

## Live-ungoverned families

- `app.cam.rosette.cnc.cnc_gcode_exporter.generate_gcode_from_toolpaths`: 2
- `inline`: 2
- `app.art_studio._inlay_gcode_addon.generate_inlay_gcode`: 1
- `app.calculators.fret_slots_cam.generate_fret_slot_toolpaths`: 1
- `app.rmos.api_contracts.generate_toolpaths_for_design`: 1
- `app.routers.geometry.bundle_router.export_bundle`: 1
- `app.routers.geometry.bundle_router.export_bundle_multi`: 1
- `app.routers.geometry.export_router.export_gcode`: 1
- `app.routers.neck.headstock_transition_export.build_transition_gcode`: 1
- `app.routers.polygon_offset_router.generate_polygon_offset_nc_program`: 1
- `app.routers.radius_dish_router.generate_radius_dish_gcode`: 1
- `app.services.saw_lab_toolpaths_from_decision_service.generate_toolpaths_from_decision`: 1
- `generate_toolpaths_from_decision`: 1

## Unknown-containment families

- `unresolved`: 189

## Reconciliation

Historical audit baseline is 420 broad candidates, 126 handler identities, and 56 candidates with at least three signals. This tree recomputes 239 live candidates, 239 handler identities, and 58 high-signal rows. The audit scanner is not in the repository. The difference is the live signal census at the pinned SHA, not a forced equal to 420. Five optional routers load only when Pillow, OpenCV, and Markdown are installed; this count includes them. HEAD and OPTIONS aliases are not separate candidates. A path token alone does not confirm emission.

This inventory is not imported by production routers. It does not qualify a generator or claim the repository is contained.
