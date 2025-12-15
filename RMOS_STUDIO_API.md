the complete /docs/RMOS_STUDIO_API.md file, written in a professional engineering tone and structured for immediate inclusion in your repository.

RMOS_STUDIO_API.md
RMOS Studio – Application Programming Interface Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines the public and internal APIs used throughout RMOS Studio.
It provides a complete reference to how components communicate, how data flows between layers, and how geometry, manufacturing, and logging operations are requested and returned.

API design goals:

Deterministic behavior

Strong typing

Clear module boundaries

Testability

Error safety

Extensibility

The API forms the foundation for UI actions, automation, plugin development, and future CNC integration.

2. Architectural API Overview

The RMOS Studio API is divided into six major domains:

Project API

Column & Pattern API

Ring Configuration API

Geometry Engine API

Manufacturing Planner API

JobLog API

Export API

Each domain is self-contained and designed to minimize cross-module coupling.

3. Project API

Project-level API manages top-level operations and state.

3.1 create_project()
create_project(project_name: str) -> Project


Creates a new RMOS project with default parameters.

3.2 load_project()
load_project(path: str) -> Project


Loads project with:

Columns

Rings

Patterns

JobLogs

3.3 save_project()
save_project(project: Project, path: str) -> None


Serializes project using deterministic JSON ordering.

3.4 clone_project()
clone_project(project_id: str) -> Project


Used for revision-based branching and experimentation.

4. Column & Pattern API
4.1 Column API
4.1.1 add_strip()
add_strip(column_id: str, strip: Strip) -> Column


Adds a strip and recalculates total width.

4.1.2 remove_strip()
remove_strip(column_id: str, strip_id: str) -> Column

4.1.3 update_strip()
update_strip(column_id: str, strip_id: str, new_values: dict) -> Column

4.1.4 normalize_column()
normalize_column(column_id: str) -> float


Returns new total width in mm.

4.2 Pattern API
4.2.1 create_pattern()
create_pattern(name: str, column_id: str, preset_family: Optional[str]) -> Pattern

4.2.2 mutate_pattern()
mutate_pattern(pattern_id: str, seed: int) -> Pattern


Applies deterministic randomization.

4.2.3 save_pattern()
save_pattern(pattern: Pattern) -> None

5. Ring Configuration API
5.1 create_ring()
create_ring(radius_mm: float, width_mm: float, tile_length_mm: float) -> Ring

5.2 update_ring()
update_ring(ring_id: int, new_values: dict) -> Ring

5.3 assign_pattern_to_ring()
assign_pattern_to_ring(ring_id: int, column_id: str) -> Ring

5.4 set_twist_angle()
set_twist_angle(ring_id: int, angle_deg: float) -> Ring

5.5 set_herringbone_mode()
set_herringbone_mode(ring_id: int, angle_deg: float) -> Ring

5.6 validate_ring_geometry()
validate_ring_geometry(ring_id: int) -> ValidationReport

6. Geometry Engine API

This is the core computational engine.

6.1 compute_circumference()
compute_circumference(radius_mm: float) -> float

6.2 compute_tile_segmentation()
compute_tile_segmentation(ring_id: int) -> SegmentationData

6.3 generate_slices()
generate_slices(segmentation_id: str) -> List<Slice>

6.4 apply_kerf_compensation()
apply_kerf_compensation(slices: List<Slice], kerf_mm: float) -> List<Slice>

6.5 compile_slice_batch()
compile_slice_batch(ring_id: int) -> SliceBatch

6.6 validate_geometry()
validate_geometry(ring_id: int) -> ValidationReport

7. Manufacturing Planner API
7.1 strip_family_requirements()
strip_family_requirements(rings: List<Ring], columns: List<Column>) -> Dict

7.2 compute_volume()
compute_volume(width_mm: float, height_mm: float, length_mm: float) -> float

7.3 generate_material_usage_report()
generate_material_usage_report(plan: ManufacturingPlan) -> MaterialUsageReport

7.4 generate_operator_checklist()
generate_operator_checklist(ring_id: int) -> OperatorChecklist

8. JobLog API
8.1 create_planning_log()
create_planning_log(project: Project) -> PlanningLog

8.2 create_execution_log()
create_execution_log(project: Project, operator_id: str) -> ExecutionLog

8.3 append_revision_record()
append_revision_record(change: RevisionRecord) -> None

8.4 add_operator_note()
add_operator_note(operator_id: str, message: str) -> None

8.5 export_run_package()
export_run_package(project: Project, destination: str) -> str


Returns path of archive folder.

9. Export API
9.1 export_json()
export_json(data: dict, path: str) -> None

9.2 export_pdf()
export_pdf(renderable: RenderableDocument, path: str) -> None

9.3 export_saw_batch()
export_saw_batch(batch: SliceBatch, path: str) -> None

9.4 export_material_usage()
export_material_usage(report: MaterialUsageReport, path: str) -> None

9.5 export_ring_summary()
export_ring_summary(summary: RingProductionSummary, path: str) -> None

10. Error Handling & Exceptions

APIs must raise structured exceptions:

RMOSValidationError
RMOSGeometryError
RMOSMaterialError
RMOSExportError
RMOSStateError


Each includes:

error_id

message

context

recommended_action

Errors block processing.
Warnings are returned inside ValidationReports.

11. Versioning Rules

Every API response must include:

"version": "1.0"


Future updates must follow semantic versioning:

Major (incompatible signature changes)

Minor (new features, backward compatible)

Patch (bug fixes and internal adjustments)

12. Security & Integrity Rules

All objects must pass validation before being passed to Geometry Engine.

No API may return partial results unless explicitly documented.

All file exports must be checksum-protected.

Project save operations must be atomic (write → rename).

13. Future API Extensions

CNC G-code generation API

Cloud synchronization API

AI-assist pattern generation API

Hardware telemetry API

Plugin API for third-party pattern modules

14. File Location

This document belongs in:

/docs/RMOS_STUDIO_API.md

End of Document

RMOS Studio — Application Programming Interface Specification (Engineering Version)

If you want to continue the documentation suite, recommended next: