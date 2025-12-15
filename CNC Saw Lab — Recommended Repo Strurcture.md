CNC Saw Lab — Recommended Repo Structure
services/
└── api/
    └── app/
        └── saw_lab/
            │
            ├── __init__.py
            ├── models.py               # SawBlade, SawPreset
            ├── schemas.py              # Pydantic input/output models
            ├── router.py               # CRUD endpoints + risk check
            ├── risk_engine.py          # Risk Engine v1 (stub -> full system later)
            │
            ├── slice_ops/
            │   ├── __init__.py
            │   ├── slice_op.py         # Single-slice operation logic
            │   ├── batch_op.py         # Multi-slice batching logic
            │   ├── gcode_builder.py    # Core G-code generator for slicing
            │
            ├── presets/
            │   ├── __init__.py
            │   ├── preset_loader.py    # Preset bundles (RPM/feed/DOC) per blade/material
            │
            ├── job_log/
            │   ├── __init__.py
            │   ├── models.py           # JobLog SQLAlchemy models
            │   ├── router.py           # Endpoints for history/telemetry
            │   ├── ingestor.py         # Parses runtime feedback into JobLog entries
            │
            └── utils/
                ├── __init__.py
                ├── calculations.py      # Helper math: rim speed, feeds, DOC sanity, etc.
                ├── validation.py        # Blade/preset validation helpers

📄 Documents Associated With Saw Lab (under /docs)
docs/
└── CNC_Saw_Lab/
     ├── CNC_Saw_Lab_Handoff.md         # The handoff document created earlier
     ├── CNC_Saw_Lab_RFQ.md             # Vendor-ready RFQ sheet
     ├── CNC_Saw_Lab_Risk_Model.md      # (Future) Formal risk modeling spec
     ├── CNC_Saw_Lab_Arbor_Spec.md      # Arbor geometry & tolerances
     ├── CNC_Saw_Lab_System_Overview.md # Hardware rules, presets, jigs, etc.
     └── img/
         ├── slicing_diagram.svg        # (Optional future diagrams)
         ├── arbor_diagram.svg
         ├── batch_workflow.svg

🧩 Explanation of Each Directory

Below is a clear description of the purpose and responsibilities of each folder:

1. models.py

Holds the SQLAlchemy models:

SawBlade

SawPreset

These represent the persistent catalog of tools and their presets.

2. schemas.py

Pydantic schemas for:

Creation

Update

Read

Enforce input validation and shape the API.

3. router.py

The main FastAPI entrypoint for:

Listing blades

Creating/updating blades

Listing presets

CRUD for presets

Risk check endpoint

The router anchors Saw Lab into your API.

4. risk_engine.py

Currently houses Risk Engine v1 (stub).

Later will grow into full:

rim speed modeling

thermal load estimation

deflection modeling

gantry oscillation prediction

arbor torsion modeling

multi-pass safety evaluation

This will become a critical safety subsystem.

5. slice_ops/

The slicing CAM engine.

slice_op.py

Handles one slice:

multi-pass logic

Z stepping

geometry decomposition

verifying cutting envelope

passing data to gcode builder

batch_op.py

Handles multiple slices:

offset increments

yield estimation

batch-level risk aggregation

G-code stitching

gcode_builder.py

Outputs safe CNC router G-code, including:

feed/RPM enforcement

safe retraction

lead-in/out moves

preamble/postamble

error handling

6. presets/

This is where all preset logic is loaded.

preset_loader.py

Provides:

default preset definitions

preset packs per blade

preset packs per material

ability to inject new preset bundles

This enables operators and automated workflows.

7. job_log/

For analytics and adaptive machining.

models.py

JobLog tables:

job id

blade id

preset id

slice parameters

heat/chatter warnings

operator notes

timestamped events

router.py

REST interface for:

retrieving past runs

slicing history

telemetry analytics

ingestor.py

Processes incoming session data:

from controller

from UI

from machine feedback

This will allow Saw Lab to become self-optimizing.

8. utils/

Holds helper logic:

rim speed calculations

material property lookups

feed/DOC limit verification

blade/preset consistency checks

🏛 How Saw Lab Fits Into the Bigger Repo

Saw Lab is a parallel CAM module, similar to:

CAM_N16 (Rosette milling)

CAM_G61 (potential future modules)

The repo expects Saw Lab to integrate only through:

Risk Engine

Toolpath output (G-code)

Blade/Preset registry

It does not integrate with RMOS until RMOS requests:

feasibility of slicing operations

toolpath outputs for slicing

This isolation keeps the architecture clean.

🎯 Final Summary of Repo Structure

If you want a single view, here it is:

saw_lab/
  models.py
  schemas.py
  router.py
  risk_engine.py
  slice_ops/
    slice_op.py
    batch_op.py
    gcode_builder.py
  presets/
    preset_loader.py
  job_log/
    models.py
    router.py
    ingestor.py
  utils/
    calculations.py
    validation.py


Plus the associated documentation under:

docs/CNC_Saw_Lab/