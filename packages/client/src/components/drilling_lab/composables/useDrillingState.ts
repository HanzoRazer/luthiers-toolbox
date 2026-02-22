/**
 * DrillingLab state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type {
  Hole,
  DrillParams,
  LinearPattern,
  CircularPattern,
  GridPattern
} from './drillingLabTypes'
import {
  DEFAULT_PARAMS,
  DEFAULT_LINEAR_PATTERN,
  DEFAULT_CIRCULAR_PATTERN,
  DEFAULT_GRID_PATTERN
} from './drillingLabTypes'

export interface DrillingStateReturn {
  // Core state
  params: Ref<DrillParams>
  holes: Ref<Hole[]>
  selectedHole: Ref<number | null>
  patternType: Ref<string>

  // Pattern state
  linearPattern: Ref<LinearPattern>
  circularPattern: Ref<CircularPattern>
  gridPattern: Ref<GridPattern>

  // UI state
  csvInput: Ref<string>
  gcodePreview: Ref<string>
  gcodeCollapsed: Ref<boolean>

  // Canvas ref
  canvas: Ref<HTMLCanvasElement | null>

  // Computed
  enabledHoles: ComputedRef<Hole[]>
  totalDepth: ComputedRef<number>
  estimatedTime: ComputedRef<number>
}

export function useDrillingState(): DrillingStateReturn {
  // Core state
  const params = ref<DrillParams>({ ...DEFAULT_PARAMS })
  const holes = ref<Hole[]>([])
  const selectedHole = ref<number | null>(null)
  const patternType = ref('manual')

  // Pattern state
  const linearPattern = ref<LinearPattern>({ ...DEFAULT_LINEAR_PATTERN })
  const circularPattern = ref<CircularPattern>({ ...DEFAULT_CIRCULAR_PATTERN })
  const gridPattern = ref<GridPattern>({ ...DEFAULT_GRID_PATTERN })

  // UI state
  const csvInput = ref('')
  const gcodePreview = ref('(No holes defined)')
  const gcodeCollapsed = ref(false)

  // Canvas ref
  const canvas = ref<HTMLCanvasElement | null>(null)

  // Computed
  const enabledHoles = computed(() => holes.value.filter((h) => h.enabled))

  const totalDepth = computed(() => {
    return enabledHoles.value.length * Math.abs(params.value.depth)
  })

  const estimatedTime = computed(() => {
    const holesCount = enabledHoles.value.length
    if (holesCount === 0) return 0

    // Simple time estimation
    const rapidTime = holesCount * 2 // 2 seconds per hole for rapids
    const drillTime = totalDepth.value / (params.value.feedRate / 60) // depth / feed_per_second

    let peckTime = 0
    if (params.value.cycle === 'G83' && params.value.peckDepth > 0) {
      const pecksPerHole = Math.ceil(Math.abs(params.value.depth) / params.value.peckDepth)
      peckTime = holesCount * pecksPerHole * 1 // 1 second per peck retract
    }

    return (rapidTime + drillTime + peckTime) / 60 // Convert to minutes
  })

  return {
    params,
    holes,
    selectedHole,
    patternType,
    linearPattern,
    circularPattern,
    gridPattern,
    csvInput,
    gcodePreview,
    gcodeCollapsed,
    canvas,
    enabledHoles,
    totalDepth,
    estimatedTime
  }
}
