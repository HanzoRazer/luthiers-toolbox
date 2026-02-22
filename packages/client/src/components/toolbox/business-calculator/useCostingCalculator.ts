/**
 * Composable for instrument costing calculations.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ============================================================================
// Types
// ============================================================================

export interface CostingData {
  wood: number
  hardware: number
  electronics: number
  finishing: number
  hourlyRate: number
  buildHours: number
  finishHours: number
  setupHours: number
}

export interface CostingCalculatorState {
  costing: Ref<CostingData>
  totalMaterials: ComputedRef<number>
  totalHours: ComputedRef<number>
  totalLabor: ComputedRef<number>
  overheadAllocation: ComputedRef<number>
  totalCost: ComputedRef<number>
}

// ============================================================================
// Composable
// ============================================================================

export function useCostingCalculator(
  monthlyOverhead: ComputedRef<number>
): CostingCalculatorState {
  const costing = ref<CostingData>({
    wood: 150,
    hardware: 120,
    electronics: 200,
    finishing: 75,
    hourlyRate: 50,
    buildHours: 40,
    finishHours: 20,
    setupHours: 3
  })

  const totalMaterials = computed(() =>
    costing.value.wood +
    costing.value.hardware +
    costing.value.electronics +
    costing.value.finishing
  )

  const totalHours = computed(() =>
    costing.value.buildHours +
    costing.value.finishHours +
    costing.value.setupHours
  )

  const totalLabor = computed(() =>
    totalHours.value * costing.value.hourlyRate
  )

  const overheadAllocation = computed(() =>
    monthlyOverhead.value / 4 // Assuming 4 instruments per month
  )

  const totalCost = computed(() =>
    totalMaterials.value + totalLabor.value + overheadAllocation.value
  )

  return {
    costing,
    totalMaterials,
    totalHours,
    totalLabor,
    overheadAllocation,
    totalCost
  }
}
