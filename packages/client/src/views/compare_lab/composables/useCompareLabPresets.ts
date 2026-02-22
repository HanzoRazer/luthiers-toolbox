/**
 * CompareLab preset management composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import type {
  DiffResult,
  ExportPreset,
  ExportFormat,
  TemplateValidation,
  PresetForm,
  PresetSaveMessage
} from './compareLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CompareLabPresetsReturn {
  loadExportPresets: () => Promise<void>
  loadPresetTemplate: () => Promise<void>
  validateTemplate: () => Promise<void>
  saveAsPreset: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareLabPresets(
  exportPresets: Ref<ExportPreset[]>,
  selectedPresetId: Ref<string>,
  filenameTemplate: Ref<string>,
  templateValidation: Ref<TemplateValidation | null>,
  exportFormat: Ref<ExportFormat>,
  neckProfileContext: Ref<string | null>,
  neckSectionContext: Ref<string | null>,
  diffResult: Ref<DiffResult | null>,
  showSavePresetModal: Ref<boolean>,
  presetSaveInProgress: Ref<boolean>,
  presetSaveMessage: Ref<PresetSaveMessage | null>,
  presetForm: Ref<PresetForm>
): CompareLabPresetsReturn {
  /**
   * Load export presets from API.
   */
  async function loadExportPresets(): Promise<void> {
    try {
      const response = await api('/api/presets?kind=export')
      exportPresets.value = await response.json()
    } catch (error) {
      console.error('Failed to load export presets:', error)
    }
  }

  /**
   * Load preset template from selected preset.
   */
  async function loadPresetTemplate(): Promise<void> {
    if (!selectedPresetId.value) {
      filenameTemplate.value = '{preset}__{compare_mode}__{date}'
      return
    }

    try {
      const response = await api(`/api/presets/${selectedPresetId.value}`)
      const preset = await response.json()
      if (preset.export_params?.filename_template) {
        filenameTemplate.value = preset.export_params.filename_template
      }
    } catch (error) {
      console.error('Failed to load preset template:', error)
    }
  }

  /**
   * Validate filename template.
   */
  async function validateTemplate(): Promise<void> {
    if (!filenameTemplate.value) return

    try {
      const response = await api('/api/presets/validate-template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template: filenameTemplate.value })
      })
      templateValidation.value = await response.json()
    } catch (error) {
      console.error('Template validation failed:', error)
      templateValidation.value = { valid: false, warnings: ['Validation failed'] }
    }
  }

  /**
   * Save current configuration as a preset.
   */
  async function saveAsPreset(): Promise<void> {
    if (!presetForm.value.name.trim()) {
      presetSaveMessage.value = { type: 'error', text: 'Preset name is required' }
      return
    }

    presetSaveInProgress.value = true
    presetSaveMessage.value = null

    try {
      // Parse tags from comma-separated input
      const tags = presetForm.value.tagsInput
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0)

      // Build export_params
      const export_params: Record<string, any> = {
        filename_template: filenameTemplate.value,
        format: exportFormat.value
      }

      // Add neck context if available
      if (neckProfileContext.value) {
        export_params.neck_profile = neckProfileContext.value
      }
      if (neckSectionContext.value) {
        export_params.neck_section = neckSectionContext.value
      }

      // Build cam_params for combo presets
      const cam_params =
        presetForm.value.kind === 'combo' && diffResult.value
          ? {
              compare_mode: diffResult.value.mode || 'neck_diff',
              baseline_name: diffResult.value.baseline_name || 'baseline'
            }
          : undefined

      // Create preset payload
      const payload = {
        name: presetForm.value.name.trim(),
        kind: presetForm.value.kind,
        description: presetForm.value.description.trim() || undefined,
        tags: tags,
        export_params: export_params,
        cam_params: cam_params,
        source: 'manual'
      }

      const response = await api('/api/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || `HTTP ${response.status}`)
      }

      const created = await response.json()

      presetSaveMessage.value = {
        type: 'success',
        text: `✅ Preset "${created.name}" saved successfully!`
      }

      // Reset form and close after 2 seconds
      setTimeout(() => {
        showSavePresetModal.value = false
        presetForm.value = {
          name: '',
          description: '',
          tagsInput: 'comparison',
          kind: 'export'
        }
        presetSaveMessage.value = null

        // Refresh export presets list
        loadExportPresets()
      }, 2000)
    } catch (error: any) {
      console.error('Failed to save preset:', error)
      presetSaveMessage.value = {
        type: 'error',
        text: `❌ Failed to save preset: ${error.message}`
      }
    } finally {
      presetSaveInProgress.value = false
    }
  }

  return {
    loadExportPresets,
    loadPresetTemplate,
    validateTemplate,
    saveAsPreset
  }
}
