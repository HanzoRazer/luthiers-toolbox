# AGENTS.md — Luthier’s Tool Box Guidance for Codex Agents

This document instructs Codex on how to explore, edit, and extend the **Luthier’s Tool Box** monorepo.  
Follow these rules unless explicitly overridden by the user or project maintainers.

---

## 1. Repository Structure (Actual)

- **services/**
  - `api/` – Primary FastAPI backend (`services/api/app/` contains routers, schemas, CAM engines, post configs).
  - `blueprint-import/` – Blueprint extraction microservice.

- **packages/**
  - `client/` – Vue 3 + TypeScript SPA (`src/views`, `src/components`, `src/stores`, `src/models`).
  - `shared/` – Cross-package utilities and types.

- **projects/**
  - Self-contained subsystems (e.g., `projects/rmos/` → Rosette Manufacturing OS process-control docs, guides, tests).

- **scripts/**
  - PowerShell-first smoke suites (with bash mirrors) used by local dev + CI (`test_adaptive_l1.ps1`, `Test-RMOS-Sandbox.ps1`, etc.).

- **docs/**
  - Patch notes, integration guides, architecture diagrams. Every major feature has a companion quickref.

- **docker/**
  - Container builds for API, client, and Nginx proxy plus compose files.

- **Legacy reference dirs**
  - `Guitar Design HTML app/`, `Luthiers Tool Box/`, `ToolBox_*` archives, etc. **Do not modify** unless the user explicitly asks; they are historical artifacts.

---

## 2. Coding Standards

### Backend (FastAPI / Python 3.11+)
- Organize routers under `services/api/app/routers/` and register them in `main.py` via `APIRouter(..., tags=[...])`.
- Use async endpoints, explicit type hints, and Pydantic models for all request/response schemas.
- Centralize shared logic in `services/api/app/cam/`, `util/`, or `services/` helpers—no ad-hoc modules.
- Handle units (mm ↔ inch) with `services/api/app/util/units.py`; never mix unit systems internally.
- Follow existing error patterns (`HTTPException`, conservative fallbacks) and keep exports compatible with DXF R12/SVG requirements.

### Frontend (Vue 3 + TypeScript)
- Use `<script setup lang="ts">` for every component and view.
- Fetch data through typed helpers or composables; maintain state in Pinia stores (`packages/client/src/stores`).
- Keep geometry/canvas math in dedicated utilities; UI components should stay declarative.
- Respect existing lab/view layout conventions (Art Studio, Blueprint Lab, CAM Essentials, RMOS sandbox) and reuse shared components when possible.

### Shared Conventions
- Every change that affects behavior must be accompanied by or referenced in an existing patch/quickref doc.
- Avoid renaming routes, API contracts, or filesystem paths without user approval—external tooling depends on them.
- Prefer pure, loggable functions inside CAM/pipeline modules so simulations can be replayed.
- Keep comments purposeful; prioritize descriptive docstrings and quickrefs over inline narration.

---

## 3. Task Rules for Codex

- Keep tasks atomic: one feature/fix per request, scoped to the relevant subsystem (API, client, scripts, docs, etc.).
- When touching multiple areas, explain cross-impact clearly and stage edits logically.
- Present changes as diffs; do not rewrite large files without justification.
- Ask before major refactors, schema changes, or API renames—assume other teams consume these surfaces.
- Respect do-not-touch directories (legacy archives) unless explicitly instructed otherwise.

---

## 4. Testing Rules

- Prefer the project’s scripted smoke tests (`scripts/*.ps1` / `.sh`) for feature verification; run the one closest to the subsystem you modified.
- Python modules should be validated with `pytest` where coverage exists; add targeted tests when altering CAM logic.
- Frontend work should include `npm run test` or the specific lab smoke checklist if provided.
- Every new API endpoint or router must ship with at least one smoke test (PowerShell is the canonical format) plus CI wiring when appropriate.
- Capture test steps/results in your response so the user can reproduce them.

---

## 5. Documentation Requirements

- Significant features/patches require updates to the relevant docs directory (`docs/`, `projects/<module>/`, or named quickrefs).
- Include code snippets, API payloads, and workflow notes so CAM operators can follow along without diving into code.
- When structural changes occur (new routers, stores, pipelines), add architecture notes describing data flow and integration points.
- Keep Rosette Manufacturing OS (RMOS) and other subsystems documented in their sandbox folders to preserve historical continuity.

---

## 6. Module & Subsystem Awareness

- **Module K** – Geometry import & multi-post export. Touch `geometry_router.py`, `util/exporters.py`, and post configs carefully.
- **Module L (L.0 → L.3)** – Adaptive pocketing engine with spiralizer, trochoids, and jerk-aware timing. CAM math lives in `services/api/app/cam/`.
- **Module M (M.1 → M.4)** – Machine profiles, energy modeling, feed overrides. Coordinate with `machines_router.py`, `cam_opt_router.py`, and related stores.
- **Rosette Manufacturing OS (RMOS)** – Backend endpoints under `/rmos`, docs in `projects/rmos/`, UI components in `packages/client/src/components/rmos/`.
- **Art Studio v16.1 & Blueprint Lab** – Large, multi-router features with their own views; keep them synchronized with associated quickrefs and CI workflows.

### Fret Slots CAM Module (Wave 15–E)

**Backend:**
- `services/api/app/calculators/fret_slots_cam.py`
- Multi-format export endpoint: `/api/cam/fret_slots/export_multi_post`
- Preview endpoint: `/api/cam/fret_slots/preview` (if present)

**Primary responsibilities:**
- Compute fret-slot positions for a given instrument model (`model_id`)
- Generate DXF/SVG/G-code for slotting operations
- Integrate with RMOS feasibility (chipload, heat, deflection) via calculators service

**Key contracts:**
- **Inputs:**
  - `model_id: str` (e.g. `"benedetto_17"`, `"dreadnought_14"`)
  - `mode: "straight" | "fan_fret"` (fan-fret optional)
  - `fret_count: int`
  - `slot_depth_mm: float`
  - `slot_width_mm: float`
  - `post_ids: List[str]` for multi-post export (e.g. `["grbl", "mach4"]`)
- **Outputs:**
  - `preview` → JSON + optional DXF/SVG snippets
  - `export_multi_post` → ZIP with DXF, SVG, one `.nc` per `post_id`, and `*_meta.json`

**Agent guidance:**
- Do **not** invent new endpoints; use `/api/cam/fret_slots/preview` and `/export_multi_post`.
- Use `instrument_geometry` loader (`load_model_spec`) for scale and layout; do not recalc scale math in-place.
- Defer physics (chipload/heat/deflection) to `calculators/service.py` and RMOS feasibility, **not** inside this module.

---

Understand which module you are touching before editing so versioned docs and smoke suites stay valid.

---

## 7. Legacy Assets & Restrictions

- Directories such as `Luthiers Tool Box/`, `Guitar Design HTML app/`, `ToolBox_*` bundles, and other archives are reference-only. Never modify or delete them unless explicitly requested—they may hold production CAM artifacts.
- Maintain compatibility with existing patch notes (A–W, L-series, M-series, N-series). If your work builds on a patch, cite it.

---

## 8. Summary

Codex must deliver **modular, testable, and well-documented** changes that align with the structure above.  
Always confirm scope, respect subsystem boundaries, and leave the project in a state that other teams can understand and reproduce.
