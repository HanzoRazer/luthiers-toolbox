/**
 * ArtStudioHeadstock notes composable.
 */
import type { Ref } from 'vue'
import { patchRiskNotes } from '@/api/camRisk'

export interface HeadstockNotesReturn {
  openNoteEditor: () => void
  cancelNoteEditor: () => void
  saveNote: () => Promise<void>
}

export function useHeadstockNotes(
  lastRiskReportId: Ref<string | null>,
  noteEditorVisible: Ref<boolean>,
  noteDraft: Ref<string>,
  noteSaving: Ref<boolean>,
  noteSaveError: Ref<string | null>
): HeadstockNotesReturn {
  function openNoteEditor(): void {
    if (!lastRiskReportId.value) return
    noteEditorVisible.value = true
    noteSaveError.value = null
  }

  function cancelNoteEditor(): void {
    noteEditorVisible.value = false
    noteSaveError.value = null
  }

  async function saveNote(): Promise<void> {
    if (!lastRiskReportId.value) return
    noteSaving.value = true
    noteSaveError.value = null
    try {
      await patchRiskNotes(lastRiskReportId.value, noteDraft.value || '')
      noteEditorVisible.value = false
    } catch (err: any) {
      console.error('Failed to save headstock note:', err)
      noteSaveError.value = err?.message || 'Failed to save note'
    } finally {
      noteSaving.value = false
    }
  }

  return {
    openNoteEditor,
    cancelNoteEditor,
    saveNote
  }
}
