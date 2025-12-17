the complete, repository-ready /docs/N14_RMOS_CNC_PIPELINE.md — the full CNC toolchain, kerf physics, blade models, jig mathematics, feed-rate rules, and safety integration specification for RMOS Studio.

This is the authoritative engineering document for the CNC backend that N12/N13 depend upon.

N14_RMOS_CNC_PIPELINE.md
Patch Bundle N14 — RMOS CNC Pipeline, Blade Models, Kerf Physics & Jig Calibration

Version 1.0 — CNC Engineering Specification

1. Purpose

Patch N14 formalizes the entire CNC toolchain within the RMOS Studio environment.
Where N12 defined the slice geometry and N13 the UI integration, N14 specifies:

CNC toolpath generation

Blade geometry & kerf physics model

Jig coordinate framework

Machine envelope constraints

Feed-rate selection rules

Safety interlocks

Export data structures

Operator checklists

Alignment metadata

Simulation requirements

After N14, CNC exports are deterministic, repeatable, and production-ready.

2. CNC Architecture Overview

The RMOS CNC pipeline is composed of:

[N12 Slice Engine]
       ↓
[N14 CNC Toolpath Generator]
       ↓
[N14 Jig/Alignment Model]
       ↓
[N14 Machine Envelope Validator]
       ↓
[N14 G-Code Exporter]
       ↓
[N10 Safety & LiveMonitor Reporting]
       ↓
[Operator Execution + N12/N15 JobLog]


The CNC pipeline is tightly coupled with:

Kerf Engine

Slice Geometry Engine

Ring Assembly Engine

Safety Engine

JobLog

UI Export Panel

3. CNC Toolchain Modules

Directory under:

services/api/app/cam/rosette/cnc/


Modules:

cnc_toolpath.py

cnc_jig_geometry.py

cnc_blade_model.py

cnc_kerf_physics.py

cnc_feed_table.py

cnc_safety_validator.py

cnc_exporter.py

cnc_simulation.py

Each module is defined below.

4. Blade Models

The CNC pipeline supports two cutting modes:

Saw Blade Mode (linear cut, single-pass or multi-pass)

Router Bit Mode (CNC milling)

This gives full flexibility for CNC routers, hybrid saw-CNC jigs, or pure CNC operations.

4.1 Saw Blade Geometry Model

Variables:

kerf_mm       = width of cut
tooth_angle   = frontal rake angle
tooth_count    = # teeth
blade_radius   = blade size
blade_runout   = wobble tolerance


Kerf is derived as:

kerf_mm = (tooth_width + side_set)

Blade Safety Envelope:
blade_runout ≤ 0.05 mm
kerf_mm ≤ 2.0 mm


If violated → safety override required.

4.2 Router Bit Geometry Model

Variables:

bit_diameter_mm
flute_angle_deg
chipload_mm
max_rpm


Kerf = bit_diameter_mm (since flutes sweep full diameter).

Chipload:

chipload_mm = feed_rate / (rpm * flute_count)


This must match material hardness.

5. Kerf Physics Model

N12 computed the angular kerf loss.
N14 extends this into a full physics model.

5.1 Radial Loss Component
kerf_radial = kerf_mm / 2

5.2 Angular Kerf Component
kerf_angle_deg = (kerf_mm / R) * (180 / π)

5.3 Drift Accumulation
drift_total = tile_count * kerf_angle_deg

5.4 Safety Threshold
drift_total ≤ 0.5°


Above this → compensate with automatic angle normalization.

6. Jig & Alignment Model

Jig supports three transformations:

Translation (X, Y)

Rotation (θ)

Local origin offset

Jig metadata file (alignment.json) contains:

{
  "origin": { "x_mm": float, "y_mm": float },
  "ring": { "radius_mm": float },
  "offsets": {
    "jig_x_mm": float,
    "jig_y_mm": float
  },
  "slice_map": [
    { "index": i, "angle": deg, "x": mm, "y": mm }
  ],
  "safety": { ... }
}


The jig must be set to this origin before the operator runs slices.

Jig Safety Constraint:
|jig_offset| ≤ machine_envelope / 2

7. Machine Envelope Model

Every CNC machine has a bounding box:

X: [0 → Xmax]
Y: [0 → Ymax]
Z: [Zmin → Zmax]

RMOS Rule:

Toolpath coordinates must always remain inside envelope.

If violated:

CNC export blocked

UI displays a red alarm

Safety Engine logs “machine envelope violation”

8. Feed-Rate & Cutting Strategy Rules

Feed models pull from:

cnc_feed_table.py

Hardwood:
feed_rate = 300–900 mm/min
optimal = 500 mm/min

Softwood:
feed_rate = 500–1500 mm/min
optimal = 800 mm/min

Composite / Stabilized:
feed_rate = 200–600 mm/min

Deep Pass (multi-pass Z-down):

For materials thicker than cutting height:

passes = ceil(material_height / max_cut_depth)


Automatic multi-pass Z sequencing:

Z = Zstart - i*cut_depth

9. RMOS CNC Toolpath Generator

Toolpaths are generated from N12 slice endpoints, including:

direction vectors

corrected angles

ring width

radial projections

Toolpath Template:
G21        ; mm units
G90        ; absolute positioning

; jig offset
G0 X{origin_x} Y{origin_y}

; slice toolpaths
( slice i )
G1 X{start_x} Y{start_y} F{feed}
G1 X{end_x}   Y{end_y}

Multi-pass Example:
G1 Z{-1.0}
G1 X...
G1 Z{-2.0}
G1 X...


All toolpaths must coordinate-match UI preview & backend geometry.

10. CNC Safety Validator

The safety validator checks:

Envelope violation

Feed-rate dangerous for material

Kerf too large

Twist angle > 45°

Herringbone > 45°

Tile too small (<0.8 mm)

Slice too steep (>75°)

Runout > tolerance

Multi-pass conflict (cut depth too large)

Decision Model:
SafetyDecision {
  decision: "allow" | "block" | "override-required"
  risk_level: "low" | "medium" | "high"
  requires_override: bool
  reasons: [...]
}


This feeds into N10’s safety engine + UI override prompts.

11. CNC Exporter

Exporter produces:

toolpaths.gcode

alignment.json

operator_checklist.pdf

cnc_preview.svg

Operations:

Preflight safety validation

Write G-code

Write alignment metadata

Package operator instructions

Emit LiveMonitor event

Log JobLog entry

12. CNC Simulation Requirements

Perform simulated checks before final export:

confirm G-code syntax

simulate spindle positioning

simulate multi-pass Z levels

verify envelope fit

calculate runtime

Sim engine returns:

{
  "passes": int,
  "estimated_runtime_sec": float,
  "max_feed_rate_used": float,
  "envelope_fit": true/false
}

13. Operator Checklist Specification

Checklist PDF includes:

Blade/bit type

Kerf

Feed rate

Jig offsets

Ring radius

Tile count

Slice angle table

Safety warnings

Steps for jig setup

Post-cut validation steps

This PDF is required for every CNC export.

14. CNC Data Structures (Final)
SliceBatch with CNC fields:
{
  "batch_id": "string",
  "ring_id": 1,
  "slices": [
    {
      "index": 0,
      "angle_raw": 91.3,
      "angle_final": 90.7,
      "start": { "x": 20.0, "y": 45.0 },
      "end":   { "x": 30.0, "y": 50.0 },
      "material_map": [...],
      "kerf_mm": 0.3,
      "twist_deg": 5,
      "herringbone_deg": 30
    }
  ]
}

CNC Export Bundle:
ring_003_export/
    toolpaths.gcode
    alignment.json
    operator_checklist.pdf
    slice_batch.json
    cnc_preview.svg

15. CNC JobLog Integration

JobLog entry fields:

job_type: "rosette_cnc_export"
parameters: {
  ring_id,
  tile_count,
  toolpaths,
  feed_rate,
  kerf_mm
}
results: {
  runtime_estimate,
  envelope_ok,
  safety_status
}


Supervisor must sign off after physical execution.

16. Full Pipeline Flow
Column → Ring → Segmentation → Slices
→ Kerf Physics → Jig Alignment
→ CNC Toolpaths → Safety Checks
→ G-Code → CNC Simulation
→ Export Package → LiveMonitor
→ Operator Execution
→ JobLog Record


Every stage is deterministic and reproducible.

17. Implementation Roadmap (N14 → N15)
Phase A — Blade & Kerf Physics

finalize kerf-angle conversion

integrate blade profile DSL

Phase B — Jig & Alignment

jig coordinate model

alignment.json emitter

Phase C — Toolpath Generation

linear slicing

optional multi-pass Z

Phase D — Safety Engine

add CNC validator

integrate override system

Phase E — Export Bundle

G-code writer

operator checklist

CNC preview SVG

18. Completion Criteria

N14 is complete when:

Full CNC path generation working

Kerf physics validated

Jig offset math correct

Machine envelope enforcement active

CNC preview panel functional

G-code exports usable in CAMotics

Safety gates mandatory for high-risk operations

JobLog fully records CNC operations

UI receives all metadata cleanly

19. File Location

Place at:

/docs/N14_RMOS_CNC_PIPELINE.md

End of Document

Patch Bundle N14 — RMOS Studio CNC Pipeline Specification

If desired, I can generate the final link in the chain:

N15_RMOS_PRODUCTION_PIPELINE.md

Complete end-to-end manufacturing workflow from design → planning → CNC → assembly → QA → archival.