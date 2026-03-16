<!-- @deprecated — dev scratch view, not routed -->
<template>
  <div class="nav-proto">
    <div class="proto-header">
      <div>
        <h2 class="proto-title">
          Navigation Redesign
        </h2>
        <p class="proto-desc">
          Current AppNav exposes 30+ routes as flat links. This prototype
          organizes them into 5 workflow domains. Click domains to explore.
        </p>
      </div>
      <div class="variant-switcher">
        <button
          v-for="v in variants"
          :key="v.id"
          class="variant-btn"
          :class="{ active: activeVariant === v.id }"
          @click="activeVariant = v.id"
        >
          {{ v.label }}
        </button>
      </div>
    </div>

    <!-- Variant: Top Nav -->
    <div
      v-if="activeVariant === 'top'"
      class="preview-frame"
    >
      <nav class="top-nav-proto">
        <div class="nav-brand">
          <span class="brand-icon">🎸</span>
          <span class="brand-name">Production Shop</span>
        </div>

        <div class="nav-domains">
          <div
            v-for="domain in domains"
            :key="domain.id"
            class="domain-item"
            :class="{ active: activeDomain === domain.id }"
            @mouseenter="activeDomain = domain.id"
            @mouseleave="activeDomain = null"
          >
            <button class="domain-btn">
              <span>{{ domain.icon }}</span>
              {{ domain.label }}
              <svg
                class="chevron"
                viewBox="0 0 16 16"
                fill="none"
              >
                <path
                  d="M4 6l4 4 4-4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
            </button>

            <div
              v-if="activeDomain === domain.id"
              class="domain-menu"
            >
              <div class="menu-header">
                <span class="menu-domain-icon">{{ domain.icon }}</span>
                <div>
                  <div class="menu-title">
                    {{ domain.label }}
                  </div>
                  <div class="menu-desc">
                    {{ domain.description }}
                  </div>
                </div>
              </div>
              <div class="menu-links">
                <a
                  v-for="link in domain.links"
                  :key="link.label"
                  href="#"
                  class="menu-link"
                  @click.prevent
                >
                  <span class="menu-link-icon">{{ link.icon }}</span>
                  <div>
                    <div class="menu-link-label">{{ link.label }}</div>
                    <div class="menu-link-desc">{{ link.desc }}</div>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>

        <div class="nav-actions">
          <button class="nav-action-btn">
            ⚙ Settings
          </button>
        </div>
      </nav>

      <div class="preview-content">
        <div class="content-placeholder">
          ← Hover a domain to see its sub-navigation
        </div>
      </div>
    </div>

    <!-- Variant: Sidebar Nav -->
    <div
      v-if="activeVariant === 'sidebar'"
      class="preview-frame sidebar-frame"
    >
      <nav class="sidebar-nav-proto">
        <div class="sidebar-brand">
          <span>🎸</span>
          <span>Production Shop</span>
        </div>

        <div class="sidebar-domains">
          <div
            v-for="domain in domains"
            :key="domain.id"
          >
            <button
              class="sidebar-domain"
              :class="{ active: activeDomain === domain.id }"
              @click="activeDomain = activeDomain === domain.id ? null : domain.id"
            >
              <span>{{ domain.icon }}</span>
              <span class="sidebar-domain-label">{{ domain.label }}</span>
              <svg
                class="sidebar-chevron"
                :class="{ rotated: activeDomain === domain.id }"
                viewBox="0 0 16 16"
                fill="none"
              >
                <path
                  d="M4 6l4 4 4-4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
            </button>

            <div
              v-if="activeDomain === domain.id"
              class="sidebar-links"
            >
              <a
                v-for="link in domain.links"
                :key="link.label"
                href="#"
                class="sidebar-link"
                @click.prevent
              >
                <span>{{ link.icon }}</span>
                {{ link.label }}
              </a>
            </div>
          </div>
        </div>
      </nav>

      <div class="preview-content">
        <div class="content-placeholder">
          ← Click a domain to expand
        </div>
      </div>
    </div>

    <!-- Analysis: before/after -->
    <div class="analysis-grid">
      <div class="analysis-card before">
        <div class="analysis-label">
          Current AppNav
        </div>
        <div class="analysis-count">
          30+ flat links
        </div>
        <ul class="analysis-list">
          <li>All routes at same hierarchy level</li>
          <li>Dropdown menus for some labs only</li>
          <li>No domain grouping — user must know all routes</li>
          <li>Navigation grows unbounded as features are added</li>
          <li>No visual cue for current workflow context</li>
        </ul>
      </div>
      <div class="analysis-card after">
        <div class="analysis-label">
          Proposed Architecture
        </div>
        <div class="analysis-count">
          5 domains × N tools
        </div>
        <ul class="analysis-list">
          <li>Design → CAM → Production → Analytics → Business</li>
          <li>Infinite tools can be added inside domains</li>
          <li>User always knows which workflow phase they're in</li>
          <li>Matches how a real instrument shop works</li>
          <li>Scales cleanly to ERP-level feature depth</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeVariant = ref('top')
const activeDomain = ref<string | null>(null)

const variants = [
  { id: 'top', label: 'Top Nav' },
  { id: 'sidebar', label: 'Sidebar Nav' },
]

const domains = [
  {
    id: 'design',
    label: 'Design',
    icon: '✏️',
    description: 'Guitar geometry, fretboard, rosette, art studio',
    links: [
      { icon: '📐', label: 'Guitar Dimensions', desc: 'Body templates and scale length' },
      { icon: '🎵', label: 'Scale Length Designer', desc: 'Multi-scale and intonation' },
      { icon: '🌹', label: 'Rosette Designer', desc: 'Ring patterns and art studio' },
      { icon: '🎨', label: 'Art Studio', desc: 'Inlay, bracing, headstock art' },
      { icon: '📋', label: 'Blueprint Importer', desc: 'DXF/image vectorization' },
    ],
  },
  {
    id: 'cam',
    label: 'CAM',
    icon: '⚙️',
    description: 'Toolpath generation, simulation, and G-code',
    links: [
      { icon: '⚡', label: 'Quick Cut', desc: 'Simplified DXF → G-code' },
      { icon: '🔧', label: 'CAM Pipeline', desc: 'Full pipeline runner' },
      { icon: '🌀', label: 'Adaptive Lab', desc: 'Adaptive pocket strategies' },
      { icon: '🪚', label: 'Saw Lab', desc: 'Contour, slice, and batch cuts' },
      { icon: '🌉', label: 'Bridge Lab', desc: 'Bridge toolpath generation' },
      { icon: '🔩', label: 'Drilling Lab', desc: 'Hole patterns and cycles' },
    ],
  },
  {
    id: 'production',
    label: 'Production',
    icon: '🏭',
    description: 'RMOS manufacturing candidates and CNC job management',
    links: [
      { icon: '📋', label: 'Manufacturing Candidates', desc: 'RMOS review queue' },
      { icon: '📡', label: 'Live Monitor', desc: 'Real-time CNC job status' },
      { icon: '📜', label: 'CNC History', desc: 'Completed job log' },
      { icon: '🔄', label: 'Compare Runs', desc: 'Side-by-side run analysis' },
      { icon: '📦', label: 'Export Queue', desc: 'G-code batch export' },
    ],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: '📊',
    description: 'Risk dashboards, run history, and AI advisory logs',
    links: [
      { icon: '⚠️', label: 'Risk Dashboard', desc: 'Cross-lab risk overview' },
      { icon: '📈', label: 'CAM Dashboard', desc: 'Pipeline performance trends' },
      { icon: '🤖', label: 'AI Log Viewer', desc: 'Advisory reasoning audit' },
      { icon: '📸', label: 'AI Images', desc: 'Vision-assisted analysis' },
      { icon: '🔬', label: 'Acoustics Analyzer', desc: 'Tonewood tap-tone data' },
    ],
  },
  {
    id: 'business',
    label: 'Business',
    icon: '💼',
    description: 'Costing, pricing, and shop financials',
    links: [
      { icon: '💰', label: 'Instrument Costing', desc: 'Materials + labor estimator' },
      { icon: '📊', label: 'CNC ROI Calculator', desc: 'Machine investment analysis' },
      { icon: '📅', label: 'Cash Flow Planner', desc: 'Revenue projection' },
      { icon: '🚀', label: 'Startup Planning', desc: 'New shop financial model' },
      { icon: '🔢', label: 'Engineering Estimator', desc: 'WBS cost breakdown' },
    ],
  },
]
</script>

<style scoped>
.nav-proto {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.proto-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
}

.proto-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-1) 0;
}

.proto-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
  max-width: 520px;
}

.variant-switcher {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.variant-btn {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  background: var(--color-surface);
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.variant-btn.active {
  background: var(--color-primary);
  color: white;
}

/* Preview frame */
.preview-frame {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: var(--color-surface-elevated);
}

/* Top nav prototype */
.top-nav-proto {
  display: flex;
  align-items: center;
  background: white;
  border-bottom: 1px solid var(--color-border);
  padding: 0 var(--space-4);
  height: 48px;
  gap: var(--space-4);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.brand-icon { font-size: 1.25rem; }

.brand-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  white-space: nowrap;
}

.nav-domains {
  display: flex;
  align-items: center;
  flex: 1;
}

.domain-item {
  position: relative;
}

.domain-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast), color var(--transition-fast);
  white-space: nowrap;
  height: 48px;
}

.domain-btn:hover,
.domain-item.active .domain-btn {
  color: var(--color-text);
  background: var(--color-surface-hover);
}

.chevron {
  width: 12px;
  height: 12px;
  transition: transform var(--transition-fast);
}

.domain-item.active .chevron {
  transform: rotate(180deg);
}

.domain-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  min-width: 280px;
  z-index: 100;
  padding: var(--space-3);
}

.menu-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-2);
}

.menu-domain-icon { font-size: 1.5rem; }

.menu-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}

.menu-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.menu-links {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2);
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: background var(--transition-fast);
}

.menu-link:hover {
  background: var(--color-surface-hover);
  text-decoration: none;
}

.menu-link-icon { font-size: 1rem; width: 1.25rem; text-align: center; }

.menu-link-label {
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.menu-link-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.nav-actions { margin-left: auto; }

.nav-action-btn {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-sm);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-muted);
}

.preview-content {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-placeholder {
  font-size: var(--font-size-sm);
  color: var(--color-text-light);
}

/* Sidebar variant */
.sidebar-frame {
  display: flex;
  height: 400px;
}

.sidebar-nav-proto {
  width: 220px;
  background: white;
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-domains {
  padding: var(--space-2) 0;
}

.sidebar-domain {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar-domain:hover,
.sidebar-domain.active {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.sidebar-domain-label { flex: 1; text-align: left; }

.sidebar-chevron {
  width: 12px;
  height: 12px;
  transition: transform var(--transition-normal);
}

.sidebar-chevron.rotated { transform: rotate(180deg); }

.sidebar-links {
  padding: var(--space-1) 0 var(--space-1) var(--space-8);
  display: flex;
  flex-direction: column;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar-link:hover {
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
  text-decoration: none;
}

/* Analysis */
.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.analysis-card {
  padding: var(--space-5);
  border-radius: var(--radius-xl);
  border: 1px solid;
}

.analysis-card.before {
  background: var(--color-danger-light);
  border-color: var(--color-danger);
}

.analysis-card.after {
  background: var(--color-success-light);
  border-color: var(--color-success);
}

.analysis-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-1);
}

.analysis-card.before .analysis-label { color: var(--color-danger-dark); }
.analysis-card.after .analysis-label { color: var(--color-success-dark); }

.analysis-count {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--space-3);
}

.analysis-card.before .analysis-count { color: var(--color-danger); }
.analysis-card.after .analysis-count { color: var(--color-success); }

.analysis-list {
  margin: 0;
  padding-left: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.analysis-list li {
  font-size: var(--font-size-sm);
  color: var(--color-text);
}
</style>
