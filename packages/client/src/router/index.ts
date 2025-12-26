// packages/client/src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

// Main RMOS view
import RosettePipelineView from "@/views/RosettePipelineView.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "Home",
    component: RosettePipelineView,
  },

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

  // Waves 15-16 — Instrument Geometry Designer (Fretboard CAM)
  {
    path: "/instrument-geometry",
    name: "InstrumentGeometry",
    component: () => import("@/views/InstrumentGeometryView.vue"),
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
    name: "RmosRunsDiff",
    component: () => import("@/views/RmosRunsDiffView.vue"),
  },

  // Run Variants Review Page (H3 Product Bundle)
  {
    path: "/rmos/runs/:run_id/variants",
    name: "RunVariantsReview",
    component: () => import("@/views/Runs/RunVariantsReviewPage.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
