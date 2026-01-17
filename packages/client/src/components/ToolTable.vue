<template>
  <div class="p-4 space-y-4">b
    <h2 class="text-xl font-bold">Tool Table</h2>
    <div class="flex items-center gap-3">
      <label class="text-sm">Machine
        <select v-model="mid" @change="refresh" class="border rounded p-1 ml-2">
          <option v-for="m in machines" :key="m.id" :value="m.id">{{ m.title }} ({{ m.id }})</option>
        </select>
      </label>
      <button class="px-3 py-1 border rounded hover:bg-gray-100" @click="refresh">Refresh</button>
      <a class="px-3 py-1 border rounded hover:bg-gray-100" :href="`/api/machines/tools/${mid}.csv`" download>Export CSV</a>
      <label class="px-3 py-1 border rounded cursor-pointer hover:bg-gray-100">
        Import CSV
        <input type="file" class="hidden" @change="importCsv" accept=".csv">
      </label>
    </div>
    <div class="overflow-auto max-h-[480px] border rounded">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100 sticky top-0">
          <tr>
            <th class="text-left p-2 border-b">T</th>
            <th class="text-left p-2 border-b">Name</th>
            <th class="text-left p-2 border-b">Type</th>
            <th class="text-right p-2 border-b">Ø (mm)</th>
            <th class="text-right p-2 border-b">Len (mm)</th>
            <th class="text-left p-2 border-b">Holder</th>
            <th class="text-right p-2 border-b">Len Offs</th>
            <th class="text-right p-2 border-b">RPM</th>
            <th class="text-right p-2 border-b">Feed</th>
            <th class="text-right p-2 border-b">Plunge</th>
            <th class="p-2 border-b"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(t,i) in tools" :key="i" class="hover:bg-gray-50">
            <td class="p-2 border-b"><input type="number" class="w-16 border rounded p-1" v-model.number="t.t" /></td>
            <td class="p-2 border-b"><input class="w-48 border rounded p-1" v-model="t.name" /></td>
            <td class="p-2 border-b"><input class="w-20 border rounded p-1" v-model="t.type" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.dia_mm" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.len_mm" /></td>
            <td class="p-2 border-b"><input class="w-24 border rounded p-1" v-model="t.holder" /></td>
            <td class="p-2 border-b text-right"><input type="number" step="0.01" class="w-24 border rounded p-1 text-right" v-model.number="t.offset_len_mm" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.spindle_rpm" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.feed_mm_min" /></td>
            <td class="p-2 border-b text-right"><input type="number" class="w-24 border rounded p-1 text-right" v-model.number="t.plunge_mm_min" /></td>
            <td class="p-2 border-b"><button class="text-red-600 hover:underline" @click="rm(i)">Delete</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex items-center gap-2">
      <button class="px-3 py-1 rounded bg-black text-white hover:bg-gray-800" @click="add">Add Tool</button>
      <button class="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700" @click="save">Save All</button>
      <span v-if="saved" class="text-green-700 text-sm">Saved ✓</span>
      <span v-if="error" class="text-red-600 text-sm">{{ error }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const machines = ref<any[]>([])
const mid = ref('')
const tools = ref<any[]>([])
const saved = ref(false)
const error = ref('')

async function loadMachines() {
  try {
    const r = await fetch('/api/machines')
    const j = await r.json()
    machines.value = j.machines || []
    if (machines.value.length) {
      mid.value = machines.value[0].id
    }
  } catch (e: any) {
    error.value = 'Failed to load machines: ' + e.message
  }
}

async function refresh() {
  if (!mid.value) return
  try {
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value))
    const j = await r.json()
    tools.value = j.tools || []
    saved.value = false
    error.value = ''
  } catch (e: any) {
    error.value = 'Failed to load tools: ' + e.message
  }
}

function add() {
  const lastT = tools.value.slice(-1)[0]?.t || 0
  tools.value.push({ 
    t: lastT + 1, 
    name: 'New Tool', 
    type: 'EM', 
    dia_mm: 3.0, 
    len_mm: 30.0,
    holder: null,
    offset_len_mm: null,
    spindle_rpm: null,
    feed_mm_min: null,
    plunge_mm_min: null
  })
  saved.value = false
}

function rm(i: number) {
  tools.value.splice(i, 1)
  saved.value = false
}

async function save() {
  try {
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value), { 
      method: 'PUT', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(tools.value) 
    })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    saved.value = true
    error.value = ''
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e: any) {
    error.value = 'Save failed: ' + e.message
  }
}

async function importCsv(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  if (!f) return
  
  try {
    const fd = new FormData()
    fd.append('file', f)
    const r = await fetch('/api/machines/tools/' + encodeURIComponent(mid.value) + '/import_csv', { 
      method: 'POST', 
      body: fd 
    })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    await refresh()
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch (e: any) {
    error.value = 'Import failed: ' + e.message
  }
  
  // Reset file input
  target.value = ''
}

onMounted(async () => { 
  await loadMachines()
  await refresh()
})
</script>
