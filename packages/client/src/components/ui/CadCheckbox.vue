<script setup lang="ts">
/**
 * CadCheckbox.vue
 *
 * VCarve/Fusion 360 style checkbox for feature toggles.
 */

import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    /** v-model binding */
    modelValue: boolean;
    /** Checkbox label */
    label?: string;
    /** Optional description below label */
    description?: string;
    /** Disabled state */
    disabled?: boolean;
    /** Indeterminate state */
    indeterminate?: boolean;
    /** Unique identifier */
    id?: string;
  }>(),
  {
    label: "",
    description: "",
    disabled: false,
    indeterminate: false,
    id: "",
  }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
}>();

const inputId = computed(() => props.id || `cad-checkbox-${Math.random().toString(36).slice(2, 9)}`);

function handleChange(event: Event) {
  const target = event.target as HTMLInputElement;
  emit("update:modelValue", target.checked);
}
</script>

<template>
  <label
    class="cad-checkbox"
    :class="{ disabled: disabled }"
    :for="inputId"
  >
    <input
      :id="inputId"
      type="checkbox"
      class="cad-checkbox-input"
      :checked="modelValue"
      :disabled="disabled"
      :indeterminate="indeterminate"
      @change="handleChange"
    />
    <span v-if="label || description" class="cad-checkbox-label">
      <span v-if="label" class="cad-checkbox-text">{{ label }}</span>
      <span v-if="description" class="cad-checkbox-description">{{ description }}</span>
    </span>
    <slot />
  </label>
</template>

<style scoped>
.cad-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}

.cad-checkbox.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cad-checkbox-input {
  position: relative;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  margin-top: 1px;
  background: var(--color-bg-input, #333333);
  border: 1px solid var(--color-border-input, #4a4a4a);
  border-radius: 3px;
  appearance: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.cad-checkbox.disabled .cad-checkbox-input {
  cursor: not-allowed;
}

.cad-checkbox-input:hover:not(:disabled) {
  border-color: var(--color-accent, #4a9eff);
}

.cad-checkbox-input:checked {
  background: var(--color-accent, #4a9eff);
  border-color: var(--color-accent, #4a9eff);
}

.cad-checkbox-input:checked::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 5px;
  width: 4px;
  height: 8px;
  border: solid #fff;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.cad-checkbox-input:focus {
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.3);
  outline: none;
}

.cad-checkbox-input:indeterminate {
  background: var(--color-accent, #4a9eff);
  border-color: var(--color-accent, #4a9eff);
}

.cad-checkbox-input:indeterminate::after {
  content: '';
  position: absolute;
  top: 6px;
  left: 3px;
  width: 8px;
  height: 2px;
  background: #fff;
}

.cad-checkbox-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cad-checkbox-text {
  font-size: 12px;
  color: var(--color-text-primary, #e0e0e0);
  line-height: 1.4;
}

.cad-checkbox-description {
  font-size: 11px;
  color: var(--color-text-muted, #707070);
  line-height: 1.4;
}
</style>
