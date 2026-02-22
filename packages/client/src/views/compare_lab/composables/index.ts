/**
 * CompareLab composables barrel export.
 */

// Types
export type {
  DiffResult,
  ExtensionMismatch,
  TemplateValidation,
  PresetForm,
  PresetSaveMessage,
  ExportPreset,
  ExportFormat
} from './compareLabTypes'
export { STORAGE_KEYS } from './compareLabTypes'

// State
export { useCompareLabState } from './useCompareLabState'
export type { CompareLabStateReturn } from './useCompareLabState'

// Storage
export { useCompareLabStorage } from './useCompareLabStorage'
export type { CompareLabStorageReturn } from './useCompareLabStorage'

// Export
export { useCompareLabExport } from './useCompareLabExport'
export type { CompareLabExportReturn } from './useCompareLabExport'

// Presets
export { useCompareLabPresets } from './useCompareLabPresets'
export type { CompareLabPresetsReturn } from './useCompareLabPresets'

// Helpers
export { useCompareLabHelpers } from './useCompareLabHelpers'
export type { CompareLabHelpersReturn } from './useCompareLabHelpers'
