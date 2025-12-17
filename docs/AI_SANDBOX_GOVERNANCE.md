# AI Sandbox Governance v2.0

## Summary

This document defines the trust boundaries and enforcement rules for AI code in the Luthier's ToolBox. AI operates in a sandbox with strict limitations to prevent it from becoming an execution authority.

## Trust Boundary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     AUTHORITATIVE ZONE                          │
│                   (Execution Authority)                         │
│                                                                 │
│  services/api/app/rmos/                                         │
│  ├── workflow/        # State machine control                   │
│  ├── toolpaths/       # G-code generation                       │
│  ├── runs/            # Immutable artifact storage              │
│  ├── feasibility/     # Risk/safety scoring                     │
│  ├── engines/         # Version registry                        │
│  └── gates/           # Policy enforcement                      │
│                                                                 │
│  POWERS: approve, generate_toolpaths, persist_run               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Public API only
                              │ (no direct imports)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ADVISORY ZONE                              │
│                    (AI Sandbox)                                 │
│                                                                 │
│  services/api/app/_experimental/                                │
│  ├── ai/              # Parameter suggestion, analysis          │
│  └── ai_graphics/     # Image generation, prompt engineering    │
│                                                                 │
│  POWERS: suggest, analyze, generate images                      │
│  FORBIDDEN: approve, toolpaths, persist artifacts               │
└─────────────────────────────────────────────────────────────────┘
```

## Enforcement Rules

### Rule 1: Import Boundary
**❌ No imports from `_experimental/ai*` into `app/rmos/**`**

RMOS must never depend on AI code. AI code is volatile, experimental, and non-deterministic.

### Rule 2: Forbidden Calls
**❌ No AI code calling authority APIs**

AI sandbox code must not call:
- `approve()` - workflow approval
- `generate_toolpaths()` - manufacturing output
- `create_run()` / `persist_run()` - artifact storage

### Rule 3: Write Path Restrictions
**❌ No AI code writing to RMOS directories**

AI sandbox must not write files to:
- `app/rmos/**`
- `rmos/runs/**`
- `rmos/toolpaths/**`
- `rmos/workflow/**`

### Rule 4: API-Only Communication
**✅ AI must use public APIs to request RMOS services**

```python
# CORRECT: AI requests feasibility via API
response = requests.post("/api/rmos/feasibility", json=params)

# WRONG: AI imports RMOS internals
from app.rmos.feasibility import score_design_feasibility  # FORBIDDEN
```

## What AI CAN Do

| Action | Allowed | Notes |
|--------|---------|-------|
| Suggest parameters | ✅ | Via API or return values |
| Generate images | ✅ | Store in _experimental or user uploads |
| Analyze designs | ✅ | Read-only access to design data |
| Request feasibility | ✅ | Via public API endpoints |
| Log suggestions | ✅ | To AI-specific log paths |
| Read run artifacts | ✅ | For analysis purposes |

## What AI CANNOT Do

| Action | Forbidden | Reason |
|--------|-----------|--------|
| Approve workflows | ❌ | Execution authority |
| Generate toolpaths | ❌ | Manufacturing output |
| Persist run artifacts | ❌ | Audit integrity |
| Bypass feasibility | ❌ | Safety requirement |
| Import RMOS internals | ❌ | Coupling prevention |
| Write to RMOS paths | ❌ | Boundary enforcement |

## CI Enforcement

These rules are enforced by CI scripts that run on every PR:

```yaml
# .github/workflows/ai_sandbox_enforcement.yml
- check_ai_import_boundaries.py    # Rule 1
- check_ai_forbidden_calls.py      # Rule 2
- check_ai_write_paths.py          # Rule 3
```

Violations **fail CI immediately**. No exceptions. No bypass flags.

## Pre-commit Hooks

Developers can catch violations before pushing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Integration Pattern for AI Features

When building AI features that need RMOS services:

```python
# In _experimental/ai_graphics/some_feature.py

class AIFeature:
    def suggest_parameters(self, design):
        """AI suggests parameters (advisory)"""
        # Do AI magic
        return suggested_params  # Just data, no authority
    
    def request_feasibility(self, params):
        """Request RMOS to evaluate feasibility (via API)"""
        # Call public API - DO NOT import RMOS
        response = requests.post(
            f"{API_BASE}/api/rmos/feasibility",
            json=params
        )
        return response.json()
```

## Promotion Path

AI code can be promoted to production (`rmos/assist/`) only if:

1. It becomes **deterministic** (same inputs → same outputs)
2. It is **type-safe** (full Pydantic/typing coverage)
3. It has **100% test coverage**
4. It passes **contract tests** (golden file matching)
5. It is reviewed and approved by maintainers

Promoted code goes to `rmos/assist/`, never to core execution modules.
