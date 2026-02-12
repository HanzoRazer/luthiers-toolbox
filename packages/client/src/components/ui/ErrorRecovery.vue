<script setup lang="ts">
/**
 * ErrorRecovery - Actionable error modal with recovery hints
 *
 * Replaces silent failures with clear:
 * - What happened
 * - Why it happened
 * - How to fix it
 */
import { computed } from 'vue'

export interface ErrorInfo {
  code?: string
  message: string
  hint?: string
  details?: string
  actions?: ErrorAction[]
}

export interface ErrorAction {
  label: string
  variant?: 'primary' | 'secondary' | 'danger'
  action: () => void | Promise<void>
}

const props = defineProps<{
  error: ErrorInfo | null
  title?: string
  show?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'retry'): void
}>()

const isVisible = computed(() => props.show !== false && props.error !== null)

const errorTitle = computed(() => props.title || 'Something went wrong')

const errorCode = computed(() => {
  if (props.error?.code) {
    return props.error.code
  }
  // Extract code from message if present
  const match = props.error?.message?.match(/^([A-Z]{2,}_\d{3}): /)
  return match ? match[1] : null
})

function handleAction(action: ErrorAction) {
  action.action()
}

function handleClose() {
  emit('close')
}

function handleRetry() {
  emit('retry')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isVisible" class="error-overlay" @click.self="handleClose">
        <div class="error-modal" role="alertdialog" aria-modal="true">
          <!-- Header -->
          <header class="error-header">
            <div class="error-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <h2 class="error-title">{{ errorTitle }}</h2>
            <button class="close-btn" @click="handleClose" aria-label="Close">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </header>

          <!-- Body -->
          <div class="error-body">
            <!-- What happened -->
            <div class="error-section">
              <h3 class="section-label">What happened</h3>
              <p class="error-message">
                <code v-if="errorCode" class="error-code">{{ errorCode }}</code>
                {{ error?.message }}
              </p>
            </div>

            <!-- Why (details) -->
            <div v-if="error?.details" class="error-section">
              <h3 class="section-label">Details</h3>
              <pre class="error-details">{{ error.details }}</pre>
            </div>

            <!-- How to fix -->
            <div v-if="error?.hint" class="error-section error-section--hint">
              <h3 class="section-label">How to fix</h3>
              <p class="error-hint">{{ error.hint }}</p>
            </div>
          </div>

          <!-- Actions -->
          <footer class="error-footer">
            <button class="btn btn--secondary" @click="handleClose">
              Dismiss
            </button>

            <div class="error-actions">
              <button
                v-for="action in error?.actions"
                :key="action.label"
                class="btn"
                :class="`btn--${action.variant || 'primary'}`"
                @click="handleAction(action)"
              >
                {{ action.label }}
              </button>

              <button
                v-if="!error?.actions?.length"
                class="btn btn--primary"
                @click="handleRetry"
              >
                Try Again
              </button>
            </div>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.error-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.error-modal {
  background: var(--color-surface, #ffffff);
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 480px;
  width: 100%;
  overflow: hidden;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
}

.error-icon {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: #dc2626;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.error-title {
  flex: 1;
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #991b1b;
}

.close-btn {
  background: none;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  color: #991b1b;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.close-btn:hover {
  opacity: 1;
}

.error-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.error-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #6b7280);
  margin: 0;
}

.error-message {
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--color-text, #1f2937);
  margin: 0;
}

.error-code {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
}

.error-details {
  font-family: monospace;
  font-size: 0.75rem;
  background: var(--color-surface-elevated, #f9fafb);
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0;
  color: var(--color-text-muted, #6b7280);
}

.error-section--hint {
  background: #eff6ff;
  margin: 0 -1.5rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #bfdbfe;
  border-bottom: 1px solid #bfdbfe;
}

.error-section--hint .section-label {
  color: #1d4ed8;
}

.error-hint {
  font-size: 0.875rem;
  color: #1e40af;
  margin: 0;
  line-height: 1.5;
}

.error-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--color-surface-elevated, #f9fafb);
  border-top: 1px solid var(--color-border, #e5e7eb);
}

.error-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn--primary {
  background: var(--color-primary, #3b82f6);
  color: white;
  border: none;
}

.btn--primary:hover {
  background: #2563eb;
}

.btn--secondary {
  background: transparent;
  color: var(--color-text-muted, #6b7280);
  border: 1px solid var(--color-border, #e5e7eb);
}

.btn--secondary:hover {
  background: var(--color-surface-elevated, #f3f4f6);
}

.btn--danger {
  background: #dc2626;
  color: white;
  border: none;
}

.btn--danger:hover {
  background: #b91c1c;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .error-modal,
.modal-leave-active .error-modal {
  transition: transform 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .error-modal,
.modal-leave-to .error-modal {
  transform: scale(0.95);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .error-modal {
    background: #1f2937;
  }

  .error-header {
    background: #450a0a;
    border-color: #7f1d1d;
  }

  .error-title {
    color: #fca5a5;
  }

  .close-btn {
    color: #fca5a5;
  }

  .error-code {
    background: #7f1d1d;
    color: #fecaca;
  }

  .error-details {
    background: #111827;
    color: #9ca3af;
  }

  .error-section--hint {
    background: #1e3a5f;
    border-color: #1d4ed8;
  }

  .error-section--hint .section-label {
    color: #93c5fd;
  }

  .error-hint {
    color: #bfdbfe;
  }

  .error-footer {
    background: #111827;
    border-color: #374151;
  }
}
</style>
