<script setup lang="ts">
/**
 * GlobalErrorHandler - Catches unhandled errors and promise rejections
 *
 * Place this component at the app root to catch any unhandled errors.
 * Works with ErrorRecovery modal for consistent error display.
 *
 * Usage:
 *   <GlobalErrorHandler>
 *     <RouterView />
 *   </GlobalErrorHandler>
 */
import { ref, onMounted, onUnmounted, provide } from 'vue'
import ErrorRecovery from './ErrorRecovery.vue'
import NetworkStatusBanner from './NetworkStatusBanner.vue'
import type { ErrorInfo } from './ErrorRecovery.vue'
import { useGlobalRetryQueue } from '@/composables/useRetryQueue'

const props = defineProps<{
  /** Show network status banner */
  showNetworkStatus?: boolean
  /** Custom error transformer */
  errorTransformer?: (error: Error) => ErrorInfo
}>()

const currentError = ref<ErrorInfo | null>(null)
const showError = ref(false)

const retryQueue = useGlobalRetryQueue()

/**
 * Transform various error types to ErrorInfo
 */
function transformError(error: any): ErrorInfo {
  // Use custom transformer if provided
  if (props.errorTransformer) {
    return props.errorTransformer(error)
  }

  // Handle fetch/network errors
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return {
      code: 'NETWORK_ERROR',
      message: 'Unable to connect to the server',
      hint: 'Check your internet connection and try again',
    }
  }

  // Handle API errors with our standard format
  if (error.ok === false && error.error) {
    return {
      code: error.code,
      message: error.error,
      hint: error.hint,
    }
  }

  // Handle DOMException (e.g., AbortError)
  if (error instanceof DOMException) {
    if (error.name === 'AbortError') {
      return {
        code: 'REQUEST_CANCELLED',
        message: 'Request was cancelled',
        hint: 'The operation was interrupted. You can try again.',
      }
    }
    return {
      code: error.name,
      message: error.message,
    }
  }

  // Handle validation errors
  if (error.name === 'ValidationError' || error.type === 'validation') {
    return {
      code: 'VALIDATION_ERROR',
      message: error.message,
      hint: 'Please check your input and try again',
      details: JSON.stringify(error.errors || error.details, null, 2),
    }
  }

  // Default error format
  return {
    message: error.message || 'An unexpected error occurred',
    details: error.stack,
    hint: 'Please try again. If the problem persists, contact support.',
  }
}

/**
 * Global error handler
 */
function handleError(event: ErrorEvent) {
  // Ignore ResizeObserver errors (browser quirk)
  if (event.message.includes('ResizeObserver')) {
    return
  }

  currentError.value = transformError(event.error || new Error(event.message))
  showError.value = true
}

/**
 * Unhandled promise rejection handler
 */
function handleRejection(event: PromiseRejectionEvent) {
  // Prevent default browser error logging
  event.preventDefault()

  currentError.value = transformError(event.reason)
  showError.value = true
}

/**
 * Close error modal
 */
function handleClose() {
  showError.value = false
  currentError.value = null
}

/**
 * Retry last failed operation
 */
function handleRetry() {
  showError.value = false
  currentError.value = null
  // Attempt to process retry queue
  retryQueue.processQueue()
}

/**
 * Programmatically show an error
 */
function showErrorModal(error: ErrorInfo | Error | string) {
  if (typeof error === 'string') {
    currentError.value = { message: error }
  } else if (error instanceof Error) {
    currentError.value = transformError(error)
  } else {
    currentError.value = error
  }
  showError.value = true
}

// Provide error showing function to children
provide('showError', showErrorModal)

onMounted(() => {
  window.addEventListener('error', handleError)
  window.addEventListener('unhandledrejection', handleRejection)
})

onUnmounted(() => {
  window.removeEventListener('error', handleError)
  window.removeEventListener('unhandledrejection', handleRejection)
})

// Expose for parent access
defineExpose({
  showError: showErrorModal,
  hideError: handleClose,
})
</script>

<template>
  <!-- Network status banner -->
  <NetworkStatusBanner
    v-if="showNetworkStatus !== false"
    :queued-operations="retryQueue.queueSize.value"
  />

  <!-- Main content -->
  <slot />

  <!-- Error modal -->
  <ErrorRecovery
    :error="currentError"
    :show="showError"
    @close="handleClose"
    @retry="handleRetry"
  />
</template>
