/**
 * Composable for contour path generation and SVG preview.
 * Extracted from SawContourPanel.vue
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'

// ==========================================================================
// Types
// ==========================================================================

export type ContourType = 'arc' | 'circle' | 'rosette'

export interface ArcParams {
  centerX: number
  centerY: number
  radius: number
  startAngle: number
  endAngle: number
}

export interface CircleParams {
  centerX: number
  centerY: number
  radius: number
}

export interface RosetteParams {
  centerX: number
  centerY: number
  outerRadius: number
  innerRadius: number
  petalCount: number
}

export interface ContourPathState {
  /** Current contour type */
  contourType: Ref<ContourType>
  /** Center X coordinate */
  centerX: Ref<number>
  /** Center Y coordinate */
  centerY: Ref<number>
  /** Radius (for arc/circle) */
  radius: Ref<number>
  /** Start angle in degrees (for arc) */
  startAngle: Ref<number>
  /** End angle in degrees (for arc) */
  endAngle: Ref<number>
  /** Outer radius (for rosette) */
  outerRadius: Ref<number>
  /** Inner radius (for rosette) */
  innerRadius: Ref<number>
  /** Number of petals (for rosette) */
  petalCount: Ref<number>
  /** Generated SVG path string */
  contourPath: Ref<string>
  /** Computed path statistics */
  pathStats: ComputedRef<{ length_mm: number }>
  /** SVG viewBox string */
  svgViewBox: ComputedRef<string>
  /** Update the contour path based on current params */
  updateContourPath: () => void
  /** Get minimum radius for validation */
  getMinRadius: () => number
}

// ==========================================================================
// Composable
// ==========================================================================

export function useSawContourPath(): ContourPathState {
  // State
  const contourType = ref<ContourType>('arc')
  const centerX = ref(100)
  const centerY = ref(100)
  const radius = ref(50)
  const startAngle = ref(0)
  const endAngle = ref(180)
  const outerRadius = ref(80)
  const innerRadius = ref(40)
  const petalCount = ref(6)
  const contourPath = ref('')

  // ==========================================================================
  // Computed
  // ==========================================================================

  const pathStats = computed(() => {
    let length = 0

    if (contourType.value === 'arc') {
      const angleRad = ((endAngle.value - startAngle.value) * Math.PI) / 180
      length = radius.value * Math.abs(angleRad)
    } else if (contourType.value === 'circle') {
      length = 2 * Math.PI * radius.value
    } else if (contourType.value === 'rosette') {
      // Approximate rosette length
      const avgRadius = (outerRadius.value + innerRadius.value) / 2
      length = 2 * Math.PI * avgRadius * petalCount.value
    }

    return { length_mm: length }
  })

  const svgViewBox = computed(() => {
    const maxRadius = contourType.value === 'rosette' ? outerRadius.value : radius.value
    const padding = 40
    const minX = centerX.value - maxRadius - padding
    const minY = centerY.value - maxRadius - padding
    const width = (maxRadius + padding) * 2
    const height = (maxRadius + padding) * 2
    return `${minX} ${minY} ${width} ${height}`
  })

  // ==========================================================================
  // Methods
  // ==========================================================================

  function updateContourPath() {
    if (contourType.value === 'arc') {
      contourPath.value = generateArcPath()
    } else if (contourType.value === 'circle') {
      contourPath.value = generateCirclePath()
    } else if (contourType.value === 'rosette') {
      contourPath.value = generateRosettePath()
    }
  }

  function generateArcPath(): string {
    const startRad = (startAngle.value * Math.PI) / 180
    const endRad = (endAngle.value * Math.PI) / 180

    const x1 = centerX.value + radius.value * Math.cos(startRad)
    const y1 = centerY.value + radius.value * Math.sin(startRad)
    const x2 = centerX.value + radius.value * Math.cos(endRad)
    const y2 = centerY.value + radius.value * Math.sin(endRad)

    const largeArc = Math.abs(endAngle.value - startAngle.value) > 180 ? 1 : 0

    return `M ${x1} ${y1} A ${radius.value} ${radius.value} 0 ${largeArc} 1 ${x2} ${y2}`
  }

  function generateCirclePath(): string {
    const x1 = centerX.value + radius.value
    const y1 = centerY.value
    const x2 = centerX.value - radius.value
    const y2 = centerY.value

    return `M ${x1} ${y1} A ${radius.value} ${radius.value} 0 1 1 ${x2} ${y2} A ${radius.value} ${radius.value} 0 1 1 ${x1} ${y1}`
  }

  function generateRosettePath(): string {
    const points: { x: number; y: number }[] = []
    const angleStep = (2 * Math.PI) / (petalCount.value * 2)

    for (let i = 0; i <= petalCount.value * 2; i++) {
      const angle = i * angleStep
      const r = i % 2 === 0 ? outerRadius.value : innerRadius.value
      const x = centerX.value + r * Math.cos(angle)
      const y = centerY.value + r * Math.sin(angle)
      points.push({ x, y })
    }

    return points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ') + ' Z'
  }

  function getMinRadius(): number {
    return contourType.value === 'rosette' ? innerRadius.value : radius.value
  }

  return {
    contourType,
    centerX,
    centerY,
    radius,
    startAngle,
    endAngle,
    outerRadius,
    innerRadius,
    petalCount,
    contourPath,
    pathStats,
    svgViewBox,
    updateContourPath,
    getMinRadius,
  }
}
