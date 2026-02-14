/**
 * Generic composable for material / geometry calculations.
 * Provides board-feet, volume, weight-by-density, and miter-angle helpers.
 *
 * Extracted & genericized from useWoodworkCalculator (Toolbox domain).
 */
import { ref, computed } from 'vue'

// ---- Public types ----

export interface BoardFeetInput {
  length: number    // inches
  width: number     // inches
  thickness: number // inches
  pricePerBF?: number
}

export interface VolumeInput {
  length: number     // mm
  width: number      // mm
  thickness: number  // mm
  materialKey: string
}

export interface AngleInput {
  rise: number
  run: number
}

export interface MaterialSpec {
  name: string
  /** Density in g/cm³. */
  density: number
}

// ---- Pure helpers ----

/** Board-feet = (L × W × T) / 144  (imperial inches). */
export function calculateBoardFeet(input: BoardFeetInput): number {
  return (input.length * input.width * input.thickness) / 144
}

/** Cost = board-feet × price per BF. */
export function calculateCost(input: BoardFeetInput): number {
  if (!input.pricePerBF) return 0
  return calculateBoardFeet(input) * input.pricePerBF
}

/** Volume in cm³ from mm dimensions (mm³ ÷ 1000). */
export function calculateVolumeCm3(input: VolumeInput): number {
  return (input.length * input.width * input.thickness) / 1000
}

/** Weight in grams from volume × density. */
export function calculateWeight(
  input: VolumeInput,
  materials: Record<string, MaterialSpec>,
): number {
  const vol = calculateVolumeCm3(input)
  const mat = materials[input.materialKey]
  return vol * (mat?.density ?? 0.5)
}

/** Miter angle (degrees) from rise / run. */
export function calculateAngle(input: AngleInput): number {
  if (input.run === 0) return 0
  return Math.atan(input.rise / input.run) * (180 / Math.PI)
}

/** Complementary angle (90° − miter). */
export function calculateComplementaryAngle(input: AngleInput): number {
  return 90 - calculateAngle(input)
}

// ---- Composable ----

export function useMaterialCalculator(
  materials: Record<string, MaterialSpec> = {},
) {
  // Board-feet calculator
  const boardFeet = ref<BoardFeetInput>({
    length: 48,
    width: 6,
    thickness: 1,
    pricePerBF: 8.5,
  })

  const boardFeetResult = computed(() => calculateBoardFeet(boardFeet.value))
  const boardCostResult = computed(() => calculateCost(boardFeet.value))

  // Volume / weight calculator
  const volume = ref<VolumeInput>({
    length: 500,
    width: 200,
    thickness: 10,
    materialKey: Object.keys(materials)[0] ?? '',
  })

  const volumeResult = computed(() => calculateVolumeCm3(volume.value))
  const weightResult = computed(() => calculateWeight(volume.value, materials))
  const weightKg = computed(() => weightResult.value / 1000)

  // Angle calculator
  const angle = ref<AngleInput>({ rise: 12, run: 100 })
  const miterAngle = computed(() => calculateAngle(angle.value))
  const complementaryAngle = computed(() => calculateComplementaryAngle(angle.value))

  // --- Resets ---

  function resetBoardFeet() {
    boardFeet.value = { length: 48, width: 6, thickness: 1, pricePerBF: 8.5 }
  }

  function resetVolume() {
    volume.value = {
      length: 500,
      width: 200,
      thickness: 10,
      materialKey: Object.keys(materials)[0] ?? '',
    }
  }

  function resetAngle() {
    angle.value = { rise: 12, run: 100 }
  }

  function resetAll() {
    resetBoardFeet()
    resetVolume()
    resetAngle()
  }

  return {
    boardFeet,
    boardFeetResult,
    boardCostResult,
    volume,
    volumeResult,
    weightResult,
    weightKg,
    angle,
    miterAngle,
    complementaryAngle,
    resetBoardFeet,
    resetVolume,
    resetAngle,
    resetAll,
  }
}
