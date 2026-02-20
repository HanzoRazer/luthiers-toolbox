/**
 * Composable for preset create/edit form management.
 * Extracted from PresetHubView.vue
 */
import { ref, type Ref } from 'vue'
import type { Preset } from './usePresetFilters'

// ==========================================================================
// Types
// ==========================================================================

export interface PresetFormData {
  name: string
  kind: 'cam' | 'export' | 'neck' | 'combo'
  description: string
  tags: string[]
  machine_id: string
  post_id: string
  units: string
  cam_params: Record<string, unknown>
  export_params: Record<string, unknown>
  neck_params: Record<string, unknown>
}

export interface PresetFormState {
  /** Whether create modal is showing */
  showCreateModal: Ref<boolean>
  /** Preset being edited (null = creating new) */
  editingPreset: Ref<Preset | null>
  /** Whether save operation is in progress */
  saving: Ref<boolean>
  /** Form data for create/edit */
  formData: Ref<PresetFormData>
  /** Comma-separated tags input */
  tagsInput: Ref<string>
  /** Export filename template */
  exportTemplate: Ref<string>
  /** Save preset (create or update) */
  savePreset: () => Promise<void>
  /** Close modal and reset form */
  closeModal: () => void
  /** Open edit modal for a preset */
  editPreset: (preset: Preset) => void
  /** Open create modal with cloned preset data */
  clonePreset: (preset: Preset) => void
}

// ==========================================================================
// Constants
// ==========================================================================

const DEFAULT_FORM_DATA: PresetFormData = {
  name: '',
  kind: 'cam',
  description: '',
  tags: [],
  machine_id: '',
  post_id: '',
  units: 'mm',
  cam_params: {},
  export_params: {},
  neck_params: {},
}

const DEFAULT_EXPORT_TEMPLATE = '{preset}__{post}__{date}.nc'

// ==========================================================================
// Composable
// ==========================================================================

export function usePresetForm(
  onSaveSuccess: () => Promise<void>
): PresetFormState {
  const showCreateModal = ref(false)
  const editingPreset = ref<Preset | null>(null)
  const saving = ref(false)

  const formData = ref<PresetFormData>({ ...DEFAULT_FORM_DATA })
  const tagsInput = ref('')
  const exportTemplate = ref(DEFAULT_EXPORT_TEMPLATE)

  // ========================================================================
  // Methods
  // ========================================================================

  function resetForm() {
    formData.value = { ...DEFAULT_FORM_DATA }
    tagsInput.value = ''
    exportTemplate.value = DEFAULT_EXPORT_TEMPLATE
  }

  function closeModal() {
    showCreateModal.value = false
    editingPreset.value = null
    resetForm()
  }

  function editPreset(preset: Preset) {
    editingPreset.value = preset
    formData.value = {
      name: preset.name,
      kind: preset.kind,
      description: preset.description || '',
      tags: preset.tags || [],
      machine_id: preset.machine_id || '',
      post_id: preset.post_id || '',
      units: preset.units || 'mm',
      cam_params: preset.cam_params || {},
      export_params: preset.export_params || {},
      neck_params: preset.neck_params || {},
    }
    tagsInput.value = (preset.tags || []).join(', ')
    exportTemplate.value =
      (preset.export_params as any)?.filename_template || DEFAULT_EXPORT_TEMPLATE
  }

  function clonePreset(preset: Preset) {
    formData.value = {
      name: `${preset.name} (Copy)`,
      kind: preset.kind,
      description: preset.description || '',
      tags: preset.tags || [],
      machine_id: preset.machine_id || '',
      post_id: preset.post_id || '',
      units: preset.units || 'mm',
      cam_params: preset.cam_params || {},
      export_params: preset.export_params || {},
      neck_params: preset.neck_params || {},
    }
    tagsInput.value = (preset.tags || []).join(', ')
    exportTemplate.value =
      (preset.export_params as any)?.filename_template || DEFAULT_EXPORT_TEMPLATE
    showCreateModal.value = true
  }

  async function savePreset() {
    saving.value = true
    try {
      // Parse tags from comma-separated input
      formData.value.tags = tagsInput.value
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0)

      // Set export params if applicable
      if (formData.value.kind === 'export' || formData.value.kind === 'combo') {
        formData.value.export_params = {
          filename_template: exportTemplate.value,
        }
      }

      const url = editingPreset.value
        ? `/api/presets/${editingPreset.value.id}`
        : '/api/presets'

      const method = editingPreset.value ? 'PATCH' : 'POST'

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData.value),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      await onSaveSuccess()
      closeModal()
    } catch (error) {
      console.error('Failed to save preset:', error)
      alert('Failed to save preset. Check console for details.')
    } finally {
      saving.value = false
    }
  }

  return {
    showCreateModal,
    editingPreset,
    saving,
    formData,
    tagsInput,
    exportTemplate,
    savePreset,
    closeModal,
    editPreset,
    clonePreset,
  }
}
