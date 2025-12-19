# Developer Handoff: RMOS Infrastructure Audit & Implementation Plan

**Date:** December 19, 2025  
**Scope:** RMOS Feasibility Engine, Run Artifacts, Advisory Assets, Database Migrations  
**Status:** 🔴 Critical gaps identified — implementation required

---

## Executive Summary

This audit reveals **significant gaps between documented specifications and actual implementation** in the RMOS (Rosette Manufacturing OS) subsystem. Several components referenced in planning documents and `__init__.py` exports **do not exist**, creating broken import chains and blocking downstream features.

### Critical Findings at a Glance

| Component | Documented Status | Actual Status | Risk Level |
|-----------|-------------------|---------------|------------|
| `BaselineFeasibilityEngineV1` | Referenced in specs | ❌ Does not exist | 🟡 Medium |
| `RunArtifact` schema | Exported in `__init__.py` | ❌ File missing | 🔴 Critical |
| `AdvisoryAsset` schema | Integration spec provided | ❌ Does not exist | 🟡 Medium |
| `advisory_store.py` | Referenced in vision spec | ❌ Does not exist | 🟡 Medium |
| `app/db/migrations/` | Planned for workflow | ❌ Directory missing | 🔴 Critical |
| `.gitignore` anchoring | Should allow `app/db/migrations/` | ❌ Blocks all `migrations/` | 🟠 High |

### Immediate Action Required

1. **Create missing `runs/` module files** — Imports are broken
2. **Fix `.gitignore`** — Currently blocks migration tracking
3. **Implement database migrations** — Required for `WorkflowSession` persistence

---

## Part I: Feasibility System Architecture

### 1.1 Current Implementation (What EXISTS)

The feasibility system uses a **function-based architecture**, not a class-based engine registry pattern.

#### File Locations

| File | Path | Purpose |
|------|------|---------|
| **Fusion Logic** | `services/api/app/rmos/feasibility_fusion.py` | Core `evaluate_feasibility()` function |
| **Router** | `services/api/app/rmos/feasibility_router.py` | FastAPI endpoints |
| **Scorers** | `services/api/app/rmos/feasibility_scorer.py` | Individual risk dimension scorers |
| **Context** | `services/api/app/rmos/context.py` | `RmosContext` class |
| **Presets** | `services/api/app/rmos/presets.py` | `PresetRegistry` (materials, tools) |

#### Function Signature (AUTHORITATIVE)

```python
# File: services/api/app/rmos/feasibility_fusion.py (line 238)

def evaluate_feasibility(
    design: Dict[str, Any],      # NOT "spec"
    context: RmosContext,        # NOT "ctx"
) -> FeasibilityReport:          # Pydantic dataclass, NOT dict
```

> ⚠️ **Parameter Names Matter**: Use `design` and `context`, not `spec` and `ctx`.

#### Return Type Structure

```python
@dataclass
class FeasibilityReport:
    overall_score: float           # 0-100
    overall_risk: RiskLevel        # Enum: GREEN, YELLOW, RED, UNKNOWN
    assessments: List[RiskAssessment]
    recommendations: List[str]
    pass_threshold: float = 70.0
    
    def is_feasible(self) -> bool    # Method, not property
    def needs_review(self) -> bool   # Method, not property
```

#### Router Call Site (Line ~130)

```python
# services/api/app/rmos/feasibility_router.py

context = RmosContext.from_dict(request.context)
report = evaluate_feasibility(request.design, context)

# Response conversion (FeasibilityReport → FeasibilityResponse)
return FeasibilityResponse(
    overall_score=report.overall_score,
    overall_risk=report.overall_risk.value,  # .value extracts enum string
    is_feasible=report.is_feasible(),        # Method call
    needs_review=report.needs_review(),      # Method call
    assessments=assessments_response,
    recommendations=report.recommendations,
    pass_threshold=report.pass_threshold,
)
```

### 1.2 What Does NOT Exist

| Documented Component | Status | Notes |
|---------------------|--------|-------|
| `BaselineFeasibilityEngineV1` | ❌ | No engine class pattern exists |
| `engines/registry.py` | ❌ | Directory doesn't exist |
| `FeasibilityEngine` base class | ❌ | Function-based, not class-based |
| `.compute()` method | ❌ | Use `evaluate_feasibility()` function |

### 1.3 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rmos/feasibility/evaluate` | POST | Evaluate with custom context |
| `/api/rmos/feasibility/evaluate/model/{model_id}` | POST | Evaluate for guitar model |
| `/api/rmos/feasibility/models` | GET | List available models |
| `/api/rmos/feasibility/risk-levels` | GET | List risk level definitions |
| `/api/rmos/feasibility/categories` | GET | List categories with weights |

---

## Part II: Run Artifacts System

### 2.1 Critical Issue: Broken Imports

The `runs/` package exports symbols from **files that don't exist**:

```python
# services/api/app/rmos/runs/__init__.py (CURRENT - BROKEN)

from .schemas import RunArtifact, RunDecision, Hashes, RunOutputs  # ❌ schemas.py missing
from .hashing import sha256_text, sha256_json, ...                  # ❌ hashing.py missing
from .store import RunStore                                         # ❌ store.py missing
```

### 2.2 Files Required

| File | Status | Purpose |
|------|--------|---------|
| `runs/schemas.py` | ❌ Missing | `RunArtifact`, `RunDecision`, `Hashes`, `RunOutputs` |
| `runs/hashing.py` | ❌ Missing | `sha256_text`, `sha256_json`, `sha256_toolpaths_payload`, `summarize_request` |
| `runs/store.py` | ❌ Missing | `RunStore` class for persistence |

### 2.3 Schema Specification (from `rmos_runs_schemas.md`)

```python
class RunArtifact(BaseModel):
    run_id: str
    created_at_utc: datetime
    mode: str                                    # 'fret_slotting', 'rosette', etc.
    tool_id: str
    status: Literal["OK", "BLOCKED", "ERROR"]
    request_summary: Dict[str, Any]
    feasibility: Dict[str, Any]                  # Server-computed
    decision: RunDecision
    hashes: Hashes
    outputs: RunOutputs
    meta: Dict[str, Any]

class Hashes(BaseModel):
    feasibility_sha256: str
    toolpaths_sha256: Optional[str]
    gcode_sha256: Optional[str]
    opplan_sha256: Optional[str]

class RunOutputs(BaseModel):
    gcode_text: Optional[str]
    opplan_json: Optional[Dict[str, Any]]
    gcode_path: Optional[str]
    opplan_path: Optional[str]
    preview_svg_path: Optional[str]

class RunDecision(BaseModel):
    risk_level: str = "UNKNOWN"
    score: Optional[float]
    block_reason: Optional[str]
    warnings: List[str]
    details: Dict[str, Any]
```

---

## Part III: Advisory Assets System

### 3.1 Current State

**`AdvisoryAsset` does NOT exist.** The proposed integration pattern references files that haven't been created.

### 3.2 Proposed Location

```
app/_experimental/ai_graphics/
├── advisory_store.py          # ❌ Does not exist
├── advisory_extensions.py     # ❌ Does not exist
├── schemas/
│   └── advisory_schemas.py    # ❌ Does not exist (ai_schemas.py exists)
└── vision/                    # ❌ Does not exist
    ├── guitar_prompt_engine.py
    ├── guitar_image_providers.py
    └── __init__.py
```

### 3.3 What EXISTS (Closest Equivalents)

| Existing File | Purpose |
|---------------|---------|
| `sessions.py` | `AiSessionState`, `AiSuggestionRecord` |
| `schemas/ai_schemas.py` | `AiRosetteSuggestion`, `RosetteParamSpec` |
| `services/ai_parameter_suggester.py` | LLM-based suggestion generation |

### 3.4 Proposed Integration Pattern

```python
# After image generation (PROPOSED, not implemented)
asset = AdvisoryAsset(
    asset_type=AdvisoryAssetType.IMAGE,
    source="guitar_vision_engine",
    provider="dalle3",
    content_hash=sha256_of_image,
    suggestion_data={"url": result.images[0].url, "prompt": user_prompt},
    approved_for_workflow=False,  # Requires human review
)
advisory_store.save_asset(asset)
```

---

## Part IV: Database Migrations

### 4.1 Current State

| Component | Status |
|-----------|--------|
| `app/db/` directory | ❌ Does not exist |
| `app/db/migrations/` | ❌ Does not exist |
| `0001_init_workflow_sessions.sql` | ❌ Does not exist |
| `0002_add_indexes.sql` | ❌ Does not exist |

### 4.2 Existing Database Infrastructure

The project DOES have SQLite infrastructure:

| File | Purpose |
|------|---------|
| `app/core/rmos_db.py` | `RMOSDatabase` class with connection pooling |
| `app/stores/sqlite_base.py` | Abstract base for SQLite stores |
| `app/stores/sqlite_pattern_store.py` | Pattern persistence |
| `app/stores/sqlite_joblog_store.py` | Job log persistence |

### 4.3 `.gitignore` Issue

**Line 110 is unanchored:**
```gitignore
migrations/        # ❌ Ignores ALL migrations/ directories
```

**Should be:**
```gitignore
/migrations/       # ✅ Only ignores root-level migrations/
```

---

## Part V: FastAPI Application Structure

### 5.1 Import Paths

| Context | Import |
|---------|--------|
| **Tests (`conftest.py`)** | `from app.main import app` |
| **Uvicorn CLI** | `app.main:app` |
| **Working directory** | `services/api/` |

### 5.2 Startup Command

```bash
cd services/api
uvicorn app.main:app --reload --port 8000
```

---

## Appendix A: File Inventory

### A.1 RMOS Directory Structure (Actual)

```
services/api/app/rmos/
├── __init__.py
├── ai_policy.py
├── ai_search.py
├── api/
├── api_ai_routes.py
├── api_ai_snapshots.py
├── api_constraint_profiles.py
├── api_contracts.py
├── api_logs_viewer.py
├── api_presets.py
├── api_profile_history.py
├── api_routes.py
├── constraint_profiles.py
├── context.py
├── context_adapter.py
├── context_router.py
├── feasibility_fusion.py      # ✅ Core feasibility logic
├── feasibility_router.py      # ✅ FastAPI endpoints
├── feasibility_scorer.py      # ✅ Risk scorers
├── fret_cam_guard.py
├── generator_snapshot.py
├── logging_ai.py
├── logging_core.py
├── logs.py
├── messages.py
├── models/
├── models.py
├── policies/
├── presets.py                 # ✅ PresetRegistry
├── profile_history.py
├── runs/
│   └── __init__.py            # ⚠️ Exports broken (missing files)
├── saw_cam_guard.py
├── schemas_ai.py
├── schemas_logs_ai.py
└── services/
```

### A.2 Key Missing Files

```
❌ services/api/app/rmos/runs/schemas.py
❌ services/api/app/rmos/runs/hashing.py
❌ services/api/app/rmos/runs/store.py
❌ services/api/app/rmos/engines/registry.py
❌ services/api/app/db/migrations/0001_init_workflow_sessions.sql
❌ services/api/app/db/migrations/0002_add_indexes.sql
❌ services/api/app/_experimental/ai_graphics/advisory_store.py
❌ services/api/app/_experimental/ai_graphics/schemas/advisory_schemas.py
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **RMOS** | Rosette Manufacturing OS — orchestration layer for CNC operations |
| **RunArtifact** | Immutable record of a CAM run (feasibility + toolpaths + hashes) |
| **FeasibilityReport** | Pydantic dataclass with overall score and risk assessments |
| **RmosContext** | Runtime context including material, tool, and machine parameters |
| **AdvisoryAsset** | (Proposed) Record for AI-generated assets requiring human review |
| **WorkflowSession** | State machine session for multi-step CNC workflows |

---

**Document Version:** 1.0  
**Author:** GitHub Copilot  
**Next Review:** Upon implementation completion
