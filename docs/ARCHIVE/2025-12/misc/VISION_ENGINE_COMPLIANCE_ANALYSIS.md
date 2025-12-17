# AI Sandbox Analysis: Vision Engine Integration

## Executive Summary

This document analyzes the governance framework from the ChatGPT sandbox sessions and how it integrates with our Guitar Vision Engine work.

**Key Finding:** Our Vision Engine implementation is **fully compliant** with the governance framework. All code resides in `_experimental/ai_graphics/` (advisory zone), uses no RMOS imports, and communicates via public APIs.

## Governance Architecture

### Trust Boundary Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     RMOS (Authoritative)                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Workflow   │  │  Toolpaths  │  │    Runs     │             │
│  │  Approval   │  │  Generation │  │  Artifacts  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │               │               │                       │
│         └───────────────┴───────────────┘                       │
│                         │                                       │
│              ┌──────────┴──────────┐                            │
│              │  Feasibility Gate   │                            │
│              └──────────┬──────────┘                            │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                    Public API Only
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│                    AI Sandbox (Advisory)                        │
│                         │                                       │
│  ┌─────────────────────┴─────────────────────┐                 │
│  │                                           │                 │
│  │  ┌─────────────┐    ┌─────────────────┐  │                 │
│  │  │   AI Core   │    │  Vision Engine  │  │                 │
│  │  │ (Rosette)   │    │   (Graphics)    │  │                 │
│  │  └─────────────┘    └─────────────────┘  │                 │
│  │                                           │                 │
│  └───────────────────────────────────────────┘                 │
│                                                                 │
│  _experimental/ai/           _experimental/ai_graphics/         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Our Vision Engine Compliance

### File Locations ✅

| Our File | Location | Zone | Compliant |
|----------|----------|------|-----------|
| `providers.py` | `_experimental/ai_graphics/` | Advisory | ✅ |
| `llm_client.py` | `_experimental/ai_graphics/` | Advisory | ✅ |
| `prompt_engine.py` | `_experimental/ai_graphics/` | Advisory | ✅ |
| `vocabulary.py` | `_experimental/ai_graphics/` | Advisory | ✅ |
| `vision_routes.py` | `_experimental/ai_graphics/api/` | Advisory | ✅ |
| Vue components | `packages/client/` | Frontend | ✅ |

### Import Analysis ✅

Our Vision Engine imports:
```python
# External libraries (OK)
import openai
import requests
from fastapi import APIRouter

# Internal but allowed
from .llm_client import ...  # Within sandbox
from .vocabulary import ...  # Within sandbox
```

**No forbidden imports detected:**
- ❌ No `from app.rmos.*`
- ❌ No `from rmos.workflow`
- ❌ No `from rmos.runs`

### Function Call Analysis ✅

Our Vision Engine calls:
```python
# Image generation (OK - our own code)
engine.generate(prompt)
transport.generate(prompt)

# API requests (OK - public API)
requests.post("/api/...")
```

**No forbidden calls detected:**
- ❌ No `approve()`
- ❌ No `persist_run()`
- ❌ No `generate_toolpaths()`

### Write Path Analysis ✅

Our Vision Engine writes to:
- `_experimental/ai_graphics/outputs/` ✅
- User uploads directory ✅
- Session/cache data ✅

**No forbidden write paths detected:**
- ❌ No writes to `app/rmos/`
- ❌ No writes to `rmos/runs/`

## How RMOS Runs Integrate with Vision Engine

### Workflow for AI-Assisted Design

```
1. User creates design in Vision Engine
   └─> AI generates guitar images
   └─> User selects preferred design
   └─> Design parameters exported

2. Design parameters sent to RMOS
   └─> POST /api/workflow/sessions
   └─> POST /api/workflow/sessions/{id}/context
   
3. RMOS evaluates feasibility
   └─> Authoritative feasibility computed
   └─> Risk bucket assigned (GREEN/YELLOW/RED)

4. Workflow approval (RMOS authority)
   └─> POST /api/workflow/sessions/{id}/approve
   └─> RunArtifact created (approval event)
   └─> Status: OK or BLOCKED

5. Toolpath generation (if approved)
   └─> POST /api/rmos/toolpaths
   └─> RunArtifact created (toolpaths event)
   └─> Attachments stored (geometry, toolpaths, gcode)

6. Audit trail complete
   └─> GET /api/runs → list all artifacts
   └─> GET /api/runs/{id} → full details
   └─> GET /api/runs/diff?a=...&b=... → compare runs
```

### Vision Engine Role in This Flow

The Vision Engine participates in steps 1-2:
- **Generates visual candidates** (AI suggestion)
- **Captures design parameters** (advisory data)
- **Submits to workflow** (via public API)

The Vision Engine does NOT participate in steps 3-6:
- **Does not compute feasibility** (RMOS authority)
- **Does not approve workflows** (RMOS authority)
- **Does not generate toolpaths** (RMOS authority)
- **Does not persist run artifacts** (RMOS authority)

## RMOS Adapter for Vision Engine

We already created `rosette_rmos_adapter.py` which handles the boundary:

```python
# rosette_rmos_adapter.py - Lives in rmos/ (authoritative)

class RosetteRmosAdapter:
    """Bridge between AI rosette generator and RMOS workflow."""
    
    def submit_to_workflow(self, design_params):
        # Creates workflow session
        # Submits AI-suggested parameters
        # Returns session_id for further processing
        pass
    
    def request_feasibility(self, session_id):
        # Requests RMOS feasibility evaluation
        # Returns authoritative risk assessment
        pass
```

This adapter:
- Lives in `rmos/` (authoritative zone)
- Receives data from AI sandbox
- Invokes RMOS authority functions
- Maintains clean boundary

## Recommendations

### 1. Keep Vision Engine in Advisory Zone

Our current placement is correct. No changes needed.

### 2. Use RMOS Adapter Pattern

When Vision Engine output needs RMOS processing:
```python
# In Vision Engine (advisory)
design = generate_design()
response = requests.post("/api/rmos/rosette/submit", json=design)

# In RMOS (authoritative)
# rosette_rmos_adapter.py handles the rest
```

### 3. Avoid Scope Creep

Vision Engine should NEVER:
- Import from `app.rmos.*`
- Call `persist_run()` or `approve()`
- Write to RMOS data directories

### 4. Run CI Checks Regularly

```bash
pre-commit run --all-files
```

## Existing AI Infrastructure

The document also reveals existing AI infrastructure in `_experimental/ai/`:
- `sessions.py` - AI session management
- `api/ai_routes.py` - AI API endpoints
- `api/session_routes.py` - Session API endpoints
- `schemas/ai_schemas.py` - AI schemas
- `services/ai_parameter_suggester.py` - Parameter suggestion
- `services/llm_client.py` - LLM client

### Integration Opportunity

Our Vision Engine's `llm_client.py` has similar purpose to existing `services/llm_client.py`. Consider:
1. **Keeping separate** - Different concerns (images vs text)
2. **Merging later** - Unified transport layer when stable

**Recommendation:** Keep separate for now. Both are in advisory zone and don't violate governance.

## Conclusion

The governance framework from the ChatGPT sessions is comprehensive and well-designed. Our Vision Engine implementation is fully compliant:

| Requirement | Status |
|-------------|--------|
| Code in advisory zone | ✅ |
| No RMOS imports | ✅ |
| No authority calls | ✅ |
| No forbidden writes | ✅ |
| API-only communication | ✅ |

We can proceed with Vision Engine development and deployment with confidence that governance rules are satisfied.
