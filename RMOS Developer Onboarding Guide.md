RMOS Developer Onboarding Guide
How to Work With the Rosette Manufacturing Operating System (RMOS 2.0)
Luthier’s ToolBox — Engineering Onboarding Document
________________________________________
1. What RMOS Is (and Is Not)
RMOS is the manufacturing operating system for the ToolBox ecosystem.
It:
•	Scores designs for manufacturability
•	Routes all geometry operations
•	Controls toolpath generation for router mode and saw-blade mode
•	Defines how Art Studio, AI, and Constraint-First flows interact with manufacturing logic
•	Prevents unsafe or impossible designs from reaching CAM
RMOS is not:
•	A UI subsystem
•	A geometry editor
•	An AI generator
•	A G-code post-processor
RMOS sits in the middle of the entire system, acting as the rule-keeper and gatekeeper.
________________________________________
2. RMOS Architecture (High-Level)
RMOS has 5 core layers:
1. RMOS Public API (Facade)
2. Feasibility Engine (Calculators + Aggregator)
3. Geometry Engine (ML/Shapely selector)
4. Toolpath Engine (Router & Saw Lab modes)
5. Calculator Layer (Chipload, Heat, Deflection, Rim Speed, BOM)
Every subsystem — Art Studio, AI, CLI tools, Saw Lab — must call RMOS through the public API only.
________________________________________
3. The RMOS Public API
Located in:
services/api/app/rmos/api_contracts.py
RMOS exposes three canonical entrypoints:
✔ 3.1 Feasibility
compute_feasibility_for_design(design, context)
✔ 3.2 BOM / Strip / Material Usage
compute_bom_for_design(design, context)
✔ 3.3 Toolpath Planning
generate_toolpaths_for_design(design, context)
These endpoints are also available over HTTP:
POST /api/rmos/feasibility
POST /api/rmos/bom
POST /api/rmos/toolpaths
Important:
All workflows must go through these functions.
________________________________________
4. Understanding RmosContext (Critical)
RmosContext defines the manufacturing environment:
class RmosContext(BaseModel):
    version: Literal["2.0"] = "2.0"
    material_id: str
    tool_id: str
    machine_profile_id: Optional[str]
    project_id: Optional[str]
    use_shapely_geometry: bool = False
    search_budget: SearchBudgetSpec = SearchBudgetSpec()
    user_notes: Optional[str]
4.1 Required Values Depend on Workflow:
Workflow Mode	Required Fields
Design-First	material_id, tool_id
Constraint-First	material_id, tool_id, search_budget
AI-Assisted	material_id, tool_id, search_budget, often use_shapely_geometry=True
4.2 Geometry Engine Selection
RMOS chooses backend using:
if context.use_shapely_geometry:
    engine = ShapelyGeometryEngine
else:
    engine = MLGeometryEngine
This avoids inconsistency between AI vs UI vs toolpath generation.
________________________________________
5. Feasibility Engine (How RMOS “Thinks”)
Feasibility = weighted blend of calculator results:
•	Chipload score
•	Heat score
•	Deflection score
•	Rim speed score
•	Material efficiency (BOM)
Result includes:
•	Overall score
•	Risk bucket (GREEN / YELLOW / RED)
•	Warnings
•	Estimated runtime
Every calculator is isolated and testable — very similar to risk_engine.py in Saw Lab (good pattern).
________________________________________
6. Geometry Engine (ML vs Shapely)
ML Engine (Legacy)
•	Extremely stable
•	Predictable
•	Safe for production CAM
Shapely Engine
•	Robust boolean ops
•	Great for AI and complex rosette designs
•	Used for previews and generative workflows
Selection Rule
context.use_shapely_geometry = True → use Shapely
else → use ML
This matches the strategy used in Saw Lab’s kerf_planner (batch/detailed mode selection).
________________________________________
7. Toolpath Engine (Router and Saw Mode)
RMOS routes all toolpath planning through:
generate_toolpaths_for_design()
It supports two execution modes:
________________________________________
7.1 Router Mode (CAM_N16 lineage)
Handles:
•	Offset contours
•	Pocketing
•	Z-step multi-pass planning
•	Lead-in/out strategies
•	Bit geometry constraints
This is the default when tool_id refers to router bits.
________________________________________
7.2 Saw Mode (CNC Saw Lab Integration)
Triggered when tool_id identifies a saw blade.
Uses insights from Saw Lab subsystem:
•	Blade geometry
•	Rim speed risk scoring (from risk_engine.py)
•	Kerf-aware path cutting (from kerf_planner.py)
•	Strip orientation
•	Rip/cross strategies
Router and saw modes share the same RMOS pipeline, diverging only inside the toolpath planner.
________________________________________
8. How Art Studio Interacts With RMOS
Art Studio calls RMOS over HTTP or via the python API.
Art Studio responsibilities:
•	Provide RmosContext
•	Provide RosetteParamSpec
•	Display RMOS results (score, warnings, risk bucket)
•	Never bypass RMOS for manufacturing logic
The Art Studio API bundle is already designed to match this.
________________________________________
9. How the AI System Interacts With RMOS
AI generates candidate RosetteParamSpec objects.
RMOS validates them.
RMOS rejects:
•	unsafe
•	impossible
•	tool-incompatible
•	geometry-invalid
Only RMOS-approved designs appear in the UI.
AI can never send raw geometry directly to toolpath engines.
________________________________________
10. Constraint-First Generative Workflow (Search Loop)
The search loop uses:
SearchBudgetSpec(
    max_attempts=25,
    min_feasibility_score=70,
    time_limit_seconds=2.0,
    stop_on_first_green=True,
    deterministic=True,
)
Loop:
for n attempts:
    candidate = generator.make_candidate()
    result = RMOS.compute_feasibility(candidate)
    if acceptable: return candidate
return failure
This ensures:
•	determinism
•	stability
•	bounded compute cost
________________________________________
11. RMOS → Toolpath Boundary (Important)
Toolpath generation begins only after feasibility passes.
Design → Feasibility → Toolpath → G-code
Every workflow (Design-First, Constraint-First, AI-Assisted) converges here.
This is how RMOS maintains manufacturing truth.
________________________________________
12. RMOS 2.0 → CNC Saw Lab Integration
Below is the integration diagram.
________________________________________
🪚 RMOS 2.0 → Saw Lab Integration Diagram
                         ┌────────────────────────┐
                         │        ART STUDIO      │
                         │   (Design Parameters)  │
                         └───────────┬────────────┘
                                     │ design + context
                                     ▼
                           ┌───────────────────────┐
                           │        RMOS API       │
                           └───────────┬───────────┘
                                       │
                             feasibility / BOM / toolpaths
                                       ▼
                           ┌───────────────────────┐
                           │  Feasibility Engine   │
                           │ (Calculators + Rules) │
                           └───────────┬───────────┘
                                       │
                          passes threshold? yes/no
                                       ▼
                           ┌───────────────────────┐
                           │    Toolpath Engine    │
                           │  (Router / Saw Mode)  │
                           └──────┬─────────┬──────┘
                                  │         │
                        router bit path  saw blade path
                                  │         │
                                  ▼         ▼
                   ┌──────────────────┐   ┌──────────────────┐
                   │  Router Planner  │   │   Saw Lab Planner │
                   │  (CAM_N16)       │   │ (kerf_planner,   │
                   │                  │   │  risk_engine)     │
                   └───┬──────────────┘   └───────────┬──────┘
                       │                               │
                       ▼                               ▼
             ┌──────────────────┐            ┌──────────────────┐
             │  Toolpath Ops    │            │  Kerf-aware Saw  │
             │  Contours, Zcuts │            │  Blade Paths     │
             └─────────┬────────┘            └─────────┬────────┘
                       │                               │
                       ▼                               ▼
                   G-CODE (router)                G-CODE (saw)
Meaning:
•	Both router and saw workflows flow through RMOS.
•	RMOS decides which toolpath logic to use based on tool_id.
•	Both use the same feasibility rules.
•	Saw workflows reuse Saw Lab’s risk and kerf logic.
