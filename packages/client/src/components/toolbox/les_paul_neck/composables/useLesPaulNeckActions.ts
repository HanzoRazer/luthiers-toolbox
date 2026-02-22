/**
 * LesPaulNeckGenerator actions composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import {
  generateLesPaulNeck,
  getDefaultLesPaulParams,
  exportNeckAsJSON,
  type NeckGeometry,
  type NeckParameters
} from '../../../../utils/neck_generator'

// ============================================================================
// Types
// ============================================================================

export interface LesPaulNeckActionsReturn {
  generateNeck: () => void
  loadDefaults: () => void
  exportJSON: () => void
  exportDXF: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useLesPaulNeckActions(
  form: NeckParameters,
  generatedGeometry: Ref<NeckGeometry | null>
): LesPaulNeckActionsReturn {
  /**
   * Generate neck geometry from current parameters.
   */
  function generateNeck(): void {
    try {
      const geometry = generateLesPaulNeck({ ...form })
      generatedGeometry.value = geometry
      alert('✅ Les Paul neck geometry generated successfully!')
    } catch (error) {
      console.error('Error generating neck:', error)
      alert('❌ Error generating neck. Check console for details.')
    }
  }

  /**
   * Load default parameters.
   */
  function loadDefaults(): void {
    const defaults = getDefaultLesPaulParams()
    Object.assign(form, defaults)
    generatedGeometry.value = null
  }

  /**
   * Export geometry as JSON file.
   */
  function exportJSON(): void {
    if (!generatedGeometry.value) {
      alert('Please generate neck geometry first')
      return
    }

    const json = exportNeckAsJSON(generatedGeometry.value)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'les_paul_neck_geometry.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  /**
   * Export geometry as DXF file via API.
   */
  async function exportDXF(): Promise<void> {
    if (!generatedGeometry.value) {
      alert('Please generate neck geometry first')
      return
    }

    try {
      const response = await api('/api/neck/export_dxf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ...form })
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `les_paul_neck_${form.scale_length}${(form as any).units || 'in'}.dxf`
      link.click()
      URL.revokeObjectURL(url)

      alert('✅ DXF exported successfully!')
    } catch (error) {
      console.error('Error exporting DXF:', error)
      alert('❌ Error exporting DXF. Check console for details.')
    }
  }

  return {
    generateNeck,
    loadDefaults,
    exportJSON,
    exportDXF
  }
}
