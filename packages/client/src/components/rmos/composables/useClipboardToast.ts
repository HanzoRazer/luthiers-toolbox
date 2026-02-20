import { ref, onBeforeUnmount } from 'vue'

/**
 * Composable for clipboard operations and toast notifications
 */
export function useClipboardToast() {
  const toast = ref<string | null>(null)
  let toastTimer: number | null = null

  /**
   * Show a toast message for 2 seconds
   */
  function showToast(msg: string, _variant?: 'ok' | 'err') {
    toast.value = msg
    if (toastTimer) window.clearTimeout(toastTimer)
    toastTimer = window.setTimeout(() => {
      toast.value = null
    }, 2000)
  }

  /**
   * Copy text to clipboard with toast feedback
   */
  async function copyText(label: string, value: string) {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(value)
      } else {
        // Fallback for older browsers
        const ta = document.createElement('textarea')
        ta.value = value
        ta.style.position = 'fixed'
        ta.style.left = '-9999px'
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      }
      showToast(`Copied ${label}`)
    } catch {
      showToast('Copy failed')
    }
  }

  /**
   * Cleanup on unmount
   */
  function cleanup() {
    if (toastTimer) window.clearTimeout(toastTimer)
  }

  onBeforeUnmount(cleanup)

  return {
    toast,
    showToast,
    copyText,
    cleanup,
  }
}
