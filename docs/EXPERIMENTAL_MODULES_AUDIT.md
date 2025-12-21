# Experimental Modules Audit

**Generated:** December 20, 2025
**Location:** `services/api/app/_experimental/`
**Total Files:** 74 Python files

---

## Module Summary

| Module | Files | Status | Production Ready? |
|--------|-------|--------|-------------------|
| `ai_cam/` | 5 | Imports OK | Yes - Mature |
| `ai_core/` | 6 | Imports OK | Yes - Mature |
| `ai_graphics/` | 24 | Imports OK | Partial - Some features experimental |
| `analytics/` | 5 | Imports OK | Yes - Stable |
| `cnc_production/` | 28 | Imports OK | Yes - In active use |
| `infra/` | 2 | Imports OK | Yes - Stable |

---

## Detailed Analysis

### 1. ai_cam/ (AI-Assisted CAM Advisor)

**Files:**
- `__init__.py` - Module exports
- `advisor.py` - CAM advisory engine
- `explain_gcode.py` - G-code explainer 2.0
- `models.py` - Data models
- `optimize.py` - CAM optimizer

**Exports:**
- `CAMAdvisory`, `CAMAnalysisResult`
- `GCodeExplanation`, `GCodeExplainerResult`
- `CAMAdvisor`, `GCodeExplainer`, `CAMOptimizer`

**Assessment:** Production ready. Well-structured with clear exports.

**Recommendation:** Graduate to `app/ai/cam/`

---

### 2. ai_core/ (AI Core Utilities)

**Files:**
- `__init__.py` - Module exports
- `clients.py` - AI client connections
- `generator_constraints.py` - Constraint system
- `generators.py` - Candidate generators
- `safety.py` - Safety utilities
- `structured_generator.py` - Structured output

**Exports:**
- `RosetteGeneratorConstraints`, `constraints_from_context`
- `coerce_to_rosette_spec`
- `get_default_candidate_generator`, `make_candidate_generator_for_request`

**Assessment:** Production ready. Core AI infrastructure.

**Recommendation:** Graduate to `app/ai/core/`

---

### 3. ai_graphics/ (Vision & Image Generation)

**Subdirectories:**
- `api/` - AI routes, session routes, teaching routes, advisory routes, vision routes
- `schemas/` - AI schemas, advisory schemas
- `services/` - Providers, LLM client, teaching loop, pattern visualizer
- `db/` - Models and store

**Key Files:**
- `image_providers.py` - Multi-provider image generation
- `prompt_engine.py` - Prompt engineering
- `rosette_generator.py` - AI rosette generation
- `vocabulary.py` - Domain vocabulary

**Assessment:** Partially production ready. Core features stable, some experimental.

**Recommendation:**
- Graduate stable components to `app/ai/graphics/`
- Keep experimental features in `_experimental/`

---

### 4. analytics/ (Advanced Analytics)

**Files:**
- `__init__.py` - Module exports
- `advanced_analytics.py` - Advanced metrics
- `job_analytics.py` - Job-level analytics
- `material_analytics.py` - Material usage
- `pattern_analytics.py` - Pattern analysis

**Assessment:** Production ready. Stable analytics engine.

**Recommendation:** Graduate to `app/analytics/`

---

### 5. cnc_production/ (CNC Production System)

**Subdirectories:**
- `feeds_speeds/` - Feeds/speeds calculation with learned overrides
  - `api/routes/` - API endpoints
  - `core/` - Chipload, deflection, heat models
  - `schemas/` - Data schemas
- `joblog/` - Job logging and telemetry
- `learn/` - Live learning system

**Key Files:**
- `routers.py` - Production routers
- `feeds_speeds/core/feeds_speeds_resolver.py` - Main resolver
- `feeds_speeds/core/learned_overrides.py` - Override system
- `learn/live_learn_ingestor.py` - Live learning

**Assessment:** Production ready. Already integrated via saw_telemetry_router.

**Recommendation:** Graduate to `app/cnc/production/`

---

### 6. infra/ (Infrastructure)

**Files:**
- `__init__.py` - Module exports
- `live_monitor.py` - Live monitoring

**Assessment:** Production ready. Minimal, stable.

**Recommendation:** Graduate to `app/infra/`

---

## Graduation Plan

### Phase 1: Create New Directories
```
app/
├── ai/
│   ├── cam/           ← from _experimental/ai_cam
│   ├── core/          ← from _experimental/ai_core
│   └── graphics/      ← from _experimental/ai_graphics (stable parts)
├── analytics/         ← from _experimental/analytics
├── cnc/
│   └── production/    ← from _experimental/cnc_production
└── infra/             ← from _experimental/infra
```

### Phase 2: Update Imports
- Update all internal imports to new paths
- Update routers (ai_cam_router.py, joblog_router.py)
- Update main.py registrations

### Phase 3: Add Compatibility Shims
- Keep `_experimental/` as re-export layer
- Add deprecation warnings
- Allow gradual migration

### Phase 4: Remove _experimental/
- After transition period (1-2 sprints)
- Delete old files
- Update documentation

---

## Priority Ranking

| Module | Priority | Reason |
|--------|----------|--------|
| `cnc_production/` | High | Already referenced by routers |
| `ai_cam/` | High | Core AI CAM functionality |
| `ai_core/` | High | Foundation for other AI modules |
| `analytics/` | Medium | Stable, less critical |
| `infra/` | Medium | Small, easy to move |
| `ai_graphics/` | Low | Partially experimental |

---

## Notes

- All 6 modules import successfully
- No circular dependency issues detected
- Code quality appears consistent
- Documentation exists in most modules
- Test coverage unknown (audit recommended)
