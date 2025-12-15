Below is the full Directional Workflow 2.0 Specification, written to drop directly into your repo:
docs/RMOS/Directional_Workflow_2_0.md
This doc formally defines the three directional workflows (Design-First, Constraint-First, AI-Assisted) and how they route through RMOS.compute_feasibility_for_design() using the RMOS 2.0 API.
________________________________________
Directional Workflow 2.0
Design-First, Constraint-First, and AI-Assisted Manufacturing Pipelines
Part of RMOS 2.0 Architecture
Author: Ross
Project: Luthier’s ToolBox
________________________________________
0. Purpose of this Document
The ToolBox now supports three distinct “directional” workflows for rosette creation:
1.	Design-First Workflow (Artist-driven)
2.	Constraint-First Workflow (Manufacturing-driven)
3.	AI-Assisted Workflow (Generative + Feasibility loop)
Directional Workflow 2.0 defines how each of these routes through RMOS using the same canonical API:
compute_feasibility_for_design(design: RosetteParamSpec, context: RmosContext)
RMOS is the manufacturing oracle that every direction must pass through before toolpaths are generated.
________________________________________
1. RMOS as the Workflow Director
Regardless of who drives the initial geometry (human, AI, or constraints), every workflow hits these RMOS layers in order:
(1) Input (Design / Constraints / AI)
      ↓
(2) RosetteParamSpec ← normalized design representation
      ↓
(3) RMOS.compute_feasibility_for_design()
      ↓
(4) FeasibilityScore (0–100), RiskBucket, Warnings, Efficiency
      ↓
(5) If feasible → RMOS.generate_toolpaths_for_design()
This ensures:
•	Manufacturability gating
•	Unified scoring and safety checks
•	Clear separation between design, constraints, physics, and toolpaths
Directional Workflow 2.0 formalizes how each lane enters this pipeline.
________________________________________
2. Directional Workflow Modes
RMOS supports 3 modes, each corresponding to a different entry point into the manufacturing process.
MODE A → Design-first (Artist)
MODE B → Constraint-first (Manufacturing-driven)
MODE C → AI-Assisted (Generative loop)
Each uses RMOS in a different order, but all funnel into:
compute_feasibility_for_design()
________________________________________
3. MODE A — Design-First Workflow (Artist-driven)
Summary
The designer starts with creative intent inside Art Studio: shapes, rings, motifs, diameters, widths, patterns.
RMOS checks manufacturability after design decisions.
Ideal for:
•	Human designers
•	Art Studio UI
•	Rosette pattern exploration
•	Revisions and refinement
________________________________________
A.1 Workflow Diagram
ARTIST
  │ (parametric input)
  ▼
Art Studio (RosetteParamSpec)
  │
  │ call RMOS.compute_feasibility_for_design(design, context)
  ▼
Feasibility Result:
  - score 0–100
  - risk bucket
  - warnings
  - cut-time estimate
  - material efficiency
  │
  ▼
User decides:
  - adjust parameters
  - accept design
  - export to CAM
  ▼
RMOS.generate_toolpaths_for_design()
________________________________________
A.2 Trigger Points
When Art Studio should call feasibility:
•	When the designer changes any parameter (outer diameter, ring widths, pattern type)
•	When switching materials or tools
•	Before enabling “Generate Toolpaths”
________________________________________
A.3 What This Mode Guarantees
•	Artist stays in control
•	RMOS provides live manufacturability guidance
•	AI is optional, not required
•	No unsafe design ever becomes a toolpath
________________________________________
4. MODE B — Constraint-First Workflow (Manufacturing-driven)
Summary
The CNC operator, production manager, or luthier sets:
•	Available materials
•	Stock strip dimensions
•	Tooling
•	Machine profile
•	Desired risk tolerance
•	Maximum cut time
•	Waste tolerance
RMOS (optionally with AI) generates acceptable design candidates that fit these constraints.
Ideal for:
•	Batch manufacturing
•	Production repeatability
•	“I have only 170 mm ebony strips left—what rosettes can I make?”
•	Automated workflows
________________________________________
B.1 Workflow Diagram
OPERATOR
  │ (manufacturing constraints)
  ▼
Constraint Input (RmosContext)
  │
AI (optional): generate candidate RosetteParamSpec
  │
  ▼
RMOS.compute_feasibility_for_design(design, context)
  │
Rejected → try another candidate
Accepted → present to user
  ▼
User approves → RMOS.generate_toolpaths_for_design()
________________________________________
B.2 Key Idea: RMOS is the Search Evaluator
The constraint-first workflow needs RMOS feasibility because:
•	RMOS enforces tool/material rules
•	RMOS enforces geometry constraints
•	RMOS evaluates safety, heat, chipload, deflection, rim-speed
•	RMOS rejects impossible or unsafe candidates
This allows controlled exploration rather than pure creativity.
________________________________________
B.3 Execution Pattern
Inside a batch or loop:
ctx = RmosContext(
    material_id="ebony",
    tool_id="v60",
    use_shapely_geometry=True,
)

for candidate in generate_candidates(constraints):
    result = compute_feasibility_for_design(candidate, ctx)
    if result.risk_bucket != RiskBucket.RED:
        yield candidate, result
________________________________________
5. MODE C — AI-Assisted Workflow (Generative Feedback Loop)
Summary
AI proposes designs. RMOS scores and filters them before presenting anything to the user.
This prevents “bad geometry” hallucinations and unsafe paths.
Ideal for:
•	Exploring variations of a rosette
•	“Show me 6 safe designs within these constraints”
•	Rapid iteration
•	Constraint-first or design-first augmentation
________________________________________
C.1 Workflow Diagram
AI Model
  │
  ├─► propose 6 design variations
  │
  ▼
RMOS.compute_feasibility_for_design() on each
  │
  ├─► Filter RED
  ├─► Score & rank GREEN/YELLOW
  │
  ▼
Art Studio presents sorted list:
   #1 score 92 — GREEN
   #2 score 84 — YELLOW (heat risk)
   #3 score 71 — GREEN
   …
  │
  ▼
User selects → RMOS.generate_toolpaths_for_design()
This is AI under RMOS governance, not AI acting independently.
________________________________________
C.2 Why RMOS is mandatory in AI mode
AI is non-deterministic. RMOS is deterministic.
AI:
•	generates shapes
•	may break rules
•	may not understand material/tool limits
RMOS:
•	prevents mistakes
•	enforces physics
•	rejects unmanufacturable results
•	clarifies tradeoffs (efficiency, heat, deflection)
AI becomes a creative partner, not a safety risk.
________________________________________
6. RMOS 2.0 Unified API for All Workflows
All three workflows converge to the same call:
result = compute_feasibility_for_design(design, context)
Inputs:
•	RosetteParamSpec (design geometry)
•	RmosContext (tools, material, machine constraints)
Outputs:
•	feasibility score
•	risk category
•	warnings
•	cut-time estimate
•	material usage efficiency
Next Step After Feasibility:
toolpaths = generate_toolpaths_for_design(design, context)
The same RMOS pipeline serves all workflows safely.
________________________________________
7. Directional Workflow Control Layer (Optional Future)
Eventually, we can add a lightweight controller:
services/api/app/workflow/directional_workflow.py
This would abstract:
•	Switching modes
•	AI suggestion generation
•	Constraint evaluation loops
•	Real-time feasibility updates
Not required today — but the architecture supports this cleanly.
________________________________________
8. Summary Table
Workflow Mode	Driver	RMOS Role	When Feasibility Is Called	Strength
Design-First	Artist	Safety & manufacturability	On every change	Creative freedom with guardrails
Constraint-First	Operator	Evaluator for candidate search	Before presenting candidates	Production consistency
AI-Assisted	AI generator	Filter + score + rank	Immediately post-generation	Controlled, supervised generative design
________________________________________
9. Final Statement
Directional Workflow 2.0 brings clarity, safety, and power to the ToolBox ecosystem:
•	Art Studio gets real-time manufacturability feedback
•	AI becomes a guided assistant rather than a liability
•	The CNC pipeline becomes predictable and trustworthy
•	RMOS sits at the center as the deterministic manufacturing authority
This doc formalizes the navigation lanes inside the ToolBox so every subsystem knows exactly how to move through RMOS.
