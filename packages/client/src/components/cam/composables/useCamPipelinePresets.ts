/**
 * CamPipeline preset management composable.
 */
import type { Ref } from 'vue'
import { api } from '@/services/apiBase'
import type { PipelinePreset } from './camPipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface CamPipelinePresetsReturn {
  loadPresets: () => Promise<void>
  applyPreset: (id: string | null) => Promise<void>
  savePreset: () => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function useCamPipelinePresets(
  presets: Ref<PipelinePreset[]>,
  selectedPresetId: Ref<string | null>,
  newPresetName: Ref<string>,
  newPresetDesc: Ref<string>,
  units: Ref<'mm' | 'inch'>,
  machineId: Ref<string | null>,
  postId: Ref<string | null>,
  error: Ref<string | null>,
  refreshInspector: () => Promise<void>
): CamPipelinePresetsReturn {
  /**
   * Load presets from API on mount.
   */
  async function loadPresets(): Promise<void> {
    try {
      const resp = await api('/api/cam/pipeline/presets')
      if (!resp.ok) return
      const data = (await resp.json()) as PipelinePreset[]
      presets.value = data
    } catch {
      // ignore
    }
  }

  /**
   * Apply a preset to current state.
   */
  async function applyPreset(id: string | null): Promise<void> {
    if (!id) return
    const preset = presets.value.find(p => p.id === id)
    if (!preset) return
    selectedPresetId.value = id
    units.value = preset.units
    machineId.value = preset.machine_id ?? null
    postId.value = preset.post_id ?? null
    await refreshInspector()
  }

  /**
   * Save current configuration as a new preset.
   */
  async function savePreset(): Promise<void> {
    if (!newPresetName.value.trim()) {
      error.value = 'Preset name is required.'
      return
    }
    error.value = null
    try {
      const body = {
        name: newPresetName.value.trim(),
        description: newPresetDesc.value.trim() || null,
        units: units.value,
        machine_id: machineId.value,
        post_id: postId.value
      }
      const resp = await api('/api/cam/pipeline/presets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(text || `HTTP ${resp.status}`)
      }
      const created = (await resp.json()) as PipelinePreset
      presets.value.push(created)
      selectedPresetId.value = created.id
      newPresetName.value = ''
      newPresetDesc.value = ''
      await refreshInspector()
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    }
  }

  return {
    loadPresets,
    applyPreset,
    savePreset
  }
}
