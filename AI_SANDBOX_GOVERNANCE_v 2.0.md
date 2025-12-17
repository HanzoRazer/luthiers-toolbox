Yes — here is a tight, repo-ready document you can drop in now. It is written to lock the AI sandbox, prevent bleed-through into production RMOS, and make future audits trivial.
________________________________________
AI_SANDBOX_GOVERNANCE.md
Purpose
This document defines hard boundaries, allowed interactions, and promotion rules for all AI-related subsystems in the Luthier’s ToolBox / RMOS ecosystem.
The goal is to ensure that:
•	AI experimentation cannot bypass safety
•	AI outputs cannot directly generate toolpaths
•	Production behavior remains deterministic, auditable, and reproducible
•	Experimental AI work remains fast without polluting core systems
________________________________________
Canonical Principle (Non-Negotiable)
AI systems may propose. RMOS decides.
AI subsystems are advisory only.
They do not own feasibility, approval, or toolpath authority.
________________________________________
Directory Boundaries
✅ Canonical Production (NO AI logic here)
services/api/app/rmos/
├── api/
│   ├── rmos_feasibility_router.py
│   ├── rmos_toolpaths_router.py
│   └── rmos_runs_router.py
├── runs/
├── policies/
└── workflow/
Rules:
•	No AI imports
•	No probabilistic logic
•	Deterministic inputs → deterministic outputs
________________________________________
🧪 AI Sandbox (Explicitly Non-Production)
services/api/app/_experimental/ai/
├── search/
├── scoring/
├── prompt_templates/
├── heuristics/
├── adapters/
└── README.md
Rules:
•	May call public RMOS APIs
•	May NOT import RMOS internals
•	May NOT write toolpaths
•	May NOT write RunArtifacts
•	May NOT approve workflows
All AI code must live here unless promoted.
________________________________________
Allowed AI → RMOS Interactions
✅ Allowed
•	Call POST /api/rmos/feasibility
•	Suggest:
o	parameter changes
o	material/tool alternatives
o	constraint relaxations
•	Attach annotations to UI (non-binding)
•	Generate candidate designs (not decisions)
❌ Forbidden
•	Calling dispatch_toolpaths
•	Writing gcode
•	Modifying feasibility results
•	Creating or mutating Run Artifacts
•	Setting WorkflowState or approvals
________________________________________
Promotion Rules (Sandbox → Core)
AI code may be promoted only if:
1.	Logic becomes deterministic
2.	Inputs and outputs are fully typed
3.	Results are explainable
4.	A golden test exists
5.	It no longer depends on:
o	prompts
o	temperature
o	model-specific behavior
Promotion Path
_experimental/ai/...  →  app/rmos/assist/
Never promote directly into rmos/.
________________________________________
Workflow Guardrails
Toolpaths Invariant
AI → (suggestions only)
RMOS Feasibility → APPROVED
RMOS Toolpaths → Generated
RunArtifact → Persisted
AI is not part of the execution path.
________________________________________
Run Artifacts & AI
AI systems:
•	❌ cannot create artifacts
•	❌ cannot modify artifacts
•	✅ may read artifacts (read-only) for analysis or learning
All persisted artifacts are authoritative system records, not AI opinions.
________________________________________
Configuration Enforcement
Required Flags (Production)
REQUIRE_SERVER_SIDE_FEASIBILITY = True
BLOCK_ON_UNKNOWN_RISK = True
ALLOW_AI_DIRECT_TOOLPATHS = False
These must not be configurable at runtime.
________________________________________
Frontend Rules
•	AI UI panels must:
o	visually indicate “Suggestion / Advisory”
o	never look like approvals
•	All “Generate” actions route through RMOS endpoints
•	No client-side feasibility scoring
________________________________________
Audit Checklist
Before any AI feature merges:
•	Does it write toolpaths? → Reject
•	Does it bypass feasibility? → Reject
•	Does it modify approval state? → Reject
•	Is it deterministic? → Required for promotion
•	Is it sandboxed? → Required
________________________________________
Final Lock Statement
AI accelerates exploration.
RMOS governs execution.
Safety is never delegated.
________________________________________
If you want next, I can:
•	generate _experimental/ai/README.md to match this
•	add CI checks that prevent AI imports in rmos/
•	draft a SUBSYSTEM_PROMOTION_CHECKLIST_AI.md aligned to this policy
Just say the word.



Yes — here is a tight, repo-ready document you can drop in now. It is written to lock the AI sandbox, prevent bleed-through into production RMOS, and make future audits trivial.
________________________________________
AI_SANDBOX_GOVERNANCE.md
Purpose
This document defines hard boundaries, allowed interactions, and promotion rules for all AI-related subsystems in the Luthier’s ToolBox / RMOS ecosystem.
The goal is to ensure that:
•	AI experimentation cannot bypass safety
•	AI outputs cannot directly generate toolpaths
•	Production behavior remains deterministic, auditable, and reproducible
•	Experimental AI work remains fast without polluting core systems
________________________________________
Canonical Principle (Non-Negotiable)
AI systems may propose. RMOS decides.
AI subsystems are advisory only.
They do not own feasibility, approval, or toolpath authority.
________________________________________
Directory Boundaries
✅ Canonical Production (NO AI logic here)
services/api/app/rmos/
├── api/
│   ├── rmos_feasibility_router.py
│   ├── rmos_toolpaths_router.py
│   └── rmos_runs_router.py
├── runs/
├── policies/
└── workflow/
Rules:
•	No AI imports
•	No probabilistic logic
•	Deterministic inputs → deterministic outputs
________________________________________
🧪 AI Sandbox (Explicitly Non-Production)
services/api/app/_experimental/ai/
├── search/
├── scoring/
├── prompt_templates/
├── heuristics/
├── adapters/
└── README.md
Rules:
•	May call public RMOS APIs
•	May NOT import RMOS internals
•	May NOT write toolpaths
•	May NOT write RunArtifacts
•	May NOT approve workflows
All AI code must live here unless promoted.
________________________________________
Allowed AI → RMOS Interactions
✅ Allowed
•	Call POST /api/rmos/feasibility
•	Suggest:
o	parameter changes
o	material/tool alternatives
o	constraint relaxations
•	Attach annotations to UI (non-binding)
•	Generate candidate designs (not decisions)
❌ Forbidden
•	Calling dispatch_toolpaths
•	Writing gcode
•	Modifying feasibility results
•	Creating or mutating Run Artifacts
•	Setting WorkflowState or approvals
________________________________________
Promotion Rules (Sandbox → Core)
AI code may be promoted only if:
1.	Logic becomes deterministic
2.	Inputs and outputs are fully typed
3.	Results are explainable
4.	A golden test exists
5.	It no longer depends on:
o	prompts
o	temperature
o	model-specific behavior
Promotion Path
_experimental/ai/...  →  app/rmos/assist/
Never promote directly into rmos/.
________________________________________
Workflow Guardrails
Toolpaths Invariant
AI → (suggestions only)
RMOS Feasibility → APPROVED
RMOS Toolpaths → Generated
RunArtifact → Persisted
AI is not part of the execution path.
________________________________________
Run Artifacts & AI
AI systems:
•	❌ cannot create artifacts
•	❌ cannot modify artifacts
•	✅ may read artifacts (read-only) for analysis or learning
All persisted artifacts are authoritative system records, not AI opinions.
________________________________________
Configuration Enforcement
Required Flags (Production)
REQUIRE_SERVER_SIDE_FEASIBILITY = True
BLOCK_ON_UNKNOWN_RISK = True
ALLOW_AI_DIRECT_TOOLPATHS = False
These must not be configurable at runtime.
________________________________________
Frontend Rules
•	AI UI panels must:
o	visually indicate “Suggestion / Advisory”
o	never look like approvals
•	All “Generate” actions route through RMOS endpoints
•	No client-side feasibility scoring
________________________________________
Audit Checklist
Before any AI feature merges:
•	Does it write toolpaths? → Reject
•	Does it bypass feasibility? → Reject
•	Does it modify approval state? → Reject
•	Is it deterministic? → Required for promotion
•	Is it sandboxed? → Required
________________________________________
Final Lock Statement
AI accelerates exploration.
RMOS governs execution.
Safety is never delegated.
________________________________________
If you want next, I can:
•	generate _experimental/ai/README.md to match this
•	add CI checks that prevent AI imports in rmos/
•	draft a SUBSYSTEM_PROMOTION_CHECKLIST_AI.md aligned to this policy
Just say the word.

