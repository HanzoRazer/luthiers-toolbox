Below is a **drop-in `docs/AUDIT_BUILT_VS_CREATED.md` draft** that covers the **33 newly-untracked directories** your verification report listed , plus the **key “now trackable” individual files** that should be handled explicitly .

Copy/paste this file into your repo as-is, then we’ll iterate it as you confirm where each subsystem is actually being imported from.

---

# docs/AUDIT_BUILT_VS_CREATED.md

```markdown
# AUDIT — Built vs Created (Recovery + Promotion Plan)

**Date:** 2025-12-14  
**Scope:** `services/api/app/` directories that became trackable after `.gitignore` anchoring fix.  
**Source:** `GITIGNORE_FIX_VERIFICATION_REPORT.md` (Phase 3 list)  
**Goal:** classify each directory as:
- **Promote (Core)**: move forward into the canonical monorepo build
- **Promote (Active Feature)**: keep, but staged after core
- **Isolate (Experimental)**: keep in `_experimental/` pending integration
- **Ignore (Artifacts/Outputs)**: keep out of git or keep ignored
- **Archive Out-of-Tree**: move out of repo to prevent drift

---

## 0) Baseline Facts (from verification)
- **169 files** in `services/api/app/` are now trackable (previously blocked).  
- **33 new untracked directories** are now visible to git.  
- Several directories are explicitly marked **CRITICAL**: `calculators/`, `data/`, `tools/`.  

---

## 1) Directory Classification Table (33)

| Directory | Contents (per report) | Status | Action | Target Location | Notes / Acceptance Check |
|---|---|---:|---|---|---|
| `calculators/` | Calculator package (**CRITICAL**) | Created | **Promote (Core)** | `services/api/app/calculators/` | Must import clean; add 1 smoke test for `service.py` facade |
| `data/` | Data modules (**CRITICAL**) | Created | **Promote (Core)** | `services/api/app/data/` | Confirm `tool_library.py` loads fixtures |
| `tools/` | Tool definitions (**CRITICAL**) | Created | **Promote (Core)** | `services/api/app/tools/` | Confirm no collision with other “tools” dirs |
| `core/` | Core utilities | Created | Promote (Core) | `services/api/app/core/` | Only if referenced by calculators/rmos/api |
| `util/` (9 files) | Utility modules | Created | Promote (Core) | `services/api/app/util/` | Consolidate duplicates w/ existing util |
| `config/` | Configuration | Created | Promote (Core) | `services/api/app/config/` | Verify no secrets; env-driven |
| `schemas/` (17 files) | Pydantic schemas | Created | Promote (Core) | `services/api/app/schemas/` | Ensure API uses these, not duplicates |
| `api/` | API submodule | Created | Promote (Core) | `services/api/app/api/` | Confirm naming doesn’t conflict w/ FastAPI “api” |
| `services/` (20 files) | Service layer | Created | Promote (Core) | `services/api/app/services/` | Must be called by routers (not direct imports everywhere) |
| `stores/` | Data stores | Created | Promote (Core) | `services/api/app/stores/` | Validate storage paths & file IO policy |
| `websocket/` | WebSocket handlers | Created | Promote (Active Feature) | `services/api/app/websocket/` | Only if router wiring exists |
| `workflow/` | Workflow modules | Created | Promote (Active Feature) | `services/api/app/workflow/` | Note: includes deprecated route file (see ignored list) |
| `pipelines/` | Pipeline modules | Created | Promote (Active Feature) | `services/api/app/pipelines/` | Must not revive deprecated pipeline router |
| `rmos/api/` | RMOS API submodule | Created | Promote (Core) | `services/api/app/rmos/api/` | Must align with `/api/rmos/*` router scheme |
| `rmos/models/` | RMOS models | Created | Promote (Core) | `services/api/app/rmos/models/` | Verify pydantic/sqlalchemy alignment |
| `rmos/services/` | RMOS services | Created | Promote (Core) | `services/api/app/rmos/services/` | Feasibility + context adapter wiring |
| `app/` | App submodule | Created | **Isolate (Review)** | `services/api/app/_experimental/app/` | High risk of namespace collision (“app.app”) |
| `infra/` | Infrastructure | Created | Isolate (Review) | `services/api/app/_experimental/infra/` | Promote only if referenced by main |
| `reports/` | Report generators | Created | **Ignore (Artifacts/Outputs)** | `services/api/app/_ignored/reports/` | If outputs only, keep out of git |
| `tests/` (13 files) | Test modules | Created | Promote (Core) | `services/api/tests/` or `services/api/app/tests/` | Pick one canonical test root |
| `cad/` | CAD utilities | Created | Promote (Active Feature) | `services/api/app/cad/` | Tie to DXF-lite + datum exports |
| `cam_core/` | CAM core modules | Created | Promote (Active Feature) | `services/api/app/cam_core/` | Must not break existing CAM engine |
| `toolpath/` (7 files) | Toolpath generators | Created | Promote (Active Feature) | `services/api/app/toolpath/` | Needed for CAM readiness |
| `cnc_production/` | CNC production modules | Created | Isolate (Review) | `services/api/app/_experimental/cnc_production/` | Promote after CAM stabilization |
| `ltb_calculators/` | LTB calculators | Created | Isolate (Review) | `services/api/app/_experimental/ltb_calculators/` | Might be older duplicate of calculators spine |
| `generators/` | Generator modules | Created | Promote (Active Feature) | `services/api/app/generators/` | Only after router-prefix sanity checks |
| `art_studio/` | Art Studio components | Created | Promote (Active Feature) | `services/api/app/art_studio/` | Tie to rosette store + AI suggestions later |
| `analytics/` | Analytics modules | Created | Isolate (Experimental) | `services/api/app/_experimental/analytics/` | Avoid mixing with core builds |
| `ai_core/` | Core AI utilities | Created | Isolate (Experimental) | `services/api/app/_experimental/ai_core/` | Keep for later sandbox |
| `ai_graphics/` | AI graphics processing | Created | Isolate (Experimental) | `services/api/app/_experimental/ai_graphics/` | Keep separate from CAM safety path |
| `ai_cam/` | AI-assisted CAM modules | Created | Isolate (Experimental) | `services/api/app/_experimental/ai_cam/` | Must never generate gcode directly (policy) |
| `art_studio/` | Art Studio components | Created | Promote (Active Feature) | `services/api/app/art_studio/` | Confirm endpoints exist and are wired |
| `cad/` | CAD utilities | Created | Promote (Active Feature) | `services/api/app/cad/` | Ensure DXF security gateway applies |
| `workflow/` | Workflow modules | Created | Promote (Active Feature) | `services/api/app/workflow/` | Audit for deprecated routes |
| `websocket/` | WebSocket handlers | Created | Promote (Active Feature) | `services/api/app/websocket/` | Confirm no open sockets in tests |

> Note: Some directories appear “generic” and may overlap with already-tracked equivalents. If duplicates exist, we keep the canonical one and archive duplicates out-of-tree.

---

## 2) Key Individual Files — Explicit Handling List
These files were called out as now trackable and should be verified directly (import + purpose):

- `calculators/alternative_temperaments.py` — Precision Fret System  
- `calculators/fret_slots_export.py` — Fret Slots CAM  
- `rmos/schemas_logs_ai.py` — AI Search schemas/logs  
- `rmos/ai_search.py` — AI Search loop  
- `data/tool_library.py` — Tool Library loader  

Each should get:
1) import check  
2) 1 smoke test (minimal)  
3) ensure it is not duplicated elsewhere under different names

---

## 3) Promotion Waves (Commit Plan)

### Wave 0 — Already done
- Commit `.gitignore` anchoring fix.

### Wave 1 — Core Spine Recovery (must be clean)
Promote:
- `calculators/`, `data/`, `tools/`, plus minimal `schemas/`, `util/`, `core/`, `config/`

### Wave 2 — RMOS Core (no AI yet)
Promote:
- `rmos/api/`, `rmos/models/`, `rmos/services/`, and any required `services/`

### Wave 3 — Geometry + CAM Readiness
Promote:
- `cad/`, `cam_core/`, `toolpath/`, `art_studio/`

### Wave 4 — Experimental / AI Isolation
Move into:
- `services/api/app/_experimental/*` (ai_* + analytics + questionable “app/”)

---

## 4) Acceptance Checks (minimum)
- `python -m compileall services/api/app` passes
- `pytest -q` passes core smoke tests for calculators + tool library + RMOS context
- `uvicorn app.main:app` boots without import errors

---

## 5) Decision Log
Record all moves/renames here with:
- original path
- new path
- reason
- commit hash

```

---

## What I need from you (so we don’t mis-place anything)

Before you start moving directories, run and paste the output of these two commands (first 60 lines each):

```powershell
git status --porcelain | Select-String "^\?\?" | Select-Object -First 60
```

```powershell
rg -n "from app\.calculators|import app\.calculators|from app\.data|import app\.data|from app\.tools|import app\.tools" services/api/app | Select-Object -First 60
```

That will let me tighten the table into “**promote vs isolate**” with high confidence based on **real import usage**, not guesses.
