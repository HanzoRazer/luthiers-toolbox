/**
 * Composable for batch bracing operations.
 */
import { ref, type Ref } from 'vue'
import { batchBracing, type BraceProfileType } from '@/api/art-studio'
import type { BraceEntry, BatchResult } from './bracingTypes'

// ============================================================================
// Types
// ============================================================================

export interface BraceBatchState {
  braces: Ref<BraceEntry[]>
  batchName: Ref<string>
  batchResult: Ref<BatchResult | null>
  addBrace: (params: {
    profileType: BraceProfileType
    width: number
    height: number
    length: number
    density: number
  }) => void
  removeBrace: (id: number) => void
  updateBrace: (brace: BraceEntry) => void
  calculateBatch: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useBraceBatch(
  loading: Ref<boolean>,
  error: Ref<string | null>
): BraceBatchState {
  const braces = ref<BraceEntry[]>([])
  const batchName = ref('X-Brace Set')
  const batchResult = ref<BatchResult | null>(null)
  const nextBraceId = ref(1)

  function addBrace(params: {
    profileType: BraceProfileType
    width: number
    height: number
    length: number
    density: number
  }): void {
    const newBrace: BraceEntry = {
      id: nextBraceId.value++,
      name: `Brace ${braces.value.length + 1}`,
      profile_type: params.profileType,
      width_mm: params.width,
      height_mm: params.height,
      length_mm: params.length,
      density_kg_m3: params.density,
      x_mm: 0,
      y_mm: 0,
      angle_deg: 0
    }
    braces.value.push(newBrace)
  }

  function removeBrace(id: number): void {
    const idx = braces.value.findIndex((b) => b.id === id)
    if (idx >= 0) braces.value.splice(idx, 1)
  }

  function updateBrace(brace: BraceEntry): void {
    const idx = braces.value.findIndex((b) => b.id === brace.id)
    if (idx >= 0) {
      braces.value[idx] = { ...brace }
    }
  }

  async function calculateBatch(): Promise<void> {
    if (braces.value.length === 0) {
      error.value = 'Add at least one brace to calculate batch'
      return
    }

    loading.value = true
    error.value = null
    try {
      const result = await batchBracing({
        name: batchName.value,
        braces: braces.value.map((b) => ({
          profile_type: b.profile_type,
          width_mm: b.width_mm,
          height_mm: b.height_mm,
          length_mm: b.length_mm,
          density_kg_m3: b.density_kg_m3
        }))
      })

      // Update individual brace results
      result.braces.forEach((res, idx) => {
        if (braces.value[idx]) {
          braces.value[idx].result = res
        }
      })

      batchResult.value = {
        total_mass_grams: result.total_mass_grams,
        total_stiffness: result.total_stiffness
      }
    } catch (e: any) {
      error.value = e.message || 'Batch calculation failed'
    } finally {
      loading.value = false
    }
  }

  return {
    braces,
    batchName,
    batchResult,
    addBrace,
    removeBrace,
    updateBrace,
    calculateBatch
  }
}
