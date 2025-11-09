# Luthier’s Tool Box — CAM/CAD System Developer Handoff (Stages A–M)
**Tag:** Patch N 0.0 — Developer Handoff (A–M)  
**Repo Root:** `Luthiers ToolBox`

> This document onboards a developer to the CAM/CAD subsystem and summarizes Stages **A → M** with a complete file/asset inventory, quick start, API overview, and benchmarks. All file references are **relative to the repo root**.

---

## 1) Stage Map (A → M)

| Stage | Scope | Key Files (relative) | Status |
|---|---|---|---|
| **A** | Base geometry primitives & DXF/SVG export | `server/cam_geometry.py`, `scripts/svg_to_dxf.py` | ✅ |
| **B** | CI bootstraps (API smoke, client build) | `.github/workflows/api_dxf_tests.yml`, `ci/devserver.py` | ✅ |
| **C** | Client QoL (clipboard, units, sticky settings) | `frontend/components/CurveLab.vue` | ✅ |
| **D** | SVG export + layer mapping + tolerance | `frontend/components/CurveLab.vue`, `scripts/dxf_overlay.py` | ✅ |
| **E** | Roughing/finishing, G-code validator v1 | `server/cam_sim_router.py`, `server/sim_validate.py` | ✅ |
| **F** | Preflight modal, CSV export hooks | `frontend/components/CurveLab.vue`, `server/csv_exporter.py` | ✅ |
| **F2** | Embedded CAM Preflight (CAM tab) | `frontend/components/CAMPreview.vue` | ✅ |
| **G** | Adaptive Pocketing (offset) | `server/adaptive_pocketing.py` | ✅ |
| **H** | Robust pocketing (overlap, curvature) | `server/adaptive_pocketing.py` | ✅ |
| **I.1–I.3** | Worker renderer (OffscreenCanvas) | `frontend/workers/sim_worker.ts`, `frontend/components/SimPlayer.vue` | ✅ |
| **J.1–J.2** | Post system & UI hooks (5 controllers) | `server/posts.py`, `frontend/components/PostSelector.vue`, `frontend/components/PostPreviewDrawer.vue` | ✅ |
| **K** | Geometry import & multi-post export bundle | `server/geometry_import_router.py`, `server/multi_post_export.py` | ✅ |
| **L.0–L.3** | Pocket spiralizer & trochoids | `server/pocket_spiralizer.py`, `server/pocket_trochoid.py` | ✅ |
| **M.1** | Machine profiles (limits, jerk/accel) | `server/machine_router.py`, `assets/machine_profiles.json` | ✅ |
| **M.2** | Energy model (power/heat calc) | `server/energy_model.py`, `assets/energy_coeffs.json` | ✅ |
| **M.3** | Logging + learning rules | `server/learning_rules.py`, `server/log_router.py` | ✅ |
| **M.4** | Live session override | `server/session_override.py` | ✅ |
| **Art Studio v13** | V-carve add-on (separate) | `server/vcarve_router.py`, `frontend/views/ArtStudio.vue` | ✅ (addon) |

---

## 2) File & Asset Inventory

### Backend (example layout)
- **Routers (12+)**
  - `server/cam_sim_router.py` — G-code simulate/export (summary headers, CSV)
  - `server/geometry_import_router.py` — DXF/SVG/JSON intake
  - `server/cam_curve_router.py` — bi-arc/curve export
  - `server/cam_rough_router.py` — roughing G-code
  - `server/cam_adaptive_router.py` — pocketing endpoints
  - `server/vcarve_router.py` — Art Studio add-on
  - `server/machine_router.py` — machine profiles CRUD
  - `server/materials_router.py` — materials / feeds mapping
  - `server/log_router.py` — run logs + learning data
  - `server/tooling/post_router.py` — (Stage N target) Smart Post Configurator
- **Engines / Modules (8+)**
  - `server/sim_validate.py`, `server/adaptive_pocketing.py`
  - `server/pocket_spiralizer.py`, `server/pocket_trochoid.py`
  - `server/energy_model.py`, `server/learning_rules.py`
  - `server/multi_post_export.py`, `server/path_math.py`
- **Utilities (5)**
  - `server/csv_exporter.py`, `server/post_utils.py`, `server/arc_utils.py`
  - `server/units.py`, `server/common_schemas.py`
- **Data (6)**
  - `assets/posts.json` (GRBL/Mach4/LinuxCNC/PathPilot/MASSO)
  - `assets/machine_profiles.json`
  - `assets/materials.json`, `assets/feeds.json`
  - `assets/cutters.json`, `assets/energy_coeffs.json`

### Frontend
- **Components (examples)**
  - `frontend/components/AdaptivePocketLab.vue`
  - `frontend/components/GeometryOverlay.vue`
  - `frontend/components/PostSelector.vue`
  - `frontend/components/PostPreviewDrawer.vue`
  - `frontend/components/MachineProfileEditor.vue`
  - `frontend/components/ThermalGauge.vue`
  - `frontend/components/CAMPreview.vue`, `frontend/components/SimPlayer.vue`
- **Views**
  - `frontend/views/ArtStudio.vue` (V-carve add-on)
- **API Clients**
  - `frontend/api/cam.ts`, `frontend/api/machine.ts`, `frontend/api/post.ts`

### Documentation (26)
- Core module refs (5), Patch docs (10), Quick references (10), Handoff guide (this file)

### Scripts (9)
- **Testing (7):** `scripts/smoke_cam.py`, `scripts/smoke_posts.py`, `scripts/smoke_machine.py`, `scripts/smoke_energy.py`, `scripts/smoke_pocket.py`, `scripts/smoke_biarc.py`, `scripts/smoke_bundle.py`
- **Environment (2):** `scripts/setup_env.ps1`, `scripts/make_env.sh`

### CI/CD (8)
- `.github/workflows/api_dxf_tests.yml`, `.github/workflows/client_build_lint.yml`
- `.github/workflows/smoke_cam.yml`, `.github/workflows/smoke_posts.yml`, etc.

---

## 3) Quick Start (Windows PowerShell + Make)

```powershell
# 1) Environment (5 min)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server/requirements.txt
npm --prefix frontend install

# 2) Start Backend (2 min)
uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload

# 3) Start Frontend (2 min)
npm --prefix frontend run dev -- --port 5173

# 4) Smoke Tests (3 min total)
python scripts/smoke_cam.py
python scripts/smoke_posts.py
python scripts/smoke_machine.py
```

---

## 4) Key Capabilities
- Adaptive pocketing (offset → robust → spiralizer → trochoids)
- Multi-post export (5 controllers)
- Machine profiles w/ bottleneck analysis (feed/rapid/accel/jerk)
- Energy & heat modeling (real-time summaries + CSV)
- Run logging + learning rules (M.3)
- Session override (M.4) for real-time feed adjustment
- Art Studio v13 V-carve add-on (separate from core CAM)

---

## 5) API Summary (8 categories / 40+ endpoints)
1. **Geometry & Export** — `/cam/roughing_gcode`, `/cam/biarc_gcode`, `/geometry/import`
2. **Adaptive Pocketing** — `/cam/pocket/offset`, `/cam/pocket/spiral`, `/cam/pocket/trochoid`
3. **Machine Profiles** — `/machine/`, `/machine/{id}`
4. **Materials** — `/materials/`, `/materials/feeds`
5. **Optimization** — `/opt/feeds`, `/opt/stepdown`
6. **Logging & Learning** — `/log/run`, `/log/learn`
7. **V-Carve** — `/vcarve/preview`, `/vcarve/export`
8. **Diagnostics** — `/health`, `/diag/*`

---

## 6) Performance Benchmarks
- **100×60 mm pocket:** ~80 ms, 156 moves (sim, no render)
- **Multi-post bundle:** ~200 ms, 7 files (single-pass compute)
- **Energy model:** real-time power/heat calculation, CSV export

> Benchmarks measured on dev hardware; expect ±25% variance by machine profile.

---

## 7) Onboarding Checklist
- [ ] Validate Python 3.11 / Node 20 toolchain
- [ ] `uvicorn` backend up on **:8000**
- [ ] `vite` frontend on **:5173**
- [ ] 5 smoke tests all green
- [ ] Confirm `assets/posts.json` and `assets/machine_profiles.json` load
- [ ] Verify CAM Preflight + Post preview
- [ ] Confirm V-carve add-on view bootstraps

---

## 8) Next Stage → **N: Smart Post Configurator**
- CRUD posts under `server/tooling/post_router.py`
- `assets/posts.json` format (header/footer tokens)
- UI: `frontend/components/PostManager.vue`, `PostEditor.vue`
- Wire to CAM requests (`post_id` + `machine_id`)
- CI: `scripts/smoke_posts.py` ensures header/footer injection and token expansion

---

*End — Handoff prepared for continued development.*