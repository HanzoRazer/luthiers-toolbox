# Luthier's Tool Box - AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI monorepo. **All geometry in mm. DXF R12 (AC1009).**

## Quick Start

```bash
# Backend
cd services/api && python -m uvicorn app.main:app --reload --port 8000
# Frontend (proxies /api -> :8000)
cd packages/client && npm run dev
# Docker (full stack)
docker compose up --build
# Tests
cd services/api && pytest tests/ -v -m cam       # By marker: unit, integration, smoke, cam, helical, bridge, adaptive, export
cd packages/client && npm run test                # Vitest
# Pre-PR gates (run ALL before submitting)
make check-boundaries                             # 7-step architectural fence check
make api-verify                                   # Full: scope + boundaries + tests
```

## Architecture

- `services/api/` -- FastAPI backend. ~40 active `include_router()` calls in `app/main.py` (many optional via try/except). Core CAM in `app/cam/`, orchestration in `app/rmos/`, reference governed ops in `app/saw_lab/`.
- `packages/client/` -- Vue 3 SPA. `<script setup lang="ts">`, Pinia stores in `src/stores/` (composition API), typed SDK in `src/sdk/endpoints/` (4 namespaces: `cam`, `rmos`, `operations`, `art`).
- `packages/shared/` -- Cross-package types/utilities.

**Data flow:** Frontend SDK -> FastAPI -> CAM/RMOS modules -> JSON artifacts or G-code.

**Operation Lanes** -- machine-executing endpoints are classified:
- **OPERATION** (governed): artifacts + feasibility gate + audit trail. Reference impl: `app/saw_lab/batch_router.py` (SPEC -> PLAN -> DECISION -> EXECUTE -> EXPORT -> FEEDBACK).
- **UTILITY** (stateless): preview/dev use, no governance. Example: `/api/cam/toolpath/roughing/gcode`.

## Critical Rules

1. **Units** -- mm internally, convert only at API boundaries.
2. **DXF** -- R12 (AC1009) with closed LWPolylines only.
3. **Frontend SDK** -- `import { cam } from "@/sdk/endpoints"`, never raw `fetch()` or `axios`.
4. **CAM Intent** -- Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`), don't create alternatives.
5. **Boundary fences** -- Check `FENCE_REGISTRY.json` before cross-domain imports. CI-enforced: `python -m app.ci.check_boundary_imports --profile toolbox`. RMOS <-> CAM, AI sandbox, external repos (`tap_tone.*`, `modes.*`) are hard walls.
6. **Cross-domain integration** -- Artifact contracts (JSON + SHA256) or HTTP APIs only. Never `from app.cam.toolpath import ...` inside `app/rmos/` or vice versa.
7. **Request IDs** -- All API responses MUST include `X-Request-Id` header.
8. **Python modules** -- Run as `python -m app.module`, not `python app/module.py`.
9. **Golden snapshots** -- Never update `tests/golden/*.nc` casually -- manufacturing intent. Only after deliberate CAM logic changes via `python scripts/regenerate_mvp_golden_gcode.py`.
10. **No bare `except:`** -- Catch specific exceptions. In safety paths (`cam/`, `rmos/`, `saw_lab/`, `calculators/`), fail-closed with `raise`.
11. **Machine profiles** -- Use IDs from `machine_profiles.json`: `GRBL_3018_Default`, `Mach4_Router_4x8`, `LinuxCNC_KneeMill`.
12. **Lazy dir creation** -- Never module-level `os.makedirs()` (crashes Docker). Create at first use.
13. **Vue components** -- `<script setup lang="ts">`, state in Pinia stores (composition API / setup store syntax).

## Key Patterns

**New router** -- create in `app/routers/`, register in `main.py`:
```python
router = APIRouter()
@router.post("/do-thing")
def do_thing(req: MyRequest) -> MyResponse: ...
# main.py: app.include_router(router, prefix="/api/my-feature", tags=["MyFeature"])
```

**Test isolation** -- `conftest.py` (659 lines) auto-uses `tmp_path` + `monkeypatch.setenv()` for all storage dirs (`RMOS_RUNS_DIR`, `RMOS_RUN_ATTACHMENTS_DIR`, etc.), resets `store_mod._default_store = None`, auto-injects `X-Request-Id`. Read `services/api/tests/conftest.py` before writing tests.

**StorePorts** -- inject store deps via dataclass for testability (see `saw_lab/decision_intel_apply_service.py`).

**Feature flags** (env): `RMOS_RUNS_V2_ENABLED=true`, `SAW_LAB_DECISION_INTEL_ENABLED=true`, `SAW_LEARNING_HOOK_ENABLED=false`.

## Common Pitfalls

| Trap | Fix |
|------|-----|
| SQLite `limit` keyword | Quote as `"limit"` in SQL |
| CSV line endings | `splitlines()` not `split('\n')` |
| Store singleton leaks in tests | `store_mod._default_store = None` in fixture |
| Post config not found | `app/data/posts/<name>.json` (lowercase) |
| Schema drift | `python -m app.ci.check_cam_intent_schema_hash` |
| `RunArtifact()` direct | Use `validate_and_persist()` from store |
| Router path confusion | Check router's internal `prefix=` + `main.py` mount = full path |

## Red Flags (Immediate Rejection)

```python
from app.cam.toolpath.roughing import ...  # WRONG inside app/rmos/
from app.rmos.workflow import ...          # WRONG inside app/cam/
from tap_tone.measurement import ...       # WRONG external repo import
artifact = RunArtifact(run_id="xyz", ...)  # WRONG bypasses validation
except:                                    # WRONG bare except
    pass
except Exception:                          # WRONG in safety paths (cam/, rmos/, saw_lab/)
    return default_value
```
```typescript
await fetch("/api/cam/roughing/gcode", {...});  // WRONG -- use SDK helpers
```

## Product Family Architecture

This repo is the **Golden Master** for the Luthier's ToolBox product family. Spin-off products use **clean-slate extraction** (copy specific files, strip extras, adapt imports) -- never runtime imports from this repo.

| Tier | Repo | Description |
|------|------|-------------|
| **Express** | `ltb-express` | Design-focused tools (hobbyists) |
| **Pro** | `ltb-pro` | Full CAM workstation (professional luthiers) |
| **Enterprise** | `ltb-enterprise` | Complete shop OS (guitar businesses) |

**Standalone micro-products** extract from: `generators/body_outline/`, `generators/neck/`, `art_studio/headstock/`, `calculators/fret_calculator.py`, `calculators/bridge/`, `vision/`.

**Cross-repo rules:**
- No runtime imports from Golden Master -- artifact contracts (JSON/DXF) only
- Each product returns `{"edition": "EXPRESS"}` from `/health`
- Independent CI per repo (no shared workflows)
- Run `python -m app.ci.check_boundary_imports` before extraction to verify clean boundaries

See `docs/products/MASTER_SEGMENTATION_STRATEGY.md` for full segmentation plan and `EXPRESS_EXTRACTION_GUIDE.md` for extraction workflow.

## Remediation Context (Feb 2026)

Codebase scored **4.7/10**. Active cleanup per `REMEDIATION_PLAN.md`: 97 bare `except:`, 1,622 `except Exception` blocks, 1,060 routes (target <300), 30+ Python god-objects.

## Key References

| Resource | What it tells you |
|----------|-------------------|
| `FENCE_REGISTRY.json` | 8 architectural boundary profiles |
| `ROUTER_MAP.md` | Router organization by deployment wave |
| `docs/ENDPOINT_TRUTH_MAP.md` | Full API surface + OPERATION/UTILITY lane classifications |
| `services/api/tests/conftest.py` | Test fixture patterns (read before writing tests) |
| `Makefile` | 16 targets including all CI gates |
| `REMEDIATION_PLAN.md` | 6-phase cleanup plan with current status |
