# RMOS Governance & AI Sandbox Integration Guide

## Overview

This bundle provides a complete governance framework for the Luthier's ToolBox, ensuring AI remains **advisory** while RMOS maintains **execution authority**.

## Quick Start

### 1. Install Pre-commit Hooks (Local Enforcement)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 2. Run CI Checks Manually

```bash
python ci/ai_sandbox/check_ai_import_boundaries.py
python ci/ai_sandbox/check_ai_forbidden_calls.py
python ci/ai_sandbox/check_ai_write_paths.py
```

### 3. Wire RMOS Runs API

In `services/api/app/main.py`:

```python
from app.rmos.runs.api_runs import router as runs_router

app.include_router(runs_router, prefix="/api")
```

## Bundle Contents

### Governance Documents (`docs/`)

| File | Purpose |
|------|---------|
| `SECURITY.md` | Security policy and trust boundaries |
| `GOVERNANCE.md` | AI sandbox rules and promotion policy |
| `AI_SANDBOX_GOVERNANCE.md` | Detailed sandbox enforcement rules |

### CI Enforcement (`ci/ai_sandbox/`)

| Script | Purpose |
|--------|---------|
| `check_ai_import_boundaries.py` | Fails if RMOS imports AI sandbox code |
| `check_ai_forbidden_calls.py` | Fails if AI calls authority functions |
| `check_ai_write_paths.py` | Fails if AI writes to RMOS directories |

### RMOS Core (`rmos/`)

| Module | Purpose |
|--------|---------|
| `runs/schemas.py` | RunArtifact dataclass |
| `runs/store.py` | Artifact persistence |
| `runs/hashing.py` | Deterministic hashing |
| `runs/attachments.py` | Content-addressed storage |
| `runs/diff.py` | Run comparison engine |
| `runs/api_runs.py` | FastAPI endpoints |
| `engines/registry.py` | Version registry |
| `gates/policy.py` | Replay drift policy |

## API Endpoints

### Runs API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/runs` | List runs with filters |
| GET | `/api/runs/{id}` | Get run details |
| GET | `/api/runs/diff?a=...&b=...` | Diff two runs |
| GET | `/api/runs/{id}/attachments` | List attachments |
| GET | `/api/runs/{id}/attachments/{sha}` | Download attachment |
| GET | `/api/runs/{id}/attachments/verify` | Verify integrity |

## Integration with AI Sandbox

### What AI Vision Engine CAN Do

```python
# In _experimental/ai_graphics/

# ✅ Generate images
result = await generate_guitar_image(prompt)

# ✅ Store images in AI sandbox
save_to_path("_experimental/ai_graphics/outputs/", image)

# ✅ Request feasibility via API
response = requests.post("/api/rmos/feasibility", json=params)

# ✅ Read run artifacts for analysis
run = requests.get("/api/runs/run_123").json()
```

### What AI Vision Engine CANNOT Do

```python
# ❌ Import RMOS internals
from app.rmos.runs.store import persist_run  # FORBIDDEN

# ❌ Call authority functions
approve_workflow_session(session_id)  # FORBIDDEN
generate_toolpaths(geometry)  # FORBIDDEN

# ❌ Write to RMOS paths
open("app/rmos/runs/data.json", "w")  # FORBIDDEN
```

## Directory Structure

```
services/api/app/
├── rmos/                          # AUTHORITATIVE ZONE
│   ├── runs/
│   │   ├── schemas.py
│   │   ├── store.py
│   │   ├── hashing.py
│   │   ├── attachments.py
│   │   ├── diff.py
│   │   └── api_runs.py
│   ├── engines/
│   │   └── registry.py
│   ├── gates/
│   │   └── policy.py
│   ├── workflow/                  # (existing)
│   ├── toolpaths/                 # (existing)
│   └── feasibility/               # (existing)
│
├── _experimental/                 # ADVISORY ZONE
│   ├── ai/                        # AI parameter suggestion
│   └── ai_graphics/               # Vision engine (our work)
│       ├── llm_client.py
│       ├── providers.py
│       ├── prompt_engine.py
│       ├── vocabulary.py
│       └── api/
│           └── vision_routes.py
│
└── routers/                       # Thin wiring only
    └── ...

ci/
└── ai_sandbox/
    ├── check_ai_import_boundaries.py
    ├── check_ai_forbidden_calls.py
    └── check_ai_write_paths.py

.github/
└── workflows/
    └── ai_sandbox_enforcement.yml
```

## Environment Variables

### RMOS Configuration

```bash
# Run artifact storage
RMOS_RUN_STORE_PATH=services/api/app/data/runs.json
RMOS_RUN_ATTACHMENTS_DIR=services/api/app/data/run_attachments

# Replay (dev-only)
ENABLE_RMOS_REPLAY=false
RMOS_REPLAY_GATE_MODE=block
RMOS_REPLAY_GATE_REQUIRE_NOTE=true
```

### AI Sandbox Configuration

```bash
# Image generation
OPENAI_API_KEY=sk-...
SD_API_URL=http://localhost:7860
GUITAR_LORA_NAME=guitar_v1
```

## Integration Checklist

### For AI Vision Engine

- [ ] All code in `_experimental/ai_graphics/`
- [ ] No imports from `app.rmos.*`
- [ ] No calls to `approve()`, `persist_run()`, etc.
- [ ] Use public APIs for RMOS services
- [ ] CI checks pass

### For RMOS Integration

- [ ] Wire `runs_router` in main.py
- [ ] Create data directories
- [ ] Configure environment variables
- [ ] Run integration tests

## Testing

### Run Governance Checks

```bash
# All checks
pre-commit run --all-files

# Individual checks
python ci/ai_sandbox/check_ai_import_boundaries.py
python ci/ai_sandbox/check_ai_forbidden_calls.py
python ci/ai_sandbox/check_ai_write_paths.py
```

### Run RMOS Tests

```bash
pytest tests/test_runs_api.py
pytest tests/test_runs_diff_api.py
pytest tests/test_runs_attachments_api.py
```

## Troubleshooting

### CI Fails with Import Boundary Violation

**Problem:** RMOS code imports from AI sandbox.

**Solution:** Remove the import. AI code must communicate via APIs only.

### CI Fails with Forbidden Call

**Problem:** AI code calls authority function.

**Solution:** Use public API endpoint instead:

```python
# Instead of:
from app.rmos.feasibility import score_design_feasibility
result = score_design_feasibility(params)

# Do:
response = requests.post("/api/rmos/feasibility", json=params)
result = response.json()
```

### CI Fails with Write Path Violation

**Problem:** AI code writes to RMOS directory.

**Solution:** Write to AI sandbox directory instead:

```python
# Instead of:
open("app/rmos/data/output.json", "w")

# Do:
open("_experimental/ai_graphics/outputs/output.json", "w")
```

## Next Steps

1. **Deploy CI workflow** - Copy `.github/workflows/ai_sandbox_enforcement.yml`
2. **Install pre-commit** - Run `pre-commit install`
3. **Wire RMOS API** - Add router to main.py
4. **Verify integration** - Run all governance checks
5. **Continue Vision Engine** - Safe to proceed with AI features
