/**
 * ArtStudioInlay types and constants.
 */
import type { InlayPatternType, InlayPresetInfo, InlayPreviewResponse, FretPositionResponse } from '@/api/art-studio'

export type { InlayPatternType, InlayPresetInfo, InlayPreviewResponse, FretPositionResponse }

/** Pattern type option for UI */
export interface PatternTypeOption {
  value: InlayPatternType
  label: string
  icon: string
}

/** All available pattern types */
export const PATTERN_TYPES: PatternTypeOption[] = [
  { value: 'dot', label: 'Dot', icon: '●' },
  { value: 'diamond', label: 'Diamond', icon: '◆' },
  { value: 'block', label: 'Block', icon: '■' },
  { value: 'trapezoid', label: 'Trapezoid', icon: '⬡' },
  { value: 'custom', label: 'Custom', icon: '✱' }
]

/** Standard fret positions for inlays */
export const STANDARD_FRETS = [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]

/** Default form values */
export const DEFAULT_SCALE_LENGTH = 647.7 // Fender scale
export const DEFAULT_FRETBOARD_WIDTH_NUT = 43.0
export const DEFAULT_FRETBOARD_WIDTH_BODY = 56.0
export const DEFAULT_NUM_FRETS = 24
export const DEFAULT_INLAY_SIZE = 6.0
export const DEFAULT_DOUBLE_SPACING = 8.0
export const DEFAULT_DXF_VERSION = 'R12'
export const DEFAULT_LAYER_PREFIX = 'INLAY'
