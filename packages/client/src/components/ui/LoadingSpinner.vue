<script setup lang="ts">
/**
 * LoadingSpinner - Animated loading indicator
 *
 * Usage:
 *   <LoadingSpinner />
 *   <LoadingSpinner size="lg" label="Processing..." />
 */
defineProps<{
  size?: 'sm' | 'md' | 'lg'
  label?: string
}>()
</script>

<template>
  <div class="spinner-container" :class="`spinner--${size || 'md'}`" role="status">
    <svg class="spinner" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle
        class="spinner-track"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="3"
      />
      <path
        class="spinner-head"
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
      />
    </svg>
    <span v-if="label" class="spinner-label">{{ label }}</span>
    <span v-else class="sr-only">Loading...</span>
  </div>
</template>

<style scoped>
.spinner-container {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2, 0.5rem);
}

.spinner {
  animation: spin 1s linear infinite;
}

.spinner-track {
  opacity: 0.2;
}

.spinner-head {
  opacity: 1;
}

/* Sizes */
.spinner--sm .spinner {
  width: 1rem;
  height: 1rem;
}

.spinner--md .spinner {
  width: 1.5rem;
  height: 1.5rem;
}

.spinner--lg .spinner {
  width: 2rem;
  height: 2rem;
}

.spinner-label {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #6b7280);
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
  border-width: 0;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
  .spinner-head {
    animation: pulse 1.5s ease-in-out infinite;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
