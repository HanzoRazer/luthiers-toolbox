# Decomposition Backlog

**Generated:** 2026-03-16  
**Source:** Direct codebase scan. No gap IDs or commit hashes. Structural debt only.

---

## 1. Python files in `services/api/app/` over 500 lines

| File path | Lines | What it does | Decomposition strategy |
|-----------|-------|--------------|------------------------|
| `cam/rosette/prototypes/herringbone_embedded_quads.py` | 1241 | Embedded herringbone DXF tile quads (dark/light parity arrays); ring dimensions and quad data for rosette manufacturing. | Move raw quad arrays to JSON/data file; keep module as loader + validation. Split DARK_QUADS_RAW / LIGHT_QUADS_RAW into separate data module. |
| `router_registry/manifest.py` | 676 | Declarative router manifest: list of RouterSpec (module, prefix, tags, required, category) for all API routers. | Keep manifest as single source of truth; extract optional helpers (e.g. category filters) to a small loader/util module if needed. |
| `cam/rosette/modern_pattern_generator.py` | 682 | CAM rosette pattern generation: tile placement, segmentation, modern pattern logic. | Split into: (1) pattern definitions/presets, (2) tile placement engine, (3) segmentation/geometry. |
| `generators/neck_headstock_config.py` | 661 | Neck and headstock config: dataclasses, enums, tool configs, presets, headstock outlines, tuner positions, profile cross-sections. | Extract presets and tool configs to YAML/JSON or separate config module; keep geometry helpers in one module, split headstock outline vs profile logic if still large. |
| `core/job_queue/queue.py` | 631 | Async job queue with SQLite persistence and background worker; job state, priority, processing loop. | Extract persistence layer (SQLite schema/ops) to a store module; keep queue orchestration and worker loop in main module. |
| `instrument_geometry/coordinate_system.py` | 629 | Unified coordinate system: transforms, conventions, conversions for instrument geometry. | Split by concern: (1) transform math, (2) convention constants and validation, (3) serialization/API adapters if any. |
| `art_studio/services/generators/inlay_patterns.py` | 625 | Inlay pattern generators: registry delegating to GridEngine, RadialEngine, PathEngine, MedallionEngine; pure functions (params → GeometryCollection). | One module per engine (grid, radial, path, medallion); thin registry in inlay_patterns.py that imports and delegates. |
| `cam/dxf_advanced_validation.py` | 615 | DXF advanced validation: format, geometry, bounds checks for CAM readiness. | Split into: (1) format checks, (2) geometry/bounds checks, (3) result aggregation and reporting. |
| `calculators/binding_geometry.py` | 781 | Binding geometry: neck/headstock/body binding paths, miter joints, bend radius validation, material constraints. | Split into: neck binding, headstock binding, body binding path, shared types and validation. |
| `calculators/cavity_position_validator.py` | 705 | Cavity position validation: factory references, cavity types per model, validate single/all cavities. | Split by instrument model family or by validator type (pickup, wiring, control cavity); keep shared types and factory data in one small module. |
| `cam/rosette/presets.py` | 578 | Rosette presets: ring definitions, segment options, tile maps, recipe presets. | Move preset data to JSON/YAML; keep loader and schema in Python. |
| `generators/stratocaster_body_generator.py` | 572 | Stratocaster body outline generator: parametric contour, horn geometry, belly cut. | Extract control-point/curve math to a shared body_curves module; keep Strat-specific params and SVG/DXF export here. |
| `saw_lab/toolpaths_validate_service.py` | 568 | Saw Lab toolpath validation service: validate toolpath artifacts and constraints. | Extract validation rules to a rules module; keep orchestration and response building in service. |
| `cam/rosette/prototypes/shape_library.py` | 587 | Rosette shape library: reusable shapes for rosette prototypes. | Split by shape family (polygons, arcs, tiles) or move to a package with one file per shape group. |
| `routers/cam_post_v155_router.py` | 518 | CAM post-processor v1.55 router: G-code post-processing endpoints. | Extract post-processor logic to cam/post_processor or existing module; keep router thin (request/response only). |
| `routers/blueprint_cam/contour_reconstruction.py` | 526 | Contour reconstruction: rebuild closed contours from LINE/ARC entities for blueprint CAM. | Split: (1) entity parsing, (2) contour assembly algorithm, (3) API handler. |
| `cam/post_processor.py` | 529 | CNC post-processor: tool length compensation (G43), cutter comp (G41/G42), tool-change sequencing, controller dialects. | Split by dialect (GRBL, Mach3, Haas, etc.) into small emitter modules; single orchestrator that delegates. |
| `cam/profiling/profile_toolpath.py` | 542 | Profile toolpath generation: outside contour from LWPOLYLINE, tabs, lead-in, climb/conventional direction. | Extract tab and lead-in geometry to helpers; keep main toolpath algorithm in one file. |
| `cam/rosette/tile_segmentation.py` | 553 | Rosette tile segmentation: split rings into tiles for manufacturing. | Split: (1) ring geometry, (2) tile boundary computation, (3) output formatting. |
| `cam/rosette/traditional_builder.py` | 539 | Traditional rosette builder: classic rosette construction from specs. | Extract pattern definitions to data; keep build steps as small functions. |
| `services/rosette_cam_bridge.py` | 516 | Bridge between rosette design and CAM: converts design to CAM-ready output. | Split: (1) design parsing, (2) toolpath generation call, (3) response shaping. |
| `generators/bezier_body.py` | 595 | Bézier body outline generator: params, presets, control points, outline generation, JSON/SVG/DXF export. | Extract presets to data file; split export formats (JSON, SVG, DXF) to small writers. |
| `calculators/unified_canvas.py` | 561 | Unified canvas calculator: coordinate transforms and region logic for inlay/canvas workflows. | Split: (1) coordinate transforms, (2) region/bounding logic, (3) any API-facing helpers. |
| `cam/carving/surface_carving.py` | 509 | 3D surface carving: graduation maps, roughing/finishing toolpaths, z-levels for carved tops. | Split: (1) graduation map math, (2) roughing strategy, (3) finishing strategy, (4) orchestration. |
| `routers/blueprint_cam/dxf_preprocessor.py` | 509 | DXF preprocessor: format normalization, curve densification, dimension validation for CAM. | Split: (1) format normalization, (2) densification, (3) validation and info endpoint. |
| `cam/rosette/prototypes/__archived__/generative_explorer_viewer.py` | 674 | Archived generative explorer viewer (rosette prototype). | Low priority; keep archived or remove if unused. |
| `cam/rosette/prototypes/__archived__/diamond_chevron_viewer.py` | 549 | Archived diamond chevron viewer (rosette prototype). | Low priority; keep archived or remove if unused. |
| `cam/rosette/prototypes/__archived__/rosette_studio_viewer.py` | 512 | Archived rosette studio viewer (rosette prototype). | Low priority; keep archived or remove if unused. |
| `cam/rosette/prototypes/herringbone_parametric.py` | 555 | Parametric herringbone rosette prototype. | Extract constants and quad generation to separate module; keep parametric API thin. |
| `tests/calculators/test_binding_geometry.py` | 536 | Unit tests for binding geometry (neck, headstock, body, miter, validation). | Split test file by calculator module (neck, headstock, body) or by test class. |
| `tests/test_e2e_workflow_integration.py` | 504 | E2E workflow integration tests. | Split by workflow (e.g. one file per major user journey) or mark as incomplete and trim. |

---

## 2. Vue files in `packages/client/src/` over 500 lines

| File path | Lines | What it does | Decomposition strategy |
|-----------|-------|--------------|------------------------|
| `views/art-studio/RosetteWheelView.vue` | 1240 | Interactive rosette wheel designer: 5-ring wheel, 19 tiles, symmetry modes, drag-drop, Tiles/Library/BOM/MFG tabs, recipes, save/load .rsd, SVG export, BOM CSV, manufacturing checks, undo/redo, shortcuts. | Extract sidebar (Tiles/Library/BOM/MFG) into child components; extract wheel canvas to RosetteWheelCanvas.vue; extract modals (rename, etc.) and toast to composables or small components. |
| `views/lab/MachineManagerView.vue` | 1014 | CNC machine manager: machine profiles CRUD, tools per machine, posts API; list/detail forms and table UI. | Split: MachineProfileList.vue, MachineProfileForm.vue, MachineToolsPanel.vue; share types and API client in composables. |
| `components/cam/ToolpathCanvas3D.vue` | 997 | 3D toolpath visualization canvas (Three.js or similar). | Extract scene setup, camera controls, and toolpath mesh building into composables or subcomponents; keep view as orchestrator. |
| `components/cam/ToolpathAnnotations.vue` | 893 | Toolpath annotations overlay (labels, markers, measurements on toolpath view). | Extract annotation types to subcomponents; use composable for annotation state and hit-testing. |
| `views/art-studio/VCarveView.vue` | 878 | V-Carve view: V-carve toolpath UI, parameters, preview. | Split toolbar, parameter panel, and preview canvas into components; share state via composable or store. |
| `components/blueprint/CalibrationPanel.vue` | 850 | Blueprint calibration panel: scale, reference points, calibration workflow. | Split: calibration form, reference point list, preview/result; extract calibration logic to composable. |
| `components/cam/ToolpathStats.vue` | 860 | Toolpath statistics panel: travel/cut time, distance, counts. | Extract stat blocks to small presentational components; keep data fetching and aggregation in composable. |
| `components/cam/ChipLoadPanel.vue` | 804 | Chip load calculator/panel: feed/speed and chip load inputs and results. | Extract form and results into subcomponents; composable for chip load calculation. |
| `components/cam/ToolpathComparePanel.vue` | 797 | Toolpath comparison panel: side-by-side or diff of toolpaths. | Split: comparison controls, left/right viewers, diff summary; composable for comparison state. |
| `components/cam/ToolpathCanvas.vue` | 798 | 2D toolpath canvas (SVG or canvas). | Extract layers (toolpath, grid, selection) to subcomponents or composables; keep canvas orchestration here. |
| `views/art-studio/InlayDesignerView.vue` | 773 | Inlay designer view: inlay pattern editing, canvas, tools. | Split: toolbar, layer/list panel, canvas; extract inlay tools to small components or composables. |
| `views/business/EngineeringEstimatorView.vue` | 771 | Engineering estimator: WBS, labor/materials, estimate workflow. | Split: WBS tree, labor panel, materials panel, summary; composable for estimate state and calculations. |
| `views/art-studio/ReliefCarvingView.vue` | 744 | Relief carving view: relief toolpath parameters and preview. | Split: parameter form, preview canvas; composable for relief params and API calls. |
| `views/business/EstimatorAnalyticsDashboard.vue` | 716 | Estimator analytics dashboard: charts and metrics for estimates. | Extract chart widgets to components; composable for data fetching and aggregation. |
| `components/cam/ToolpathFilter.vue` | 697 | Toolpath filter UI: filter by type, layer, or other criteria. | Extract filter groups to subcomponents; composable for filter state and applied filters. |
| `views/AppDashboardView.vue` | 663 | App dashboard: landing or overview of main app sections. | Split dashboard into widget components (cards, links, recent activity); keep layout and routing here. |
| `components/wizards/JobCreationWizard.vue` | 656 | Job creation wizard: multi-step job creation flow. | One component per step; parent wizard handles step state and navigation. |
| `views/dev/NavProto.vue` | 651 | Dev navigation prototype: experimental nav structure. | Low priority; split or remove when nav is finalized. |
| `components/cam/FeedAnalysisPanel.vue` | 671 | Feed/speed analysis panel: feed analysis inputs and results. | Extract form and result blocks to subcomponents; composable for analysis logic. |
| `components/cam/ToolpathCompare.vue` | 560 | Toolpath compare (compact): compare two toolpaths. | Extract viewer and diff summary to subcomponents; composable for comparison data. |
| `components/cam/ToolpathAudioPanel.vue` | 566 | Toolpath audio panel: audio feedback or simulation for toolpath. | Extract controls and visualization to subcomponents; composable for audio/timing logic. |
| `components/generators/neck/StratocasterNeckGenerator.vue` | 573 | Stratocaster neck generator: neck params and preview. | Split: param form, preview area; composable for generator state and API. |
| `components/rmos/ManufacturingCandidateList.vue` | 579 | Manufacturing candidate list: list of candidates with actions. | Extract list item to component; extract filters and actions to composable. |
| `components/rmos/ManufacturingCandidateListV2.vue` | 565 | Manufacturing candidate list v2: updated list UI. | Same as v1: item component, filters, composable. |
| `components/rmos/RosettePresetBrowser.vue` | 563 | Rosette preset browser: browse and select rosette presets. | Extract preset card and grid to components; composable for preset loading and selection. |
| `components/wizards/DxfToGcodeWizard.vue` | 581 | DXF to G-code wizard: multi-step DXF import and G-code generation. | One component per step; wizard parent for state and flow. |
| `components/wizards/FretboardWizard.vue` | 591 | Fretboard wizard: fretboard design steps. | One component per step; composable for fretboard state. |
| `views/business/EstimatorComparePanel.vue` | 658 | Estimator compare panel: compare two estimates. | Split: comparison controls, left/right summary, diff; composable for data. |
| `views/business/EstimatorHistoryPanel.vue` | 560 | Estimator history panel: list of past estimates. | Extract list and row to components; composable for fetching and filtering. |
| `views/business/EstimatorPresetsPanel.vue` | 609 | Estimator presets panel: save/load estimate presets. | Extract preset list and form to components; composable for preset CRUD. |
| `views/business/EstimatorTemplatesPanel.vue` | 506 | Estimator templates panel: estimate templates. | Extract template list and editor to components; composable for template state. |
| `views/dev/ComponentGallery.vue` | 505 | Dev component gallery: showcase of components. | Low priority; keep for dev or split by category. |
| `components/cam/StockSimulationPanel.vue` | 531 | Stock simulation panel: stock geometry and simulation. | Extract form and 3D preview to subcomponents; composable for simulation state. |
| `components/adaptive/AdaptivePocketLab.vue` | 502 | Adaptive pocket lab: adaptive pocketing parameters and preview. | Split: param form, preview; composable for adaptive logic and API. |
| `components/saw_lab/SawContourPanel.vue` | 514 | Saw Lab contour panel: contour display and editing for saw jobs. | Extract contour viewer and controls to subcomponents; composable for contour state. |
| `views/InstrumentDesignView.vue` | 520 | Instrument design view: high-level instrument design layout. | Split: instrument selector, design panels by section; composable for design state. |

---

## 3. Broad exception count by domain

Counts are of literal `except Exception` (or `except Exception as e`) in the listed directories. Commented or narrowed catches (e.g. `except (ValueError, OSError)`) are not counted.

| Domain | Directory | Count | Notes |
|--------|-----------|-------|--------|
| CAM | `services/api/app/cam/` | 4 | `dxf_advanced_validation.py` (2), `routers/fret_slots_router.py` (2). |
| RMOS | `services/api/app/rmos/` | 7 | `rosette_cam_router.py` (4), `mvp_router.py` (1), `safety_router.py` (1), `runs_v2/store_delete.py` (1; intentional broad catch for callback re-raise, audited). |
| Saw Lab | `services/api/app/saw_lab/` | 0 | None. |
| Calculators | `services/api/app/calculators/` | 0 | None. |

**Total (broad `except Exception` in these four domains):** 11 (or 10 if the single intentional catch in `store_delete.py` is excluded from remediation).

---

*End of backlog.*
