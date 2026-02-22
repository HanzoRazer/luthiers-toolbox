/**
 * Composable for design-first workflow state transitions.
 */
import { computed, type ComputedRef } from 'vue'
import { useArtDesignFirstWorkflowStore } from '@/stores/artDesignFirstWorkflowStore'
import { useToastStore } from '@/stores/toastStore'

// ============================================================================
// Types
// ============================================================================

export interface WorkflowActionsState {
  // Computed state from store
  session: ComputedRef<any>
  state: ComputedRef<string | null>
  busy: ComputedRef<boolean>
  err: ComputedRef<string | null>
  hasSession: ComputedRef<boolean>
  canIntent: ComputedRef<boolean>
  lastIntent: ComputedRef<any>
  sessionId: ComputedRef<string | null>

  // Actions
  ensure: () => Promise<void>
  toReview: () => Promise<void>
  approve: () => Promise<void>
  reject: () => Promise<void>
  reopen: () => Promise<void>
  intent: () => Promise<void>
  clearIntent: () => void
  hydrateFromLocalStorage: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useWorkflowActions(): WorkflowActionsState {
  const wf = useArtDesignFirstWorkflowStore()
  const toast = useToastStore()

  // Computed state from store
  const session = computed(() => wf.session)
  const state = computed(() => wf.stateName)
  const busy = computed(() => wf.loading)
  const err = computed(() => wf.error)
  const hasSession = computed(() => wf.hasSession)
  const canIntent = computed(() => wf.canRequestIntent)
  const lastIntent = computed(() => wf.lastPromotionIntent)
  const sessionId = computed(() => wf.sessionId)

  async function ensure(): Promise<void> {
    if (wf.hasSession) {
      wf.clearSession()
    }
    await wf.ensureSessionDesignFirst()
  }

  async function toReview(): Promise<void> {
    if (!wf.hasSession) {
      await wf.ensureSessionDesignFirst()
    }
    await wf.transition('in_review')
  }

  async function approve(): Promise<void> {
    await wf.transition('approved')
  }

  async function reject(): Promise<void> {
    await wf.transition('rejected', 'Design needs revision')
  }

  async function reopen(): Promise<void> {
    await wf.transition('draft')
  }

  async function intent(): Promise<void> {
    const payload = await wf.requestPromotionIntent()
    if (payload) {
      toast.info('Intent payload ready. Use Log Viewer / CAM lane to consume.')
      console.log('[ArtStudio] CAM handoff intent:', payload)
    }
  }

  function clearIntent(): void {
    wf.clearSession()
    toast.info('Session cleared')
  }

  function hydrateFromLocalStorage(): void {
    wf.hydrateFromLocalStorage()
  }

  return {
    session,
    state,
    busy,
    err,
    hasSession,
    canIntent,
    lastIntent,
    sessionId,
    ensure,
    toReview,
    approve,
    reject,
    reopen,
    intent,
    clearIntent,
    hydrateFromLocalStorage
  }
}
