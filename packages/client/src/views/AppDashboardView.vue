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
              <template v-if="domain.links.length">
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
              </template>
              <p
                v-else
                class="dropdown-coming-soon"
              >
                Coming soon
              </p>
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
              5
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
              :to="assistantTo"
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
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useInstrumentProject } from '@/instrument-workspace/shared-state/useInstrumentProject'

const route = useRoute()
const { projectId: hubProjectId } = useInstrumentProject()

const assistantTo = computed(() => {
  const q = route.query.project_id
  const fromRoute =
    typeof q === 'string' && q
      ? q
      : Array.isArray(q) && q[0]
        ? String(q[0])
        : ''
  const pid = fromRoute || hubProjectId.value || ''
  if (pid) {
    return {
      name: 'AiAssistantProject' as const,
      params: { projectId: pid },
    }
  }
  return { name: 'AiAssistant' as const }
})

const activeMenu = ref<string | null>(null)

// Nav reorganized into 5 modules (routes unchanged)
const domains = [
  // MODULE 1 — DESIGN
  {
    id: 'design',
    label: 'Design',
    icon: '✏️',
    description: 'New project, instrument hub, blueprint lab',
    links: [
      { icon: '📁', label: 'New Project',     to: '/design-hub' },
      { icon: '🎸', label: 'Instrument Hub',   to: '/instrument-geometry' },
      { icon: '📋', label: 'Blueprint Lab',    to: '/blueprint' },
    ],
  },
  // MODULE 2 — ART STUDIO
  {
    id: 'art-studio',
    label: 'Art Studio',
    icon: '🎨',
    description: 'Soundhole & rosette, inlay, binding & purfling, headstock',
    links: [
      { icon: '🌹', label: 'Soundhole & Rosette', to: '/art-studio/soundhole-rosette-workspace' },
      { icon: '💠', label: 'Inlay Workspace', to: '/art-studio/inlay-workspace' },
      { icon: '🔲', label: 'Binding & Purfling', to: '/art-studio/binding' },
      { icon: '🎸', label: 'Headstock',       to: '/art-studio/headstock' },
    ],
  },
  // MODULE 3 — CAM
  {
    id: 'cam',
    label: 'CAM',
    icon: '⚙️',
    description: 'Adaptive, saw, bridge, helical, V-Carve, relief, polygon offset',
    links: [
      { icon: '📐', label: 'CAM Workspace',   to: '/cam/workspace' },
      { icon: '🎸', label: 'Neck Designer',  to: '/cam/neck' },
      { icon: '🌀', label: 'Adaptive Lab',    to: '/lab/adaptive' },
      { icon: '🪚', label: 'Saw Lab',         to: '/lab/saw/slice' },
      { icon: '🌉', label: 'Bridge Lab',      to: '/lab/bridge' },
      { icon: '🌊', label: 'Helical Ramp Lab', to: '/lab/helical' },
      { icon: '🔧', label: 'V-Carve',         to: '/art-studio/vcarve' },
      { icon: '🗿', label: 'Relief Carving',  to: '/art-studio/relief' },
      { icon: '🔺', label: 'Polygon Offset Lab', to: '/lab/polygon-offset' },
    ],
  },
  // MODULE 4 — SHOP FLOOR
  {
    id: 'shop-floor',
    label: 'Shop Floor',
    icon: '🏭',
    description: 'Manufacturing runs, job queue',
    links: [
      { icon: '📋', label: 'Manufacturing Runs', to: '/rmos/runs' },
      { icon: '📬', label: 'Job Queue',       to: '/job-queue' },
    ],
  },
  // MODULE 5 — SMART GUITAR
  {
    id: 'smart-guitar',
    label: 'Smart Guitar',
    icon: '🎸',
    description: 'Body design, electronics, RPi5 cavity, WiFi, export & BOM',
    links: [
      { icon: '🎸', label: 'Smart Guitar', to: '/smart-guitar' },
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

.dropdown-coming-soon {
  padding: var(--space-3, 0.75rem);
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #64748b);
  font-style: italic;
  margin: 0;
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
