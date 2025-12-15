docs/Instrument_Geometry_Migration_Plan.md

I’ve baked your caveat in: you’ll be doing the repo mining, and we’ll treat the “knowledge base” as a first-class citizen (those magical saw blade geometry papers absolutely belong in the spine).

# Instrument Geometry Migration Plan  
**Scope:** Fret/scale/bridge/radius math for all instruments (flat-top, archtop, electric, etc.)  
**Owner:** Ross / ToolBox Core  
**Status:** Draft v1.0  

---

## 1. Purpose

This document defines how to migrate all **instrument geometry math** (fret positions, scale length, bridge location, radii, related calculators) into a **single, well-defined subsystem** inside the Luthier's ToolBox architecture.

Goals:

1. **Centralize** all instrument geometry formulas that are currently scattered across:
   - `neck_router.py`
   - Archtop modules
   - legacy `server/pipelines/` code
   - ad-hoc calculators and snippets
2. Define a dedicated `instrument_geometry` package with **pure math APIs** that can be used by:
   - RMOS 2.0
   - Art Studio
   - CAM / Toolpath engine
3. Create a **technical knowledge base** where underlying theory, references, and vendor/academic notes are stored and linked to the code.
   - Example: the saw-blade geometry article you found that explains how blade physics is derived from geometry.

---

## 2. Target Architecture (End State)

### 2.1 New Package Layout

Create a new domain package:

```text
services/api/app/instrument_geometry/
  __init__.py

  scale_length.py         # fret positions, intonation offsets
  fretboard_geometry.py   # outline, taper, compound radius helpers
  bridge_geometry.py      # bridge location, height, compensation, radius
  radius_profiles.py      # radius curves and transitions
  profiles.py             # InstrumentSpec, FretboardSpec, BridgeSpec dataclasses


Design principles:

Pure functions: these modules should not know about HTTP, FastAPI, or persistence.

No side effects: all functions take clear inputs and return simple values or dataclasses.

Unit-testable: each function gets tests with known scales and geometries.

2.2 Example APIs

These are not final signatures, but they represent the shape we’re aiming for:

# scale_length.py
def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> list[float]:
    ...

def compute_compensated_scale_length_mm(scale_length_mm: float, saddle_comp_mm: float) -> float:
    ...


# fretboard_geometry.py
def compute_fretboard_outline(
    nut_width_mm: float,
    heel_width_mm: float,
    scale_length_mm: float,
    fret_count: int,
) -> list[tuple[float, float]]:
    """
    Returns 2D outline of fretboard in mm (local coordinate system).
    """


# radius_profiles.py
def compute_compound_radius_for_fret(
    fret_index: int,
    total_frets: int,
    start_radius_mm: float,
    end_radius_mm: float,
) -> float:
    ...


# bridge_geometry.py
def compute_bridge_location_mm(scale_length_mm: float) -> float:
    """
    Returns distance from nut to bridge reference line (e.g., saddle compensation).
    """

def compute_bridge_height_profile(
    top_arch_curve: list[tuple[float, float]],
    string_heights_mm: dict[str, float],
    action_spec_mm: dict[str, float],
) -> list[tuple[float, float]]:
    """
    Used by Archtop & flat-top bridges.
    """

2.3 Integration Points

RMOS 2.0

When RMOS evaluates a neck/bridge design, it calls instrument_geometry.* to derive fret positions, bridge placement, and radius info before passing shapes into the toolpath engine.

Art Studio

When a user sets scale length, radius, number of frets, etc., Art Studio calls instrument_geometry.* APIs to generate:

neck outlines

fret slot guides

bridge reference geometry

Then passes resulting geometry to toolpath/DXF modules.

CAM / Toolpath engine

Receives MLPath or coordinate lists from instrument_geometry and converts to toolpaths; does not re-implement any fret/bridge math.

3. Knowledge Base: Where the “Magic” Lives

The theory behind these calculators (and things like saw blade physics) must be captured in a formal knowledge base, not just in your head or random notes.

3.1 Directory Layout

Create:

docs/KnowledgeBase/
  README.md

  Instrument_Geometry/
    Fret_Scale_Theory.md
    Bridge_Compensation_Notes.md
    Radius_Theory_Compound.md

  Saw_Physics/
    Saw_Blade_Geometry_Reference.md
    Vendor_Blade_Physics_Notes.md

  Materials/
    Wood_Properties_Tables.md

3.2 Content Guidelines

Each knowledge base document should:

Summarize the core formulas and their meaning.

e.g., fret positions using 12th root of 2:

fret_n = scale_length - scale_length / (2^(n/12))

Include references:

lutherie books

vendor tech notes

academic articles

Clearly state:

assumptions (e.g., equal temperament, reference temperature/humidity)

limitations (e.g., not modeling nut compensation, string stiffness)

3.3 Linking Code ↔ Knowledge

For each calculator module, add a header comment pointing to the knowledge base:

# scale_length.py
"""
Instrument Geometry: Scale Length & Fret Positions

See docs/KnowledgeBase/Instrument_Geometry/Fret_Scale_Theory.md
for derivations, references, and assumptions.
"""


And inside the knowledge base markdown, note the code location:

Implements:
- services/api/app/instrument_geometry/scale_length.py


This way, when you find a golden document (like the saw blade geometry article), you:

Drop it into docs/KnowledgeBase (as a PDF or linked reference).

Summarize key formulas and conclusions in a .md file.

Link the relevant calculator module to that .md.

4. Current State – What Needs to Be Migrated

You’ll perform the repo mining; this section describes what to look for and how to classify it.

4.1 Files to Identify

Search for:

Neck / fret / scale logic

neck_router.py (services/api/app/routers)

Any neck_calc.py, fret_calc.py, scale_length.* in:

server/pipelines/

Archtop/

tools, snippets, or similar folders

Bridge / radius / archtop

archtop/bridge_generator.py

archtop_contour_generator.py

Any code that mentions:

“radius”

“compound radius”

“bridge height”

“intonation” / “compensation”

Spreadsheets / JSON configs

scale length tables

fret position tables

radius presets (9.5", 12", compound formulas, etc.)

As you discover files, append an inventory to this document or create:

docs/Instrument_Geometry_Inventory.md


with entries like:

- services/api/app/routers/neck_router.py
  - Contains fret formula and neck outline logic, mixed with FastAPI.
- server/pipelines/neck/neck_calc.py
  - Legacy neck geometry; likely superseded but has reference math.
- Archtop/archtop/bridge_generator.py
  - Bridge height calculation for archtop.

4.2 Classification

For each discovered item, decide:

Math to keep:

formulas, numeric constants, algorithms.

Routing / I/O only:

these stay in routers, but math moves out.

Legacy / redundant:

keep only as documentation or delete after migration.

5. Phased Migration Strategy
Phase 1 — Discovery & Inventory (Your Repo Search Phase)

Owner: You (manual + Copilot-assisted search)

Tasks:

Search the repo for:

fret, scale_length, intonation, bridge, radius, compound radius.

Build docs/Instrument_Geometry_Inventory.md with:

file path

short description

whether it contains math worth preserving.

Identify any external references:

PDFs, scanned pages, web articles (e.g., saw blade geometry paper).

Add them as entries in docs/KnowledgeBase/README.md with links or filenames.

Exit criteria:

You have a clear list of all instrument-geometry-relevant files.

You know which ones are math heavy vs. glue/router.

Phase 2 — Define the Instrument Geometry API & Profiles

Tasks:

Create the package skeleton:

services/api/app/instrument_geometry/
  __init__.py
  scale_length.py
  fretboard_geometry.py
  bridge_geometry.py
  radius_profiles.py
  profiles.py


In profiles.py, define high-level dataclasses:

from dataclasses import dataclass
from typing import Optional

@dataclass
class InstrumentSpec:
    instrument_type: str          # "electric", "flat_top", "archtop", etc.
    scale_length_mm: float
    fret_count: int
    string_count: int
    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None  # for compound
    tuning: Optional[list[str]] = None

@dataclass
class FretboardSpec:
    nut_width_mm: float
    heel_width_mm: float
    scale_length_mm: float
    fret_count: int
    base_radius_mm: Optional[float] = None
    end_radius_mm: Optional[float] = None

@dataclass
class BridgeSpec:
    scale_length_mm: float
    intonation_offsets_mm: dict[str, float]  # per string
    base_height_mm: float
    radius_mm: Optional[float] = None


Define function stubs in each module with docstrings describing intent and linking to KnowledgeBase.

Exit criteria:

Package exists with clean, documented APIs.

No math yet, but signatures are stable enough for RMOS/Art Studio to depend on.

Phase 3 — Extract & Move Math Into instrument_geometry

Tasks:

For each item in Instrument_Geometry_Inventory.md:

Open the file.

Identify pure math (formulas, numeric constants, loops that compute positions).

Move those formulas into the appropriate module:

fret positions → scale_length.py

board outline, neck widths → fretboard_geometry.py

bridge location/height → bridge_geometry.py

radius transitions → radius_profiles.py

Replace in-place logic with calls into the new package.

Example (in neck_router.py):

from app.instrument_geometry.scale_length import compute_fret_positions_mm
from app.instrument_geometry.fretboard_geometry import compute_fretboard_outline


And use those functions instead of inline formulas.

Add doc references in KnowledgeBase:

Where you move a formula, update the corresponding .md file to match what the code does.

Exit criteria:

neck_router.py and relevant Archtop / pipeline modules no longer define their own instrument math.

All math lives in instrument_geometry.*.

Phase 4 — Add Tests & Validation

Tasks:

Create tests under:

services/api/app/tests/instrument_geometry/
  test_scale_length.py
  test_fretboard_geometry.py
  test_bridge_geometry.py
  test_radius_profiles.py


Add canonical test cases:

Known fret positions for common scales (e.g., 25.5", 24.75").

Simple rectangular fretboard outline with expected coordinates.

Archtop bridge height test derived from your existing formula or reference plot.

Compound radius: check radius progression across frets.

Add tolerance bounds instead of exact equality (floating point).

Exit criteria:

All instrument geometry tests pass.

CI includes these tests.

You trust that a given InstrumentSpec produces the same geometry every time.

Phase 5 — Integrate With RMOS 2.0 & Art Studio

Tasks:

In RMOS:

Extend RmosContext to include instrument parameters (scale length, fret count, radius, etc.) where appropriate.

Have RMOS call:

instrument_geometry.scale_length for fret positions.

instrument_geometry.bridge_geometry for bridge placement before toolpath planning.

In Art Studio:

When the user configures an instrument:

Pass parameters to instrument_geometry to generate:

geometry preview (fretboard outline, frets, bridge reference)

data for feasibility (string lengths, tension, etc. later if needed).

Document the flow in an updated Directional Workflow 2.0 diagram, showing:

Art Studio → Instrument Geometry → RMOS → Toolpath → CAM → Gcode


Exit criteria:

Instrument configuration in Art Studio flows through the new geometry API.

RMOS uses the same API to score and constrain designs.

6. Handling “Magic” Technical References (Saw Blade Example)

When you find high-value technical documents (e.g., the saw blade geometry article that explains how a manufacturer models blade physics):

Save the PDF (or scanned pages) under:

docs/KnowledgeBase/Saw_Physics/
  Vendor_Blade_Physics_Whitepaper.pdf


Create a summary markdown:

docs/KnowledgeBase/Saw_Physics/Saw_Blade_Geometry_Reference.md


With:

Summary of key formulas and concepts.

How they map to:

saw_lab calculators.

tool_library entries (kerf, tooth count, hook angle, etc.).

Notes on safety limits, empirical coefficients, anything that affects your risk model.

Add a brief reference comment in the relevant calculator module:

# saw_lab/calculators/heat_model.py
"""
Saw Lab Heat Model

Based on formulas and recommendations from:
- docs/KnowledgeBase/Saw_Physics/Saw_Blade_Geometry_Reference.md
"""


This ensures the “magic” isn’t implicit; it’s documented, discoverable, and cross-linked to the code that uses it.

7. Definition of Done

The Instrument Geometry migration is considered complete when:

✅ All fret/scale/bridge/radius math lives in services/api/app/instrument_geometry/.

✅ neck_router, Archtop modules, and any legacy pipelines call into this package instead of re-implementing formulas.

✅ docs/KnowledgeBase/Instrument_Geometry/* contains the theory, with references.

✅ At least one tested case exists for each:

scale length → fret positions

fretboard outline

bridge location / compensation

radius profile or compound radius progression

✅ RMOS 2.0 and Art Studio workflows use these APIs in their directional flows.

✅ You can extend to new instruments (e.g., multiscale, 7-string) by updating profiles and tests, not by hunting down math in random routers.

Notes for future you:

You do not have to finish all knowledge base docs before starting the migration, but whenever you touch a calculator, you should at least stub a matching .md file in docs/KnowledgeBase/.

Don’t worry if the first pass is rough; this plan is meant to be iterative. The key win is centralization and discoverability.


