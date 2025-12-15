# AI System Rehabilitation — Surgical Plan

**Date:** December 14, 2025  
**Status:** Phase B + C Complete, Phase D/E/F Pending  
**Branch:** `feature/client-migration`  
**Last Updated:** December 15, 2025

---

## Executive Summary

The AI subsystem verification is complete. **No conflation detected** between AI/RMOS and Temperament domains. The existing code is architecturally sound.

**Progress Update:**
- ✅ **Phase A**: Stabilize — Ready to commit
- ✅ **Phase B**: RMOS AI Search Loop — **COMPLETE**
- ✅ **Phase C**: Profile Management — **COMPLETE**
- ⏳ **Phase D**: Analytics — Pending
- ⏳ **Phase E**: Frontend — Pending
- ⏳ **Phase F**: Real AI Integration — Pending

---

## Part 1: Current State Assessment

### ✅ VERIFIED CLEAN — Ready to Commit

| Component | Location | Status | Domain |
|-----------|----------|--------|--------|
| `ai_core/__init__.py` | `services/api/app/ai_core/` | ✅ Clean | AI package exports |
| `ai_core/clients.py` | `services/api/app/ai_core/` | ✅ Clean | AI client abstraction (stub pattern) |
| `ai_core/safety.py` | `services/api/app/ai_core/` | ✅ Clean | Output validation, coerce → RosetteParamSpec |
| `ai_core/generators.py` | `services/api/app/ai_core/` | ✅ Clean | Candidate generator factory for RMOS |
| `ai_core/generator_constraints.py` | `services/api/app/ai_core/` | ✅ Clean | RMOS constraint adapter |
| `ai_core/structured_generator.py` | `services/api/app/ai_core/` | ✅ Clean | Constraint-aware generation |
| `alternative_temperaments.py` | `services/api/app/calculators/` | ✅ Clean | PFS fret math (separate domain) |
| `temperament_router.py` | `services/api/app/routers/` | ✅ Wired | `/api/smart-guitar/temperaments` |

### 🗑️ ORPHANS — To Delete or Ignore

| File | Location | Action |
|------|----------|--------|
| `ai_core_generator_constraints.py` | Root level | Delete (conversation dump, not code) |

---

## Part 2: Gap Analysis — Designed vs. Implemented

### From ChatGPT Transcript (December 13, 2025)

| Component | Designed | Implemented | Gap |
|-----------|----------|-------------|-----|
| **CAD Package** | | | |
| `cad/__init__.py` | ✅ | ✅ | None |
| `cad/exceptions.py` | ✅ | ✅ | None |
| `cad/geometry_models.py` | ✅ | ✅ | None |
| `cad/dxf_layers.py` | ✅ | ✅ | None |
| `cad/dxf_validators.py` | ✅ | ✅ | None |
| `cad/dxf_engine.py` | ✅ | ✅ | None |
| `cad/offset_engine.py` | ✅ | ✅ | None |
| `cad/api/dxf_routes.py` | ✅ | ✅ | None |
| `cad/schemas/dxf_export.py` | ✅ | ✅ | None |
| **AI Core Package** | | | |
| `ai_core/__init__.py` | ✅ | ✅ | None |
| `ai_core/clients.py` | ✅ | ✅ | None |
| `ai_core/safety.py` | ✅ | ✅ | None |
| `ai_core/generators.py` | ✅ | ✅ | None |
| `ai_core/generator_constraints.py` | ✅ | ✅ | None |
| `ai_core/structured_generator.py` | ✅ | ✅ | None |
| **RMOS AI Extensions (Phase B)** | | | |
| `rmos/schemas_ai.py` | ✅ | ✅ | **COMPLETE** |
| `rmos/ai_search.py` | ✅ | ✅ | **COMPLETE** |
| `rmos/logging_ai.py` | ✅ | ✅ | Existed + integrated |
| `rmos/api_ai_routes.py` | ✅ | ✅ | **COMPLETE** |
| **Profile Management (Phase C)** | | | |
| `rmos/constraint_profiles.py` | ✅ | ✅ | **COMPLETE** |
| `rmos/profile_history.py` | ✅ | ✅ | **COMPLETE** |
| `rmos/api_constraint_profiles.py` | ✅ | ✅ | **COMPLETE** |
| `rmos/api_profile_history.py` | ✅ | ✅ | **COMPLETE** |
| `config/rmos_constraint_profiles.yaml` | ✅ | ✅ | **COMPLETE** (14 profiles) |
| **Analytics (Phase D)** | | | |
| `rmos/ai_analytics.py` | ✅ | ❌ | **Pending** |
| `rmos/api_ai_analytics.py` | ✅ | ❌ | **Pending** |
| `rmos/api_ai_snapshots.py` | ✅ | ⚠️ | Partial |
| **Frontend Components (Phase E)** | | | |
| `RmosAiLogViewer.vue` | ✅ | ❌ | **Pending** |
| `RmosAiSnapshotInspector.vue` | ✅ | ❌ | **Pending** |
| `RmosAiProfilePerformance.vue` | ✅ | ❌ | **Pending** |
| `RmosAiProfileEditor.vue` | ✅ | ❌ | **Pending** |
| `RmosAiOpsDashboard.vue` | ✅ | ❌ | **Pending** |

---

## Part 3: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LUTHIER'S TOOLBOX AI SYSTEM                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   FRONTEND      │     │   AI CORE       │     │   RMOS          │
│   (Vue 3)       │     │   (Python)      │     │   (Python)      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│                 │     │                 │     │                 │
│ RmosAiOps       │────▶│ clients.py      │────▶│ ai_search.py    │
│ Dashboard.vue   │     │ ├─NullAiClient  │     │ └─run_constraint│
│ [PHASE E]       │     │ └─OpenAIClient  │     │   _first_search │
│                 │     │   [STUB]        │     │   [✅ IMPL]     │
│ RmosAiLog       │     │                 │     │                 │
│ Viewer.vue      │────▶│ safety.py       │────▶│ logging_ai.py   │
│ [PHASE E]       │     │ └─coerce_to_    │     │ └─log_ai_       │
│                 │     │   rosette_spec  │     │   constraint_   │
│ RmosAiProfile   │     │   [✅ IMPL]     │     │   attempt       │
│ Editor.vue      │────▶│                 │     │   [✅ IMPL]     │
│ [PHASE E]       │     │ generators.py   │     │                 │
│                 │     │ └─make_cand_    │────▶│ feasibility_    │
│ RmosAiSnapshot  │     │   generator_    │     │ scorer.py       │
│ Inspector.vue   │     │   for_request   │     │ [✅ IMPL]       │
│ [PHASE E]       │     │   [✅ IMPL]     │     │                 │
└─────────────────┘     │                 │     │ api_ai_routes.py│
                        │ structured_     │     │ [✅ IMPL]       │
                        │ generator.py    │     │                 │
                        │ [✅ IMPL]       │     │ constraint_     │
                        │                 │     │ profiles.py     │
                        │ generator_      │     │ [✅ IMPL]       │
                        │ constraints.py  │     │                 │
                        │ [✅ IMPL]       │     │ api_constraint_ │
                        └─────────────────┘     │ profiles.py     │
                                │               │ [✅ IMPL]       │
                                ▼               └─────────────────┘
                        ┌─────────────────┐             │
                        │   CAD ENGINE    │             ▼
                        │   (Python)      │     ┌─────────────────┐
                        ├─────────────────┤     │   CONFIG        │
                        │                 │     │   (YAML/JSONL)  │
                        │ dxf_engine.py   │     ├─────────────────┤
                        │ [✅ IMPL]       │     │                 │
                        │                 │     │ rmos_constraint_│
                        │ geometry_       │     │ profiles.yaml   │
                        │ models.py       │     │ [✅ IMPL]       │
                        │ [✅ IMPL]       │     │ (14 profiles)   │
                        │                 │     │                 │
                        │ offset_engine.py│     │ profile_history │
                        │ [✅ IMPL]       │     │ .jsonl          │
                        │                 │     │ [✅ IMPL]       │
                        └─────────────────┘     └─────────────────┘
```

---

## Part 4: Rehabilitation Phases

### ✅ Phase A: Stabilize (Current Sprint)

**Objective:** Commit existing clean code, fix CI  
**Status:** Ready to execute

| Task | Files | Action | Status |
|------|-------|--------|--------|
| A1 | `services/api/app/ai_core/*` | Commit as part of migration | ⏳ Ready |
| A2 | `services/api/app/cad/*` | Commit as part of migration | ⏳ Ready |
| A3 | `services/api/app/calculators/alternative_temperaments.py` | Commit as part of migration | ⏳ Ready |
| A4 | Root `ai_core_generator_constraints.py` | Delete or .gitignore | ⏳ Ready |
| A5 | Verify router wiring in `main.py` | Confirm CAD routes registered | ⏳ Ready |

---

### ✅ Phase B: RMOS AI Search Loop — COMPLETE

**Objective:** Implement constraint-first search with logging  
**Status:** ✅ COMPLETE

| Task | File | Description | Status |
|------|------|-------------|--------|
| B1 | `rmos/schemas_ai.py` | Pydantic models for AI search requests/responses | ✅ Done |
| B2 | `rmos/ai_search.py` | `run_constraint_first_search()` loop | ✅ Done |
| B3 | `rmos/logging_ai.py` | AI attempt/run logging (integrated with existing) | ✅ Done |
| B4 | `rmos/api_ai_routes.py` | 5 endpoints including `/constraint-search` | ✅ Done |
| B5 | Wire router in `main.py` | Add `rmos_ai_router` | ⏳ On commit |

**New API Endpoints (Phase B):**
```
POST /api/rmos/ai/constraint-search    # Full search
POST /api/rmos/ai/quick-check          # 5-attempt preview
GET  /api/rmos/ai/status/{code}        # Status descriptions
GET  /api/rmos/ai/workflows            # List workflow modes
GET  /api/rmos/ai/health               # Subsystem health
```

---

### ✅ Phase C: Profile Management — COMPLETE

**Objective:** YAML-based constraint profiles with history  
**Status:** ✅ COMPLETE

| Task | File | Description | Status |
|------|------|-------------|--------|
| C1 | `config/rmos_constraint_profiles.yaml` | 14 preset profiles | ✅ Done |
| C2 | `rmos/constraint_profiles.py` | ProfileStore + YAML I/O | ✅ Done |
| C3 | `rmos/profile_history.py` | JSONL change journal | ✅ Done |
| C4 | `rmos/api_constraint_profiles.py` | CRUD endpoints | ✅ Done |
| C5 | `rmos/api_profile_history.py` | History/rollback endpoints | ✅ Done |

**New API Endpoints (Phase C):**
```
GET    /api/rmos/profiles              # List all profiles
GET    /api/rmos/profiles/ids          # List profile IDs
GET    /api/rmos/profiles/tags/{tag}   # List by tag
GET    /api/rmos/profiles/{id}         # Get profile
POST   /api/rmos/profiles              # Create profile
PUT    /api/rmos/profiles/{id}         # Update profile
DELETE /api/rmos/profiles/{id}         # Delete profile
GET    /api/rmos/profiles/{id}/constraints  # Get constraints only
GET    /api/rmos/profiles/history              # All history
GET    /api/rmos/profiles/history/{entry_id}   # Get entry detail
GET    /api/rmos/profiles/{id}/history         # Profile history
POST   /api/rmos/profiles/{id}/rollback        # Rollback to entry
```

**14 Preset Profiles:**
| Profile ID | Use Case |
|------------|----------|
| `default` | General balanced |
| `beginner`, `first_rosette` | New builders |
| `classical`, `steel_string` | Guitar types |
| `advanced`, `master` | Complex designs |
| `herringbone`, `abalone`, `minimalist` | Style-specific |
| `exotic_woods` | Premium materials |
| `cnc_3018`, `production` | Machine-specific |

---

### ⏳ Phase D: Analytics

**Objective:** Performance statistics and hotspot analysis  
**Status:** Pending

| Task | File | Description |
|------|------|-------------|
| D1 | `rmos/ai_analytics.py` | `compute_profile_performance_stats()`, `compute_hotspots()` |
| D2 | `rmos/api_ai_analytics.py` | Analytics endpoints |
| D3 | `rmos/api_ai_snapshots.py` | Snapshot sampling |

**API Endpoints:**
```
GET /api/rmos/ai/analytics/profile-stats
GET /api/rmos/ai/analytics/hotspots
GET /api/rmos/ai/snapshots/sample
```

---

### ⏳ Phase E: Frontend

**Objective:** Vue components for AI Ops dashboard  
**Status:** Pending

| Task | Component | Description |
|------|-----------|-------------|
| E1 | `RmosAiLogViewer.vue` | Attempts/runs viewer with context filters |
| E2 | `RmosAiSnapshotInspector.vue` | Snapshot sampling without full search |
| E3 | `RmosAiProfilePerformance.vue` | Success rates, risk distribution |
| E4 | `RmosAiProfileEditor.vue` | Profile edit/save/history UI |
| E5 | `RmosAiOpsDashboard.vue` | Unified dashboard at `/dev/rmos-ai-ops` |

---

### ⏳ Phase F: Real AI Integration

**Objective:** Swap stub client for real LLM  
**Status:** Pending

| Task | File | Description |
|------|------|-------------|
| F1 | `ai_core/clients.py` | Implement `OpenAIClient` |
| F2 | `ai_core/clients.py` | Implement `AnthropicClient` |
| F3 | Environment config | `AI_PROVIDER`, `AI_API_KEY`, etc. |
| F4 | Prompt engineering | Rosette/inlay generation prompts |

---

## Part 5: Implementation Priority

```
✅ COMPLETE                    ⏳ PRIORITY 2 (Core AI)      ⏳ PRIORITY 3 (UI/Polish)
─────────────────────          ────────────────────         ─────────────────────
Phase A: Stabilize             Phase D: Analytics           Phase E: Frontend
├─ Commit ai_core/             ├─ ai_analytics.py           ├─ RmosAiLogViewer
├─ Commit cad/                 └─ api_ai_analytics.py       ├─ RmosAiSnapshotInspector
├─ Delete orphans                                           ├─ RmosAiProfilePerformance
└─ Verify routing              Phase F: Real AI             ├─ RmosAiProfileEditor
                               ├─ OpenAIClient              └─ RmosAiOpsDashboard
Phase B: Search Loop ✅        ├─ AnthropicClient
├─ schemas_ai.py               └─ Prompt engineering
├─ ai_search.py
├─ logging_ai.py
└─ api_ai_routes.py

Phase C: Profiles ✅
├─ constraint_profiles.yaml
├─ constraint_profiles.py
├─ profile_history.py
├─ api_constraint_profiles.py
└─ api_profile_history.py
```

---

## Part 6: Environment Variables

```bash
# CAD Engine
DXF_EXPORT_ENABLED=1                    # Enable/disable DXF endpoints

# AI Core
AI_PROVIDER=null                        # "null" | "openai" | "anthropic"
AI_MODEL=gpt-4                          # Model name
AI_API_KEY=sk-...                       # API key (only if AI_PROVIDER != null)
AI_TEMPERATURE=0.7                      # Generation temperature
AI_MAX_TOKENS=2000                      # Max tokens per request

# RMOS AI (Phase C)
RMOS_PROFILE_YAML_PATH=config/rmos_constraint_profiles.yaml
RMOS_PROFILE_HISTORY_PATH=config/rmos_profile_history.jsonl
ENABLE_RMOS_PROFILE_ADMIN=true          # DEV-only guard
```

---

## Part 7: Testing Strategy

### Unit Tests

```
tests/
├── ai_core/
│   ├── test_clients.py           # Client factory, stub behavior
│   ├── test_safety.py            # Validation, sanitization
│   └── test_generators.py        # Generator contracts
├── cad/
│   ├── test_dxf_engine.py        # Engine operations
│   ├── test_validators.py        # Guardrails
│   └── test_offset_engine.py     # Shapely integration
└── rmos/
    ├── test_ai_search.py         # Search loop logic
    ├── test_logging_ai.py        # Log entry creation
    ├── test_constraint_profiles.py  # Profile store
    └── test_profile_history.py   # History journal
```

### Integration Tests

```powershell
# CAD Health
curl http://localhost:8000/api/cad/dxf/health

# AI Health (Phase B)
curl http://localhost:8000/api/rmos/ai/health

# AI Constraint Search (Phase B)
$body = @{
    workflow_mode = "constraint_first"
    context = @{ tool_id = "T1"; material_id = "M1" }
    search_budget = @{ max_attempts = 5; time_limit_seconds = 10 }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/api/rmos/ai/constraint-search" `
    -Method POST -Body $body -ContentType "application/json"

# Profile List (Phase C)
curl http://localhost:8000/api/rmos/profiles

# Profile Detail (Phase C)
curl http://localhost:8000/api/rmos/profiles/classical
```

---

## Part 8: Success Criteria

| Metric | Previous | Current | Target |
|--------|----------|---------|--------|
| CI Build | ❌ Failing | ❌ Failing | ✅ Passing |
| Router Count | 91 | 91 | 94+ (add AI routes) |
| ai_core/ committed | ❌ No | ❌ No | ✅ Yes |
| cad/ committed | ❌ No | ❌ No | ✅ Yes |
| RMOS AI search endpoint | ❌ No | ✅ **Ready** | ✅ Yes |
| Profile management | ❌ No | ✅ **Ready** | ✅ Yes |
| Analytics dashboard | ❌ No | ❌ No | ⚠️ Phase D |
| AI Ops dashboard | ❌ No | ❌ No | ⚠️ Phase E |

---

## Part 9: Immediate Next Steps

1. ~~**Execute Migration Strategy** — Commit all packages (Phase A)~~
2. ~~**Begin Phase B** — RMOS AI search loop implementation~~ ✅ COMPLETE
3. ~~**Begin Phase C** — Profile management~~ ✅ COMPLETE
4. **Copy Phase B+C files to repo** — Use `phase_bc_rmos_complete.zip`
5. **Wire routers in main.py** — Add 3 new routers
6. **Execute Migration Strategy** — Commit all packages
7. **Verify CI passes** — Docker build should succeed
8. **Begin Phase D** — Analytics (optional)
9. **Begin Phase E** — Frontend (optional)

---

## Appendix: File Locations Reference

```
services/api/app/
├── ai_core/                          # ✅ EXISTS - AI client layer
│   ├── __init__.py
│   ├── clients.py                    # Stub + OpenAI client
│   ├── safety.py                     # Output validation
│   ├── generators.py                 # Candidate factory
│   ├── generator_constraints.py      # RMOS adapter
│   └── structured_generator.py       # Constraint-aware gen
│
├── cad/                              # ✅ EXISTS - DXF engine
│   ├── __init__.py
│   ├── exceptions.py
│   ├── geometry_models.py
│   ├── dxf_layers.py
│   ├── dxf_validators.py
│   ├── dxf_engine.py
│   ├── offset_engine.py
│   ├── api/
│   │   └── dxf_routes.py
│   └── schemas/
│       └── dxf_export.py
│
├── calculators/
│   └── alternative_temperaments.py   # ✅ EXISTS - PFS (separate domain)
│
├── rmos/                             # ✅ COMPLETE - Phase B+C ready
│   ├── __init__.py                   # ✅ Updated exports
│   ├── api_contracts.py              # ✅ EXISTS
│   ├── api_routes.py                 # ✅ EXISTS
│   ├── feasibility_fusion.py         # ✅ EXISTS
│   ├── feasibility_router.py         # ✅ EXISTS
│   ├── feasibility_scorer.py         # ✅ EXISTS
│   ├── logging_ai.py                 # ✅ EXISTS (integrated)
│   ├── schemas_logs_ai.py            # ✅ EXISTS
│   ├── ai_policy.py                  # ✅ EXISTS
│   ├── schemas_ai.py                 # ✅ NEW - Phase B
│   ├── ai_search.py                  # ✅ NEW - Phase B
│   ├── api_ai_routes.py              # ✅ NEW - Phase B
│   ├── constraint_profiles.py        # ✅ NEW - Phase C
│   ├── profile_history.py            # ✅ NEW - Phase C
│   ├── api_constraint_profiles.py    # ✅ NEW - Phase C
│   ├── api_profile_history.py        # ✅ NEW - Phase C
│   ├── ai_analytics.py               # ❌ MISSING - Phase D
│   └── api_ai_analytics.py           # ❌ MISSING - Phase D
│
├── config/                           # ✅ NEW - Phase C
│   └── rmos_constraint_profiles.yaml # ✅ 14 preset profiles
│
└── routers/
    └── temperament_router.py         # ✅ EXISTS - already wired
```

---

## Appendix: Router Wiring (main.py)

Add these imports and router registrations:

```python
# Phase B+C Routers
from app.rmos.api_ai_routes import router as rmos_ai_router
from app.rmos.api_constraint_profiles import router as rmos_profiles_router
from app.rmos.api_profile_history import router as rmos_history_router

# Register routers
app.include_router(rmos_ai_router, prefix="/api/rmos")
app.include_router(rmos_profiles_router, prefix="/api/rmos")
app.include_router(rmos_history_router, prefix="/api/rmos")
```

---

**Document Version:** 2.0  
**Author:** Claude (Anthropic) + Ross collaboration  
**Last Updated:** December 15, 2025
