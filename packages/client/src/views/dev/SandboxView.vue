<template>
  <div class="sandbox">
    <!-- Sidebar -->
    <aside class="sandbox-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-logo">🎸</span>
        <div>
          <div class="sidebar-title">
            Dev Sandbox
          </div>
          <div class="sidebar-sub">
            Production Shop UI Lab
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="section in sections"
          :key="section.id"
          class="nav-section"
        >
          <div class="nav-section-label">
            {{ section.label }}
          </div>
          <button
            v-for="item in section.items"
            :key="item.id"
            class="nav-item"
            :class="{ active: activePanel === item.id }"
            @click="activePanel = item.id"
          >
            <span class="nav-item-icon">{{ item.icon }}</span>
            {{ item.label }}
          </button>
        </div>
      </nav>

      <div class="sidebar-footer">
        <RouterLink
          to="/"
          class="back-link"
        >
          ← Back to App
        </RouterLink>
      </div>
    </aside>

    <!-- Main content -->
    <main class="sandbox-main">
      <div class="sandbox-toolbar">
        <h1 class="panel-title">
          {{ currentPanel?.label }}
        </h1>
        <div class="toolbar-meta">
          <span class="meta-chip">Vue 3 + TypeScript</span>
          <span class="meta-chip">Tailwind + CSS Tokens</span>
          <span class="meta-chip">530 components</span>
        </div>
      </div>

      <div class="sandbox-content">
        <TokenExplorer v-if="activePanel === 'tokens'" />
        <ComponentGallery v-else-if="activePanel === 'components'" />
        <NavProto v-else-if="activePanel === 'nav'" />
        <LayoutProto v-else-if="activePanel === 'layout'" />
        <TypographyScale v-else-if="activePanel === 'typography'" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import TokenExplorer from './TokenExplorer.vue'
import ComponentGallery from './ComponentGallery.vue'
import NavProto from './NavProto.vue'
import LayoutProto from './LayoutProto.vue'
import TypographyScale from './TypographyScale.vue'

const activePanel = ref('tokens')

const sections = [
  {
    id: 'foundations',
    label: 'Foundations',
    items: [
      { id: 'tokens', label: 'Design Tokens', icon: '🎨' },
      { id: 'typography', label: 'Typography', icon: '✏️' },
    ],
  },
  {
    id: 'components',
    label: 'Components',
    items: [
      { id: 'components', label: 'Component Gallery', icon: '🧩' },
    ],
  },
  {
    id: 'layout',
    label: 'Architecture',
    items: [
      { id: 'nav', label: 'Nav Prototype', icon: '🗺️' },
      { id: 'layout', label: 'Layout Prototype', icon: '📐' },
    ],
  },
]

const allItems = sections.flatMap(s => s.items)
const currentPanel = computed(() => allItems.find(i => i.id === activePanel.value))
</script>

<style scoped>
.sandbox {
  display: flex;
  min-height: 100vh;
  background: var(--color-surface-elevated);
  font-family: var(--font-family-sans);
}

/* Sidebar */
.sandbox-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}

.sidebar-logo {
  font-size: 1.5rem;
}

.sidebar-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}

.sidebar-sub {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-3) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.nav-section {
  display: flex;
  flex-direction: column;
}

.nav-section-label {
  font-size: 0.625rem;
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-light);
  padding: 0 var(--space-4) var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast);
  border-left: 2px solid transparent;
}

.nav-item:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.nav-item.active {
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
  border-left-color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

.nav-item-icon {
  font-size: 0.875rem;
  width: 1.25rem;
  text-align: center;
}

.sidebar-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.back-link {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--color-primary);
  text-decoration: none;
}

/* Main */
.sandbox-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sandbox-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.panel-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0;
}

.toolbar-meta {
  display: flex;
  gap: var(--space-2);
}

.meta-chip {
  font-size: var(--font-size-xs);
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-muted);
}

.sandbox-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}
</style>
