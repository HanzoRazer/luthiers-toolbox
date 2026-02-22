/**
 * Composable for CAM promotion request functionality.
 */
import { useToastStore } from '@/stores/toastStore'

// ============================================================================
// Types
// ============================================================================

export interface CamPromotionState {
  promoteToCam: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPromotion(
  getSessionId: () => string | null,
  getApiBaseUrl: () => string,
  getCamProfileId: () => string
): CamPromotionState {
  const toast = useToastStore()

  async function promoteToCam(): Promise<void> {
    const sid = getSessionId()
    if (!sid) {
      toast.error('No session available')
      return
    }

    try {
      const base = getApiBaseUrl()
      const camProfileId = getCamProfileId() || undefined
      const params = new URLSearchParams()
      if (camProfileId) params.set('cam_profile_id', camProfileId)

      const url = `${base}/art/design-first-workflow/sessions/${encodeURIComponent(sid)}/promote_to_cam${params.toString() ? '?' + params.toString() : ''}`

      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}))
        toast.error(`Promotion failed: ${errData.detail || resp.statusText}`)
        return
      }

      const data = await resp.json()

      if (!data.ok) {
        toast.warning(`Promotion blocked: ${data.blocked_reason || 'unknown'}`)
        return
      }

      const requestId = data.request?.promotion_request_id
      toast.success(`CAM promotion request created: ${requestId?.slice(0, 8) || 'OK'}…`)
      console.log('[ArtStudio] CAM promotion request:', data.request)
    } catch (e: any) {
      toast.error(`Promotion error: ${e.message || e}`)
    }
  }

  return {
    promoteToCam
  }
}
