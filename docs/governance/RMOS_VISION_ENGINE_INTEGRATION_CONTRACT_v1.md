# RMOS Vision Engine Integration Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 16, 2025
**Status:** AUTHORITATIVE
**Source:** Vision Engine Bundle - INTEGRATION_GUIDE.md

---

## Governance Statement

This document establishes the **canonical integration contract** for the RMOS Governance and AI Vision Engine subsystems within the Luthier's ToolBox platform. All integrations MUST conform to the specifications herein. This contract ensures AI remains **advisory** while RMOS maintains **execution authority**.

### Governing Principles

1. **Separation of Authority** — AI advises, RMOS executes
2. **API-Only Communication** — AI sandbox uses public APIs, never internal imports
3. **Deterministic Execution** — RMOS operations produce reproducible results
4. **Audit-Grade Tracking** — All decisions are recorded immutably
5. **Automated Enforcement** — CI and pre-commit hooks enforce boundaries

---

## Quick Start Integration

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

**File:** `services/api/app/main.py`

```python
from app.rmos.runs.api_runs import router as runs_router

app.include_router(runs_router, prefix="/api")
```

---

## Bundle Architecture

### Governance Documents

| File | Purpose | Authority |
|------|---------|-----------|
| `SECURITY.md` | Security policy and trust boundaries | CANONICAL |
| `GOVERNANCE.md` | AI sandbox rules and promotion policy | CANONICAL |
| `AI_SANDBOX_GOVERNANCE.md` | Detailed sandbox enforcement rules | CANONICAL |

### CI Enforcement Scripts

| Script | Purpose | Failure Mode |
|--------|---------|--------------|
| `check_ai_import_boundaries.py` | Fails if RMOS imports AI sandbox code | HARD FAIL |
| `check_ai_forbidden_calls.py` | Fails if AI calls authority functions | HARD FAIL |
| `check_ai_write_paths.py` | Fails if AI writes to RMOS directories | HARD FAIL |

### RMOS Core Modules

| Module | Purpose | Authority Level |
|--------|---------|-----------------|
| `runs/schemas.py` | RunArtifact dataclass | AUTHORITATIVE |
| `runs/store.py` | Artifact persistence | AUTHORITATIVE |
| `runs/hashing.py` | Deterministic hashing | AUTHORITATIVE |
| `runs/attachments.py` | Content-addressed storage | AUTHORITATIVE |
| `runs/diff.py` | Run comparison engine | AUTHORITATIVE |
| `runs/api_runs.py` | FastAPI endpoints | AUTHORITATIVE |
| `engines/registry.py` | Version registry | AUTHORITATIVE |
| `gates/policy.py` | Replay drift policy | AUTHORITATIVE |

---

## API Endpoints Contract

### Runs API (RMOS Authoritative)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/runs` | List runs with filters | Yes |
| GET | `/api/runs/{id}` | Get run details | Yes |
| GET | `/api/runs/diff?a=...&b=...` | Diff two runs | Yes |
| GET | `/api/runs/{id}/attachments` | List attachments | Yes |
| GET | `/api/runs/{id}/attachments/{sha}` | Download attachment | Yes |
| GET | `/api/runs/{id}/attachments/verify` | Verify integrity | Yes |

---

## AI Sandbox Integration Rules

### PERMITTED Actions (AI Vision Engine)

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

### FORBIDDEN Actions (AI Vision Engine)

```python
# ❌ Import RMOS internals
from app.rmos.runs.store import persist_run  # FORBIDDEN

# ❌ Call authority functions
approve_workflow_session(session_id)  # FORBIDDEN
generate_toolpaths(geometry)  # FORBIDDEN

# ❌ Write to RMOS paths
open("app/rmos/runs/data.json", "w")  # FORBIDDEN
```

---

## Directory Structure Contract

```
services/api/app/
├── rmos/                          # AUTHORITATIVE ZONE
│   ├── runs/
│   │   ├── schemas.py             # RunArtifact definition
│   │   ├── store.py               # Persistence layer
│   │   ├── hashing.py             # Deterministic hashing
│   │   ├── attachments.py         # Content-addressed storage
│   │   ├── diff.py                # Comparison engine
│   │   └── api_runs.py            # REST endpoints
│   ├── engines/
│   │   └── registry.py            # Version registry
│   ├── gates/
│   │   └── policy.py              # Replay drift policy
│   ├── workflow/                  # (existing)
│   ├── toolpaths/                 # (existing)
│   └── feasibility/               # (existing)
│
├── _experimental/                 # ADVISORY ZONE
│   ├── ai/                        # AI parameter suggestion
│   └── ai_graphics/               # Vision engine
│       ├── llm_client.py          # Transport layer
│       ├── providers.py           # Provider adapters
│       ├── prompt_engine.py       # Prompt engineering
│       ├── vocabulary.py          # Domain vocabulary
│       └── api/
│           └── vision_routes.py   # Vision API routes
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

---

## Environment Variables Contract

### RMOS Configuration (Required)

```bash
# Run artifact storage
RMOS_RUN_STORE_PATH=services/api/app/data/runs.json
RMOS_RUN_ATTACHMENTS_DIR=services/api/app/data/run_attachments

# Replay (dev-only)
ENABLE_RMOS_REPLAY=false
RMOS_REPLAY_GATE_MODE=block
RMOS_REPLAY_GATE_REQUIRE_NOTE=true
```

### AI Sandbox Configuration (Optional)

```bash
# Image generation
OPENAI_API_KEY=sk-...
SD_API_URL=http://localhost:7860
GUITAR_LORA_NAME=guitar_v1
```

---

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

---

## Compliance Requirements

### MUST (Mandatory)

| ID | Requirement |
|----|-------------|
| I1 | All RMOS modules MUST be in `app/rmos/` directory |
| I2 | All AI modules MUST be in `app/_experimental/` directory |
| I3 | CI enforcement scripts MUST run on every PR |
| I4 | Pre-commit hooks MUST be installed for local development |
| I5 | API endpoints MUST follow the documented paths |

### MUST NOT (Prohibited)

| ID | Prohibition |
|----|-------------|
| I6 | AI code MUST NOT import from `app.rmos.*` |
| I7 | AI code MUST NOT call authority functions directly |
| I8 | AI code MUST NOT write to RMOS directories |
| I9 | CI bypass flags MUST NOT be added |

---

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

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-16 | Claude Opus 4.5 | Initial canonical specification |

---

## Amendment Process

Changes to this contract require:

1. **Proposal** — Written specification of proposed change
2. **Impact Analysis** — Assessment of breaking changes
3. **Review** — Technical review by maintainers
4. **Approval** — Sign-off from project lead
5. **Version Increment** — Update version and history

---

*This document is the authoritative specification for RMOS Vision Engine integration.*
*Non-conforming implementations are considered defects.*
