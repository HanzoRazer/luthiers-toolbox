/**
 * AudioAnalyzer pack loading composable.
 */
import type { Ref, ShallowRef } from 'vue'
import { loadNormalizedPack } from '@/evidence'
import type { NormalizedPack, SelectedPeak } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerPackReturn {
  loadZip: (f: File) => Promise<void>
  onPick: (ev: Event) => Promise<void>
  onDrop: (ev: DragEvent) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerPack(
  pack: ShallowRef<NormalizedPack | null>,
  err: Ref<string>,
  activePath: Ref<string>,
  kindFilter: Ref<string>,
  selectedPeak: Ref<SelectedPeak | null>,
  audioJumpError: Ref<string>,
  resetError: () => void,
  emitArtifactCreated: (type: string, confidence: number) => void,
  emitViewRendered: (view: string, schema: string) => void,
  emitAnalysisFailed: (error: string) => void
): AudioAnalyzerPackReturn {
  async function loadZip(f: File): Promise<void> {
    resetError()
    try {
      pack.value = await loadNormalizedPack(f)
      // Default preview: first CSV if present, else first file
      const firstCsv = pack.value.files.find((x) => x.kind.endsWith('_csv'))
      activePath.value = (firstCsv ?? pack.value.files[0])?.relpath ?? ''
      kindFilter.value = ''
      selectedPeak.value = null
      audioJumpError.value = ''

      // Agentic M1: emit artifact created events
      const hasWolfData = pack.value.files.some((x) => x.kind.includes('wolf'))
      const hasOdsData = pack.value.files.some((x) => x.kind.includes('ods'))
      if (hasWolfData) {
        emitArtifactCreated('wolf_candidates_v1', 0.75)
      }
      if (hasOdsData) {
        emitArtifactCreated('ods_snapshot_v1', 0.8)
      }
      // Emit view rendered to trigger FIRST_SIGNAL
      emitViewRendered('audio_analyzer', pack.value.schema_id)
    } catch (e: unknown) {
      pack.value = null
      activePath.value = ''
      err.value = e instanceof Error ? e.message : String(e)

      // Agentic M1: emit failure
      emitAnalysisFailed(err.value)
    }
  }

  async function onPick(ev: Event): Promise<void> {
    const input = ev.target as HTMLInputElement
    const f = input.files?.[0]
    if (f) await loadZip(f)
  }

  async function onDrop(ev: DragEvent): Promise<void> {
    const f = ev.dataTransfer?.files?.[0]
    if (f) await loadZip(f)
  }

  return {
    loadZip,
    onPick,
    onDrop
  }
}
