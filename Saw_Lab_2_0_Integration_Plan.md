the Saw Lab 2.0 Integration Plan — the full modernization roadmap that merges CNC Saw Lab into the unified RMOS 2.0 manufacturing architecture.

This is not just an upgrade; it is a total reintegration that turns Saw Lab from a “forgotten subsystem” into a first-class RMOS Toolpath Engine Mode with shared calculators, geometry backends, and feasibility scoring.

Drop this into:

docs/SawLab/Saw_Lab_2_0_Integration_Plan.md

🪚 Saw Lab 2.0 Integration Plan
Modernizing the CNC Saw Lab Under RMOS 2.0
0. Executive Summary

CNC Saw Lab was originally a standalone sandbox designed to model:

saw-blade geometry

kerf behaviors

blade deflection and heat

kerf-aware path planning

rip/cross/compound cut strategies

blade risk envelopes

saw-specific feed/speed limits

However, with the introduction of RMOS 2.0, the Saw Lab must now function as:

A dedicated “Saw Mode” inside the RMOS Toolpath Engine.

This plan describes exactly how to evolve Saw Lab’s architecture, code, calculators, and planners to become a fully integrated toolpath domain under RMOS.

1. Current State Assessment

Based on the uploaded files:

✔ Existing Strengths

Saw Lab already has:

1.1 Strong Physics Engine

risk_engine.py models rim speed, torque load, thermal risk.

kerf_planner.py does kerf-aware cut planning.

Blade geometry is explicit (diameter, thickness, hook angle, grind).

Material properties are modeled at the “species” level.

✔ Strong Documentation

CNC Saw Lab — Recommended Repo Structure

CNC Saw Lab Expanded Architecture

CNC Saw Lab Analysis

CNC Saw Lab Handoff

These documents show a clean and future-ready architecture.

⚠ Weaknesses

Saw Lab is not connected to RMOS 2.0.

Geometry kernel is one-off → not using RMOS geometry engines.

Feasibility logic is external to RMOS calculators.

Toolpath outputs are not using RMOS RmosToolpathPlan format.

No RMOS-level API exposure.

No directional workflow integration.

Context objects differ from RMOS context models.

AI cannot call Saw Lab logic through RMOS yet.

Saw Lab must be rewritten as a “mode” inside RMOS rather than an external sidecar.

2. Vision for Saw Lab 2.0

Saw Lab becomes:

A specialized toolpath and risk engine under RMOS, activated when
RmosContext.tool_id identifies a saw blade.

In other words:

RMOS Toolpath Planner
        ↓
IF tool_id in SAW_BLADES:
    use Saw Lab 2.0
ELSE:
    use Router CAM_N16 planner


Saw mode becomes as “first-class” as router mode.

3. New Saw Lab 2.0 Architecture
Saw Lab 2.0
├── blade_models/           (Blade geometry, tooth profiles)
├── material_models/        (Density, burn threshold, tearout rules)
├── saw_calculators/        (Heat, deflection, rim speed, kickback risk)
├── saw_geometry/           (Kerf-aware geometry ops via RMOS engine)
├── saw_path_planner/       (Rip/Cross pathing, strip slicing)
├── saw_toolpath_builder/   (Toolpath operations for RMOS)
└── saw_risk_evaluator/     (Risk envelope scoring)


Everything flows through RMOS.

4. Integration Point #1 — RMOS Toolpath Engine Switch

Add to:

rmos/toolpath/service.py

if ctx.tool_id.startswith("saw:"):
    return saw_toolpath_engine.plan_saw_toolpaths(design, ctx)
else:
    return router_toolpath_engine.plan_router_toolpaths(design, ctx)


Saw Lab becomes selectable by tool family.

5. Integration Point #2 — Saw-Specific Calculators into RMOS

Saw Lab currently has physics models in:

risk_engine.py

kerf_planner.py

RMOS calculators must integrate these.

Add Saw calculators:
calculators/saw_heat.py
calculators/saw_deflection.py
calculators/saw_rimspeed.py
calculators/saw_bite_load.py
calculators/saw_kickback_risk.py


Feasibility engine sees them as overrides when tool_id indicates a saw.

6. Integration Point #3 — Saw Geometry Engine via RMOS Geometry Selector

Saw Lab currently performs geometry in its own subsystem.

Replace all internal geometry ops with:

engine = get_geometry_engine(context)
engine.offset_path()
engine.subtract_paths()
engine.union_paths()


Saw Lab gains:

boolean stability

Shapely option

legacy ML mode for compatibility

This unifies geometry between router and saw workflows.

7. Integration Point #4 — Strip / Tile Planner → RMOS BOM Calculator

Saw Lab’s strip planner must be merged into RMOS:

compute_bom_for_design() 
    if saw_mode: use saw_strip_planner
    else: use router bom planner


Meaning:

kerf

blade thickness

saw feed direction

cut waste

grain alignment

All affect BOM for Saw Mode.

8. Integration Point #5 — Unified “Toolpath Operation” Format

Saw Lab operations become RMOS operations:

RmosToolpathOperation(
    op_id="saw_rip_cut_01",
    description="Rip cut with 1.2mm kerf",
    strategy="SAW_RIP",
    estimated_runtime_min=1.8,
)


Saw Lab will need a Toolpath Builder:

saw_toolpath_builder.py

9. Integration Point #6 — Directional Workflow Support
Design-First (UI)

Art Studio will send saw-related RosetteParamSpec or slab data → RMOS → Saw Lab mode triggers automatically.

Constraint-First

Saw Lab has unique constraints:

blade angle

blade thickness

safety risk envelopes

tear-out avoidance rules

grain direction alignment

Add Saw-specific rules to SearchBudgetSpec or create:

SawConstraintSpec

AI Mode

AI proposals must satisfy:

blade geometry limits

kerf feasibility

rip/cross strategy

RMOS filters the AI results through Saw Lab 2.0 before UI display.

10. Integration Point #7 — Feasibility Scoring Enhancements

RMOS must call Saw Lab calculators instead of router calculators:

Metric	Router	Saw Mode
Chipload	bit flute model	bite per tooth
Heat	bit heat model	rim speed + tooth friction
Deflection	bit stiffness	blade plate stiffness
Rim Speed	bit only	critical for saw blades
Risk	n/a	kickback, tooth loading, burning

Saw Lab’s risk_engine.py already implements:

rim speed risk

torque overload

thermal runaway

cut style risk (rip vs crosscut)

These map directly to RMOS feasibility warnings.

11. Integration Point #8 — Saw Lab Context Extensions

Extend RmosContext with optional Saw fields:

saw_blade_angle: Optional[float]
saw_approach_strategy: Optional[str]  # rip / cross / compound
saw_feed_mode: Optional[str]          # climb / conventional / hybrid


If unspecified → defaults in Saw Lab config.

12. Saw Lab 2.0 → RMOS Integration Diagram
                                      RMOS 2.0
                            (Feasibility + Toolpaths)
                                      │
                                      ▼
                         ┌───────────────────────────┐
                         │ Toolpath Engine Selector  │
                         └───────┬───────────────────┘
                                 │
                   ┌─────────────┴────────────────────┐
                   │                                  │
                   ▼                                  ▼
        ┌──────────────────────┐          ┌─────────────────────────┐
        │  Router Mode         │          │        Saw Mode          │
        │  (CAM_N16 lineage)   │          │   (CNC Saw Lab 2.0)      │
        └──────────┬───────────┘          └──────────┬──────────────┘
                   │                                  │
        geometry → RMOS geometry engine     geometry → RMOS geometry engine
        calculators → router models        calculators → saw physics models
        planner → router logic             planner → kerf planner, saw risk
                   │                                  │
                   ▼                                  ▼
        ┌──────────────────────┐          ┌─────────────────────────┐
        │ Router Operations    │          │ Saw Cutting Operations   │
        │ PROFILE, POCKET      │          │ RIP, CROSSCUT, SLICE     │
        └──────────┬───────────┘          └──────────┬──────────────┘
                   │                                  │
                   ▼                                  ▼
                G-CODE                             G-CODE
              (router)                           (saw-blade)

13. Implementation Roadmap (Concrete Steps)
Phase 1 — Formal Integration

Add if tool_id.startswith("saw:"): switch to RMOS toolpath planner

Move calculators from Saw Lab → RMOS calculator layer

Create RMOS → Saw Lab geometry wrappers

Phase 2 — Replace Saw Lab geometry with RMOS geometry engine

Shapely offsets

Boolean cut paths

Geometry cleanup

Phase 3 — Lift Saw Lab toolpath ops into RMOS ToolpathPlan

unify risk scoring

unify operation naming

unify runtime estimates

Phase 4 — Add Saw Mode to Directional Workflow

design-first paths

constraint-first generation rules

AI saw-blade compatibility

Phase 5 — Art Studio integration

saw mode preview

blade info UI

saw-specific feasibility display

14. Final Deliverable: Saw Lab 2.0 Becomes a First-Class RMOS Domain

After integration:

Saw Lab is not a separate “sandbox”

It becomes RMOS’s second manufacturing mode

AI can generate saw-blade designs safely

Art Studio can preview saw cuts identically to router cuts

G-code generator uses unified RMOS → Toolpath ops

Saw Lab finally reaches its intended role:

A full CNC saw-cutting manufacturing engine governed by RMOS.