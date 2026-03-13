<script setup lang="ts">
/**
 * ErrorBoundary - Catches and displays component errors gracefully
 *
 * Wraps child components and catches Vue errors, preventing full app crashes.
 * Shows a recovery UI when an error occurs.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <ComponentThatMightFail />
 *   </ErrorBoundary>
 */
import { ref, onErrorCaptured } from 'vue'

const props = defineProps<{
  /** Custom error title */
  title?: string
  /** Show technical details in dev mode */
  showDetails?: boolean
  /** Fallback message when slot content fails */
  fallbackMessage?: string
}>()

const emit = defineEmits<{
  (e: 'error', error: Error, info: string): void
}>()

const hasError = ref(false)
const errorMessage = ref('')
const errorStack = ref('')
const errorInfo = ref('')

// Capture errors from child components
onErrorCaptured((error: Error, instance, info) => {
  hasError.value = true
  errorMessage.value = error.message
  errorStack.value = error.stack || ''
  errorInfo.value = info

  // Emit for parent handling
  emit('error', error, info)

  // Return false to prevent error from propagating
  return false
})

function handleRetry() {
  // Reset error state to re-render children
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
  errorInfo.value = ''
}

const isDev = import.meta.env.DEV
const showTechnicalDetails = props.showDetails ?? isDev
</script>

<template>
  <slot v-if="!hasError" />

  <div
    v-else
    class="error-boundary"
    role="alert"
  >
    <div class="error-boundary__content">
      <div class="error-boundary__icon">
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>

      <h3 class="error-boundary__title">
        {{ title || 'Something went wrong' }}
      </h3>

      <p class="error-boundary__message">
        {{ fallbackMessage || 'This section encountered an error and could not be displayed.' }}
      </p>

      <div
        v-if="showTechnicalDetails && errorMessage"
        class="error-boundary__details"
      >
        <p class="error-boundary__error-msg">
          {{ errorMessage }}
        </p>
        <p
          v-if="errorInfo"
          class="error-boundary__info"
        >
          Component: {{ errorInfo }}
        </p>
        <details
          v-if="errorStack"
          class="error-boundary__stack"
        >
          <summary>Stack trace</summary>
          <pre>{{ errorStack }}</pre>
        </details>
      </div>

      <div class="error-boundary__actions">
        <button
          class="error-boundary__btn error-boundary__btn--primary"
          @click="handleRetry"
        >
          Try Again
        </button>
        <button
          class="error-boundary__btn error-boundary__btn--secondary"
          @click="$router?.go(0)"
        >
          Reload Page
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.error-boundary {
  padding: 2rem;
  background: var(--color-surface-elevated, #f9fafb);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  text-align: center;
}

.error-boundary__content {
  max-width: 400px;
  margin: 0 auto;
}

.error-boundary__icon {
  color: #f59e0b;
  margin-bottom: 1rem;
}

.error-boundary__title {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text, #1f2937);
}

.error-boundary__message {
  margin: 0 0 1.5rem;
  color: var(--color-text-muted, #6b7280);
  font-size: 0.9375rem;
}

.error-boundary__details {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #fef3c7;
  border-radius: 6px;
  text-align: left;
}

.error-boundary__error-msg {
  margin: 0 0 0.5rem;
  font-family: monospace;
  font-size: 0.8125rem;
  color: #92400e;
  word-break: break-word;
}

.error-boundary__info {
  margin: 0;
  font-size: 0.75rem;
  color: #b45309;
}

.error-boundary__stack {
  margin-top: 0.75rem;
}

.error-boundary__stack summary {
  cursor: pointer;
  font-size: 0.75rem;
  color: #92400e;
}

.error-boundary__stack pre {
  margin: 0.5rem 0 0;
  padding: 0.5rem;
  background: #fffbeb;
  border-radius: 4px;
  font-size: 0.6875rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-boundary__actions {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

.error-boundary__btn {
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.error-boundary__btn--primary {
  background: var(--color-primary, #3b82f6);
  color: white;
  border: none;
}

.error-boundary__btn--primary:hover {
  background: #2563eb;
}

.error-boundary__btn--secondary {
  background: transparent;
  color: var(--color-text-muted, #6b7280);
  border: 1px solid var(--color-border, #e5e7eb);
}

.error-boundary__btn--secondary:hover {
  background: var(--color-surface, #ffffff);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .error-boundary {
    background: #1f2937;
    border-color: #374151;
  }

  .error-boundary__details {
    background: #78350f;
  }

  .error-boundary__error-msg {
    color: #fde68a;
  }

  .error-boundary__info {
    color: #fcd34d;
  }

  .error-boundary__stack summary {
    color: #fde68a;
  }

  .error-boundary__stack pre {
    background: #451a03;
    color: #fef3c7;
  }
}
</style>
