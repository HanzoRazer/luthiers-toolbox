/**
 * CompareLab type definitions.
 */

// ============================================================================
// Diff Types
// ============================================================================

export interface DiffResult {
  baseline_id: string
  baseline_name: string
  summary?: { added: number; removed: number; matched: number }
  segments?: Array<{ status: string; length: number; path_index: number }>
  mode?: string
}

// ============================================================================
// Extension Types
// ============================================================================

export interface ExtensionMismatch {
  templateExt: string
  expectedExt: string
  hasConflict: boolean
}

// ============================================================================
// Template Types
// ============================================================================

export interface TemplateValidation {
  valid: boolean
  warnings?: string[]
}

// ============================================================================
// Preset Types
// ============================================================================

export interface PresetForm {
  name: string
  description: string
  tagsInput: string
  kind: 'export' | 'combo'
}

export interface PresetSaveMessage {
  type: 'success' | 'error'
  text: string
}

export interface ExportPreset {
  id: string
  name: string
  export_params?: {
    filename_template?: string
    format?: string
    neck_profile?: string
    neck_section?: string
  }
  [key: string]: any
}

// ============================================================================
// Storage Keys
// ============================================================================

export const STORAGE_KEYS = {
  GEOMETRY: 'toolbox.compare.currentGeometry',
  NECK_PROFILE: 'toolbox.compare.neckProfile',
  NECK_SECTION: 'toolbox.compare.neckSection',
  EXPORT_PREFIX: 'toolbox.compare.exportPrefix',
  PRESET_ID: 'comparelab.selectedPresetId',
  TEMPLATE: 'comparelab.filenameTemplate',
  FORMAT: 'comparelab.exportFormat'
} as const

// ============================================================================
// Export Types
// ============================================================================

export type ExportFormat = 'svg' | 'png' | 'csv'
