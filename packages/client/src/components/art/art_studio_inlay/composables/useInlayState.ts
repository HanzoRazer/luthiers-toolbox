/**
 * ArtStudioInlay state composable.
 */
import { ref, computed, type Ref, type ComputedRef, type WritableComputedRef } from 'vue'
import { COMMON_SCALE_LENGTHS } from '@/api/art-studio'
import type { InlayPatternType, InlayPresetInfo, InlayPreviewResponse, FretPositionResponse } from './artStudioInlayTypes'
import {
  DEFAULT_SCALE_LENGTH,
  DEFAULT_FRETBOARD_WIDTH_NUT,
  DEFAULT_FRETBOARD_WIDTH_BODY,
  DEFAULT_NUM_FRETS,
  DEFAULT_INLAY_SIZE,
  DEFAULT_DOUBLE_SPACING,
  DEFAULT_DXF_VERSION,
  DEFAULT_LAYER_PREFIX,
  STANDARD_FRETS
} from './artStudioInlayTypes'

export interface InlayStateReturn {
  // Loading / error
  loading: Ref<boolean>
  error: Ref<string | null>

  // Preview / data
  previewResult: Ref<InlayPreviewResponse | null>
  fretData: Ref<FretPositionResponse | null>

  // Presets
  presets: Ref<InlayPresetInfo[]>
  selectedPreset: Ref<string | null>

  // Form inputs
  patternType: Ref<InlayPatternType>
  scaleLength: Ref<number>
  fretboardWidthNut: Ref<number>
  fretboardWidthBody: Ref<number>
  numFrets: Ref<number>
  inlaySize: Ref<number>
  doubleAt12: Ref<boolean>
  doubleSpacing: Ref<number>

  // Fret selection
  selectedFrets: Ref<number[]>

  // Export options
  dxfVersion: Ref<string>
  layerPrefix: Ref<string>

  // Computed
  selectedScalePreset: WritableComputedRef<string | null>
}

export function useInlayState(): InlayStateReturn {
  // Loading / error
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Preview / data
  const previewResult = ref<InlayPreviewResponse | null>(null)
  const fretData = ref<FretPositionResponse | null>(null)

  // Presets
  const presets = ref<InlayPresetInfo[]>([])
  const selectedPreset = ref<string | null>(null)

  // Form inputs
  const patternType = ref<InlayPatternType>('dot')
  const scaleLength = ref(DEFAULT_SCALE_LENGTH)
  const fretboardWidthNut = ref(DEFAULT_FRETBOARD_WIDTH_NUT)
  const fretboardWidthBody = ref(DEFAULT_FRETBOARD_WIDTH_BODY)
  const numFrets = ref(DEFAULT_NUM_FRETS)
  const inlaySize = ref(DEFAULT_INLAY_SIZE)
  const doubleAt12 = ref(true)
  const doubleSpacing = ref(DEFAULT_DOUBLE_SPACING)

  // Fret selection
  const selectedFrets = ref<number[]>([...STANDARD_FRETS])

  // Export options
  const dxfVersion = ref(DEFAULT_DXF_VERSION)
  const layerPrefix = ref(DEFAULT_LAYER_PREFIX)

  // Computed: scale preset selector
  const selectedScalePreset = computed<string | null>({
    get: () => {
      const found = COMMON_SCALE_LENGTHS.find(
        (s) => Math.abs(s.mm - scaleLength.value) < 0.1
      )
      return found?.name || null
    },
    set: (name: string | null) => {
      const found = COMMON_SCALE_LENGTHS.find((s) => s.name === name)
      if (found) scaleLength.value = found.mm
    }
  })

  return {
    loading,
    error,
    previewResult,
    fretData,
    presets,
    selectedPreset,
    patternType,
    scaleLength,
    fretboardWidthNut,
    fretboardWidthBody,
    numFrets,
    inlaySize,
    doubleAt12,
    doubleSpacing,
    selectedFrets,
    dxfVersion,
    layerPrefix,
    selectedScalePreset
  }
}
