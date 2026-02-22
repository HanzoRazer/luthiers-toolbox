/**
 * Composable for pipeline preset management.
 */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { api } from '@/services/apiBase'
import type { PipelinePreset } from './pipelineTypes'

// ============================================================================
// Types
// ============================================================================

export interface PipelinePresetsState {
  presets: Ref<PipelinePreset[]>
  selectedPresetId: Ref<string | null>
  newPresetName: Ref<string>
  newPresetDesc: Ref<string>
  selectedPreset: ComputedRef<PipelinePreset | null>
  loadPresets: () => Promise<void>
  applyPreset: (
    id: string | null,
    callbacks: {
      setUnits: (u: 'mm' | 'inch') => void
      setMachineId: (id: string | null) => void
      setPostId: (id: string | null) => void
      refreshInspector: () => Promise<void>
    }
  ) => Promise<void>
  savePreset: (
    config: {
      units: 'mm' | 'inch'
      machineId: string | null
      postId: string | null
    },
    callbacks: {
      setError: (msg: string | null) => void
      refreshInspector: () => Promise<void>
    }
  ) => Promise<void>
}

// ============================================================================
// Composable
// ============================================================================

export function usePipelinePresets(): PipelinePresetsState {
  const presets = ref<PipelinePreset[]>([])
  const selectedPresetId = ref<string | null>(null)
  const newPresetName = ref('')
  const newPresetDesc = ref('')

  const selectedPreset = computed(() =>
    presets.value.find(p => p.id === selectedPresetId.value) ?? null
  )

  async function loadPresets(): Promise<void> {
    try {
      const resp = await api('/api/cam/pipeline/presets')
      if (!resp.ok) return
      const data = await resp.json() as PipelinePreset[]
      presets.value = data
    } catch {
      // ignore
    }
  }

  async function applyPreset(
    id: string | null,
    callbacks: {
      setUnits: (u: 'mm' | 'inch') => void
      setMachineId: (id: string | null) => void
      setPostId: (id: string | null) => void
      refreshInspector: () => Promise<void>
    }
  ): Promise<void> {
    if (!id) return
    const preset = presets.value.find(p => p.id === id)
    if (!preset) return

    selectedPresetId.value = id
    callbacks.setUnits(preset.units)
    callbacks.setMachineId(preset.machine_id ?? null)
    callbacks.setPostId(preset.post_id ?? null)
    await callbacks.refreshInspector()
  }

  async function savePreset(
    config: {
      units: 'mm' | 'inch'
      machineId: string | null
      postId: string | null
    },
    callbacks: {
      setError: (msg: string | null) => void
      refreshInspector: () => Promise<void>
    }
  ): Promise<void> {
    if (!newPresetName.value.trim()) {
      callbacks.setError('Preset name is required.')
      return
    }

    callbacks.setError(null)

    try {
      const body = {
        name: newPresetName.value.trim(),
        description: newPresetDesc.value.trim() || null,
        units: config.units,
        machine_id: config.machineId,
        post_id: config.postId
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

      const created = await resp.json() as PipelinePreset
      presets.value.push(created)
      selectedPresetId.value = created.id
      newPresetName.value = ''
      newPresetDesc.value = ''
      await callbacks.refreshInspector()
    } catch (e: any) {
      callbacks.setError(e?.message ?? String(e))
    }
  }

  return {
    presets,
    selectedPresetId,
    newPresetName,
    newPresetDesc,
    selectedPreset,
    loadPresets,
    applyPreset,
    savePreset
  }
}
