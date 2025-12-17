the complete, repo-ready /docs/N12_ROSETTE_ENGINE_PLAN.md — the full geometry + CNC implementation blueprint that will replace all N11 scaffolding logic with production-grade algorithms, data structures, and pipeline behavior.

This is the central engineering document for the real RMOS Studio engine.
It is structured for direct inclusion in your N-series system architecture.

N12_ROSETTE_ENGINE_PLAN.md
Patch Bundle N12 — RMOS Rosette Engine (Full Geometry + CNC Implementation)

Version 1.0 — Core Algorithm & Pipeline Specification

1. Purpose of Patch N12

This patch replaces the stub scaffolding of N11 with the complete, production-grade:

Tile Segmentation Engine

Slice Geometry Engine

Kerf Compensation Engine

Twist / Herringbone Transform Engine

Ring Assembly + Multi-Ring Alignment Logic

CNC Export Engine

Manufacturing Planner Engine

Final Rosette Preview Engine

N12 is the true RMOS Studio engine—the mathematical and computational core powering real rosette generation.

N11 established the integration layer;
N12 adds the real geometry, algorithms, and CNC interfaces.

2. Architectural Overview (N8–N12 Integration)

The N12 engine plugs into:

N8 – PatternStore, SQLite schema, pattern registry

N9 – Analytics & strip-family infrastructure

N10 – LiveMonitor, safety policy system

N11 – Rosette scaffolding (API, UI, stores, routes)

N12 replaces the N11 stub logic but preserves:

File names

Endpoints

Store interfaces

Component signatures

Data schemas

This guarantees zero-breaking-change integration.

3. N12 Modules & Responsibilities

New full modules under:

services/api/app/cam/rosette/
    tile_segmentation.py
    ring_geometry.py
    twist_engine.py
    herringbone_engine.py
    kerf_engine.py
    slice_generator.py
    cnc_exporter.py
    manufacturing_planner.py
    preview_engine.py


N11 used these as scaffolding;
N12 fills them with complete implementations.

4. Algorithms (Deep Specification)
4.1 Tile Segmentation Algorithm (SegEngine)
Inputs:
radius_mm
width_mm
tile_length_mm (user)
column_width_mm
twist_angle_deg
herringbone_angle_deg
kerf_mm

Computations:
Step 1 — Compute circumference:
C = 2πR

Step 2 — Compute nominal tile count:
tile_count_nominal = C / tile_length_mm

Step 3 — Snap to integer tile count:
tile_count = round(tile_count_nominal)

Step 4 — Compute effective tile length:
tile_effective_length = C / tile_count

Step 5 — Compute angular tile width:
θ_tile = 360 / tile_count

Output:

tile_count

tile_effective_length

array of tile boundaries [θ0, θ1, θ2 …]

This is the core deterministic segmentation logic.

4.2 Slice Geometry Algorithm (SliceEngine)
For each tile:
Compute raw slice angle:
raw_angle = 90° relative to tangent = tile_angle + 90°

Apply twist:
twisted_angle = raw_angle + twist_angle_deg

Apply herringbone:
if herringbone_mode:
    angle = twisted_angle * (-1)**tile_index
else:
    angle = twisted_angle

Compute direction vector:
dx = cos(angle)
dy = sin(angle)

Compute line endpoints using ring width:
inner = (R - width, θ_start)
outer = (R, θ_start)

project endpoints along dx, dy


Output slice:

endpoints

angle

tile index

material mappings

4.3 Kerf Compensation Algorithm (KerfEngine)
Compute angular kerf loss:
kerf_angle = (kerf_mm / R) in radians → convert to degrees


For each slice:

final_angle = slice_angle - kerf_angle


This ensures zero drift across the circumference.

4.4 Ring Assembly Logic (RingEngine)

Combines:

segmentation

slice generation

kerf compensation

herringbone

twist

strip-family mapping

tile → material mapping

Produces final SliceBatch.

5. Multi-Ring Assembly Algorithm

For each ring:

Compute segmentation

Generate slices

Kerf-correct slices

Compute preview geometry

Register tile materials (strip-family)

Append to assembly

Finally:

Verify all ring boundaries

Detect inter-ring alignment issues

Produce final multi-ring preview map

6. CNC Export Engine (Full Implementation)

The CNC Exporter replaces N11’s stub.

6.1 Toolpath Generation

Each slice becomes one CNC pass:

G1 X(start.x) Y(start.y) F(feed_rate)
G1 X(end.x)   Y(end.y)


Optional multi-pass Z levels if user enables “deep slices.”

6.2 Jig Alignment Metadata

Computes:

jig_x_mm

jig_y_mm

origin offsets

starting angle alignment

tile index → jig coordinate lookup table

Produced as:

alignment.json

6.3 CNC Safety Enforcement

CNC exporter must ensure:

toolpaths inside machine envelope

feed rate within material limits

kerf-corrected angles applied

sequential tile ordering preserved

fails on negative motion constraints

Outputs:

toolpaths.gcode

alignment.json

operator_checklist.pdf

7. Manufacturing Planner (Full Engine)

Planner computes:

7.1 Strip-family lengths & volume
strip_length = tile_effective_length * tile_count
material_volume = strip_width * strip_height * strip_length

7.2 Scrap Estimation
scrap_mm = strip_length * scrap_factor (default 5%)

7.3 Risk Indicators

High-risk factors flagged:

thin strips < 0.5 mm

tile_count > 200

kerf too large

extreme twist > 45°

extreme herringbone > 45°

7.4 Operator Checklist

Automatically created for each ring:

tool

blade

kerf

feed rate

angle table

tile count

material requirements

8. Final Preview Engine

Generates:

vectorized multi-ring preview

slice-angle overlay

herringbone/twist visualization

tile grid preview

color/material continuity map

Supports SVG/Canvas output.

9. API Upgrades (N11 → N12)

All /api/rmos/rosette/* endpoints now perform real calculations.

/segment-ring

Uses real SegEngine.

/generate-slices

Uses SliceEngine + KerfEngine.

/patterns

Now writes real rosette_geometry JSON.

/preview

(NEW) returns live preview rendering.

10. Data Model Upgrades

Update rosette_geometry:

{
  "rings": [
    {
      "ring_id": 1,
      "radius_mm": 45,
      "width_mm": 3,
      "tile_length_mm": 2.4,
      "tile_count": 128,
      "twist_angle_deg": 5,
      "herringbone_angle_deg": 30,
      "kerf_mm": 0.3,
      "segmentation": { ... },
      "slices": { ... }
    }
  ]
}


N11 stored only raw inputs.
N12 stores all computed fields.

11. LiveMonitor Integration (Real Events)

N12 emits events at key checkpoints:

rosette.segmentation.start

rosette.segmentation.complete

rosette.slicing.start

rosette.slicing.complete

rosette.cnc.export

rosette.planner.complete

Each event contains:

job_id

pattern_id

ring_id

tile_count

warnings

durations

12. Safety Engine Upgrades

Rosette CNC operations now require elevated safety checks:

detect excessive drift

detect invalid CNC origin

detect extreme slice angles

enforce override token for dangerous configurations

New safety modes:

"rosette_cnc"
"rosette_cutting"
"rosette_high_risk"

13. Analytics Extensions (N9 Integration)

N12 adds rosette-aware analytics:

tile distribution curves

strip-family consumption heatmaps

twist/herringbone clustering

kerf vs material deviation statistics

CNC drift analysis

14. Implementation Order (Critical Path)
Phase 1 — Core Math (Segmentation + Slice + Kerf)

segmentation engine

slice engine

kerf engine

ring assembly

Phase 2 — CNC Export

toolpaths

alignment metadata

CNC safety checks

Phase 3 — Manufacturing Planner

volume & material calculations

scrap estimation

operator checklist

Phase 4 — Preview Engine

SVG preview

multi-ring compilation

Phase 5 — API + UI Integration

replace N11 stubs with N12 engines

frontend previews

LiveMonitor + Safety

15. N12 Completion Criteria

N12 is considered complete when:

All calculations use real engines, not stubs

CNC export passes simulation

Manufacturing plan produces correct strip-family requirements

Multi-ring preview works for all rings

JobLog traces real computational steps

Safety engine enforces CNC constraints

No N11 stub call paths remain

16. Deliverables Summary

N12 delivers:

✔ Full Segmentation Engine
✔ Full Slice Generator
✔ Full Kerf Engine
✔ Twist & Herringbone Engines
✔ CNC Export Engine
✔ Manufacturing Planner
✔ Preview Engine
✔ Real API computations
✔ Real analytics integration
✔ Real LiveMonitor events
✔ Full safety enforcement

This is the complete RMOS geometry and CNC core.

17. File Location

Place this document at:

/docs/N12_ROSETTE_ENGINE_PLAN.md

End of Document

Patch Bundle N12 — Full Rosette Engine Implementation Blueprint

If you want, I can immediately generate:

N13_ROSETTE_UI_DEEP_INTEGRATION.md

(Full UI/UX rewrite for the completed engine — real preview panels, real editors, real CNC export UI.)

or

N14_RMOS_CNC_PIPELINE.md