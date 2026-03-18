/**
 * Composable for simple toast notifications.
 * Auto-dismisses after a configurable timeout.
 *
 * @deprecated Prefer useToastStore from '@/stores/toastStore' for a single app-wide toast system.
 * This composable is local-state only; will be migrated/removed in a future release.
 * See CRITICAL_SYSTEMS_REVIEW_2026-03-18.md (Usability — single toast system).
 */
import { ref, onBeforeUnmount, type Ref } from 'vue'

export interface ToastState {
  toast: Ref<string | null>
  showToast: (msg: string, variant?: 'ok' | 'err') => void
  clearToast: () => void
}

export function useToast(timeout = 2000): ToastState {
  const toast = ref<string | null>(null)
  let _toastTimer: number | null = null

  function showToast(msg: string, _variant?: 'ok' | 'err') {
    toast.value = msg
    if (_toastTimer) window.clearTimeout(_toastTimer)
    _toastTimer = window.setTimeout(() => {
      toast.value = null
    }, timeout)
  }

  function clearToast() {
    toast.value = null
    if (_toastTimer) {
      window.clearTimeout(_toastTimer)
      _toastTimer = null
    }
  }

  onBeforeUnmount(() => {
    if (_toastTimer) window.clearTimeout(_toastTimer)
  })

  return {
    toast,
    showToast,
    clearToast,
  }
}
