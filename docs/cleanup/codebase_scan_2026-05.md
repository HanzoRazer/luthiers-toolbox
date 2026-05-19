# Production Shop Codebase Scan — May 2026

## Executive Summary

This scan inventories the current state of the luthiers-toolbox codebase to inform a subsequent planning sprint and cleanup execution. The codebase is **large and active** (1,401+ Python files in services/api alone, 325+ test files, 52+ CI workflows) with **well-organized architecture** but **accumulated artifacts and some security issues** requiring attention.

**Key findings:**
1. **SECURITY**: Exposed API keys in `.env` and `services/api/.env` — immediate remediation required
2. **Artifacts**: ~14 directories at root and in services/ containing generated outputs, downloads, and test artifacts
3. **Config sprawl**: 12 .env files, 7 Dockerfiles, 52+ CI workflows — consolidation opportunity
4. **AI subsystems**: All 5 directories (ai, agentic, advisory, analyzer, ai_context_adapter) are **canonical with distinct purposes** — no legacy duplication
5. **Orphaned pages**: 4 hostinger/ HTML landing pages + 12 unrouted Vue views — user confirmation needed on which are abandoned

---

## Code Inventory

### services/api/ (Primary Backend)

| Metric | Count |
|--------|-------|
| Python files | 1,401 |
| App directories | 52+ |
| Router files | 100+ |
| Test files | 273 |

**Key directories:**
- `app/routers/` — 100+ router files across domains (cam, instrument, ai, rmos, etc.)
- `app/calculators/` — Core calculation logic
- `app/cam/`, `app/cam_core/` — CAM operations
- `app/instrument_geometry/` — Guitar geometry modules
- `app/ai/`, `app/agentic/`, `app/advisory/`, `app/analyzer/`, `app/ai_context_adapter/` — AI subsystems (all canonical)
- `app/rmos/` — Rosette Manufacturing Orchestration System
- `app/router_registry/` — Centralized router loading (6 domain manifests)

**Cleanup candidates in services/api/:**
- `app/_experimental/` — Experimental code
- `app/routers/_archived/` — Archived pipeline code
- `app/router_rewire_report/` — One-time migration artifact
- `app/Users/` — Accidental directory (unusual)
- `app/util/` AND `app/utils/` — Duplication

### services/blueprint-import/ (Vectorizer Service)

| Metric | Count |
|--------|-------|
| Python files | 67 |
| Test files | 12 |
| Output directories | 2+ |

**Key files:**
- `vectorizer_phase2.py`, `vectorizer_phase3.py`, `vectorizer_enhancements.py` — Core vectorization
- `dxf_parser.py`, `dxf_compat.py`, `dxf_postprocessor.py` — DXF processing
- `phase4/` — Dimension linking pipeline
- `calibration/` — Scale calibration

**Status:** Active development, Phase 4 dimension linking in progress

### services/photo-vectorizer/ (Photo Extraction Service)

| Metric | Count |
|--------|-------|
| Python files | 72 |
| Test files | 33 |
| Test output dirs | 14+ |

**Key files:**
- `photo_vectorizer_v2.py` — Main photo vectorizer
- `geometry_coach.py`, `geometry_coach_v2.py` — Geometry coaching
- `cognitive_extraction_engine.py`, `cognitive_extractor.py` — AI extraction
- Multiple `extract_body_grid_v*.py` versions (v2-v5) — Consolidation candidate

**Cleanup candidates:**
- 14+ test output directories (`live_test_output/`, `march_test_*`, `test_*`)
- Multiple extract_body_grid versions suggest incomplete consolidation

### packages/client/ (Vue Frontend)

| Metric | Count |
|--------|-------|
| Vue components | 200+ |
| Views | 50+ |
| Router routes | 80+ |

**Structure:**
- `src/views/` — Page-level components
- `src/components/` — Reusable components (art, cam, rmos, toolbox, etc.)
- `src/router/index.ts` — Route definitions

**Orphaned views (not in router, not imported):**
- ArtStudioPhase15_5.vue
- ArtStudioDashboard.vue
- ArtJobDetail.vue
- ArtJobTimeline.vue
- ArtStudioUnified.vue
- ArtPresetManager.vue
- MachineListView.vue
- PostListView.vue
- CamProductionView.vue
- MultiRunComparisonView.vue
- OffsetLabView.vue
- LabsIndex.vue

### production_shop_agent/ (Separate Subproject)

**Purpose:** Claude-powered static website generator API

| Component | Description |
|-----------|-------------|
| `main.py` | FastAPI entry point (port 8000) |
| `api/` | site_generator_router, auth, config |
| `site_agent/` | Website generation agent |
| `admin_ui.html` | Admin interface |
| `output/` | Generated websites (production_shop, lutherie_portfolio) |

**Relationship to services/api:** Completely separate — different port, different purpose. Could potentially be moved to `services/site-generator/` for consistency.

---

## Dependency Analysis

### ai/ vs api/ vs api_v1/ Split State

**api/** (3 files):
- `__init__.py`
- `deps/__init__.py`
- `deps/rmos_stores.py`

**api_v1/** (11 files):
- `rmos_safety.py`, `instrument.py`, `fret_math.py`, `acoustics.py`
- `machines.py`, `jobs.py`, `cam_operations.py`, `art_studio.py`
- `dxf_workflow.py`, `fretboard.py`, `__init__.py`

**Assessment:** api/ is minimal (just deps), api_v1/ contains domain modules. This may represent incomplete migration or intentional versioning. Needs clarification.

### AI Subsystem Architecture

All 5 AI directories are **CANONICAL** with distinct architectural roles:

| Directory | Purpose | Status |
|-----------|---------|--------|
| `ai/` | Shared AI infrastructure (LLM clients, safety, observability) | Active, canonical |
| `agentic/` | User guidance system (coach bubble, M1 Advisory mode) | Active, canonical |
| `advisory/` | AI/RMOS boundary layer (asset storage) | Active, canonical |
| `analyzer/` | Acoustic interpretation (tap tone analysis) | Active, canonical |
| `ai_context_adapter/` | Context envelope builder with redaction | Active, canonical |

**No legacy AI systems found — no cleanup needed.**

---

## Endpoint Reality vs. Claims

**Router registry structure:**
- 6 domain manifests (system, cam, rmos, art_studio, business, acoustics)
- Routers loaded via `router_registry.load_all_routers()`
- Endpoint governance middleware active

**Archived routers:**
- `routers/_archived/pipeline_schemas.py`
- `routers/_archived/pipeline_context.py`
- `routers/_archived/pipeline_helpers.py`
- `routers/_archived/pipeline_validators.py`
- `routers/_archived/pipeline_operations.py`

---

## Frontend Landing Pages — Candidates for Confirmation

### hostinger/ (4 static HTML files)

| File | Description |
|------|-------------|
| `production-shop-hub.html` | Main marketing landing page |
| `blueprint-reader.html` | Blueprint Reader tool landing |
| `archtop-graduation-studio.html` | Archtop graduation studio |
| `body-outline-editor.html` | Body outline editor |

**Status:** Unknown deployment state. User should confirm which are abandoned.

### blueprint-reader/ (Root directory)

Empty or minimal — may be orphaned from hostinger deployment.

---

## Configuration Surface

### .env Files (12 total)

| Location | Purpose | Issue |
|----------|---------|-------|
| `.env` (root) | API keys | **EXPOSED KEYS — SECURITY ISSUE** |
| `.env.example` (root) | Template with Supabase config | OK |
| `services/api/.env` | API + Supabase config | **EXPOSED KEYS — SECURITY ISSUE** |
| `packages/client/.env.local` | Client config | OK (anon key expected) |
| `packages/client/.env.local.example` | Template | OK |
| `packages/client/.env.production` | Production client | Check before deploy |
| `production_shop_agent/.env.example` | Site generator template | OK |
| `templates/env/.env.express` | Express tier template | OK |
| `templates/env/.env.pro` | Pro tier template | OK |
| `templates/env/.env.enterprise` | Enterprise tier template | OK |
| `templates/env/.env.neck` | Neck designer template | OK |
| `templates/env/.env.parametric` | Parametric tier template | OK |

**IMMEDIATE ACTION:** Rotate exposed API keys and add `.env` to `.gitignore`

### Dockerfiles (7 total)

| Location | Purpose |
|----------|---------|
| `docker/api/Dockerfile` | API container (sg-spec support) |
| `docker/client/Dockerfile` | Client container (nginx) |
| `docker/client/Dockerfile.railway` | Railway deployment |
| `docker/client/Dockerfile.production` | Production build |
| `docker/nginx/Dockerfile` | Nginx proxy |
| `packages/client/Dockerfile` | **Duplicate?** |
| `services/api/Dockerfile` | **Duplicate?** |

**Consolidation opportunity:** `packages/client/Dockerfile` and `services/api/Dockerfile` may be duplicates of docker/ versions.

### docker-compose Files (2)

- `docker-compose.yml` — Development
- `docker-compose.production.yml` — Production

---

## Test Surface

### Test File Distribution

| Location | Count |
|----------|-------|
| services/api/tests | 273 |
| services/blueprint-import/tests | 12 |
| services/photo-vectorizer (root) | 33 |
| tests/ (root) | 7 |
| **Total** | **325** |

### pytest Configuration

- **Config:** `services/api/pytest.ini`
- **Coverage targets:** app.core.safety, app.rmos.feasibility, app.safety
- **Coverage threshold:** 20% (fail-under=20)
- **Markers:** unit, integration, smoke, slow, router, geometry, adaptive, bridge, helical, cam, export, ai_context

### CI Workflows (52+)

Large number of workflows — consolidation opportunity. Key categories:

**Test workflows:**
- `api_pytest.yml`, `api_tests.yml`, `api_verify.yml`
- `core_ci.yml`, `rmos_ci.yml`, `spine-ci.yml`

**Gate workflows:**
- `cbsp21_gate.yml`, `mvp_golden_gate.yml`
- `geometry_parity.yml`, `routing_truth.yml`
- `dxf_validation_gate.yml`, `smart_guitar_export_gate.yml`

**Validation:**
- `api_contract_check.yml`, `governance_baseline_guard.yml`

**Deployment:**
- `railway-deploy.yml`, `containers.yml`, `publish-images.yml`

---

## Database Surface

### Alembic Migrations (2)

| Revision | Description |
|----------|-------------|
| `0001_supabase_auth` | Supabase auth tables (user_profiles, projects, feature_flags) |
| `42a488dcbc25` | Initial schema from SQLite |

**Architecture:** Database-agnostic (SQLite dev, PostgreSQL prod) with `dual_write.py` suggesting transitional state.

### Static Data Files

| Location | Contents |
|----------|----------|
| `app/data/posts/` | G-code post configs (grbl, mach4, linuxcnc, etc.) |
| `app/data/machines.json` | Machine definitions |
| `app/data/tool_library.json` | Tool definitions |
| `app/data/presets.json` | Pipeline presets |
| `app/data/art_studio/cam_promotion/requests/` | 30+ request JSON files |
| `app/data/baselines/` | 20+ comparison baseline files |
| `app/data_registry/system/materials/wood_species.json` | Wood species data |

**Cleanup candidates:** `art_studio/cam_promotion/requests/` may contain old requests.

---

## Strategic Alignment Audit

### Standalone Tools at Root

| Directory | Files | Status |
|-----------|-------|--------|
| `Interactive_Headstock_Generator/` | 23 | Unclear integration |
| `Interactive_Neck and Cam _Modules/` | 97 | Unclear integration |
| `Rosette Designer/` | 1 | Unclear integration |
| `Guitar Plans/` | 567 | Reference data |

**Question:** Should these integrate into packages/client or remain separate standalone tools?

### Artifact/Download Directories

| Directory | Files | Status |
|-----------|-------|--------|
| `files - 2026-03-31T002554.594/` | 3 | Timestamped download — cleanup |
| `files - 2026-04-14T102549.923/` | 3 | Timestamped download — cleanup |
| `files - 2026-04-16T160551.956/` | 3 | Timestamped download — cleanup |
| `files - 2026-04-16T161657.416/` | 2 | Timestamped download — cleanup |
| `files - 2026-04-23T090806.069/` | 3 | Timestamped download — cleanup |
| `benchmark_dxf_outputs/` | 6 | Test outputs — cleanup |
| `benchmark_exports/` | 3 | Test outputs — cleanup |
| `benchmark_outputs/` | 27 | Test outputs — cleanup |
| `benchmark_results/` | 1 | Test outputs — cleanup |

---

## Cleanup Candidates

### High Value, Low Effort

| Item | Effort | Impact |
|------|--------|--------|
| **Rotate exposed API keys** | 30 min | CRITICAL security |
| **Add .env to .gitignore** | 5 min | Prevent future exposure |
| Root `files - *` directories (5) | 10 min | Clean up downloads |
| Root `benchmark_*` directories (4) | 10 min | Clean up test outputs |
| photo-vectorizer test output dirs (14) | 15 min | Clean up test outputs |

### High Value, High Effort

| Item | Effort | Impact |
|------|--------|--------|
| CI workflow consolidation (52+ → ~20) | 2-3 days | Maintainability |
| Docker/config consolidation | 1 day | Deployment clarity |
| api/ vs api_v1/ resolution | 1 day | Architecture clarity |
| Standalone tool integration decision | Variable | Strategic |

### Low Value, Low Effort

| Item | Effort | Impact |
|------|--------|--------|
| `app/util/` + `app/utils/` merge | 30 min | Minor cleanup |
| `routers/_archived/` deletion | 10 min | Minor cleanup |
| `app/Users/` deletion | 5 min | Minor cleanup |
| `router_rewire_report/` deletion | 5 min | Minor cleanup |

### Requires User Confirmation

| Item | Question |
|------|----------|
| hostinger/ landing pages | Which are abandoned? |
| 12 orphaned Vue views | Which are abandoned? |
| Standalone tools at root | Integrate or keep separate? |
| production_shop_agent | Integrate into services/ or keep separate? |

---

## Risk Inventory

### Security

- **CRITICAL:** Exposed API keys in committed .env files
- OpenAI and Anthropic API keys visible in repository

### Technical Debt

- 52+ CI workflows may have overlap/redundancy
- 7 Dockerfiles may have duplication
- `dual_write.py` suggests incomplete database migration

### Complexity

- 1,401 Python files is a large codebase
- Router registry helps but 100+ router files is substantial
- Photo-vectorizer has multiple versioned files (extract_body_grid_v2-v5)

---

## Recommendations

### Immediate (This Week)

1. **Rotate all exposed API keys** — both OpenAI and Anthropic
2. **Add `.env` and `services/api/.env` to `.gitignore`**
3. **Delete root artifact directories** — `files - *`, `benchmark_*`
4. **User confirms** which hostinger pages and Vue views are abandoned

### Short-term (Next Sprint)

1. **Clean up photo-vectorizer test output directories**
2. **Consolidate extract_body_grid versions**
3. **Resolve api/ vs api_v1/ split** — clarify whether this is versioning or incomplete migration
4. **Decision on standalone tools** — integrate into main app or keep separate

### Medium-term (Following Sprints)

1. **CI workflow audit and consolidation**
2. **Dockerfile deduplication**
3. **Config file consolidation**

---

## Appendix: File Counts by Directory

| Directory | Python Files |
|-----------|-------------|
| services/api/app | 1,401 |
| services/blueprint-import | 67 |
| services/photo-vectorizer | 72 |
| production_shop_agent | ~15 |
| **Total** | **~1,555** |

| Directory | Test Files |
|-----------|-----------|
| services/api/tests | 273 |
| services/blueprint-import/tests | 12 |
| services/photo-vectorizer | 33 |
| tests/ (root) | 7 |
| **Total** | **325** |

---

*Scan completed: 2026-05-03*
*Scan type: Discovery only — no changes made*
*Next step: Planning sprint to prioritize cleanup work*
