/docs/governance/LPMD_Migration_Report_Template.md
# Legacy Pipeline Migration Report

**Run Date:** YYYY-MM-DD  
**Author:** (Your name or "System")  
**Repo:** Luthier's ToolBox  

---

## 1. Summary

- **Goal of this run:**  
  (e.g., "Migrate rosette calculators and tool library from server/pipelines.")

- **Scope:**  
  (e.g., `server/pipelines/rosette`, `server/pipelines/assets/tool_library.json`)

---

## 2. Inventory Inputs

- **Python inventory file:** `lpmd_python_inventory.txt`
- **Data inventory file:** `lpmd_data_inventory.txt`
- **Other references:**  
  - (e.g., `docs/rosette_notes.md`, older spec docs, etc.)

---

## 3. High-Priority Items (Migrated This Run)

| Legacy Path                                      | New Path                                           | Description                             | Status   |
|--------------------------------------------------|---------------------------------------------------|-----------------------------------------|----------|
| server/pipelines/rosette/rosette_calc.py         | services/api/app/calculators/rosette_calc.py      | Rosette channel geometry calculator     | Migrated |
| server/pipelines/assets/tool_library.json        | services/api/app/data/tool_library.json           | Tool + material library                 | Migrated |
| …                                                | …                                                 | …                                       | …        |

---

## 4. Medium/Low Priority Items (Deferred or Not Migrated)

| Legacy Path                                      | Priority | Rationale for Deferral / Not Migrating Yet          |
|--------------------------------------------------|----------|-----------------------------------------------------|
| server/pipelines/wiring/switch_validate.py       | MEDIUM   | Useful, but not required for current RMOS features  |
| server/pipelines/financial/roi_calc.py          | MEDIUM   | Business calculator; schedule for later             |
| …                                                | …        | …                                                   |

---

## 5. Changes Made in `services/api/app`

### 5.1 New or Updated Modules

- `services/api/app/calculators/rosette_calc.py`
  - **Purpose:** Ported from legacy rosette calculator.
  - **API:** `compute_rosette_channels(spec: RosetteParamSpec) -> RosetteCalcResult`
  - **Used by:** RMOS feasibility, Art Studio views.

- `services/api/app/data/tool_library.json`
  - **Purpose:** Canonical tool/material library for all calculators.
  - **Used by:** Saw Lab calculators, generic calculator service.

### 5.2 Façades / Service Layer

- Updated `services/api/app/calculators/service.py`:
  - Added `calculate_rosette()` → calls `rosette_calc.compute_rosette_channels()`.
  - Added tool library loader → reads `data/tool_library.json`.

---

## 6. Tests

- New tests added:

  - `services/api/app/tests/test_rosette_calculator.py`  
    - ✅ Basic correctness on known input  
    - ✅ Edge-case coverage (if applicable)

- Existing tests impacted:
  - (List any that had to be updated.)

- Test commands executed:

  ```bash
  pytest services/api/app/tests -m "sawlab or rmos"
