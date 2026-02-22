/**
 * ArtStudioCanvas types and constants.
 */
import type { MLPoint } from '@/stores/useArtStudioEngine'

export type { MLPoint, MLPath } from '@/stores/useArtStudioEngine'

export interface CanvasColors {
  background: string
  grid: string
  gridMajor: string
  path: string
  pathFill: string
  toolpath: string
  fretboard: string
  fretSlot: string
  origin: string
}

export const COLORS: CanvasColors = {
  background: '#f8f9fa',
  grid: '#e9ecef',
  gridMajor: '#dee2e6',
  path: '#212529',
  pathFill: 'rgba(33, 37, 41, 0.05)',
  toolpath: '#0d6efd',
  fretboard: '#6c757d',
  fretSlot: '#dc3545',
  origin: '#198754'
}

export interface ViewState {
  zoom: number
  panX: number
  panY: number
}

export interface MouseState {
  isDragging: boolean
  lastX: number
  lastY: number
}
