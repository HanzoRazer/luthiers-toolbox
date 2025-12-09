<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
CamPipelinePresetList - List, select, delete pipeline presets

Repository: HanzoRazer/luthiers-toolbox
Updated: November 2025
-->

<template>
  <div class="border rounded-lg p-3 bg-white text-[11px] space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        Pipeline Presets
      </h3>
      <div class="flex items-center gap-2">
        <input
          v-model="query"
          placeholder="Filter presets…"
          class="border rounded px-2 py-0.5 text-[10px] w-32"
        />
        <button
          class="px-2 py-0.5 rounded border border-gray-300 text-[10px] disabled:opacity-50"
          :disabled="loading"
          @click="loadPresets"
        >
          <span v-if="!loading">Reload</span>
          <span v-else>Loading…</span>
        </button>
      </div>
    </div>

    <p v-if="error" class="text-[11px] text-red-600">
      {{ error }}
    </p>

    <div
      v-if="!filteredPresets.length && !loading && !error"
      class="text-[11px] text-gray-500"
    >
      No presets. Save one from Bridge Lab to see it here.
    </div>

    <ul v-else class="space-y-1 max-h-52 overflow-auto pr-1">
      <li
        v-for="preset in filteredPresets"
        :key="preset.id"
        class="flex items-start justify-between gap-2 px-2 py-1 rounded cursor-pointer hover:bg-gray-50"
        :class="preset.id === selectedId ? 'bg-gray-100' : ''"
        @click="selectPreset(preset.id)"
      >
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-1">
            <div class="truncate">
              <span class="font-semibold">{{ preset.name }}</span>
            </div>
            <span class="text-[9px] text-gray-400 font-mono">
              {{ preset.id }}
            </span>
          </div>
          <p class="text-[10px] text-gray-500 truncate">
            {{ preset.description || 'No description' }}
          </p>
        </div>
        <button
          class="ml-1 px-1.5 py-0.5 rounded text-[9px] border border-rose-200 text-rose-600 hover:bg-rose-50"
          @click.stop="deletePreset(preset.id)"
        >
          delete
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

interface PipelinePreset {
  id: string
  name: string
  description?: string | null
  created_at?: string | null
  updated_at?: string | null
}

const emit = defineEmits<{
  (e: 'preset-selected', id: string): void
  (e: 'preset-deleted', id: string): void
}>()

const presets = ref<PipelinePreset[]>([])
const selectedId = ref<string>('')
const loading = ref(false)
const error = ref<string | null>(null)
const query = ref('')

const filteredPresets = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return presets.value
  return presets.value.filter((p) => {
    const hay = `${p.id} ${p.name} ${p.description || ''}`.toLowerCase()
    return hay.includes(q)
  })
})

async function loadPresets () {
  loading.value = true
  error.value = null

  try {
    const resp = await fetch('/cam/pipeline/presets')
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    const data = await resp.json() as PipelinePreset[]
    presets.value = data
    if (!selectedId.value && presets.value.length > 0) {
      selectedId.value = presets.value[0].id
      emit('preset-selected', selectedId.value)
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  } finally {
    loading.value = false
  }
}

function selectPreset (id: string) {
  selectedId.value = id
  emit('preset-selected', id)
}

async function deletePreset (id: string) {
  if (!window.confirm(`Delete preset ${id}?`)) return

  try {
    const resp = await fetch(`/cam/pipeline/presets/${encodeURIComponent(id)}`, {
      method: 'DELETE'
    })
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    presets.value = presets.value.filter((p) => p.id !== id)
    if (selectedId.value === id) {
      selectedId.value = ''
    }
    emit('preset-deleted', id)
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  }
}

onMounted(() => {
  void loadPresets()
})
</script>
