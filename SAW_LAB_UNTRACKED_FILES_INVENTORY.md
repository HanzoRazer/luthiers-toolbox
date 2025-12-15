# CNC Saw Lab — Untracked Files Inventory

**Generated:** December 6, 2025  
**Branch:** `feature/rmos-2-0-skeleton`  
**Status:** ❌ ALL files listed below are UNTRACKED (never committed to git)

---

## 📁 CORE APPLICATION CODE

### Frontend — Vue Components
| File | Path |
|------|------|
| `SawLabView.vue` | `packages/client/src/views/SawLabView.vue` |
| `SawLabShell.vue` | `packages/client/src/components/saw_lab/SawLabShell.vue` |
| `SawLabQueuePanel.vue` | `packages/client/src/components/saw_lab/SawLabQueuePanel.vue` |
| `SawLabDiffPanel.vue` | `packages/client/src/components/saw_lab/SawLabDiffPanel.vue` |
| `SawBatchPanel.vue` | `packages/client/src/components/saw_lab/SawBatchPanel.vue` |
| `SawContourPanel.vue` | `packages/client/src/components/saw_lab/SawContourPanel.vue` |
| `SawSlicePanel.vue` | `packages/client/src/components/saw_lab/SawSlicePanel.vue` |

### Frontend — Stores
| File | Path |
|------|------|
| `sawLearnStore.ts` | `packages/client/src/stores/sawLearnStore.ts` |

### Backend — API Routers
| File | Path |
|------|------|
| `saw_blade_router.py` | `services/api/app/routers/saw_blade_router.py` |
| `saw_gcode_router.py` | `services/api/app/routers/saw_gcode_router.py` |
| `saw_telemetry_router.py` | `services/api/app/routers/saw_telemetry_router.py` |
| `saw_validate_router.py` | `services/api/app/routers/saw_validate_router.py` |

### Backend — Saw Lab Core (`services/api/app/saw_lab/`)
| File | Path |
|------|------|
| `__init__.py` | `services/api/app/saw_lab/__init__.py` |
| `models.py` | `services/api/app/saw_lab/models.py` |
| `geometry.py` | `services/api/app/saw_lab/geometry.py` |
| `path_planner.py` | `services/api/app/saw_lab/path_planner.py` |
| `toolpath_builder.py` | `services/api/app/saw_lab/toolpath_builder.py` |
| `risk_evaluator.py` | `services/api/app/saw_lab/risk_evaluator.py` |
| `debug_router.py` | `services/api/app/saw_lab/debug_router.py` |
| `debug_schemas.py` | `services/api/app/saw_lab/debug_schemas.py` |

### Backend — Saw Lab Calculators (`services/api/app/saw_lab/calculators/`)
| File | Path |
|------|------|
| `__init__.py` | `services/api/app/saw_lab/calculators/__init__.py` |
| `saw_bite_load.py` | `services/api/app/saw_lab/calculators/saw_bite_load.py` |
| `saw_deflection.py` | `services/api/app/saw_lab/calculators/saw_deflection.py` |
| `saw_heat.py` | `services/api/app/saw_lab/calculators/saw_heat.py` |
| `saw_kickback.py` | `services/api/app/saw_lab/calculators/saw_kickback.py` |
| `saw_rimspeed.py` | `services/api/app/saw_lab/calculators/saw_rimspeed.py` |

### Backend — CAM Core Saw Lab (`services/api/app/cam_core/saw_lab/`)
| File | Path |
|------|------|
| `__init__.py` | `services/api/app/cam_core/saw_lab/__init__.py` |
| `models.py` | `services/api/app/cam_core/saw_lab/models.py` |
| `operations.py` | `services/api/app/cam_core/saw_lab/operations.py` |
| `queue.py` | `services/api/app/cam_core/saw_lab/queue.py` |
| `learning.py` | `services/api/app/cam_core/saw_lab/learning.py` |
| `saw_blade_registry.py` | `services/api/app/cam_core/saw_lab/saw_blade_registry.py` |
| `saw_blade_validator.py` | `services/api/app/cam_core/saw_lab/saw_blade_validator.py` |

### Backend — PDF Importer (`services/api/app/cam_core/saw_lab/importers/`)
| File | Path |
|------|------|
| `pdf_saw_blade_importer.py` | `services/api/app/cam_core/saw_lab/importers/pdf_saw_blade_importer.py` |

### Backend — Toolpath Engine
| File | Path |
|------|------|
| `saw_engine.py` | `services/api/app/toolpath/saw_engine.py` |

---

## 📄 DOCUMENTATION FILES

### Root Level Docs
| File | Path |
|------|------|
| `CNC Saw Lab — Full Checkpoint_Developer Audit Guide.txt` | `./CNC Saw Lab — Full Checkpoint_Developer Audit Guide.txt` |
| `CNC Saw Lab — Recommended Repo Strurcture.md` | `./CNC Saw Lab — Recommended Repo Strurcture.md` |
| `CNC Saw Lab.md` | `./CNC Saw Lab.md` |
| `CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md` | `./CNC_SAW_LAB_MISSING_COMPONENTS_VISUAL.md` |
| `CNC_SAW_LAB_RECONCILIATION_REPORT.md` | `./CNC_SAW_LAB_RECONCILIATION_REPORT.md` |
| `CNC_Saw_Lab_Handoff.md` | `./CNC_Saw_Lab_Handoff.md` |
| `CP_S50_SAW_BLADE_REGISTRY.md` | `./CP_S50_SAW_BLADE_REGISTRY.md` |
| `CP_S51_SAW_BLADE_VALIDATOR.md` | `./CP_S51_SAW_BLADE_VALIDATOR.md` |
| `CP_S53_SAW_OPERATION_PANELS.md` | `./CP_S53_SAW_OPERATION_PANELS.md` |
| `SAW_LAB_2_0_QUICKREF.md` | `./SAW_LAB_2_0_QUICKREF.md` |
| `RMOS_STUDIO_SAW_PIPELINE.md` | `./RMOS_STUDIO_SAW_PIPELINE.md` |
| `SawLab_2_0_Test_Hierarchy.md` | `./SawLab_2_0_Test_Hierarchy.md` |
| `SawLab_Saw_Physics_Debugger.md` | `./SawLab_Saw_Physics_Debugger.md` |
| `Saw_Lab_2_0_Integration_Plan.md` | `./Saw_Lab_2_0_Integration_Plan.md` |
| `Saw_Path_Planner_2_1_Upgrade_Plan.md` | `./Saw_Path_Planner_2_1_Upgrade_Plan.md` |
| `Saw Lab 2.0 — Architecture Overview.md` | `./Saw Lab 2.0 — Architecture Overview.md` |
| `Saw Lab 2.0 Code Skeleton.md` | `./Saw Lab 2.0 Code Skeleton.md` |

### Docs Folder
| File | Path |
|------|------|
| `CNC_Saw_Blade_RFQ.md` | `docs/CNC_Saw_Blade_RFQ.md` |
| `CNC_Saw_Lab_Conversation.md` | `docs/CNC_Saw_Lab_Conversation.md` |
| `CNC_Saw_Lab_Technical.md` | `docs/CNC_Saw_Lab_Technical.md` |
| `README.md` | `docs/CNC_Saw_Lab/README.md` |

---

## 🧪 TEST FILES

| File | Path |
|------|------|
| `test_saw_lab_2_0.ps1` | `scripts/test_saw_lab_2_0.ps1` |
| `test_saw_blade_registry.ps1` | `./test_saw_blade_registry.ps1` |
| `test_saw_blade_validator.ps1` | `./test_saw_blade_validator.ps1` |
| `test_saw_frontend_integration.ps1` | `./test_saw_frontend_integration.ps1` |
| `test_saw_telemetry.ps1` | `./test_saw_telemetry.ps1` |
| `test_saw_lab_integration.py` | `./test_saw_lab_integration.py` |
| `test_saw_toolpath_builder.py` | `./test_saw_toolpath_builder.py` |

---

## 📦 DATA FILES

| File | Path |
|------|------|
| `saw_lab_blades.json` | `./saw_lab_blades.json` |
| `Circular Saw Blade Specifications.pdf` | `./Circular Saw Blade Specifications.pdf` |
| `Sawblade Anatomy Trend Tool Technology.pdf` | `./Sawblade Anatomy Trend Tool Technology.pdf` |

---

## 🔧 STANDALONE PYTHON SCRIPTS (Root Level)

| File | Path |
|------|------|
| `calculators_saw_bite_load.py` | `./calculators_saw_bite_load.py` |
| `calculators_saw_deflection.py` | `./calculators_saw_deflection.py` |
| `calculators_saw_heat.py` | `./calculators_saw_heat.py` |
| `calculators_saw_kickback.py` | `./calculators_saw_kickback.py` |
| `calculators_saw_rimspeed.py` | `./calculators_saw_rimspeed.py` |
| `saw_calculators_service.py` | `./saw_calculators_service.py` |
| `saw_lab_debug_schemas.py` | `./saw_lab_debug_schemas.py` |
| `saw_lab_path_planner.py` | `./saw_lab_path_planner.py` |
| `Saw_Planner_Config.py` | `./Saw_Planner_Config.py` |
| `Saw Lab 2.0 Code Skeleton.py` | `./Saw Lab 2.0 Code Skeleton.py` |
| `Saw Lab 2.0 Skeleton.py` | `./Saw Lab 2.0 Skeleton.py` |
| `Saw Lab 2.0 testable.py` | `./Saw Lab 2.0 testable.py` |
| `toolpath_saw_engine.py` | `./toolpath_saw_engine.py` |
| `Wave 5 _ Saw Lab_Physics_plug-in.txt` | `./Wave 5 _ Saw Lab_Physics_plug-in.txt` |

---

## 📊 SUMMARY

| Category | File Count |
|----------|------------|
| **Frontend (Vue + TS)** | 8 files |
| **Backend Routers** | 4 files |
| **Backend Core** | 8 files |
| **Backend Calculators** | 6 files |
| **Backend CAM Core** | 8 files |
| **Toolpath Engine** | 1 file |
| **Documentation** | 17+ files |
| **Test Scripts** | 7 files |
| **Data Files** | 3 files |
| **Standalone Scripts** | 14 files |
| **TOTAL** | ~76 files |

---

## ⚡ QUICK COMMIT COMMAND

To commit all essential Saw Lab code (excluding standalone scripts and PDFs):

```powershell
git add packages/client/src/views/SawLabView.vue
git add packages/client/src/components/saw_lab/
git add packages/client/src/stores/sawLearnStore.ts
git add services/api/app/routers/saw_blade_router.py
git add services/api/app/routers/saw_gcode_router.py
git add services/api/app/routers/saw_telemetry_router.py
git add services/api/app/routers/saw_validate_router.py
git add services/api/app/saw_lab/
git add services/api/app/cam_core/saw_lab/
git add services/api/app/toolpath/saw_engine.py
git add docs/CNC_Saw_Lab/
git add scripts/test_saw_lab_2_0.ps1

git commit -m "feat(saw-lab): Add CNC Saw Lab module - CP-S50 through CP-S63

- Frontend: SawLabView, 6 panel components, sawLearnStore
- Backend: 4 routers (blade, gcode, telemetry, validate)
- Core: calculators, path planner, toolpath builder, risk evaluator
- CAM Core: blade registry, validator, PDF importer, queue, learning
- Docs: CNC_Saw_Lab technical documentation
- Tests: integration test scripts"
```
