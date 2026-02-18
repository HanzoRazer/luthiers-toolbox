<script setup lang="ts">
/**
 * CardPanel.vue - Reusable card container with header
 *
 * Reduces repetitive card/section patterns across god objects.
 * Provides consistent styling for bordered sections with optional header.
 */
defineOptions({ name: 'CardPanel' })

withDefaults(defineProps<{
  title?: string
  collapsible?: boolean
  defaultCollapsed?: boolean
}>(), {
  collapsible: false,
  defaultCollapsed: false,
})

import { ref } from 'vue'

const props = defineProps<{
  title?: string
  collapsible?: boolean
  defaultCollapsed?: boolean
}>()

const collapsed = ref(props.defaultCollapsed)

function toggle() {
  if (props.collapsible) {
    collapsed.value = !collapsed.value
  }
}
</script>

<template>
  <div class="card-panel">
    <div
      v-if="title || $slots.header"
      class="card-header"
      :class="{ clickable: collapsible }"
      @click="toggle"
    >
      <slot name="header">
        <h3 class="card-title">{{ title }}</h3>
      </slot>
      <div class="header-actions">
        <slot name="actions" />
        <button
          v-if="collapsible"
          class="collapse-btn"
          :aria-label="collapsed ? 'Expand' : 'Collapse'"
        >
          {{ collapsed ? '▸' : '▾' }}
        </button>
      </div>
    </div>
    <div
      v-show="!collapsed"
      class="card-body"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.card-panel {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.card-header.clickable {
  cursor: pointer;
  user-select: none;
}

.card-header.clickable:hover {
  background: #f3f4f6;
}

.card-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.collapse-btn {
  background: none;
  border: none;
  font-size: 0.875rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
}

.card-body {
  padding: 1rem;
}
</style>
