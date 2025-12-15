docs/Calculators/Calculator_Spine_Overview.md

This file is formatted exactly as a master architecture document for your repo.
Drop it directly into:

docs/Calculators/Calculator_Spine_Overview.md

📘 Calculator Spine Overview
Luthier’s ToolBox — Unified Calculator Architecture

Version: 1.0
Audience: Backend developers, RMOS 2.0 contributors, Saw Lab maintainers, Art Studio integrators

1. 🎯 Purpose of the Calculator Spine

The Calculator Spine is the single source of truth for all technical, mathematical, physics-based, or domain-specific computations in the Luthier’s ToolBox ecosystem.

Before Wave 8–9, calculators were scattered across:

server/pipelines/

Legacy Art Studio folders

Saw Lab scratch space

Front-end TypeScript utilities

RMOS feasibility logic

Inline code inside routers

Untracked documents & sandbox sessions

This fragmentation caused:

Loss of critical algorithms

Inconsistency between components

Hard-to-reproduce results

Difficulty training GitHub Copilot or AI agents

Breakage when migrating to new architectures (RMOS 2.0, Art Studio 2.0)

The Calculator Spine solves this.

2. 🧠 What the Calculator Spine is

A backend-centered, highly structured directory + API that:

✔ Centralizes calculators from all subsystems
✔ Exposes clean façade functions (via calculator_service)
✔ Feeds RMOS feasibility models
✔ Powers Art Studio risk overlays (Wave 9)
✔ Feeds the Saw Lab physics engine
✔ Supplies instrument geometry to UI and toolpath generators
✔ Keeps frontend math simple, backend math canonical

Every important calculation must pass through this spine.

3. 🗂 Directory Structure (Authoritative)

This directory is located here:

services/api/app/calculators/


And contains the following structure:

calculators/
│
├── service.py                        # Central façade — called by all subsystems
│
├── physics/                          # Router-bit & general cutting physics
│   ├── chipload.py
│   ├── heat.py
│   ├── deflection.py
│   ├── rim_speed.py
│   └── engagement.py                 # Optional (radial/axial engagement factors)
│
├── instrument/
│   ├── scale_length.py
│   ├── fret_positions.py
│   ├── string_spacing.py
│   ├── fretboard_geometry.py
│   ├── bridge_geometry.py
│   ├── radius_profiles.py
│   └── bracing.py
│
├── saw/                               # Saw Lab integration layer
│   ├── bite_per_tooth_adapter.py
│   ├── heat_adapter.py
│   ├── deflection_adapter.py
│   ├── rim_speed_adapter.py
│   └── kickback_adapter.py
│
├── wiring/
│   ├── treble_bleed.py
│   ├── switch_validator.py
│   └── impedance_math.py
│
└── business/
    ├── roi.py
    ├── amortization.py
    └── machine_throughput.py

4. 🧩 Calculator Spine: Layer Overview

The Spine operates in four internal layers:

4.1 ⭐ Layer A — Calculator Façade (service.py)

All subsystems call this file instead of calling calculators directly.

It provides:

• evaluate_cut_operation()

Unified router-bit + saw-blade interface.
Used by RMOS feasibility and Art Studio Debug panels.

• evaluate_string_spacing()
• evaluate_scale_length()
• evaluate_fretboard_outline()

Instrument geometry entry points.

• evaluate_roi()
• compute_switch_validation()

Business and electronics calculators.

Every calculator call should pass through the façade.

4.2 ⭐ Layer B — Physics Calculators

These compute physical machining phenomena:

Chipload

Heat generation

Deflection

Rim speed

Tool engagement

Kickback risk (via saw adapters)

These feed:

RMOS feasibility scoring

Art Studio Wave 9 risk overlays

Saw Lab physics debug views

Toolpath planners

4.3 ⭐ Layer C — Instrument Geometry Calculators

These compute lutherie math essential to guitar design:

Scale length → fret positions (12th-root-of-2 or historical models)

String spacing (linear, compensated, multi-scale)

Bridge location (compensation, action height)

Radius profiles (compound or fixed radii)

Bracing mass & stiffness estimates

These feed:

Art Studio instrument CAD panels

RMOS toolpath generation

Manufacturing geometry (DXF export)

4.4 ⭐ Layer D — Domain-Specific Calculators
Saw Lab

Adapts Saw Lab 2.0 physics models into the Spine.

Wiring

Calculates:

Treble bleed resistor/capacitor values

Pot/tone network impedance

Valid switch configurations

Business / ROI

Provides:

CNC amortization

Shop throughput modeling

Material cost analysis

5. 🔌 How Subsystems Connect to the Spine

Here is a map of who calls the calculators, and how:

Subsystem	Calls Spine For	Functions Used
RMOS 2.0	Feasibility	evaluate_cut_operation, instrument methods
Art Studio 2.0	Geometry preview, risk overlay	evaluate_cut_operation, instrument geometry
Saw Lab 2.0	Physics adapters	calls physics calculators directly
Toolpath Engine	Engagement factors, deflection	chipload, deflection
DXF Export	Geometry precision	instrument geometry
Wiring Workbench	Circuit math	treble_bleed, switch_validator
ROI Dashboard	Finances	roi.evaluate_roi()
6. 🛠 APIs Exposed to the Front-End

The following FASTAPI routers mirror the calculator façade:

/api/calculators/evaluate-cut
/api/calculators/string-spacing
/api/calculators/fret-positions
/api/calculators/fretboard
/api/calculators/bridge
/api/calculators/radius-profile
/api/calculators/roi
/api/calculators/wiring/*


This ensures:

Art Studio stays thin

All math is backend source-of-truth

Copilot can reason about a consistent API

7. 🔒 Safety & Consistency Rules
Rule 1 — Calculators MUST NOT live in UI

Simple helpers (such as inch→mm) are OK, but all lutherie math must live in Python.

Rule 2 — Every subsystem MUST use service.py

No backdoor imports into physics calculators.

Rule 3 — All calculators MUST be unit-testable

Every calculator module must have a corresponding test file:

tests/calculators/test_scale_length.py
tests/calculators/test_chipload.py
tests/calculators/test_rim_speed.py
...

Rule 4 — All tool/material data comes from Tool Library

Never hardcode:

chipload ranges

max RPM

kerf

flute count

Rule 5 — Every calculator must document assumptions

Inside each calculator, include:

# MODEL NOTES:
# - Assumes perfectly sharp tool
# - Assumes dry cutting (Air)
# - Assumes 2-flute bit unless OVERRIDE

8. 🧬 RMOS Feasibility + Calculator Spine

RMOS feasibility works like this:

Design → geometry engine → (paths)
        → for each toolpath:
            → CutOperationSpec
            → evaluate_cut_operation()
            → collect:
                chipload
                heat
                deflection
                rim-speed (if saw)
                kickback (if saw)
        → overall score
        → per-path risk map (Wave 9)
        → Art Studio overlays


This is why the calculator spine exists —
without centralized, consistent physics/math, RMOS cannot meaningfully score a design.

9. 🔎 Migration Status (based on searches)

From your search bundles:

✔ Already migrated or scaffolded

Saw Lab calculators (Wave 7–8)

Feasibility façade

Tool Library

Instrument Geometry skeleton

ROI calculators (identified)

⚠ Requires migration into Calculator Spine

Rosette calculators

Bracing calculators

String spacing calculators

Existing front-end math in TS

Legacy Art Studio geometry helpers

Wiring & treble bleed

Blocked-off calculators in server/pipelines/

❌ Missing entirely in repo

Some router-bit geometry calculators

Some saw-blade technical models (but you have local copies)

Several missing instrument geometry scripts (confirmed)

10. 📜 Developer Workflow Using the Calculator Spine

When a developer needs a calculation:

1) They never import modules directly

Wrong:

from app.saw_lab.calculators.deflection_model import compute_deflection


Correct:

from app.calculators.service import evaluate_cut_operation

2) They create a CutOperationSpec or instrument-specific request

Then call the façade.

3) They get a structured result for RMOS, UI, or debugging.
4) They optionally inspect raw calculators for debugging only.
11. 🏁 Next Steps
Step 1 — Move remaining calculators into calculators/

Especially instrument geometry and wiring calculators.

Step 2 — Write unit tests for each module

Wave 8–9 prepared the internal API signatures.

Step 3 — Update RMOS feasibility to return path-level risk

This activates full Wave 9 overlays in Art Studio.

Step 4 — Remove all duplicate or legacy calculators

After migration is complete.

Step 5 — Merge Saw Lab 2.0 adapters fully

Ensure Saw Lab physics feeds through the façade.

12. ✔ Summary

The Calculator Spine ensures:

One location for all math and physics

One API surface for RMOS, Art Studio, and Saw Lab

Long-term maintainability

Consistent manufacturing outcomes

Prevents knowledge loss across patches and sandboxes

It is the central nervous system for all manufacturing logic in the Luthier’s ToolBox.