/**
 * DrillingLab hole management composable.
 */
import { useConfirm } from '@/composables/useConfirm'
import type { Ref } from 'vue'
import type { Hole, LinearPattern, CircularPattern, GridPattern } from './drillingLabTypes'

export interface DrillingHolesReturn {
  selectHole: (index: number) => void
  toggleHole: (index: number, enabled: boolean) => void
  removeHole: (index: number) => void
  clearAll: () => void | Promise<void>
  generateLinearPattern: () => void
  generateCircularPattern: () => void
  generateGridPattern: () => void
  importCsv: () => void
}

export function useDrillingHoles(
  holes: Ref<Hole[]>,
  selectedHole: Ref<number | null>,
  linearPattern: Ref<LinearPattern>,
  circularPattern: Ref<CircularPattern>,
  gridPattern: Ref<GridPattern>,
  csvInput: Ref<string>,
  updatePreview: () => void
): DrillingHolesReturn {
  function selectHole(index: number): void {
    selectedHole.value = index === selectedHole.value ? null : index
  }

  function toggleHole(index: number, enabled: boolean): void {
    holes.value[index].enabled = enabled
    updatePreview()
  }

  function removeHole(index: number): void {
    holes.value.splice(index, 1)
    if (selectedHole.value === index) {
      selectedHole.value = null
    }
    updatePreview()
  }

  const { confirm } = useConfirm()
  async function clearAll(): Promise<void> {
    const ok = holes.value.length === 0 || (await confirm('Clear all holes?'))
    if (!ok) return
    holes.value = []
    selectedHole.value = null
    updatePreview()
  }

  function generateLinearPattern(): void {
    holes.value = []
    const { direction, startX, startY, spacing, count } = linearPattern.value

    for (let i = 0; i < count; i++) {
      if (direction === 'x') {
        holes.value.push({
          x: startX + i * spacing,
          y: startY,
          enabled: true
        })
      } else {
        holes.value.push({
          x: startX,
          y: startY + i * spacing,
          enabled: true
        })
      }
    }

    updatePreview()
  }

  function generateCircularPattern(): void {
    holes.value = []
    const { centerX, centerY, radius, count, startAngle } = circularPattern.value

    for (let i = 0; i < count; i++) {
      const angle = (startAngle + (360 / count) * i) * (Math.PI / 180)
      holes.value.push({
        x: Math.round((centerX + radius * Math.cos(angle)) * 10) / 10,
        y: Math.round((centerY + radius * Math.sin(angle)) * 10) / 10,
        enabled: true
      })
    }

    updatePreview()
  }

  function generateGridPattern(): void {
    holes.value = []
    const { startX, startY, spacingX, spacingY, countX, countY } = gridPattern.value

    for (let row = 0; row < countY; row++) {
      for (let col = 0; col < countX; col++) {
        holes.value.push({
          x: startX + col * spacingX,
          y: startY + row * spacingY,
          enabled: true
        })
      }
    }

    updatePreview()
  }

  function importCsv(): void {
    holes.value = []
    const lines = csvInput.value.trim().split('\n')

    for (const line of lines) {
      const [xStr, yStr] = line.split(',').map((s) => s.trim())
      const x = parseFloat(xStr)
      const y = parseFloat(yStr)

      if (!isNaN(x) && !isNaN(y)) {
        holes.value.push({ x, y, enabled: true })
      }
    }

    updatePreview()
  }

  return {
    selectHole,
    toggleHole,
    removeHole,
    clearAll,
    generateLinearPattern,
    generateCircularPattern,
    generateGridPattern,
    importCsv
  }
}
