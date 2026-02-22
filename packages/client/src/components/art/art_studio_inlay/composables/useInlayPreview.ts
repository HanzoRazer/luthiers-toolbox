/**
 * ArtStudioInlay preview and export composable.
 */
import type { Ref } from 'vue'
import { previewInlay, exportInlayDXF, downloadBlob } from '@/api/art-studio'
import type { InlayPatternType, InlayPreviewResponse } from './artStudioInlayTypes'

export interface InlayPreviewReturn {
  refreshPreview: () => Promise<void>
  exportDXF: () => Promise<void>
}

export function useInlayPreview(
  loading: Ref<boolean>,
  error: Ref<string | null>,
  previewResult: Ref<InlayPreviewResponse | null>,
  // Form values
  patternType: Ref<InlayPatternType>,
  selectedFrets: Ref<number[]>,
  scaleLength: Ref<number>,
  fretboardWidthNut: Ref<number>,
  fretboardWidthBody: Ref<number>,
  numFrets: Ref<number>,
  inlaySize: Ref<number>,
  doubleAt12: Ref<boolean>,
  doubleSpacing: Ref<number>,
  dxfVersion: Ref<string>,
  layerPrefix: Ref<string>
): InlayPreviewReturn {
  /**
   * Build the common request payload.
   */
  function buildPayload() {
    return {
      pattern_type: patternType.value,
      fret_positions: selectedFrets.value,
      scale_length_mm: scaleLength.value,
      fretboard_width_nut_mm: fretboardWidthNut.value,
      fretboard_width_body_mm: fretboardWidthBody.value,
      num_frets: numFrets.value,
      inlay_size_mm: inlaySize.value,
      double_at_12: doubleAt12.value,
      double_spacing_mm: doubleSpacing.value
    }
  }

  /**
   * Refresh inlay preview.
   */
  async function refreshPreview(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      previewResult.value = await previewInlay(buildPayload())
    } catch (e: any) {
      error.value = e.message || 'Preview failed'
    } finally {
      loading.value = false
    }
  }

  /**
   * Export inlay pattern as DXF file.
   */
  async function exportDXF(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const blob = await exportInlayDXF({
        ...buildPayload(),
        dxf_version: dxfVersion.value,
        layer_prefix: layerPrefix.value
      })
      downloadBlob(
        blob,
        `inlay_${patternType.value}_${scaleLength.value.toFixed(0)}mm.dxf`
      )
    } catch (e: any) {
      error.value = e.message || 'Export failed'
    } finally {
      loading.value = false
    }
  }

  return {
    refreshPreview,
    exportDXF
  }
}
