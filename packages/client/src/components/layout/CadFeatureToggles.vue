<script setup lang="ts">
/**
 * CadFeatureToggles.vue
 *
 * Panel with checkbox toggles for view-specific display features.
 * Used in right sidebar for controlling visibility and behavior options.
 */

import CadCheckbox from "@/components/ui/CadCheckbox.vue";

export interface FeatureToggleItem {
  key: string;
  label: string;
  description?: string;
  checked: boolean;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    /** Feature toggles configuration */
    features: FeatureToggleItem[];
    /** Panel title */
    title?: string;
    /** Show panel title */
    showTitle?: boolean;
    /** Compact mode (less padding) */
    compact?: boolean;
  }>(),
  {
    title: "Display Options",
    showTitle: false,
    compact: false,
  }
);

const emit = defineEmits<{
  (e: "toggle", key: string, checked: boolean): void;
  (e: "update:features", features: FeatureToggleItem[]): void;
}>();

function handleToggle(feature: FeatureToggleItem) {
  if (feature.disabled) return;

  const newChecked = !feature.checked;
  emit("toggle", feature.key, newChecked);

  // Emit updated features array
  const updatedFeatures = props.features.map((f) =>
    f.key === feature.key ? { ...f, checked: newChecked } : f
  );
  emit("update:features", updatedFeatures);
}
</script>

<template>
  <div class="cad-feature-toggles" :class="{ compact: compact }">
    <div v-if="showTitle" class="toggles-title">{{ title }}</div>
    <div class="toggles-list">
      <div
        v-for="feature in features"
        :key="feature.key"
        class="toggle-item"
        :class="{ disabled: feature.disabled }"
      >
        <CadCheckbox
          :model-value="feature.checked"
          :label="feature.label"
          :description="feature.description"
          :disabled="feature.disabled"
          @update:model-value="handleToggle(feature)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.cad-feature-toggles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toggles-title {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary, #a0a0a0);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 8px;
}

.toggles-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cad-feature-toggles.compact .toggles-list {
  gap: 6px;
}

.toggle-item {
  padding: 4px 0;
}

.toggle-item.disabled {
  opacity: 0.5;
}

/* Hover state for toggle items */
.toggle-item:hover:not(.disabled) {
  background: var(--color-bg-panel-elevated, #2d2d2d);
  margin: 0 -8px;
  padding: 4px 8px;
  border-radius: 4px;
}

.cad-feature-toggles.compact .toggle-item {
  padding: 2px 0;
}
</style>
