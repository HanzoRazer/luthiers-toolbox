/**
 * CompareLab state composable.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { CanonicalGeometry } from '@/utils/geometry'
import type {
  DiffResult,
  ExtensionMismatch,
  TemplateValidation,
  PresetForm,
  PresetSaveMessage,
  ExportPreset,
  ExportFormat
} from './compareLabTypes'
import { STORAGE_KEYS } from './compareLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CompareLabStateReturn {
  // File input
  fileInput: Ref<HTMLInputElement | null>

  // Geometry
  currentGeometry: Ref<CanonicalGeometry | null>
  diffResult: Ref<DiffResult | null>
  hasStoredGeometry: ComputedRef<boolean>

  // Export dialog
  showExportDialog: Ref<boolean>
  exportFormat: Ref<ExportFormat>
  exportInProgress: Ref<boolean>
  exportPrefix: Ref<string>

  // Template
  exportPresets: Ref<ExportPreset[]>
  selectedPresetId: Ref<string>
  filenameTemplate: Ref<string>
  templateValidation: Ref<TemplateValidation | null>

  // Neck context
  neckProfileContext: Ref<string | null>
  neckSectionContext: Ref<string | null>

  // Extension mismatch
  extensionMismatch: ComputedRef<ExtensionMismatch | null>

  // Save preset modal
  showSavePresetModal: Ref<boolean>
  presetSaveInProgress: Ref<boolean>
  presetSaveMessage: Ref<PresetSaveMessage | null>
  presetForm: Ref<PresetForm>

  // Export filename
  exportFilename: ComputedRef<string>
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareLabState(): CompareLabStateReturn {
  // File input
  const fileInput = ref<HTMLInputElement | null>(null)

  // Geometry
  const currentGeometry = ref<CanonicalGeometry | null>(null)
  const diffResult = ref<DiffResult | null>(null)

  const hasStoredGeometry = computed(() =>
    Boolean(localStorage.getItem(STORAGE_KEYS.GEOMETRY))
  )

  // Export dialog
  const showExportDialog = ref(false)
  const exportFormat = ref<ExportFormat>('svg')
  const exportInProgress = ref(false)
  const exportPrefix = ref(localStorage.getItem(STORAGE_KEYS.EXPORT_PREFIX) || '')

  // Template
  const exportPresets = ref<ExportPreset[]>([])
  const selectedPresetId = ref('')
  const filenameTemplate = ref('{preset}__{compare_mode}__{date}')
  const templateValidation = ref<TemplateValidation | null>(null)

  // Neck context
  const neckProfileContext = ref<string | null>(null)
  const neckSectionContext = ref<string | null>(null)

  // Extension mismatch detection
  const extensionMismatch = computed((): ExtensionMismatch | null => {
    const template = filenameTemplate.value.toLowerCase()
    const format = exportFormat.value.toLowerCase()

    // Extract extension from template (last .xxx after removing tokens)
    const withoutTokens = template.replace(/\{[^}]+\}/g, '')
    const match = withoutTokens.match(/\.(svg|png|csv|dxf|nc|gcode)$/i)
    const templateExt = match ? match[1].toLowerCase() : null

    if (!templateExt) return null // No extension in template

    if (templateExt !== format) {
      return {
        templateExt,
        expectedExt: format,
        hasConflict: true
      }
    }

    return null
  })

  // Save preset modal
  const showSavePresetModal = ref(false)
  const presetSaveInProgress = ref(false)
  const presetSaveMessage = ref<PresetSaveMessage | null>(null)
  const presetForm = ref<PresetForm>({
    name: '',
    description: '',
    tagsInput: 'comparison',
    kind: 'export'
  })

  // Export filename
  const exportFilename = computed(() => {
    if (!diffResult.value) return 'compare.svg'

    // If using template engine, resolve tokens
    if (filenameTemplate.value && filenameTemplate.value.includes('{')) {
      // Build context for token resolution
      const context: Record<string, string> = {
        preset: exportPrefix.value || diffResult.value.baseline_name || 'compare',
        compare_mode: 'neck_diff',
        date: new Date().toISOString().slice(0, 10),
        timestamp: new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      }

      // Add neck context if available
      if (neckProfileContext.value) {
        context.neck_profile = neckProfileContext.value
      }
      if (neckSectionContext.value) {
        context.neck_section = neckSectionContext.value
      }

      // Resolve template
      let resolved = filenameTemplate.value
      Object.keys(context).forEach(key => {
        const regex = new RegExp(`\\{${key}\\}`, 'gi')
        resolved = resolved.replace(regex, context[key] || '')
      })

      // Sanitize
      resolved = resolved.replace(/[^a-zA-Z0-9_.-]/g, '_').replace(/_+/g, '_')

      return `${resolved}.${exportFormat.value}`
    }

    // Fallback to legacy naming
    const parts: string[] = []
    if (exportPrefix.value.trim()) {
      parts.push(exportPrefix.value.trim())
    }

    const baseline = diffResult.value.baseline_name || 'baseline'
    const compare = 'compare'
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const ext = exportFormat.value

    const baseName =
      parts.length > 0
        ? `${parts.join('_')}_baseline-${baseline}_vs_${compare}`
        : `compare_${baseline}_vs_${compare}`

    return `${baseName}_${timestamp}.${ext}`
  })

  return {
    // File input
    fileInput,

    // Geometry
    currentGeometry,
    diffResult,
    hasStoredGeometry,

    // Export dialog
    showExportDialog,
    exportFormat,
    exportInProgress,
    exportPrefix,

    // Template
    exportPresets,
    selectedPresetId,
    filenameTemplate,
    templateValidation,

    // Neck context
    neckProfileContext,
    neckSectionContext,

    // Extension mismatch
    extensionMismatch,

    // Save preset modal
    showSavePresetModal,
    presetSaveInProgress,
    presetSaveMessage,
    presetForm,

    // Export filename
    exportFilename
  }
}
