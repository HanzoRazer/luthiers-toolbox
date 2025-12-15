(1) a drop-in Developer Onboarding Guide and (2) ready-to-save SVG diagrams for your workflows.
You can paste the guide into:
docs/RMOS/RMOS_Developer_Onboarding.md
and the SVGs into something like:
docs/RMOS/img/*.svg
________________________________________
1. Developer Onboarding Guide (RMOS 2.0 + Directional Workflow 2.0)
# RMOS 2.0 + Directional Workflow 2.0  
## Developer Onboarding Guide

**Project:** Luthier’s ToolBox  
**Subsystem:** RMOS (Rosette Manufacturing OS) + Directional Workflow 2.0  
**Audience:** Backend devs, frontend devs (Art Studio / RMOS UI), AI/ML devs, CAM devs

---

## 0. What RMOS Is (and Is Not)

RMOS (Rosette Manufacturing OS) is the **deterministic manufacturing brain** of the ToolBox:

- It evaluates whether a rosette design is **manufacturable, safe, and efficient**.
- It provides **scores, risk buckets, warnings, and cut-time estimates**.
- It **gates toolpath generation**: unsafe designs never reach CAM.

RMOS is **not**:

- A freeform geometry playground.
- A rendering layer.
- A G-code post-processor (that’s CAM_N16 and friends).

Instead, RMOS sits in the middle of the ecosystem as:

> **Manufacturing oracle** for all directional workflows.

---

## 1. Core Concepts

### 1.1 RosetteParamSpec

`RosetteParamSpec` is the **canonical design representation** for rosettes:

- Diameters, ring widths, counts
- Strip families and motifs
- Pattern parameters
- Symmetry and layout

Every workflow (Design-First, Constraint-First, AI-Assisted) must end up with a `RosetteParamSpec` before calling RMOS.

> If you’re consuming or producing rosette designs, you speak `RosetteParamSpec`.

---

### 1.2 RmosContext

`RmosContext` describes the **manufacturing environment**:

- Material: density, hardness, heat sensitivity, strip stock limits
- Tools: cutters, spindle ranges, chipload limits
- Machine profile: feed/speed envelope, rigidity, max RPM, axis limits
- Policy knobs: risk tolerance, max cut time, waste tolerance, geometry mode (e.g. `use_shapely_geometry=True`)

You can think of `RmosContext` as:

> A snapshot of “what machine + material + policy” we are allowed to use right now.

---

### 1.3 Feasibility API

All workflows converge on this API:

```python
result = compute_feasibility_for_design(design: RosetteParamSpec, context: RmosContext)
Inputs
•	design: the rosette geometry/parameters
•	context: the manufacturing environment
Outputs (conceptual)
•	score: 0–100 manufacturability score
•	risk_bucket: e.g. GREEN / YELLOW / RED
•	warnings: list of human-readable notes (heat risk, too thin strips, tool deflection, etc.)
•	cut_time_estimate: approximate runtime
•	material_efficiency: ratio of useful material vs waste
If feasible, the next step is:
toolpaths = generate_toolpaths_for_design(design, context)
________________________________________
2. Directional Workflows
RMOS supports three directional “lanes” into the same pipeline:
1.	Design-First (Mode A) – Artist-driven from Art Studio
2.	Constraint-First (Mode B) – Operator/production driven
3.	AI-Assisted (Mode C) – AI proposes designs, RMOS filters
All three must go through:
compute_feasibility_for_design()
before toolpaths are generated.
2.1 Mode A — Design-First (Artist-Driven)
•	Driver: Human designer using Art Studio
•	Flow:
1.	User edits design parameters in Art Studio, which builds a RosetteParamSpec.
2.	Art Studio calls compute_feasibility_for_design(design, context):
	On parameter changes
	When tools/material change
	Before enabling “Generate Toolpaths”
3.	Result shows score, risk, warnings, estimates.
4.	If acceptable → call generate_toolpaths_for_design() → CAM.
•	Guarantees:
o	Artist stays in control.
o	RMOS provides live manufacturability feedback.
o	Unsafe designs are blocked before CAM.
________________________________________
2.2 Mode B — Constraint-First (Manufacturing-Driven)
•	Driver: Operator, luthier, production planner.
•	Inputs:
o	Material inventory & dimensions
o	Available tools / machine limits
o	Risk tolerance, max cut time, waste tolerance
•	Flow (pseudo):
•	ctx = RmosContext(
•	    material_id="ebony",
•	    tool_id="v60",
•	    use_shapely_geometry=True,
•	    # plus risk + time + waste policies
•	)
•	
•	for candidate in generate_candidates(constraints):
•	    result = compute_feasibility_for_design(candidate, ctx)
•	    if result.risk_bucket != RiskBucket.RED:
•	        yield candidate, result  # usable design
•	RMOS serves as a search evaluator: AI or rule-based logic proposes candidates, RMOS decides what’s safe/acceptable.
________________________________________
2.3 Mode C — AI-Assisted (Generative Feedback Loop)
•	Driver: AI model (LLM, generative geometry engine, etc.)
•	Flow:
1.	AI proposes N design variations (N ~ 3–10).
2.	RMOS calls compute_feasibility_for_design() on each.
3.	RMOS:
	Drops RED designs.
	Scores and ranks remaining designs.
	Annotates with warnings (heat, deflection, etc.).
4.	Art Studio UI presents a sorted list for the user to pick from.
5.	User selects design → generate_toolpaths_for_design().
•	Philosophy:
o	AI is creative but non-authoritative.
o	RMOS is authoritative on physics and safety.
________________________________________
3. First 60 Minutes: What a New Dev Should Do
3.1 Clone & Start the API
1.	Clone the repo.
2.	Activate the Python virtual environment.
3.	Start the FastAPI server:
4.	uvicorn app.main:app --reload --port 8000
5.	Open the API docs (typically http://127.0.0.1:8000/docs).
3.2 Run a Feasibility Call (Mode A Example)
•	Use either:
o	Swagger UI (/docs), or
o	A small script or HTTP client (curl, Postman, etc.)
•	Example JSON payload (simplified):
•	{
•	  "design": {
•	    "outer_diameter": 100.0,
•	    "rings": [
•	      {"width": 2.0, "pattern": "herringbone"},
•	      {"width": 1.0, "pattern": "black_white_black"}
•	    ],
•	    "center_pattern": "mosaic"
•	  },
•	  "context": {
•	    "material_id": "ebony",
•	    "tool_id": "v60",
•	    "machine_id": "grbl_router",
•	    "risk_tolerance": "medium"
•	  }
•	}
•	Verify you get back a feasibility result with:
o	score
o	risk_bucket
o	warnings
3.3 Follow the Design-First Loop
•	With the server running, adjust your design input and re-hit the endpoint.
•	Observe how feasibility changes.
•	This mirrors what Art Studio will do in real time.
________________________________________
4. Extending RMOS
4.1 Adding a New Risk Metric
Examples: new heat model, new deflection heuristic, or strip delamination risk.
Steps:
1.	Locate the RMOS risk evaluation module (e.g. rmos/risk_engine.py).
2.	Add your metric as a function that:
o	Takes design + context.
o	Returns a scalar score and/or a warning string.
3.	Register it in the main feasibility pipeline.
4.	Update tests and docs.
Key invariant:
Your metric must be deterministic for a given (design, context).
________________________________________
4.2 Adding a New Workflow Feature
If you’re extending:
•	Art Studio (Design-First)
•	Constraint search logic
•	AI suggestion generation
Do:
•	Keep your upstream logic stateless wrt manufacturing rules.
•	Always call compute_feasibility_for_design() before unlocking toolpaths.
•	Pass both design and context into RMOS, don’t “guess” constraints on the client.
________________________________________
4.3 Adding a New Direction Mode (Future)
The architecture allows new “modes” (e.g., Library-First: pick from catalog + tweak). The rules:
•	You may add new workflows.
•	You may not bypass RMOS. Every path must still call:
o	compute_feasibility_for_design()
o	then generate_toolpaths_for_design() if feasible.
________________________________________
5. Safety & Invariants
These invariants must never be broken:
1.	No toolpaths without feasibility.
Any code path that outputs toolpaths must have a successful feasibility call upstream.
2.	RMOS is deterministic.
Same (design, context) → same result. Don’t introduce randomness in core scoring.
3.	AI is advisory only.
AI proposals must be filtered by RMOS; no direct AI → toolpath path is allowed.
4.	Context must be explicit.
Don’t bake hidden machine/material assumptions into Art Studio or AI logic. Use RmosContext.
5.	Versioning:
o	Don’t silently change what score means without a version bump or clear docs.
o	If you change scoring, update regression tests and golden baselines.
________________________________________
6. Where Things Live (Typical Repo Layout)
(Exact paths may vary; adjust to match your repo.)
•	docs/RMOS/Directional_Workflow_2_0.md
→ The document that explains Modes A/B/C.
•	docs/RMOS/RMOS_Developer_Onboarding.md
→ This guide.
•	app/rmos/
→ Core RMOS engine (feasibility, risk, scoring).
•	app/cam/
→ CAM_N16 and toolpath engine (not RMOS, but downstream).
•	client/app/art_studio/
→ Art Studio UI (Design-First front-end).
•	client/app/workflows/
→ Optional directional workflow control layer (future).
________________________________________
7. Quick FAQ for New Devs
Q: Can I call CAM directly with a RosetteParamSpec?
A: No. You must go through RMOS and get a feasibility result first.
Q: Does AI pick toolpaths?
A: No. AI only proposes designs. RMOS + CAM generate toolpaths.
Q: Where do I add a new risk visualization in the UI?
A: In the Art Studio / RMOS panel that consumes the feasibility result and renders scores and warnings.
Q: How do I add a new workflow mode?
A: Add a front-end flow or service layer, but end it in compute_feasibility_for_design() and then generate_toolpaths_for_design().
________________________________________
8. Final Mental Model
Think of RMOS as:
The gatekeeper between “cool rosette idea” and “steel cutting wood.”
All workflows, no matter how clever or creative, must pass through the same deterministic manufacturing gate.
Welcome aboard.

---

## 2. SVG Visual Diagrams for the Workflows

Below are **ready-to-save SVGs**.  
You can drop each into its own file under `docs/RMOS/img/` (or wherever you keep diagrams).

### 2.1 Overview: All Workflows Converge on RMOS

**File:** `docs/RMOS/img/directional_workflow_overview.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="880" height="260" viewBox="0 0 880 260">
  <style>
    .box { fill:#ffffff; stroke:#333333; stroke-width:1.5; rx:8; ry:8; }
    .primary { fill:#f0f7ff; }
    .rmos { fill:#e4ffe6; }
    .cam { fill:#fff4e0; }
    .label { font-family:system-ui, sans-serif; font-size:12px; fill:#222222; }
    .title { font-family:system-ui, sans-serif; font-size:16px; font-weight:bold; fill:#222222; }
    .arrow { stroke:#444444; stroke-width:1.5; marker-end:url(#arrowhead); fill:none; }
  </style>
  <defs>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#444444" />
    </marker>
  </defs>

  <text x="440" y="26" text-anchor="middle" class="title">
    Directional Workflow 2.0 — All Modes Converge on RMOS
  </text>

  <!-- Design-First -->
  <rect x="40" y="70" width="180" height="50" class="box primary"/>
  <text x="130" y="92" text-anchor="middle" class="label">Mode A: Design-First</text>
  <text x="130" y="110" text-anchor="middle" class="label">Artist / Art Studio</text>

  <!-- Constraint-First -->
  <rect x="40" y="140" width="180" height="50" class="box primary"/>
  <text x="130" y="162" text-anchor="middle" class="label">Mode B: Constraint-First</text>
  <text x="130" y="180" text-anchor="middle" class="label">Operator / Production</text>

  <!-- AI-Assisted -->
  <rect x="40" y="210" width="180" height="50" class="box primary"/>
  <text x="130" y="232" text-anchor="middle" class="label">Mode C: AI-Assisted</text>
  <text x="130" y="250" text-anchor="middle" class="label">Generative Suggestions</text>

  <!-- Arrows into RosetteParamSpec -->
  <line x1="220" y1="95" x2="300" y2="95" class="arrow" />
  <line x1="220" y1="165" x2="300" y2="165" class="arrow" />
  <line x1="220" y1="235" x2="300" y2="235" class="arrow" />

  <!-- RosetteParamSpec box -->
  <rect x="300" y="110" width="180" height="60" class="box"/>
  <text x="390" y="135" text-anchor="middle" class="label">RosetteParamSpec</text>
  <text x="390" y="153" text-anchor="middle" class="label">Canonical Design Representation</text>

  <!-- Arrow to RMOS -->
  <line x1="480" y1="140" x2="560" y2="140" class="arrow" />

  <!-- RMOS box -->
  <rect x="560" y="80" width="200" height="60" class="box rmos"/>
  <text x="660" y="103" text-anchor="middle" class="label">RMOS.compute_feasibility_for_design()</text>
  <text x="660" y="121" text-anchor="middle" class="label">Score · Risk · Warnings · Estimates</text>

  <!-- Arrow to Toolpaths -->
  <line x1="660" y1="140" x2="660" y2="185" class="arrow" />

  <!-- Toolpath/CAM box -->
  <rect x="560" y="185" width="200" height="55" class="box cam"/>
  <text x="660" y="208" text-anchor="middle" class="label">RMOS.generate_toolpaths_for_design()</text>
  <text x="660" y="226" text-anchor="middle" class="label">→ CAM / CNC Toolpaths</text>
</svg>
________________________________________
2.2 Mode A — Design-First Workflow Diagram
File: docs/RMOS/img/mode_a_design_first.svg
 
________________________________________
2.3 Mode B — Constraint-First Workflow Diagram
File: docs/RMOS/img/mode_b_constraint_first.svg
 
________________________________________
2.4 Mode C — AI-Assisted Workflow Diagram
File: docs/RMOS/img/mode_c_ai_assisted.svg
 



