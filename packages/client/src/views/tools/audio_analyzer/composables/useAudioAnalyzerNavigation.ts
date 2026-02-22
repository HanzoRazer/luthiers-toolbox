/**
 * AudioAnalyzer audio navigation composable.
 */
import type { Ref, ShallowRef } from 'vue'
import type { NormalizedPack, SelectedPeak } from './audioAnalyzerTypes'

// ============================================================================
// Types
// ============================================================================

export interface AudioAnalyzerNavigationReturn {
  jumpToPointAudio: () => void
}

// ============================================================================
// Helpers
// ============================================================================

function audioRelpathForPoint(pointId: string): string {
  // Contracted path for point audio in viewer_pack_v1
  return `audio/points/${pointId}.wav`
}

// ============================================================================
// Composable
// ============================================================================

export function useAudioAnalyzerNavigation(
  pack: ShallowRef<NormalizedPack | null>,
  selectedPeak: Ref<SelectedPeak | null>,
  activePath: Ref<string>,
  audioJumpError: Ref<string>
): AudioAnalyzerNavigationReturn {
  function jumpToPointAudio(): void {
    audioJumpError.value = ''
    if (!pack.value || !selectedPeak.value?.pointId) return
    const audioRel = audioRelpathForPoint(selectedPeak.value.pointId)
    const exists = pack.value.files.some((f) => f.relpath === audioRel)
    if (!exists) {
      audioJumpError.value = `Audio missing for point ${selectedPeak.value.pointId}: expected ${audioRel}`
      return
    }
    activePath.value = audioRel
  }

  return {
    jumpToPointAudio
  }
}
