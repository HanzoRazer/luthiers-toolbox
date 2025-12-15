# Orphaned Client Files Inventory

**Generated:** December 7, 2025  
**Branch:** `feature/rmos-2-0-skeleton`

---

## Executive Summary

The repository contains **two client folders** with significant duplication and orphaned code:

| Folder | Status | Files | Tracked in Git |
|--------|--------|-------|----------------|
| `packages/client/src/` | **Primary (Active)** | 148 files | 44 tracked |
| `client/src/` | **Legacy/Orphaned** | 188 files | 3 tracked |

### Key Findings:
- **55 files** have identical names across both folders (potential duplicates)
- **133 files** exist ONLY in `client/src/` (orphaned from primary location)
- **93 files** exist ONLY in `packages/client/src/` (newer additions)
- The `client/` folder appears to be a **legacy version** that was not fully migrated

---

## Folder Structure Comparison

### `packages/client/src/` (Primary - Monorepo Structure)
```
api/
cam_core/
components/
  ├── art/
  ├── artstudio/
  ├── cam/
  ├── common/
  ├── compare/
  ├── curvelab/
  ├── rmos/
  └── saw_lab/
composables/
models/
router/
stores/
types/
utils/
views/
  ├── art/
  └── lab/
```

### `client/src/` (Legacy - Standalone Structure)
```
api/
cam/
  └── compare/
cnc_production/
components/
  ├── art/
  ├── cam/
  ├── compare/
  ├── rosette/
  ├── saw_lab/
  └── toolbox/          ← UNIQUE (89 calculator/toolbox components!)
composables/
labs/
router/
types/
utils/
  └── math/
views/
  ├── art/
  ├── cam/
  ├── lab/
  └── labs/
workers/
```

---

## Orphaned Files (133 files ONLY in `client/src/`)

These files exist in `client/src/` but have NO counterpart in `packages/client/src/`.

### Core Files
| File | Location |
|------|----------|
| `style.css` | `client/src/` |
| `vite-env.d.ts` | `client/src/` |

### API Layer (6 files)
| File | Location |
|------|----------|
| `camRisk.ts` | `client/src/api/` |
| `n15.ts` | `client/src/api/` |
| `n16.ts` | `client/src/api/` |
| `n17_n18.ts` | `client/src/api/` |
| `post.ts` | `client/src/api/` |
| `sawLab.ts` | `client/src/api/` |

### CAM Compare Module (2 files)
| File | Location |
|------|----------|
| `compare_storage.ts` | `client/src/cam/compare/` |
| `compare_types.ts` | `client/src/cam/compare/` |

### CNC Production (1 file)
| File | Location |
|------|----------|
| `PresetManagerPanel.vue` | `client/src/cnc_production/` |

### Base Components (12 files)
| File | Location |
|------|----------|
| `AppNav.vue` | `client/src/components/` |
| `Breadcrumbs.vue` | `client/src/components/` |
| `CamBackplot3D.vue` | `client/src/components/` |
| `CamBackplotPanel.vue` | `client/src/components/` |
| `CamJobInsightsSummaryPanel.vue` | `client/src/components/` |
| `CamOffsetVisualizer.vue` | `client/src/components/` |
| `CamPipelinePresetList.vue` | `client/src/components/` |
| `CamPipelineRunResultPanel.vue` | `client/src/components/` |
| `CAMPreview.vue` | `client/src/components/` |
| `CamSimMetricsPanel.vue` | `client/src/components/` |
| `CurveLab.vue` | `client/src/components/` |
| `DrillingLab.vue` | `client/src/components/` |
| `PostEditor.vue` | `client/src/components/` |
| `PostManager.vue` | `client/src/components/` |

### Art Components (3 files)
| File | Location |
|------|----------|
| `ReliefRiskPresetPanel.vue` | `client/src/components/art/` |
| `RosetteCompareHistory.vue` | `client/src/components/art/` |
| `RosetteComparePanel.vue` | `client/src/components/art/` |

### CAM Components (6 files)
| File | Location |
|------|----------|
| `CamIssuesList.vue` | `client/src/components/cam/` |
| `CamPresetEvolutionTrend.vue` | `client/src/components/cam/` |
| `CamRiskCompareBars.vue` | `client/src/components/cam/` |
| `CamRiskJobList.vue` | `client/src/components/cam/` |
| `CamRiskPresetTrend.vue` | `client/src/components/cam/` |
| `CamRiskTimeline.vue` | `client/src/components/cam/` |

### Compare Components (19 files) ⚠️ SIGNIFICANT
| File | Location |
|------|----------|
| `compareBlinkBehavior.spec.ts` | `client/src/components/compare/` |
| `compareBlinkBehavior.ts` | `client/src/components/compare/` |
| `compareLayerPanel.vue` | `client/src/components/compare/` |
| `compareLayers.spec.ts` | `client/src/components/compare/` |
| `compareLayers.ts` | `client/src/components/compare/` |
| `compareLayerVisibility.spec.ts` | `client/src/components/compare/` |
| `compareLayerVisibility.ts` | `client/src/components/compare/` |
| `CompareModeButton.vue` | `client/src/components/compare/` |
| `compareModes.spec.ts` | `client/src/components/compare/` |
| `compareModes.ts` | `client/src/components/compare/` |
| `compareViewportMath.spec.ts` | `client/src/components/compare/` |
| `compareViewportMath.ts` | `client/src/components/compare/` |
| `compareXrayBehavior.spec.ts` | `client/src/components/compare/` |
| `compareXrayBehavior.ts` | `client/src/components/compare/` |
| `DiffModeToggle.vue` | `client/src/components/compare/` |
| `DualSvgDisplay.vue` | `client/src/components/compare/` |
| `ExportToolbar.vue` | `client/src/components/compare/` |
| `MetricsDisplay.vue` | `client/src/components/compare/` |
| `PanZoomSvg.vue` | `client/src/components/compare/` |
| `README.md` | `client/src/components/compare/` |

### Rosette Components (3 files)
| File | Location |
|------|----------|
| `MaterialPalette.vue` | `client/src/components/rosette/` |
| `PatternTemplates.vue` | `client/src/components/rosette/` |
| `RosetteCanvas.vue` | `client/src/components/rosette/` |

### Toolbox Components (38 files) ⚠️ MAJOR ORPHANED COLLECTION
| File | Location | Purpose |
|------|----------|---------|
| `AdaptiveBench.vue` | `client/src/components/toolbox/` | Adaptive benchmarking |
| `AdaptiveBenchLab.vue` | `client/src/components/toolbox/` | Adaptive bench lab UI |
| `AdaptivePoly.vue` | `client/src/components/toolbox/` | Polygon adaptive |
| `ArchtopCalculator.vue` | `client/src/components/toolbox/` | Archtop guitar calc |
| `ArtStudioCAM.vue` | `client/src/components/toolbox/` | Art Studio CAM |
| `BackplotGcode.vue` | `client/src/components/toolbox/` | G-code backplot |
| `BracingCalculator.vue` | `client/src/components/toolbox/` | Bracing calculator |
| `BridgeCalculator.vue` | `client/src/components/toolbox/` | Bridge calculator |
| `BusinessCalculator.vue` | `client/src/components/toolbox/` | Business/ROI calc |
| `CalculatorHub.vue` | `client/src/components/toolbox/` | Calculator hub |
| `CAMEssentialsLab.vue` | `client/src/components/toolbox/` | CAM essentials |
| `CNCBusinessFinancial.vue` | `client/src/components/toolbox/` | CNC financials |
| `CNCROICalculator.vue` | `client/src/components/toolbox/` | ROI calculator |
| `DXFCleaner.vue` | `client/src/components/toolbox/` | DXF cleanup tool |
| `DxfPreflightValidator.vue` | `client/src/components/toolbox/` | DXF preflight |
| `EnhancedRadiusDish.vue` | `client/src/components/toolbox/` | Radius dish designer |
| `ExportQueue.vue` | `client/src/components/toolbox/` | Export queue |
| `FinishingDesigner.vue` | `client/src/components/toolbox/` | Finishing designer |
| `FinishPlanner.vue` | `client/src/components/toolbox/` | Finish planner |
| `FractionCalculator.vue` | `client/src/components/toolbox/` | Fraction calc |
| `FretboardCompoundRadius.vue` | `client/src/components/toolbox/` | Fretboard radius |
| `GCodeExplainer.vue` | `client/src/components/toolbox/` | G-code explainer |
| `GuitarDesignHub.vue` | `client/src/components/toolbox/` | Guitar design hub |
| `GuitarDimensionsForm.vue` | `client/src/components/toolbox/` | Guitar dimensions |
| `HardwareLayout.vue` | `client/src/components/toolbox/` | Hardware layout |
| `HelicalRampLab.vue` | `client/src/components/toolbox/` | Helical ramping |
| `LesPaulNeckGenerator.vue` | `client/src/components/toolbox/` | Les Paul neck gen |
| `PolygonOffsetLab.vue` | `client/src/components/toolbox/` | Polygon offset |
| `PostSelector.vue` | `client/src/components/toolbox/` | Post selector |
| `RadiusDishDesigner.vue` | `client/src/components/toolbox/` | Radius dish |
| `RosetteDesigner.vue` | `client/src/components/toolbox/` | Rosette designer |
| `ScaleLengthDesigner.vue` | `client/src/components/toolbox/` | Scale length |
| `ScientificCalculator.vue` | `client/src/components/toolbox/` | Scientific calc |
| `SimLab_BACKUP_Enhanced.vue` | `client/src/components/toolbox/` | SimLab backup |
| `SimLab.vue` | `client/src/components/toolbox/` | Simulation lab |
| `SimLabWorker.vue` | `client/src/components/toolbox/` | SimLab worker |
| `WiringWorkbench.vue` | `client/src/components/toolbox/` | Wiring workbench |

### Composables (3 files)
| File | Location |
|------|----------|
| `useCompareState.spec.ts` | `client/src/composables/` |
| `useCompareState.ts` | `client/src/composables/` |
| `usePresetQueryBootstrap.ts` | `client/src/composables/` |

### Labs (2 files)
| File | Location |
|------|----------|
| `ReliefKernelLab.vue` | `client/src/labs/` |
| `ReliefKernelLab_backup_phase24_6.vue` | `client/src/labs/` |

### Utilities (13 files)
| File | Location |
|------|----------|
| `analytics.ts` | `client/src/utils/` |
| `captureElementScreenshot.ts` | `client/src/utils/` |
| `compareReportBuilder.spec.ts` | `client/src/utils/` |
| `compareReportBuilder.ts` | `client/src/utils/` |
| `curvemath_dxf.ts` | `client/src/utils/` |
| `curvemath.ts` | `client/src/utils/` |
| `downloadBlob.ts` | `client/src/utils/` |
| `neck_generator.ts` | `client/src/utils/` |
| `switch_validator.ts` | `client/src/utils/` |
| `treble_bleed.ts` | `client/src/utils/` |
| `compoundRadius.ts` | `client/src/utils/math/` |
| `curveRadius.ts` | `client/src/utils/math/` |
| `compoundRadius.spec.ts` | `client/src/utils/math/__tests__/` |
| `curveRadius.spec.ts` | `client/src/utils/math/__tests__/` |

### Views (14 files)
| File | Location |
|------|----------|
| `AdaptiveLabView.vue` | `client/src/views/` |
| `ArtStudioDashboard.vue` | `client/src/views/` |
| `ArtStudioRosetteCompare.vue` | `client/src/views/` |
| `CAMDashboard.vue` | `client/src/views/` |
| `CamProductionView.vue` | `client/src/views/` |
| `LabsIndex.vue` | `client/src/views/` |
| `MachineListView.vue` | `client/src/views/` |
| `MachineManagerView.vue` | `client/src/views/` |
| `OffsetLabView.vue` | `client/src/views/` |
| `PipelineLabView_backup.vue` | `client/src/views/` |
| `PostListView.vue` | `client/src/views/` |
| `PostManagerView.vue` | `client/src/views/` |
| `PresetHubView.vue` | `client/src/views/` |
| `SawLabDashboard.vue` | `client/src/views/` |

### Art Views (2 files)
| File | Location |
|------|----------|
| `ArtStudioHeadstock.vue` | `client/src/views/art/` |
| `RiskDashboardCrossLab_Phase28_16.vue` | `client/src/views/art/` |

### CAM Views (2 files)
| File | Location |
|------|----------|
| `RiskPresetSideBySide.vue` | `client/src/views/cam/` |
| `RiskTimelineRelief.vue` | `client/src/views/cam/` |

### Lab Views (2 files)
| File | Location |
|------|----------|
| `RiskTimelineLab.vue` | `client/src/views/lab/` |
| `CompareLab.vue` | `client/src/views/labs/` |

### Workers (1 file)
| File | Location |
|------|----------|
| `sim_worker.ts` | `client/src/workers/` |

---

## Duplicate Files (55 files with same name in both locations)

These files exist in BOTH `client/src/` AND `packages/client/src/`:

| Filename | client/src/ | packages/client/src/ |
|----------|-------------|----------------------|
| `adaptive.ts` | ✓ | ✓ |
| `AdaptiveKernelLab.vue` | ✓ | ✓ |
| `api.ts` | ✓ | ✓ |
| `App.vue` | ✓ | ✓ |
| `ArtJobDetail.vue` | ✓ | ✓ |
| `ArtJobTimeline.vue` | ✓ | ✓ |
| `ArtPresetCompareAB.vue` | ✓ | ✓ |
| `ArtPresetManager.vue` | ✓ | ✓ |
| `ArtPresetSelector.vue` | ✓ | ✓ |
| `ArtStudio.vue` | ✓ | ✓ |
| `ArtStudioPhase15_5.vue` | ✓ | ✓ |
| `ArtStudioRelief.vue` | ✓ | ✓ |
| `ArtStudioRosette.vue` | ✓ | ✓ |
| `ArtStudioUnified.vue` | ✓ | ✓ |
| `ArtStudioV16.vue` | ✓ | ✓ |
| `BlueprintLab.vue` | ✓ | ✓ |
| `cam.ts` | ✓ | ✓ |
| `CamBackplotViewer.vue` | ✓ | ✓ |
| `CamPipelineGraph.vue` | ✓ | ✓ |
| `CamPipelineRunner.vue` | ✓ | ✓ |
| `CamSettingsView.vue` | ✓ | ✓ |
| `CompareBaselinePicker.vue` | ✓ | ✓ |
| `CompareDiffViewer.vue` | ✓ | ✓ |
| `CompareLabView.vue` | ✓ | ✓ |
| `CompareRunsPanel.vue` | ✓ | ✓ |
| `CompareSvgDualViewer.vue` | ✓ | ✓ |
| `geometry.ts` | ✓ | ✓ |
| `index.ts` | ✓ | ✓ |
| `infill.ts` | ✓ | ✓ |
| `main.ts` | ✓ | ✓ |
| `pipeline.ts` | ✓ | ✓ |
| `PipelineLabView.vue` | ✓ | ✓ |
| `PipelinePresetRunner.vue` | ✓ | ✓ |
| `postv155.ts` | ✓ | ✓ |
| `ReliefGrid.vue` | ✓ | ✓ |
| `ReliefKernelLab.vue` | ✓ | ✓ |
| `RiskDashboardCrossLab.vue` | ✓ | ✓ |
| `SawBatchPanel.vue` | ✓ | ✓ |
| `SawContourPanel.vue` | ✓ | ✓ |
| `SawLabDiffPanel.vue` | ✓ | ✓ |
| `SawLabQueuePanel.vue` | ✓ | ✓ |
| `SawLabShell.vue` | ✓ | ✓ |
| `SawSlicePanel.vue` | ✓ | ✓ |
| `SvgCanvas.vue` | ✓ | ✓ |
| `Toast.vue` | ✓ | ✓ |
| `ToolpathPreview3D.vue` | ✓ | ✓ |
| `types.ts` | ✓ | ✓ |
| `v16.ts` | ✓ | ✓ |
| `v161.ts` | ✓ | ✓ |
| `vcarve.ts` | ✓ | ✓ |

---

## Recommendations

### Priority 1: Critical Orphaned Code (Should Migrate)

The following **38 toolbox components** in `client/src/components/toolbox/` represent significant functionality that has NO equivalent in the primary location:

- Calculator components (ArchtopCalculator, BridgeCalculator, BusinessCalculator, etc.)
- Lab components (AdaptiveBenchLab, CAMEssentialsLab, HelicalRampLab, etc.)
- Design tools (RosetteDesigner, RadiusDishDesigner, GuitarDesignHub, etc.)
- Utility components (GCodeExplainer, DXFCleaner, WiringWorkbench)

**Action:** Review and migrate to `packages/client/src/components/toolbox/`

### Priority 2: Compare Module (19 files)

The `client/src/components/compare/` module contains extensive compare functionality with unit tests that appears more complete than `packages/client/src/components/compare/`.

**Action:** Evaluate which version is authoritative and consolidate.

### Priority 3: Utility Functions (13 files)

Several utility files in `client/src/utils/` including curve math, neck generators, and wiring calculators.

**Action:** Migrate to `packages/client/src/utils/`

### Priority 4: Cleanup Duplicates

55 files exist in both locations. Determine which is authoritative:
- If `packages/client/src/` is newer → delete from `client/src/`
- If `client/src/` has features not in packages → merge then delete

---

## Git Status Summary

```
client/                    → 3 files tracked (mostly untracked legacy folder)
packages/client/           → 44 files tracked (primary monorepo location)
```

The `client/` folder should be considered for:
1. **Migration** of unique components to `packages/client/`
2. **Archival** after migration is complete
3. **Deletion** from working tree (keep in git history)

---

## File Count Summary

| Category | Count |
|----------|-------|
| Total files in `client/src/` | 188 |
| Total files in `packages/client/src/` | 148 |
| Files ONLY in `client/src/` (orphaned) | **133** |
| Files ONLY in `packages/client/src/` | 93 |
| Files in BOTH (duplicates) | 55 |
