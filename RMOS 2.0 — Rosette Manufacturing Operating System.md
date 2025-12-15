🎼 RMOS 2.0 — Rosette Manufacturing Operating System
Final Integrated Specification — December 2025
________________________________________
0. Mission Statement
RMOS is the manufacturing brain of the Luthier’s ToolBox ecosystem.
It governs all manufacturability rules, geometry processing, toolpath planning, and feasibility scoring across:
•	Art Studio (design-first workflows)
•	Constraint-First Generator (AI or rules-driven workflows)
•	CNC Saw Lab (saw-blade toolpath domain)
•	CAM_N16 lineage (router/bit-based toolpath domain)
RMOS ensures that every design is evaluated, scored, and manufactured under a single canonical logic path.
No subsystem bypasses RMOS.
________________________________________
1. RMOS Architecture Overview
RMOS consists of five cooperating layers:
1. Public API Layer (RMOS Facade)
2. Feasibility Layer (Calculators + Aggregator)
3. Geometry Layer (Engine Selector: ML / Shapely)
4. Toolpath Layer (Router / Saw modes)
5. Calculator Layer (Chipload, Heat, Deflection, Rim Speed, BOM)
Every layer is isolated behind a clean boundary so RMOS can evolve without breaking Art Studio or AI workflows.
________________________________________
2. RMOS Public API (Authoritative Interface)
Defined in:
rmos/api_contracts.py
RMOS exposes three core functions:
2.1 Feasibility Evaluation
compute_feasibility_for_design(design: RosetteParamSpec, context: RmosContext)
    -> RmosFeasibilityResult
Returns:
•	Overall feasibility score
•	Risk bucket (GREEN / YELLOW / RED)
•	Efficiency
•	Estimated cut time
•	Warnings
•	Raw details for debugging UI
________________________________________
2.2 Bill of Materials (Material Usage / Scrap / Strip Length)
compute_bom_for_design(design, context) -> RmosBomResult
________________________________________
2.3 Toolpath Planning (High-Level CAM Operations)
generate_toolpaths_for_design(design, context) -> RmosToolpathPlan
This represents:
•	PROFILE operations
•	POCKET cutters
•	SAW mode (via Saw Lab integration)
•	Estimated runtime
•	Sequencing logic (CAM_N16 lineage)
NOT raw G-code — the actual g-code generator is a downstream consumer.
________________________________________
3. Directional Workflow 2.0 (How Subsystems Call RMOS)
RMOS supports three directional workflows, all of which go through the same API:
________________________________________
3.1 Design-First Workflow (Art Studio)
User Adjusts Parameters
        ↓
Art Studio → RMOS.compute_feasibility
        ↓
UI updates:
  Score, risk bucket, warnings, cut-time estimate
Triggered on:
•	slider changes
•	parameter edits
•	tool/material/profile changes
________________________________________
3.2 Constraint-First Workflow (Rules + AI)
Constraints → Generator → Candidate → RMOS Feasibility
Repeated until:
•	Budget exhausted
•	Acceptable candidate found
This uses the SearchBudgetSpec formalized in Appendix B.
________________________________________
3.3 AI-Assisted Workflow
Same as constraint-first, but:
•	AI proposes param specs
•	RMOS filters them
•	Only GREEN/YELLOW are surfaced to UI
•	RED designs never reach the user
AI never bypasses RMOS.
________________________________________
4. Feasibility Layer (The Heart of RMOS)
The feasibility scorer aggregates the results from:
1.	Chipload Calculator
2.	Heat Calculator
3.	Deflection Calculator
4.	Rim Speed Calculator
5.	BOM Calculator
Each calculator returns:
•	score (0–100)
•	risk (GREEN/YELLOW/RED)
•	warning (if any)
Feasibility Decision Flow:
collect calculator results  
↓  
weighted scoring system  
↓  
risk bucket resolution  
↓  
material efficiency  
↓  
estimated cut time  
↓  
RMOS Feasibility Result
This ensures deterministic, repeatable manufacturability decisions.
________________________________________
5. Geometry Engine Layer (ML vs Shapely)
RMOS 2.0 formalizes the geometry backend:
Selection Rule (finalized in Appendix C)
IF context.use_shapely_geometry == True:
    USE ShapelyGeometryEngine
ELSE:
    USE MLGeometryEngine (legacy stable)
Why this matters:
•	Shapely is robust for:
o	boolean ops
o	complex offsets
o	clearance operations
o	AI-generated designs
•	ML engine retains:
o	strict determinism
o	legacy validations
o	compatibility with CAM_N16
________________________________________
6. Toolpath Engine Layer
RMOS toolpath engine sits after feasibility:
Workflow:
Design  
↓  
Feasibility (must pass)  
↓  
Toolpath Planner  
   • Router mode (CAM_N16)
   • Saw mode (Saw Lab)
↓  
Operation Plan  
↓  
G-code Generator (outside RMOS)
Router Mode
Produces:
•	contours
•	pockets
•	multi-pass Z stepping
•	lead-in/out
•	safe heights
Saw Mode (via CNC Saw Lab integration)
Produces:
•	kerf-aligned paths
•	blade-angle-aware cuts
•	blade-specific risk scoring
•	strip-slicing patterns
•	rip/cross/compound directionality
Reference implementation in:
•	kerf_planner.py
•	risk_engine.py
•	CNC Saw Lab Expanded Architecture
Toolpath planning is workflow-independent.
________________________________________
7. Calculator Layer Responsibilities
Each calculator is modular and testable.
Chipload Calculator
Inputs:
•	flute count
•	feed rate
•	RPM
•	material density
Outputs:
•	chipload_mm
•	score
•	warning
________________________________________
Heat Calculator
Uses:
•	chipload
•	cut length
•	material burn threshold
•	tool thermal properties
________________________________________
Deflection Calculator
Uses:
•	tool stick-out
•	lateral load
•	tool material (carbide / HSS)
•	beam deflection formulas
________________________________________
Rim Speed Calculator
Used heavily in Saw Lab workflows:
•	blade diameter
•	RPM
•	allowable surface speed per material
________________________________________
BOM Calculator
Computes:
•	strip length
•	scrap
•	tiling
•	material efficiency
Saw Lab BOM is more advanced thanks to kerf_planner.py.
________________________________________
8. RMOS Data Models (Formal)
RMOS 2.0 uses these canonical Pydantic models:
•	RosetteParamSpec
•	RmosContext
•	RmosFeasibilityResult
•	RmosBomResult
•	RmosToolpathPlan
•	SearchBudgetSpec
•	RiskBucket
•	RmosToolpathOperation
These are stable across the entire stack.
________________________________________
9. Appendix Bundle (Integrated)
Included below:
________________________________________
Appendix A — RmosContext Spec
class RmosContext(BaseModel):
    version: Literal["2.0"] = "2.0"

    material_id: str
    tool_id: str

    machine_profile_id: Optional[str] = None
    project_id: Optional[str] = None

    use_shapely_geometry: bool = False

    search_budget: SearchBudgetSpec = SearchBudgetSpec()

    user_notes: Optional[str] = None
Required per workflow:
Mode	Required Fields
Design-First	material_id, tool_id
Constraint-First	material_id, tool_id, search_budget
AI-Assisted	same as constraint-first + often use_shapely_geometry = True
Versioning rule: Always specify version="2.0".
________________________________________
Appendix B — SearchBudgetSpec
class SearchBudgetSpec(BaseModel):
    max_attempts: int = 25
    min_feasibility_score: float = 70.0
    time_limit_seconds: float = 2.0
    stop_on_first_green: bool = True
    deterministic: bool = True
Defines the constraint-first stopping logic.
________________________________________
Appendix C — Geometry Engine Selection
IF context.use_shapely_geometry → Shapely
ELSE → ML (legacy)
This ensures deterministic behavior and clear mode-switching for AI, Art Studio, and CAM.
________________________________________
Appendix D — Workflow → Toolpath Boundary
Toolpath planning begins only after feasibility passes.
All three workflows converge to:
RMOS.generate_toolpaths_for_design()
Whether suggestions came from:
•	user design
•	constraint-first rules
•	AI proposal
Toolpath planning does NOT depend on workflow mode — only on the final accepted design.
Router and Saw workflows share this entrypoint.
________________________________________
10. RMOS 2.0 Integration With CNC Saw Lab
Although Saw Lab is a separate subsystem, RMOS 2.0 fully supports:
•	Saw-based toolpath planning
•	Kerf-aware feed/speed calculations
•	Blade geometry validation
•	Saw-specific risk scoring
•	Blade angle optimization
•	Material ripping strategies
•	Heat buildup modeling (using Saw Lab’s more advanced methods)
Saw Lab’s architecture already contains:
•	risk_engine.py for blade physics
•	kerf_planner.py for material slicing
•	Expanded_Architecture.docx (full domain map)
These concepts are now absorbed into RMOS as part of the Toolpath Engine domain.
________________________________________
11. RMOS 2.0 In One Diagram
                ┌──────────────────────────────────┐
                │           ART STUDIO             │
                │    (Design-First Workflow)       │
                └───────────────┬──────────────────┘
                                │
                                │ Feasibility Request
                                ▼
                       ┌──────────────────┐
                       │      RMOS        │
                       │  Public API      │
                       └───────┬──────────┘
                               │
             ┌─────────────────┴──────────────────┐
             │                                    │
             │                    Constraint-First / AI
             ▼                                    ▼
     ┌───────────────┐                     ┌───────────────┐
     │ Feasibility   │  ← Calculators →    │  Search Loop  │
     │ Engine         │                    │ (Budget rules)│
     └───────┬────────┘                     └───────┬──────┘
             │                                        │
             └──────────────────┬─────────────────────┘
                                ▼
                       ┌─────────────────────────┐
                       │  Toolpath Engine        │
                       │ (Router / Saw modes)    │
                       └──────────┬──────────────┘
                                  ▼
                           ┌──────────┐
                           │  G-Code  │
                           └──────────┘
________________________________________
12. Status: RMOS 2.0 is now COMPLETE
This specification is:
•	internally consistent
•	code-aligned
•	directional-workflow aligned
•	Saw Lab aligned
•	ready for real physics/math to be plugged in
•	stable for Art Studio integration
•	durable for future AI workflows
•	versioned and fully documented
________________________________________
