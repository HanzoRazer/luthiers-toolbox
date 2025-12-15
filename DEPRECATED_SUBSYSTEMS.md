# Deprecated Subsystems Registry

**Purpose:** Track all archived subsystems with rationale, migration status, and recovery notes.  
**Last Updated:** December 5, 2025  
**Policy:** See `LEGACY_ARCHIVE_POLICY.md` for archival procedures.

---

## Archive Categories

| Category | Location | Description |
|----------|----------|-------------|
| Build Bundles | `__ARCHIVE__/build_bundles/` | AI-generated code bundles (already integrated) |
| Patch Bundles | `__ARCHIVE__/patch_bundles/` | Versioned patch directories (applied) |
| Server Legacy | `__ARCHIVE__/server_legacy/` | Pre-RMOS 2.0 server implementations |
| Legacy Subsystems | `__ARCHIVE__/legacy_subsystems/` | Retired modules and old versions |
| Sandbox History | `__ARCHIVE__/sandbox_history/` | Promoted/retired experiments |

---

## Archived Subsystems

### Build Bundles (Root Python Files)

| Subsystem | Original Location | Archived To | Date | Reason |
|-----------|-------------------|-------------|------|--------|
| RMOS Feasibility | `rmos_feasibility.py`, `rmos_feasibility_2.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/feasibility_scorer.py` |
| RMOS API Contracts | `rmos_api_contracts.py`, `rmos_api_contracts_2.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/api_contracts.py` |
| RMOS Presets | `rmos_presets.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/presets.py` |
| RMOS Profile History | `rmos_profile_history.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/profile_history.py` |
| RMOS Logging | `rmos_logging_ai.py`, `rmos_logs_helper.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/logging_*.py` |
| RMOS AI Analytics | `rmos_ai_analytics.py` | `build_bundles/rmos/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/` |
| Saw Calculators | `calculators_saw_*.py` (5 files) | `build_bundles/saw_lab/` | YYYY-MM-DD | Integrated into `services/api/app/saw_lab/calculators/` |
| Saw Lab Skeletons | `Saw Lab 2.0 *.py` (3 files) | `build_bundles/saw_lab/` | YYYY-MM-DD | Superseded by full implementation |
| Saw Lab Path Planner | `saw_lab_path_planner.py` | `build_bundles/saw_lab/` | YYYY-MM-DD | Integrated into `services/api/app/saw_lab/path_planner.py` |
| Toolpath Engines | `toolpath_*.py` (4 files) | `build_bundles/toolpath/` | YYYY-MM-DD | Integrated into `services/api/app/toolpath/` |
| Art Studio Files | `art_studio_*.py` (10+ files) | `build_bundles/art_studio/` | YYYY-MM-DD | Integrated into `services/api/app/art_studio/` |
| AI Graphics | `ai_graphics_*.py` (4 files) | `build_bundles/ai_graphics/` | YYYY-MM-DD | Integrated into `services/api/app/ai_graphics/` |
| Constraint Profiles | `constraint_profiles_ai.py` | `build_bundles/ai/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/constraint_profiles.py` |
| Calculator Service | `calculators_service.py`, `calculators_service_2.py` | `build_bundles/calculators/` | YYYY-MM-DD | Integrated into `services/api/app/calculators/service.py` |
| Compare Automation | `compare_automation_router.py` | `build_bundles/routers/` | YYYY-MM-DD | Integrated into `services/api/app/routers/` |
| Mode Preview | `mode_preview_routes.py` | `build_bundles/routers/` | YYYY-MM-DD | Integrated into Art Studio routers |
| Schemas | `schemas_logs_ai.py` | `build_bundles/schemas/` | YYYY-MM-DD | Integrated into `services/api/app/rmos/schemas_logs_ai.py` |

---

### Patch Bundle Directories (ToolBox_*)

| Subsystem | Original Location | Archived To | Date | Status |
|-----------|-------------------|-------------|------|--------|
| Patch A-D | `ToolBox_PatchA_*` through `ToolBox_PatchD_*` | `patch_bundles/patches_a_d/` | YYYY-MM-DD | Applied ✅ |
| Patch E-F | `ToolBox_PatchE_*`, `ToolBox_PatchF2_*` | `patch_bundles/patches_e_f/` | YYYY-MM-DD | Applied ✅ |
| Patch G-H | `ToolBox_PatchG_*`, `ToolBox_PatchH_*`, `ToolBox_PatchH0_*` | `patch_bundles/patches_g_h/` | YYYY-MM-DD | Applied ✅ |
| Patch I Series | `ToolBox_PatchI_*`, `ToolBox_PatchI1_*`, `ToolBox_Patch_I1_*` | `patch_bundles/patches_i/` | YYYY-MM-DD | Applied ✅ |
| Patch J Series | `ToolBox_PatchJ_*`, `ToolBox_PatchJ1_*`, `ToolBox_PatchJ2_*` | `patch_bundles/patches_j/` | YYYY-MM-DD | Applied ✅ |
| Patch N Series | `ToolBox_Patch_N*` (N01-N17) | `patch_bundles/patches_n/` | YYYY-MM-DD | Applied ✅ |
| CurveLab Patches | `ToolBox_CurveLab_*` | `patch_bundles/curvelab/` | YYYY-MM-DD | Applied ✅ |
| CurveMath Patches | `ToolBox_CurveMath_*` | `patch_bundles/curvemath/` | YYYY-MM-DD | Applied ✅ |
| Art Studio Patches | `ToolBox_Art_Studio*` | `patch_bundles/art_studio/` | YYYY-MM-DD | Applied ✅ |
| Monorepo Patches | `ToolBox_Monorepo_*`, `ToolBox_Workspace_*` | `patch_bundles/monorepo/` | YYYY-MM-DD | Applied ✅ |
| Scripts Consolidated | `ToolBox_All_Scripts_*` | `patch_bundles/scripts/` | YYYY-MM-DD | Applied ✅ |
| Scripts Recovered | `ToolBox_Scripts_Recovered*` | `patch_bundles/scripts/` | YYYY-MM-DD | Applied ✅ |
| Misc Patches | `ToolBox_DXF_*`, `ToolBox_PathDoctor_*` | `patch_bundles/misc/` | YYYY-MM-DD | Applied ✅ |

---

### Legacy Server

| Subsystem | Original Location | Archived To | Date | Reason |
|-----------|-------------------|-------------|------|--------|
| Legacy Server | `server/` | `server_legacy/server/` | YYYY-MM-DD | Superseded by `services/api/app/` - contains unique pipelines for potential migration |

**Migration Notes:**
- `server/pipelines/bracing/` - Bracing calculator (unique, may migrate later)
- `server/pipelines/hardware/` - Hardware layout (unique, may migrate later)
- `server/pipelines/wiring/` - Wiring calculator (unique, may migrate later)
- `server/pipelines/rosette/` - Demo G-code generator (superseded)
- CAM routers superseded by `services/api/app/routers/cam_*.py`

---

### Legacy Subsystems

| Subsystem | Original Location | Archived To | Date | Reason |
|-----------|-------------------|-------------|------|--------|
| Guitar Design HTML App | `Guitar Design HTML app/` | `legacy_subsystems/` | YYYY-MM-DD | Reference only - not RMOS 2.0 |
| Luthiers Tool Box (old) | `Luthiers Tool Box/` | `legacy_subsystems/` | YYYY-MM-DD | Legacy MVP, superseded |
| Lutherier Project | `Lutherier Project/` | `legacy_subsystems/` | YYYY-MM-DD | CAD project files, not code |
| Feature Extractions | `Feature_*` directories | `legacy_subsystems/features/` | YYYY-MM-DD | Already extracted into main codebase |
| Integration Patches | `Integration_Patch_*` | `legacy_subsystems/integrations/` | YYYY-MM-DD | Already applied |
| Wiring/Finish Bundle | `Luthiers_Tool_Box_Addons_*` | `legacy_subsystems/addons/` | YYYY-MM-DD | Features integrated |
| Smart Guitar Bundle | `Luthiers_ToolBox_Smart_Guitar_*` | `legacy_subsystems/addons/` | YYYY-MM-DD | Separate project |

---

## Recovery Procedures

### To recover archived code:

1. **Locate in archive:**
   ```powershell
   Get-ChildItem -Path "__ARCHIVE__" -Recurse -Filter "*<search_term>*"
   ```

2. **Copy back (don't move):**
   ```powershell
   Copy-Item "__ARCHIVE__/path/to/item" -Destination "target/location" -Recurse
   ```

3. **Update this registry** if recovery is permanent.

4. **Run tests** to verify no conflicts:
   ```powershell
   pytest services/api/app/tests/
   ```

---

## Subsystem Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Applied | Patch/bundle fully integrated into main codebase |
| ⚠️ Partial | Some features integrated, some may need future work |
| 📦 Archived | Moved to `__ARCHIVE__/`, no longer active |
| 🔄 Migrating | In process of being moved to new location |
| ❌ Deprecated | Intentionally retired, will not be migrated |

---

## Governance

- **Before archiving:** Create entry in this document
- **After archiving:** Update status and date
- **Recovery requests:** Document in this file with justification
- **Quarterly review:** Audit `__ARCHIVE__/` for items that can be permanently deleted

---

## Questions for Future Reference

1. **Q: Why keep `server/pipelines/` instead of deleting?**  
   A: Contains unique domain calculators (bracing, hardware, wiring) that may be migrated to RMOS 2.0 later.

2. **Q: Can I delete `ToolBox_*` directories after archiving?**  
   A: Keep in archive for 6 months minimum for provenance tracking, then evaluate.

3. **Q: What about the .zip files in root?**  
   A: Archive alongside their extracted directories for completeness.
