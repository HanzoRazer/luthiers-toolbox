import { useToast } from './useToast'

/**
 * Composable for clipboard operations and toast notifications.
 * Composes useToast internally to avoid duplicating timer/cleanup logic.
 */
export function useClipboardToast() {
  const { toast, showToast, clearToast } = useToast(2000)

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

  return {
    toast,
    showToast,
    copyText,
    cleanup: clearToast,
  }
}
