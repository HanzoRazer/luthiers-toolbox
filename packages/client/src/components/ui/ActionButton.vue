<script setup lang="ts">
/**
 * ActionButton.vue - Button with loading and disabled states
 *
 * Reduces repetitive button patterns across god objects.
 * Supports primary, secondary, danger variants.
 */
defineOptions({ name: 'ActionButton' })

type Variant = 'primary' | 'secondary' | 'danger' | 'success'
type Size = 'sm' | 'md' | 'lg'

withDefaults(defineProps<{
  variant?: Variant
  size?: Size
  loading?: boolean
  disabled?: boolean
  loadingText?: string
}>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

function onClick(event: MouseEvent) {
  emit('click', event)
}
</script>

<template>
  <button
    class="action-btn"
    :class="[variant, size, { loading }]"
    :disabled="disabled || loading"
    @click="onClick"
  >
    <span v-if="loading" class="spinner" aria-hidden="true" />
    <span :class="{ 'sr-only': loading && loadingText }">
      <slot />
    </span>
    <span v-if="loading && loadingText" class="loading-text">
      {{ loadingText }}
    </span>
  </button>
</template>

<style scoped>
.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-weight: 500;
  border-radius: 0.375rem;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Sizes */
.action-btn.sm {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
}

.action-btn.md {
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
}

.action-btn.lg {
  font-size: 1rem;
  padding: 0.625rem 1.25rem;
}

/* Variants */
.action-btn.primary {
  background: #2563eb;
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.action-btn.secondary {
  background: white;
  color: #374151;
  border-color: #d1d5db;
}

.action-btn.secondary:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
}

.action-btn.danger {
  background: #dc2626;
  color: white;
}

.action-btn.danger:hover:not(:disabled) {
  background: #b91c1c;
}

.action-btn.success {
  background: #059669;
  color: white;
}

.action-btn.success:hover:not(:disabled) {
  background: #047857;
}

/* Loading state */
.spinner {
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
