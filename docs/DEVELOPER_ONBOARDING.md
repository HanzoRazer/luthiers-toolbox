# Luthier's Tool Box – Developer Onboarding Guide

> Last updated: 2025-11-23 · Target audience: new contributors working on CAM, Blueprint, or Art Studio stacks.

---

## 1. Quick Start (5-Minute Tour)

### 1.1 Prerequisites
- Windows 11 or macOS 13+ (Linux works, but PowerShell scripts assume Windows Core).
- Python 3.11 (make sure `python --version` prints 3.11.x).
- Node.js 18 LTS (Vite + Vue 3 rely on modern ESM syntax).
- Git 2.40+ with long path support enabled (`git config --global core.longpaths true`).
- Docker Desktop 4.30+ (only required for full-stack parity testing).

### 1.2 Clone & Configure
```pwsh
# Clone repository
cd C:\workspace
 git clone https://github.com/HanzoRazer/luthiers-toolbox.git
 cd luthiers-toolbox

# Optional: keep legacy artifacts read-only to avoid accidental edits
attrib +R "Luthiers Tool Box" /S
```

### 1.3 Backend Bootstrap
```pwsh
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Key endpoints now live at `http://localhost:8000` (Swagger UI under `/docs`).

### 1.4 Frontend Bootstrap
```pwsh
cd packages/client
npm install
npm run dev
```
Vite serves the SPA on `http://localhost:5173` with `/api` proxying to `localhost:8000`.

### 1.5 Docker Compose (Production Parity)
```pwsh
# Runs FastAPI, Vue client, and Nginx proxy
./docker-start.ps1
# or manually
docker compose up --build
```
Expose: API `:8000`, Client `:8080`, Proxy `:8088`.

---

## 2. System Architecture Tour

### 2.1 Top-Level Layout
```
services/api/            FastAPI backend, CAM engines, routers
packages/client/         Vue 3 SPA (labs, Art Studio, CAM dashboards)
packages/shared/         Cross-cutting utilities & types
projects/                Standalone sandboxes (RMOS, Rosette, etc.)
docs/                    Patch notes, quick references, onboarding guides
scripts/, tools/         PowerShell + Bash smoke suites and helpers
```

### 2.2 Backend Highlights
- **Routers** live under `services/api/app/routers/` and are grouped by module (geometry, adaptive, blueprint, helical, machines).
- **CAM engines** (`services/api/app/cam/`) host adaptive pocketing (L-series), feed-time models, and trochoidal logic.
- **Post-processors** reside in `services/api/app/data/posts/*.json` with headers/footers for each CNC dialect.
- **Utilities**: `util/units.py` (mm/inch scaling), `util/exporters.py` (DXF/SVG), `utils/post_presets.py` (arc/dwell modes).
- **Versioning pattern**: keep legacy imports (e.g., `adaptive_core_l1`, `adaptive_core_l2`, `adaptive_core_l3`) and avoid breaking routers.

### 2.3 Frontend Highlights
- Vue 3 Composition API with `<script setup lang="ts">` standard.
- Views under `packages/client/src/views/` (AdaptiveKernelLab, BlueprintLab, ArtStudio, etc.).
- Components under `packages/client/src/components/` with specialized subfolders (e.g., `curvelab/`, `posts/`, `rmos/`).
- State handled with Pinia stores in `packages/client/src/stores/`.
- Shared styling via Tailwind (utility-first) plus small CSS modules.

### 2.4 Data Flow (Typical CAM Job)
```
DXF Upload → BlueprintLab (Vue) → /api/dxf/... (FastAPI) → Geometry validation → Adaptive plan → Post export
        ↑                                            ↓
   CurveLab modal ← Inline curve report  ← /dxf/preflight/curve_report
```

### 2.5 Documentation Strategy
- Every major module ships three docs: overview, patch summary, quick reference (see `ADAPTIVE_POCKETING_MODULE_L.md`, `PATCH_L3_SUMMARY.md`, etc.).
- `AGENTS.md` + `.github/copilot-instructions.md` define agent behavior; read both before writing automation.
- Legacy directories (`Luthiers Tool Box/`, `Guitar Design HTML app/`, etc.) are **read-only references**.

---

## 3. Patch Integration Guide

### 3.1 Patch Naming
- **Letters (A–W)** cover general features (export systems, Art Studio, etc.).
- **L-series**: Adaptive pocketing evolution.
- **M-series**: Machine profiles and analytics.
- **N-series**: Post processors and CAM Essentials.
- Keep doc references updated when touching these modules (e.g., editing `adaptive_core_l3.py` means updating `PATCH_L3_SUMMARY.md`).

### 3.2 Working a Patch Bundle
1. **Read the source bundle** (often under `ToolBox_*` directories). Do not copy wholesale—port relevant files into `/services` or `/packages`.
2. **Plan with Todos**: break tasks into API, UI, docs, tests.
3. **Implement** with incremental commits; prefer `create_file`/`apply_patch` to keep diffs crisp.
4. **Document**: add or update quick references, mention patch letter in doc headings.
5. **Test** using the nearest script (e.g., `test_adaptive_l2.ps1`).

### 3.3 Common Pitfalls
- Deleting or altering reference archives (forbidden).
- Changing API request/response schemas without updating clients and docs.
- Skipping metadata injection in exports `(POST=<id>;UNITS=<units>;DATE=...)`.
- Mixing units internally—always convert at the boundary.

### 3.4 Merge Discipline
- Keep `main` deployable; no experimental code without feature flags.
- Use `git status` often—repo contains thousands of files and long paths.
- Coordinate with doc updates; CI expects documentation for new features.

---

## 4. Testing Workflow

### 4.1 Tiers
1. **Unit tests** (target 80% coverage): run `pytest` for backend modules, `npm run test` for frontend packages when available.
2. **Smoke scripts** (PowerShell-first):
   - `test_adaptive_l1.ps1`, `test_adaptive_l2.ps1` for adaptive planner.
   - `test_blueprint_lab.ps1` for DXF ingestion loops.
   - `test_post_chooser.ps1` for multi-post exports.
   - `test_phaseX_*.ps1` for Art Studio release validation.
3. **CI Workflows** under `.github/workflows/` mirror the scripts; ensure new features have at least one automation hook.

### 4.2 Running Tests
```pwsh
# Backend lint + unit
cd services/api
.\.venv\Scripts\Activate.ps1
pytest -q
ruff check .

# Client build smoke
cd packages/client
npm run build

# Adaptive smoke example
pwsh ./test_adaptive_l2.ps1
```

### 4.3 Coverage Tracking
- Goal: raise Python coverage to 80% (currently ~40%). Add parametrized tests in `services/api/app/tests/` mirroring routers.
- For frontend, prefer Vitest snapshots for deterministic UI pieces; labs rely on manual verification but aim to add targeted tests.

### 4.4 Test Data
- Use provided fixtures (`test_bridge*.dxf`, `tmp_bridge.json`, etc.).
- Never commit proprietary instrument DXFs—use sanitized versions under `tests/` directories.

---

## 5. Debugging & Troubleshooting

### 5.1 Common Backend Issues
- **`ezdxf` ImportError**: ensure `pip install -r requirements.txt` succeeded; some features degrade without it.
- **CORS failures**: check `services/api/app/main.py` for allowed origins; adjust `.env` if running through Docker.
- **Unit mismatch bugs**: log geometry widths; `_mm_diag` helper in `dxf_preflight_router.py` helps detect scaling mistakes.
- **Slow adaptive planning**: verify `pyclipper` is using release wheels; consider reducing `stepover` for debugging.

### 5.2 Frontend Issues
- **Vite Proxy**: confirm `/api` proxy configured in `vite.config.ts`; 404 often means backend not running or port mismatch.
- **LocalStorage presets**: pipelines/labs cache JSON under keys like `ltb_pipeline_adaptive_preset_v1`. Clear storage when values look stale.
- **Canvas artifacts**: when touching labs, throttle re-render by wrapping watchers in `requestAnimationFrame` if necessary.

### 5.3 Docker Debugging
- Use `docker compose logs -f api` to inspect FastAPI output.
- For `proxy` service, ensure SSL cert paths exist; missing certs will prevent Nginx start.
- If volumes conflict on Windows, move repo to a short path (e.g., `C:\ltb`).

### 5.4 Logging Helpers
- Backend uses standard `logging` configured in `main.py`; set `LOG_LEVEL=DEBUG` in environment to expose more detail.
- Some scripts write to `reports/` (CSV/JSON). Check there when tests report “See reports for details”.

### 5.5 Escalation Checklist
1. Capture failing command output (PowerShell transcript helps).
2. Note Git SHA + branch.
3. Identify affected module (L-series, Blueprint, etc.).
4. Update relevant quickref doc with “Known Issues” snippet if bug persists.

---

## 6. Contribution Workflow

1. **Sync main**: `git pull origin main`.
2. **Create feature branch**: `git checkout -b feature/<short-description>`.
3. **Track work with Todos** via the provided automation (one in-progress item at a time).
4. **Use apply_patch/create_file** for deterministic diffs.
5. **Run targeted tests** before pushing.
6. **Document** in `/docs` and update quickrefs.
7. **Open PR** referencing roadmap item (e.g., “P3.3 Developer Onboarding”).

---

## 7. Reference Checklist

- [ ] Backend + frontend run locally.
- [ ] Essential docs read (`ADAPTIVE_POCKETING_MODULE_L.md`, `PATCH_K_EXPORT_QUICKREF.md`, `BLUEPRINT_LAB_QUICKREF.md`).
- [ ] Copilot instructions understood (see `.github/copilot-instructions.md`).
- [ ] Smoke tests executed for touched modules.
- [ ] Documentation updated (this file, quickrefs, or module notes).
- [ ] CI status green (or failing tests understood and noted).

---

## 8. Helpful Links

| Area | File / Script |
| ---- | ------------- |
| Adaptive Pocketing | `ADAPTIVE_POCKETING_MODULE_L.md`, `test_adaptive_l2.ps1` |
| Blueprint Pipeline | `BLUEPRINT_LAB_QUICKREF.md`, `test_blueprint_lab.ps1` |
| Post Chooser / Export | `PATCH_K_EXPORT_QUICKREF.md`, `test_post_chooser.ps1` |
| Helical Ramping v16.1 | `ART_STUDIO_V16_1_QUICKREF.md`, `smoke_v161_helical.ps1` |
| RMOS Sandbox | `projects/rmos/README.md`, `docs/RMOS_Onboarding.md` |
| Coding Policy | `CODING_POLICY.md`, `.github/copilot-instructions.md` |

---

_Questions? Ping the maintainer listed in `TEAM_ASSEMBLY_ROADMAP.md` or leave notes in `reports/triage.md` before diving deeper._
