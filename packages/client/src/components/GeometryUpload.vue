<template>
  <div class="p-3 border rounded space-y-2">
    <h3 class="text-base font-semibold">
      Geometry Upload (DXF/SVG/JSON)
    </h3>
    <div class="flex gap-2 items-center">
      <input
        type="file"
        accept=".dxf,.svg"
        @change="onFile"
      >
      <button
        class="px-3 py-1 border rounded"
        @click="sendJson"
      >
        Send JSON Example
      </button>
    </div>
    <pre
      v-if="resp"
      class="text-xs bg-slate-50 p-2 overflow-auto"
    >Response: {{ resp }}</pre>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref } from 'vue'

const resp = ref<string>('')

async function onFile(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || !files[0]) return
  const fd = new FormData()
  fd.append('file', files[0])
  const r = await api('/api/geometry/import', { method: 'POST', body: fd })
  resp.value = await r.text()
}

async function sendJson() {
  const body = {
    units: 'mm',
    paths: [
      { type: 'line', x1: 0, y1: 0, x2: 60, y2: 0 },
      { type: 'arc', cx: 30, cy: 20, r: 20, start: 180, end: 0, cw: false }
    ]
  }
  const r = await api('/api/geometry/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  resp.value = await r.text()
}
</script>
