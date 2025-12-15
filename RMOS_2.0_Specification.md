Below is the Official RMOS 2.0 Specification — written as a real architectural document for your repo, suitable for long-term development, collaboration, and onboarding.
This is clean, modular, modern, and perfectly aligned with the AI + Shapely + Feasibility + Toolpath engine architecture we have built together.
You can drop this into:
docs/RMOS/RMOS_2_0_Spec.md
________________________________________
RMOS 2.0 Specification
Rosette Manufacturing Operating System — Architecture, Philosophy, and Subsystem Contracts
Author: Ross
Project: Luthier’s ToolBox
Version: RMOS 2.0
Release Intent: Foundation for AI-assisted rosette manufacturing, Art Studio integration, feasibility scoring, Shapely geometry kernel, and CAM_N16 toolpath workflows.
________________________________________
0. Executive Summary
RMOS 1.0 (original build) was a single monolithic module responsible for:
•	mosaic tile planning
•	strip usage + scrap estimation
•	manufacturing feasibility
•	toolpath offset preparation
•	glue-up and material planning
Over time, the system expanded well beyond the boundaries of that design.
The new ToolBox architectural layers—AI, Feasibility, Calculators, Geometry Engine, CAM—reflect a significant evolution of capability.
RMOS 2.0 preserves the name and identity, but restructures RMOS into a modular manufacturing framework that orchestrates, validates, and prepares designs for real CNC machining.
RMOS 2.0 = the Manufacturing Brain of the ToolBox.
________________________________________
1. RMOS 2.0 Philosophy
1.	Manufacturability first.
Every design must pass through physics-based constraints before entering CAM.
2.	Parameter-driven, not pixel-driven.
RMOS works on structural geometry, not artwork.
3.	Separation of concerns.
Manufacturing logic is separated into calculators, geometry engines, and toolpath planners.
4.	AI-safe boundaries.
AI can propose a design, but RMOS validates it using measurable constraints.
5.	Deterministic outputs.
Regardless of input source (human, AI, Art Studio), RMOS always produces predictable,
CNC-safe structures.
6.	RMOS is the API, not the implementation.
The RMOS name is the top-level contract, not a single file or “God object.”
________________________________________
2. RMOS 2.0 Subsystem Overview
RMOS is composed of six subsystems, each isolated but orchestrated via the RMOS layer.
RMOS 2.0
├── 1. Material & Tool Models
├── 2. Calculator Layer (Physics Engine)
├── 3. Feasibility Scoring Layer
├── 4. Geometry Engine (Shapely + M/L)
├── 5. Toolpath Engine (CAM_N16 lineage)
└── 6. BOM / Tiling / Glue-Up Planner
Each subsystem is independently testable, mockable, and replaceable.
________________________________________
3. RMOS 2.0 Subsystems (Detailed)
________________________________________
3.1 Material & Tool Models
Defines the physical constants required for all manufacturing calculations.
Includes:
•	Wood species data (density, hardness, thermal sensitivity)
•	Tool materials (carbide, HSS, diamond)
•	Tool geometries (flute count, diameter, stick-out)
•	Machine constraints (max RPM, feed rate limits)
Outputs used by:
•	chipload calculator
•	heat model
•	deflection model
•	rim-speed calculator
•	feasibility scoring
________________________________________
3.2 Calculator Layer (Physics Engine)
The “oracle” of manufacturing physics.
Modules:
•	chipload_resolver.py
•	heat_model.py
•	deflection_model.py
•	rim_speed_engine.py
•	tile_strip_bom.py
Responsibilities:
•	compute chipload
•	compute thermal load + burn risk
•	compute cutter deflection
•	compute rim speed safety
•	compute material usage + scrap factor
Input:
•	tool parameters
•	material properties
•	proposed feeds/speeds
•	geometry lengths
Output:
Structured results for scoring:
ChiploadResult
HeatResult
DeflectionResult
MaterialUsageResult
The Calculator Layer never talks to CAM or Geometry Engine.
________________________________________
3.3 Feasibility Scoring Layer
Role:
Aggregates calculator outputs into a design score:
overall_score: 0–100
risk_bucket: GREEN / YELLOW / RED
warnings: [ ... ]
material_efficiency: float
estimated_cut_time_min: float
Responsibilities:
•	combine physics results
•	apply manufacturing rules
•	determine if a design can proceed to CAM
Users:
•	Art Studio
•	AI Suggestion Engine
•	RMOS’s own tiling planner
•	Any constraint-first design workflow
RMOS Guarantee:
No unsafe or impossible design moves to toolpath generation.
________________________________________
3.4 Geometry Engine (Shapely + M/L)
Modules:
•	geometry_engine.py (selector)
•	shapely_geometry_engine.py (new)
•	ml_geometry_engine.py (legacy adapter)
Responsibilities:
•	offset geometry
•	boolean operations (union, subtract, intersect)
•	clean invalid geometry
•	translate MLPath ↔ Shapely
•	decompose polygon structures
•	simplify paths for machining
Design rules:
•	Geometry Engine outputs MLPath, never G-code
•	CAM consumes MLPath, not Shapely
•	Shapely is optional via feature flag
•	Legacy engine remains as safe fallback
Future expansion:
•	ezdxf adapters
•	arc-fitting
•	pocket-step planners
•	inlay cavity compensation
________________________________________
3.5 Toolpath Engine (CAM_N16 lineage)
Responsibilities:
•	generate machining passes
•	apply cutter-radius compensation
•	compute Z stepping (multi-pass)
•	determine climb vs conventional direction
•	compute lead-in / lead-out arcs
•	generate per-operation toolpaths
Does NOT do:
•	offsetting (handled by Geometry Engine)
•	feasibility scoring (handled by previous layers)
•	parameter generation (Art Studio or AI)
Toolpath engine consumes:
•	MLPaths (2D geometry)
•	cut parameters (depth, feed, RPM, pass count)
Outputs:
•	toolpath primitives
•	G-code-ready sequences
________________________________________
3.6 BOM / Tiling / Glue-Up Planner
Responsibilities:
•	compute strip usage
•	compute tile counts
•	plan glue-up order
•	detect insufficient stock
•	estimate scrap
This module replaces old RMOS’s “mosaic” logic with a more modular, physics-aware approach.
________________________________________
4. RMOS 2.0 API Boundary (VERY IMPORTANT)
RMOS defines a stable API that all upstream systems use.
from rmos import (
    compute_feasibility,
    compute_bom,
    generate_toolpaths,
    geometry_engine,
    material_models,
)
Inside services/api/app/rmos/__init__.py, RMOS re-exports the safe public API.
Internally, RMOS pulls from:
•	calculators
•	feasibility
•	geometry engines
•	toolpath engines
•	material models
•	tiling planners
But external modules NEVER import those internals directly.
This prevents architectural drift.
________________________________________
5. RMOS 2.0 Flow Diagram
              ┌───────────────────────┐
              │      Art Studio       │
              │ (Design Parameters)   │
              └───────────▲───────────┘
                          │
                          │ passes design→
                          │
              ┌────────────────────────┐
              │     RMOS 2.0 API       │
              │ compute_feasibility()  │
              └───────────┬────────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐
  │ Calculators   │ │ Feasibility  │ │ Geometry Engine│
  └──────────────┘ └──────────────┘ └────────────────┘
                                              │
                                              ▼
                                      ┌────────────┐
                                      │ Toolpaths  │
                                      │ (CAM_N16)  │
                                      └────────────┘
                                              │
                                              ▼
                                      ┌────────────┐
                                      │ G-Code     │
                                      └────────────┘
________________________________________
6. RMOS 2.0 Naming Standards
All RMOS modules sit “under” a branded directory:
services/api/app/rmos/
    __init__.py
    api_contracts.py
    factories.py
    version.py
Modules it re-exports stay in:
services/api/app/calculators/
services/api/app/feasibility/
services/api/app/toolpath/
services/api/app/geometry_engine/
services/api/app/materials/
RMOS is the umbrella, not the implementation.
________________________________________
7. RMOS 2.0 Versioning
RMOS follows semantic versioning aligned with ToolBox releases:
•	RMOS 2.0 — new architecture
•	RMOS 2.1 — add Shapely as optional backend
•	RMOS 2.2 — ezdxf adapters
•	RMOS 2.3 — pocketing strategies
•	RMOS 2.4 — Saw-Lab integration
•	RMOS 3.0 — adaptive machining, AI toolpath optimization
________________________________________
8. Migration Plan (What happens to RMOS 1.0 code?)
RMOS 1.0 was never a failure. It was the prototype for a manufacturing framework.
Migration steps:
1.	Move BOM/tiling logic → new BOM module
2.	Move old offset code → MLGeometryEngine wrapper
3.	Move feasibility scoring → new Feasibility Layer
4.	Archive RMOS_legacy for reference
5.	Rebind all “RMOS entrypoints” to RMOS 2.0 API
You lose nothing.
Everything is assimilated into a more powerful structure.
________________________________________
9. RMOS 2.0 Promise
RMOS will:
•	Validate every design
•	Provide deterministic manufacturing guidance
•	Secure boundaries between AI and CAM
•	Deliver safe, optimized toolpaths
•	Anchor the ToolBox manufacturing philosophy
RMOS is no longer a module.
It is the architecture of manufacturability.
________________________________________
10. End of Spec
If you wish, I can now generate:
✔ services/api/app/rmos/__init__.py


Drop-in doc snippets (polished for repo use)
2.1 Appendix A — RmosContext Schema (v1.0)
Add this to RMOS_2.0_Specification.md:
## Appendix A — RmosContext Schema (v1.0)

### Purpose

`RmosContext` defines the manufacturing environment in which a design is evaluated.  
It answers the question: *“With which material, tooling, and machine constraints is this design allowed to run?”*

This appendix is **normative** for RMOS 2.0.

### Fields

| Field               | Type    | Required | Default  | Description                                                                                           |
|---------------------|---------|----------|----------|-------------------------------------------------------------------------------------------------------|
| material_id         | string  | Yes      | –        | Material key used by calculators (wood species, density, heat characteristics, strip stock catalog). |
| tool_id             | string  | Yes      | –        | Primary tool identifier (used to look up diameter, flute count, stick-out, RPM/Feed envelope, etc.).|
| machine_profile_id  | string  | No       | `null`   | Machine profile (max feed, spindle RPM, acceleration, axis limits).                                  |
| project_id          | string  | No       | `null`   | Optional project/grouping identifier for logging and analytics.                                      |
| use_shapely_geometry| bool    | No       | `false` | If true, prefer the Shapely-based geometry engine over the legacy ML engine.                         |

> **Note:** Additional optional fields may be introduced in minor versions (v1.x).  
> New required fields are only allowed in a major version bump (v2.0, etc.).

### Versioning

A future field `context_version` MAY be added to allow coexistence of multiple context schemas.  
Until then, RMOS 2.0 assumes `RmosContext` conforms to this v1.0 table.
________________________________________
2.2 Geometry Backend Selection (Direction doc)
Add this section to Directional_Workflow_2_0.md after the modes:
## Geometry Backend Selection

RMOS supports multiple geometry engines under the hood (e.g., `MLGeometryEngine` and `ShapelyGeometryEngine`).  
Directional Workflow 2.0 treats geometry as an implementation detail, but selection rules are:

1. If `context.use_shapely_geometry == true`, RMOS MUST use the Shapely-based geometry engine for this request.
2. Otherwise, RMOS defers to its internal default as configured in `geometry_engine.py` (typically the legacy ML engine).
3. All three workflow modes (Design-First, Constraint-First, AI-Assisted) share this same selection logic.

This allows:

- Art Studio to explicitly request Shapely for high-fidelity previews.
- AI-assisted search to request Shapely when generating complex candidates.
- CAM and legacy pipelines to continue using the ML engine until Shapely is fully validated in production.
________________________________________
2.3 Appendix B — Constraint-First Stopping Rules
Append to the Directional Workflow doc:
## Appendix B — Constraint-First Stopping Rules

Constraint-First mode (Mode B) relies on a generator loop that proposes candidate designs and evaluates them via RMOS.  
To keep this loop deterministic, testable, and safe, a **StoppingRuleSpec** MUST be defined.

Stopping rules live in the **Directional Workflow Controller**, not inside RMOS itself.

### StoppingRuleSpec (conceptual)

| Field                 | Type    | Required | Description                                                   |
|-----------------------|---------|----------|---------------------------------------------------------------|
| max_candidates        | int     | Yes      | Maximum number of candidate designs to evaluate per request. |
| min_accept_score      | int     | Yes      | Minimum feasibility score (0–100) to consider a design usable.|
| preferred_risk_bucket | string  | Yes      | Preferred risk class, e.g. `GREEN` or `GREEN_OR_YELLOW`.     |
| time_budget_ms        | int     | No       | Optional time budget for the entire search loop.             |
| stop_on_first_green   | bool    | No       | If true, stop early when a GREEN candidate is found.         |

### Example (JSON)

```json
{
  "max_candidates": 20,
  "min_accept_score": 70,
  "preferred_risk_bucket": "GREEN",
  "stop_on_first_green": true,
  "time_budget_ms": 400
}
The controller is responsible for honoring these rules while calling:
result = compute_feasibility_for_design(candidate, ctx)
RMOS remains a pure evaluator and does not own search budget policy.

---

### 2.4 Toolpath Generation Is Workflow-Independent

Add this section near the end of Directional Workflow:

```markdown
## Toolpath Generation Is Workflow-Independent

Regardless of workflow mode (Design-First, Constraint-First, AI-Assisted), all paths into manufacturing converge on the same boundary:

1. Feasibility:
   ```python
   result = compute_feasibility_for_design(design, context)
2.	Toolpaths:
3.	toolpaths = generate_toolpaths_for_design(design, context)
Key invariants:
1.	Feasibility is mandatory. No toolpaths may be generated without a successful feasibility evaluation.
2.	Toolpath logic is downstream. Direction mode does not change the CAM engine; it only changes the input design.
3.	Geometry backend is resolved before toolpath planning. By the time toolpaths are generated, RMOS has already selected the appropriate geometry engine.
4.	AI and UI cannot bypass RMOS. AI suggestions and Art Studio design changes must pass through compute_feasibility_for_design() before toolpaths become eligible.
This guarantees:
•	Consistent CAM behavior across all workflows.
•	AI cannot accidentally create unsafe G-code.
•	Human designers always benefit from the same safety and efficiency checks.

---

## 3. Directional Workflow Controller Skeleton

Here’s a **code skeleton** for the controller you alluded to:

**File:**

`services/api/app/workflow/directional_workflow.py`  
(adjust path to match your repo layout)

```python
"""
Directional Workflow Controller (RMOS 2.0)

Implements the three directional lanes into RMOS:

- Mode A: Design-First (artist-driven)
- Mode B: Constraint-First (manufacturing-driven search)
- Mode C: AI-Assisted (generative feedback loop)

All modes converge on:
    compute_feasibility_for_design(design, context)
    generate_toolpaths_for_design(design, context)
"""

from typing import List, Optional, Literal, Iterable, Tuple
from pydantic import BaseModel

from app.rmos.api import (
    RosetteParamSpec,
    RmosContext,
    FeasibilityResult,
    compute_feasibility_for_design,
    generate_toolpaths_for_design,
)
from app.rmos.types import RiskBucket  # or wherever you define risk enums


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

WorkflowMode = Literal["design_first", "constraint_first", "ai_assisted"]


class StoppingRuleSpec(BaseModel):
    """Constraint-First loop policy (Appendix B)."""

    max_candidates: int = 20
    min_accept_score: int = 70
    preferred_risk_bucket: Literal["GREEN", "GREEN_OR_YELLOW"] = "GREEN"
    time_budget_ms: Optional[int] = None
    stop_on_first_green: bool = True


class CandidateWithResult(BaseModel):
    design: RosetteParamSpec
    result: FeasibilityResult


# ---------------------------------------------------------------------------
# Mode A — Design-First helpers
# ---------------------------------------------------------------------------

def evaluate_design_first(
    design: RosetteParamSpec,
    context: RmosContext,
) -> FeasibilityResult:
    """
    Mode A: Single-shot evaluation of an artist-driven design.

    This is essentially a thin wrapper around compute_feasibility_for_design,
    but it exists so the workflow layer can evolve without changing RMOS core.
    """
    return compute_feasibility_for_design(design, context)


def generate_toolpaths_if_feasible(
    design: RosetteParamSpec,
    context: RmosContext,
    min_score: int = 0,
    allowed_risks: Optional[List[RiskBucket]] = None,
):
    """
    Mode A: Convenience helper for "only generate toolpaths if it's safe enough".

    UI / API should call this instead of calling generate_toolpaths_for_design
    directly, so the feasibility gate is enforced in one place.
    """
    result = compute_feasibility_for_design(design, context)

    if result.score < min_score:
        raise ValueError(f"Design score {result.score} below minimum {min_score}")

    if allowed_risks is not None and result.risk_bucket not in allowed_risks:
        raise ValueError(f"Design risk {result.risk_bucket} not in allowed set")

    return generate_toolpaths_for_design(design, context), result


# ---------------------------------------------------------------------------
# Mode B — Constraint-First helpers
# ---------------------------------------------------------------------------

def iterate_constraint_candidates(
    context: RmosContext,
    candidates: Iterable[RosetteParamSpec],
    stopping: StoppingRuleSpec,
) -> Tuple[List[CandidateWithResult], List[CandidateWithResult]]:
    """
    Mode B: Given a context and a stream of candidate designs, run a controlled
    evaluation loop using StoppingRuleSpec.

    Returns:
        (accepted_candidates, rejected_candidates)
    """
    accepted: List[CandidateWithResult] = []
    rejected: List[CandidateWithResult] = []

    count = 0

    for design in candidates:
        if count >= stopping.max_candidates:
            break

        result = compute_feasibility_for_design(design, context)
        wrapped = CandidateWithResult(design=design, result=result)

        # Check risk and score thresholds
        risk_ok = False
        if stopping.preferred_risk_bucket == "GREEN":
            risk_ok = result.risk_bucket == RiskBucket.GREEN
        elif stopping.preferred_risk_bucket == "GREEN_OR_YELLOW":
            risk_ok = result.risk_bucket in (RiskBucket.GREEN, RiskBucket.YELLOW)

        score_ok = result.score >= stopping.min_accept_score

        if risk_ok and score_ok:
            accepted.append(wrapped)
            if stopping.stop_on_first_green and result.risk_bucket == RiskBucket.GREEN:
                break
        else:
            rejected.append(wrapped)

        count += 1

    return accepted, rejected


# ---------------------------------------------------------------------------
# Mode C — AI-Assisted helpers
# ---------------------------------------------------------------------------

class RankedCandidate(BaseModel):
    design: RosetteParamSpec
    result: FeasibilityResult


def rank_ai_candidates(
    designs: List[RosetteParamSpec],
    context: RmosContext,
) -> List[RankedCandidate]:
    """
    Mode C: Evaluate a batch of AI-proposed designs and return them
    ranked by feasibility score (descending), with RED designs removed.
    """
    ranked: List[RankedCandidate] = []

    for d in designs:
        result = compute_feasibility_for_design(d, context)
        if result.risk_bucket == RiskBucket.RED:
            # drop unsafe designs entirely
            continue
        ranked.append(RankedCandidate(design=d, result=result))

    # Sort by score (highest first), then by risk bucket (GREEN before YELLOW)
    risk_order = {RiskBucket.GREEN: 0, RiskBucket.YELLOW: 1, RiskBucket.RED: 2}

    ranked.sort(
        key=lambda rc: (
            risk_order.get(rc.result.risk_bucket, 9),
            -rc.result.score,
        )
    )

    return ranked
This gives you:
•	Mode A: simple wrappers enforcing “feasibility before toolpaths”.
•	Mode B: a generic constraint loop that takes an iterable of RosetteParamSpec candidates and a StoppingRuleSpec.
•	Mode C: AI batch ranking with RED designs filtered out and GREEN/YELLOW sorted by risk then score.

