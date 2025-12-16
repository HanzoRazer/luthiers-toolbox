AI Subsystem Integration Handoff
Luthier's ToolBox — RMOS AI Scaffolding
December 16, 2025
1. Executive Summary
This document provides integration instructions for the AI subsystem scaffolding. The sandbox has produced a comprehensive Workflow State Machine & Approval Gate Bundle that enforces explicit workflow sessions, state transitions, and server-side feasibility verification before toolpath generation.
The codebase has existing AI infrastructure that is partially implemented. This handoff identifies the gaps and provides specific wiring instructions to connect the sandbox's work to the production codebase.
2. Codebase Reality Check
2.1 What Actually Exists (Implemented)
Component	Location	Status
ai_search.py	rmos/ai_search.py	Complete
schemas_ai.py	rmos/schemas_ai.py	Complete
api_ai_routes.py	rmos/api_ai_routes.py	Complete
feasibility_scorer.py	rmos/feasibility_scorer.py	Complete
cad/ package	cad/	Complete
ai_core generators	_experimental/ai_core/	In _experimental
2.2 What Is Missing (Phantom Imports)
The file rmos/runs/__init__.py imports modules that do not exist:
from .schemas import RunArtifact, RunDecision, Hashes, RunOutputs  # MISSING
from .hashing import sha256_text, sha256_json, ...  # MISSING
from .store import RunStore  # MISSING
2.3 Import Path Mismatch
The api_ai_routes.py health check imports from ..ai_core.generators but ai_core is actually at _experimental/ai_core/. This import will fail at runtime.
3. Integration Tasks
3.1 Task A: Implement Run Artifact Files
Create three files in services/api/app/rmos/runs/ based on the RUN_ARTIFACT_PERSISTENCE.md specification:
1.	schemas.py — RunArtifact, RunDecision, Hashes, RunOutputs Pydantic models
2.	hashing.py — sha256_text(), sha256_json(), sha256_toolpaths_payload(), summarize_request()
3.	store.py — RunStore class with write_artifact() and new_run_id()
3.2 Task B: Promote ai_core from _experimental
Move the ai_core package to the production location:
mv services/api/app/_experimental/ai_core services/api/app/ai_core
Then update imports in:
•	rmos/ai_search.py (line 55-60)
•	rmos/api_ai_routes.py (line 226)
3.3 Task C: Add Workflow State Machine Files
Create the sandbox's workflow files at these locations:
4.	rmos/workflow_state.py — WorkflowState enum, WorkflowEvent enum, reduce_state()
5.	rmos/workflow_store.py — JSON-based session persistence
6.	rmos/api_workflow.py — FastAPI router with /sessions, /context, /approve endpoints
7.	routers/rmos_toolpaths_workflow_guard.py — Guard router requiring APPROVED state
3.4 Task D: Wire Integration Points
The sandbox identified two TODO integration points that must be wired:
Integration Point 1: compute_server_feasibility()
In api_workflow.py, replace the stub with:
from .feasibility_scorer import score_design_feasibility
from .api_contracts import RmosContext, RosetteParamSpec
Integration Point 2: generate_toolpaths_server_side()
In rmos_toolpaths_workflow_guard.py, wire to existing toolpath generation. The exact integration depends on which toolpath builder you want to use (saw vs router mode).
4. Router Registration
Add to services/api/app/main.py:
from .rmos.api_workflow import router as workflow_router
from .routers.rmos_toolpaths_workflow_guard import router as toolpaths_guard
app.include_router(workflow_router, prefix="/api")
app.include_router(toolpaths_guard, prefix="/api")
5. Workflow State Machine Overview
The sandbox's state machine enforces this flow:
State	Allowed Events	Description
DRAFT	SET_CONTEXT	Initial state, binding tool/material/machine
FEASIBILITY_CHECKED	APPROVE, RECORD_CANDIDATES	Server computed feasibility
APPROVED	GENERATE_TOOLPATHS	Only GREEN feasibility can reach this state
TOOLPATHS_GENERATED	(terminal)	Success — toolpaths available
BLOCKED	(terminal)	RED feasibility — cannot proceed
6. Key Architectural Principle
The core rule enforced by this system: No toolpaths without APPROVED state. Approval requires GREEN feasibility computed server-side. Client-provided feasibility is stripped and ignored.
This guarantees:
•	Safety decisions are server-controlled and auditable
•	Malicious clients cannot bypass safety checks
•	One feasibility engine, one source of truth
•	Authoritative feasibility included in error responses
7. Test Verification
After implementation, run the sandbox's test to verify the approval gate:
pytest tests/test_workflow_approval_gate.py -v
The test proves:
•	Toolpaths fail before approval (HTTP 409)
•	Approval fails if feasibility is not GREEN
•	When feasibility is GREEN, toolpaths are allowed
8. File Checklist
Files to create or modify:
File Path	Action	Priority
rmos/runs/schemas.py	CREATE	P0
rmos/runs/hashing.py	CREATE	P0
rmos/runs/store.py	CREATE	P0
ai_core/ (move from _experimental)	MOVE	P0
rmos/workflow_state.py	CREATE	P1
rmos/workflow_store.py	CREATE	P1
rmos/api_workflow.py	CREATE	P1
routers/rmos_toolpaths_workflow_guard.py	CREATE	P1
main.py	MODIFY (add routers)	P2
tests/test_workflow_approval_gate.py	CREATE	P2
9. Next Steps After This Bundle
Once the workflow state machine is integrated:
8.	Workflow → Run Artifact Binding — Automatically create RunArtifact when toolpaths are generated
9.	Run Artifact Query API — List runs by day, tool_id, mode, status
10.	Frontend Run Browser — Vue components for viewing run history
11.	Diff Viewer — Compare runs side-by-side
Appendix: Source Documents
This handoff synthesizes requirements from:
•	SERVER_SIDE_FEASIBILITY_ENFORCEMENT.md
•	BIDIRECTIONAL_WORKFLOW_ANALYSIS_REPORT.md
•	RUN_ARTIFACT_PERSISTENCE.md
•	AI_SCHEMA_NAMESPACE_REPORT.md
•	AI_Workflow_State_Machine_Approval_Gate.docx (sandbox output)
