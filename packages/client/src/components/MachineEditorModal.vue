<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50"
  >
    <div
      class="absolute inset-0 bg-black/40"
      @click="$emit('update:modelValue', false)"
    />
    <div class="absolute inset-0 sm:inset-10 bg-white rounded-xl shadow-xl flex flex-col">
      <div class="px-4 py-3 border-b flex items-center gap-2">
        <h3 class="text-lg font-semibold">
          {{ title }}
        </h3>
        <button
          class="ml-auto px-3 py-1 border rounded hover:bg-gray-50"
          @click="save"
        >
          Save
        </button>
        <button
          class="px-3 py-1 border rounded hover:bg-gray-50"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </button>
      </div>
      <div class="p-3 grid gap-2 overflow-y-auto">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-medium">ID</label>
            <input
              v-model="working.id"
              class="border px-2 py-1 rounded w-full"
              placeholder="unique_id"
            >
          </div>
          <div>
            <label class="text-xs font-medium">Title</label>
            <input
              v-model="working.title"
              class="border px-2 py-1 rounded w-full"
              placeholder="Display Name"
            >
          </div>
        </div>
        <label class="text-xs font-medium">JSON Configuration</label>
        <textarea 
          v-model="jsonText" 
          class="border rounded w-full h-96 font-mono text-[12px] p-2"
          spellcheck="false"
        />
        <div class="text-xs text-gray-500">
          💡 Tip: Use <b>Clone As...</b> to duplicate an existing profile, change id/title, then Save.
        </div>
        <div class="flex gap-2">
          <button
            class="px-3 py-1 border rounded hover:bg-gray-50"
            @click="cloneAs"
          >
            Clone As...
          </button>
          <button
            class="px-3 py-1 border rounded hover:bg-gray-50"
            @click="formatJson"
          >
            Format JSON
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{ 
  modelValue: boolean
  profile: any | null 
}>()

const emit = defineEmits<{ 
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved', id: string): void 
}>()

const title = computed(() => 
  props.profile ? `Edit Machine: ${props.profile.id}` : 'New Machine Profile'
)

const working = ref<any>({})
const jsonText = ref('')

watch(() => props.profile, (p) => {
  working.value = p 
    ? JSON.parse(JSON.stringify(p)) 
    : {
        id: 'NewProfile',
        title: 'New Machine',
        controller: '',
        axes: { travel_mm: [0, 0, 0] },
        limits: {
          feed_xy: 1200,
          rapid: 3000,
          accel: 800,
          jerk: 2000,
          corner_tol_mm: 0.2
        },
        spindle: { max_rpm: 12000 },
        feed_override: { min: 0.5, max: 1.2 },
        post_id_default: null
      }
  jsonText.value = JSON.stringify(working.value, null, 2)
}, { immediate: true })

async function save() {
  try {
    const obj = JSON.parse(jsonText.value)
    const r = await fetch('/api/machine/profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(obj)
    })
    if (!r.ok) throw new Error(await r.text())
    emit('saved', obj.id)
    emit('update:modelValue', false)
  } catch (e: any) {
    alert(`Save failed: ${e.message || e}`)
  }
}

async function cloneAs() {
  const newId = prompt('New ID for clone:', (working.value.id || 'NewProfile') + '_Copy')
  if (!newId) return
  
  const newTitle = prompt('Title:', (working.value.title || '') + ' (Copy)')
  
  try {
    const r = await fetch(
      `/api/machine/profiles/clone/${encodeURIComponent(working.value.id)}?new_id=${encodeURIComponent(newId)}&new_title=${encodeURIComponent(newTitle || '')}`,
      { method: 'POST' }
    )
    if (!r.ok) {
      const errorText = await r.text()
      alert(`Clone failed: ${errorText}`)
      return
    }
    const { id } = await r.json()
    emit('saved', id)
    emit('update:modelValue', false)
  } catch (e: any) {
    alert(`Clone failed: ${e.message || e}`)
  }
}

function formatJson() {
  try {
    const obj = JSON.parse(jsonText.value)
    jsonText.value = JSON.stringify(obj, null, 2)
  } catch (e: any) {
    alert(`Invalid JSON: ${e.message || e}`)
  }
}
</script>
