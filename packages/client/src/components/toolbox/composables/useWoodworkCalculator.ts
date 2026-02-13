/**
 * Composable for woodworking calculations.
 * Extracted from ScientificCalculator.vue
 */
import { ref, computed } from 'vue'

export interface BoardFeetInput {
  length: number    // inches
  width: number     // inches
  thickness: number // inches
  pricePerBF?: number
}

export interface WoodVolumeInput {
  length: number     // mm
  width: number      // mm
  thickness: number  // mm
  species: string
}

export interface MiterInput {
  rise: number
  run: number
}

// Wood species densities in g/cm³
export const WOOD_SPECIES: Record<string, { name: string; density: number }> = {
  spruce: { name: 'Spruce', density: 0.43 },
  cedar: { name: 'Western Red Cedar', density: 0.37 },
  mahogany: { name: 'Mahogany', density: 0.54 },
  maple: { name: 'Maple (Hard)', density: 0.71 },
  walnut: { name: 'Walnut', density: 0.64 },
  rosewood: { name: 'Rosewood', density: 0.85 },
  ebony: { name: 'Ebony', density: 1.12 },
  oak: { name: 'Oak', density: 0.75 },
  ash: { name: 'Ash', density: 0.67 },
  alder: { name: 'Alder', density: 0.45 },
  basswood: { name: 'Basswood', density: 0.42 },
  poplar: { name: 'Poplar', density: 0.43 }
}

/**
 * Calculate board feet.
 * BF = (length × width × thickness) / 144
 */
export function calculateBoardFeet(input: BoardFeetInput): number {
  const { length, width, thickness } = input
  return (length * width * thickness) / 144
}

/**
 * Calculate board cost.
 */
export function calculateBoardCost(input: BoardFeetInput): number {
  if (!input.pricePerBF) return 0
  return calculateBoardFeet(input) * input.pricePerBF
}

/**
 * Calculate wood volume in cm³ from mm dimensions.
 */
export function calculateVolumeCm3(input: WoodVolumeInput): number {
  const { length, width, thickness } = input
  // mm³ to cm³: divide by 1000
  return (length * width * thickness) / 1000
}

/**
 * Calculate wood weight in grams.
 */
export function calculateWoodWeight(input: WoodVolumeInput): number {
  const volumeCm3 = calculateVolumeCm3(input)
  const species = WOOD_SPECIES[input.species]
  const density = species?.density || 0.5
  return volumeCm3 * density
}

/**
 * Calculate miter angle from rise/run.
 */
export function calculateMiterAngle(input: MiterInput): number {
  const { rise, run } = input
  if (run === 0) return 0
  return Math.atan(rise / run) * (180 / Math.PI)
}

/**
 * Calculate complementary angle (for miter saw setting).
 */
export function calculateComplementaryAngle(input: MiterInput): number {
  return 90 - calculateMiterAngle(input)
}

export function useWoodworkCalculator() {
  // Board feet calculator
  const boardFeet = ref<BoardFeetInput>({
    length: 48,
    width: 6,
    thickness: 1,
    pricePerBF: 8.5
  })

  const boardFeetResult = computed(() => calculateBoardFeet(boardFeet.value))
  const boardCostResult = computed(() => calculateBoardCost(boardFeet.value))

  // Wood volume/weight calculator
  const woodVolume = ref<WoodVolumeInput>({
    length: 650,
    width: 200,
    thickness: 3,
    species: 'spruce'
  })

  const volumeResult = computed(() => calculateVolumeCm3(woodVolume.value))
  const weightResult = computed(() => calculateWoodWeight(woodVolume.value))
  const weightKg = computed(() => weightResult.value / 1000)

  // Miter angle calculator
  const miter = ref<MiterInput>({
    rise: 12,
    run: 100
  })

  const miterAngle = computed(() => calculateMiterAngle(miter.value))
  const complementaryAngle = computed(() => calculateComplementaryAngle(miter.value))

  // Reset functions
  function resetBoardFeet() {
    boardFeet.value = { length: 48, width: 6, thickness: 1, pricePerBF: 8.5 }
  }

  function resetWoodVolume() {
    woodVolume.value = { length: 650, width: 200, thickness: 3, species: 'spruce' }
  }

  function resetMiter() {
    miter.value = { rise: 12, run: 100 }
  }

  function resetAll() {
    resetBoardFeet()
    resetWoodVolume()
    resetMiter()
  }

  return {
    // Board feet
    boardFeet,
    boardFeetResult,
    boardCostResult,

    // Wood volume/weight
    woodVolume,
    volumeResult,
    weightResult,
    weightKg,

    // Miter
    miter,
    miterAngle,
    complementaryAngle,

    // Methods
    resetBoardFeet,
    resetWoodVolume,
    resetMiter,
    resetAll
  }
}
