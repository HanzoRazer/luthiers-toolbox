<script setup lang="ts">
/**
 * CadPanel.vue
 *
 * Collapsible panel for VCarve/Fusion 360 style property groups.
 * Used in right sidebar for organizing tool settings, parameters, etc.
 */

import { ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    /** Panel title */
    title: string;
    /** Initial collapsed state */
    collapsed?: boolean;
    /** Show collapse/expand chevron */
    collapsible?: boolean;
    /** Panel icon (optional SVG path) */
    icon?: string;
  }>(),
  {
    collapsed: false,
    collapsible: true,
    icon: "",
  }
);

const emit = defineEmits<{
  (e: "toggle", collapsed: boolean): void;
}>();

const isCollapsed = ref(props.collapsed);

watch(
  () => props.collapsed,
  (val) => {
    isCollapsed.value = val;
  }
);

function toggle() {
  if (!props.collapsible) return;
  isCollapsed.value = !isCollapsed.value;
  emit("toggle", isCollapsed.value);
}
</script>

<template>
  <div class="cad-panel" :class="{ collapsed: isCollapsed }">
    <!-- Panel Header -->
    <div
      class="cad-panel-header"
      :class="{ clickable: collapsible }"
      @click="toggle"
    >
      <div class="header-left">
        <svg
          v-if="icon"
          class="panel-icon"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path :d="icon" />
        </svg>
        <span class="panel-title">{{ title }}</span>
      </div>

      <div class="header-right">
        <!-- Custom header actions -->
        <slot name="header-actions" />

        <!-- Collapse chevron -->
        <svg
          v-if="collapsible"
          class="chevron"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </div>
    </div>

    <!-- Panel Content -->
    <div v-show="!isCollapsed" class="cad-panel-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.cad-panel {
  background: var(--color-bg-panel, #242424);
  border-radius: 4px;
  margin-bottom: 8px;
  overflow: hidden;
}

.cad-panel:last-child {
  margin-bottom: 0;
}

.cad-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: linear-gradient(
    180deg,
    var(--color-bg-panel-elevated, #2d2d2d) 0%,
    var(--color-bg-panel, #242424) 100%
  );
  border-bottom: 1px solid var(--color-border-panel, #3a3a3a);
  user-select: none;
}

.cad-panel-header.clickable {
  cursor: pointer;
}

.cad-panel-header.clickable:hover {
  background: var(--color-bg-panel-elevated, #2d2d2d);
}

.cad-panel.collapsed .cad-panel-header {
  border-bottom: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-icon {
  flex-shrink: 0;
  color: var(--color-accent, #4a9eff);
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chevron {
  flex-shrink: 0;
  color: var(--color-text-muted, #707070);
  transition: transform 0.15s ease;
}

.cad-panel.collapsed .chevron {
  transform: rotate(-90deg);
}

.cad-panel-content {
  padding: 12px;
}

/* Support for nested panels */
.cad-panel .cad-panel {
  background: var(--color-bg-panel-elevated, #2d2d2d);
}

.cad-panel .cad-panel .cad-panel-header {
  background: transparent;
  padding: 8px 10px;
}

.cad-panel .cad-panel .cad-panel-content {
  padding: 10px;
}
</style>
