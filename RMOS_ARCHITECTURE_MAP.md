# RMOS System Architecture Map

**Date:** December 19, 2025  
**Purpose:** Developer reference for feature development and integration  
**Scope:** RMOS subsystem architecture, file locations, and extension points

---

## Overview

The RMOS (Rosette Manufacturing OS) system lives within:
```
services/api/app/
```

This document maps all major subsystems, their file locations, and integration points for developing new features.

---

## 1. Feasibility Engine System

The feasibility system evaluates manufacturing safety and risk.

### File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| **Engine Base** | `rmos/engines/base.py` | `FeasibilityEngine` abstract class |
| **Baseline V1** | `rmos/engines/feasibility_baseline_v1.py` | `BaselineFeasibilityEngineV1.compute()` |
| **Stub Engine** | `rmos/engines/feasibility_stub.py` | `StubFeasibilityEngine` for testing |
| **Registry** | `rmos/engines/registry.py` | `EngineRegistry` — single source of truth |
| **Fusion Logic** | `rmos/feasibility_fusion.py` | `evaluate_feasibility(design, context)` |
| **Router** | `rmos/feasibility_router.py` | FastAPI endpoints `/api/rmos/feasibility/*` |
| **Scorer** | `rmos/feasibility_scorer.py` | Individual risk dimension scorers |

### Key Function Signature

```python
# File: rmos/feasibility_fusion.py

def evaluate_feasibility(
    design: Dict[str, Any],      # NOT "spec"
    context: RmosContext,        # NOT "ctx"
) -> FeasibilityReport:          # Pydantic dataclass, NOT dict
```

### Integration Point: Adding a New Feasibility Engine

```python
# 1. Create: rmos/engines/feasibility_my_engine.py
from .base import FeasibilityEngine

class MyFeasibilityEngine(FeasibilityEngine):
    def compute(self, design: Dict, context: RmosContext) -> FeasibilityReport:
        # Your implementation
        pass

# 2. Register in: rmos/engines/registry.py
from .feasibility_my_engine import MyFeasibilityEngine
```

---

## 2. Run Artifacts System

Immutable records of all CAM operations for audit-grade tracking.

### File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| **Schemas** | `rmos/runs/schemas.py` | `RunArtifact`, `RunDecision`, `RunAttachment` |
| **Hashing** | `rmos/runs/hashing.py` | `sha256_text`, `sha256_json`, content hashing |
| **Store** | `rmos/runs/store.py` | `RunStore` — file-based persistence |
| **Diff** | `rmos/runs/diff.py` | Artifact comparison utilities |
| **Attachments** | `rmos/runs/attachments.py` | Content-addressed blob storage |
| **API** | `rmos/runs/api_runs.py` | REST endpoints for run queries |
| **Index** | `rmos/run_artifacts/index.py` | Artifact indexing/search |

### Key Data Structure

```python
# File: rmos/runs/schemas.py

@dataclass
class RunArtifact:
    run_id: str
    created_at_utc: str
    workflow_session_id: Optional[str]
    tool_id: Optional[str]
    material_id: Optional[str]
    machine_id: Optional[str]
    workflow_mode: Optional[str]
    toolchain_id: Optional[str]
    post_processor_id: Optional[str]
    # ... additional fields
```

### Integration Point: Adding New Artifact Fields

```python
# 1. Extend: rmos/runs/schemas.py → RunArtifact dataclass
@dataclass
class RunArtifact:
    # ... existing fields ...
    my_new_field: Optional[str] = None  # Add here

# 2. Update: rmos/runs/hashing.py if field needs hashing
# 3. Update: rmos/runs/store.py for persistence logic
```

---

## 3. Advisory Assets System (AI-Generated Content)

Separate trust boundary for AI-generated content requiring human approval.

### File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| **Schemas** | `_experimental/ai_graphics/schemas/advisory_schemas.py` | `AdvisoryAsset`, `AdvisoryAssetType` |
| **Store** | `_experimental/ai_graphics/advisory_store.py` | `AdvisoryAssetStore` |
| **Image Providers** | `_experimental/ai_graphics/image_providers.py` | `GuitarVisionEngine` |
| **Prompt Engine** | `_experimental/ai_graphics/prompt_engine.py` | LLM prompt construction |
| **Sessions** | `_experimental/ai_graphics/sessions.py` | `AiSessionState`, deduplication |
| **Vocabulary** | `_experimental/ai_graphics/vocabulary.py` | Domain-specific terms |

### Key Store Pattern

```python
# File: _experimental/ai_graphics/advisory_store.py

class AdvisoryAssetStore:
    """
    GOVERNANCE: This store is SEPARATE from RunStore.
    AI can write here, but cannot write to run_artifacts.
    """
    
    def save_asset(self, asset: AdvisoryAsset) -> AdvisoryAsset: ...
    def get_asset(self, asset_id: str) -> Optional[AdvisoryAsset]: ...
    def list_assets(self, **filters) -> List[AdvisoryAsset]: ...
```

### Integration Point: Adding New AI Asset Types

```python
# 1. Add enum value: schemas/advisory_schemas.py
class AdvisoryAssetType(str, Enum):
    IMAGE = "IMAGE"
    EXPLANATION = "EXPLANATION"
    MY_NEW_TYPE = "MY_NEW_TYPE"  # Add here

# 2. Create provider: my_provider.py
class MyProvider:
    def generate(self, prompt: str) -> MyResult:
        pass

# 3. Store result
asset = AdvisoryAsset(
    asset_type=AdvisoryAssetType.MY_NEW_TYPE,
    source="my_provider",
    provider="my_backend",
    content_hash=compute_content_hash(content),
    suggestion_data={"result": result},
    approved_for_workflow=False,  # Requires human review
)
advisory_store.save_asset(asset)
```

---

## 4. Database & Persistence Layer

SQLite-based persistence with connection pooling.

### File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| **Core DB** | `core/rmos_db.py` | `RMOSDatabase` — connection manager |
| **Store Base** | `stores/sqlite_base.py` | `SQLiteStoreBase` — abstract CRUD |
| **Pattern Store** | `stores/sqlite_pattern_store.py` | Rosette pattern persistence |
| **JobLog Store** | `stores/sqlite_joblog_store.py` | Manufacturing job records |
| **Strip Family** | `stores/sqlite_strip_family_store.py` | Material strip configs |
| **Aggregation** | `stores/rmos_stores.py` | Store factory/aggregation |

### Database Location
```
services/api/data/rmos.db
```

### Integration Point: Adding New Persistent Entities

```python
# 1. Add migration: db/migrations/000X_new_table.sql
CREATE TABLE IF NOT EXISTS my_entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

# 2. Create store: stores/sqlite_my_store.py
from .sqlite_base import SQLiteStoreBase

class MyEntityStore(SQLiteStoreBase):
    @property
    def table_name(self) -> str:
        return "my_entities"
    
    @property
    def id_field(self) -> str:
        return "id"

# 3. Register in stores/__init__.py or rmos_stores.py
```

---

## 5. Context & Presets System

Runtime context and configuration presets.

### File Locations

| Component | Path | Purpose |
|-----------|------|---------|
| **Context** | `rmos/context.py` | `RmosContext` — runtime context |
| **Context Adapter** | `rmos/context_adapter.py` | Model → Context conversion |
| **Presets** | `rmos/presets.py` | `PresetRegistry` — materials, tools |
| **Constraint Profiles** | `rmos/constraint_profiles.py` | Safety constraints |
| **API Presets** | `rmos/api_presets.py` | REST endpoints for presets |

### Key Pattern

```python
# File: rmos/context.py

class RmosContext:
    @classmethod
    def from_model_id(cls, model_id: str) -> "RmosContext":
        """Create context from guitar model ID."""
        pass
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RmosContext":
        """Deserialize from dict."""
        pass
```

---

## 6. System Integration Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        RMOS SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Context    │────▶│  Feasibility │────▶│ Run Artifact │    │
│  │   Builder    │     │    Engine    │     │    Store     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Presets    │     │   Engine     │     │   Hashing    │    │
│  │   Registry   │     │   Registry   │     │   Utils      │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                              │                                  │
│                              │                                  │
│                              ▼                                  │
│                       ┌──────────────┐                         │
│                       │   SQLite     │                         │
│                       │   Database   │                         │
│                       └──────────────┘                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ADVISORY ZONE (Trust Boundary)               │  │
│  │  ┌──────────────┐     ┌──────────────┐                   │  │
│  │  │   Vision     │────▶│   Advisory   │                   │  │
│  │  │   Engine     │     │    Store     │ (separate from    │  │
│  │  └──────────────┘     └──────────────┘  Run Artifacts)   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Quick Reference: Where to Add Features

| Feature Type | Primary Location | Supporting Files |
|--------------|-----------------|------------------|
| **New feasibility check** | `rmos/engines/` | `feasibility_fusion.py`, `registry.py` |
| **New run artifact field** | `rmos/runs/schemas.py` | `hashing.py`, `store.py` |
| **New AI asset type** | `_experimental/ai_graphics/schemas/` | `advisory_store.py` |
| **New database table** | `db/migrations/` | `stores/sqlite_*.py` |
| **New API endpoint** | `rmos/api_*.py` | Corresponding service |
| **New preset type** | `rmos/presets.py` | `api_presets.py` |
| **New workflow mode** | `rmos/models.py` | `context.py`, guards |

---

## 8. Key Import Statements

```python
# Feasibility Engine
from app.rmos.engines.base import FeasibilityEngine
from app.rmos.engines.registry import get_engine_registry
from app.rmos.feasibility_fusion import evaluate_feasibility

# Run Artifacts
from app.rmos.runs.schemas import RunArtifact, RunDecision
from app.rmos.runs.store import RunStore
from app.rmos.runs.hashing import sha256_json, sha256_text

# Advisory Assets
from app._experimental.ai_graphics.advisory_store import AdvisoryAssetStore
from app._experimental.ai_graphics.schemas.advisory_schemas import (
    AdvisoryAsset, 
    AdvisoryAssetType
)

# Database
from app.core.rmos_db import get_rmos_db, RMOSDatabase
from app.stores.sqlite_base import SQLiteStoreBase

# Context
from app.rmos.context import RmosContext
from app.rmos.presets import get_preset_registry, PresetRegistry
```

---

## 9. API Endpoints Reference

### Feasibility Endpoints
| Endpoint | Method | Handler |
|----------|--------|---------|
| `/api/rmos/feasibility/evaluate` | POST | `feasibility_router.py` |
| `/api/rmos/feasibility/evaluate/model/{model_id}` | POST | `feasibility_router.py` |
| `/api/rmos/feasibility/models` | GET | `feasibility_router.py` |
| `/api/rmos/feasibility/risk-levels` | GET | `feasibility_router.py` |
| `/api/rmos/feasibility/categories` | GET | `feasibility_router.py` |

### Run Artifact Endpoints
| Endpoint | Method | Handler |
|----------|--------|---------|
| `/api/rmos/runs` | GET | `runs/api_runs.py` |
| `/api/rmos/runs/{run_id}` | GET | `runs/api_runs.py` |

### Preset Endpoints
| Endpoint | Method | Handler |
|----------|--------|---------|
| `/api/rmos/presets/materials` | GET | `api_presets.py` |
| `/api/rmos/presets/tools` | GET | `api_presets.py` |

---

## 10. Testing Imports

```bash
# From services/api/ directory

# Test feasibility imports
python -c "from app.rmos.engines.registry import EngineRegistry; print('✅ Engine Registry OK')"

# Test run artifact imports
python -c "from app.rmos.runs import RunArtifact, RunStore; print('✅ Run Artifacts OK')"

# Test advisory imports  
python -c "from app._experimental.ai_graphics.advisory_store import AdvisoryAssetStore; print('✅ Advisory Store OK')"

# Test database imports
python -c "from app.core.rmos_db import get_rmos_db; print('✅ Database OK')"
```

---

**Document Version:** 1.0  
**Last Updated:** December 19, 2025
