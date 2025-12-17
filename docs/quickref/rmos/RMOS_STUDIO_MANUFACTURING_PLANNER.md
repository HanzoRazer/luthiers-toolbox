the complete /docs/RMOS_STUDIO_MANUFACTURING_PLANNER.md file, written in a professional engineering tone and fully aligned with the RMOS Studio architecture.

RMOS_STUDIO_MANUFACTURING_PLANNER.md
RMOS Studio – Manufacturing Planner Specification

Version 1.0 — Engineering Document

1. Purpose

The Manufacturing Planner converts RMOS Studio design data into material requirements, machining instructions, yield analyses, and production-ready preparation steps. It serves as the operational bridge between the digital rosette design and the physical fabrication process.

This planner is responsible for:

Strip-family material calculations

Volume and mass estimation

Tile count reporting

Scrap and risk modeling

Manufacturing checklists & validation

Production readiness signaling

Integration with RMOS JobLog and Saw Pipeline

It ensures that the operator enters the cutting phase with complete, accurate, and validated material requirements.

2. Planner Overview

The Manufacturing Planner operates after tile segmentation and saw batch generation are complete. It aggregates:

Pattern → Column Data

Ring Configuration

Strip-Family Assignments

Tile Segmentation Data

Slice Geometry from Saw Pipeline

Operator-Defined Constraints

The output consists of:

Material Usage Tables

Scrap Estimation Reports

Tile Distribution Tables

Strip-Family Requirements

Production Checklists

Ring-by-Ring Summaries

JSON & PDF Exports

3. Input Data Requirements

The Manufacturing Planner requires the following validated inputs:

3.1 Column Structure

Strip widths (mm)

Material/Color IDs

Strip-family assignment

Normalized total column width

3.2 Ring Configuration

For each ring:

Ring radius (mm)

Ring width (mm)

Tile length (effective)

Tile count

Twist/angle modifiers

Assigned pattern

3.3 Saw Pipeline Data

Slice angles

Tile boundaries

Per-slice material/color mapping

Kerf compensation

3.4 Operator Parameters

Safety factor

Scrap margin (3–7% default)

Preferred material dimensional stock

Manufacturing tolerances

4. Material Requirements Calculation

Material usage depends on:

Total number of tiles

Length of strips required to form the initial column

Conversion of tiles to strip families

Scrap rate

Yield efficiency

4.1 Strip-Family Length Calculation

Each strip family corresponds to a specific material grouping.

For each strip:

strip_length_required = (sum of all ring circumferences) + (scrap margin)


Total strip-family requirement:

family_length = Σ(strip_length_required for all strips in that family)

4.2 Volume Estimation

Assuming strips are rectangular:

volume_mm3 = width_mm × height_mm × required_length_mm
volume_cm3 = volume_mm3 / 1000


If strips are end-grain:

Adjust height_mm based on block thickness

Add end-grain safety factor (10–20%)

4.3 Tile Count Table

For each ring:

tile_count = N


The system must provide:

Tile count summary

Tile length distribution

Color/material tile percentage

4.4 Scrap Estimation

Default scrap rate: 5%

Formula:

scrap_mm = strip_length_required × scrap_rate


Scrap must not exceed:

10% for standard strips

15% for end-grain

20% for synthetic composites

5. Manufacturing Validation Steps

Before the operator proceeds to cutting, all validations must pass.

5.1 Column-to-Ring Compatibility

Checks:

Column width ≤ Ring width

No strip narrower than minimum threshold

No zero-width or negative-width values

5.2 Slicing Feasibility

Sufficient material height

Strip-families consistent through slices

No collapsed angles or invalid twist values

5.3 Material Availability

If available stock < required stock:

Error state

Operator must revise strip lengths

Optionally adjust tile length

5.4 Environmental Constraints

Optional checks include:

Humidity-level compensation

Wood movement expansion

Adhesive cure window

6. Manufacturing Output Reports

RMOS Studio generates structured output suitable for workshop use.

6.1 Material Usage Report

Fields include:

Strip-family

Required length (mm/cm/m)

Required volume (cm³)

Weight estimate (optional if density known)

Scrap allowance

Total material to prepare

Generated in:

/exports/manufacturing/material_usage.json

6.2 Tile Distribution Report

Per ring:

Tile count (N)

Effective tile length

Color distribution

Pattern variation warnings

Output file:

/exports/manufacturing/tile_distribution.json

6.3 Ring Production Summary

For every ring, report includes:

Ring width

Ring radius

Pattern assignment

Tile count

Slice angles

Risk indicators

Exported to:

/exports/manufacturing/ring_summary.json

6.4 Operator Checklist (PDF)

Includes:

Material prep steps

Required tool settings

Jig alignment notes

Blade selection

Twist and angle configuration

Safety checks

Sequence of cuts

RMOS generates:

/exports/manufacturing/operator_checklist.pdf

7. Manufacturing Planner UI Integration

The planner is represented in the bottom-right region of RMOS Studio, sharing space with JobLog.

UI displays:

Strip family breakdown table

Tile count summary

Scrap estimation

Checkboxes for operator readiness

Status indicators (green/yellow/red)

Red status prevents:

Saw Pipeline operation

Export of manufacturing packages

8. Planner API Structure

Used internally for computing material values.

8.1 strip_family_requirements()
Input: Column strips, ring circumferences
Output: Dict<family_id, required_length_mm>

8.2 generate_material_usage_report()
Input: strip_family_lengths, scrap_rate
Output: JSON structure

8.3 compute_volume()
volume_mm3 = width_mm * height_mm * length_mm

8.4 generate_operator_checklist()

Compiles all manufacturing data into PDF form.

9. Performance Requirements

Compute full manufacturing plan in < 40 ms

Support up to 10 rings per rosette

Support up to 40 strip families

All computations must be deterministic

10. Future Enhancements

Density-based weight estimation

Multilayer compression modeling

CNC jig calibration module

Real-time cost estimation system

AI-based material optimization

11. File Location

This document belongs in:

/docs/RMOS_STUDIO_MANUFACTURING_PLANNER.md

End of Document

RMOS Studio — Manufacturing Planner Specification (Engineering Version)