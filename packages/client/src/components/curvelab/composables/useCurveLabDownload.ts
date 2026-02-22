/**
 * CurveLab download utilities composable.
 */
import type { Ref } from 'vue'
import type { CurvePreflightResponse, ValidationReport } from './curveLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CurveLabDownloadReturn {
  downloadInlineJson: () => void
  downloadFileJson: () => void
  downloadFixedDxf: () => void
}

// ============================================================================
// Helpers
// ============================================================================

function base64ToBlob(base64: string, mime: string): Blob {
  const byteCharacters = atob(base64)
  const bytes = new Uint8Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i += 1) {
    bytes[i] = byteCharacters.charCodeAt(i)
  }
  return new Blob([bytes], { type: mime })
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

// ============================================================================
// Composable
// ============================================================================

export function useCurveLabDownload(
  filename: string,
  inlineResponse: Ref<CurvePreflightResponse | null>,
  fileResponse: Ref<ValidationReport | null>,
  fixedDownload: Ref<string | null>
): CurveLabDownloadReturn {
  function downloadInlineJson(): void {
    if (!inlineResponse.value) return
    const blob = new Blob([JSON.stringify(inlineResponse.value, null, 2)], {
      type: 'application/json'
    })
    triggerDownload(blob, 'curvelab_curve_report.json')
  }

  function downloadFileJson(): void {
    if (!fileResponse.value) return
    const blob = new Blob([JSON.stringify(fileResponse.value, null, 2)], {
      type: 'application/json'
    })
    triggerDownload(blob, 'curvelab_dxf_report.json')
  }

  function downloadFixedDxf(): void {
    if (!fixedDownload.value) return
    const blob = base64ToBlob(fixedDownload.value, 'application/dxf')
    triggerDownload(blob, `curvelab_fixed_${filename}`)
  }

  return {
    downloadInlineJson,
    downloadFileJson,
    downloadFixedDxf
  }
}
