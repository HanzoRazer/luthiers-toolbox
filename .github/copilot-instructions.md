# Luthier's Tool Box – AI Agent Instructions

> CNC guitar lutherie platform: Vue 3 + FastAPI. **All geometry in mm. DXF R12 (AC1009).**
> **Last Updated:** 2026-02-05

## ⚡ Quick Start

```bash
# Backend (FastAPI on :8000)
cd services/api && python -m uvicorn app.main:app --reload --port 8000

# Frontend (Vue on :5173, proxies /api → :8000)
cd packages/client && npm run dev

# Docker (full stack) – recommended for integration testing
docker compose up --build

# Key Tests
cd services/api && pytest tests/ -v                      # All backend tests
cd services/api && pytest tests/ -v -m cam               # By marker: cam, unit, integration, smoke, slow
cd services/api && pytest tests/ -v -m "cam or helical"  # Multiple markers
cd packages/client && npm run test                       # Vitest unit tests
make smoke-helix-posts                                   # Helical post-processor smoke test
make check-boundaries                                    # All architectural fence checks (run before PR)
make api-verify                                          # Full verification: scope + boundaries + tests
```

### Pytest Markers (from `services/api/pytest.ini`)

`unit` `integration` `smoke` `slow` `router` `geometry` `adaptive` `bridge` `helical` `cam` `export` `allow_missing_request_id`

## 🔑 Critical Rules

1. **Units**: Always mm internally – convert only at API boundaries
2. **DXF**: R12 format (AC1009) with closed LWPolylines – never newer versions
3. **SDK**: Use typed helpers (`import { cam } from "@/sdk/endpoints"`) – never raw `fetch()`
4. **CAM Intent**: Use `CamIntentV1` envelope (`app.rmos.cam.CamIntentV1`) – don't create alternatives
5. **DO NOT MODIFY**: `__REFERENCE__/` directory, legacy archives (`Guitar Design HTML app/`, `ToolBox_*`) — **NOTE (2026-02-05):** `__REFERENCE__/` is scheduled for external archival and deletion after WP-0/WP-1/WP-4 complete. See `CHIEF_ENGINEER_HANDOFF.md` Section 11.
6. **Request IDs**: All API responses MUST include `X-Request-Id` header
7. **Machine Profiles**: Use IDs from `machine_profiles.json` (`GRBL_3018_Default`, `Mach4_Router_4x8`, `LinuxCNC_KneeMill`)
8. **Python Modules**: Run as modules (`python -m app.ci.check_boundary_imports`) not scripts
9. **Architectural Fences**: Check [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) before cross-domain imports – CI-enforced
10. **Vue Components**: Use `<script setup lang="ts">` – state in Pinia stores (`packages/client/src/stores/`)
11. **Golden Snapshots**: Never update `tests/golden/*.nc` files casually – they represent manufacturing intent

## 📁 Key Paths

| Area                | Path                                                     |
| ------------------- | -------------------------------------------------------- |
| API Entry           | `services/api/app/main.py` – ~95 routers (19 legacy deleted Jan 2026) |
| CAM Algorithms      | `services/api/app/cam/` – pocketing, helical, biarc      |
| RMOS Orchestration  | `services/api/app/rmos/` – workflow, CAM intent          |
| Runs v2 Store       | `services/api/app/rmos/runs_v2/` – artifacts, attachments|
| MVP Wrapper         | `services/api/app/rmos/mvp_wrapper.py` – DXF→GRBL path   |
| Saw Lab (Reference) | `services/api/app/saw_lab/` – governed operation pattern |
| CAM Intent Schema   | `services/api/app/rmos/cam/schemas_intent.py`            |
| Frontend SDK        | `packages/client/src/sdk/endpoints/` – typed helpers     |
| Post Configs        | `services/api/app/data/posts/*.json` – grbl, mach4, etc. |
| CI Workflows        | `.github/workflows/` – ~50 workflow files                |
| Pinia Stores        | `packages/client/src/stores/` – frontend state           |
| Shared Utils        | `packages/shared/` – cross-package types/utilities       |
| CI Boundary Checks  | `services/api/app/ci/` – boundary enforcement scripts    |

## 🏛️ Architecture Overview

**Monorepo Structure:**

- `services/api/` – FastAPI backend (~95 routers in `app/main.py`, post-consolidation)
- `packages/client/` – Vue 3 SPA with Pinia stores
- `packages/shared/` – Cross-package types/utilities
- `projects/rmos/` – Rosette Manufacturing OS documentation

**Data Flow:** Frontend SDK → FastAPI → CAM/RMOS modules → JSON artifacts or G-code

## 🏗️ Architecture: Operation Lanes

Machine-executing endpoints follow **Operation Lane Governance**:

| Lane          | Description                                               | Example                   |
| ------------- | --------------------------------------------------------- | ------------------------- |
| **OPERATION** | Full governance: artifacts, feasibility gate, audit trail | `/api/saw/batch/*`        |
| **UTILITY**   | Stateless/preview, no artifacts                           | `/api/cam/roughing/gcode` |

**Reference Implementation**: CNC Saw Lab (`services/api/app/saw_lab/batch_router.py`)

- Stage sequence: SPEC → PLAN → DECISION → EXECUTE → EXPORT → FEEDBACK
- **Decision Intelligence**: Plan responses include `plan_auto_suggest` for UI tuning recommendations
  - `override_state`: `"CHOSEN"` | `"CLEARED"` | `None`
  - `applied_override`: Active operator override (when CHOSEN)
  - `recommended_latest_approved`: Suggested tuning (only when CLEARED)

### Service Abstraction: StorePorts Pattern

Use `ArtifactStorePorts` dataclass to inject store dependencies into services:

```python
# services/api/app/saw_lab/decision_intel_apply_service.py
@dataclass
class ArtifactStorePorts:
    list_runs_filtered: Any   # callable(**filters) -> list[dict]
    persist_run_artifact: Any # callable(kind, payload, index_meta, parent_artifact_id=...) -> dict

# Router wires real store at runtime via helper
def _get_store_ports() -> ArtifactStorePorts:
    from app.rmos.runs_v2 import store as runs_store
    return ArtifactStorePorts(
        list_runs_filtered=getattr(runs_store, "list_runs_filtered", lambda **kw: []),
        persist_run_artifact=getattr(runs_store, "persist_run_artifact", lambda **kw: {}),
    )

result = service_function(_get_store_ports(), ...)  # Service receives abstract ports
```

This pattern enables testing with mock stores and enforces boundary isolation.

### Decision Intelligence (Saw Lab)

The Saw Lab implements **Decision Intelligence** for tuning parameter recommendations:

- **Advisory on `/plan`**: When `SAW_LAB_DECISION_INTEL_ENABLED=true`, plan responses include `decision_intel_advisory` with recommended tuning from prior approved decisions
- **Signal detection**: `_conservative_delta_from_signals()` converts operator feedback (burn, tearout, kickback, chatter) into tuning multipliers (rpm_mul, feed_mul, doc_mul)
- **Apply flow**: `/stamp-plan-link` persists link between plan and approved tuning decision

```python
# Key files:
# - decision_intel_advisory.py — Simple helper for plan responses
# - decision_intelligence_service.py — Signal-to-delta heuristics
# - decision_intel_apply_service.py — find_latest_approved_tuning_decision()
```

### RMOS Runs v2 & Operator Packs

The **runs_v2** system provides governance-compliant artifact storage:

- **Immutable artifacts**: Date-partitioned (`{YYYY-MM-DD}/{run_id}.json`), write-once
- **Risk-gated exports**: Operator pack ZIP export blocked for YELLOW/RED without override
- **Deterministic ZIPs**: Fixed timestamps (`1980-01-01`) for reproducibility
- **Content-addressed attachments**: `{sha[0:2]}/{sha[2:4]}/{sha}.ext`

```python
# Creating a governed run artifact:
from app.rmos.runs_v2.store import create_run_id, persist_run
from app.rmos.runs_v2.schemas import RunArtifact, Hashes, RunDecision

run_id = create_run_id()
artifact = RunArtifact(
    run_id=run_id,
    mode="roughing",
    tool_id="cam_roughing_v1",
    status="OK",
    hashes=Hashes(feasibility_sha256=sha256_of_obj(feasibility)),
    decision=RunDecision(risk_level="GREEN"),
    feasibility=feasibility,
    # ... other fields
)
persist_run(artifact)  # Atomic write via .tmp + os.replace()
```

## 🔗 Cross-Boundary Patterns

**Never import directly across domains.** Use these patterns:

### Pattern 1: Artifact Contract (Domain A needs B's output)

```python
# Producer writes JSON artifact with SHA256
write_json_artifact("measurement.json", result, sha256=True)
# Consumer reads without code dependency
data = load_json(artifact_path); validate_schema(data)
```

### Pattern 2: HTTP API Contract (Domain A invokes B)

```python
from app.rmos.cam import CamIntentV1
intent = CamIntentV1(mode="roughing", design={"entities": [...]})
response = requests.post("/api/cam/toolpath/roughing/gcode", json=intent.dict())
```

### Pattern 3: SDK Adapter (Frontend → API)

```typescript
// ✅ CORRECT: Typed SDK helper
import { cam } from "@/sdk/endpoints";
const { gcode, summary, requestId } = await cam.roughingGcode(payload);

// ❌ WRONG: Raw fetch bypasses type safety
const response = await fetch("/api/cam/roughing/gcode", {...});
```

### Pattern 4: MVP Wrapper (DXF → GRBL Golden Path)

The MVP wrapper (`/api/rmos/wrap/mvp/dxf-to-grbl`) wraps the locked manufacturing path with RMOS governance:

```python
# services/api/app/rmos/mvp_wrapper.py
# Policy: Best-effort RMOS (returns gcode even if RMOS storage fails)
# Response includes: run_id, decision (risk_level), hashes, attachments, gcode
```

### Pattern 5: Operator Pack Export

Operator packs bundle run artifacts for manufacturing handoff:

```python
# GET /api/rmos/runs_v2/{run_id}/operator-pack.zip
# Gate behavior:
#   - GREEN: allowed immediately
#   - YELLOW/RED: requires override attachment OR status == "OK"
# Contents: manifest.json, feasibility.json, decision.json, output.nc, override.json (if present)
```

See [operator_pack.py](services/api/app/rmos/runs_v2/operator_pack.py) for deterministic ZIP generation.

## 🧪 Essential Patterns

### Backend: New Router

```python
# services/api/app/routers/my_feature_router.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/do-thing")
def do_thing(req: MyRequest) -> MyResponse: ...

# Register in main.py
app.include_router(my_feature_router, prefix="/api/my-feature", tags=["MyFeature"])
```

### Frontend: SDK Usage

```typescript
import { cam } from "@/sdk/endpoints";
import { ApiError } from "@/sdk/core/errors";

try {
  const { gcode, summary, requestId } = await cam.roughingGcode(payload);
} catch (err) {
  if (err instanceof ApiError && err.is(422)) {
    errorMsg.value = err.details?.message;
  }
}
```

### CAM Intent Envelope

```python
from app.rmos.cam import CamIntentV1
intent = CamIntentV1(mode="roughing", units="mm", design={...})
# CI validation: python -m app.ci.check_cam_intent_schema_hash
```

### Testing

```python
# Backend (pytest markers from pytest.ini)
@pytest.mark.cam
def test_roughing():
    response = client.post("/api/cam/roughing/gcode", json=payload)
    assert "X-Request-Id" in response.headers

# Run by marker
# pytest tests/ -v -m cam           # CAM toolpath tests
# pytest tests/ -v -m integration   # API endpoint tests
# pytest tests/ -v -m smoke         # Quick validation tests
# pytest tests/ -v -m "cam or helical"  # Multiple markers
```

### Test Isolation Pattern

Use `tmp_path` and `monkeypatch` to isolate file storage in tests:

```python
@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create test client with isolated storage directories."""
    runs_dir = tmp_path / "runs" / "rmos"
    atts_dir = tmp_path / "run_attachments"
    runs_dir.mkdir(parents=True, exist_ok=True)
    atts_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("RMOS_RUNS_DIR", str(runs_dir))
    monkeypatch.setenv("RMOS_RUN_ATTACHMENTS_DIR", str(atts_dir))

    # Reset store singleton if present
    try:
        import app.rmos.runs_v2.store as store_mod
        store_mod._default_store = None
    except Exception:
        pass

    from app.main import app
    return TestClient(app)
```

### Golden Snapshot Policy

⚠️ **Never update `tests/golden/*.nc` casually.** Golden G-code represents manufacturing intent.

Update only when:
1. You intentionally changed CAM logic, feeds/speeds, or post-processing
2. You understand and accept the resulting G-code differences
3. The change is reviewed as a **manufacturing behavior change**

```bash
# Regenerate golden snapshot (intentional changes only)
cd services/api
python scripts/regenerate_mvp_golden_gcode.py
git add tests/golden/mvp_rect_with_island__grbl.nc
git commit -m "Update MVP GRBL golden gcode (intentional CAM change)"
```

### Feature Flags

```python
# Environment-based feature flags (default shown)
RMOS_RUNS_V2_ENABLED=true                    # Runs v2 implementation
SAW_LEARNING_HOOK_ENABLED=false              # Feedback loop learning
SAW_METRICS_ROLLUP_HOOK_ENABLED=false        # Metrics rollup persistence
SAW_LAB_APPLY_APPROVED_TUNING_ON_PLAN=false  # Decision Intelligence: apply approved tuning to plans
SAW_LAB_DECISION_INTEL_ENABLED=true          # Decision Intelligence advisory on /plan
```

## 🗺️ API Surface

- **Canonical**: `/api/cam/toolpath/*`, `/api/cam/drilling/*`, `/api/rmos/*`, `/api/art/*`
- **Legacy routes removed** (January 2026): 19 routers deleted, all migrated to consolidated aggregators
- See [ROUTER_MAP.md](../ROUTER_MAP.md) for ~95-router organization

## ⚠️ Common Pitfalls

| Issue                        | Fix                                                 |
| ---------------------------- | --------------------------------------------------- |
| DXF not recognized           | Export R12 (AC1009) with closed LWPolylines         |
| Missing request headers      | Use SDK helpers, not raw fetch                      |
| Post config not found        | Check `app/data/posts/<name>.json` (lowercase)      |
| Schema drift                 | Run `python -m app.ci.check_cam_intent_schema_hash` |
| SQLite `limit` keyword       | Quote as `"limit"` in SQL statements                |
| CSV line endings             | Use `splitlines()` not `split('\n')`                |
| Import boundary violation    | Use artifacts/HTTP, never direct imports            |
| Module-level `os.makedirs()` | Use lazy directory creation (Docker crashes)        |
| Direct `RunArtifact()`       | Use `validate_and_persist()` from store             |
| Frontend raw `fetch()`       | Import from `@/sdk/endpoints`                       |
| Test uses real file paths    | Use `tmp_path` + `monkeypatch.setenv()` for isolation |
| Store singleton not reset    | Set `store_mod._default_store = None` in test fixture |
| Python run as script         | Use `python -m app.module` not `python app/module.py` |
| Machine profile not found    | Use IDs from `machine_profiles.json` (e.g. `GRBL_3018_Default`) |

## 🛠️ Essential CLI Commands

```bash
# CI Gates (run before commit)
python -m app.ci.check_boundary_imports --profile toolbox
python -m app.ci.check_cam_intent_schema_hash
make check-boundaries

# RMOS Management
python -m app.rmos.runs_v2.cli_audit tail -n 50

# Package Scripts (from packages/client/)
npm run dev          # Start dev server
npm run test         # Vitest
npm run lint         # ESLint (max-warnings=0)

# Makefile Targets (from repo root)
make smoke-helix-posts        # Test helical ramping with all post presets
make test-api                 # Run API smoke tests
make check-art-studio-scope   # Art Studio ornament-authority scope gate
make viewer-pack-gate         # Full viewer pack v1 contract gate
make api-verify               # Full verification (scope + boundaries + tests)
```

## 🎸 Module Awareness

| Module         | Scope                                                   | Key Files                                 |
| -------------- | ------------------------------------------------------- | ----------------------------------------- |
| **Module L**   | Adaptive pocketing (spiralizer, trochoids, jerk timing) | `services/api/app/cam/`                   |
| **Module M**   | Machine profiles, energy modeling, feed overrides       | `machines_router.py`, `cam_opt_router.py` |
| **Art Studio** | SVG editor, relief mapper, helical Z-ramping            | `art_studio/`, `/api/art/*` routes        |
| **Saw Lab**    | Reference implementation for governed operations        | `saw_lab/batch_router.py`                 |
| **RMOS**       | Manufacturing orchestration system                      | `rmos/`, `/api/rmos/*` routes             |

## � Active Remediation (Feb 2026)

The codebase is undergoing structured cleanup. See `CHIEF_ENGINEER_HANDOFF.md` and `REMEDIATION_PLAN.md` for full details.

### Work Package Status

| WP | Focus | Priority | Status |
|----|-------|----------|--------|
| WP-0 | Dead code purge | P0 | Pending (delete `__ARCHIVE__/`, `__REFERENCE__/`, stale `client/`, `streamlit_demo/`) |
| WP-1 | Exception hardening | P0 | Pending (97 bare `except:`, 278 safety-critical `except Exception`) |
| WP-2 | API surface reduction | P1 | Pending (1,060 → <300 routes target) |
| WP-3 | God-object decomposition | P1 | Pending (30 Python + 25 Vue files over size limits) |
| WP-4 | Documentation triage | P1 | Pending (685 → ≤50 markdown files) |
| WP-5 | Quick Cut onboarding | P2 | Not started |

### Safety-Critical Exception Handling

**Never use broad exception handlers in safety modules.** These paths control CNC machinery:

```python
# ❌ WRONG in safety-critical paths (feasibility/, gates/, cam/, calculators/)
except Exception:
    return fallback_value  # Masks bugs that could produce unsafe G-code

# ✅ CORRECT: Specific exceptions, fail-closed
except (ValueError, KeyError) as e:
    logger.error(f"Failed: {e}")
    raise  # Let caller handle — never swallow in safety paths
```

**Affected modules (verified counts):**
- `rmos/` — 197 `except Exception` blocks
- `cam/` — 35 blocks
- `saw_lab/` — 32 blocks
- `calculators/` — 14 blocks

## �🚨 Red Flags (Immediate Rejection)

```python
# ❌ RMOS importing CAM execution
from app.cam.toolpath.roughing import generate_roughing_toolpath

# ❌ CAM importing RMOS orchestration
from app.rmos.workflow import approve_workflow

# ❌ Direct RunArtifact construction
artifact = RunArtifact(run_id="xyz", ...)  # Bypasses validation!

# ❌ External repo import
from tap_tone.measurement import perform_analysis
# ❌ Bare except (catches SystemExit, KeyboardInterrupt — always wrong)
except:
    pass

# ❌ Broad except in safety paths (masks bugs in CNC code generation)
except Exception:
    return default_value  # In rmos/, cam/, saw_lab/, calculators/
```

```typescript
// ❌ Frontend raw fetch
const response = await fetch("/api/cam/roughing/gcode", {...});
```

## 🏭 Product Family Architecture

This repository is the **Golden Master** for the Luthier's ToolBox product family. Features are extracted to standalone products using the **Lean Extraction Strategy**.

### Product Tiers

| Tier | Repository | Description | Target Market |
|------|------------|-------------|---------------|
| **Express** | `ltb-express` | Design-focused tools | Hobbyists, guitar players |
| **Pro** | `ltb-pro` | Full CAM workstation | Professional luthiers |
| **Enterprise** | `ltb-enterprise` | Complete shop OS | Guitar businesses |

### Standalone Designers (Micro-Products)

| Product | Repository | Source Module |
|---------|------------|---------------|
| Parametric Guitar | `ltb-parametric-guitar` | `generators/body_outline/` |
| Neck Designer | `ltb-neck-designer` | `generators/neck/`, `routers/neck_router.py` |
| Headstock Designer | `ltb-headstock-designer` | `art_studio/headstock/` |
| Fingerboard Designer | `ltb-fingerboard-designer` | `calculators/fret_calculator.py`, `routers/temperament_router.py` |
| Bridge Designer | `ltb-bridge-designer` | `calculators/bridge/`, `routers/bridge_router.py` |
| Blueprint Reader | `blueprint-reader` | `vision/`, `art_studio/blueprint/` |

### Lean Extraction Strategy

All spin-off repos follow **clean slate extraction** – no template stubs, only implemented code:

```bash
# Extraction workflow
1. Identify feature in Golden Master (this repo)
2. Copy specific files/components needed
3. Strip unnecessary features (downgrade to edition tier)
4. Adapt imports (remove cross-domain dependencies)
5. Test extraction
6. Commit with clear feature description
```

### Cross-Repo Boundaries

| Rule | Description |
|------|-------------|
| **No Golden Master imports** | Spin-offs must NOT import from `luthiers-toolbox` at runtime |
| **Artifact contracts only** | Share data via JSON/DXF files, not code dependencies |
| **Edition flag** | Each product returns `{"edition": "EXPRESS"}` from `/health` |
| **Independent CI** | Each repo has its own GitHub Actions, not shared workflows |

### Feature Extraction Checklist

When extracting a feature to a spin-off product:

- [ ] Identify all source files in Golden Master
- [ ] Check for cross-domain imports (use `python -m app.ci.check_boundary_imports`)
- [ ] Copy only necessary dependencies
- [ ] Update `requirements.txt` / `package.json` for minimal deps
- [ ] Adapt API prefixes if needed (standalone may use `/api/` directly)
- [ ] Add edition-specific feature gates if applicable
- [ ] Test in isolation (no Golden Master running)
- [ ] Document extraction in spin-off's README

### Related Documentation

- [MASTER_SEGMENTATION_STRATEGY.md](../docs/products/MASTER_SEGMENTATION_STRATEGY.md) – Full segmentation plan
- [PRODUCT_REPO_SETUP.md](../PRODUCT_REPO_SETUP.md) – Repo creation workflow
- [EXPRESS_EXTRACTION_GUIDE.md](../EXPRESS_EXTRACTION_GUIDE.md) – Express edition extraction

## 📚 References

- [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) – Architectural boundaries (8 profiles)
- [ROUTER_MAP.md](../ROUTER_MAP.md) – Router organization (~95 routers)
- [docs/ENDPOINT_TRUTH_MAP.md](../docs/ENDPOINT_TRUTH_MAP.md) – API surface + lane classifications
- [docs/BOUNDARY_RULES.md](../docs/BOUNDARY_RULES.md) – Import boundaries (CI-enforced)
- [packages/client/src/sdk/endpoints/README.md](../packages/client/src/sdk/endpoints/README.md) – SDK patterns
- [services/api/tests/README.md](../services/api/tests/README.md) – Golden snapshot policy
- [services/api/pytest.ini](../services/api/pytest.ini) – Test markers and configuration

## 📝 Task Guidelines

- **Atomic changes**: One feature/fix per request, scoped to relevant subsystem
- **Present diffs**: Don't rewrite large files without justification
- **Ask before**: Major refactors, schema changes, or API renames (external tooling depends on surfaces)
- **Test verification**: Run the smoke test closest to the subsystem you modified
- **Document features**: Update relevant `docs/` or quickref when adding functionality
