<script setup lang="ts">
/**
 * CadInput.vue
 *
 * VCarve/Fusion 360 style input field with label and suffix support.
 */

import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    /** v-model binding */
    modelValue: string | number;
    /** Input label */
    label?: string;
    /** Input type */
    type?: "text" | "number" | "email" | "password";
    /** Placeholder text */
    placeholder?: string;
    /** Suffix (e.g., "mm", "%") */
    suffix?: string;
    /** Prefix (e.g., "$") */
    prefix?: string;
    /** Disabled state */
    disabled?: boolean;
    /** Read-only state */
    readonly?: boolean;
    /** Minimum value (for number input) */
    min?: number;
    /** Maximum value (for number input) */
    max?: number;
    /** Step value (for number input) */
    step?: number;
    /** Unique identifier */
    id?: string;
  }>(),
  {
    label: "",
    type: "text",
    placeholder: "",
    suffix: "",
    prefix: "",
    disabled: false,
    readonly: false,
    min: undefined,
    max: undefined,
    step: undefined,
    id: "",
  }
);

const emit = defineEmits<{
  (e: "update:modelValue", value: string | number): void;
  (e: "blur", event: FocusEvent): void;
  (e: "focus", event: FocusEvent): void;
}>();

const inputId = computed(() => props.id || `cad-input-${Math.random().toString(36).slice(2, 9)}`);

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  const value = props.type === "number" ? parseFloat(target.value) || 0 : target.value;
  emit("update:modelValue", value);
}

function handleBlur(event: FocusEvent) {
  emit("blur", event);
}

function handleFocus(event: FocusEvent) {
  emit("focus", event);
}
</script>

<template>
  <div class="cad-input" :class="{ disabled: disabled }">
    <label v-if="label" :for="inputId" class="cad-input-label">
      {{ label }}
    </label>
    <div class="cad-input-wrapper">
      <span v-if="prefix" class="cad-input-prefix">{{ prefix }}</span>
      <input
        :id="inputId"
        :type="type"
        class="cad-input-field"
        :class="{ 'has-prefix': prefix, 'has-suffix': suffix }"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :min="min"
        :max="max"
        :step="step"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      <span v-if="suffix" class="cad-input-suffix">{{ suffix }}</span>
    </div>
  </div>
</template>

<style scoped>
.cad-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cad-input.disabled {
  opacity: 0.5;
}

.cad-input-label {
  font-size: 11px;
  color: var(--color-text-secondary, #a0a0a0);
}

.cad-input-wrapper {
  display: flex;
  align-items: center;
  background: var(--color-bg-input, #333333);
  border: 1px solid var(--color-border-input, #4a4a4a);
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.15s ease;
}

.cad-input-wrapper:focus-within {
  border-color: var(--color-accent, #4a9eff);
  box-shadow: 0 0 0 1px var(--color-accent, #4a9eff);
}

.cad-input.disabled .cad-input-wrapper {
  background: var(--color-bg-panel, #242424);
  cursor: not-allowed;
}

.cad-input-field {
  flex: 1;
  min-width: 0;
  padding: 6px 8px;
  background: transparent;
  border: none;
  color: var(--color-text-primary, #e0e0e0);
  font-size: 12px;
  font-family: inherit;
  outline: none;
}

.cad-input-field.has-prefix {
  padding-left: 4px;
}

.cad-input-field.has-suffix {
  padding-right: 4px;
}

.cad-input-field::placeholder {
  color: var(--color-text-muted, #707070);
}

.cad-input-field:disabled {
  cursor: not-allowed;
}

/* Number input: remove spinners */
.cad-input-field[type="number"]::-webkit-inner-spin-button,
.cad-input-field[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.cad-input-field[type="number"] {
  -moz-appearance: textfield;
}

.cad-input-prefix,
.cad-input-suffix {
  padding: 0 8px;
  font-size: 11px;
  color: var(--color-text-muted, #707070);
  background: var(--color-bg-panel, #242424);
  white-space: nowrap;
  line-height: 28px;
}

.cad-input-prefix {
  border-right: 1px solid var(--color-border-input, #4a4a4a);
}

.cad-input-suffix {
  border-left: 1px solid var(--color-border-input, #4a4a4a);
}
</style>
