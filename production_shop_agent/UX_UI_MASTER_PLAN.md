# The Production Shop - UX/UI Master Plan

**Created:** March 3, 2026
**Purpose:** Comprehensive documentation to prevent build setbacks and guide feature consolidation
**Status:** Active Development

---

## Table of Contents

1. [Complete Feature Inventory](#complete-feature-inventory)
2. [Information Architecture](#information-architecture)
3. [Component-to-Route Mapping](#component-to-route-mapping)
4. [Marketing Page Requirements](#marketing-page-requirements)
5. [Session Continuity Protocol](#session-continuity-protocol)
6. [Implementation Checklist](#implementation-checklist)

---

## Complete Feature Inventory

### 1. INSTRUMENT LIBRARY (21 Models)

| Model | ID | Category | Status | Scale Length | Assets |
|-------|-----|----------|--------|--------------|--------|
| Fender Stratocaster | `stratocaster` | Electric | STUB | 648mm (25.5") | - |
| Fender Telecaster | `telecaster` | Electric | STUB | 648mm (25.5") | - |
| Gibson Les Paul | `les_paul` | Electric | STUB | 628.65mm (24.75") | - |
| Gibson SG | `sg` | Electric | STUB | 628.65mm (24.75") | - |
| Gibson ES-335 | `es_335` | Electric | STUB | 628.65mm (24.75") | - |
| Gibson Flying V | `flying_v` | Electric | ASSETS_ONLY | 628.65mm (24.75") | 3 DWG files |
| Gibson Explorer | `explorer` | Electric | STUB | 628.65mm (24.75") | - |
| Gibson Firebird | `firebird` | Electric | STUB | 628.65mm (24.75") | - |
| Gibson Moderne | `moderne` | Electric | STUB | 628.65mm (24.75") | - |
| PRS Custom 24 | `prs` | Electric | STUB | 635mm (25") | - |
| Benedetto 17" Archtop | `benedetto_17` | Archtop | COMPLETE | 635mm (25") | DXF, graduation map |
| Gibson L-5 | `l5` | Archtop | STUB | 635mm (25") | - |
| Gibson Super 400 | `super_400` | Archtop | STUB | 635mm (25") | - |
| Dreadnought (D-28 style) | `dreadnought` | Acoustic | STUB | 645.16mm (25.4") | - |
| OM/000 | `om_000` | Acoustic | STUB | 645.16mm (25.4") | - |
| Gibson J-45 | `j_45` | Acoustic | STUB | 628.65mm (24.75") | - |
| Gibson J-200 Jumbo | `jumbo_j200` | Acoustic | ASSETS_ONLY | 645.16mm (25.4") | PDF plans |
| Gibson L-00 | `gibson_l_00` | Acoustic | ASSETS_ONLY | 628.65mm (24.75") | PDF plans |
| Classical Guitar | `classical` | Acoustic | STUB | 650mm (25.6") | - |
| Fender Jazz Bass | `jazz_bass` | Bass | STUB | 863.6mm (34") | - |
| Soprano Ukulele | `ukulele` | Ukulele | ASSETS_ONLY | 330mm (13") | 3 DXF files |
| **Smart Guitar** | `smart_guitar` | Electric/IoT | **COMPLETE** | 648mm (25.5") | Full IoT specs |

**Smart Guitar Special Features:**
- Raspberry Pi 5 embedded (8GB RAM, 64GB storage)
- BLE 5.0, Wi-Fi 6, USB-C 3.1
- 24-bit/96kHz audio, 3ms latency
- 6 piezo pickups, accelerometer, gyroscope
- LED fret markers (RGB addressable)
- DAW integration (Giglad, Band-in-a-Box)
- 8-hour battery life

---

### 2. TOOLBOX COMPONENTS (83 Components)

#### 2.1 Calculators (23 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| BasicCalculatorPad | `/calculators` | No (frontend) | Basic arithmetic |
| ScientificCalculator | `/calculators` | No (frontend) | Scientific functions |
| ScientificCalculatorV2 | `/calculators` | No (frontend) | Enhanced scientific |
| FractionCalculator | `/calculators` | No (frontend) | Fraction math |
| WoodworkPanel | `/calculators` | No (frontend) | Woodworking conversions |
| UnitConverterPanel | `/calculators` | No (frontend) | Unit conversions |
| BracingCalculator | `/calculators` | Yes | Bracing patterns |
| BridgeCalculator | `/lab/bridge` | Yes | Bridge placement/compensation |
| ArchtopCalculator | TBD | Yes | Archtop graduation |
| RadiusDishCalculator | TBD | Yes | Radius dish design |
| RadiusDishDesigner | TBD | Yes | Full dish workflow |
| RadiusDishCncSetup | TBD | Yes | CNC setup for dishes |
| EnhancedRadiusDish | TBD | Yes | Advanced dish features |
| ScaleLengthDesigner | TBD | Yes | Scale length calculator |
| FretboardCompoundRadius | TBD | Yes | Compound radius design |
| TensionCalculatorPanel | TBD | Yes | String tension |
| IntonationPanel | TBD | Yes | Intonation compensation |
| MultiscalePanel | TBD | Yes | Fanned fret design |
| AdaptiveBench | `/lab/adaptive` | Yes | Adaptive clearing bench |
| AdaptiveBenchLab | `/lab/adaptive` | Yes | Extended bench |
| AdaptivePoly | `/lab/adaptive` | Yes | Polygon adaptive |
| CalculatorHub | `/calculators` | Mixed | Calculator container |
| CalculatorDisplay | `/calculators` | No | Display component |

#### 2.2 Guitar Design (8 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| GuitarDesignHub | TBD | Yes | Central design hub |
| GuitarBodyPreview | TBD | Yes | Body outline preview |
| GuitarDimensionsForm | TBD | Yes | Dimension inputs |
| GuitarTypeSelector | TBD | Yes | Model selector |
| ScaleCard | TBD | No | Scale display card |
| ScalePresetsPanel | TBD | Yes | Scale presets |
| DesignPhaseSection | TBD | No | Design workflow |
| DimensionInputGrid | TBD | No | Dimension grid |

#### 2.3 Business Suite (9 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| **BusinessCalculator** | TBD | Yes | **5-tab business calculator** |
| StartupPlanningPanel | (tab 1) | Yes | Equipment, facilities, financing |
| InstrumentCostingPanel | (tab 2) | Yes | Materials & labor costing |
| PricingStrategyPanel | (tab 3) | Yes | Pricing & break-even |
| CashFlowPanel | (tab 4) | Yes | Cash flow projections |
| GrowthPlanningPanel | (tab 5) | Yes | Scaling scenarios |
| AmortizationSection | (sub) | Yes | Loan amortization |
| CNCROICalculator | `/calculators` | Yes | CNC ROI analysis |
| CNCBusinessFinancial | TBD | Yes | CNC financial planning |

#### 2.4 CAM & CNC (17 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| ArtStudioCAM | `/art-studio` | Yes | Art-to-CAM pipeline |
| BackplotGcode | TBD | Yes | G-code visualization |
| CAMEssentialsLab | TBD | Yes | CAM essentials |
| CamResultsPanel | (sub) | Yes | CAM results display |
| DXFCleaner | `/blueprint` | Yes | DXF cleanup tool |
| DxfPreflightValidator | TBD | Yes | DXF validation |
| ExportQueue | TBD | Yes | Export queue manager |
| GCodeExplainer | `/cam/advisor` | Yes | G-code explanation AI |
| GcodeOutputPanel | (sub) | Yes | G-code output |
| HelicalRampLab | TBD | Yes | Helical ramping |
| PatternOperationCard | (sub) | No | Pattern op display |
| PolygonOffsetLab | TBD | Yes | Polygon offset testing |
| ProbeOperationCard | (sub) | No | Probe op display |
| RetractOperationCard | (sub) | No | Retract op display |
| SimLab | TBD | Yes | Simulation lab |
| SimLabWorker | (worker) | Yes | Sim web worker |
| SpiralParamsPanel | (sub) | No | Spiral parameters |

#### 2.5 Finishing & Production (7 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| FinishingDesigner | TBD | Yes | Finish planning |
| FinishPlanner | TBD | Yes | Finish scheduler |
| FinishTypesPanel | (sub) | Yes | Finish types |
| HardwareLayout | TBD | Yes | Hardware placement |
| WiringWorkbench | TBD | Yes | Pickup wiring |
| LaborInputSection | (sub) | No | Labor inputs |
| LaborResultsSection | (sub) | No | Labor results |

#### 2.6 Rosette & Art (3 components in toolbox)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| RosetteDesigner | `/rosette` | Yes | Rosette pattern design |
| BurstControlsPanel | (sub) | Yes | Sunburst controls |
| BurstPreviewCanvas | (sub) | Yes | Burst preview |

#### 2.7 Bench & Testing (5 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| BenchInfoSection | (sub) | No | Bench info |
| BenchOutputPanel | (sub) | No | Bench output |
| BenchParamsPanel | (sub) | No | Bench params |
| BenchResultsPanel | (sub) | No | Bench results |
| PreviewLinkModePanel | (sub) | No | Preview linking |

#### 2.8 Misc (6 components)
| Component | Route | API Connected | Description |
|-----------|-------|---------------|-------------|
| PostSelector | TBD | Yes | Post processor selector |
| PresetSelector | TBD | Yes | Preset selector |
| ToolCard | (sub) | No | Tool display card |
| ToolTable | (sub) | No | Tool table display |

---

### 3. VIEWS (128 Views)

#### 3.1 Art Studio Suite (11 views)
- `ArtStudio.vue` - Main art studio
- `ArtStudioDashboard.vue` - Dashboard
- `ArtStudioHeadstock.vue` - Headstock design
- `ArtStudioPhase15_5.vue` - Phase 15.5 features
- `ArtStudioRelief.vue` - Relief carving
- `ArtStudioRosetteCompare.vue` - Rosette comparison
- `ArtStudioUnified.vue` - Unified interface
- `ArtStudioV16.vue` - Version 16
- `ArtJobDetail.vue` - Job details
- `ArtJobTimeline.vue` - Job timeline
- `ArtPresetManager.vue` - Preset management

#### 3.2 Rosette Suite (5 views + sub-components)
- `RosetteDesignerView.vue` - Designer
- `RosettePipelineView.vue` - Full pipeline
- `RosettePreviewSvg.vue` - SVG preview
- `CompareDiffSummary.vue` - Diff summary
- `CompareHistorySidebar.vue` - History sidebar

#### 3.3 RMOS Suite (8 views)
- `RmosAnalyticsView.vue` - Analytics dashboard
- `RMOSCncHistoryView.vue` - CNC history
- `RMOSCncJobDetailView.vue` - Job details
- `RMOSLiveMonitorView.vue` - Live monitoring
- `RmosRunsDiffView.vue` - Run comparison
- `RmosRunsView.vue` - Runs browser
- `RmosRunViewerView.vue` - Run viewer
- `RmosStripFamilyLabView.vue` - Strip family lab

#### 3.4 CAM Suite (7 views)
- `AdaptiveLabView.vue` - Adaptive clearing
- `CamAdvisorView.vue` - CAM advisor AI
- `CAMDashboard.vue` - CAM dashboard
- `CamProductionView.vue` - Production view
- `CamSettingsView.vue` - Settings
- `DxfToGcodeView.vue` - DXF to G-code
- `QuickCutView.vue` - Quick cut workflow

#### 3.5 Audio/Acoustics Suite (4 views)
- `AcousticsIngestEvents.vue` - Ingest audit log
- `AudioAnalyzerLibrary.vue` - Library browser
- `AudioAnalyzerRunsLibrary.vue` - Runs library
- `AudioAnalyzerViewer.vue` - Evidence viewer

#### 3.6 Labs Suite (15 views)
- `BlueprintLab.vue` - Blueprint analysis
- `BridgeLabView.vue` - Bridge design
- `CompareLab.vue` - Comparison lab
- `CompareLabView.vue` - Compare view
- `LabsIndex.vue` - Labs hub
- `MachineManagerView.vue` - Machine management
- `OffsetLabView.vue` - Offset testing
- `PipelineLab.vue` - Pipeline lab
- `PipelineLabView.vue` - Pipeline view
- `PipelinePresetRunner.vue` - Preset runner
- `RiskTimelineLab.vue` - Risk timeline
- `SawLabDashboard.vue` - Saw lab dashboard
- `SawLabView.vue` - Saw lab (3 modes)

#### 3.7 Business Suite (13 views)
- `EngineeringEstimatorView.vue` - Main estimator
- `EstimatorAnalyticsDashboard.vue` - Analytics
- `EstimatorComparePanel.vue` - Compare estimates
- `EstimatorDiffPanel.vue` - Diff view
- `EstimatorExportPanel.vue` - Export
- `EstimatorGoalsPanel.vue` - Goals tracking
- `EstimatorHistoryPanel.vue` - History
- `EstimatorInputsPanel.vue` - Inputs
- `EstimatorPresetsPanel.vue` - Presets
- `EstimatorSyncStatus.vue` - Sync status
- `EstimatorTemplatesPanel.vue` - Templates
- `EstimatorValidationStep.vue` - Validation
- `BackCalcTab.vue`, `MaterialsTab.vue`, `QuoteTab.vue`, `WbsBreakdownTab.vue`

#### 3.8 AI Suite (3 views)
- `AiImagesView.vue` - Visual analyzer
- `AiContextPanel.vue` - Context builder
- `GenerateTabPanel.vue` - Generation

#### 3.9 Design Suite (4 views)
- `InstrumentGeometryView.vue` - Geometry designer
- `InlayDesignerView.vue` - Inlay design
- `ReliefCarvingView.vue` - Relief carving
- `VCarveView.vue` - V-carve design

#### 3.10 Core Views (5 views)
- `AppDashboardView.vue` - Home dashboard
- `CalculatorHubView.vue` - Calculator hub
- `PresetHubView.vue` - Preset hub
- `CncProductionView.vue` - CNC production
- `PostManagerView.vue` - Post processor manager

---

## Information Architecture

### Proposed Navigation Structure

```
HOME (AppDashboardView)
│
├── DESIGN
│   ├── Instrument Library (21 models)
│   │   ├── Electric Guitars (10)
│   │   ├── Acoustic Guitars (6)
│   │   ├── Archtops (3)
│   │   ├── Bass (1)
│   │   └── Ukulele (1)
│   ├── Instrument Geometry
│   ├── Blueprint Lab
│   └── Guitar Design Hub
│
├── ART STUDIO
│   ├── Rosette Designer
│   ├── Rosette Pipeline
│   ├── Relief Carving
│   ├── Inlay Designer
│   ├── V-Carve
│   ├── Headstock Design
│   └── Bracing Designer
│
├── CALCULATORS
│   ├── Basic Calculator
│   ├── Scientific Calculator
│   ├── Fraction Calculator
│   ├── Woodworking Calculator
│   ├── Unit Converter
│   ├── Scale Length Designer
│   ├── Fretboard Compound Radius
│   ├── Tension Calculator
│   ├── Intonation Calculator
│   ├── Multiscale/Fan Fret
│   ├── Radius Dish Designer
│   ├── Archtop Calculator
│   └── Bracing Calculator
│
├── CAM
│   ├── Quick Cut (DXF → G-code)
│   ├── Adaptive Lab
│   ├── Saw Lab (Batch/Contour/Slice)
│   ├── Bridge Lab
│   ├── Drilling Lab
│   ├── G-code Explainer
│   ├── CAM Advisor (AI)
│   ├── DXF Cleaner
│   ├── Helical Ramp Lab
│   ├── Polygon Offset Lab
│   ├── Sim Lab
│   └── V-Carve Toolpaths
│
├── PRODUCTION
│   ├── RMOS Manufacturing
│   │   ├── Candidates
│   │   ├── Runs Browser
│   │   ├── Run Viewer
│   │   ├── Run Comparison
│   │   └── Strip Family Lab
│   ├── Live Monitor
│   ├── CNC History
│   ├── CNC Production
│   ├── Machine Manager
│   ├── Post Manager
│   ├── Preset Hub
│   ├── Pipeline Lab
│   ├── Risk Timeline
│   ├── Hardware Layout
│   ├── Wiring Workbench
│   ├── Finish Planner
│   └── Compare Runs
│
├── BUSINESS
│   ├── Business Calculator (5 tabs)
│   │   ├── Startup Planning
│   │   ├── Instrument Costing
│   │   ├── Pricing Strategy
│   │   ├── Cash Flow
│   │   └── Growth Planning
│   ├── Engineering Estimator (Pro)
│   ├── CNC ROI Calculator
│   └── CNC Business Financial
│
├── AI & ANALYTICS
│   ├── AI Visual Analyzer
│   ├── Material Analytics
│   ├── Acoustics Analyzer
│   │   ├── Evidence Viewer
│   │   ├── Library
│   │   ├── Runs Library
│   │   └── Ingest Events
│   └── Risk Dashboard
│
└── SETTINGS
    ├── CAM Settings
    ├── Machine Profiles
    └── Post Processors
```

---

## Component-to-Route Mapping

### Current Routes (from router/index.ts)

| Route | View | Status |
|-------|------|--------|
| `/` | AppDashboardView | Active |
| `/rosette` | RosettePipelineView | Active |
| `/quick-cut` | QuickCutView | Active |
| `/lab/bridge` | BridgeLabView | Active |
| `/lab/adaptive` | AdaptiveLabView | Active |
| `/lab/pipeline` | PipelineLabView | Active |
| `/lab/saw/slice` | SawLabView (slice) | Active |
| `/lab/saw/batch` | SawLabView (batch) | Active |
| `/lab/saw/contour` | SawLabView (contour) | Active |
| `/lab/risk-timeline` | RiskTimelineLab | Active |
| `/lab/machines` | MachineManagerView | Active |
| `/settings/cam` | CamSettingsView | Active |
| `/calculators` | CalculatorHubView | Active |
| `/rmos` | RosettePipelineView | Active |
| `/rmos/live-monitor` | RMOSLiveMonitorView | Active |
| `/rmos/strip-family-lab` | RmosStripFamilyLabView | Active |
| `/rmos/material-analytics` | RmosAnalyticsView | Active |
| `/rmos/analytics` | AnalyticsDashboard | Active |
| `/rmos/rosette-designer` | RosetteDesignerView | Active |
| `/art-studio` | ArtStudio | Active |
| `/art-studio/v16` | ArtStudioV16 | Active |
| `/art-studio/relief` | ReliefCarvingView | Active |
| `/art-studio/inlay` | InlayDesignerView | Active |
| `/art-studio/vcarve` | VCarveView | Active |
| `/preset-hub` | PresetHubView | Active |
| `/pipeline` | PipelineLabView | Active |
| `/blueprint` | BlueprintLab | Active |
| `/saw` | SawLabView | Active |
| `/cam-settings` | CamSettingsView | Active |
| `/bridge` | BridgeLabView | Active |
| `/cnc` | CncProductionView | Active |
| `/compare` | CompareLabView | Active |
| `/cam/advisor` | CamAdvisorView | Active |
| `/cam/dxf-to-gcode` | DxfToGcodeView | Active |
| `/instrument-geometry` | InstrumentGeometryView | Active |
| `/rmos/runs` | RmosRunsView | Active |
| `/rmos/runs/diff` | RmosRunsDiffView | Active |
| `/rmos/runs/:id` | RmosRunViewerView | Active |
| `/rmos/runs/:run_id/variants` | RunVariantsReviewPage | Active |
| `/tools/audio-analyzer` | AudioAnalyzerViewer | Active |
| `/tools/audio-analyzer/library` | AudioAnalyzerLibrary | Active |
| `/tools/audio-analyzer/runs` | AudioAnalyzerRunsLibrary | Active |
| `/tools/audio-analyzer/ingest` | AcousticsIngestEvents | Active |
| `/business/estimator` | EngineeringEstimatorView | Active (Pro) |
| `/ai-images` | AiImagesView | Active |

### MISSING Routes (Need to Add)

| Proposed Route | Component | Priority |
|----------------|-----------|----------|
| `/business/calculator` | BusinessCalculator | HIGH |
| `/design/guitar-hub` | GuitarDesignHub | HIGH |
| `/design/scale-length` | ScaleLengthDesigner | MEDIUM |
| `/design/radius-dish` | RadiusDishDesigner | MEDIUM |
| `/design/archtop` | ArchtopCalculator | MEDIUM |
| `/design/tension` | TensionCalculatorPanel | MEDIUM |
| `/design/finishing` | FinishingDesigner | MEDIUM |
| `/production/hardware` | HardwareLayout | MEDIUM |
| `/production/wiring` | WiringWorkbench | MEDIUM |
| `/production/finish-planner` | FinishPlanner | MEDIUM |
| `/cam/helical-ramp` | HelicalRampLab | LOW |
| `/cam/polygon-offset` | PolygonOffsetLab | LOW |
| `/cam/sim-lab` | SimLab | LOW |

---

## Marketing Page Requirements

### features.html Must Include

#### Design Tab
- [ ] Instrument Library (ALL 21 models with status badges)
- [ ] Smart Guitar showcase (IoT features)
- [ ] Instrument Geometry Designer
- [ ] Blueprint Lab (3 phases)
- [ ] Guitar Design Hub

#### Calculators Tab
- [ ] Basic Calculator
- [ ] Scientific Calculator
- [ ] Fraction Calculator
- [ ] Woodworking Calculator
- [ ] Unit Converter
- [ ] Scale Length Designer
- [ ] Fretboard Compound Radius
- [ ] Tension Calculator
- [ ] Intonation Calculator
- [ ] Multiscale Designer
- [ ] Radius Dish Designer
- [ ] Archtop Calculator
- [ ] Bracing Calculator
- [ ] Bridge Calculator

#### CAM Tab
- [ ] Quick Cut
- [ ] Adaptive Lab
- [ ] Saw Lab (3 modes)
- [ ] Bridge Lab
- [ ] Drilling Lab
- [ ] G-code Explainer
- [ ] CAM Advisor (AI)
- [ ] V-Carve Toolpaths
- [ ] DXF Cleaner
- [ ] Helical Ramp Lab
- [ ] Polygon Offset Lab
- [ ] Sim Lab

#### Art Studio Tab (NEW - separate from Design)
- [ ] Rosette Designer
- [ ] Rosette Pipeline
- [ ] Relief Carving
- [ ] Inlay Designer
- [ ] V-Carve Designer
- [ ] Headstock Design
- [ ] Bracing Design
- [ ] Burst/Sunburst Designer

#### Production Tab
- [ ] RMOS Manufacturing Candidates
- [ ] Live Monitor
- [ ] CNC History
- [ ] Compare Runs
- [ ] Machine Manager
- [ ] Preset Hub
- [ ] Pipeline Lab
- [ ] Risk Timeline
- [ ] Hardware Layout
- [ ] Wiring Workbench
- [ ] Finish Planner
- [ ] DXF Cleaner

#### Business Tab
- [ ] **Business Calculator** (5 tabs - SEPARATE from Estimator)
  - Startup Planning
  - Instrument Costing
  - Pricing Strategy
  - Cash Flow
  - Growth Planning
- [ ] Engineering Estimator (Pro)
- [ ] CNC ROI Calculator
- [ ] CNC Business Financial

#### AI & Analytics Tab (NEW)
- [ ] AI Visual Analyzer
- [ ] Material Analytics
- [ ] Acoustics Analyzer (4 sub-views)
- [ ] Risk Dashboard

---

## Session Continuity Protocol

### Before Starting Work
1. Read `SESSION_BOOKMARK.md` for context
2. Read this `UX_UI_MASTER_PLAN.md` for feature inventory
3. Check `ORPHANED_APPS_STATUS.md` for connection status
4. Run `git status` to see current state

### During Work
1. Commit frequently with descriptive messages
2. Update `SESSION_BOOKMARK.md` after significant changes
3. Update this document when adding features
4. Use TodoWrite to track progress

### Before Ending Session
1. Commit all changes
2. Update `SESSION_BOOKMARK.md` with:
   - What was accomplished
   - What's in progress
   - What's next
3. Update any status documents

### Critical Files to Preserve
```
production_shop_agent/
├── UX_UI_MASTER_PLAN.md          # This document
├── SESSION_BOOKMARK.md           # Session continuity
├── ORPHANED_APPS_STATUS.md       # API connection status
└── site_agent/output/production_shop/
    ├── features.html             # Marketing page
    ├── index.html                # Home page
    ├── pricing.html              # Pricing page
    └── about.html                # About page
```

### Git Commit Message Format
```
[AREA] Brief description

- Detail 1
- Detail 2

Session: X | Features: Y added, Z updated
```

---

## Implementation Checklist

### Phase 1: Documentation (Current)
- [x] Create feature inventory
- [x] Document all components
- [x] Document all views
- [x] Map routes
- [ ] Create wireframes

### Phase 2: Route Consolidation
- [ ] Add missing routes to router/index.ts
- [ ] Create route groups for organization
- [ ] Add breadcrumb support
- [ ] Update AppNav.vue

### Phase 3: Marketing Page Rebuild
- [ ] Rebuild features.html with ALL features
- [ ] Add Art Studio tab (separate from Design)
- [ ] Add AI & Analytics tab
- [ ] Fix all "Try Now" links (use correct port)
- [ ] Add status badges (Complete/Assets/Stub)

### Phase 4: Component Integration
- [ ] Add BusinessCalculator to route
- [ ] Add GuitarDesignHub to route
- [ ] Add missing calculators to CalculatorHub
- [ ] Integrate finishing tools

### Phase 5: Polish
- [ ] Consistent styling
- [ ] Mobile responsiveness
- [ ] Loading states
- [ ] Error handling

---

## API Endpoints Reference

### Backend Routers (77 total)
Key routers for frontend integration:

| Router | Prefix | Purpose |
|--------|--------|---------|
| `instrument_router.py` | `/api/instruments` | Instrument data |
| `neck_router.py` | `/api/neck` | Neck geometry |
| `blueprint.py` | `/api/blueprint` | Blueprint analysis |
| `relief_router.py` | `/api/cam/relief` | Relief carving |
| `inlay_router.py` | `/api/art-studio/inlay` | Inlay design |
| `vcarve_router.py` | `/api/art-studio/vcarve` | V-carve |
| `machines_router.py` | `/api/machines` | Machine management |
| `posts_consolidated_router.py` | `/api/posts` | Post processors |
| `business/estimator_router.py` | `/api/business/estimator` | Cost estimation |
| `calculators/` | `/api/calculators` | Calculator backends |

---

## Notes

- **Port Issue:** Vite dev server may run on 5173 or 5174 depending on availability
- **features.html links:** Currently hardcoded to localhost:5173 - need dynamic or relative
- **Business Calculator vs Engineering Estimator:** These are SEPARATE tools
  - Business Calculator: General business planning (5 tabs)
  - Engineering Estimator: Per-project cost estimation (Pro feature)

---

*Last Updated: March 3, 2026*
