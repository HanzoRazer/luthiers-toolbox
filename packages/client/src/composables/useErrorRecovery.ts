/**
 * useErrorRecovery - Composable for standardized error handling
 *
 * Provides consistent error capture, display, and recovery across the app.
 */
import { ref, readonly } from 'vue'
import type { ErrorInfo, ErrorAction } from '@/components/ui/ErrorRecovery.vue'

export interface ApiError {
  ok: false
  error: string
  hint?: string
  code?: string
}

export interface UseErrorRecoveryOptions {
  defaultTitle?: string
  autoRetry?: boolean
  maxRetries?: number
}

export function useErrorRecovery(options: UseErrorRecoveryOptions = {}) {
  const error = ref<ErrorInfo | null>(null)
  const isErrorVisible = ref(false)
  const retryCount = ref(0)
  const lastOperation = ref<(() => Promise<any>) | null>(null)

  /**
   * Show error with recovery options
   */
  function showError(errorInfo: ErrorInfo | string | Error) {
    if (typeof errorInfo === 'string') {
      error.value = { message: errorInfo }
    } else if (errorInfo instanceof Error) {
      error.value = {
        message: errorInfo.message,
        details: errorInfo.stack,
      }
    } else {
      error.value = errorInfo
    }
    isErrorVisible.value = true
    retryCount.value = 0
  }

  /**
   * Parse API response error
   */
  function fromApiResponse(response: ApiError): ErrorInfo {
    return {
      code: response.code,
      message: response.error,
      hint: response.hint,
    }
  }

  /**
   * Dismiss error
   */
  function dismissError() {
    isErrorVisible.value = false
    error.value = null
  }

  /**
   * Retry last operation
   */
  async function retry() {
    if (!lastOperation.value) return

    const maxRetries = options.maxRetries ?? 3
    if (retryCount.value >= maxRetries) {
      showError({
        message: 'Maximum retry attempts reached',
        hint: 'Please try again later or contact support',
      })
      return
    }

    retryCount.value++
    dismissError()

    try {
      await lastOperation.value()
    } catch (e: any) {
      showError(e)
    }
  }

  /**
   * Wrap an async operation with error handling
   */
  async function withErrorHandling<T>(
    operation: () => Promise<T>,
    errorTransform?: (error: any) => ErrorInfo
  ): Promise<T | null> {
    lastOperation.value = operation

    try {
      const result = await operation()

      // Check for API error format
      if (typeof result === 'object' && result !== null && 'ok' in result) {
        const apiResult = result as { ok: boolean; error?: string; hint?: string }
        if (!apiResult.ok && apiResult.error) {
          showError({
            message: apiResult.error,
            hint: apiResult.hint,
          })
          return null
        }
      }

      return result
    } catch (e: any) {
      const errorInfo = errorTransform ? errorTransform(e) : {
        message: e.message || 'An unexpected error occurred',
        details: e.stack,
        hint: 'Check your network connection and try again',
      }
      showError(errorInfo)
      return null
    }
  }

  /**
   * Wrap fetch with error handling
   */
  async function fetchWithErrorHandling<T>(
    url: string,
    init?: RequestInit
  ): Promise<T | null> {
    return withErrorHandling(async () => {
      const response = await fetch(url, init)

      if (!response.ok) {
        const text = await response.text()
        let errorData: any
        try {
          errorData = JSON.parse(text)
        } catch {
          errorData = { error: text || `HTTP ${response.status}` }
        }

        throw {
          message: errorData.error || errorData.detail || `Request failed: ${response.status}`,
          hint: errorData.hint,
          code: errorData.code,
        }
      }

      return response.json()
    })
  }

  return {
    // State
    error: readonly(error),
    isErrorVisible: readonly(isErrorVisible),
    retryCount: readonly(retryCount),

    // Actions
    showError,
    dismissError,
    retry,
    withErrorHandling,
    fetchWithErrorHandling,
    fromApiResponse,
  }
}

/**
 * Common error codes and their user-friendly messages
 */
export const ERROR_MESSAGES: Record<string, { message: string; hint: string }> = {
  NETWORK_ERROR: {
    message: 'Unable to connect to the server',
    hint: 'Check your internet connection and try again',
  },
  AUTH_REQUIRED: {
    message: 'Authentication required',
    hint: 'Please log in to continue',
  },
  FORBIDDEN: {
    message: 'Access denied',
    hint: 'You do not have permission to perform this action',
  },
  NOT_FOUND: {
    message: 'Resource not found',
    hint: 'The requested item may have been deleted or moved',
  },
  VALIDATION_ERROR: {
    message: 'Invalid input',
    hint: 'Please check your input and try again',
  },
  RATE_LIMITED: {
    message: 'Too many requests',
    hint: 'Please wait a moment before trying again',
  },
  SERVER_ERROR: {
    message: 'Server error',
    hint: 'Our team has been notified. Please try again later.',
  },
}

/**
 * Get user-friendly error message for HTTP status
 */
export function getErrorForStatus(status: number): { message: string; hint: string } {
  switch (status) {
    case 400:
      return ERROR_MESSAGES.VALIDATION_ERROR
    case 401:
      return ERROR_MESSAGES.AUTH_REQUIRED
    case 403:
      return ERROR_MESSAGES.FORBIDDEN
    case 404:
      return ERROR_MESSAGES.NOT_FOUND
    case 429:
      return ERROR_MESSAGES.RATE_LIMITED
    default:
      if (status >= 500) {
        return ERROR_MESSAGES.SERVER_ERROR
      }
      return {
        message: `Request failed (${status})`,
        hint: 'Please try again or contact support',
      }
  }
}
