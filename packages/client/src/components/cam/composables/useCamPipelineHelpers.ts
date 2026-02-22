/**
 * CamPipeline helper functions composable.
 */
import type { Ref } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface CamPipelineHelpersReturn {
  onFileChange: (ev: Event) => void
  formatPayload: (payload: any) => string
  togglePayload: (idx: number) => void
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPipelineHelpers(
  file: Ref<File | null>,
  openPayloadIndex: Ref<number | null>
): CamPipelineHelpersReturn {
  /**
   * Handle file input change.
   */
  function onFileChange(ev: Event): void {
    const input = ev.target as HTMLInputElement
    const f = input.files?.[0]
    if (f) file.value = f
  }

  /**
   * Format payload for display.
   */
  function formatPayload(payload: any): string {
    try {
      return JSON.stringify(payload, null, 2)
    } catch {
      return String(payload)
    }
  }

  /**
   * Toggle payload visibility.
   */
  function togglePayload(idx: number): void {
    openPayloadIndex.value = openPayloadIndex.value === idx ? null : idx
  }

  return {
    onFileChange,
    formatPayload,
    togglePayload
  }
}
