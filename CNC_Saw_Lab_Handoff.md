docs/CNC_Saw_Lab/CNC_Saw_Lab_Handoff.md
CNC Saw Lab — Engineering Handoff Document
Subsystem of the Luthier’s ToolBox Manufacturing Platform
Author: Ross / CNC Saw Lab Sandbox
Purpose: Enable expansion, maintenance, and future development
0. Executive Summary

The CNC Saw Lab subsystem is a dedicated, production-grade CAM module inside the ToolBox ecosystem responsible for:

Ultra-thin precision slicing (1.0 mm kerf range)

Rosette sausage cutting

Veneer slicing

Mosaic strip preparation

Batch slicing workflows

Blade + preset registry

Risk classification and feasibility

Operator safety gatekeeping

Integration with CAM_N16 toolpath pipelines

It is designed as a fully modular CAM extension, capable of interfacing with:

RMOS 2.0 (manufacturing oracle)

Art Studio (frontend)

ToolBox job logging

External vendors (via RFQ spec)

This document details what exists, how it works, and what the next engineer should extend.

1. System Components Completed So Far

The following pieces are fully implemented and ready for use or extension.

1.1 Saw Blade Registry (Complete)
Models (SQLAlchemy)

SawBlade

SawPreset

Includes full metadata for:

diameter, kerf, plate, bore

tooth geometry, hook angle

max RPM

recommended rim-speed band

material classification

lifecycle flag (active/inactive)

one-to-many blade → presets

Schemas (Pydantic)

Create, Update, Read schemas for both blades and presets

Input validation (kerf ≥ plate, enum validation, risk-band rules)

API Router (FastAPI)

Endpoints include:

Category	Endpoints
Blades	List / Create / Get / Patch / Deactivate
Presets	List per blade / Create / Update / Deactivate
Risk Check	/blades/{id}/risk-check
1.2 Risk-Check Stub (Functional Prototype)

The router includes a operational risk evaluation:

RED if RPM > max allowable

YELLOW if DOC > 1.0 mm

GREEN otherwise

Purpose:
This stub is the placeholder for the full risk engine (see Section 4).
It currently supports UI testing and operator workflow validation.

1.3 CNC Saw Lab RFQ Document (Vendor Ready)

A full RFQ document exists specifying:

Ultra-thin 125–140 mm blade

1.0 mm kerf, 0.80–0.85 mm plate

72–96T Hi-ATB geometry

CNC router spindle requirements

Blade tensioning & arbor specs

Vendor deliverables list

Pandoc-ready Markdown → PDF generator

This enables sourcing custom precision blades for production runs.

1.4 Engineering Specification (System Overview)

Detailed mechanical + CAM specifications exist, including:

Gantry dynamics & resonance considerations

Arbor engineering requirements

Clamping flange geometry

Jig fixture designs

Slicing presets: RPM, feed, DOC

Sausage log workflows

Mosaic strip slicing angles

Vacuum/mechanical hybrid fixtures

Full Saw Lab operating envelope

These specs form the mechanical basis for toolpath and risk modeling.

1.5 Slice Operation Framework (Design Complete)

While not yet implemented in code, the following operation primitives are defined:

SawSliceOp

Performs one slice

Multi-pass stepping based on DOC

Uses offsets from geometry engine

Outputs G-code primitives

SawSliceBatchOp

Repeats slicing operations

Applies positional offsets

Aggregates risk + statistics

Produces full batch G-code

These form the core CAM operation units for Saw Lab.

1.6 JobLog Integration (Specification Ready)

The job logging system is designed to capture:

tool id

preset id

RPM / Feed / DOC

vibration warnings

slice yield

per-pass data

operator notes

success/failure state

The schema is defined and ready for implementation.

2. Architectural Position in the ToolBox Ecosystem

CNC Saw Lab sits inside the ToolBox CAM layer.

Upstream Dependencies

RMOS 2.0 (feasibility + physics modeling)

Materials/Tools registry

Machine profiles

Downstream Outputs

CAM_N16 toolpaths

G-code generation

JobLog telemetry packets

Parallel Systems

Art Studio (design UI is NOT part of Saw Lab)

Directional Workflow Controller (Saw Lab plugs into Mode B & C)

3. What Can Be Immediately Extended (Roadmap)

Use the next sections as a development plan for extension.

4. Next Engineering Targets

Below is what remains to be built, organized in recommended development order.

4.1 Full Risk Engine (Priority #1)

Replace risk stub with a production-ready multi-factor engine.

Inputs

Blade parameters

Preset parameters

Machine profile

Workholding type

Material density

Cutting kinematics

Risk Modules

Rim Speed Assessment

Chipload Modeling

Thermal Load / Burn Risk

Deflection Estimation

Gantry Oscillation Probability

Arbor Torsional Stability

DOC and Multi-Pass Safety Envelope

Outputs

risk bucket

warnings

recommended corrective actions

This engine will drive production decisions and operator safety.

4.2 SawSliceOp Implementation (Priority #2)

Goal: Produce real, safe G-code.

Key components:

Multi-pass Z stepping

Linear path generation

Lead-in/out strategies

Machine-specific speed/RPM enforcement

Safety margin for blade diameter

Checks against risk engine

This will be the first deliverable that actually cuts wood.

4.3 SawSliceBatchOp Implementation (Priority #3)

Adds productivity:

Automatic offsets for subsequent slices

Batch statistics aggregation

Batch risk classification

Memory of slice-spacing tolerance

4.4 JobLog Subsystem (Priority #4)

Requires:

SQLAlchemy Job model

Job event stream

Runtime warnings

Operator UI hooks

Historical analysis (for adaptive presets)

4.5 Integration With RMOS Feasibility Engine (Priority #5)

Saw Lab will feed physics safety data into RMOS 2.0 calculators.

This requires:

standardized metric exchange format

risk → feasibility weighting

cut-time estimation via slicing ops

integration tests

4.6 Saw Lab UI API (Optional / Future)

Endpoints for frontend display:

blade list

preset preview

risk visualization

operation simulation

per-slice G-code preview

5. Requirements for Future Developers
5.1 Do Not Bypass the Risk Engine

All slicing must be validated before generating G-code.

5.2 Maintain Determinism

Same inputs must always yield identical paths.

5.3 Document All Presets

RPM/feed/DOC presets must include machine-specific or blade-specific justifications.

5.4 Preserve Modular Architecture

Saw Lab must remain an independent CAM module.

5.5 Follow Existing Naming Conventions

Stay consistent with:

SawBlade

SawPreset

SawSliceOp

SawSliceBatchOp

6. Directory Structure (Recommended)
services/api/app/saw_lab/
    models.py
    schemas.py
    router.py
    risk_engine.py
    slice_ops/
        slice_op.py
        batch_op.py
        gcode_builder.py
    job_log/
        models.py
        router.py
    presets/
        preset_loader.py
docs/CNC_Saw_Lab/
    CNC_Saw_Lab_Handoff.md
    CNC_Saw_Lab_Risk_Model.md
    CNC_Saw_Lab_RFQ.md
    CNC_Saw_Lab_Arbor_Spec.md

7. Final Notes for Extension Planning

The CNC Saw Lab is now positioned to grow into a full industrial slicing engine.
Your next steps should focus on:

Implementing risk → feasibility → CAM pipeline

Completing SliceOp and BatchOp

Integrating JobLog

Expanding presets

Adding operator-centered UX

Once the risk engine and slicing operations are implemented, your system becomes production-ready for real rosette and veneer manufacturing.

✔ This handoff document is now complete

Tell me if you want:

A matching developer onboarding guide for Saw Lab

A project roadmap timeline (2-week, 6-week, 3-month)

The full directory scaffolding code

Implementation of Risk Engine v1

Implementation of SawSliceOp v1 (G-code generator)