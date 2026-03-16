<!-- @deprecated — dev scratch view, not routed -->
<template>
  <div class="layout-proto">
    <div class="proto-intro">
      <p>Drag-compose domain layouts using real design tokens. Select a layout template to preview.</p>
    </div>

    <div class="layout-picker">
      <button
        v-for="layout in layouts"
        :key="layout.id"
        class="layout-option"
        :class="{ active: activeLayout === layout.id }"
        @click="activeLayout = layout.id"
      >
        <div
          class="layout-thumb"
          v-html="layout.thumb"
        />
        <div class="layout-name">
          {{ layout.label }}
        </div>
      </button>
    </div>

    <!-- Previews -->
    <div class="frame-container">
      <!-- Two-panel: sidebar + main -->
      <div
        v-if="activeLayout === 'sidebar-main'"
        class="mock-app two-panel"
      >
        <div class="mock-sidebar">
          <div class="mock-section-label">
            Parameters
          </div>
          <div class="mock-field" />
          <div class="mock-field short" />
          <div class="mock-field" />
          <div class="mock-field short" />
          <div class="mock-btn primary">
            Run CAM
          </div>
        </div>
        <div class="mock-main">
          <div class="mock-toolbar">
            <div class="mock-breadcrumb" />
            <div class="mock-actions">
              <div class="mock-btn sm" />
              <div class="mock-btn sm primary" />
            </div>
          </div>
          <div class="mock-canvas">
            <div class="mock-preview-box">
              SVG / G-code Preview
            </div>
          </div>
        </div>
      </div>

      <!-- Three-panel: list + detail + inspector -->
      <div
        v-if="activeLayout === 'three-panel'"
        class="mock-app three-panel"
      >
        <div class="mock-list-panel">
          <div class="mock-section-label">
            Runs
          </div>
          <div class="mock-list-item active" />
          <div class="mock-list-item" />
          <div class="mock-list-item" />
          <div class="mock-list-item" />
        </div>
        <div class="mock-detail-panel">
          <div class="mock-toolbar">
            <div class="mock-breadcrumb wide" />
          </div>
          <div class="mock-detail-content">
            <div class="mock-stat-row">
              <div class="mock-stat" />
              <div class="mock-stat" />
              <div class="mock-stat" />
            </div>
            <div class="mock-block tall" />
          </div>
        </div>
        <div class="mock-inspector-panel">
          <div class="mock-section-label">
            Inspector
          </div>
          <div class="mock-field" />
          <div class="mock-field short" />
          <div class="mock-field" />
          <div class="mock-field" />
        </div>
      </div>

      <!-- Dashboard: header + card grid -->
      <div
        v-if="activeLayout === 'dashboard'"
        class="mock-app dashboard-layout"
      >
        <div class="mock-toolbar full">
          <div class="mock-breadcrumb" />
          <div class="mock-actions">
            <div class="mock-btn sm" />
            <div class="mock-btn sm primary" />
          </div>
        </div>
        <div class="mock-stat-row top-stats">
          <div class="mock-stat-card" />
          <div class="mock-stat-card" />
          <div class="mock-stat-card" />
          <div class="mock-stat-card" />
        </div>
        <div class="mock-card-grid">
          <div class="mock-card tall" />
          <div class="mock-card" />
          <div class="mock-card" />
          <div class="mock-card wide" />
        </div>
      </div>
    </div>

    <!-- Token annotations -->
    <div class="annotation-row">
      <div class="annotation">
        <div
          class="annotation-swatch"
          style="background: var(--color-surface)"
        />
        Surface
      </div>
      <div class="annotation">
        <div
          class="annotation-swatch"
          style="background: var(--color-surface-elevated)"
        />
        Elevated
      </div>
      <div class="annotation">
        <div
          class="annotation-swatch"
          style="background: var(--color-primary)"
        />
        Primary CTA
      </div>
      <div class="annotation">
        <div
          class="annotation-swatch"
          style="background: var(--color-border); border: 1px solid var(--color-border-light)"
        />
        Border
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const activeLayout = ref('sidebar-main')

const layouts = [
  {
    id: 'sidebar-main',
    label: 'Sidebar + Main',
    thumb: `<svg viewBox="0 0 60 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="60" height="40" rx="3" fill="#f9fafb"/>
      <rect x="1" y="1" width="16" height="38" rx="2" fill="#e5e7eb"/>
      <rect x="19" y="1" width="40" height="38" rx="2" fill="#fff"/>
      <rect x="21" y="3" width="36" height="5" rx="1" fill="#e5e7eb"/>
      <rect x="21" y="10" width="36" height="28" rx="1" fill="#dbeafe"/>
    </svg>`,
  },
  {
    id: 'three-panel',
    label: 'Three Panel',
    thumb: `<svg viewBox="0 0 60 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="60" height="40" rx="3" fill="#f9fafb"/>
      <rect x="1" y="1" width="13" height="38" rx="2" fill="#e5e7eb"/>
      <rect x="16" y="1" width="28" height="38" rx="2" fill="#fff"/>
      <rect x="46" y="1" width="13" height="38" rx="2" fill="#e5e7eb"/>
    </svg>`,
  },
  {
    id: 'dashboard',
    label: 'Dashboard',
    thumb: `<svg viewBox="0 0 60 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="60" height="40" rx="3" fill="#f9fafb"/>
      <rect x="1" y="1" width="58" height="6" rx="2" fill="#e5e7eb"/>
      <rect x="1" y="9" width="13" height="8" rx="1" fill="#dbeafe"/>
      <rect x="16" y="9" width="13" height="8" rx="1" fill="#dbeafe"/>
      <rect x="31" y="9" width="13" height="8" rx="1" fill="#dbeafe"/>
      <rect x="46" y="9" width="13" height="8" rx="1" fill="#dbeafe"/>
      <rect x="1" y="19" width="27" height="20" rx="1" fill="#fff"/>
      <rect x="30" y="19" width="13" height="9" rx="1" fill="#fff"/>
      <rect x="30" y="30" width="13" height="9" rx="1" fill="#fff"/>
      <rect x="45" y="19" width="14" height="20" rx="1" fill="#fff"/>
    </svg>`,
  },
]
</script>

<style scoped>
.layout-proto {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.proto-intro {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.layout-picker {
  display: flex;
  gap: var(--space-4);
}

.layout-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  cursor: pointer;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.layout-option.active {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.layout-thumb {
  width: 80px;
  height: 54px;
}

.layout-thumb svg {
  width: 100%;
  height: 100%;
}

.layout-name {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* Frame */
.frame-container {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  height: 360px;
}

.mock-app {
  height: 100%;
  display: flex;
  background: var(--color-surface-elevated);
}

/* Two panel */
.two-panel {}

.mock-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.mock-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mock-toolbar {
  height: 44px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-4);
}

.mock-canvas {
  flex: 1;
  padding: var(--space-4);
  display: flex;
}

.mock-preview-box {
  flex: 1;
  background: var(--color-primary-light);
  border: 2px dashed var(--color-primary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  color: var(--color-primary-dark);
  font-weight: var(--font-weight-medium);
}

/* Three panel */
.three-panel {}

.mock-list-panel {
  width: 180px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.mock-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
}

.mock-detail-content {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.mock-inspector-panel {
  width: 200px;
  flex-shrink: 0;
  background: var(--color-surface-elevated);
  border-left: 1px solid var(--color-border);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.mock-list-item {
  height: 36px;
  background: var(--color-surface-elevated);
  border-radius: var(--radius-md);
}

.mock-list-item.active {
  background: var(--color-primary-light);
  border-left: 3px solid var(--color-primary);
}

/* Dashboard */
.dashboard-layout {
  flex-direction: column;
  background: var(--color-surface-elevated);
}

.mock-toolbar.full {
  background: var(--color-surface);
}

.top-stats {
  padding: var(--space-3) var(--space-4) 0;
  gap: var(--space-3);
}

.mock-stat-card {
  flex: 1;
  height: 64px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.mock-card-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  grid-template-rows: 1fr 1fr;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  flex: 1;
}

.mock-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.mock-card.tall { grid-row: span 2; }
.mock-card.wide { grid-column: span 2; grid-row: span 2; }

/* Shared mock atoms */
.mock-section-label {
  font-size: 0.625rem;
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-light);
  margin-bottom: var(--space-1);
}

.mock-field {
  height: 28px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.mock-field.short { width: 60%; }

.mock-btn {
  height: 32px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mock-btn.primary { background: var(--color-primary); border-color: transparent; }
.mock-btn.sm { width: 60px; height: 26px; }

.mock-breadcrumb {
  height: 14px;
  width: 140px;
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
}

.mock-breadcrumb.wide { width: 200px; }

.mock-actions { display: flex; gap: var(--space-2); }

.mock-stat-row { display: flex; gap: var(--space-3); }

.mock-stat {
  flex: 1;
  height: 48px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.mock-block {
  background: var(--color-surface-elevated);
  border-radius: var(--radius-lg);
  flex: 1;
}

.mock-block.tall { flex: 1; }

/* Annotations */
.annotation-row {
  display: flex;
  gap: var(--space-6);
  align-items: center;
}

.annotation {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.annotation-swatch {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}
</style>
