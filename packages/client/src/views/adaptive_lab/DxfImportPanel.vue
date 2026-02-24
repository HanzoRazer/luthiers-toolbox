<template>
  <div class="border rounded-lg p-3 bg-white space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        DXF → Loops
      </h3>
      <span class="text-[10px] text-gray-500">
        Plan from DXF
      </span>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-[11px]">
      <input
        type="file"
        accept=".dxf"
        class="text-[11px]"
        @change="onFileChange"
      >
      <select
        :value="units"
        class="border rounded px-2 py-1 text-[11px]"
        @change="$emit('update:units', ($event.target as HTMLSelectElement).value as 'mm' | 'inch')"
      >
        <option value="mm">
          mm
        </option>
        <option value="inch">
          inch
        </option>
      </select>
      <input
        :value="geometryLayer"
        placeholder="geometry_layer (optional)"
        class="border rounded px-2 py-1 text-[11px] w-40"
        @input="$emit('update:geometryLayer', ($event.target as HTMLInputElement).value)"
      >
      <button
        class="px-2 py-1 rounded bg-gray-900 text-white text-[11px] disabled:opacity-50"
        :disabled="!hasFile || loading"
        @click="$emit('import')"
      >
        <span v-if="!loading">Import DXF → Loops</span>
        <span v-else>Importing…</span>
      </button>
    </div>
    <p
      v-if="error"
      class="text-[11px] text-red-600"
    >
      {{ error }}
    </p>
    <p
      v-if="debug"
      class="text-[10px] text-gray-500 whitespace-pre-wrap"
    >
      {{ debug }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  units: 'mm' | 'inch'
  geometryLayer: string
  hasFile: boolean
  loading: boolean
  error: string | null
  debug: string | null
}>()

const emit = defineEmits<{
  'update:units': [value: 'mm' | 'inch']
  'update:geometryLayer': [value: string]
  'file-change': [file: File]
  import: []
}>()

function onFileChange(ev: Event) {
  const input = ev.target as HTMLInputElement
  const f = input.files?.[0]
  if (f) emit('file-change', f)
}
</script>
