/**
 * StratocasterNeckGenerator preset management composable.
 */
import { computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import {
  convertStratParameters,
  validateStratParameters,
  type StratNeckParameters,
  type StratValidationWarning
} from '@/utils/strat_neck_generator'
import type { StratNeckPreset, StratNeckGeometry } from './stratNeckTypes'

// ============================================================================
// Types
// ============================================================================

export interface StratNeckPresetsReturn {
  isModifiedFromPreset: ComputedRef<boolean>
  fetchNeckPresets: () => Promise<void>
  loadPresetParams: () => Promise<void>
  clearPreset: () => void
  revertToPreset: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useStratNeckPresets(
  form: StratNeckParameters,
  generatedGeometry: Ref<StratNeckGeometry | null>,
  neckPresets: Ref<StratNeckPreset[]>,
  selectedPresetId: Ref<string>,
  presetLoadedMessage: Ref<string>,
  originalPresetParams: Ref<StratNeckParameters | null>,
  validationWarnings: Ref<StratValidationWarning[]>
): StratNeckPresetsReturn {
  /**
   * Check if form was modified from loaded preset.
   */
  const isModifiedFromPreset = computed(() => {
    if (!originalPresetParams.value || !selectedPresetId.value) return false

    const original = originalPresetParams.value
    const current = form

    // Compare all numeric fields
    const numericFields: (keyof StratNeckParameters)[] = [
      'blank_length',
      'blank_width',
      'blank_thickness',
      'scale_length',
      'nut_width',
      'heel_width',
      'neck_length',
      'fretboard_radius',
      'fretboard_offset',
      'fretboard_radius_heel',
      'thickness_1st_fret',
      'thickness_12th_fret',
      'shoulder_width',
      'headstock_length',
      'headstock_thickness',
      'headstock_taper',
      'tuner_spacing',
      'tuner_diameter',
      'truss_rod_channel_width',
      'truss_rod_channel_depth'
    ]

    return numericFields.some((field) => {
      const originalVal = original[field]
      const currentVal = current[field]
      if (originalVal === undefined || currentVal === undefined) return false
      return Math.abs((originalVal as number) - (currentVal as number)) > 0.001
    })
  })

  /**
   * Fetch available neck presets.
   */
  async function fetchNeckPresets(): Promise<void> {
    try {
      const response = await api('/api/neck/presets?type=stratocaster')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()
      neckPresets.value = data.presets || []
    } catch (error) {
      console.error('Failed to fetch Strat neck presets:', error)
      neckPresets.value = []
    }
  }

  /**
   * Load parameters from selected preset.
   */
  async function loadPresetParams(): Promise<void> {
    if (!selectedPresetId.value) return

    try {
      const response = await api(`/api/presets/${selectedPresetId.value}`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const preset = await response.json()

      // Map neck_params to form fields
      if (preset.neck_params) {
        let params = preset.neck_params

        // Detect units and convert if necessary
        const presetUnits = params.units || 'inch'
        const formUnits = 'inch' // StratocasterNeckGenerator uses inches

        if (presetUnits !== formUnits) {
          params = convertStratParameters(params, presetUnits, formUnits)
          presetLoadedMessage.value = `Loaded preset: ${preset.name} (converted from ${presetUnits} to ${formUnits})`
        } else {
          presetLoadedMessage.value = `Loaded preset: ${preset.name}`
        }

        // Store original params for revert functionality
        originalPresetParams.value = { ...params } as StratNeckParameters

        // Map all available fields from neck_params to form
        const fieldMappings: (keyof StratNeckParameters)[] = [
          'blank_length',
          'blank_width',
          'blank_thickness',
          'scale_length',
          'nut_width',
          'heel_width',
          'neck_length',
          'fretboard_radius',
          'fretboard_offset',
          'compound_radius',
          'fretboard_radius_heel',
          'include_fretboard',
          'fret_count',
          'profile_type',
          'thickness_1st_fret',
          'thickness_12th_fret',
          'shoulder_width',
          'headstock_length',
          'headstock_thickness',
          'headstock_taper',
          'tuner_spacing',
          'tuner_diameter',
          'string_tree_positions',
          'truss_rod_channel_width',
          'truss_rod_channel_depth',
          'truss_rod_access',
          'alignment_pin_holes',
          'skunk_stripe'
        ]

        fieldMappings.forEach((field) => {
          if (params[field] !== undefined) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            ;(form as any)[field] = params[field]
          }
        })

        // Validate parameters
        const validation = validateStratParameters(form)
        validationWarnings.value = validation.warnings

        setTimeout(() => {
          presetLoadedMessage.value = ''
        }, 3000)

        // Clear generated geometry when loading new preset
        generatedGeometry.value = null
      } else {
        presetLoadedMessage.value = 'Preset has no neck parameters'
        setTimeout(() => {
          presetLoadedMessage.value = ''
        }, 3000)
      }
    } catch (error) {
      console.error('Failed to load preset:', error)
      alert('Failed to load preset. Check console for details.')
    }
  }

  /**
   * Clear preset selection.
   */
  function clearPreset(): void {
    selectedPresetId.value = ''
    presetLoadedMessage.value = ''
    originalPresetParams.value = null
    validationWarnings.value = []
  }

  /**
   * Revert to original preset values.
   */
  function revertToPreset(): void {
    if (!originalPresetParams.value) return

    const original = originalPresetParams.value

    // Restore all parameters
    Object.keys(original).forEach((key) => {
      const typedKey = key as keyof StratNeckParameters
      if (original[typedKey] !== undefined) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(form as any)[typedKey] = original[typedKey]
      }
    })

    // Re-validate
    const validation = validateStratParameters(form)
    validationWarnings.value = validation.warnings

    // Clear geometry since params changed
    generatedGeometry.value = null

    presetLoadedMessage.value = 'Reverted to original preset values'
    setTimeout(() => {
      presetLoadedMessage.value = ''
    }, 3000)
  }

  return {
    isModifiedFromPreset,
    fetchNeckPresets,
    loadPresetParams,
    clearPreset,
    revertToPreset
  }
}
