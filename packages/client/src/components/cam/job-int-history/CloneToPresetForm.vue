<script setup lang="ts">
/**
 * CloneToPresetForm - Modal form for cloning job entries to presets
 * Extracted from JobIntHistoryPanel.vue
 */

interface JobEntry {
  run_id: string
  job_name?: string | null
  machine_id?: string | null
  post_id?: string | null
  sim_time_s?: number | null
  use_helical?: boolean | null
}

interface CloneFormState {
  name: string
  description: string
  kind: 'cam' | 'combo'
  tagsInput: string
  cam_params?: {
    strategy?: string
  }
}

defineProps<{
  entry: JobEntry
  form: CloneFormState
  cloning: boolean
  success: boolean
  error: string | null
}>()

const emit = defineEmits<{
  'close': []
  'execute': []
  'update:form': [form: CloneFormState]
}>()

function formatTime(seconds?: number | null): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}m ${secs}s`
}
</script>

<template>
  <div class="flex flex-col gap-3 text-xs">
    <!-- Source Job Info -->
    <div class="p-3 bg-slate-50 rounded border">
      <div class="font-semibold mb-2">
        Source Job
      </div>
      <div class="grid grid-cols-2 gap-2 text-[11px]">
        <div><span class="text-gray-500">Job:</span> {{ entry.job_name || '(unnamed)' }}</div>
        <div><span class="text-gray-500">Run ID:</span> <span class="font-mono">{{ entry.run_id }}</span></div>
        <div><span class="text-gray-500">Machine:</span> {{ entry.machine_id || '—' }}</div>
        <div><span class="text-gray-500">Post:</span> {{ entry.post_id || '—' }}</div>
        <div><span class="text-gray-500">Time:</span> {{ formatTime(entry.sim_time_s) }}</div>
        <div><span class="text-gray-500">Helical:</span> {{ entry.use_helical ? 'Yes' : 'No' }}</div>
      </div>
    </div>

    <!-- Preset Configuration -->
    <div class="flex flex-col gap-2">
      <label class="flex flex-col gap-1">
        <span class="font-semibold">Preset Name *</span>
        <input
          :value="form.name"
          type="text"
          class="border rounded px-2 py-1"
          placeholder="e.g., Helical Pocket - VF2 - GRBL"
          @input="emit('update:form', { ...form, name: ($event.target as HTMLInputElement).value })"
        >
      </label>

      <label class="flex flex-col gap-1">
        <span class="font-semibold">Description</span>
        <textarea
          :value="form.description"
          class="border rounded px-2 py-1 h-16"
          placeholder="Optional description of this preset..."
          @input="emit('update:form', { ...form, description: ($event.target as HTMLTextAreaElement).value })"
        />
      </label>

      <div class="grid grid-cols-2 gap-2">
        <label class="flex flex-col gap-1">
          <span class="font-semibold">Preset Kind</span>
          <select
            :value="form.kind"
            class="border rounded px-2 py-1"
            @change="emit('update:form', { ...form, kind: ($event.target as HTMLSelectElement).value as 'cam' | 'combo' })"
          >
            <option value="cam">CAM</option>
            <option value="combo">Combo (CAM + Export)</option>
          </select>
        </label>

        <label class="flex flex-col gap-1">
          <span class="font-semibold">Tags</span>
          <input
            :value="form.tagsInput"
            type="text"
            class="border rounded px-2 py-1"
            placeholder="helical, production, test"
            @input="emit('update:form', { ...form, tagsInput: ($event.target as HTMLInputElement).value })"
          >
          <span class="text-[10px] text-gray-500">Comma-separated</span>
        </label>
      </div>
    </div>

    <!-- CAM Parameters Preview (from job) -->
    <div class="p-3 bg-blue-50 rounded border border-blue-200">
      <div class="font-semibold mb-2">
        CAM Parameters (auto-filled from job)
      </div>
      <div class="grid grid-cols-2 gap-2 text-[11px]">
        <div><span class="text-gray-600">Machine:</span> {{ entry.machine_id || 'Not specified' }}</div>
        <div><span class="text-gray-600">Post:</span> {{ entry.post_id || 'Not specified' }}</div>
        <div><span class="text-gray-600">Strategy:</span> {{ form.cam_params?.strategy || 'Spiral (default)' }}</div>
        <div><span class="text-gray-600">Helical:</span> {{ entry.use_helical ? 'Enabled' : 'Disabled' }}</div>
      </div>
      <p class="text-[10px] text-blue-700 mt-2">
        Info: Full CAM params will be loaded from job detail on save
      </p>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-2 pt-2 border-t">
      <button
        type="button"
        class="px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50"
        @click="emit('close')"
      >
        Cancel
      </button>
      <button
        type="button"
        class="px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        :disabled="!form.name || cloning"
        @click="emit('execute')"
      >
        {{ cloning ? 'Cloning...' : 'Create Preset' }}
      </button>
    </div>

    <!-- Success/Error Messages -->
    <div
      v-if="success"
      class="p-2 bg-green-50 border border-green-200 rounded text-green-700 text-[11px]"
    >
      Preset created successfully! <a
        href="#/lab/preset-hub"
        class="underline"
      >View in Preset Hub</a>
    </div>
    <div
      v-if="error"
      class="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-[11px]"
    >
      {{ error }}
    </div>
  </div>
</template>
