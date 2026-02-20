/**
 * Composable for saw blade registry loading and selection.
 * Extracted from SawSlicePanel.vue
 */
import { ref, type Ref } from 'vue'
import { api } from '@/services/apiBase'

// ==========================================================================
// Types
// ==========================================================================

export interface SawBlade {
  blade_id: string
  vendor: string
  model_code: string
  diameter_mm: number
  kerf_mm: number
  teeth: number
}

export interface BladeRegistryState {
  /** Available blades from registry */
  blades: Ref<SawBlade[]>
  /** Currently selected blade ID */
  selectedBladeId: Ref<string>
  /** Full blade object for selected ID */
  selectedBlade: Ref<SawBlade | null>
  /** Load blades from API */
  loadBlades: () => Promise<void>
  /** Handle blade selection change */
  onBladeChange: () => void
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawBladeRegistry(
  onSelectionChange?: () => void
): BladeRegistryState {
  const blades = ref<SawBlade[]>([])
  const selectedBladeId = ref<string>('')
  const selectedBlade = ref<SawBlade | null>(null)

  async function loadBlades() {
    try {
      const response = await api('/api/saw/blades')
      blades.value = await response.json()
    } catch (err) {
      console.error('Failed to load blades:', err)
    }
  }

  function onBladeChange() {
    const blade = blades.value.find((b) => b.blade_id === selectedBladeId.value)
    selectedBlade.value = blade || null
    onSelectionChange?.()
  }

  return {
    blades,
    selectedBladeId,
    selectedBlade,
    loadBlades,
    onBladeChange,
  }
}
