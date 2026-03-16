/**
 * StratocasterNeckGenerator actions composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import {
  generateStratNeck,
  getDefaultStratParams,
  getVintageStratParams,
  get24FretStratParams,
  exportStratNeckAsJSON,
  type StratNeckGeometry,
  type StratNeckParameters
} from '@/utils/strat_neck_generator'

// ============================================================================
// Types
// ============================================================================

export interface StratNeckActionsReturn {
  generateNeck: () => void
  loadDefaults: () => void
  loadVintagePreset: () => void
  load24FretPreset: () => void
  exportJSON: () => void
  exportDXF: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useStratNeckActions(
  form: StratNeckParameters,
  generatedGeometry: Ref<StratNeckGeometry | null>
): StratNeckActionsReturn {
  /**
   * Generate neck geometry from current parameters.
   */
  function generateNeck(): void {
    try {
      const geometry = generateStratNeck({ ...form })
      generatedGeometry.value = geometry
      alert('Stratocaster neck geometry generated successfully!')
    } catch (error) {
      console.error('Error generating Strat neck:', error)
      alert('Error generating neck. Check console for details.')
    }
  }

  /**
   * Load default modern Strat parameters.
   */
  function loadDefaults(): void {
    const defaults = getDefaultStratParams()
    Object.assign(form, defaults)
    generatedGeometry.value = null
  }

  /**
   * Load vintage (50s-60s) Strat parameters.
   */
  function loadVintagePreset(): void {
    const vintage = getVintageStratParams()
    Object.assign(form, vintage)
    generatedGeometry.value = null
  }

  /**
   * Load 24-fret extended range parameters.
   */
  function load24FretPreset(): void {
    const extended = get24FretStratParams()
    Object.assign(form, extended)
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

    const json = exportStratNeckAsJSON(generatedGeometry.value)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `stratocaster_neck_${form.profile_type}_${form.fret_count}fret.json`
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
        body: JSON.stringify({
          ...form,
          neck_type: 'stratocaster'
        })
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `stratocaster_neck_${form.profile_type}_${form.fret_count}fret.dxf`
      link.click()
      URL.revokeObjectURL(url)

      alert('DXF exported successfully!')
    } catch (error) {
      console.error('Error exporting DXF:', error)
      alert('Error exporting DXF. Check console for details.')
    }
  }

  return {
    generateNeck,
    loadDefaults,
    loadVintagePreset,
    load24FretPreset,
    exportJSON,
    exportDXF
  }
}
