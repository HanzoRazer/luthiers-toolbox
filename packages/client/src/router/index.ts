// packages/client/src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

// Lazy load RosettePipelineView to prevent it from breaking other routes if it has runtime errors
const RosettePipelineView = () => import("@/views/RosettePipelineView.vue");

// Import route guards
import { requireGuest, requireAuth, requireTier, initAuthGuard } from "./guards";

const routes: RouteRecordRaw[] = [
  // ============================================================================
  // AUTH ROUTES
  // ============================================================================
  {
    path: "/auth/login",
    name: "Login",
    component: () => import("@/views/auth/LoginView.vue"),
    beforeEnter: requireGuest,
  },
  {
    path: "/auth/signup",
    name: "Signup",
    component: () => import("@/views/auth/SignupView.vue"),
    beforeEnter: requireGuest,
  },
  {
    path: "/auth/callback",
    name: "AuthCallback",
    component: () => import("@/views/auth/CallbackView.vue"),
  },
  {
    path: "/upgrade",
    name: "Upgrade",
    component: () => import("@/views/auth/UpgradeView.vue"),
  },

  // Dashboard - New home page showing all domains
  {
    path: "/",
    name: "Home",
    component: () => import("@/views/AppDashboardView.vue"),
  },

  // Smart Guitar — Module 5 shell (Body Design, Electronics, RPi5 Cavity, WiFi, Export & BOM)
  {
    path: "/smart-guitar",
    name: "SmartGuitar",
    component: () => import("@/views/smart-guitar/SmartGuitarShell.vue"),
  },

  // Rosette Pipeline - moved from home to /rosette
  {
    path: "/rosette",
    name: "Rosette",
    component: RosettePipelineView,
  },

  // Quick Cut - Simplified DXF to G-code flow (Phase 5)
  {
    path: "/quick-cut",
    name: "QuickCut",
    component: () => import("@/views/QuickCutView.vue"),
  },

  // ============================================================================
  // LAB ROUTES (match AppNav.vue links)
  // ============================================================================

  // Bridge Lab
  {
    path: "/lab/bridge",
    name: "LabBridge",
    component: () => import("@/views/BridgeLabView.vue"),
  },

  // Adaptive Lab
  {
    path: "/lab/adaptive",
    name: "LabAdaptive",
    component: () => import("@/views/AdaptiveLabView.vue"),
  },

  // Pipeline Lab
  {
    path: "/lab/pipeline",
    name: "LabPipeline",
    component: () => import("@/views/PipelineLabView.vue"),
  },

  // Saw Lab routes
  {
    path: "/lab/saw/slice",
    name: "LabSawSlice",
    component: () => import("@/views/SawLabView.vue"),
    props: { mode: "slice" },
  },
  {
    path: "/lab/saw/batch",
    name: "LabSawBatch",
    component: () => import("@/views/SawLabView.vue"),
    props: { mode: "batch" },
  },
  {
    path: "/lab/saw/contour",
    name: "LabSawContour",
    component: () => import("@/views/SawLabView.vue"),
    props: { mode: "contour" },
  },

  // Risk Timeline Lab
  {
    path: "/lab/risk-timeline",
    name: "LabRiskTimeline",
    component: () => import("@/views/lab/RiskTimelineLab.vue"),
  },

  // Helical Ramp Lab (CU-A6: promoted to CAM Tools nav)
  {
    path: "/lab/helical",
    name: "LabHelical",
    component: () => import("@/components/toolbox/HelicalRampLab.vue"),
  },

  // Polygon Offset Lab (CU-A6: promoted to Design Utilities nav)
  {
    path: "/lab/polygon-offset",
    name: "LabPolygonOffset",
    component: () => import("@/components/toolbox/PolygonOffsetLab.vue"),
  },

  // Machine Manager
  {
    path: "/lab/machines",
    alias: "/lab/machine-manager",
    name: "LabMachines",
    component: () => import("@/views/lab/MachineManagerView.vue"),
  },

  // CAM Settings (match nav link)
  {
    path: "/settings/cam",
    name: "SettingsCam",
    component: () => import("@/views/CamSettingsView.vue"),
  },

  // Calculator Hub
  {
    path: "/calculators",
    name: "Calculators",
    component: () => import("@/views/CalculatorHubView.vue"),
  },

  // ============================================================================
  // LEGACY ROUTES (keep for backwards compatibility)
  // ============================================================================


  // RMOS main view as its own route (optional)
  {
    path: "/rmos",
    name: "RMOS",
    component: RosettePipelineView,
  },

  // N10.0 Real-time Monitoring Dashboard
  {
    path: "/rmos/live-monitor",
    name: "RMOSLiveMonitor",
    component: () => import("@/views/RMOSLiveMonitorView.vue"),
  },

  // MM-0 Mixed-Material Strip Family Lab
  {
    path: "/rmos/strip-family-lab",
    name: "RmosStripFamilyLab",
    component: () => import("@/views/RmosStripFamilyLabView.vue"),
  },

  // RMOS Management Views
  {
    path: "/rmos/inventory",
    name: "RmosInventory",
    component: () => import("@/views/rmos/InventoryView.vue"),
  },
  {
    path: "/rmos/quality",
    name: "RmosQualityControl",
    component: () => import("@/views/rmos/QualityControlView.vue"),
  },
  {
    path: "/rmos/time",
    name: "RmosTimeTracking",
    component: () => import("@/views/rmos/TimeTrackingView.vue"),
  },
  {
    path: "/rmos/orders",
    name: "RmosOrders",
    component: () => import("@/views/rmos/OrdersView.vue"),
  },

  // MM-4 Material-Aware Analytics Dashboard
  {
    path: "/rmos/material-analytics",
    name: "RmosMaterialAnalytics",
    component: () => import("@/views/RmosAnalyticsView.vue"),
  },

  // Analytics Dashboard (N9.0 - legacy)
  {
    path: "/rmos/analytics",
    name: "RMOSAnalytics",
    component: () => import("@/components/rmos/AnalyticsDashboard.vue"),
  },

  // N11.2 Rosette Designer (Scaffolding)
  {
    path: "/rmos/rosette-designer",
    name: "RosetteDesigner",
    component: () => import("@/views/RosetteDesignerView.vue"),
  },

  // Art Studio views
  {
    path: "/art-studio",
    name: "ArtStudio",
    component: () => import("@/views/ArtStudio.vue"),
  },
  {
    path: "/art-studio/v16",
    name: "ArtStudioV16",
    component: () => import("@/views/ArtStudioV16.vue"),
  },
  {
    path: "/art-studio/relief",
    name: "ArtStudioRelief",
    component: () => import("@/views/art-studio/ReliefCarvingView.vue"),
  },
  {
    path: "/art-studio/inlay",
    name: "ArtStudioInlay",
    component: () => import("@/views/art-studio/InlayDesignerView.vue"),
  },
  {
    path: "/art-studio/inlay-workspace",
    name: "ArtStudioInlayWorkspace",
    component: () => import("@/views/art-studio/InlayWorkspaceShell.vue"),
  },
  {
    path: "/art-studio/soundhole-rosette-workspace",
    name: "ArtStudioSoundholeRosette",
    component: () => import("@/views/art-studio/SoundholeRosetteShell.vue"),
  },
  {
    path: "/art-studio/vcarve",
    name: "ArtStudioVCarve",
    component: () => import("@/views/art-studio/VCarveView.vue"),
  },
  {
    path: "/art-studio/bracing",
    name: "ArtStudioBracing",
    component: () => import("@/components/art/ArtStudioBracing.vue"),
  },
  {
    path: "/art-studio/binding",
    name: "ArtStudioBinding",
    component: () => import("@/views/art-studio/BindingDesignerView.vue"),
  },
  {
    path: "/art-studio/headstock",
    name: "ArtStudioHeadstock",
    component: () => import("@/views/art-studio/HeadstockDesignerView.vue"),
  },
  {
    path: "/art-studio/purfling",
    name: "ArtStudioPurfling",
    component: () => import("@/views/art-studio/PurflingDesignerView.vue"),
  },
  {
    path: "/art-studio/soundhole",
    name: "ArtStudioSoundhole",
    component: () => import("@/views/art-studio/SoundholeDesignerView.vue"),
  },
  {
    path: "/art-studio/inlay-patterns",
    name: "ArtStudioInlayPatterns",
    component: () => import("@/views/art-studio/InlayPatternView.vue"),
  },
  {
    path: "/art-studio/rosette-designer",
    name: "ArtStudioRosetteDesigner",
    component: () =>
      import("@/views/art-studio/RosetteWheelView.vue"),
  },

  // Preset Hub
  {
    path: "/preset-hub",
    name: "PresetHub",
    component: () => import("@/views/PresetHubView.vue"),
  },

  // Pipeline Lab
  {
    path: "/pipeline",
    name: "PipelineLab",
    component: () => import("@/views/PipelineLabView.vue"),
  },

  // Blueprint Lab
  {
    path: "/blueprint",
    name: "BlueprintLab",
    component: () => import("@/views/BlueprintLab.vue"),
  },

  // Saw Lab
  {
    path: "/saw",
    name: "SawLab",
    component: () => import("@/views/SawLabView.vue"),
  },

  // CAM Settings
  {
    path: "/cam-settings",
    name: "CAMSettings",
    component: () => import("@/views/CamSettingsView.vue"),
  },

  // Bridge Lab
  {
    path: "/bridge",
    name: "BridgeLab",
    component: () => import("@/views/BridgeLabView.vue"),
  },

  // CNC Production
  {
    path: "/cnc",
    name: "CNCProduction",
    component: () => import("@/views/CncProductionView.vue"),
  },

  // Compare Lab
  {
    path: "/compare",
    name: "CompareLab",
    component: () => import("@/views/CompareLabView.vue"),
  },

  // Wave 12 — CAM Advisor & G-Code Explainer
  {
    path: "/cam/advisor",
    name: "CamAdvisor",
    component: () => import("@/views/cam/CamAdvisorView.vue"),
  },

  // Shop-floor DXF → G-code (GRBL)
  {
    path: "/cam/dxf-to-gcode",
    name: "DxfToGcode",
    component: () => import("@/views/DxfToGcodeView.vue"),
  },

  // CAM Operations
  {
    path: "/cam/pocket",
    name: "CamPocketClearing",
    component: () => import("@/views/cam/PocketClearingView.vue"),
  },
  {
    path: "/cam/contour",
    name: "CamContourCutting",
    component: () => import("@/views/cam/ContourCuttingView.vue"),
  },
  {
    path: "/cam/surfacing",
    name: "CamSurfacing",
    component: () => import("@/views/cam/SurfacingView.vue"),
  },
  {
    path: "/cam/drilling",
    name: "CamDrilling",
    component: () => import("@/views/cam/DrillingView.vue"),
  },
  {
    path: "/cam/fret-slots",
    name: "CamFretSlotting",
    component: () => import("@/views/cam/FretSlottingView.vue"),
  },
  {
    path: "/cam/simulator",
    name: "CamToolpathSimulator",
    component: () => import("@/views/cam/ToolpathSimulatorView.vue"),
  },

  // Guitar Design Hub - Body Outline Generator, Bracing, Archtop, etc.
  {
    path: "/design-hub",
    name: "GuitarDesignHub",
    component: () => import("@/views/GuitarDesignHubView.vue"),
  },

  // Individual Instrument Design (dynamic route for /design/stratocaster, /design/les-paul, etc.)
  {
    path: "/design/:instrumentId",
    name: "InstrumentDesign",
    component: () => import("@/views/InstrumentDesignView.vue"),
    props: true,
  },

  // Waves 15-16 — Instrument Geometry Designer (Fretboard CAM)
  {
    path: "/instrument-geometry",
    alias: "/instrument-hub",
    name: "InstrumentGeometry",
    component: () => import("@/views/InstrumentGeometryView.vue"),
  },

  // Guitar Body Dimensions (Parametric Designer from Blueprint Lab)
  {
    path: "/guitar-dimensions",
    name: "GuitarDimensions",
    component: () => import("@/views/GuitarDimensionsView.vue"),
  },

  // Run Artifacts Browser
  {
    path: "/rmos/runs",
    name: "RmosRuns",
    component: () => import("@/views/RmosRunsView.vue"),
  },

  // Run Artifact Diff Viewer
  {
    path: "/rmos/runs/diff",
    alias: "/runs/diff",
    name: "RmosRunsDiff",
    component: () => import("@/views/RmosRunsDiffView.vue"),
  },

  // Run Artifact Viewer (single run detail page)
  {
    path: "/rmos/runs/:id",
    alias: "/runs/:id",
    name: "RmosRunViewer",
    component: () => import("@/views/RmosRunViewerView.vue"),
    props: true,
  },

  // Run Variants Review Page (H3 Product Bundle)
  {
    path: "/rmos/runs/:run_id/variants",
    name: "RunVariantsReview",
    component: () => import("@/views/Runs/RunVariantsReviewPage.vue"),
  },

  // Tools: Audio Analyzer Evidence Viewer
  {
    path: "/tools/audio-analyzer",
    name: "AudioAnalyzerViewer",
    component: () => import("@/views/tools/AudioAnalyzerViewer.vue"),
  },

  // Tools: Acoustics Library (browse/import viewer_packs)
  {
    path: "/tools/audio-analyzer/library",
    name: "AudioAnalyzerLibrary",
    component: () => import("@/views/tools/AudioAnalyzerLibrary.vue"),
  },

  // Tools: Acoustics Runs Browser (session/run-centric library)
  {
    path: "/tools/audio-analyzer/runs",
    name: "AudioAnalyzerRunsLibrary",
    component: () => import("@/views/tools/AudioAnalyzerRunsLibrary.vue"),
  },

  // Tools: Acoustics Ingest Audit Log (browse import events)
  {
    path: "/tools/audio-analyzer/ingest",
    name: "AcousticsIngestEvents",
    component: () => import("@/views/tools/AcousticsIngestEvents.vue"),
  },

  // Business: Engineering Cost Estimator (Pro Feature)
  {
    path: "/business/estimator",
    name: "EngineeringEstimator",
    component: () => import("@/views/business/EngineeringEstimatorView.vue"),
    beforeEnter: requireTier("pro"),
    meta: { requiresPro: true, featureName: "Engineering Cost Estimator" },
  },

  // AI Images — Visual Analyzer (Production)
  {
    path: "/ai-images",
    name: "AiImages",
    component: () => import("@/views/AiImagesView.vue"),
  },

  // AI Tools
  {
    path: "/ai/wood-grading",
    name: "AiWoodGrading",
    component: () => import("@/views/ai/WoodGradingView.vue"),
  },
  {
    path: "/ai/recommendations",
    name: "AiRecommendations",
    component: () => import("@/views/ai/RecommendationsView.vue"),
  },
  {
    path: "/ai/assistant",
    name: "AiAssistant",
    component: () => import("@/views/ai/AssistantView.vue"),
  },
  {
    path: "/ai/defect-detection",
    name: "AiDefectDetection",
    component: () => import("@/views/ai/DefectDetectionView.vue"),
  },

  // Dev: Vision Attach Widget Test
  {
    path: "/dev/vision-attach",
    name: "VisionAttachTest",
    component: () => import("@/views/VisionAttachTestView.vue"),
  },

  // CU-A4: Dev scratch views removed from routing (SandboxView, CadLayoutDemo, etc.)
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Initialize auth state on every navigation
// This ensures auth is loaded before any route guard checks
router.beforeEach(initAuthGuard);

export default router;
