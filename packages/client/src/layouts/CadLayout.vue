<script setup lang="ts">
/**
 * CadLayout.vue
 *
 * Master 3-panel layout wrapper for VCarve/Fusion 360 style UI.
 * Provides consistent structure across all CAM views.
 *
 * Layout:
 * ┌──────────────────────────────────────────────────────────────┐
 * │  HeaderBar                                                    │
 * ├────────────┬────────────────────────────┬────────────────────┤
 * │  LeftPanel │      CenterCanvas          │    RightPanel      │
 * │  (nav)     │      (main content)        │    (properties)    │
 * ├────────────┴────────────────────────────┴────────────────────┤
 * │  StatusBar                                                    │
 * └──────────────────────────────────────────────────────────────┘
 */

import { computed } from "vue";
import CadHeaderBar from "@/components/layout/CadHeaderBar.vue";
import CadStatusBar from "@/components/layout/CadStatusBar.vue";

const props = withDefaults(
  defineProps<{
    /** Show left sidebar panel */
    showLeftPanel?: boolean;
    /** Show right properties panel */
    showRightPanel?: boolean;
    /** Width of left panel */
    leftPanelWidth?: string;
    /** Width of right panel */
    rightPanelWidth?: string;
    /** Show header bar */
    showHeader?: boolean;
    /** Show status bar */
    showStatus?: boolean;
    /** Page title for header */
    title?: string;
  }>(),
  {
    showLeftPanel: true,
    showRightPanel: true,
    leftPanelWidth: "240px",
    rightPanelWidth: "320px",
    showHeader: true,
    showStatus: true,
    title: "",
  }
);

const gridStyle = computed(() => {
  const cols: string[] = [];

  if (props.showLeftPanel) {
    cols.push(props.leftPanelWidth);
  }

  cols.push("1fr"); // Center always flex

  if (props.showRightPanel) {
    cols.push(props.rightPanelWidth);
  }

  return {
    gridTemplateColumns: cols.join(" "),
  };
});
</script>

<template>
  <div class="cad-layout">
    <!-- Header -->
    <header v-if="showHeader" class="cad-header">
      <slot name="header">
        <CadHeaderBar :title="title" />
      </slot>
    </header>

    <!-- Main Content Area -->
    <div class="cad-main" :style="gridStyle">
      <!-- Left Sidebar -->
      <aside v-if="showLeftPanel" class="cad-left-panel">
        <slot name="left">
          <!-- Default: empty, views provide navigation -->
        </slot>
      </aside>

      <!-- Center Canvas -->
      <main class="cad-canvas">
        <slot>
          <!-- Main content goes here -->
        </slot>
      </main>

      <!-- Right Properties Panel -->
      <aside v-if="showRightPanel" class="cad-right-panel">
        <slot name="right">
          <!-- Properties panels go here -->
        </slot>
      </aside>
    </div>

    <!-- Status Bar -->
    <footer v-if="showStatus" class="cad-status">
      <slot name="status">
        <CadStatusBar />
      </slot>
    </footer>
  </div>
</template>

<style scoped>
.cad-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-app, #1a1a1a);
  color: var(--color-text-primary, #e0e0e0);
  overflow: hidden;
}

.cad-header {
  flex-shrink: 0;
  height: 48px;
  background: var(--color-bg-panel, #242424);
  border-bottom: 1px solid var(--color-border-panel, #3a3a3a);
}

.cad-main {
  flex: 1;
  display: grid;
  overflow: hidden;
}

.cad-left-panel {
  background: var(--color-bg-panel, #242424);
  border-right: 1px solid var(--color-border-panel, #3a3a3a);
  overflow-y: auto;
  overflow-x: hidden;
}

.cad-canvas {
  background: var(--color-bg-canvas, #1e1e1e);
  overflow: auto;
  position: relative;
}

.cad-right-panel {
  background: var(--color-bg-panel, #242424);
  border-left: 1px solid var(--color-border-panel, #3a3a3a);
  overflow-y: auto;
  overflow-x: hidden;
}

.cad-status {
  flex-shrink: 0;
  height: 24px;
  background: var(--color-bg-panel-elevated, #2d2d2d);
  border-top: 1px solid var(--color-border-panel, #3a3a3a);
}

/* Scrollbar styling for dark theme */
.cad-left-panel::-webkit-scrollbar,
.cad-right-panel::-webkit-scrollbar,
.cad-canvas::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.cad-left-panel::-webkit-scrollbar-track,
.cad-right-panel::-webkit-scrollbar-track,
.cad-canvas::-webkit-scrollbar-track {
  background: var(--color-bg-panel, #242424);
}

.cad-left-panel::-webkit-scrollbar-thumb,
.cad-right-panel::-webkit-scrollbar-thumb,
.cad-canvas::-webkit-scrollbar-thumb {
  background: var(--color-border-panel, #3a3a3a);
  border-radius: 4px;
}

.cad-left-panel::-webkit-scrollbar-thumb:hover,
.cad-right-panel::-webkit-scrollbar-thumb:hover,
.cad-canvas::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}
</style>
