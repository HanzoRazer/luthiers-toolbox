/**
 * useGuitarCAM - Composable for CAM toolpath generation
 *
 * Handles:
 * - CAM toolpath generation via API
 * - G-code post-processing
 * - G-code export with post-processor headers
 */

import { ref } from 'vue'
import { api } from '@/services/apiBase'
import type { GuitarDimensions } from './useGuitarDimensions'

export interface CamStats {
  length_mm: number
  area_mm2: number
  time_min: number
  time_s: number
  volume_mm3: number
  move_count: number
}

export interface CamParams {
  tool_d: number
  stepover: number
  strategy: string
}

export interface GcodeMove {
  code: string
  x?: number
  y?: number
  z?: number
  f?: number
}

export interface CamResults {
  stats: CamStats
  cam_params: CamParams
  moves: GcodeMove[]
}

export type PostProcessor = 'GRBL' | 'Mach3' | 'Mach4' | 'LinuxCNC' | 'PathPilot'

const POST_HEADERS: Record<PostProcessor, string[]> = {
  GRBL: ['G21', 'G90', 'G17', '(POST=GRBL;UNITS=mm)'],
  Mach3: ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=Mach3;UNITS=mm)'],
  Mach4: ['G21', 'G90', 'G17', 'G40', 'G49', 'G80', '(POST=Mach4;UNITS=mm)'],
  LinuxCNC: ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=LinuxCNC;UNITS=mm)'],
  PathPilot: ['G21', 'G90', 'G17', 'G40', 'G49', '(POST=PathPilot;UNITS=mm)'],
}

const POST_FOOTERS: Record<PostProcessor, string[]> = {
  GRBL: ['M30', '(End of program)'],
  Mach3: ['M30', '(End of program)'],
  Mach4: ['M30', '(End of program)'],
  LinuxCNC: ['M2', '(End of program)'],
  PathPilot: ['M30', '(End of program)'],
}

export function useGuitarCAM() {
  const isGenerating = ref(false)
  const camResults = ref<CamResults | null>(null)
  const selectedPost = ref<PostProcessor>('GRBL')

  // Generate CAM toolpath
  async function generateToolpath(
    dimensions: GuitarDimensions,
    guitarType: string
  ): Promise<{ success: boolean; error?: string }> {
    isGenerating.value = true
    camResults.value = null

    try {
      const response = await api('/api/guitar/design/parametric/to-cam', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dimensions,
          guitarType,
          resolution: 48,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`CAM planning failed: ${response.status} ${errorText}`)
      }

      const result = await response.json()
      camResults.value = result

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    } finally {
      isGenerating.value = false
    }
  }

  // Generate G-code with post-processor
  function generateGCode(moves: GcodeMove[], postId: PostProcessor): string {
    const lines: string[] = []

    // Add headers
    lines.push(...(POST_HEADERS[postId] || POST_HEADERS.GRBL))
    lines.push('')

    // Add moves
    moves.forEach((move) => {
      const parts: string[] = [move.code]
      if (move.x !== undefined) parts.push(`X${move.x.toFixed(4)}`)
      if (move.y !== undefined) parts.push(`Y${move.y.toFixed(4)}`)
      if (move.z !== undefined) parts.push(`Z${move.z.toFixed(4)}`)
      if (move.f !== undefined) parts.push(`F${move.f.toFixed(1)}`)
      lines.push(parts.join(' '))
    })

    lines.push('')

    // Add footers
    lines.push(...(POST_FOOTERS[postId] || POST_FOOTERS.GRBL))

    return lines.join('\n')
  }

  // Format moves for preview
  function formatMoves(moves: GcodeMove[], limit = 20): string {
    return moves
      .slice(0, limit)
      .map((move, i) => {
        const parts: string[] = [`N${i + 1}`, move.code]
        if (move.x !== undefined) parts.push(`X${move.x.toFixed(4)}`)
        if (move.y !== undefined) parts.push(`Y${move.y.toFixed(4)}`)
        if (move.z !== undefined) parts.push(`Z${move.z.toFixed(4)}`)
        if (move.f !== undefined) parts.push(`F${move.f.toFixed(1)}`)
        return parts.join(' ')
      })
      .join('\n')
  }

  // Download G-code file
  function downloadGCode(guitarType: string): boolean {
    if (!camResults.value) return false

    try {
      const gcode = generateGCode(camResults.value.moves, selectedPost.value)
      const blob = new Blob([gcode], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `guitar_body_${guitarType}_${selectedPost.value.toLowerCase()}.nc`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      return true
    } catch {
      return false
    }
  }

  // Clear results
  function clearResults() {
    camResults.value = null
  }

  return {
    // State
    isGenerating,
    camResults,
    selectedPost,

    // Methods
    generateToolpath,
    generateGCode,
    formatMoves,
    downloadGCode,
    clearResults,
  }
}
