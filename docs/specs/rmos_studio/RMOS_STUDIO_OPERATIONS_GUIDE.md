the complete /docs/RMOS_STUDIO_OPERATIONS_GUIDE.md file — written specifically for shop-floor workflow, production operators, luthiers, CNC technicians, and QA inspectors.
This is the final document in the RMOS Studio operational suite.

RMOS_STUDIO_OPERATIONS_GUIDE.md
RMOS Studio – Production Operations & Shop-Floor Workflow Guide

Version 1.0 — Manufacturing-Facing Document

1. Purpose

This guide documents the shop-floor use of RMOS Studio, from pattern preparation to cutting, assembly, and QA. It is intended for:

CNC operators

Saw operators

Luthiers

Workshop supervisors

QA inspectors

It focuses on practical execution, not design or engineering theory.
Every step is expressed as a repeatable manufacturing procedure.

2. Roles & Responsibilities
Role	Responsibilities
Designer	Creates patterns, columns, and rings in RMOS Studio
Planner	Generates manufacturing plan & verifies material supply
Operator	Executes saw/CNC operations using exported files
QA Inspector	Validates tile geometry and assembly accuracy
Supervisor	Signs off on final alignment and correctness
3. Required Shop Equipment
3.1 Minimum Equipment

Precision saw or CNC router

Adjustable jig with rotational indexing

Digital calipers (0.01 mm accuracy)

Dust extraction

Strip stock (veneers, woods, composites)

Adhesive materials

3.2 Recommended Additions

CAMotics CNC simulator

Digital protractor (±0.1° accuracy)

Micrometer for kerf validation

Shop computer or tablet running RMOS Studio

4. Workflow Overview

RMOS production follows a 5-stage pipeline:

1. Pattern & Ring Setup  
2. Slice Generation  
3. Manufacturing Plan  
4. Cutting (Saw or CNC)  
5. Assembly & QA  


Each stage has strict validation rules to ensure repeatable craftsmanship.

5. Stage 1 — Pattern & Ring Setup (Pre-Production)

Performed by Designer or Planner.

5.1 Verify Pattern Validity

Strip widths ≥ 0.5 mm

No undefined colors or materials

Column width ≤ Ring width

5.2 Verify Ring Parameters

Radius correct for design

Width supports selected column

Kerf value matches actual blade thickness

Tile length appropriate (1.5–3.0 mm recommended for classical rosettes)

5.3 Required Outputs

Pattern JSON

Ring configuration JSON

Multi-ring preview snapshot

6. Stage 2 — Slice Generation

Performed by Designer or Planner in RMOS Studio.

6.1 Generate Slices

Click:
Ring Panel → Generate Slices

Outputs include:

Raw slice angles

Twisted angles

Herringbone alternation

Kerf-adjusted angles

Slice index and geometry

6.2 Validation Requirements

No drift errors

No negative angles

No tile gaps or overlaps

Slice count matches ring segmentation

6.3 Required Outputs

SliceBatch JSON

Preview of slice-angle diagram

7. Stage 3 — Manufacturing Plan

Performed by Planner.

7.1 Generate the Plan

Click:
Manufacturing Planner → Generate Plan

Planner computes:

Material volume

Strip-family requirements

Estimated scrap

Production time estimation

Operator checklist

7.2 Supply Chain Check

Before cutting begins, verify:

Material	Required	Available
Wood strips	(auto-calculated)	Stock room
Accent strips	(auto-calculated)	Stock room
Adhesives	As required	Bench stock
CNC bits / saw blades	Verified	Verified
7.3 Required Outputs

material_usage.json

operator_checklist.pdf

production_plan.json

8. Stage 4 — Cutting Operations

Performed by Operator.

8.1 Select Cutting Mode

RMOS supports two real shop-floor modes:

A) Saw-Based Cutting Mode

Used when cutting with a precision saw and indexing jig.

Step-by-step Checklist

Load SliceBatch into the shop tablet/computer.

Set jig zero-point using the alignment metadata.

Confirm blade kerf matches value in RMOS (±0.02 mm).

For each slice:

Rotate jig to the specified angle

Make a clean cut

Label the tile (optional)

Place finished tiles into ring-indexed tray.

Key Warnings

Do NOT modify blade tilt mid-run.

Replace blade if kerf deviates by >0.05 mm.

Ensure tile order is preserved.

B) CNC-Based Cutting Mode

Used when exporting G-code.

Step-by-step Checklist

Open CNC Export Panel in RMOS.

Export CNC Package:

toolpaths.gcode

alignment.json

Operator checklist PDF

Load G-code into CNC simulator (CAMotics recommended).

Inspect for:

correct origin

proper slice indexing

toolpath staying within machine envelope

Mount stock using jig offsets from alignment.json.

Run CNC operation.

8.2 Common Operator Errors & Prevention
Error	Cause	Prevention
Tile mismatch	Wrong jig index	Double-check angle display
Drift accumulation	Kerf mismatch	Measure kerf before every run
CNC offset shift	Wrong origin	Use alignment.json values
Strip tearing	Feed too fast	Reduce feed rate 20–40%
Tile chipping	Dull blade	Replace blade / lower feed
9. Stage 5 — Assembly & QA

Performed by Operator and QA Inspector.

9.1 Sorting Tiles

Sort tiles by:

ring

color family

pattern orientation

Maintain correct ordering from SliceBatch.

9.2 Dry-Fit Assembly Check

Before gluing:

Align tiles around a mock circular frame

Verify continuity of patterns

Check for angular mismatch (>0.1°)

Look for color/strip misalignment

If errors appear, consult JobLog for root cause.

9.3 Gluing Procedure

Apply adhesive to inner edge.

Place tiles sequentially around ring.

Clamp using circular press or jig.

Cure according to material instructions.

9.4 Final Quality Checks

QA verifies:

Pattern alignment

No visible tile gaps

Consistent tile thickness

Tile faces undamaged

Roundness within acceptable tolerance

Recommended tolerance:

±0.2 mm radial deviation

10. JobLog & Documentation Requirements

Every run must be logged.

RMOS exports:

plan.json

execution.json

revision_history.json

notes.json

slice_batch.json

alignment.json

operator_checklist.pdf

Supervisor signs off on:

material usage

machine parameters

completed ring

alignment accuracy

11. Safety Procedures
11.1 General Safety

Always wear eye and ear protection.

Keep work area clean of dust buildup.

Do not operate saw/CNC while fatigued.

11.2 Saw Safety

Always verify blade alignment before each session.

Never adjust jig with saw running.

Keep hands at least 100 mm from blade path.

11.3 CNC Safety

Keep enclosure closed during operation.

Never reach into active machine.

Secure all loose clothing and tools.

12. Troubleshooting (Shop-Floor Quick Reference)
Issue	Solution
Tiles vary in length	Check kerf calibration
Tile seams visible	Reduce tile_count or increase tile_length
Ring feels “twisted”	Lower twist_angle
CNC cuts shifted	Re-zero machine origin
Strips misaligned	Verify column width vs ring width
Chipping during cut	Reduce feed rate / change blade
13. Best Practices for Professional Rosette Production

Keep tile lengths between 1.8–3.0 mm

Use high-contrast strip colors for clarity during assembly

Aim for tile_count between 60–120 for traditional designs

Re-measure kerf every 20–30 tiles

Always run a CNC simulation before cutting

Save a Run Package for every completed ring

Train new operators using the built-in Tutorials Module

14. File Location

This document belongs in:

/docs/RMOS_STUDIO_OPERATIONS_GUIDE.md

End of Document

RMOS Studio — Shop-Floor Workflow & Operations Guide (Production Edition)