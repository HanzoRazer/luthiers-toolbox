the complete /docs/RMOS_STUDIO_DATA_STRUCTURES.md file, written in a professional engineering tone and structured for immediate inclusion in your repository.

RMOS_STUDIO_DATA_STRUCTURES.md
RMOS Studio – Data Structures & Object Model Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines all data structures, object models, serialization formats, and internal representations used within RMOS Studio.

It provides:

Canonical object definitions

Field-level specifications

Required/optional attributes

Constraints and validation rules

Serialization formats (JSON-centric)

Versioning considerations

Inter-module compatibility guidelines

This specification ensures that all modules—UI, Logic, Geometry, Planner, and JobLog—operate on consistent, standardized data objects.

2. Global Structural Principles

RMOS Studio data structures follow these rules:

Immutability for computed geometry
(Slices, tile segmentation, kerf calculations)

Mutable state for user-configuration objects
(Columns, rings, global parameters)

JSON-safe, deterministic serialization

Explicit version tagging
Every top-level structure must contain:

"version": "1.0"


Strict typing

Numerical values defined in millimeters

Angles in degrees

UI units convertible to mm

Colors defined as standardized codes

3. Core Object Model Overview
Project
 ├── Column
 │     └── List<Strip>
 ├── Pattern
 ├── List<Ring>
 ├── SegmentationData
 ├── List<Slice>
 ├── ManufacturingPlan
 └── JobLog


Each section below defines these objects in detail.

4. Column & Strip Structures
4.1 Strip Object
Strip {
    strip_id: string,
    width_ui: float,            // 1.0 ui = 1.0 mm
    width_mm: float,
    color_id: string,
    material_id: string,
    family_id: string,
    locked: bool
}

Constraints

width_ui ≥ 0.4

width_mm = width_ui * 1.0 (auto-converted)

family_id required for material planning

locked prevents UI manipulation

4.2 Column Object
Column {
    column_id: string,
    strips: List<Strip>,
    total_width_mm: float
}

Behavior

total_width_mm recalculated on any change

Strips must be in ordered sequence

5. Pattern Structure

Patterns represent presets or user-defined configurations.

5.1 Pattern Object
Pattern {
    pattern_id: string,
    name: string,
    type: "user" | "preset",
    preset_family: "traditional_spanish" | "herringbone" | "checkerboard" | null,
    seed: int,
    column_reference: string,   // column_id
    parameters: dict
}

6. Ring Structures
6.1 Ring Object
Ring {
    ring_id: int,
    radius_mm: float,
    width_mm: float,
    tile_length_mm: float,
    tile_count: int,
    twist_angle: float,
    herringbone_angle: float,
    kerf_mm: float,
    pattern_assignment: string,   // column_id
    segmentation_ref: string      // segmentation_id
}

Constraints

tile_length_mm > 0

tile_count ≥ 2

ring.width_mm ≥ column.total_width_mm

twist_angle within ±180°

kerf_mm > 0

7. Tile Segmentation Structures
7.1 SegmentationData Object
SegmentationData {
    segmentation_id: string,
    ring_id: int,
    radius_mm: float,
    circumference_mm: float,
    tile_count: int,
    tile_effective_length_mm: float,
    tile_bounds: List<TileBounds>
}

7.2 TileBounds Object
TileBounds {
    tile_index: int,
    angle_start_deg: float,
    angle_end_deg: float
}

8. Slice Structures (Saw Pipeline)
8.1 Slice Object
Slice {
    slice_id: string,
    ring_id: int,
    tile_index: int,
    angle_start_deg: float,
    angle_end_deg: float,
    slice_angle_deg: float,
    kerf_adjusted_angle_deg: float,
    material_map: List<string>,       // color/material ids
    strip_family_map: List<string>,   // material families
    geometry_ref: string              // segmentation_id
}

Behavior

Immutable after creation

Must remain in sequence tile_index = 0..N-1

8.2 SliceBatch Object
SliceBatch {
    batch_id: string,
    ring_id: int,
    kerf_mm: float,
    twist_angle: float,
    herringbone_angle: float,
    slices: List<Slice>
}

9. Manufacturing Planner Structures
9.1 MaterialUsage Object
MaterialUsage {
    strip_family_id: string,
    required_length_mm: float,
    scrap_mm: float,
    volume_mm3: float,
    volume_cm3: float
}

9.2 RingProductionSummary Object
RingProductionSummary {
    ring_id: int,
    tile_count: int,
    tile_length_mm: float,
    material_usage: List<MaterialUsage>,
    risk_indicators: List<string>
}

9.3 OperatorChecklist Object
OperatorChecklist {
    checklist_id: string,
    ring_id: int,
    steps: List<string>,
    warnings: List<string>,
    errors: List<string>
}

10. JobLog Structures
10.1 PlanningLog Object
PlanningLog {
    log_id: string,
    timestamp: string,
    pattern_id: string,
    column_data: Column,
    rings: List<Ring>,
    segmentation_refs: List<string>,
    warnings: List<string>,
    errors: List<string>,
    version: "1.0"
}

10.2 ExecutionLog Object
ExecutionLog {
    log_id: string,
    timestamp: string,
    operator_id: string,
    machine_id: string,
    environment: {
        humidity: float,
        temperature_c: float
    },
    ring_execution: List<RingExecutionData>,
    issues: List<string>,
    notes: string,
    version: "1.0"
}

10.3 RingExecutionData Object
RingExecutionData {
    ring_id: int,
    status: "completed" | "partial" | "failed",
    deviations: List<string>,
    actual_tile_count: int,
    material_used_mm: float,
    scrap_mm: float
}

10.4 RevisionHistory Object
RevisionHistory {
    revisions: List<RevisionRecord>
}

10.5 RevisionRecord Object
RevisionRecord {
    timestamp: string,
    user: string,
    change: string,
    previous_value: any,
    new_value: any
}

10.6 OperatorNotes Object
OperatorNotes {
    notes: List<NoteRecord>
}

10.7 NoteRecord Object
NoteRecord {
    timestamp: string,
    operator_id: string,
    note: string
}

11. Export Structures

Exports mirror internal structures but may include:

Rendering snapshots

PDF operator guides

Raw batch files

Summary JSON reports

Export naming convention:

{project_id}_{ring_id}_{timestamp}.json

12. Validation Structures

Validation engine consumes these structures:

ValidationReport {
    warnings: List<string>,
    errors: List<string>,
    pass: bool
}

13. Serialization Rules
13.1 JSON Required

All persistent data is stored in JSON.

13.2 No circular references

Only references by ID, not by nested objects.

13.3 Deterministic ordering

Lists must be sorted:

Strips by order in column

Tiles by tile_index

Slices by index

Rings by ring_id

13.4 Versioning Required

Every top-level structure must contain:

"version": "1.0"

14. Future Data Structure Extensions

CNC G-code object structures

Composite material metadata

3D geometry extensions

Multi-rosette project bundles

Cloud-sync metadata for collaborative workflows

15. File Location

This document belongs in:

/docs/RMOS_STUDIO_DATA_STRUCTURES.md

End of Document

RMOS Studio — Data Structures Specification (Engineering Version)