4️⃣ (Optional) Doc stub: docs/ArtStudio/ArtStudio_Bracing_Integration.md

Totally optional, but this nails it down for future-you and collaborators.

# Art Studio – Bracing Integration

## Backend Wiring Overview

Bracing physics currently lives in the migrated legacy module:

- `pipelines/bracing/bracing_calc.py`
  - `calculate_brace_section(...)`
  - `estimate_mass_grams(...)`

To integrate this into the modern ToolBox stack, we have:

1. **Calculator façade:**

   - `services/api/app/calculators/bracing_calc.py`
     - `BracingCalcInput`
     - `BraceSectionResult`
     - `calculate_brace_section(...)`
     - `estimate_mass_grams(...)`

2. **Calculator service layer:**

   - `services/api/app/calculators/service.py`
     - `calculate_bracing_section(...)`
     - `estimate_bracing_mass_grams(...)`

3. **Art Studio router:**

   - `services/api/app/art_studio/bracing_router.py`
     - `POST /api/art-studio/bracing/preview`

## Call Flow

```text
Art Studio UI (future)
    │
    ▼
POST /api/art-studio/bracing/preview
    │
    ▼
calculators.service.calculate_bracing_section(...)
    │
    ▼
calculators.bracing_calc.calculate_brace_section(...)
    │
    ▼
pipelines.bracing.bracing_calc.calculate_brace_section(...)


This preserves the legacy bracing math while giving RMOS/Art Studio a stable
entrypoint for future development.


---

### How to apply this bundle

1. **Create** the new files:

- `services/api/app/calculators/bracing_calc.py`
- `services/api/app/art_studio/__init__.py`
- `services/api/app/art_studio/bracing_router.py`
- (Optional) `docs/ArtStudio/ArtStudio_Bracing_Integration.md`

2. **Patch** `services/api/app/calculators/service.py` with the import + two new functions.

3. **Include** the router into your FastAPI app.

After that, you can:

- let CoPilot help you refine `BracingCalcInput` to match real parameters,
- gradually migrate Art Studio UI to call `/api/art-studio/bracing/preview`,
- and eventually move the actual math from `pipelines.bracing.bracing_calc` into `calculators/bracing_calc.py` if you want everything under one roof.

If you want the **next bundle** to be a tiny `pytest` file that hits `/api/art-studio/bracing/previ