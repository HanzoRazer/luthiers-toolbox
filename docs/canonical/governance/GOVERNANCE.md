# Governance — AI Sandbox & RMOS Execution Authority

## Purpose

This document defines how AI is integrated safely into RMOS without allowing AI to become an execution authority.

## Roles

### RMOS (Execution Authority)

RMOS:
- computes feasibility and risk
- enforces safety policy
- controls workflow state transitions
- generates toolpaths and manufacturing outputs
- writes immutable run artifacts

### AI Sandbox (Advisory Only)

AI:
- proposes candidates or parameter adjustments
- may request feasibility evaluation via public APIs
- may analyze logs/snapshots/artifacts

AI must **never**:
- approve workflows
- generate toolpaths
- write/modify run artifacts
- bypass server-side feasibility enforcement

## Directory Contract

### Must remain deterministic
- `services/api/app/rmos/**`

### Must remain advisory
- `services/api/app/_experimental/ai/**`
- `services/api/app/_experimental/ai_graphics/**`

### Promotion policy

AI code may be promoted only if it becomes:
- deterministic
- type-safe
- fully test-covered

Promotion target:
- `services/api/app/rmos/assist/**` (never into core execution modules)

## Required Execution Spine

AI suggestions do not grant authority.

Required spine:
```
AI (suggest) → RMOS Feasibility → Workflow APPROVED → RMOS Toolpaths → Run Artifacts
```

## Automated Guards

CI + pre-commit enforce:
- no imports from AI sandbox into `rmos/**`
- no forbidden authority calls from AI sandbox
- no AI write-path patterns into RMOS execution directories

## Forbidden Patterns

### AI Sandbox MUST NOT import:
```python
# These imports are forbidden in _experimental/ai/**
from rmos.workflow import ...
from rmos.toolpaths import ...
from rmos.runs import ...
from rmos.api_workflow import ...
from rmos.api_toolpaths import ...
```

### AI Sandbox MUST NOT call:
```python
# These function calls are forbidden
approve(...)
generate_toolpaths(...)
create_run(...)
persist_run(...)
```

### AI Sandbox MUST NOT write to:
```
app/rmos/**
rmos/runs/**
rmos/toolpaths/**
rmos/workflow/**
```

## Version Stamping

All run artifacts must include:
- `engine_version` - feasibility engine version
- `toolchain_version` - toolpath generator version  
- `post_processor_version` - G-code post-processor version
- `config_fingerprint` - hash of configuration state

This enables deterministic replay and drift detection.

## Drift Detection

Replay endpoints (dev-only) detect when:
- Code changes alter outputs for identical inputs
- Configuration changes affect determinism
- Engine versions produce different results

Drift requires explicit human override to accept forked runs.
