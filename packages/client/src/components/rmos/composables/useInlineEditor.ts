/**
 * Composable for inline note editing in candidate list.
 * Handles edit state, start/cancel/save operations.
 */
import { ref, type Ref } from 'vue'
import { decideManufacturingCandidate, type ManufacturingCandidate, type RiskLevel } from '@/sdk/rmos/runs'

export interface InlineEditorState {
  editingId: Ref<string | null>
  editValue: Ref<string>
  saving: Ref<boolean>
  saveError: Ref<string | null>
  startEdit: (candidate: ManufacturingCandidate) => void
  cancelEdit: () => void
  saveEdit: (runId: string, candidate: ManufacturingCandidate, decidedBy: string | null) => Promise<void>
}

export function useInlineEditor(
  onUpdateCandidate: (id: string, res: any) => void,
  onUpdateRequestId: (requestId: string) => void
): InlineEditorState {
  const editingId = ref<string | null>(null)
  const editValue = ref<string>('')
  const saving = ref(false)
  const saveError = ref<string | null>(null)

  function startEdit(candidate: ManufacturingCandidate) {
    // Spine-locked: don't allow note editing until a decision exists
    if (candidate.decision == null) return
    editingId.value = candidate.candidate_id
    editValue.value = candidate.decision_note ?? ''
    saveError.value = null
  }

  function cancelEdit() {
    editingId.value = null
    editValue.value = ''
    saveError.value = null
  }

  async function saveEdit(runId: string, candidate: ManufacturingCandidate, decidedBy: string | null) {
    if (!runId) return
    if (candidate.decision == null) return

    saving.value = true
    saveError.value = null

    try {
      const res = await decideManufacturingCandidate(runId, candidate.candidate_id, {
        decision: candidate.decision as RiskLevel,
        note: editValue.value,
        decided_by: decidedBy,
      })

      if (res.requestId) {
        onUpdateRequestId(res.requestId)
      }

      onUpdateCandidate(candidate.candidate_id, res)
      cancelEdit()
    } catch (e: unknown) {
      saveError.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  return {
    editingId,
    editValue,
    saving,
    saveError,
    startEdit,
    cancelEdit,
    saveEdit,
  }
}
