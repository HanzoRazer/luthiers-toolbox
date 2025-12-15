/docs/governance/LPMD_Checklist.md
# Legacy Pipeline Migration Directive – Checklist

This checklist is the **human-facing companion** to the LPMD spec and tools.

Use it whenever you:
- Refactor `server/pipelines`
- Migrate subsystems into `services/api/app`
- Prepare to delete or archive old code

---

## 1. Prepare

- [ ] Confirm `Legacy_Pipeline_Migration_Directive.md` exists under `docs/governance/`.
- [ ] Confirm this checklist file exists under `docs/governance/`.
- [ ] Ensure `server/pipelines/` is **committed** and not ignored.

---

## 2. Run Inventory (Local or CI)

### Option A – Local PowerShell

From repo root:

- [ ] Run: `.\LPMD_Runner.ps1`
- [ ] Confirm these files are generated:
  - `lpmd_python_inventory.txt`
  - `lpmd_data_inventory.txt`

### Option B – GitHub Actions

- [ ] Go to **Actions** → **LPMD Inventory Scan**.
- [ ] Trigger the workflow (`Run workflow`).
- [ ] Download the artifact `lpmd-inventory`.
- [ ] Extract:
  - `lpmd_python_inventory.txt`
  - `lpmd_data_inventory.txt`

---

## 3. Identify High-Value Targets

From `lpmd_python_inventory.txt`:

- [ ] Highlight lines with `MISSING IN services/api/app` for files that:
  - Contain calculators/physics (heat, chipload, deflection, rim speed, bracing, rosette, hardware).
  - Generate DXF/G-Code or geometry for core tools.

From `lpmd_data_inventory.txt`:

- [ ] Highlight lines with `MISSING DATA IN services/api/app` for:
  - Tool libraries (`tool_library.json`, etc.)
  - Blade libraries (`*blades*.json`)
  - Material libraries
  - ROI/business preset data

---

## 4. Classify by Priority

For each highlighted item:

- [ ] Mark as **HIGH** if:
  - Physics / safety-related
  - Core geometry or calculator for lutherie, RMOS, or Saw Lab
- [ ] Mark as **MEDIUM** if:
  - Planning utility, DXF cleaners, G-Code explainers, wiring tools
- [ ] Mark as **LOW** if:
  - One-off scripts, legacy prototypes, UI helpers

*(You can keep this classification in `LPMD_Migration_Report_Template.md`.)*

---

## 5. Plan Migration

For each **HIGH priority** item:

- [ ] Decide target location:
  - Calculator → `services/api/app/calculators/`
  - Toolpath / DXF / G-Code → `services/api/app/toolpath/`
  - Data → `services/api/app/data/`
- [ ] Create or update facade in:
  - `services/api/app/calculators/service.py`
  - `services/api/app/rmos/feasibility.py`
  - or relevant service/router

For each **MEDIUM** item:

- [ ] Decide whether to migrate now or later.
- [ ] If deferring, note it in the migration report.

---

## 6. Execute Migration

For each selected file:

- [ ] Copy code/data into the target folder in `services/api/app/`.
- [ ] Clean imports / paths to match new structure.
- [ ] Add at least one smoke test in `services/api/app/tests/`.
- [ ] Commit as a named bundle, e.g.:
  - `feat/calculators-migrate-rosette`
  - `feat/data-migrate-tool-library`

---

## 7. Finalize and Document

- [ ] Fill out `LPMD_Migration_Report_Template.md` for this run.
- [ ] Commit the report (or store it under `docs/migration_reports/`).
- [ ] If appropriate, deprecate or archive the migrated `server/pipelines` modules.

---
