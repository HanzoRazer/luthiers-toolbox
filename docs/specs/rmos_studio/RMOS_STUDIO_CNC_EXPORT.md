the complete /docs/RMOS_STUDIO_CNC_EXPORT.md file, written in a professional engineering tone and structured for direct placement into your repository.

RMOS_STUDIO_CNC_EXPORT.md
RMOS Studio – CNC Export Pipeline & Machine Integration Specification

Version 1.0 — Engineering Document

1. Purpose

This document defines the CNC export architecture for RMOS Studio. It outlines how digital pattern, slice, and ring geometry data is translated into CNC-ready output formats, including:

G-code export

Jig alignment metadata

Blade-angle maps

Tile length and slice-angle structures

Toolpath sequencing

CNC-safe constraints and validation steps

The CNC Export Module is an extension of the Saw Pipeline and Manufacturing Planner and completes the digital-to-physical workflow.

2. CNC Export Overview

The CNC Export Layer produces three categories of outputs:

Machine Instructions

G-code / router paths

Saw slice alignment guides

Feed-rate plans

Calibration & Setup Metadata

Jig coordinates

Blade angle targets

Kerf offsets

Stock alignment coordinates

Manufacturing Documentation

Operator CNC checklist

Toolpath diagrams

Angular maps

Material handling instructions

The export must be deterministic, safety-validated, and consistent with RMOS Studio’s geometry model.

3. CNC Export Pipeline

The CNC export process follows the sequence:

Ring Geometry → Slice Batch → Toolpath Mapping → CNC Constraints → Export File Generation


Each step is handled by a dedicated subsystem.

4. CNC Output Types
4.1 G-Code Export

Used for CNC routers, mills, or jig-positioning systems.

Supported Output

G0 / G1 Linear moves

G2 / G3 Arc moves (optional)

M-codes for start/stop

Blade positioning codes (custom)

G-Code File Structure
( RMOS CNC Export )
( Ring ID: 1 )
( Tile Count: 128 )
( Effective Tile Length: 2.35 mm )

G21          ; mm units
G90          ; absolute positioning

; jig alignment
G0 X0 Y0     ; set origin
G0 X{jig_x_offset} Y{jig_y_offset}

; iterative slices
; each slice contains a linear cut operation
G1 X{start_x} Y{start_y} F{feed_rate}
G1 X{end_x}   Y{end_y}   F{feed_rate}

M30          ; program end

4.2 Slice Angle & Jig Alignment Export

For saw-based operations requiring angular precision.

Contents
slice_angle_deg
kerf_adjusted_angle_deg
tile_index
slice_length_mm
jig_offset_x_mm
jig_offset_y_mm


Exported as:

slice_alignment_{ring_id}.json

4.3 CNC Position Map

Machine coordinate positions for:

Stock alignment

Cut origin

Blade entry point

Tile boundary transitions

Example:

{
  "ring_id": 2,
  "origin": { "x": 0, "y": 0 },
  "alignment": {
      "jig_x_mm": 15.0,
      "jig_y_mm": 25.0
  },
  "slice_positions": [
      { "tile_index": 0, "x": 20.1, "y": 5.0 },
      ...
  ]
}

4.4 Operator CNC Checklist (PDF)

Includes:

Machine setup steps

Jig alignment visuals

Reference tile/slice diagrams

Feed-rate tables

Safety procedures

Generated using RMOS PDF engine.

5. Toolpath Generation Logic

Toolpaths depend on slice geometry and manufacturing method.

5.1 Linear Slice Toolpaths

For straight saw-like operations:

compute start_x, start_y from tile_index
compute end_x, end_y from tile_index
G1 X(start_x) Y(start_y)
G1 X(end_x)   Y(end_y)

5.2 Angular Slice Toolpaths

Where angle ≠ 0:

θ = slice_angle_deg
dx = cos(θ)
dy = sin(θ)


Toolpath must compensate for:

Strip width

Ring radius

Tile length

5.3 Kerf Compensation Toolpaths

Implement offset:

offset_x = (kerf_mm / 2) * sin(θ)
offset_y = (kerf_mm / 2) * cos(θ)


Applied before machine move is emitted.

5.4 Multi-Pass Cutting

If material height > blade capacity:

for pass in passes_required:
    shift Z-depth
    re-run toolpath

6. CNC Constraints & Safety Rules

Before generating CNC output, RMOS must validate:

6.1 Jig & Stock Constraints

Stock must be large enough for ring dimensions

Offsets must keep cuts within machine envelope

Zero-point must not fall outside workspace

6.2 Machine Envelope Validation
if max(toolpath_coordinate) > machine_limit:
    error("Toolpath exceeds machine limits.")

6.3 Feed Rate Safety

Bounded by:

Material type

Blade/bit configuration

Machine capability

Safety table (example):

Material	Typical Feed (mm/min)	Max Feed
Hardwood	300–600	900
Softwood	500–1000	1500
Composite	200–400	600
6.4 Angular Safety

Angles > 60° are warned:

warn("Steep slice angle; ensure blade twist support.")

6.5 Kerf Drift Safety

If cumulative kerf drift exceeds threshold:

error("Kerf drift exceeds safe alignment threshold.")

7. CNC Export API
7.1 generate_cnc_toolpaths()
generate_cnc_toolpaths(batch: SliceBatch, jig_params: dict) -> ToolpathSet

7.2 export_gcode()
export_gcode(toolpaths: ToolpathSet, path: str) -> None

7.3 export_alignment_metadata()
export_alignment_metadata(batch: SliceBatch, jig_params: dict, path: str) -> None

7.4 export_cnc_package()
export_cnc_package(project: Project, ring_id: int, dest: str) -> str


Produces:

gcode
alignment JSON
operator CNC checklist
slice batch
material usage summary

8. CNC Export Directory Structure
exports/
   cnc/
      ring_{ring_id}/
         slices_batch.json
         toolpaths.gcode
         alignment.json
         operator_checklist.pdf

9. CNC Jig Integration

RMOS CNC export includes support for jig-based systems:

XY-plane alignment

Rotational alignment

Tile-index targeting

Blade angle alignment patterns

Jig origin must match the G-code origin reference.

10. CNC Export Testing Requirements

All CNC exports must pass:

Geometry validation

Machine envelope constraints

Kerf drift validation

G-code syntax checks

Toolpath ordering checks

Preview rendering test (optional)

Automated snapshot tests are recommended.

11. Future CNC Export Features

Full 3D carving support

Toolpath optimization (Trochoidal, adaptive clearing)

Auto-nesting multi-ring layouts for sheet stock

Real-time CNC telemetry integration

RMOS → Fusion CAM adapter

Pre-flight collision simulation

Multi-blade/dual-axis saw export

12. File Location

This document belongs in:

/docs/RMOS_STUDIO_CNC_EXPORT.md

End of Document

RMOS Studio — CNC Export Pipeline & Machine Integration Specification (Engineering Version)