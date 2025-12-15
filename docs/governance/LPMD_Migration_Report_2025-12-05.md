# Legacy Pipeline Migration Report

**Run Date:** 2025-12-05  
**Author:** System (AI-assisted)  
**Repo:** Luthier's ToolBox  
**Branch:** feature/rmos-2-0-skeleton

---

## 1. Summary

- **Goal of this run:**  
  Migrate high-priority calculators and tool library from `server/pipelines/` to `services/api/app/`.

- **Scope:**  
  - `server/pipelines/rosette/rosette_calc.py`
  - `server/pipelines/bracing/bracing_calc.py`
  - `server/pipelines/gcode_explainer/explain_gcode_ai.py`
  - `server/assets/tool_library.json`

---

## 2. Inventory Inputs

- **Python inventory file:** `lpmd_python_inventory.txt`
- **Data inventory file:** `lpmd_data_inventory.txt` (empty - no data files in pipelines)
- **Script used:** `LPMD_Runner.ps1`

---

## 3. High-Priority Items (Migrated This Run)

| Legacy Path | New Path | Description | Status |
|-------------|----------|-------------|--------|
| `server/pipelines/rosette/rosette_calc.py` | `services/api/app/pipelines/rosette/rosette_calc.py` | Rosette channel width/depth calculator | ✅ Migrated + Fixed |
| `server/pipelines/bracing/bracing_calc.py` | `services/api/app/pipelines/bracing/bracing_calc.py` | Bracing mass/glue area calculator | ✅ Migrated |
| `server/pipelines/gcode_explainer/explain_gcode_ai.py` | `services/api/app/pipelines/gcode_explainer/explain_gcode_ai.py` | G-code human annotation | ✅ Migrated + Fixed |
| `server/assets/tool_library.json` | `services/api/app/data/tool_library.json` | 12 tools + 7 materials | ✅ Copied |

---

## 4. Medium Priority Items (Migrated This Run)

| Legacy Path | New Path | Description | Status |
|-------------|----------|-------------|--------|
| `server/pipelines/bridge/bridge_to_dxf.py` | `services/api/app/pipelines/bridge/bridge_to_dxf.py` | R12 DXF saddle compensation | ✅ Migrated |
| `server/pipelines/dxf_cleaner/clean_dxf.py` | `services/api/app/pipelines/dxf_cleaner/clean_dxf.py` | Entity→LWPOLYLINE converter | ✅ Migrated + Parameterized |
| `server/pipelines/hardware/hardware_layout.py` | `services/api/app/pipelines/hardware/hardware_layout.py` | Hardware cavity DXF | ✅ Migrated |
| `server/pipelines/rosette/rosette_make_gcode.py` | `services/api/app/pipelines/rosette/rosette_make_gcode.py` | Spiral G-code generator | ✅ Migrated |
| `server/pipelines/rosette/rosette_post_fill.py` | `services/api/app/pipelines/rosette/rosette_post_fill.py` | G-code template filler | ✅ Migrated |
| `server/pipelines/rosette/rosette_to_dxf.py` | `services/api/app/pipelines/rosette/rosette_to_dxf.py` | Minimal DXF circles | ✅ Migrated |
| `server/pipelines/wiring/switch_validate.py` | `services/api/app/pipelines/wiring/switch_validate.py` | Pickup switch validator | ✅ Migrated |
| `server/pipelines/wiring/treble_bleed.py` | `services/api/app/pipelines/wiring/treble_bleed.py` | RC circuit calculator | ✅ Migrated |

---

## 5. Low Priority Items (Deferred)

| Legacy Path | Priority | Rationale for Deferral |
|-------------|----------|------------------------|
| CNC ROI Calculator (inline in `server/app.py`) | MEDIUM | Business tool; extract when needed |

---

## 6. Changes Made in `services/api/app`

### 6.1 New Modules (Full Structure)

```
services/api/app/
├── data/
│   └── tool_library.json          # 12 tools + 7 materials
└── pipelines/
    ├── __init__.py                # Package init (7 modules)
    ├── rosette/
    │   ├── __init__.py            # Exports all rosette functions
    │   ├── rosette_calc.py        # Channel geometry calculator
    │   ├── rosette_make_gcode.py  # Spiral G-code generator (NEW)
    │   ├── rosette_post_fill.py   # Template variable filler (NEW)
    │   └── rosette_to_dxf.py      # Minimal DXF circles (NEW)
    ├── bracing/
    │   ├── __init__.py            # Exports calculation functions
    │   └── bracing_calc.py        # Mass/glue calculator
    ├── gcode_explainer/
    │   ├── __init__.py            # Exports ModalState, explain_line
    │   └── explain_gcode_ai.py    # G-code annotation
    ├── bridge/
    │   ├── __init__.py            # Exports create_dxf, load_model (NEW)
    │   └── bridge_to_dxf.py       # R12 DXF saddle compensation (NEW)
    ├── dxf_cleaner/
    │   ├── __init__.py            # Exports clean_dxf, converters (NEW)
    │   └── clean_dxf.py           # Entity→LWPOLYLINE converter (NEW)
    ├── hardware/
    │   ├── __init__.py            # Exports generate_dxf, run (NEW)
    │   └── hardware_layout.py     # Hardware cavity DXF (NEW)
    └── wiring/
        ├── __init__.py            # Exports validators + calculators (NEW)
        ├── switch_validate.py     # Pickup switch validator (NEW)
        └── treble_bleed.py        # RC circuit calculator (NEW)
```

### 6.2 Bug Fixes Applied During Migration

1. **rosette_calc.py** (line 16):
   - Fixed `TypeError: 'float' object is not iterable` when `inner+outer` is empty
   - Added conditional check before unpacking in `max()`

2. **explain_gcode_ai.py** (line 83):
   - Fixed `SyntaxWarning: "\|" is an invalid escape sequence`
   - Changed `'\|'` to `'\\|'` for proper escaping

3. **clean_dxf.py** (refactored):
   - Parameterized input/output paths (was hardcoded filenames)
   - Added tolerance parameter for endpoint merging
   - Returns stats dict for programmatic use

---

## 7. Tests

### Verification Commands Executed:

```powershell
# Rosette calculator
python -c "from app.pipelines.rosette import compute; result = compute({'soundhole_diameter_mm': 100, 'central_band': {'width_mm': 18, 'thickness_mm': 1}}); print(result)"
# Output: {'soundhole_diameter_mm': 100.0, 'channel_width_mm': 18.16, 'channel_depth_mm': 1.15, ...}

# Bracing calculator
python -c "from app.pipelines.bracing import brace_section_area_mm2, estimate_mass_grams; print(brace_section_area_mm2({'type': 'parabolic', 'width_mm': 10, 'height_mm': 15}), estimate_mass_grams(200, 99, 420))"
# Output: 99.0 8.316...

# G-code explainer
python -c "from app.pipelines.gcode_explainer import ModalState, explain_line; st = ModalState(); print(explain_line('G21 G90', st))"
# Output: ('G21 G90', 'Units → millimeters (G21). Absolute (G90).', ...)

# Tool library
python -c "import json; from pathlib import Path; print(json.loads(Path('app/data/tool_library.json').read_text()).keys())"
# Output: dict_keys(['units', 'materials', 'tools'])
```

---

## 7. Governance Artifacts

| File | Location | Status |
|------|----------|--------|
| `LPMD_Runner.ps1` | Repo root | ✅ Executable |
| `lpmd-inventory.yml` | `.github/workflows/` | ✅ CI workflow |
| `LPMD_Checklist.md` | `docs/governance/` | ✅ Moved |
| `LPMD_Migration_Report_Template.md` | `docs/governance/` | ✅ Moved |
| `Legacy_Pipeline_Migration_Directive.md` | `docs/governance/` | ✅ Moved |
| This report | `docs/governance/` | ✅ Created |

---

## 9. Next Steps

1. [ ] Run `pytest` on new pipelines modules
2. [ ] Wire `rosette_calc.compute()` into RMOS feasibility scorer
3. [ ] Wire `bracing_calc` into Art Studio bracing view (if applicable)
4. [x] ~~Consider migrating MEDIUM priority items in next sprint~~ **DONE**
5. [ ] Archive `server/pipelines/` once verification complete
6. [ ] Create FastAPI router endpoints for new pipelines:
   - `/api/bridge/dxf` - saddle compensation DXF export
   - `/api/dxf/clean` - DXF cleaning endpoint
   - `/api/hardware/layout` - hardware cavity DXF
   - `/api/wiring/validate` - switch combo validation
   - `/api/wiring/treble-bleed` - RC calculator

---

## 10. Migration Statistics

| Category | Count |
|----------|-------|
| High Priority Migrated | 4 |
| Medium Priority Migrated | 8 |
| Total Modules Created | 7 |
| Total Python Files | 11 |
| Bug Fixes Applied | 3 |
| Data Files Migrated | 1 |

---

**Report Generated:** 2025-12-05  
**Last Updated:** 2025-12-05 (Medium priority migration complete)
