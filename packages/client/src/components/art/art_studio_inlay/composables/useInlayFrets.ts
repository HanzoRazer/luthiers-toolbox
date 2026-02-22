/**
 * ArtStudioInlay fret position and selection composable.
 */
import type { Ref } from 'vue'
import { getFretPositions } from '@/api/art-studio'
import type { FretPositionResponse } from './artStudioInlayTypes'
import { STANDARD_FRETS } from './artStudioInlayTypes'

export interface InlayFretsReturn {
  loadFretPositions: () => Promise<void>
  toggleFret: (fret: number) => void
  selectStandardFrets: () => void
  clearFrets: () => void
}

export function useInlayFrets(
  fretData: Ref<FretPositionResponse | null>,
  selectedFrets: Ref<number[]>,
  scaleLength: Ref<number>,
  numFrets: Ref<number>
): InlayFretsReturn {
  /**
   * Load fret position data from API.
   */
  async function loadFretPositions(): Promise<void> {
    try {
      fretData.value = await getFretPositions(scaleLength.value, numFrets.value)
    } catch (e: any) {
      console.warn('Failed to load fret positions:', e)
    }
  }

  /**
   * Toggle a fret in/out of selection.
   */
  function toggleFret(fret: number): void {
    const idx = selectedFrets.value.indexOf(fret)
    if (idx >= 0) {
      selectedFrets.value.splice(idx, 1)
    } else {
      selectedFrets.value.push(fret)
      selectedFrets.value.sort((a, b) => a - b)
    }
  }

  /**
   * Select all standard fret positions.
   */
  function selectStandardFrets(): void {
    selectedFrets.value = [...STANDARD_FRETS]
  }

  /**
   * Clear all selected frets.
   */
  function clearFrets(): void {
    selectedFrets.value = []
  }

  return {
    loadFretPositions,
    toggleFret,
    selectStandardFrets,
    clearFrets
  }
}
