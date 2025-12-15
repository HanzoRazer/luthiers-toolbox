the complete /docs/RMOS_STUDIO_VALIDATION.md file, written in a professional engineering tone and structured to finalize the RMOS Studio software-engineering suite.

RMOS_STUDIO_VALIDATION.md
RMOS Studio – Validation Engine & Constraint Enforcement Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines the validation framework used throughout RMOS Studio.
It ensures that every component—from strip definitions to final slice batches—meets strict structural, geometric, and manufacturing constraints.

The validation system:

Prevents unsafe manufacturing output

Ensures consistent geometric operations

Controls input accuracy

Maintains system integrity

Enforces data structure compliance

Blocks downstream errors before they occur

Validation applies at every stage of the RMOS pipeline.

2. Validation Framework Overview

RMOS Studio uses a multi-layer validation architecture:

Input Validation

Column Validation

Ring Geometry Validation

Segmentation Validation

Slice Generation Validation

Kerf Compensation Validation

Manufacturing Planner Validation

JobLog Validation

Export Validation

All validations return a standardized:

ValidationReport {
    warnings: List<string>,
    errors: List<string>,
    pass: bool
}


Errors block the operation; warnings allow continuation.

3. Input Validation

Validates all user-supplied or UI-transmitted values.

3.1 Numerical Input Rules

Must be numeric

Must be finite (no NaN / Infinity)

Must be ≥ 0 unless explicitly allowed

Units must be correct (UI → mm conversion applied)

3.2 Column Input Rules
width_ui ≥ MIN_STRIP_WIDTH_UI (0.4)
color_id != null
material_id != null
family_id != null

3.3 Ring Input Rules

radius_mm > MIN_RADIUS (default: 10 mm)

width_mm > 0

tile_length_mm > MIN_TILE_LENGTH (0.4 mm)

twist_angle ∈ [-180°, +180°]

herringbone_angle ∈ [0°, 60°]

kerf_mm ≥ 0.1 mm

4. Column Validation

Ensures column structure is manufacturable and geometrically compatible.

4.1 Strip Width Validation

Checks each strip:

if strip.width_mm < MIN_STRIP_WIDTH:
    error("Strip width below threshold.")

4.2 Column Width Validation

Checks total width:

total_width_mm = Σ strip.width_mm
if total_width_mm < MIN_COLUMN_WIDTH:
    warn("Column unusually narrow.")

4.3 Column Consistency Validation

No negative widths

No missing color/material IDs

Strips must be ordered (UI enforces)

No duplicate strip IDs

5. Ring Geometry Validation

Before tile segmentation, the system validates geometry at the ring level.

5.1 Width vs Column Constraint
if ring.width_mm < column.total_width_mm:
    error("Ring width < Column width.")

5.2 Radius Constraint
if ring.radius_mm < MIN_RADIUS_MM:
    error("Ring radius below structural threshold.")

5.3 Tile Length Constraint
if ring.tile_length_mm < MIN_TILE_LENGTH_MM:
    error("Tile length too small for safe slicing.")

5.4 Twist Constraint

Large twist angles trigger warnings:

if abs(ring.twist_angle) > 45:
    warn("High twist angle may cause visual distortion.")

5.5 Herringbone Constraints
if herringbone_angle > 45:
    warn("Extreme herringbone angle.")

6. Segmentation Validation

Ensures tile segmentation is mathematically correct.

6.1 Tile Count Validation
if N < 2:
    error("Tile count must be ≥ 2.")
if N > 300:
    warn("Very high tile count may reduce performance.")

6.2 Angular Coverage Validation

Ensures tiles correctly span 360°:

sum(θ_end - θ_start) ≈ 360°


Tolerance: ±0.001°.

6.3 Consistency Check

Tiles must be monotonically increasing:

θ_end[i] ≤ θ_start[i+1]

7. Slice Generation Validation

Ensures slices map correctly to column structure.

7.1 Sequential Index Validation
slice.index == tile_index

7.2 Angle Validation

slice_angle must be within ±180°

No NaN values

No angle inversions

7.3 Material Map Validation

Ensure slices inherit column materials:

len(material_map) == len(column.strips)

7.4 Strip-Family Map Validation

Family IDs must match known strip families.

8. Kerf Compensation Validation

Ensures blade thickness adjustments do not break geometry.

8.1 Drift Validation

Cumulative drift:

total_drift = Σ angle_loss_per_slice
if total_drift > MAX_ALLOWED_DRIFT:
    error("Kerf drift exceeds allowed threshold.")

8.2 Kerf Range Validation
if kerf_mm <= 0:
    error("Kerf must be > 0.")
if kerf_mm > MAX_KERF_MM (2.0):
    warn("Unusually high kerf value.")

9. Manufacturing Planner Validation
9.1 Material Requirement Validation
required_length_mm > 0

9.2 Scrap Validation
scrap_mm = required_length_mm * scrap_rate
if scrap_mm < 0:
    error("Scrap cannot be negative.")

9.3 Volume Validation

Ensure no impossible volume:

volume_mm3 > 0

9.4 Risk Indicators

Planner must emit warnings for:

Excessive scrap

Narrow strips

Very short tiles

High material usage variance

Unsupported material-family mixes

10. JobLog Validation

Ensures audit trail integrity.

10.1 Planning Log Validation

Must contain all rings

Must contain segmentation references

Must contain no geometry errors

10.2 Execution Log Validation

Status fields must be valid

Deviations must be strings

Material usage numbers must be non-negative

10.3 Revision History Validation

Previous & new values must exist

Timestamp required

11. Export Validation

Validation before file writing:

11.1 JSON Validation

Circular references prohibited

Keys must meet schema

Version field must exist

11.2 PDF Validation

No empty pages

All required operator steps included

11.3 Saw Batch Validation

Must include all slices

Must be sequential

Must contain kerf-adjusted angles

12. Validation API Summary
validate_input()

Validates raw UI inputs.

validate_column()

Validates strip widths and metadata.

validate_ring_geometry()

Validates ring dimensions.

validate_segmentation()

Validates tile boundaries.

validate_slices()

Validates slice geometry.

validate_kerf()

Validates kerf adjustments.

validate_planner()

Validates material usage and scrap.

validate_joblog()

Validates planning/execution logs.

validate_export()

Validates batch files and reports.

All return:

ValidationReport

13. Error Conditions Blocking Pipeline

The following always halt processing:

strip width < 0.4 mm

tile_length_mm < 0.4 mm

ring.width_mm < column.total_width_mm

radius too small

kerf_mm <= 0

failed segmentation

invalid slice geometry

corrupted JobLog entries

export write failures

14. Warning Conditions (Allow Continuation)

twist_angle > 45°

tile_count > 200

herringbone_angle > 30°

scrap_rate > 10%

unusually thin strips

extreme tile geometry

Warnings must be visible in the UI and JobLog.

15. Future Validation Enhancements

Schema-based JSON validation

AI-assisted anomaly detection

Wood grain alignment validation

End-grain tensile stress predictions

Adaptive kerf modeling by blade type

Multi-blade angle consistency validation

16. File Location

This document belongs in:

/docs/RMOS_STUDIO_VALIDATION.md

End of Document

RMOS Studio — Validation Engine & Constraint Enforcement (Engineering Version)