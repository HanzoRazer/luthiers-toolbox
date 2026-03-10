<script setup lang="ts">
/**
 * CadSidebar.vue
 *
 * Navigation sidebar with collapsible domain groups.
 * Based on VCarve/Fusion 360 navigation patterns.
 */

import { ref, computed } from "vue";
import { useRoute, useRouter } from "vue-router";

interface NavItem {
  label: string;
  path: string;
  icon?: string;
}

interface NavDomain {
  id: string;
  label: string;
  icon: string;
  items: NavItem[];
}

const route = useRoute();
const router = useRouter();

// Track expanded domains
const expandedDomains = ref<Set<string>>(new Set(["cam"]));

// Navigation structure
const domains: NavDomain[] = [
  {
    id: "design",
    label: "Design",
    icon: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    items: [
      { label: "Guitar Design Hub", path: "/design-hub" },
      { label: "Instrument Geometry", path: "/instrument-geometry" },
      { label: "Rosette Designer", path: "/rmos/rosette-designer" },
      { label: "Art Studio", path: "/art-studio" },
      { label: "Blueprint Import", path: "/blueprint" },
    ],
  },
  {
    id: "cam",
    label: "CAM",
    icon: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z",
    items: [
      { label: "DXF to G-code", path: "/cam/dxf-to-gcode" },
      { label: "Quick Cut", path: "/quick-cut" },
      { label: "Adaptive Lab", path: "/lab/adaptive" },
      { label: "Pipeline Lab", path: "/lab/pipeline" },
      { label: "Bridge Lab", path: "/lab/bridge" },
      { label: "Saw Lab", path: "/saw" },
      { label: "Pocket Clearing", path: "/cam/pocket" },
      { label: "Contour Cutting", path: "/cam/contour" },
      { label: "Drilling", path: "/cam/drilling" },
      { label: "Fret Slotting", path: "/cam/fret-slots" },
      { label: "Toolpath Simulator", path: "/cam/simulator" },
    ],
  },
  {
    id: "production",
    label: "Production",
    icon: "M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2",
    items: [
      { label: "RMOS Dashboard", path: "/rmos" },
      { label: "Live Monitor", path: "/rmos/live-monitor" },
      { label: "Run Artifacts", path: "/rmos/runs" },
      { label: "CNC Production", path: "/cnc" },
      { label: "Compare Lab", path: "/compare" },
      { label: "Preset Hub", path: "/preset-hub" },
      { label: "CAM Settings", path: "/cam-settings" },
    ],
  },
  {
    id: "analytics",
    label: "Analytics",
    icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
    items: [
      { label: "Risk Timeline", path: "/lab/risk-timeline" },
      { label: "Material Analytics", path: "/rmos/material-analytics" },
      { label: "CAM Advisor", path: "/cam/advisor" },
      { label: "Audio Analyzer", path: "/tools/audio-analyzer" },
      { label: "Acoustics Library", path: "/tools/audio-analyzer/library" },
    ],
  },
  {
    id: "ai",
    label: "AI Tools",
    icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
    items: [
      { label: "AI Images", path: "/ai-images" },
      { label: "Wood Grading", path: "/ai/wood-grading" },
      { label: "Defect Detection", path: "/ai/defect-detection" },
      { label: "AI Assistant", path: "/ai/assistant" },
    ],
  },
  {
    id: "business",
    label: "Business",
    icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    items: [
      { label: "Engineering Estimator", path: "/business/estimator" },
      { label: "Calculators", path: "/calculators" },
    ],
  },
];

function toggleDomain(domainId: string) {
  if (expandedDomains.value.has(domainId)) {
    expandedDomains.value.delete(domainId);
  } else {
    expandedDomains.value.add(domainId);
  }
}

function isExpanded(domainId: string): boolean {
  return expandedDomains.value.has(domainId);
}

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + "/");
}

function navigateTo(path: string) {
  router.push(path);
}

// Auto-expand domain containing current route
const currentDomain = computed(() => {
  for (const domain of domains) {
    for (const item of domain.items) {
      if (isActive(item.path)) {
        return domain.id;
      }
    }
  }
  return null;
});

// Expand current domain on mount
if (currentDomain.value) {
  expandedDomains.value.add(currentDomain.value);
}
</script>

<template>
  <nav class="cad-sidebar">
    <!-- Logo/Brand -->
    <div class="sidebar-brand" @click="navigateTo('/')">
      <span class="brand-icon">PS</span>
      <span class="brand-text">Production Shop</span>
    </div>

    <!-- Navigation Domains -->
    <div class="sidebar-nav">
      <div
        v-for="domain in domains"
        :key="domain.id"
        class="nav-domain"
        :class="{ expanded: isExpanded(domain.id) }"
      >
        <!-- Domain Header -->
        <button class="domain-header" @click="toggleDomain(domain.id)">
          <svg class="domain-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path :d="domain.icon" />
          </svg>
          <span class="domain-label">{{ domain.label }}</span>
          <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>

        <!-- Domain Items -->
        <div v-show="isExpanded(domain.id)" class="domain-items">
          <button
            v-for="item in domain.items"
            :key="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            @click="navigateTo(item.path)"
          >
            {{ item.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom Actions -->
    <div class="sidebar-footer">
      <button class="nav-item" @click="navigateTo('/settings/cam')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
        Settings
      </button>
    </div>
  </nav>
</template>

<style scoped>
.cad-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 8px 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border-panel, #3a3a3a);
  margin-bottom: 8px;
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--color-accent, #4a9eff);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.brand-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.nav-domain {
  margin-bottom: 4px;
}

.domain-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #a0a0a0);
  font-size: 12px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}

.domain-header:hover {
  background: var(--color-bg-panel-elevated, #2d2d2d);
  color: var(--color-text-primary, #e0e0e0);
}

.nav-domain.expanded .domain-header {
  color: var(--color-text-primary, #e0e0e0);
}

.domain-icon {
  flex-shrink: 0;
}

.domain-label {
  flex: 1;
}

.chevron {
  flex-shrink: 0;
  transition: transform 0.15s;
}

.nav-domain.expanded .chevron {
  transform: rotate(180deg);
}

.domain-items {
  padding: 4px 0 4px 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #a0a0a0);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}

.nav-item:hover {
  background: var(--color-bg-panel-elevated, #2d2d2d);
  color: var(--color-text-primary, #e0e0e0);
}

.nav-item.active {
  background: var(--color-accent, #4a9eff);
  color: #fff;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--color-border-panel, #3a3a3a);
  margin-top: 8px;
}

.sidebar-footer .nav-item {
  padding: 8px;
}

/* Scrollbar */
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--color-border-panel, #3a3a3a);
  border-radius: 3px;
}
</style>
