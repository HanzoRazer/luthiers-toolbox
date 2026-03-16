<template>
  <div class="dashboard">
    <!-- Top Navigation Bar -->
    <nav class="top-nav">
      <div class="nav-brand">
        <h1 class="brand-title">
          Production Shop
        </h1>
      </div>

      <div class="nav-menu">
        <div
          v-for="domain in domains"
          :key="domain.id"
          class="nav-item"
          @mouseenter="openMenu(domain.id)"
          @mouseleave="closeMenu(domain.id)"
        >
          <button
            class="nav-button"
            :class="{ active: activeMenu === domain.id }"
          >
            <span class="nav-icon">{{ domain.icon }}</span>
            <span class="nav-label">{{ domain.label }}</span>
            <span class="nav-arrow">▼</span>
          </button>

          <!-- Dropdown Menu -->
          <div
            v-if="activeMenu === domain.id"
            class="dropdown-menu"
          >
            <div class="dropdown-header">
              <span class="dropdown-icon">{{ domain.icon }}</span>
              <div>
                <div class="dropdown-title">
                  {{ domain.label }}
                </div>
                <div class="dropdown-desc">
                  {{ domain.description }}
                </div>
              </div>
            </div>
            <div class="dropdown-links">
              <RouterLink
                v-for="link in domain.links"
                :key="link.to"
                :to="link.to"
                class="dropdown-link"
                @click="closeAllMenus"
              >
                <span class="link-icon">{{ link.icon }}</span>
                <span class="link-label">{{ link.label }}</span>
                <span class="link-arrow">→</span>
              </RouterLink>
            </div>
          </div>
        </div>
      </div>

      <div class="nav-actions">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          class="nav-action-btn"
        >
          API Docs
        </a>
      </div>
    </nav>

    <!-- Main Content Area -->
    <div class="main-content">
      <div class="welcome-section">
        <h2 class="welcome-title">
          Welcome to Production Shop
        </h2>
        <p class="welcome-text">
          Select a module from the navigation above to get started. Use the dropdowns to access all tools and features.
        </p>

        <div class="quick-stats">
          <div class="stat-card">
            <div class="stat-icon">
              ⚙️
            </div>
            <div class="stat-value">
              8
            </div>
            <div class="stat-label">
              Modules
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              🛠️
            </div>
            <div class="stat-value">
              46
            </div>
            <div class="stat-label">
              Tools
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              ✨
            </div>
            <div class="stat-value">
              Vue 3
            </div>
            <div class="stat-label">
              Framework
            </div>
          </div>
        </div>

        <div class="quick-links">
          <h3 class="quick-links-title">
            Quick Access
          </h3>
          <div class="quick-links-grid">
            <RouterLink
              to="/rosette"
              class="quick-link-card"
            >
              <span class="quick-link-icon">🌹</span>
              <span class="quick-link-label">Rosette Pipeline</span>
            </RouterLink>
            <RouterLink
              to="/quick-cut"
              class="quick-link-card"
            >
              <span class="quick-link-icon">⚡</span>
              <span class="quick-link-label">Quick Cut</span>
            </RouterLink>
            <RouterLink
              to="/design-hub"
              class="quick-link-card"
            >
              <span class="quick-link-icon">🎸</span>
              <span class="quick-link-label">Design Hub</span>
            </RouterLink>
            <RouterLink
              to="/ai/assistant"
              class="quick-link-card"
            >
              <span class="quick-link-icon">🤖</span>
              <span class="quick-link-label">AI Assistant</span>
            </RouterLink>
            <RouterLink
              to="/art-studio"
              class="quick-link-card"
            >
              <span class="quick-link-icon">🎨</span>
              <span class="quick-link-label">Art Studio</span>
            </RouterLink>
            <RouterLink
              to="/cam/simulator"
              class="quick-link-card"
            >
              <span class="quick-link-icon">🎥</span>
              <span class="quick-link-label">Toolpath Simulator</span>
            </RouterLink>
            <RouterLink
              to="/rmos/runs"
              class="quick-link-card"
            >
              <span class="quick-link-icon">📋</span>
              <span class="quick-link-label">RMOS Runs</span>
            </RouterLink>
            <RouterLink
              to="/calculators"
              class="quick-link-card"
            >
              <span class="quick-link-icon">💰</span>
              <span class="quick-link-label">Calculators</span>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Status Bar -->
    <div class="footer-bar">
      <span class="footer-chip ok">✓ App running</span>
      <span class="footer-chip">Vite HMR Active</span>
      <a
        href="../production_shop/index.html"
        class="footer-chip link"
      >
        ← Marketing Site
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeMenu = ref<string | null>(null)

const domains = [
  {
    id: 'design',
    label: 'Design',
    icon: '✏️',
    description: 'Guitar geometry, rosette, art studio, blueprint import',
    links: [
      { icon: '🎸', label: 'Design Hub',      to: '/design-hub' },
      { icon: '🌹', label: 'Rosette Pipeline', to: '/rosette' },
      { icon: '🎨', label: 'Art Studio',       to: '/art-studio' },
      { icon: '📋', label: 'Blueprint Lab',    to: '/blueprint' },
      { icon: '📐', label: 'Instrument Geometry', to: '/instrument-geometry' },
    ],
  },
  {
    id: 'art-studio',
    label: 'Art Studio',
    icon: '🎨',
    description: 'Decorative elements: binding, headstock, purfling, rosettes',
    links: [
      { icon: '🎨', label: 'Art Studio Home', to: '/art-studio' },
      { icon: '📐', label: 'Bracing',        to: '/art-studio/bracing' },
      { icon: '🔲', label: 'Binding',         to: '/art-studio/binding' },
      { icon: '🎸', label: 'Headstock',       to: '/art-studio/headstock' },
      { icon: '〰️', label: 'Purfling',        to: '/art-studio/purfling' },
      { icon: '⭕', label: 'Soundhole',       to: '/art-studio/soundhole' },
      { icon: '💎', label: 'Fret Markers',    to: '/art-studio/fret-markers' },
      { icon: '🗿', label: 'Relief Carving',  to: '/art-studio/relief' },
      { icon: '💠', label: 'Inlay Workspace', to: '/art-studio/inlay-workspace' },
      { icon: '💠', label: 'Inlay Designer',  to: '/art-studio/inlay' },
      { icon: '✒️', label: 'V-Carve',         to: '/art-studio/vcarve' },
    ],
  },
  {
    id: 'cam',
    label: 'CAM',
    icon: '⚙️',
    description: 'Toolpath generation, G-code, and CNC pipeline',
    links: [
      { icon: '⚡', label: 'Quick Cut',       to: '/quick-cut' },
      { icon: '🔧', label: 'CAM Pipeline',    to: '/pipeline' },
      { icon: '🕳️', label: 'Pocket Clearing', to: '/cam/pocket' },
      { icon: '✂️', label: 'Contour Cutting', to: '/cam/contour' },
      { icon: '🔳', label: 'Surfacing',       to: '/cam/surfacing' },
      { icon: '🔩', label: 'Drilling',        to: '/cam/drilling' },
      { icon: '🎸', label: 'Fret Slotting',   to: '/cam/fret-slots' },
      { icon: '🎥', label: 'Simulator',       to: '/cam/simulator' },
      { icon: '↔️', label: 'DXF → G-code',   to: '/cam/dxf-to-gcode' },
      { icon: '🌀', label: 'Adaptive Lab',    to: '/lab/adaptive' },
      { icon: '🪚', label: 'Saw Lab',         to: '/lab/saw/slice' },
      { icon: '🌉', label: 'Bridge Lab',      to: '/lab/bridge' },
    ],
  },
  {
    id: 'production',
    label: 'Production',
    icon: '🏭',
    description: 'RMOS manufacturing, inventory, quality, orders',
    links: [
      { icon: '📋', label: 'RMOS Runs',       to: '/rmos/runs' },
      { icon: '📡', label: 'Live Monitor',    to: '/rmos/live-monitor' },
      { icon: '📦', label: 'Inventory',       to: '/rmos/inventory' },
      { icon: '✅', label: 'Quality Control', to: '/rmos/quality' },
      { icon: '⏱️', label: 'Time Tracking',   to: '/rmos/time' },
      { icon: '📝', label: 'Orders',          to: '/rmos/orders' },
      { icon: '🔄', label: 'Compare Runs',    to: '/compare' },
      { icon: '🏭', label: 'CNC Production',  to: '/cnc' },
    ],
  },
  {
    id: 'ai',
    label: 'AI Tools',
    icon: '🤖',
    description: 'AI-powered analysis, recommendations, and assistance',
    links: [
      { icon: '🎨', label: 'AI Images',       to: '/ai-images' },
      { icon: '🪵', label: 'Wood Grading',    to: '/ai/wood-grading' },
      { icon: '💡', label: 'Recommendations', to: '/ai/recommendations' },
      { icon: '💬', label: 'Assistant',       to: '/ai/assistant' },
      { icon: '🔍', label: 'Defect Detection', to: '/ai/defect-detection' },
    ],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: '📊',
    description: 'Risk dashboards, acoustics, and monitoring',
    links: [
      { icon: '📈', label: 'CAM Dashboard',   to: '/saw' },
      { icon: '🔬', label: 'Audio Analyzer',  to: '/tools/audio-analyzer' },
      { icon: '📚', label: 'Acoustics Library', to: '/tools/audio-analyzer/library' },
      { icon: '🎵', label: 'Acoustics Runs',  to: '/tools/audio-analyzer/runs' },
      { icon: '⚠️', label: 'Risk Timeline',   to: '/lab/risk-timeline' },
    ],
  },
  {
    id: 'business',
    label: 'Business',
    icon: '💼',
    description: 'Costing, ROI, cash flow, and engineering estimators',
    links: [
      { icon: '💰', label: 'Calculators',     to: '/calculators' },
      { icon: '📊', label: 'Estimator',       to: '/business/estimator' },
    ],
  },
  {
    id: 'dev',
    label: 'Dev Tools',
    icon: '🛠️',
    description: 'Design sandbox, component gallery, nav prototype',
    links: [
      { icon: '🎨', label: 'UI Sandbox',      to: '/dev/sandbox' },
    ],
  },
]

function openMenu(id: string) {
  activeMenu.value = id
}

function closeMenu(id: string) {
  if (activeMenu.value === id) {
    activeMenu.value = null
  }
}

function closeAllMenus() {
  activeMenu.value = null
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-alt, #f8fafc);
}

/* ===== TOP NAVIGATION BAR ===== */
.top-nav {
  background: var(--color-surface, #ffffff);
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 var(--space-6, 1.5rem);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  margin-right: var(--space-8, 2rem);
}

.brand-title {
  font-size: var(--font-size-xl, 1.25rem);
  font-weight: 700;
  color: var(--color-text, #1e293b);
  margin: 0;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: var(--space-1, 0.25rem);
  flex: 1;
}

.nav-item {
  position: relative;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
  padding: var(--space-2, 0.5rem) var(--space-4, 1rem);
  background: none;
  border: none;
  border-radius: var(--radius-md, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 500;
  color: var(--color-text-muted, #64748b);
  cursor: pointer;
  transition: all 0.2s;
}

.nav-button:hover,
.nav-button.active {
  background: var(--color-primary-light, #dbeafe);
  color: var(--color-primary, #2563eb);
}

.nav-icon {
  font-size: 1.125rem;
}

.nav-arrow {
  font-size: 0.625rem;
  opacity: 0.6;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
}

.nav-action-btn {
  padding: var(--space-2, 0.5rem) var(--space-4, 1rem);
  background: var(--color-primary, #2563eb);
  color: white;
  border-radius: var(--radius-md, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s;
}

.nav-action-btn:hover {
  background: var(--color-primary-dark, #1d4ed8);
  text-decoration: none;
}

/* ===== DROPDOWN MENUS ===== */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 320px;
  background: var(--color-surface, #ffffff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-lg, 0.75rem);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  padding: var(--space-3, 0.75rem);
  z-index: 1000;
  animation: dropdownFadeIn 0.2s ease;
}

@keyframes dropdownFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
  padding: var(--space-3, 0.75rem);
  border-bottom: 1px solid var(--color-border, #e2e8f0);
  margin-bottom: var(--space-2, 0.5rem);
}

.dropdown-icon {
  font-size: 1.5rem;
}

.dropdown-title {
  font-size: var(--font-size-base, 1rem);
  font-weight: 700;
  color: var(--color-text, #1e293b);
}

.dropdown-desc {
  font-size: var(--font-size-xs, 0.75rem);
  color: var(--color-text-muted, #64748b);
  margin-top: 2px;
}

.dropdown-links {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-link {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
  padding: var(--space-2, 0.5rem) var(--space-3, 0.75rem);
  border-radius: var(--radius-md, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text, #1e293b);
  text-decoration: none;
  transition: all 0.15s;
}

.dropdown-link:hover {
  background: var(--color-primary-light, #dbeafe);
  color: var(--color-primary, #2563eb);
  text-decoration: none;
}

.link-icon {
  width: 1.25rem;
  text-align: center;
}

.link-label {
  flex: 1;
}

.link-arrow {
  opacity: 0;
  font-size: 0.75rem;
  transition: opacity 0.15s;
}

.dropdown-link:hover .link-arrow {
  opacity: 1;
}

/* ===== MAIN CONTENT ===== */
.main-content {
  flex: 1;
  padding: var(--space-8, 2rem) var(--space-6, 1.5rem);
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-8, 2rem);
}

.welcome-title {
  font-size: var(--font-size-3xl, 1.875rem);
  font-weight: 800;
  color: var(--color-text, #1e293b);
  margin: 0;
}

.welcome-text {
  font-size: var(--font-size-lg, 1.125rem);
  color: var(--color-text-muted, #64748b);
  max-width: 600px;
  margin: 0;
}

/* Quick Stats */
.quick-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4, 1rem);
}

.stat-card {
  background: var(--color-surface, #ffffff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-lg, 0.75rem);
  padding: var(--space-6, 1.5rem);
  text-align: center;
  transition: all 0.2s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 2rem;
  margin-bottom: var(--space-2, 0.5rem);
}

.stat-value {
  font-size: var(--font-size-3xl, 1.875rem);
  font-weight: 800;
  color: var(--color-primary, #2563eb);
  margin-bottom: var(--space-1, 0.25rem);
}

.stat-label {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
  font-weight: 500;
}

/* Quick Links */
.quick-links-title {
  font-size: var(--font-size-xl, 1.25rem);
  font-weight: 700;
  color: var(--color-text, #1e293b);
  margin-bottom: var(--space-4, 1rem);
}

.quick-links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-4, 1rem);
}

.quick-link-card {
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
  padding: var(--space-4, 1rem);
  background: var(--color-surface, #ffffff);
  border: 2px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-lg, 0.75rem);
  text-decoration: none;
  transition: all 0.2s;
}

.quick-link-card:hover {
  border-color: var(--color-primary, #2563eb);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
  transform: translateY(-2px);
  text-decoration: none;
}

.quick-link-icon {
  font-size: 1.5rem;
}

.quick-link-label {
  font-size: var(--font-size-base, 1rem);
  font-weight: 600;
  color: var(--color-text, #1e293b);
}

/* ===== FOOTER BAR ===== */
.footer-bar {
  background: var(--color-surface, #ffffff);
  border-top: 1px solid var(--color-border, #e2e8f0);
  padding: var(--space-3, 0.75rem) var(--space-6, 1.5rem);
  display: flex;
  align-items: center;
  gap: var(--space-3, 0.75rem);
}

.footer-chip {
  font-size: var(--font-size-xs, 0.75rem);
  padding: var(--space-1, 0.25rem) var(--space-3, 0.75rem);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: var(--radius-full, 9999px);
  color: var(--color-text-muted, #64748b);
  text-decoration: none;
}

.footer-chip.ok {
  border-color: var(--color-success, #10b981);
  color: var(--color-success, #10b981);
  background: rgba(16, 185, 129, 0.1);
}

.footer-chip.link:hover {
  border-color: var(--color-primary, #2563eb);
  color: var(--color-primary, #2563eb);
  text-decoration: none;
}
</style>
