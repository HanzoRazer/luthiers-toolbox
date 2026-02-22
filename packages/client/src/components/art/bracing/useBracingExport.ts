/**
 * Composable for bracing DXF export.
 */
import { ref, type Ref } from 'vue'
import { exportBracingDXF, downloadBlob } from '@/api/art-studio'
import type { BraceEntry } from './bracingTypes'

// ============================================================================
// Types
// ============================================================================

export interface BracingExportState {
  dxfVersion: Ref<string>
  includeCenterlines: Ref<boolean>
  includeLabels: Ref<boolean>
  exportDXF: (braces: BraceEntry[], batchName: string) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useBracingExport(
  loading: Ref<boolean>,
  error: Ref<string | null>
): BracingExportState {
  const dxfVersion = ref('R12')
  const includeCenterlines = ref(true)
  const includeLabels = ref(true)

  async function exportDXF(braces: BraceEntry[], batchName: string): Promise<void> {
    if (braces.length === 0) {
      error.value = 'Add at least one brace to export'
      return
    }

    loading.value = true
    error.value = null
    try {
      const blob = await exportBracingDXF({
        braces: braces.map((b) => ({
          profile_type: b.profile_type,
          width_mm: b.width_mm,
          height_mm: b.height_mm,
          length_mm: b.length_mm,
          x_mm: b.x_mm,
          y_mm: b.y_mm,
          angle_deg: b.angle_deg
        })),
        dxf_version: dxfVersion.value,
        include_centerlines: includeCenterlines.value,
        include_labels: includeLabels.value
      })
      downloadBlob(blob, `bracing_${batchName.replace(/\s+/g, '_')}.dxf`)
    } catch (e: any) {
      error.value = e.message || 'Export failed'
    } finally {
      loading.value = false
    }
  }

  return {
    dxfVersion,
    includeCenterlines,
    includeLabels,
    exportDXF
  }
}
